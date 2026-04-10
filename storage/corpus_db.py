#!/usr/bin/env python3
"""SQLite corpus storage and retrieval helpers for Brotherizer."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS donor_snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    text_hash TEXT NOT NULL UNIQUE,
    platform TEXT DEFAULT '',
    source_kind TEXT DEFAULT '',
    content_role TEXT DEFAULT '',
    audience_mode TEXT DEFAULT '',
    lang_hint TEXT DEFAULT '',
    voice_bucket TEXT DEFAULT '',
    donor_score REAL DEFAULT 0,
    topic_tags_json TEXT DEFAULT '[]',
    source_ref_json TEXT DEFAULT '{}',
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS donor_snippets_fts USING fts5(
    text,
    voice_bucket,
    topic_tags,
    content='donor_snippets',
    content_rowid='id'
);

CREATE TABLE IF NOT EXISTS snippet_embeddings (
    snippet_id INTEGER PRIMARY KEY,
    model TEXT NOT NULL,
    dim INTEGER NOT NULL,
    vector_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(snippet_id) REFERENCES donor_snippets(id) ON DELETE CASCADE
);
"""

TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def stable_text_hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def upsert_rows(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> int:
    inserted = 0
    for row in rows:
        text = row.get("text", "").strip()
        if not text:
            continue
        text_hash = stable_text_hash(text)
        payload = (
            text,
            text_hash,
            row.get("platform", ""),
            row.get("source_kind", ""),
            row.get("content_role", ""),
            row.get("audience_mode", ""),
            row.get("lang_hint", ""),
            row.get("voice_bucket", ""),
            float(row.get("donor_score", 0) or 0),
            json.dumps(row.get("topic_tags", []), ensure_ascii=False),
            json.dumps(row.get("source_ref", {}), ensure_ascii=False),
            json.dumps({"why": row.get("why", "")}, ensure_ascii=False),
        )
        existing = conn.execute(
            "SELECT id, voice_bucket, donor_score FROM donor_snippets WHERE text_hash = ?",
            (text_hash,),
        ).fetchone()
        if existing is None:
            cur = conn.execute(
                """
                INSERT INTO donor_snippets (
                    text, text_hash, platform, source_kind, content_role, audience_mode, lang_hint,
                    voice_bucket, donor_score, topic_tags_json, source_ref_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            rowid = cur.lastrowid
            conn.execute(
                "INSERT INTO donor_snippets_fts(rowid, text, voice_bucket, topic_tags) VALUES (?, ?, ?, ?)",
                (rowid, text, row.get("voice_bucket", ""), " ".join(row.get("topic_tags", []))),
            )
            inserted += 1
        else:
            existing_bucket = existing["voice_bucket"] or ""
            existing_score = float(existing["donor_score"] or 0)
            new_bucket = row.get("voice_bucket", "") or ""
            new_score = float(row.get("donor_score", 0) or 0)
            should_upgrade = (
                (not existing_bucket and new_bucket)
                or new_score > existing_score
            )
            if should_upgrade:
                conn.execute(
                    """
                    UPDATE donor_snippets
                    SET platform = ?, source_kind = ?, content_role = ?, audience_mode = ?, lang_hint = ?,
                        voice_bucket = ?, donor_score = ?, topic_tags_json = ?, source_ref_json = ?, metadata_json = ?
                    WHERE id = ?
                    """,
                    (
                        row.get("platform", ""),
                        row.get("source_kind", ""),
                        row.get("content_role", ""),
                        row.get("audience_mode", ""),
                        row.get("lang_hint", ""),
                        new_bucket,
                        new_score,
                        json.dumps(row.get("topic_tags", []), ensure_ascii=False),
                        json.dumps(row.get("source_ref", {}), ensure_ascii=False),
                        json.dumps({"why": row.get("why", "")}, ensure_ascii=False),
                        existing["id"],
                    ),
                )
                conn.execute("DELETE FROM donor_snippets_fts WHERE rowid = ?", (existing["id"],))
                conn.execute(
                    "INSERT INTO donor_snippets_fts(rowid, text, voice_bucket, topic_tags) VALUES (?, ?, ?, ?)",
                    (existing["id"], text, new_bucket, " ".join(row.get("topic_tags", []))),
                )
    conn.commit()
    return inserted


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS c FROM donor_snippets").fetchone()["c"]
    embedded = conn.execute("SELECT COUNT(*) AS c FROM snippet_embeddings").fetchone()["c"]
    buckets = {
        row["voice_bucket"]: row["c"]
        for row in conn.execute(
            "SELECT voice_bucket, COUNT(*) AS c FROM donor_snippets GROUP BY voice_bucket ORDER BY c DESC"
        ).fetchall()
    }
    langs = {
        row["lang_hint"]: row["c"]
        for row in conn.execute(
            "SELECT lang_hint, COUNT(*) AS c FROM donor_snippets GROUP BY lang_hint ORDER BY c DESC"
        ).fetchall()
    }
    return {"total_rows": total, "embedded_rows": embedded, "bucket_counts": buckets, "lang_counts": langs}


def rows_missing_embeddings(conn: sqlite3.Connection, limit: int = 500) -> list[dict[str, Any]]:
    sql = """
    SELECT d.id, d.text, d.voice_bucket, d.lang_hint, d.topic_tags_json
         , d.content_role
    FROM donor_snippets d
    LEFT JOIN snippet_embeddings e ON d.id = e.snippet_id
    WHERE e.snippet_id IS NULL
    ORDER BY d.id ASC
    LIMIT ?
    """
    rows = []
    for row in conn.execute(sql, (limit,)).fetchall():
        rows.append(
            {
                "id": row["id"],
                "text": row["text"],
                "voice_bucket": row["voice_bucket"],
                "lang_hint": row["lang_hint"],
                "content_role": row["content_role"],
                "topic_tags": json.loads(row["topic_tags_json"]),
            }
        )
    return rows


def upsert_embedding(conn: sqlite3.Connection, snippet_id: int, model: str, vector: list[float]) -> None:
    conn.execute(
        """
        INSERT INTO snippet_embeddings (snippet_id, model, dim, vector_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(snippet_id) DO UPDATE SET
            model=excluded.model,
            dim=excluded.dim,
            vector_json=excluded.vector_json
        """,
        (snippet_id, model, len(vector), json.dumps(vector)),
    )
    conn.commit()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    import math

    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_query_rows(
    conn: sqlite3.Connection,
    query_vector: list[float],
    bucket: str = "",
    tag: str = "",
    limit: int = 8,
) -> list[dict[str, Any]]:
    sql = """
    SELECT d.*, e.vector_json
    FROM donor_snippets d
    JOIN snippet_embeddings e ON d.id = e.snippet_id
    """
    clauses = []
    params: list[Any] = []
    if bucket:
        clauses.append("d.voice_bucket = ?")
        params.append(bucket)
    if tag:
        clauses.append("d.topic_tags_json LIKE ?")
        params.append(f'%"{tag}"%')
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    candidates = []
    for row in conn.execute(sql, params).fetchall():
        vector = json.loads(row["vector_json"])
        sim = cosine_similarity(query_vector, vector)
        candidates.append(
            (
                sim,
                {
                    "text": row["text"],
                    "platform": row["platform"],
                    "source_kind": row["source_kind"],
                    "content_role": row["content_role"],
                    "audience_mode": row["audience_mode"],
                    "lang_hint": row["lang_hint"],
                    "voice_bucket": row["voice_bucket"],
                    "donor_score": row["donor_score"],
                    "topic_tags": json.loads(row["topic_tags_json"]),
                    "source_ref": json.loads(row["source_ref_json"]),
                },
            )
        )
    candidates.sort(key=lambda item: (-item[0], -item[1]["donor_score"], len(item[1]["text"])))
    return [row for _, row in candidates[:limit]]


def query_rows(
    conn: sqlite3.Connection,
    query: str,
    bucket: str = "",
    tag: str = "",
    limit: int = 8,
) -> list[dict[str, Any]]:
    query_tokens = [tok.lower() for tok in TOKEN_RE.findall(query)]
    if not query_tokens:
        return []
    fts_query = " OR ".join(query_tokens)

    sql = """
    SELECT d.*
    FROM donor_snippets d
    JOIN donor_snippets_fts f ON d.id = f.rowid
    WHERE donor_snippets_fts MATCH ?
    """
    params: list[Any] = [fts_query]

    if bucket:
        sql += " AND d.voice_bucket = ?"
        params.append(bucket)
    if tag:
        sql += " AND d.topic_tags_json LIKE ?"
        params.append(f'%"{tag}"%')

    sql += " ORDER BY d.donor_score DESC, d.id DESC LIMIT ?"
    params.append(limit)

    rows = []
    for row in conn.execute(sql, params).fetchall():
        rows.append(
            {
                "text": row["text"],
                    "platform": row["platform"],
                    "source_kind": row["source_kind"],
                    "content_role": row["content_role"],
                    "audience_mode": row["audience_mode"],
                "lang_hint": row["lang_hint"],
                "voice_bucket": row["voice_bucket"],
                "donor_score": row["donor_score"],
                "topic_tags": json.loads(row["topic_tags_json"]),
                "source_ref": json.loads(row["source_ref_json"]),
            }
        )
    return rows
