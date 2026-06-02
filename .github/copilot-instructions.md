# LOL Ranked Analytics

Personal DS portfolio project — analyzing ranked LoL performance via the official Riot Games API. Single-summoner scope, no real-time in-game interaction. End product: a live Streamlit dashboard deployed on Streamlit Cloud.

## Module Contracts

Each module owns exactly one layer. Never reach across.

| Module | Owns | Never |
|---|---|---|
| `collector.py` | Riot API calls, rate limiting, raw JSON persistence | Transform or parse data |
| `processor.py` | Parse raw JSON, insert to DuckDB | Call external APIs |
| `features.py` | Compute features from DuckDB tables | Read `data/raw/` directly |
| `models.py` | Train, evaluate, save models | Build features or call APIs |
| `dashboard/app.py` | Streamlit rendering | Contain business logic |