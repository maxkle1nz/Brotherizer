#!/usr/bin/env python3
"""Small benchmark harness for Brotherizer modes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_runtime_env() -> dict[str, str]:
    env = dict(os.environ)
    candidates = []
    explicit = env.get("BROTHERIZER_ENV_FILE", "").strip()
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(ROOT / ".runtime" / "brotherizer.env")

    for path in candidates:
        if not path.exists():
            continue
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip())
        break
    return env


def run_mode(db: Path, mode: str, text: str, use_xai_judge: bool = False) -> dict:
    env = load_runtime_env()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "result.json"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "brotherize.py"),
                "--db",
                str(db),
                "--mode",
                mode,
                "--text",
                text,
                *(["--use-xai-judge"] if use_xai_judge else []),
                "--out",
                str(out),
            ],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        return json.loads(out.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path, help="JSON array: [{name, text, modes:[...]}]")
    parser.add_argument("--use-xai-judge", action="store_true")
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text())
    results = []
    for case in cases:
        case_result = {"name": case["name"], "text": case["text"], "runs": []}
        for mode in case["modes"]:
            data = run_mode(args.db, mode, case["text"], use_xai_judge=args.use_xai_judge)
            winner = data.get("winner", {})
            case_result["runs"].append(
                {
                    "mode": mode,
                    "mode_profile": data.get("mode_profile"),
                    "winner_text": winner.get("text", ""),
                    "winner_label": winner.get("label", ""),
                    "rerank_score": winner.get("rerank_score"),
                    "composition_penalty": winner.get("composition_penalty"),
                    "xai_judge_score": winner.get("xai_judge_score"),
                    "judge_enabled": args.use_xai_judge,
                    "donor_buckets": [row.get("voice_bucket", "") for row in data.get("donor_snippets", [])[:6]],
                    "style_signals": [row.get("title") or row.get("signal_key", "") for row in data.get("style_signals", [])],
                }
            )
        results.append(case_result)

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
