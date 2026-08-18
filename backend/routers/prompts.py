"""Prompt templates endpoints — /api/prompts/*"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_entries: list[dict] = []
_lists: list[dict] = []


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
    return {"entries": _entries}


@router.put("/entries/{entry_id}")
async def save_entry(entry_id: str, body: PromptEntry):
    for i, e in enumerate(_entries):
        if e["id"] == entry_id:
            _entries[i] = {**body.dict(), "id": entry_id}
            return _entries[i]
    # Create new
    entry = {**body.dict(), "id": entry_id}
    _entries.append(entry)
    return entry


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str):
    global _entries
    before = len(_entries)
    _entries = [e for e in _entries if e["id"] != entry_id]
    if len(_entries) == before:
        raise HTTPException(404, "Entry not found")
    return None


@router.post("/entries/bulk")
async def bulk_save_entries(body: BulkEntries):
    result = []
    for entry in body.entries:
        eid = entry.id or uuid.uuid4().hex[:8]
        record = {**entry.dict(), "id": eid}
        # Upsert
        _entries[:] = [e for e in _entries if e["id"] != eid]
        _entries.append(record)
        result.append(record)
    return {"entries": result}


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------
@router.get("/lists")
async def list_prompt_lists():
    return {"lists": _lists}


@router.put("/lists/{list_id}")
async def save_list(list_id: str, body: PromptList):
    for i, l in enumerate(_lists):
        if l["id"] == list_id:
            _lists[i] = {**body.dict(), "id": list_id}
            return _lists[i]
    lst = {**body.dict(), "id": list_id}
    _lists.append(lst)
    return lst


@router.delete("/lists/{list_id}")
async def delete_list(list_id: str):
    global _lists
    before = len(_lists)
    _lists = [l for l in _lists if l["id"] != list_id]
    if len(_lists) == before:
        raise HTTPException(404, "List not found")
    return None


@router.post("/lists/bulk")
async def bulk_save_lists(body: BulkLists):
    result = []
    for lst in body.lists:
        lid = lst.id or uuid.uuid4().hex[:8]
        record = {**lst.dict(), "id": lid}
        _lists[:] = [l for l in _lists if l["id"] != lid]
        _lists.append(record)
        result.append(record)
    return {"lists": result}
