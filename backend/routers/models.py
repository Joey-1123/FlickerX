"""Models router — list, config, VRAM summary, load/unload, load times, GGUF variants."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import MODELS_DIR, STUDIO_HOME

router = APIRouter()

# Track model load times in-memory
_load_times: dict[str, dict] = {}
_SCAN_FOLDERS_FILE = STUDIO_HOME / "model_scan_folders.json"


def _read_json_file(path: Path, default=None):
    if default is None:
        default = []
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _write_json_file(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _scan_local_models() -> list[dict]:
    models = []
    if not MODELS_DIR.exists():
        return models
    for entry in MODELS_DIR.iterdir():
        if entry.is_dir():
            gguf_files = list(entry.glob("*.gguf"))
            safetensor_files = list(entry.glob("*.safetensors"))
            config = None
            config_path = entry / "config.json"
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text())
                except Exception:
                    pass
            models.append({
                "name": entry.name,
                "path": str(entry),
                "type": "gguf" if gguf_files else ("safetensors" if safetensor_files else "directory"),
                "size_bytes": sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()),
                "files": [f.name for f in gguf_files] + [f.name for f in safetensor_files],
                "architecture": config.get("architectures", [None])[0] if config and "architectures" in config else None,
                "model_type": config.get("model_type") if config else None,
            })
    return models


@router.get("/list")
def list_models():
    local = _scan_local_models()
    return {
        "models": local,
        "default_models": {"llm": None, "image": None, "video": None, "audio": None},
    }


@router.get("/local")
def list_local_models():
    local = _scan_local_models()
    return {
        "models_dir": str(MODELS_DIR),
        "hf_cache_dir": str(Path.home() / ".cache" / "huggingface" / "hub"),
        "lmstudio_dirs": [],
        "models": local,
    }


@router.get("/config/defaults")
def model_config_defaults():
    return {
        "llm": {
            "n_ctx": 4096,
            "n_batch": 512,
            "n_threads": None,
            "gpu_layers": -1,
            "rope_freq_base": None,
            "rope_freq_scale": None,
            "mul_mat_q": True,
            "no_kv_offload": False,
            "flash_attn": False,
            "cache_type_k": "f16",
            "cache_type_v": "f16",
        },
        "image": {"width": 512, "height": 512, "steps": 30, "cfg_scale": 7.0},
        "video": {"width": 512, "height": 512, "frames": 24, "fps": 8},
        "audio": {"temperature": 0.7, "top_p": 0.9},
    }


@router.get("/config/llm")
def llm_config():
    return {
        "n_ctx": 4096,
        "n_batch": 512,
        "n_threads": None,
        "gpu_layers": -1,
        "rope_freq_base": None,
        "rope_freq_scale": None,
        "mul_mat_q": True,
        "no_kv_offload": False,
        "flash_attn": False,
        "cache_type_k": "f16",
        "cache_type_v": "f16",
    }


@router.get("/config/mlx")
def mlx_config():
    return {
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
    }


@router.get("/vram-summary")
def vram_summary():
    from routers.system import _get_gpu_info
    gpus = _get_gpu_info()
    total_vram = sum(g.get("vram_total_mb", 0) for g in gpus)
    used_vram = sum(g.get("vram_used_mb", 0) for g in gpus)
    return {
        "total_vram_mb": total_vram,
        "used_vram_mb": used_vram,
        "free_vram_mb": total_vram - used_vram,
        "gpus": gpus,
    }


@router.get("/load-times")
def load_times():
    return {"load_times": _load_times}


def record_load_time(model_path: str, load_seconds: float) -> None:
    name = Path(model_path).name
    _load_times[name] = {"path": model_path, "load_seconds": round(load_seconds, 3), "timestamp": time.time()}


@router.get("/model-load-defaults")
def model_load_defaults():
    return {
        "n_ctx": 4096,
        "gpu_layers": -1,
        "n_batch": 512,
        "n_threads": None,
    }


@router.get("/supported-quantizers")
def supported_quantizers():
    return {
        "quantizers": [
            {"id": "q2_k", "name": "Q2_K", "description": "Smallest, fastest, lowest quality"},
            {"id": "q3_k_s", "name": "Q3_K_S", "description": "Small"},
            {"id": "q3_k_m", "name": "Q3_K_M", "description": "Medium"},
            {"id": "q4_0", "name": "Q4_0", "description": "Fastest 4-bit"},
            {"id": "q4_k_s", "name": "Q4_K_S", "description": "Small, recommended"},
            {"id": "q4_k_m", "name": "Q4_K_M", "description": "Medium, recommended"},
            {"id": "q5_0", "name": "Q5_0", "description": "Fast 5-bit"},
            {"id": "q5_k_s", "name": "Q5_K_S", "description": "Small, high quality"},
            {"id": "q5_k_m", "name": "Q5_K_M", "description": "Medium, high quality"},
            {"id": "q6_k", "name": "Q6_K", "description": "Very high quality"},
            {"id": "q8_0", "name": "Q8_0", "description": "Near lossless"},
            {"id": "f16", "name": "F16", "description": "Full half precision"},
            {"id": "f32", "name": "F32", "description": "Full precision"},
        ]
    }


@router.get("/supported-methods")
def supported_methods():
    return {
        "methods": [
            {"id": "base", "name": "Base (no quantization)"},
            {"id": "imatrix", "name": "Importance Matrix"},
        ]
    }


class LoadModelRequest(BaseModel):
    model_path: str
    n_ctx: int = 4096
    gpu_layers: int = -1
    n_batch: int = 512
    n_threads: int | None = None


@router.post("/load")
def load_model(req: LoadModelRequest, user: dict = Depends(get_current_user)):
    path = Path(req.model_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_path}")
    return {
        "status": "loaded",
        "model_path": str(path),
        "n_ctx": req.n_ctx,
        "gpu_layers": req.gpu_layers,
    }


@router.post("/unload")
def unload_model(user: dict = Depends(get_current_user)):
    return {"status": "unloaded"}


@router.get("/scan-folders")
def scan_folders():
    folders = []
    if MODELS_DIR.exists():
        folders.append({"id": "default", "path": str(MODELS_DIR), "name": "Default models folder"})
    custom = _read_json_file(_SCAN_FOLDERS_FILE, [])
    folders.extend(custom)
    return {"folders": folders}


@router.get("/gguf-variants")
def gguf_variants(repo_id: str):
    variants = []
    model_dir = MODELS_DIR / repo_id.replace("/", "_")
    if not model_dir.exists():
        model_dir = MODELS_DIR / repo_id
    if model_dir.exists():
        for f in model_dir.rglob("*.gguf"):
            quant = _parse_quant_from_filename(f.name)
            variants.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "quantization": quant,
            })
    return {"variants": variants, "repo_id": repo_id}


def _parse_quant_from_filename(name: str) -> str | None:
    lower = name.lower()
    for q in ("q2_k", "q3_k_s", "q3_k_m", "q3_k_l", "q4_0", "q4_k_s", "q4_k_m",
              "q5_0", "q5_k_s", "q5_k_m", "q6_k", "q8_0", "f16", "f32"):
        if q in lower:
            return q.upper()
    return None


@router.get("/kv-cache-estimate")
def kv_cache_estimate(repo_id: str, quant: str = "q4_0", n_ctx: int = 4096, cache_type_kv: str = "f16"):
    # Try to read model config for actual parameters
    model_dir = MODELS_DIR / repo_id.replace("/", "_")
    if not model_dir.exists():
        model_dir = MODELS_DIR / repo_id

    n_layers = 32
    n_heads = 32
    head_dim = 128
    n_params = 7_000_000_000  # default 7B

    config_path = model_dir / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            n_layers = config.get("num_hidden_layers", n_layers)
            n_heads = config.get("num_attention_heads", n_heads)
            hidden = config.get("hidden_size", n_heads * head_dim)
            head_dim = hidden // n_heads
            # Estimate n_params from config
            if "num_parameters" in config:
                n_params = config["num_parameters"]
        except Exception:
            pass

    # Bytes per element based on cache type
    bytes_per_element = {"f16": 2, "f32": 4, "q8_0": 1, "q4_0": 0.5}.get(cache_type_kv, 2)

    # KV cache = 2 (K+V) * n_layers * n_ctx * n_heads * head_dim * bytes_per_element
    kv_bytes = 2 * n_layers * n_ctx * n_heads * head_dim * bytes_per_element

    # Weight size estimate from quant type
    bits_per_weight = {"q2_k": 2.5, "q3_k_s": 3, "q3_k_m": 3.4, "q4_0": 4, "q4_k_s": 4.5,
                       "q4_k_m": 4.7, "q5_0": 5, "q5_k_s": 5.5, "q5_k_m": 5.7, "q6_k": 6.5,
                       "q8_0": 8, "f16": 16, "f32": 32}.get(quant, 4)
    weights_bytes = int(n_params * bits_per_weight / 8)

    # Native context: assume 4096 default
    native_context = 4096

    return {
        "kv_bytes": kv_bytes,
        "weights_bytes": weights_bytes,
        "native_context": native_context,
        "n_layers": n_layers,
        "n_heads": n_heads,
        "head_dim": head_dim,
        "n_params": n_params,
    }


@router.get("/recommended-folders")
def recommended_folders():
    folders = [str(MODELS_DIR)]
    home = Path.home()
    candidates = [
        home / ".cache" / "huggingface" / "hub",
        home / ".local" / "share" / "lm-studio" / "models",
        Path("/usr/share/ollama/.ollama/models"),
        home / ".ollama" / "models",
        home / ".cache" / "lm-studio",
    ]
    for c in candidates:
        if c.exists() and str(c) not in folders:
            folders.append(str(c))
    return {"folders": folders}


@router.get("/browse-folders")
def browse_folders(path: str = "/", show_hidden: bool = False):
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    entries = []
    try:
        for entry in sorted(p.iterdir()):
            if not show_hidden and entry.name.startswith("."):
                continue
            entries.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else 0,
            })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"path": str(p), "entries": entries}


@router.get("/loras")
def list_loras(outputs_dir: str = ""):
    loras = []
    scan_dirs = [MODELS_DIR]
    if outputs_dir:
        scan_dirs.append(Path(outputs_dir))
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for entry in scan_dir.rglob("adapter_config.json"):
            try:
                cfg = json.loads(entry.read_text())
                parent = entry.parent
                adapter_model = parent / "adapter_model.safetensors"
                if not adapter_model.exists():
                    adapter_model = parent / "adapter_model.bin"
                loras.append({
                    "name": parent.name,
                    "path": str(parent),
                    "rank": cfg.get("r", cfg.get("rank")),
                    "lora_alpha": cfg.get("lora_alpha"),
                    "target_modules": cfg.get("target_modules", []),
                    "base_model": cfg.get("base_model_name_or_path", ""),
                    "size_bytes": adapter_model.stat().st_size if adapter_model.exists() else 0,
                })
            except Exception:
                pass
    return {"loras": loras}


@router.get("/checkpoints")
def list_checkpoints():
    checkpoints = []
    if MODELS_DIR.exists():
        for entry in MODELS_DIR.rglob("trainer_state.json"):
            try:
                state = json.loads(entry.read_text())
                parent = entry.parent
                checkpoints.append({
                    "name": parent.name,
                    "path": str(parent),
                    "epoch": state.get("epoch"),
                    "global_step": state.get("global_step"),
                    "best_metric": state.get("best_metric"),
                    "metrics": state.get("log_history", [])[-1] if state.get("log_history") else None,
                })
            except Exception:
                pass
    return {"outputs_dir": str(MODELS_DIR), "models": checkpoints}


@router.post("/scan-folders")
def scan_folders_post(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if not path:
        return {"ok": False, "error": "No path provided"}
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Path not found")
    if not p.is_dir():
        raise HTTPException(400, "Path is not a directory")
    # Scan for model files
    model_files = []
    for f in p.rglob("*"):
        if f.is_file() and f.suffix in (".gguf", ".safetensors", ".bin", ".pt", ".pth", ".onnx"):
            model_files.append({"name": f.name, "path": str(f), "size": f.stat().st_size, "type": f.suffix[1:]})
    return {"ok": True, "path": str(p), "models": model_files, "count": len(model_files)}


@router.delete("/delete-finetuned")
def delete_finetuned(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "No path provided")
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Path not found")
    import shutil
    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
    if p.is_dir():
        shutil.rmtree(str(p))
    else:
        p.unlink()
    return {"ok": True, "deleted_bytes": size}


@router.post("/discard-remote-code")
def discard_remote_code(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "No path provided")
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Path not found")
    removed = []
    remote_code_patterns = ("modeling_", "configuration_", "tokenization_", "processing_", "feature_extraction_")
    for f in p.glob("*.py"):
        if any(f.name.startswith(pat) for pat in remote_code_patterns):
            f.unlink()
            removed.append(f.name)
    return {"ok": True, "removed": removed, "count": len(removed)}


@router.post("/remote-code-scan")
def remote_code_scan(body: dict):
    path = body.get("path", "")
    if not path:
        return {"has_remote_code": False, "files": []}
    p = Path(path)
    if not p.exists():
        return {"has_remote_code": False, "files": []}
    remote_code_patterns = ("modeling_", "configuration_", "tokenization_", "processing_", "feature_extraction_")
    found = []
    for f in p.glob("*.py"):
        if any(f.name.startswith(pat) for pat in remote_code_patterns):
            found.append(f.name)
    return {"has_remote_code": len(found) > 0, "files": found}


@router.post("/reveal-cached-model")
def reveal_cached_model(body: dict, user: dict = Depends(get_current_user)):
    cache_path = body.get("path", "")
    if not cache_path:
        raise HTTPException(400, "No path provided")
    p = Path(cache_path)
    if not p.exists():
        raise HTTPException(404, "Source not found")
    model_name = body.get("name", p.name)
    dest = MODELS_DIR / model_name
    if dest.exists():
        return {"ok": True, "path": str(dest), "message": "Already in models directory"}
    import shutil
    if p.is_dir():
        shutil.copytree(str(p), str(dest))
    else:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(p), str(dest))
    return {"ok": True, "path": str(dest)}
