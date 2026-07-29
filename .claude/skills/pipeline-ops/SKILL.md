---
name: pipeline-ops
description: Run and verify the LoL analytics pipeline. Use when collecting new matches, reprocessing DuckDB from scratch, adding a new field from the Riot API, building the deployment snapshot, or verifying DuckDB after an ingestion run.
---

# Pipeline operations

**Adding new matches** — re-run `collector.py`. It skips files that already exist in `data/raw/`, so it is safe to run repeatedly.

**Reprocessing from scratch** — run `.\scripts\workflow.ps1 rebuild`. It recreates `data/lol.duckdb` from raw files, then rebuilds features and models. Raw files are untouched; no API calls are made.

**Adding a new field from the API** — verify the field exists in an actual raw JSON file before touching any code. Then add parsing in `processor.py`, update the schema in `init_schema()`, and run the rebuild workflow. Never edit files in `data/raw/`.

**Deployment snapshot** — after tests and DuckDB verification pass, run `.\scripts\workflow.ps1 deploy-db`. The dashboard reads `data/lol_deploy.duckdb` read-only. Review public-data exposure before committing the snapshot.

## Verifying DuckDB after an ingestion run

After every ingestion run, verify DuckDB before moving forward. The minimum checks:

- Row count matches how many files are in `data/raw/`
- No NULL values in `win`, `match_id`, or `champion_name`
- `MIN` and `MAX` of `game_datetime` fall within an expected range
- `match_timelines` row count is roughly `matches count × average game duration in minutes`
- Feature and cluster-label counts match the current Season 16 mid-lane population
- A grouped `feature_matrix`/`cluster_labels` query returns exactly one row per cluster

If all pass, mark the task done in `CONTEXT.md` and move on.
