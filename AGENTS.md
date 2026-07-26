# FlickerX — Agent Instructions

This file governs how AI coding agents operate on this repository.

---

## Core Principles

Priority (highest → lowest):

1. **Correctness** — code must work, edge cases handled
2. **Security** — never bypass auth, leak secrets, or skip validation
3. **Simplicity** — shortest correct solution, YAGNI, stdlib first
4. **Performance** — streaming over buffering, no N+1, no blocking I/O
5. **Developer convenience** — readability, predictability

Never sacrifice correctness or security for simplicity.

---

## Decision Framework

When multiple solutions exist, climb the ladder:

1. **Does this need to exist at all?** (YAGNI — skip speculative code)
2. **Already in this codebase?** Reuse it — look before you write
3. **Stdlib does it?** Use it
4. **Native platform feature covers it?** `<input type="date">` over a picker lib
5. **Existing dependency solves it?** Never add a new one for what a few lines cover
6. **Can it be one line?** One line
7. **Only then:** the minimum code that works

---

## Before Editing

Read and understand the full flow before making any change:

- Read the files you plan to edit
- Check neighbouring files for conventions and patterns
- Grep every caller of any function you touch
- Read imports, exports, tests, config, and related docs
- Understand the actual data flow end-to-end

**Never edit in isolation.** The smallest change in the wrong place creates a second bug.

---

## Fix Root Causes

Never patch symptoms:

- Identify why the bug occurred
- Find the first bad assumption
- One root fix beats ten caller fixes
- If you find the same pattern elsewhere, fix it there too

---

## After Editing

- Syntax check backend files with `node -c`
- Run `cd frontend && npm run lint` for frontend
- Remove dead code (commented blocks, unused imports, stale tracking comments)
- Verify the app starts: `npm run dev`
- Ensure no TODOs or debugging artifacts remain

---

## Commit Style

```
feat:      new feature
fix:       bug fix
refactor:  code change with no feature/fix
chore:     maintenance, tooling, deps
docs:      documentation only
security:  security fix
```

Every commit should compile, pass checks, be reversible, and represent one logical change. Use `git add -p` to split hunks when a file has multiple unrelated changes.

---

## Code Quality Checklist

Before committing, ask:

- [ ] Can this be deleted?
- [ ] Can this be shorter?
- [ ] Can stdlib solve it?
- [ ] Will a new contributor understand it?
- [ ] Does this duplicate existing logic?
- [ ] Are there edge cases not handled?
- [ ] Are there security implications?

---

## File and Function Guidelines

| Scope | Ideal | Maximum |
|-------|-------|---------|
| Function | 20-40 lines | ~80 lines |
| File | <300 lines | <500 lines (services) |

### Functions

- Single responsibility
- Descriptive verb+noun names
- Early return over nested if
- Pure where possible (no side effects)
- No boolean flags as function parameters

### Naming

```
fetchUser()           ✓
getChatResponse()     ✓
run()                 ✗
temp()                ✗
helper()              ✗
```

---

## Security Rules

**Never:**
- Hardcode secrets or API keys
- Commit `.env` files or tokens
- Trust client input without validation (Zod schemas)
- Disable validation for convenience
- Bypass authentication
- Log passwords, tokens, secrets, or PII

### Security Checklist

- Input validated at the boundary
- Output escaped (React auto-escapes)
- Secrets from `process.env.*` only
- Rate limiting active on auth and chat endpoints
- Authorization checked on admin routes

---

## Error Handling

- Fail fast — validate at the boundary
- Throw descriptive errors: `"Failed to upload image: Cloudinary returned HTTP 403"`
- Never: `"Failed."`
- Log unexpected failures with context
- Never silently swallow exceptions
- Never leak stack traces to the client

---

## Architecture Constraints

```
Controller → Service → External API    ✓
Controller → Controller                 ✗
Service → Controller                    ✗
```

### Layer Rules

- **Controllers:** HTTP only — parse request, delegate, respond
- **Services:** Business logic only — no `req`/`res`
- **Middleware:** Cross-cutting concerns only — auth, rate limiting
- **Routes:** Route definitions only — no logic

---

## Dependencies

Before adding a package:
1. Can stdlib solve it?
2. Can an existing dependency solve it?
3. Is the maintenance burden worth it?
4. Is the package actively maintained?
5. Is the license compatible?
6. Does the community trust it?

---

## AI Behaviour Rules

### When uncertain
- Search the project for existing implementations
- Read the relevant code before guessing
- Ask the user — never guess

### Never
- Invent APIs, endpoints, or packages that don't exist
- Fabricate file paths or environment variables
- Claim tests passed without executing them
- Make up CLI flags or library features

### Responses
- Summarise what changed and why
- Reference edited files with paths
- State any remaining risks or assumptions
- Be concise — no essay-length explanations

---

## Planning

For changes larger than ~200 lines:

1. Understand the architecture
2. Create a plan
3. Identify risks
4. Implement
5. Verify

Do not jump directly into editing without understanding the flow.

---

## Refactoring Rules

Refactoring should never change:
- Behaviour
- API shape
- Output format

Unless explicitly requested. One change per refactor.

---

## Repository Invariants

These must always remain true:

- Authentication is never bypassed
- No secrets committed to git
- API responses backwards compatible
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

## Definition of Done

A task is complete only when:

- Implementation finished
- Syntax valid
- Lint passes (frontend)
- Dead code removed
- No TODOs or debugging artifacts left
- Committed with conventional message
- Working tree clean

---

## Quick Reference

```bash
npm run dev                   # start both
npm run backend               # backend only
npm run frontend              # frontend only
cd frontend && npm run lint   # lint frontend
node -c backend/**/*.js       # syntax check backend
```
