# Safety and Sanitization

Brotherizer's public research surface has to stay useful **and** safe.

## Sanitization rules

Before a pack is committed:

- remove `@handles`
- remove names where they identify the author
- remove emails
- remove signatures
- remove source references
- remove identity-bearing metadata

The repo already includes a sanitization helper:

- [`scripts/sanitize_donor_packs.py`](../scripts/sanitize_donor_packs.py)

## Secret handling

Never commit:

- provider keys
- tokens
- private source dumps
- local env files

Use:

- `.runtime/brotherizer.env.example` as the template
- `.runtime/brotherizer.env` as your ignored local file

## Copyright and provenance

Brotherizer is interested in reusable voice signals, not in shipping personal archives.

Contributors should avoid packing identifiable personal material or proprietary source dumps into public packs.

## Public-repo rule

If a contribution makes the repo harder to trust, it is not a good contribution.

Clean data wins.
