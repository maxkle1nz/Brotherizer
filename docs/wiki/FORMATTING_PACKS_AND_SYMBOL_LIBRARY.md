# Formatting Packs and Symbol Library

Brotherizer does not only retrieve donor text.

It also retrieves surface behavior.

That is what formatting packs are for.

## What they are

Formatting packs are curated bundles that tell Brotherizer what kinds of:

- reactions
- emotive markers
- separators
- arrows
- markdown moves
- formatting moves
- surface-specific rules

belong on a given writing surface.

The public source of truth lives in:

- [`configs/internet_symbol_library.json`](../../configs/internet_symbol_library.json)

## How they differ from style radar

These layers are related, but they are not the same thing:

- **style radar** helps Brotherizer understand the broader signal environment
- **formatting packs** tell Brotherizer which formatting moves are culturally native on the surface itself

In plain terms:

- style radar says "what kind of surface energy is this?"
- formatting packs say "what marks and structures belong here?"

## Runtime role

During payload building, Brotherizer resolves a formatting pack based on:

- preferred buckets
- mode profile
- surface mode

That pack is then injected into the rewrite prompt as part of the conditioning payload.

## Why this matters

Human writing is not only about wording.

It is also about:

- where the line breaks
- how compact the reply stays
- whether emphasis is clean or loose
- whether a caption can carry a reaction marker
- whether a note should stay restrained

Formatting packs help Brotherizer handle that without falling back to generic emoji sludge or fake internet voice.

## Contribution rules

If you want to extend the symbol library:

- add patterns that are genuinely native to the target surface
- prefer restraint over decoration
- do not add symbols just because they look "internet-y"
- do not turn professional or reflective surfaces into meme surfaces
- explain intended use clearly in the pack entry

## Public guardrail

Brotherizer should feel more human, not more gimmicky.

If a formatting pack makes the output louder but less believable, it is not a good pack.
