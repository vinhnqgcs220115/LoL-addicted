# LOL Ranked Analytics

Personal DS portfolio project — analyzing ranked LoL performance via the official Riot Games API. Single-summoner scope, no real-time in-game interaction. End product: a live Streamlit dashboard deployed on Streamlit Cloud.

## Target Architecture

Current and planned data flow moves in one direction. `collector.py` fetches from Riot and persists raw JSON to `data/raw/`. `processor.py` parses those files into DuckDB. `features.py` builds the feature matrix from DuckDB tables. `models.py` trains and serializes. `dashboard/app.py` will render only — importing from `src/` and holding no business logic. Notebooks are sandboxed exploration and are never imported by `src/`.

## Module Contracts

Each module owns exactly one layer. Never reach across.

| Module | Owns | Never |
|---|---|---|
| `collector.py` | Riot API calls, rate limiting, raw JSON persistence | Transform or parse data |
| `processor.py` | Parse raw JSON, insert to DuckDB | Call external APIs |
| `features.py` | Compute features from DuckDB tables | Read `data/raw/` directly |
| `models.py` | Train, evaluate, save models | Build features or call APIs |
| `dashboard/app.py` | Streamlit rendering | Contain business logic |

## Data Rules

Files in `data/raw/` are write-once. Never modify after saving. DuckDB is the single source of truth for processed data. Schema is declared once in `processor.py::init_schema()`. All column names use `snake_case`; timestamps use ISO 8601 strings. Use explicit columns when reading persistent tables. `SELECT *` is acceptable only for controlled registered DataFrames whose schema is defined in code.

`game_version` must be stored on every match row. Parse it from `match["info"]["gameVersion"]` in `processor.py` and keep the first two dot-separated segments. Riot API values use labels such as `"16.12.xxxxxxx"`; project discussions may call the same patch `26.12`. Store the API-derived `16.12` form and never hardcode a current patch.

## Code Conventions

Type hints on all functions. Module-level constants in `UPPER_SNAKE_CASE`. All secrets via `python-dotenv`, never hardcoded. Catch specific exceptions, not bare `except`. Docstrings on public functions.

## Riot API Routing

Vietnam server uses split routing across three hosts — getting this wrong causes silent 404s:

- Account-v1 (PUUID lookup): `asia.api.riotgames.com`
- Summoner-v4, League-v4: `vn1.api.riotgames.com`
- Match-v5: `sea.api.riotgames.com`

Free dev key expires every 24h — must regenerate at `developer.riotgames.com`. Rate limit: 20 req/s and 100 req/2min. Guard all calls with `time.sleep(1.3)`. On HTTP 429, wait `Retry-After + 1` seconds before retry.

## Hard Rules

- No hardcoded API keys anywhere in `src/`
- No Riot API calls outside `collector.py`
- No writes to `data/raw/` after initial save
- No logic inside `dashboard/app.py`
- Never commit `.env`, `data/raw/`, or local `*.duckdb` files; `data/lol_deploy.duckdb` is the only deployment exception

## Preferred Libraries

| Purpose | Library |
|---|---|
| Data wrangling | `pandas`, `duckdb` |
| ML | `scikit-learn`, `joblib` |
| Charts | `plotly` (dashboard), `seaborn` (notebooks only) |
| Dashboard | `streamlit` |
| Linting | `ruff` |

## Verification

Before writing any collection code, test the target endpoint in Postman or curl first. Inspect the actual response shape — Riot docs occasionally omit fields or nest things unexpectedly. Set `X-Riot-Token` as a Postman environment variable, not inline.

For unit tests, use `pytest`. Mirror `src/` structure under `tests/` (`tests/test_collector.py`, `tests/test_processor.py`, etc.). Test parsing logic against fixture files: save one real API response per endpoint to `tests/fixtures/` and load it in tests. Never call the real API in unit tests — mock with `unittest.mock.patch`. Always cover edge cases: zero deaths in KDA, a match where the timeline is missing a minute, an empty match ID list.

After every ingestion run, verify DuckDB before moving forward. The minimum checks:

- Row count matches how many files are in `data/raw/`
- No NULL values in `win`, `match_id`, or `champion_name`
- `MIN` and `MAX` of `game_datetime` fall within an expected range
- `match_timelines` row count is roughly `matches count × average game duration in minutes`

If all pass, mark the task done in `CONTEXT.md` and move on.

## Debugging

Work layer by layer from the earliest point in the data flow. Don't jump to assumptions.

**First: is the raw file there?** Check `data/raw/{match_id}.json`. If it exists, the API call succeeded — the problem is in `processor.py` or later. If it doesn't, the problem is in `collector.py` or the key.

**Second: what does the raw JSON actually say?** Open one file manually before touching any code. Riot responses nest participant data inside `info.participants[]` — a field you expect might be two levels deeper than assumed or named differently than the docs show.

**Third: isolate in a notebook.** Load the raw file, run the suspect function step by step. Far faster than adding print statements and re-running the full pipeline.

Common failure patterns:

| Symptom | Likely cause |
|---|---|
| HTTP 403 | API key expired — regenerate at `developer.riotgames.com` |
| HTTP 404 on match-v5 | Wrong routing host — must be `sea.api.riotgames.com`, not `vn1` |
| Empty match ID list | Wrong PUUID, or no ranked games in the requested time window |
| NULL values in feature matrix | Field missing from raw JSON, or timeline lacks that exact minute |
| Streamlit shows stale data | `@st.cache_data` is holding old results — call `.clear()` or restart the server |
| DuckDB "column not found" | Schema in `init_schema()` is out of sync with what `processor.py` inserts |
| Tilt index looks wrong | Missing `.shift(1)` — current game result is leaking into its own feature |

If stuck after going through all three steps, log the issue in `CONTEXT.md` under Known Issues with what was already tried, and move to a different task. Return with fresh context.

## Testing Strategy

Three levels, each with a clear scope:

**Unit tests** (`tests/`) — test one function in isolation with mocked dependencies. Every parsing function in `processor.py` and every feature calculation in `features.py` needs a unit test. Run with `pytest tests/`.

**Manual integration checks** — run the full pipeline on a small batch (10 matches) and verify DuckDB output with the queries listed in Verification above. Not automated; run this after any change to `collector.py` or `processor.py`.

**Notebook smoke tests** — before committing a finished notebook, restart the kernel and run all cells top to bottom. A notebook that only works with leftover kernel state is broken.

No end-to-end test against the real Riot API in CI — the free key expires every 24h, making automated tests impractical. Unit tests with fixtures are sufficient.

## Pipeline Operations

**Adding new matches** — re-run `collector.py`. It skips files that already exist in `data/raw/`, so it is safe to run repeatedly.

**Reprocessing from scratch** — delete `data/lol.duckdb`, then re-run `processor.py`. Raw files are untouched; no API calls needed.

**Adding a new field from the API** — verify the field exists in an actual raw JSON file before touching any code. Then add parsing in `processor.py`, update the schema in `init_schema()`, delete the DB, and reprocess. Never edit files in `data/raw/`.

**Full reset** — delete `data/raw/`, `data/lol.duckdb`, and `models/`. Re-run `collector.py` then `processor.py` in sequence.
