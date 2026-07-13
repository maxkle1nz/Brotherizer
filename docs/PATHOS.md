# Brotherizer PATHOS

Last updated: 2026-07-13
Scope: local continuity artifact for `/Users/kle1nz/Documents/Brotherizer`. Internal handoff — not public copy, no secrets.

## North Star

Brotherizer is voice middleware: it takes LLM text that lands the facts but goes flat on feeling, and rewrites it until it sounds like a person meant it. Retrieve donor texture → resolve mode+surface → generate multiple candidates → rerank with the local taste machinery → persist the decision (winner + overridable choice history).

It is deliberately narrow: not a chat model, not a prompt suite, not detector evasion. The taste machinery (donor packs, style directives, heuristic reranker) is the moat — the generation lane is swappable.

## Current State (2026-07-13 — recovered and stood back up)

- **Recovery session (Claude, 2026-07-13):** the project had been dormant since April. Recovered and proven alive:
  - Repo: `~/Documents/Brotherizer`, `main` == `origin/main` (github.com/maxkle1nz/Brotherizer, public), CI green.
  - An April working-tree diff that never got committed (CI wiring + README section for the Codex-native skill) was validated (10/10 tests) and landed as `b0bc601`.
  - Data recovered from the old `cosmophonix` account install: `data/runtime/brotherizer_runtime.db` (1.5MB — real job/candidate/choice history through Apr 20) and `data/corpus/style_radar.db`. Both live under gitignored paths.
  - `.runtime/brotherizer.env` rebuilt with `XAI_API_KEY` from the login Keychain (0600). **PERPLEXITY_API_KEY is still trapped** in `/Users/cosmophonix/Brotherizer/.runtime/brotherizer.env` (permission denied for this user — owner can `sudo cat` it over if the HTTP generation lane is wanted).
  - API stood up and proven: `http://127.0.0.1:5555/health` → `{"ok": true, "service": "brotherizer", "version": "1.0.0"}`; `/modes` and `/capabilities` serve.
  - **End-to-end cycle proven via the Codex-native lane (no external keys):** `payload` (en_professional_human_mode, 6 donor snippets + directives) → 3 agent-written candidates → `rerank` → winner selected by `brotherizer-local-heuristic` (score 1.6954), and the ranking preferred the driest candidate — the taste machinery behaves as designed.
  - Script exec bits fixed (`scripts/*.sh` were tracked 644 — a fresh checkout couldn't run them as documented) and m1nd `ingest_roots.json` artifacts ignored (`f2e1432`).

## Known Problems

- `pip install -e .` fails at build-dependency resolution in the local `.venv` (Python 3.12). NOT blocking: everything runs from source (the API and skill insert `sys.path` themselves). Console-script entry points (`brotherize`, `brotherizer-api`, …) are unavailable until this is fixed.
- HTTP `/rewrite` generation lane requires `PERPLEXITY_API_KEY` (see above — key still trapped in the other account). The Codex-native lane covers rewrite work without it.
- `scripts/start_brotherizer_api.sh` invokes bare `python3` — on this machine that's 3.14 (system). Start it with the venv first on PATH: `PATH="$PWD/.venv/bin:$PATH" scripts/start_brotherizer_api.sh`.
- The old install at `/Users/cosmophonix/Brotherizer` is now redundant (data recovered) but was NOT deleted — owner's call.

## How To Run (proven commands)

```bash
cd ~/Documents/Brotherizer
.venv/bin/python -m unittest tests/test_runtime_service.py tests/test_runtime_api.py tests/test_brotherizer_codex_skill.py
PATH="$PWD/.venv/bin:$PATH" scripts/start_brotherizer_api.sh   # port 5555
curl -s http://127.0.0.1:5555/health
scripts/stop_brotherizer_api.sh
```

Codex-native lane (no keys):

```bash
.venv/bin/python skills/brotherizer-codex-runtime/scripts/brotherizer_codex.py doctor
.venv/bin/python skills/brotherizer-codex-runtime/scripts/brotherizer_codex.py payload --mode en_professional_human_mode --text "..." --out /tmp/p.json
# agent writes candidates.json: {"candidates":[{"label","text","why"},...]}
.venv/bin/python skills/brotherizer-codex-runtime/scripts/brotherizer_codex.py rerank --payload /tmp/p.json --candidates /tmp/c.json
```

## Operating Doctrine

- Git identity: Max Kle1nz — never Claude. Commits in English. Repo is PUBLIC: no personal paths, no keys, no internal-process language in commits or docs.
- `data/runtime/`, `.runtime/` are gitignored — keep it that way (runtime DB holds real usage history; env holds keys).
- The taste machinery is the product. Generation lanes (Perplexity HTTP, Codex-native, whatever comes next) stay swappable behind it.
- Related knowledge: the HN voice-rewrite system (auto-memory `hn-voice-rewrite-system`) and Brotherizer's style directives are the same doctrine — "prefer human asymmetry over polished AI symmetry" is literally a directive in `configs/`. Cross-pollinate deliberately.

## Next Steps (owner to prioritize)

1. Free the Perplexity key from the old account (or decide the Codex-native lane is the only generation path and say so in the README).
2. Fix the editable install (build-deps pin) so console scripts work.
3. Decide the fate of `/Users/cosmophonix/Brotherizer` (delete after confirming nothing else is unique there).
4. Dogfood candidate: run the GitRooms Show HN draft through Brotherizer's en_professional_human_mode as a real job — the two projects share a soul.
