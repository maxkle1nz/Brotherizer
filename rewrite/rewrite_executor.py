#!/usr/bin/env python3
"""Generate rewrite candidates for Brotherizer using Perplexity Sonar."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "retrieval"))

from rewrite_context_builder import build_payload  # noqa: E402

API_URL = "https://api.perplexity.ai/v1/sonar"


def extract_json_block(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def build_messages(payload: dict[str, Any], candidate_count: int) -> list[dict[str, str]]:
    system = (
        "You are a rewrite engine for Brotherizer. "
        "Your job is to rewrite text so it feels less generic and more human, "
        "while preserving the original meaning. "
        "Use the donor snippets as style references, but never copy them verbatim. "
        "Return strict JSON only."
    )
    donor_lines = []
    for item in payload.get("donor_snippets", []):
        donor_lines.append(
            f"- [{item.get('voice_bucket','')}] {item.get('text','')}"
        )
    style_signal_lines = []
    for item in payload.get("style_signals", []):
        style_signal_lines.append(
            f"- [{item.get('signal_key','')}] title={item.get('title','')} | description={item.get('description','')} | meme_family={item.get('meme_family','')} | caption_style={item.get('caption_style','')} | visual_style={item.get('visual_style','')}"
        )
    user = (
        f"Source text:\n{payload['source_text']}\n\n"
        f"Rewrite goal:\n{payload['rewrite_goal']}\n\n"
        f"Preferred bucket:\n{payload.get('preferred_bucket','')}\n\n"
        f"Preferred buckets list:\n{', '.join(payload.get('preferred_buckets', []))}\n\n"
        f"Mode profile:\n{payload.get('mode_profile','default')}\n\n"
        f"Surface mode:\n{payload.get('surface_mode','') or 'default'}\n\n"
        "Style directives:\n"
        + "\n".join(f"- {line}" for line in payload.get("style_directives", []))
        + (
            "\n\nSurface formatting pack:\n"
            + f"- title: {payload.get('formatting_pack', {}).get('title', 'none')}\n"
            + f"- description: {payload.get('formatting_pack', {}).get('description', 'none')}\n"
            + (
                f"- reactions: {', '.join(payload.get('formatting_pack', {}).get('reactions', []))}\n"
                f"- emoticons: {', '.join(payload.get('formatting_pack', {}).get('emoticons', []))}\n"
                f"- separators: {', '.join(payload.get('formatting_pack', {}).get('separators', []))}\n"
                f"- arrows: {', '.join(payload.get('formatting_pack', {}).get('arrows', []))}\n"
                f"- markdown moves: {', '.join(payload.get('formatting_pack', {}).get('markdown', []))}\n"
                f"- formatting moves: {', '.join(payload.get('formatting_pack', {}).get('formatting_moves', []))}\n"
                + "\n".join(f"- format rule: {line}" for line in payload.get('formatting_pack', {}).get('rules', []))
              if payload.get("formatting_pack")
              else "- none"
            )
          )
        + "\n\nStyle radar signals:\n"
        + ("\n".join(style_signal_lines) if style_signal_lines else "- none")
        + "\n\nDonor snippets:\n"
        + "\n".join(donor_lines)
        + (
            "\n\nSeriously mode rules:\n"
            "- keep the language human, but calmer and more grounded\n"
            "- avoid theatrical exaggeration, random metaphors, and over-clever punchlines\n"
            "- prioritize semantic fidelity over style flex\n"
            "- still sound like a person, just less \"trying too hard\"\n"
            if payload.get("mode_profile") == "seriously"
            else ""
        )
        + (
            "\n\nNarrative mode rules:\n"
            "- default to a light-touch rewrite; if a line already works, do not reinvent it just to sound authored\n"
            "- keep the writing human and reflective, not performative\n"
            "- preserve the sentence movement when it already works: event first, motive next, concrete image after\n"
            "- punctuation can breathe a bit; do not over-correct every pause into clean essay prose\n"
            "- avoid thread energy, meme cadence, and forced gíria\n"
            "- preserve natural pauses and small human irregularities if they help the voice\n"
            "- if a noun phrase already sounds human in the source, keep it nearly verbatim instead of reaching for a fresher synonym\n"
            "- if the source already has a good sentence turn, contrast, or pause pattern, keep it and loosen it only slightly instead of rebuilding the sentence from scratch\n"
            "- keep prepositions and verb complements idiomatic; avoid awkward half-spoken constructions that a real person would not actually say\n"
            "- when in doubt, keep the original causal clause closer to the source wording instead of trying to make it more colloquial\n"
            "- do not swap simple verbs for nicer ones like 'carregava', 'sumir', or 'poupa' unless the source clearly wants that register\n"
            "- at least one candidate should preserve the original sentence skeleton and key lexical anchors almost verbatim\n"
            "- keep concrete objects, image-bearing details, and emotional logic intact; if the source lists items, keep them all and keep the order unless there is a strong reason not to\n"
            "- do not borrow donor nouns or donor images just because they sound nice; donors are for texture, not new props\n"
            "- do not add new causal judgments, extra motives, or explanatory afterthoughts that are not already implied by the source\n"
            "- do not introduce new metaphors, elevated abstractions, or literary images unless the source already strongly suggests them\n"
            "- stay close to the original semantic image system: keep objects, scenes, and emotional logic recognizable\n"
            "- do not reach for em dashes or dramatic punctuation just to make the line feel literary; plain pauses usually read more human\n"
            if payload.get("mode_profile") == "narrative"
            else ""
        )
        + (
            "\n\nBritish professional mode rules:\n"
            "- sound experienced, practical, and understated\n"
            "- avoid consultancy polish, pitch-deck rhythm, and tidy strategic triads\n"
            "- prefer ordinary verbs over glossy phrasing; plainer is better here\n"
            "- keep a mild British understatement if it helps, but do not turn it into a character bit\n"
            "- avoid formulas like 'what they stand for', 'work that lands', or other neat consultancy finishes\n"
            "- keep one concrete professional noun from the source if it is already doing useful work; do not abstract it away into 'purpose', 'thinking', or 'what matters'\n"
            "- avoid polished consultancy nouns like 'purpose', 'strategy' as a slogan, 'value', 'impact', or 'transformation' unless the source already leans that way\n"
            "- prefer plain wording like 'help companies explain themselves better' or 'make the message clearer' over 'get clear on their purpose'\n"
            "- if you mention execution, use ordinary phrasing like 'in day-to-day work' or 'once people start using it', not 'works in practice' or 'turns into something'\n"
            "- avoid jokier British shorthand like 'what they're on about' when the source is professional and straightforward\n"
            "- let the sentence breathe; do not compress everything into slogan-like shorthand or vague phrasey summaries\n"
            if payload.get("mode_profile") == "british_professional"
            else ""
        )
        + (
            "\n\nCasual mode rules:\n"
            "- sound current and plainspoken, like a real American note or reply\n"
            "- use contractions naturally; fragments are okay if they feel spoken\n"
            "- do not drift into brand strategy jargon, deck language, or polished summary mode\n"
            "- avoid canned phrases like 'the whole stack', 'moves the needle', or 'actually ships' unless the source already lives there\n"
            "- keep it conversational without trying too hard to be witty or online\n"
            "- for short complaint-like inputs, prefer two short sentences max\n"
            "- keep the tone like a real text reply, not a bit, punchline, or quote-tweet\n"
            "- do not escalate the temperature beyond the source\n"
            "- avoid meme markers, irony-posturing, and internet-performance wording unless the source already has it\n"
            "- if the source is already clear, make it sound more lived-in, not more dramatic\n"
            if payload.get("mode_profile") == "casual"
            else ""
        )
        + (
            "\n\nPunctuation rules:\n"
            "- do not automatically normalize punctuation into perfect schoolbook prose\n"
            "- use punctuation the way a real person in this surface would use it\n"
            "- a little looseness is good when it sounds natural\n"
            "- avoid over-clean symmetrical sentence rhythm that screams LLM\n"
        )
        + (
            "\n\nInternet surface rules:\n"
            "- formatting is allowed to carry meaning, rhythm, or tone when it suits the surface\n"
            "- line breaks, markdown emphasis, quotes, bullets, separators, reactions, and emoticons can be used when they feel culturally native\n"
            "- never add decorative symbols just to make the text look styled\n"
            "- never use generic AI emoji habits when a sharper native marker would be better, or when no marker is needed at all\n"
            "- if the source is professional or reflective, keep formatting restrained\n"
        )
        + f"\n\nReturn strict JSON in this shape:\n"
        + "{\n"
        + '  "candidates": [\n'
        + "    {\n"
        + '      "label": "short label",\n'
        + '      "text": "rewritten text",\n'
        + '      "why": "why this variant works"\n'
        + "    }\n"
        + "  ]\n"
        + "}\n\n"
        + f"Return exactly {candidate_count} candidates."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


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
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--model", default="sonar")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        print("Missing PERPLEXITY_API_KEY", file=sys.stderr)
        return 1

    if not args.pack and not args.db and not args.mode:
        raise SystemExit("use --pack or --db or --mode")

    context_cmd = [
        sys.executable,
        str(ROOT / "retrieval" / "rewrite_context_builder.py"),
        *(["--pack", str(args.pack)] if args.pack else []),
        *(["--db", str(args.db)] if args.db else []),
        *(["--mode", args.mode] if args.mode else []),
        "--source-text",
        args.source_text,
        "--query",
        args.query,
        "--surface-mode",
        args.surface_mode,
        "--preferred-bucket",
        args.preferred_bucket,
        "--fallback-bucket",
        args.fallback_bucket,
        "--top-k",
        str(args.top_k),
    ]
    payload = json.loads(
        subprocess.run(
            context_cmd,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": args.model,
            "messages": build_messages(payload, args.candidate_count),
            "temperature": 0.6 if payload.get("mode_profile") == "narrative" else 0.8,
        },
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed = extract_json_block(content)

    result = {
        "source_text": args.source_text,
        "rewrite_goal": payload.get("rewrite_goal", args.query),
        "preferred_bucket": payload.get("preferred_bucket", args.preferred_bucket),
        "preferred_buckets": payload.get("preferred_buckets", []),
        "mode_profile": payload.get("mode_profile", "default"),
        "surface_mode": payload.get("surface_mode", args.surface_mode),
        "donor_snippets": payload["donor_snippets"],
        "style_signals": payload.get("style_signals", []),
        "candidates": parsed.get("candidates", []),
        "_meta": {
            "model": data.get("model", args.model),
            "usage": data.get("usage", {}),
        },
    }

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
