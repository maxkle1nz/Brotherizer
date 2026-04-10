#!/usr/bin/env python3
"""Normalize raw collected text into Brotherizer retrieval snippets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SPACE_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+")


def normalize_text(text: str) -> str:
    text = URL_RE.sub("", text)
    text = SPACE_RE.sub(" ", text).strip()
    return text


def lightweight_style_tags(text: str) -> dict[str, object]:
    lowered = text.lower()
    return {
        "text_len": len(text),
        "word_count": len(text.split()),
        "has_laughter": any(tok in lowered for tok in ("kkkk", "kkk", "haha", "rs", "rsrs", "lol", "lmao")),
        "has_caps_burst": any(chunk.isupper() and len(chunk) >= 3 for chunk in text.split()),
        "has_emoji_like": any(ch in text for ch in ("😂", "😭", "🔥", "💀", "🙏", "😭", "🤣", "❤️", "😍", "😅")),
        "has_question": "?" in text,
        "has_ellipsis": "..." in text,
        "has_slang_hint": any(tok in lowered for tok in ("mano", "tipo", "slk", "pprt", "tbh", "lowkey", "ngl", "idk")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-chars", type=int, default=24)
    parser.add_argument("--max-chars", type=int, default=420)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with args.input.open("r", encoding="utf-8") as src, args.out.open("w", encoding="utf-8") as dst:
        for line in src:
            row = json.loads(line)
            text = normalize_text(row.get("text", ""))
            if not text:
                continue
            if len(text) < args.min_chars or len(text) > args.max_chars:
                continue

            snippet = {
                "text": text,
                "platform": row.get("platform", ""),
                "source_kind": row.get("source_kind", ""),
                "audience_mode": row.get("audience_mode", ""),
                "lang_hint": row.get("lang_hint", ""),
                "topic_tags": row.get("topic_tags", []),
                "source_ref": {
                    "channel_id": row.get("channel_id", ""),
                    "channel_label": row.get("channel_label", ""),
                    "video_id": row.get("video_id", ""),
                    "thread_id": row.get("thread_id", ""),
                    "comment_id": row.get("comment_id", ""),
                },
                "style_features": lightweight_style_tags(text),
            }
            dst.write(json.dumps(snippet, ensure_ascii=False) + "\n")
            written += 1

    print(json.dumps({"ok": True, "snippets_written": written, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
