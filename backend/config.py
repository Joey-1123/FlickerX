"""FlickerX Studio configuration."""

from __future__ import annotations

import os
from pathlib import Path

import structlog

logger = structlog.get_logger()

STUDIO_HOME = Path(os.environ.get("FLICKERX_STUDIO_HOME", Path.home() / ".flickerx" / "studio"))
DATA_DIR = STUDIO_HOME / "data"
AUTH_DB = DATA_DIR / "auth.db"
STUDIO_DB = DATA_DIR / "studio.db"
MODELS_DIR = STUDIO_HOME / "models"
CACHE_DIR = STUDIO_HOME / "cache"
LOGS_DIR = STUDIO_HOME / "logs"

HOST = os.environ.get("FLICKERX_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLICKERX_PORT", "8080"))
SECRET_KEY = os.environ.get("FLICKERX_SECRET_KEY", "flickerx-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def ensure_dirs() -> None:
    for d in (STUDIO_HOME, DATA_DIR, MODELS_DIR, CACHE_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
