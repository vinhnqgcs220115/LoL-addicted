# LOL Ranked Analytics

Personal DS portfolio project — analyzing ranked LoL performance via the official Riot Games API. Single-summoner scope, no real-time in-game interaction. End product: a live Streamlit dashboard deployed on Streamlit Cloud.

## Where Facts Live

Every fact has exactly one home. Read the home file; do not restate its content elsewhere.

| Kind of fact | Home | Read it when |
|---|---|---|
| What we are building, who for, when it is done, non-goals | `PRODUCT.md` | Before proposing any feature or UI change |
| Standing engineering rules | this file and `AGENTS.md` | Always |
| Mid-lane domain truth | `GAME_MECHANICS.md` | Before touching any gameplay feature |
| Runnable procedures | `.claude/skills/` | When running or debugging the pipeline |
| Current state: counts, metrics, phase, open items, decisions | `.claude/CONTEXT.md` | Before claiming anything about current status |
| How we work together | `.claude/COLLAB.md` | At session start |
| What happened and when | `git log` | When history matters |

**The state rule: `.claude/CONTEXT.md` is the only file that may contain project state — a row count, a metric, a date, a phase, or a done/not-done claim.** Every other document holds rules, product intent, or domain constants only. A session that changes project state edits `CONTEXT.md` and no other document. There is no session log; `git log` is the log.

Not project state, and therefore allowed elsewhere: domain constants and patch-verification dates in `GAME_MECHANICS.md`, dated decision entries, code constants, and thresholds declared in source.

Never trust a status claim in a chat handoff, a plan, or a summary over the repository. Verify against the tree.

## Module Contracts

Each module owns exactly one layer. Never reach across. Notebooks are sandboxed exploration and are never imported by `src/`.

| Module | Owns | Never |
|---|---|---|
| `collector.py` | Riot API calls, rate limiting, raw JSON persistence | Transform or parse data |
| `processor.py` | Parse raw JSON, insert to DuckDB | Call external APIs |
| `features.py` | Compute features from DuckDB tables | Read `data/raw/` directly |
| `models.py` | Train, evaluate, save models | Build features or call APIs |
| `dashboard/app.py` | Streamlit rendering | Contain feature/business logic |

## Data Rules

Files in `data/raw/` are write-once. Never modify after saving. DuckDB is the single source of truth for processed data. Schema is declared once in `processor.py::init_schema()`. All column names use `snake_case`; timestamps use ISO 8601 strings. Use explicit columns when reading persistent tables. `SELECT *` is acceptable only for controlled registered DataFrames whose schema is defined in code.

Collection and processing retain all ranked roles. The current analytical product is mid-only: every Season 16 baseline, dashboard query, feature row, and cluster label must be scoped to `team_position = 'MIDDLE'`. `opp_*` fields currently represent the enemy mid laner. Expanding to all roles requires role-aware opponent extraction, direct tests, and a full DuckDB rebuild.

`game_version` must be stored on every match row. Parse it from `match["info"]["gameVersion"]` in `processor.py` and keep the first two dot-separated segments. Riot API values use labels such as `"16.12.xxxxxxx"`; project discussions may call the same patch `26.12`. Store the API-derived `16.12` form and never hardcode a current patch.

`GAME_MECHANICS.md` is authoritative for mid-lane domain mechanics. Read it before changing roam, death-context, throw/comeback, wave-state, or objective-timing features. Current dashboard labels such as Throw, Comeback, Overextension, Deficit Fight, Post-Laning Throw, and roam-derived cluster features are heuristic proxies from single-player timeline data unless the code explicitly parses full team/opponent state.

## Code Conventions

Type hints on all functions. Module-level constants in `UPPER_SNAKE_CASE`. All secrets via `python-dotenv`, never hardcoded. Catch specific exceptions, not bare `except`. Docstrings on public functions.

## Riot API Routing

Vietnam server uses split routing across two hosts — getting this wrong causes silent 404s:

- Account-v1 (PUUID lookup): `asia.api.riotgames.com`
- Match-v5: `sea.api.riotgames.com`

Free dev key expires every 24h — must regenerate at `developer.riotgames.com`. Rate limit: 20 req/s and 100 req/2min. Guard all calls with `time.sleep(1.3)`. On HTTP 429, wait `Retry-After + 1` seconds before retry.

## Hard Rules

- No hardcoded API keys anywhere in `src/`
- No Riot API calls outside `collector.py`
- No writes to `data/raw/` after initial save
- No feature/business logic inside `dashboard/app.py`; UI queries, caching, and rendering only
- No deriving model features from DataFrame columns; `src/models.py::FEATURE_COLS` is the canonical list
- No hard-coded semantic meaning for numeric cluster IDs; derive feature means from `feature_matrix` joined to `cluster_labels`
- No user-facing proxy label may be presented as gameplay ground truth; qualify it or rename it
- No dashboard dependency on gitignored `models/*.pkl`; those artifacts are local training outputs only
- Never commit `.env`, `data/raw/`, or local `*.duckdb` files; `data/lol_deploy.duckdb` is the only deployment exception

## Preferred Libraries

Charts: `plotly` in the dashboard, `seaborn` in notebooks only. Linting: `ruff`. Everything else is pinned in `requirements.txt`.

## Verification

Before writing any collection code, test the target endpoint in Postman or curl first. Inspect the actual response shape — Riot docs occasionally omit fields or nest things unexpectedly. Set `X-Riot-Token` as a Postman environment variable, not inline.

For unit tests, use `pytest`. Test parsing logic against fixture files: save one real API response per endpoint to `tests/fixtures/` and load it in tests. Never call the real API in unit tests — mock with `unittest.mock.patch`. Always cover edge cases: zero deaths in KDA, a match where the timeline is missing a minute, an empty match ID list.

After every ingestion run, verify DuckDB before moving forward — the checklist lives in the `pipeline-ops` skill.

## Testing Strategy

Three levels, each with a clear scope:

**Unit tests** (`tests/`) — every parsing function in `processor.py` and every feature calculation in `features.py` needs a unit test.

**Manual integration checks** — run the full pipeline on a small batch (10 matches) and verify DuckDB output with the checklist in the `pipeline-ops` skill. Not automated; run this after any change to `collector.py` or `processor.py`.

**Notebook smoke tests** — before committing a finished notebook, restart the kernel and run all cells top to bottom. A notebook that only works with leftover kernel state is broken.

No end-to-end test against the real Riot API in CI — the free key expires every 24h, making automated tests impractical. Unit tests with fixtures are sufficient.
