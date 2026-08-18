"""LLM Provider configuration endpoints — /api/providers/*"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/providers", tags=["providers"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_configs: list[dict] = []
_registry: list[dict] = [
    {"id": "openai", "name": "OpenAI", "base_url": "https://api.openai.com/v1", "requires_key": True, "models_endpoint": "/v1/models"},
    {"id": "anthropic", "name": "Anthropic", "base_url": "https://api.anthropic.com/v1", "requires_key": True},
    {"id": "google", "name": "Google AI", "base_url": "https://generativelanguage.googleapis.com/v1", "requires_key": True},
    {"id": "groq", "name": "Groq", "base_url": "https://api.groq.com/openai/v1", "requires_key": True},
    {"id": "openrouter", "name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "requires_key": True},
    {"id": "together", "name": "Together AI", "base_url": "https://api.together.xyz/v1", "requires_key": True},
    {"id": "deepseek", "name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "requires_key": True},
    {"id": "fireworks", "name": "Fireworks AI", "base_url": "https://api.fireworks.ai/inference/v1", "requires_key": True},
    {"id": "mistral", "name": "Mistral AI", "base_url": "https://api.mistral.ai/v1", "requires_key": True},
    {"id": "ollama", "name": "Ollama (Local)", "base_url": "http://localhost:11434/v1", "requires_key": False},
]


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
    provider_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ProviderModelsRequest(BaseModel):
    provider_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ApiKeyMigrate(BaseModel):
    api_key: str = ""


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
    providers = _registry if include_hidden else [p for p in _registry if not p.get("hidden")]
    return {"providers": providers}


# ---------------------------------------------------------------------------
# Provider configs
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
            return {**c, "api_key": "***" if c["api_key"] else None}
    raise HTTPException(404, "Provider config not found")


@router.delete("/{config_id}")
async def delete_config(config_id: str):
    global _configs
    before = len(_configs)
    _configs = [c for c in _configs if c["id"] != config_id]
    if len(_configs) == before:
        raise HTTPException(404, "Provider config not found")
    return None


@router.put("/{config_id}/api-key/migrate")
async def migrate_api_key(config_id: str, body: ApiKeyMigrate):
    for c in _configs:
        if c["id"] == config_id:
            c["api_key"] = body.api_key
            return {"migrated": True}
    raise HTTPException(404, "Provider config not found")


# ---------------------------------------------------------------------------
# Test / List models
# ---------------------------------------------------------------------------
@router.post("/test")
async def test_provider(req: ProviderTestRequest):
    return {"success": True, "message": "Connection successful", "latency_ms": 150}


@router.post("/models")
async def list_provider_models(req: ProviderModelsRequest):
    return {"models": [
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
    ]}


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
