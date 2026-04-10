#!/usr/bin/env python3
"""Local donor-pack retrieval for Brotherizer."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in TOKEN_RE.findall(text)]


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def lexical_score(query_tokens: list[str], row: dict[str, Any]) -> float:
    text_tokens = tokenize(row.get("text", ""))
    if not text_tokens:
        return 0.0
    overlap = sum(1 for tok in query_tokens if tok in text_tokens)
    density = overlap / max(1, len(set(query_tokens)))
    bonus = row.get("donor_score", 0) / 20
    return density + bonus


def passes_filters(row: dict[str, Any], bucket: str, tag: str) -> bool:
    if bucket and row.get("voice_bucket") != bucket:
        return False
    if tag and tag not in row.get("topic_tags", []):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--bucket", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--semantic", action="store_true")
    args = parser.parse_args()

    if not args.pack and not args.db:
        raise SystemExit("use --pack or --db")

    if args.db:
        try:
            from storage.corpus_db import connect, query_rows, semantic_query_rows  # type: ignore
            from integrations.ollama_embedder import embed_text  # type: ignore
        except ImportError:  # pragma: no cover - script-mode fallback
            import sys
            ROOT = Path(__file__).resolve().parent.parent
            sys.path.insert(0, str(ROOT / "storage"))
            sys.path.insert(0, str(ROOT / "integrations"))
            from corpus_db import connect, query_rows, semantic_query_rows  # type: ignore
            from ollama_embedder import embed_text  # type: ignore

        conn = connect(args.db)
        if args.semantic:
            vec = embed_text(args.query)
            rows = semantic_query_rows(conn, vec, bucket=args.bucket, tag=args.tag, limit=args.top_k)
        else:
            rows = query_rows(conn, args.query, bucket=args.bucket, tag=args.tag, limit=args.top_k)
        top = [(row.get("donor_score", 0) / 10, row) for row in rows]
    else:
        rows = load_rows(args.pack)
        query_tokens = tokenize(args.query)

        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            if not passes_filters(row, args.bucket, args.tag):
                continue
            score = lexical_score(query_tokens, row)
            if score <= 0:
                continue
            scored.append((score, row))

        scored.sort(key=lambda item: (-item[0], -item[1].get("donor_score", 0), len(item[1].get("text", ""))))
        top = scored[: args.top_k]

    output = []
    for score, row in top:
        output.append(
            {
                "score": round(score, 4),
                "voice_bucket": row.get("voice_bucket", ""),
                "donor_score": row.get("donor_score", 0),
                "topic_tags": row.get("topic_tags", []),
                "text": row.get("text", ""),
                "platform": row.get("platform", ""),
                "source_kind": row.get("source_kind", ""),
            }
        )

    print(json.dumps({"query": args.query, "count": len(output), "results": output}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
