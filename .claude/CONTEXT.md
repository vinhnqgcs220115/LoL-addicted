# Project Context

The only file in this repository that may contain project state — counts, metrics, dates, phase, or a done/not-done claim. Everything here must be verifiable against the tree or a stored artifact. Anything that cannot be verified is marked as such.

**Phase:** Phase 4 complete. Product definition and dashboard rework in progress.
**Last verified:** 2026-08-12

---

## Verified state

Verified 2026-08-20 after a full data refresh: collect, rebuild, retrain, snapshot, and the suite.

| Check | Value | How verified |
|---|---|---|
| Deploy DB matches (S16 mid) | 483 | query on `data/lol_deploy.duckdb` |
| Deploy DB timelines | 14,406 | same |
| Deploy DB deaths | 3,775 | same |
| Deploy DB events | 35,385 | same |
| Deploy DB roam windows | 641 | same |
| Deploy DB feature rows / labels | 483 / 483 | same |
| Deploy DB cluster sizes | 213 / 105 / 142 / 23 | same |
| Silhouette | 0.194 | `src.models` |
| Deploy DB match date range | 2026-01-10 to 2026-08-19 | same |
| Deploy DB file size | 5.3 MB | `ls` |
| Deploy DB privacy audit | no `puuid`, 0 original Riot IDs, 1 distinct time-of-day | query |
| Tests | 98 passed | `pytest tests -q` |
| Lint | clean | `ruff check src tests dashboard scripts` |
| Dashboard | 4 tabs, 0 exceptions | Streamlit `AppTest` |

Local-only, gitignored, verified 2026-08-20 on this machine:

| Check | Value |
|---|---|
| `data/raw/` files | 1,408 (704 detail + 704 timeline) |
| Source DB matches / timelines / deaths / events | 704 / 20,856 / 5,592 / 118,701 |
| Source DB match date range | 2025-09-11 to 2026-08-19 |

**Season 16 record, cross-checked against the user's own count.** The pipeline reports 577 Season 16 games at 296W-281L, a 51.3% win rate. The user reported 569 games at 292W-277L, also 51.3%. The rates agree exactly and the eight-game gap is consistent with remakes, which appear in match history but are usually excluded from a tracker's record. By role: MIDDLE 483, BOTTOM 56, UTILITY 28, TOP 7, JUNGLE 3. Only the 483 mid games reach the dashboard, per `PRODUCT.md` section 9.

**Season boundary verified.** Patch 16.1 first appears on 2026-01-10, exactly the value of `CURRENT_SEASON_START`, and 15.24 runs through 2026-01-01. One game sits between those dates and is on 15.24.

**Collection is complete for the analytical scope but not for all history.** The Riot API lists 856 ranked solo games; 704 are on disk. `DEFAULT_MATCH_COUNT` in `src/collector.py` caps a run at 500 IDs, and the 500th most recent is dated 2026-01-29, so the 152 missing games are all older than that and therefore pre-Season-16. They are out of analytical scope and were deliberately not collected. Raise the count if all-history coverage is ever wanted.

**Live deployment verified 2026-08-20** — first time since 2026-07-18. The app at `https://myishaa.streamlit.app/` serves the refreshed snapshot and reports 483 games. It required a manual reboot from the Streamlit Cloud console: Community Cloud suspends inactive apps, and a suspended app does not rebuild on push, so a commit lands but the served container stays on the previous build. Expect the same after any future refresh — pushing is not sufficient, the app has to be awake or rebooted.

Not verified:

- The three files in `docs/screenshots/` predate the four-tab UI.

## Open items

Ordered by dependency and by the `PRODUCT.md` section 13 priority ladder. Sourced from the 2026-08-12 pipeline audit and the product specification absorbed into `PRODUCT.md` on the same date.

### P0 — correctness. Done 2026-08-12.

Shipped in the same session as the audit. No rebuild was required; the deploy snapshot is unchanged.

- U3 done — the invented 55% / 45% cutoff is gone, and as of 2026-08-20 the verdict rule is an exact one-sided binomial test against the player's own baseline rather than a Wilson interval that excludes it. Wilson is a normal approximation and is anti-conservative at small samples with extreme proportions: on the refreshed data a 4-0 record produced an interval whose lower bound cleared the 50.9% baseline by a thousandth and rendered as a verdict a single loss would reverse. The exact test gives that record p = 0.067 and withholds it while keeping 15-5 at p = 0.025. The interval is still computed and shown, because it communicates precision; the test decides. Measured on the 2026-08-20 snapshot at baseline 50.9%: **two verdicts across all groupings** — opponent TwistedFate 15/20 = 75% (p = 0.025, Positive) and opponent Naafiri 2/11 = 18% (p = 0.029, Negative). Zero of 483 champion or matchup-pair groupings clear.
- U4 done — every mislabeled proxy renamed to what it measures. "Deaths while ahead" is now "Deaths above your own gold curve"; the death-context categories name the gold-curve comparison explicitly; "Estimated Throws / Comebacks" are now "Strong start, lost" and "Weak start, won". Cluster names `Behind & Spiraling` and `Ahead but Overextending` were deliberately left alone: they carry the same false ahead/behind semantics but are a user decision and are subject to M1.
- Low-data framing done — the Champions empty state now says "not a result of 0%, a result of too few games", and the patch and time-of-day charts are labeled reference with their sample caveat.
- Quick win done — `opp_gold_earned` is now surfaced as a `Gold Diff` column against the actual lane opponent, alongside `CS Diff`.

Still open at P0:

- `Skill-based` is not emitted. Separating "reliably close to baseline" from "not enough evidence" requires a minimum interesting effect size, which `PRODUCT.md` section 12 makes a user decision. Both cases currently report as Uncertain. On the present snapshot the choice would reclassify at most 5 of 98 groupings, so nothing is blocked — but it needs a number before the dataset grows.
- Named confidence bands (High / Medium / Low / Insufficient) are not emitted either; the interval and the game count are shown instead, which invents no cuts. `PRODUCT.md` section 7 lists the bands as an option, not a requirement.

### P1 — the product layer. Buildable from `matches` alone; not blocked by the reparse.

Pages that exist today: Overview, Champions, Matchups, Patterns. `PRODUCT.md` section 3 specifies six. Match History is blocked on the privacy decision below; Match Detail is blocked on the stage 0 reparse. The sidebar champion filter scopes Champions and Matchups only — Overview and Patterns ignore it, and the caption now says so.

- Match History page — "Which games should I inspect?" Filters and sorting by date, champion, opponent, role, result, queue, season, and date range. Optimize for fast scanning over density. All fields already exist in `matches`.
- Champion Pool done 2026-08-12 — `champion_pool()` returns games, W-L, win rate with interval and class, KDA, CS/min, gold/min, damage/min, average duration, and CS and gold differential against the actual lane opponent, for all 38 champions played in scope.
- Own-archetype composition done — the Champions tab shows the pool grouped by the archetype of the champion the player picked. Measured 2026-08-12: Burst Mages are 52.0% of the pool at 55.8% over 206 games; Control Mages 25.0% at 49.5% over 99; Assassins 9.1% at 38.9% over 36. All Uncertain against the 51.3% baseline, but the assassin figure is the weakest own-archetype number in the pool and matches the opponent-side assassin result.
- Tabs split 2026-08-12 — Champions and Matchups are now separate tabs, each with the user question `PRODUCT.md` section 3 assigns it. They were one tab, which is why the pool had nowhere to go.
- D6 done 2026-08-12 — `src/archetypes.py` maps all 62 champions present in the data across 12 archetypes. Bruisers and Fighters were dropped by user decision: Riot's Fighter class *is* Divers plus Juggernauts and "bruiser" is colloquial for the same group, so keeping all three let identical playstyles land in different buckets. Data Dragon `tags` were rejected as the source — they return Mage/Support for Hwei and Orianna and carry no burst-versus-control split, which is the exact distinction the `PRODUCT.md` worked example needs.
- Build-dependent archetypes. Sylas is held out of the archetype buckets rather than assigned, on the user's point that he plays as either an AP bruiser or an assassin mage depending on the build. He keeps his own champion-level verdict and is marked reference-only in archetype aggregates. Resolving this properly needs per-game item data: items are present in the raw match JSON and are not parsed into DuckDB, so it folds into the stage 0 reparse. `BUILD_DEPENDENT` in `src/archetypes.py` currently holds only Sylas; other flex mids (Ekko, Diana, Vladimir, Jayce, Yasuo, Yone, Kayle) are candidates and are a user decision, not an agent default.
- Archetype results, measured 2026-08-12 against the deploy snapshot at baseline 51.3%: Assassins 114 games at 44.7% CI [0.36, 0.54]; Burst Mages 90 at 47.8% CI [0.38, 0.58]; Control Mages 90 at 54.4% CI [0.44, 0.64]; Specialists 25 at 60.0%; Skirmishers 19 at 57.9%; Artillery 13 at 46.2%; Marksmen 12 at 58.3%; Tanks 6 at 16.7%. **Zero archetype verdicts clear the baseline.** The assassin weakness the `PRODUCT.md` worked example hypothesizes is present directionally but not separable from noise; roughly 106 more assassin games at the current rate would settle it. Per user decision, direction is shown with explicit uncertainty rather than withheld.
- Archetype-level matchup classification done. The Matchups tab reads verdicts, then opponent archetypes, then champion-into-archetype, then pairs as reference.
- Champion-into-archetype done — `champion_archetype_matchups()` is one level finer than the archetype table and one coarser than a pair. It produced the first matchup verdict this project has had: **Syndra into Assassins, 0 wins in 5 games, CI [0.00, 0.43], Negative.** Measured 2026-08-12; 135 cells, 1 verdict.
- Pocket-pick detection done — `pocket_picks()` labels champions outside the core pool that beat the baseline, using the four labels fixed in `PRODUCT.md` section 6. "Rarely played" is derived from the player's own usage rather than a game count: the core pool is the smallest set of champions covering half of all games, currently Zoe, Hwei, Viktor, Ahri, and Syndra. Measured 2026-08-12: zero Potential Pocket Picks, zero Matchup-specific, three Emerging Picks (Mel 10/18, Aurora 8/13, Galio 7/11), and seven Insufficient Data including five champions with a single game at 100%. Those five are exactly the outliers section 6 forbids promoting, and the label vocabulary is what keeps them from becoming recommendations.
- Overview rebuilt around "How am I doing, and what should I investigate?" — current form, streak, strongest and weakest champions, pool composition, high-confidence insights only.

### Stage 0 — the reparse. Done 2026-08-12, snapshot included.

D1 and D2 are both implemented and the source database has been rebuilt from the immutable raw files. No Riot API calls were made.

- D1 done — `match_timelines` now carries the lane opponent's gold, CS, XP, level, and position, the player's own level, and both team gold totals. Verified on the rebuilt source DB: 11,795 Season 16 mid rows with **zero** NULL opponent gold and zero NULL level.
- D2 done — `match_deaths` gained position, killer champion, assist count, XP at death, and the opponent's gold at that minute. New `match_events` table holds champion kills, turret plates, buildings, and elite monsters for both teams, plus the player's own ward events. Verified: 4,743 deaths with zero NULL positions and 5 NULL killers (executions and turret kills, which have no champion); 99,342 events.
- **Nothing reads the new columns yet.** Verified 2026-08-12 by grep across `src/features.py`, `src/models.py`, and `dashboard/app.py`: no consumer of `opp_gold`, `opp_cs`, `opp_xp`, `team_gold`, `killer_champion`, `assist_count`, or `match_events`. `query_gold_trajectories` still selects own gold only. The reparse has produced zero visible change so far; it is groundwork, and the features and UI that use it are the P2 items below.
- `build_deploy_db.py` publishes the new columns and a filtered slice of `match_events` — rows with player involvement, plus objectives. The unfiltered table is roughly 100,000 rows and the committed snapshot should not carry what nothing reads.
- `tests/test_build_deploy_db.py` no longer restates the source schema by hand; it calls `processor.init_schema`. The hand-copied copy is what silently drifted when the timeline gained columns.

**What the opponent data shows, measured 2026-08-12 on the rebuilt source DB.** At minute 14 in Season 16 mid games: won games average **+269 gold and +11.0 CS** against the lane opponent; lost games average **-401 gold and +2.9 CS**. A 670-gold swing that the previous self-referential baseline could not see. CS differential stays positive in both, so the lane is not where the gold is lost.

**Unblocked and rebuilt 2026-08-12.** `src/models.py` now remaps a clean renumbering instead of refusing it.

- `_align_clusters_to_names()` replaces `_guard_cluster_name_binding()`. It matches each raw cluster to its nearest named centroid and, when that matching is one-to-one, renumbers the labels, the profile, and the model's own centres together so the persisted model predicts named IDs. When two raw clusters are nearest the same named centroid the mapping is not one-to-one, the run no longer corresponds to the names, and it still warns and refuses.
- The rationale is the measurement recorded under M1: K-Means IDs reshuffle whenever the dataset grows, so refusing every renumbering meant a manual decision on essentially every refresh. Rejecting arbitrary renumbering was never what the guard was for; rejecting genuine drift is.
- The retrain applied `0 → 3, 1 → 2, 2 → 0, 3 → 1` and produced cluster sizes 188 / 73 / 128 / 7 with silhouette 0.227, so each name is back on its own cluster and dashboard output is unchanged.
- Deploy snapshot rebuilt and audited: no `puuid`, zero original Riot match IDs, zero orphan feature or label rows, complete opponent columns, 5.1 MB. The Streamlit app renders all four tabs with zero exceptions against it.
- The centroid snapshot `models/cluster_centroids.json` is **intentionally frozen**. It is the naming anchor, not a record of the latest fit, and `_align_clusters_to_names()` only ever writes it when it does not yet exist. It therefore holds the values it was taken at, on a smaller dataset, while real centroids drift as data grows. That is correct and must not be "refreshed": rewriting it on each run would redefine the names to whatever the newest fit produced and destroy the binding it exists to protect. It needs replacing only if the names themselves are redefined, or if drift grows large enough that the mapping stops being one-to-one — at which point the guard refuses and says so.
- Privacy note: the snapshot now also carries per-death positions and `killer_champion`. Each game therefore exposes an **ordered sequence of (minute, enemy champion) pairs** alongside the retained `game_datetime`, the patch, and both mid champions. Coordinates are not identifying, but that sequence is a materially stronger fingerprint than the champion-plus-timestamp combination already flagged. This does not change the standing decision, and it strengthens the case for settling the Match History privacy item below before a per-game view ships.

M1 remains open and is unaffected: the remap makes the clusters maintainable, it does not make them less circular.

**Retrained 2026-08-12 after D3 and D4 changed three model features.** `total_roams`, `avg_cs_sacrifice` and `roam_impact_rate` all moved when roam detection was fixed, and `deaths_while_ahead` now measures a real lane lead. The guard found a one-to-one mapping (`0 → 0, 1 → 2, 2 → 3, 3 → 1`) and persisted. Cluster sizes are now 176 / 88 / 118 / 14 against the previous 188 / 73 / 128 / 7, and silhouette fell from 0.227 to **0.193**.

**Known limitation, surfaced by this run:** the guard compares centroid positions, not cluster membership. It cannot tell "the same clusters were renumbered" from "the features were redefined and the new clusters happen to sit near the old centroids". This run was the second kind. The centroid semantics still line up — cluster 0 is behind and dying, 1 is ahead and overextending, 2 is clean, 3 is the outlier bucket — but the games inside them changed, and the names deserve a human re-review rather than a silent pass. The falling silhouette also strengthens the M1 recommendation.

### P2 — advanced analysis. Blocked by stage 0.

- Match Detail page — "What actually happened in this game?" Lane phase with CS, XP, gold, and level differences, first recall, plates, solo kills; a chronological timeline of important events; per-death context.
- Death context rebuilt on real evidence, done 2026-08-12. `death_context()` now reads position, killer champion, assist count, and the opponent's gold at that minute. Measured over 3,117 Season 16 mid deaths: **3,115 have full context**; 1,205 (39%) came from the lane opponent and the other 61% from elsewhere on the map; 1,024 (33%) were solo kills with no assist; 1,129 (36%) happened in the enemy half. By zone: 1,815 in the mid corridor, 748 bot side, 554 top side. By phase: 404 before 6 minutes, 826 in laning, 1,887 after. `is_overextension_ahead` and `is_deficit_fight` keep their names but now compare the player to the actual opponent rather than to their own season average. The two deaths lacking position or killer are reported as unknown, not guessed.
- D3 done 2026-08-12 — the `len(block) < 2` guard is gone, so a roam occupying a single minute frame is no longer discarded. Detection went from 84 windows across 81 games to **513 windows across 308 games**. `roam_windows` gained `assists_during_roam`, filled from the parsed event stream: 194 assists are now counted, and `roam_result` reads a kill *or* an assist as impact, so a mid laner collapsing on a side lane is no longer scored as a failed roam. 245 of the 513 windows now register impact.
- D4 done 2026-08-12 — Throw and Comeback are defined on `team_gold - enemy_team_gold` at the frame closest to minute 14, which the reparse made available. A throw is the team being ahead and losing; a comeback the reverse. The boundary is zero, so no lead size is invented. Measured: 202 of 388 games ahead at 14 and 56 of those lost; 186 behind and 55 of those won. Team gold at 14 averages +1,918 in wins and -1,710 in losses. `feature_matrix` gained `team_lead_14` and `lane_gold_diff_14`; `gold_delta` is unchanged because it is a model feature and altering it would redefine the clusters.

### P3 — higher-level intelligence. Blocked by P2.

- D5 — rebuild the feature set. `total_deaths`, `tilt_spiral_ratio`, and `max_death_streak` correlate pairwise at r = 0.75-0.82, so K-Means is close to one-dimensional on death count. `roam_impact_rate` is the neutral fill value 0.5 in 318 of 396 rows.
- M1 — decide whether K-Means survives. **Investigated 2026-08-12 on the reparsed source database.** The finding is that clustering cannot be rescued by better features, and the cluster-ID instability is inherent rather than a bug. Evidence, all measured on 396 Season 16 mid games:

  | Feature set | Silhouette (k=4) | Win-rate spread across clusters | Max \|corr\| with winning | Collinear pairs |
  |---|---|---|---|---|
  | Current 9 features | 0.227 | 42% | 0.41 | 4 |
  | Opponent-relative (gold/CS/XP diff, real deaths-while-behind) | 0.184 | 51% | 0.54 | 14 |
  | Playstyle (wards, plates, objectives, death position, CS/min) | 0.149 | 52% | 0.42 | 0 |

  - **Opponent data made clustering worse, not better.** Lane differentials describe how the game went, so clustering on them recovers the outcome even more sharply than the old proxies did.
  - **No natural structure at any cluster count.** Sweeping k from 2 to 8 on the current features: silhouette 0.200, 0.224, 0.227, 0.258, 0.275, 0.229, 0.232. The peak is 0.275 at k=6 — weak-but-present rather than absent, so the argument does not rest on it. What does rest on it: at that peak the win-rate spread is still 43% and the n=7 outlier bucket is intact. Win-rate spread stays between 37% and 63% at every k, so the clusters sort by outcome regardless of k.
  - **The n=7 bucket is an outlier group, not an under-sampled archetype.** It appears with exactly 7 members at every k from 4 through 8.
  - **The cluster-ID permutation is inherent.** K-Means is deterministic on fixed input — three identical runs gave identical sizes — but the ID assignment reshuffles whenever the dataset grows. Fitting on the first n rows for n = 300, 340, 354, 380, 396 put the low-death "Clean Games" centroid on id 1, 3, 2, 1, 1 respectively. The named snapshot in `models/cluster_centroids.json` was taken on a smaller dataset, which is why the current fit reads as a permutation of it. **The guard will therefore fire on essentially every data refresh, forever**, and no amount of care in the fit prevents it.

  Reading: the circularity is not a feature-quality problem. A single player's match data has one dominant axis of variation — how the game went — and any unsupervised partition recovers it. Three independent feature sets, eight cluster counts, same answer.

  Recommended: retire K-Means and replace it with explicit named patterns computed directly from the reparsed opponent data, which the schema now supports (for example: lost lane by minute 14 and then died away from mid; won lane and gave the lead back before the first objective). Explicit patterns are checkable, nameable, stable across refreshes, and carry no ID binding. Retiring K-Means also dissolves the permutation decision below rather than answering it. Still a user decision.
- Cluster-ID permutation — **resolved 2026-08-12**, open since 2026-07-18. IDs are now remapped to the nearest named centroid on persist, so the guard fires on genuine drift rather than on renumbering. This makes the clusters maintainable and is independent of M1, which asks whether they should exist at all.
- Recurring pattern detection on repeated evidence. One unusual game is never a pattern.

### Cross-cutting

- Metric definitions. `PRODUCT.md` section 7 requires every important metric to document source, calculation, assumptions, and limitations. No file owns this yet. Write it once the metrics stabilize after stage 0, not before.
- Privacy: timestamps are coarsened (see known issues), which removes the strongest identifier. A per-game view would still expose a dated game list; revisit before Match History or Match Detail ships.
- Superseded — original entry: privacy decision before Match History or Match Detail ships. The known issue below accepts `game_datetime` in the deploy DB as portfolio-scale risk, but that assessment predates any per-game view. A dated game list plus champion plus patch is materially more identifying than a season aggregate. Not an agent decision.
- Recapture `docs/screenshots/` after the UI rework, not before.
- Re-verify the live deployment and record the result here.

## Known issues

Accepted limitations. Not scheduled work.

- Throw, Comeback, Overextension, Deficit Fight and Post-Laning Throw are **no longer proxies** as of 2026-08-12. Throw and Comeback read a real team gold lead at minute 14; the three death labels compare the player to the actual lane opponent at the minute of death. What remains heuristic is roam detection and the cluster labels, below.
- Roam detection stays heuristic. A roam is a minute frame more than 2,500 units off the mid diagonal, so a detour into the player's own jungle counts as one, and the corridor width itself is a constant rather than a measured lane boundary. Impact is a kill or assist during the window, which cannot see a roam that created pressure without a takedown.
- Cluster 3 (n=7) is an outlier bucket, not an under-sampled archetype. Its defining feature `avg_cs_sacrifice` sits at z = +7.01, the signature of the roam detector misfiring rather than of a behavior pattern awaiting more games. Corrected 2026-08-12; the previous entry recorded it as deliberately uncharacterized. Clusters 0/1/2 are named from centroid review and are subject to the M1 decision above.
- The centroid-binding guard has no absolute-distance cutoff. It refuses to persist a retrain whenever any cluster's centroid is no longer nearest its own previously-named centroid — including a clean bijective permutation — and performs no remapping.
- `game_datetime` in the deploy DB is truncated to midnight UTC as of 2026-08-12, before the first public push carrying per-death killer champions. The exact kickoff time plus the patch, both mid champions, and the death sequence was enough to locate a game on third-party match sites. Every consumer uses `>=` comparisons, so season, patch and date-range filtering are unaffected, and `hour_of_day` and `time_bucket` are computed in the source database before publishing, so time-of-day analysis survives. Locked down by `test_deploy_db_never_publishes_a_precise_timestamp`.

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
