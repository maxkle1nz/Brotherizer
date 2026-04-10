# Brotherizer

Brotherizer is an API-first rewrite engine for making LLM output sound less generic, less polished-for-no-reason, and more like something a real person would actually say.

It does that by combining:

- donor-memory retrieval
- mode-based voice routing
- surface-aware rewrite conditioning
- heuristic reranking
- optional judge scoring

The product surface is intentionally narrow:

- send text in
- get ranked rewrite options back
- pick the winner, or choose another candidate

No bundled workspace. No embedded review app. Just the engine.

## What it is

Brotherizer is for teams, agents, and products that already have LLM text generation, but are tired of:

- polished-but-dead copy
- safe generic phrasing
- fake “humanized” output that still reads like a bot
- outputs that ignore audience and surface

If your model still sounds like it was focus-grouped to death, this is the lane.

## What it does

Brotherizer takes:

- `text`
- `mode`
- optional `surface_mode`
- optional `candidate_count`
- optional judge lane

And returns:

- a stable `job_id`
- a ranked `winner`
- ranked `candidates`
- donor and style-signal context
- durable `choose` semantics for selecting a non-winner candidate

## Core features

### 1. Rewrite modes

Brotherizer ships with mode routing for distinct voice families:

- `british_banter_mode`
- `worldwide_ironic_mode`
- `en_reflective_human_mode`
- `en_professional_human_mode`
- `british_professional_human_mode`
- `casual_us_human_mode`
- `ptbr_twitter_mode`
- `ptbr_narrative_human_mode`
- `ptbr_professional_human_mode`
- `seriously_english_mode`
- `seriously_ptbr_mode`

Defined in:

- [brotherizer_modes.json](/Users/cosmophonix/Brotherizer/configs/brotherizer_modes.json)

### 2. Surface-aware rewriting

Brotherizer can condition the rewrite for the intended surface:

- `reply`
- `post`
- `caption`
- `note`
- `bio`

This is not cosmetic. It changes:

- rhythm
- punctuation looseness
- formatting tolerance
- reranking behavior

### 3. Donor memory

Brotherizer uses donor packs built from real writing patterns instead of relying on generic prompt adjectives alone.

The repo ships with donor packs under:

- [`data/donor_packs/`](/Users/cosmophonix/Brotherizer/data/donor_packs)

### 4. Style radar + internet formatting packs

Brotherizer supports formatting-aware and culture-aware steering through:

- [internet_symbol_library.json](/Users/cosmophonix/Brotherizer/configs/internet_symbol_library.json)
- [style_radar_seed_signals.json](/Users/cosmophonix/Brotherizer/configs/style_radar_seed_signals.json)

That lets it reason about:

- internet-native markers
- compact reaction language
- reflective vs casual surfaces
- profile/bio cleanliness
- thread vs reply structure

### 5. Candidate ranking

Brotherizer does not just emit one rewrite and hope for the best.

It generates multiple candidates and reranks them with:

- semantic preservation
- mode fit
- surface fit
- anti-generic heuristics
- composition penalties
- optional xAI judge score

Key files:

- [rewrite_executor.py](/Users/cosmophonix/Brotherizer/rewrite/rewrite_executor.py)
- [rewrite_reranker.py](/Users/cosmophonix/Brotherizer/rewrite/rewrite_reranker.py)
- [xai_judge.py](/Users/cosmophonix/Brotherizer/rewrite/xai_judge.py)

### 6. Durable runtime jobs

The runtime persists:

- jobs
- candidates
- choices
- runtime errors
- idempotency keys

This gives you:

- stable `job_id`
- restart-safe reads of completed jobs
- `winner` vs `chosen`
- idempotent rewrite submission

Key files:

- [service.py](/Users/cosmophonix/Brotherizer/runtime/service.py)
- [runtime_db.py](/Users/cosmophonix/Brotherizer/storage/runtime_db.py)
- [runtime_ids.py](/Users/cosmophonix/Brotherizer/runtime/runtime_ids.py)

## API surface

### Canonical endpoints

- `GET /`
- `GET /v1/health`
- `GET /v1/modes`
- `GET /v1/capabilities`
- `POST /v1/rewrite`
- `GET /v1/jobs/:id`
- `POST /v1/jobs/:id/choose`

### Legacy wrappers

- `GET /health`
- `GET /modes`
- `POST /rewrite`

The legacy endpoints are still supported, but `/v1/*` is the canonical contract.

## Quick start

### 1. Create a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests
```

### 2. Export credentials

```bash
export PERPLEXITY_API_KEY=your_key_here
export XAI_API_KEY=your_key_here
```

Notes:

- generation currently runs through **Perplexity Sonar**
- the xAI lane is optional and currently used as a **judge**
- current xAI default in code is `grok-4.20-reasoning`

### 3. Build the local stores

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

### 4. Run from the CLI

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

### 5. Run the API

```bash
python api/brotherizer_api.py
```

### 6. Rewrite via API

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

This returns:

- stable `job_id`
- ranked `winner`
- ranked `candidates`

### 7. Choose a non-winner candidate

```bash
curl -X POST http://127.0.0.1:5555/v1/jobs/<job_id>/choose \
  -H 'Content-Type: application/json' \
  -d '{
    "candidate_id": "<candidate_id>",
    "actor": { "type": "client", "id": "codex" },
    "reason": "User preferred the alternate"
  }'
```

## Capabilities

`GET /v1/capabilities` currently reports:

- generation provider/model
- judge provider/model
- practical request limits
- supported runtime features

Milestone 1 is intentionally API-only.

## Milestone 1 scope

Included:

- phrase/paragraph rewrite
- multiple candidate generation
- ranking and optional judge
- durable runtime jobs
- `winner` vs `chosen`
- idempotency

Not included:

- file rewrite parity
- document rewrite parity
- chunked document assembly
- embedded UI

## Repository layout

### Product code

- [`api/`](/Users/cosmophonix/Brotherizer/api)
- [`runtime/`](/Users/cosmophonix/Brotherizer/runtime)
- [`retrieval/`](/Users/cosmophonix/Brotherizer/retrieval)
- [`rewrite/`](/Users/cosmophonix/Brotherizer/rewrite)
- [`scoring/`](/Users/cosmophonix/Brotherizer/scoring)
- [`storage/`](/Users/cosmophonix/Brotherizer/storage)
- [`tests/`](/Users/cosmophonix/Brotherizer/tests)

### Product assets

- [`configs/brotherizer_modes.json`](/Users/cosmophonix/Brotherizer/configs/brotherizer_modes.json)
- [`configs/internet_symbol_library.json`](/Users/cosmophonix/Brotherizer/configs/internet_symbol_library.json)
- [`configs/style_radar_seed_signals.json`](/Users/cosmophonix/Brotherizer/configs/style_radar_seed_signals.json)
- [`data/donor_packs/`](/Users/cosmophonix/Brotherizer/data/donor_packs)

## Verification

Core regression checks:

```bash
python3 -m py_compile api/brotherizer_api.py runtime/service.py storage/runtime_db.py tests/test_runtime_service.py tests/test_runtime_api.py
python3 -m unittest tests/test_runtime_service.py tests/test_runtime_api.py
```

## Positioning

Brotherizer is not trying to be:

- a general-purpose chat model
- a complete writing app
- a giant orchestration framework

It is the rewrite engine you call when the model output is technically fine but socially dead.
