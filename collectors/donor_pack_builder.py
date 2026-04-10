#!/usr/bin/env python3
"""Merge collected snippets and build a cleaner donor pack for Brotherizer."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scoring.source_quality_scorer import score_source_quality

SPACE_RE = re.compile(r"\s+")

BAD_TEXT_PATTERNS = (
    re.compile(r"\bprivacy policy\b", re.IGNORECASE),
    re.compile(r"\buser agreement\b", re.IGNORECASE),
    re.compile(r"\ball rights reserved\b", re.IGNORECASE),
    re.compile(r"\brendered by pid\b", re.IGNORECASE),
    re.compile(r"\bregistered trademarks?\b", re.IGNORECASE),
    re.compile(r"\bsubmitted\s+\d+", re.IGNORECASE),
    re.compile(r"\bposted\s+\d+", re.IGNORECASE),
)

GOOD_STYLE_HINTS = (
    "lol",
    "lmao",
    "nah",
    "yeah",
    "mate",
    "banter",
    "reckon",
    "tbf",
    "ngl",
    "bro",
    "innit",
    "honestly",
    "i think",
    "does anyone",
    "mano",
    "tipo",
    "pô",
    "po",
    "cara",
    "slk",
    "sei lá",
    "pra",
    "tá",
)

BRITISH_HINTS = (
    "british",
    "chippy",
    "tesco",
    "wembley",
    "mate",
    "banter",
    "reckon",
    "fair play",
    "innit",
)

IRONY_HINTS = (
    "muh politics",
    "lol",
    "lmao",
    "why won't women sleep with me",
    "fools",
    "clearly he is a true",
    "collectivise gaming",
    "goon material",
)

EN_REFLECTIVE_HINTS = (
    "quietly",
    "in silence",
    "old photo",
    "old photograph",
    "on the road",
    "lighter",
    "staying",
    "without saying anything",
    "never had an answer",
)

EN_PROFESSIONAL_HINTS = (
    "branding",
    "positioning",
    "go-to-market",
    "growth",
    "communications strategy",
    "digital brands",
    "ecommerce",
    "stakeholders",
)

BRITISH_PRO_HINTS = (
    "whilst",
    "properly",
    "practical eye",
    "brand strategy",
    "positioning",
    "messaging",
    "clear enough",
    "digital products",
)

CASUAL_US_HINTS = (
    "kind of",
    "pretty much",
    "straight-up",
    "worked on",
    "put together",
    "real person",
    "got things done",
    "honestly",
)

REPLY_BODY_HINTS = (
    "i think",
    "i believe",
    "assuming",
    "doesn't work",
    "i was",
    "years ago",
    "as a ",
    "thank you",
    "eu",
    "acho",
    "pra mim",
    "na moral",
)

PTBR_HINTS = (
    "mano",
    "cara",
    "pô",
    "po",
    "tipo",
    "slk",
    "sei lá",
    "na moral",
    "tá",
    "pra",
)

PTBR_IRONY_HINTS = (
    "kkkk",
    "kkk",
    "vsf",
    "pqp",
    "intankavel",
    "meu deus",
    "ah pronto",
)

PTBR_REFLECTIVE_HINTS = (
    "talvez",
    "silêncio",
    "na estrada",
    "na mochila",
    "sem dizer nada",
    "mais leve",
    "ficar",
    "pergunta sem resposta",
)

PTBR_PROFESSIONAL_HINTS = (
    "branding",
    "posicionamento",
    "performance",
    "narrativas para marcas",
    "estratégias de comunicação",
    "crescimento sustentável",
    "conexão com o público",
    "e-commerces",
)

EN_REFLECTIVE_HINTS = (
    "sometimes leaving quietly",
    "old photograph",
    "the road",
    "without saying anything",
    "maybe the weight",
    "the farther away",
    "staying",
)

EN_PROFESSIONAL_HINTS = (
    "branding",
    "positioning",
    "performance",
    "digital brands",
    "data-led",
    "sustainable growth",
    "market differentiation",
    "audience",
)


def normalize_text(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip()


def score_row(row: dict[str, Any]) -> int:
    text = normalize_text(row.get("text", ""))
    lowered = text.lower()
    score = 0
    content_role = row.get("content_role", "")

    if 45 <= len(text) <= 260:
        score += 2
    if row.get("audience_mode") == "reply-like":
        score += 2
    if any(hint in lowered for hint in GOOD_STYLE_HINTS):
        score += 2
    if "?" in text or "!" in text:
        score += 1
    if any(tag in row.get("topic_tags", []) for tag in ("british-english", "internet-native", "irony", "banter", "ptbr")):
        score += 2
    if row.get("platform") in {"reddit-web", "hackernews"}:
        score += 1
    if sum(ch.isalpha() for ch in text) > 40:
        score += 1
    if any(hint in lowered for hint in REPLY_BODY_HINTS):
        score += 2
    if row.get("platform") == "hackernews":
        score += 2
    if any(hint in lowered for hint in PTBR_HINTS):
        score += 1
    if content_role in {"comment_body", "reply_body"}:
        score += 3
    elif content_role == "comment_thread":
        score += 1
    elif content_role in {"community_meta", "listing_or_thread_surface"}:
        score -= 2

    for pattern in BAD_TEXT_PATTERNS:
        if pattern.search(text):
            score -= 5

    return score


def classify_bucket(row: dict[str, Any]) -> str:
    text = normalize_text(row.get("text", ""))
    lowered = text.lower()
    tags = set(row.get("topic_tags", []))
    content_role = row.get("content_role", "")

    if content_role in {"comment_body", "reply_body"}:
        return "reply_bodies"
    if any(hint in lowered for hint in EN_PROFESSIONAL_HINTS):
        return "en_professional_human"
    if any(hint in lowered for hint in EN_REFLECTIVE_HINTS):
        return "en_reflective"
    if any(hint in lowered for hint in REPLY_BODY_HINTS) and row.get("platform") == "hackernews":
        return "reply_bodies"
    if "ptbr" in tags and any(hint in lowered for hint in PTBR_PROFESSIONAL_HINTS):
        return "ptbr_professional_human"
    if "ptbr" in tags and any(hint in lowered for hint in PTBR_REFLECTIVE_HINTS):
        return "ptbr_reflective"
    if "ptbr" in tags and any(hint in lowered for hint in PTBR_IRONY_HINTS):
        return "ptbr_ironic"
    if "ptbr" in tags and any(hint in lowered for hint in PTBR_HINTS):
        return "ptbr_casual"
    if "ptbr" in tags:
        return "ptbr_discussion"
    if "british-english" in tags and any(hint in lowered for hint in BRITISH_HINTS):
        return "british_banter"
    if "british-english" in tags and any(hint in lowered for hint in BRITISH_PRO_HINTS):
        return "british_professional_human"
    if "british-english" in tags:
        return "british_casual"
    if any(hint in lowered for hint in EN_PROFESSIONAL_HINTS):
        return "en_professional_human"
    if any(hint in lowered for hint in EN_REFLECTIVE_HINTS):
        return "en_reflective"
    if any(hint in lowered for hint in CASUAL_US_HINTS):
        return "casual_us_human"
    if any(hint in lowered for hint in IRONY_HINTS) or "irony" in tags:
        return "worldwide_ironic"
    return "worldwide_discussion"


def iter_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                text = normalize_text(row.get("text", ""))
                if not text:
                    continue
                if text in seen:
                    continue
                seen.add(text)
                row["text"] = text
                rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--min-score", type=int, default=4)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--buckets", default="")
    parser.add_argument("--lang", default="")
    args = parser.parse_args()

    rows = iter_rows(args.inputs)
    bucket_filter = {item.strip() for item in args.buckets.split(",") if item.strip()}
    scored: list[dict[str, Any]] = []
    for row in rows:
        score = score_row(row)
        quality = score_source_quality(row["text"])
        score += quality
        row["donor_score"] = score
        row["source_quality_score"] = quality
        row["voice_bucket"] = classify_bucket(row)
        if bucket_filter and row["voice_bucket"] not in bucket_filter:
            continue
        if args.lang and row.get("lang_hint") != args.lang:
            continue
        if score < args.min_score:
            continue
        scored.append(row)

    scored.sort(key=lambda item: (-item["donor_score"], len(item["text"])))
    selected = scored[: args.limit]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "ok": True,
                "input_rows": len(rows),
                "selected_rows": len(selected),
                "out": str(args.out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
