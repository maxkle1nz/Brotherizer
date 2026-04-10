# Providers

Brotherizer routes different tasks to different providers. That is not accidental. It is how the system stays focused.

## Perplexity

**Role:** fast rewrite generation

**What it powers:**
- `rewrite_executor.py`
- The first-pass candidate generation lane

**Requires:** `PERPLEXITY_API_KEY`

**If missing:** the API still boots, but runtime rewrite generation requests fail.

## xAI / Grok

**Role:** optional judgment-heavy reranking

**What it powers:**
- `xai_judge.py`
- The optional judge lane in the runtime

**Current model:** `grok-4.20-reasoning`

Earlier reasoning-capable Grok variants work via `BROTHERIZER_XAI_MODEL`.

**Requires:** `XAI_API_KEY`

**If missing:** the judge lane is disabled and the main rewrite flow continues unchanged.

## Ollama

**Role:** optional local embeddings

**What it powers:**
- `build_embedding_index.py`
- Optional semantic donor retrieval

**Requires:**
- A local Ollama instance
- A compatible embedding model (default: `nomic-embed-text`)

**If missing:** Lexical and database retrieval continue. Semantic retrieval does not.

## Why this architecture

Generation and judgment are different problems. Brotherizer separates them intentionally:

- A fast lane for generation
- A reasoning-focused lane for harder decisions
- A local lane for optional semantic work

This gives Brotherizer better control than asking one provider to handle every part of the job equally well.
