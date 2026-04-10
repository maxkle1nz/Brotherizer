# Brotherizer

> The rewrite engine that gives LLM text a pulse.

LLM text can be technically correct and still feel socially dead. Brotherizer exists for that exact problem.

It is an API-first style-retrieval, rewrite, and reranking system for teams, agents, and products that already generate text with models but want the output to sound warmer, sharper, more human, and less like it was polished by a committee of very anxious robots.

No detector cosplay. No fake-human sludge. No polished-for-no-reason copy.

Just better text.

## What Brotherizer is

Brotherizer is a narrow product on purpose:

- it retrieves donor writing patterns
- it rewrites for the right mode and surface
- it reranks multiple candidates
- it lets the client keep the winner or choose another option

Think of it as voice middleware for LLM output.

If your model already knows what to say but keeps saying it like a brand-safe hostage statement, this is the lane.

## What it is not

Brotherizer is not:

- a general chat model
- a giant prompt-management suite
- a full writing app
- a detector-evasion gimmick

The point is not to make text look "less AI" in some scammy benchmark sense.

The point is to make it sound more like a person actually meant it.

## How it works

Brotherizer runs a five-part pipeline:

1. **Retrieve donor texture**
   - pull donor snippets from local packs or the corpus database
   - optionally use local embeddings for semantic lookup

2. **Resolve mode + surface**
   - choose the right voice family
   - apply surface-aware formatting and style directives

3. **Generate multiple rewrites**
   - produce several candidates instead of pretending the first shot is always the best shot

4. **Rerank**
   - score candidates for semantic fidelity, mode fit, surface fit, anti-generic behavior, and composition quality
   - optionally run an xAI/Grok judge pass for harder selection calls

5. **Persist the decision**
   - keep the `winner`
   - allow a client or user to `choose` a different candidate later
   - store job, candidate, and choice history in the runtime DB

The result is simple:

- send text in
- get ranked options back
- keep the winner, or override it

## Current model stack

Brotherizer does not pretend all providers are interchangeable. The repo ships with a specific split today:

- **Generation lane:** Perplexity Sonar
- **Judge lane:** xAI Grok reasoning models
- **Optional semantic retrieval lane:** local Ollama embeddings

In practice, that means:

- **Perplexity Sonar** handles the fast rewrite pass
- **Grok** handles the optional judgment-heavy pass when selection quality matters more than speed
- **Ollama** is there if you want local semantic retrieval for the donor corpus

Current defaults in the repo:

- generation model: `sonar`
- judge model: `grok-4.20-reasoning`
- embedding model: `nomic-embed-text`

Earlier Grok reasoning variants can still be used by setting `BROTHERIZER_XAI_MODEL`. The public docs explain this in more detail in [`docs/wiki/MODEL_ROUTING_AND_PROVIDERS.md`](docs/wiki/MODEL_ROUTING_AND_PROVIDERS.md).

## The research system is still here

It was **not** removed.

What changed is the public framing.

The live scraping and internal acquisition lanes are no longer part of the public repo, but the public research substrate is still very real:

- donor packs under [`data/donor_packs/`](data/donor_packs/)
- corpus DB builder
- optional embedding index builder
- style radar seed signals and DB builder
- formatting / internet-symbol packs
- retrieval selectors that feed the rewrite engine

If you want the full public explanation, go here:

- [`docs/wiki/HOW_IT_WORKS.md`](docs/wiki/HOW_IT_WORKS.md)
- [`docs/wiki/LOCAL_SETUP_AND_DATABASES.md`](docs/wiki/LOCAL_SETUP_AND_DATABASES.md)
- [`RESEARCH/README.md`](RESEARCH/README.md)

## Core features

### 1. Rewrite modes

Brotherizer ships with multiple voice families, including:

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

Defined in [`configs/brotherizer_modes.json`](configs/brotherizer_modes.json).

### 2. Surface-aware rewriting

Brotherizer can condition the rewrite for:

- `reply`
- `post`
- `thread`
- `bio`
- `caption`
- `note`

That changes more than formatting. It changes rhythm, looseness, compression, and reranking behavior.

### 3. Donor memory

Brotherizer does not rely on prompt adjectives alone.

It retrieves donor snippets from real writing packs and uses them as texture, pressure, and voice reference without copying them verbatim.

See [`RESEARCH/DONOR_PACKS.md`](RESEARCH/DONOR_PACKS.md).

### 4. Style radar + formatting packs

Brotherizer also uses:

- [`configs/style_radar_seed_signals.json`](configs/style_radar_seed_signals.json)
- [`configs/internet_symbol_library.json`](configs/internet_symbol_library.json)

That helps it reason about:

- internet-native markers
- compact reaction language
- reflective vs casual surfaces
- profile/bio cleanliness
- reply vs thread vs note behavior

### 5. Candidate ranking

Brotherizer does not emit one rewrite and pray.

It generates several candidates and reranks them with:

- semantic preservation
- mode fit
- surface fit
- anti-generic heuristics
- composition penalties
- optional xAI judge scoring

### 6. Durable runtime jobs

The runtime persists:

- jobs
- candidates
- choices
- runtime errors
- idempotency keys

That gives you:

- stable `job_id`
- `winner` vs `chosen`
- replay-safe reads of completed jobs
- idempotent rewrite submission

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

- `PERPLEXITY_API_KEY` is required for generation
- `XAI_API_KEY` is only required if you want the judge lane
- local embeddings require a running Ollama instance if you choose to build them

You can also copy the example env:

```bash
cp .runtime/brotherizer.env.example .runtime/brotherizer.env
```

### 3. Build the local stores

Build the corpus DB:

```bash
python3 storage/build_corpus_db.py \
  --inputs data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson \
  --db data/corpus/brotherizer.db
```

Build the style radar DB:

```bash
python3 storage/build_style_radar_db.py \
  --input configs/style_radar_seed_signals.json \
  --db data/corpus/style_radar.db
```

Optional: build embeddings for semantic retrieval:

```bash
python3 storage/build_embedding_index.py \
  --db data/corpus/brotherizer.db
```

## Run Brotherizer

### CLI

Recommended mode-driven example:

```bash
python3 brotherize.py \
  --mode casual_us_human_mode \
  --text "This still sounds too polished and generic." \
  --use-xai-judge
```

Grounded, more restrained example:

```bash
python3 brotherize.py \
  --mode seriously_english_mode \
  --text "I think this still sounds too polished and generic." \
  --use-xai-judge
```

### API

Run the API directly:

```bash
python3 api/brotherizer_api.py
```

Or use the helper script:

```bash
./scripts/start_brotherizer_api.sh
```

By default, Brotherizer serves on `http://127.0.0.1:5555`.

Rewrite via API:

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

Choose a non-winner candidate later:

```bash
curl -X POST http://127.0.0.1:5555/v1/jobs/<job_id>/choose \
  -H 'Content-Type: application/json' \
  -d '{
    "candidate_id": "<candidate_id>",
    "actor": { "type": "client", "id": "codex" },
    "reason": "User preferred the alternate"
  }'
```

## API surface

Canonical endpoints:

- `GET /`
- `GET /v1/health`
- `GET /v1/modes`
- `GET /v1/capabilities`
- `POST /v1/rewrite`
- `GET /v1/jobs/:id`
- `POST /v1/jobs/:id/choose`

Legacy wrappers:

- `GET /health`
- `GET /modes`
- `POST /rewrite`

The real contract lives under `/v1/*`.

## Repo docs / wiki

Start here:

- [`docs/README.md`](docs/README.md)
- [`docs/wiki/START_HERE.md`](docs/wiki/START_HERE.md)

Most useful pages:

- [`docs/wiki/HOW_IT_WORKS.md`](docs/wiki/HOW_IT_WORKS.md)
- [`docs/wiki/POSITIONING.md`](docs/wiki/POSITIONING.md)
- [`docs/wiki/MODEL_ROUTING_AND_PROVIDERS.md`](docs/wiki/MODEL_ROUTING_AND_PROVIDERS.md)
- [`docs/wiki/API_REFERENCE.md`](docs/wiki/API_REFERENCE.md)
- [`docs/wiki/SECURITY_AND_SECRETS.md`](docs/wiki/SECURITY_AND_SECRETS.md)

Research and corpus-building docs:

- [`RESEARCH/README.md`](RESEARCH/README.md)
- [`RESEARCH/BUILDING_DATABASES.md`](RESEARCH/BUILDING_DATABASES.md)
- [`RESEARCH/DONOR_PACKS.md`](RESEARCH/DONOR_PACKS.md)
- [`RESEARCH/CONTRIBUTING.md`](RESEARCH/CONTRIBUTING.md)

## Contributing

Brotherizer gets stronger when the donor packs get better.

We especially want:

- more languages
- more registers
- cleaner professional voices
- better note / reply / caption coverage

If you can build a clean, text-only donor pack in your language, we want it.

Please keep identity out of the data:

- no handles
- no names
- no emails
- no signatures
- no `source_ref`
- no metadata that can reveal the author

Start here:

- [`RESEARCH/CONTRIBUTING.md`](RESEARCH/CONTRIBUTING.md)
- [`RESEARCH/SAFETY_AND_SANITIZATION.md`](RESEARCH/SAFETY_AND_SANITIZATION.md)
- [`RESEARCH/LANGUAGE_COVERAGE.md`](RESEARCH/LANGUAGE_COVERAGE.md)

## Positioning

Brotherizer sits between a brand-voice system and LLM middleware.

It is closer to:

- a style-retrieval runtime
- a rewrite-and-rerank engine
- a choice layer for agent output

It is not trying to be:

- Jasper
- Grammarly
- PromptLayer
- LangSmith
- an "undetectable AI" circus

Those are adjacent categories. Brotherizer's lane is tighter:

**retrieve the right texture, rewrite the line, rerank the options, and keep the one that actually sounds alive.**

## Verification

Core regression checks:

```bash
python3 -m py_compile api/brotherizer_api.py brotherize.py runtime/service.py storage/runtime_db.py tests/test_runtime_service.py tests/test_runtime_api.py
python3 -m unittest tests/test_runtime_service.py tests/test_runtime_api.py
```
