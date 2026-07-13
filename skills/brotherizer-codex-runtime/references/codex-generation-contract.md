# Codex Generation Contract

Use this reference after building a payload with `brotherizer_codex.py payload`.

## Input Payload

The payload includes:

- `source_text`: the exact text to preserve semantically.
- `rewrite_goal`: retrieval and style intent.
- `preferred_bucket` and `preferred_buckets`: voice family signals.
- `mode_profile`: one of `default`, `seriously`, `narrative`, `casual`, or `british_professional`.
- `surface_mode`: `reply`, `post`, `thread`, `bio`, `caption`, or `note`.
- `formatting_pack`: optional surface markers and formatting rules.
- `donor_snippets`: local voice references.
- `style_directives`: required writing constraints.

## Generation Rules

- Preserve meaning, factual claims, names, numbers, and constraints from `source_text`.
- Use donor snippets for texture only; never copy a donor sentence or distinctive phrase verbatim.
- Produce distinct candidates, not tiny punctuation variants.
- Include one conservative candidate that stays close to the source.
- Include one candidate that leans harder into the selected surface.
- Avoid generic AI symmetry, brochure cadence, filler warmth, and over-explaining.
- Keep language culturally native to the requested mode.
- For `bio`, prefer concise profile-ready phrasing.
- For `post`, make the text scannable and public-facing without turning it into LinkedIn slop.
- For `reply`, keep it short, conversational, and low-friction.
- For `note`, allow line breaks and breathing room when useful.
- For `caption`, keep a compact visual beat.

## Output Schema

Return candidate JSON in this exact shape:

```json
{
  "candidates": [
    {
      "label": "codex-a",
      "text": "rewritten text",
      "why": "why this version fits the payload"
    },
    {
      "label": "codex-b",
      "text": "rewritten text",
      "why": "why this version fits the payload"
    },
    {
      "label": "codex-c",
      "text": "rewritten text",
      "why": "why this version fits the payload"
    }
  ]
}
```

Use stable labels: `codex-a`, `codex-b`, `codex-c`, etc.

## Rerank Input

Save only the candidate JSON above to a file, then run:

```bash
python skills/brotherizer-codex-runtime/scripts/brotherizer_codex.py rerank \
  --payload /tmp/brotherizer-payload.json \
  --candidates /tmp/brotherizer-candidates.json \
  --out /tmp/brotherizer-ranked.json
```

The reranker adds `rerank_score`, composition metadata, and `winner`.
