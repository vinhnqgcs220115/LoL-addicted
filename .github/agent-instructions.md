# LOL Ranked Analytics

Personal DS portfolio project — analyzing ranked LoL performance via the official Riot Games API. Single-summoner scope, no real-time in-game interaction. End product: a live Streamlit dashboard deployed on Streamlit Cloud.

## Target Architecture

`collector.py` → `data/raw/` (JSON) → `processor.py` → DuckDB → `features.py` → `models.py` → `dashboard/app.py`

## Module Contracts

Each module owns exactly one layer. Never reach across.

| Module | Owns | Never |
|---|---|---|
| `collector.py` | Riot API calls, rate limiting, raw JSON persistence | Transform or parse data |
| `processor.py` | Parse raw JSON, insert to DuckDB | Call external APIs |
| `features.py` | Compute features from DuckDB tables | Read `data/raw/` directly |
| `models.py` | Train, evaluate, save models | Build features or call APIs |
| `dashboard/app.py` | Streamlit rendering | Contain business logic |

## Riot API Routing

Vietnam server uses three distinct hosts — using the wrong one causes silent 404s:

- Account-v1 (PUUID): `asia.api.riotgames.com`
- Summoner-v4, League-v4: `vn1.api.riotgames.com`
- Match-v5: `sea.api.riotgames.com`

## Data Rules

Raw files in `data/raw/` are write-once. Never overwrite after saving. DuckDB is the single source of truth for all processed data. `game_version` must be stored on every match row: parse `match["info"]["gameVersion"]` and keep the first two dot-separated segments. Store the API-derived form (for example, `"16.12"` even when project discussions call the patch `26.12`) and never hardcode a current patch.

## Code Conventions

Type hints on all functions. All secrets from `.env` via `python-dotenv` — never hardcoded. `snake_case` for all variables, functions, and column names. Catch specific exceptions, not bare `except`.

## Hard Rules

- No hardcoded API keys anywhere in `src/`
- No Riot API calls outside `collector.py`
- No writes to `data/raw/` after initial save
- No logic inside `dashboard/app.py`
- Never commit `.env`, `data/raw/`, or local `*.duckdb` files; `data/lol_deploy.duckdb` is the only deployment exception
