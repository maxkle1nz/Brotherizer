#!/usr/bin/env python3
"""Multimodal style radar storage for Brotherizer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS style_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_key TEXT NOT NULL UNIQUE,
    signal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    aesthetic_tags_json TEXT DEFAULT '[]',
    cultural_tags_json TEXT DEFAULT '[]',
    language_tags_json TEXT DEFAULT '[]',
    meme_family TEXT DEFAULT '',
    caption_style TEXT DEFAULT '',
    visual_style TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    source_platform TEXT DEFAULT '',
    image_ref TEXT DEFAULT '',
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS snippet_signal_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snippet_text_hash TEXT NOT NULL,
    signal_key TEXT NOT NULL,
    strength REAL DEFAULT 0,
    rationale TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(snippet_text_hash, signal_key)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def upsert_signal(conn: sqlite3.Connection, signal: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO style_signals (
            signal_key, signal_type, title, description,
            aesthetic_tags_json, cultural_tags_json, language_tags_json,
            meme_family, caption_style, visual_style,
            source_url, source_platform, image_ref, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(signal_key) DO UPDATE SET
            signal_type=excluded.signal_type,
            title=excluded.title,
            description=excluded.description,
            aesthetic_tags_json=excluded.aesthetic_tags_json,
            cultural_tags_json=excluded.cultural_tags_json,
            language_tags_json=excluded.language_tags_json,
            meme_family=excluded.meme_family,
            caption_style=excluded.caption_style,
            visual_style=excluded.visual_style,
            source_url=excluded.source_url,
            source_platform=excluded.source_platform,
            image_ref=excluded.image_ref,
            metadata_json=excluded.metadata_json
        """,
        (
            signal["signal_key"],
            signal.get("signal_type", "aesthetic_cluster"),
            signal.get("title", ""),
            signal.get("description", ""),
            json.dumps(signal.get("aesthetic_tags", []), ensure_ascii=False),
            json.dumps(signal.get("cultural_tags", []), ensure_ascii=False),
            json.dumps(signal.get("language_tags", []), ensure_ascii=False),
            signal.get("meme_family", ""),
            signal.get("caption_style", ""),
            signal.get("visual_style", ""),
            signal.get("source_url", ""),
            signal.get("source_platform", ""),
            signal.get("image_ref", ""),
            json.dumps(signal.get("metadata", {}), ensure_ascii=False),
        ),
    )
    conn.commit()


def upsert_link(
    conn: sqlite3.Connection,
    *,
    snippet_text_hash: str,
    signal_key: str,
    strength: float,
    rationale: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO snippet_signal_links (snippet_text_hash, signal_key, strength, rationale)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(snippet_text_hash, signal_key) DO UPDATE SET
            strength=excluded.strength,
            rationale=excluded.rationale
        """,
        (snippet_text_hash, signal_key, strength, rationale),
    )
    conn.commit()


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    total_signals = conn.execute("SELECT COUNT(*) AS c FROM style_signals").fetchone()["c"]
    total_links = conn.execute("SELECT COUNT(*) AS c FROM snippet_signal_links").fetchone()["c"]
    signal_types = {
        row["signal_type"]: row["c"]
        for row in conn.execute(
            "SELECT signal_type, COUNT(*) AS c FROM style_signals GROUP BY signal_type ORDER BY c DESC"
        ).fetchall()
    }
    return {
        "total_signals": total_signals,
        "total_links": total_links,
        "signal_types": signal_types,
    }


def query_signals(
    conn: sqlite3.Connection,
    *,
    language_tag: str = "",
    intended_bucket: str = "",
    limit: int = 4,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM style_signals WHERE 1=1"
    params: list[Any] = []
    if language_tag:
        sql += " AND language_tags_json LIKE ?"
        params.append(f'%"{language_tag}"%')
    rows = conn.execute(sql, params).fetchall()

    out = []
    for row in rows:
        metadata = json.loads(row["metadata_json"])
        if intended_bucket and metadata.get("intended_bucket") not in {"", intended_bucket}:
            continue
        out.append(
            {
                "signal_key": row["signal_key"],
                "signal_type": row["signal_type"],
                "title": row["title"],
                "description": row["description"],
                "aesthetic_tags": json.loads(row["aesthetic_tags_json"]),
                "cultural_tags": json.loads(row["cultural_tags_json"]),
                "language_tags": json.loads(row["language_tags_json"]),
                "meme_family": row["meme_family"],
                "caption_style": row["caption_style"],
                "visual_style": row["visual_style"],
                "metadata": metadata,
            }
        )
    return out[:limit]
