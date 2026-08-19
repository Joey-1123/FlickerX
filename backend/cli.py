"""FlickerX CLI — single-command startup."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file to find the repo root (has frontend/ and backend/)."""
    here = Path(__file__).resolve().parent
    for candidate in [here, here.parent, here.parent.parent]:
        if (candidate / "frontend").is_dir() and (candidate / "backend").is_dir():
            return candidate
    return here.parent  # fallback


def _frontend_dist(project_root: Path) -> Path:
    return project_root / "frontend" / "dist"


def _build_frontend(project_root: Path) -> None:
    """Build frontend if dist/ doesn't exist."""
    dist = _frontend_dist(project_root)
    if dist.exists() and (dist / "index.html").exists():
        return

    frontend_dir = project_root / "frontend"
    if not (frontend_dir / "package.json").exists():
        print("Warning: no frontend/package.json, skipping build", file=sys.stderr)
        return

    print("Building frontend...", flush=True)
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(frontend_dir),
        capture_output=False,
    )
    if result.returncode != 0:
        print("Error: frontend build failed", file=sys.stderr)
        sys.exit(1)


def _run_production(host: str, port: int, project_root: Path) -> None:
    """Single-process: serve frontend + backend on one port."""
    _build_frontend(project_root)
    backend_dir = project_root / "backend"
    os.chdir(str(backend_dir))
    sys.path.insert(0, str(backend_dir))

    import uvicorn
    print(f"FlickerX Studio running on http://{host}:{port}/", flush=True)
    uvicorn.run("main:app", host=host, port=port, log_level="info")


def _run_dev(project_root: Path) -> None:
    """Two-process: backend + Vite dev server with hot reload."""
    result = subprocess.run(
        ["npm", "run", "dev"],
        cwd=str(project_root),
    )
    sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flickerx",
        description="FlickerX Studio — single-command startup",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")
    parser.add_argument("--dev", action="store_true", help="Development mode (Vite + backend)")
    args = parser.parse_args()

    project_root = _find_project_root()

    if args.dev:
        _run_dev(project_root)
    else:
        _run_production(args.host, args.port, project_root)


if __name__ == "__main__":
    main()
