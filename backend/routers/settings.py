"""Settings router — read, write, list, export, import, HF token, personalization."""

from __future__ import annotations

import json
import secrets

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


class HfTokenRequest(BaseModel):
    token: str


# ---------------------------------------------------------------------------
# Core CRUD
# ---------------------------------------------------------------------------
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
# Hugging Face token
# ---------------------------------------------------------------------------
@router.get("/hugging-face-token")
def get_hugging_face_token(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'hugging_face_token'")
    token = rows[0]["value"] if rows else None
    return {"token": token}


@router.put("/hugging-face-token")
def save_hugging_face_token(body: HfTokenRequest, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('hugging_face_token', ?, datetime('now'))",
            (body.token,))
    return {"ok": True}


@router.delete("/hugging-face-token")
def delete_hugging_face_token(user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "DELETE FROM settings WHERE key = 'hugging_face_token'")
    return {"ok": True}


@router.put("/hugging-face-token/migrate")
def migrate_hugging_face_token(body: HfTokenRequest, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('hugging_face_token', ?, datetime('now'))",
            (body.token,))
    return {"ok": True, "token": body.token}


# ---------------------------------------------------------------------------
# Generation presets (image + video)
# ---------------------------------------------------------------------------
_GENERATION_PRESETS = {
    "image": {"width": 512, "height": 512, "steps": 20, "guidance_scale": 7.5, "seed": -1, "scheduler": "euler_a"},
    "video": {"frames": 16, "fps": 8, "width": 256, "height": 256, "steps": 20, "guidance_scale": 7.5, "seed": -1},
}


@router.get("/generation-presets")
def get_generation_presets(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'generation_presets'")
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
            merged = dict(_GENERATION_PRESETS)
            merged.update(stored)
            return {"presets": merged}
        except Exception:
            pass
    return {"presets": _GENERATION_PRESETS}


@router.put("/generation-presets")
def save_generation_presets(body: dict, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('generation_presets', ?, datetime('now'))",
            (json.dumps(body.get("presets", {})),))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Upload limits
# ---------------------------------------------------------------------------
@router.get("/upload-limits")
def get_upload_limits(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'upload_limits'")
    if rows:
        try:
            return {"limits": json.loads(rows[0]["value"])}
        except Exception:
            pass
    return {"limits": {"max_file_size_mb": 100, "max_total_mb": 1024, "allowed_types": ["image/*", "audio/*", "video/*", "application/pdf"]}}


# ---------------------------------------------------------------------------
# Personalization
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Generic settings by key — covers any /api/settings/{key} GET/PUT
# ---------------------------------------------------------------------------
@router.get("/{key}")
def get_setting_by_key(key: str, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = ?", (key,))
    if not rows:
        return {"key": key, "value": None}
    return {"key": key, "value": rows[0]["value"]}


@router.put("/{key}")
def put_setting_by_key(key: str, body: dict, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, json.dumps(body) if isinstance(body, dict) else str(body)))
    return {"ok": True}


@router.delete("/{key}")
def delete_setting_by_key(key: str, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "DELETE FROM settings WHERE key = ?", (key,))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Preview sharing — rotate signing secret
# ---------------------------------------------------------------------------
@router.post("/preview-links/rotate")
def rotate_preview_links(user: dict = Depends(get_current_user)):
    new_secret = secrets.token_urlsafe(32)
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('preview_signing_secret', ?, datetime('now'))",
            (new_secret,))
    return {"ok": True, "secret": new_secret}

