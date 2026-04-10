#!/usr/bin/env python3
"""Discover source seeds for Brotherizer using Perplexity Sonar."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

API_URL = "https://api.perplexity.ai/v1/sonar"


def extract_json_block(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def build_prompt(target: str, subculture: str, region: str) -> list[dict[str, str]]:
    system = (
        "You are helping build a donor corpus for a writing-style engine. "
        "Your job is to identify public, text-rich, internet-native English sources "
        "that are valuable for learning real human phrasing and online discourse. "
        "Prefer discoverability, language quality, and distinctive voice over mainstream SEO sludge. "
        "Return strict JSON only."
    )
    user = f"""
Target language: {target}
Subculture focus: {subculture}
Region focus: {region}

Find public web sources, communities, creators, and search seeds that are useful for collecting:
- British English or worldwide English internet-native language
- irony, understatement, banter, comments, replies, shortform rhetoric
- young-adult to adult online language

Return strict JSON with this shape:
{{
  "seed_queries": ["..."],
  "priority_sources": [
    {{
      "name": "...",
      "kind": "creator|community|site|platform|query-cluster",
      "why": "...",
      "collection_hint": "youtube-comments|bluesky-search|forum-scrape|manual-review",
      "region_bias": "GB|US|worldwide|mixed"
    }}
  ],
  "avoid": ["..."],
  "notes": ["..."]
}}

Keep seed_queries concise and directly usable.
Prefer quality over quantity.
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="English")
    parser.add_argument("--subculture", default="British internet commentary, music, gaming, online pop culture")
    parser.add_argument("--region", default="UK first, then worldwide English")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", default="sonar")
    args = parser.parse_args()

    api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        print("Missing PERPLEXITY_API_KEY", file=sys.stderr)
        return 1

    payload = {
        "model": args.model,
        "messages": build_prompt(args.target, args.subculture, args.region),
        "temperature": 0.2,
        "search_mode": "web",
        "return_related_questions": True,
    }
    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()

    content = data["choices"][0]["message"]["content"]
    parsed = extract_json_block(content)
    parsed["_meta"] = {
        "model": data.get("model", args.model),
        "citations": data.get("citations", []),
        "search_results": data.get("search_results", []),
        "related_questions": data.get("related_questions", []),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "out": str(args.out), "seed_queries": len(parsed.get("seed_queries", []))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
