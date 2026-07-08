# Session Log

Purpose: preserve project continuity across chat sessions. Read this file at the start of each new session, after `.claude/CLAUDE.md` and `.claude/CONTEXT.md`, before proposing or editing anything.

## How To Use This File

- At session start: read `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/CONTEXT.md`, `.claude/COLLAB.md`, and `.claude/SESSIONS.md` first. Continue from the latest session entry and respect the open items. If this touches gameplay labels/mechanics, also read `GAME_MECHANICS.md` before changing anything.
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

Last verified on 2026-07-05 after refresh, deploy-db, tests, and Ruff.

- Phase: Phase 4 complete.
- Source DB: `data/lol.duckdb`, local/generated, gitignored.
- Deploy DB: `data/lol_deploy.duckdb`, committed deployment artifact, dashboard opens it read-only.
- Data counts: 542 matches total; 354 Season 16 mid rows; 16,080 timeline rows; 354 feature rows; 354 cluster labels.
- Cluster sizes: 175 / 60 / 112 / 7; silhouette 0.243.
- Deploy DB counts: 354 matches, 10,573 timeline rows, 2,775 death rows, 354 feature rows, 354 cluster labels.
- Tests: 52 passed. Ruff clean after latest Python changes.
- Dashboard: public app verified at `https://myishaa.streamlit.app/`; refreshed deploy DB was committed/pushed on `main` at `db5a55a`.
- Worktree at initialization had tracked edits in `.claude/CLAUDE.md`, `.claude/CONTEXT.md`, `README.md`, `data/lol_deploy.duckdb`, `src/collector.py`, `tests/test_collector.py`; untracked `GAME_MECHANICS.md` and `assets/`.

## Open Items

- Do not name clusters until centroid and trajectory review supports the names. Cluster 3 has only 7 games, so avoid strong conclusions.
- Improve gameplay fidelity if needed: parse assists and objective events for roam impact; use opponent/team gold, XP, turret/objective state, position, and death context for throw/death labels; treat missing death snapshots as unknown, not zero-gold evidence.
- Pro comparison remains stretch work: KR/EUW routing, collect Challenger mid games, compare CS diff curve and roaming timing.
- All-role analytics remain future work and require role-aware opponent extraction, tests, and a full DuckDB rebuild.
- `GAME_MECHANICS.md` and `assets/` were untracked at initialization. Decide whether to commit them with the docs changes.

## Sessions

### 2026-07-07 - Hardcode deploy feature matrix columns

Files changed:
- `scripts/build_deploy_db.py`
- `tests/test_build_deploy_db.py`
- `data/lol_deploy.duckdb`
- `.claude/SESSIONS.md`

Behavior changed:
- Deploy DB feature_matrix publishing now uses a fixed `FEATURE_MATRIX_COLUMNS` tuple kept in sync with `src.features.build_feature_matrix()` instead of deriving output columns from `DESCRIBE source.feature_matrix`.
- `build_deploy_db.py` now compares the fixed tuple against `source.feature_matrix` and raises with missing/unexpected column names before publishing on drift.
- Added a regression test proving an extra source feature column raises instead of silently appearing in the deploy DB.

Verification results:
- `pytest tests/test_build_deploy_db.py -q` failed in this shell with `ModuleNotFoundError: No module named 'scripts'` before setting `PYTHONPATH`.
- `$env:PYTHONPATH = (Get-Location).Path; pytest tests/test_build_deploy_db.py -q` passed: 1 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_build_deploy_db.py -q` passed: 1 passed.
- `.\scripts\workflow.ps1 deploy-db` passed: matches=354, match_timelines=10573, match_deaths=2775, feature_matrix=354, cluster_labels=354.
- `DESCRIBE feature_matrix` before and after deploy-db matched the same 19 columns in the same order.
- `.\.venv\Scripts\python.exe -m ruff check scripts tests\test_build_deploy_db.py` passed: all checks passed.
- `git diff --check` passed with LF-to-CRLF normalization warnings only.

Generated-data effects:
- `data/lol_deploy.duckdb` was regenerated by `workflow.ps1 deploy-db`; row counts are unchanged from the current deploy snapshot.

Open items:
- None for this fix.

### 2026-07-06 - Display-name, dependency-fragility, and dead-path fixes

Files changed:
- `dashboard/app.py`
- `scripts/build_deploy_db.py`
- `src/collector.py`
- `tests/test_collector.py`
- `tests/test_features.py`
- `tests/test_models.py`

Behavior changed:
- Dashboard cluster feature labels now cover the remaining displayed feature columns instead of falling back to raw names.
- Deploy DB feature-matrix copying replaced `SELECT * EXCLUDE (match_id)` with a DESCRIBE-based dynamic column enumeration. This does not close the explicit-columns gap: a simulation with an injected extra column confirmed it still publishes automatically with no review checkpoint. Real fix (hardcoded, human-maintained column list with a mismatch check) is scoped and not yet implemented.
- Collector connection-error retry pacing is documented and directly asserted in tests.
- Roam timing has regression coverage for the CS-drop fallback path when position data is missing.
- Model profile comparison ignores index type only, keeping column and value checks intact.

Verification results:
- `$env:PYTHONPATH = (Get-Location).Path; pytest tests -q` passed on rerun: 54 passed.
- `.\.venv\Scripts\python.exe -m pytest tests -q` passed: 54 passed.
- `.\.venv\Scripts\python.exe -m ruff check src tests` passed: all checks passed.
- `git diff --check` passed with LF-to-CRLF normalization warnings only.

Generated-data effects:
- None. No DuckDB, raw data, feature, model, or deploy DB files were regenerated.

Open items:
- build_deploy_db.py's feature_matrix column list still needs to be a fixed, hardcoded tuple with an explicit mismatch check — DESCRIBE-based enumeration doesn't provide it. See CONTEXT.md / this thread for the scoped prompt.

### 2026-07-06 - DuckDB schema drift check

Summary: made `processor.init_schema()` fail loudly when an existing DuckDB table column-name set no longer matches the code-declared table columns.

Changes made:
- Updated `src/processor.py`: added `SchemaMismatchError` and column-name set validation after each `CREATE TABLE IF NOT EXISTS` in `init_schema()`.
- Updated `tests/test_processor.py`: added regression coverage for a pre-existing `matches` table missing `opp_assists`.
- Left all `CREATE TABLE IF NOT EXISTS` column lists unchanged; no migration/type/order validation was added.

Verification run:
- `pytest tests/test_processor.py -q` failed in this shell with `ModuleNotFoundError: No module named 'src'` before setting `PYTHONPATH`.
- `$env:PYTHONPATH = (Get-Location).Path; pytest tests/test_processor.py -q` passed: 17 passed.
- `$env:PYTHONPATH = (Get-Location).Path; pytest tests -q` passed on rerun: 54 passed.
- `.\.venv\Scripts\python.exe -m pytest tests/test_processor.py -q` passed: 17 passed.
- `.\.venv\Scripts\python.exe -m pytest tests -q` passed: 54 passed.
- `.\.venv\Scripts\python.exe -m ruff check src tests` passed: all checks passed.
- `git diff --check` passed; Git printed existing LF-to-CRLF normalization warnings for touched/dirty files.

Generated-data effects:
- None. No DuckDB, raw data, feature, model, or deploy DB changes.

Open items:
- Bare global `pytest` still needs repo root on `PYTHONPATH` in this shell; the project `.venv` Python path works.
- Full-suite count is 54, not the prompt expectation of 53; this repo currently collects 54 tests after adding this regression test.

### 2026-07-06 - Remove phantom documentation audit entry

Summary: removed session entry that claimed documentation edits which were not present in the actual file state.

Changes made:
- Replaced the false `2026-07-06 - Documentation audit corrections` entry in `.claude/SESSIONS.md` with this correction entry.
- No changes were made to `AGENTS.md`, `README.md`, `.claude/CLAUDE.md`, `.claude/COLLAB.md`, `.claude/CONTEXT.md`, or `GAME_MECHANICS.md` in this correction.

Verification run:
- Before this edit, `git status --short` and `git diff --stat` showed a clean worktree; the false entry was already in the committed tree.
- Read `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/CONTEXT.md`, `.claude/COLLAB.md`, and `.claude/SESSIONS.md` before changing the log.
- No tests run; session-log-only correction.

Generated-data effects:
- None.

Open items:
- Cluster names remain blocked on centroid and trajectory review; cluster 3 has only 7 games.
- Gameplay fidelity remains future work: parse assists/objectives and fuller team/opponent/objective/vision state before treating proxy labels as ground truth.

### 2026-07-05 - Data refresh and deploy snapshot update

Summary: refreshed Riot data, rebuilt processed data/features/models, rebuilt the deployment DB, and verified tests/lint for the current audit baseline.

Changes made:
- Refreshed raw/local generated data: 20 new matches saved; source DB now has 542 matches.
- Rebuilt feature matrix and clusters: 354 Season 16 mid rows, 354 cluster labels, silhouette 0.243, cluster sizes 175 / 60 / 112 / 7.
- Rebuilt `data/lol_deploy.duckdb`: 354 sanitized matches, 10,573 timeline rows, 2,775 death rows, 354 feature rows, 354 cluster labels, 0 original Riot match IDs.
- Updated `.claude/CONTEXT.md` and `.claude/SESSIONS.md` with refreshed counts.

Verification run:
- `workflow.ps1 refresh` passed: 20 new matches saved, processed 542 matches, wrote 354 cluster labels.
- `workflow.ps1 deploy-db` passed: 354 sanitized matches.
- DuckDB verification passed: win/match_id/champion_name NULLs all 0; death attribution reported=4,320, stored=4,320, mismatched matches=0; feature NULL rows=0.
- `python -m ruff check src tests dashboard scripts` passed.
- `workflow.ps1 test` passed: 52 tests.

Generated-data effects:
- `data/lol.duckdb`, `models/kmeans.pkl`, `models/scaler.pkl`, and `data/raw/` changed locally but are gitignored.
- `data/lol_deploy.duckdb` changed in this session and was later committed/pushed on `main` at `db5a55a`.

Open items:
- Cluster names remain blocked on centroid and trajectory review; cluster 3 has only 7 games.
- Gameplay fidelity remains future work: parse assists/objectives and fuller team/opponent/objective/vision state before treating proxy labels as ground truth.

### 2026-07-05 - Phase 4 closed without screenshots

Summary: README screenshots were dropped as a Phase 4 requirement; the deployed app and live URL are sufficient for current progress.

Changes made:
- Updated `.claude/CONTEXT.md`: marked Phase 4 complete and recorded the screenshot-skip decision.
- Updated `.claude/SESSIONS.md`: removed screenshot TODOs from open items and recorded this closeout.

Verification run:
- No tests run; documentation/status-only change.

Generated-data effects:
- None. No DuckDB, raw data, feature, model, or deploy DB changes.

Open items:
- Cluster names remain blocked on centroid and trajectory review; cluster 3 still has only 7 games.
- Gameplay fidelity remains future work: parse assists/objectives and fuller team/opponent/objective/vision state before treating proxy labels as ground truth.

### 2026-07-05 - Streamlit Cloud deployment verified

Summary: public Streamlit deployment is live at `https://myishaa.streamlit.app/` and accessible after a transient wake attempt.

Changes made:
- Updated `README.md`: added the live deployed app URL.
- Updated `.claude/CONTEXT.md`: marked Streamlit Cloud deployment complete, recorded the live URL, and split README screenshots into the remaining open item.
- Updated `.claude/SESSIONS.md`: recorded deployment verification and updated open items.

Verification run:
- User verified `https://myishaa.streamlit.app/` loads normally in browser/incognito after wake.
- Streamlit Cloud logs showed repository clone and dependency installation only; no app traceback was reported.
- No tests run; documentation/status-only change.

Generated-data effects:
- None. No DuckDB, raw data, feature, model, or deploy DB changes.

Open items:
- Cluster names remain blocked on centroid and trajectory review; cluster 3 still has only 7 games.
- Gameplay fidelity remains future work: parse assists/objectives and fuller team/opponent/objective/vision state before treating proxy labels as ground truth.

### 2026-07-02 - Dashboard proxy-label qualification

Summary: qualified dashboard-facing heuristic labels so proxy metrics are not presented as gameplay ground truth.

Changes made:
- Updated `dashboard/app.py`: Throw/Comeback summary now says Estimated; proxy captions were added; death-context proxy categories are labelled; cluster heatmap labels qualify gold/roam proxy features.
- Updated `.claude/CONTEXT.md`: known issue now tracks the underlying fidelity gap, not unfinished UI wording.
- Updated `.claude/SESSIONS.md`: removed the completed label-qualification open item and recorded this handoff.

Verification run:
- `.\scripts\workflow.ps1 test` passed: 52 tests.
- `.\.venv\Scripts\python.exe -m ruff check src tests dashboard scripts` passed.
- `.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('dashboard/app.py')"` passed; Streamlit emitted expected bare-mode warnings.
- `.\scripts\workflow.ps1 dashboard` timed out because it starts an interactive Streamlit server and blocks; stopped the two `streamlit run dashboard\app.py` Python processes it left running.

Generated-data effects:
- None. No DuckDB, raw data, feature, model, or deploy DB changes.

Open items:
- Gameplay fidelity remains future work: parse assists/objectives for roam impact and fuller team/opponent/objective/vision state for true throw/death labels.
- Cluster names remain blocked on centroid and trajectory review; cluster 3 still has only 7 games.

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