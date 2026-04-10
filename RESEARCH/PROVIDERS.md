# Providers

Brotherizer uses different providers for different jobs.

That is deliberate.

## Perplexity

Role:

- fast rewrite generation

What it powers:

- `rewrite_executor.py`
- the first-pass candidate generation lane

What key it needs:

- `PERPLEXITY_API_KEY`

Without it:

- runtime generation will not work
- the API can still boot, but rewrite generation requests will fail

## xAI / Grok

Role:

- optional judgment-heavy reranking

What it powers:

- `xai_judge.py`
- the optional judge lane in the runtime

Current default:

- `grok-4.20-reasoning`

Earlier reasoning-capable Grok variants can still be used through `BROTHERIZER_XAI_MODEL`.

What key it needs:

- `XAI_API_KEY`

Without it:

- the judge lane is disabled
- the main rewrite flow can still run without judging

## Ollama

Role:

- optional local embeddings

What it powers:

- `build_embedding_index.py`
- optional semantic donor retrieval

What it needs:

- a local Ollama instance
- a compatible embedding model, default `nomic-embed-text`

Without it:

- lexical/database retrieval still works
- semantic retrieval will not

## Why the split exists

Generation and judgment are not the same job.

Brotherizer prefers:

- a fast lane for generation
- a reasoning-heavy lane for harder selection calls
- a local lane for optional semantic retrieval

That gives the product better control than pretending one provider should do everything equally well.
