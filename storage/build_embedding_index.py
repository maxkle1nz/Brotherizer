#!/usr/bin/env python3
"""Build semantic embedding index for Brotherizer corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .corpus_db import connect, rows_missing_embeddings, upsert_embedding, stats
    from integrations.ollama_embedder import embed_text
except ImportError:  # pragma: no cover - script-mode fallback
    import sys

    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT / "integrations"))
    from corpus_db import connect, rows_missing_embeddings, upsert_embedding, stats
    from ollama_embedder import embed_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--model", default="nomic-embed-text")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    conn = connect(args.db)
    rows = rows_missing_embeddings(conn, limit=args.limit)
    embedded = 0
    for row in rows:
        vector = embed_text(row["text"], model=args.model)
        upsert_embedding(conn, row["id"], args.model, vector)
        embedded += 1
    summary = stats(conn)
    summary["embedded_now"] = embedded
    summary["db"] = str(args.db)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
