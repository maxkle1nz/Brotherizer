# Runtime Lifecycle and Recovery

Brotherizer treats rewriting as a real runtime, not just a string-in, string-out helper.

## States

Current states:

- `accepted`
- `generating`
- `reranking`
- `judging`
- `completed`
- `failed`
- `cancelled`
- `chosen`

## Typical flow

The normal happy path is:

`accepted -> generating -> reranking -> judging? -> completed`

If `use_xai_judge` is disabled or unavailable, the job can go straight from:

`reranking -> completed`

If the client later chooses a non-winner candidate:

`completed -> chosen`

## Chooseable state

A job is chooseable once it is terminal and has persisted candidates.

In practice, Brotherizer only allows choosing from:

- `completed`
- `chosen`

## Winner vs chosen

- `winner` is the runtime-selected best candidate
- `chosen` is the client-selected override, if one exists

The product keeps both because those are different facts.

## Failure behavior

If runtime execution fails:

- the job moves to `failed`
- a runtime error row is recorded
- the error is returned through the job surface

## Restart behavior

On runtime startup, Brotherizer looks for jobs that were in-flight when the previous process stopped.

If a job was left in:

- `accepted`
- `generating`
- `reranking`
- `judging`

the runtime marks it as:

- `failed`

and records a runtime error explaining that the process restarted while the job was still running.

That is intentional for v1. It keeps the system honest and easy to reason about.

## Why this matters

Brotherizer keeps a runtime record of the rewrite decision, so it behaves like a product service instead of a throwaway text transform.
