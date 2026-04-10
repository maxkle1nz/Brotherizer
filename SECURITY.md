# Security Policy

## Reporting

If you find a security issue in Brotherizer, please do not open a public issue with exploit details.

Use one of these routes instead:

- GitHub Security Advisories, if enabled
- direct contact with the maintainer

## Scope

Security-sensitive areas include:

- API request handling
- runtime persistence
- provider key handling
- donor-pack sanitization
- any code path that touches local files or external providers

## Secrets

Never commit:

- API keys
- bearer tokens
- local env files
- private source dumps

Use:

- `.runtime/brotherizer.env.example` as the template
- `.runtime/brotherizer.env` as the ignored local file

## Public data hygiene

Keep public donor packs text-only and identity-safe.

Do not ship:

- handles
- names
- emails
- signatures
- source refs
- private provenance details
