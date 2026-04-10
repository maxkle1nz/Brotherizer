# Model Routing and Providers

Brotherizer keeps its provider split visible. Fast rewrite, optional judgment, and local embeddings each get their own lane.

## Current lanes

### Generation

- provider: **Perplexity**
- model: **Sonar**
- role: fast rewrite generation

Why it is here:

- quick response
- grounded/search-oriented model behavior
- good fit for the first rewrite pass

### Judge

- provider: **xAI**
- default model: **`grok-4.20-reasoning`**
- role: optional judgment-heavy reranking pass

Why it is here:

- stronger reasoning pressure on hard selection calls
- useful when multiple candidates preserve meaning but only one really lands

Earlier Grok reasoning variants can still be used by setting:

```bash
export BROTHERIZER_XAI_MODEL=<older-grok-reasoning-model>
```

or any other compatible xAI reasoning model you want to test.

### Local embeddings

- provider: **Ollama**
- default embedding model: **`nomic-embed-text`**
- role: optional semantic retrieval for the donor corpus

This is not required for the main runtime path.

## Publicly documented provider facts

Current at time of writing; re-check the vendor docs before repeating these numbers publicly in future updates.

As of the current official docs:

- **Perplexity Sonar** is documented as a **non-reasoning** model with **128K context length**
- **xAI Grok 4.20** is documented with a **2,000,000 context window**

Those facts matter because they explain the split:

- Sonar is the fast rewrite workhorse
- Grok is the heavier reasoning lane

## The clean public explanation

The safest honest explanation is:

> Brotherizer uses a search-grounded model for fast rewrite passes and a reasoning model for optional judgment-heavy selection.

That is accurate, clear, and does not overclaim.

## What we do not claim

We do not say:

- "Grok is better than everything else"
- "Perplexity is weaker"
- "Brotherizer is provider-agnostic magic"

The repo is wired around real lanes, and the docs should say exactly that.
