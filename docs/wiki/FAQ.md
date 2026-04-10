# FAQ

## Did you remove the research system?

No.

The public repo still ships:

- donor packs
- corpus DB builders
- style radar
- formatting packs
- optional embedding index generation

What is gone is the live internal acquisition layer, not the product-facing retrieval substrate.

## Do I need Grok to use Brotherizer?

No.

The judge lane is optional. Brotherizer can run rewrite generation without xAI.

## Do I need embeddings to use Brotherizer?

No.

Embeddings are optional. The main shipped runtime path still works through lexical/database retrieval.

## Why multiple candidates?

Because one-shot rewrites are often "fine" in the most annoying possible way.

Brotherizer prefers to generate options and then decide.

## Does Brotherizer bypass AI detectors?

That is not the product claim.

Brotherizer exists to make text sound less generic and more human, not to market detector evasion.

## Can I contribute a new language?

Yes, please.

That is one of the most useful ways to improve Brotherizer.

Start here:

- [`RESEARCH/CONTRIBUTING.md`](../../RESEARCH/CONTRIBUTING.md)
- [`RESEARCH/LANGUAGE_COVERAGE.md`](../../RESEARCH/LANGUAGE_COVERAGE.md)

## Why 5555?

Because the public scripts and docs are standardized around that local port today. You can still override it with `BROTHERIZER_PORT`.
