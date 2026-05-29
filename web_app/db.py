"""SQLite database for users."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from .config import database_path


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_db(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = _connect(path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db(db_path: Path | None = None) -> None:
    with get_db(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                original_sentence TEXT NOT NULL,
                gloss_tokens TEXT,
                gloss_token TEXT,
                submission_id TEXT,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                reporter_id INTEGER,
                reporter_username TEXT,
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewed_by INTEGER,
                admin_note TEXT,
                FOREIGN KEY (reporter_id) REFERENCES users (id)
            )
            """
        )


def create_user(
    *,
    email: str,
    username: str,
    password: str,
    is_admin: bool = False,
    db_path: Path | None = None,
) -> int:
    password_hash = generate_password_hash(password)
    created_at = datetime.now(UTC).isoformat()
    with get_db(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (email, username, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email.lower(), username, password_hash, int(is_admin), created_at),
        )
        return int(cursor.lastrowid)


def get_user_by_id(user_id: int, db_path: Path | None = None) -> sqlite3.Row | None:
    with get_db(db_path) as connection:
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_email(email: str, db_path: Path | None = None) -> sqlite3.Row | None:
    with get_db(db_path) as connection:
        return connection.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()


def get_user_by_username(username: str, db_path: Path | None = None) -> sqlite3.Row | None:
    with get_db(db_path) as connection:
        return connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def verify_user(email: str, password: str, db_path: Path | None = None) -> sqlite3.Row | None:
    user = get_user_by_email(email, db_path)
    if user is None:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def count_users(db_path: Path | None = None) -> int:
    with get_db(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        return int(row["count"]) if row else 0
