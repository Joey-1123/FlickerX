"""System router — status, hardware info, GPU, CUDA, disk, metrics, logs."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from collections import deque
from pathlib import Path

import psutil
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from config import LOGS_DIR

router = APIRouter()

# Historical metrics buffer (last 300 data points = ~10 min at 2s intervals)
_gpu_history: deque[dict] = deque(maxlen=300)
_cpu_history: deque[float] = deque(maxlen=300)
_prev_disk_io: dict | None = None
_prev_net_io: dict | None = None


def _get_cpu_info() -> dict:
    try:
        with open("/proc/cpuinfo") as f:
            lines = f.readlines()
        model = "unknown"
        cores = 0
        for line in lines:
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
            if line.startswith("processor"):
                cores += 1
        return {"model": model, "cores": cores, "architecture": platform.machine()}
    except Exception:
        return {"model": platform.processor() or "unknown", "cores": os.cpu_count() or 0, "architecture": platform.machine()}


def _get_memory_info() -> dict:
    mem = psutil.virtual_memory()
    return {"total_bytes": mem.total, "available_bytes": mem.available, "used_bytes": mem.used, "percent": mem.percent}


def _get_gpu_info() -> list[dict]:
    gpus = []
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "name": parts[0],
                        "vram_total_mb": int(parts[1]),
                        "vram_used_mb": int(parts[2]),
                        "vram_free_mb": int(parts[3]),
                        "utilization_gpu": int(parts[4]),
                        "temperature_gpu": int(parts[5]),
                    })
    except Exception:
        pass
    if not gpus:
        gpus.append({"name": "No GPU detected", "vram_total_mb": 0, "vram_used_mb": 0, "vram_free_mb": 0, "utilization_gpu": 0, "temperature_gpu": 0})
    return gpus


def _get_disk_info() -> dict:
    usage = psutil.disk_usage("/")
    return {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free, "percent": usage.percent, "path": "/"}


def _get_disk_io() -> dict:
    global _prev_disk_io
    io = psutil.disk_io_counters()
    if not io:
        return {"read_bytes": 0, "write_bytes": 0, "read_bytes_per_sec": 0, "write_bytes_per_sec": 0}
    current = {"read_bytes": io.read_bytes, "write_bytes": io.write_bytes}
    rate = {"read_bytes_per_sec": 0, "write_bytes_per_sec": 0}
    if _prev_disk_io:
        dt = 1.0
        rate["read_bytes_per_sec"] = max(0, (current["read_bytes"] - _prev_disk_io["read_bytes"]) / dt)
        rate["write_bytes_per_sec"] = max(0, (current["write_bytes"] - _prev_disk_io["write_bytes"]) / dt)
    _prev_disk_io = current
    return {**current, **rate}


def _get_network_io() -> dict:
    global _prev_net_io
    net = psutil.net_io_counters()
    current = {"bytes_sent": net.bytes_sent, "bytes_recv": net.bytes_recv}
    rate = {"bytes_sent_per_sec": 0, "bytes_recv_per_sec": 0}
    if _prev_net_io:
        dt = 1.0
        rate["bytes_sent_per_sec"] = max(0, (current["bytes_sent"] - _prev_net_io["bytes_sent"]) / dt)
        rate["bytes_recv_per_sec"] = max(0, (current["bytes_recv"] - _prev_net_io["bytes_recv"]) / dt)
    _prev_net_io = current
    return {**current, **rate}


def _get_process_metrics() -> dict:
    proc = psutil.Process()
    mem = proc.memory_info()
    return {
        "pid": proc.pid,
        "rss_bytes": mem.rss,
        "vms_bytes": mem.vms,
        "cpu_percent": proc.cpu_percent(interval=0),
        "num_threads": proc.num_threads(),
        "uptime_seconds": time.time() - proc.create_time(),
    }


# --- Endpoints ---

@router.get("/status")
def system_status():
    return {
        "status": "ok",
        "version": "0.1.0",
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }


@router.get("/hardware")
@router.get("/hardware-info")
def hardware_info():
    return {
        "cpu": _get_cpu_info(),
        "memory": _get_memory_info(),
        "gpus": _get_gpu_info(),
        "disk": _get_disk_info(),
    }


@router.get("/gpu-info")
def gpu_info():
    return {"gpus": _get_gpu_info()}


@router.get("/cuda-info")
def cuda_info():
    gpus = _get_gpu_info()
    has_cuda = any(g["name"] != "No GPU detected" for g in gpus)
    return {"available": has_cuda, "gpus": gpus}


@router.get("/disk-info")
def disk_info():
    return _get_disk_info()


@router.get("/accelerator-usage")
def accelerator_usage():
    return {"history": list(_gpu_history)}


@router.get("/process-metrics")
def process_metrics():
    return _get_process_metrics()


@router.get("/logs")
def get_logs(since: str = "", limit: int = 100):
    log_files = sorted(LOGS_DIR.glob("*.log"), reverse=True)
    if not log_files:
        return {"logs": [], "sources": []}
    lines = []
    with open(log_files[0]) as f:
        for line in f:
            lines.append(line.rstrip())
            if len(lines) >= limit:
                break
    return {"logs": lines, "sources": [str(f) for f in log_files]}


@router.get("/metrics-stream")
def metrics_stream():
    """Real SSE metrics stream using psutil."""
    def generate():
        global _prev_disk_io, _prev_net_io
        # Prime the delta counters
        _get_disk_io()
        _get_network_io()
        psutil.cpu_percent(interval=None)

        while True:
            ts = time.time()
            cpu_pct = psutil.cpu_percent(interval=0)
            mem = _get_memory_info()
            gpus = _get_gpu_info()
            disk_io = _get_disk_io()
            net_io = _get_network_io()
            proc = _get_process_metrics()

            # Track history
            _cpu_history.append(cpu_pct)
            gpu_snapshot = {"timestamp": ts, "gpus": gpus}
            _gpu_history.append(gpu_snapshot)

            data = {
                "cpu_percent": cpu_pct,
                "cpu_count": psutil.cpu_count(),
                "ram_used_bytes": mem["used_bytes"],
                "ram_total_bytes": mem["total_bytes"],
                "ram_percent": mem["percent"],
                "gpus": gpus,
                "disk_read_bytes_per_sec": disk_io["read_bytes_per_sec"],
                "disk_write_bytes_per_sec": disk_io["write_bytes_per_sec"],
                "net_sent_bytes_per_sec": net_io["bytes_sent_per_sec"],
                "net_recv_bytes_per_sec": net_io["bytes_recv_per_sec"],
                "process": proc,
                "timestamp": ts,
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(2)

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
