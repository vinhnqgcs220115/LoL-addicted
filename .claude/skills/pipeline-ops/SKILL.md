---
name: pipeline-ops
description: Run and verify the LoL analytics pipeline. Use when collecting new matches, reprocessing DuckDB from scratch, adding a new field from the Riot API, building the deployment snapshot, or verifying DuckDB after an ingestion run.
---

# Pipeline operations

> **L2 Reference** · procedure: run and verify the pipeline · owner: Claude · update: when `scripts/workflow.ps1` or pipeline behavior changes

## Commands

Run `.\scripts\workflow.ps1 <command>` from the repo root. Each command stops at the first failing step.

| Command | Does |
|---|---|
| `sync` | Create `.venv` (Python 3.11, via uv) and install `requirements-dev.txt` |
| `collect` | Download new Riot data to `data/raw/` |
| `process` | Load new raw files into `data/lol.duckdb` |
| `features` | Rebuild the mid-lane feature matrix |
| `models` | Retrain K-Means and persist labels (retired in ROADMAP M1.8) |
| `refresh` | Run `collect`, then `process`, then `features`, then `models` |
| `rebuild` | Delete `data/lol.duckdb`, recreate it from raw files, then run `features` and `models`. Use after parser or schema changes. |
| `test` | Run `pytest tests -q` |
| `smoke` | Five-match live pipeline check; needs a valid Riot key |
| `deploy-db` | Build `data/lol_deploy.duckdb` for the live app |
| `dashboard` | Run the Streamlit app locally |

Lint separately: `python -m ruff check src tests dashboard scripts`.

## Procedures

**Adding new matches.** Run `collect`. It skips files that already exist in `data/raw/`, so it is safe to run repeatedly.

**Reprocessing from scratch.** Run `rebuild`. Raw files are untouched, and no API calls are made.

**Adding a new field from the API.**
1. Verify the field exists in an actual raw JSON file before touching any code.
2. Add parsing in `src/processor.py` and update the schema in `init_schema()`.
3. Run `rebuild`.

Never edit files in `data/raw/`.

**Deployment snapshot.** After tests and the DuckDB checks pass, run `deploy-db`. The dashboard reads `data/lol_deploy.duckdb` read-only. Check that the snapshot holds no secrets before committing it.

## Verifying DuckDB after an ingestion run

Verify DuckDB after every ingestion run, before moving forward. The minimum checks:

- The `matches` row count equals the number of match detail files in `data/raw/` (files not ending in `_timeline.json`).
- `win`, `match_id` and `champion_name` contain no NULLs.
- `MIN` and `MAX` of `game_datetime` fall within the expected range.
- The `match_timelines` row count is roughly the `matches` count × the average game length in minutes.
- Feature and cluster-label counts match the current-season mid-lane population.
- A grouped `feature_matrix`/`cluster_labels` query returns exactly one row per cluster.

If every check passes, tick the task in `ROADMAP.md` and move on.
