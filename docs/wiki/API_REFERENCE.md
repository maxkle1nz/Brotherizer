# API Reference

Brotherizer is API-first.

## Canonical endpoints

- `GET /`
- `GET /v1/health`
- `GET /v1/modes`
- `GET /v1/capabilities`
- `POST /v1/rewrite`
- `GET /v1/jobs/:id`
- `POST /v1/jobs/:id/choose`

Legacy wrappers still exist:

- `GET /health`
- `GET /modes`
- `POST /rewrite`

Compatibility details live in [Legacy Wrappers and Compatibility](LEGACY_WRAPPERS_AND_COMPATIBILITY.md).

## Default host and port

By default:

- host: `127.0.0.1`
- port: `5555`

Override with:

- `BROTHERIZER_HOST`
- `BROTHERIZER_PORT`

## `POST /v1/rewrite`

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
- `use_xai_judge` enables the optional Grok judge lane

## `GET /v1/capabilities`

Current shipped capability groups:

- `providers`
- `limits`
- `features`

What they mean:

- `providers.generation` describes the fast rewrite lane
- `providers.judge` describes the optional judge lane
- `limits.max_input_chars` is the practical input ceiling enforced by the runtime
- `limits.max_candidate_count` is the supported candidate cap
- `limits.supports_document_rewrite` is currently `false`
- `features.surface_mode` indicates surface-aware rewriting is supported
- `features.choose_candidate` indicates winner override is supported
- `features.streaming` is currently `false`

## `GET /v1/jobs/:id`

Returns the full persisted job shape, including:

- `winner`
- `chosen`
- `candidates`
- `choice_history`
- `errors`
- timestamps
- request metadata
- provider/model insight

## `GET /`

The root endpoint is a small descriptor surface.

It is useful for:

- quick service discovery
- local smoke checks
- simple clients that want to enumerate endpoints without fetching the full docs

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
    "/health",
    "/modes",
    "/rewrite"
  ]
}
```

## `POST /v1/jobs/:id/choose`

Choose a non-winner candidate later:

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
