# How It Works

Brotherizer is a retrieval-conditioned rewrite system with reranking and durable runtime choices.

## 1. Retrieve donor texture

Brotherizer starts by selecting donor snippets from either:

- shipped donor-pack files
- the local corpus database

By default, the runtime relies on lexical/FTS-style retrieval. Optional semantic retrieval exists through local embeddings, but it is not the default production rewrite path in this repo.

## 2. Resolve mode and surface

Modes define the broad voice family.

Examples:

- casual US
- reflective English
- understated British professional
- PT-BR internet-native

Surfaces define the delivery context.

Examples:

- reply
- post
- thread
- bio
- caption
- note

This changes more than formatting. It changes compression, looseness, rhythm, and reranking pressure.

## 3. Build the rewrite payload

Brotherizer then builds a conditioning payload that includes:

- source text
- rewrite goal
- preferred bucket(s)
- mode profile
- surface mode
- donor snippets
- style directives
- style radar signals
- formatting pack

That is the bridge between raw retrieval and generation.

## 4. Generate multiple candidates

The repo currently uses **Perplexity Sonar** for the first-pass generation lane.

Brotherizer does not ask for one answer and call it a day. It asks for several candidates because selection quality matters, especially when multiple lines preserve the meaning but only one actually sounds right.

## 5. Rerank

Candidates are reranked using:

- semantic preservation
- mode fit
- surface fit
- anti-generic penalties
- composition grounding
- optional xAI judge score

This is the part many rewrite tools skip. Brotherizer does not.

## 6. Optional judge lane

When enabled, Brotherizer calls an xAI reasoning model as a stricter judge pass.

Why:

- generation and judgment are not always the same job
- fast rewrite generation and slower selection-heavy reasoning can be split cleanly

In this repo, **Grok is the default judge lane** because the project is tuned around using reasoning-heavy judgment for tougher selection calls.

## 7. Persist the decision

Every rewrite job gets a durable runtime record:

- `job_id`
- `winner`
- `chosen`
- candidate list
- choice history
- runtime errors

That means you can:

- fetch the winning result later
- override it with a different candidate
- keep idempotent request behavior

## The simplest mental model

Brotherizer is:

`retrieve -> rewrite -> rerank -> choose`

It is not trying to be more mystical than that.
