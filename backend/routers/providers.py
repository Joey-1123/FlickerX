"""LLM Provider configuration — real HTTP testing, model listing via /v1/models."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Optional

import httpx
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import STUDIO_DB
from database import execute, query

logger = structlog.get_logger()
router = APIRouter(prefix="/api/providers", tags=["providers"])

# ---------------------------------------------------------------------------
# Registry — known providers with defaults
# ---------------------------------------------------------------------------
_PROVIDER_DEFAULTS: dict[str, dict[str, Any]] = {
    "openai": {"base_url": "https://api.openai.com/v1", "requires_key": True},
    "anthropic": {"base_url": "https://api.anthropic.com/v1", "requires_key": True},
    "google": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "requires_key": True},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "requires_key": True},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "requires_key": True},
    "together": {"base_url": "https://api.together.xyz/v1", "requires_key": True},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "requires_key": True},
    "fireworks": {"base_url": "https://api.fireworks.ai/inference/v1", "requires_key": True},
    "mistral": {"base_url": "https://api.mistral.ai/v1", "requires_key": True},
    "ollama": {"base_url": "http://localhost:11434/v1", "requires_key": False},
}

_configs: list[dict] = []


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def _load_from_db() -> None:
    rows = query(STUDIO_DB, "SELECT * FROM provider_configs ORDER BY created_at")
    for row in rows:
        _configs.append({
            "id": row["id"],
            "provider_id": row["provider_id"],
            "name": row["name"],
            "api_key": row["api_key"],
            "base_url": row["base_url"],
            "models": json.loads(row["models_json"] or "[]"),
            "created_at": row["created_at"],
        })


def _save_to_db(config: dict) -> None:
    execute(STUDIO_DB, (
        "INSERT OR REPLACE INTO provider_configs (id, provider_id, name, api_key, base_url, models_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    ), (
        config["id"], config["provider_id"], config["name"],
        config.get("api_key"), config.get("base_url"),
        json.dumps(config.get("models", [])), config["created_at"],
    ))


def _delete_from_db(config_id: str) -> None:
    execute(STUDIO_DB, "DELETE FROM provider_configs WHERE id = ?", (config_id,))


_load_from_db()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ProviderConfigCreate(BaseModel):
    provider_id: str
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[list[str]] = None


class ProviderConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[list[str]] = None


class ProviderTestRequest(BaseModel):
    provider_type: str
    provider_id: Optional[str] = None
    encrypted_api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_id: Optional[str] = None


class ProviderModelsRequest(BaseModel):
    provider_type: str
    provider_id: Optional[str] = None
    encrypted_api_key: Optional[str] = None
    base_url: Optional[str] = None


class ApiKeyMigrate(BaseModel):
    api_key: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_config(provider_type: str, provider_id: Optional[str] = None) -> dict:
    """Find the stored config for a provider, falling back to registry defaults."""
    if provider_id:
        for c in _configs:
            if c["id"] == provider_id:
                return c
    for c in _configs:
        if c["provider_id"] == provider_type:
            return c
    defaults = _PROVIDER_DEFAULTS.get(provider_type, {})
    return {"provider_id": provider_type, "base_url": defaults.get("base_url", ""), "api_key": None}


def _get_api_key(provider_type: str, provider_id: Optional[str] = None,
                 encrypted_key: Optional[str] = None) -> Optional[str]:
    """Resolve API key: explicit encrypted key takes precedence over saved."""
    config = _resolve_config(provider_type, provider_id)
    # ponytail: encrypted_api_key is RSA-OAEP from the frontend. We accept it as-is
    # for now. In production, decrypt with the private key. The frontend encrypts
    # client-side, but for local dev we pass it through.
    if encrypted_key:
        return encrypted_key
    return config.get("api_key")


def _get_base_url(provider_type: str, provider_id: Optional[str] = None,
                   base_url: Optional[str] = None) -> str:
    if base_url:
        return base_url
    config = _resolve_config(provider_type, provider_id)
    return config.get("base_url") or _PROVIDER_DEFAULTS.get(provider_type, {}).get("base_url", "")


async def _fetch_models(base_url: str, api_key: Optional[str]) -> list[dict]:
    """Fetch model list from an OpenAI-compatible /v1/models endpoint."""
    url = f"{base_url.rstrip('/')}/models"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for m in data.get("data", []):
            models.append({
                "id": m.get("id", ""),
                "display_name": m.get("id", ""),
                "context_length": None,
                "owned_by": m.get("owned_by"),
            })
        return models


async def _test_connection(base_url: str, api_key: Optional[str],
                            model_id: Optional[str] = None) -> dict:
    """Test provider connectivity. Tries /v1/models first, falls back to chat probe."""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Try /v1/models
        try:
            resp = await client.get(f"{base_url.rstrip('/')}/models", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("data", []))
                return {"success": True, "message": f"Connected ({count} models)", "models_count": count}
        except Exception:
            pass

        # Fallback: 1-token chat probe
        try:
            probe_model = model_id or "gpt-3.5-turbo"
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={**headers, "Content-Type": "application/json"},
                json={"model": probe_model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                timeout=10.0,
            )
            if resp.status_code in (200, 401, 403):
                msg = "Connection successful" if resp.status_code == 200 else f"Endpoint reachable (HTTP {resp.status_code})"
                return {"success": True, "message": msg, "models_count": None}
        except Exception:
            pass

    return {"success": False, "message": f"Failed to connect to {base_url}", "models_count": None}


# ---------------------------------------------------------------------------
# Public key (for client-side encryption — placeholder)
# ---------------------------------------------------------------------------
@router.get("/public-key")
async def public_key():
    return {"public_key": "(placeholder-public-key)"}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
@router.get("/registry")
async def list_registry(include_hidden: bool = False):
    providers = [
        {"id": pid, "name": pid.replace("_", " ").title(), **info}
        for pid, info in _PROVIDER_DEFAULTS.items()
    ]
    return {"providers": providers}


# ---------------------------------------------------------------------------
# Provider configs CRUD
# ---------------------------------------------------------------------------
@router.get("/")
async def list_configs():
    safe = [{**c, "api_key": "***" if c.get("api_key") else None} for c in _configs]
    return {"providers": safe}


@router.post("/")
async def create_config(req: ProviderConfigCreate):
    config = {
        "id": uuid.uuid4().hex[:12],
        "provider_id": req.provider_id,
        "name": req.name or req.provider_id,
        "api_key": req.api_key,
        "base_url": req.base_url,
        "models": req.models or [],
        "created_at": time.time(),
    }
    _configs.append(config)
    _save_to_db(config)
    return {**config, "api_key": "***" if config["api_key"] else None}


@router.put("/{config_id}")
async def update_config(config_id: str, body: ProviderConfigUpdate):
    for c in _configs:
        if c["id"] == config_id:
            if body.name is not None:
                c["name"] = body.name
            if body.api_key is not None:
                c["api_key"] = body.api_key
            if body.base_url is not None:
                c["base_url"] = body.base_url
            if body.models is not None:
                c["models"] = body.models
            _save_to_db(c)
            return {**c, "api_key": "***" if c["api_key"] else None}
    raise HTTPException(404, "Provider config not found")


@router.delete("/{config_id}")
async def delete_config(config_id: str):
    global _configs
    before = len(_configs)
    _configs = [c for c in _configs if c["id"] != config_id]
    if len(_configs) == before:
        raise HTTPException(404, "Provider config not found")
    _delete_from_db(config_id)
    return None


@router.put("/{config_id}/api-key/migrate")
async def migrate_api_key(config_id: str, body: ApiKeyMigrate):
    for c in _configs:
        if c["id"] == config_id:
            c["api_key"] = body.api_key
            _save_to_db(c)
            return {"migrated": True}
    raise HTTPException(404, "Provider config not found")


# ---------------------------------------------------------------------------
# Test / List models — REAL HTTP calls
# ---------------------------------------------------------------------------
@router.post("/test")
async def test_provider(req: ProviderTestRequest):
    base_url = _get_base_url(req.provider_type, req.provider_id, req.base_url)
    api_key = _get_api_key(req.provider_type, req.provider_id, req.encrypted_api_key)
    result = await _test_connection(base_url, api_key, req.model_id)
    logger.info("provider_test", provider=req.provider_type, base_url=base_url, success=result["success"])
    return result


@router.post("/models")
async def list_provider_models(req: ProviderModelsRequest):
    base_url = _get_base_url(req.provider_type, req.provider_id, req.base_url)
    api_key = _get_api_key(req.provider_type, req.provider_id, req.encrypted_api_key)
    try:
        models = await _fetch_models(base_url, api_key)
        return models
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Provider returned error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch models: {e}")


# ---------------------------------------------------------------------------
# OAuth (Codex — placeholder)
# ---------------------------------------------------------------------------
@router.post("/{config_id}/oauth/start")
async def start_oauth(config_id: str):
    flow_id = uuid.uuid4().hex[:8]
    return {"flow_id": flow_id, "url": f"https://example.com/oauth/{flow_id}"}


@router.get("/{config_id}/oauth/flows/{flow_id}")
async def get_oauth_flow(config_id: str, flow_id: str):
    return {"flow_id": flow_id, "status": "pending"}


@router.post("/{config_id}/oauth/flows/{flow_id}/complete")
async def complete_oauth(config_id: str, flow_id: str):
    return {"status": "completed", "token": "(placeholder)"}


@router.delete("/{config_id}/oauth/flows/{flow_id}")
async def cancel_oauth_flow(config_id: str, flow_id: str):
    return {"status": "cancelled"}


@router.delete("/{config_id}/oauth")
async def disconnect_oauth(config_id: str):
    return {"status": "disconnected"}
