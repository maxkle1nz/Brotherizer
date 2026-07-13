#!/usr/bin/env python3
"""Codex-native helper for running Brotherizer without Perplexity generation."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


REQUIRED_ROOT_FILES = (
    "configs/brotherizer_modes.json",
    "retrieval/rewrite_context_builder.py",
    "rewrite/rewrite_reranker.py",
)

PACK_BY_BUCKET = {
    "british_banter": "british_banter_v2.ndjson",
    "british_casual": "british_casual_v2.ndjson",
    "british_professional_human": "british_professional_human_v1.ndjson",
    "casual_us_human": "casual_us_human_v1.ndjson",
    "en_professional_human": "en_professional_human_v1.ndjson",
    "en_reflective": "en_reflective_v1.ndjson",
    "ptbr_casual": "ptbr_v2.ndjson",
    "ptbr_ironic": "ptbr_v2.ndjson",
    "ptbr_professional_human": "ptbr_professional_human_v1.ndjson",
    "ptbr_reflective": "ptbr_reflective_v1.ndjson",
    "reply_bodies": "english_v3.ndjson",
    "worldwide_ironic": "english_v3.ndjson",
}


def is_brotherizer_root(path: Path) -> bool:
    return all((path / item).exists() for item in REQUIRED_ROOT_FILES)


def candidate_roots(explicit_root: str | None) -> list[Path]:
    roots: list[Path] = []
    if explicit_root:
        roots.append(Path(explicit_root).expanduser())
    if os.environ.get("BROTHERIZER_ROOT"):
        roots.append(Path(os.environ["BROTHERIZER_ROOT"]).expanduser())

    cwd = Path.cwd().resolve()
    roots.extend([cwd, *cwd.parents])

    script_path = Path(__file__).resolve()
    roots.extend(script_path.parents)

    home = Path.home()
    roots.extend(
        [
            home / "Documents" / "Brotherizer",
            home / "documents" / "Brotherizer",
            home / "Brotherizer",
        ]
    )
    return roots


def find_root(explicit_root: str | None = None) -> Path:
    seen: set[Path] = set()
    for root in candidate_roots(explicit_root):
        try:
            resolved = root.resolve()
        except FileNotFoundError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if is_brotherizer_root(resolved):
            return resolved
    searched = "\n".join(f"- {path}" for path in seen)
    raise SystemExit(
        "Could not locate a Brotherizer checkout. Set BROTHERIZER_ROOT or pass --root.\n"
        f"Searched:\n{searched}"
    )


def add_root_to_path(root: Path) -> None:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path | None, data: Any) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n")
    print(rendered)


def split_buckets(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_pack_paths(root: Path, preferred_bucket: str, explicit_pack: str | None) -> list[Path]:
    if explicit_pack:
        pack = Path(explicit_pack).expanduser()
        if not pack.is_absolute():
            pack = root / pack
        return [pack]

    packs: list[Path] = []
    for bucket in split_buckets(preferred_bucket):
        pack_name = PACK_BY_BUCKET.get(bucket)
        if not pack_name:
            continue
        pack = root / "data" / "donor_packs" / pack_name
        if pack.exists() and pack not in packs:
            packs.append(pack)

    if not packs:
        fallback = root / "data" / "donor_packs" / "english_v3.ndjson"
        if fallback.exists():
            packs.append(fallback)

    missing = [str(pack) for pack in packs if not pack.exists()]
    if missing:
        raise SystemExit("Missing donor pack(s):\n" + "\n".join(missing))
    return packs


def load_pack_rows(pack_paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    from retrieval.donor_index import load_rows

    for pack in pack_paths:
        for row in load_rows(pack):
            key = (row.get("voice_bucket", ""), row.get("text", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = find_root(args.root)
    add_root_to_path(root)

    from retrieval.rewrite_context_builder import build_payload as build_context_payload
    from retrieval.rewrite_context_builder import resolve_mode, select_rows

    query, preferred_bucket, _resolved_db, mode_profile = resolve_mode(
        args.mode,
        args.query,
        args.bucket,
        None,
    )
    if not query:
        raise SystemExit("query is required unless --mode supplies one")

    pack_paths = resolve_pack_paths(root, preferred_bucket, args.pack)
    rows = load_pack_rows(pack_paths)
    selected = select_rows(
        rows=rows,
        query=query,
        preferred_bucket=preferred_bucket,
        fallback_bucket=args.fallback_bucket,
        top_k=args.top_k,
    )

    payload = build_context_payload(
        args.text,
        query,
        selected,
        preferred_bucket,
        style_signals=[],
        mode_profile=mode_profile,
        surface_mode=args.surface_mode,
    )
    payload["_codex_runtime"] = {
        "root": str(root),
        "pack_paths": [str(path) for path in pack_paths],
        "generator": "codex",
        "external_generation_provider": None,
    }
    return payload


def normalize_candidates(raw: Any) -> list[dict[str, str]]:
    if isinstance(raw, dict):
        raw_candidates = raw.get("candidates", [])
    elif isinstance(raw, list):
        raw_candidates = raw
    else:
        raise SystemExit("Candidates must be a JSON object with candidates[] or a JSON array")

    candidates: list[dict[str, str]] = []
    for index, item in enumerate(raw_candidates, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"Candidate #{index} must be an object")
        text = str(item.get("text", "")).strip()
        if not text:
            raise SystemExit(f"Candidate #{index} is missing text")
        label = str(item.get("label", f"codex-{index}")).strip() or f"codex-{index}"
        why = str(item.get("why", "")).strip()
        candidates.append({"label": label, "text": text, "why": why})
    if not candidates:
        raise SystemExit("At least one candidate is required")
    return candidates


def rerank(args: argparse.Namespace) -> dict[str, Any]:
    root = find_root(args.root)
    add_root_to_path(root)

    from rewrite.rewrite_reranker import rerank_payload

    payload = load_json(Path(args.payload))
    candidate_data = load_json(Path(args.candidates))
    merged = dict(payload)
    merged["candidates"] = normalize_candidates(candidate_data)
    result = rerank_payload(merged, use_xai_judge=False)
    result["_codex_runtime"] = {
        **dict(payload.get("_codex_runtime", {})),
        "root": str(root),
        "reranker": "brotherizer-local-heuristic",
    }
    return result


def doctor(args: argparse.Namespace) -> dict[str, Any]:
    root = find_root(args.root)
    modes = load_json(root / "configs" / "brotherizer_modes.json")
    packs = sorted(str(path.relative_to(root)) for path in (root / "data" / "donor_packs").glob("*.ndjson"))
    return {
        "ok": True,
        "root": str(root),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "modes": sorted(modes.keys()),
        "donor_packs": packs,
        "codex_native_generation": True,
        "requires_perplexity_api_key": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_root = argparse.ArgumentParser(add_help=False)
    common_root.add_argument("--root", default="", help="Brotherizer checkout root. Defaults to BROTHERIZER_ROOT/current tree/~/Documents/Brotherizer.")

    payload_parser = subparsers.add_parser("payload", parents=[common_root])
    payload_parser.add_argument("--text", required=True)
    payload_parser.add_argument("--mode", default="seriously_english_mode")
    payload_parser.add_argument("--surface-mode", default="")
    payload_parser.add_argument("--query", default="")
    payload_parser.add_argument("--bucket", default="")
    payload_parser.add_argument("--fallback-bucket", default="reply_bodies")
    payload_parser.add_argument("--pack", default="")
    payload_parser.add_argument("--top-k", type=int, default=6)
    payload_parser.add_argument("--out", type=Path)

    rerank_parser = subparsers.add_parser("rerank", parents=[common_root])
    rerank_parser.add_argument("--payload", required=True)
    rerank_parser.add_argument("--candidates", required=True)
    rerank_parser.add_argument("--out", type=Path)

    doctor_parser = subparsers.add_parser("doctor", parents=[common_root])
    doctor_parser.add_argument("--out", type=Path)

    args = parser.parse_args()
    if args.command == "payload":
        write_json(args.out, build_payload(args))
    elif args.command == "rerank":
        write_json(args.out, rerank(args))
    elif args.command == "doctor":
        write_json(args.out, doctor(args))
    else:  # pragma: no cover
        parser.error(f"unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
