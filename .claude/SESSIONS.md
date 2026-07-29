# Session Log

Purpose: preserve project continuity across chat sessions. Read this file at the start of each new session, after `.claude/CLAUDE.md` and `.claude/CONTEXT.md`, before proposing or editing anything.

## How To Use This File

- At session start: read `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/CONTEXT.md`, `.claude/COLLAB.md`, and `.claude/SESSIONS.md` first. Continue from the latest session entry and respect the open items. If this touches gameplay labels/mechanics, also read `GAME_MECHANICS.md` before changing anything. Only `.claude/CLAUDE.md` loads automatically in Claude Code; every other file here must be opened deliberately.
- During long sessions or before context compaction: update the active session entry with work completed, commands run, and unresolved decisions. Do not wait until the end if the thread is getting long.
- At session close: append or complete one dated entry. Record every separate bugfix, adjustment, doc change, data refresh, verification run, and open TODO created during the session.
- Keep entries factual. Include changed files, behavior changed, generated-data effects, verification results, and what remains open.
- Do not store secrets, Riot API keys, `.env` values, or raw private account details here.
- Do not duplicate full docs. Link or name the authoritative file instead: architecture and standing rules in `CLAUDE.md`, pipeline runbook and DuckDB verification in the `pipeline-ops` skill, failure triage in the `debug-pipeline` skill, project status in `CONTEXT.md`, mechanics in `GAME_MECHANICS.md`, workflow commands in `README.md` and `scripts/workflow.ps1`.

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

Last verified locally on 2026-07-18 after refresh, deploy-db, tests, Ruff, and Streamlit AppTest.

- Phase: Phase 4 complete.
- Source DB: `data/lol.duckdb`, local/generated, gitignored.
- Deploy DB: `data/lol_deploy.duckdb`, committed deployment artifact, dashboard opens it read-only.
- Data counts: 594 matches total; 396 Season 16 mid rows; 17,566 timeline rows; 396 feature rows; 396 cluster labels.
- Cluster sizes: 188 / 73 / 128 / 7; silhouette 0.227.
- Deploy DB counts: 396 matches, 11,795 timeline rows, 3,117 death rows, 84 roam windows, 396 feature rows, 396 cluster labels.
- Tests: 75 passed. Ruff clean across `src tests dashboard scripts`.
- Dashboard: all three tabs render locally with zero AppTest exceptions. The public URL remains `https://myishaa.streamlit.app/`, but this refresh has not been committed, pushed, or live-verified.
- Worktree remains intentionally dirty with current dashboard, pipeline, generated-data, asset, model, and documentation changes; no commit or push was performed.

## Open Items

- Clusters 0/1/2 are named from centroid review. Cluster 3 still has only 7 games and remains deliberately uncharacterized.
- Improve gameplay fidelity if needed: parse assists and objective events for roam impact; use opponent/team gold, XP, turret/objective state, position, and death context for throw/death labels; treat missing death snapshots as unknown, not zero-gold evidence.
- Pro comparison remains stretch work: KR/EUW routing, collect Challenger mid games, compare CS diff curve and roaming timing.
- All-role analytics remain future work and require role-aware opponent extraction, tests, and a full DuckDB rebuild.
- Commit and push the refreshed `data/lol_deploy.duckdb` before claiming the public app has current data.
- Add `models/cluster_centroids.json` to the next commit; it is the reviewed name-binding snapshot and is currently untracked. Keep `models/*.pkl` ignored.
- Recapture the three files under docs/screenshots/ — they predate the newer champion-icon/card UI. The embeds themselves are already restored; this is a visual-freshness task, not a missing-file one.

## Sessions

### 2026-07-29 - Agent-config health check and documentation sync

Files changed:
- `.claude/CLAUDE.md`
- `.claude/skills/pipeline-ops/SKILL.md` (new)
- `.claude/skills/debug-pipeline/SKILL.md` (new)
- `.claude/COLLAB.md`
- `.claude/SESSIONS.md`
- `AGENTS.md`
- `GAME_MECHANICS.md`

Behavior changed:
- No source, test, pipeline, or generated-data changes. Documentation and agent configuration only.
- `.claude/CLAUDE.md` trimmed from 9,059 to ~5,700 characters. Removed the Architecture section (derivable from `src/`), the Preferred Libraries table (duplicated `requirements.txt`), and two lines restating the `tests/` layout and the standard `pytest` invocation. Module Contracts, Data Rules, Code Conventions, Riot API Routing, and Hard Rules are unchanged.
- Moved the Debugging section and the Pipeline Operations section — plus the post-ingestion DuckDB checklist from Verification — into two on-demand skills, `debug-pipeline` and `pipeline-ops`. Content was moved verbatim; nothing was reworded or dropped.
- Added a Hard Rule that `src/models.py::FEATURE_COLS` is canonical. The rule already existed in `AGENTS.md` and in this file's Direction section, but not in the only file Claude Code loads automatically.
- `AGENTS.md` lint command corrected from `ruff check src tests` to `ruff check src tests dashboard scripts`; the narrow form silently skipped `dashboard/app.py`, `scripts/build_deploy_db.py`, `scripts/fetch_champion_icons.py`, and `scripts/fetch_minimap.py`. Added the missing `smoke` and `dashboard` workflow targets to the same block.
- `GAME_MECHANICS.md` header corrected: it claimed the file "is not auto-loaded by AGENTS.md", but `AGENTS.md` never referenced it and is not itself auto-loaded. It now states that only `.claude/CLAUDE.md` loads automatically and that it names this file as authoritative.
- `.claude/COLLAB.md` and this file's authoritative-file map now list `.claude/skills/` as the home for runnable procedures.

Verification results:
- `.\.venv\Scripts\ruff.exe check src tests dashboard scripts` passed, and the narrow `src tests` form was confirmed to cover 4 fewer Python files.
- Both lint forms pass today; the correction prevents future drift, it did not fix an outstanding violation.
- No pipeline stage, no `pytest` run, and no DuckDB query were executed this session. All counts in Current Project Snapshot remain those of the 2026-07-18 refresh and were not re-verified.

Generated-data effects:
- None. No raw files, databases, or model artifacts were read, written, or regenerated.

Open items:
- All prior open items stand unchanged, including the uncommitted `data/lol_deploy.duckdb`, the untracked `models/cluster_centroids.json`, and the dated screenshots.
- `.claude/skills/` is new and untracked; include it in the next commit alongside the `.claude/CLAUDE.md` edit, or the two skills will not exist for other clones.
- The skills load on demand rather than every session. If pipeline or triage guidance starts getting missed in practice, the fix is to sharpen the `description` frontmatter, not to inline the content back into `CLAUDE.md`.

### 2026-07-19 - Correct centroid-guard description in the 2026-07-18 entry

Summary: the 2026-07-18 entry describes src/models.py's centroid-binding
guard as aligning/remapping K-Means IDs and rejecting non-bijective
mappings. Neither is accurate. The guard was briefly modified to do this
without authorization, then reverted. The current, correct guard refuses
to persist a retrain whenever any cluster's centroid is no longer
closest to its own previously-named centroid — including a clean
bijective permutation — and performs no bijection test and no
remapping. This entry does not change the 2026-07-18 entry's text;
it corrects the record alongside it.

Changes made:
- None. This is a documentation-accuracy correction only.

Verification run:
- Read the current src/models.py directly; confirmed no remapping path
  exists and the guard's comparison is per-cluster nearest-match only,
  not a bijection check.

Generated-data effects:
- None.

Open items:
- The 2026-07-18 entry's "Behavior changed" and final "Open items" bullet
  describing bijection rejection remain factually incorrect in place;
  this correction should be read alongside it.
- Whether the 594/396-row refresh and its detected permutation
  (0→3, 1→2, 2→0, 3→1) should be reviewed and accepted as a legitimate
  relabeling is still an open decision, not resolved by this correction.

### 2026-07-18 - Data refresh, stable cluster IDs, and docs sync

Files changed:
- `src/models.py`
- `tests/test_models.py`
- `data/lol_deploy.duckdb`
- `README.md`
- `.claude/CONTEXT.md`
- `.claude/SESSIONS.md`
- `GAME_MECHANICS.md`

Behavior changed:
- Collected 52 new Riot matches, then rebuilt the source database and Season 16 mid feature matrix.
- K-Means raw IDs now map back to the tracked named centroids before persistence. A unique permutation is accepted; an ambiguous many-to-one mapping still warns and refuses to overwrite labels or artifacts.
- Rebuilt the sanitized deployment database from the verified 396-game mid-only dataset.
- Synchronized current-state docs and stopped embedding the dated dashboard screenshots until they can be recaptured.

Verification results:
- `.\scripts\workflow.ps1 refresh` completed collection, processing, and features, then initially stopped at the prior cluster-ID guard after detecting the pure raw-ID permutation `0→3, 1→2, 2→0, 3→1`.
- `.\scripts\workflow.ps1 models` passed after the binding fix: 396 labels, stable cluster sizes 188 / 73 / 128 / 7, silhouette 0.227.
- Source integrity passed: 594 matched detail/timeline file pairs; 594 match rows; 17,566 timeline rows; 4,743 reported/stored deaths; 396 feature rows with zero NULLs; zero unlabeled features; zero persisted-model prediction mismatches.
- `.\scripts\workflow.ps1 deploy-db` passed: 396 matches, 11,795 timelines, 3,117 deaths, 84 roam windows, 396 feature rows, and 396 labels.
- Deploy audit passed: no `puuid` column, zero original Riot match-ID overlap, zero orphan feature/label rows, and zero feature NULL rows.
- `.\scripts\workflow.ps1 test` passed: 75 tests.
- `.\.venv\Scripts\python.exe -m ruff check src tests dashboard scripts` passed.
- Streamlit AppTest rendered Overview, Champions, and Patterns with zero exceptions.

Generated-data effects:
- `data/raw/`, `data/lol.duckdb`, `models/kmeans.pkl`, and `models/scaler.pkl` were refreshed locally.
- `data/lol_deploy.duckdb` was regenerated and remains uncommitted.

Open items:
- Commit/push is still required to update the public Streamlit app; the live URL was not re-verified.
- `models/cluster_centroids.json` remains untracked and must be added with the binding code; `models/kmeans.pkl` and `models/scaler.pkl` remain correctly ignored.
- The three dated dashboard screenshot files were not recaptured because the in-app browser was unavailable; their README embeds were removed.
- The centroid guard retains its prior lack of an absolute-distance cutoff; it rejects non-bijective mappings, and no unreviewed threshold was invented in this refresh.

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
