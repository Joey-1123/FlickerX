<#
.SYNOPSIS
    FlickerX Installer for Windows
.DESCRIPTION
    Detects GPU (NVIDIA CUDA, AMD ROCm/HIP, Vulkan, Intel XPU), installs
    llama-cpp-python with the right backend, optional torch+diffusers.
.PARAMETER Gpu
    Force GPU backend: cuda, rocm, vulkan, intel, cpu (default: auto-detect)
.PARAMETER WithTorch
    Also install torch+diffusers for image/video generation
.PARAMETER InstallDir
    Installation directory (default: $env:USERPROFILE\.flickerx)
.EXAMPLE
    .\install.ps1
    .\install.ps1 -Gpu cuda -WithTorch
    .\install.ps1 -Gpu cpu
#>
param(
    [ValidateSet("cuda", "rocm", "vulkan", "intel", "cpu")]
    [string]$Gpu = "",
    [switch]$WithTorch,
    [string]$InstallDir = "$env:USERPROFILE\.flickerx"
)

$ErrorActionPreference = "Stop"
$ShimDir = "$env:USERPROFILE\.local\bin"
$VenvDir = "$InstallDir\venv"

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Info    { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Cyan }
function Write-Ok      { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn    { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Fail    { param($Msg) Write-Host "[FAIL]  $Msg" -ForegroundColor Red; exit 1 }

# ── Check dependencies ───────────────────────────────────────────────────────

function Test-Dependencies {
    Write-Info "Checking dependencies..."

    # Python 3.10+
    $py = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
    if (-not $py) { Write-Fail "Python 3 not found. Install Python 3.10+ from https://python.org" }

    $ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    $major, $minor = $ver.Split(".")
    if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
        Write-Fail "Python $ver found, need 3.10+."
    }
    Write-Ok "Python $ver"

    # uv
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Info "Installing uv..."
        irm https://astral.sh/uv/install.ps1 | iex
        $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
    }
    Write-Ok "uv installed"

    # Node.js
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        Write-Warn "Node.js not found — frontend build skipped."
        Write-Warn "Install Node.js 18+ from https://nodejs.org"
    } else {
        $nodeVer = & node --version 2>$null
        Write-Ok "Node.js $nodeVer"
    }

    # Git
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) { Write-Fail "git not found." }
    Write-Ok "git"
}

# ── GPU detection ────────────────────────────────────────────────────────────

function Detect-NvidiaCuda {
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $nvidiaSmi) { return $false }

    $smi = & nvidia-smi 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }

    $match = [regex]::Match($smi, 'CUDA Version:\s+(\d+)\.(\d+)')
    if (-not $match.Success) { return $false }

    $cuMajor = [int]$match.Groups[1].Value
    $cuMinor = [int]$match.Groups[2].Value

    if ($cuMajor -ge 13)       { $script:GpuBackend = "cu130" }
    elseif ($cuMajor -eq 12 -and $cuMinor -ge 5) { $script:GpuBackend = "cu125" }
    elseif ($cuMajor -eq 12 -and $cuMinor -ge 4) { $script:GpuBackend = "cu124" }
    elseif ($cuMajor -eq 12 -and $cuMinor -ge 3) { $script:GpuBackend = "cu123" }
    elseif ($cuMajor -eq 12 -and $cuMinor -ge 2) { $script:GpuBackend = "cu122" }
    elseif ($cuMajor -eq 12 -and $cuMinor -ge 1) { $script:GpuBackend = "cu121" }
    elseif ($cuMajor -eq 11 -and $cuMinor -ge 8) { $script:GpuBackend = "cu118" }
    else { Write-Warn "CUDA $cuMajor.$cuMinor — no matching wheel."; return $false }

    $script:TorchIndex = "https://download.pytorch.org/whl/cu${cuMajor}${cuMinor}"

    $gpuName = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1
    Write-Ok "NVIDIA GPU: $gpuName (CUDA $cuMajor.$cuMinor -> $($script:GpuBackend))"
    return $true
}

function Detect-AmdRocm {
    $rocmSmi = Get-Command rocm-smi -ErrorAction SilentlyContinue
    $lspci = Get-Command lspci -ErrorAction SilentlyContinue

    $found = $false
    if ($rocmSmi) { $found = $true }
    elseif ($lspci) {
        $gpu = & lspci 2>$null | Select-String -Pattern "AMD|Radeon|Navi"
        if ($gpu) { $found = $true }
    }
    else {
        # Check WMI for AMD GPU
        $wmi = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -match "AMD|Radeon" }
        if ($wmi) { $found = $true }
    }

    if (-not $found) { return $false }

    $script:GpuBackend = "hip-radeon"
    Write-Ok "AMD GPU detected -> $($script:GpuBackend)"
    return $true
}

function Detect-Vulkan {
    $vulkaninfo = Get-Command vulkaninfo -ErrorAction SilentlyContinue
    if (-not $vulkaninfo) { return $false }

    $info = & vulkaninfo 2>$null
    if ($info -match "GPU") {
        $script:GpuBackend = "vulkan"
        Write-Ok "Vulkan GPU detected -> $($script:GpuBackend)"
        return $true
    }
    return $false
}

function Detect-Intel {
    $wmi = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -match "Intel|Arc|Iris" }
    if (-not $wmi) { return $false }

    $script:GpuBackend = "sycl"
    Write-Ok "Intel GPU detected: $($wmi.Name) -> $($script:GpuBackend)"
    return $true
}

function Detect-Gpu {
    if ($Gpu) {
        switch ($Gpu) {
            "cuda"   { if (-not (Detect-NvidiaCuda)) { Write-Fail "CUDA forced but nvidia-smi not found." } }
            "rocm"   { if (-not (Detect-AmdRocm))   { Write-Fail "ROCm forced but not detected." } }
            "vulkan" { $script:GpuBackend = "vulkan"; Write-Ok "Forced Vulkan" }
            "intel"  { $script:GpuBackend = "sycl";   Write-Ok "Forced Intel SYCL" }
            "cpu"    { $script:GpuBackend = "cpu";    Write-Ok "Forced CPU-only" }
        }
        return
    }

    Write-Info "Detecting GPU..."
    if (Detect-NvidiaCuda) { return }
    if (Detect-AmdRocm)    { return }
    if (Detect-Intel)      { return }
    if (Detect-Vulkan)     { return }

    Write-Warn "No GPU detected — falling back to CPU."
    $script:GpuBackend = "cpu"
}

# ── Clone / update ───────────────────────────────────────────────────────────

function Update-Repo {
    if (Test-Path "$InstallDir\.git") {
        Write-Info "Updating existing install..."
        git -C $InstallDir pull --ff-only 2>$null
    } else {
        Write-Info "Cloning FlickerX..."
        git clone "https://github.com/joey/flickerx.git" $InstallDir
    }
}

# ── Install backend ──────────────────────────────────────────────────────────

function Install-Backend {
    Write-Info "Creating venv..."
    uv venv $VenvDir
    & "$VenvDir\Scripts\Activate.ps1"

    Write-Info "Installing llama-cpp-python ($($script:GpuBackend))..."
    if ($script:GpuBackend -eq "cpu") {
        # Try pre-built wheel first (no compiler needed)
        $installed = $false
        try {
            uv pip install "llama-cpp-python[server]>=0.3.0" --only-binary llama-cpp-python --quiet 2>$null
            $installed = $true
        } catch {}
        if (-not $installed) {
            # No pre-built wheel — need MSVC compiler
            $hasCl = Get-Command cl.exe -ErrorAction SilentlyContinue
            if (-not $hasCl) {
                Write-Fail "No pre-built wheel available and no C compiler found."
                Write-Info "Install Visual Studio Build Tools with C++ workload:"
                Write-Info "  https://aka.ms/vs/17/release/vs_BuildTools.exe"
                Write-Info "Select 'Desktop development with C++' workload, then re-run this installer."
                exit 1
            }
            uv pip install "llama-cpp-python[server]>=0.3.0" --quiet
        }
    } elseif ($script:GpuBackend -eq "cu*") {
        uv pip install "llama-cpp-python[server]>=0.3.0" `
            --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/$($script:GpuBackend)" --quiet
    } elseif ($script:GpuBackend -match "^(rocm|hip-radeon)$") {
        uv pip install "llama-cpp-python[server]>=0.3.0" `
            --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/$($script:GpuBackend)" --quiet
    } elseif ($script:GpuBackend -eq "vulkan") {
        uv pip install "llama-cpp-python[server]>=0.3.0" `
            --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/vulkan" --quiet
    } elseif ($script:GpuBackend -eq "sycl") {
        $env:CMAKE_ARGS = "-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx"
        uv pip install "llama-cpp-python[server]>=0.3.0" --quiet
    }
    Write-Ok "llama-cpp-python installed."

    Write-Info "Installing remaining dependencies..."
    uv pip install `
        fastapi "uvicorn[standard]>=0.34.0" "pydantic>=2.0" `
        "pyjwt>=2.10.0" "passlib[bcrypt]>=1.7.4" "bcrypt==4.0.1" `
        "aiosqlite>=0.20.0" "structlog>=24.0" "httpx>=0.27.0" `
        "python-multipart>=0.0.9" "huggingface-hub>=0.27.0" `
        "psutil>=5.9.0" --quiet
    Write-Ok "Backend dependencies installed."

    if ($WithTorch) {
        Write-Info "Installing torch + diffusers..."
        if ($script:TorchIndex) {
            uv pip install torch diffusers --index-url $script:TorchIndex --quiet
        } else {
            uv pip install torch diffusers --quiet
        }
        uv pip install transformers accelerate safetensors Pillow --quiet
        Write-Ok "torch + diffusers installed."
    }
}

# ── Build frontend ───────────────────────────────────────────────────────────

function Build-Frontend {
    $node = Get-Command node -ErrorAction SilentlyContinue
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $node -or -not $npm) {
        Write-Warn "Skipping frontend build (Node.js not found)."
        return
    }

    Write-Info "Building frontend..."
    Push-Location "$InstallDir\frontend"
    npm ci --silent 2>$null
    npm run build --silent 2>$null
    Pop-Location
    Write-Ok "Frontend built."
}

# ── Create shim ──────────────────────────────────────────────────────────────

function New-Shim {
    New-Item -ItemType Directory -Force -Path $ShimDir | Out-Null

    $shimContent = @"
`$env:VIRTUAL_ENV = "$VenvDir"
& "$VenvDir\Scripts\python.exe" "$InstallDir\backend\cli.py" @args
"@

    Set-Content -Path "$ShimDir\FlickerX.ps1" -Value $shimContent -Encoding UTF8
    Write-Ok "Shim created: $ShimDir\FlickerX.ps1"

    # Check PATH
    if ($env:PATH -notlike "*$ShimDir*") {
        Write-Warn "$ShimDir is not in your PATH."
        Write-Warn "Add it in PowerShell: `$env:PATH = `"$ShimDir;`$env:PATH`""
    }
}

# ── Summary ──────────────────────────────────────────────────────────────────

function Show-Summary {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "  FlickerX installed successfully!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Install dir:  $InstallDir"
    Write-Host "  Venv:         $VenvDir"
    Write-Host "  GPU backend:  $($script:GpuBackend)"
    $torchStatus = if ($WithTorch) { "installed" } else { "not installed (use -WithTorch)" }
    Write-Host "  Torch:        $torchStatus"
    Write-Host ""
    Write-Host "  Launch (PowerShell):"
    Write-Host "    $ShimDir\FlickerX.ps1"
    Write-Host "  Launch (cmd):"
    Write-Host "    $VenvDir\Scripts\python.exe $InstallDir\backend\cli.py"
    Write-Host ""
}

# ── Main ─────────────────────────────────────────────────────────────────────

$script:GpuBackend = "cpu"
$script:TorchIndex = ""

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "      FlickerX Installer (Windows)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Test-Dependencies
Detect-Gpu
Update-Repo
Install-Backend
Build-Frontend
New-Shim
Show-Summary
