"""Chat router — completions (SSE), threads, messages, folders, projects, attachments."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth import get_current_user
from database import execute, query, STUDIO_DB
from routers.inference import _inference_state, _inference_lock, ChatCompletionRequest

router = APIRouter()


# ===== Chat Completions (OpenAI-compatible SSE) =====

@router.post("/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint with SSE streaming."""

    if req.stream:
        return StreamingResponse(
            _stream_chat(req),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming fallback (when model not loaded)
    generation_id = str(uuid.uuid4())
    from routers.inference import _llm
    if _llm is None:
        return {
            "id": f"chatcmpl-{generation_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": f"Model '{req.model}' is not loaded. Load a model to start chatting."},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    messages = [{"role": m.role, "content": m.content or ""} for m in req.messages]
    try:
        resp = _llm.create_chat_completion(
            messages=messages,
            temperature=req.temperature,
            top_p=req.top_p,
            max_tokens=req.max_tokens,
            stop=req.stop,
        )
        return {
            "id": f"chatcmpl-{generation_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": resp["choices"][0]["message"],
                "finish_reason": "stop",
            }],
            "usage": resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
        }
    except Exception as e:
        return {
            "id": f"chatcmpl-{generation_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": f"[Error] {e}"},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }


async def _stream_chat(req: ChatCompletionRequest):
    """Generate SSE stream for chat completions."""
    generation_id = str(uuid.uuid4())
    model_name = req.model

    from routers.inference import _llm

    if _llm is None:
        error_chunk = {
            "error": {"message": f"Model '{model_name}' is not loaded. Load a model first.", "type": "invalid_request_error"}
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        return

    messages = [{"role": m.role, "content": m.content or ""} for m in req.messages]
    prompt_tokens = 0
    completion_tokens = 0

    try:
        stream = _llm.create_chat_completion(
            messages=messages,
            temperature=req.temperature,
            top_p=req.top_p,
            max_tokens=req.max_tokens,
            top_k=req.top_k,
            stop=req.stop,
            stream=True,
        )
        prompt_tokens = len(messages) * 4  # rough estimate

        for chunk in stream:
            delta = chunk["choices"][0].get("delta", {})
            if delta.get("content"):
                completion_tokens += 1
                sse_chunk = {
                    "id": f"chatcmpl-{generation_id}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": delta["content"]},
                        "finish_reason": None,
                    }],
                }
                yield f"data: {json.dumps(sse_chunk)}\n\n"

    except Exception as e:
        error_chunk = {"error": {"message": str(e), "type": "inference_error"}}
        yield f"data: {json.dumps(error_chunk)}\n\n"

    # Final chunk
    final_chunk = {
        "id": f"chatcmpl-{generation_id}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model_name,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens},
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


# ===== Chat History — Threads =====

@router.get("/threads")
def list_threads(
    model_type: str = "",
    pair_id: str = "",
    project_id: str = "",
    include_archived: bool = False,
):
    sql = "SELECT * FROM chat_threads WHERE 1=1"
    params: list[Any] = []
    if model_type:
        sql += " AND model_type = ?"
        params.append(model_type)
    if pair_id:
        sql += " AND pair_id = ?"
        params.append(pair_id)
    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)
    if not include_archived:
        sql += " AND archived = 0"
    sql += " ORDER BY updated_at DESC"
    rows = query(STUDIO_DB, sql, tuple(params))
    return {"threads": [_row_to_dict(r) for r in rows]}


@router.get("/threads/{thread_id}")
def get_thread(thread_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM chat_threads WHERE id = ?", (thread_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Thread not found")
    return _row_to_dict(rows[0])


class ThreadWrite(BaseModel):
    id: str | None = None
    title: str | None = None
    model: str | None = None
    model_type: str | None = None
    pair_id: str | None = None
    project_id: str | None = None
    folder_id: str | None = None
    pinned: bool = False
    bookmarked: bool = False
    archived: bool = False


@router.post("/threads")
def save_thread(req: ThreadWrite):
    thread_id = req.id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    execute(STUDIO_DB,
        "INSERT OR REPLACE INTO chat_threads (id, title, model, model_type, pair_id, project_id, folder_id, pinned, bookmarked, archived, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM chat_threads WHERE id = ?), ?), ?)",
        (thread_id, req.title, req.model, req.model_type, req.pair_id, req.project_id, req.folder_id,
         1 if req.pinned else 0, 1 if req.bookmarked else 0, 1 if req.archived else 0, thread_id, now, now))
    rows = query(STUDIO_DB, "SELECT * FROM chat_threads WHERE id = ?", (thread_id,))
    return _row_to_dict(rows[0])


class ThreadPatch(BaseModel):
    title: str | None = None
    model: str | None = None
    model_type: str | None = None
    pair_id: str | None = None
    project_id: str | None = None
    folder_id: str | None = None
    pinned: bool | None = None
    bookmarked: bool | None = None
    archived: bool | None = None


@router.patch("/threads/{thread_id}")
def update_thread(thread_id: str, req: ThreadPatch):
    rows = query(STUDIO_DB, "SELECT * FROM chat_threads WHERE id = ?", (thread_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Thread not found")
    updates = []
    params: list[Any] = []
    for field in ("title", "model", "model_type", "pair_id", "project_id", "folder_id"):
        val = getattr(req, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    for field in ("pinned", "bookmarked", "archived"):
        val = getattr(req, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(1 if val else 0)
    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(thread_id)
        execute(STUDIO_DB, f"UPDATE chat_threads SET {', '.join(updates)} WHERE id = ?", tuple(params))
    rows = query(STUDIO_DB, "SELECT * FROM chat_threads WHERE id = ?", (thread_id,))
    return _row_to_dict(rows[0])


class DeleteThreadsRequest(BaseModel):
    ids: list[str]
    delete_files: bool = False


@router.delete("/threads")
def delete_threads(req: DeleteThreadsRequest):
    for tid in req.ids:
        execute(STUDIO_DB, "DELETE FROM chat_threads WHERE id = ?", (tid,))
    return {"deletedThreadIds": req.ids, "sandboxes_kept": []}


@router.post("/threads/{thread_id}/fork")
def fork_thread(thread_id: str, body: dict):
    return {"thread": {}, "messages": [], "containerSnapshotWarning": None}


@router.get("/threads/{thread_id}/messages/{message_id}/forks")
def fork_count(thread_id: str, message_id: str):
    return {"count": 0}


# ===== Chat History — Messages =====

@router.get("/threads/{thread_id}/messages")
def list_messages(thread_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM chat_messages WHERE thread_id = ? ORDER BY created_at", (thread_id,))
    return {"messages": [_row_to_dict(r) for r in rows]}


@router.get("/threads/{thread_id}/messages/{message_id}")
def get_message(thread_id: str, message_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM chat_messages WHERE id = ? AND thread_id = ?", (message_id, thread_id))
    if not rows:
        raise HTTPException(status_code=404, detail="Message not found")
    return _row_to_dict(rows[0])


class MessageWrite(BaseModel):
    id: str | None = None
    role: str
    content: str | None = None
    model: str | None = None
    tool_calls: str | None = None
    tool_call_id: str | None = None
    name: str | None = None
    reasoning: str | None = None
    extra_content: str | None = None


@router.put("/threads/{thread_id}/messages/{message_id}")
def save_message(thread_id: str, message_id: str, req: MessageWrite):
    now = datetime.now(timezone.utc).isoformat()
    execute(STUDIO_DB,
        "INSERT OR REPLACE INTO chat_messages (id, thread_id, role, content, model, tool_calls, tool_call_id, name, reasoning, extra_content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (message_id, thread_id, req.role, req.content, req.model, req.tool_calls, req.tool_call_id, req.name, req.reasoning, req.extra_content, now))
    execute(STUDIO_DB, "UPDATE chat_threads SET updated_at = ? WHERE id = ?", (now, thread_id))
    rows = query(STUDIO_DB, "SELECT * FROM chat_messages WHERE id = ?", (message_id,))
    return _row_to_dict(rows[0])


class SyncMessagesRequest(BaseModel):
    messages: list[MessageWrite]
    pruneMissing: bool = False


@router.put("/threads/{thread_id}/messages")
def sync_messages(thread_id: str, req: SyncMessagesRequest):
    now = datetime.now(timezone.utc).isoformat()
    for msg in req.messages:
        msg_id = msg.id or str(uuid.uuid4())
        execute(STUDIO_DB,
            "INSERT OR REPLACE INTO chat_messages (id, thread_id, role, content, model, tool_calls, tool_call_id, name, reasoning, extra_content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (msg_id, thread_id, msg.role, msg.content, msg.model, msg.tool_calls, msg.tool_call_id, msg.name, msg.reasoning, msg.extra_content, now))
    rows = query(STUDIO_DB, "SELECT * FROM chat_messages WHERE thread_id = ? ORDER BY created_at", (thread_id,))
    return {"messages": [_row_to_dict(r) for r in rows]}


class BatchMessagesRequest(BaseModel):
    threadIds: list[str]


@router.post("/messages:batch")
def batch_list_messages(req: BatchMessagesRequest):
    result = {}
    for tid in req.threadIds:
        rows = query(STUDIO_DB, "SELECT * FROM chat_messages WHERE thread_id = ? ORDER BY created_at", (tid,))
        result[tid] = [_row_to_dict(r) for r in rows]
    return {"messagesByThreadId": result}


# ===== Folders =====

@router.get("/folders")
def list_folders():
    rows = query(STUDIO_DB, "SELECT * FROM chat_folders ORDER BY name")
    return {"folders": [_row_to_dict(r) for r in rows]}


class FolderWrite(BaseModel):
    id: str | None = None
    name: str
    parent_id: str | None = None


@router.post("/folders")
def save_folder(req: FolderWrite):
    folder_id = req.id or str(uuid.uuid4())
    execute(STUDIO_DB, "INSERT OR REPLACE INTO chat_folders (id, name, parent_id) VALUES (?, ?, ?)",
            (folder_id, req.name, req.parent_id))
    rows = query(STUDIO_DB, "SELECT * FROM chat_folders WHERE id = ?", (folder_id,))
    return _row_to_dict(rows[0])


@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: str):
    execute(STUDIO_DB, "DELETE FROM chat_folders WHERE id = ?", (folder_id,))
    return {"ok": True}


# ===== Projects =====

@router.get("/projects")
def list_projects(include_archived: bool = False):
    sql = "SELECT * FROM chat_projects"
    if not include_archived:
        sql += " WHERE archived = 0"
    sql += " ORDER BY updated_at DESC"
    rows = query(STUDIO_DB, sql)
    return {"projects": [_row_to_dict(r) for r in rows]}


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM chat_projects WHERE id = ?", (project_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    return _row_to_dict(rows[0])


class ProjectWrite(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    archived: bool = False


@router.post("/projects")
def save_project(req: ProjectWrite):
    project_id = req.id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    execute(STUDIO_DB,
        "INSERT OR REPLACE INTO chat_projects (id, name, description, archived, created_at, updated_at) VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM chat_projects WHERE id = ?), ?), ?)",
        (project_id, req.name, req.description, 1 if req.archived else 0, project_id, now, now))
    rows = query(STUDIO_DB, "SELECT * FROM chat_projects WHERE id = ?", (project_id,))
    return _row_to_dict(rows[0])


@router.patch("/projects/{project_id}")
def update_project(project_id: str, body: dict):
    rows = query(STUDIO_DB, "SELECT * FROM chat_projects WHERE id = ?", (project_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    updates = []
    params: list[Any] = []
    for field in ("name", "description"):
        if field in body:
            updates.append(f"{field} = ?")
            params.append(body[field])
    if "archived" in body:
        updates.append("archived = ?")
        params.append(1 if body["archived"] else 0)
    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(project_id)
        execute(STUDIO_DB, f"UPDATE chat_projects SET {', '.join(updates)} WHERE id = ?", tuple(params))
    rows = query(STUDIO_DB, "SELECT * FROM chat_projects WHERE id = ?", (project_id,))
    return _row_to_dict(rows[0])


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, delete_files: bool = False):
    rows = query(STUDIO_DB, "SELECT * FROM chat_projects WHERE id = ?", (project_id,))
    execute(STUDIO_DB, "DELETE FROM chat_projects WHERE id = ?", (project_id,))
    if rows:
        return {**_row_to_dict(rows[0]), "sandboxes_kept": []}
    return {"ok": True}


# ===== Attachments =====

@router.get("/attachments")
def list_attachments(offset: int = 0, limit: int = 50):
    rows = query(STUDIO_DB, "SELECT * FROM chat_attachments ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
    return {"attachments": [_row_to_dict(r) for r in rows], "nextOffset": offset + limit}


@router.get("/attachments/{message_id}/{attachment_id}/file")
def fetch_attachment_blob(message_id: str, attachment_id: str):
    rows = query(STUDIO_DB, "SELECT data, filename, mime_type FROM chat_attachments WHERE id = ? AND message_id = ?",
                 (attachment_id, message_id))
    if not rows:
        raise HTTPException(status_code=404, detail="Attachment not found")
    from fastapi.responses import Response
    return Response(content=rows[0]["data"], media_type=rows[0]["mime_type"] or "application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{rows[0]["filename"]}"'})


@router.delete("/attachments/{message_id}/{attachment_id}")
def delete_attachment(message_id: str, attachment_id: str):
    execute(STUDIO_DB, "DELETE FROM chat_attachments WHERE id = ? AND message_id = ?", (attachment_id, message_id))
    return {"ok": True}


# ===== Chat count / clear / export / import =====

@router.get("/count")
def count_chats():
    rows = query(STUDIO_DB, "SELECT COUNT(*) as count FROM chat_threads")
    return {"count": rows[0]["count"] if rows else 0}


class ClearChatsRequest(BaseModel):
    ids: list[str] | None = None
    operationId: str | None = None


@router.delete("")
def clear_chats(req: ClearChatsRequest | None = None, delete_files: bool = False):
    if req and req.ids:
        for tid in req.ids:
            execute(STUDIO_DB, "DELETE FROM chat_threads WHERE id = ?", (tid,))
        return {"deletedThreadIds": req.ids, "sandboxes_kept": []}
    execute(STUDIO_DB, "DELETE FROM chat_threads")
    execute(STUDIO_DB, "DELETE FROM chat_messages")
    return {"deletedThreadIds": [], "sandboxes_kept": []}


@router.get("/export")
def export_chat():
    threads = [_row_to_dict(r) for r in query(STUDIO_DB, "SELECT * FROM chat_threads ORDER BY created_at")]
    messages = [_row_to_dict(r) for r in query(STUDIO_DB, "SELECT * FROM chat_messages ORDER BY created_at")]
    projects = [_row_to_dict(r) for r in query(STUDIO_DB, "SELECT * FROM chat_projects ORDER BY created_at")]
    return {
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "threadCount": len(threads),
        "projects": projects,
        "threads": threads,
        "messages": messages,
    }


@router.get("/import-ledger")
def import_ledger():
    rows = query(STUDIO_DB, "SELECT thread_id FROM chat_import_ledger ORDER BY created_at")
    return {"threadIds": [r["thread_id"] for r in rows]}


class ImportLedgerRequest(BaseModel):
    threadIds: list[str]


@router.post("/import-ledger")
def record_import_ledger(req: ImportLedgerRequest):
    before = query(STUDIO_DB, "SELECT COUNT(*) as c FROM chat_import_ledger")[0]["c"]
    for tid in req.threadIds:
        execute(STUDIO_DB, "INSERT OR IGNORE INTO chat_import_ledger (thread_id) VALUES (?)", (tid,))
    after = query(STUDIO_DB, "SELECT COUNT(*) as c FROM chat_import_ledger")[0]["c"]
    return {"accepted": len(req.threadIds), "inserted": after - before}


# ===== Chat Settings =====

@router.get("/settings")
def get_chat_settings():
    rows = query(STUDIO_DB, "SELECT value FROM settings WHERE key = 'chat_settings'")
    if rows:
        return {"settings": json.loads(rows[0]["value"])}
    return {"settings": {}}


@router.put("/settings")
def save_chat_settings(body: dict):
    settings = body.get("settings", body)
    execute(STUDIO_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('chat_settings', ?, datetime('now'))",
            (json.dumps(settings),))
    return {"settings": settings}

# ===== Helpers =====

def _row_to_dict(row) -> dict:
    d = dict(row)
    # Convert pinned/bookmarked/archived from int to bool
    for field in ("pinned", "bookmarked", "archived"):
        if field in d:
            d[field] = bool(d[field])
    return d

