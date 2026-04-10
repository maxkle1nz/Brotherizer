#!/usr/bin/env python3
"""Source quality scoring for Brotherizer donor snippets."""

from __future__ import annotations

import re

BAD_PATTERNS = (
    re.compile(r"\bprivacy\b", re.IGNORECASE),
    re.compile(r"\buser agreement\b", re.IGNORECASE),
    re.compile(r"\ball rights reserved\b", re.IGNORECASE),
    re.compile(r"\blogin\b", re.IGNORECASE),
    re.compile(r"\bcreate account\b", re.IGNORECASE),
    re.compile(r"\bmodmail\b", re.IGNORECASE),
    re.compile(r"\bsubmission guidelines\b", re.IGNORECASE),
    re.compile(r"\bsubreddit rules\b", re.IGNORECASE),
    re.compile(r"\bweekly scheduled discussion threads\b", re.IGNORECASE),
)

GOOD_PATTERNS = (
    re.compile(r"\bmate\b", re.IGNORECASE),
    re.compile(r"\binnit\b", re.IGNORECASE),
    re.compile(r"\bmano\b", re.IGNORECASE),
    re.compile(r"\bcara\b", re.IGNORECASE),
    re.compile(r"\bkkk+\b", re.IGNORECASE),
    re.compile(r"\blol\b", re.IGNORECASE),
    re.compile(r"[?!]{1,}"),
    re.compile(r"\bI think\b", re.IGNORECASE),
    re.compile(r"\beu acho\b", re.IGNORECASE),
)


def score_source_quality(text: str) -> float:
    lowered = text.lower()
    score = 0.0

    if 35 <= len(text) <= 260:
        score += 1.5
    if sum(ch.isalpha() for ch in text) > 30:
        score += 1.0
    if any(p.search(text) for p in GOOD_PATTERNS):
        score += 2.0
    if any(ch in text for ch in ("?", "!")):
        score += 0.5

    for pattern in BAD_PATTERNS:
        if pattern.search(text):
            score -= 3.0

    return round(score, 4)
