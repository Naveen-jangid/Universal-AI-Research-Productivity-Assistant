"""
SQLite-backed persistence layer for conversation history and long-term memory.
Uses the standard-library `sqlite3` module so no extra database driver is needed.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from backend.core.config import settings


# ── Connection helper ───────────────────────────────────────────────────────

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with row_factory set to dict-like Row."""
    db_path = settings.sqlite_path
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema bootstrap ────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT 'New Conversation',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),
    content         TEXT NOT NULL,
    metadata        TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_facts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    fact            TEXT NOT NULL,
    category        TEXT NOT NULL DEFAULT 'general',
    importance      REAL NOT NULL DEFAULT 0.5,
    created_at      TEXT NOT NULL,
    last_accessed   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    file_size   INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'pending',
    metadata    TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_facts(session_id);
"""


def init_db() -> None:
    """Create all tables if they don't exist."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)


# ── Conversation CRUD ───────────────────────────────────────────────────────

def create_conversation(conv_id: str, title: str = "New Conversation") -> Dict:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?,?,?,?)",
            (conv_id, title, now, now),
        )
    return {"id": conv_id, "title": title, "created_at": now}


def get_conversation(conv_id: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        ).fetchone()
    return dict(row) if row else None


def list_conversations() -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_conversation(conv_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))


# ── Message CRUD ────────────────────────────────────────────────────────────

def add_message(
    conv_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None,
) -> int:
    now = datetime.utcnow().isoformat()
    meta_json = json.dumps(metadata or {})
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO messages (conversation_id, role, content, metadata, created_at) VALUES (?,?,?,?,?)",
            (conv_id, role, content, meta_json, now),
        )
        # update conversation timestamp
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id)
        )
    return cur.lastrowid


def get_messages(conv_id: str, limit: int = 100) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC LIMIT ?",
            (conv_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Document registry ───────────────────────────────────────────────────────

def register_document(
    doc_id: str,
    filename: str,
    file_type: str,
    file_size: int,
    metadata: Optional[Dict] = None,
) -> None:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO documents (id, filename, file_type, file_size, metadata, created_at) VALUES (?,?,?,?,?,?)",
            (doc_id, filename, file_type, file_size, json.dumps(metadata or {}), now),
        )


def update_document_status(doc_id: str, status: str, chunk_count: int = 0) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
            (status, chunk_count, doc_id),
        )


def list_documents() -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


# ── Memory facts ────────────────────────────────────────────────────────────

def save_memory_fact(
    session_id: str,
    fact: str,
    category: str = "general",
    importance: float = 0.5,
) -> None:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO memory_facts (session_id, fact, category, importance, created_at, last_accessed) VALUES (?,?,?,?,?,?)",
            (session_id, fact, category, importance, now, now),
        )


def get_memory_facts(session_id: str, limit: int = 50) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM memory_facts WHERE session_id = ? ORDER BY importance DESC, last_accessed DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def search_memory_facts(session_id: str, keyword: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM memory_facts WHERE session_id = ? AND fact LIKE ? ORDER BY importance DESC",
            (session_id, f"%{keyword}%"),
        ).fetchall()
    return [dict(r) for r in rows]
