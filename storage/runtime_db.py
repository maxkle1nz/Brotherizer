#!/usr/bin/env python3
"""Durable runtime storage for Brotherizer jobs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    source_text TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT '',
    surface_mode TEXT NOT NULL DEFAULT '',
    query TEXT NOT NULL DEFAULT '',
    candidate_count INTEGER NOT NULL DEFAULT 3,
    judge_enabled INTEGER NOT NULL DEFAULT 0,
    generation_provider TEXT NOT NULL DEFAULT '',
    generation_model TEXT NOT NULL DEFAULT '',
    judge_provider TEXT NOT NULL DEFAULT '',
    judge_model TEXT NOT NULL DEFAULT '',
    winner_candidate_id TEXT,
    chosen_candidate_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    cancelled_at TEXT,
    failed_at TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    why TEXT NOT NULL DEFAULT '',
    diagnostics_json TEXT NOT NULL DEFAULT '{}',
    donor_snippets_json TEXT NOT NULL DEFAULT '[]',
    style_signals_json TEXT NOT NULL DEFAULT '[]',
    is_winner INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS choices (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    actor_type TEXT NOT NULL DEFAULT 'client',
    actor_id TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_sessions (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE,
    review_url_token TEXT NOT NULL,
    ui_mode TEXT NOT NULL DEFAULT 'off',
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS runtime_errors (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key TEXT PRIMARY KEY,
    request_hash TEXT NOT NULL,
    job_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_job_rank ON candidates(job_id, rank);
CREATE INDEX IF NOT EXISTS idx_choices_job_created ON choices(job_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runtime_errors_job_created ON runtime_errors(job_id, created_at DESC);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def create_job(conn: sqlite3.Connection, *, job: dict) -> None:
    conn.execute(
        """
        INSERT INTO jobs (
            id, status, request_hash, source_text, mode, surface_mode, query, candidate_count,
            judge_enabled, generation_provider, generation_model, judge_provider, judge_model,
            winner_candidate_id, chosen_candidate_id, created_at, updated_at, completed_at,
            cancelled_at, failed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job["id"],
            job["status"],
            job["request_hash"],
            job["source_text"],
            job.get("mode", ""),
            job.get("surface_mode", ""),
            job.get("query", ""),
            int(job.get("candidate_count", 3)),
            1 if job.get("judge_enabled") else 0,
            job.get("generation_provider", ""),
            job.get("generation_model", ""),
            job.get("judge_provider", ""),
            job.get("judge_model", ""),
            job.get("winner_candidate_id"),
            job.get("chosen_candidate_id"),
            job["created_at"],
            job["updated_at"],
            job.get("completed_at"),
            job.get("cancelled_at"),
            job.get("failed_at"),
        ),
    )
    conn.commit()


def update_job_state(
    conn: sqlite3.Connection,
    *,
    job_id: str,
    status: str,
    updated_at: str,
    completed_at: str | None = None,
    cancelled_at: str | None = None,
    failed_at: str | None = None,
    winner_candidate_id: str | None = None,
    chosen_candidate_id: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE jobs
        SET status = ?, updated_at = ?, completed_at = COALESCE(?, completed_at),
            cancelled_at = COALESCE(?, cancelled_at), failed_at = COALESCE(?, failed_at),
            winner_candidate_id = COALESCE(?, winner_candidate_id),
            chosen_candidate_id = COALESCE(?, chosen_candidate_id)
        WHERE id = ?
        """,
        (
            status,
            updated_at,
            completed_at,
            cancelled_at,
            failed_at,
            winner_candidate_id,
            chosen_candidate_id,
            job_id,
        ),
    )
    conn.commit()


def replace_candidates(conn: sqlite3.Connection, *, job_id: str, candidates: list[dict]) -> None:
    conn.execute("DELETE FROM candidates WHERE job_id = ?", (job_id,))
    conn.executemany(
        """
        INSERT INTO candidates (
            id, job_id, rank, label, text, score, why, diagnostics_json,
            donor_snippets_json, style_signals_json, is_winner
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                job_id,
                int(item["rank"]),
                item.get("label", ""),
                item.get("text", ""),
                float(item.get("score", 0)),
                item.get("why", ""),
                json.dumps(item.get("diagnostics", {}), ensure_ascii=False),
                json.dumps(item.get("donor_snippets", []), ensure_ascii=False),
                json.dumps(item.get("style_signals", []), ensure_ascii=False),
                1 if item.get("is_winner") else 0,
            )
            for item in candidates
        ],
    )
    conn.commit()


def create_choice(conn: sqlite3.Connection, *, choice: dict) -> None:
    conn.execute(
        """
        INSERT INTO choices (id, job_id, candidate_id, actor_type, actor_id, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            choice["id"],
            choice["job_id"],
            choice["candidate_id"],
            choice.get("actor_type", "client"),
            choice.get("actor_id", ""),
            choice.get("reason", ""),
            choice["created_at"],
        ),
    )
    conn.commit()


def upsert_review_session(conn: sqlite3.Connection, *, review_session: dict) -> None:
    conn.execute(
        """
        INSERT INTO review_sessions (id, job_id, review_url_token, ui_mode, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            id = excluded.id,
            review_url_token = excluded.review_url_token,
            ui_mode = excluded.ui_mode
        """,
        (
            review_session["id"],
            review_session["job_id"],
            review_session["review_url_token"],
            review_session["ui_mode"],
            review_session["created_at"],
        ),
    )
    conn.commit()


def create_runtime_error(conn: sqlite3.Connection, *, error: dict) -> None:
    conn.execute(
        """
        INSERT INTO runtime_errors (id, job_id, phase, code, message, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            error["id"],
            error["job_id"],
            error["phase"],
            error["code"],
            error["message"],
            json.dumps(error.get("details", {}), ensure_ascii=False),
            error["created_at"],
        ),
    )
    conn.commit()


def get_idempotency_record(conn: sqlite3.Connection, *, key: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT key, request_hash, job_id, created_at FROM idempotency_keys WHERE key = ?",
        (key,),
    ).fetchone()


def create_idempotency_record(conn: sqlite3.Connection, *, key: str, request_hash: str, job_id: str, created_at: str) -> None:
    conn.execute(
        "INSERT INTO idempotency_keys (key, request_hash, job_id, created_at) VALUES (?, ?, ?, ?)",
        (key, request_hash, job_id, created_at),
    )
    conn.commit()


def get_job(conn: sqlite3.Connection, *, job_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def list_candidates(conn: sqlite3.Connection, *, job_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM candidates WHERE job_id = ? ORDER BY rank ASC, id ASC",
        (job_id,),
    ).fetchall()


def get_review_session(conn: sqlite3.Connection, *, job_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM review_sessions WHERE job_id = ?", (job_id,)).fetchone()


def list_choices(conn: sqlite3.Connection, *, job_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM choices WHERE job_id = ? ORDER BY created_at DESC, id DESC",
        (job_id,),
    ).fetchall()


def list_runtime_errors(conn: sqlite3.Connection, *, job_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM runtime_errors WHERE job_id = ? ORDER BY created_at DESC, id DESC",
        (job_id,),
    ).fetchall()
