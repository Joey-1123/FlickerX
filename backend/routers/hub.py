"""Hub router — search, download, local models, cache management, GGUF metadata."""

from __future__ import annotations

import json
import os
import struct
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import CACHE_DIR, MODELS_DIR, STUDIO_HOME

router = APIRouter()

# In-memory download state
_download_progress: dict[str, dict] = {}
_download_lock = threading.Lock()
_sync_cancelled = False

# Persistent state files
_SCAN_FOLDERS_FILE = STUDIO_HOME / "scan_folders.json"
_PINNED_MODELS_FILE = STUDIO_HOME / "pinned_models.json"
_HIDDEN_MODELS_FILE = STUDIO_HOME / "hidden_models.json"
_RECENT_SEARCHES_FILE = STUDIO_HOME / "recent_searches.json"
_DOWNLOAD_HISTORY_FILE = STUDIO_HOME / "download_history.json"


def _read_json_file(path: Path, default=None):
    if default is None:
        default = []
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _write_json_file(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


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
        # Record search if non-empty
        if q:
            _record_search(q)
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"results": [], "total": 0, "error": str(e)}


def _record_search(query_str: str) -> None:
    searches = _read_json_file(_RECENT_SEARCHES_FILE, [])
    searches = [s for s in searches if s.get("query") != query_str]
    searches.insert(0, {"query": query_str, "timestamp": time.time()})
    _write_json_file(_RECENT_SEARCHES_FILE, searches[:20])


@router.get("/owners")
def list_owners():
    from huggingface_hub import HfApi
    try:
        api = HfApi()
        models = list(list_models(limit=100, sort="downloads", direction=-1))
        owners = {}
        for m in models:
            if m.author:
                owners[m.author] = owners.get(m.author, 0) + 1
        sorted_owners = sorted(owners.items(), key=lambda x: -x[1])[:50]
        return {"owners": [{"name": name, "count": count} for name, count in sorted_owners]}
    except Exception:
        return {"owners": []}


# --- Cache ---

@router.get("/cached-gguf")
def cached_gguf():
    cached = []
    for cache_dir in (CACHE_DIR, MODELS_DIR):
        if cache_dir.exists():
            for entry in cache_dir.iterdir():
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
    for cache_dir in (CACHE_DIR, MODELS_DIR):
        if cache_dir.exists():
            for entry in cache_dir.iterdir():
                if entry.is_dir():
                    size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
                    if size > 0:
                        cached.append({
                            "repo_id": entry.name,
                            "path": str(entry),
                            "size": size,
                        })
    return {"cached": cached}


@router.get("/cached-model-catalog")
def cached_model_catalog():
    catalog = []
    for cache_dir in (CACHE_DIR, MODELS_DIR):
        if not cache_dir.exists():
            continue
        for entry in cache_dir.iterdir():
            if not entry.is_dir():
                continue
            info = {"repo_id": entry.name, "path": str(entry), "files": [], "config": None}
            config_path = entry / "config.json"
            if config_path.exists():
                try:
                    info["config"] = json.loads(config_path.read_text())
                except Exception:
                    pass
            for f in entry.rglob("*"):
                if f.is_file():
                    info["files"].append({"name": f.name, "size": f.stat().st_size, "path": str(f)})
            info["total_size"] = sum(f["size"] for f in info["files"])
            if info["files"]:
                catalog.append(info)
    return {"catalog": catalog}


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
            _record_download(req.repo_id, "completed")
        except Exception as e:
            with _download_lock:
                _download_progress[job_key].update({"state": "failed", "error": str(e)})
            _record_download(req.repo_id, "failed")

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


def _record_download(repo_id: str, status: str) -> None:
    history = _read_json_file(_DOWNLOAD_HISTORY_FILE, [])
    history.append({"repo_id": repo_id, "status": status, "timestamp": time.time()})
    _write_json_file(_DOWNLOAD_HISTORY_FILE, history[-100:])


@router.get("/transport-status")
def transport_status(repo_id: str, gguf_variant: str = ""):
    has_aria2 = os.system("which aria2c > /dev/null 2>&1") == 0
    has_git_lfs = os.system("which git-lfs > /dev/null 2>&1") == 0
    mode = "aria2" if has_aria2 else ("git-lfs" if has_git_lfs else "default")
    return {"mode": mode, "available": True, "aria2c": has_aria2, "git_lfs": has_git_lfs}


# --- Local models ---

@router.get("/local")
def list_local_models():
    models = []
    if MODELS_DIR.exists():
        for entry in MODELS_DIR.iterdir():
            if entry.is_dir():
                gguf_files = list(entry.glob("**/*.gguf"))
                models.append({
                    "id": entry.name,
                    "display_name": entry.name,
                    "source": "models_dir",
                    "name": entry.name,
                    "path": str(entry),
                    "type": "gguf" if gguf_files else "directory",
                    "size_bytes": sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()),
                    "files": [f.name for f in gguf_files],
                })
    return {"models": models, "models_dir": str(MODELS_DIR)}


@router.post("/local-model-eject")
def eject_local_model(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "No path provided")
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Model not found")
    # Safety: only delete within MODELS_DIR or CACHE_DIR
    if not (p.resolve().is_relative_to(MODELS_DIR.resolve()) or p.resolve().is_relative_to(CACHE_DIR.resolve())):
        raise HTTPException(403, "Cannot delete outside models/cache directories")
    import shutil
    shutil.rmtree(str(p))
    return {"ok": True, "deleted": str(p)}


@router.post("/local-model-rename")
def rename_local_model(body: dict, user: dict = Depends(get_current_user)):
    old_path = body.get("path", "")
    new_name = body.get("name", "")
    if not old_path or not new_name:
        raise HTTPException(400, "path and name required")
    old = Path(old_path)
    if not old.exists():
        raise HTTPException(404, "Model not found")
    if "/" in new_name or "\\" in new_name:
        raise HTTPException(400, "Name cannot contain path separators")
    new = old.parent / new_name
    if new.exists():
        raise HTTPException(409, "A model with that name already exists")
    old.rename(new)
    return {"ok": True, "path": str(new), "old_path": str(old)}


@router.delete("/delete-cached")
def delete_cached_model(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "No path provided")
    p = Path(path)
    if not p.exists():
        return {"ok": True, "message": "Already deleted"}
    if not (p.resolve().is_relative_to(MODELS_DIR.resolve()) or p.resolve().is_relative_to(CACHE_DIR.resolve())):
        raise HTTPException(403, "Cannot delete outside models/cache directories")
    import shutil
    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    shutil.rmtree(str(p))
    return {"ok": True, "deleted_bytes": size}


@router.post("/delete-impact")
def delete_impact(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if not path:
        return {"ok": True, "impact": {}}
    p = Path(path)
    if not p.exists():
        return {"ok": True, "impact": {"exists": False}}
    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
    file_count = sum(1 for _ in p.rglob("*") if _.is_file()) if p.is_dir() else 1
    # Check for adapters that reference this model
    references = []
    for model_dir in MODELS_DIR.iterdir() if MODELS_DIR.exists() else []:
        if model_dir.is_dir():
            adapter_cfg = model_dir / "adapter_config.json"
            if adapter_cfg.exists():
                try:
                    cfg = json.loads(adapter_cfg.read_text())
                    if cfg.get("base_model_name_or_path", "") in str(p):
                        references.append(model_dir.name)
                except Exception:
                    pass
    return {"ok": True, "impact": {
        "exists": True,
        "size_bytes": size,
        "file_count": file_count,
        "references": references,
        "has_references": len(references) > 0,
    }}


@router.get("/orphan-companions")
def orphan_companions():
    orphans = []
    total_bytes = 0
    for cache_dir in (CACHE_DIR, MODELS_DIR):
        if not cache_dir.exists():
            continue
        for entry in cache_dir.iterdir():
            if not entry.is_dir():
                continue
            has_model_file = False
            companion_files = []
            for f in entry.rglob("*"):
                if f.is_file():
                    if f.suffix in (".gguf", ".safetensors", ".bin", ".pt", ".pth", ".onnx"):
                        has_model_file = True
                    elif f.suffix in (".json", ".txt", ".py", ".model", ".tiktoken"):
                        companion_files.append(f)
            if not has_model_file and companion_files:
                for cf in companion_files:
                    sz = cf.stat().st_size
                    total_bytes += sz
                    orphans.append({"path": str(cf), "name": cf.name, "size_bytes": sz, "parent": entry.name})
    return {"companions": orphans, "total_bytes": total_bytes}


# --- Sync ---

@router.post("/sync")
def sync_hub(user: dict = Depends(get_current_user)):
    global _sync_cancelled
    _sync_cancelled = False
    models_found = []
    scan_dirs = [MODELS_DIR, CACHE_DIR]
    # Add user-configured scan folders
    custom_folders = _read_json_file(_SCAN_FOLDERS_FILE, [])
    for folder in custom_folders:
        p = Path(folder.get("path", ""))
        if p.exists() and p.is_dir():
            scan_dirs.append(p)

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for entry in scan_dir.iterdir():
            if _sync_cancelled:
                return {"status": "cancelled", "models": models_found}
            if not entry.is_dir():
                continue
            gguf_files = list(entry.glob("**/*.gguf"))
            safetensor_files = list(entry.glob("**/*.safetensors"))
            config_path = entry / "config.json"
            config = None
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text())
                except Exception:
                    pass
            models_found.append({
                "id": entry.name,
                "display_name": entry.name,
                "source": "models_dir",
                "name": entry.name,
                "path": str(entry),
                "source_dir": str(scan_dir),
                "type": "gguf" if gguf_files else ("safetensors" if safetensor_files else "directory"),
                "has_config": config is not None,
                "architecture": config.get("architectures", [None])[0] if config and "architectures" in config else None,
                "size_bytes": sum(f.stat().st_size for f in entry.rglob("*") if f.is_file()),
            })

    return {"status": "synced", "models": models_found, "count": len(models_found), "scan_dirs": [str(d) for d in scan_dirs]}


@router.post("/sync/cancel")
def cancel_sync(user: dict = Depends(get_current_user)):
    global _sync_cancelled
    _sync_cancelled = True
    return {"ok": True, "message": "Sync cancellation requested"}


# --- Scan folders ---

@router.get("/scan-folders")
def scan_folders():
    folders = []
    if MODELS_DIR.exists():
        folders.append({"id": "default", "path": str(MODELS_DIR), "name": "Default"})
    custom = _read_json_file(_SCAN_FOLDERS_FILE, [])
    folders.extend(custom)
    return {"folders": folders}


class AddScanFolderRequest(BaseModel):
    path: str
    name: str | None = None


@router.post("/scan-folders")
def add_scan_folder(req: AddScanFolderRequest, user: dict = Depends(get_current_user)):
    p = Path(req.path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    folder_id = p.name
    custom = _read_json_file(_SCAN_FOLDERS_FILE, [])
    # Don't duplicate
    if any(f["id"] == folder_id for f in custom):
        return {"id": folder_id, "path": str(p), "name": req.name or p.name}
    entry = {"id": folder_id, "path": str(p), "name": req.name or p.name}
    custom.append(entry)
    _write_json_file(_SCAN_FOLDERS_FILE, custom)
    return entry


@router.post("/token/validate")
def validate_hf_token(body: dict):
    token = body.get("token", "")
    if not token:
        return {"valid": False, "error": "No token provided"}
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        whoami = api.whoami()
        return {"valid": True, "user": whoami.get("name", ""), "type": whoami.get("type", "")}
    except Exception as e:
        return {"valid": False, "error": str(e)[:200]}


@router.delete("/scan-folders/{folder_id}")
def remove_scan_folder(folder_id: str, user: dict = Depends(get_current_user)):
    if folder_id == "default":
        raise HTTPException(400, "Cannot remove default folder")
    custom = _read_json_file(_SCAN_FOLDERS_FILE, [])
    before = len(custom)
    custom = [f for f in custom if f["id"] != folder_id]
    if len(custom) == before:
        raise HTTPException(404, "Folder not found")
    _write_json_file(_SCAN_FOLDERS_FILE, custom)
    return {"ok": True, "deleted": folder_id}


# --- GGUF metadata ---

@router.get("/gguf-metadata")
def gguf_metadata(repo_id: str):
    # Try to find the model in MODELS_DIR
    model_dir = MODELS_DIR / repo_id.replace("/", "_")
    if not model_dir.exists():
        # Try exact name
        model_dir = MODELS_DIR / repo_id
    if not model_dir.exists():
        # Search all dirs
        for d in MODELS_DIR.iterdir() if MODELS_DIR.exists() else []:
            if d.is_dir() and repo_id.replace("/", "_") in d.name:
                model_dir = d
                break

    if not model_dir.exists():
        return {"metadata": {}, "repo_id": repo_id, "error": "Model directory not found"}

    # Try config.json first
    config_path = model_dir / "config.json"
    metadata = {"repo_id": repo_id}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            metadata["architecture"] = config.get("architectures", [None])[0]
            metadata["model_type"] = config.get("model_type")
            metadata["vocab_size"] = config.get("vocab_size")
            metadata["hidden_size"] = config.get("hidden_size")
            metadata["num_hidden_layers"] = config.get("num_hidden_layers")
            metadata["num_attention_heads"] = config.get("num_attention_heads")
            metadata["max_position_embeddings"] = config.get("max_position_embeddings")
            metadata["torch_dtype"] = config.get("torch_dtype")
        except Exception:
            pass

    # Try GGUF header
    gguf_files = list(model_dir.glob("**/*.gguf"))
    if gguf_files:
        gguf = gguf_files[0]
        metadata["gguf_file"] = gguf.name
        metadata["gguf_size"] = gguf.stat().st_size
        metadata["quantization"] = _parse_quant_from_filename(gguf.name)
        # Try reading GGUF magic and version
        try:
            with open(gguf, "rb") as f:
                magic = f.read(4)
                if magic == b"GGUF":
                    version = struct.unpack("<I", f.read(4))[0]
                    metadata["gguf_version"] = version
        except Exception:
            pass
    else:
        metadata["gguf_file"] = None

    # List all files
    files = []
    for f in model_dir.rglob("*"):
        if f.is_file():
            files.append({"name": f.name, "size": f.stat().st_size, "relative": str(f.relative_to(model_dir))})
    metadata["files"] = files
    metadata["total_size"] = sum(f["size"] for f in files)

    return {"metadata": metadata, "repo_id": repo_id}


def _parse_quant_from_filename(name: str) -> str | None:
    lower = name.lower()
    for q in ("q2_k", "q3_k_s", "q3_k_m", "q3_k_l", "q4_0", "q4_k_s", "q4_k_m",
              "q5_0", "q5_k_s", "q5_k_m", "q6_k", "q8_0", "f16", "f32"):
        if q in lower:
            return q.upper()
    return None


# --- Insights ---

@router.get("/insights")
def hub_insights():
    recent_searches = _read_json_file(_RECENT_SEARCHES_FILE, [])[:10]
    download_history = _read_json_file(_DOWNLOAD_HISTORY_FILE, [])
    # Count downloads per repo
    download_counts: dict[str, int] = {}
    for entry in download_history:
        repo = entry.get("repo_id", "")
        download_counts[repo] = download_counts.get(repo, 0) + 1
    popular = sorted(download_counts.items(), key=lambda x: -x[1])[:10]
    return {
        "recent_searches": recent_searches,
        "popular_models": [{"repo_id": r, "downloads": c} for r, c in popular],
        "total_downloads": len(download_history),
    }


# --- Pinned models ---

@router.get("/pinned-models")
def pinned_models():
    pins = _read_json_file(_PINNED_MODELS_FILE, [])
    return {"pinned": pins}


class PinModelRequest(BaseModel):
    repo_id: str
    name: str | None = None
    path: str | None = None


@router.post("/pinned-models")
def pin_model(req: PinModelRequest, user: dict = Depends(get_current_user)):
    pins = _read_json_file(_PINNED_MODELS_FILE, [])
    if any(p["repo_id"] == req.repo_id for p in pins):
        return {"ok": True, "pinned": pins}
    pins.append({"repo_id": req.repo_id, "name": req.name or req.repo_id, "path": req.path, "pinned_at": time.time()})
    _write_json_file(_PINNED_MODELS_FILE, pins)
    return {"ok": True, "pinned": pins}


@router.delete("/pinned-models/{repo_id:path}")
def unpin_model(repo_id: str, user: dict = Depends(get_current_user)):
    pins = _read_json_file(_PINNED_MODELS_FILE, [])
    pins = [p for p in pins if p["repo_id"] != repo_id]
    _write_json_file(_PINNED_MODELS_FILE, pins)
    return {"ok": True, "pinned": pins}


# --- Recent searches ---

@router.get("/recent-searches")
def recent_searches():
    searches = _read_json_file(_RECENT_SEARCHES_FILE, [])
    return {"searches": searches[:20]}


@router.delete("/recent-searches")
def clear_recent_searches(user: dict = Depends(get_current_user)):
    _write_json_file(_RECENT_SEARCHES_FILE, [])
    return {"ok": True}


# --- Transport pref ---

@router.get("/transport-pref")
def transport_pref():
    has_aria2 = os.system("which aria2c > /dev/null 2>&1") == 0
    return {"mode": "aria2" if has_aria2 else "default"}


# --- Download paths ---

@router.get("/download-paths")
def download_paths():
    paths = [str(MODELS_DIR)]
    if CACHE_DIR.exists():
        paths.append(str(CACHE_DIR))
    return {"paths": paths}


# --- Hidden models ---

@router.get("/hidden-models")
def hidden_models():
    return {"models": _read_json_file(_HIDDEN_MODELS_FILE, [])}


class HideModelRequest(BaseModel):
    repo_id: str


@router.post("/hidden-models")
def hide_model(req: HideModelRequest, user: dict = Depends(get_current_user)):
    hidden = _read_json_file(_HIDDEN_MODELS_FILE, [])
    if req.repo_id not in hidden:
        hidden.append(req.repo_id)
        _write_json_file(_HIDDEN_MODELS_FILE, hidden)
    return {"ok": True, "models": hidden}


@router.delete("/hidden-models/{repo_id:path}")
def unhide_model(repo_id: str, user: dict = Depends(get_current_user)):
    hidden = _read_json_file(_HIDDEN_MODELS_FILE, [])
    hidden = [h for h in hidden if h != repo_id]
    _write_json_file(_HIDDEN_MODELS_FILE, hidden)
    return {"ok": True, "models": hidden}
