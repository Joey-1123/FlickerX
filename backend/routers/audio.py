"""Audio endpoints — /api/inference/audio/*"""

from __future__ import annotations

import asyncio
import base64
import io
import tempfile
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import STUDIO_DB
from database import execute, query

router = APIRouter(prefix="/api/inference/audio", tags=["audio"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_stt_model: Any = None  # ponytail: global whisper instance — one at a time

_stt_status = {
    "available": False,
    "loaded_model": None,
    "loading": False,
    "device": "cpu",
    "keep_alive_seconds": 300,
    "default_model": "openai/whisper-base",
    "models": [
        "openai/whisper-tiny",
        "openai/whisper-base",
        "openai/whisper-small",
        "openai/whisper-medium",
        "openai/whisper-large-v3",
    ],
}

_audio_gallery: list[dict] = []


def _load_from_db() -> None:
    for row in query(STUDIO_DB, "SELECT * FROM audio_gallery ORDER BY created_at"):
        _audio_gallery.append(dict(row))


def _save_to_db(clip: dict) -> None:
    execute(
        STUDIO_DB,
        "INSERT OR REPLACE INTO audio_gallery (id, prompt, model, audio_type, sample_rate, duration_s, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (clip["id"], clip.get("prompt"), clip.get("model"), clip.get("audio_type"),
         clip.get("sample_rate"), clip.get("duration_s"), clip["created_at"]),
    )


def _delete_from_db(clip_id: str) -> None:
    execute(STUDIO_DB, "DELETE FROM audio_gallery WHERE id = ?", (clip_id,))


def _clear_db() -> None:
    execute(STUDIO_DB, "DELETE FROM audio_gallery")


_load_from_db()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    messages: list[dict]
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048


class SttLoadRequest(BaseModel):
    model: str = "openai/whisper-base"
    engine: str = "transformers"


class SttValidateRequest(BaseModel):
    model: str = "openai/whisper-base"


# ---------------------------------------------------------------------------
# TTS — Audio Generation
# ---------------------------------------------------------------------------
@router.post("/generate")
async def audio_generate(req: TTSRequest):
    # Extract text from messages
    text = " ".join(m.get("content", "") for m in req.messages if m.get("role") == "user")
    if not text:
        text = "Hello, this is a test audio clip."

    clip_id = uuid.uuid4().hex[:12]
    # Generate a tiny silent WAV as placeholder (1 second, 16kHz, mono, 16-bit)
    # Real impl would use TTS model
    sample_rate = 24000
    duration_s = max(0.5, len(text) * 0.05)  # rough estimate
    num_samples = int(sample_rate * duration_s)

    # Minimal PCM silence (no actual audio data — placeholder)
    pcm_bytes = b"\x00\x00" * num_samples
    wav_header = _make_wav_header(sample_rate, num_samples)
    wav_bytes = wav_header + pcm_bytes
    audio_b64 = base64.b64encode(wav_bytes).decode()

    clip = {
        "id": clip_id,
        "url": f"/api/inference/audio/gallery/{clip_id}/file",
        "prompt": text[:200],
        "model": "tts-placeholder",
        "audio_type": "wav",
        "sample_rate": sample_rate,
        "duration_s": duration_s,
        "created_at": time.time(),
    }
    _audio_gallery.append(clip)
    _save_to_db(clip)

    return {
        "model": "tts-placeholder",
        "audio": {"data": audio_b64, "format": "wav", "sample_rate": sample_rate},
        "clip_id": clip_id,
    }


# ---------------------------------------------------------------------------
# STT — Speech to Text
# ---------------------------------------------------------------------------
@router.get("/stt/status")
async def stt_status(refresh: bool = False, model: str = ""):
    return {**_stt_status}


@router.post("/stt/validate")
async def stt_validate(req: SttValidateRequest):
    if req.model in _stt_status["models"]:
        return {"valid": True, "model": req.model}
    raise HTTPException(400, f"Unknown model: {req.model}")


@router.post("/stt/load")
async def stt_load(req: SttLoadRequest):
    global _stt_model
    _stt_status["loading"] = True
    _stt_status["available"] = False
    try:
        from faster_whisper import WhisperModel
        from gpu import get_device
        device = get_device()
        compute_type = "float16" if device != "cpu" else "int8"
        _stt_model = WhisperModel(req.model, device=device, compute_type=compute_type)
        _stt_status["device"] = device
        _stt_status["loading"] = False
        _stt_status["available"] = True
        _stt_status["loaded_model"] = req.model
        return {"loaded": True, "model": req.model}
    except Exception as e:
        _stt_status["loading"] = False
        raise HTTPException(status_code=500, detail=f"Failed to load STT model: {e}")


@router.post("/stt/download")
async def stt_download(req: SttLoadRequest):
    return {"status": "started", "model": req.model}


@router.post("/stt/download/cancel")
async def stt_download_cancel(req: SttLoadRequest):
    return {"cancelled": True}


@router.post("/stt/unload")
async def stt_unload(engine: str = "", model: str = ""):
    global _stt_model
    _stt_model = None
    _stt_status.update({"available": False, "loaded_model": None})
    return {"unloaded": True}


@router.post("/transcribe/raw")
async def transcribe_raw(
    request: Request,
    model: str = "openai/whisper-base",
    fast: bool = True,
    engine: str = "",
    language: str = "",
):
    global _stt_model

    if _stt_model is None:
        raise HTTPException(status_code=400, detail="No STT model loaded. Call /stt/load first.")

    audio_bytes = await request.body()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data in request body")

    # Write to temp file — faster-whisper needs a file path or numpy array
    suffix = ".webm"
    ct = request.headers.get("content-type", "")
    if "wav" in ct:
        suffix = ".wav"
    elif "mp3" in ct:
        suffix = ".mp3"
    elif "ogg" in ct:
        suffix = ".ogg"
    elif "flac" in ct:
        suffix = ".flac"
    elif "mpeg" in ct:
        suffix = ".mp3"

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            segments, info = _stt_model.transcribe(
                tmp.name,
                language=language if language else None,
                beam_size=1 if fast else 5,
                vad_filter=fast,
            )
            text = " ".join(seg.text.strip() for seg in segments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    return {"text": text, "language": info.language if info else language}


# ---------------------------------------------------------------------------
# Audio Gallery
# ---------------------------------------------------------------------------
@router.get("/gallery")
async def audio_gallery(offset: int = 0, limit: int = 50, before_mtime: float = 0, before_id: str = ""):
    items = sorted(_audio_gallery, key=lambda c: c["created_at"], reverse=True)
    if before_mtime:
        items = [c for c in items if c["created_at"] < before_mtime]
    page = items[offset: offset + limit]
    has_more = offset + limit < len(items)
    next_before_mtime = page[-1]["created_at"] if has_more and page else None
    next_before_id = page[-1]["id"] if has_more and page else None
    return {"audio": page, "has_more": has_more, "next_before_mtime": next_before_mtime, "next_before_id": next_before_id}


@router.delete("/gallery/{clip_id}")
async def audio_gallery_delete(clip_id: str):
    global _audio_gallery
    before = len(_audio_gallery)
    _audio_gallery = [c for c in _audio_gallery if c["id"] != clip_id]
    if len(_audio_gallery) == before:
        raise HTTPException(404, "Clip not found")
    _delete_from_db(clip_id)
    return None


@router.delete("/gallery")
async def audio_gallery_clear():
    global _audio_gallery
    count = len(_audio_gallery)
    _audio_gallery.clear()
    _clear_db()
    return {"removed": count}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_wav_header(sample_rate: int, num_samples: int) -> bytes:
    """Build a minimal WAV file header for PCM 16-bit mono."""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align
    header = bytearray(44)
    header[0:4] = b"RIFF"
    header[4:8] = (36 + data_size).to_bytes(4, "little")
    header[8:12] = b"WAVE"
    header[12:16] = b"fmt "
    header[16:20] = (16).to_bytes(4, "little")  # chunk size
    header[20:22] = (1).to_bytes(2, "little")  # PCM
    header[22:24] = num_channels.to_bytes(2, "little")
    header[24:28] = sample_rate.to_bytes(4, "little")
    header[28:32] = byte_rate.to_bytes(4, "little")
    header[32:34] = block_align.to_bytes(2, "little")
    header[34:36] = bits_per_sample.to_bytes(2, "little")
    header[36:40] = b"data"
    header[40:44] = data_size.to_bytes(4, "little")
    return bytes(header)
