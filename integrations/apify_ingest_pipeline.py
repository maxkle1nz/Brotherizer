#!/usr/bin/env python3
"""Run a complete Apify -> Brotherizer ingestion lane."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_presets(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--presets-file", default=str(ROOT / "configs" / "apify_presets.json"))
    args = parser.parse_args()

    presets = load_presets(Path(args.presets_file))
    if args.preset not in presets:
        raise SystemExit(f"unknown preset: {args.preset}")

    preset = presets[args.preset]
    raw_output = ROOT / "data" / "raw" / f"{args.preset}.json"
    processed_output = ROOT / preset["processed_output"]
    donor_pack_output = ROOT / preset["donor_pack_output"]
    db_path = Path(args.db)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "integrations" / "apify_actor_runner.py"),
            "--actor",
            preset["actor"],
            "--input-file",
            str(ROOT / preset["input_file"]),
            "--output",
            str(raw_output),
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(ROOT / preset["converter"]),
            "--input",
            str(raw_output),
            "--out",
            str(processed_output),
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "collectors" / "donor_pack_builder.py"),
            "--inputs",
            str(processed_output),
            "--out",
            str(donor_pack_output),
        ],
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "storage" / "build_corpus_db.py"),
            "--inputs",
            str(ROOT / "data" / "donor_packs" / "english_v2.ndjson"),
            str(ROOT / "data" / "donor_packs" / "ptbr_v1.ndjson"),
            str(donor_pack_output),
            "--db",
            str(db_path),
        ],
        check=True,
    )

    print(
        json.dumps(
            {
                "ok": True,
                "preset": args.preset,
                "raw_output": str(raw_output),
                "processed_output": str(processed_output),
                "donor_pack_output": str(donor_pack_output),
                "db": str(db_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
