"""GPU detection — shared utility for all inference paths."""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass


@dataclass
class GPUInfo:
    available: bool
    device: str  # "cuda", "mps", "cpu"
    name: str
    vram_total_mb: int
    vram_free_mb: int


def detect_gpu() -> GPUInfo:
    """Detect best available GPU. Returns GPUInfo with device string."""
    # 1. Try CUDA (nvidia-smi)
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    return GPUInfo(
                        available=True,
                        device="cuda",
                        name=parts[0],
                        vram_total_mb=int(parts[1]),
                        vram_free_mb=int(parts[2]),
                    )
    except Exception:
        pass

    # 2. Try Apple MPS
    if platform.system() == "Darwin":
        try:
            import torch  # noqa: F401
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return GPUInfo(
                    available=True, device="mps",
                    name="Apple Silicon (MPS)", vram_total_mb=0, vram_free_mb=0,
                )
        except ImportError:
            pass

    # 3. CPU fallback
    return GPUInfo(available=False, device="cpu", name="No GPU detected", vram_total_mb=0, vram_free_mb=0)


def get_device() -> str:
    """Return 'cuda', 'mps', or 'cpu' — used by all inference paths."""
    return detect_gpu().device


def get_n_gpu_layers(default: int = 99) -> int:
    """Return GPU layers for llama-cpp. default=all layers on GPU, 0=CPU."""
    return default if detect_gpu().available else 0


def get_torch_dtype():
    """Return best torch dtype for the available device."""
    try:
        import torch
        device = get_device()
        if device == "cuda":
            return torch.float16
        return torch.float32
    except ImportError:
        return None


def is_cuda_available() -> bool:
    """Quick check — is CUDA available?"""
    return detect_gpu().device == "cuda"
