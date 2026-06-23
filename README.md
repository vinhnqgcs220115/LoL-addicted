# LOL Ranked Analytics

Single-summoner League of Legends analytics built with the Riot Games API, DuckDB, K-Means clustering, and Streamlit. The current analytical scope is ranked mid-lane games from Season 16; collection and processing retain all roles for future expansion.

## Development Setup

Install `uv`, then run from the repository root in PowerShell:

```powershell
Copy-Item .env.example .env
.\scripts\workflow.ps1 sync
```

Set `RIOT_API_KEY` and either `GAME_NAME` plus `TAG`, or an existing `PUUID`, in `.env`. The project uses Python 3.11 and creates `.venv` automatically.

`sync` installs `requirements-dev.txt`. With an existing environment, run `uv pip install -r requirements-dev.txt` directly. Streamlit Cloud reads `requirements.txt` automatically, so Jupyter and development tools are not installed in production.

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
.\scripts\workflow.ps1 dashboard
```

- `refresh` incrementally collects and runs the complete pipeline.
- `rebuild` recreates `data/lol.duckdb` from immutable raw files, then rebuilds features and models. Use it after parser or schema changes.
- `smoke` runs a five-match live pipeline check and requires a valid Riot API key.
- `deploy-db` builds a sanitized `data/lol_deploy.duckdb` for Streamlit Cloud.
- `dashboard` starts the local Streamlit app.

Every command stops on the first failed native process. Run `python -m ruff check src tests dashboard scripts` and `.\scripts\workflow.ps1 test` before committing.

## Deployment Data

The dashboard must open `data/lol_deploy.duckdb` read-only. Regenerate it locally with `deploy-db` after verification; never write to it in Streamlit Cloud. Review the database contents before making the repository public because match identifiers are included.

## Updating Deployed Data

```powershell
.\scripts\workflow.ps1 refresh   # collect → process → features → models
.\scripts\workflow.ps1 deploy-db # builds sanitised lol_deploy.duckdb
```

Commit `data/lol_deploy.duckdb`. The deploy step strips the `puuid` column and replaces Riot match IDs with surrogate IDs before writing the deployment file. The dashboard reads the committed file because Streamlit Cloud has no persistent disk.

## Dashboard

- Local: `.\scripts\workflow.ps1 dashboard`
- Deployed: [add after first Streamlit Cloud deployment]
- Streamlit Cloud entry point: `dashboard/app.py`
- Python version: 3.11
