# Building Databases

Brotherizer's public research stack is local-first.

## Corpus DB

The corpus DB is the main donor store.

Build it:

```bash
python3 storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson \
  --db data/corpus/brotherizer.db
```

This ingests donor rows into SQLite, including the text, voice bucket, topic tags, and scoring fields Brotherizer uses for retrieval.

## Style radar DB

The style radar DB is a curated signal store, not a giant learned model.

Build it:

```bash
python3 storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db
```

## Optional embedding index

Semantic retrieval is optional.

Build it:

```bash
python3 storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

Requirements:

- Ollama running locally
- a compatible embedding model, default `nomic-embed-text`

## Suggested local workflow

1. add or update a donor pack
2. rebuild the corpus DB
3. rebuild style radar if signal definitions changed
4. optionally rebuild embeddings
5. test a few rewrites before opening a PR

## Important note

Embeddings are a useful research and retrieval option, but they are **not** required for the default runtime path in this repo.
