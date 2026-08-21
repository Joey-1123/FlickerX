# GPU Setup & Troubleshooting

FlickerX auto-detects your GPU and installs the correct llama-cpp-python wheel. No manual config needed in most cases.

---

## Quick Start

```bash
bash install.sh
```

The installer detects your GPU in this order and stops at the first match:

1. **NVIDIA CUDA** — checks `nvidia-smi`
2. **AMD ROCm** — checks `rocm-smi`, `/opt/rocm*`, or `lspci`
3. **Intel XPU** — checks `/dev/dri/render*`, `lspci`, `sycl-ls`
4. **Vulkan** — checks `vulkaninfo`
5. **Apple Metal** — checks `uname == Darwin`
6. **CPU fallback** — always available

It then installs `llama-cpp-python` with the matching pre-built wheel. Launch with `FlickerX` or `FlickerX --dev`.

**Windows:** Use `.\install.ps1` instead — same flags, same auto-detection (except Metal).

---

## Manual Selection

Force a specific backend even if auto-detect picks something else:

```bash
bash install.sh --gpu cuda      # NVIDIA CUDA
bash install.sh --gpu rocm      # AMD ROCm
bash install.sh --gpu vulkan    # Vulkan
bash install.sh --gpu intel     # Intel XPU/SYCL
bash install.sh --gpu metal     # Apple Metal (macOS only)
bash install.sh --gpu cpu       # CPU only
```

Windows:

```powershell
.\install.ps1 -Gpu cuda
.\install.ps1 -Gpu cpu
```

---

## Torch (Optional)

Image and video generation require PyTorch + diffusers. These are **not** installed by default — only llama-cpp-python is needed for text inference.

```bash
bash install.sh --with-torch
```

This installs: `torch`, `diffusers`, `transformers`, `accelerate`, `safetensors`, `Pillow`.

Torch is fetched from the correct index URL for your GPU (e.g. `download.pytorch.org/whl/cu124` for CUDA 12.4). On CPU-only installs, the default PyPI torch is used.

---

## GPU Detection

Runtime detection (`backend/gpu.py`) runs at inference time, separate from the installer:

```python
from backend.gpu import detect_gpu, get_device, get_n_gpu_layers
```

**Detection order:**

| Priority | Device | How it detects |
|----------|--------|----------------|
| 1 | `cuda` | `nvidia-smi --query-gpu=name,memory.total,memory.free` |
| 2 | `mps` | `platform.system() == "Darwin"` + `torch.backends.mps.is_available()` |
| 3 | `cpu` | Always available as fallback |

The `GPUInfo` dataclass reports: `available` (bool), `device` (`"cuda"` / `"mps"` / `"cpu"`), `name`, `vram_total_mb`, `vram_free_mb`.

`get_device()` returns `"cuda"`, `"mps"`, or `"cpu"` — used by all inference paths. `get_n_gpu_layers()` returns 99 (all layers on GPU) when GPU is available, 0 when CPU-only.

---

## Per-Backend Details

### NVIDIA CUDA

**Installer detects:** `nvidia-smi` output → parses `CUDA Version: X.Y`

**Pre-built wheels** (from `abetlen.github.io/llama-cpp-python/whl`):

| CUDA Version | Wheel Tag |
|-------------|-----------|
| 11.8+ | `cu118` |
| 12.1+ | `cu121` |
| 12.2+ | `cu122` |
| 12.3+ | `cu123` |
| 12.4+ | `cu124` |
| 12.5+ | `cu125` |
| 13.0+ | `cu130` |

**Requirements:**
- NVIDIA driver installed and `nvidia-smi` on PATH
- Driver must support CUDA 11.8+ minimum

**Common issues:**
- `nvidia-smi` not found → install NVIDIA drivers from [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx)
- CUDA version too old (pre-11.8) → update drivers

### AMD ROCm

**Installer detects:** `rocm-smi` on PATH, `/opt/rocm*/bin/rocm-smi`, or `lspci` matching `amd|radeon|navi|gfx`

| Platform | Wheel |
|----------|-------|
| Linux | `rocm72` |
| Windows | `hip-radeon` |

**Requirements:**
- Linux: ROCm 7.x installed (`/opt/rocm`)
- Windows: AMD HIP SDK installed
- GPU must be in [ROCm's supported list](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html)

**Common issues:**
- `rocm-smi` not found → install ROCm from [rocm.docs.amd.com](https://rocm.docs.amd.com/)
- GPU not recognized → check the supported GPU list; older cards may not have ROCm support

### Apple Metal

**Installer detects:** macOS (`uname == Darwin`) — always succeeds on macOS.

No extra tools needed. Metal acceleration is automatic on Apple Silicon (M1/M2/M3/M4). Intel Macs fall back to CPU.

### Intel XPU

**Installer detects:** `/dev/dri/render*` + `lspci` matching `intel`, or `sycl-ls` on PATH.

**Builds from source** (no pre-built wheel):

```
CMAKE_ARGS="-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx"
```

**Requirements:**
- Intel oneAPI toolkit installed (`icx`, `icpx` compilers)
- Linux: Intel GPU in `/dev/dri`
- Windows: Intel Arc or Iris GPU detected via WMI

**Common issues:**
- `icx` not found → install [Intel oneAPI Base Toolkit](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit.html)
- Build fails → ensure oneAPI environment is sourced before running the installer

### Vulkan

**Installer detects:** `vulkaninfo` on PATH + output contains `GPU`

**Requirements:**
- Vulkan SDK installed (`vulkaninfo` on PATH)
- Works with NVIDIA, AMD, and Intel GPUs — a cross-vendor fallback

**Common issues:**
- `vulkaninfo` not found → install [Vulkan SDK](https://vulkan.lunarg.com/sdk/home)
- No GPU in output → update GPU drivers

### CPU

Always available as the final fallback. No GPU required. Uses `llama-cpp-python` default build with no GPU acceleration.

---

## Troubleshooting

### "No GPU detected — falling back to CPU"

1. Verify your GPU driver is installed and working:
   - NVIDIA: `nvidia-smi`
   - AMD: `rocm-smi`
   - Vulkan: `vulkaninfo`
2. Run the installer with explicit GPU flag to see the actual error:
   ```bash
   bash install.sh --gpu cuda 2>&1
   ```
3. Check that the GPU device is visible to the OS (`lspci | grep -i vga`).

### Wrong CUDA version detected

The installer reads the **maximum supported CUDA version** from `nvidia-smi`, not the toolkit version. If you have CUDA 12.4 installed but `nvidia-smi` reports CUDA 12.5 support, it installs `cu125`. This is correct — the pre-built wheels are forward-compatible within the same major version.

### llama-cpp-python install fails

- **CUDA:** Ensure `nvidia-smi` runs successfully before installing. The installer pulls from `abetlen.github.io/llama-cpp-python/whl/cu*`.
- **ROCm:** The `rocm72` wheel requires ROCm 7.x. Older ROCm versions need a different wheel tag.
- **SYCL/Intel:** Source the oneAPI environment first:
  ```bash
  source /opt/intel/oneapi/setvars.sh
  bash install.sh --gpu intel
  ```

### Frontend build skipped

Node.js 18+ is required for the frontend. Install it from [nodejs.org](https://nodejs.org) and re-run the installer.

### "uv not found"

The installer auto-installs [uv](https://github.com/astral-sh/uv) if missing. If the auto-install fails, install manually:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### App starts but inference is slow

- Verify GPU is detected at runtime, not just at install time. Check startup logs for `device: cuda` vs `device: cpu`.
- See [Memory](#memory) below — you may need to tune `n_gpu_layers`.

---

## Memory

### VRAM Requirements (approximate)

| Model Size | FP16 VRAM | Q4_K_M VRAM | Recommended GPU |
|-----------|-----------|-------------|-----------------|
| 1–3B | ~2–6 GB | ~2–3 GB | Any 4GB+ VRAM |
| 7–8B | ~14–16 GB | ~5–6 GB | 8GB+ VRAM |
| 13B | ~26 GB | ~8–10 GB | 12GB+ VRAM |
| 30–34B | ~60–68 GB | ~18–22 GB | 24GB+ VRAM (or multi-GPU) |
| 70B | ~140 GB | ~40 GB | 2× 24GB or 1× 48GB+ |

### Tuning `n_gpu_layers`

`n_gpu_layers` controls how many transformer layers run on GPU. The runtime default is **99** (put everything on GPU if available).

- **0** = fully CPU
- **99** = all layers on GPU (default when GPU detected)
- **Partial** = set between 0 and the model's total layer count to split CPU/GPU

To override at runtime, set the environment variable before starting:

```bash
export N_GPU_LAYERS=20   # partial offload
FlickerX
```

**When to reduce layers:**
- Out of VRAM errors → reduce `n_gpu_layers` until it fits
- Want to run multiple models simultaneously → split VRAM across them
- System OOM on shared memory (integrated GPUs like Apple Silicon) → lower layers to leave RAM for the OS

**When to increase:**
- `nvidia-smi` shows VRAM headroom and inference is slow → increase layers
- Model runs mostly on CPU but GPU has free memory → bump up layers

### Apple Silicon Memory

On Apple Silicon, `n_gpu_layers` controls Metal offload. The unified memory is shared between CPU and GPU, so VRAM = system RAM minus OS overhead. You can offload most layers even on 8GB models with 16GB unified memory, but expect some swap.
