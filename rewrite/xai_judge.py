#!/usr/bin/env python3
"""xAI-based judge for Brotherizer rewrite candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

API_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("BROTHERIZER_XAI_MODEL", "grok-4.20-reasoning")


def extract_json_block(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def build_messages(data: dict) -> list[dict[str, str]]:
    source_text = data.get("source_text", "")
    preferred_bucket = data.get("preferred_bucket", "")
    donor_snippets = data.get("donor_snippets", [])
    candidates = data.get("candidates", [])

    donor_lines = "\n".join(
        f"- [{item.get('voice_bucket','')}] {item.get('text','')}"
        for item in donor_snippets[:8]
    )
    candidate_lines = "\n".join(
        f"- {item.get('label','candidate')}: {item.get('text','')}"
        for item in candidates
    )

    system = (
        "You are a strict rewrite judge for Brotherizer. "
        "Score candidates for semantic preservation, style fit, and anti-generic human naturalness. "
        "Return strict JSON only."
    )
    user = (
        f"Source text:\n{source_text}\n\n"
        f"Preferred bucket:\n{preferred_bucket}\n\n"
        f"Donor snippets:\n{donor_lines}\n\n"
        f"Candidates:\n{candidate_lines}\n\n"
        "Return JSON in this shape:\n"
        "{\n"
        '  "scores": [\n'
        "    {\n"
        '      "label": "candidate label",\n'
        '      "semantic_preservation": 0-10,\n'
        '      "style_fit": 0-10,\n'
        '      "anti_generic": 0-10,\n'
        '      "overall": 0-10,\n'
        '      "why": "short explanation"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        print("Missing XAI_API_KEY", file=sys.stderr)
        return 1

    data = json.loads(args.input.read_text())

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": args.model,
            "messages": build_messages(data),
            "temperature": 0.1,
        },
        timeout=120,
    )
    resp.raise_for_status()
    payload = resp.json()
    content = payload["choices"][0]["message"]["content"]
    parsed = extract_json_block(content)

    result = {
        "judge_model": args.model,
        "scores": parsed.get("scores", []),
        "_meta": payload.get("usage", {}),
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
