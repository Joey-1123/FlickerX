#!/usr/bin/env bash
set -euo pipefail

# ── FlickerX Installer ───────────────────────────────────────────────────────
# Detects GPU, installs llama-cpp-python with the right backend, optional
# torch+diffusers for image/video generation.
#
# Usage:
#   bash install.sh              # auto-detect GPU
#   bash install.sh --gpu cuda   # force CUDA
#   bash install.sh --gpu rocm   # force ROCm
#   bash install.sh --gpu vulkan # force Vulkan
#   bash install.sh --gpu intel  # force Intel XPU/SYCL
#   bash install.sh --gpu metal  # force Metal (macOS)
#   bash install.sh --gpu cpu    # CPU only
#   bash install.sh --with-torch # also install torch+diffusers (image/video)
# ──────────────────────────────────────────────────────────────────────────────

REPO_URL="https://github.com/Joey-1123/FlickerX.git"
INSTALL_DIR="${FLICKERX_DIR:-$HOME/.flickerx}"
VENV_DIR="$INSTALL_DIR/venv"
SHIM_DIR="${HOME}/.local/bin"

# ── Parse args ───────────────────────────────────────────────────────────────

FORCE_GPU=""
WITH_TORCH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu)    FORCE_GPU="$2"; shift 2 ;;
    --with-torch) WITH_TORCH=true; shift ;;
    -h|--help)
      echo "Usage: bash install.sh [--gpu cuda|rocm|vulkan|intel|metal|cpu] [--with-torch]"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Colors ───────────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ── Check dependencies ───────────────────────────────────────────────────────

check_deps() {
  info "Checking dependencies..."

  # Python 3.10+
  if ! command -v python3 &>/dev/null; then
    fail "Python 3 not found. Install Python 3.10+ first."
  fi
  PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
  PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
  if [[ "$PY_MAJOR" -lt 3 || ("$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 10) ]]; then
    fail "Python $PY_VER found, need 3.10+."
  fi
  ok "Python $PY_VER"

  # uv
  if ! command -v uv &>/dev/null; then
    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  ok "uv $(uv --version 2>/dev/null || echo 'installed')"

  # Node.js + npm (for frontend build)
  if ! command -v node &>/dev/null; then
    warn "Node.js not found — frontend build will be skipped."
    warn "Install Node.js 18+ for full functionality: https://nodejs.org"
  else
    ok "Node.js $(node --version)"
  fi

  # git
  if ! command -v git &>/dev/null; then
    fail "git not found."
  fi
  ok "git"
}

# ── GPU detection ────────────────────────────────────────────────────────────

detect_nvidia_cuda() {
  if ! command -v nvidia-smi &>/dev/null; then
    return 1
  fi
  local smi_output
  smi_output=$(nvidia-smi 2>/dev/null) || return 1
  # Parse CUDA version from nvidia-smi output (e.g. "CUDA Version: 12.4")
  local cuda_ver
  cuda_ver=$(echo "$smi_output" | grep -oP 'CUDA Version:\s*\K[0-9.]+' | head -1)
  if [[ -z "$cuda_ver" ]]; then
    return 1
  fi
  # Map CUDA version to llama-cpp-python wheel tag
  local major minor
  major=$(echo "$cuda_ver" | cut -d. -f1)
  minor=$(echo "$cuda_ver" | cut -d. -f2)
  if [[ "$major" -ge 13 ]]; then
    LLAMA_GPU_BACKEND="cu130"
  elif [[ "$major" -eq 12 && "$minor" -ge 5 ]]; then
    LLAMA_GPU_BACKEND="cu125"
  elif [[ "$major" -eq 12 && "$minor" -ge 4 ]]; then
    LLAMA_GPU_BACKEND="cu124"
  elif [[ "$major" -eq 12 && "$minor" -ge 3 ]]; then
    LLAMA_GPU_BACKEND="cu123"
  elif [[ "$major" -eq 12 && "$minor" -ge 2 ]]; then
    LLAMA_GPU_BACKEND="cu122"
  elif [[ "$major" -eq 12 && "$minor" -ge 1 ]]; then
    LLAMA_GPU_BACKEND="cu121"
  elif [[ "$major" -eq 11 && "$minor" -ge 8 ]]; then
    LLAMA_GPU_BACKEND="cu118"
  else
    warn "CUDA $cuda_ver detected but no matching wheel available."
    return 1
  fi
  # PyTorch CUDA tag
  TORCH_INDEX_URL="https://download.pytorch.org/whl/cu${major}${minor}"
  GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
  ok "NVIDIA GPU detected: $GPU_NAME (CUDA $cuda_ver → $LLAMA_GPU_BACKEND)"
  return 0
}

detect_amd_rocm() {
  local rocm_found=false

  # Check rocm-smi
  if command -v rocm-smi &>/dev/null; then
    rocm_found=true
  # Check /opt/rocm directory
  elif ls /opt/rocm*/bin/rocm-smi &>/dev/null 2>&1; then
    rocm_found=true
  # Check lspci for AMD GPU
  elif command -v lspci &>/dev/null && lspci 2>/dev/null | grep -qi 'amd\|radeon\|navi\|gfx'; then
    rocm_found=true
  fi

  if [[ "$rocm_found" == "false" ]]; then
    return 1
  fi

  if [[ "$(uname)" == "Linux" ]]; then
    LLAMA_GPU_BACKEND="rocm72"
    TORCH_INDEX_URL="https://download.pytorch.org/whl/rocm6.2.4"
  else
    # Windows ROCm via HIP Radeon
    LLAMA_GPU_BACKEND="hip-radeon"
    TORCH_INDEX_URL=""
  fi

  GPU_NAME="AMD GPU"
  if command -v rocm-smi &>/dev/null; then
    GPU_NAME=$(rocm-smi --showproductname 2>/dev/null | grep -oP 'Card series:\s*\K.*' | head -1 || echo "AMD GPU")
  elif command -v lspci &>/dev/null; then
    GPU_NAME=$(lspci 2>/dev/null | grep -i 'amd\|radeon' | head -1 || echo "AMD GPU")
  fi
  ok "AMD GPU detected: $GPU_NAME → $LLAMA_GPU_BACKEND"
  return 0
}

detect_vulkan() {
  if command -v vulkaninfo &>/dev/null; then
    if vulkaninfo 2>/dev/null | grep -q 'GPU'; then
      LLAMA_GPU_BACKEND="vulkan"
      GPU_NAME=$(vulkaninfo 2>/dev/null | grep -oP 'deviceName\s*=\s*\K.*' | head -1 || echo "Vulkan GPU")
      ok "Vulkan GPU detected: $GPU_NAME → $LLAMA_GPU_BACKEND"
      return 0
    fi
  fi
  return 1
}

detect_intel() {
  local intel_found=false

  # Check for Intel GPU in /dev/dri (Linux)
  if ls /dev/dri/render* &>/dev/null 2>&1; then
    if command -v lspci &>/dev/null && lspci 2>/dev/null | grep -qi 'intel.*vulkan\|intel.*gfx\|intel.*iris'; then
      intel_found=true
    fi
  fi

  # Check for sycl-ls
  if command -v sycl-ls &>/dev/null; then
    intel_found=true
  fi

  if [[ "$intel_found" == "false" ]]; then
    return 1
  fi

  LLAMA_GPU_BACKEND="sycl"
  GPU_NAME="Intel GPU"
  ok "Intel GPU detected → $LLAMA_GPU_BACKEND"
  return 0
}

detect_metal() {
  if [[ "$(uname)" != "Darwin" ]]; then
    return 1
  fi
  LLAMA_GPU_BACKEND="metal"
  GPU_NAME=$(system_profiler SPDisplaysDataType 2>/dev/null | grep -oP 'Chipset Model:\s*\K.*' | head -1 || echo "Apple Silicon")
  ok "macOS Metal detected: $GPU_NAME → $LLAMA_GPU_BACKEND"
  return 0
}

detect_gpu() {
  if [[ -n "$FORCE_GPU" ]]; then
    case "$FORCE_GPU" in
      cuda)   detect_nvidia_cuda || fail "CUDA forced but nvidia-smi not found or failed." ;;
      rocm)   detect_amd_rocm  || fail "ROCm forced but not detected." ;;
      vulkan) LLAMA_GPU_BACKEND="vulkan"; GPU_NAME="Vulkan (forced)"; ok "Forced Vulkan backend" ;;
      intel)  LLAMA_GPU_BACKEND="sycl";   GPU_NAME="Intel XPU (forced)"; ok "Forced SYCL/Intel backend" ;;
      metal)  LLAMA_GPU_BACKEND="metal";  GPU_NAME="Metal (forced)"; ok "Forced Metal backend" ;;
      cpu)    LLAMA_GPU_BACKEND="cpu";    GPU_NAME="CPU only"; ok "Forced CPU-only mode" ;;
      *)      fail "Unknown GPU backend: $FORCE_GPU" ;;
    esac
    return
  fi

  info "Detecting GPU..."
  if detect_nvidia_cuda; then return; fi
  if detect_amd_rocm; then return; fi
  if detect_intel; then return; fi
  if detect_vulkan; then return; fi
  if detect_metal; then return; fi

  warn "No GPU detected — falling back to CPU."
  LLAMA_GPU_BACKEND="cpu"
  GPU_NAME="CPU only"
}

# ── Clone / update repo ─────────────────────────────────────────────────────

setup_repo() {
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    info "Updating existing install at $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || warn "Pull failed, using existing code."
  else
    info "Cloning FlickerX to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || fail "Clone failed."
  fi
}

# ── Create venv and install deps ────────────────────────────────────────────

install_backend() {
  info "Creating venv at $VENV_DIR..."
  uv venv "$VENV_DIR" --python "python${PY_VER}" 2>/dev/null || uv venv "$VENV_DIR"
  ok "Venv created."

  # Activate venv
  source "$VENV_DIR/bin/activate"

  # Install llama-cpp-python with GPU backend
  info "Installing llama-cpp-python ($LLAMA_GPU_BACKEND)..."
  if [[ "$LLAMA_GPU_BACKEND" == "cpu" ]]; then
    # Try pre-built wheel first (no compiler needed)
    if ! uv pip install "llama-cpp-python[server]>=0.3.0" --only-binary llama-cpp-python --quiet 2>/dev/null; then
      # No pre-built wheel — need gcc/g++ for source build
      if ! command -v gcc &>/dev/null && ! command -v g++ &>/dev/null; then
        fail "No pre-built wheel available and no C compiler found.
  Install build tools first:
    Ubuntu/Debian: sudo apt install build-essential
    Fedora/RHEL:   sudo dnf groupinstall 'Development Tools'
    Arch:          sudo pacman -S base-devel
  Then re-run this installer."
      fi
      uv pip install "llama-cpp-python[server]>=0.3.0" --quiet
    fi
  elif [[ "$LLAMA_GPU_BACKEND" == "cu"* ]]; then
    uv pip install "llama-cpp-python[server]>=0.3.0" \
      --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/$LLAMA_GPU_BACKEND" --quiet
  elif [[ "$LLAMA_GPU_BACKEND" == "rocm"* || "$LLAMA_GPU_BACKEND" == "hip-radeon" ]]; then
    uv pip install "llama-cpp-python[server]>=0.3.0" \
      --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/$LLAMA_GPU_BACKEND" --quiet
  elif [[ "$LLAMA_GPU_BACKEND" == "vulkan" ]]; then
    uv pip install "llama-cpp-python[server]>=0.3.0" \
      --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/vulkan" --quiet
  elif [[ "$LLAMA_GPU_BACKEND" == "metal" ]]; then
    uv pip install "llama-cpp-python[server]>=0.3.0" \
      --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/metal" --quiet
  elif [[ "$LLAMA_GPU_BACKEND" == "sycl" ]]; then
    # Intel SYCL needs source build — set CMAKE_ARGS before install
    CMAKE_ARGS="-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx" \
      uv pip install "llama-cpp-python[server]>=0.3.0" --quiet
  fi
  ok "llama-cpp-python installed."

  # Install remaining deps
  info "Installing remaining dependencies..."
  uv pip install -r pyproject.toml --quiet 2>/dev/null || uv pip install \
    fastapi "uvicorn[standard]>=0.34.0" "pydantic>=2.0" "pyjwt>=2.10.0" \
    "passlib[bcrypt]>=1.7.4" "bcrypt==4.0.1" "aiosqlite>=0.20.0" \
    "structlog>=24.0" "httpx>=0.27.0" "python-multipart>=0.0.9" \
    "huggingface-hub>=0.27.0" "psutil>=5.9.0" --quiet
  ok "Backend dependencies installed."

  # Optional: torch + diffusers for image/video generation
  if [[ "$WITH_TORCH" == "true" ]]; then
    info "Installing torch + diffusers (image/video generation)..."
    if [[ -n "${TORCH_INDEX_URL:-}" ]]; then
      uv pip install torch diffusers --index-url "$TORCH_INDEX_URL" --quiet
    else
      uv pip install torch diffusers --quiet
    fi
    uv pip install transformers accelerate safetensors Pillow --quiet
    ok "torch + diffusers installed."
  fi
}

# ── Build frontend ───────────────────────────────────────────────────────────

build_frontend() {
  if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    warn "Skipping frontend build (Node.js not found)."
    return
  fi

  info "Building frontend..."
  (
    cd "$INSTALL_DIR/frontend"
    npm ci --silent 2>/dev/null || npm install --silent
    npm run build --silent 2>/dev/null || warn "Frontend build failed — run 'cd frontend && npm run build' manually."
  )
  ok "Frontend built."
}

# ── Create shim ──────────────────────────────────────────────────────────────

create_shim() {
  mkdir -p "$SHIM_DIR"

  cat > "$SHIM_DIR/FlickerX" << SHIM
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$INSTALL_DIR/backend/cli.py" "\$@"
SHIM
  chmod +x "$SHIM_DIR/FlickerX"

  ok "Shim created: $SHIM_DIR/FlickerX"

  # Check if ~/.local/bin is in PATH
  if [[ ":$PATH:" != *":$SHIM_DIR:"* ]]; then
    warn "$SHIM_DIR is not in your PATH."
    warn "Add to your shell profile:"
    warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
}

# ── Print summary ────────────────────────────────────────────────────────────

summary() {
  echo ""
  echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  FlickerX installed successfully!${NC}"
  echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
  echo ""
  echo "  Install dir:  $INSTALL_DIR"
  echo "  Venv:         $VENV_DIR"
  echo "  GPU backend:  $LLAMA_GPU_BACKEND ($GPU_NAME)"
  echo "  Torch:        $([ "$WITH_TORCH" == "true" ] && echo "installed" || echo "not installed (use --with-torch to add)")"
  echo ""
  echo "  Launch:"
  echo "    FlickerX"
  echo "    # or:"
  echo "    $SHIM_DIR/FlickerX"
  echo "    # or directly:"
  echo "    $VENV_DIR/bin/python $INSTALL_DIR/backend/cli.py"
  echo ""
  echo "  Dev mode (hot reload):"
  echo "    FlickerX --dev"
  echo ""
  echo "  Options:"
  echo "    --port 8080     Change port (default: 8080)"
  echo "    --host 0.0.0.0   Bind to all interfaces"
  echo ""
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
  echo ""
  echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║        FlickerX Installer                ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
  echo ""

  check_deps
  detect_gpu
  setup_repo
  install_backend
  build_frontend
  create_shim
  summary
}

main "$@"
