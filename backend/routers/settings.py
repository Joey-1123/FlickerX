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
            pass
    return {
        "version": 1,
        "profile": {
            "displayName": "",
            "nickname": "",
            "avatarDataUrl": None,
            "avatarShape": "circle",
            "showGreetingAvatar": True,
        },
        "appearance": {
            "theme": "dark",
            "palette": "standard",
            "language": "en",
            "customization": {},
        },
        "saved": False,
        "customizationSaved": False,
        "paletteSaved": False,
        "greetingAvatarSaved": False,
    }


@router.put("/personalization")
def save_personalization(body: dict, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('personalization', ?, datetime('now'))",
            (json.dumps(body),))
    return {"saved": True}


# ---------------------------------------------------------------------------
# Embedding model settings
# ---------------------------------------------------------------------------
@router.get("/embedding-model")
def get_embedding_model(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'embedding_model'")
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
            return {
                "embedding_model": stored.get("embedding_model", ""),
                "embedding_gguf_repo": stored.get("embedding_gguf_repo", ""),
                "default_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "default_embedding_gguf_repo": "nomic-ai/nomic-embed-text-v1.5-GGUF",
                "is_custom": bool(stored.get("embedding_model")),
            }
        except Exception:
            pass
    return {
        "embedding_model": "",
        "embedding_gguf_repo": "",
        "default_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "default_embedding_gguf_repo": "nomic-ai/nomic-embed-text-v1.5-GGUF",
        "is_custom": False,
    }


@router.put("/embedding-model")
def save_embedding_model(body: dict, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('embedding_model', ?, datetime('now'))",
            (json.dumps(body),))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Hugging Face cache paths
# ---------------------------------------------------------------------------
@router.get("/hugging-face-cache")
def get_hugging_face_cache(user: dict = Depends(get_current_user)):
    import os
    from pathlib import Path
    cache_home = os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    hub_cache = str(Path(cache_home) / "hub")
    return {
        "cache_home": cache_home,
        "hub_cache": hub_cache,
        "xet_cache": str(Path(cache_home) / "xet"),
        "source": "environment" if os.environ.get("HF_HOME") else "default",
        "editable": True,
        "is_custom": bool(os.environ.get("HF_HOME")),
        "available": True,
        "writable": True,
        "free_bytes": 0,
        "environment_variable": "HF_HOME",
    }


# ---------------------------------------------------------------------------
# Preview sharing
# ---------------------------------------------------------------------------
@router.get("/preview-sharing")
def get_preview_sharing(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'preview_sharing'")
    enabled = True
    if rows:
        try:
            enabled = json.loads(rows[0]["value"]).get("enabled", True)
        except Exception:
            pass
    return {"enabled": enabled, "default_enabled": True}


@router.put("/preview-sharing")
def save_preview_sharing(body: dict, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('preview_sharing', ?, datetime('now'))",
            (json.dumps(body),))
    return {"enabled": body.get("enabled", True), "default_enabled": True}


# ---------------------------------------------------------------------------
# Upload limit (singular — frontend uses /upload-limit)
# ---------------------------------------------------------------------------
@router.get("/upload-limit")
def get_upload_limit(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'upload_limits'")
    stored = {}
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
        except Exception:
            pass
    max_mb = stored.get("max_file_size_mb", 500)
    max_bytes = max_mb * 1024 * 1024
    return {
        "max_upload_size_mb": max_mb,
        "max_upload_size_bytes": max_bytes,
        "max_upload_size_label": f"{max_mb}MB",
        "default_upload_size_mb": 500,
        "min_upload_size_mb": 1,
        "max_allowed_upload_size_mb": max_mb,
    }


@router.put("/upload-limit")
def save_upload_limit(body: dict, user: dict = Depends(get_current_user)):
    max_mb = body.get("max_upload_size_mb", 500)
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('upload_limits', ?, datetime('now'))",
            (json.dumps({"max_file_size_mb": max_mb, "max_total_mb": 1024, "allowed_types": ["image/*", "audio/*", "video/*", "application/pdf"]}),))
    max_bytes = max_mb * 1024 * 1024
    return {
        "max_upload_size_mb": max_mb,
        "max_upload_size_bytes": max_bytes,
        "max_upload_size_label": f"{max_mb}MB",
        "default_upload_size_mb": 500,
        "min_upload_size_mb": 1,
        "max_allowed_upload_size_mb": max_mb,
    }


# ---------------------------------------------------------------------------
# Helper precache
# ---------------------------------------------------------------------------
@router.get("/helper-precache")
def get_helper_precache(user: dict = Depends(get_current_user)):
    return {"enabled": True, "default_enabled": True, "disabled_by_env": False}


# ---------------------------------------------------------------------------
# Coding agents detection
# ---------------------------------------------------------------------------
@router.get("/coding-agents")
def get_coding_agents(user: dict = Depends(get_current_user)):
    import shutil
    detected = []
    for agent in ("claude", "codex", "opencode", "cursor", "aider"):
        if shutil.which(agent):
            detected.append(agent)
    return {"agents": detected, "detected": detected}


# ---------------------------------------------------------------------------
# Model memory settings
# ---------------------------------------------------------------------------
@router.get("/model-memory")
def get_model_memory(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'model_memory'")
    stored = {}
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
        except Exception:
            pass
    return {
        "keep_resident": stored.get("keep_resident", True),
        "no_ram_reserve": stored.get("no_ram_reserve", False),
        "default_keep_resident": True,
        "default_no_ram_reserve": False,
        "mlock_active": not stored.get("no_ram_reserve", False),
        "reload_required": False,
        "memlock_limit_bytes": None,
    }


@router.put("/model-memory")
def save_model_memory(body: dict, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'model_memory'")
    stored = {}
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
        except Exception:
            pass
    stored.update(body)
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('model_memory', ?, datetime('now'))",
            (json.dumps(stored),))
    return {
        "keep_resident": stored.get("keep_resident", True),
        "no_ram_reserve": stored.get("no_ram_reserve", False),
        "default_keep_resident": True,
        "default_no_ram_reserve": False,
        "mlock_active": not stored.get("no_ram_reserve", False),
        "reload_required": False,
        "memlock_limit_bytes": None,
    }


# ---------------------------------------------------------------------------
# OpenAI auto-switch
# ---------------------------------------------------------------------------
@router.get("/openai-auto-switch")
def get_openai_auto_switch(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'openai_auto_switch'")
    stored = {}
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
        except Exception:
            pass
    return {
        "enabled": stored.get("enabled", False),
        "auto_unload_idle_seconds": stored.get("auto_unload_idle_seconds", 300),
        "default_enabled": False,
        "idle_unload_active": stored.get("enabled", False),
        "auto_unload_keep_kv": stored.get("auto_unload_keep_kv", True),
        "auto_download_model": stored.get("auto_download_model", False),
        "auto_unload_api_only": stored.get("auto_unload_api_only", False),
        "media_auto_unload_idle_seconds": stored.get("media_auto_unload_idle_seconds", 0),
        "media_idle_unload_active": False,
        "media_auto_switch_model": stored.get("media_auto_switch_model", False),
    }


@router.put("/openai-auto-switch")
def save_openai_auto_switch(body: dict, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'openai_auto_switch'")
    stored = {}
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
        except Exception:
            pass
    stored.update(body)
    execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('openai_auto_switch', ?, datetime('now'))",
            (json.dumps(stored),))
    return {
        "enabled": stored.get("enabled", False),
        "auto_unload_idle_seconds": stored.get("auto_unload_idle_seconds", 300),
        "default_enabled": False,
        "idle_unload_active": stored.get("enabled", False),
        "auto_unload_keep_kv": stored.get("auto_unload_keep_kv", True),
        "auto_download_model": stored.get("auto_download_model", False),
        "auto_unload_api_only": stored.get("auto_unload_api_only", False),
        "media_auto_unload_idle_seconds": stored.get("media_auto_unload_idle_seconds", 0),
        "media_idle_unload_active": False,
        "media_auto_switch_model": stored.get("media_auto_switch_model", False),
    }


# ---------------------------------------------------------------------------
# VRAM budget
# ---------------------------------------------------------------------------
@router.get("/vram-budget")
def get_vram_budget(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT value FROM settings WHERE key = 'vram_budget'")
    stored = {}
    if rows:
        try:
            stored = json.loads(rows[0]["value"])
        except Exception:
            pass
    return {
        "fraction": stored.get("fraction", 0.9),
        "is_stored": bool(stored.get("fraction")),
        "default_fraction": 0.9,
        "min_fraction": 0.1,
        "max_fraction": 1.0,
        "reload_required": False,
    }


@router.put("/vram-budget")
def save_vram_budget(body: dict, user: dict = Depends(get_current_user)):
    fraction = body.get("fraction")
    if fraction is not None:
        execute(AUTH_DB, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('vram_budget', ?, datetime('now'))",
                (json.dumps({"fraction": fraction}),))
    else:
        execute(AUTH_DB, "DELETE FROM settings WHERE key = 'vram_budget'")
    return {
        "fraction": fraction if fraction is not None else 0.9,
        "is_stored": fraction is not None,
        "default_fraction": 0.9,
        "min_fraction": 0.1,
        "max_fraction": 1.0,
        "reload_required": False,
    }


# ---------------------------------------------------------------------------
# Remote access
# ---------------------------------------------------------------------------
@router.get("/remote-access")
def get_remote_access(user: dict = Depends(get_current_user)):
    return {
        "state": "off",
        "url": None,
        "error": None,
        "auto_start": False,
        "default_auto_start": False,
        "available": False,
        "managed_by": None,
        "can_start": False,
        "can_stop": False,
        "block_reason": None,
        "password_pending": False,
        "streaming_supported": False,
    }


@router.post("/remote-access/start")
def start_remote_access(user: dict = Depends(get_current_user)):
    return {
        "state": "off",
        "url": None,
        "error": "Remote access is not configured in this deployment",
        "auto_start": False,
        "default_auto_start": False,
        "available": False,
        "managed_by": None,
        "can_start": False,
        "can_stop": False,
        "block_reason": None,
        "password_pending": False,
        "streaming_supported": False,
    }


@router.post("/remote-access/stop")
def stop_remote_access(user: dict = Depends(get_current_user)):
    return {
        "state": "off",
        "url": None,
        "error": None,
        "auto_start": False,
        "default_auto_start": False,
        "available": False,
        "managed_by": None,
        "can_start": False,
        "can_stop": False,
        "block_reason": None,
        "password_pending": False,
        "streaming_supported": False,
    }


@router.put("/remote-access/auto-start")
def update_remote_access_auto_start(body: dict, user: dict = Depends(get_current_user)):
    return {
        "state": "off",
        "url": None,
        "error": None,
        "auto_start": body.get("enabled", False),
        "default_auto_start": False,
        "available": False,
        "managed_by": None,
        "can_start": False,
        "can_stop": False,
        "block_reason": None,
        "password_pending": False,
        "streaming_supported": False,
    }


# ---------------------------------------------------------------------------
# Debug logs
# ---------------------------------------------------------------------------
@router.get("/debug/logs/sources")
def get_debug_log_sources(user: dict = Depends(get_current_user)):
    from config import LOGS_DIR
    sources = []
    if LOGS_DIR.exists():
        for f in sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.is_file():
                sources.append({
                    "id": f.name,
                    "family": f.suffix.lstrip(".") or "log",
                    "label": f.stem.replace("-", " ").replace("_", " ").title(),
                    "realpath": str(f.resolve()),
                    "size_bytes": f.stat().st_size,
                    "modified_at": int(f.stat().st_mtime),
                    "is_current": len(sources) == 0,
                })
    default_id = sources[0]["id"] if sources else None
    return {"sources": sources, "default_source_id": default_id, "file_logging_disabled": False}


@router.get("/debug/logs")
def get_debug_logs(source: str = "", cursor: str = "", user: dict = Depends(get_current_user)):
    from config import LOGS_DIR
    lines = []
    status = "ok"
    realpath = None
    size_bytes = 0
    log_files = sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True) if LOGS_DIR.exists() else []
    target = None
    for f in log_files:
        if f.name == source or (not source and len(lines) == 0):
            target = f
            break
    if not target and log_files:
        target = log_files[0]
    if target and target.exists():
        realpath = str(target.resolve())
        size_bytes = target.stat().st_size
        try:
            with open(target) as fh:
                lines = [l.rstrip() for l in fh.readlines()[-200:]]
        except Exception:
            status = "unreadable"
    elif not log_files:
        status = "missing"
    return {
        "status": status,
        "reason": None,
        "source_id": target.name if target else None,
        "realpath": realpath,
        "lines": lines,
        "cursor": None,
        "reset": False,
        "reset_reason": None,
        "dropped_bytes": 0,
        "truncated_head": False,
        "more_pending": False,
        "file_logging_disabled": False,
        "size_bytes": size_bytes,
    }


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

