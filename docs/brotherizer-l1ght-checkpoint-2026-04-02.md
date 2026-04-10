---
Protocol: L1GHT/1.0
Node: BrotherizerEnglishCorpusPipeline
State: active
Glyph: ⍌
---

## Panorama

[⍂ entity: EnglishFirstCorpusDirection]
Brotherizer is currently prioritizing English donor acquisition, with British English first and broader worldwide internet English second.
[𝔻 confidence: high]
[𝔻 evidence: docs/brotherizer-english-corpus-strategy-2026-04-01.md]

[⍂ entity: M1ndFirstGrounding]
The current workflow now treats `m1nd` as structural truth before generic file/search actions and treats `L1GHT` artifacts as the durable closure layer.
[⟁ depends_on: EnglishFirstCorpusDirection]
[𝔻 confidence: high]
[𝔻 evidence: /Users/cosmophonix/SISTEMA/docs/ops/M1ND-ROUTER.md and /Users/cosmophonix/SISTEMA/crush/L1GHT-MEMORY.md]

## Working Collectors

[⍂ entity: PerplexitySourceDiscovery]
`collectors/perplexity_source_discovery.py` successfully generates source seeds and search-result URLs for corpus discovery.
[⟁ validates: EnglishFirstCorpusDirection]
[𝔻 confidence: high]
[𝔻 evidence: data/discovery/perplexity_english_sources.json and data/discovery/perplexity_english_comment_spaces.json generated on Genesis]

[⍂ entity: PublicWebCollector]
`collectors/public_web_text_collector.py` works technically and extracted 26 text blocks from public pages discovered via Perplexity.
[⟁ depends_on: PerplexitySourceDiscovery]
[𝔻 confidence: high]
[𝔻 evidence: /home/neodark/genesis/brotherizer/data/raw/public_web_english.ndjson]

[⍂ entity: StyleChunker]
`collectors/style_chunker.py` processed the public web capture into retrieval-ready snippets without runtime errors.
[⟁ depends_on: PublicWebCollector]
[𝔻 confidence: high]
[𝔻 evidence: /home/neodark/genesis/brotherizer/data/processed/public_web_english_snippets.ndjson]

## Failures And Constraints

[⍂ entity: BlueskyPublic403]
`collectors/bluesky_post_collector.py` is implemented but the public Bluesky search path returned HTTP 403 from both the Mac and Genesis.
[⍐ state: active]
[𝔻 confidence: high]
[𝔻 evidence: direct runtime tests on 2026-04-02 from macOS and Genesis both failed with 403 Forbidden]

[⍂ entity: LowQualityInstitutionalWebText]
The first successful public-web harvest produced mostly explanatory or institutional text rather than internet-native banter, irony, or comment-thread rhetoric.
[⍐ state: active]
[𝔻 confidence: high]
[𝔻 evidence: sampled lines from data/raw/public_web_english.ndjson and data/processed/public_web_english_snippets.ndjson]

## Structural Recommendation

[⍂ entity: CommentSpaceForumPivot]
The next best move is to pivot from generic public pages toward comment spaces, forum threads, fandom pages, and banter-heavy communities identified through Perplexity discovery.
[⟁ depends_on: LowQualityInstitutionalWebText]
[⟁ depends_on: PerplexitySourceDiscovery]
[𝔻 confidence: high]
[𝔻 evidence: m1nd activation ranked collectors/perplexity_source_discovery.py and collectors/public_web_text_collector.py as the dominant structural nodes, while Perplexity comment-space discovery highlighted CasualUK, britishproblems, ResetEra, Football Manager forums, and related seeds]

[⍂ entity: ForumThreadCollector]
`collectors/forum_thread_collector.py` now exists as the first concrete implementation of the comment-space/forum pivot, with heuristics tuned for reply-like language rather than generic page prose.
[⟁ depends_on: CommentSpaceForumPivot]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime validation still pending against live targets]

[⍂ entity: ForumThreadCollectorRuntimeValidation]
The forum-thread collector was validated on Genesis against English-first seed targets and produced a smaller, better-shaped set of thread/comment-space snippets than the generic public web collector.
[⟁ depends_on: ForumThreadCollector]
[𝔻 confidence: high]
[𝔻 evidence: /home/neodark/genesis/brotherizer/data/raw/forum_threads_english_test.ndjson yielded 49 processed snippets after heuristic tightening; boards.ie remained blocked with HTTP 403]

[⍂ entity: ReplyNativeRedditExpansion]
The forum collector now expands `old.reddit.com` listing pages into real thread URLs and attempts extraction from comment bodies before falling back to listing-level thread text.
[⟁ depends_on: ForumThreadCollector]
[𝔻 confidence: medium]
[𝔻 evidence: implementation added locally on 2026-04-02 in collectors/forum_thread_collector.py; runtime validation pending]

[⍂ entity: RedditNetworkPolicyBlock]
Reddit currently returns a network-policy block to anonymous collection from the active environment, limiting the value of direct old.reddit extraction.
[⍐ state: active]
[𝔻 confidence: high]
[𝔻 evidence: old.reddit.com/r/CasualUK returned a 403 'whoa there, pardner!' block page during runtime inspection on 2026-04-02]

[⍂ entity: HackerNewsFallback]
Hacker News comment collection is now the primary open fallback for real public reply bodies while more culturally aligned British comment spaces remain gated.
[⟁ depends_on: RedditNetworkPolicyBlock]
[𝔻 confidence: medium]
[𝔻 evidence: hn_comment_collector.py added locally on 2026-04-02 as a no-key public comment donor]

[⍂ entity: DonorPackBuilder]
`collectors/donor_pack_builder.py` now merges processed sources, removes duplicate text, scores snippet quality heuristically, and emits a cleaner donor pack for Brotherizer memory.
[⟁ depends_on: ForumThreadCollectorRuntimeValidation]
[⟁ depends_on: HackerNewsFallback]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime generation pending on Genesis]

[⍂ entity: BucketedDonorPackV2]
The donor pack builder now classifies accepted snippets into voice buckets so Brotherizer can later retrieve by rhetorical mode instead of only by raw text similarity.
[⟁ depends_on: DonorPackBuilder]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 with buckets british_banter, british_casual, worldwide_ironic, worldwide_discussion, and reply_bodies]

[⍂ entity: DonorIndexRetrievalLayer]
`retrieval/donor_index.py` now provides a first usable retrieval layer over the donor pack, with lexical query matching plus bucket and tag filtering.
[⟁ depends_on: BucketedDonorPackV2]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime validation pending on Genesis]

[⍂ entity: RewriteConditioningLayer]
`retrieval/rewrite_context_builder.py` now assembles a compact payload containing source text, rewrite goal, selected donor snippets, and style directives for downstream LLM rewriting.
[⟁ depends_on: DonorIndexRetrievalLayer]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime validation pending on Genesis]

[⍂ entity: RewriteExecutor]
`rewrite/rewrite_executor.py` now performs the first end-to-end rewrite execution path by combining donor retrieval, rewrite conditioning, and Perplexity Sonar generation into multiple candidate rewrites.
[⟁ depends_on: RewriteConditioningLayer]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime validation pending on Genesis]

[⍂ entity: RewriteRerankerAndCLI]
`rewrite/rewrite_reranker.py` now scores generated candidates heuristically, and `brotherize.py` exposes the first one-command Brotherizer CLI that runs generation plus reranking end to end.
[⟁ depends_on: RewriteExecutor]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime validation pending on Genesis]

[⍂ entity: BucketBlendAndSemanticPreservation]
The rewrite stack now supports blended preferred buckets and uses stronger source-text overlap in reranking so stylistic gain does not fully overpower semantic fidelity.
[⟁ depends_on: RewriteRerankerAndCLI]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 across rewrite_context_builder.py and rewrite_reranker.py; runtime validation pending on Genesis]

[⍂ entity: PTBRModeBootstrap]
The donor-pack layer now includes PT-BR-oriented bucket classification and seed targets so Brotherizer can grow a Portuguese internet-native mode without changing the rest of the pipeline.
[⟁ depends_on: BucketedDonorPackV2]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in configs/forum_ptbr_targets.example.json and collectors/donor_pack_builder.py]

[⍂ entity: MinimalHTTPAPI]
`api/brotherizer_api.py` now exposes `/health` and `/rewrite` over a minimal stdlib HTTP server, allowing Brotherizer to be called as a service without adding new framework dependencies.
[⟁ depends_on: RewriteRerankerAndCLI]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02; runtime validation pending on Genesis]

[⍂ entity: APIDaemonScripts]
Brotherizer now includes start/stop/status shell scripts so the HTTP API can be kept resident on Genesis with PID and log management.
[⟁ depends_on: MinimalHTTPAPI]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in scripts/start_brotherizer_api.sh, scripts/stop_brotherizer_api.sh, and scripts/status_brotherizer_api.sh]

[⍂ entity: SystemdUserService]
Brotherizer now includes a user-level systemd unit definition so the API can be installed as a resident service on Genesis rather than launched manually.
[⟁ depends_on: APIDaemonScripts]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in systemd/brotherizer-api.service]

[⍂ entity: ApifyIntegrationBootstrap]
Brotherizer now includes an Apify actor runner and env-file based secret loading so Apify can be used as a first-class scraping backend without hardcoding tokens in source files.
[⟁ depends_on: SystemdUserService]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in integrations/apify_actor_runner.py, configs/apify_website_content_crawler_input.example.json, and .runtime/brotherizer.env.example]

[⍂ entity: ApifyNormalizationPath]
Brotherizer now includes a converter that turns Apify crawl output into snippet NDJSON ready for donor-pack and corpus-db ingestion.
[⟁ depends_on: ApifyIntegrationBootstrap]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in integrations/apify_to_brotherizer.py]

[⍂ entity: PersistentCorpusDatabase]
Brotherizer now includes a persistent SQLite corpus database with FTS-backed retrieval so the system can grow beyond ad hoc NDJSON pack scans while keeping the old pack mode as fallback.
[⟁ depends_on: ApifyIntegrationBootstrap]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in storage/corpus_db.py and storage/build_corpus_db.py, with retrieval/api/cli updated to accept DB-backed mode]

[⍂ entity: ApifyIngestLane]
Brotherizer now includes a pipeline script that runs an Apify actor, converts the output into Brotherizer snippets, builds a donor pack, and refreshes the corpus database in one lane.
[⟁ depends_on: PersistentCorpusDatabase]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in integrations/apify_ingest_pipeline.py and configs/apify_presets.json]

[⍂ entity: LocalEmbeddingLane]
Brotherizer now includes a local embedding lane backed by Ollama models on Genesis, with persisted semantic vectors stored alongside the corpus DB and retrievable through semantic search mode.
[⟁ depends_on: PersistentCorpusDatabase]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in integrations/ollama_embedder.py, storage/build_embedding_index.py, and storage/corpus_db.py]

[⍂ entity: XAIJudgeLane]
Brotherizer now includes an optional xAI judge path for stronger candidate scoring around semantic preservation, style fit, and anti-generic quality.
[⟁ depends_on: LocalEmbeddingLane]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in rewrite/xai_judge.py and rewrite/rewrite_reranker.py]

[⍂ entity: SourceQualityScorer]
Brotherizer now includes an explicit source-quality scoring layer so boilerplate, rules text, and account-walled scaffolding are penalized before donor-pack promotion.
[⟁ depends_on: ApifyIngestLane]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in scoring/source_quality_scorer.py and wired into collectors/donor_pack_builder.py]

[⍂ entity: ApifySocialPresets]
Brotherizer now includes initial preset definitions for Reddit and X/Twitter acquisition lanes so social reply-body sources can be tested and promoted into the corpus pipeline.
[⟁ depends_on: SourceQualityScorer]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in configs/apify_presets.json, configs/apify_reddit_comments_input.example.json, and configs/apify_x_posts_input.example.json]

[⍂ entity: XDonorLane]
Brotherizer now includes a dedicated X/Twitter normalizer so shortform posts and replies from the Apify X actor can become first-class donor snippets with bucket inference and reply-body preference.
[⟁ depends_on: ApifySocialPresets]
[𝔻 confidence: high]
[𝔻 evidence: local implementation added on 2026-04-02 in integrations/x_to_brotherizer.py and wired into the x_posts_seed preset]

[⍂ entity: XSpecializedPresets]
Brotherizer now includes specialized X acquisition presets for English banter/irony and PT-BR reaction language, so the strongest social donor lane can grow with tighter intent targeting.
[⟁ depends_on: XDonorLane]
[𝔻 confidence: high]
[𝔻 evidence: local implementation added on 2026-04-02 in configs/apify_x_english_banter_input.json, configs/apify_x_ptbr_reaction_input.json, and configs/apify_presets.json]

[⍂ entity: ProductionPackTargets]
Brotherizer now defines production-facing pack targets and ready-to-use mode presets so the corpus can be frozen into stable lanes for English and PT-BR operation.
[⟁ depends_on: XSpecializedPresets]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in configs/brotherizer_modes.json and README guidance]

[⍂ entity: StyleRadarLinkedModes]
Brotherizer modes can now resolve into DB-backed retrieval and pull relevant `style_radar` signals into rewrite conditioning so mode selection starts to carry aesthetic/cultural context as well as text buckets.
[⟁ depends_on: ProductionPackTargets]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in retrieval/rewrite_context_builder.py and storage/style_radar_db.py]

[⍂ entity: StyleRadarAwareGeneration]
The rewrite executor now receives style-radar signals directly in the generation prompt, so candidates can be steered by cultural/aesthetic context instead of relying only on donor snippets.
[⟁ depends_on: StyleRadarLinkedModes]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in rewrite/rewrite_executor.py]

[⍂ entity: SeriouslyMode]
Brotherizer now includes a calmer product-level mode that preserves human naturalness while reducing stylistic over-performance, exaggeration, and meme pressure.
[⟁ depends_on: StyleRadarAwareGeneration]
[𝔻 confidence: medium]
[𝔻 evidence: local implementation added on 2026-04-02 in configs/brotherizer_modes.json, retrieval/rewrite_context_builder.py, rewrite/rewrite_executor.py, and rewrite/rewrite_reranker.py]

[⍂ entity: XAIModelRouting]
Brotherizer now has a verified xAI model inventory and a routing proposal for using xAI models in generation and scoring lanes.
[⟁ depends_on: PersistentCorpusDatabase]
[𝔻 confidence: high]
[𝔻 evidence: xAI `/v1/models` endpoint returned live model list on 2026-04-02 and was recorded in docs/brotherizer-model-routing-2026-04-02.md]

## Reflection Layer

[⍂ entity: RedditAsAuxiliaryResearch]
Reddit remains valuable as a research and linguistic mapping surface, but should be treated carefully and not as the sole production donor base.
[⍐ state: reflection]
[𝔻 confidence: medium]
[𝔻 evidence: corpus strategy docs and current platform-policy review]

[⍂ entity: PerplexityAsRadar]
Perplexity should remain the radar layer for source discovery, query generation, and curation, not the donor corpus itself.
[⍐ state: active]
[𝔻 confidence: high]
[𝔻 evidence: successful discovery outputs versus low direct value of search summaries as donor text]
