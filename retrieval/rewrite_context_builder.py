#!/usr/bin/env python3
"""Build a compact rewrite-conditioning payload from a donor pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .donor_index import load_rows, passes_filters, lexical_score, tokenize
except ImportError:  # pragma: no cover - script-mode fallback
    from donor_index import load_rows, passes_filters, lexical_score, tokenize

from runtime.paths import resource_path

ROOT = Path(__file__).resolve().parent.parent
FORMAT_LIBRARY_PATH = resource_path("configs", "internet_symbol_library.json")


def resolve_mode(mode: str, explicit_query: str, explicit_bucket: str, explicit_db: Path | None) -> tuple[str, str, Path | None, str]:
    if not mode:
        return explicit_query, explicit_bucket, explicit_db, "default"
    modes = json.loads(resource_path("configs", "brotherizer_modes.json").read_text())
    if mode not in modes:
        raise SystemExit(f"unknown mode: {mode}")
    cfg = modes[mode]
    return (
        explicit_query or cfg.get("query", ""),
        explicit_bucket or cfg.get("bucket", ""),
        explicit_db or (Path(cfg["db"]) if cfg.get("db") else None),
        cfg.get("profile", "default"),
    )


def resolve_formatting_pack(preferred_buckets: list[str], mode_profile: str, surface_mode: str = "") -> dict | None:
    library = json.loads(FORMAT_LIBRARY_PATH.read_text())

    if surface_mode == "caption" and ("ptbr_casual" in preferred_buckets or "ptbr_ironic" in preferred_buckets):
      return library.get("ptbr_caption")
    if surface_mode == "note" and ("ptbr_reflective" in preferred_buckets or mode_profile == "narrative"):
      return library.get("ptbr_reflective")
    if surface_mode == "note" and ("en_reflective" in preferred_buckets or mode_profile == "narrative"):
      return library.get("english_note_reflective")
    if surface_mode == "bio" and ("en_professional_human" in preferred_buckets or "british_professional_human" in preferred_buckets):
      return library.get("english_bio_operator")
    if surface_mode == "thread":
      return library.get("thread_scanner")
    if "ptbr_casual" in preferred_buckets or "ptbr_ironic" in preferred_buckets:
      return library.get("ptbr_internet")
    if "ptbr_reflective" in preferred_buckets or mode_profile == "narrative":
      return library.get("ptbr_reflective")
    if "casual_us_human" in preferred_buckets or mode_profile == "casual":
      return library.get("casual_us_reply")
    if "british_banter" in preferred_buckets:
      return library.get("british_banter")
    if "worldwide_ironic" in preferred_buckets:
      return library.get("worldwide_ironic")
    if "british_professional_human" in preferred_buckets or "en_professional_human" in preferred_buckets:
      return library.get("professional_clean")
    return None


def select_rows(
    rows: list[dict],
    query: str,
    preferred_bucket: str,
    fallback_bucket: str,
    top_k: int,
) -> list[dict]:
    query_tokens = tokenize(query)
    preferred_buckets = [item.strip() for item in preferred_bucket.split(",") if item.strip()]

    scored: list[tuple[float, dict]] = []
    for row in rows:
        if preferred_buckets and row.get("voice_bucket") not in preferred_buckets:
            continue
        score = lexical_score(query_tokens, row)
        if score <= 0:
            continue
        scored.append((score, row))

    scored.sort(key=lambda item: (-item[0], -item[1].get("donor_score", 0), len(item[1].get("text", ""))))
    selected = [row for _, row in scored[:top_k]]

    if selected or not fallback_bucket:
        return selected

    fallback_scored: list[tuple[float, dict]] = []
    for row in rows:
        if not passes_filters(row, fallback_bucket, ""):
            continue
        score = lexical_score(query_tokens, row)
        if score <= 0:
            continue
        fallback_scored.append((score, row))
    fallback_scored.sort(key=lambda item: (-item[0], -item[1].get("donor_score", 0), len(item[1].get("text", ""))))
    return [row for _, row in fallback_scored[:top_k]]


def build_payload(source_text: str, query: str, rows: list[dict], preferred_bucket: str, style_signals: list[dict] | None = None, mode_profile: str = "default", surface_mode: str = "") -> dict:
    preferred_buckets = [item.strip() for item in preferred_bucket.split(",") if item.strip()]
    formatting_pack = resolve_formatting_pack(preferred_buckets, mode_profile, surface_mode)
    if mode_profile == "casual" and "casual_us_human" in preferred_buckets:
        lowered_source = source_text.lower()
        if len(source_text) <= 160 and any(term in lowered_source for term in ("too clean", "generic", "real person", "actual person", "doesn't sound", "doesnt sound")):
            reply_like_rows = [row for row in rows if row.get("audience_mode") == "reply-like"]
            if len(reply_like_rows) >= 3:
                rows = reply_like_rows + [row for row in rows if row.get("audience_mode") != "reply-like"]
            rows = sorted(
                rows,
                key=lambda row: (
                    0 if row.get("audience_mode") == "reply-like" else 1,
                    -float(row.get("donor_score", 0) or 0),
                    len(row.get("text", "")),
                ),
            )
    style_directives = [
        "Preserve the original meaning and constraints.",
        "Prefer human asymmetry over polished AI symmetry.",
        "Borrow rhythm, rhetorical stance, and phrasing texture from donor snippets without copying verbatim.",
        "Avoid generic AI filler and over-explaining.",
    ]

    if mode_profile == "narrative":
        style_directives.extend(
            [
                "Prefer a light-touch rewrite when the source already has a clear scene and good imagery.",
                "Preserve the sentence movement of the source whenever it already works: event first, motive next, concrete image after.",
                "Preserve the scene objects and emotional logic of the original.",
                "Keep concrete nouns, image-bearing details, and list order intact whenever you can.",
                "If a noun phrase already sounds human in the source, prefer keeping it nearly verbatim over finding a fresher synonym.",
                "If the source already has a strong turn of phrase or pause structure, keep that architecture instead of replacing it with a cleverer paraphrase.",
                "Do not inject internet-comment energy or forced slang.",
                "Do not borrow donor nouns or donor imagery unless the source already clearly points there.",
                "Do not add new judgments, motives, or explanatory afterthoughts that the source does not already imply.",
                "If the source uses plain wording that already works, keep that plainness instead of upgrading it.",
                "If you loosen the syntax, keep it idiomatic; do not introduce half-spoken constructions that a real person would not actually say.",
                "Let punctuation breathe a little, but do not rewrite everything into polished literary prose.",
                "Stay close to the original image system: do not invent new metaphors just to sound deep.",
                "Avoid semicolons and tidy hinge punctuation unless the source already uses them.",
            ]
        )

    if mode_profile == "seriously":
        style_directives.extend(
            [
                "Keep the language clear, grounded, and calm.",
                "Avoid brochure tone, executive filler, and motivational cadence.",
                "Do not overcorrect the text into schoolbook perfection if a looser line feels more human.",
            ]
        )

    if mode_profile == "casual" or "casual_us_human" in preferred_buckets:
        style_directives.extend(
            [
                "Sound like a current American note or reply, not brand copy.",
                "Use contractions naturally when they fit.",
                "Short, direct lines beat polished summary cadence.",
                "Avoid startup deck language, canned self-awareness, and tidy three-part phrasing.",
                "A little roughness is fine if it makes the voice feel lived-in.",
                "If the source is already complaining that something sounds fake or generic, do not just paraphrase that complaint literally; toss it off the way a real person would.",
                "One sharper sentence and one shorter follow-up usually beat a full tidy paraphrase.",
                "Prefer lived-in complaints like 'sounds canned', 'too tidy', 'off-the-shelf', or 'not how anyone would say it' over cleaned-up meta phrasing.",
            ]
        )

    if "british_professional_human" in preferred_buckets:
        style_directives.extend(
            [
                "Keep the tone understated, matter-of-fact, and lightly British rather than polished-consultancy.",
                "Avoid phrases that sound like agency copy, deck language, or a tidy value proposition.",
                "Prefer plainspoken wording and a little modesty over crisp leadership-post polish.",
                "If a sentence can be simpler and less performative without losing meaning, choose that version.",
                "Avoid formulas like 'what they stand for', 'work that lands', or neat little strategic wrap-ups.",
                "Do not over-compress into vague shorthand like 'what counts', 'what they're about', or 'the practical side'.",
                "Prefer first-person, plain openings like 'I work across...' or 'Most of my work...' over grand role labels if the sentence allows it.",
                "Avoid turning the second sentence into a mini value proposition; it should read like a person describing the work, not summing up a pitch.",
            ]
        )

    if formatting_pack:
        style_directives.extend(
            [
                "Treat formatting as part of the writing surface, not decoration.",
                "You may use markdown-like line breaks, quote blocks, or list rhythm if they improve readability and feel native to the surface.",
                "If you use reactions, symbols, or emotive markers, prefer the culture-native ones from the provided formatting pack.",
                "Do not add generic emoji unless they are explicitly native to the formatting pack.",
                "One well-placed marker is better than a cluster of generic internet noise.",
            ]
        )

    if surface_mode == "reply":
        style_directives.extend(
            [
                "This should read like something posted quickly into a thread, comment chain, or reply box.",
                "Prefer tighter line length, sharper opener, and less scene-setting unless the source already needs it.",
            ]
        )
    if surface_mode == "post":
        style_directives.extend(
            [
                "This should feel post-ready: easy to scan, slightly more structured, still native to the internet.",
                "A line break or isolated closer is okay if it improves punch or readability.",
            ]
        )
    if surface_mode == "thread":
        style_directives.extend(
            [
                "Allow more line breaks and structured emphasis than a reply, but keep the tone native and readable.",
                "Formatting should help scanning, not look like a LinkedIn essay.",
            ]
        )
    if surface_mode == "bio":
        style_directives.extend(
            [
                "This should feel profile-ready and concise.",
                "Use formatting for clarity only; do not over-style.",
            ]
        )
    if surface_mode == "caption":
        style_directives.extend(
            [
                "This should feel caption-ready with compact rhythm and a clear visual beat.",
                "One reaction or marker can work if culturally native, but restraint is better than clutter.",
            ]
        )
    if surface_mode == "note":
        style_directives.extend(
            [
                "This should feel note-like: breathable, personal, and lightly structured.",
                "Line breaks can carry emotion or pacing if they feel natural.",
            ]
        )

    return {
        "source_text": source_text,
        "rewrite_goal": query,
        "preferred_bucket": preferred_bucket,
        "preferred_buckets": preferred_buckets,
        "mode_profile": mode_profile,
        "surface_mode": surface_mode,
        "formatting_pack": formatting_pack,
        "donor_snippets": [
            {
                "text": row.get("text", ""),
                "voice_bucket": row.get("voice_bucket", ""),
                "donor_score": row.get("donor_score", 0),
                "topic_tags": row.get("topic_tags", []),
                "platform": row.get("platform", ""),
            }
            for row in rows
        ],
        "style_directives": style_directives,
        "style_signals": style_signals or [],
    }


def select_db_rows(conn, query: str, preferred_bucket: str, fallback_bucket: str, top_k: int):
    from corpus_db import query_rows  # type: ignore

    preferred_buckets = [item.strip() for item in preferred_bucket.split(",") if item.strip()]
    if not preferred_buckets:
        preferred_buckets = [fallback_bucket] if fallback_bucket else []

    specialized = [bucket for bucket in preferred_buckets if bucket != "reply_bodies"]
    support = [bucket for bucket in preferred_buckets if bucket == "reply_bodies"]
    ordered_buckets = [*specialized, *support]

    selected: list[dict] = []
    seen_texts: set[str] = set()
    remaining = top_k

    if specialized:
        # Prefer specialization first. reply_bodies should support the mode,
        # not wash it out.
        per_bucket_targets: dict[str, int] = {}
        if len(specialized) == 1:
            per_bucket_targets[specialized[0]] = max(1, top_k - 1)
        else:
            lead = max(1, round(top_k * 0.5))
            per_bucket_targets[specialized[0]] = lead
            leftover = max(0, top_k - lead - (1 if support else 0))
            for bucket in specialized[1:]:
                per_bucket_targets[bucket] = max(1, leftover // max(1, len(specialized) - 1))
        if support:
            per_bucket_targets["reply_bodies"] = 1
    else:
        per_bucket_targets = {bucket: max(1, top_k // max(1, len(ordered_buckets))) for bucket in ordered_buckets}

    for index, bucket in enumerate(ordered_buckets):
        if remaining <= 0:
            break
        bucket_limit = min(remaining, max(1, per_bucket_targets.get(bucket, 1)))
        rows = query_rows(conn, query, bucket=bucket, limit=max(bucket_limit, 2))
        for row in rows:
            text = row.get("text", "")
            if not text or text in seen_texts:
                continue
            selected.append(row)
            seen_texts.add(text)
            remaining -= 1
            if remaining <= 0:
                break

    if selected or not fallback_bucket:
        return selected

    rows = query_rows(conn, query, bucket=fallback_bucket, limit=top_k)
    for row in rows:
        text = row.get("text", "")
        if not text or text in seen_texts:
            continue
        selected.append(row)
        if len(selected) >= top_k:
            break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--mode", default="")
    parser.add_argument("--source-text", required=True)
    parser.add_argument("--query", default="")
    parser.add_argument("--surface-mode", default="")
    parser.add_argument("--preferred-bucket", default="")
    parser.add_argument("--fallback-bucket", default="reply_bodies")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    query, preferred_bucket, resolved_db, mode_profile = resolve_mode(args.mode, args.query, args.preferred_bucket, args.db)
    if not args.pack and not resolved_db:
        raise SystemExit("use --pack or --db or provide a mode with db")
    if not query:
        raise SystemExit("query is required or must come from mode")

    style_signals = []
    if resolved_db:
        ROOT = Path(__file__).resolve().parent.parent
        try:
            from storage.corpus_db import connect  # type: ignore
            from storage.style_radar_db import connect as connect_style, query_signals  # type: ignore
        except ImportError:  # pragma: no cover - script-mode fallback
            sys.path.insert(0, str(ROOT / "storage"))
            from corpus_db import connect  # type: ignore
            from style_radar_db import connect as connect_style, query_signals  # type: ignore

        conn = connect(resolved_db)
        primary_bucket = preferred_bucket.split(",")[0] if preferred_bucket else ""
        selected = select_db_rows(conn, query, preferred_bucket, args.fallback_bucket, args.top_k)
        style_conn = connect_style(resolved_db.parent / "style_radar.db")
        lang = selected[0].get("lang_hint", "") if selected else ""
        style_signals = query_signals(style_conn, language_tag=lang, intended_bucket=primary_bucket, limit=4)
    else:
        rows = load_rows(args.pack)
        selected = select_rows(
            rows=rows,
            query=query,
            preferred_bucket=preferred_bucket,
            fallback_bucket=args.fallback_bucket,
            top_k=args.top_k,
        )
    payload = build_payload(args.source_text, query, selected, preferred_bucket, style_signals=style_signals, mode_profile=mode_profile, surface_mode=args.surface_mode)

    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
