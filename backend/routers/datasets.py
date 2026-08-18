"""Dataset management endpoints — /api/hub/datasets/*"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from config import STUDIO_HOME

router = APIRouter(prefix="/api/hub/datasets", tags=["datasets"])

DATASETS_DIR = STUDIO_HOME / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class CheckFormatRequest(BaseModel):
    dataset_name: str
    subset: Optional[str] = None
    train_split: str = "train"
    is_vlm: bool = False
    prefer_local_cache: bool = False
    local_path: Optional[str] = None


class AiAssistMappingRequest(BaseModel):
    columns: list[str]
    samples: list[list[str]]
    dataset_name: Optional[str] = None
    model_name: Optional[str] = None
    model_type: Optional[str] = None


class LocalOptionsRequest(BaseModel):
    dataset_name: str
    local_path: Optional[str] = None


class DatasetDownloadRequest(BaseModel):
    repo_id: str
    hf_token: Optional[str] = None
    use_xet: Optional[bool] = None
    transport_mode: Optional[str] = None


class DatasetCancelRequest(BaseModel):
    repo_id: str
    generation: Optional[str] = None


class DatasetCacheDeleteRequest(BaseModel):
    repo_id: str
    cache_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------
@router.post("/check-format")
async def check_dataset_format(req: CheckFormatRequest):
    """Detect dataset format and suggest column mapping."""
    # Check if local path exists
    local_path = req.local_path or str(DATASETS_DIR / req.dataset_name)
    columns = []
    preview_samples = []
    detected_format = "unknown"

    if os.path.exists(local_path):
        # Try to read a CSV/JSON/JSONL file
        for fname in os.listdir(local_path):
            fpath = os.path.join(local_path, fname)
            if fname.endswith(".csv"):
                import csv
                with open(fpath) as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    columns = headers
                    for i, row in enumerate(reader):
                        if i >= 3:
                            break
                        preview_samples.append(row)
                detected_format = "csv"
                break
            elif fname.endswith(".jsonl") or fname.endswith(".json"):
                try:
                    with open(fpath) as f:
                        first_lines = [f.readline() for _ in range(3)]
                    data = [json.loads(line) for line in first_lines if line.strip()]
                    if data:
                        columns = list(data[0].keys())
                        preview_samples = [list(d.values()) for d in data[:3]]
                    detected_format = "jsonl" if fname.endswith(".jsonl") else "json"
                    break
                except Exception:
                    pass

    return {
        "requires_manual_mapping": len(columns) == 0,
        "detected_format": detected_format,
        "columns": columns,
        "suggested_mapping": {},
        "preview_samples": preview_samples,
    }


@router.post("/ai-assist-mapping")
async def ai_assist_mapping(req: AiAssistMappingRequest):
    """AI-assisted column mapping suggestion."""
    # Simple heuristic — map 'text', 'instruction', 'input', 'output', 'response' columns
    mapping = {}
    for col in req.columns:
        lower = col.lower()
        if lower in ("text", "content", "message"):
            mapping[col] = "text"
        elif lower in ("instruction", "prompt", "question"):
            mapping[col] = "instruction"
        elif lower in ("input",):
            mapping[col] = "input"
        elif lower in ("output", "response", "answer", "completion"):
            mapping[col] = "output"

    return {
        "success": True,
        "suggested_mapping": mapping,
        "warning": None,
        "system_prompt": None,
        "label_mapping": mapping,
    }


@router.post("/local-options")
async def local_dataset_options(req: LocalOptionsRequest):
    """List splits available in a local dataset."""
    local_path = req.local_path or str(DATASETS_DIR / req.dataset_name)
    splits = []
    if os.path.isdir(local_path):
        for entry in os.scandir(local_path):
            if entry.is_dir() and entry.name in ("train", "validation", "test", "val"):
                splits.append({"name": entry.name, "num_examples": len(list(Path(entry.path).glob("*")))})
            elif entry.is_file() and entry.name.endswith((".csv", ".jsonl", ".json")):
                splits.append({"name": "train", "num_examples": 0})
    if not splits:
        splits = [{"name": "train", "num_examples": 0}]
    return {"splits": splits}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a dataset file."""
    dest = DATASETS_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename, "stored_path": str(dest)}


# ---------------------------------------------------------------------------
# Local datasets inventory
# ---------------------------------------------------------------------------
@router.get("/local")
async def list_local_datasets():
    datasets = []
    if DATASETS_DIR.exists():
        for entry in DATASETS_DIR.iterdir():
            if entry.is_dir() or entry.suffix in (".csv", ".jsonl", ".json"):
                datasets.append({
                    "name": entry.stem if entry.is_file() else entry.name,
                    "path": str(entry),
                    "type": "file" if entry.is_file() else "directory",
                })
    return {"datasets": datasets}


@router.get("/cached")
async def list_cached_datasets():
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    cached = []
    if cache_dir.exists():
        for entry in cache_dir.iterdir():
            if entry.is_dir() and "datasets" in entry.name:
                cached.append({"repo_id": entry.name, "cache_path": str(entry)})
    return {"cached": cached}


@router.delete("/cached")
async def delete_cached_dataset(body: DatasetCacheDeleteRequest):
    cache_path = body.cache_path
    if cache_path and os.path.exists(cache_path):
        shutil.rmtree(cache_path)
    return None


# ---------------------------------------------------------------------------
# Dataset downloads
# ---------------------------------------------------------------------------
@router.get("/active-downloads")
async def active_downloads(repo_id: str = ""):
    return {"downloads": []}


@router.post("/download")
async def download_dataset(req: DatasetDownloadRequest):
    return {"status": "started", "repo_id": req.repo_id}


@router.post("/download/cancel")
async def cancel_dataset_download(req: DatasetCancelRequest):
    return {"repo_id": req.repo_id, "state": "cancelled"}


@router.get("/download-status")
async def dataset_download_status(repo_id: str = ""):
    return {"status": "idle", "repo_id": repo_id}


@router.get("/download-progress")
async def dataset_download_progress(repo_id: str = "", expected_bytes: int = 0):
    return {"bytes_downloaded": 0, "bytes_total": expected_bytes, "fraction": 0}


@router.get("/transport-status")
async def dataset_transport_status(repo_id: str = ""):
    return {"repo_id": repo_id, "transport": None, "active": False}
