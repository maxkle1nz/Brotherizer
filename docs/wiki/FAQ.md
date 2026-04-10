# FAQ

## Did you remove the research system?

No. It is still here.

The repo still ships donor packs, corpus DB builders, style radar, formatting packs, and optional embeddings.

What dropped out of the public repo was the private live acquisition layer. The user-facing retrieval substrate is still there.

## Do I need Grok to use Brotherizer?

No.

You can skip the judge lane entirely. The main rewrite flow still runs without xAI.

## Do I need embeddings to use Brotherizer?

No.

Embeddings are optional. Lexical/database retrieval still handles the main flow.

## Why multiple candidates?

Single rewrites often come back technically fine and forgettable.

Brotherizer generates a few, then chooses. That usually gives you a better line than trusting the first pass.

## Does Brotherizer bypass AI detectors?

That is not the claim.

The goal is to make text less canned and more human. No detector promises.

## Can I contribute a new language?

Absolutely.

It is one of the best ways to improve the product.

Start here:
- [`RESEARCH/CONTRIBUTING.md`](../../RESEARCH/CONTRIBUTING.md)
- [`RESEARCH/LANGUAGE_COVERAGE.md`](../../RESEARCH/LANGUAGE_COVERAGE.md)

## Why 5555?

That is the standard port used by the public scripts and docs.

You can still override it with `BROTHERIZER_PORT`.
