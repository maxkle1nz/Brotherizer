# Brotherizer Operations Map

Date: 2026-04-02

## What Brotherizer is today

Brotherizer is currently a **style-retrieval + rewrite + rerank system**.

It is not yet:

- a continuously training system,
- a database-heavy platform,
- a vector database product,
- a fine-tuned model,
- a polished end-user SaaS.

Today it works as:

1. collect donor text,
2. clean and bucket donor snippets,
3. retrieve donor snippets by style goal,
4. build rewrite context,
5. generate multiple rewrites,
6. rerank and choose a winner.

## Where things live

### Local repo

Main project root:

- `/Users/cosmophonix/Brotherizer`

### Genesis runtime copy

Main runtime/work directory:

- `/home/neodark/genesis/brotherizer`

## Genesis directory map

### `collectors/`

Purpose:

- acquire raw donor text from sources

Current files:

- `youtube_comments_collector.py`
- `bluesky_post_collector.py`
- `public_web_text_collector.py`
- `forum_thread_collector.py`
- `hn_comment_collector.py`
- `perplexity_source_discovery.py`
- `style_chunker.py`
- `donor_pack_builder.py`

### `retrieval/`

Purpose:

- donor search and rewrite conditioning

Current files:

- `donor_index.py`
- `rewrite_context_builder.py`

### `rewrite/`

Purpose:

- candidate generation and reranking

Current files:

- `rewrite_executor.py`
- `rewrite_reranker.py`

### `api/`

Purpose:

- expose Brotherizer as HTTP service

Current files:

- `brotherizer_api.py`

### `scripts/`

Purpose:

- service operations

Current files:

- `start_brotherizer_api.sh`
- `stop_brotherizer_api.sh`
- `status_brotherizer_api.sh`

### `configs/`

Purpose:

- source and style seeds

Current files:

- `source_targets.example.json`
- `bluesky_english_targets.example.json`
- `forum_english_targets.example.json`
- `forum_ptbr_targets.example.json`

### `data/raw/`

Purpose:

- raw collected text before final shaping

Grows when:

- collectors run

Safe to prune:

- yes, after processed outputs and donor packs are confirmed good

### `data/processed/`

Purpose:

- chunked snippets ready for donor-pack creation

Grows when:

- chunker runs

Safe to prune:

- selectively, after donor pack versions are stable

### `data/donor_packs/`

Purpose:

- clean packs actually used by retrieval/rewrite

Current important files:

- `english_v1.ndjson`
- `english_v2.ndjson`
- `ptbr_v1.ndjson`

This is the most important persisted data layer today.

### `data/rewrite_contexts/`

Purpose:

- intermediate context payloads for debugging

Safe to prune:

- yes

### `data/rewrites/`

Purpose:

- generated rewrite outputs

Safe to prune:

- yes, unless you want an evaluation archive

### `.runtime/`

Purpose:

- pid and daemon log files

Current important files:

- `brotherizer_api.pid`
- `brotherizer_api.log`

## What grows over time

### Small growth

- `.runtime/brotherizer_api.log`
- `data/rewrites/`
- `data/rewrite_contexts/`

### Medium growth

- `data/processed/`
- `data/donor_packs/` if many versions accumulate

### Largest potential growth

- `data/raw/`

Raw collection is the first place that can bloat.

## What to keep vs what to clean

### Keep

- latest stable donor packs
- latest stable configs
- rewrite examples that prove quality
- docs and checkpoints

### Clean regularly

- failed or low-value raw harvests
- stale rewrite contexts
- old ad hoc test rewrites
- logs older than needed

## Recommended cleanup policy

### Always keep

- latest `english_v*`
- latest `ptbr_v*`
- latest successful API smoke test output
- latest L1GHT checkpoint docs

### Remove safely

- `data/raw/*test*` older than 7 days
- `data/processed/*test*` older than 7 days
- `data/rewrites/*example*` older than 14 days if not useful
- old log files after checking service health

## What Brotherizer can do right now

### Working now

- build donor corpora in English and PT-BR
- classify donor snippets by style buckets
- retrieve donor snippets by query + bucket
- build rewrite-conditioning payloads
- generate rewrite candidates with Perplexity
- rerank and choose a winner
- serve rewrites over local HTTP API

### English buckets

- `british_banter`
- `british_casual`
- `worldwide_ironic`
- `worldwide_discussion`
- `reply_bodies`

### PT-BR buckets

- `ptbr_ironic`
- `ptbr_casual`
- `ptbr_discussion`

## What Brotherizer does NOT do yet

- continuous auto-learning from user edits
- vector retrieval / embeddings-based semantic retrieval over donor packs
- semantic preservation scoring using embeddings or NLI
- source provenance analytics dashboard
- multi-user auth and persistence
- product UI

## Best next product steps

### Stage 1: harden v1

- add rotation/cleanup script
- add service auto-start (systemd user unit)
- add stronger source quality filters
- add provenance fields for each rewrite result

### Stage 2: improve quality

- semantic scorer for meaning preservation
- better donor ranking
- more PT-BR reply-body sources
- bucket blending presets

### Stage 3: productize

- REST API with clearer response schema
- simple web UI
- saved presets
- revision history and A/B candidate comparison

## Concrete recommendation

If the goal is to make Brotherizer usable day to day without chaos:

1. treat `data/donor_packs/` as the real asset layer,
2. keep `data/raw/` and `data/processed/` as disposable staging,
3. keep the API running on Genesis,
4. add one cleanup/rotation script next,
5. then improve quality rather than adding more source sprawl.
