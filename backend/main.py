"""FlickerX Studio — FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from middleware import SecurityHeadersMiddleware, BodySizeMiddleware, RequestLoggingMiddleware

from config import ensure_dirs, HOST, PORT, STUDIO_HOME
from database import init_auth_db, init_studio_db

logger = structlog.get_logger()

# Create tables before router imports — routers call _load_from_db() at import time
ensure_dirs()
init_auth_db()
init_studio_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("flickerx_backend_started", host=HOST, port=PORT, data_dir=str(STUDIO_HOME))
    yield
    logger.info("flickerx_backend_stopped")


app = FastAPI(title="FlickerX Studio", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# --- Import and register routers ---
from routers.auth import router as auth_router
from routers.settings import router as settings_router
from routers.system import router as system_router
from routers.models import router as models_router
from routers.hub import router as hub_router
from routers.inference import router as inference_router
from routers.chat import router as chat_router
from routers.images import router as images_router
from routers.video import router as video_router
from routers.audio import router as audio_router
from routers.train import router as train_router
from routers.datasets import router as datasets_router
from routers.rag import router as rag_router
from routers.research import router as research_router
from routers.export import router as export_router
from routers.providers import router as providers_router
from routers.prompts import router as prompts_router
from routers.mcp import router as mcp_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(system_router, prefix="/api/system", tags=["system"])
app.include_router(models_router, prefix="/api/models", tags=["models"])
app.include_router(hub_router, prefix="/api/hub", tags=["hub"])
app.include_router(inference_router, prefix="/api/inference", tags=["inference"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(chat_router, prefix="/v1", tags=["v1"])
app.include_router(images_router)
app.include_router(video_router)
app.include_router(audio_router)
app.include_router(train_router)
app.include_router(datasets_router)
app.include_router(rag_router)
app.include_router(research_router)
app.include_router(export_router)
app.include_router(providers_router)
app.include_router(prompts_router)
app.include_router(mcp_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


import json as _json
import subprocess as _sp
import re as _re
import time as _time
from datetime import datetime, timezone


def _run_cmd(args: list[str], timeout: int = 10) -> str:
    try:
        r = _sp.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _get_installed_version(package: str) -> str:
    out = _run_cmd(["pip", "show", package])
    for line in out.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return ""


def _get_latest_pypi_version(package: str) -> str:
    out = _run_cmd(["pip", "index", "versions", package], timeout=15)
    if not out:
        return ""
    m = _re.search(r"LATEST:\s*(\S+)", out)
    if m:
        return m.group(1)
    parts = out.split()
    return parts[1] if len(parts) >= 2 else ""


def _get_git_remote_version() -> str:
    cwd = str(Path(__file__).parent.parent)
    tag = _run_cmd(["git", "-C", cwd, "describe", "--tags", "--abbrev=0"], timeout=5)
    if tag:
        return tag.lstrip("v")
    commit = _run_cmd(["git", "-C", cwd, "rev-parse", "--short", "HEAD"], timeout=5)
    return f"0.0.0+{commit}" if commit else ""


@app.get("/api/llama/update-status")
def llama_update_status(force_refresh: bool = False):
    installed = _get_installed_version("llama-cpp-python")
    latest = _get_latest_pypi_version("llama-cpp-python") if force_refresh or not installed else installed
    return {
        "supported": True,
        "update_available": bool(installed and latest and installed != latest),
        "installed_tag": installed or None,
        "latest_tag": latest or installed or "0.1.0",
        "update_size_bytes": 0,
        "job": {
            "state": "idle",
            "operation": None,
            "requested_backend": None,
            "message": "",
            "from_tag": None,
            "to_tag": None,
            "reload_required": None,
            "error": None,
            "progress": None,
            "started_at": None,
            "finished_at": None,
        },
    }


@app.get("/api/studio/update-status")
def studio_update_status():
    current = _get_git_remote_version() or "0.1.0"
    return {
        "can_show_web_notification": False,
        "update_available": False,
        "install_source": "pypi",
        "latest_version": current,
        "current_version": current,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/shutdown")
def shutdown_server():
    import os, signal
    os.kill(os.getpid(), signal.SIGTERM)
    return {"ok": True}


@app.get("/api/llama/backend")
def llama_backend_get():
    installed = _get_installed_version("llama-cpp-python")
    backends = []
    if installed:
        backends.append({"backend": "llama-cpp", "available": True, "resolved_backend": "llama-cpp", "release_tag": installed, "download_size_bytes": 0})
    else:
        backends.append({"backend": "llama-cpp", "available": False, "resolved_backend": None, "release_tag": None, "download_size_bytes": 0})
    return {
        "supported": True,
        "reason": None,
        "env_backend": None,
        "backend": "llama-cpp" if installed else None,
        "backend_request": "auto",
        "selection_applied": True,
        "installed_tag": installed or None,
        "options": backends,
        "job": {"state": "idle", "operation": None, "requested_backend": None, "message": "", "error": None, "progress": None, "reload_required": None, "started_at": None, "finished_at": None},
    }


@app.post("/api/llama/backend")
def llama_backend_post(backend: str = "auto"):
    return {"started": False, "reason": "Backend switching not yet implemented", "message": "Use auto-detection", "job": {"state": "idle", "operation": None, "requested_backend": None, "message": "", "error": None, "progress": None, "reload_required": None, "started_at": None, "finished_at": None}}


@app.get("/api/llama/update")
@app.post("/api/llama/update")
def llama_update():
    installed = _get_installed_version("llama-cpp-python")
    latest = _get_latest_pypi_version("llama-cpp-python")
    if not installed:
        return {"started": False, "reason": "llama-cpp-python is not installed", "message": "Install llama-cpp-python first", "job": {"state": "error", "operation": "update", "requested_backend": None, "message": "Not installed", "error": "Package not found", "progress": None, "reload_required": None, "started_at": None, "finished_at": None}}
    if installed == latest:
        return {"started": False, "reason": "Already up to date", "message": f"Running {installed}", "job": {"state": "idle", "operation": None, "requested_backend": None, "message": "", "error": None, "progress": None, "reload_required": None, "started_at": None, "finished_at": None}}
    _run_cmd(["pip", "install", "--upgrade", "llama-cpp-python"], timeout=120)
    new_ver = _get_installed_version("llama-cpp-python")
    return {
        "started": True,
        "reason": None,
        "message": f"Updated {installed} → {new_ver}",
        "job": {
            "state": "success",
            "operation": "update",
            "requested_backend": None,
            "message": f"Updated {installed} → {new_ver}",
            "from_tag": installed,
            "to_tag": new_ver,
            "reload_required": True,
            "error": None,
            "progress": 1.0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        },
    }


@app.get("/api/picker/validate-chat-template")
@app.post("/api/picker/validate-chat-template")
def validate_chat_template(body: dict | None = None):
    template = (body or {}).get("template", "")
    if not template:
        return {"valid": False, "error": "Template is empty"}
    depth = 0
    for i, ch in enumerate(template):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return {"valid": False, "error": f"Unmatched '}}' at position {i}"}
    if depth > 0:
        return {"valid": False, "error": f"Unmatched '{{' — {depth} unclosed block(s)"}
    blocks = {"if": 0, "for": 0, "set": 0}
    for tag in blocks:
        blocks[tag] = len(_re.findall(r"{%\s*" + tag + r"\b", template))
    for tag, count in blocks.items():
        end_count = len(_re.findall(r"{%\s*end" + tag + r"\s*%}", template))
        if count != end_count:
            return {"valid": False, "error": f"Unclosed '{tag}' block ({count} open, {end_count} close)"}
    return {"valid": True, "error": None}


@app.get("/api/youtube/transcript")
@app.post("/api/youtube/transcript")
def youtube_transcript():
    raise HTTPException(status_code=501, detail="youtube_transcript_api package not installed. Run: pip install youtube-transcript-api")


@app.get("/api/studio/release-notes")
async def release_notes(version: str = "", refresh: bool = False):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.github.com/repos/Omii-004/FlickerX/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if resp.status_code != 200:
                return {
                    "version": version or "0.0.0",
                    "markdown": None,
                    "heading": None,
                    "tag": None,
                    "html_url": None,
                    "matched": False,
                    "truncated": False,
                    "source": None,
                    "release_notes_url": None,
                    "error": f"GitHub API returned {resp.status_code}",
                }
            release = resp.json()
            tag = release.get("tag_name", "")
            body = release.get("body") or None
            return {
                "version": version or "0.0.0",
                "markdown": body,
                "heading": release.get("name"),
                "tag": tag,
                "html_url": release.get("html_url"),
                "matched": tag == version if version else False,
                "truncated": False,
                "source": "github",
                "release_notes_url": release.get("html_url"),
                "error": None,
            }
    except Exception as exc:
        return {
            "version": version or "0.0.0",
            "markdown": None,
            "heading": None,
            "tag": None,
            "html_url": None,
            "matched": False,
            "truncated": False,
            "source": None,
            "release_notes_url": None,
            "error": str(exc),
        }


@app.get("/api/system")
def system_info():
    import time as _time
    import platform
    import psutil
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_freq = psutil.cpu_freq()
    gpus = []
    try:
        r = _sp.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            for line in r.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "name": parts[0],
                        "memory_total_gb": round(int(parts[1]) / 1024, 2),
                        "vram_used_gb": round(int(parts[2]) / 1024, 2),
                        "vram_free_gb": round(int(parts[3]) / 1024, 2),
                        "vram_utilization_pct": int(parts[4]),
                    })
    except Exception:
        pass
    device_backend = "cpu"
    if gpus and gpus[0].get("name", "No GPU") != "No GPU detected":
        device_backend = "cuda"
    proc = psutil.Process()
    ml_torch = ""
    ml_transformers = ""
    try:
        import torch
        ml_torch = getattr(torch, "__version__", "")
    except Exception:
        pass
    try:
        import transformers
        ml_transformers = getattr(transformers, "__version__", "")
    except Exception:
        pass
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "device_backend": device_backend,
        "uptime_seconds": int(_time.time() - proc.create_time()),
        "cpu": {
            "logical_count": psutil.cpu_count() or 0,
            "physical_count": psutil.cpu_count(logical=False) or 0,
            "usage_percent": psutil.cpu_percent(interval=0),
            "frequency_mhz": round(cpu_freq.current) if cpu_freq else None,
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent,
            "process_used_mb": round(proc.memory_info().rss / (1024**2)),
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round(disk.percent, 1),
        },
        "gpu": {
            "available": bool(gpus),
            "devices": gpus,
        },
        "ml_packages": {
            "torch": ml_torch or None,
            "transformers": ml_transformers or None,
        },
    }


# Serve frontend static files (if built)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
FRONTEND_DIST_RESOLVED = FRONTEND_DIST.resolve()


class _ImmutableStaticFiles(StaticFiles):
    """Serve Vite's content-hashed assets without browser revalidation."""

    def file_response(self, full_path, stat_result, scope, status_code=200):
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def _build_index_html():
    return (FRONTEND_DIST / "index.html").read_bytes()


def _frontend_request_allowed(request: Request) -> bool:
    return True  # ponytail: no tunnel restriction, add when LAN/Cloudflare support exists


if FRONTEND_DIST.exists():
    _assets_dir = FRONTEND_DIST / "assets"
    if _assets_dir.exists():
        app.mount("/assets", _ImmutableStaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/")
    async def serve_root(request: Request):
        if not _frontend_request_allowed(request):
            return Response(status_code=404)
        return HTMLResponse(
            content=_build_index_html(),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        if full_path.startswith(("api/", "v1/")):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API endpoint not found")
        if not _frontend_request_allowed(request):
            return Response(status_code=404)

        file_path = (FRONTEND_DIST / full_path).resolve()
        if not file_path.is_relative_to(FRONTEND_DIST_RESOLVED):
            return Response(status_code=403)
        if file_path.is_file():
            return FileResponse(file_path)

        return HTMLResponse(
            content=_build_index_html(),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )


def main():
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")


if __name__ == "__main__":
    main()
