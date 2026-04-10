# Brotherizer

Brotherizer is a RAG rewrite system built to strip the generic AI voice out of LLM outputs. It learns from how real people actually write—rhythm, phrasing, audience fit—and uses that to make responses sound human instead of templated.

> For anyone exhausted by LLM copy that's too polished, too safe, and suspiciously dead behind the eyes.

## Current scope

This repo currently contains:

- research memos in [`docs/`](/Users/cosmophonix/Brotherizer/docs)
- donor acquisition lanes for web, forums, HN, Apify, and X
- donor-pack builders and persistent corpus storage
- semantic retrieval with local embeddings
- rewrite generation, reranking, and mode-based routing
- a local runtime API and daemon scripts for Genesis

## Why this starter

The quickest way to make Brotherizer useful is:

1. collect real shortform human text,
2. normalize it into retrieval-ready snippets,
3. tag it with style metadata,
4. use it as donor memory for rewrite + rerank.

If your model still sounds like it was focus-grouped to death, this is the lane.

## Local structure

- `collectors/youtube_comments_collector.py`
- `collectors/bluesky_post_collector.py`
- `collectors/public_web_text_collector.py`
- `collectors/forum_thread_collector.py`
- `collectors/hn_comment_collector.py`
- `collectors/donor_pack_builder.py`
- `collectors/style_chunker.py`
- `collectors/perplexity_source_discovery.py`
- `retrieval/donor_index.py`
- `retrieval/rewrite_context_builder.py`
- `storage/corpus_db.py`
- `storage/build_corpus_db.py`
- `storage/style_radar_db.py`
- `storage/build_style_radar_db.py`
- `configs/source_targets.example.json`
- `configs/bluesky_english_targets.example.json`
- `configs/forum_english_targets.example.json`
- `configs/forum_ptbr_targets.example.json`

## Quick start

### 1. Create a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests
```

### 2. Copy and edit targets

```bash
cp configs/source_targets.example.json configs/source_targets.json
```

The example targets are currently biased toward:

- British English internet discourse
- English worldwide pop-culture/gaming/comments

### 3. Export the keys you actually want to use

```bash
export PERPLEXITY_API_KEY=your_key_here
export XAI_API_KEY=your_key_here
```

Optional:

```bash
export APIFY_API_TOKEN=your_key_here
export YOUTUBE_API_KEY=your_key_here
```

### 4. Build the persistent stores

```bash
python storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson \
  --db data/corpus/brotherizer.db

python storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db

python storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

### 5. Run Brotherizer from the CLI

```bash
python brotherize.py \
  --db data/corpus/brotherizer.db \
  --mode casual_us_human_mode \
  --text "This still sounds too polished and generic." \
  --use-xai-judge
```

Seriously mode:

```bash
python brotherize.py \
  --db data/corpus/brotherizer.db \
  --mode seriously_english_mode \
  --text "I think this sounds too polished and generic." \
  --use-xai-judge
```

Notes:

- rewrite generation currently runs through **Perplexity Sonar**
- the xAI lane is optional and currently used as a **judge**
- current xAI default in code is `grok-4.20-reasoning`

### 6. Run the local API

```bash
python api/brotherizer_api.py
```

This serves the API only.

Root:

- `GET /`
  - returns a minimal API descriptor

Legacy endpoints still work:

- `GET /health`
- `GET /modes`
- `POST /rewrite`

Canonical runtime endpoints:

- `GET /v1/health`
- `GET /v1/modes`
- `GET /v1/capabilities`
- `POST /v1/rewrite`
- `GET /v1/jobs/:id`
- `POST /v1/jobs/:id/choose`

Or use the daemon helpers:

```bash
./scripts/start_brotherizer_api.sh
./scripts/status_brotherizer_api.sh
```

Example request:

```bash
curl -X POST http://127.0.0.1:5555/rewrite \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "This still sounds too polished and generic.",
    "mode": "casual_us_human_mode",
    "db": "data/corpus/brotherizer.db",
    "use_xai_judge": true
  }'
```

Canonical runtime request:

```bash
curl -X POST http://127.0.0.1:5555/v1/rewrite \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "I think this sounds too polished and generic.",
    "mode": "casual_us_human_mode",
    "surface_mode": "reply",
    "candidate_count": 3,
    "use_xai_judge": false
  }'
```

That returns:

- stable `job_id`
- `winner`
- ranked `candidates`

If a non-winner option is better for the user, choose it later with:

```bash
curl -X POST http://127.0.0.1:5555/v1/jobs/<job_id>/choose \
  -H 'Content-Type: application/json' \
  -d '{
    "candidate_id": "<candidate_id>",
    "actor": { "type": "client", "id": "codex" },
    "reason": "User preferred the alternate"
  }'
```

Capabilities currently report:

- generation provider/model
- judge provider/model
- practical request limits
- supported features

## Genesis

The local Linux server `Genesis` is documented in the workspace memory as:

- host: `192.168.0.43`
- user: `neodark`

If the host is online:

```bash
ssh genesis
```

Typical Genesis workflow:

```bash
cd /home/neodark/genesis/brotherizer
set -a && . ./.runtime/brotherizer.env && set +a
python3 brotherize.py \
  --db data/corpus/brotherizer.db \
  --mode casual_us_human_mode \
  --text "This still sounds too polished and generic." \
  --use-xai-judge
```

The starter collector supports two source modes:

- `channel_id`: collect recent videos from a specific channel
- `query`: search YouTube by topic/region/language, then collect comments from matching videos

For Brotherizer's early corpus work, `query` mode is usually better because it lets us build donor sets by:

- language variety (`en-GB`, `en`)
- region (`GB`, `US`)
- subculture (music, gaming, commentary, podcasts, reaction culture)

Perplexity is best used as:

- source discovery,
- query/seed generation,
- source ranking and enrichment,

not as the donor corpus itself.

Bluesky is currently the cleanest no-auth donor source in this starter.

### 4c. Collect text blocks from public pages discovered via Perplexity

```bash
python collectors/public_web_text_collector.py \
  --input data/discovery/perplexity_english_sources.json \
  --out data/raw/public_web_english.ndjson \
  --limit 10
```

This is a good fallback when platform APIs are blocked or require credentials.

### 4d. Collect comment-space and forum-thread text

```bash
python collectors/forum_thread_collector.py \
  --targets configs/forum_english_targets.example.json \
  --out data/raw/forum_threads_english.ndjson
```

This collector is intentionally tuned for:

- reply-like language,
- banter,
- shorter rhetorical turns,
- thread/comment spaces rather than general web prose.

For `old.reddit.com` targets it now tries to:

- expand listing pages into real thread URLs
- fetch thread pages
- extract actual comment bodies before falling back to listing-level text

### 4e. Collect real public comments from Hacker News

```bash
python collectors/hn_comment_collector.py \
  --query "british" \
  --out data/raw/hn_british_comments.ndjson
```

This is a useful no-key fallback for real reply bodies when other platforms block scraping.

### 5. Build a donor pack

```bash
python collectors/donor_pack_builder.py \
  --inputs \
    data/processed/forum_threads_english_test_snippets.ndjson \
    data/processed/hn_british_comment_snippets.ndjson \
    data/processed/public_web_english_snippets.ndjson \
  --out data/donor_packs/english_v1.ndjson
```

This step merges sources, dedupes by text, scores quality heuristically, and keeps the cleaner snippets.

### 5b. Build a persistent corpus database

```bash
python storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v2.ndjson data/donor_packs/ptbr_v1.ndjson \
  --db data/corpus/brotherizer.db
```

### 5c. Build the style radar database

```bash
python storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db
```

### 5d. Build the embedding index

```bash
python storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

Each selected row also gets:

- `donor_score`
- `source_quality_score`
- `voice_bucket`

Current buckets:

- `british_banter`
- `british_casual`
- `worldwide_ironic`
- `worldwide_discussion`
- `reply_bodies`
- `ptbr_ironic`
- `ptbr_casual`
- `ptbr_discussion`

Current production modes:

- `british_banter_mode`
- `worldwide_ironic_mode`
- `ptbr_twitter_mode`
- `seriously_english_mode`
- `seriously_ptbr_mode`

The donor score now includes a source-quality layer that penalizes policy/boilerplate/community-rules text and rewards more human-looking snippet structure.

### 6. Query the donor pack

```bash
python retrieval/donor_index.py \
  --db data/corpus/brotherizer.db \
  --query "british banter casual complaint" \
  --bucket british_banter \
  --top-k 6
```

Semantic mode:

```bash
python retrieval/donor_index.py \
  --db data/corpus/brotherizer.db \
  --query "british banter casual complaint" \
  --bucket british_banter \
  --semantic \
  --top-k 6
```

This is the first usable retrieval layer for Brotherizer:

- query by intent
- filter by bucket
- return donor snippets that can condition a rewrite or rerank pass

### PT-BR mode

The same stack now supports PT-BR-oriented donor packs through:

- `configs/forum_ptbr_targets.example.json`
- PT-BR bucketing in `collectors/donor_pack_builder.py`

Recommended PT-BR buckets:

- `ptbr_ironic`
- `ptbr_casual`
- `ptbr_discussion`

### 7. Build rewrite conditioning context

```bash
python retrieval/rewrite_context_builder.py \
  --pack data/donor_packs/english_v2.ndjson \
  --source-text "I think this sounds too polished and generic." \
  --query "british banter casual complaint" \
  --preferred-bucket british_banter \
  --out data/rewrite_contexts/example_british_banter.json
```

This emits a compact payload ready to be fed into a downstream rewriter model.

The payload can now include `style_signals` from `style_radar.db`, so generation has access to aesthetic/cultural steering in addition to donor snippets.

### 8. Generate rewrite candidates

```bash
export PERPLEXITY_API_KEY=your_key_here

python rewrite/rewrite_executor.py \
  --pack data/donor_packs/english_v2.ndjson \
  --source-text "I think this sounds too polished and generic." \
  --query "british banter casual complaint" \
  --preferred-bucket british_banter \
  --out data/rewrites/example_british_banter.json
```

This uses the donor pack plus rewrite conditioning context to produce multiple candidate rewrites.

### 9. Rerank and pick a winner

```bash
python rewrite/rewrite_reranker.py \
  --input data/rewrites/example_british_banter.json
```

### 10. Run Brotherizer end to end

```bash
export PERPLEXITY_API_KEY=your_key_here

python brotherize.py \
  --db data/corpus/brotherizer.db \
  --text "I think this sounds too polished and generic." \
  --query "british banter casual complaint" \
  --bucket british_banter
```

With xAI judge:

```bash
export XAI_API_KEY=your_xai_key_here
python brotherize.py \
  --db data/corpus/brotherizer.db \
  --text "I think this sounds too polished and generic." \
  --query "british banter casual complaint" \
  --bucket british_banter \
  --use-xai-judge
```

### 11. Run the local API

```bash
export PERPLEXITY_API_KEY=your_key_here
python api/brotherizer_api.py
```

Health check:

```bash
curl http://127.0.0.1:5555/health
```

Rewrite request:

```bash
curl -X POST http://127.0.0.1:5555/rewrite \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "This still sounds too polished and generic.",
    "query": "casual American direct internet-native reply",
    "bucket": "casual_us_human",
    "pack": "data/donor_packs/english_v3.ndjson"
  }'
```

### 12. Run as a simple daemon

```bash
export PERPLEXITY_API_KEY=your_key_here
./scripts/start_brotherizer_api.sh
./scripts/status_brotherizer_api.sh
./scripts/stop_brotherizer_api.sh
```

### 13. Install as systemd user service on Genesis

Copy the unit file:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/brotherizer-api.service ~/.config/systemd/user/brotherizer-api.service
systemctl --user daemon-reload
systemctl --user enable --now brotherizer-api.service
systemctl --user status brotherizer-api.service --no-pager
```

Notes:

- the service assumes the repo lives at `/home/neodark/genesis/brotherizer`
- `PERPLEXITY_API_KEY` and optional `APIFY_API_TOKEN` should live in `.runtime/brotherizer.env`
- `/health` should still respond even if rewrite credentials are missing

Example:

```bash
cp .runtime/brotherizer.env.example .runtime/brotherizer.env
```

You can also add:

- `XAI_API_KEY`

for future xAI-powered rewrite/scoring lanes.

### 14. Validate Apify token

```bash
export APIFY_API_TOKEN=your_apify_token_here
python integrations/apify_actor_runner.py --validate-token
```

### 15. Run an Apify actor

```bash
python integrations/apify_actor_runner.py \
  --actor apify/website-content-crawler \
  --input-file configs/apify_website_content_crawler_input.example.json \
  --output data/raw/apify_website_content_crawler_example.json
```

### 16. Convert Apify output into Brotherizer snippets

```bash
python integrations/apify_to_brotherizer.py \
  --input data/raw/apify_seed_run.json \
  --out data/processed/apify_seed_snippets.ndjson
```

### 17. Run the Apify ingestion lane

```bash
python integrations/apify_ingest_pipeline.py \
  --preset website_content_english_seed \
  --db data/corpus/brotherizer.db
```

Planned presets:

- `website_content_english_seed`
- `reddit_comments_seed`
- `x_posts_seed`
- `x_english_banter`
- `x_ptbr_reaction`

The `x_posts_seed` preset uses `integrations/x_to_brotherizer.py` and is currently one of the strongest donor lanes for shortform irony, banter, and reply-native internet language.

### Production donor packs

Suggested production packs:

- `english_v3`
  - buckets: `british_banter,british_casual,worldwide_ironic,reply_bodies`
  - langs: `en,en-GB`
- `ptbr_v2`
  - buckets: `ptbr_casual,ptbr_ironic,reply_bodies`
  - lang: `pt-BR`

### Ready-to-use modes

See:

- `configs/brotherizer_modes.json`

You can use modes directly:

```bash
python brotherize.py \
  --mode british_banter_mode \
  --text "I think this sounds too polished and generic."
```

Modes now also allow style-radar-linked conditioning when the backing DBs are present.

### Seriously mode

Use this when you still want:

- human
- natural
- anti-generic

but less:

- meme pressure
- exaggeration
- punchline theater

Examples:

```bash
python brotherize.py \
  --mode seriously_english_mode \
  --text "I think this sounds too polished and generic."
```

```bash
python brotherize.py \
  --mode seriously_english_mode \
  --text "This still sounds too polished and generic."
```

You can also blend buckets:

```bash
python brotherize.py \
  --pack data/donor_packs/english_v2.ndjson \
  --text "I think this sounds too polished and generic." \
  --query "british banter casual complaint" \
  --bucket british_banter,reply_bodies
```

## Next recommended step

After validating the YouTube pipeline, add:

1. a Bluesky collector,
2. metadata tagging,
3. deduping,
4. style scoring,
5. retrieval experiments.
