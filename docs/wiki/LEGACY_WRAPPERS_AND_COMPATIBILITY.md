# Legacy Wrappers and Compatibility

Brotherizer still ships a small legacy surface for compatibility:

- `GET /health`
- `GET /modes`
- `POST /rewrite`

But the canonical contract is:

- `/v1/*`

## Why the legacy surface exists

To keep older clients and quick scripts alive while the runtime grows up.

## Legacy vs canonical

### Health

- `GET /health`
  - small legacy health payload
  - returns:

```json
{
  "ok": true,
  "service": "brotherizer",
  "version": "1.0.0"
}
```
- `GET /v1/health`
  - canonical runtime health payload with version/time/runtime details

### Modes

- `GET /modes`
  - raw mode config style response
  - returns the underlying mode config object keyed by mode slug
- `GET /v1/modes`
  - canonical normalized mode listing for clients
  - returns `slug`, `label`, and inferred `surfaces`

### Rewrite

- `POST /rewrite`
  - compatibility wrapper
  - flatter response shape
- `POST /v1/rewrite`
  - canonical runtime response
  - durable job shape
  - richer request/insight/error semantics

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

That way you get the real runtime semantics instead of the historical shortcut surface.
