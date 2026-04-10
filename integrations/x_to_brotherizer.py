#!/usr/bin/env python3
"""Convert X/Twitter actor output into Brotherizer-ready snippet NDJSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SPACE_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+")


def normalize(text: str) -> str:
    text = URL_RE.sub("", text)
    return SPACE_RE.sub(" ", text).strip()


def infer_tags(item: dict) -> tuple[str, list[str]]:
    text = (item.get("fullText") or item.get("text") or "").lower()
    lang = item.get("lang") or "en"
    tags: list[str] = []

    if lang.startswith("pt"):
        tags.append("ptbr")
    else:
        tags.append("english-worldwide")

    if "banter" in text:
        tags.append("banter")
    if any(term in text for term in ("lol", "lmao", "muh", "nah", "lowkey", "imo")):
        tags.append("irony")
    if any(term in text for term in ("football", "gamer", "gaming", "fifa", "madrid", "barca")):
        tags.append("sports-or-gaming")
    if item.get("isReply"):
        tags.append("reply-like")
    return lang, tags


def infer_bucket(lang: str, tags: list[str], text: str) -> str:
    lowered = text.lower()
    if lang.startswith("pt"):
        if any(term in lowered for term in ("kkkk", "kkk", "mano", "cara", "meme", "vsf", "pqp")):
            return "ptbr_ironic"
        return "ptbr_casual"
    if "banter" in tags and any(term in lowered for term in ("british", "innit", "rubbish", "bollocks", "mate")):
        return "british_banter"
    if "irony" in tags or "banter" in tags:
        return "worldwide_ironic"
    return "worldwide_discussion"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-chars", type=int, default=24)
    parser.add_argument("--max-chars", type=int, default=320)
    args = parser.parse_args()

    items = json.loads(args.input.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    seen: set[str] = set()
    with args.out.open("w", encoding="utf-8") as handle:
        for item in items:
            text = normalize(item.get("fullText") or item.get("text") or "")
            if len(text) < args.min_chars or len(text) > args.max_chars:
                continue
            if text in seen:
                continue
            seen.add(text)

            lang, tags = infer_tags(item)
            bucket = infer_bucket(lang, tags, text)

            row = {
                "platform": "x",
                "source_kind": "post" if not item.get("isReply") else "reply",
                "content_role": "reply_body" if item.get("isReply") else "post_body",
                "audience_mode": "reply-like" if item.get("isReply") else "post-like",
                "lang_hint": "pt-BR" if lang.startswith("pt") else "en",
                "topic_tags": tags,
                "voice_bucket": bucket,
                "text": text,
                "source_ref": {
                    "url": item.get("url", ""),
                    "author": (item.get("author") or {}).get("userName", ""),
                    "conversation_id": item.get("conversationId", ""),
                },
                "metadata": {
                    "like_count": item.get("likeCount", 0),
                    "reply_count": item.get("replyCount", 0),
                    "view_count": item.get("viewCount", 0),
                },
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    print(json.dumps({"ok": True, "rows_written": written, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
