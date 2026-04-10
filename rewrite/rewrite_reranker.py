#!/usr/bin/env python3
"""Heuristic reranker for Brotherizer rewrite candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scoring"))
from composition_grounding import composition_penalty  # noqa: E402
from runtime.paths import writable_path  # noqa: E402

TMP_ROOT = Path(os.environ.get("BROTHERIZER_TMPDIR", writable_path(".omx", "state", "tmp")))

TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9']+")
GENERIC_PATTERNS = (
    re.compile(r"\btoo polished\b", re.IGNORECASE),
    re.compile(r"\bgeneric\b", re.IGNORECASE),
    re.compile(r"\bin conclusion\b", re.IGNORECASE),
    re.compile(r"\boverall\b", re.IGNORECASE),
)
BRITISH_HINTS = ("bit", "miffed", "bog-standard", "chippy", "mate", "reckon", "sorry, but")
IRONY_HINTS = ("lol", "dead", "yeah right", "muh", "clearly", "properly")
CASUAL_US_BROCHURE_HINTS = (
    "the whole stack",
    "moves the needle",
    "actually ships",
    "work across",
    "drive growth",
    "turn strategy into",
    "digital brands",
    "communication strategy",
    "positioning sharper",
    "better signal",
    "on paper",
    "dying in the deck",
)
CASUAL_US_HUMAN_HINTS = ("yeah", "honestly", "kind of", "kinda", "a little", "straight up", "pretty much", "feels like", "sounds like")
CASUAL_US_FRESH_HINTS = (
    "canned",
    "lived-in",
    "rough edges",
    "too tidy",
    "smoothed out",
    "app copy",
    "nobody actually says",
    "polished within an inch of its life",
    "real talk",
    "off-the-shelf",
)
CASUAL_US_REPLY_HINTS = (
    "yeah",
    "still",
    "doesn't sound like",
    "doesnt sound like",
    "actually say that",
    "actual people talk",
    "too clean",
)
CASUAL_US_STALE_ECHO_PATTERNS = (
    re.compile(r"\breal person would actually say\b", re.IGNORECASE),
    re.compile(r"\bactual people talk\b", re.IGNORECASE),
    re.compile(r"\bsomething a real person would actually say\b", re.IGNORECASE),
    re.compile(r"\bhow anyone would say it\b", re.IGNORECASE),
    re.compile(r"\bwords a real person would say out loud\b", re.IGNORECASE),
    re.compile(r"\bnot how anyone would say it\b", re.IGNORECASE),
)
CASUAL_US_MEME_HINTS = ("tf", "irl", "ai slop", "slop", "lmao", "lol", "bro", "muh", "who talks like that")
NARRATIVE_AWKWARD_PATTERNS = (
    re.compile(r"\bev(?:ita|itou) a gente de\b", re.IGNORECASE),
    re.compile(r"\bpoupa a gente de\b", re.IGNORECASE),
)
BRITISH_PRO_UNDERSTATED_HINTS = ("mostly", "usually", "a fair bit", "real life", "holds up", "practical", "sensible", "without making a song and dance", "sort out", "getting at", "a bit more clearly", "once it's in play", "day-to-day", "say what they mean", "on about more plainly", "say plainly")
BRITISH_PRO_CLICHE_PATTERNS = (
    re.compile(r"\bexperienced strategist\b", re.IGNORECASE),
    re.compile(r"\bover the years i'?ve helped startups and established companies\b", re.IGNORECASE),
    re.compile(r"\btighten their communication\b", re.IGNORECASE),
    re.compile(r"\bwork that actually sticks\b", re.IGNORECASE),
    re.compile(r"\bget clear on (?:their|your|our) purpose\b", re.IGNORECASE),
    re.compile(r"\bmake sure the strategy turns into\b", re.IGNORECASE),
    re.compile(r"\bworks in practice\b", re.IGNORECASE),
    re.compile(r"\bclarif(?:y|ies|ying) what (?:they|you|we) stand for\b", re.IGNORECASE),
    re.compile(r"\bwhat (?:they|you|we) stand for\b", re.IGNORECASE),
    re.compile(r"\bclarif(?:y|ies|ying) (?:their|your|our) stance\b", re.IGNORECASE),
    re.compile(r"\bturn (?:strategy|that) into work that actually (?:lands|connects)\b", re.IGNORECASE),
    re.compile(r"\blands properly\b", re.IGNORECASE),
    re.compile(r"\bover the past several years\b", re.IGNORECASE),
    re.compile(r"\bsharpen (?:their|your|our) positioning\b", re.IGNORECASE),
    re.compile(r"\bdigital brands\b", re.IGNORECASE),
    re.compile(r"\bgrowth strategies\b", re.IGNORECASE),
    re.compile(r"\bwhat counts\b", re.IGNORECASE),
    re.compile(r"\bstuff that holds up\b", re.IGNORECASE),
    re.compile(r"\bthe practical side\b", re.IGNORECASE),
    re.compile(r"\bwhat they'?re about\b", re.IGNORECASE),
    re.compile(r"\bwhat they'?re on about\b", re.IGNORECASE),
    re.compile(r"\bthink clearly about what they'?re doing\b", re.IGNORECASE),
    re.compile(r"\bsurvives contact with the real world\b", re.IGNORECASE),
    re.compile(r"\bbrand positioning, messaging and growth areas\b", re.IGNORECASE),
    re.compile(r"\bturn it into something that holds up\b", re.IGNORECASE),
)
PTBR_NARRATIVE_ANCHOR_PHRASES = (
    "ele decidiu",
    "sem avisar",
    "não por",
    "falta de coragem",
    "às vezes",
    "em silêncio",
    "evita se perder",
    "na mochila",
    "na mochila, levava",
    "levava um caderno",
    "foto antiga",
    "explicando demais",
    "pergunta que nunca",
    "nunca se",
    "nunca se resolveu",
)
PTBR_NARRATIVE_EXACT_IMAGE_PAIRS = (
    ("sem avisar", "sem dizer nada", 0.2),
    ("foto antiga", "foto velha", 0.22),
    ("na mochila, levava", "na mochila, carregava", 0.14),
    ("partir em silêncio", "sumir quieto", 0.22),
    ("falta de coragem", "covardia", 0.26),
    ("nunca se resolveu", "nunca fechou", 0.28),
    ("nunca se resolveu", "sem solução", 0.24),
    ("nunca se resolveu", "sem resposta", 0.16),
)
PTBR_NARRATIVE_DRIFT_TERMS = (
    "covardia",
    "não por medo",
    "alarde",
    "armadilha",
    "moral",
    "destino",
    "drama",
    "truque",
    "peso real",
    "sem solução",
    "tantas palavras",
    "sem avisar ninguém",
    "sem dizer nada",
    "sumir quieto",
    "poupa a gente",
    "evita a gente de",
    "carregava um caderno",
    "aquela coisa de",
    "aí explicando tudo",
)

CONTENT_STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "até",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dela",
    "dele",
    "deles",
    "demais",
    "do",
    "dos",
    "e",
    "ela",
    "ele",
    "eles",
    "em",
    "era",
    "essa",
    "esse",
    "esta",
    "este",
    "eu",
    "foi",
    "há",
    "isso",
    "mais",
    "mas",
    "me",
    "mesmo",
    "na",
    "nas",
    "nem",
    "ninguém",
    "no",
    "nos",
    "nunca",
    "o",
    "os",
    "ou",
    "para",
    "por",
    "pra",
    "que",
    "se",
    "sem",
    "ser",
    "só",
    "sua",
    "suas",
    "te",
    "tem",
    "tinha",
    "um",
    "uma",
    "umas",
    "uns",
    "vezes",
}

NARRATIVE_SKIP_TOKENS = {
    "decidiu",
    "embora",
    "indo",
    "levava",
    "partir",
    "resolveu",
    "sair",
    "sumir",
}


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in TOKEN_RE.findall(text)]


def lexical_overlap(a: str, b: str) -> float:
    a_set = set(tokenize(a))
    b_set = set(tokenize(b))
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / max(1, len(a_set))


def content_tokens(text: str) -> set[str]:
    return {
        tok
        for tok in tokenize(text)
        if len(tok) >= 4 and tok not in CONTENT_STOPWORDS
    }


def extract_narrative_anchor_tokens(source_text: str) -> list[str]:
    anchors: list[str] = []
    seen: set[str] = set()
    for tok in tokenize(source_text):
        if len(tok) < 4 or tok in CONTENT_STOPWORDS or tok in NARRATIVE_SKIP_TOKENS:
            continue
        if tok in seen:
            continue
        anchors.append(tok)
        seen.add(tok)
    return anchors


def extract_inventory_tokens(source_text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[.!?]", source_text) if "," in part and " e " in part]
    seen: set[str] = set()
    ordered: list[str] = []
    for part in parts:
        for tok in tokenize(part):
            if len(tok) < 4 or tok in CONTENT_STOPWORDS or tok in NARRATIVE_SKIP_TOKENS:
                continue
            if tok in seen:
                continue
            ordered.append(tok)
            seen.add(tok)
    return ordered


def narrative_phrase_architecture_adjustment(source_text: str, text: str) -> float:
    source_lower = source_text.lower()
    candidate_lower = text.lower()
    adjustment = 0.0

    for phrase in PTBR_NARRATIVE_ANCHOR_PHRASES:
        if phrase in source_lower and phrase in candidate_lower:
            adjustment += 0.12

    if "não por" in source_lower and "não por" not in candidate_lower:
        adjustment -= 0.18
    if "sem avisar" in source_lower and "sem avisar" not in candidate_lower:
        adjustment -= 0.14
    if "falta de coragem" in source_lower and "falta de coragem" not in candidate_lower:
        adjustment -= 0.24
    if "em silêncio" in source_lower and not any(term in candidate_lower for term in ("em silêncio", "silêncio", "calado", "quieto")):
        adjustment -= 0.14
    if "evita se perder" in source_lower and "evita se perder" in candidate_lower:
        adjustment += 0.18
    if "na mochila, levava" in source_lower and "na mochila, levava" not in candidate_lower:
        adjustment -= 0.14
    if "na mochila, levava" in source_lower and "na mochila:" in candidate_lower:
        adjustment -= 0.22
    if "levava um caderno" in source_lower and "levava um caderno" in candidate_lower:
        adjustment += 0.14
    if "foto antiga" in source_lower and "foto antiga" in candidate_lower:
        adjustment += 0.14
    if "nunca se resolveu" in source_lower and "nunca se resolveu" in candidate_lower:
        adjustment += 0.18

    for source_phrase, drift_phrase, penalty in PTBR_NARRATIVE_EXACT_IMAGE_PAIRS:
        if source_phrase in source_lower and drift_phrase in candidate_lower:
            adjustment -= penalty

    drift_hits = sum(1 for term in PTBR_NARRATIVE_DRIFT_TERMS if term in candidate_lower and term not in source_lower)
    adjustment -= min(0.66, drift_hits * 0.22)
    return round(adjustment, 4)


def narrative_fidelity_adjustment(source_text: str, donor_snippets: list[dict], text: str) -> float:
    adjustment = 0.0
    candidate_tokens = set(tokenize(text))
    anchor_tokens = extract_narrative_anchor_tokens(source_text)
    if anchor_tokens:
        preserved = sum(1 for tok in anchor_tokens if tok in candidate_tokens)
        missing = len(anchor_tokens) - preserved
        adjustment += preserved * 0.12
        adjustment -= missing * 0.1

    inventory_tokens = extract_inventory_tokens(source_text)
    if inventory_tokens:
        preserved_inventory = [tok for tok in inventory_tokens if tok in candidate_tokens]
        adjustment += len(preserved_inventory) * 0.08
        if len(preserved_inventory) >= 2 and preserved_inventory == inventory_tokens[: len(preserved_inventory)]:
            adjustment += 0.12
        if len(preserved_inventory) == len(inventory_tokens):
            adjustment += 0.14

    donor_content = set()
    for donor in donor_snippets:
        donor_content |= content_tokens(donor.get("text", ""))
    source_content = content_tokens(source_text)
    candidate_content = content_tokens(text)
    novel_tokens = candidate_content - source_content - donor_content
    if len(novel_tokens) > 2:
        adjustment -= (len(novel_tokens) - 2) * 0.18

    donor_drift_tokens = (candidate_content & donor_content) - source_content
    if len(donor_drift_tokens) > 1:
        adjustment -= min(0.36, (len(donor_drift_tokens) - 1) * 0.12)

    source_sentences = len([part for part in re.split(r"[.!?]+", source_text) if part.strip()])
    candidate_sentences = len([part for part in re.split(r"[.!?]+", text) if part.strip()])
    if candidate_sentences > source_sentences + 1:
        adjustment -= 0.15
    if candidate_sentences < max(1, source_sentences - 1):
        adjustment -= 0.1

    source_parts = [part.strip().lower() for part in re.split(r"[.!?]+", source_text) if part.strip()]
    candidate_parts = [part.strip().lower() for part in re.split(r"[.!?]+", text) if part.strip()]
    if source_parts and candidate_parts:
        adjustment += lexical_overlap(source_parts[0], candidate_parts[0]) * 0.25
        source_second = source_parts[min(1, len(source_parts) - 1)]
        candidate_second = candidate_parts[min(1, len(candidate_parts) - 1)]
        adjustment += lexical_overlap(source_second, candidate_second) * 0.18

    if "—" in text or " - " in text:
        adjustment -= 0.12
    if ";" in text:
        adjustment -= 0.3
    if ":" in text and ":" not in source_text:
        adjustment -= 0.1

    adjustment += narrative_phrase_architecture_adjustment(source_text, text)

    return round(adjustment, 4)


def score_candidate(
    source_text: str,
    preferred_bucket: str,
    donor_snippets: list[dict],
    candidate: dict,
    mode_profile: str = "default",
    surface_mode: str = "",
) -> float:
    text = candidate.get("text", "")
    lowered = text.lower()
    source_lowered = source_text.lower()
    score = 0.0
    preferred_buckets = [item.strip() for item in preferred_bucket.split(",") if item.strip()]

    # Meaning preservation through lexical anchoring to source.
    source_overlap = lexical_overlap(source_text, text)
    score += source_overlap * 2.5

    # Donor alignment.
    donor_bonus = 0.0
    for donor in donor_snippets:
        donor_bonus = max(donor_bonus, lexical_overlap(donor.get("text", ""), text))
    score += donor_bonus * 1.5

    # Bucket-specific flavor.
    if "british_banter" in preferred_buckets and any(h in lowered for h in BRITISH_HINTS):
        score += 1.5
    if "worldwide_ironic" in preferred_buckets and any(h in lowered for h in IRONY_HINTS):
        score += 1.5
    if "reply_bodies" in preferred_buckets and any(tok in lowered for tok in ("i", "my", "me", "we", "you")):
        score += 1.0
    if "casual_us_human" in preferred_buckets:
        if any(h in lowered for h in CASUAL_US_HUMAN_HINTS):
            score += 0.35
        if any(h in lowered for h in CASUAL_US_FRESH_HINTS):
            score += 0.45
        if lowered.startswith("yeah,") or lowered.startswith("honestly"):
            score += 0.18
        if "anybody'd" in lowered or "would've" in lowered or "person would've" in lowered:
            score += 0.14
        if len(source_text) <= 120 and len(text) <= 110:
            score += 0.3
        if len(source_text) <= 120 and text.count(".") <= 2:
            score += 0.2
        if len(source_text) <= 110:
            if len(text) <= 95:
                score += 0.25
            if text.count(".") <= 2 and "?" not in text and "!" not in text:
                score += 0.2
            if any(h in lowered for h in CASUAL_US_REPLY_HINTS):
                score += 0.25
        for hint in CASUAL_US_BROCHURE_HINTS:
            if hint in lowered and hint not in source_lowered:
                score -= 0.35
        for pattern in CASUAL_US_STALE_ECHO_PATTERNS:
            if pattern.search(text):
                score -= 0.45
        if any(h in lowered for h in CASUAL_US_MEME_HINTS):
            score -= 0.65
    if "british_professional_human" in preferred_buckets:
        if any(hint in lowered for hint in BRITISH_PRO_UNDERSTATED_HINTS):
            score += 0.35
        if lowered.startswith("i work across") or lowered.startswith("most of my work") or lowered.startswith("a fair bit"):
            score += 0.25
        score += source_overlap * 0.45
        for pattern in BRITISH_PRO_CLICHE_PATTERNS:
            if pattern.search(text):
                score -= 0.8

    # Reward asymmetry and punch.
    if 25 <= len(text) <= 140:
        score += 1.0
    if "?" in text or "!" in text:
        score += 0.5

    # Penalize genericness.
    for pattern in GENERIC_PATTERNS:
        if pattern.search(text):
            score -= 1.5

    if source_overlap < 0.08:
        score -= 1.0

    if mode_profile == "narrative":
        score += source_overlap * 0.9
        score += narrative_fidelity_adjustment(source_text, donor_snippets, text)

    if surface_mode == "reply":
        if len(text) <= 140:
            score += 0.2
        if text.count("\n") <= 1:
            score += 0.1
        if text.count(".") <= 2:
            score += 0.1
    if surface_mode == "post":
        if "\n" in text:
            score += 0.12
        if len(text) >= 60:
            score += 0.08
    if surface_mode == "thread":
        if text.count("\n") >= 1:
            score += 0.18
        if any(marker in text for marker in ("- ", "> ", "**")):
            score += 0.12
    if surface_mode == "bio":
        if "\n" not in text:
            score += 0.15
        if text.count(".") <= 2:
            score += 0.12
    if surface_mode == "caption":
        if len(text) <= 180:
            score += 0.14
        if text.count("\n") <= 2:
            score += 0.08
    if surface_mode == "note":
        if text.count("\n") >= 1:
            score += 0.1

    return round(score, 4)


def apply_mode_profile_penalty(mode_profile: str, text: str, surface_mode: str = "") -> float:
    lowered = text.lower()
    penalty = 0.0
    if mode_profile == "seriously":
        if any(term in lowered for term in ("bollocks", "fucking", "pra caralho", "goon", "muh politics")):
            penalty -= 1.0
        if lowered.count("!") >= 2:
            penalty -= 0.5
        if any(term in lowered for term in ("kkk", "kkkk", "mano", "véi", "vei", "pô", "po", "irl", "frfr")):
            penalty -= 0.35
    if mode_profile == "narrative":
        if any(term in lowered for term in ("mano", "véi", "vei", "pô", "po", "kkk", "kkkk", "irl", "frfr")):
            penalty -= 0.45
        if any(pattern.search(text) for pattern in NARRATIVE_AWKWARD_PATTERNS):
            penalty -= 0.45
    if mode_profile == "casual":
        if any(term in lowered for term in ("muh", "goon", "bollocks", "innit")):
            penalty -= 0.4
        if lowered.count("!") >= 2:
            penalty -= 0.35
    if mode_profile == "british_professional":
        if any(
            term in lowered
            for term in (
                "what they stand for",
                "actually lands",
                "actually connects",
                "actually works",
                "turn strategy into",
                "clarify their stance",
                "experienced strategist",
                "their purpose",
                "what matters",
                "works in practice",
                "turn into something",
                "get clear on",
                "on about",
                "holds up",
            )
        ):
            penalty -= 0.85
        if lowered.count(" and ") >= 2 and "," in lowered:
            penalty -= 0.2
        if "!" in lowered:
            penalty -= 0.35
    if surface_mode == "bio":
        if "\n" in text:
            penalty -= 0.22
        if any(token in lowered for token in ("lol", "kkk", "lmao", "😭", "💀")):
            penalty -= 0.45
    if surface_mode == "reply":
        if len(text) > 220:
            penalty -= 0.25
    if surface_mode == "caption":
        if len(text) > 260:
            penalty -= 0.2
    if surface_mode == "thread":
        if len(text) < 50:
            penalty -= 0.12
    return penalty


DEFAULT_XAI_MODEL = os.environ.get("BROTHERIZER_XAI_MODEL", "grok-4.20-reasoning")


def make_tempdir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TMP_ROOT)


def run_xai_judge_scores(
    *,
    source_text: str,
    preferred_bucket: str,
    donor_snippets: list[dict],
    candidates: list[dict],
    xai_model: str = DEFAULT_XAI_MODEL,
) -> dict[str, float]:
    if not os.environ.get("XAI_API_KEY"):
        return {}
    judge_payload = {
        "source_text": source_text,
        "preferred_bucket": preferred_bucket,
        "donor_snippets": donor_snippets,
        "candidates": candidates,
    }
    try:
        with make_tempdir() as tmpdir:
            judge_in = Path(tmpdir) / "judge-input.json"
            judge_out = Path(tmpdir) / "judge-output.json"
            judge_in.write_text(json.dumps(judge_payload, ensure_ascii=False, indent=2) + "\n")
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "rewrite" / "xai_judge.py"),
                    "--input",
                    str(judge_in),
                    "--model",
                    xai_model,
                    "--out",
                    str(judge_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=dict(os.environ),
            )
            parsed = json.loads(judge_out.read_text())
        return {
            item.get("label", ""): float(item.get("overall", 0))
            for item in parsed.get("scores", [])
        }
    except Exception:
        return {}


def heuristic_rerank(data: dict) -> list[dict]:
    source_text = data.get("source_text", "")
    preferred_bucket = data.get("preferred_bucket", "")
    mode_profile = data.get("mode_profile", "default")
    surface_mode = data.get("surface_mode", "")
    donor_snippets = data.get("donor_snippets", [])
    candidates = data.get("candidates", [])
    scored = []
    for candidate in candidates:
        score = score_candidate(
            source_text,
            preferred_bucket,
            donor_snippets,
            candidate,
            mode_profile=mode_profile,
            surface_mode=surface_mode,
        )
        score += apply_mode_profile_penalty(mode_profile, candidate.get("text", ""), surface_mode=surface_mode)
        composition_score_penalty, composition_matches = composition_penalty(
            candidate.get("text", ""),
            mode_profile=mode_profile,
        )
        score -= composition_score_penalty
        enriched = dict(candidate)
        enriched["composition_penalty"] = composition_score_penalty
        enriched["composition_matches"] = composition_matches
        enriched["rerank_score"] = score
        scored.append(enriched)
    scored.sort(key=lambda item: (-item["rerank_score"], len(item.get("text", ""))))
    return scored


def merge_xai_scores(scored: list[dict], xai_scores: dict[str, float]) -> list[dict]:
    merged = []
    for candidate in scored:
        item = dict(candidate)
        label = item.get("label", "")
        if label in xai_scores:
            item["xai_judge_score"] = xai_scores[label]
            item["rerank_score"] = float(item.get("rerank_score", 0)) + xai_scores[label] / 10
        merged.append(item)
    merged.sort(key=lambda entry: (-entry["rerank_score"], len(entry.get("text", ""))))
    return merged


def rerank_payload(data: dict, *, use_xai_judge: bool = False, xai_model: str = DEFAULT_XAI_MODEL) -> dict:
    scored = heuristic_rerank(data)
    if use_xai_judge and os.environ.get("XAI_API_KEY"):
        xai_scores = run_xai_judge_scores(
            source_text=data.get("source_text", ""),
            preferred_bucket=data.get("preferred_bucket", ""),
            donor_snippets=data.get("donor_snippets", []),
            candidates=data.get("candidates", []),
            xai_model=xai_model,
        )
        scored = merge_xai_scores(scored, xai_scores)
    result = dict(data)
    result["candidates"] = scored
    result["winner"] = scored[0] if scored else None
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--use-xai-judge", action="store_true")
    parser.add_argument("--xai-model", default=DEFAULT_XAI_MODEL)
    args = parser.parse_args()

    data = json.loads(args.input.read_text())
    result = rerank_payload(data, use_xai_judge=args.use_xai_judge, xai_model=args.xai_model)

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
