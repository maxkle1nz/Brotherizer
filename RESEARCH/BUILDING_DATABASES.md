# Building Databases

Brotherizer's public research stack is local-first. That keeps the build path straightforward and under your control.

## Corpus DB

This is the main donor store. It holds the core text Brotherizer retrieves from.

Build it like this:

```bash
python3 storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson \
  --db data/corpus/brotherizer.db
```

It pulls donor rows into SQLite, along with the voice buckets, topic tags, and scoring fields that retrieval relies on.

## Style Radar DB

This is a curated signal store. Not a giant trained model, just the focused signals Brotherizer actually uses.

Build it:

```bash
python3 storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db
```

## Optional Embedding Index

Use this if you want semantic retrieval.

Build it:

```bash
python3 storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

Requirements:

- Ollama running locally
- a compatible embedding model, default `nomic-embed-text`

## Suggested Local Workflow

1. add or update a donor pack
2. rebuild the corpus DB
3. rebuild style radar if the signal definitions changed
4. rebuild embeddings if you are using the semantic lane
5. test a few rewrites before opening a PR

## Important Note

Embeddings help with research retrieval, but they are **not** required for the default runtime in this repo.
