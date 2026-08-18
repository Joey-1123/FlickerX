"""RAG / Knowledge Base endpoints — /api/rag/*"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

router = APIRouter(prefix="/api/rag", tags=["rag"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_kbs: list[dict] = []
_documents: list[dict] = []
_linked_folders: list[dict] = []
_jobs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class KBCreate(BaseModel):
    name: str
    description: Optional[str] = None


class KBUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LinkedFolderCreate(BaseModel):
    path: str
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Knowledge Bases
# ---------------------------------------------------------------------------
@router.get("/knowledge-bases")
async def list_kbs():
    return {"knowledge_bases": _kbs}


@router.post("/knowledge-bases")
async def create_kb(req: KBCreate):
    kb = {
        "id": uuid.uuid4().hex[:12],
        "name": req.name,
        "description": req.description,
        "document_count": 0,
        "created_at": time.time(),
    }
    _kbs.append(kb)
    return kb


@router.patch("/knowledge-bases/{kb_id}")
async def update_kb(kb_id: str, body: KBUpdate):
    for kb in _kbs:
        if kb["id"] == kb_id:
            if body.name is not None:
                kb["name"] = body.name
            if body.description is not None:
                kb["description"] = body.description
            return kb
    raise HTTPException(404, "Knowledge base not found")


@router.delete("/knowledge-bases/{kb_id}")
async def delete_kb(kb_id: str):
    global _kbs
    before = len(_kbs)
    _kbs = [kb for kb in _kbs if kb["id"] != kb_id]
    if len(_kbs) == before:
        raise HTTPException(404, "Knowledge base not found")
    return None


@router.get("/knowledge-bases/{kb_id}/documents")
async def list_kb_documents(kb_id: str):
    docs = [d for d in _documents if d.get("kb_id") == kb_id]
    return {"documents": docs}


@router.post("/knowledge-bases/{kb_id}/documents")
async def upload_kb_document(kb_id: str, file: UploadFile = File(...)):
    doc = {
        "id": uuid.uuid4().hex[:12],
        "kb_id": kb_id,
        "filename": file.filename,
        "status": "indexed",
        "chunk_count": 0,
        "created_at": time.time(),
    }
    _documents.append(doc)
    return doc


# ---------------------------------------------------------------------------
# Thread / Project Documents
# ---------------------------------------------------------------------------
@router.get("/threads/{thread_id}/documents")
async def list_thread_documents(thread_id: str):
    docs = [d for d in _documents if d.get("thread_id") == thread_id]
    return {"documents": docs}


@router.post("/threads/{thread_id}/documents")
async def upload_thread_document(thread_id: str, file: UploadFile = File(...)):
    doc = {
        "id": uuid.uuid4().hex[:12],
        "thread_id": thread_id,
        "filename": file.filename,
        "status": "indexed",
        "chunk_count": 0,
        "created_at": time.time(),
    }
    _documents.append(doc)
    return doc


@router.get("/projects/{project_id}/documents")
async def list_project_documents(project_id: str):
    docs = [d for d in _documents if d.get("project_id") == project_id]
    return {"documents": docs}


@router.post("/projects/{project_id}/documents")
async def upload_project_document(project_id: str, file: UploadFile = File(...)):
    doc = {
        "id": uuid.uuid4().hex[:12],
        "project_id": project_id,
        "filename": file.filename,
        "status": "indexed",
        "chunk_count": 0,
        "created_at": time.time(),
    }
    _documents.append(doc)
    return doc


@router.get("/documents")
async def list_all_documents():
    return {"documents": _documents}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    global _documents
    before = len(_documents)
    _documents = [d for d in _documents if d["id"] != document_id]
    if len(_documents) == before:
        raise HTTPException(404, "Document not found")
    return None


@router.get("/documents/{document_id}/preview-target")
async def preview_target(document_id: str, chunk_id: str = ""):
    for d in _documents:
        if d["id"] == document_id:
            return {"document": d, "chunk_id": chunk_id, "content": "(preview placeholder)"}
    raise HTTPException(404, "Document not found")


@router.get("/documents/{document_id}/file-url")
async def document_file_url(document_id: str):
    for d in _documents:
        if d["id"] == document_id:
            return {"url": f"/api/rag/documents/{document_id}/file"}
    raise HTTPException(404, "Document not found")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


async def _job_events_stream(job_id: str):
    import asyncio, json
    job = _jobs.get(job_id, {"status": "completed"})
    yield f"data: {json.dumps({'type': 'status', 'status': job['status']})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(_job_events_stream(job_id), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Linked Folders
# ---------------------------------------------------------------------------
@router.get("/linked-folders")
async def list_linked_folders(scope_type: str = "", scope_id: str = ""):
    folders = _linked_folders
    if scope_type:
        folders = [f for f in folders if f.get("scope_type") == scope_type]
    if scope_id:
        folders = [f for f in folders if f.get("scope_id") == scope_id]
    return {"linked_folders": folders}


@router.post("/knowledge-bases/{kb_id}/linked-folders")
async def create_kb_linked_folder(kb_id: str, body: LinkedFolderCreate):
    folder = {
        "id": uuid.uuid4().hex[:12],
        "path": body.path,
        "scope_type": "knowledge_base",
        "scope_id": kb_id,
        "status": "synced",
        "created_at": time.time(),
    }
    _linked_folders.append(folder)
    return folder


@router.post("/projects/{project_id}/linked-folders")
async def create_project_linked_folder(project_id: str, body: LinkedFolderCreate):
    folder = {
        "id": uuid.uuid4().hex[:12],
        "path": body.path,
        "scope_type": "project",
        "scope_id": project_id,
        "status": "synced",
        "created_at": time.time(),
    }
    _linked_folders.append(folder)
    return folder


@router.delete("/linked-folders/{folder_id}")
async def delete_linked_folder(folder_id: str, remove_index: bool = False):
    global _linked_folders
    before = len(_linked_folders)
    _linked_folders = [f for f in _linked_folders if f["id"] != folder_id]
    if len(_linked_folders) == before:
        raise HTTPException(404, "Linked folder not found")
    return None


@router.post("/linked-folders/{folder_id}/sync")
async def sync_linked_folder(folder_id: str):
    for f in _linked_folders:
        if f["id"] == folder_id:
            f["status"] = "syncing"
            return {"status": "syncing"}
    raise HTTPException(404, "Linked folder not found")


@router.post("/linked-folders/{folder_id}/rebuild")
async def rebuild_linked_folder(folder_id: str):
    for f in _linked_folders:
        if f["id"] == folder_id:
            return {"status": "rebuilding"}
    raise HTTPException(404, "Linked folder not found")


@router.get("/linked-folder-jobs/{job_id}")
async def get_folder_sync_job(job_id: str):
    return {"job_id": job_id, "status": "completed"}


async def _folder_job_events_stream(job_id: str):
    import json
    yield f"data: {json.dumps({'type': 'status', 'status': 'completed'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/linked-folder-jobs/{job_id}/events")
async def stream_folder_sync_job_events(job_id: str):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(_folder_job_events_stream(job_id), media_type="text/event-stream")
