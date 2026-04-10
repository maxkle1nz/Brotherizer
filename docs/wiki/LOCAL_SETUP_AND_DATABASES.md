# Local Setup and Databases

Brotherizer has three local data layers worth knowing about:

1. **corpus DB**
2. **style radar DB**
3. **optional embedding index**

## 1. Corpus DB

The corpus DB stores donor snippets and the retrieval surfaces around them.

Build it like this:

```bash
python3 storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson \
  --db data/corpus/brotherizer.db
```

This is the main retrieval substrate.

## 2. Style radar DB

The style radar DB stores curated signal seeds used to influence surface-aware behavior.

Build it like this:

```bash
python3 storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db
```

## 3. Optional embedding index

If you want semantic retrieval on top of the donor corpus, build embeddings locally:

```bash
python3 storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

This uses Ollama by default.

If Ollama is not running, this step will fail. That does **not** mean Brotherizer is broken. It just means the optional semantic lane is unavailable.

## Recommended setup order

1. build corpus DB
2. build style radar DB
3. optionally build embeddings
4. run rewrite tests
5. start the API

## Where to go next

- [API Reference](API_REFERENCE.md)
- [`RESEARCH/BUILDING_DATABASES.md`](../../RESEARCH/BUILDING_DATABASES.md)
- [`RESEARCH/DONOR_PACKS.md`](../../RESEARCH/DONOR_PACKS.md)
