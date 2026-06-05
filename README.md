# LOL Ranked Analytics

Single-summoner League of Legends ranked analytics project built around the Riot Games API, raw JSON persistence, DuckDB processing, and a Streamlit dashboard.

## UV Workflow

This repo uses the local virtual environment at `.venv` and installs dependencies with `uv pip`.

From the repo root, use the workflow script:

```powershell
.\scripts\workflow.ps1 sync
.\scripts\workflow.ps1 collect
.\scripts\workflow.ps1 process
.\scripts\workflow.ps1 refresh
.\scripts\workflow.ps1 test
.\scripts\workflow.ps1 smoke
.\scripts\workflow.ps1 status
```

What each command does:

- `sync` activates `.venv\Scripts\Activate.ps1` and runs `uv pip install -r requirements.txt`
- `collect` runs the Riot API collector in `src.collector`
- `process` parses `data/raw/` into `data/lol.duckdb`
- `refresh` runs collection and then processing in sequence
- `test` runs `pytest` against the fixture-backed test suite in `tests/`
- `smoke` runs a small live collection (`count=5`), processes the current raw dataset, and prints DuckDB counts
- `status` shows whether the repo `.venv` is currently active by checking `$env:VIRTUAL_ENV`

## Terminal Activation

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
python -m src.collector
python -m src.processor
python -m pytest tests -q
```