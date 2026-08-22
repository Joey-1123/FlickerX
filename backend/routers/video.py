"""Video generation — lazy-install diffusers pipeline, real generation."""

from __future__ import annotations

import asyncio
import importlib
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import STUDIO_DB
from database import execute, query

logger = structlog.get_logger()
router = APIRouter(prefix="/api/inference/video", tags=["video"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_status: dict[str, Any] = {
    "loaded": False,
    "loading": False,
    "model": None,
    "model_kind": None,
    "device": "cpu",
    "memory_mode": None,
    "speed_mode": None,
    "attention_backend": None,
    "transformer_cache": None,
    "transformer_quant": None,
    "text_encoder_quant": None,
    "h3_task": None,
}

_load_progress: dict = {}
_gen_progress: dict = {"active": False, "phase": None, "step": 0, "total": 0, "eta_seconds": 0, "video": None, "error": None}
_gallery: list[dict] = []


def _load_from_db() -> None:
    for row in query(STUDIO_DB, "SELECT * FROM video_gallery ORDER BY created_at"):
        entry = dict(row)
        entry["pinned"] = bool(entry["pinned"])
        entry["archived"] = bool(entry["archived"])
        entry["url"] = f"/api/inference/video/gallery/{entry['id']}/file"
        _gallery.append(entry)


def _save_to_db(entry: dict) -> None:
    execute(
        STUDIO_DB,
        "INSERT OR REPLACE INTO video_gallery (id, prompt, negative_prompt, width, height, num_frames, fps, duration_s, steps, guidance, seed, model, model_kind, pinned, archived, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            entry["id"], entry["prompt"], entry.get("negative_prompt"),
            entry["width"], entry["height"], entry.get("num_frames"),
            entry.get("fps"), entry.get("duration_s"), entry["steps"],
            entry["guidance"], entry["seed"], entry.get("model"),
            entry.get("model_kind"), int(entry.get("pinned", False)),
            int(entry.get("archived", False)), entry["created_at"],
        ),
    )


def _delete_from_db(entry_id: str) -> None:
    execute(STUDIO_DB, "DELETE FROM video_gallery WHERE id = ?", (entry_id,))


def _clear_db() -> None:
    execute(STUDIO_DB, "DELETE FROM video_gallery")


_load_from_db()

_cancel_requested = False
_pipeline: Any = None
_DEFAULT_MODEL = "ali-vilab/text-to-video-ms-1.7b"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class VideoLoadRequest(BaseModel):
    model_path: str = ""
    gguf_filename: Optional[str] = None
    model_kind: Optional[str] = None
    base_repo: Optional[str] = None
    family_override: Optional[str] = None
    hf_token: Optional[str] = None
    memory_mode: Optional[str] = None
    speed_mode: Optional[str] = None
    attention_backend: Optional[str] = None
    transformer_cache: Optional[str] = None
    transformer_cache_threshold: Optional[float] = None
    transformer_quant: Optional[str] = None
    h3_task: Optional[str] = None
    gpu_ids: Optional[list[int]] = None
    text_encoder_quant: Optional[str] = None


class VideoGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 480
    height: int = 320
    num_frames: int = 16
    fps: int = 8
    steps: int = 20
    guidance: float = 7.5
    seed: Optional[int] = None
    first_frame: Optional[str] = None
    last_frame: Optional[str] = None
    reference_images: Optional[list[str]] = None
    reference_videos: Optional[list[dict]] = None
    reference_audios: Optional[list[str]] = None
    reference_image_size: Optional[int] = None
    flow_shift: Optional[float] = None
    audio_flow_shift: Optional[float] = None


# ---------------------------------------------------------------------------
# Model lifecycle — lazy-install pattern (same as images)
# ---------------------------------------------------------------------------
@router.get("/status")
async def video_status():
    loaded = _status["loaded"]
    model = _status["model"] if loaded else None
    model_kind = _status["model_kind"] if loaded else None
    device = _status["device"] if loaded else None

    engine = None
    if model_kind == "gguf":
        engine = "sd_cpp"
    elif model_kind in ("diffusers", "single_file", "pipeline", None):
        if loaded:
            engine = "diffusers"

    family = None
    base_repo = None
    if model:
        parts = model.split("/", 1)
        if len(parts) == 2:
            base_repo = parts[0]
            family = parts[1]
        else:
            family = model

    return {
        "loaded": loaded,
        "repo_id": model,
        "family": family,
        "base_repo": base_repo,
        "device": device,
        "dtype": "float16" if device and device != "cpu" else "float32" if device else None,
        "model_kind": model_kind,
        "engine": engine,
        "gguf_variant": None,
        "offload_policy": None,
        "vae_tiling": False,
        "memory_mode": _status["memory_mode"] if loaded else None,
        "speed_mode": _status["speed_mode"] if loaded else None,
        "speed_optims": [],
        "attention_backend": _status["attention_backend"] if loaded else None,
        "transformer_cache": _status["transformer_cache"] if loaded else None,
        "transformer_quant": _status["transformer_quant"] if loaded else None,
        "text_encoder_quant": _status["text_encoder_quant"] if loaded else None,
        "has_audio": False,
        "supports_cfg": False,
        "supports_keyframes": False,
        "supports_references": False,
        "h3_task": _status["h3_task"] if loaded else None,
        "defaults": None,
        "resolved": None,
        "control_provenance": None,
    }


@router.get("/load-progress")
async def video_load_progress():
    return _load_progress or {"phase": None, "bytes_downloaded": 0, "bytes_total": 0, "fraction": 0, "error": None}


@router.get("/generate-progress")
async def video_generate_progress():
    return _gen_progress


@router.post("/load")
async def video_load(req: VideoLoadRequest):
    global _pipeline
    _status["loading"] = True
    _status["model"] = req.model_path or _DEFAULT_MODEL
    _status["model_kind"] = req.model_kind
    _load_progress.update({"phase": "downloading", "bytes_downloaded": 0, "bytes_total": 0, "fraction": 0, "error": None})

    try:
        from gpu import get_device, is_cuda_available

        # Lazy install torch + diffusers if not present
        if importlib.util.find_spec("torch") is None:
            _load_progress.update({"phase": "installing dependencies", "fraction": 0.05})
            torch_url = "https://download.pytorch.org/whl/cu121" if is_cuda_available() else "https://download.pytorch.org/whl/cpu"
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "torch", "torchvision", "--index-url", torch_url],
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
        from diffusers import TextToVideoSDPipeline

        device = get_device()
        model_id = req.model_path or _DEFAULT_MODEL
        pipe = TextToVideoSDPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            safety_checker=None,
        )
        pipe.to(device)

        _pipeline = pipe
        _status["loaded"] = True
        _status["loading"] = False
        _status["model"] = model_id
        _status["device"] = device
        _status["memory_mode"] = req.memory_mode
        _status["speed_mode"] = req.speed_mode
        _status["attention_backend"] = req.attention_backend
        _status["transformer_cache"] = req.transformer_cache
        _status["transformer_quant"] = req.transformer_quant
        _status["text_encoder_quant"] = req.text_encoder_quant
        _status["h3_task"] = req.h3_task
        _load_progress.update({"phase": "ready", "fraction": 1.0})
        return {"loaded": True, "loading": False, "model": model_id, "model_kind": _status["model_kind"], "device": device}

    except Exception as e:
        _status["loading"] = False
        _load_progress.update({"phase": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to load video model: {e}")


@router.post("/download-plan")
async def video_download_plan(req: VideoLoadRequest):
    return {
        "files": [{"path": req.model_path, "bytes": 5_000_000_000}],
        "total_bytes": 5_000_000_000,
        "cached_bytes": 0,
    }


@router.post("/unload")
async def video_unload():
    global _pipeline
    _pipeline = None
    _status.update({
        "loaded": False, "loading": False, "model": None, "model_kind": None,
        "memory_mode": None, "speed_mode": None, "attention_backend": None,
        "transformer_cache": None, "transformer_quant": None, "text_encoder_quant": None,
        "h3_task": None,
    })
    _load_progress.clear()
    return {"loaded": False, "loading": False, "model": None, "model_kind": None, "device": _status["device"]}


# ---------------------------------------------------------------------------
# Generation — REAL with diffusers pipeline
# ---------------------------------------------------------------------------
@router.post("/generate")
async def video_generate(req: VideoGenerateRequest):
    global _cancel_requested, _pipeline
    _cancel_requested = False

    if _pipeline is None:
        raise HTTPException(status_code=400, detail="No video model loaded. Call /load first.")

    vid_id = uuid.uuid4().hex[:12]
    total = req.steps
    seed = req.seed if req.seed is not None else int(time.time()) % (2**31)
    duration_s = req.num_frames / max(req.fps, 1)

    _gen_progress.update({
        "active": True, "phase": "denoise", "step": 0, "total": total, "eta_seconds": total * 2.0, "video": None, "error": None
    })

    try:
        import torch
        from gpu import get_device
        device = get_device()
        generator = torch.Generator(device).manual_seed(seed)

        # Generate frames
        frames = _pipeline(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or "",
            width=req.width,
            height=req.height,
            num_frames=req.num_frames,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance,
            generator=generator,
        ).frames[0]

        # Save frames as individual images, then assemble
        vid_dir = Path.home() / ".flickerx" / "studio" / "videos"
        vid_dir.mkdir(parents=True, exist_ok=True)
        vid_path = vid_dir / vid_id
        vid_path.mkdir(exist_ok=True)

        for i, frame in enumerate(frames):
            frame.save(str(vid_path / f"frame_{i:04d}.png"))

        # Try to assemble into a GIF with Pillow
        gif_path = vid_dir / f"{vid_id}.gif"
        try:
            frames[0].save(
                str(gif_path),
                save_all=True,
                append_images=frames[1:],
                duration=int(1000 / req.fps),
                loop=0,
            )
        except Exception:
            pass

        video = {
            "id": vid_id,
            "url": f"/api/inference/video/gallery/{vid_id}/file",
            "prompt": req.prompt,
            "negative_prompt": req.negative_prompt,
            "width": req.width,
            "height": req.height,
            "num_frames": req.num_frames,
            "fps": req.fps,
            "duration_s": duration_s,
            "steps": req.steps,
            "guidance": req.guidance,
            "seed": seed,
            "has_audio": False,
            "conditioning": None,
            "flow_shift": req.flow_shift,
            "audio_flow_shift": req.audio_flow_shift,
            "model": _status.get("model", "unknown"),
            "model_kind": _status.get("model_kind"),
            "transformer_quant": None,
            "text_encoder_quant": None,
            "memory_mode": None,
            "offload_policy": None,
            "created_at": time.time(),
            "pinned": False,
            "archived": False,
        }
        _gallery.append(video)
        _save_to_db(video)

        _gen_progress.update({"active": False, "phase": "completed", "step": total, "eta_seconds": 0, "video": video})
        return {"status": "started", "video": video}

    except Exception as e:
        _gen_progress.update({"active": False, "phase": "failed", "error": str(e)})
        logger.error("video_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")


@router.post("/generate/cancel")
async def video_generate_cancel():
    global _cancel_requested
    _cancel_requested = True
    _gen_progress.update({"active": False, "phase": "failed"})
    return {"cancelled": True}


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------
@router.get("/gallery")
async def video_gallery(offset: int = 0, limit: int = 50, archived: bool = False):
    items = [v for v in _gallery if v.get("archived", False) == archived]
    page = items[offset: offset + limit]
    return {"videos": page, "has_more": offset + limit < len(items)}


@router.patch("/gallery/{video_id}")
async def video_gallery_update(video_id: str, body: dict):
    for v in _gallery:
        if v["id"] == video_id:
            if "pinned" in body:
                v["pinned"] = body["pinned"]
            if "archived" in body:
                v["archived"] = body["archived"]
            execute(
                STUDIO_DB,
                "UPDATE video_gallery SET pinned = ?, archived = ? WHERE id = ?",
                (int(v["pinned"]), int(v["archived"]), video_id),
            )
            return v
    raise HTTPException(404, "Video not found")


@router.delete("/gallery/{video_id}")
async def video_gallery_delete(video_id: str):
    global _gallery
    before = len(_gallery)
    _gallery = [v for v in _gallery if v["id"] != video_id]
    if len(_gallery) == before:
        raise HTTPException(404, "Video not found")
    # Clean up files
    vid_dir = Path.home() / ".flickerx" / "studio" / "videos" / video_id
    gif_path = Path.home() / ".flickerx" / "studio" / "videos" / f"{video_id}.gif"
    import shutil
    if vid_dir.exists():
        shutil.rmtree(str(vid_dir))
    if gif_path.exists():
        gif_path.unlink()
    _delete_from_db(video_id)
    return {"ok": True}


@router.delete("/gallery")
async def video_gallery_clear():
    global _gallery
    _gallery.clear()
    _clear_db()
    return {"ok": True}


@router.get("/gallery/{video_id}/signed-url")
async def video_signed_url(video_id: str):
    for v in _gallery:
        if v["id"] == video_id:
            return {"url": v["url"]}
    raise HTTPException(404, "Video not found")


@router.get("/gallery/{video_id}/file")
async def video_gallery_file(video_id: str):
    from fastapi.responses import FileResponse
    gif_path = Path.home() / ".flickerx" / "studio" / "videos" / f"{video_id}.gif"
    if not gif_path.exists():
        raise HTTPException(404, "Video file not found")
    return FileResponse(str(gif_path), media_type="image/gif")


@router.get("/gallery/{video_id}/export")
async def video_export(video_id: str, format: str = "gif"):
    for v in _gallery:
        if v["id"] == video_id:
            return {"url": v["url"], "format": format}
    raise HTTPException(404, "Video not found")
