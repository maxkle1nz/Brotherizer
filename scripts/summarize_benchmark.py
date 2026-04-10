#!/usr/bin/env python3
"""Summarize Brotherizer benchmark runs into a short report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def classify_run(run: dict) -> str:
    score = float(run.get("rerank_score") or 0)
    penalty = float(run.get("composition_penalty") or 0)
    judge = run.get("xai_judge_score")
    if judge is not None and float(judge) >= 8 and penalty <= 0.35 and score >= 3:
        return "strong"
    if score >= 2.4 and penalty <= 0.55:
        return "usable"
    return "experimental"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    data = json.loads(args.input.read_text())
    report = {
        "cases": [],
        "mode_summary": {},
    }

    mode_buckets: dict[str, list[str]] = {}
    for case in data:
        case_entry = {
            "name": case["name"],
            "runs": [],
        }
        for run in case["runs"]:
            classification = classify_run(run)
            case_entry["runs"].append(
                {
                    "mode": run["mode"],
                    "classification": classification,
                    "winner_text": run["winner_text"],
                    "rerank_score": run["rerank_score"],
                    "composition_penalty": run["composition_penalty"],
                    "xai_judge_score": run.get("xai_judge_score"),
                    "donor_buckets": run.get("donor_buckets", []),
                    "style_signals": run.get("style_signals", []),
                }
            )
            mode_buckets.setdefault(run["mode"], []).append(classification)
        report["cases"].append(case_entry)

    for mode, classes in mode_buckets.items():
        strong = classes.count("strong")
        usable = classes.count("usable")
        experimental = classes.count("experimental")
        if strong >= max(1, len(classes) // 2):
            overall = "ready"
        elif strong + usable >= max(1, len(classes) - 1):
            overall = "usable"
        else:
            overall = "experimental"
        report["mode_summary"][mode] = {
            "overall": overall,
            "strong": strong,
            "usable": usable,
            "experimental": experimental,
            "total": len(classes),
        }

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
