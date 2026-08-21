<p align="center">
  <img src="frontend/public/flickerx-logo.svg" alt="FlickerX" width="400">
</p>

<p align="center">
  Local-first AI studio — chat, generate, train, research.
  <br>
  Universal model marketplace with GPU-accelerated inference.
</p>

<p align="center">
  <a href="CODE_OF_CONDUCT.md">Code of Conduct</a> •
  <a href="CONTRIBUTING.md">Contributing</a> •
  <a href="SECURITY.md">Security</a> •
  <a href="LICENSE">License</a>
</p>

---

## Features

| Feature | Description |
| ------- | ----------- |
| **Smart Chat** | Multi-model chat with SSE streaming, OpenAI-compatible API |
| **Model Hub** | Browse, download, and manage GGUF models from HuggingFace |
| **Image Generation** | Stable Diffusion via diffusers (CUDA/ROCm/Metal) |
| **Video Generation** | Text-to-video with diffusers pipelines |
| **Audio** | TTS/STT with faster-whisper |
| **Fine-tuning** | LoRA training with transformers |
| **RAG** | Retrieval-augmented generation with SQLite knowledge bases |
| **Deep Research** | Multi-step research agents with local LLMs |
| **Dataset Management** | HuggingFace dataset download and management |
| **Prompt Management** | Save, organize, and reuse prompt templates |
| **MCP Integration** | Model Context Protocol server probing |
| **Export** | GGUF quantization, LoRA export, HuggingFace Hub push |
| **User Auth** | JWT + refresh tokens, bcrypt, rate limiting, admin CRUD |
| **Dark Mode** | Full dark mode support |
| **GPU Acceleration** | CUDA, ROCm, Vulkan, Intel XPU, Apple Metal |

## Tech Stack

| Layer     | Tech |
| --------- | ---- |
| Frontend  | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend   | Python 3.10+, FastAPI, SQLite (aiosqlite), structlog |
| Auth      | JWT (HS256, 15min) + refresh tokens (30d, rotated) + bcrypt |
| AI        | llama-cpp-python (local), OpenRouter (cloud), diffusers |
| Storage   | SQLite database, local filesystem (`~/.flickerx/`) |
| GPU       | CUDA, ROCm, Vulkan, Intel XPU, Apple Metal, CPU fallback |
| Build     | uv (Python), npm (frontend), Vite (build) |

## Quick Start

### Install (recommended)

```bash
# Linux/macOS — auto-detects GPU
curl -sL https://raw.githubusercontent.com/joey/flickerx/main/install.sh | bash

# Or clone and install
git clone https://github.com/Joey-1123/FlickerX.git
cd FlickerX
bash install.sh
```

```powershell
# Windows (PowerShell)
.\install.ps1
```

### Manual Setup

```bash
git clone https://github.com/Joey-1123/FlickerX.git
cd FlickerX

# Backend
cd backend
uv venv && source .venv/bin/activate
uv sync

# Frontend
cd ../frontend
npm install
npm run build

# Run
cd ../backend
uv run python cli.py
# → http://127.0.0.1:8080
```

### GPU Selection

```bash
bash install.sh --gpu cuda     # NVIDIA CUDA
bash install.sh --gpu rocm     # AMD ROCm
bash install.sh --gpu vulkan   # Vulkan (cross-vendor)
bash install.sh --gpu intel    # Intel XPU
bash install.sh --gpu metal    # Apple Metal (macOS)
bash install.sh --gpu cpu      # CPU only
```

### Optional: Image/Video Generation

```bash
bash install.sh --with-torch   # installs torch + diffusers
# or:
cd backend && uv pip install -e ".[torch]"
```

## Scripts

| Command | Description |
| ------- | ----------- |
| `npm run FlickerX` | Production — single process, SPA serving |
| `npm run dev` | Development — Vite hot reload + backend |
| `npm run build` | Build frontend only |

### CLI Options

```bash
FlickerX                    # http://127.0.0.1:8080
FlickerX --port 3000        # custom port
FlickerX --host 0.0.0.0     # bind all interfaces
FlickerX --dev              # Vite dev mode (two processes)
```

## Project Structure

```
FlickerX/
├── install.sh               # Linux/macOS installer (GPU detection)
├── install.ps1              # Windows installer
├── package.json             # Root scripts (FlickerX, dev, build)
├── backend/
│   ├── main.py              # FastAPI app, SPA serving, router registration
│   ├── cli.py               # CLI entry point (FlickerX command)
│   ├── config.py            # Paths, constants, HOST, PORT
│   ├── database.py          # SQLite init, migrations, execute_returning()
│   ├── middleware.py         # Security headers, body size limit, logging
│   ├── auth.py              # JWT creation/verification, bcrypt
│   ├── pyproject.toml       # Python deps, [project.scripts]
│   └── routers/             # 18 API routers (262 endpoints)
│       ├── auth.py          # Register, login, logout, refresh, admin CRUD, API keys
│       ├── chat.py          # OpenAI-compatible chat completions (SSE)
│       ├── models.py        # Model listing, config, load/unload
│       ├── hub.py           # HuggingFace hub search, download, cache
│       ├── inference.py     # Local LLM inference (llama-cpp-python)
│       ├── images.py        # Image generation (diffusers)
│       ├── video.py         # Video generation (diffusers)
│       ├── audio.py         # TTS/STT (faster-whisper)
│       ├── train.py         # LoRA fine-tuning
│       ├── datasets.py      # Dataset management (HF snapshot_download)
│       ├── rag.py           # RAG (SQLite KBs, chunks, keyword search)
│       ├── research.py      # Research agents (llama-cpp local LLM)
│       ├── export.py        # GGUF export, LoRA export, HF Hub push
│       ├── providers.py     # External provider management (HTTP test)
│       ├── prompts.py       # Prompt entry/list management (SQLite)
│       ├── mcp.py           # MCP server probing (JSON-RPC)
│       ├── settings.py      # HF token, generation presets, upload limits
│       └── system.py        # Hardware info, GPU, metrics, logs
└── frontend/
    ├── vite.config.ts       # Proxy /api → :8080
    └── src/
        ├── features/        # 14 feature modules (chat, hub, images, etc.)
        ├── components/      # Shared UI (shadcn/ui)
        ├── hooks/           # Custom React hooks
        └── lib/             # Utilities, API client
```

## Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `FLICKERX_HOST` | `127.0.0.1` | Backend bind host |
| `FLICKERX_PORT` | `8080` | Backend bind port |
| `JWT_SECRET` | (generated) | JWT signing secret |
| `HF_TOKEN` | (none) | HuggingFace API token |

## Security

See [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities.

## Documentation

- [API Reference](docs/api-reference.md) — all 262 endpoints
- [User Guide](docs/user-guide.md) — step-by-step workflows
- [Architecture](docs/architecture.md) — system design and data flow
- [GPU Setup](docs/gpu-setup.md) — CUDA, ROCm, Metal, Vulkan, Intel XPU

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on commits, PRs, and code style.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.

## License

MIT — see [LICENSE](LICENSE) for details.
