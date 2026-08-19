"""Auth router — login, logout, refresh, status, register, change-password, API keys."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
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
from database import execute, query, AUTH_DB

router = APIRouter()


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


# --- Public endpoints ---

@router.get("/status")
def auth_status():
    users = query(AUTH_DB, "SELECT id FROM users LIMIT 1")
    initialized = len(users) > 0
    return {"initialized": initialized, "requires_password_change": False}


@router.post("/register", response_model=TokenResponse)
def register(req: LoginRequest):
    existing = query(AUTH_DB, "SELECT id FROM users WHERE username = ?", (req.username,))
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    pw_hash = hash_password(req.password)
    is_email = "@" in req.username
    cursor = execute(AUTH_DB, "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                     (req.username, req.username if is_email else None, pw_hash))
    user_id = cursor.lastrowid
    access = create_access_token(user_id, req.username)
    refresh = create_refresh_token(user_id)
    return TokenResponse(access_token=access, refresh_token=refresh, must_change_password=False)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    rows = query(AUTH_DB, "SELECT id, password_hash, must_change_password FROM users WHERE username = ?", (req.username,))
    if not rows:
        rows = query(AUTH_DB, "SELECT id, password_hash, must_change_password FROM users WHERE email = ?", (req.username,))
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    row = rows[0]
    if not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access = create_access_token(row["id"], req.username)
    refresh = create_refresh_token(row["id"])
    return TokenResponse(access_token=access, refresh_token=refresh, must_change_password=bool(row["must_change_password"]))


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    token_hash = hash_token(req.refresh_token)
    rows = query(AUTH_DB, "SELECT id, user_id, expires_at FROM refresh_tokens WHERE token_hash = ?", (token_hash,))
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    row = rows[0]
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE id = ?", (row["id"],))
        raise HTTPException(status_code=401, detail="Refresh token expired")
    user = query(AUTH_DB, "SELECT id, username, must_change_password FROM users WHERE id = ?", (row["user_id"],))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE id = ?", (row["id"],))
    access = create_access_token(user[0]["id"], user[0]["username"])
    refresh_token = create_refresh_token(user[0]["id"])
    return TokenResponse(access_token=access, refresh_token=refresh_token, must_change_password=bool(user[0]["must_change_password"]))


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    return {"ok": True}


@router.post("/change-password", response_model=TokenResponse)
def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    rows = query(AUTH_DB, "SELECT id, password_hash FROM users WHERE id = ?", (user["id"],))
    if not rows or not verify_password(req.current_password, rows[0]["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = hash_password(req.new_password)
    execute(AUTH_DB, "UPDATE users SET password_hash = ?, must_change_password = 0, updated_at = datetime('now') WHERE id = ?",
            (new_hash, user["id"]))
    execute(AUTH_DB, "DELETE FROM refresh_tokens WHERE user_id = ?", (user["id"],))
    access = create_access_token(user["id"], user["username"])
    refresh_token = create_refresh_token(user["id"])
    return TokenResponse(access_token=access, refresh_token=refresh_token, must_change_password=False)


# --- API Keys ---

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
        from datetime import timedelta
        expires_at = (datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)).isoformat()
    cursor = execute(AUTH_DB, "INSERT INTO api_keys (user_id, name, key_hash, key_prefix, expires_at) VALUES (?, ?, ?, ?, ?)",
                     (user["id"], req.name, key_hash, prefix, expires_at))
    api_key = {"id": cursor.lastrowid, "name": req.name, "key_prefix": prefix, "expires_at": expires_at, "created_at": datetime.now(timezone.utc).isoformat()}
    return {"key": raw_key, "api_key": api_key}


@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: int, user: dict = Depends(get_current_user)):
    execute(AUTH_DB, "DELETE FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user["id"]))
    return {"ok": True}
