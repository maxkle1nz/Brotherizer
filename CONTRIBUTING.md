# Contributing to Brotherizer

Brotherizer is an API-first rewrite engine with a public research substrate behind it. Contributions are welcome, but the repo should stay sharp, safe, and easy to reason about.

## Ground rules

- keep the public repo product-safe
- do not commit secrets or private source material
- preserve runtime behavior unless you are intentionally changing it
- prefer small, reviewable diffs
- keep docs in English

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
make test
```

Useful local commands:

- `make run-api`
- `make build-corpus`
- `make build-style-radar`
- `make build-embeddings`
- `make test`

## What to contribute

High-value contribution lanes:

- runtime/API improvements
- retrieval and reranking quality improvements
- better docs
- multilingual donor packs
- cleaner style-radar and formatting-pack contributions

For donor-pack and language work, start here:

- [`RESEARCH/CONTRIBUTING.md`](RESEARCH/CONTRIBUTING.md)
- [`RESEARCH/SAFETY_AND_SANITIZATION.md`](RESEARCH/SAFETY_AND_SANITIZATION.md)

## Before opening a PR

- run `make test`
- verify any README/docs command you touched
- keep identity-bearing data out of donor packs
- do not commit generated `.db` files unless explicitly requested

## Public-repo rule

If a change makes the repo harder to trust, it is probably the wrong change.
