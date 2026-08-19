# Contributing to FlickerX

Thanks for your interest in contributing!

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-change`
3. Make your changes
4. Verify: `cd backend && python -c "import main"` and `cd frontend && npm run lint`
5. Commit with a clear message: `git commit -m "feat: add ..."`
6. Push and open a Pull Request

## Setup

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
```

## Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `refactor:` — code change without feature or fix
- `chore:` — maintenance, tooling, deps
- `docs:` — documentation only
- `security:` — security fix

## Code Style

### Python (Backend)

- Python 3.10+
- FastAPI for HTTP
- Pydantic v2 for validation
- Structured logging via `structlog`
- No ORM — raw sqlite3 with `execute_returning()` helper
- Type hints on all public functions
- Early return over nested if
- Single responsibility per function
- Ideal: 20-40 lines per function, <300 lines per file

### TypeScript (Frontend)

- React 19 with hooks, functional components only
- TypeScript strict mode
- Tailwind CSS for styling
- shadcn/ui components
- No class components
- No prop drilling — use context or composition

### General

- Reuse existing patterns — look before you write
- Prefer standard library over custom utilities
- No commented-out code or stale tracking comments
- No new dependencies without discussion
- Security: never hardcode secrets, validate all input

## Architecture

```
Controller → Service → External API    ✓
Controller → Controller                 ✗
Service → Controller                    ✗
```

- **Controllers (routers/):** HTTP only — parse request, delegate, respond
- **Services:** Business logic — no `req`/`res`
- **Middleware:** Cross-cutting concerns only — auth, rate limiting

## Pull Request Process

1. Link any related issues
2. Describe what changed and why
3. Keep PRs focused — one feature/fix per PR
4. Ensure the app starts: `cd backend && uv run python cli.py`
5. Run lint: `cd frontend && npm run lint`

## Testing

- Non-trivial logic leaves one runnable check
- Bug fixes: reproduce → fix → verify
- No test frameworks unless explicitly requested
