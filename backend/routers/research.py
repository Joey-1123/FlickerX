"""Deep Research — real LLM-backed research runs with SSE events."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any, Optional

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import STUDIO_DB
from database import execute, query

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["research"])

# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------
_RESEARCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    user_message_id TEXT,
    assistant_message_id TEXT,
    query TEXT,
    status TEXT DEFAULT 'planning',
    plan TEXT,
    plan_revision INTEGER DEFAULT 0,
    plan_hash TEXT,
    steps TEXT DEFAULT '[]',
    sources TEXT DEFAULT '[]',
    document_sources TEXT DEFAULT '[]',
    config TEXT,
    cancel_requested INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    error TEXT,
    report TEXT,
    last_event_seq INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_research_thread ON research_runs(thread_id);
"""


def _init_research_db() -> None:
    conn = sqlite3.connect(str(STUDIO_DB))
    try:
        conn.executescript(_RESEARCH_SCHEMA)
        conn.commit()
    finally:
        conn.close()


_init_research_db()


def _save_run(run: dict) -> None:
    execute(STUDIO_DB,
            """INSERT OR REPLACE INTO research_runs
               (id, thread_id, user_message_id, assistant_message_id, query, status,
                plan, plan_revision, plan_hash, steps, sources, document_sources,
                config, cancel_requested, retry_count, error, report, last_event_seq, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (run["id"], run.get("thread_id"), run.get("user_message_id"),
             run.get("assistant_message_id"), run.get("query"), run.get("status", "planning"),
             json.dumps(run.get("plan")), run.get("plan_revision", 0), run.get("plan_hash"),
             json.dumps(run.get("steps", [])), json.dumps(run.get("sources", [])),
             json.dumps(run.get("document_sources", [])),
             json.dumps(run.get("config")), 1 if run.get("cancel_requested") else 0,
             run.get("retry_count", 0), run.get("error"),
             json.dumps(run.get("report")) if run.get("report") else None,
             run.get("last_event_seq", 0)))


def _load_run(run_id: str) -> Optional[dict]:
    rows = query(STUDIO_DB, "SELECT * FROM research_runs WHERE id = ?", (run_id,))
    if not rows:
        return None
    r = dict(rows[0])
    for field in ("plan", "steps", "sources", "document_sources", "config", "report"):
        if r.get(field):
            try:
                r[field] = json.loads(r[field])
            except (json.JSONDecodeError, TypeError):
                pass
    r["cancel_requested"] = bool(r.get("cancel_requested"))
    return r


def _load_active_runs(thread_id: str = "") -> list[dict]:
    sql = "SELECT * FROM research_runs WHERE status IN ('planning', 'awaiting_approval', 'queued', 'running')"
    params: list[str] = []
    if thread_id:
        sql += " AND thread_id = ?"
        params.append(thread_id)
    rows = query(STUDIO_DB, sql, tuple(params))
    runs = []
    for row in rows:
        run = dict(row)
        for field in ("plan", "steps", "sources", "document_sources", "config", "report"):
            if run.get(field):
                try:
                    run[field] = json.loads(run[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        run["cancel_requested"] = bool(run.get("cancel_requested"))
        runs.append(run)
    return runs


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ResearchRunCreate(BaseModel):
    thread_id: Optional[str] = None
    user_message_id: Optional[str] = None
    assistant_message_id: Optional[str] = None
    query: str = ""
    plan: Optional[list[dict]] = None
    inference_request: Optional[dict] = None
    rag_scope: Optional[dict] = None
    budgets: Optional[dict] = None
    website_policy: Optional[dict] = None
    instructions: Optional[str] = None


class ResearchPlanUpdate(BaseModel):
    plan: list[dict]
    expected_revision: int = 0


class ResearchApprove(BaseModel):
    plan_revision: int = 0
    plan_hash: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/research-runs")
async def create_research_run(req: ResearchRunCreate):
    run_id = uuid.uuid4().hex[:12]
    now = time.time()
    run = {
        "id": run_id,
        "thread_id": req.thread_id,
        "user_message_id": req.user_message_id,
        "assistant_message_id": req.assistant_message_id,
        "query": req.query,
        "status": "planning",
        "plan": None,
        "plan_revision": 0,
        "plan_hash": None,
        "steps": [],
        "sources": [],
        "document_sources": [],
        "config": {
            "inference_request": req.inference_request,
            "rag_scope": req.rag_scope,
            "budgets": req.budgets,
            "website_policy": req.website_policy,
            "instructions": req.instructions,
        },
        "cancel_requested": False,
        "retry_count": 0,
        "error": None,
        "report": None,
        "last_event_seq": 0,
        "createdAt": now,
        "updatedAt": now,
    }
    _save_run(run)

    # Auto-generate plan from query
    query_text = req.query
    # Generate a simple research plan based on the query
    plan = {
        "title": f"Research: {query_text[:80]}",
        "steps": [
            {"title": f"Search for information about: {query_text[:60]}", "query": query_text},
            {"title": "Synthesize findings", "query": f"Summarize and analyze: {query_text}"},
        ],
    }
    run["plan"] = plan
    run["status"] = "awaiting_approval"
    run["plan_revision"] = 1
    run["plan_hash"] = uuid.uuid4().hex[:16]
    _save_run(run)

    return run


@router.get("/research-runs/{run_id}")
async def get_research_run(run_id: str):
    run = _load_run(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    return run


@router.get("/research-runs/active")
async def get_research_thread_state(threadId: str = ""):
    runs = _load_active_runs(threadId)
    return {"runs": runs, "hasRun": len(runs) > 0}


@router.post("/research-runs/{run_id}/approve")
async def approve_research_run(run_id: str, body: ResearchApprove = ResearchApprove()):
    run = _load_run(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["status"] = "running"
    run["plan_revision"] = body.plan_revision or run.get("plan_revision", 0)
    _save_run(run)

    # Execute the research in background
    threading.Thread(target=_execute_research, args=(run_id,), daemon=True).start()
    return run


@router.post("/research-runs/{run_id}/cancel")
async def cancel_research_run(run_id: str):
    run = _load_run(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["status"] = "cancelling"
    run["cancel_requested"] = True
    _save_run(run)
    return run


@router.post("/research-runs/{run_id}/retry")
async def retry_research_run(run_id: str):
    run = _load_run(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["status"] = "running"
    run["retry_count"] = run.get("retry_count", 0) + 1
    run["cancel_requested"] = False
    _save_run(run)
    threading.Thread(target=_execute_research, args=(run_id,), daemon=True).start()
    return run


@router.put("/research-runs/{run_id}/plan")
async def update_research_plan(run_id: str, body: ResearchPlanUpdate):
    run = _load_run(run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    run["plan"] = body.plan
    run["plan_revision"] = body.expected_revision + 1
    run["plan_hash"] = uuid.uuid4().hex[:16]
    _save_run(run)
    return run


# ---------------------------------------------------------------------------
# Research execution — real LLM calls
# ---------------------------------------------------------------------------
def _execute_research(run_id: str) -> None:
    """Run research steps using the loaded LLM."""
    run = _load_run(run_id)
    if not run or run.get("cancel_requested"):
        return

    plan = run.get("plan") or {}
    steps = run.get("steps") or []
    query_text = run.get("query", "")

    try:
        for i, step in enumerate(plan.get("steps", [])):
            current = _load_run(run_id)
            if current and current.get("cancel_requested"):
                current["status"] = "cancelled"
                _save_run(current)
                return

            step_result = {
                "title": step.get("title", ""),
                "query": step.get("query", ""),
                "position": i + 1,
                "status": "running",
            }
            steps.append(step_result)
            run["steps"] = steps
            run["status"] = "running"
            _save_run(run)

            try:
                from routers import inference as _inf
                llm = _inf._llm
                if llm is not None:
                    result = llm.create_chat_completion(
                        messages=[{"role": "user", "content": step.get("query", query_text)}],
                        max_tokens=1024,
                        temperature=0.3,
                    )
                    response_text = result["choices"][0]["message"]["content"]
                else:
                    response_text = f"Research result for '{step.get('query', query_text)}': [LLM not loaded — load a model to enable real research]"
                step_result["status"] = "completed"
                step_result["result"] = {"excerpt": response_text}
            except Exception as e:
                step_result["status"] = "failed"
                step_result["result"] = {"error": str(e)[:200]}

            run["steps"] = steps
            _save_run(run)

        report_parts = []
        for s in steps:
            if s.get("result", {}).get("excerpt"):
                report_parts.append(f"## {s['title']}\n\n{s['result']['excerpt']}")
        report = "\n\n".join(report_parts) if report_parts else f"No results found for: {query_text}"

        run["status"] = "completed"
        run["report"] = report
        _save_run(run)

    except Exception as e:
        run["status"] = "failed"
        run["error"] = str(e)[:500]
        _save_run(run)
        logger.error("research_failed", run_id=run_id, error=str(e))


# ---------------------------------------------------------------------------
# SSE events
# ---------------------------------------------------------------------------
async def _research_events_stream(run_id: str, after: int = 0):
    seq = after
    while True:
        run = _load_run(run_id)
        if not run:
            yield f"data: {json.dumps({'type': 'run.failed', 'error': 'Run not found'})}\n\n"
            return

        status = run.get("status", "planning")

        # Send status update
        event = {"type": f"run.{status}", "run": run, "lastEventSeq": seq}
        yield f"data: {json.dumps(event)}\n\n"
        seq += 1

        if status in ("completed", "failed", "cancelled"):
            return

        import asyncio
        await asyncio.sleep(1)


@router.post("/research-runs/{run_id}/events")
async def stream_research_events(run_id: str, after: int = 0):
    return StreamingResponse(_research_events_stream(run_id, after), media_type="text/event-stream")
