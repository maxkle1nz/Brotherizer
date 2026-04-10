#!/usr/bin/env python3
"""Convert Apify actor output into Brotherizer-ready snippet NDJSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SPACE_RE = re.compile(r"\s+")

BAD_PREFIXES = (
    "cookie",
    "privacy",
    "user agreement",
    "all rights reserved",
)


def normalize(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip()


def split_markdown_blocks(markdown: str) -> list[str]:
    parts = re.split(r"\n\s*\n+", markdown)
    blocks = []
    for part in parts:
        text = normalize(part.replace("#", " ").replace("|", " ").replace("*", " "))
        if text:
            blocks.append(text)
    return blocks


def looks_usable(text: str, min_chars: int, max_chars: int) -> bool:
    lowered = text.lower()
    if len(text) < min_chars or len(text) > max_chars:
        return False
    if any(lowered.startswith(prefix) for prefix in BAD_PREFIXES):
        return False
    if sum(ch.isalpha() for ch in text) < 24:
        return False
    return True


def infer_tags(item: dict) -> tuple[str, list[str]]:
    url = item.get("url", "")
    title = ((item.get("metadata") or {}).get("title") or "").lower()
    tags = []
    lang = ((item.get("metadata") or {}).get("languageCode") or "en")
    if "casualuk" in url or "casualuk" in title:
        tags.extend(["british-english", "casual", "internet-native"])
        lang = "en-GB"
    elif "/r/brasil" in url or "brasil" in title:
        tags.extend(["ptbr", "casual", "internet-native"])
        lang = "pt-BR"
    elif "hacker news" in title:
        tags.extend(["english-worldwide", "discussion", "comments"])
        lang = "en"
    else:
        tags.extend(["web", "discussion"])
    return lang, tags


def infer_content_role(item: dict, text: str) -> str:
    url = item.get("url", "")
    title = ((item.get("metadata") or {}).get("title") or "").lower()
    lowered = text.lower()

    if "news.ycombinator.com/item?id=" in url:
        return "comment_thread"
    if "news.ycombinator.com/" in url and any(term in lowered for term in ("points by", "comments", "show hn", "ask hn")):
        return "listing_or_thread_surface"
    if "reddit.com/r/" in url or "old.reddit.com/r/" in url:
        if any(term in lowered for term in ("welcome to", "subreddit", "rules", "guidelines", "modmail", "community", "weekly scheduled")):
            return "community_meta"
        return "listing_or_thread_surface"
    if "/comments/" in url:
        return "comment_thread"
    return "page_text"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-chars", type=int, default=40)
    parser.add_argument("--max-chars", type=int, default=360)
    parser.add_argument("--per-doc-limit", type=int, default=20)
    args = parser.parse_args()

    items = json.loads(args.input.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with args.out.open("w", encoding="utf-8") as handle:
        for item in items:
            lang, topic_tags = infer_tags(item)
            markdown = item.get("markdown") or item.get("text") or ""
            blocks = split_markdown_blocks(markdown)
            emitted = 0
            for text in blocks:
                if not looks_usable(text, args.min_chars, args.max_chars):
                    continue
                content_role = infer_content_role(item, text)
                row = {
                    "platform": "apify",
                    "source_kind": "web-crawl",
                    "content_role": content_role,
                    "audience_mode": "post-like",
                    "lang_hint": lang,
                    "topic_tags": topic_tags,
                    "text": text,
                    "source_ref": {
                        "url": item.get("url", ""),
                        "loaded_url": (item.get("crawl") or {}).get("loadedUrl", ""),
                        "title": (item.get("metadata") or {}).get("title", ""),
                    },
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1
                emitted += 1
                if emitted >= args.per_doc_limit:
                    break

    print(json.dumps({"ok": True, "rows_written": written, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
