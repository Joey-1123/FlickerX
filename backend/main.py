"""FlickerX Studio — FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from middleware import SecurityHeadersMiddleware, BodySizeMiddleware, RequestLoggingMiddleware

from config import ensure_dirs, HOST, PORT, STUDIO_HOME
from database import init_auth_db, init_studio_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    init_auth_db()
    init_studio_db()
    logger.info("flickerx_backend_started", host=HOST, port=PORT, data_dir=str(STUDIO_HOME))
    yield
    logger.info("flickerx_backend_stopped")


app = FastAPI(title="FlickerX Studio", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/api/llama/update-status")
def llama_update_status(force_refresh: bool = False):
    return {"update_available": False, "current_version": "0.1.0", "latest_version": "0.1.0"}


@app.get("/api/studio/update-status")
def studio_update_status():
    return {"update_available": False, "current_version": "0.1.0", "latest_version": "0.1.0"}


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
