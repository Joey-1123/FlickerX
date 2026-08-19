"""Hub router — search, download, local models, cache management, GGUF metadata."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import CACHE_DIR, MODELS_DIR

router = APIRouter()

# In-memory download state
_download_progress: dict[str, dict] = {}
_download_lock = threading.Lock()


class DownloadRequest(BaseModel):
    repo_id: str
    gguf_variant: str | None = None
    hf_token: str | None = None
    use_xet: bool | None = None
    scope_id: str | None = None
    files: list[str] | None = None
    transport_mode: str | None = None


class CancelDownloadRequest(BaseModel):
    repo_id: str
    gguf_variant: str | None = None
    generation: int | None = None


# --- Search ---

@router.get("/search")
def search_models(q: str = "", owner: str = "all", limit: int = 20):
    from huggingface_hub import list_models
    try:
        filters = {}
        if q:
            filters["search"] = q
        if owner and owner != "all":
            filters["author"] = owner
        models = list(list_models(limit=limit, sort="downloads", direction=-1, **filters))
        results = []
        for m in models:
            results.append({
                "id": m.id,
                "author": m.author or "",
                "downloads": m.downloads or 0,
                "likes": m.likes or 0,
                "tags": m.tags or [],
                "pipeline_tag": m.pipeline_tag or "",
                "last_modified": m.last_modified.isoformat() if m.last_modified else None,
            })
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"results": [], "total": 0, "error": str(e)}


@router.get("/owners")
def list_owners():
    return {"owners": []}


# --- Cache ---

@router.get("/cached-gguf")
def cached_gguf():
    cached = []
    if CACHE_DIR.exists():
        for entry in CACHE_DIR.iterdir():
            if entry.is_dir():
                gguf_files = list(entry.glob("**/*.gguf"))
                if gguf_files:
                    cached.append({
                        "repo_id": entry.name,
                        "path": str(entry),
                        "files": [{"name": f.name, "size": f.stat().st_size} for f in gguf_files],
                        "total_size": sum(f.stat().st_size for f in gguf_files),
                    })
    return {"cached": cached}


@router.get("/cached-models")
def cached_models():
    cached = []
    if CACHE_DIR.exists():
        for entry in CACHE_DIR.iterdir():
            if entry.is_dir():
                cached.append({
                    "repo_id": entry.name,
                    "path": str(entry),
                    "size": sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()),
                })
    return {"cached": cached}


@router.get("/cached-model-catalog")
def cached_model_catalog():
    return {"catalog": []}


# --- Downloads ---

@router.post("/download")
def start_download(req: DownloadRequest, user: dict = Depends(get_current_user)):
    job_key = f"{req.repo_id}:{req.gguf_variant or 'default'}"
    with _download_lock:
        _download_progress[job_key] = {
            "repo_id": req.repo_id,
            "variant": req.gguf_variant,
            "state": "starting",
            "progress": 0.0,
            "downloaded_bytes": 0,
            "expected_bytes": 0,
            "started_at": time.time(),
        }

    def _background_download():
        try:
            from huggingface_hub import snapshot_download
            with _download_lock:
                _download_progress[job_key]["state"] = "downloading"
            path = snapshot_download(
                repo_id=req.repo_id,
                local_dir=str(MODELS_DIR / req.repo_id.replace("/", "_")),
                token=req.hf_token,
            )
            with _download_lock:
                _download_progress[job_key].update({"state": "completed", "progress": 1.0, "path": path})
        except Exception as e:
            with _download_lock:
                _download_progress[job_key].update({"state": "failed", "error": str(e)})

    threading.Thread(target=_background_download, daemon=True).start()
    return {"state": "started", "accepted": True, "job_key": job_key}


@router.post("/download/cancel")
def cancel_download(req: CancelDownloadRequest, user: dict = Depends(get_current_user)):
    job_key = f"{req.repo_id}:{req.gguf_variant or 'default'}"
    with _download_lock:
        if job_key in _download_progress:
            _download_progress[job_key]["state"] = "cancelled"
    return {"job_key": job_key, "state": "cancelled"}


@router.get("/download-progress")
def download_progress(repo_id: str, expected_bytes: int = 0):
    job_key = repo_id
    with _download_lock:
        progress = _download_progress.get(job_key, _download_progress.get(f"{repo_id}:default", {}))
    return {
        "downloaded_bytes": progress.get("downloaded_bytes", 0),
        "expected_bytes": progress.get("expected_bytes", expected_bytes),
        "progress": progress.get("progress", 0.0),
        "state": progress.get("state", "unknown"),
    }


@router.get("/download-status")
def download_status(repo_id: str, gguf_variant: str = ""):
    job_key = f"{repo_id}:{gguf_variant or 'default'}"
    with _download_lock:
        progress = _download_progress.get(job_key, {})
    return {
        "state": progress.get("state", "idle"),
        "progress": progress.get("progress", 0.0),
    }


@router.get("/active-downloads")
def active_downloads(repo_id: str = ""):
    with _download_lock:
        active = [v for v in _download_progress.values() if v.get("state") in ("starting", "downloading")]
    return {"downloads": active}


@router.get("/gguf-download-progress")
def gguf_download_progress(repo_id: str, variant: str = "", expected_bytes: int = 0):
    return download_progress(repo_id, expected_bytes)


@router.get("/transport-status")
def transport_status(repo_id: str, gguf_variant: str = ""):
    return {"mode": "default", "available": True}


# --- Local models ---

@router.get("/local")
def list_local_models():
    models = []
    if MODELS_DIR.exists():
        for entry in MODELS_DIR.iterdir():
            if entry.is_dir():
                gguf_files = list(entry.glob("**/*.gguf"))
                models.append({
                    "name": entry.name,
                    "path": str(entry),
                    "type": "gguf" if gguf_files else "directory",
                    "size_bytes": sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()),
                    "files": [f.name for f in gguf_files],
                })
    return {"models": models, "models_dir": str(MODELS_DIR)}


@router.post("/local-model-eject")
def eject_local_model(body: dict, user: dict = Depends(get_current_user)):
    return {"ok": True}


@router.post("/local-model-rename")
def rename_local_model(body: dict, user: dict = Depends(get_current_user)):
    return {"ok": True}


@router.delete("/delete-cached")
def delete_cached_model(body: dict, user: dict = Depends(get_current_user)):
    return {"ok": True}


@router.post("/delete-impact")
def delete_impact(body: dict, user: dict = Depends(get_current_user)):
    return None


@router.get("/orphan-companions")
def orphan_companions():
    return {"companions": [], "total_bytes": 0}


# --- Sync ---

@router.post("/sync")
def sync_hub(user: dict = Depends(get_current_user)):
    return {"status": "synced"}


@router.post("/sync/cancel")
def cancel_sync(user: dict = Depends(get_current_user)):
    return {"ok": True}


# --- Scan folders ---

@router.get("/scan-folders")
def scan_folders():
    folders = []
    if MODELS_DIR.exists():
        folders.append({"id": "default", "path": str(MODELS_DIR), "name": "Default"})
    return {"folders": folders}


class AddScanFolderRequest(BaseModel):
    path: str


@router.post("/scan-folders")
def add_scan_folder(req: AddScanFolderRequest, user: dict = Depends(get_current_user)):
    p = Path(req.path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    return {"id": str(p.name), "path": str(p), "name": p.name}


@router.delete("/scan-folders/{folder_id}")
def remove_scan_folder(folder_id: str, user: dict = Depends(get_current_user)):
    return {"ok": True}


# --- GGUF metadata ---

@router.get("/gguf-metadata")
def gguf_metadata(repo_id: str):
    return {"metadata": {}, "repo_id": repo_id}


# --- Insights ---

@router.get("/insights")
def hub_insights():
    return {"recent_searches": [], "popular_models": []}


# --- Pinned models ---

@router.get("/pinned-models")
def pinned_models():
    return {"pinned": []}


# --- Recent searches ---

@router.get("/recent-searches")
def recent_searches():
    return {"searches": []}


# --- Transport pref ---

@router.get("/transport-pref")
def transport_pref():
    return {"mode": "default"}


# --- Download paths ---

@router.get("/download-paths")
def download_paths():
    return {"paths": [str(MODELS_DIR)]}


@router.get("/hidden-models")
def hidden_models():
    return {"models": []}
