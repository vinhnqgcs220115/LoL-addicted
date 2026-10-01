# LoL Mid-Lane Analytics

> **L0 Constitution** · scope, rules and doc map; auto-loads every session · owner: Claude, scope changes need the user's OK · update: in the same commit as any scope or rule change

## 1. Purpose

A personal League of Legends review tool for one mid laner. It answers, in this order:

1. **Per game:** what happened in my mid lane, what decisions did I make, how good were they?
2. **Per season:** what are my real strengths, weaknesses, champion tendencies and recurring patterns?
3. **Later:** how do my decisions differ from pro mid laners in the same matchup and patch?

Personal usefulness beats portfolio polish. The long-form vision is `docs/VISION.md`; this file wins where they differ.

## 2. Scope

| Area | Rule |
|---|---|
| Account | One summoner, set in `.env`. Public identity is fine: the Riot ID and rank may appear on the live app. |
| Queue | Ranked Solo/Duo only (`queue=420`). |
| Season | Current season = patch major version: 16.x is Season 16, and 17.1 starts Season 17. Pre-season patches (such as 15.24) belong to the old season. Stats and match history cover the current season only; older raw data stays on disk. The user may write patches as 26.x; store Riot's 16.x form. *Target: the code uses `CURRENT_SEASON_START` until ROADMAP M1.2.* |
| Roles | Every role is collected, stored and listed in match history. Analytics are mid only (`team_position = 'MIDDLE'`). |
| Deployment | Streamlit Community Cloud: https://myishaa.streamlit.app/ |

**Forbidden**
- Live or in-game features.
- Win-probability prediction. It was removed before because its output had no use.
- Verdicts on trading or wave management. Match-V5 has no minion state, ability casts, cooldowns or ward positions. At most, point the user to a replay minute.
- Invented certainty: a claim the sample can't support, or a proxy shown as fact.

**Not now:** multi-user or public profiles, all-role analytics, and an AI explanation layer. An AI layer only ever sits on top of validated analytics.

## 3. Order of work

Milestones run in this order. Tasks and their status live in `ROADMAP.md`.

| Milestone | Goal |
|---|---|
| M1 Dashboard scaffold | Season-stats landing page, champion pool with matchups, current-season match history, local collect button. Time-boxed. |
| M1b Live collection | Collect button on the live app. Runs in parallel; needs a non-expiring Riot key, cloud storage and an owner-only guard. |
| M2 Per-game report | Measurements only: lane phase 0–14 min against the lane opponent. The window is temporary. |
| M3 Decision analysis | Rules from the decision catalogue. Blocked on the user's catalogue review and thresholds. |
| M4 Season patterns | Named recurring decision patterns built from M3 records. Never clusters. |
| M5 Pro comparison | One matchup at a time, patch-aware. |

**Putting M1 first is the user's decision (2026-10-01).** It deliberately overrides `docs/VISION.md` §16 ("don't optimize the UI before definitions are stable") and the 2026-09-16 design rule "statistics never the headline", for M1 only. From M2 onward, per-game decisions lead and statistics are context.

## 4. Principles

- **Layers of meaning.** Keep raw facts, derived values, interpretation and recommendations separate, and label which is which.
- **Provenance.** Every derived value states its source (a Riot field, a derivation, or an inference) and a confidence.
- **Proxies read as estimates.** Inferred recalls, roam detection and death categories are labelled as inferred.
- **Sample size gates claims.** No verdict, ranking or colour on a slice too small to support it, and the count is shown beside the claim. A 2-game 100% record never outranks a 35-game 60% record. Small-sample outliers are never recommended.
- **No invented thresholds.** A cutoff that changes a conclusion is the user's decision. Ask; don't default.
- **Context for every number.** Compare against the player's own baseline or the actual lane opponent, e.g. "+8% above your overall mid-lane baseline", never against a coin flip.
- **Every element answers a question.** Each page, chart and metric serves a stated user question. Use a chart only when it reads better than the table. No metric explosion.
- **Correctness before presentation.** A wrong number that looks good is worse than no number.

## 5. Architecture

Riot API → `data/raw/*.json` (immutable) → DuckDB → `src/` analytics → `dashboard/` (Streamlit).

| Module | Owns | Never |
|---|---|---|
| `src/collector.py` | Riot API calls, rate limiting, raw JSON persistence | parse or transform |
| `src/processor.py` | Parse raw JSON into DuckDB; schema in `init_schema()` | call APIs |
| `src/features.py` | All queries and analytics on DuckDB tables | read `data/raw/` |
| `src/archetypes.py`, `src/mapping.py` | Champion archetypes (user-owned constants); minimap projection | — |
| `src/models.py` | K-Means. **Being retired in M1.8; do not extend.** | — |
| `dashboard/app.py` | Rendering, caching, layout | business logic or SQL beyond calling `src/` |
| `scripts/build_deploy_db.py` | Builds `data/lol_deploy.duckdb` for the live app (still anonymizes until M1.3) | — |
| `notebooks/` | Exploration sandbox | being imported by `src/` |

**Data rules**
- `data/raw/` is write-once. Rebuild DuckDB from it; never edit it.
- DuckDB is the single source of processed data. Use `snake_case` columns, ISO 8601 timestamps, and explicit column lists on persistent tables.
- Store `game_version` on every match as the first two segments of `info.gameVersion` (e.g. `16.12`). Never hardcode a patch.
- Queries live in `src/`, never in `dashboard/`, so a later schema rebuild changes one layer, not the UI.
- The live app reads `data/lol_deploy.duckdb` read-only. It is committed because Community Cloud has no persistent disk; M1b replaces this.

**Data integrity.** Before changing analytics, verify:
- match, role and lane filtering;
- champion identity;
- patch and season;
- duplicates and timestamps;
- participant and opponent mapping;
- win/loss;
- timeline alignment.

Watch for off-role games, missing timeline minutes and stale derived tables.

**Key decisions.** The old rationale is in git, at tag `pre-docs-refactor`.
- DuckDB over SQLite: analytical SQL without a server.
- Raw JSON is saved before processing, so data can be reprocessed without hitting the API again.
- Ranked Solo/Duo only, for a cleaner signal.
- K-Means is retired. Its clusters recovered win/loss rather than playstyle (silhouette ≈ 0.19), and the cluster IDs reshuffled on every refresh.

**Known gaps.** Roam detection is heuristic, and `MID_LANE_CORRIDOR_WIDTH = 2500` in `src/features.py` is an invented constant. Its real value is the user's call.

## 6. Riot API

- Account-V1 uses `asia.api.riotgames.com`; Match-V5 uses `sea.api.riotgames.com`. Wrong routing gives silent 404s.
- Any other endpoint, such as League for rank: verify the host and response shape with a real call before writing code.
- The dev key expires every 24 h; regenerate it at developer.riotgames.com.
- Rate limits are 20 req/s and 100 req/2 min. Keep the 1.3 s delay; on a 429, wait `Retry-After` + 1 s.
- Timelines are per-minute snapshots plus millisecond-exact events. What exists and what doesn't is measured in `docs/DATA_AUDIT.md`.

## 7. Hard rules

- Secrets come only from `.env` or Streamlit secrets. Never commit `.env`, `data/raw/` or local `*.duckdb`; `data/lol_deploy.duckdb` is the one exception.
- No Riot API calls outside `src/collector.py`.
- No business logic in `dashboard/`.
- No user-facing label that claims more than the data shows.
- Stage explicit paths in git; never `git add -A` or `git add .`.

## 8. Testing

- Use `pytest` with fixtures in `tests/fixtures/`, and never call the real API in tests.
- Every parser and feature function gets a test. Cover edge cases: zero deaths, a missing timeline minute, an empty ID list.
- Lint with `ruff check src tests dashboard scripts`.
- After any collector or processor change, run a small batch and check DuckDB (see the `pipeline-ops` skill).
- A UI task is done only after the app has been run and the rendered page inspected.

## 9. Session protocol

- **Start:**
  - read `ROADMAP.md` → *Now*, and the newest entry in `.claude/CONTEXT.md`;
  - verify status against the repo, never against a doc or a summary.
- **During:**
  - stay inside the task;
  - surface product, domain, threshold and architecture choices to the user instead of deciding them;
  - routine implementation details are yours.
- **End:**
  - tick the ROADMAP tasks and update *Now*;
  - add a CONTEXT entry at the top;
  - commit;
  - if scope or rules changed, edit this file in the same commit.

## 10. Doc map

| Level | File | Job | Read when |
|---|---|---|---|
| L0 | `.claude/CLAUDE.md` | Scope, rules, this map | Always (auto-loaded) |
| L1 | `ROADMAP.md` | Milestones, tasks, status, open decisions, parking lot | Every session |
| L1 | `.claude/CONTEXT.md` | Session journal: what happened, what was decided | Every session |
| L2 | `README.md` | Front door for humans | Setup or features change |
| L2 | `.claude/COLLAB.md` | Roles and how we work | Process questions |
| L2 | `GAME_MECHANICS.md`, `docs/domain/` | Domain knowledge (user-owned) | Touching gameplay logic |
| L2 | `.claude/skills/` | Running and debugging the pipeline | Pipeline work |
| L3 | `docs/VISION.md`, `docs/ANALYSIS_SPEC.md`, `docs/DATA_AUDIT.md`, `docs/design/`, `docs/research/` | Archive and reference | Only when a task names them |

**Rules**
- A higher level wins a conflict.
- Measured facts beat any doc on what is true: the code, a DuckDB query, `docs/DATA_AUDIT.md`.
- `GAME_MECHANICS.md` §5–6 describe data and code as of July 2026; the code and DATA_AUDIT win there.
- One fact, one home: link to it, don't restate it.
- An L3 file is not authoritative until a recorded decision promotes it into L0 or L1.
- Status lives only in ROADMAP; history lives only in CONTEXT and git.
- Every doc opens with one header line: level · purpose · owner · update rule.
