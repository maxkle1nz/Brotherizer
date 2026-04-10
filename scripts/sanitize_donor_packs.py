#!/usr/bin/env python3
"""Sanitize donor packs for public distribution."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HANDLE_RE = re.compile(r"(?<!\w)@[A-Za-z0-9_]+")
SPACE_RE = re.compile(r"\s+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?])")

KEEP_KEYS = (
    "platform",
    "source_kind",
    "content_role",
    "audience_mode",
    "lang_hint",
    "topic_tags",
    "voice_bucket",
    "text",
    "donor_score",
    "source_quality_score",
)


def sanitize_text(text: str) -> str:
    text = HANDLE_RE.sub("", text)
    text = SPACE_RE.sub(" ", text).strip()
    text = SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    return text


def sanitize_row(row: dict) -> dict | None:
    sanitized = {key: row.get(key) for key in KEEP_KEYS if key in row}
    sanitized["text"] = sanitize_text(str(row.get("text", "")))
    if not sanitized["text"]:
        return None
    return sanitized


def sanitize_file(path: Path) -> tuple[int, int]:
    original_rows = 0
    written_rows = 0
    output_lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        original_rows += 1
        row = json.loads(line)
        sanitized = sanitize_row(row)
        if sanitized is None:
            continue
        output_lines.append(json.dumps(sanitized, ensure_ascii=False))
        written_rows += 1
    path.write_text("\n".join(output_lines) + ("\n" if output_lines else ""), encoding="utf-8")
    return original_rows, written_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("data/donor_packs"))
    args = parser.parse_args()

    files = sorted(args.dir.glob("*.ndjson"))
    summary = []
    for path in files:
        original, written = sanitize_file(path)
        summary.append(
            {
                "file": str(path),
                "original_rows": original,
                "written_rows": written,
            }
        )
    print(json.dumps({"files": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
