# FlickerX Studio — System Architecture

## System Overview

FlickerX Studio is a self-hosted local AI workstation. A single FastAPI process
serves both the REST API and the React SPA, with all data stored under
`~/.flickerx/studio/`.

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (localhost:8080 or :5173 dev)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  React SPA (Vite)                                   │   │
│  │  TanStack Router · Zustand · Radix UI · Tailwind    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │  /api/*  /v1/*                     │
├─────────────────────────┼───────────────────────────────────┤
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI (uvicorn)                                   │   │
│  │                                                      │   │
│  │  Middleware stack (bottom → top):                     │   │
│  │    RequestLogging → BodySize(10 MB) → SecurityHeaders│   │
│  │    → CORS(origins:*)                                 │   │
│  │                                                      │   │
│  │  Routers:                                            │   │
│  │    auth · chat · images · video · audio · models     │   │
│  │    hub · inference · train · datasets · rag          │   │
│  │    research · export · providers · prompts · mcp     │   │
│  │    settings · system                                 │   │
│  │                                                      │   │
│  │  /v1 re-exports chat router (OpenAI-compatible)      │   │
│  └────┬───────────────────┬────────────────────────────┘   │
│       │                   │                                │
│       ▼                   ▼                                │
│  auth.db              studio.db                            │
│  (users, keys,        (chat, images, video, audio,         │
│   refresh tokens,      training, settings, providers,      │
│   settings)            mcp, datasets, rag, export)         │
│                                                             │
│  GPU: nvidia-smi → CUDA / Apple MPS → CPU fallback         │
│  Models: llama-cpp · diffusers · transformers              │
└─────────────────────────────────────────────────────────────┘
```

## Backend Architecture

### Entry point

`backend/main.py` — FastAPI app with async lifespan. On startup: create
directories, initialize both SQLite databases. On shutdown: log exit.

### Middleware chain

Applied in reverse order (last added runs first on inbound requests):

| Order | Middleware | Purpose |
|-------|-----------|---------|
| 1 | `RequestLoggingMiddleware` | Structured log (method, path, status, duration_ms). No PII. |
| 2 | `BodySizeMiddleware` | Reject `Content-Length > 10 MB` with 413. |
| 3 | `SecurityHeadersMiddleware` | Sets `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` on every response. |
| 4 | `CORSMiddleware` | Wildcard origins (local dev). Tighten for production. |

### Router system

Each domain gets its own file under `backend/routers/`. Routers are registered
in `main.py` with prefix + tag. The `/v1` prefix re-registers the chat router
for OpenAI-compatible endpoints.

| Prefix | Router | Responsibility |
|--------|--------|----------------|
| `/api/auth` | `auth.py` | Login, register, refresh, logout, API keys, password reset |
| `/api/chat` | `chat.py` | Thread management, message history, streaming |
| `/api/inference` | `inference.py` | Model loading, text generation, embeddings |
| `/api/models` | `models.py` | Model listing, download, quantization info |
| `/api/images` | `images.py` | Text-to-image, image-to-image, gallery |
| `/api/video` | `video.py` | Text-to-video, video gallery |
| `/api/audio` | `audio.py` | Text-to-speech, audio gallery |
| `/api/train` | `train.py` | Fine-tuning job management |
| `/api/hub` | `hub.py` | HuggingFace Hub integration |
| `/api/datasets` | `datasets.py` | Dataset management |
| `/api/rag` | `rag.py` | RAG pipeline, document ingestion |
| `/api/research` | `research.py` | Web research tool |
| `/api/export` | `export.py` | Model export |
| `/api/providers` | `providers.py` | External API provider config |
| `/api/prompts` | `prompts.py` | Prompt templates |
| `/api/mcp` | `mcp.py` | Model Context Protocol server management |
| `/api/settings` | `settings.py` | App settings CRUD |
| `/api/system` | `system.py` | System info, GPU status |

### Database layer

`backend/database.py` — raw `sqlite3`, no ORM. Two databases:

- **`auth.db`**: `users`, `api_keys`, `refresh_tokens`, `password_resets`, `settings`
- **`studio.db`**: `chat_threads`, `chat_messages`, `chat_folders`, `chat_projects`, `chat_attachments`, `image_gallery`, `video_gallery`, `audio_gallery`, `training_runs`, `provider_configs`, `mcp_servers`, `settings`

Both use WAL mode, foreign keys enabled, connection-per-request with explicit
close. Thread-safe via `_schema_lock` for init only.

Helper functions: `query()`, `execute()`, `execute_returning()`, `execute_many()`.
Each opens a fresh connection, runs the statement, commits, and closes.

Migrations run inline via `_run_migrations()` — each migration is a single
`ALTER TABLE ... ADD COLUMN` wrapped in try/except (idempotent).

## Frontend Architecture

### Stack

- **React 19** + TypeScript
- **Vite 8** (dev server + build)
- **TanStack Router** — file-based routing
- **Zustand** — state management
- **Radix UI** / **shadcn/ui** — component primitives
- **Tailwind CSS v4** — utility styling
- **@assistant-ui/react** — chat UI primitives

### Dev proxy

`vite.config.ts` proxies to backend:

| Pattern | Target |
|---------|--------|
| `/api/*` | `http://127.0.0.1:8080` |
| `/v1/*` | `http://127.0.0.1:8080` |
| `/seed/*`, `/preview`, `/validate`, `/tools` | `http://127.0.0.1:8004` |

### Feature modules

All under `src/features/`:

```
auth/               login, register, password reset
chat/               threads, messages, streaming, markdown
images/             gallery, generation UI
video/              gallery, generation UI
audio/              gallery, TTS UI
model-picker/       model selection, catalog
loaded-models/      active model management
training/           fine-tuning UI
datasets/           dataset browser
rag/                document ingestion, retrieval
research/           web search tool
export/             model export
hub/                HuggingFace integration
provider- configs/  external API settings
mcp/                MCP server management
settings/           app settings
profile/            user profile, password
security/           API keys
studio/             main layout
tour/               onboarding tour
generation-presets/  saved generation configs
```

### Layout

`src/app/` contains:
- `router.tsx` — TanStack Router definition
- `app.tsx` — root layout
- `provider.tsx` — context providers
- `auth-guards.ts` — route protection
- `routes/` — page components

## Data Flow

### Authenticated request

```
Browser
  │  POST /api/chat/messages
  │  Authorization: Bearer <access_token>
  ▼
CORSMiddleware
  │  (no-op, allows *)
  ▼
SecurityHeadersMiddleware
  │  (wraps response)
  ▼
BodySizeMiddleware
  │  check Content-Length ≤ 10 MB → 413
  ▼
RequestLoggingMiddleware
  │  record start time
  ▼
Router dispatch
  │  /api/chat/messages → chat.py
  ▼
get_current_user() dependency
  │  extract Bearer token
  │  decode JWT (HS256, SECRET_KEY)
  │  lookup user in auth.db
  │  → 401 if invalid/missing/expired
  ▼
Handler function
  │  query/studio.db via get_studio_conn()
  │  business logic
  ▼
Response
  │  structlog logged by RequestLoggingMiddleware
  │  security headers added
  │  CORS headers added
  ▼
Browser receives JSON
```

### Streaming chat (SSE)

```
Browser → POST /api/chat/stream → chat router
  │  SSE response (text/event-stream)
  │  each chunk: data: {"delta": "..."}\n\n
  ▼
Browser reads stream, appends to UI
```

## Storage Layout

All data lives under `~/.flickerx/studio/` (overridable via `FLICKERX_STUDIO_HOME`):

```
~/.flickerx/studio/
├── data/
│   ├── auth.db          # users, keys, tokens, settings
│   └── studio.db        # chat, images, video, audio, training
├── models/              # downloaded model weights
├── cache/               # temporary cache (HuggingFace hub cache)
└── logs/                # structured logs
```

Environment variables:
- `FLICKERX_STUDIO_HOME` — base directory (default `~/.flickerx/studio`)
- `FLICKERX_HOST` — bind address (default `127.0.0.1`)
- `FLICKERX_PORT` — bind port (default `8080`)
- `FLICKERX_SECRET_KEY` — JWT signing key (change in production)

## Auth Flow

### Token lifecycle

```
                    ┌──────────────┐
                    │  POST /login │
                    └──────┬───────┘
                           │  username + password
                           ▼
                    bcrypt.verify(password, hash)
                           │
                    ┌──────▼───────┐
                    │  Issue pair  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
       access_token               refresh_token
       (JWT, 30 min)              (opaque, 7 days)
       sub=<user_id>              SHA-256 hash stored
       type="access"              in refresh_tokens table

              │                         │
              ▼                         ▼
       Bearer in header           POST /api/auth/refresh
              │                         │
              ▼                         ▼
       get_current_user()         verify hash in DB
       decode JWT                 issue new pair
       lookup user                delete old refresh token
```

### Key details

- **Password hashing**: bcrypt via `passlib` (auto-deprecation)
- **JWT signing**: HS256 with `SECRET_KEY`
- **Refresh rotation**: each refresh is single-use; new pair issued on refresh
- **API keys**: SHA-256 hashed, prefix stored for lookup, optional expiry
- **Optional auth**: `get_optional_user()` returns `None` instead of 401
- **No rate limiting in code** — left to reverse proxy (nginx/Caddy) or future addition

## GPU Pipeline

`backend/gpu.py` — detection runs once per call (no caching, lazy is fine).

```
detect_gpu()
  │
  ├─ 1. nvidia-smi (subprocess, 5s timeout)
  │     → parse name, vram_total, vram_free
  │     → GPUInfo(device="cuda")
  │
  ├─ 2. torch.backends.mps.is_available() (macOS only)
  │     → GPUInfo(device="mps")
  │
  └─ 3. CPU fallback
        → GPUInfo(device="cpu")
```

### Inference paths

| Tool | Device selection | GPU layers |
|------|-----------------|------------|
| llama-cpp (local LLMs) | `get_device()` | `get_n_gpu_layers()` — all on GPU if available, else CPU |
| diffusers (image/video) | `get_torch_dtype()` — fp16 on CUDA, fp32 on CPU/MPS |
| transformers (TTS/embeddings) | `get_device()` | auto |

### Helpers

- `get_device()` → `"cuda"` / `"mps"` / `"cpu"`
- `get_n_gpu_layers(default=99)` → 99 if GPU, 0 if CPU
- `get_torch_dtype()` → `torch.float16` (CUDA) / `torch.float32` (rest)
- `is_cuda_available()` → bool

## SPA Serving

Production mode (`frontend/dist/` exists):

1. **`/assets/*`** → `_ImmutableStaticFiles` — Vite content-hashed assets served
   with `Cache-Control: public, max-age=31536000, immutable` (no revalidation).

2. **`/`** → serves `index.html` with `Cache-Control: no-cache, no-store, must-revalidate`.

3. **`/{any}`** → catch-all SPA route:
   - Rejects paths starting with `api/` or `v1/` (returns 404, not SPA fallback).
   - Checks path traversal: `file_path.is_relative_to(FRONTEND_DIST_RESOLVED)`.
   - If the resolved path is a file → serve it directly.
   - Otherwise → serve `index.html` (client-side routing handles it).

### Path traversal protection

```python
file_path = (FRONTEND_DIST / full_path).resolve()
if not file_path.is_relative_to(FRONTEND_DIST_RESOLVED):
    return Response(status_code=403)
```

This prevents `../../etc/passwd` style attacks. The resolved path must stay
within the dist directory.

### Dev mode

During development, `vite.config.ts` runs on `:5173` (or adjacent port) with
proxy rules forwarding `/api/*` and `/v1/*` to the backend on `:8080`. No
SPA catch-all needed — Vite handles it.
