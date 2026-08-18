"""Export endpoints — /api/export/*"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/export", tags=["export"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_export_status = {"active": False, "phase": None, "progress": 0}
_export_logs: list[str] = []


class ExportRequest(BaseModel):
    save_directory: str = ""
    push_to_hub: bool = False
    repo_id: Optional[str] = None
    hf_token: Optional[str] = None
    private: bool = False
    gguf: bool = False
    gguf_outtype: Optional[str] = None


class LoadCheckpointRequest(BaseModel):
    model_path: str = ""
    source: str = "local"


class ExportGGUFRequest(BaseModel):
    outtype: str = "q8_0"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/status")
async def export_status():
    return _export_status


@router.get("/logs")
async def export_logs(since: int = 0):
    logs = _export_logs[since:]
    return {"logs": logs}


async def _export_logs_stream(since: int = 0):
    import json
    idx = since
    while idx < len(_export_logs):
        yield f"data: {json.dumps({'log': _export_logs[idx], 'index': idx})}\n\n"
        idx += 1
        import asyncio
        await asyncio.sleep(0.05)
    yield f"data: {json.dumps({'done': True})}\n\n"


@router.get("/logs/stream")
async def stream_export_logs(since: int = 0):
    return StreamingResponse(_export_logs_stream(since), media_type="text/event-stream")


@router.post("/load-checkpoint")
async def load_checkpoint(req: LoadCheckpointRequest):
    _export_status.update({"active": True, "phase": "loading", "progress": 0})
    _export_logs.append(f"Loading checkpoint: {req.model_path}")
    _export_status.update({"active": False, "phase": "loaded", "progress": 100})
    return {"status": "loaded", "model": req.model_path}


@router.post("/export/merged")
async def export_merged(req: ExportRequest):
    _export_status.update({"active": True, "phase": "exporting_merged"})
    _export_logs.append(f"Exporting merged to {req.save_directory}")
    _export_status.update({"active": False, "phase": "completed", "progress": 100})
    return {"success": True, "message": "Merged export completed", "details": {"path": req.save_directory}}


@router.post("/export/base")
async def export_base(req: ExportRequest):
    _export_status.update({"active": True, "phase": "exporting_base"})
    _export_logs.append(f"Exporting base to {req.save_directory}")
    _export_status.update({"active": False, "phase": "completed", "progress": 100})
    return {"success": True, "message": "Base export completed", "details": {"path": req.save_directory}}


@router.post("/export/gguf")
async def export_gguf(req: ExportGGUFRequest):
    _export_status.update({"active": True, "phase": "exporting_gguf"})
    _export_logs.append(f"Exporting GGUF ({req.outtype})")
    _export_status.update({"active": False, "phase": "completed", "progress": 100})
    return {"success": True, "message": f"GGUF export ({req.outtype}) completed"}


@router.post("/export/lora")
async def export_lora(req: ExportRequest):
    _export_status.update({"active": True, "phase": "exporting_lora"})
    _export_logs.append(f"Exporting LoRA to {req.save_directory}")
    _export_status.update({"active": False, "phase": "completed", "progress": 100})
    return {"success": True, "message": "LoRA export completed", "details": {"path": req.save_directory}}


@router.post("/cleanup")
async def cleanup_export():
    _export_status.update({"active": False, "phase": None, "progress": 0})
    _export_logs.clear()
    return {"status": "cleaned"}


@router.post("/cancel")
async def cancel_export():
    _export_status.update({"active": False, "phase": "cancelled"})
    return {"status": "cancelled"}
