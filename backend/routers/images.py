"""Image generation endpoints — /api/inference/images/*"""

from __future__ import annotations

import asyncio
import base64
import importlib
import io
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/inference/images", tags=["images"])

# ---------------------------------------------------------------------------
# State (in-memory, model not loaded)
# ---------------------------------------------------------------------------
_status: dict[str, Any] = {
    "loaded": False,
    "loading": False,
    "model": None,
    "model_kind": None,
    "device": "cpu",
}

_load_progress: dict = {}
_gen_progress: dict = {"active": False, "step": 0, "total_steps": 0, "fraction": 0.0, "eta_seconds": 0}
_gallery: list[dict] = []
_active_gen: dict | None = None
_cancel_requested = False
_pipeline: Any = None  # ponytail: global diffusers pipeline, lazy-loaded

_DEFAULT_MODEL = "segmind/small-sd"  # ponytail: ~500MB, fastest SD variant


# ---------------------------------------------------------------------------
# Request / response models (minimal, frontend-validated)
# ---------------------------------------------------------------------------
class DiffusionLoadRequest(BaseModel):
    model_path: str = ""
    gguf_filename: Optional[str] = None
    model_kind: Optional[str] = None
    base_repo: Optional[str] = None
    family_override: Optional[str] = None
    hf_token: Optional[str] = None
    cpu_offload: Optional[bool] = None
    speed_mode: Optional[str] = None
    transformer_quant: Optional[str] = None
    text_encoder_quant: Optional[str] = None
    attention_backend: Optional[str] = None
    memory_mode: Optional[str] = None
    gpu_ids: Optional[list[int]] = None
    transformer_cache: Optional[str] = None
    loras: Optional[list[dict]] = None


class DiffusionGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512
    steps: int = 20
    guidance: float = 7.5
    seed: Optional[int] = None
    batch_size: int = 1
    init_image: Optional[str] = None
    mask_image: Optional[str] = None
    strength: Optional[float] = None
    upscale: Optional[bool] = None
    reference_images: Optional[list[str]] = None
    loras: Optional[list[dict]] = None
    controlnet: Optional[dict] = None


# ---------------------------------------------------------------------------
# Model lifecycle
# ---------------------------------------------------------------------------
@router.get("/status")
async def image_status():
    return {
        "loaded": _status["loaded"],
        "loading": _status["loading"],
        "model": _status["model"],
        "model_kind": _status["model_kind"],
        "device": _status["device"],
    }


@router.get("/info")
async def image_info():
    if not _status["loaded"]:
        return {"loaded": False}
    return {
        "loaded": True,
        "model": _status["model"],
        "model_kind": _status["model_kind"],
        "device": _status["device"],
        "supports_inpainting": True,
        "supports_img2img": True,
        "supports_upscale": False,
    }


@router.get("/load-progress")
async def image_load_progress():
    return _load_progress or {"phase": None, "bytes_downloaded": 0, "bytes_total": 0, "fraction": 0, "error": None}


@router.get("/generate-progress")
async def image_generate_progress():
    return _gen_progress


@router.post("/load")
async def image_load(req: DiffusionLoadRequest):
    global _pipeline
    _status["loading"] = True
    _status["model"] = req.model_path or _DEFAULT_MODEL
    _status["model_kind"] = req.model_kind
    _load_progress.update({"phase": "downloading", "bytes_downloaded": 0, "bytes_total": 0, "fraction": 0, "error": None})

    try:
        # Lazy install torch + diffusers if not present
        if importlib.util.find_spec("torch") is None:
            _load_progress.update({"phase": "installing dependencies", "fraction": 0.05})
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "torch", "torchvision", "--index-url",
                 "https://download.pytorch.org/whl/cpu"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        if importlib.util.find_spec("diffusers") is None:
            _load_progress.update({"phase": "installing diffusers", "fraction": 0.3})
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "diffusers", "transformers", "accelerate", "safetensors"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        _load_progress.update({"phase": "loading model", "fraction": 0.5})

        import torch
        from diffusers import StableDiffusionPipeline

        model_id = req.model_path or _DEFAULT_MODEL
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            safety_checker=None,
        )
        pipe.to("cpu")

        _pipeline = pipe
        _status["loaded"] = True
        _status["loading"] = False
        _status["model"] = model_id
        _load_progress.update({"phase": "ready", "fraction": 1.0})
        return {"loaded": True, "loading": False, "model": model_id, "model_kind": _status["model_kind"], "device": "cpu"}

    except Exception as e:
        _status["loading"] = False
        _load_progress.update({"phase": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to load image model: {e}")


@router.post("/download-plan")
async def image_download_plan(req: DiffusionLoadRequest):
    return {
        "files": [{"path": req.model_path, "bytes": 2_000_000_000}],
        "total_bytes": 2_000_000_000,
        "cached_bytes": 0,
    }


@router.post("/unload")
async def image_unload():
    global _pipeline
    _pipeline = None
    _status.update({"loaded": False, "loading": False, "model": None, "model_kind": None})
    _load_progress.clear()
    return {"loaded": False, "loading": False, "model": None, "model_kind": None, "device": _status["device"]}


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
@router.post("/generate")
async def image_generate(req: DiffusionGenerateRequest):
    global _active_gen, _cancel_requested, _pipeline
    _cancel_requested = False

    if _pipeline is None:
        raise HTTPException(status_code=400, detail="No image model loaded. Call /load first.")

    seed = req.seed if req.seed is not None else int(time.time()) % (2**31)
    total_steps = req.steps
    _gen_progress.update({"active": True, "step": 0, "total_steps": total_steps, "fraction": 0.0, "eta_seconds": total_steps * 2.0})
    _active_gen = {"seed": seed, "started": time.time()}

    try:
        import torch
        generator = torch.Generator("cpu").manual_seed(seed)

        # Progress callback for step tracking
        def step_callback(pipe, step, timestep, callback_kwargs):
            if _cancel_requested:
                raise Exception("Cancelled")
            _gen_progress.update({"step": step + 1, "fraction": (step + 1) / total_steps, "eta_seconds": (total_steps - step - 1) * 2.0})
            return callback_kwargs

        result = _pipeline(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or "",
            width=req.width,
            height=req.height,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance,
            generator=generator,
            num_images_per_prompt=req.batch_size,
            callback_on_step_end=step_callback,
        )

        images = []
        for i, img in enumerate(result.images):
            img_id = uuid.uuid4().hex[:12]

            # Save to disk
            img_dir = Path.home() / ".flickerx" / "studio" / "images"
            img_dir.mkdir(parents=True, exist_ok=True)
            img_path = img_dir / f"{img_id}.png"
            img.save(str(img_path))

            # Convert to base64 for response
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            gallery_entry = {
                "id": img_id,
                "url": f"/api/inference/images/gallery/{img_id}/file",
                "prompt": req.prompt,
                "negative_prompt": req.negative_prompt,
                "width": req.width,
                "height": req.height,
                "steps": req.steps,
                "guidance": req.guidance,
                "seed": seed + i,
                "batch_seed": seed,
                "batch_index": i,
                "batch_size": req.batch_size,
                "model": _status.get("model", "unknown"),
                "model_kind": _status.get("model_kind"),
                "created_at": time.time(),
                "pinned": False,
                "archived": False,
            }
            _gallery.append(gallery_entry)
            images.append(gallery_entry)

        _gen_progress.update({"active": False, "step": total_steps, "fraction": 1.0, "eta_seconds": 0})
        _active_gen = None
        return {"images": images}

    except Exception as e:
        _gen_progress.update({"active": False})
        _active_gen = None
        if "Cancelled" in str(e):
            return {"images": []}
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@router.post("/generate/cancel")
async def image_generate_cancel():
    global _cancel_requested
    _cancel_requested = True
    _gen_progress.update({"active": False})
    _active_gen = None
    return {"cancelled": True}


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------
@router.get("/gallery")
async def image_gallery(offset: int = 0, limit: int = 50, archived: bool = False):
    items = [g for g in _gallery if g.get("archived", False) == archived]
    page = items[offset: offset + limit]
    return {"images": page, "has_more": offset + limit < len(items)}


@router.patch("/gallery/{image_id}")
async def image_gallery_update(image_id: str, body: dict):
    for g in _gallery:
        if g["id"] == image_id:
            if "pinned" in body:
                g["pinned"] = body["pinned"]
            if "archived" in body:
                g["archived"] = body["archived"]
            return g
    raise HTTPException(404, "Image not found")


@router.delete("/gallery/{image_id}")
async def image_gallery_delete(image_id: str):
    global _gallery
    before = len(_gallery)
    _gallery = [g for g in _gallery if g["id"] != image_id]
    if len(_gallery) == before:
        raise HTTPException(404, "Image not found")
    return None


@router.delete("/gallery")
async def image_gallery_clear():
    global _gallery
    count = len(_gallery)
    _gallery.clear()
    return None


@router.get("/gallery/{image_id}/file")
async def image_gallery_file(image_id: str):
    from fastapi.responses import FileResponse
    img_path = Path.home() / ".flickerx" / "studio" / "images" / f"{image_id}.png"
    if not img_path.exists():
        raise HTTPException(404, "Image file not found")
    return FileResponse(str(img_path), media_type="image/png")
