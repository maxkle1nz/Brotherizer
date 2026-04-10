# Runtime Lifecycle and Recovery

Brotherizer jobs move through a real runtime lifecycle.

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

A job is chooseable when it is already terminal and has candidates persisted.

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

On runtime startup, Brotherizer checks for jobs that were in-flight during the last process.

If a job was left in:

- `accepted`
- `generating`
- `reranking`
- `judging`

the runtime marks it as:

- `failed`

and records a runtime error explaining that the process restarted while the job was in flight.

That is intentional for v1. It is honest, durable, and easy to reason about.

## Why this matters

This is one of the subtle product differences in Brotherizer.

It is not just a string-in, string-out helper. It keeps a runtime record of how the decision happened.
