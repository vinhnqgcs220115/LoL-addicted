# LOL Ranked Analytics

Single-summoner League of Legends analytics built with the Riot Games API, DuckDB, K-Means clustering, and a planned Streamlit dashboard. The current analytical scope is ranked mid-lane games from Season 16; collection and processing retain all roles for future expansion.

## Setup

Install `uv`, then run from the repository root in PowerShell:

```powershell
Copy-Item .env.example .env
.\scripts\workflow.ps1 sync
```

Set `RIOT_API_KEY` and either `GAME_NAME` plus `TAG`, or an existing `PUUID`, in `.env`. The project uses Python 3.11 and creates `.venv` automatically.

## Workflow

```powershell
.\scripts\workflow.ps1 collect
.\scripts\workflow.ps1 process
.\scripts\workflow.ps1 features
.\scripts\workflow.ps1 models
.\scripts\workflow.ps1 refresh
.\scripts\workflow.ps1 rebuild
.\scripts\workflow.ps1 test
.\scripts\workflow.ps1 smoke
.\scripts\workflow.ps1 deploy-db
```

- `refresh` incrementally collects and runs the complete pipeline.
- `rebuild` recreates `data/lol.duckdb` from immutable raw files, then rebuilds features and models. Use it after parser or schema changes.
- `smoke` runs a five-match live pipeline check and requires a valid Riot API key.
- `deploy-db` copies the verified local database to `data/lol_deploy.duckdb` for Streamlit Cloud.

Every command stops on the first failed native process. Run `python -m ruff check src tests` and `.\scripts\workflow.ps1 test` before committing.

## Deployment Data

The dashboard must open `data/lol_deploy.duckdb` read-only. Regenerate it locally with `deploy-db` after verification; never write to it in Streamlit Cloud. Review the database contents before making the repository public because match identifiers are included.

Phase 4 will add the live URL and screenshots.
