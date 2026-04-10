#!/usr/bin/env python3
"""Seed Brotherizer style radar database from curated signals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .style_radar_db import connect, stats, upsert_signal
except ImportError:  # pragma: no cover - script-mode fallback
    from style_radar_db import connect, stats, upsert_signal


def load_signals(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--db", required=True, type=Path)
    args = parser.parse_args()

    signals = load_signals(args.input)
    conn = connect(args.db)
    for signal in signals:
        upsert_signal(conn, signal)
    summary = stats(conn)
    summary["input_signals"] = len(signals)
    summary["db"] = str(args.db)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
