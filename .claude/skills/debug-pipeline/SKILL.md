---
name: debug-pipeline
description: Triage a broken LoL analytics pipeline layer by layer. Use when a Riot API call fails (401/403/404), the match ID list comes back empty, the feature matrix has unexpected NULLs, DuckDB reports "column not found", Streamlit shows stale data, or a computed feature like the tilt index looks wrong.
---

# Debugging the pipeline

> **L2 Reference** · procedure: triage a broken pipeline · owner: Claude · update: when pipeline behavior changes

Work layer by layer from the earliest point in the data flow. Don't jump to assumptions.

**First: is the raw file there?** Check `data/raw/{match_id}.json`. If it exists, the API call succeeded — the problem is in `src/processor.py` or later. If it doesn't, the problem is in `src/collector.py` or the key.

**Second: what does the raw JSON actually say?** Open one file manually before touching any code. Riot responses nest participant data inside `info.participants[]` — a field you expect might be two levels deeper than assumed or named differently than the docs show.

**Third: isolate in a notebook.** Load the raw file, run the suspect function step by step. Far faster than adding print statements and re-running the full pipeline.

Common failure patterns:

| Symptom | Likely cause |
|---|---|
| HTTP 401 or 403 | API key rejected or expired — regenerate at `developer.riotgames.com` |
| HTTP 404 on match-v5 | Wrong routing host — must be `sea.api.riotgames.com` |
| Empty match ID list | Wrong PUUID, or no ranked games in the requested time window |
| NULL values in feature matrix | Field missing from raw JSON, or timeline lacks that exact minute |
| Streamlit shows stale data | `@st.cache_data` is holding old results — call `.clear()` or restart the server |
| DuckDB "column not found" | Schema in `init_schema()` is out of sync with what `src/processor.py` inserts |
| Tilt index looks wrong | Missing `.shift(1)` — current game result is leaking into its own feature |

If you're still stuck after all three steps:
- write what you tried in this session's `.claude/CONTEXT.md` entry;
- add a task for it in `ROADMAP.md`;
- move to a different task, and come back with fresh context.
