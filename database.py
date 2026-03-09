"""
AuraLynx MVP — SQLite Database
Schema, deduplication, and signal storage.
"""

import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from config import DB_PATH

log = logging.getLogger("auralynx.db")


def get_connection():
    """Get a SQLite connection with WAL mode for better concurrency."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS seen_posts (
            post_id     TEXT PRIMARY KEY,
            seen_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id     TEXT,
            title       TEXT,
            body        TEXT,
            author      TEXT,
            url         TEXT,
            subreddit   TEXT,
            score       INTEGER,
            signal_type TEXT,
            summary     TEXT,
            reply_draft TEXT,
            source      TEXT DEFAULT 'reddit',
            alerted     INTEGER DEFAULT 0,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS seen_inbox (
            message_id  TEXT PRIMARY KEY,
            seen_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    log.info("Database initialized at %s", DB_PATH)


# ─── Deduplication ────────────────────────────────────────────

def already_seen(conn: sqlite3.Connection, post_id: str) -> bool:
    """Check if a post has already been processed."""
    row = conn.execute(
        "SELECT 1 FROM seen_posts WHERE post_id = ?", (post_id,)
    ).fetchone()
    return row is not None


def mark_seen(conn: sqlite3.Connection, post_id: str):
    """Mark a post as seen."""
    conn.execute(
        "INSERT OR IGNORE INTO seen_posts (post_id) VALUES (?)", (post_id,)
    )
    conn.commit()


def already_seen_inbox(conn: sqlite3.Connection, message_id: str) -> bool:
    """Check if an inbox message has already been processed."""
    row = conn.execute(
        "SELECT 1 FROM seen_inbox WHERE message_id = ?", (message_id,)
    ).fetchone()
    return row is not None


def mark_seen_inbox(conn: sqlite3.Connection, message_id: str):
    """Mark an inbox message as seen."""
    conn.execute(
        "INSERT OR IGNORE INTO seen_inbox (message_id) VALUES (?)", (message_id,)
    )
    conn.commit()


# ─── Signal Storage ───────────────────────────────────────────

def save_signal(conn: sqlite3.Connection, signal: dict):
    """Save a scored signal to the database."""
    conn.execute("""
        INSERT INTO signals (
            post_id, title, body, author, url, subreddit,
            score, signal_type, summary, reply_draft, source, alerted
        ) VALUES (
            :post_id, :title, :body, :author, :url, :subreddit,
            :score, :signal_type, :summary, :reply_draft, :source, :alerted
        )
    """, signal)
    conn.commit()
    log.debug("Saved signal: %s (score=%s)", signal.get("post_id"), signal.get("score"))


# ─── Queries ──────────────────────────────────────────────────

def get_signals_since(conn: sqlite3.Connection, hours: int = 24) -> list:
    """Get all signals from the last N hours."""
    rows = conn.execute(
        "SELECT * FROM signals WHERE detected_at >= datetime('now', ? || ' hours') ORDER BY score DESC",
        (f"-{hours}",)
    ).fetchall()
    return [dict(r) for r in rows]


def get_top_signals(conn: sqlite3.Connection, n: int = 3, hours: int = 24) -> list:
    """Get top N signals by score from the last N hours."""
    rows = conn.execute(
        "SELECT * FROM signals WHERE detected_at >= datetime('now', ? || ' hours') ORDER BY score DESC LIMIT ?",
        (f"-{hours}", n)
    ).fetchall()
    return [dict(r) for r in rows]


def get_signal_counts(conn: sqlite3.Connection, hours: int = 24) -> dict:
    """Get signal counts grouped by signal_type for the last N hours."""
    rows = conn.execute("""
        SELECT signal_type, COUNT(*) as count, AVG(score) as avg_score
        FROM signals WHERE detected_at >= datetime('now', ? || ' hours')
        GROUP BY signal_type
    """, (f"-{hours}",)).fetchall()
    return {r["signal_type"]: {"count": r["count"], "avg_score": round(r["avg_score"], 1)} for r in rows}

