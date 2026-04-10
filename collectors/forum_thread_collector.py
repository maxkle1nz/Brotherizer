#!/usr/bin/env python3
"""Collect comment-space and forum-thread text into NDJSON for Brotherizer."""

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
from urllib.parse import urljoin

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
}

SPACE_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+")

BAD_PREFIXES = (
    "cookie",
    "sign up",
    "log in",
    "advertisement",
    "related articles",
    "share this",
    "javascript is disabled",
    "submitted ",
    "posted ",
    "share ",
    "use of this site constitutes acceptance",
    "reddit and the alien logo",
    "rendered by pid",
)

THREAD_HINTS = (
    "forum",
    "thread",
    "comment",
    "reply",
    "posted by",
    "replied",
    "member",
    "joined",
)

METADATA_PATTERNS = (
    re.compile(r"^submitted\s+\d+"),
    re.compile(r"^posted\s+\d+"),
    re.compile(r"^\d+\s+(hours?|days?|minutes?)\s+ago\b"),
    re.compile(r"\bself\.[a-z0-9_]+\b", re.IGNORECASE),
    re.compile(r"\bjoin one of thousands of communities\b", re.IGNORECASE),
    re.compile(r"\bfront page of the internet\b", re.IGNORECASE),
    re.compile(r"\ball rights reserved\b", re.IGNORECASE),
    re.compile(r"\bprivacy policy\b", re.IGNORECASE),
    re.compile(r"\buser agreement\b", re.IGNORECASE),
    re.compile(r"\bregistered trademarks?\b", re.IGNORECASE),
    re.compile(r"\brendered by pid\b", re.IGNORECASE),
    re.compile(r"\bby\s+[A-Za-z0-9_\-]{2,}\s*$"),
)


def normalize_text(text: str) -> str:
    text = unescape(text)
    text = URL_RE.sub("", text)
    return SPACE_RE.sub(" ", text).strip()


def looks_like_comment(text: str, min_chars: int, max_chars: int) -> bool:
    lowered = text.lower().strip()
    if len(text) < min_chars or len(text) > max_chars:
        return False
    if any(lowered.startswith(prefix) for prefix in BAD_PREFIXES):
        return False
    if sum(ch.isalpha() for ch in text) < 24:
        return False
    if any(pattern.search(text) for pattern in METADATA_PATTERNS):
        return False
    if lowered.count("reply") > 3:
        return False
    return True


def score_block(text: str) -> int:
    lowered = text.lower()
    score = 0
    if any(hint in lowered for hint in ("mate", "innit", "banter", "taking the piss", "fair play", "reckon")):
        score += 3
    if any(hint in lowered for hint in ("lol", "lmao", "nah", "yeah", "bro", "tbf", "ngl")):
        score += 2
    if "?" in text:
        score += 1
    if len(text.split()) <= 60:
        score += 1
    return score


def fetch_html(url: str) -> str | None:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=40)
    if resp.status_code >= 400:
        print(f"[warn] {url} -> HTTP {resp.status_code}", file=sys.stderr)
        return None
    return resp.text


def extract_old_reddit_thread_urls(listing_url: str, html: str, limit: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for link in soup.select("a.title, a[href*='/comments/']"):
        href = (link.get("href") or "").strip()
        if not href or "/comments/" not in href:
            continue
        full = urljoin(listing_url, href)
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)
        if len(urls) >= limit:
            break
    return urls


def extract_old_reddit_comments(html: str, min_chars: int, max_chars: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "form"]):
        tag.decompose()

    comments: list[tuple[int, str]] = []
    seen: set[str] = set()
    selectors = [
        ".comment .usertext-body",
        ".entry .usertext-body",
        ".comment .md",
        ".entry .md",
    ]
    for selector in selectors:
        for tag in soup.select(selector):
            text = normalize_text(tag.get_text(" ", strip=True))
            if not looks_like_comment(text, min_chars, max_chars):
                continue
            if text in seen:
                continue
            seen.add(text)
            score = score_block(text) + 4
            comments.append((score, text))

    comments.sort(key=lambda item: (-item[0], len(item[1])))
    return [text for _, text in comments]


def extract_comment_blocks(html: str, min_chars: int, max_chars: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "form"]):
        tag.decompose()

    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    selectors = [
        "[class*=comment]",
        "[id*=comment]",
        "[class*=reply]",
        "[class*=post]",
        "[class*=message]",
        "[class*=body]",
        "article",
        "blockquote",
        "p",
        "li",
    ]

    for selector in selectors:
        for tag in soup.select(selector):
            text = normalize_text(tag.get_text(" ", strip=True))
            if not looks_like_comment(text, min_chars, max_chars):
                continue
            if text in seen:
                continue
            seen.add(text)
            score = score_block(text)
            if any(hint in selector.lower() for hint in THREAD_HINTS):
                score += 2
            candidates.append((score, text))

    candidates.sort(key=lambda item: (-item[0], len(item[1])))
    return [text for _, text in candidates]


def load_targets(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("targets file must be a JSON list")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-chars", type=int, default=28)
    parser.add_argument("--max-chars", type=int, default=420)
    parser.add_argument("--sleep-ms", type=int, default=500)
    parser.add_argument("--per-page-limit", type=int, default=40)
    parser.add_argument("--thread-limit", type=int, default=12)
    args = parser.parse_args()

    targets = load_targets(args.targets)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0

    with args.out.open("w", encoding="utf-8") as handle:
        for target in targets:
            url = target.get("url", "").strip()
            if not url:
                continue
            try:
                listing_html = fetch_html(url)
                if not listing_html:
                    continue

                emitted = 0
                if "old.reddit.com" in url:
                    thread_urls = extract_old_reddit_thread_urls(url, listing_html, args.thread_limit)
                    for thread_url in thread_urls:
                        thread_html = fetch_html(thread_url)
                        if not thread_html:
                            continue
                        blocks = extract_old_reddit_comments(thread_html, args.min_chars, args.max_chars)
                        for text in blocks[: args.per_page_limit]:
                            row = {
                                "platform": target.get("platform", "web"),
                                "source_kind": "forum-comment",
                                "name": target.get("name", ""),
                                "url": thread_url,
                                "lang_hint": target.get("lang", "en"),
                                "topic_tags": target.get("topic_tags", []),
                                "audience_mode": target.get("audience_mode", "reply-like"),
                                "text": text,
                            }
                            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                            written += 1
                            emitted += 1
                        time.sleep(args.sleep_ms / 1000)
                if emitted == 0:
                    blocks = extract_comment_blocks(listing_html, args.min_chars, args.max_chars)
                    for text in blocks[: args.per_page_limit]:
                        row = {
                            "platform": target.get("platform", "web"),
                            "source_kind": target.get("source_kind", "forum-thread"),
                            "name": target.get("name", ""),
                            "url": url,
                            "lang_hint": target.get("lang", "en"),
                            "topic_tags": target.get("topic_tags", []),
                            "audience_mode": target.get("audience_mode", "reply-like"),
                            "text": text,
                        }
                        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                        written += 1
            except Exception as exc:
                print(f"[warn] {url} -> {exc}", file=sys.stderr)
            time.sleep(args.sleep_ms / 1000)

    print(json.dumps({"ok": True, "rows_written": written, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
