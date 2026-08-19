"""Settings router — read, write, list, export, import."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from database import execute, query, AUTH_DB

router = APIRouter()


class SettingsWriteRequest(BaseModel):
    key: str
    value: str


class SettingsBulkWriteRequest(BaseModel):
    settings: dict[str, str]


@router.get("/read")
def read_setting(key: str, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = ?", (key,))
    if not rows:
        return {"key": key, "value": None}
    return {"key": key, "value": rows[0]["value"]}


@router.get("/list")
def list_settings(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT key, value FROM settings")
    return {"settings": {r["key"]: r["value"] for r in rows}}


@router.put("/write")
def write_setting(req: SettingsWriteRequest, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (req.key, req.value))
    return {"ok": True}


@router.put("/bulk-write")
def bulk_write_settings(req: SettingsBulkWriteRequest, user: dict = Depends(get_current_user)):
    for key, value in req.settings.items():
        execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                (key, value))
    return {"ok": True, "count": len(req.settings)}


@router.get("/export")
def export_settings(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT key, value FROM settings")
    return {"settings": {r["key"]: r["value"] for r in rows}, "exported_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}


@router.put("/import")
def import_settings(body: dict, user: dict = Depends(get_current_user)):
    settings = body.get("settings", {})
    count = 0
    for key, value in settings.items():
        execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                (key, value))
        count += 1
    return {"ok": True, "imported": count}


# ---------------------------------------------------------------------------
# Convenience endpoints the frontend expects
# ---------------------------------------------------------------------------
@router.get("/hugging-face-token")
def get_hugging_face_token(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'hugging_face_token'")
    token = rows[0]["value"] if rows else None
    return {"token": token}


@router.get("/personalization")
def get_personalization(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'personalization'")
    if rows:
        try:
            return json.loads(rows[0]["value"])
        except Exception:
            return {"personalization": rows[0]["value"]}
    return {"theme": "dark", "language": "en", "notifications": True}


@router.put("/personalization")
def save_personalization(body: dict, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('personalization', ?, datetime('now'))",
            (json.dumps(body),))
    return {"saved": True}
