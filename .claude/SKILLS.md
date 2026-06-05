# Skills

---

## riot-data-collector

```yaml
name: riot-data-collector
description: >
  Fetches match data from the Riot Games API and persists raw responses to disk.
  Use when adding new endpoints, extending what data is collected, or debugging
  collection failures.
compatibility: requests, python-dotenv
```

### Trigger Guidance

- **Use when**: Adding new Riot API endpoints, running initial data collection, re-fetching missing matches, debugging 4xx/5xx errors from the API
- **Do NOT use when**: Transforming or analyzing already-collected data — that belongs in `processor.py` or `features.py`

### Workflow

1. Check whether `data/raw/{match_id}.json` already exists. If it does, skip the API call entirely.
2. Call the appropriate endpoint via `riot_get_safe()`.
3. Persist the raw response immediately with `save_raw()` before doing anything else.
4. Return only success/failure status — never transform in-flight.

### Decision Rules

- **If HTTP 429**: read `Retry-After` header, wait that many seconds + 1, retry up to 3 times
- **If HTTP 404**: match does not exist or is unavailable; skip silently and log the ID
- **If HTTP 403**: API key is expired; raise immediately with a clear message pointing to `developer.riotgames.com`
- **If raw file already exists**: skip API call, treat as success

### Output

A saved file at `data/raw/{match_id}.json`. No processing, no return value beyond a status flag.

---

## feature-engineer

```yaml
name: feature-engineer
description: >
  Adds or modifies engineered features in the feature matrix.
  Use when introducing new analytical dimensions, improving model inputs,
  or investigating a new hypothesis about performance.
compatibility: pandas, duckdb
```

### Trigger Guidance

- **Use when**: Adding a new feature column, modifying existing feature logic, merging timeline data into the matrix, debugging NaN values in features
- **Do NOT use when**: Collecting raw data, training models, or building UI components

### Workflow

1. Add new logic inside `build_feature_matrix()` in `features.py`.
2. Source all data from DuckDB tables — never read from `data/raw/` directly.
3. For timeline-based features, query `match_timelines` and merge on `match_id`.
4. Fill all NaN values explicitly before returning — never leave them for the model layer to handle.

### Decision Rules

- **If a feature needs a column not yet in DuckDB**: add it to `processor.py` first and re-run ingestion, then build the feature
- **If a feature uses a rolling window**: always `.shift(1)` to prevent data leakage from the current match
- **If a feature is categorical**: leave as-is for XGBoost (handles natively) or encode as integer — do not one-hot encode unless specifically required
- **If adding a feature for model training**: also add it to `FEATURE_COLS` in `models.py`

### Output

A new column present in the DataFrame returned by `build_feature_matrix()`. The column must have no NaN values and a documented meaning in a comment above its calculation.

---

## model-trainer

```yaml
name: model-trainer
description: >
  Trains, evaluates, and saves ML models from the feature matrix.
  Use when building a new model, tuning an existing one, or generating
  evaluation artifacts for the portfolio.
compatibility: xgboost, scikit-learn, joblib, pandas
```

### Trigger Guidance

- **Use when**: Training a new classifier or clustering model, tuning hyperparameters, regenerating evaluation metrics, saving a new model version
- **Do NOT use when**: Building features (that's `features.py`), fetching data, or rendering results (that's the dashboard)

### Workflow

1. Load the feature matrix from DuckDB via `build_feature_matrix()`.
2. Define `FEATURE_COLS` explicitly — no dynamic column selection.
3. Fill NaN values before splitting.
4. Split with `train_test_split(..., stratify=y)` for classification tasks.
5. Train, evaluate, and print key metrics before saving.
6. Save with `joblib.dump()` to `models/`.

### Decision Rules

- **If ROC-AUC < 0.55**: do not save the model; investigate feature quality or class balance first
- **If training set < 50 samples**: note the limitation in a comment; results will be unreliable
- **For clustering**: always scale features with `StandardScaler` before fitting; raw magnitudes will dominate
- **For win prediction**: use `XGBClassifier` with `device="cpu"` — no CUDA available
- **If saving a new model version**: overwrite `models/win_predictor.pkl` rather than versioning files; version control handles history

### Output Format

Console output during training must include:

```
ROC-AUC : 0.XXX
Accuracy: 0.XXX
[classification_report output]
Saved → models/win_predictor.pkl
```