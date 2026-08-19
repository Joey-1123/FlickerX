# FlickerX — Project Handbook

## Overview

FlickerX is a local-first AI studio — universal model marketplace with GPU-accelerated inference. Chat, generate images/video, fine-tune models, run RAG, and manage datasets — all from a single process.

**Goal:** Simple, maintainable, production-ready AI studio.

**Mission:** Build an AI platform that is maintainable, fast, privacy-conscious, secure, and easy to contribute to. Every decision should support this mission.

---

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

---

## Design Principles

- Small modules with single responsibility
- Predictable, consistent APIs
- Explicit over implicit
- Minimal dependencies — stdlib first
- Local-first — no external services required

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Frontend (React)                │
│  Vite dev server :5173 → proxy /api, /v1 → :8080│
└──────────────────────┬──────────────────────────┘
                       │ HTTP + SSE
┌──────────────────────▼──────────────────────────┐
│                Backend (FastAPI)                  │
│  Python 3.10+, 18 routers, 262 endpoints        │
│  SQLite (WAL mode), JWT auth, structlog          │
├──────────────────────────────────────────────────┤
│  Routers:                                        │
│    auth.py      → /api/auth/*        (15+ eps)  │
│    chat.py      → /api/chat/* + /v1/* (30+ eps) │
│    models.py    → /api/models/*      (15+ eps)  │
│    hub.py       → /api/hub/*         (25+ eps)  │
│    inference.py → /api/inference/*   (10+ eps)  │
│    images.py    → /api/images/*      (8+ eps)   │
│    video.py     → /api/video/*       (6+ eps)   │
│    audio.py     → /api/audio/*       (8+ eps)   │
│    train.py     → /api/train/*       (10+ eps)  │
│    datasets.py  → /api/datasets/*    (8+ eps)   │
│    rag.py       → /api/rag/*         (10+ eps)  │
│    research.py  → /api/research/*    (6+ eps)   │
│    export.py    → /api/export/*      (8+ eps)   │
│    providers.py → /api/providers/*   (6+ eps)   │
│    prompts.py   → /api/prompts/*     (8+ eps)   │
│    mcp.py       → /api/mcp/*         (6+ eps)   │
│    settings.py  → /api/settings/*    (6+ eps)   │
│    system.py    → /api/system/*      (10+ eps)  │
├──────────────────────────────────────────────────┤
│  Storage:                                        │
│    ~/.flickerx/studio/auth.db   (users, keys)   │
│    ~/.flickerx/studio/studio.db (projects, RAG) │
│    ~/.flickerx/studio/models/   (GGUF files)    │
│    ~/.flickerx/studio/cache/    (HF cache)      │
└──────────────────────────────────────────────────┘
```

### Layer Rules

```
Router → Service → External API    ✓
Router → Router                    ✗
Service → Router                   ✗
```

- **Routers:** HTTP only — parse request, delegate, respond
- **Services:** Business logic — no `req`/`res`
- **Middleware:** Cross-cutting concerns only — auth, rate limiting

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, SPA serving, router registration, middleware |
| `backend/cli.py` | CLI entry point (`FlickerX` command) |
| `backend/config.py` | Paths, secrets, ports, token expiry |
| `backend/database.py` | SQLite setup, schema, migrations, `execute_returning()` |
| `backend/auth.py` | JWT creation/validation, bcrypt hashing |
| `backend/middleware.py` | Security headers, body size limit, request logging |
| `backend/pyproject.toml` | Python deps, optional `[torch]` extras |
| `frontend/vite.config.ts` | Vite config, proxy → :8080 |

---

## Startup Commands

```bash
# Production — single process, single port
cd backend && uv run python cli.py               # http://127.0.0.1:8080
cd backend && uv run python cli.py --port 3000   # custom port

# Development — Vite hot reload
cd backend && uv run python cli.py --dev
npm run dev

# Build frontend
npm run build

# uv dependency management
cd backend && uv sync
cd backend && uv add <package>
```

---

## Installation

### Quick install

```bash
bash install.sh                    # auto-detect GPU
bash install.sh --gpu cuda         # force NVIDIA CUDA
bash install.sh --gpu rocm         # force AMD ROCm
bash install.sh --gpu vulkan       # force Vulkan
bash install.sh --gpu intel        # force Intel XPU
bash install.sh --gpu metal        # force Apple Metal
bash install.sh --gpu cpu          # CPU only
bash install.sh --with-torch       # + image/video generation
```

### Windows

```powershell
.\install.ps1                     # auto-detect
.\install.ps1 -Gpu cuda           # force CUDA
.\install.ps1 -WithTorch          # + torch
```

### GPU Backends

| Backend | Pre-built wheel | Detection |
|---------|----------------|-----------|
| NVIDIA CUDA | `cu118`–`cu130` | `nvidia-smi` |
| AMD ROCm | `rocm72` (Linux), `hip-radeon` (Windows) | `rocm-smi`, WMI |
| Intel XPU | Build from source (SYCL) | WMI, `sycl-ls` |
| Vulkan | `vulkan` | `vulkaninfo` |
| Apple Metal | `metal` | macOS auto |
| CPU | fallback | none detected |

---

## Coding Standards

### Python

```python
# Prefer
type hints              # on all public functions
async/await             # for I/O
early return            # over deep if/else
f-strings               # over .format()
dataclasses/Pydantic    # over raw dicts

# Avoid
deep nesting (>3 levels)
magic numbers (name them)
duplicate logic
boolean flags as function params
```

### TypeScript

```typescript
// Prefer
const                   // over let/let
async/await             // over .then()
optional chaining (?.)  // over && chains
early returns           // over deep if/else

// Avoid
deep nesting (>3 levels)
magic numbers
duplicate logic
```

### Naming

```
fetchUser()           ✓
getChatResponse()     ✓
run()                 ✗
temp()                ✗
helper()              ✗
```

### Functions

- Single responsibility
- Descriptive verb+noun names
- Early return over nested if
- Pure where possible (no side effects)
- Ideal: 20-40 lines
- Maximum: ~80 lines before extraction

### Files

- Ideal: <300 lines
- Maximum: <500 lines
- Split before navigation suffers

---

## API Guidelines

### Endpoints

- RESTful, predictable URLs
- Consistent JSON response shape
- POST for mutations, GET for reads
- SSE for real-time streaming

### Response Shape

```json
{ "status": "ok", "data": { ... } }
{ "error": "Human-readable message" }
```

### Rules

- Never leak stack traces to the client
- Validate input before business logic
- Keep handlers stateless
- Return appropriate HTTP status codes
- Rate-limit auth endpoints

---

## Error Handling

- Fail fast — validate at the boundary
- Throw descriptive errors with meaningful messages
- Log unexpected failures with context
- Never silently swallow exceptions
- Never leak stack traces to the client

```
Bad:  "Failed."
Good: "Failed to upload image: Cloudinary returned HTTP 403."
```

---

## Security

### Rules

| Rule | Enforcement |
|------|-------------|
| Validate all input | Pydantic v2 schemas |
| Escape all output | React auto-escapes |
| Secrets from env only | `process.env.*`, gitignored `.env` |
| Rate limiting | FastAPI middleware |
| Authentication | JWT required for protected routes |
| Authorization | Admin check on admin routes |

### Never

- Hardcode secrets
- Commit API keys or tokens
- Trust client input without validation
- Disable validation for convenience
- Bypass authentication
- Log passwords, tokens, or API keys

---

## Logging

Logs should explain: **what happened**, **why**, and **relevant identifiers**.

```python
structlog.info("user_login", user_id=user.id)           # ✓
structlog.info("password_reset_token", token=reset_url)  # ✗ (leaks token)
```

### Never log

- Passwords
- Tokens (JWT, API keys, reset tokens)
- Session secrets
- Personal identifiable information

---

## Testing Policy

- Non-trivial logic leaves one runnable check
- Bug fixes: reproduce → fix → verify
- No test frameworks unless explicitly requested
- Priority: unit → integration → end-to-end

---

## Commands

```bash
# Development
npm run dev                   # Both frontend + backend
npm run backend               # Backend only
npm run frontend              # Frontend only

# Production
npm run FlickerX              # Single process SPA

# Verification
cd frontend && npm run lint   # ESLint
cd backend && python -c "import main"  # Syntax check
```

---

## Dependencies

### Policy

Before adding a package, ask:

1. Can stdlib solve it?
2. Can an existing dependency solve it?
3. Is the maintenance burden worth it?
4. Is the package actively maintained?
5. Is the license compatible?
6. Does the community trust it?

### Current Key Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | HTTP server |
| uvicorn | ASGI server |
| llama-cpp-python | GGUF inference |
| pydantic | Validation |
| structlog | Logging |
| aiosqlite | SQLite async |
| huggingface-hub | Model downloads |
| psutil | System metrics |

---

## Git Workflow

```
Branch (feat/my-change)
    ↓
Implement
    ↓
Verify (syntax + lint)
    ↓
Commit (conventional)
    ↓
Push
    ↓
Pull Request
```

### Commit Style

```
feat:      new feature
fix:       bug fix
refactor:  code change with no feature/fix
chore:     maintenance, tooling, deps
docs:      documentation
security:  security fix
```

Every commit should compile, pass checks, be reversible, and represent one logical change.

### Never Commit

- `node_modules/`
- `.env` files
- `dist/`, `build/`
- `__pycache__/`
- `.venv/`
- API keys or secrets

---

## Repository Invariants

These must always remain true:

- Authentication is never bypassed
- No secrets committed to git
- API responses are backwards compatible
- No breaking route changes without deprecation
- Error responses always include an `error` field
- The app starts with `npm run dev` or `FlickerX`

---

## Recovery Strategy

If an implementation fails:
1. Undo the change
2. Identify root cause (why did it fail?)
3. Retry with a simpler approach
4. Never stack speculative fixes on top of broken ones

---

## License

MIT — see [LICENSE](LICENSE).

---

## More Information

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
