"""SQLite database setup — raw sqlite3, no ORM."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

import structlog

from config import AUTH_DB, STUDIO_DB, DATA_DIR

logger = structlog.get_logger()
_schema_lock = threading.Lock()

_AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    must_change_password INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

_STUDIO_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_threads (
    id TEXT PRIMARY KEY,
    title TEXT,
    model TEXT,
    model_type TEXT,
    pair_id TEXT,
    project_id TEXT,
    pinned INTEGER DEFAULT 0,
    bookmarked INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    folder_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    model TEXT,
    tool_calls TEXT,
    tool_call_id TEXT,
    name TEXT,
    reasoning TEXT,
    extra_content TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (thread_id) REFERENCES chat_threads(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chat_folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_attachments (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT,
    size INTEGER,
    data BLOB,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


def _get_conn(db_path: Path) -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_auth_db() -> None:
    with _schema_lock:
        conn = _get_conn(AUTH_DB)
        try:
            conn.executescript(_AUTH_SCHEMA)
            try:
                conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
            except Exception:
                pass
            conn.commit()
        finally:
            conn.close()


def init_studio_db() -> None:
    with _schema_lock:
        conn = _get_conn(STUDIO_DB)
        try:
            conn.executescript(_STUDIO_SCHEMA)
            conn.commit()
        finally:
            conn.close()


def get_auth_conn() -> sqlite3.Connection:
    return _get_conn(AUTH_DB)


def get_studio_conn() -> sqlite3.Connection:
    return _get_conn(STUDIO_DB)


def query(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
        return rows
    finally:
        conn.close()


def execute(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor
    finally:
        conn.close()


def execute_many(db_path: Path, sql: str, params_list: list[tuple[Any, ...]]) -> None:
    conn = _get_conn(db_path)
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()
