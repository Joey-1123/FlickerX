"""Prompt templates — SQLite persistence."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import execute, query, STUDIO_DB

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------
_PROMPTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS prompt_entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    tags TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS prompt_lists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entries TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def _init_prompts_db() -> None:
    conn = sqlite3.connect(str(STUDIO_DB))
    try:
        conn.executescript(_PROMPTS_SCHEMA)
        conn.commit()
    finally:
        conn.close()


_init_prompts_db()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class PromptEntry(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[list[str]] = None


class PromptList(BaseModel):
    id: Optional[str] = None
    name: str
    entries: list[dict] = []


class BulkEntries(BaseModel):
    entries: list[PromptEntry]


class BulkLists(BaseModel):
    lists: list[PromptList]


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------
@router.get("/entries")
async def list_entries():
    rows = query(STUDIO_DB, "SELECT * FROM prompt_entries ORDER BY created_at")
    entries = []
    for r in rows:
        e = dict(r)
        try:
            e["tags"] = json.loads(e.get("tags", "[]"))
        except Exception:
            e["tags"] = []
        entries.append(e)
    return {"entries": entries}


@router.put("/entries/{entry_id}")
async def save_entry(entry_id: str, body: PromptEntry):
    tags_json = json.dumps(body.tags or [])
    existing = query(STUDIO_DB, "SELECT id FROM prompt_entries WHERE id = ?", (entry_id,))
    if existing:
        execute(STUDIO_DB,
                "UPDATE prompt_entries SET title = ?, content = ?, category = ?, tags = ? WHERE id = ?",
                (body.title, body.content, body.category, tags_json, entry_id))
        return {**body.model_dump(), "id": entry_id}
    else:
        execute(STUDIO_DB,
                "INSERT INTO prompt_entries (id, title, content, category, tags) VALUES (?, ?, ?, ?, ?)",
                (entry_id, body.title, body.content, body.category, tags_json))
        return {**body.model_dump(), "id": entry_id}


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str):
    execute(STUDIO_DB, "DELETE FROM prompt_entries WHERE id = ?", (entry_id,))
    return {"ok": True}


@router.post("/entries/bulk")
async def bulk_save_entries(body: BulkEntries):
    result = []
    for entry in body.entries:
        eid = entry.id or uuid.uuid4().hex[:8]
        tags_json = json.dumps(entry.tags or [])
        existing = query(STUDIO_DB, "SELECT id FROM prompt_entries WHERE id = ?", (eid,))
        if existing:
            execute(STUDIO_DB,
                    "UPDATE prompt_entries SET title = ?, content = ?, category = ?, tags = ? WHERE id = ?",
                    (entry.title, entry.content, entry.category, tags_json, eid))
        else:
            execute(STUDIO_DB,
                    "INSERT INTO prompt_entries (id, title, content, category, tags) VALUES (?, ?, ?, ?, ?)",
                    (eid, entry.title, entry.content, entry.category, tags_json))
        result.append({**entry.model_dump(), "id": eid})
    return {"entries": result}


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------
@router.get("/lists")
async def list_prompt_lists():
    rows = query(STUDIO_DB, "SELECT * FROM prompt_lists ORDER BY created_at")
    lists = []
    for r in rows:
        lst = dict(r)
        try:
            lst["entries"] = json.loads(lst.get("entries", "[]"))
        except Exception:
            lst["entries"] = []
        lists.append(lst)
    return {"lists": lists}


@router.put("/lists/{list_id}")
async def save_list(list_id: str, body: PromptList):
    entries_json = json.dumps(body.entries)
    existing = query(STUDIO_DB, "SELECT id FROM prompt_lists WHERE id = ?", (list_id,))
    if existing:
        execute(STUDIO_DB, "UPDATE prompt_lists SET name = ?, entries = ? WHERE id = ?",
                (body.name, entries_json, list_id))
        return {**body.model_dump(), "id": list_id}
    else:
        execute(STUDIO_DB, "INSERT INTO prompt_lists (id, name, entries) VALUES (?, ?, ?)",
                (list_id, body.name, entries_json))
        return {**body.model_dump(), "id": list_id}


@router.delete("/lists/{list_id}")
async def delete_list(list_id: str):
    execute(STUDIO_DB, "DELETE FROM prompt_lists WHERE id = ?", (list_id,))
    return {"ok": True}


@router.post("/lists/bulk")
async def bulk_save_lists(body: BulkLists):
    result = []
    for lst in body.lists:
        lid = lst.id or uuid.uuid4().hex[:8]
        entries_json = json.dumps(lst.entries)
        existing = query(STUDIO_DB, "SELECT id FROM prompt_lists WHERE id = ?", (lid,))
        if existing:
            execute(STUDIO_DB, "UPDATE prompt_lists SET name = ?, entries = ? WHERE id = ?",
                    (lst.name, entries_json, lid))
        else:
            execute(STUDIO_DB, "INSERT INTO prompt_lists (id, name, entries) VALUES (?, ?, ?)",
                    (lid, lst.name, entries_json))
        result.append({**lst.model_dump(), "id": lid})
    return {"lists": result}
