# Donor Packs

Donor packs are the raw style memory that powers Brotherizer.

They are deliberately simple:

- one JSON object per line
- text-first
- identity-safe
- easy to review

## What's in a donor row

Public donor rows usually include:
- `platform`
- `source_kind`
- `content_role`
- `audience_mode`
- `lang_hint`
- `topic_tags`
- `voice_bucket`
- `text`
- `donor_score`
- `source_quality_score`

Check [`pack-schema.example.ndjson`](pack-schema.example.ndjson) for a clean example.

## What to leave out

Do not include:
- `@handles`
- names
- emails
- signatures
- source URLs
- source refs
- any metadata that IDs the author

Brotherizer wants the writing behavior, not the trail back to who wrote it.

## Voice buckets

`voice_bucket` routes text families for retrieval.

Examples in the repo:
- `reply_bodies`
- `casual_us_human`
- `british_banter`
- `en_reflective`
- `en_professional_human`
- `ptbr_reflective`
- `ptbr_professional_human`

## Habits for good packs

- one language per pack
- text-only rows
- tone that stays coherent inside the pack
- topic tags for retrieval, not for identifying sources
- compact, high-signal rows over bloated dumps

## What makes packs useful

Not just "nice writing."

They need:
- repeatable rhythm
- clear tone pressure
- useful compression
- human asymmetry
- punctuation and pacing that feels surface-native

That is the good stuff.
