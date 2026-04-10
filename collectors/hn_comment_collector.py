#!/usr/bin/env python3
"""Collect public Hacker News comment text into NDJSON for Brotherizer."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

SEARCH_API = "https://hn.algolia.com/api/v1/search_by_date"
SPACE_RE = re.compile(r"\s+")
TAG_RE = re.compile(r"<[^>]+>")


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = TAG_RE.sub(" ", text)
    return SPACE_RE.sub(" ", text).strip()


def fetch_comments(query: str, hits_per_page: int, pages: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(pages):
        params = {
            "query": query,
            "tags": "comment",
            "hitsPerPage": hits_per_page,
            "page": page,
        }
        resp = requests.get(SEARCH_API, params=params, timeout=40)
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload.get("hits", []))
        if page >= payload.get("nbPages", 0) - 1:
            break
        time.sleep(0.25)
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--hits-per-page", type=int, default=50)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--min-chars", type=int, default=40)
    parser.add_argument("--max-chars", type=int, default=600)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--topic-tags", default="english-worldwide,discussion,comments")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    topic_tags = [tag.strip() for tag in args.topic_tags.split(",") if tag.strip()]

    try:
        hits = fetch_comments(args.query, args.hits_per_page, args.pages)
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    written = 0
    with args.out.open("w", encoding="utf-8") as handle:
        for hit in hits:
            text = normalize_text(hit.get("comment_text") or "")
            if len(text) < args.min_chars or len(text) > args.max_chars:
                continue
            row = {
                "platform": "hackernews",
                "source_kind": "comment",
                "query": args.query,
                "lang_hint": args.lang,
                "topic_tags": topic_tags,
                "audience_mode": "reply-like",
                "text": text,
                "object_id": hit.get("objectID", ""),
                "story_title": hit.get("story_title", ""),
                "author": hit.get("author", ""),
                "created_at": hit.get("created_at", ""),
                "story_url": hit.get("story_url", ""),
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    print(json.dumps({"ok": True, "rows_written": written, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
