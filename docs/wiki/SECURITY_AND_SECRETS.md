# Security and Secrets

Brotherizer is public. That means the repo has to stay boring in the right ways.

## Secrets

Never commit:

- API keys
- bearer tokens
- local runtime env files
- database snapshots with private data

Use:

- `.runtime/brotherizer.env.example` as the template
- `.runtime/brotherizer.env` as your ignored local file

## Donor-pack hygiene

Public donor packs should stay text-only and identity-safe.

Do not include:

- `@handles`
- names
- emails
- signatures
- author metadata
- `source_ref`

Brotherizer cares about voice, not attribution.

## Research docs

The repo documents the public research substrate:

- donor packs
- local database building
- style radar
- optional embeddings

It does **not** document private acquisition infrastructure or secret-bearing integrations.

## Public copy guardrail

Good public docs explain:

- what the system does
- what the providers do
- how to contribute safely

Bad public docs leak:

- internal decision history
- secret handling patterns
- private provenance details
- ranking logic described like a cheat sheet

The goal is clarity without self-sabotage.
