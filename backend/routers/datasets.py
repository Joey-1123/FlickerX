"""Dataset management — real HF hub downloads, format detection, upload."""

from __future__ import annotations

import csv
import json
import os
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import structlog
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from config import STUDIO_HOME

logger = structlog.get_logger()
router = APIRouter(prefix="/api/hub/datasets", tags=["datasets"])

DATASETS_DIR = STUDIO_HOME / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Download state
# ---------------------------------------------------------------------------
_downloads: dict[str, dict[str, Any]] = {}
_download_lock = threading.Lock()


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
    transport_mode: Optional[str] = "auto"


class DatasetCancelRequest(BaseModel):
    repo_id: str
    generation: Optional[str] = None


class DatasetCacheDeleteRequest(BaseModel):
    repo_id: str
    cache_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_csv_preview(path: str, max_rows: int = 5) -> tuple[list[str], list[list[str]], int]:
    columns, samples, total = [], [], 0
    with open(path) as f:
        reader = csv.reader(f)
        headers = next(reader, [])
        columns = headers
        for row in reader:
            total += 1
            if len(samples) < max_rows:
                samples.append(row)
    return columns, samples, total


def _read_jsonl_preview(path: str, max_rows: int = 5) -> tuple[list[str], list[list[str]], int]:
    columns, samples, total = [], [], 0
    with open(path) as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            total += 1
            if i == 0:
                first = json.loads(line)
                columns = list(first.keys())
            if len(samples) < max_rows:
                row = json.loads(line)
                samples.append([str(v) for v in row.values()])
    return columns, samples, total


def _detect_format(path: str) -> tuple[str, list[str], list[list[str]], int]:
    """Detect CSV/JSONL/JSON and return (format, columns, preview_rows, total_rows)."""
    p = Path(path)
    if p.is_file():
        if p.suffix == ".csv":
            fmt, cols, samples, total = "csv", *_read_csv_preview(str(p))
            return fmt, cols, samples, total
        elif p.suffix in (".jsonl", ".json"):
            fmt, cols, samples, total = "jsonl", *_read_jsonl_preview(str(p))
            return fmt, cols, samples, total
    elif p.is_dir():
        for fname in sorted(p.iterdir()):
            if fname.is_file():
                fmt, cols, samples, total = _detect_format(str(fname))
                if cols:
                    return fmt, cols, samples, total
    return "unknown", [], [], 0


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------
@router.post("/check-format")
async def check_dataset_format(req: CheckFormatRequest):
    local_path = req.local_path or str(DATASETS_DIR / req.dataset_name)

    fmt, columns, preview_samples, total_rows = "unknown", [], [], 0
    if os.path.exists(local_path):
        fmt, columns, preview_samples, total_rows = _detect_format(local_path)

    detected_image_column = None
    detected_text_column = None
    multimodal_columns = None
    if columns:
        for col in columns:
            lower = col.lower()
            if lower in ("image", "images", "pixel_values", "image_path", "img"):
                detected_image_column = col
            if lower in ("text", "content", "message", "instruction", "prompt", "question"):
                detected_text_column = col

    return {
        "requires_manual_mapping": len(columns) == 0,
        "detected_format": fmt,
        "columns": columns,
        "suggested_mapping": {},
        "detected_image_column": detected_image_column,
        "detected_audio_column": None,
        "detected_text_column": detected_text_column,
        "detected_speaker_column": None,
        "chat_column": None,
        "preview_samples": preview_samples if preview_samples else None,
        "total_rows": total_rows or None,
        "is_image": detected_image_column is not None,
        "is_audio": False,
        "multimodal_columns": multimodal_columns,
        "warning": None,
    }


@router.post("/ai-assist-mapping")
async def ai_assist_mapping(req: AiAssistMappingRequest):
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
    local_path = req.local_path or str(DATASETS_DIR / req.dataset_name)
    splits = []
    if os.path.isdir(local_path):
        for entry in os.scandir(local_path):
            if entry.is_dir() and entry.name in ("train", "validation", "test", "val"):
                splits.append({"name": entry.name, "num_examples": len(list(Path(entry.path).glob("*")))})
            elif entry.is_file() and entry.name.endswith((".csv", ".jsonl", ".json")):
                _, _, _, total = _detect_format(entry.path)
                splits.append({"name": "train", "num_examples": total})
    if not splits:
        splits = [{"name": "train", "num_examples": 0}]
    return {"splits": splits}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
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
            if entry.is_dir() and entry.name.startswith("datasets--"):
                repo_id = entry.name.replace("--", "/").replace("datasets___", "")
                cached.append({"repo_id": repo_id, "cache_path": str(entry)})
    return {"cached": cached}


@router.delete("/cached")
async def delete_cached_dataset(body: DatasetCacheDeleteRequest):
    cache_path = body.cache_path
    if cache_path and os.path.exists(cache_path):
        shutil.rmtree(cache_path)
    return None


# ---------------------------------------------------------------------------
# Dataset downloads — REAL HF hub
# ---------------------------------------------------------------------------
@router.get("/active-downloads")
async def active_downloads(repo_id: str = ""):
    with _download_lock:
        if repo_id:
            dl = _downloads.get(repo_id)
            return {"downloads": [dl] if dl and dl["state"] in ("downloading", "starting") else []}
        active = [d for d in _downloads.values() if d["state"] in ("downloading", "starting")]
        return {"downloads": active}


@router.post("/download")
async def download_dataset(req: DatasetDownloadRequest):
    repo_id = req.repo_id
    with _download_lock:
        existing = _downloads.get(repo_id)
        if existing and existing["state"] in ("downloading", "starting"):
            return {"status": "already_running", "repo_id": repo_id}

        job = {
            "repo_id": repo_id,
            "state": "starting",
            "error": None,
            "generation": str(uuid.uuid4().hex[:8]),
            "started_at": time.time(),
        }
        _downloads[repo_id] = job

    def _run_download():
        try:
            from huggingface_hub import snapshot_download
            _downloads[repo_id]["state"] = "downloading"

            def progress_fn(filename: str, bytes_downloaded: int, bytes_total: int):
                if bytes_total:
                    _downloads[repo_id]["bytes_downloaded"] = bytes_downloaded
                    _downloads[repo_id]["bytes_total"] = bytes_total

            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                local_dir=str(DATASETS_DIR / repo_id.replace("/", "_")),
                token=req.hf_token,
            )
            _downloads[repo_id]["state"] = "completed"
        except Exception as e:
            _downloads[repo_id]["state"] = "failed"
            _downloads[repo_id]["error"] = str(e)[:500]
            logger.error("dataset_download_failed", repo_id=repo_id, error=str(e))

    thread = threading.Thread(target=_run_download, daemon=True)
    thread.start()
    return {"status": "started", "repo_id": repo_id}


@router.post("/download/cancel")
async def cancel_dataset_download(req: DatasetCancelRequest):
    with _download_lock:
        dl = _downloads.get(req.repo_id)
        if dl:
            dl["state"] = "cancelled"
    return {"repo_id": req.repo_id, "state": "cancelled"}


@router.get("/download-status")
async def dataset_download_status(repo_id: str = ""):
    with _download_lock:
        dl = _downloads.get(repo_id)
        if not dl:
            return {"status": "idle", "repo_id": repo_id}
        return {"status": dl["state"], "repo_id": repo_id, "error": dl.get("error")}


@router.get("/download-progress")
async def dataset_download_progress(repo_id: str = "", expected_bytes: int = 0):
    with _download_lock:
        dl = _downloads.get(repo_id)
        if not dl:
            return {"bytes_downloaded": 0, "bytes_total": expected_bytes, "fraction": 0}
        downloaded = dl.get("bytes_downloaded", 0)
        total = dl.get("bytes_total", expected_bytes)
        fraction = downloaded / total if total else 0
        return {"bytes_downloaded": downloaded, "bytes_total": total, "fraction": fraction}


@router.get("/transport-status")
async def dataset_transport_status(repo_id: str = ""):
    with _download_lock:
        dl = _downloads.get(repo_id)
        active = dl is not None and dl["state"] in ("downloading", "starting")
    return {"repo_id": repo_id, "transport": None, "active": active}
