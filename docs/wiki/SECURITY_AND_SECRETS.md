# Security and Secrets

Brotherizer is public. Keep the repo boring in the right ways.

## Secrets

Never commit:

- API keys
- bearer tokens
- local runtime env files
- database snapshots with private data

Template: `.runtime/brotherizer.env.example`
Local file (ignored): `.runtime/brotherizer.env`

## Donor-pack hygiene

Public donor packs should stay text-only and identity-safe.

Do not include:

- @handles, names, emails
- signatures, author metadata
- `source_ref`

Brotherizer cares about voice, not attribution.

## Public research substrate

Documented:

- donor packs
- local database building
- style radar
- optional embeddings

Not documented: private acquisition infrastructure, secret-bearing integrations, anything that breaks the system if it leaks.

## Public docs: the line

Clear:

- what the system does
- what providers do
- how to contribute safely

Don't leak:

- internal decision history
- secret handling patterns
- private provenance details
- ranking logic as a cheat sheet

Clarity without self-sabotage.
