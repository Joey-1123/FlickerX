"""RAG / Knowledge Base — real SQLite persistence, text extraction, chunking."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import structlog
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import execute, execute_returning, query, STUDIO_DB

logger = structlog.get_logger()
router = APIRouter(prefix="/api/rag", tags=["rag"])

# ---------------------------------------------------------------------------
# DB setup — rag tables in studio.db
# ---------------------------------------------------------------------------
_RAG_SCHEMA = """
CREATE TABLE IF NOT EXISTS rag_knowledge_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS rag_documents (
    id TEXT PRIMARY KEY,
    kb_id TEXT,
    thread_id TEXT,
    project_id TEXT,
    filename TEXT NOT NULL,
    mime_type TEXT,
    file_hash TEXT,
    status TEXT DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    error TEXT,
    stored_path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (kb_id) REFERENCES rag_knowledge_bases(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS rag_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    page_number INTEGER,
    FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS rag_linked_folders (
    id TEXT PRIMARY KEY,
    kb_id TEXT,
    project_id TEXT,
    path TEXT NOT NULL,
    scope_type TEXT,
    scope_id TEXT,
    status TEXT DEFAULT 'synced',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rag_docs_kb ON rag_documents(kb_id);
CREATE INDEX IF NOT EXISTS idx_rag_docs_thread ON rag_documents(thread_id);
CREATE INDEX IF NOT EXISTS idx_rag_docs_project ON rag_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks(document_id);
"""


def _init_rag_db() -> None:
    conn = sqlite3.connect(str(STUDIO_DB))
    try:
        conn.executescript(_RAG_SCHEMA)
        conn.commit()
    finally:
        conn.close()


# Init on import
_init_rag_db()

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
_MAX_CHUNK_TOKENS = 500  # ponytail: word-based, not real tokenizer
_OVERLAP_WORDS = 50


def _extract_text(path: str) -> str:
    """Extract text from common file formats."""
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix in (".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".yaml", ".yml", ".toml"):
        return p.read_text(errors="replace")

    if suffix == ".pdf":
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", "-layout", str(p), "-"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except Exception:
            pass
        # Fallback: try PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(p))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except Exception:
            pass
        return f"[PDF file: {p.name}]"

    if suffix in (".docx", ".doc"):
        try:
            import subprocess
            result = subprocess.run(
                ["catdoc", str(p)], capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass

    if suffix == ".html":
        try:
            import re
            html = p.read_text(errors="replace")
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception:
            pass

    # Unknown format: return filename as content
    return f"[File: {p.name}]"


def _chunk_text(text: str, max_tokens: int = _MAX_CHUNK_TOKENS,
                overlap: int = _OVERLAP_WORDS) -> list[str]:
    """Split text into word-based chunks."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
        if start >= len(words):
            break
    return chunks


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
    rows = query(STUDIO_DB, "SELECT * FROM rag_knowledge_bases ORDER BY created_at")
    return {"knowledge_bases": [dict(r) for r in rows]}


@router.post("/knowledge-bases")
async def create_kb(req: KBCreate):
    kb_id = uuid.uuid4().hex[:12]
    execute(STUDIO_DB,
            "INSERT INTO rag_knowledge_bases (id, name, description) VALUES (?, ?, ?)",
            (kb_id, req.name, req.description))
    return {"id": kb_id, "name": req.name, "description": req.description, "document_count": 0}


@router.patch("/knowledge-bases/{kb_id}")
async def update_kb(kb_id: str, body: KBUpdate):
    rows = query(STUDIO_DB, "SELECT id FROM rag_knowledge_bases WHERE id = ?", (kb_id,))
    if not rows:
        raise HTTPException(404, "Knowledge base not found")
    updates, params = [], []
    if body.name is not None:
        updates.append("name = ?")
        params.append(body.name)
    if body.description is not None:
        updates.append("description = ?")
        params.append(body.description)
    if updates:
        params.append(kb_id)
        execute(STUDIO_DB, f"UPDATE rag_knowledge_bases SET {', '.join(updates)} WHERE id = ?", tuple(params))
    rows = query(STUDIO_DB, "SELECT * FROM rag_knowledge_bases WHERE id = ?", (kb_id,))
    return dict(rows[0])


@router.delete("/knowledge-bases/{kb_id}")
async def delete_kb(kb_id: str):
    execute(STUDIO_DB, "DELETE FROM rag_chunks WHERE document_id IN (SELECT id FROM rag_documents WHERE kb_id = ?)", (kb_id,))
    execute(STUDIO_DB, "DELETE FROM rag_documents WHERE kb_id = ?", (kb_id,))
    execute(STUDIO_DB, "DELETE FROM rag_knowledge_bases WHERE id = ?", (kb_id,))
    return {"ok": True}


@router.get("/knowledge-bases/{kb_id}/documents")
async def list_kb_documents(kb_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents WHERE kb_id = ? ORDER BY created_at", (kb_id,))
    return {"documents": [dict(r) for r in rows]}


@router.post("/knowledge-bases/{kb_id}/documents")
async def upload_kb_document(kb_id: str, file: UploadFile = File(...)):
    doc_id, job_id = uuid.uuid4().hex[:12], uuid.uuid4().hex[:12]
    upload_dir = Path.home() / ".flickerx" / "studio" / "rag_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = str(upload_dir / f"{doc_id}_{file.filename}")
    with open(stored_path, "wb") as f:
        content = await file.read()
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()

    execute(STUDIO_DB,
            "INSERT INTO rag_documents (id, kb_id, filename, file_hash, status, stored_path) VALUES (?, ?, ?, ?, 'indexed', ?)",
            (doc_id, kb_id, file.filename, file_hash, stored_path))

    # Extract, chunk, store
    try:
        text = _extract_text(stored_path)
        chunks = _chunk_text(text)
        for i, chunk_content in enumerate(chunks):
            chunk_id = uuid.uuid4().hex[:12]
            execute(STUDIO_DB,
                    "INSERT INTO rag_chunks (id, document_id, chunk_index, content, token_count) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, doc_id, i, chunk_content, len(chunk_content.split())))
        execute(STUDIO_DB, "UPDATE rag_documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
        # Update KB count
        count = query(STUDIO_DB, "SELECT COUNT(*) as c FROM rag_documents WHERE kb_id = ?", (kb_id,))
        execute(STUDIO_DB, "UPDATE rag_knowledge_bases SET document_count = ? WHERE id = ?",
                (count[0]["c"] if count else 0, kb_id))
    except Exception as e:
        logger.error("rag_index_failed", doc_id=doc_id, error=str(e))
        execute(STUDIO_DB, "UPDATE rag_documents SET status = 'error', error = ? WHERE id = ?", (str(e)[:500], doc_id))

    return {"documentId": doc_id, "jobId": job_id, "filename": file.filename}


# ---------------------------------------------------------------------------
# Thread / Project Documents
# ---------------------------------------------------------------------------
@router.get("/threads/{thread_id}/documents")
async def list_thread_documents(thread_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents WHERE thread_id = ? ORDER BY created_at", (thread_id,))
    return {"documents": [dict(r) for r in rows]}


@router.post("/threads/{thread_id}/documents")
async def upload_thread_document(thread_id: str, file: UploadFile = File(...)):
    doc_id, job_id = uuid.uuid4().hex[:12], uuid.uuid4().hex[:12]
    upload_dir = Path.home() / ".flickerx" / "studio" / "rag_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = str(upload_dir / f"{doc_id}_{file.filename}")
    with open(stored_path, "wb") as f:
        content = await file.read()
        f.write(content)

    execute(STUDIO_DB,
            "INSERT INTO rag_documents (id, thread_id, filename, status, stored_path) VALUES (?, ?, ?, 'indexed', ?)",
            (doc_id, thread_id, file.filename, stored_path))

    try:
        text = _extract_text(stored_path)
        chunks = _chunk_text(text)
        for i, chunk_content in enumerate(chunks):
            chunk_id = uuid.uuid4().hex[:12]
            execute(STUDIO_DB,
                    "INSERT INTO rag_chunks (id, document_id, chunk_index, content, token_count) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, doc_id, i, chunk_content, len(chunk_content.split())))
        execute(STUDIO_DB, "UPDATE rag_documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
    except Exception as e:
        execute(STUDIO_DB, "UPDATE rag_documents SET status = 'error', error = ? WHERE id = ?", (str(e)[:500], doc_id))

    return {"documentId": doc_id, "jobId": job_id, "filename": file.filename}


@router.get("/projects/{project_id}/documents")
async def list_project_documents(project_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents WHERE project_id = ? ORDER BY created_at", (project_id,))
    return {"documents": [dict(r) for r in rows]}


@router.post("/projects/{project_id}/documents")
async def upload_project_document(project_id: str, file: UploadFile = File(...)):
    doc_id, job_id = uuid.uuid4().hex[:12], uuid.uuid4().hex[:12]
    upload_dir = Path.home() / ".flickerx" / "studio" / "rag_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = str(upload_dir / f"{doc_id}_{file.filename}")
    with open(stored_path, "wb") as f:
        content = await file.read()
        f.write(content)

    execute(STUDIO_DB,
            "INSERT INTO rag_documents (id, project_id, filename, status, stored_path) VALUES (?, ?, ?, 'indexed', ?)",
            (doc_id, project_id, file.filename, stored_path))

    try:
        text = _extract_text(stored_path)
        chunks = _chunk_text(text)
        for i, chunk_content in enumerate(chunks):
            chunk_id = uuid.uuid4().hex[:12]
            execute(STUDIO_DB,
                    "INSERT INTO rag_chunks (id, document_id, chunk_index, content, token_count) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, doc_id, i, chunk_content, len(chunk_content.split())))
        execute(STUDIO_DB, "UPDATE rag_documents SET chunk_count = ? WHERE id = ?", (len(chunks), doc_id))
    except Exception as e:
        execute(STUDIO_DB, "UPDATE rag_documents SET status = 'error', error = ? WHERE id = ?", (str(e)[:500], doc_id))

    return {"documentId": doc_id, "jobId": job_id, "filename": file.filename}


@router.get("/documents")
async def list_all_documents():
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents ORDER BY created_at")
    return {"documents": [dict(r) for r in rows]}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    execute(STUDIO_DB, "DELETE FROM rag_chunks WHERE document_id = ?", (document_id,))
    execute(STUDIO_DB, "DELETE FROM rag_documents WHERE id = ?", (document_id,))
    return {"ok": True}


@router.get("/documents/{document_id}/preview-target")
async def preview_target(document_id: str, chunk_id: str = ""):
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents WHERE id = ?", (document_id,))
    if not rows:
        raise HTTPException(404, "Document not found")
    doc = dict(rows[0])
    chunk_rows = query(STUDIO_DB, "SELECT * FROM rag_chunks WHERE document_id = ? ORDER BY chunk_index LIMIT 5", (document_id,))
    doc["chunks"] = [dict(r) for r in chunk_rows]
    return {"document": doc, "chunk_id": chunk_id, "content": chunk_rows[0]["content"] if chunk_rows else ""}


@router.get("/documents/{document_id}/file-url")
async def document_file_url(document_id: str):
    rows = query(STUDIO_DB, "SELECT stored_path FROM rag_documents WHERE id = ?", (document_id,))
    if not rows:
        raise HTTPException(404, "Document not found")
    return {"url": f"/api/rag/documents/{document_id}/file"}


@router.get("/documents/{document_id}/file")
async def serve_document_file(document_id: str):
    from fastapi.responses import FileResponse
    rows = query(STUDIO_DB, "SELECT stored_path FROM rag_documents WHERE id = ?", (document_id,))
    if not rows or not rows[0]["stored_path"]:
        raise HTTPException(404, "Document file not found")
    path = Path(rows[0]["stored_path"])
    if not path.exists():
        raise HTTPException(404, "Document file missing from disk")
    return FileResponse(str(path))


# ---------------------------------------------------------------------------
# Search — simple keyword matching
# ---------------------------------------------------------------------------
@router.post("/search")
async def search_chunks(body: dict):
    query_text = body.get("query", "")
    kb_id = body.get("kb_id")
    limit = int(body.get("limit", 10))

    if not query_text:
        return {"chunks": []}

    # Simple keyword search — ponytail: FTS5 would be better but this works
    sql = """SELECT rc.*, rd.filename, rd.kb_id
             FROM rag_chunks rc
             JOIN rag_documents rd ON rc.document_id = rd.id
             WHERE rc.content LIKE ?"""
    params: list[Any] = [f"%{query_text}%"]
    if kb_id:
        sql += " AND rd.kb_id = ?"
        params.append(kb_id)
    sql += f" LIMIT {limit}"

    rows = query(STUDIO_DB, sql, tuple(params))
    return {"chunks": [dict(r) for r in rows]}


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents WHERE id = ?", (job_id,))
    if not rows:
        raise HTTPException(404, "Job not found")
    doc = dict(rows[0])
    return {"id": job_id, "documentId": job_id, "status": doc.get("status", "completed"),
            "numChunks": doc.get("chunk_count", 0)}


async def _job_events_stream(job_id: str):
    rows = query(STUDIO_DB, "SELECT * FROM rag_documents WHERE id = ?", (job_id,))
    status = dict(rows[0])["status"] if rows else "completed"
    num_chunks = dict(rows[0])["chunk_count"] if rows else 0
    yield f"data: {json.dumps({'type': 'progress', 'status': status, 'num_chunks': num_chunks})}\n\n"
    yield f"data: {json.dumps({'type': 'complete', 'num_chunks': num_chunks})}\n\n"


@router.get("/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    return StreamingResponse(_job_events_stream(job_id), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Linked Folders
# ---------------------------------------------------------------------------
@router.get("/linked-folders")
async def list_linked_folders(scope_type: str = "", scope_id: str = ""):
    sql = "SELECT * FROM rag_linked_folders WHERE 1=1"
    params: list[str] = []
    if scope_type:
        sql += " AND scope_type = ?"
        params.append(scope_type)
    if scope_id:
        sql += " AND scope_id = ?"
        params.append(scope_id)
    rows = query(STUDIO_DB, sql, tuple(params))
    return {"linked_folders": [dict(r) for r in rows]}


@router.post("/knowledge-bases/{kb_id}/linked-folders")
async def create_kb_linked_folder(kb_id: str, body: LinkedFolderCreate):
    folder_id = uuid.uuid4().hex[:12]
    execute(STUDIO_DB,
            "INSERT INTO rag_linked_folders (id, kb_id, path, scope_type, scope_id, status) VALUES (?, ?, ?, 'knowledge_base', ?, 'synced')",
            (folder_id, kb_id, body.path, kb_id))
    return {"id": folder_id, "path": body.path, "scope_type": "knowledge_base", "scope_id": kb_id, "status": "synced"}


@router.post("/projects/{project_id}/linked-folders")
async def create_project_linked_folder(project_id: str, body: LinkedFolderCreate):
    folder_id = uuid.uuid4().hex[:12]
    execute(STUDIO_DB,
            "INSERT INTO rag_linked_folders (id, project_id, path, scope_type, scope_id, status) VALUES (?, ?, ?, 'project', ?, 'synced')",
            (folder_id, project_id, body.path, project_id))
    return {"id": folder_id, "path": body.path, "scope_type": "project", "scope_id": project_id, "status": "synced"}


@router.delete("/linked-folders/{folder_id}")
async def delete_linked_folder(folder_id: str, remove_index: bool = False):
    execute(STUDIO_DB, "DELETE FROM rag_linked_folders WHERE id = ?", (folder_id,))
    return {"ok": True}


@router.post("/linked-folders/{folder_id}/sync")
async def sync_linked_folder(folder_id: str):
    execute(STUDIO_DB, "UPDATE rag_linked_folders SET status = 'syncing' WHERE id = ?", (folder_id,))
    # In production: scan folder, ingest new/changed files
    execute(STUDIO_DB, "UPDATE rag_linked_folders SET status = 'synced' WHERE id = ?", (folder_id,))
    return {"status": "synced"}


@router.post("/linked-folders/{folder_id}/rebuild")
async def rebuild_linked_folder(folder_id: str):
    execute(STUDIO_DB, "UPDATE rag_linked_folders SET status = 'rebuilding' WHERE id = ?", (folder_id,))
    # In production: re-ingest all files
    execute(STUDIO_DB, "UPDATE rag_linked_folders SET status = 'synced' WHERE id = ?", (folder_id,))
    return {"status": "synced"}


@router.get("/linked-folder-jobs/{job_id}")
async def get_folder_sync_job(job_id: str):
    return {"job_id": job_id, "status": "completed"}


async def _folder_job_events_stream(job_id: str):
    yield f"data: {json.dumps({'type': 'status', 'status': 'completed'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/linked-folder-jobs/{job_id}/events")
async def stream_folder_sync_job_events(job_id: str):
    return StreamingResponse(_folder_job_events_stream(job_id), media_type="text/event-stream")
