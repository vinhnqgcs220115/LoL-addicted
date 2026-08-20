# Project Context

The only file in this repository that may contain project state — counts, metrics, dates, phase, or a done/not-done claim. Everything here must be verifiable against the tree or a stored artifact. Anything that cannot be verified is marked as such.

**Phase:** Phase 4 complete. Product definition and dashboard rework in progress.
**Last verified:** 2026-08-12

---

## Verified state

Verified 2026-08-12 by querying committed artifacts and running the suite in this repository.

| Check | Value | How verified |
|---|---|---|
| Deploy DB matches | 396 | query on `data/lol_deploy.duckdb` |
| Deploy DB timelines | 11,795 | same |
| Deploy DB deaths | 3,117 | same |
| Deploy DB roam windows | 84 | same |
| Deploy DB feature rows | 396 | same |
| Deploy DB cluster labels | 396 | same |
| Deploy DB cluster sizes | 188 / 73 / 128 / 7 | same |
| Deploy DB match date range | 2026-01-10 to 2026-07-18 | same |
| Tests | 75 passed | `pytest tests -q` |
| Lint | clean | `ruff check src tests dashboard scripts` |
| `models/cluster_centroids.json` | tracked | `git ls-files` |
| `data/lol_deploy.duckdb` | tracked, committed at `e4b8f07` | `git log` |
| Worktree at session start | clean | `git status` |

Local-only, gitignored, verified 2026-08-12 on this machine but not reproducible from the repository:

| Check | Value |
|---|---|
| `data/raw/` files | 1,188 (594 detail + 594 timeline) |
| Source DB matches / timelines / deaths | 594 / 17,566 / 4,743 |
| Source DB feature rows / labels | 396 / 396 |
| Source DB match date range | 2025-09-11 to 2026-07-18 |

Not verified since 2026-07-18 — treat as stale until re-run:

- Silhouette score 0.227.
- Live app at `https://myishaa.streamlit.app/` serving the current snapshot. The snapshot is committed; the deployment itself has not been loaded and checked since.
- The three files in `docs/screenshots/` predate the champion-icon and card UI.

---

## Open items

Ordered by dependency, from the 2026-08-12 pipeline audit. Stage 0 blocks stages 1-3.

**Ship immediately — blocked by nothing, no rebuild needed**

- U3 — sample-size gating. Verified 2026-08-12 against `champion_matchup_stats` on the deploy DB: 71 matchup pairs render, 46 receive a colored win-rate verdict chip at the 55% / 45% cut, 39 of those from 3 games or fewer, and 32 read exactly 0% or 100%. Only 5 pairs have 5 or more games. Patch rates run 5-60 games per patch with no interval; time-of-day the same.
- Quick win — `opp_gold_earned` is collected and stored on every match row and read by nothing. It is the only opponent-anchored gold figure available before D1 lands, and it yields a real end-of-game gold differential per matchup today with no reparse. Partially serves the `PRODUCT.md` section 4 baseline-comparison tier ahead of stage 0.
- U4 — rename or remove every mislabeled proxy. "Deaths while ahead", "Overextension", "Deficit Fight" all compare the player to their own season average, not to the opponent. `PRODUCT.md` section 8 violation as displayed.

**Stage 0 — the reparse. No Riot API calls. Blocks stages 1-3.**

- D1 — store all ten `participantFrames` per timeline frame instead of one. Verified 2026-08-12 against `tests/fixtures/sample_match_timeline.json`: every frame carries all ten participants with `totalGold`, `xp`, `minionsKilled`, `level`, and `position`. Unlocks a true per-minute lane differential and retires every self-referential baseline in the project.
- D2 — parse the timeline event stream. One representative match carries 61 `CHAMPION_KILL` (with `position`, `killerId`, `assistingParticipantIds`), 126 `WARD_PLACED`, 60 `TURRET_PLATE_DESTROYED`, 15 `BUILDING_KILL`, 9 `ELITE_MONSTER_KILL`. `extract_death_rows()` reads the kill event and keeps only its timestamp.
- Cost for D1 + D2 together: `processor.py` parsing, schema change, `_assert_table_columns` update, new fixtures and tests, full `rebuild`, `FEATURE_MATRIX_COLUMNS` update in `build_deploy_db.py` (raises on drift by design), re-verified deploy snapshot. No collection, no key, no rate limit.

**Stage 1 — honest features. Blocked by stage 0.**

- D3 — fix roam detection. Verified 2026-08-12 by re-running the detector over the deploy DB: the `len(block) < 2` guard in `roam_timing()` alone accounts for the entire shortfall. Minimum contiguous minutes of 1 yields 308 of 390 games and 513 windows; the current value of 2 yields 81 games and 84 windows, exactly what is persisted; 3 yields 15. Riot samples once per minute and a mid roam takes 30-60 seconds, so the typical roam occupies one frame. Replace contiguity with a position-change threshold or corroboration from a kill/assist event.
- D4 — redefine Throw and Comeback on real opponent gold difference at minute 14, or rename them. Current definition is gold at 14 versus the player's own season mean crossed with the result.
- Replace every self-referential "lead" with the true lane differential.
- Deaths by map region, now that death position exists.

**Stage 2 — model decision. Blocked by stage 1.**

- D5 — rebuild the feature set. `total_deaths`, `tilt_spiral_ratio`, and `max_death_streak` correlate pairwise at r = 0.75-0.82, so K-Means is close to one-dimensional on death count. `roam_impact_rate` is the neutral fill value 0.5 in 318 of 396 rows. Reconsider whether `tilt_index`, a rolling win rate of prior games, belongs in a model meant to describe in-game behavior.
- M1 — decide whether K-Means survives. Cluster win rates are 76.6% / 50.7% / 34.6% against `total_deaths` z-scores of -1.03 / +0.22 / +0.60, so the clusters restate "you lose the games where you die more". `PRODUCT.md` section 8 requires interpretation to be earned. User decision, not an agent default.

**Stage 3 — dashboard rebuild. Blocked by stage 1; U1's narrative layer by stage 2.**

- U1 — game list and match detail view. `PRODUCT.md` 30-second test sentence 3 and done-criterion 5 both require the player to leave knowing which games to rewatch; there is currently no game list, no match detail, and no path from a pattern back to its games. Zero coverage, largest single product gap. `src/mapping.py` and the minimap assets already exist and are tested but are imported by nothing outside `tests/test_mapping.py`; `roam_windows` and per-minute `position_x`/`position_y` ship in the deploy DB and are queried by no dashboard code. **Privacy flag:** the known-issue below accepts `game_datetime` retention in the deploy DB as a portfolio-scale risk, but that assessment predates any per-game view. A dated game list plus champion plus patch is materially more identifying than a season aggregate. Not a blocker and not an agent decision — decide it before U1 ships, not after.
- U2 — every tab opens with a conclusion, evidence second, raw numbers as reference.
- U5 — demote the OP.GG-parity surface to a labeled reference strip.
- U6 — rebuild Champions around champion class buckets rather than pairs.

**Independent — blocked by nothing, needs one user decision**

- D6 — champion class mapping. Riot Data Dragon tags are coarser than "control mage" and "early-pressure assassin"; the category list is a product decision.

**Housekeeping**

- Confirm the two `UNCONFIRMED` reconstructions in `PRODUCT.md` and supply the two `<FILL IN>` fragments lost in the source paste: the UI evaluation question ("Can a player understand t...") and the body of the "Personal-first Scope" section.
- Recapture `docs/screenshots/` after the dashboard rework, not before.
- Re-verify the live deployment and record the result here.

## Known issues

Accepted limitations. Not scheduled work.

- Throw, Comeback, Overextension, Deficit Fight, Post-Laning Throw, and roam-impact metrics are heuristic proxies from single-player timeline data. The UI qualifies them. True ground truth needs fuller team, opponent, objective, and vision state.
- Cluster 3 (n=7) is an outlier bucket, not an under-sampled archetype. Its defining feature `avg_cs_sacrifice` sits at z = +7.01, the signature of the roam detector misfiring rather than of a behavior pattern awaiting more games. Corrected 2026-08-12; the previous entry recorded it as deliberately uncharacterized. Clusters 0/1/2 are named from centroid review and are subject to the M1 decision above.
- The centroid-binding guard has no absolute-distance cutoff. It refuses to persist a retrain whenever any cluster's centroid is no longer nearest its own previously-named centroid — including a clean bijective permutation — and performs no remapping.
- `game_datetime` is retained in the deploy DB. Timestamps plus champion and version data could identify matches on public sites; accepted for a portfolio project.

## Backlog

Not part of the definition of done. May be abandoned without ceremony.

- Pro comparison: KR/EUW routing in `collector.py`, collect ranked mid games from 3–5 Challenger mids, compare CS-diff curve and roam timing on shared champions.
- All-role analytics: role-aware opponent extraction, direct tests, full DuckDB rebuild.

---

## Decisions log

| Decision | Rationale |
|---|---|
| DuckDB over SQLite | Window functions and analytical queries without a server |
| K-Means over XGBoost | Win predictor removed; clustering behavioral aggregates does not benefit from gradient boosting |
| Cluster names follow centroid review | Pre-naming would imply unsupported behavior |
| Clusters 0/1/2 named; cluster 3 left numeric | n=7 is too small to support a name |
| K-Means IDs guarded, not aligned, before persistence | Numeric IDs are arbitrary; the guard rejects a drifted binding rather than remapping it |
| Plotly over Matplotlib | Interactive charts required in Streamlit |
| `requests` over `httpx` | Sync is sufficient at this data scale; simpler API |
| Ranked Solo/Duo only (queue 420) | Cleaner signal; removes ARAM and normal-queue noise |
| Raw JSON saved before processing | Allows re-processing without re-hitting the API |
| Predictor tab removed | Manual input form has no use case during or after a game |
| Win predictor model removed | Output was not surfaceable usefully; clustering is sufficient |
| EDA refocused to death context, throw detection, roaming | More differentiated from OP.GG; answers "what am I doing wrong" |
| Season 16 filter on the feature matrix | S15 gold rates differ; mixed-era baselines distort `gold_lead_approx` and `gold_delta` |
| Analytics are mid-only | Personal and time-boxed; off-role games stay collected for future expansion |
| `tilt_index` scoped to S16 mid | Consistent with `ANALYSIS_ROLE`; loses S15 rolling context for the first S16 games |
| Dashboard derives cluster means from DuckDB | `models/*.pkl` stay local and gitignored |
| Deployment uses committed `data/lol_deploy.duckdb` | Streamlit Cloud has no persistent disk; S3 or LFS adds infra for under 10 MB |
| Gameplay labels stay heuristic until full state is parsed | `GAME_MECHANICS.md` owns the domain caveats |
| Session log deleted, 2026-08-12 | `.claude/SESSIONS.md` accumulated superseded counts and corrections that stayed wrong in place, and contradicted the tree on three items. `git log` is the history; this file is the state |
| Claude web scoped to domain input only, 2026-08-12 | A planner without repository access must be hand-fed context, and hand-fed context is what drifted across sessions |
| Personal-first over portfolio-first, 2026-08-12 | Primary user is the player reviewing their own games. Portfolio value follows from a tool that genuinely serves its one user; it does not follow from statistic accumulation. `PRODUCT.md` section 1 is authoritative |
| Insight hierarchy is the UI acceptance test, 2026-08-12 | Elements must reach layer 4 or higher, or be explicitly framed as reference rather than as a finding. Replaces "is this chart nice" with a checkable criterion. `PRODUCT.md` section 4 is authoritative |

---

## Deployment

Two DuckDB files:

- `data/lol.duckdb` — development, gitignored, rebuilt locally from raw JSON.
- `data/lol_deploy.duckdb` — production read-only artifact, committed, opened read-only by the dashboard.

To update deployed data: verify `lol.duckdb`, run `.\scripts\workflow.ps1 deploy-db`, review residual re-identification risk, then commit the generated file.

## Notes

- Vietnam routing: `asia` for account-v1, `sea` for match-v5.
- Free API key expires every 24 hours; regenerate at `developer.riotgames.com`.
- Summoner identity is `GameName#TAG`; PUUID is fetched once and stored in `.env`.
