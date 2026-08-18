"""FlickerX Studio — FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# Serve frontend static files (if built)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


def main():
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")


if __name__ == "__main__":
    main()
