# Safety and Sanitization

Brotherizer's public research surface stays useful **and** safe.

## Sanitization rules

Before committing a pack:

- remove `@handles`
- remove names where they identify the author
- remove emails
- remove signatures
- remove source references
- remove identity-bearing metadata

The repo includes a sanitization helper:

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

Brotherizer focuses on reusable voice signals, not personal archives.

Contributors should avoid packing identifiable personal material or proprietary source dumps into public packs.

## Public-repo rule

If a contribution makes the repo harder to trust, it is not a good one.

Clean data wins.
