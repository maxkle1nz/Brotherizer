# Legacy Wrappers and Compatibility

Brotherizer still ships a slim legacy surface for older clients and quick scripts, but `/v1/*` is the contract to build against.

- `GET /health`
- `GET /modes`
- `POST /rewrite`

## Why the legacy surface exists

It keeps old callers alive while the runtime grows up.

## Legacy vs canonical

### Health

- `GET /health`
  - small legacy payload
  - returns the basic service shape

```json
{
  "ok": true,
  "service": "brotherizer",
  "version": "1.0.0"
}
```
- `GET /v1/health`
  - canonical runtime health payload with version, time, and runtime details

### Modes

- `GET /modes`
  - raw config-shaped response keyed by mode slug
- `GET /v1/modes`
  - normalized client-facing mode listing
  - returns `slug`, `label`, and inferred `surfaces`

### Rewrite

- `POST /rewrite`
  - compatibility wrapper
  - flatter response shape
- `POST /v1/rewrite`
  - canonical runtime response
  - durable job shape
  - richer request, insight, and error semantics

#### What the legacy rewrite wrapper keeps

- `job_id`
- `source_text`
- `surface_mode`
- `candidates`
- `winner`
- top-level `donor_snippets`
- top-level `style_signals`

#### What the legacy rewrite wrapper drops

Compared with `/v1/rewrite`, the legacy wrapper does **not** preserve:

- `status`
- `request`
- `winner_candidate_id`
- `chosen_candidate_id`
- `chosen`
- `choice_history`
- `errors`
- timestamps
- `insight`

## Recommendation

If you are integrating Brotherizer today:

- build against `/v1/*`
- treat legacy wrappers as compatibility-only

That way you get the runtime semantics, not the historical shortcut surface.
