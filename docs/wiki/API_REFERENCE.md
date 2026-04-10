# API Reference

Brotherizer is API-first, but it does not make a thing of it. One runtime. Typed `/v1` endpoints. Legacy wrappers only where compatibility still matters.

## Canonical endpoints

- `GET /`
- `GET /v1/health`
- `GET /v1/modes`
- `GET /v1/capabilities`
- `POST /v1/rewrite`
- `GET /v1/jobs/:id`
- `POST /v1/jobs/:id/choose`
- `GET /demo`

Build against `/v1/*`.

Legacy wrappers still exist for older callers:

- `GET /health`
- `GET /modes`
- `POST /rewrite`

Compatibility details live in [Legacy Wrappers and Compatibility](LEGACY_WRAPPERS_AND_COMPATIBILITY.md).

## `GET /demo`

Brotherizer ships a public-facing interactive demo route.

`/demo` is a packaged static experience served by the same runtime. It is meant to show:

- plain model output vs Brotherized output
- multiple style examples
- a slider-driven transformation demo
- an optional live playground that calls `/v1/rewrite`

The page is useful for:

- first-time product evaluation
- quick stakeholder demos
- showing the value of mode and surface routing without reading the whole handbook

## Default host and port

By default:

- host: `127.0.0.1`
- port: `5555`

Override with:

- `BROTHERIZER_HOST`
- `BROTHERIZER_PORT`

## `POST /v1/rewrite`

Brotherizer rewrites are job-based: submit text, pick a mode, and get back a durable runtime job with candidates, a winner, and optional judge insight.

Request body:

```json
{
  "text": "I think this still sounds too polished and generic.",
  "mode": "casual_us_human_mode",
  "surface_mode": "reply",
  "query": "",
  "candidate_count": 3,
  "use_xai_judge": false
}
```

Notes:

- `text` is required
- `mode` is required
- `surface_mode` is optional
- `query` is optional
- `candidate_count` defaults to `3`
- `use_xai_judge` turns on the optional Grok judge lane

## `GET /v1/capabilities`

This endpoint is the client-facing feature gate. Treat it as the source of truth for what the runtime can do right now.

Current shipped capability groups:

- `providers`
- `limits`
- `features`

What they mean:

- `providers.generation` names the fast rewrite lane
- `providers.judge` names the optional judge lane
- `limits.max_input_chars` is the practical input ceiling enforced by the runtime
- `limits.max_candidate_count` is the supported candidate cap
- `limits.supports_document_rewrite` is currently `false`
- `features.surface_mode` indicates surface-aware rewriting is supported
- `features.choose_candidate` indicates winner override is supported
- `features.streaming` is currently `false`

## `GET /v1/jobs/:id`

Returns the full persisted job record, including:

- `winner`
- `chosen`
- `candidates`
- `choice_history`
- `errors`
- timestamps
- request metadata
- provider/model insight

## `GET /`

The root endpoint is a small discovery surface. It is handy for smoke checks and for simple clients that want the shape of Brotherizer without reading the full docs first.

Current response shape:

```json
{
  "ok": true,
  "service": "brotherizer",
  "api": "v1",
  "endpoints": [
    "/v1/health",
    "/v1/modes",
    "/v1/capabilities",
    "/v1/rewrite",
    "/v1/jobs/:id",
    "/v1/jobs/:id/choose",
    "/demo",
    "/health",
    "/modes",
    "/rewrite"
  ]
}
```

## `POST /v1/jobs/:id/choose`

Use this when a client wants to override the runtime-selected winner later:

```json
{
  "candidate_id": "brc_...",
  "actor": {
    "type": "client",
    "id": "codex"
  },
  "reason": "User preferred the alternate"
}
```

This updates:

- `status` to `chosen`
- `chosen_candidate_id`
- choice history

It does **not** erase the original `winner`.

Full lifecycle details live in [Runtime Lifecycle and Recovery](RUNTIME_LIFECYCLE_AND_RECOVERY.md).

## Job states

Current runtime states:

- `accepted`
- `generating`
- `reranking`
- `judging`
- `completed`
- `failed`
- `cancelled`
- `chosen`

## Idempotency

Brotherizer supports idempotent rewrite submission through the `Idempotency-Key` request header.

If the same key is reused with the same request body, the existing job is returned.

If the same key is reused with a different request body, the runtime returns a conflict.

## Typed errors

The `/v1/*` surface uses typed runtime errors with:

- `code`
- `message`
- `phase`
- `retryable`
- `details`

Examples include:

- `MISSING_TEXT`
- `MISSING_MODE`
- `UNKNOWN_MODE`
- `INVALID_CANDIDATE_COUNT`
- `IDEMPOTENCY_KEY_REUSED`
- `JOB_NOT_FOUND`
- `JOB_NOT_CHOOSEABLE`

## Practical limits

See `GET /v1/capabilities` for the current runtime report.

That includes:

- provider names/models
- `max_input_chars`
- `max_candidate_count`
- support flags such as `choose_candidate`
