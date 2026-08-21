<p align="center">
  <img src="frontend/public/flickerx-mascot.svg" alt="FlickerX Mascot" width="120">
</p>

<h1 align="center">FlickerX</h1>

<p align="center">
  Local-first AI studio — chat, generate, train, research.
  <br>
  Universal model marketplace with GPU-accelerated inference.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey" alt="Platform">
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
| **Fine-tuning** | LoRA, QLoRA, full fine-tune, DPO, GRPO, pre-training |
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
| Backend   | Python 3.10+, FastAPI, SQLite, structlog |
| Auth      | JWT (HS256) + refresh tokens + bcrypt |
| AI        | llama-cpp-python (local), OpenRouter (cloud), diffusers |
| Storage   | SQLite database, local filesystem (`~/.flickerx/`) |
| GPU       | CUDA, ROCm, Vulkan, Intel XPU, Apple Metal, CPU fallback |
| Build     | uv (Python), npm (frontend), Vite (build) |

## Quick Start

### Install (recommended)

```bash
# Clone and install — auto-detects GPU
git clone FlickerX
cd FlickerX
bash install.sh
```

```powershell
# Windows (PowerShell)
.\install.ps1
```

### Manual Setup

```bash
git clone FlickerX
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

## CLI

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
│   ├── database.py          # SQLite init, migrations
│   ├── middleware.py         # Security headers, body size limit, logging
│   ├── auth.py              # JWT creation/verification, bcrypt
│   └── routers/             # 18 API routers (~280 endpoints)
│       ├── auth.py          # Register, login, logout, refresh, admin, API keys
│       ├── chat.py          # OpenAI-compatible chat completions (SSE)
│       ├── models.py        # Local model scan, config, load/unload
│       ├── hub.py           # HuggingFace hub search, download, cache
│       ├── inference.py     # Local LLM inference (llama-cpp-python)
│       ├── images.py        # Image generation (diffusers)
│       ├── video.py         # Video generation (diffusers)
│       ├── audio.py         # TTS/STT (faster-whisper)
│       ├── train.py         # LoRA, QLoRA, full fine-tune, DPO, GRPO
│       ├── datasets.py      # Dataset management (HF snapshot_download)
│       ├── rag.py           # RAG (SQLite KBs, chunks, keyword search)
│       ├── research.py      # Research agents (llama-cpp local LLM)
│       ├── export.py        # GGUF export, LoRA export, HF Hub push
│       ├── providers.py     # External provider management
│       ├── prompts.py       # Prompt entry/list management
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
| `FLICKERX_SECRET_KEY` | (dev default) | JWT signing secret |
| `FLICKERX_STUDIO_HOME` | `~/.flickerx/studio` | Data directory |

## Security

See [SECURITY.md](SECURITY.md) for our security policy.

## Documentation

- [API Reference](docs/api-reference.md) — all endpoints
- [User Guide](docs/user-guide.md) — step-by-step workflows
- [Architecture](docs/architecture.md) — system design and data flow
- [GPU Setup](docs/gpu-setup.md) — CUDA, ROCm, Metal, Vulkan, Intel XPU

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.
