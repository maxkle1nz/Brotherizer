# Donor Packs

Donor packs are the raw style memory behind Brotherizer.

They are deliberately simple:

- one JSON object per line
- text-first
- identity-safe
- easy to review

## What a donor row contains

Current public donor rows typically include:

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

See [`pack-schema.example.ndjson`](pack-schema.example.ndjson) for a minimal public-safe example.

## What a donor row should not contain

Do not include:

- `@handles`
- names
- emails
- signatures
- source URLs
- source refs
- metadata that can identify the author

Brotherizer wants the writing behavior, not the author trail.

## Voice buckets

`voice_bucket` is how Brotherizer routes text families during retrieval.

Examples in the repo include:

- `reply_bodies`
- `casual_us_human`
- `british_banter`
- `en_reflective`
- `en_professional_human`
- `ptbr_reflective`
- `ptbr_professional_human`

## Good donor-pack habits

- keep one language per pack
- keep the pack text-only
- keep tone internally coherent
- use topic tags to help retrieval, not to narrate source identity
- prefer compact, high-signal rows over bloated dumps

## What makes a pack useful

Good packs do not just contain "nice writing."

They contain:

- repeatable rhythm
- clear tone pressure
- useful compression habits
- human asymmetry
- surface-native punctuation and pacing

That is the good stuff.
