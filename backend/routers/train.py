"""Training endpoints — /api/train/*"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import STUDIO_DB
from database import execute, query

router = APIRouter(prefix="/api/train", tags=["training"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_job: dict | None = None
_runs: list[dict] = []
_metric_history: list[dict] = []
_cancel_requested = False
_start_requests: dict[str, dict] = {}


def _load_runs_from_db() -> None:
    for row in query(STUDIO_DB, "SELECT * FROM training_runs ORDER BY created_at"):
        entry = dict(row)
        if entry.get("config_json"):
            entry["config"] = __import__("json").loads(entry["config_json"])
            del entry["config_json"]
        _runs.append(entry)


def _save_run_to_db(run: dict) -> None:
    import json
    execute(
        STUDIO_DB,
        "INSERT OR REPLACE INTO training_runs (id, model_name, display_name, training_type, status, config_json, completed_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (run.get("job_id"), run.get("model_name"), run.get("display_name"),
         run.get("training_type"), run.get("status"),
         json.dumps(run.get("config", {})),
         run.get("completed_at"), run.get("started_at", run.get("completed_at", time.time()))),
    )


def _delete_run_from_db(run_id: str) -> None:
    execute(STUDIO_DB, "DELETE FROM training_runs WHERE id = ?", (run_id,))


_load_runs_from_db()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class TrainingStartRequest(BaseModel):
    model_name: str = ""
    training_type: str = "lora"
    hf_dataset: Optional[str] = None
    local_dataset_path: Optional[str] = None
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    learning_rate: float = 2e-5
    num_epochs: int = 3
    batch_size: int = 1
    max_seq_length: int = 2048
    warmup_steps: int = 100
    save_steps: int = 500
    logging_steps: int = 10
    gradient_accumulation_steps: int = 4
    bf16: bool = True
    output_dir: Optional[str] = None
    start_request_id: Optional[str] = None


class TrainingStopRequest(BaseModel):
    save: bool = True
    expected_job_id: Optional[str] = None


class TrainingResetRequest(BaseModel):
    expected_job_id: Optional[str] = None


class RunRenameRequest(BaseModel):
    display_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Training lifecycle
# ---------------------------------------------------------------------------
@router.post("/start")
async def train_start(req: TrainingStartRequest):
    global _job, _metric_history, _cancel_requested
    _cancel_requested = False
    _metric_history.clear()

    job_id = uuid.uuid4().hex[:12]
    _job = {
        "job_id": job_id,
        "model_name": req.model_name,
        "training_type": req.training_type,
        "phase": "initializing",
        "is_training_running": True,
        "step": 0,
        "total_steps": req.num_epochs * 1000,
        "loss": 0.0,
        "learning_rate": req.learning_rate,
        "config": {
            "lora_rank": req.lora_rank,
            "lora_alpha": req.lora_alpha,
            "learning_rate": req.learning_rate,
            "num_epochs": req.num_epochs,
            "batch_size": req.batch_size,
            "max_seq_length": req.max_seq_length,
        },
        "started_at": time.time(),
    }

    # Register start request if provided
    if req.start_request_id:
        _start_requests[req.start_request_id] = {
            "status": "completed",
            "job_id": job_id,
        }

    return {"job_id": job_id, "status": "started", "message": "Training job created", "error": None, "error_code": None}


@router.get("/start-requests/{start_request_id}")
async def train_start_request_status(start_request_id: str):
    req = _start_requests.get(start_request_id)
    if not req:
        raise HTTPException(404, "Start request not found")
    return req


@router.post("/start-requests/{start_request_id}/acknowledge")
async def train_start_request_acknowledge(start_request_id: str):
    if start_request_id in _start_requests:
        _start_requests[start_request_id]["acknowledged"] = True
    return None


@router.post("/start-requests/{start_request_id}/cancel")
async def train_start_request_cancel(start_request_id: str):
    if start_request_id in _start_requests:
        _start_requests[start_request_id]["status"] = "cancelled"
        return _start_requests[start_request_id]
    raise HTTPException(404, "Start request not found")


@router.post("/stop")
async def train_stop(req: TrainingStopRequest):
    global _job
    if not _job:
        return {"status": "idle", "message": "No training job running"}
    if req.expected_job_id and _job["job_id"] != req.expected_job_id:
        raise HTTPException(409, "Job ID mismatch")
    _job["is_training_running"] = False
    _job["phase"] = "stopped"
    # Save to runs history
    run_record = {
        **_job,
        "display_name": _job["model_name"],
        "completed_at": time.time(),
        "status": "stopped",
    }
    _runs.append(run_record)
    _save_run_to_db(run_record)
    job = _job
    _job = None
    return {"status": "stopped", "message": f"Training stopped at step {job['step']}"}


@router.post("/reset")
async def train_reset(req: TrainingResetRequest):
    global _job, _metric_history
    if req.expected_job_id and _job and _job["job_id"] != req.expected_job_id:
        raise HTTPException(409, "Job ID mismatch")
    _job = None
    _metric_history.clear()
    return {"status": "reset"}


@router.get("/status")
async def train_status():
    if not _job:
        return {"job_id": None, "phase": None, "is_training_running": False, "details": None, "metric_history": []}
    return {
        "job_id": _job["job_id"],
        "phase": _job["phase"],
        "is_training_running": _job["is_training_running"],
        "details": {
            "model": _job["model_name"],
            "step": _job["step"],
            "total_steps": _job["total_steps"],
            "loss": _job["loss"],
        },
        "metric_history": _metric_history[-50:],
    }


@router.get("/metrics")
async def train_metrics(expected_job_id: str = ""):
    if not _job:
        return {"job_id": None, "loss_history": [], "lr_history": [], "step_history": []}
    if expected_job_id and _job["job_id"] != expected_job_id:
        raise HTTPException(409, "Job ID mismatch")
    return {
        "job_id": _job["job_id"],
        "loss_history": [m.get("loss", 0) for m in _metric_history],
        "lr_history": [m.get("learning_rate", 0) for m in _metric_history],
        "step_history": [m.get("step", 0) for m in _metric_history],
    }


async def _progress_stream():
    """SSE stream of training progress events."""
    step = 0
    total = _job["total_steps"] if _job else 100
    while _job and _job["is_training_running"] and step < total:
        step += 1
        _job["step"] = step
        _job["loss"] = max(0.01, 2.0 - (step / total) * 1.8)
        _job["learning_rate"] = 2e-5 * max(0, 1 - step / total)
        _job["phase"] = "training"
        event = {
            "job_id": _job["job_id"],
            "step": step,
            "total_steps": total,
            "loss": round(_job["loss"], 4),
            "learning_rate": _job["learning_rate"],
        }
        _metric_history.append(event)
        yield f"data: {__import__('json').dumps(event)}\n\n"
        await asyncio.sleep(0.2)
    # Final event
    if _job:
        _job["is_training_running"] = False
        _job["phase"] = "completed"
        run_record = {**_job, "display_name": _job["model_name"], "completed_at": time.time(), "status": "completed"}
        _runs.append(run_record)
        _save_run_to_db(run_record)
    yield f"data: {__import__('json').dumps({'done': True})}\n\n"


@router.get("/progress")
async def train_progress(expected_job_id: str = ""):
    if not _job or not _job["is_training_running"]:
        async def empty():
            yield "data: {\"done\": true}\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream")
    if expected_job_id and _job["job_id"] != expected_job_id:
        raise HTTPException(409, "Job ID mismatch")
    return StreamingResponse(_progress_stream(), media_type="text/event-stream")


@router.get("/hardware")
async def train_hardware():
    """GPU utilization for training — reuses system GPU info."""
    import subprocess, json
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            return {
                "available": True,
                "backend": "cuda",
                "devices": [{"name": parts[0], "vram_used_mb": int(parts[1]), "vram_total_mb": int(parts[2]), "utilization_pct": int(parts[3])}],
                "gpu_utilization_pct": int(parts[3]),
                "vram_used_mb": int(parts[1]),
                "vram_total_mb": int(parts[2]),
            }
    except Exception:
        pass
    return {"available": False, "backend": "none", "devices": [], "gpu_utilization_pct": 0, "vram_used_mb": 0, "vram_total_mb": 0}


# ---------------------------------------------------------------------------
# Training runs history
# ---------------------------------------------------------------------------
@router.get("/runs")
async def train_runs(limit: int = 20, offset: int = 0):
    page = _runs[offset: offset + limit]
    return {"runs": page, "total": len(_runs)}


@router.get("/runs/{run_id}")
async def train_run_detail(run_id: str):
    for r in _runs:
        if r.get("job_id") == run_id:
            return {"run": r, "config": r.get("config", {}), "metrics": _metric_history}
    raise HTTPException(404, "Run not found")


@router.delete("/runs/{run_id}")
async def train_run_delete(run_id: str, delete_artifacts: bool = False):
    global _runs
    before = len(_runs)
    _runs = [r for r in _runs if r.get("job_id") != run_id]
    if len(_runs) == before:
        raise HTTPException(404, "Run not found")
    _delete_run_from_db(run_id)
    return {"status": "deleted", "message": "Run deleted", "artifacts_deleted": delete_artifacts, "artifacts_kept_reason": None}


@router.patch("/runs/{run_id}")
async def train_run_rename(run_id: str, body: RunRenameRequest):
    for r in _runs:
        if r.get("job_id") == run_id:
            r["display_name"] = body.display_name
            return r
    raise HTTPException(404, "Run not found")
