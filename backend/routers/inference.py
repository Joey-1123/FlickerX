"""Inference router — load, unload, status, load-progress, active-generations, monitor, completions, validate, llama-flags."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth import get_current_user

router = APIRouter()

_inference_state: dict[str, Any] = {
    "loaded": False,
    "model_path": None,
    "model_name": None,
    "n_ctx": 4096,
    "gpu_layers": -1,
    "loaded_at": None,
    "load_progress": {"phase": "idle", "bytes_loaded": 0, "bytes_total": 0, "fraction": 0.0},
}
_inference_lock = threading.Lock()
_active_generations: dict[str, dict] = {}
_monitor_entries: list[dict] = []
_tool_confirmations: dict[str, dict] = {}

_llm: Any = None


class LoadModelRequest(BaseModel):
    model_path: str
    n_ctx: int = 4096
    gpu_layers: int | None = None
    n_batch: int = 512
    n_threads: int | None = None
    adapter_path: str | None = None
    chat_template: str | None = None
    trust_remote_code: bool = False
    use_mmap: bool = True
    use_mlock: bool = False
    rope_freq_base: float | None = None
    rope_freq_scale: float | None = None
    flash_attn: bool = False
    mul_mat_q: bool = True
    no_kv_offload: bool = False
    cache_type_k: str = "f16"
    cache_type_v: str = "f16"
    n_parallel: int = 1


class UnloadModelRequest(BaseModel):
    model_path: str | None = None


class OpenAIChatMessage(BaseModel):
    role: str
    content: str | list | None = None
    tool_calls: list | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[OpenAIChatMessage]
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    top_k: int = 40
    min_p: float = 0.05
    repetition_penalty: float = 1.1
    presence_penalty: float = 0.0
    stop: str | list[str] | None = None
    n: int = 1
    user: str | None = None
    session_id: str | None = None
    cancel_id: str | None = None


class CountTokensRequest(BaseModel):
    model: str
    messages: list[OpenAIChatMessage]
    enable_thinking: bool | None = None
    reasoning_effort: str | None = None


# --- Monitor helpers ---

def _add_monitor_event(event_type: str, data: dict) -> None:
    entry = {"id": uuid.uuid4().hex[:8], "type": event_type, "data": data, "timestamp": time.time()}
    _monitor_entries.append(entry)
    if len(_monitor_entries) > 200:
        _monitor_entries.pop(0)


# --- Status ---

@router.get("/status")
def inference_status():
    with _inference_lock:
        return {
            "loaded": _inference_state["loaded"],
            "model_path": _inference_state["model_path"],
            "model_name": _inference_state["model_name"],
            "n_ctx": _inference_state["n_ctx"],
            "gpu_layers": _inference_state["gpu_layers"],
            "loaded_at": _inference_state["loaded_at"],
        }


@router.get("/load-progress")
def load_progress():
    with _inference_lock:
        return _inference_state["load_progress"]


@router.get("/active-generations")
def active_generations():
    with _inference_lock:
        active = {k: v for k, v in _active_generations.items() if v.get("active")}
    return {
        "count": len(active),
        "thread_ids": list(active.keys()),
        "active": bool(active),
        "parallel_slots": 1,
    }


# --- Load/Unload ---

@router.post("/load")
def load_model(req: LoadModelRequest, user: dict = Depends(get_current_user)):
    global _llm
    path = Path(req.model_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_path}")

    load_start = time.time()

    if _llm is not None:
        del _llm
        _llm = None

    try:
        from gpu import get_n_gpu_layers
        from llama_cpp import Llama
        n_threads = req.n_threads or max(1, os.cpu_count() // 2)
        resolved_gpu_layers = req.gpu_layers if req.gpu_layers is not None else get_n_gpu_layers()
        _llm = Llama(
            model_path=str(path),
            n_ctx=req.n_ctx,
            n_gpu_layers=resolved_gpu_layers,
            n_batch=req.n_batch,
            n_threads=n_threads,
            verbose=False,
        )
    except Exception as e:
        _llm = None
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")

    load_seconds = time.time() - load_start
    from routers.models import record_load_time
    record_load_time(str(path), load_seconds)

    with _inference_lock:
        _inference_state.update({
            "loaded": True,
            "model_path": str(path),
            "model_name": path.name,
            "n_ctx": req.n_ctx,
            "gpu_layers": resolved_gpu_layers,
            "loaded_at": time.time(),
            "load_progress": {"phase": "loaded", "bytes_loaded": 0, "bytes_total": 0, "fraction": 1.0},
        })

    _add_monitor_event("model_loaded", {"model": path.name, "load_seconds": round(load_seconds, 2)})

    return {
        "status": "loaded",
        "model_path": str(path),
        "model_name": path.name,
        "n_ctx": req.n_ctx,
        "gpu_layers": resolved_gpu_layers,
        "load_seconds": round(load_seconds, 2),
    }


@router.post("/unload")
def unload_model(req: UnloadModelRequest | None = None, user: dict = Depends(get_current_user)):
    global _llm
    old_name = _inference_state.get("model_name")
    if _llm is not None:
        del _llm
        _llm = None
    with _inference_lock:
        _inference_state.update({
            "loaded": False,
            "model_path": None,
            "model_name": None,
            "loaded_at": None,
            "load_progress": {"phase": "idle", "bytes_loaded": 0, "bytes_total": 0, "fraction": 0.0},
        })
    if old_name:
        _add_monitor_event("model_unloaded", {"model": old_name})
    return {"status": "unloaded"}


# --- Monitor ---

@router.get("/monitor")
def api_monitor(limit: int = 50):
    entries = _monitor_entries[-limit:]
    return {"entries": entries, "total": len(_monitor_entries)}


@router.get("/monitor/{entry_id}")
def api_monitor_entry(entry_id: str):
    for e in _monitor_entries:
        if e["id"] == entry_id:
            return e
    raise HTTPException(404, "Monitor entry not found")


@router.delete("/monitor")
def clear_api_monitor():
    _monitor_entries.clear()
    return {"cleared": True}


# --- Tool confirmation ---

@router.post("/tool-confirm")
def resolve_tool_confirmation(body: dict, user: dict = Depends(get_current_user)):
    confirmation_id = body.get("id", "")
    approved = body.get("approved", True)
    if confirmation_id in _tool_confirmations:
        _tool_confirmations[confirmation_id]["status"] = "approved" if approved else "denied"
        _tool_confirmations[confirmation_id]["resolved_at"] = time.time()
    return {"resolved": True, "approved": approved}


@router.get("/tool-confirmations")
def list_tool_confirmations():
    pending = {k: v for k, v in _tool_confirmations.items() if v.get("status") == "pending"}
    return {"pending": pending, "total": len(_tool_confirmations)}


# --- Token counting ---

@router.post("/chat/count_tokens")
def count_tokens(req: CountTokensRequest, user: dict = Depends(get_current_user)):
    if _llm is not None:
        try:
            total = 0
            for msg in req.messages:
                text = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                if text:
                    tokens = _llm.tokenize(text.encode("utf-8"))
                    total += len(tokens)
            return {"input_tokens": total, "model": req.model}
        except Exception:
            pass
    # Fallback: ~4 chars per token heuristic
    total = 0
    for msg in req.messages:
        if isinstance(msg.content, str):
            total += len(msg.content) / 4
        elif isinstance(msg.content, list):
            for part in msg.content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += len(part.get("text", "")) / 4
    return {"input_tokens": int(total), "model": req.model}


# --- Chat completions proxy ---

@router.post("/chat/completions")
def inference_chat_completions(req: ChatCompletionRequest):
    from routers.chat import chat_completions
    return chat_completions(req)


# --- Validate model ---

@router.post("/validate")
def validate_model(body: dict):
    path = body.get("path", body.get("model_path", ""))
    if not path:
        return {"valid": False, "error": "No path provided"}
    p = Path(path)
    if not p.exists():
        return {"valid": False, "error": f"Path not found: {path}"}
    issues = []
    if p.is_file():
        if p.suffix == ".gguf":
            try:
                with open(p, "rb") as f:
                    magic = f.read(4)
                    if magic != b"GGUF":
                        issues.append("Not a valid GGUF file (bad magic)")
            except Exception as e:
                issues.append(f"Cannot read file: {e}")
        return {"valid": len(issues) == 0, "issues": issues, "path": str(p)}
    # Directory: check for model files
    model_files = list(p.glob("*.gguf")) + list(p.glob("*.safetensors")) + list(p.glob("*.bin"))
    config = p / "config.json"
    tokenizer = p / "tokenizer.json"
    if not model_files:
        issues.append("No model weight files found (.gguf, .safetensors, .bin)")
    if not config.exists() and not tokenizer.exists():
        issues.append("No config.json or tokenizer.json found")
    return {"valid": len(issues) == 0, "issues": issues, "path": str(p), "model_files": [f.name for f in model_files]}


# --- Llama-flags ---

@router.get("/llama-flags")
def llama_flags():
    flags = []
    # Check llama-cpp-python build config
    try:
        from llama_cpp import Llama
        # Try to get build info
        import llama_cpp
        lib_path = Path(llama_cpp.__file__).parent
        cmake_cache = lib_path / "llama.cpp" / "build" / "CMakeCache.txt"
        if cmake_cache.exists():
            content = cmake_cache.read_text()
            if "LLAMA_CUDA=ON" in content:
                flags.append({"flag": "LLAMA_CUDA", "enabled": True, "description": "CUDA GPU acceleration"})
            if "LLAMA_VULKAN=ON" in content:
                flags.append({"flag": "LLAMA_VULKAN", "enabled": True, "description": "Vulkan GPU acceleration"})
            if "LLAMA_METAL=ON" in content:
                flags.append({"flag": "LLAMA_METAL", "enabled": True, "description": "Apple Metal acceleration"})
            if "LLAMA_HIPBLAS=ON" in content:
                flags.append({"flag": "LLAMA_HIPBLAS", "enabled": True, "description": "ROCm GPU acceleration"})
            if "LLAMA_AVX2=ON" in content:
                flags.append({"flag": "LLAMA_AVX2", "enabled": True, "description": "AVX2 CPU acceleration"})
    except Exception:
        pass
    # Check GPU availability regardless
    if shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                flags.append({"flag": "NVIDIA_GPU", "enabled": True, "description": f"NVIDIA GPU: {result.stdout.strip()}"})
        except Exception:
            pass
    if not flags:
        flags.append({"flag": "CPU_ONLY", "enabled": True, "description": "CPU-only mode (no GPU flags detected)"})
    return {"flags": flags}


# --- Transformers management ---

@router.post("/install-latest-transformers")
def install_latest_transformers():
    try:
        result = subprocess.run(
            [shutil.which("pip") or "pip", "install", "--upgrade", "transformers", "accelerate", "bitsandbytes"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return {"ok": True, "message": "transformers upgraded successfully", "output": result.stdout[-500:]}
        return {"ok": False, "message": f"Install failed: {result.stderr[-500:]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "message": "Install timed out after 120s"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


@router.post("/transformers-upgrade-check")
def transformers_upgrade_check():
    try:
        import importlib.metadata
        current = importlib.metadata.version("transformers")
        result = subprocess.run(
            [shutil.which("pip") or "pip", "index", "versions", "transformers"],
            capture_output=True, text=True, timeout=15,
        )
        latest = current
        if result.returncode == 0 and "Available versions:" in result.stdout:
            versions_line = result.stdout.split("Available versions:")[1].strip()
            latest = versions_line.split(",")[0].strip()
        return {"current_version": current, "latest_version": latest, "upgrade_available": current != latest}
    except Exception:
        return {"current_version": "unknown", "latest_version": "unknown", "upgrade_available": False}


# --- Codex containers (real Docker detection) ---

@router.post("/external/openai/containers/list")
def list_containers():
    if not shutil.which("docker"):
        return {"containers": [], "docker_available": False}
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=10,
        )
        containers = []
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return {"containers": containers, "docker_available": True}
    except Exception as e:
        return {"containers": [], "docker_available": False, "error": str(e)}


@router.post("/external/openai/containers/create")
def create_container(body: dict):
    if not shutil.which("docker"):
        return {"container_id": None, "status": "error", "message": "Docker not installed"}
    image = body.get("image", "python:3.11-slim")
    try:
        result = subprocess.run(
            ["docker", "run", "-d", "--name", f"flickerx-codex-{uuid.uuid4().hex[:6]}", image, "sleep", "infinity"],
            capture_output=True, text=True, timeout=30,
        )
        container_id = result.stdout.strip()[:12] if result.returncode == 0 else None
        return {"container_id": container_id, "status": "created" if container_id else "failed", "error": result.stderr if result.returncode else None}
    except Exception as e:
        return {"container_id": None, "status": "failed", "message": str(e)}


@router.post("/external/openai/containers/delete")
def delete_container(body: dict):
    container_id = body.get("container_id", "")
    if not container_id or not shutil.which("docker"):
        return {"ok": True}
    try:
        subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, timeout=10)
        return {"ok": True, "deleted": container_id}
    except Exception:
        return {"ok": True}
