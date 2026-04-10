#!/usr/bin/env python3
"""Collect public Bluesky posts into NDJSON for Brotherizer."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}


def load_targets(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("targets file must be a JSON list")
    return data


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def search_posts(query: str, limit: int, cursor: str = "", sort: str = "latest") -> dict[str, Any]:
    params = {
        "q": query,
        "limit": min(limit, 100),
        "sort": sort,
    }
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(API_BASE, params=params, headers=DEFAULT_HEADERS, timeout=45)
    if resp.status_code >= 400:
        raise requests.HTTPError(
            f"{resp.status_code} {resp.reason} for query={query!r} body={resp.text[:400]}",
            response=resp,
        )
    return resp.json()


def flatten_post(source: dict[str, Any], post_view: dict[str, Any]) -> dict[str, Any] | None:
    record = post_view.get("record", {})
    text = (record.get("text") or "").strip()
    if not text:
        return None

    author = post_view.get("author", {})
    labels = [item.get("val", "") for item in post_view.get("labels", []) if item.get("val")]

    return {
        "platform": "bluesky",
        "source_kind": "post",
        "query_label": source.get("label", ""),
        "query": source.get("query", ""),
        "lang_hint": source.get("lang", ""),
        "topic_tags": source.get("topic_tags", []),
        "audience_mode": source.get("audience_mode", "post-like"),
        "uri": post_view.get("uri", ""),
        "cid": post_view.get("cid", ""),
        "text": text,
        "author_handle": author.get("handle", ""),
        "author_display_name": author.get("displayName", ""),
        "author_did": author.get("did", ""),
        "reply_count": post_view.get("replyCount", 0),
        "repost_count": post_view.get("repostCount", 0),
        "like_count": post_view.get("likeCount", 0),
        "quote_count": post_view.get("quoteCount", 0),
        "indexed_at": post_view.get("indexedAt", ""),
        "labels": labels,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-posts", type=int, default=300)
    parser.add_argument("--sleep-ms", type=int, default=300)
    parser.add_argument("--sort", choices=["latest", "top"], default="latest")
    args = parser.parse_args()

    targets = load_targets(args.targets)
    ensure_parent(args.out)
    total_rows = 0

    with args.out.open("w", encoding="utf-8") as handle:
        for source in targets:
            query = source.get("query", "").strip()
            if not query:
                continue

            cursor = ""
            fetched = 0

            while fetched < args.max_posts:
                page_size = min(100, args.max_posts - fetched)
                payload = search_posts(query=query, limit=page_size, cursor=cursor, sort=args.sort)
                posts = payload.get("posts", [])
                if not posts:
                    break

                for post in posts:
                    row = flatten_post(source, post)
                    if row is None:
                        continue
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    total_rows += 1
                    fetched += 1
                    if fetched >= args.max_posts:
                        break

                cursor = payload.get("cursor", "")
                if not cursor:
                    break
                time.sleep(args.sleep_ms / 1000)

            

    print(json.dumps({"ok": True, "rows_written": total_rows, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
