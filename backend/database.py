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
CREATE TABLE IF NOT EXISTS chat_import_ledger (
    thread_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS provider_configs (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    name TEXT NOT NULL,
    api_key TEXT,
    base_url TEXT,
    models_json TEXT DEFAULT '[]',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS mcp_servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    transport TEXT NOT NULL DEFAULT 'http',
    command TEXT,
    args_json TEXT DEFAULT '[]',
    url TEXT,
    headers_json TEXT DEFAULT '{}',
    env_json TEXT DEFAULT '{}',
    enabled INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS image_gallery (
    id TEXT PRIMARY KEY,
    prompt TEXT,
    negative_prompt TEXT,
    width INTEGER,
    height INTEGER,
    steps INTEGER,
    guidance REAL,
    seed INTEGER,
    batch_seed INTEGER,
    batch_index INTEGER,
    batch_size INTEGER,
    model TEXT,
    model_kind TEXT,
    pinned INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS video_gallery (
    id TEXT PRIMARY KEY,
    prompt TEXT,
    negative_prompt TEXT,
    width INTEGER,
    height INTEGER,
    num_frames INTEGER,
    fps INTEGER,
    duration_s REAL,
    steps INTEGER,
    guidance REAL,
    seed INTEGER,
    model TEXT,
    model_kind TEXT,
    pinned INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audio_gallery (
    id TEXT PRIMARY KEY,
    prompt TEXT,
    model TEXT,
    audio_type TEXT,
    sample_rate INTEGER,
    duration_s REAL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS training_runs (
    id TEXT PRIMARY KEY,
    model_name TEXT,
    display_name TEXT,
    training_type TEXT,
    status TEXT,
    config_json TEXT,
    completed_at REAL,
    created_at REAL NOT NULL
);
"""


def _get_conn(db_path: Path) -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_AUTH_MIGRATIONS = [
    ("ALTER TABLE users ADD COLUMN email TEXT",),
    ("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'",),
    ("ALTER TABLE users ADD COLUMN display_name TEXT",),
    ("ALTER TABLE users ADD COLUMN system_prompt TEXT",),
    ("ALTER TABLE users ADD COLUMN policies_accepted INTEGER DEFAULT 0",),
    ("ALTER TABLE api_keys ADD COLUMN last_used_at TEXT",),
    ("ALTER TABLE api_keys ADD COLUMN is_active INTEGER DEFAULT 1",),
]


def _run_migrations(conn: sqlite3.Connection, migrations: list[tuple[str, ...]]) -> None:
    for (sql,) in migrations:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e):
                logger.warning("migration_failed", sql=sql, error=str(e))


def init_auth_db() -> None:
    with _schema_lock:
        conn = _get_conn(AUTH_DB)
        try:
            conn.executescript(_AUTH_SCHEMA)
            _run_migrations(conn, _AUTH_MIGRATIONS)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
                CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
                CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
                CREATE INDEX IF NOT EXISTS idx_password_resets_hash ON password_resets(token_hash);
            """)
            conn.commit()
        finally:
            conn.close()


def init_studio_db() -> None:
    with _schema_lock:
        conn = _get_conn(STUDIO_DB)
        try:
            conn.executescript(_STUDIO_SCHEMA)
            conn.executescript("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_thread ON chat_messages(thread_id);
                CREATE INDEX IF NOT EXISTS idx_chat_attachments_message ON chat_attachments(message_id);
            """)
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


def execute_returning(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def execute_many(db_path: Path, sql: str, params_list: list[tuple[Any, ...]]) -> None:
    conn = _get_conn(db_path)
    try:
        conn.executemany(sql, params_list)
        conn.commit()
    finally:
        conn.close()
