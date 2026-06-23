# Project Context

**Phase:** 4 implementation complete — Streamlit Cloud deployment pending
**Last updated:** 2026-06-24

---

## Roadmap

### Phase 1 — Data Collection
- [x] Scaffold `src/collector.py`: `get_puuid()`, `get_match_ids()`, `get_match_detail()`, `get_match_timeline()`
- [x] Scaffold `src/processor.py`: `init_schema()`, `process_match()`
- [x] Run full pipeline end-to-end
- [x] Verify: 513 rows in `matches`, 15,273 rows in `match_timelines`

### Phase 2 — EDA & Feature Engineering
- [x] `notebooks/01_eda.ipynb`: death context analysis, throw pattern detection, roaming timing analysis (not generic win rate / KDA charts)
- [x] `src/features.py`: `death_context()`, `is_throw_game()`, `roam_timing()`, `tilt_index`, `champion_matchup_stats()`, temporal features
- [x] Verify: `feature_matrix` populated with no NULL values (328 Season 16 mid rows; 41 throw games, 53 comebacks)

### Phase 3 — ML Models
- [x] `notebooks/02_clustering.ipynb`: executed centroid heatmap, cluster summary, and average gold trajectory analysis without pre-naming archetypes
- [x] `src/models.py`: uses `gold_delta`, `total_deaths`, `deaths_while_ahead`, `tilt_spiral_ratio`, `max_death_streak`, `total_roams`, `avg_cs_sacrifice`, `roam_impact_rate`, and `tilt_index` as `FEATURE_COLS`
- [x] Scale with `StandardScaler`, then fit `KMeans(n_clusters=4, random_state=42, n_init=20)`; reject NULL and non-finite feature values
- [x] Save `models/kmeans.pkl` and `models/scaler.pkl`, print cluster sizes and silhouette score, and write `cluster_labels` to DuckDB

### Phase 4 — Dashboard & Deploy
- [x] `dashboard/app.py`: Overview / Champions / Patterns tabs (3 tabs, no Predictor)
- [ ] Deployed to Streamlit Cloud with public URL
- [ ] `README.md` with screenshots and live demo link

### Stretch Goal — Pro Comparison (if Phase 2–4 finish on time)
- [ ] Extend `collector.py` with KR/EUW server routing
- [ ] Collect ranked mid games from 3–5 known Challenger mid players (e.g. Faker, Chovy)
- [ ] Compare CS diff curve and roaming timing against personal data on same champions

---

## Current Status

```
Matches collected    : 513 (328 S16 mid, 58 S16 off-role, 127 S15)
Matches NULLs        : win=0, match_id=0, champion_name=0
Matches date range   : 2025-09-11 to 2026-06-21
Mid opponent fields  : champion=328/328, cs=328/328
Death attribution    : reported=4,124, stored=4,124, mismatched matches=0
Timelines collected  : 513 (15,273 timeline rows)
Feature matrix       : 328 rows, 19 columns, 0 NULL — Season 16 mid only
Clustering           : trained — 328 labels, silhouette 0.245, cluster sizes 166 / 103 / 7 / 52
Tests                : 51 passed; Ruff clean
Deployment snapshot  : 328 sanitized matches; 0 original Riot match IDs
Dashboard            : 3 tabs implemented; local Streamlit runtime verified
Live URL             : —
```

---

## Decisions Log

| Decision | Rationale |
|---|---|
| DuckDB over SQLite | Window functions and analytical queries without a server |
| K-Means over XGBoost for modeling | Win predictor removed; clustering behavioral aggregates does not benefit from gradient boosting |
| Cluster names remain a user decision | Names must follow centroid and trajectory review; pre-naming would imply unsupported behavior |
| Plotly over Matplotlib | Interactive charts required in Streamlit |
| `requests` over `httpx` | Sync is sufficient at this data scale; simpler API |
| Ranked Solo/Duo only (queue=420) | Cleaner signal; removes ARAM and normal queue noise |
| Raw JSON saved before processing | Allows re-processing without re-hitting the API |
| Predictor tab removed | Manual input form has no practical use case during or after a game |
| EDA refocused to death context / throw detection / roaming | More differentiated from OP.GG; directly answers "what am I doing wrong" |
| Win predictor model removed | Model output not surfaceable in a useful way; clustering is sufficient |
| Pro comparison added as stretch goal | Requires multi-server routing; blocked on Phase 2-4 completion |
| Season 16 filter in feature matrix | S15 gold rates differ; mixed-era baselines distort `gold_lead_approx` and `gold_delta` |
| Current analytics are mid-only | The project is personal and time-boxed; raw/processed off-role games remain available for future role-aware expansion |
| Dashboard derives cluster means from DuckDB | `models/*.pkl` stay local and gitignored; feature means come from `feature_matrix` joined to `cluster_labels` |
| Deployment uses committed `data/lol_deploy.duckdb` | Streamlit Cloud has no persistent disk; S3/LFS adds infra complexity for <10 MB; simple git commit is correct at this scale |
| tilt_index scoped to S16 mid only | Consistent with ANALYSIS_ROLE filter; loses S15 rolling context for first S16 games, accepted at this data scale |
| game_datetime retained in deploy DB | Timestamps plus champion/version could identify matches on public sites; accepted risk for a portfolio project |

### Deployment notes (Phase 4)

Two DuckDB files, two different purposes:
- `data/lol.duckdb` — development DB, gitignored, rebuilt locally from raw JSON
- `data/lol_deploy.duckdb` — production read-only artifact, committed to git, read by the dashboard

To update deployed data: verify `lol.duckdb`, run `.\scripts\workflow.ps1 deploy-db`, then commit the generated file. The dashboard must read from `lol_deploy.duckdb` in read-only mode, not `lol.duckdb`.

Before the public deployment commit, review match-identifier exposure in the deployment database.

---

## Phase 4 Decisions

- Decide whether `is_early_death` appears in Overview or Patterns before implementing either tab.
- Review current per-cluster means before assigning user-facing names. Until then, display numeric cluster IDs and measured values only.
- Show cluster sample sizes in the dashboard; cluster 2 currently has only 7 games and must not support strong conclusions.
- Keep the Champions tab mid-only. All-role support requires role-aware opponent extraction and a full rebuild.

## Known Issues

None blocking Phase 4 after the pending repository commit.

---

## Notes

- Vietnam routing: `asia` for account-v1, `vn1` for summoner/league, `sea` for match-v5
- Free API key expires every 24h — regenerate at `developer.riotgames.com`
- Summoner identity is `GameName#TAG` (e.g. `PlayerName#VN1`); PUUID is fetched once and stored in `.env`
