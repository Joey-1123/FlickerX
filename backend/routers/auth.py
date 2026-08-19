"""Auth router — login, logout, refresh, status, register, change-password, API keys, /me, admin, password reset."""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)
from database import execute, execute_returning, query, AUTH_DB

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CreateApiKeyRequest(BaseModel):
    name: str
    expires_in_days: int | None = None


class ProfileUpdate(BaseModel):
    systemPrompt: str | None = None
    name: str | None = None


class AdminRoleRequest(BaseModel):
    role: str


class PasswordResetRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ---------------------------------------------------------------------------
# Rate limiting — adapted from Unsloth's deque-based per-IP+per-user limiter
# ponytail: single-process only; multi-worker needs shared store
# ---------------------------------------------------------------------------
_LOGIN_BUCKETS: dict[tuple[str, str], deque] = {}
_LOGIN_IP_BUCKETS: dict[str, deque] = {}
_LOGIN_LOCK = threading.Lock()
_LOGIN_WINDOW = 60.0
_LOGIN_MAX_FAILS = 5
_LOGIN_IP_MAX_FAILS = 30
_UNKNOWN_USER = "\x00unknown-user"


def _client_ip(request: Request | None) -> str:
    if request is None:
        return "_unknown"
    return (request.client.host if request.client else None) or "_unknown"


def _bucket_key(request: Request, username: str) -> tuple[str, str]:
    return (_client_ip(request), (username or "").casefold())


def _prune(bucket: deque, now: float) -> None:
    while bucket and now - bucket[0] > _LOGIN_WINDOW:
        bucket.popleft()


def _record_failure(key: tuple[str, str]) -> int:
    now = time.monotonic()
    with _LOGIN_LOCK:
        ip = key[0]
        ip_bucket = _LOGIN_IP_BUCKETS.setdefault(ip, deque())
        _prune(ip_bucket, now)
        ip_bucket.append(now)

        account_bucket = _LOGIN_BUCKETS.setdefault(key, deque())
        _prune(account_bucket, now)
        account_bucket.append(now)
        return len(account_bucket)


def _blocked_seconds(key: tuple[str, str]) -> int:
    now = time.monotonic()
    with _LOGIN_LOCK:
        ip = key[0]
        ip_bucket = _LOGIN_IP_BUCKETS.get(ip)
        if ip_bucket:
            _prune(ip_bucket, now)
            if len(ip_bucket) >= _LOGIN_IP_MAX_FAILS:
                return max(1, int(_LOGIN_WINDOW - (now - ip_bucket[0])))
        account_bucket = _LOGIN_BUCKETS.get(key)
        if account_bucket:
            _prune(account_bucket, now)
            if len(account_bucket) >= _LOGIN_MAX_FAILS:
                return max(1, int(_LOGIN_WINDOW - (now - account_bucket[0])))
    return 0


def _clear_bucket(key: tuple[str, str]) -> None:
    with _LOGIN_LOCK:
        _LOGIN_BUCKETS.pop(key, None)
        _LOGIN_IP_BUCKETS.pop(key[0], None)


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
@router.get("/status")
def auth_status():
    users = query(AUTH_DB, "SELECT id FROM users LIMIT 1")
    initialized = len(users) > 0
    pw_change = False
    if initialized:
        rows = query(AUTH_DB, "SELECT must_change_password FROM users LIMIT 1")
        if rows:
            pw_change = bool(rows[0]["must_change_password"])
    return {"initialized": initialized, "requires_password_change": pw_change}


@router.post("/register", response_model=TokenResponse)
def register(req: LoginRequest):
    existing = query(AUTH_DB, "SELECT id FROM users WHERE username = ?", (req.username,))
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    if any(ch.isspace() for ch in req.password):
        raise HTTPException(status_code=400, detail="Password cannot contain spaces")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    pw_hash = hash_password(req.password)
    is_email = "@" in req.username
    cursor = execute(AUTH_DB, "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                     (req.username, req.username if is_email else None, pw_hash))
    user_id = cursor.lastrowid
    access = create_access_token(user_id, req.username)
    refresh = create_refresh_token(user_id)
    return TokenResponse(access_token=access, refresh_token=refresh, must_change_password=False)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request):
    key = _bucket_key(request, req.username)
    unknown_key = (_client_ip(request), _UNKNOWN_USER)
    blocked = max(_blocked_seconds(key), _blocked_seconds(unknown_key))
    if blocked > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {blocked} seconds.",
            headers={"Retry-After": str(blocked)},
        )

    # Single query: username OR email
    rows = query(AUTH_DB,
        "SELECT id, username, password_hash, must_change_password FROM users WHERE username = ? OR email = ?",
        (req.username, req.username))
    if not rows:
        _record_failure(unknown_key)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    row = rows[0]
    if not verify_password(req.password, row["password_hash"]):
        _record_failure(key)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    _clear_bucket(key)
    _clear_bucket(unknown_key)
    access = create_access_token(row["id"], row["username"])
    refresh = create_refresh_token(row["id"])
    return TokenResponse(access_token=access, refresh_token=refresh, must_change_password=bool(row["must_change_password"]))


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    token_hash = hash_token(req.refresh_token)
    # Race-safe: DELETE + RETURNING in one atomic operation
    rows = execute_returning(AUTH_DB,
        "DELETE FROM refresh_tokens WHERE token_hash = ? AND expires_at > datetime('now') RETURNING id, user_id",
        (token_hash,))
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    row = rows[0]
    user = query(AUTH_DB, "SELECT id, username, must_change_password FROM users WHERE id = ?", (row["user_id"],))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(user[0]["id"], user[0]["username"])
    refresh_token = create_refresh_token(user[0]["id"])
    return TokenResponse(access_token=access, refresh_token=refresh_token, must_change_password=bool(user[0]["must_change_password"]))


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    # ponytail: real token revocation — delete all refresh tokens for this user
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE user_id = ?", (user["id"],))
    return {"ok": True}


@router.post("/change-password", response_model=TokenResponse)
def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT id, password_hash FROM users WHERE id = ?", (user["id"],))
    if not rows or not verify_password(req.current_password, rows[0]["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if any(ch.isspace() for ch in req.new_password):
        raise HTTPException(status_code=400, detail="New password cannot contain spaces")
    if req.current_password == req.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password")
    new_hash = hash_password(req.new_password)
    execute(AUTH_DB, "UPDATE users SET password_hash = ?, must_change_password = 0, updated_at = datetime('now') WHERE id = ?",
            (new_hash, user["id"]))
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE user_id = ?", (user["id"],))
    access = create_access_token(user["id"], user["username"])
    refresh_token = create_refresh_token(user["id"])
    return TokenResponse(access_token=access, refresh_token=refresh_token, must_change_password=False)


# ---------------------------------------------------------------------------
# Profile — GET /me, PUT /me (what the frontend calls)
# ---------------------------------------------------------------------------
@router.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT id, username, email, role, system_prompt, created_at FROM users WHERE id = ?", (user["id"],))
    if not rows:
        raise HTTPException(status_code=404, detail="User not found")
    r = dict(rows[0])
    r["role"] = r.get("role", "user")
    r["systemPrompt"] = r.pop("system_prompt", None) or ""
    return r


@router.put("/me")
def update_profile(body: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = []
    params = []
    if body.systemPrompt is not None:
        updates.append("system_prompt = ?")
        params.append(body.systemPrompt)
    if body.name is not None:
        updates.append("display_name = ?")
        params.append(body.name)
    if updates:
        params.append(user["id"])
        execute(AUTH_DB, f"UPDATE users SET {', '.join(updates)}, updated_at = datetime('now') WHERE id = ?", tuple(params))
    return {"ok": True}


@router.delete("/me")
def delete_account(user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE user_id = ?", (user["id"],))
    execute(AUTH_DB, "DELETE FROM api_keys WHERE user_id = ?", (user["id"],))
    execute(AUTH_DB, "DELETE FROM users WHERE id = ?", (user["id"],))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Password reset — forgot-password + reset-password
# ---------------------------------------------------------------------------
@router.post("/forgot-password")
def forgot_password(body: PasswordResetRequest):
    rows = query(AUTH_DB, "SELECT id FROM users WHERE email = ?", (body.email,))
    if not rows:
        # Don't leak whether email exists
        return {"ok": True, "message": "If the email exists, a reset link has been sent."}
    reset_token = secrets.token_urlsafe(32)
    token_hash = hash_token(reset_token)
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    execute(AUTH_DB, "DELETE FROM password_resets WHERE user_id = ?", (rows[0]["id"],))
    execute(AUTH_DB, "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (rows[0]["id"], token_hash, expires))
    # ponytail: in production, send email with reset_token. For now return it.
    return {"ok": True, "message": "If the email exists, a reset link has been sent.", "debug_token": reset_token}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    if any(ch.isspace() for ch in body.new_password):
        raise HTTPException(status_code=400, detail="Password cannot contain spaces")
    token_hash = hash_token(body.token)
    rows = query(AUTH_DB, "SELECT id, user_id, expires_at FROM password_resets WHERE token_hash = ?", (token_hash,))
    if not rows:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    row = rows[0]
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        execute(AUTH_DB, "DELETE FROM password_resets WHERE id = ?", (row["id"],))
        raise HTTPException(status_code=400, detail="Reset token expired")
    new_hash = hash_password(body.new_password)
    execute(AUTH_DB, "UPDATE users SET password_hash = ?, must_change_password = 0, updated_at = datetime('now') WHERE id = ?",
            (new_hash, row["user_id"]))
    execute(AUTH_DB, "DELETE FROM password_resets WHERE user_id = ?", (row["user_id"],))
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE user_id = ?", (row["user_id"],))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Policy acceptance
# ---------------------------------------------------------------------------
@router.post("/accept-policies")
def accept_policies(user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "UPDATE users SET policies_accepted = 1, updated_at = datetime('now') WHERE id = ?", (user["id"],))
    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin — user management
# ---------------------------------------------------------------------------
@router.get("/admin/users")
def admin_list_users(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    rows = query(AUTH_DB, "SELECT id, username, email, role, created_at FROM users ORDER BY created_at")
    return {"users": [dict(r) for r in rows]}


@router.delete("/admin/users/{target_user_id}")
def admin_delete_user(target_user_id: int, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if target_user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE user_id = ?", (target_user_id,))
    execute(AUTH_DB, "DELETE FROM api_keys WHERE user_id = ?", (target_user_id,))
    execute(AUTH_DB, "DELETE FROM users WHERE id = ?", (target_user_id,))
    return {"ok": True}


@router.patch("/admin/users/{target_user_id}/role")
def admin_change_role(target_user_id: int, body: AdminRoleRequest, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
    execute(AUTH_DB, "UPDATE users SET role = ?, updated_at = datetime('now') WHERE id = ?", (body.role, target_user_id))
    return {"ok": True}


# ---------------------------------------------------------------------------
# File upload (what the frontend calls)
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_file(request: Request, user: dict = Depends(get_current_user)):
    from pathlib import Path
    import uuid
    content_type = request.headers.get("content-type", "")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty upload")
    ext = ".bin"
    if "image/png" in content_type:
        ext = ".png"
    elif "image/jpeg" in content_type:
        ext = ".jpg"
    elif "image/webp" in content_type:
        ext = ".webp"
    elif "application/pdf" in content_type:
        ext = ".pdf"
    upload_dir = Path.home() / ".flickerx" / "studio" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    file_path = upload_dir / f"{file_id}{ext}"
    file_path.write_bytes(body)
    return {"url": f"/api/auth/uploads/{file_id}{ext}", "id": file_id, "filename": file_id + ext}


@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    from fastapi.responses import FileResponse
    from pathlib import Path
    file_path = Path.home() / ".flickerx" / "studio" / "uploads" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path))


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
@router.get("/api-keys")
def list_api_keys(user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT id, name, key_prefix, expires_at, created_at FROM api_keys WHERE user_id = ?", (user["id"],))
    return {"api_keys": [dict(r) for r in rows]}


@router.post("/api-keys")
def create_api_key(req: CreateApiKeyRequest, user: dict = Depends(get_current_user)):
    raw_key = f"fk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:8]
    expires_at = None
    if req.expires_in_days:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)).isoformat()
    cursor = execute(AUTH_DB, "INSERT INTO api_keys (user_id, name, key_hash, key_prefix, expires_at) VALUES (?, ?, ?, ?, ?)",
                     (user["id"], req.name, key_hash, prefix, expires_at))
    api_key = {"id": cursor.lastrowid, "name": req.name, "key_prefix": prefix, "expires_at": expires_at, "created_at": datetime.now(timezone.utc).isoformat()}
    return {"key": raw_key, "api_key": api_key}


@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: int, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT id FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user["id"]))
    if not rows:
        raise HTTPException(status_code=404, detail="API key not found")
    execute(AUTH_DB, "DELETE FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user["id"]))
    return {"ok": True}
