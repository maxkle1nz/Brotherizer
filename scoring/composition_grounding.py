#!/usr/bin/env python3
"""Detect and penalize overused LLM discourse patterns."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9']+")


@dataclass(frozen=True)
class CompositionPattern:
    key: str
    regex: re.Pattern[str]
    penalty: float
    description: str


PATTERNS: tuple[CompositionPattern, ...] = (
    CompositionPattern(
        key="not_x_but_y",
        regex=re.compile(r"\bnot\b.{0,48}\bbut\b", re.IGNORECASE | re.DOTALL),
        penalty=0.85,
        description="Classic contrast mold: 'not X but Y'.",
    ),
    CompositionPattern(
        key="not_just_x_but_y",
        regex=re.compile(r"\bnot just\b.{0,48}\bbut\b", re.IGNORECASE | re.DOTALL),
        penalty=1.0,
        description="Overframed contrast: 'not just X but Y'.",
    ),
    CompositionPattern(
        key="not_about_x_about_y",
        regex=re.compile(r"\bnot (?:about|really|just)\b.{0,48}\b(?:about|it'?s|it is)\b", re.IGNORECASE | re.DOTALL),
        penalty=0.9,
        description="Self-conscious reframing formula.",
    ),
    CompositionPattern(
        key="dash_thesis_splice",
        regex=re.compile(r"(?:\s[—–-]\s|\w[—–-]\w)"),
        penalty=0.35,
        description="Dash splice often overused by LLMs for dramatic thought framing.",
    ),
    CompositionPattern(
        key="clean_triplet",
        regex=re.compile(r"\b[^,]{2,40},\s[^,]{2,40},\sand\s[^,]{2,40}\b", re.IGNORECASE),
        penalty=0.55,
        description="Too-clean rhetorical triplet.",
    ),
    CompositionPattern(
        key="false_depth_maybe",
        regex=re.compile(r"\bmaybe\b.{0,36}\bmaybe\b", re.IGNORECASE | re.DOTALL),
        penalty=0.45,
        description="Repetitive faux-depth uncertainty framing.",
    ),
    CompositionPattern(
        key="overexplicit_conclusion",
        regex=re.compile(r"\b(?:in conclusion|overall|ultimately|at the end of the day)\b", re.IGNORECASE),
        penalty=0.8,
        description="Essay conclusion scaffolding.",
    ),
    CompositionPattern(
        key="thesis_then_reframe",
        regex=re.compile(r"\.\s*(?:it'?s|it is|this is|that is)\s+not\b", re.IGNORECASE),
        penalty=0.7,
        description="Sentence-two reframing habit.",
    ),
    CompositionPattern(
        key="elevated_abstraction",
        regex=re.compile(r"\b(?:the act of|the weight of|the burden of|the idea of|the notion of)\b", re.IGNORECASE),
        penalty=0.55,
        description="Abstract elevation that often makes text sound writerly/LLM-ish.",
    ),
    CompositionPattern(
        key="corporate_speak",
        regex=re.compile(r"\b(?:leverage|drive impact|unlock|maximize|optimize|foster|seamless|best-in-class|world-class|robust|end-to-end|stakeholder alignment)\b", re.IGNORECASE),
        penalty=0.6,
        description="Corporate brochure phrasing.",
    ),
    CompositionPattern(
        key="consultancy_polish",
        regex=re.compile(
            r"\b(?:what (?:they|you|we) stand for|work that actually (?:lands|connects|works)|turn (?:that|it|strategy) into work|clarify (?:their|your|our) stance|experienced strategist)\b",
            re.IGNORECASE,
        ),
        penalty=0.7,
        description="Professional copy that slips into tidy consultancy phrasing.",
    ),
)

HUMAN_RHYTHM_HINTS = (
    re.compile(r"\b(?:kind of|sort of|a bit|a little|i mean|you know|sabe|tipo|meio que|sei lá)\b", re.IGNORECASE),
    re.compile(r"\b(?:though|anyway|still|honestly|frankly|véi|mano|cara|pô|aff)\b", re.IGNORECASE),
    re.compile(r"\b(?:didn'?t|can'?t|won'?t|isn'?t|tá|cê|pra|pro)\b", re.IGNORECASE),
)

OVERCLEAN_PATTERNS = (
    re.compile(r"^[A-ZÀ-Ý][^.?!]+(?:\.\s+[A-ZÀ-Ý][^.?!]+){3,}\.?$", re.DOTALL),
    re.compile(r":\s+[a-zà-ÿ0-9]", re.IGNORECASE),
)

INTERNET_LOOSE_HINTS = (
    re.compile(r"\.\.\."),
    re.compile(r"\?{1,2}"),
    re.compile(r"\b(?:mano|cara|véi|pô|tipo|sei lá)\b", re.IGNORECASE),
)

CASUAL_BROCHURE_PATTERNS = (
    re.compile(r"\b(?:the whole stack|moves the needle|actually ships|turn strategy into|communication strategy|digital brands|better signal|on paper)\b", re.IGNORECASE),
)
CASUAL_PERFORMANCE_PATTERNS = (
    re.compile(r"\b(?:ai slop|irl|tf|lmao|lol|bro|muh)\b", re.IGNORECASE),
    re.compile(r"[!?]{2,}"),
    re.compile(r"\bwho talks like that\b", re.IGNORECASE),
)

NARRATIVE_SLANG_HINTS = (
    re.compile(r"\b(?:mano|pô|po|véi|kkk+|rolê|pirou|frescura|palhaçada)\b", re.IGNORECASE),
)

BRITISH_UNDERSTATEMENT_HINTS = (
    re.compile(r"\b(?:mostly|usually|fairly|quite|a bit|tend to|properly|plainly|straightforward enough)\b", re.IGNORECASE),
)


def punctuation_looseness_adjustment(text: str, mode_profile: str = "default") -> float:
    adjustment = 0.0
    sentence_endings = text.count(".") + text.count("?") + text.count("!")
    comma_count = text.count(",")
    has_ellipsis = "..." in text or "…" in text

    if mode_profile == "default":
        if any(pattern.search(text) for pattern in INTERNET_LOOSE_HINTS):
            adjustment += 0.25
        if sentence_endings >= 4 and comma_count == 0 and not has_ellipsis:
            adjustment -= 0.3

    if mode_profile == "seriously":
        if any(pattern.search(text) for pattern in OVERCLEAN_PATTERNS):
            adjustment -= 0.35
        if text.count("!") >= 2:
            adjustment -= 0.35
        if has_ellipsis:
            adjustment += 0.1

    if mode_profile == "narrative":
        if text.count("!") > 0:
            adjustment -= 0.4
        if any(pattern.search(text) for pattern in OVERCLEAN_PATTERNS):
            adjustment -= 0.45
        if has_ellipsis or comma_count >= 1:
            adjustment += 0.15
        if re.search(r"\n\n", text):
            adjustment += 0.15

    if mode_profile == "casual":
        if any(pattern.search(text) for pattern in OVERCLEAN_PATTERNS):
            adjustment -= 0.4
        if sentence_endings >= 4 and not has_ellipsis:
            adjustment -= 0.25
        if any(hint in text.lower() for hint in ("yeah", "honestly", "kind of", "kinda", "feels like", "sounds like")):
            adjustment += 0.2

    if mode_profile == "british_professional":
        if any(pattern.search(text) for pattern in OVERCLEAN_PATTERNS):
            adjustment -= 0.35
        if text.count("!") > 0:
            adjustment -= 0.45
        if any(pattern.search(text) for pattern in BRITISH_UNDERSTATEMENT_HINTS):
            adjustment += 0.15

    return round(adjustment, 4)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def detect_llm_discourse_patterns(text: str) -> list[dict]:
    matches: list[dict] = []
    for pattern in PATTERNS:
        found = pattern.regex.search(text)
        if not found:
            continue
        excerpt = found.group(0).strip()
        matches.append(
            {
                "key": pattern.key,
                "penalty": pattern.penalty,
                "description": pattern.description,
                "excerpt": excerpt[:120],
            }
        )
    return matches


def human_rhythm_bonus(text: str) -> float:
    bonus = 0.0
    if any(pattern.search(text) for pattern in HUMAN_RHYTHM_HINTS):
        bonus += 0.35
    tokens = tokenize(text)
    if 8 <= len(tokens) <= 28:
        bonus += 0.2
    if "..." in text:
        bonus -= 0.15
    return round(bonus, 4)


def composition_penalty(text: str, mode_profile: str = "default") -> tuple[float, list[dict]]:
    matches = detect_llm_discourse_patterns(text)
    penalty = sum(match["penalty"] for match in matches)
    penalty -= human_rhythm_bonus(text)
    penalty -= punctuation_looseness_adjustment(text, mode_profile)

    if mode_profile == "seriously":
        for match in matches:
            if match["key"] in {
                "not_x_but_y",
                "not_just_x_but_y",
                "dash_thesis_splice",
                "thesis_then_reframe",
            }:
                penalty += 0.25

    if mode_profile == "narrative":
        for match in matches:
            if match["key"] in {
                "not_x_but_y",
                "not_just_x_but_y",
                "thesis_then_reframe",
                "clean_triplet",
                "elevated_abstraction",
                "corporate_speak",
            }:
                penalty += 0.2
        if any(pattern.search(text) for pattern in NARRATIVE_SLANG_HINTS):
            penalty += 0.55

    if mode_profile == "seriously":
        for match in matches:
            if match["key"] == "corporate_speak":
                penalty += 0.35

    if mode_profile == "casual":
        for match in matches:
            if match["key"] in {"corporate_speak", "clean_triplet"}:
                penalty += 0.25
        if any(pattern.search(text) for pattern in CASUAL_BROCHURE_PATTERNS):
            penalty += 0.55
        if any(pattern.search(text) for pattern in CASUAL_PERFORMANCE_PATTERNS):
            penalty += 0.55

    if mode_profile == "british_professional":
        for match in matches:
            if match["key"] in {"clean_triplet", "corporate_speak", "consultancy_polish", "thesis_then_reframe"}:
                penalty += 0.25
        if any(pattern.search(text) for pattern in BRITISH_UNDERSTATEMENT_HINTS):
            penalty -= 0.15

    return round(max(penalty, 0.0), 4), matches


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--mode-profile", default="default")
    args = parser.parse_args()

    penalty, matches = composition_penalty(args.text, args.mode_profile)
    print(
        json.dumps(
            {
                "text": args.text,
                "mode_profile": args.mode_profile,
                "composition_penalty": penalty,
                "matches": matches,
                "human_rhythm_bonus": human_rhythm_bonus(args.text),
                "punctuation_looseness_adjustment": punctuation_looseness_adjustment(args.text, args.mode_profile),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
