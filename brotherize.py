#!/usr/bin/env python3
"""One-command CLI for Brotherizer v1."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_json(cmd: list[str], env: dict[str, str] | None = None) -> dict:
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", default=str(ROOT / "data" / "donor_packs" / "english_v2.ndjson"))
    parser.add_argument("--db", default="")
    parser.add_argument("--mode", default="")
    parser.add_argument("--text", required=True)
    parser.add_argument("--query", default="")
    parser.add_argument("--bucket", default="")
    parser.add_argument("--fallback-bucket", default="reply_bodies")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--model", default="sonar")
    parser.add_argument("--use-xai-judge", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    env = dict(os.environ)
    if not env.get("PERPLEXITY_API_KEY"):
        print("Missing PERPLEXITY_API_KEY", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        rewrite_path = Path(tmpdir) / "rewrite.json"
        reranked_path = Path(tmpdir) / "reranked.json"

        subprocess.run(
            [
                sys.executable,
                str(ROOT / "rewrite" / "rewrite_executor.py"),
                "--pack",
                args.pack,
                *(["--db", args.db] if args.db else []),
                *(["--mode", args.mode] if args.mode else []),
                "--source-text",
                args.text,
                "--query",
                args.query,
                "--preferred-bucket",
                args.bucket,
                "--fallback-bucket",
                args.fallback_bucket,
                "--top-k",
                str(args.top_k),
                "--candidate-count",
                str(args.candidate_count),
                "--model",
                args.model,
                "--out",
                str(rewrite_path),
            ],
            check=True,
            env=env,
        )

        subprocess.run(
            [
                sys.executable,
                str(ROOT / "rewrite" / "rewrite_reranker.py"),
                "--input",
                str(rewrite_path),
                *(["--use-xai-judge"] if args.use_xai_judge else []),
                "--out",
                str(reranked_path),
            ],
            check=True,
            env=env,
        )

        result = json.loads(reranked_path.read_text())
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
