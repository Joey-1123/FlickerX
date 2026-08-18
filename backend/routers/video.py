"""Video generation endpoints — /api/inference/video/*"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/inference/video", tags=["video"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_status = {
    "loaded": False,
    "loading": False,
    "model": None,
    "model_kind": None,
    "device": "cpu",
}

_load_progress: dict = {}
_gen_progress: dict = {"active": False, "phase": None, "step": 0, "total": 0, "eta_seconds": 0, "video": None, "error": None}
_gallery: list[dict] = []
_cancel_requested = False


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
# Model lifecycle
# ---------------------------------------------------------------------------
@router.get("/status")
async def video_status():
    return {
        "loaded": _status["loaded"],
        "loading": _status["loading"],
        "model": _status["model"],
        "model_kind": _status["model_kind"],
        "device": _status["device"],
    }


@router.get("/load-progress")
async def video_load_progress():
    return _load_progress or {"phase": None, "bytes_downloaded": 0, "bytes_total": 0, "fraction": 0, "error": None}


@router.get("/generate-progress")
async def video_generate_progress():
    return _gen_progress


@router.post("/load")
async def video_load(req: VideoLoadRequest):
    _status["loading"] = True
    _status["model"] = req.model_path
    _status["model_kind"] = req.model_kind
    _load_progress.update({"phase": "downloading", "bytes_downloaded": 0, "bytes_total": 0, "fraction": 0, "error": None})

    await asyncio.sleep(2)

    _status["loaded"] = True
    _status["loading"] = False
    _load_progress.update({"phase": "ready", "fraction": 1.0})
    return {"loaded": True, "loading": False, "model": _status["model"], "model_kind": _status["model_kind"], "device": _status["device"]}


@router.post("/download-plan")
async def video_download_plan(req: VideoLoadRequest):
    return {
        "files": [{"path": req.model_path, "bytes": 5_000_000_000}],
        "total_bytes": 5_000_000_000,
        "cached_bytes": 0,
    }


@router.post("/unload")
async def video_unload():
    _status.update({"loaded": False, "loading": False, "model": None, "model_kind": None})
    _load_progress.clear()
    return {"loaded": False, "loading": False, "model": None, "model_kind": None, "device": _status["device"]}


# ---------------------------------------------------------------------------
# Generation (async — frontend polls generate-progress)
# ---------------------------------------------------------------------------
@router.post("/generate")
async def video_generate(req: VideoGenerateRequest):
    global _cancel_requested
    _cancel_requested = False

    vid_id = uuid.uuid4().hex[:12]
    total = req.steps
    phases = ["queued", "denoise", "decode", "export"]
    seed = req.seed if req.seed is not None else int(time.time()) % (2**31)
    duration_s = req.num_frames / max(req.fps, 1)

    _gen_progress.update({
        "active": True, "phase": "denoise", "step": 0, "total": total, "eta_seconds": total * 2.0, "video": None, "error": None
    })

    # Simulate generation
    for step in range(1, total + 1):
        if _cancel_requested:
            _gen_progress.update({"active": False, "phase": "failed", "error": "Cancelled"})
            return {"status": "cancelled", "video": None}
        _gen_progress.update({"step": step, "eta_seconds": (total - step) * 2.0})
        await asyncio.sleep(0.15)

    # Decode phase
    _gen_progress.update({"phase": "decode", "step": total, "eta_seconds": 1.0})
    await asyncio.sleep(0.5)

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

    _gen_progress.update({"active": False, "phase": "completed", "step": total, "eta_seconds": 0, "video": video})
    return {"status": "started", "video": video}


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
            return v
    raise HTTPException(404, "Video not found")


@router.delete("/gallery/{video_id}")
async def video_gallery_delete(video_id: str):
    global _gallery
    before = len(_gallery)
    _gallery = [v for v in _gallery if v["id"] != video_id]
    if len(_gallery) == before:
        raise HTTPException(404, "Video not found")
    return None


@router.delete("/gallery")
async def video_gallery_clear():
    global _gallery
    _gallery.clear()
    return None


@router.get("/gallery/{video_id}/signed-url")
async def video_signed_url(video_id: str):
    for v in _gallery:
        if v["id"] == video_id:
            return {"url": v["url"]}
    raise HTTPException(404, "Video not found")


@router.get("/gallery/{video_id}/export")
async def video_export(video_id: str, format: str = "webm"):
    for v in _gallery:
        if v["id"] == video_id:
            return {"url": v["url"], "format": format}
    raise HTTPException(404, "Video not found")
