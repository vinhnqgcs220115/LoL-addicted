# Roadmap

> **L1 Working** · what to build next, and its status · owner: Claude keeps it current, the user sets priorities · update: every session, by ticking tasks and refreshing *Now*

## Now

- **Milestone:** M1 Dashboard scaffold. Not started.
- **Next task:** M1.1.
- **Waiting on you:** B1 (a non-expiring Riot key), which starts M1b.

Status marks: `[ ]` todo · `[~]` in progress · `[x]` done. "Done" means the acceptance check passed.

## M1 Dashboard scaffold

Tasks are ordered by dependency: data first, then UI. "Season" means the current patch major (see CLAUDE.md → Scope).

- [ ] **M1.1 Collector: full current season, plus rank.**
  - Page through match IDs until the patch major drops below the current one. This replaces the fixed 500-ID cap (`DEFAULT_MATCH_COUNT`).
  - Add a rank snapshot. Verify the League endpoint and its routing with a real call first.
  - *Done when:* the number of season SoloQ IDs the API lists equals the files in `data/raw/`, and the rank is stored with its fetch time.
- [ ] **M1.2 Season from patch.**
  - The current season is the patch major of the newest game. This replaces `CURRENT_SEASON_START`.
  - *Done when:* no hardcoded season date remains, and a test covers the 15.24 → 16.1 boundary.
- [ ] **M1.3 Deploy DB publishes the season.**
  - `scripts/build_deploy_db.py` publishes every current-season SoloQ game (all roles), plus the Riot ID and rank, without anonymization.
  - Update `test_deploy_db_never_publishes_a_precise_timestamp` to match.
  - *Done when:* the deploy DB's game count equals the season's SoloQ game count, and the tests pass.
- [ ] **M1.4 Landing page.**
  - Shows the Riot ID, rank, season games and win rate (overall and mid), and the mid champion-pool size.
  - *Done when:* the numbers match a DuckDB query, and the page renders locally.
- [ ] **M1.5 Champions tab.**
  - An icon grid from `assets/champion_icons/`. Clicking a champion shows its matchups and the win rate per opponent.
  - Reuse `champion_pool()` and `champion_matchup_stats()` in `src/features.py`.
  - *Done when:* every mid champion of the season appears, and its matchup counts sum to its games.
- [ ] **M1.6 Match history.**
  - Every current-season SoloQ game, all roles, newest first.
  - Filters for champion, role and result, and a "load more" button that runs until no games are left.
  - *Done when:* paging reaches the oldest game of the season.
- [ ] **M1.7 Local collect button.**
  - When the app runs locally, it collects, processes and refreshes from the dashboard.
  - Local mode reads `data/lol.duckdb`; today `DB_PATH` is hardcoded to the deploy snapshot.
  - *Done when:* a newly played game appears after one click, locally.
- [ ] **M1.8 Retire K-Means and the old tabs.**
  - Remove `src/models.py`, `models/cluster_centroids.json`, `tests/test_models.py`, the Patterns tab, the `models` workflow step, and the cluster checks in the `pipeline-ops` skill.
  - *Done when:* nothing references clusters, and the suite is green.
- [ ] **M1.9 Redeploy.**
  - Push the new deploy DB and the new app, and reboot the Streamlit app if it was asleep.
  - Refresh the README screenshots.
  - *Done when:* the live app shows the new landing page and the season's game count.

## M1b Live collection

A parallel track that starts after B1.

- [ ] **B1 (you).** Get a Riot API key that doesn't expire. A dev key dies every 24 h.
- [ ] **B2 Storage decision.** The app container's disk resets, so collected data needs cloud storage. Compare 2–3 options on free tier, fit with DuckDB, and effort; you choose.
- [ ] **B3 Owner-only guard.** The collect button needs a password from Streamlit secrets, so visitors can't trigger it.
- [ ] **B4 Live collect.** The live app collects into the chosen storage and reads from it. The committed-snapshot flow retires.

## M2 Per-game report (measurements only)

Covers the lane phase, 0–14 min, against the actual lane opponent. No verdicts, no thresholds, and no catalogue rules yet.

- [ ] **Decide first (you):** rebuild the schema to hold all 10 participants (needed later for outside pressure), or start on the current tables?
- [ ] **Lane phase:** CS, gold, XP and level differences against the lane opponent.
- [ ] **Deaths with context:** killer, assists, position, and gold against the opponent at that minute.
- [ ] **Timeline events:** item buys, recalls (inferred, because Riot logs no recall event), plates and objectives.
- [ ] **Roams:** heuristic, labelled as estimates.
- [ ] **Decide after testing (you):** extend the report from 0–14 min to the full game?

## M3–M5 (blocked)

- **M3 Decision analysis.** Needs your verdicts on `docs/domain/DECISION_CATALOGUE_v1.md`. Start with the 13 BUILDABLE entries in the review sheet `docs/design/CATALOGUE_REVIEW.md`, then settle the thresholds below.
- **M4 Season patterns.** Named recurring patterns built from M3 decision records.
- **M5 Pro comparison.** One matchup at a time, patch-aware.

## Open decisions (yours)

| Decision | Blocks |
|---|---|
| Cloud storage for live collection | M1b |
| Schema rebuild for all 10 participants | the start of M2 |
| Extend the per-game window past 14 min | after M2 testing |
| Catalogue verdicts (23 entries on the review sheet) | M3 |
| Six thresholds (#13, 14, 15, 25, 38, 43) | M3 |
| Mid-corridor width (an invented 2500 today) and the "at the fight" radius | M3 |
| Multiple-comparison policy and minimum effect size | champion verdicts |

## Parking lot

Promising, but not scheduled. Each line says where its detail lives.

- **K-Means story for interviews.** It was measured and then retired: silhouette ≈ 0.19, clusters tracked win/loss rather than playstyle, and IDs reshuffled on every refresh. Detail: the old `.claude/CONTEXT.md`, item M1, at tag `pre-docs-refactor`.
- **Objective spawn timers.** These can be derived from the corpus instead of kept by hand (`docs/design/FINALIZATION_DECISIONS.md` §1).
- **Replay annotation** for the wave and trading questions the data can't see (`docs/design/FINALIZATION_DECISIONS.md` §12).
