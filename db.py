"""DarkGuard AI – SQLite database layer."""
import sqlite3
import threading
from pathlib import Path
from backend.config import config

_local = threading.local()


def get_db() -> sqlite3.Connection:
    import os
    db_path = Path(os.getenv("DATABASE_PATH", config.DATABASE_PATH))
    if not hasattr(_local, "conn") or _local.conn is None or getattr(_local, "db_path", None) != str(db_path):
        if hasattr(_local, "conn") and _local.conn is not None:
            _local.conn.close()
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
        _local.db_path = str(db_path)
    return _local.conn


def close_db():
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    full_name       TEXT NOT NULL DEFAULT '',
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT,
    provider        TEXT NOT NULL DEFAULT 'email',
    provider_user_id TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token           TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at      TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS password_resets (
    token           TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at      TEXT NOT NULL,
    used            INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audits (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL,
    platform_other  TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    score           REAL,
    result_json     TEXT,
    is_simulated    INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS audit_files (
    id              TEXT PRIMARY KEY,
    audit_id        TEXT NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
    slot            INTEGER NOT NULL,
    filename        TEXT NOT NULL,
    path            TEXT NOT NULL,
    size            INTEGER NOT NULL,
    deleted         INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db():
    db = get_db()
    for statement in SCHEMA.split(";"):
        stmt = statement.strip()
        if stmt:
            db.execute(stmt)
    db.commit()
