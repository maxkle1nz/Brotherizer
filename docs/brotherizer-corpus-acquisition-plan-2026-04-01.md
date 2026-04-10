# Brotherizer Corpus Acquisition Plan

Date: 2026-04-01

## Goal

Build a donor corpus for **young-to-mid internet language**:

- roughly 18-40,
- online-native,
- casual,
- ironic,
- meme-literate,
- mixed formal/informal,
- often PT-BR or PT-BR plus English code-switching.

The goal is **not** generic "social media text".
The goal is a corpus that captures:

- stance,
- rhythm,
- irony,
- abbreviations,
- internet shortcuts,
- sentence fragmentation,
- punchy endings,
- disagreement patterns,
- DM/comment/reply behavior.

## High-level decision

For Brotherizer, the best donor strategy is:

1. prioritize **consented personal corpora**,
2. supplement with **public shortform internet text**,
3. add **contrast data** for anti-generic scoring,
4. avoid sources whose terms make model training or commercial usage risky.

## Best source tiers

### Tier A: highest value

These should be the backbone.

1. Personal WhatsApp exports from consenting users
2. Personal Telegram exports from consenting users
3. Personal Discord data packages from consenting users
4. Personal tweet / Bluesky / post archives from consenting users
5. Email/newsletter/caption archives from consenting creators who opt in

Why they matter:

- strongest persona signal,
- real interaction patterns,
- stable punctuation habits,
- real slang usage,
- real code-switching,
- audience adaptation is visible.

### Tier B: best public web donors

These are strong for style retrieval and phrase memory.

1. Bluesky public posts
2. YouTube comments on channels with younger audiences
3. Public forums / niche communities / comment sections
4. Reddit only for limited research or heuristic mining, not as a core commercial donor

Why:

- public,
- conversational,
- shortform,
- opinionated,
- current,
- rich in stance markers.

### Tier C: support donors

These are useful, but not primary.

1. spoken dialogue corpora
2. subtitles / conversational transcripts
3. public podcasts with transcripts
4. chat-like fiction or forum roleplay only as weak style support

These help with rhythm and repair, but they are less online-native.

## Important platform/legal constraints

### Reddit

Reddit is useful for research, but high-risk as a commercial donor base.

What current official guidance says:

- Reddit says commercial use of developer tools/services requires permission.
- Reddit explicitly says you may not use Reddit content as model-training input without explicit consent.

Implication:

- OK as a **research reference** or manual phrase analysis source.
- Not ideal as the long-term foundation for a production Brotherizer model or style memory if commercialization is expected.

### Bluesky

Bluesky has a public API with public search endpoints.

Implication:

- very attractive for collection of public conversational text,
- especially useful for current internet register,
- still requires careful storage, attribution, and user-respect policies.

### YouTube comments

The YouTube Data API exposes comment resources and listing.

Implication:

- strong donor for audience-facing casual language,
- especially useful for reactions, jokes, micro-opinions, and conversational phrasing,
- less good for long coherent personal voice than personal corpora.

### Discord / Telegram / WhatsApp / personal exports

These are strongest when the user explicitly consents and uploads or exports their own data.

Implication:

- best product path for personalized voices,
- legally and ethically much cleaner,
- much better for actual style transfer than public web scraping.

## Recommended Brotherizer acquisition strategy

### Lane 1: personal voice lane

Build the premium/high-quality lane around uploads and exports:

- WhatsApp exports,
- Telegram exports,
- Discord data package,
- Twitter/Bluesky archive,
- notes, emails, captions, docs.

This becomes the user's private donor memory.

### Lane 2: public internet lane

Build a broader non-personal style memory from public text:

- public Bluesky posts,
- YouTube comments,
- public forums,
- comments/replies from communities with younger adult language.

This lane teaches:

- slang,
- discourse markers,
- ironic cadence,
- shortform internet rhetoric,
- comment-thread interaction patterns.

### Lane 3: anti-generic lane

Build a separate contrast corpus:

- human internet text,
- parallel LLM rewrites,
- known LLM-ish phrases,
- Brotherizer outputs accepted vs rejected by users.

This lane should feed the:

- genericness scorer,
- banned phrase list,
- reranking model,
- future preference-tuning datasets.

## Source selection for "language until 40 on the internet"

This should be modeled by **subculture and platform**, not age literally.

The best buckets:

1. PT-BR Twitter/Bluesky-adjacent discourse
2. PT-BR YouTube comments in tech, humor, culture, fashion, gaming, relationships, football, gossip
3. Discord/Telegram exports from consenting users
4. meme-heavy public communities
5. mixed PT-BR / EN posts from internet-native professionals and creators

Avoid over-indexing on:

- teenagers only,
- gamer-only language,
- stan-twitter-only language,
- corporate social copy,
- LinkedIn "young professional" writing,
- ragebait / engagement-bait sludge.

You want **broad online-native adult language**, not one caricature.

## Corpus composition target

If building a first useful corpus, target this approximate balance:

- 35% consenting personal corpora
- 25% public short posts and replies
- 20% public comments
- 10% spoken/conversational corpora
- 10% contrast / synthetic-for-eval only

The exact mix can move, but personal corpora should dominate if the product is personalization-first.

## What to scrape

Store short snippets, not full pages.

Best units:

- single post,
- post + first reply,
- comment,
- 2-5 message chat window,
- short thread fragment,
- caption,
- short paragraph.

Avoid:

- giant threads,
- full article pages,
- pages with lots of duplicated UI text,
- bot-heavy feeds,
- repost-only accounts,
- quote-dunk chains without real language value.

## Metadata to capture

For each snippet:

- `text`
- `lang`
- `platform`
- `source_url`
- `author_hash`
- `timestamp`
- `topic_tags`
- `tone_tags`
- `irony_score`
- `slang_score`
- `emoji_score`
- `fragment_score`
- `formality_score`
- `reply_depth`
- `is_reply`
- `audience_mode`
- `consent_status`
- `license_or_terms_note`

This is necessary for retrieval quality and compliance.

## Filtering heuristics

### Keep

- text with contractions or spoken markers
- text with stance
- text with clear personhood
- non-symmetric sentence rhythm
- code-switching when natural
- well-formed fragments
- comments with punchy endings
- casual disagreement
- playful understatement

### Remove

- bot spam
- templated promotion
- giveaway spam
- engagement bait
- repetitive meme copypasta
- hashtag sludge
- low-information reaction spam
- raw toxicity unless specifically building a toxicity-aware mode
- text that is mostly URLs or tags

## Style labels Brotherizer should learn

At ingestion time, attach labels like:

- deadpan
- dry
- affectionate
- blunt
- ranty
- underplayed
- unserious
- sharp
- cynical
- self-aware
- internet-native
- normie
- niche-nerdy
- polished
- messy
- DM-like
- caption-like
- comment-like

These labels make retrieval and reranking much more useful than pure vector similarity.

## Genesis server role

Use the Linux `genesis` server for:

- scheduled scraping jobs,
- HTML cleanup,
- rate-limited collectors,
- periodic deduping,
- embedding pipelines,
- batch metadata enrichment,
- offline scorer experiments.

Suggested responsibilities:

1. fetch public donor text,
2. normalize and chunk,
3. run language / quality filters,
4. compute embeddings,
5. store clean artifacts,
6. export compact retrieval-ready rows.

## Current blocker on genesis

The local machine does **not** currently resolve `genesis` via SSH alias.

What was verified:

- `ssh genesis ...` failed with hostname resolution error
- `~/.ssh/config` currently exposed a host entry for `kosmo-openclaw-tunnel`
- no `genesis` alias was present in `~/.ssh/config` or `/etc/hosts`

Implication:

- the data collection plan is ready,
- but actual remote execution needs the real hostname/IP or correct SSH alias.

## Recommended scraping stack

On genesis:

- Python
- `httpx`
- `beautifulsoup4`
- `selectolax` for fast HTML parsing
- small per-platform collectors
- Postgres for storage
- object storage or flat files for raw captures

Do not start with a giant all-in-one crawler.
Use one collector per source.

## Collector order

### Collector 1

Bluesky public post collector

Why first:

- current internet language,
- public API,
- shortform,
- very good signal-to-noise for online-native voice.

### Collector 2

YouTube comment collector

Why second:

- large volume,
- easy to target by channel/topic,
- great for reactions, irony, micro-arguments.

### Collector 3

Forum/comment collector

Target a few high-value communities rather than scraping the whole web.

### Collector 4

Personal import pipeline

This is actually the most important product feature even if it is not the first scraper.

## Recommended first experiments

1. Build a 50k-200k snippet corpus from public sources
2. Build a 5k-20k snippet corpus from personal-consent exports
3. Train a simple style classifier and genericness scorer
4. Compare retrieval quality:
   - semantic only
   - style only
   - hybrid
5. Run rewrite evaluations using identical prompts and different donor sets

## Product interpretation

The product should say:

- "bring your own voice"
- "adapt to internet-native tone"
- "less generic, more like you"

The product should not say:

- "bypass AI detection"

That keeps the product more durable and the data strategy cleaner.

## Recommended next move

As soon as the real `genesis` SSH target is available:

1. create a small `collectors/` repo structure,
2. implement Bluesky collector,
3. implement YouTube comment collector,
4. store normalized snippets in Postgres,
5. generate first retrieval-ready donor set,
6. evaluate rewrite quality against a baseline with no donor memory.

## Sources

- Reddit developer/data access policy: https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data
- Bluesky docs and searchPosts API: https://docs.bsky.app/ and https://docs.bsky.app/docs/api/app-bsky-feed-search-posts
- YouTube comments API docs: https://developers.google.com/youtube/v3/docs/comments
- Discord data package: https://support.discord.com/hc/en-us/articles/360004957991-Your-Discord-Data-Package
- Telegram export references: https://bugs.telegram.org/c/60 and https://translations.telegram.org/eo/unigram/login/TosDeclineDeleteAccount
