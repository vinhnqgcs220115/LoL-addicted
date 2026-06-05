# Project Context

**Phase:** 1 — Data Collection
**Last updated:** 2026-06-05

---

## Roadmap

### Phase 1 — Data Collection
- [x] Scaffold `src/collector.py`: `get_puuid()`, `get_match_ids()`, `get_match_detail()`, `get_match_timeline()`
- [x] Scaffold `src/processor.py`: `init_schema()`, `process_match()`
- [x] Run full pipeline end-to-end
- [x] Verify: 100 rows in `matches`, 2,980 rows in `match_timelines`

### Phase 2 — EDA & Feature Engineering
- [ ] `notebooks/01_eda.ipynb`: win rate by champion/role/hour, KDA distribution, heatmaps
- [ ] `src/features.py`: `early_game_score`, `tilt_index`, `champion_games_so_far`, temporal features
- [ ] Verify: `feature_matrix` table populated, no NaN values

### Phase 3 — ML Models
- [ ] `notebooks/02_win_prediction.ipynb`: XGBoost classifier, ROC-AUC ≥ 0.60, feature importance chart
- [ ] `notebooks/03_clustering.ipynb`: K-Means on game stats, label clusters with meaningful names
- [ ] `models/win_predictor.pkl` saved and loadable

### Phase 4 — Dashboard & Deploy
- [ ] `dashboard/app.py`: Overview / Champions / Patterns / Predictor tabs
- [ ] Deployed to Streamlit Cloud with public URL
- [ ] `README.md` with screenshots and live demo link

---

## Current Status

```
Matches collected    : 102 / 10000
Timelines collected  : 102 / 10000 (3,045 timeline rows)
Feature matrix       : not built
Win predictor        : not trained
Clustering           : not trained
Dashboard            : not started
Live URL             : —
```

---

## Decisions Log

| Decision | Rationale |
|---|---|
| DuckDB over SQLite | Window functions and analytical queries without a server |
| XGBoost over sklearn RF | Better tabular performance; handles categoricals natively |
| Plotly over Matplotlib | Interactive charts required in Streamlit |
| `requests` over `httpx` | Sync is sufficient at this data scale; simpler API |
| Ranked Solo/Duo only (queue=420) | Cleaner signal; removes ARAM and normal queue noise |
| Raw JSON saved before processing | Allows re-processing without re-hitting the API |

---

## Known Issues

None yet.

---

## Notes

- Vietnam routing: `asia` for account-v1, `vn1` for summoner/league, `sea` for match-v5
- Free API key expires every 24h — regenerate at `developer.riotgames.com`
- Summoner identity is `GameName#TAG` (e.g. `PlayerName#VN1`); PUUID is fetched once and stored in `.env`