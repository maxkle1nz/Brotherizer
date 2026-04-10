# Formatting Packs and Symbol Library

Brotherizer goes beyond just pulling donor text. It also picks up surface behavior. That is where formatting packs come in.

## What they are

Formatting packs are curated sets that guide Brotherizer on the right:

- reactions
- emotive markers
- separators
- arrows
- markdown moves
- formatting moves
- surface-specific rules

for a given writing surface.

The public source of truth lives in:

- [`configs/internet_symbol_library.json`](../../configs/internet_symbol_library.json)

## How they differ from style radar

These are related but distinct:

- **style radar** reads the broader signal environment
- **formatting packs** specify formatting that's native to the surface

Put simply:

- style radar asks: what kind of surface energy is this?
- formatting packs ask: what marks and structures belong here?

## Runtime role

During payload building, Brotherizer resolves a formatting pack based on:

- preferred buckets
- mode profile
- surface mode

That pack is then injected into the rewrite prompt as conditioning.

## Why this matters

Human writing is not only about wording.

It is also about:

- where the line breaks
- how compact the reply stays
- whether emphasis is clean or loose
- whether a caption can carry a reaction marker
- whether a note should stay restrained

Formatting packs help Brotherizer handle that without defaulting to generic emoji or forced internet voice.

## Contribution rules

If you want to extend the symbol library:

- add patterns that are genuinely native to the target surface
- prefer restraint over decoration
- do not add symbols just because they look "internet-y"
- do not turn professional or reflective surfaces into meme surfaces
- explain intended use clearly in the pack entry

## Public guardrail

Brotherizer should feel more human, not gimmicky.

If a formatting pack makes the output louder but less believable, it is not a good pack.
