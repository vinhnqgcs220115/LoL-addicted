# Session Log

Purpose: preserve project continuity across chat sessions. Read this file at the start of each new session, after `.claude/CLAUDE.md` and `.claude/CONTEXT.md`, before proposing or editing anything.

## How To Use This File

- At session start: read `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/CONTEXT.md`, `.claude/COLLAB.md`, this file, and any target files. If the work touches gameplay labels, also read `GAME_MECHANICS.md`.
- During long sessions or before context compaction: update the active session entry with work completed, commands run, and unresolved decisions. Do not wait until the end if the thread is getting long.
- At session close: append or complete one dated entry. Record every separate bugfix, adjustment, doc change, data refresh, verification run, and open TODO created during the session.
- Keep entries factual. Include changed files, behavior changed, generated-data effects, verification results, and what remains open.
- Do not store secrets, Riot API keys, `.env` values, or raw private account details here.
- Do not duplicate full docs. Link or name the authoritative file instead: architecture in `CLAUDE.md`, project status in `CONTEXT.md`, mechanics in `GAME_MECHANICS.md`, workflow commands in `README.md` and `scripts/workflow.ps1`.

## Direction For Future Sessions

- The project is a single-summoner League of Legends ranked analytics app using Riot API raw JSON, DuckDB, feature engineering, K-Means, and Streamlit.
- Current product scope is Season 16 `MIDDLE` only. Collection and processing retain all roles, but analytics, feature matrix, model labels, deploy DB, and dashboard queries must stay scoped to mid unless all-role support is explicitly implemented.
- `src/collector.py` owns Riot API access and raw immutable JSON writes. `src/processor.py` owns parsing and database writes. `src/features.py` owns analytics logic. `src/models.py` owns clustering. `dashboard/app.py` should only render/query, not define feature logic.
- `src/models.py::FEATURE_COLS` is canonical. Do not derive model features from DataFrame columns.
- Dashboard labels around Throw, Comeback, Overextension, Deficit Fight, Post-Laning Throw, and roam impact are proxy labels. Do not present them as gameplay ground truth unless the code is changed to parse the required team/opponent/objective/vision state.
- `GAME_MECHANICS.md` is authoritative for mid-lane mechanics. Current known mismatch: code uses personal timeline proxies where true mechanics require fuller game state.
- Use `scripts/workflow.ps1` from the repo root. Commands stop on first failed native process. Run `.\scripts\workflow.ps1 test` and `python -m ruff check src tests dashboard scripts` or the equivalent `.venv` Python command before finishing code changes.
- Generated data matters. If collection, processing, features, models, deploy DB, or dashboard data changes, record counts and whether `data/lol_deploy.duckdb` was regenerated.

## Current Project Snapshot

Last verified on 2026-07-02 after running all workflow commands.

- Phase: Phase 4 implementation complete; Streamlit Cloud deployment still pending.
- Source DB: `data/lol.duckdb`, local/generated, gitignored.
- Deploy DB: `data/lol_deploy.duckdb`, committed deployment artifact, dashboard opens it read-only.
- Data counts: 522 matches total; 337 Season 16 mid rows; 15,523 timeline rows; 337 feature rows; 337 cluster labels.
- Cluster sizes: 169 / 54 / 7 / 107; silhouette 0.244.
- Deploy DB counts: 337 matches, 10,081 timeline rows, 2,658 death rows, 337 feature rows, 337 cluster labels.
- Tests: 52 passed. Ruff clean after latest Python changes.
- Dashboard: local health check passed on `http://localhost:8501/_stcore/health`; no server left running.
- Worktree at initialization had tracked edits in `.claude/CLAUDE.md`, `.claude/CONTEXT.md`, `README.md`, `data/lol_deploy.duckdb`, `src/collector.py`, `tests/test_collector.py`; untracked `GAME_MECHANICS.md` and `assets/`.

## Open Items

- Deploy to Streamlit Cloud, then update README live URL and screenshots.
- Before public presentation, rename or qualify proxy labels in dashboard UI: Throw, Comeback, Overextension, Deficit Fight, Post-Laning Throw, and roam impact.
- Do not name clusters until centroid and trajectory review supports the names. Cluster 2 has only 7 games, so avoid strong conclusions.
- Improve gameplay fidelity if needed: parse assists and objective events for roam impact; use opponent/team gold, XP, turret/objective state, position, and death context for throw/death labels; treat missing death snapshots as unknown, not zero-gold evidence.
- Pro comparison remains stretch work: KR/EUW routing, collect Challenger mid games, compare CS diff curve and roaming timing.
- All-role analytics remain future work and require role-aware opponent extraction, tests, and a full DuckDB rebuild.
- `GAME_MECHANICS.md` and `assets/` were untracked at initialization. Decide whether to commit them with the docs changes.

## Sessions

### 2026-07-02 - Mechanics docs, collector auth, workflow verification, session log bootstrap

Summary: reviewed the project against `GAME_MECHANICS.md`, updated docs to make proxy labels explicit, fixed Riot `401` auth handling, verified every workflow command, refreshed generated data, and initialized this session log.

Changes made:
- Added proxy caveats to `README.md`: dashboard labels are heuristic, not full team-state ground truth.
- Updated `.claude/CLAUDE.md`: dashboard is implemented, `GAME_MECHANICS.md` is authoritative for gameplay features, and user-facing proxy labels must be qualified or renamed.
- Updated `.claude/CONTEXT.md`: current counts, last verified status, workflow/dashboard verification, and non-blocking proxy-label known issue.
- Updated `GAME_MECHANICS.md`: objective timer verification date, observable-vs-inferred caveats, codebase implications for proxy labels, and open items for label renaming plus assist/objective parsing.
- Updated `src/collector.py`: Riot `401` and `403` now both raise a clear `PermissionError`; module CLI exits cleanly without a Python traceback for rejected API keys.
- Updated `tests/test_collector.py`: added regression coverage for `401 Unauthorized`.
- Refreshed `data/lol_deploy.duckdb` after final rebuild/deploy verification.
- Created `.claude/SESSIONS.md` as the cross-session project log.

Verification run:
- `.\scripts\workflow.ps1 help` passed.
- `.\scripts\workflow.ps1 sync` passed: checked 15 packages.
- `.\scripts\workflow.ps1 collect` passed: saved 9 new matches, skipped existing files.
- `.\scripts\workflow.ps1 process` passed: 522 match rows.
- `.\scripts\workflow.ps1 features` passed: 337 feature rows, 41 throw proxy games, 53 comeback proxy games.
- `.\scripts\workflow.ps1 models` passed: 337 labels, silhouette 0.244.
- `.\scripts\workflow.ps1 deploy-db` passed after running serially: 337 sanitized matches.
- `.\scripts\workflow.ps1 refresh` passed end-to-end.
- `.\scripts\workflow.ps1 smoke` passed: `{'matches': 522, 'timelines': 15523, 'features': 337, 'labels': 337}`.
- `.\scripts\workflow.ps1 dashboard` passed local health check at `/_stcore/health`.
- `.\scripts\workflow.ps1 rebuild` passed and recreated `data/lol.duckdb`.
- `.\scripts\workflow.ps1 test` passed: 52 tests.
- `.\.venv\Scripts\python.exe -m ruff check src tests` passed.

Notes:
- A first `deploy-db` attempt failed because it was run in parallel with `features`, causing a DuckDB file lock. Serial execution passed; do not run DB-writing workflow commands in parallel.
- Riot API key worked during final collection/smoke/refresh verification. It may expire later; regenerate at `developer.riotgames.com` if `401` or `403` returns.
- `apply_patch` was unavailable in this environment because the Windows sandbox helper was missing; file edits were applied with PowerShell writes under escalation.