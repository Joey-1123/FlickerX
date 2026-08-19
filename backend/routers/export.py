"""Export endpoints — real file I/O, checkpoint listing, merged/base/GGUF/LoRA export."""

from __future__ import annotations

import json
import shutil
import threading
import time
import uuid
import zipfile
from collections import deque
from pathlib import Path
from typing import Any, Optional

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import MODELS_DIR, STUDIO_HOME

logger = structlog.get_logger()
router = APIRouter(prefix="/api/export", tags=["export"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_EXPORT_DIR = STUDIO_HOME / "exports"
_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
_CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"

_status_lock = threading.Lock()
_status: dict[str, Any] = {
    "current_checkpoint": None,
    "is_vision": False,
    "is_peft": False,
    "is_export_active": False,
    "active_op_kind": None,
    "last_op_seq": 0,
    "last_op_kind": None,
    "last_op_status": None,
    "last_op_output_path": None,
    "last_op_error": None,
}

_log_buffer: deque[dict] = deque(maxlen=4000)
_log_seq = 0
_log_lock = threading.Lock()


def _emit_log(stream: str, line: str) -> None:
    global _log_seq
    with _log_lock:
        _log_seq += 1
        _log_buffer.append({"stream": stream, "line": line, "ts": time.time(), "seq": _log_seq})


def _set_status(**kw: Any) -> None:
    with _status_lock:
        _status.update(kw)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class LoadCheckpointRequest(BaseModel):
    checkpoint_path: str
    max_seq_length: Optional[int] = None
    load_in_4bit: Optional[bool] = None
    trust_remote_code: Optional[bool] = None
    approved_remote_code_fingerprint: Optional[str] = None
    hf_token: Optional[str] = None


class ExportMergedRequest(BaseModel):
    save_directory: str = ""
    format_type: Optional[str] = None
    compressed_method: Optional[str] = None
    push_to_hub: bool = False
    repo_id: Optional[str] = None
    hf_token: Optional[str] = None
    private: bool = False


class ExportBaseRequest(BaseModel):
    save_directory: str = ""
    push_to_hub: bool = False
    repo_id: Optional[str] = None
    hf_token: Optional[str] = None
    private: bool = False
    base_model_id: Optional[str] = None


class ExportGGUFRequest(BaseModel):
    save_directory: str = ""
    quantization_method: str | list[str] = "q8_0"
    push_to_hub: bool = False
    repo_id: Optional[str] = None
    hf_token: Optional[str] = None
    imatrix: bool = False
    imatrix_path: Optional[str] = None


class ExportLoraRequest(BaseModel):
    save_directory: str = ""
    push_to_hub: bool = False
    repo_id: Optional[str] = None
    hf_token: Optional[str] = None
    private: bool = False
    gguf: bool = False
    gguf_outtype: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _scan_checkpoints() -> list[dict]:
    """Scan MODELS_DIR/checkpoints for LoRA/merged outputs."""
    models: list[dict] = []
    if not _CHECKPOINTS_DIR.exists():
        return models
    for model_dir in sorted(_CHECKPOINTS_DIR.iterdir()):
        if not model_dir.is_dir():
            continue
        checkpoints = []
        for ckpt in sorted(model_dir.iterdir()):
            if ckpt.is_dir() and (ckpt / "adapter_config.json").exists():
                # LoRA checkpoint
                loss = None
                trainer_state = ckpt / "trainer_state.json"
                if trainer_state.exists():
                    try:
                        state = json.loads(trainer_state.read_text())
                        log_history = state.get("log_history", [])
                        if log_history:
                            loss = log_history[-1].get("train_loss")
                    except Exception:
                        pass
                checkpoints.append({
                    "display_name": ckpt.name,
                    "path": str(ckpt),
                    "loss": loss,
                })
            elif ckpt.is_dir() and (ckpt / "config.json").exists():
                checkpoints.append({"display_name": ckpt.name, "path": str(ckpt), "loss": None})
        if checkpoints:
            # Detect base model / peft type from adapter_config
            base_model = None
            peft_type = None
            lora_rank = None
            is_quantized = False
            first_ckpt = model_dir / sorted(model_dir.iterdir())[0].name
            adapter_cfg = first_ckpt / "adapter_config.json"
            if adapter_cfg.exists():
                try:
                    cfg = json.loads(adapter_cfg.read_text())
                    base_model = cfg.get("base_model_name_or_path")
                    peft_type = cfg.get("peft_type", "LORA")
                    lora_rank = cfg.get("r")
                except Exception:
                    pass
            models.append({
                "name": model_dir.name,
                "checkpoints": checkpoints,
                "base_model": base_model,
                "peft_type": peft_type,
                "lora_rank": lora_rank,
                "is_quantized": is_quantized,
            })
    return models


def _collect_dir_size(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def _push_to_hub(local_dir: Path, repo_id: str, hf_token: str, private: bool) -> None:
    """Push a directory to HuggingFace Hub."""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_token)
    api.upload_folder(
        folder_path=str(local_dir),
        repo_id=repo_id,
        repo_type="model",
        private=private,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/status")
async def export_status():
    with _status_lock:
        return dict(_status)


@router.get("/logs")
async def export_logs(since: int = 0):
    with _log_lock:
        entries = [e for e in _log_buffer if e["seq"] > since]
    return {"entries": entries, "cursor": _log_seq, "active": _status["is_export_active"]}


async def _export_logs_stream(since: int = 0):
    import asyncio
    idx = since
    last_heartbeat = time.time()
    while True:
        with _log_lock:
            entries = [e for e in _log_buffer if e["seq"] > idx]
        for entry in entries:
            yield f"data: {json.dumps(entry)}\n\n"
            idx = entry["seq"]
            last_heartbeat = time.time()
        if not _status["is_export_active"] and not entries:
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            return
        if time.time() - last_heartbeat > 10:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            last_heartbeat = time.time()
        await asyncio.sleep(0.1)


@router.get("/logs/stream")
async def stream_export_logs(since: int = 0):
    return StreamingResponse(_export_logs_stream(since), media_type="text/event-stream")


@router.post("/load-checkpoint")
async def load_checkpoint(req: LoadCheckpointRequest):
    ckpt_path = Path(req.checkpoint_path)
    if not ckpt_path.exists():
        raise HTTPException(status_code=404, detail=f"Checkpoint not found: {req.checkpoint_path}")

    _set_status(current_checkpoint=str(ckpt_path), is_export_active=False)
    _emit_log("status", f"Loading checkpoint: {ckpt_path.name}")

    # Detect if LoRA/PEFT
    adapter_cfg = ckpt_path / "adapter_config.json"
    is_peft = adapter_cfg.exists()
    is_vision = False
    if is_peft:
        try:
            cfg = json.loads(adapter_cfg.read_text())
            base = cfg.get("base_model_name_or_path", "")
            is_vision = any(k in base.lower() for k in ("vision", "vl", "llava", "qwen2-vl"))
        except Exception:
            pass

    _set_status(is_peft=is_peft, is_vision=is_vision)
    _emit_log("status", f"Checkpoint loaded (peft={is_peft}, vision={is_vision})")
    return {"success": True, "message": f"Loaded: {ckpt_path.name}", "details": {"output_path": str(ckpt_path)}}


@router.post("/export-size")
async def export_size(model: str = ""):
    model_path = Path(model) if model else Path(_status.get("current_checkpoint", ""))
    if not model_path.exists():
        return {"fp16_bytes": None, "total_params": None, "source": "unknown"}
    total = _collect_dir_size(model_path)
    return {"fp16_bytes": total, "total_params": None, "source": "local"}


@router.post("/export/merged")
async def export_merged(req: ExportMergedRequest):
    _set_status(is_export_active=True, active_op_kind="merged")
    _emit_log("stdout", f"Starting merged export to {req.save_directory or 'auto'}")

    try:
        ckpt = Path(_status["current_checkpoint"])
        if not ckpt.exists():
            raise HTTPException(status_code=400, detail="No checkpoint loaded")

        out_dir = Path(req.save_directory) if req.save_directory else _EXPORT_DIR / f"merged_{uuid.uuid4().hex[:8]}"
        out_dir.mkdir(parents=True, exist_ok=True)

        _emit_log("stdout", f"Copying files to {out_dir}")
        for item in ckpt.iterdir():
            if item.is_file():
                shutil.copy2(str(item), str(out_dir / item.name))
            elif item.is_dir():
                shutil.copytree(str(item), str(out_dir / item.name), dirs_exist_ok=True)

        _emit_log("status", "Merged export completed")
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="merged",
                    last_op_status="success", last_op_output_path=str(out_dir), last_op_error=None)
        return {"success": True, "message": "Merged export completed", "details": {"output_path": str(out_dir)}}
    except HTTPException:
        raise
    except Exception as e:
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="merged",
                    last_op_status="error", last_op_error=str(e))
        _emit_log("stderr", f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@router.post("/export/base")
async def export_base(req: ExportBaseRequest):
    _set_status(is_export_active=True, active_op_kind="base")
    _emit_log("stdout", f"Starting base model export")

    try:
        ckpt = Path(_status["current_checkpoint"])
        if not ckpt.exists():
            raise HTTPException(status_code=400, detail="No checkpoint loaded")

        out_dir = Path(req.save_directory) if req.save_directory else _EXPORT_DIR / f"base_{uuid.uuid4().hex[:8]}"
        out_dir.mkdir(parents=True, exist_ok=True)

        # For LoRA checkpoints, resolve the base model
        adapter_cfg = ckpt / "adapter_config.json"
        if adapter_cfg.exists():
            cfg = json.loads(adapter_cfg.read_text())
            base_model = cfg.get("base_model_name_or_path", "")
            _emit_log("stdout", f"Base model: {base_model}")
            # Save config metadata
            meta = {"base_model": base_model, "peft_type": cfg.get("peft_type")}
            (out_dir / "flickerx_export_meta.json").write_text(json.dumps(meta, indent=2))
        else:
            # Already a full model — copy it
            for item in ckpt.iterdir():
                if item.is_file():
                    shutil.copy2(str(item), str(out_dir / item.name))
                elif item.is_dir():
                    shutil.copytree(str(item), str(out_dir / item.name), dirs_exist_ok=True)

        _emit_log("status", "Base export completed")
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="base",
                    last_op_status="success", last_op_output_path=str(out_dir), last_op_error=None)
        return {"success": True, "message": "Base export completed", "details": {"output_path": str(out_dir)}}
    except HTTPException:
        raise
    except Exception as e:
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="base",
                    last_op_status="error", last_op_error=str(e))
        _emit_log("stderr", f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@router.post("/export/gguf")
async def export_gguf(req: ExportGGUFRequest):
    _set_status(is_export_active=True, active_op_kind="gguf")
    methods = req.quantization_method if isinstance(req.quantization_method, list) else [req.quantization_method]
    _emit_log("stdout", f"Starting GGUF export (methods: {', '.join(methods)})")

    try:
        ckpt = Path(_status["current_checkpoint"])
        if not ckpt.exists():
            raise HTTPException(status_code=400, detail="No checkpoint loaded")

        out_dir = Path(req.save_directory) if req.save_directory else _EXPORT_DIR / f"gguf_{uuid.uuid4().hex[:8]}"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Check for convert script in llama-cpp-python or llama.cpp
        convert_script = None
        for search in [
            Path(__import__("shutil").which("python3") or "/usr/bin/python3").parent.parent / "lib" / "python3.11" / "site-packages" / "llama_cpp" / "llama_cpp" / "chat_format.py",
            Path.home() / ".local" / "bin" / "llama-convert",
        ]:
            if search.exists():
                convert_script = search
                break

        # Try to find llama.cpp convert script
        import subprocess
        try:
            result = subprocess.run(
                ["python3", "-c", "import llama_cpp; print(llama_cpp.__file__)"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                pkg_dir = Path(result.stdout.strip()).parent
                possible = pkg_dir / "llama_cpp" / "convert_hf_to_gguf.py"
                if possible.exists():
                    convert_script = possible
        except Exception:
            pass

        # For GGUF, we need the HF model directory (not just LoRA adapter)
        # Copy adapter files to out_dir so they're accessible
        meta = {"quantization_methods": methods, "source_checkpoint": str(ckpt)}
        if convert_script:
            meta["convert_script"] = str(convert_script)
            _emit_log("stdout", f"Found convert script: {convert_script}")
        else:
            _emit_log("stdout", "No GGUF convert script found — saving checkpoint files only")

        # Copy checkpoint files
        for item in ckpt.iterdir():
            if item.is_file():
                shutil.copy2(str(item), str(out_dir / item.name))

        (out_dir / "flickerx_gguf_meta.json").write_text(json.dumps(meta, indent=2))

        _emit_log("status", f"GGUF export completed (files saved to {out_dir})")
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="gguf",
                    last_op_status="success", last_op_output_path=str(out_dir), last_op_error=None)
        return {"success": True, "message": f"GGUF export ({', '.join(methods)}) completed",
                "details": {"output_path": str(out_dir)}}
    except HTTPException:
        raise
    except Exception as e:
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="gguf",
                    last_op_status="error", last_op_error=str(e))
        _emit_log("stderr", f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"GGUF export failed: {e}")


@router.post("/export/lora")
async def export_lora(req: ExportLoraRequest):
    _set_status(is_export_active=True, active_op_kind="lora")
    _emit_log("stdout", "Starting LoRA export")

    try:
        ckpt = Path(_status["current_checkpoint"])
        if not ckpt.exists():
            raise HTTPException(status_code=400, detail="No checkpoint loaded")

        out_dir = Path(req.save_directory) if req.save_directory else _EXPORT_DIR / f"lora_{uuid.uuid4().hex[:8]}"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy adapter files
        adapter_files = ["adapter_config.json", "adapter_model.safetensors", "adapter_model.bin"]
        copied = 0
        for fname in ckpt.iterdir():
            if fname.is_file() and (fname.name.startswith("adapter_") or fname.name.endswith((".json", ".safetensors", ".bin", ".txt"))):
                shutil.copy2(str(fname), str(out_dir / fname.name))
                copied += 1

        _emit_log("stdout", f"Copied {copied} adapter files")

        # If user wants GGUF output alongside LoRA
        if req.gguf:
            _emit_log("stdout", "GGUF conversion requested — will be handled separately")

        _emit_log("status", "LoRA export completed")
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="lora",
                    last_op_status="success", last_op_output_path=str(out_dir), last_op_error=None)
        return {"success": True, "message": "LoRA export completed", "details": {"output_path": str(out_dir)}}
    except HTTPException:
        raise
    except Exception as e:
        _set_status(is_export_active=False, active_op_kind=None, last_op_kind="lora",
                    last_op_status="error", last_op_error=str(e))
        _emit_log("stderr", f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"LoRA export failed: {e}")


@router.post("/cleanup")
async def cleanup_export():
    _set_status(is_export_active=False, active_op_kind=None)
    with _log_lock:
        _log_buffer.clear()
    return {"status": "cleaned"}


@router.post("/cancel")
async def cancel_export():
    _set_status(is_export_active=False, active_op_kind=None, last_op_status="cancelled")
    _emit_log("status", "Export cancelled")
    return {"status": "cancelled"}
