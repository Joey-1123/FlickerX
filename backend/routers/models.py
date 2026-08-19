"""Models router — list, config, VRAM summary, load/unload, load times."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import MODELS_DIR

router = APIRouter()


def _scan_local_models() -> list[dict]:
    models = []
    if not MODELS_DIR.exists():
        return models
    for entry in MODELS_DIR.iterdir():
        if entry.is_dir():
            gguf_files = list(entry.glob("*.gguf"))
            models.append({
                "name": entry.name,
                "path": str(entry),
                "type": "gguf" if gguf_files else "directory",
                "size_bytes": sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()),
                "files": [f.name for f in gguf_files],
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
        "hf_cache_dir": None,
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
    return {"load_times": {}}


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
    return {"folders": folders}


@router.get("/gguf-variants")
def gguf_variants(repo_id: str):
    return {"variants": [], "repo_id": repo_id}


@router.get("/kv-cache-estimate")
def kv_cache_estimate(repo_id: str, quant: str = "q4_0", n_ctx: int = 4096, cache_type_kv: str = "f16"):
    return {"kv_bytes": 0, "weights_bytes": 0, "native_context": 0}


@router.get("/recommended-folders")
def recommended_folders():
    return {"folders": [str(MODELS_DIR)]}


@router.get("/browse-folders")
def browse_folders(path: str = "/", show_hidden: bool = False):
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    entries = []
    for entry in sorted(p.iterdir()):
        if not show_hidden and entry.name.startswith("."):
            continue
        entries.append({"name": entry.name, "path": str(entry), "is_dir": entry.is_dir()})
    return {"path": str(p), "entries": entries}


@router.get("/loras")
def list_loras(outputs_dir: str = ""):
    return {"loras": []}


@router.get("/checkpoints")
def list_checkpoints():
    return {"outputs_dir": str(MODELS_DIR), "models": []}
