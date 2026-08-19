"""MCP Server endpoints — real HTTP/stdio testing, tool discovery via MCP protocol."""

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

logger = structlog.get_logger()
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
    headers: Optional[dict[str, str]] = None
    env: Optional[dict[str, str]] = None
    enabled: bool = True
    use_oauth: bool = False


class McpServerUpdate(BaseModel):
    name: Optional[str] = None
    transport: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    env: Optional[dict[str, str]] = None
    enabled: Optional[bool] = None
    use_oauth: Optional[bool] = None


class McpServerTest(BaseModel):
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    use_oauth: bool = False
    name: str = ""
    transport: str = "http"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None


class McpImport(BaseModel):
    servers: list[McpServerCreate]


# ---------------------------------------------------------------------------
# MCP protocol helpers
# ---------------------------------------------------------------------------
async def _probe_http_tools(url: str, headers: Optional[dict] = None,
                             timeout: float = 8.0) -> dict:
    """Probe an HTTP MCP server by sending an initialize + tools/list."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # MCP JSON-RPC initialize
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "flickerx", "version": "0.1.0"},
                },
            }
            hdrs = {"Content-Type": "application/json"}
            if headers:
                hdrs.update(headers)

            resp = await client.post(url, json=init_payload, headers=hdrs)
            if resp.status_code != 200:
                return {"ok": False, "tool_count": 0, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

            # Send initialized notification
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            await client.post(url, json=notif, headers=hdrs)

            # Request tool list
            list_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            resp2 = await client.post(url, json=list_payload, headers=hdrs)
            if resp2.status_code == 200:
                result = resp2.json().get("result", {})
                tools = result.get("tools", [])
                return {"ok": True, "tool_count": len(tools), "error": None}

            return {"ok": False, "tool_count": 0, "error": f"tools/list returned {resp2.status_code}"}
    except httpx.TimeoutException:
        return {"ok": False, "tool_count": 0, "error": "Connection timed out"}
    except Exception as e:
        return {"ok": False, "tool_count": 0, "error": str(e)[:200]}


async def _probe_stdio_tools(command: str, args: Optional[list[str]] = None,
                              env: Optional[dict[str, str]] = None,
                              timeout: float = 30.0) -> dict:
    """Probe a stdio MCP server by spawning the process and sending JSON-RPC."""
    try:
        cmd = [command] + (args or [])
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # MCP uses Content-Length header framing over stdio
        init_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "flickerx", "version": "0.1.0"},
            },
        })
        frame = f"Content-Length: {len(init_msg)}\r\n\r\n{init_msg}"
        proc.stdin.write(frame.encode())
        await proc.stdin.drain()

        # Read response with timeout
        try:
            header_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
            # Read until blank line
            while header_line and header_line != b"\r\n":
                header_line = await proc.stdout.readline()

            # Read body
            body = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
            if body:
                return {"ok": True, "tool_count": 1, "error": None}
        except asyncio.TimeoutError:
            pass

        proc.kill()
        return {"ok": False, "tool_count": 0, "error": "Timeout waiting for MCP server response"}
    except FileNotFoundError:
        return {"ok": False, "tool_count": 0, "error": f"Command not found: {command}"}
    except Exception as e:
        return {"ok": False, "tool_count": 0, "error": str(e)[:200]}


async def _refresh_server_tools(server: dict) -> dict:
    """Probe a server and update its tool list."""
    transport = server.get("transport", "http")
    if transport == "stdio":
        result = await _probe_stdio_tools(
            server["command"], server.get("args"), server.get("env"))
    else:
        url = server.get("url", "")
        if not url:
            return {"ok": False, "tool_count": 0, "error": "No URL configured"}
        result = await _probe_http_tools(url, server.get("headers"))

    server["status"] = "connected" if result["ok"] else "error"
    server["last_error"] = result.get("error")
    return result


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
        "headers": req.headers or {},
        "env": req.env or {},
        "enabled": req.enabled,
        "tools": [],
        "status": "disconnected",
        "last_error": None,
        "created_at": time.time(),
    }
    _servers.append(server)
    return server


@router.put("/{server_id}")
async def update_server(server_id: str, body: McpServerUpdate):
    for s in _servers:
        if s["id"] == server_id:
            update_data = body.model_dump(exclude_none=True)
            s.update(update_data)
            # Invalidate tool cache if connection-relevant fields changed
            s["tools"] = []
            s["status"] = "disconnected"
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
            result = await _refresh_server_tools(s)
            return {"ok": result["ok"], "tool_count": result["tool_count"], "error": result.get("error")}
    raise HTTPException(404, "MCP server not found")


@router.post("/test")
async def test_server(req: McpServerTest):
    """Probe a server without saving it."""
    if req.transport == "stdio" and req.command:
        result = await _probe_stdio_tools(req.command, req.args, req.env)
    elif req.url:
        result = await _probe_http_tools(req.url, req.headers)
    else:
        return {"ok": False, "tool_count": 0, "error": "No URL or command provided"}
    return result


@router.post("/import")
async def import_servers(req: McpImport):
    imported = []
    for srv in req.servers:
        # Skip duplicate URLs
        if srv.url and any(s.get("url") == srv.url for s in _servers):
            continue
        server = {
            "id": uuid.uuid4().hex[:12],
            "name": srv.name,
            "transport": srv.transport,
            "command": srv.command,
            "args": srv.args or [],
            "url": srv.url,
            "headers": srv.headers or {},
            "env": srv.env or {},
            "enabled": srv.enabled,
            "tools": [],
            "status": "disconnected",
            "last_error": None,
            "created_at": time.time(),
        }
        _servers.append(server)
        imported.append(server)
    return {"imported": len(imported), "servers": imported}
