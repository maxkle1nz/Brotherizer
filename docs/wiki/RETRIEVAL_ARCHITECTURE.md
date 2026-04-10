# Retrieval Architecture

Brotherizer is not prompt-only.

The rewrite engine runs on a three-layer retrieval stack:

1. donor snippets
2. style radar signals
3. formatting packs

## Donor retrieval

Brotherizer can pull donor material from local donor-pack files or the corpus database.

The default runtime path is lexical and database retrieval, not mandatory semantic embeddings.

That matters because the product still works even if you have not built a local embedding index.

## Semantic retrieval

Semantic retrieval exists as an optional local lane.

- build embeddings locally
- query semantically when you want that extra retrieval behavior

Useful, but not required.

## Style radar

Style radar is the curated signal layer that helps the runtime read surface behavior.

It does not replace donor snippets. It sits alongside them.

## Formatting packs

Formatting packs help Brotherizer decide:

- how loose punctuation can be
- whether internet-native markers belong
- whether a reply should stay compact or a note can breathe

## Retrieval precedence

At a high level:

- mode config picks the retrieval frame
- donor retrieval brings in the actual style texture
- style radar adds contextual signal
- formatting packs refine surface-native behavior

That combined payload then feeds generation and reranking.

## Public takeaway

Brotherizer is a retrieval-conditioned rewrite system.

Not just a clever prompt.
