#!/usr/bin/env python3
"""Build Brotherizer corpus database from donor packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from corpus_db import connect, stats, upsert_rows


def load_rows(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True, type=Path)
    parser.add_argument("--db", required=True, type=Path)
    args = parser.parse_args()

    rows = load_rows(args.inputs)
    conn = connect(args.db)
    inserted = upsert_rows(conn, rows)
    summary = stats(conn)
    summary["inserted_rows"] = inserted
    summary["input_rows"] = len(rows)
    summary["db"] = str(args.db)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
