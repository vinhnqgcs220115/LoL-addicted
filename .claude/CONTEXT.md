# Project Context

**Phase:** 4 — Dashboard & Deploy
**Last updated:** 2026-06-22

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
- [x] Verify: `feature_matrix` populated with no NULL values (386 Season 16 rows; 48 throw games, 64 comebacks)

### Phase 3 — ML Models
- [x] `notebooks/02_clustering.ipynb`: executed centroid heatmap, cluster summary, and average gold trajectory analysis without pre-naming archetypes
- [x] `src/models.py`: uses `gold_delta`, `total_deaths`, `deaths_while_ahead`, `tilt_spiral_ratio`, `max_death_streak`, `total_roams`, `avg_cs_sacrifice`, `roam_impact_rate`, and `tilt_index` as `FEATURE_COLS`
- [x] Scale with `StandardScaler`, then fit `KMeans(n_clusters=4, random_state=42, n_init=20)`; reject NULL and non-finite feature values
- [x] Save `models/kmeans.pkl` and `models/scaler.pkl`, print cluster sizes and silhouette score, and write `cluster_labels` to DuckDB

### Phase 4 — Dashboard & Deploy
- [ ] `dashboard/app.py`: Overview / Champions / Patterns tabs (3 tabs, no Predictor)
- [ ] Deployed to Streamlit Cloud with public URL
- [ ] `README.md` with screenshots and live demo link

### Stretch Goal — Pro Comparison (if Phase 2–4 finish on time)
- [ ] Extend `collector.py` with KR/EUW server routing
- [ ] Collect ranked mid games from 3–5 known Challenger mid players (e.g. Faker, Chovy)
- [ ] Compare CS diff curve and roaming timing against personal data on same champions

---

## Current Status

```
Matches collected    : 513 (386 games on Season 16, 127 games on Season 15 — S15 excluded from feature matrix)
Timelines collected  : 513 (15,273 timeline rows)
Feature matrix       : 386 rows, 19 columns, 0 NULL — Season 16 only
Clustering           : trained — 386 labels, silhouette 0.226, cluster sizes 76 / 24 / 169 / 117
Dashboard            : not started
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
| Deployment uses committed `data/lol_deploy.duckdb` | Streamlit Cloud has no persistent disk; S3/LFS adds infra complexity for <10 MB; simple git commit is correct at this scale |

### Deployment notes (Phase 4)

Two DuckDB files, two different purposes:
- `data/lol.duckdb` — development DB, gitignored, rebuilt locally from raw JSON
- `data/lol_deploy.duckdb` — production read-only artifact, committed to git, read by the dashboard

To update deployed data: regenerate `lol_deploy.duckdb` locally and commit the new file. The dashboard must read from `lol_deploy.duckdb`, not `lol.duckdb`.

---

## Known Issues

None.

---

## Notes

- Vietnam routing: `asia` for account-v1, `vn1` for summoner/league, `sea` for match-v5
- Free API key expires every 24h — regenerate at `developer.riotgames.com`
- Summoner identity is `GameName#TAG` (e.g. `PlayerName#VN1`); PUUID is fetched once and stored in `.env`
