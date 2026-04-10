# Local Setup and Databases

Brotherizer uses three local data stores worth setting up:

1. **corpus DB**
2. **style radar DB**
3. **optional embedding index**

## 1. Corpus DB

This is the main donor store. It holds the text Brotherizer retrieves from, along with the fields that make retrieval useful.

Run:

```bash
python3 storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson \
  --db data/corpus/brotherizer.db
```

## 2. Style radar DB

This holds the curated signal layer that shapes surface-aware behavior.

```bash
python3 storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db
```

## 3. Optional embedding index

Use this if you want semantic retrieval on top of the donor corpus:

```bash
python3 storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

This step depends on Ollama. If Ollama is not running, the optional semantic lane fails, but the core runtime still works.

## Suggested order

1. corpus DB
2. style radar DB
3. embeddings (optional)
4. rewrite tests
5. API launch

## Next steps

- [API Reference](API_REFERENCE.md)
- [`RESEARCH/BUILDING_DATABASES.md`](../../RESEARCH/BUILDING_DATABASES.md)
- [`RESEARCH/DONOR_PACKS.md`](../../RESEARCH/DONOR_PACKS.md)
