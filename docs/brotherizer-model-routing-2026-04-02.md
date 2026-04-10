# Brotherizer Model Routing

Date: 2026-04-02

## Verified xAI models

Verified live from `GET https://api.x.ai/v1/models` on 2026-04-02.

Current useful text models:

- `grok-4.20-0309-reasoning`
- `grok-4.20-0309-non-reasoning`
- `grok-4.20-multi-agent-0309`
- `grok-4-1-fast-reasoning`
- `grok-4-1-fast-non-reasoning`
- `grok-code-fast-1`
- older but still listed: `grok-4-0709`, `grok-4-fast-*`, `grok-3`, `grok-3-mini`

## Recommended Brotherizer routing

### Rewrite generation

Use:

- `grok-4-1-fast-non-reasoning`

Why:

- fast enough for candidate generation
- should keep latency tolerable for multi-candidate rewrite flows

### Harder style transformation / delicate rewrites

Use:

- `grok-4.20-0309-reasoning`

Why:

- better for nuanced voice transfer
- better when meaning preservation and tone tension matter together

### Scoring / adjudication

Use:

- `grok-4-1-fast-reasoning`

Why:

- good fit for judge/scorer behavior
- likely better cost/latency tradeoff than always using the heaviest reasoning model

### Code helpers inside Brotherizer

Use:

- `grok-code-fast-1`

Why:

- code-oriented helper model for internal implementation/support tasks

## Concrete proposal

For Brotherizer next phase:

1. keep Perplexity for search/discovery
2. keep OpenRouter as general fallback lane
3. add xAI as:
   - candidate rewrite lane
   - semantic-preservation judge lane
   - anti-generic style judge lane

That gives:

- discovery from Perplexity
- generation from xAI
- fallback/flexibility from OpenRouter
