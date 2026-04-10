#!/usr/bin/env python3
"""Persistent workspace storage for Brotherizer UI."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_outputs (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    why TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def list_workspace(conn: sqlite3.Connection) -> dict:
    sessions = []
    session_rows = conn.execute(
        "SELECT id, name, created_at FROM sessions ORDER BY created_at DESC, id DESC"
    ).fetchall()
    for session in session_rows:
        file_rows = conn.execute(
            """
            SELECT id, session_id, name, text, mode, created_at, updated_at
            FROM files
            WHERE session_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (session["id"],),
        ).fetchall()
        files = []
        for file_row in file_rows:
            output_rows = conn.execute(
                """
                SELECT id, saved_at, mode, label, text, why
                FROM saved_outputs
                WHERE file_id = ?
                ORDER BY saved_at DESC, id DESC
                """,
                (file_row["id"],),
            ).fetchall()
            files.append(
                {
                    "id": file_row["id"],
                    "name": file_row["name"],
                    "text": file_row["text"],
                    "mode": file_row["mode"],
                    "createdAt": file_row["created_at"],
                    "updatedAt": file_row["updated_at"],
                    "rewrites": [
                        {
                            "id": row["id"],
                            "savedAt": row["saved_at"],
                            "mode": row["mode"],
                            "label": row["label"],
                            "text": row["text"],
                            "why": row["why"],
                        }
                        for row in output_rows
                    ],
                }
            )
        sessions.append(
            {
                "id": session["id"],
                "name": session["name"],
                "createdAt": session["created_at"],
                "files": files,
            }
        )
    return {"sessions": sessions}


def insert_session(conn: sqlite3.Connection, *, session_id: str, name: str, created_at: str) -> None:
    conn.execute(
        "INSERT INTO sessions (id, name, created_at) VALUES (?, ?, ?)",
        (session_id, name, created_at),
    )
    conn.commit()


def insert_file(
    conn: sqlite3.Connection,
    *,
    file_id: str,
    session_id: str,
    name: str,
    text: str,
    mode: str,
    created_at: str,
    updated_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO files (id, session_id, name, text, mode, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (file_id, session_id, name, text, mode, created_at, updated_at),
    )
    conn.commit()


def update_file(conn: sqlite3.Connection, *, file_id: str, name: str, text: str, mode: str, updated_at: str) -> bool:
    cur = conn.execute(
        """
        UPDATE files
        SET name = ?, text = ?, mode = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, text, mode, updated_at, file_id),
    )
    conn.commit()
    return cur.rowcount > 0


def insert_saved_output(
    conn: sqlite3.Connection,
    *,
    output_id: str,
    file_id: str,
    saved_at: str,
    mode: str,
    label: str,
    text: str,
    why: str,
) -> None:
    conn.execute(
        """
        INSERT INTO saved_outputs (id, file_id, saved_at, mode, label, text, why)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (output_id, file_id, saved_at, mode, label, text, why),
    )
    conn.commit()
