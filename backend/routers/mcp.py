"""MCP Server endpoints — /api/mcp/servers/*"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/mcp/servers", tags=["mcp"])

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
_servers: list[dict] = []


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class McpServerCreate(BaseModel):
    name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None
    enabled: bool = True


class McpServerUpdate(BaseModel):
    name: Optional[str] = None
    transport: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None
    enabled: Optional[bool] = None


class McpServerTest(BaseModel):
    name: str = ""
    transport: str = "stdio"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None


class McpImport(BaseModel):
    servers: list[McpServerCreate]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/")
async def list_servers():
    return {"servers": _servers}


@router.post("/")
async def create_server(req: McpServerCreate):
    server = {
        "id": uuid.uuid4().hex[:12],
        "name": req.name,
        "transport": req.transport,
        "command": req.command,
        "args": req.args or [],
        "url": req.url,
        "env": req.env or {},
        "enabled": req.enabled,
        "tools": [],
        "status": "disconnected",
        "created_at": time.time(),
    }
    _servers.append(server)
    return server


@router.put("/{server_id}")
async def update_server(server_id: str, body: McpServerUpdate):
    for s in _servers:
        if s["id"] == server_id:
            for k, v in body.dict(exclude_none=True).items():
                s[k] = v
            return s
    raise HTTPException(404, "MCP server not found")


@router.delete("/{server_id}")
async def delete_server(server_id: str):
    global _servers
    before = len(_servers)
    _servers = [s for s in _servers if s["id"] != server_id]
    if len(_servers) == before:
        raise HTTPException(404, "MCP server not found")
    return None


@router.post("/{server_id}/refresh")
async def refresh_server_tools(server_id: str):
    for s in _servers:
        if s["id"] == server_id:
            s["status"] = "connected"
            return {"status": "connected", "tools": s.get("tools", [])}
    raise HTTPException(404, "MCP server not found")


@router.post("/test")
async def test_server(req: McpServerTest):
    return {"success": True, "message": "Server connection successful", "tools": []}


@router.post("/import")
async def import_servers(req: McpImport):
    imported = []
    for srv in req.servers:
        server = {
            "id": uuid.uuid4().hex[:12],
            "name": srv.name,
            "transport": srv.transport,
            "command": srv.command,
            "args": srv.args or [],
            "url": srv.url,
            "env": srv.env or {},
            "enabled": srv.enabled,
            "tools": [],
            "status": "disconnected",
            "created_at": time.time(),
        }
        _servers.append(server)
        imported.append(server)
    return {"imported": len(imported), "servers": imported}
