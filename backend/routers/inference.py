"""Inference router — load, unload, status, load-progress, active-generations, monitor, completions."""

from __future__ import annotations

import json
import os
import time
import threading
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth import get_current_user

router = APIRouter()

# Inference state
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

# ponytail: global LLM instance — one model at a time, swap requires unload+load
_llm: Any = None  # llama_cpp.Llama instance


class LoadModelRequest(BaseModel):
    model_path: str
    n_ctx: int = 4096
    gpu_layers: int | None = None  # None = auto-detect GPU
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
    from pathlib import Path
    path = Path(req.model_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_path}")

    # Unload existing model first
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

    return {
        "status": "loaded",
        "model_path": str(path),
        "model_name": path.name,
        "n_ctx": req.n_ctx,
        "gpu_layers": resolved_gpu_layers,
    }


@router.post("/unload")
def unload_model(req: UnloadModelRequest | None = None, user: dict = Depends(get_current_user)):
    global _llm
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
    return {"status": "unloaded"}


# --- Monitor ---

@router.get("/monitor")
def api_monitor():
    return {"entries": [], "total": 0}


@router.get("/monitor/{entry_id}")
def api_monitor_entry(entry_id: str):
    return {"id": entry_id, "status": "not_found"}


@router.delete("/monitor")
def clear_api_monitor():
    return {"cleared": True}


# --- Tool confirmation ---

@router.post("/tool-confirm")
def resolve_tool_confirmation(body: dict, user: dict = Depends(get_current_user)):
    return {"resolved": True}


# --- Token counting ---

@router.post("/chat/count_tokens")
def count_tokens(req: CountTokensRequest, user: dict = Depends(get_current_user)):
    total = 0
    for msg in req.messages:
        if isinstance(msg.content, str):
            total += len(msg.content.split()) * 1.3
        elif isinstance(msg.content, list):
            for part in msg.content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += len(part.get("text", "").split()) * 1.3
    return {"input_tokens": int(total), "model": req.model}
