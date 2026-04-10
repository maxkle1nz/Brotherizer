#!/usr/bin/env python3
"""Collect public web page text blocks into NDJSON for Brotherizer."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from html import unescape
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
}

SPACE_RE = re.compile(r"\s+")
BAD_PREFIXES = ("cookie", "sign up", "log in", "advertisement", "related articles")


def normalize_text(text: str) -> str:
    text = unescape(text)
    text = SPACE_RE.sub(" ", text).strip()
    return text


def looks_usable(text: str, min_chars: int, max_chars: int) -> bool:
    lowered = text.lower().strip()
    if len(text) < min_chars or len(text) > max_chars:
        return False
    if any(lowered.startswith(prefix) for prefix in BAD_PREFIXES):
        return False
    if text.count("http") > 0:
        return False
    if sum(ch.isalpha() for ch in text) < 20:
        return False
    return True


def extract_blocks(html: str, min_chars: int, max_chars: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "form"]):
        tag.decompose()

    blocks: list[str] = []
    seen: set[str] = set()
    for tag in soup.find_all(["p", "li", "blockquote"]):
        text = normalize_text(tag.get_text(" ", strip=True))
        if not looks_usable(text, min_chars, max_chars):
            continue
        if text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def load_seed_urls(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    urls: list[dict[str, Any]] = []

    if isinstance(data, dict):
        meta = data.get("_meta", {})
        for item in meta.get("search_results", []):
            url = item.get("url", "").strip()
            if not url:
                continue
            urls.append(
                {
                    "name": item.get("title", ""),
                    "url": url,
                    "source_kind": "search-result",
                    "topic_tags": [],
                    "lang": "en",
                }
            )
        for item in data.get("priority_sources", []):
            # Keep priority source names for downstream manual mapping, even if no URL exists.
            if item.get("name"):
                urls.append(
                    {
                        "name": item.get("name", ""),
                        "url": "",
                        "source_kind": item.get("kind", "source"),
                        "topic_tags": [],
                        "lang": "en",
                    }
                )
        return urls

    if not isinstance(data, list):
        raise ValueError("seed input must be a JSON list or a Perplexity discovery JSON object")

    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="JSON list of sources or Perplexity discovery JSON")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-chars", type=int, default=40)
    parser.add_argument("--max-chars", type=int, default=360)
    parser.add_argument("--sleep-ms", type=int, default=400)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    seeds = load_seed_urls(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    attempted = 0

    with args.out.open("w", encoding="utf-8") as handle:
        for source in seeds:
            url = source.get("url", "").strip()
            if not url:
                continue
            attempted += 1
            if attempted > args.limit:
                break
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=40)
                if resp.status_code >= 400:
                    print(f"[warn] {url} -> HTTP {resp.status_code}", file=sys.stderr)
                    continue
                blocks = extract_blocks(resp.text, args.min_chars, args.max_chars)
                for block in blocks:
                    row = {
                        "platform": "web",
                        "source_kind": source.get("source_kind", "page"),
                        "name": source.get("name", ""),
                        "url": url,
                        "lang_hint": source.get("lang", "en"),
                        "topic_tags": source.get("topic_tags", []),
                        "audience_mode": "post-like",
                        "text": block,
                    }
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    written += 1
            except Exception as exc:
                print(f"[warn] {url} -> {exc}", file=sys.stderr)
            time.sleep(args.sleep_ms / 1000)

    print(json.dumps({"ok": True, "rows_written": written, "pages_attempted": attempted, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
