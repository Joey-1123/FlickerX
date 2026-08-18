"""Deep Research endpoints — /api/chat/research-runs/*"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["research"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_runs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ResearchRunCreate(BaseModel):
    thread_id: Optional[str] = None
    query: str = ""
    plan: Optional[list[dict]] = None


class ResearchPlanUpdate(BaseModel):
    plan: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/research-runs")
async def create_research_run(req: ResearchRunCreate):
    run_id = uuid.uuid4().hex[:12]
    run = {
        "id": run_id,
        "thread_id": req.thread_id,
        "query": req.query,
        "status": "pending",
        "plan": req.plan or [],
        "results": [],
        "created_at": time.time(),
    }
    _runs[run_id] = run
    return run


@router.get("/research-runs/{run_id}")
async def get_research_run(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    return run


@router.get("/research-runs/active")
async def get_research_thread_state(threadId: str = ""):
    active = [r for r in _runs.values() if r["status"] in ("pending", "running") and (not threadId or r.get("thread_id") == threadId)]
    return {"runs": active}


@router.post("/research-runs/{run_id}/approve")
async def approve_research_run(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["status"] = "running"
    return run


@router.post("/research-runs/{run_id}/cancel")
async def cancel_research_run(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["status"] = "cancelled"
    return run


@router.post("/research-runs/{run_id}/retry")
async def retry_research_run(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["status"] = "pending"
    return run


@router.put("/research-runs/{run_id}/plan")
async def update_research_plan(run_id: str, body: ResearchPlanUpdate):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["plan"] = body.plan
    return run


async def _research_events_stream(run_id: str, after: int = 0):
    import json
    run = _runs.get(run_id, {"status": "completed"})
    yield f"data: {json.dumps({'type': 'status', 'status': run['status']})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/research-runs/{run_id}/events")
async def stream_research_events(run_id: str, after: int = 0):
    return StreamingResponse(_research_events_stream(run_id, after), media_type="text/event-stream")
