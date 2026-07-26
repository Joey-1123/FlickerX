# FlickerX — Project Handbook

## Overview

FlickerX is an AI chat and file intelligence platform. Users chat with AI models via OpenRouter, upload files to Cloudinary, and get structured answers — all through a dark-mode-ready React frontend with JWT auth.

**Goal:** Simple, maintainable, production-ready AI chat.

**Mission:** Build an AI chat platform that is maintainable, fast, privacy-conscious, secure, and easy to contribute to. Every decision should support this mission.

---

## Tech Stack

| Layer     | Tech                                                   |
| --------- | ------------------------------------------------------ |
| Frontend  | React 19, Vite, Tailwind CSS, React Router, Lucide     |
| Backend   | Express 5, Helmet, CORS, Cookie Parser                 |
| Auth      | JWT (access + refresh tokens), bcryptjs                |
| AI        | OpenRouter API (multi-model with automatic fallbacks)  |
| Storage   | Cloudinary (file uploads)                              |
| Validation| Zod                                                    |

---

## Design Principles

- Small modules with single responsibility
- Predictable, consistent APIs
- Explicit over implicit
- Minimal dependencies — stdlib first

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  React SPA  │────▶│  Express API │────▶│  OpenRouter  │
│  (Vite)     │     │  (Server)    │     │  (AI Models) │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │  Cloudinary  │
                    │  (Uploads)   │
                    └──────────────┘
```

### Layer Rules

```
backend/
  controllers/    HTTP only — parse request, delegate, respond
  services/       Business logic — AI calls, auth workflows
  middleware/     Cross-cutting — auth, rate limiting
  routes/         Route definitions only
  config/         Configuration only

frontend/
  src/
    pages/        Route-level components
    components/   Reusable UI
    services/     API client functions
    context/      React context providers
    utils/        Pure helper functions
```

**Flow constraints (never violate):**

```
Controller → Service → External API    ✓
Controller → Controller                 ✗
Service → Controller                    ✗
```

---

## Project Structure

```
FlickerX/
├── backend/
│   ├── config/           # Cloudinary config
│   ├── controllers/      # Route handlers
│   │   ├── authController.js
│   │   ├── chatController.js
│   │   └── uploadController.js
│   ├── middleware/        # Auth, rate limiting
│   │   ├── authMiddleware.js
│   │   └── rateLimit.js
│   ├── routes/            # Express route definitions
│   │   ├── authRoutes.js
│   │   ├── chatRoutes.js
│   │   ├── uploadRoutes.js
│   │   └── adminRoutes.js
│   ├── services/          # Business logic
│   │   ├── openrouterService.js
│   │   └── tokenService.js
│   ├── .env               # Local secrets (gitignored)
│   └── server.js          # Entry point
├── frontend/
│   ├── public/
│   │   ├── logo.svg
│   │   ├── favicon.svg
│   │   └── manifest.json
│   └── src/
│       ├── assets/
│       ├── auth/
│       │   └── AuthContext.jsx
│       ├── components/    # Reusable UI
│       │   ├── ChatBox.jsx
│       │   ├── ChatInput.jsx
│       │   ├── Navbar.jsx
│       │   ├── Sidebar.jsx
│       │   ├── ProtectedRoute.jsx
│       │   └── AdminRoute.jsx
│       ├── context/
│       │   └── ThemeContext.jsx
│       ├── pages/
│       │   ├── Chat.jsx
│       │   ├── Home.jsx
│       │   ├── Login.jsx
│       │   ├── Register.jsx
│       │   ├── Profile.jsx
│       │   ├── Admin.jsx
│       │   ├── About.jsx
│       │   ├── Contact.jsx
│       │   └── Policies.jsx
│       ├── services/
│       │   ├── api.js
│       │   ├── auth.js
│       │   └── admin.js
│       └── utils/
│           ├── models.js
│           └── sessions.js
├── AGENTS.md
├── CLAUDE.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── package.json
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/server.js` | Express entry point, middleware setup, route mounting |
| `backend/services/openrouterService.js` | AI model calls, fallback logic, error normalization |
| `backend/controllers/chatController.js` | Chat + streaming SSE endpoints |
| `backend/controllers/authController.js` | Register, login, refresh, logout, profile, password reset |
| `backend/middleware/authMiddleware.js` | JWT verification, admin check |
| `backend/middleware/rateLimit.js` | Per-endpoint rate limiting |
| `frontend/src/services/api.js` | API client: chat, stream, upload |
| `frontend/src/services/auth.js` | Auth API client |
| `frontend/src/pages/Chat.jsx` | Main chat UI with streaming |

---

## Model Configuration

Default model: `google/gemma-4-31b-it:free`

Fallback order (on rate-limit or failure):
1. `nvidia/nemotron-3-super-120b-a12b:free`
2. `poolside/laguna-m.1:free`
3. `inclusionai/ling-3.0-flash:free`
4. `openai/gpt-oss-20b:free`

All models are fetched at build time from `https://openrouter.ai/api/v1/models`.

---

## Environment Variables

### Backend `.env`

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OPENROUTER_BASE` | `https://openrouter.ai/api/v1/chat/completions` | API base URL |
| `OPENROUTER_TIMEOUT_MS` | `10000` | HTTP request timeout |
| `OPENROUTER_STREAM_TIMEOUT_MS` | `30000` | Stream timeout |
| `JWT_SECRET` | — | JWT signing secret |
| `JWT_ACCESS_EXPIRES` | `15m` | Access token TTL |
| `JWT_REFRESH_EXPIRES_SECONDS` | `2592000` (30d) | Refresh token TTL |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `RESET_TOKEN_EXPIRES_MS` | `3600000` (1h) | Password reset TTL |
| `RATE_LIMIT_CHAT_MAX` | `20` | Chat requests per window |
| `RATE_LIMIT_AUTH_MAX` | `10` | Auth requests per window |
| `RATE_LIMIT_WINDOW_MS` | `60000` | Rate limit window |
| `CLOUD_NAME` | — | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | — | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | — | Cloudinary secret |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin |
| `BCRYPT_SALT_ROUNDS` | `12` | Hash rounds |
| `PORT` | `5000` | Server port |

### Frontend `.env`

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE` | `http://localhost:5000` | Backend URL |

---

## Coding Standards

### JavaScript

```js
// Prefer
const                     // over let/var
async/await               // over .then()
optional chaining (?.)    // over && chains
early returns             // over deep if/else
destructuring             // over direct access
template literals         // over string concat

// Avoid
deep nesting (>3 levels)
magic numbers (name them)
duplicate logic
boolean flags as function params
hidden state / mutations
```

### Naming

```js
// Good
fetchUser()
getChatResponse()
parseJsonResponse()
FREE_FALLBACKS
OPENROUTER_BASE

// Bad
run()
temp()
newThing()
helper()
data
```

### Functions

- Single responsibility
- Descriptive names (verb + noun)
- Early return over nested if
- Pure where possible (no side effects)
- Ideal: 20-40 lines
- Maximum: ~80 lines before extraction

### Files

- Ideal: <300 lines
- Maximum: <500 lines (services)
- Split before navigation suffers

### React

- Functional components + hooks only
- No class components
- No prop drilling — use context or composition
- Memoize expensive computations (`useMemo`/`useCallback`)
- Avoid unnecessary re-renders

### CSS

- Tailwind CSS utility classes
- Dark mode via `dark:` prefix
- Consistent with `ThemeContext` accent colors

---

## API Guidelines

### Endpoints

- RESTful, predictable URLs
- Versioned via path (`/api/v1/...`) if needed
- Consistent JSON response shape
- POST for mutations, GET for reads

### Request/Response

```js
// Success
{ "reply": "..." }
{ "user": { ... } }

// Error
{ "error": "Human-readable message" }
```

### Rules

- Never leak stack traces to the client
- Validate input before business logic
- Keep handlers stateless
- Return appropriate HTTP status codes
- Rate-limit auth and chat endpoints separately

---

## Error Handling

### Backend

- Fail fast — validate at the boundary
- Throw descriptive errors with meaningful messages
- Log unexpected failures with context
- Never silently swallow exceptions
- Centralized error handler catches everything that slips through (`server.js:37`)
- 404 handler returns consistent `{"error":"Route not found."}`

### Frontend

- Catch API errors and show toast notifications
- Never expose raw error objects to users
- Graceful degradation on network failure

### Error Messages

```
Bad:  "Failed."
Good: "Failed to upload image: Cloudinary returned HTTP 403."
```

---

## Security

### Rules

| Rule | Enforcement |
|------|-------------|
| Validate all input | Zod schemas + middleware |
| Escape all output | React auto-escapes |
| Secrets from env only | `process.env.*`, gitignored `.env` |
| HTTPS only | Set `NODE_ENV=production` |
| Rate limiting | `express-rate-limit` per endpoint |
| Authentication | JWT required for protected routes |
| Authorization | Admin check on admin routes |
| Cookies | `httpOnly: true`, `sameSite: "strict"`, `secure` in production |

### Never

- Hardcode secrets
- Commit API keys or tokens
- Trust client input without validation
- Disable validation for convenience
- Bypass authentication
- Log passwords, tokens, or API keys

### Security Checklist

- [ ] Input validated
- [ ] Output escaped
- [ ] Queries parameterized
- [ ] Least privilege applied
- [ ] Secrets from environment
- [ ] HTTPS enforced
- [ ] Rate limiting active
- [ ] Authentication verified
- [ ] Authorization checked

---

## Logging

Logs should explain: **what happened**, **why**, and **relevant identifiers**.

```js
console.error("Chat failed:", err.message);       // ✓
console.log(`User ${userId} logged in`);           // ✓
console.log(`Password reset link: ${resetUrl}`);   // ✗ (leaks token)
console.log("Decoded token:", decodedUnsafe);     // ✗ (leaks secrets)
```

### Never log

- Passwords
- Tokens (JWT, API keys, reset tokens)
- Session secrets
- Personal identifiable information

---

## Performance

### Avoid

- N+1 loops over API calls
- Duplicate network requests
- Blocking filesystem operations in request handlers
- Large JSON parse/copy in hot paths
- Repeated parsing of the same data

### Prefer

- Streaming over buffering (SSE for chat)
- Pagination over loading all data
- Debouncing rapid user input
- Memoizing expensive computations

---

## Testing Policy

- Non-trivial logic leaves one runnable check (inline `__main__` or `test_*.py`)
- No test frameworks unless explicitly requested
- Every bug fix includes: reproduction → fix → verification
- Priority: unit → integration → end-to-end
- Prefer fast tests that cover the actual failure mode

---

## Commands

```bash
# Development
npm run dev                   # Both frontend + backend
npm run backend               # Backend only
npm run frontend              # Frontend only

# Verification
cd frontend && npm run lint   # ESLint
node -c backend/server.js     # Syntax check
node -c backend/controllers/*.js
node -c backend/services/*.js
node -c backend/middleware/*.js
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

| Package | Version | Purpose |
|---------|---------|---------|
| express | ^5.0.0 | HTTP server |
| react | ^19.0.0 | UI framework |
| vite | ^6.0.0 | Build tool |
| tailwindcss | ^3.4.0 | CSS utility framework |
| axios | ^1.16.0 | HTTP client (backend) |
| zod | ^4.4.0 | Schema validation |

---

## Git Workflow

```
Branch (feat/my-change)
    ↓
Implement
    ↓
Syntax check
    ↓
Lint (frontend)
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
- Coverage reports
- Log files
- Cache directories
- API keys or secrets

---

## Code Review Checklist

Before committing, ask:

- [ ] Can this be deleted?
- [ ] Can this be shorter?
- [ ] Can stdlib solve it?
- [ ] Will a new contributor understand it?
- [ ] Does this duplicate existing logic?
- [ ] Are there edge cases not handled?
- [ ] Are there security implications?

---

## Refactoring Rules

Refactoring should never change behavior, API shape, or output format — unless explicitly requested. One change per refactor.

---

## Code Smells

Watch for:

- Magic numbers without named constants
- Duplicate code blocks
- Functions over 80 lines
- Boolean flags as function parameters
- Deep nesting (>3 levels)
- Hidden mutations of input data
- Circular imports

---

## Repository Invariants

These must always remain true:

- Authentication is never bypassed
- No secrets committed to git
- API responses are backwards compatible
- No breaking route changes without deprecation
- Error responses always include an `error` field
- The app starts with `npm run dev`

---

## Recovery Strategy

If an implementation fails:
1. Undo the change
2. Identify root cause (why did it fail?)
3. Retry with a simpler approach
4. Never stack speculative fixes on top of broken ones

---

## Future Roadmap

Current priority areas (unordered):

- Authentication and session management
- Real-time streaming (SSE)
- Multi-model routing with fallbacks
- File upload and analysis
- Chat history and persistence
- Admin dashboard
- PWA offline support

---

## License

MIT — see [LICENSE](LICENSE).

---

## More Information

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
