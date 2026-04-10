# Retrieval Architecture

Brotherizer is not prompt-only.

The rewrite engine is fed by a retrieval stack with three main layers:

1. donor snippets
2. style radar signals
3. formatting packs

## Donor retrieval

Brotherizer can pull donor material from:

- local donor-pack files
- the corpus database

The default runtime path is lexical/database retrieval, not mandatory semantic embeddings.

That is important because it means the product still works even if you have not built the local embedding index.

## Semantic retrieval

Semantic retrieval exists as an optional local lane:

- build embeddings locally
- query semantically when you want that extra retrieval behavior

Useful, but not required.

## Style radar

Style radar is the curated signal layer that helps the runtime understand surface behavior.

It does not replace donor snippets. It complements them.

## Formatting packs

Formatting packs help Brotherizer decide:

- how loose punctuation can be
- whether internet-native markers belong
- whether a reply should stay compact or a note can breathe

## Retrieval precedence

At a high level:

- mode config chooses the retrieval frame
- donor retrieval supplies actual style texture
- style radar supplies contextual signal
- formatting packs refine surface-native behavior

That payload then feeds generation and reranking.

## Public takeaway

Brotherizer is a retrieval-conditioned rewrite system.

Not just a clever prompt.
