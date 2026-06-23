from __future__ import annotations

from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "lol.duckdb"
MODELS_DIR = BASE_DIR / "models"

FEATURE_COLS = [
    "gold_delta",
    "total_deaths",
    "deaths_while_ahead",
    "tilt_spiral_ratio",
    "max_death_streak",
    "total_roams",
    "avg_cs_sacrifice",
    "roam_impact_rate",
    "tilt_index",
]

N_CLUSTERS = 4
RANDOM_STATE = 42
N_INIT = 20


def fit_clusters(
    feature_df: pd.DataFrame,
) -> tuple[KMeans, StandardScaler, np.ndarray, float]:
    """Scale the configured features and fit the fixed four-cluster model."""
    missing_columns = [column for column in FEATURE_COLS if column not in feature_df.columns]
    if missing_columns:
        raise ValueError(f"Missing model features: {missing_columns}")
    if len(feature_df) <= N_CLUSTERS:
        raise ValueError(f"K-Means requires more than {N_CLUSTERS} feature rows.")

    features = feature_df[FEATURE_COLS]
    null_columns = features.columns[features.isna().any()].tolist()
    if null_columns:
        raise ValueError(f"NULL values found in model features: {null_columns}")
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ValueError("Non-finite values found in model features.")

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    model = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=N_INIT,
    )
    labels = model.fit_predict(scaled_features)
    score = float(silhouette_score(scaled_features, labels))
    return model, scaler, labels, score


def train_and_persist(
    conn: duckdb.DuckDBPyConnection,
    models_dir: Path = MODELS_DIR,
) -> tuple[pd.DataFrame, float]:
    """Train, report, and persist the clustering pipeline."""
    feature_df = conn.execute(f"""
        SELECT match_id, {", ".join(FEATURE_COLS)}
        FROM feature_matrix
        ORDER BY match_id
    """).df()
    if feature_df.empty:
        raise ValueError("feature_matrix is empty; run the feature pipeline first.")

    model, scaler, labels, score = fit_clusters(feature_df)
    labeled = feature_df[["match_id", *FEATURE_COLS]].copy()
    labeled["cluster_id"] = labels
    profile = labeled.groupby("cluster_id")[FEATURE_COLS].mean().sort_index()
    cluster_sizes = pd.Series(labels).value_counts().sort_index().to_dict()

    print(f"Cluster sizes     : {cluster_sizes}")
    print(f"Silhouette score  : {score:.3f}")
    print("Feature means by cluster:")
    print(profile.round(3).to_string())

    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, models_dir / "kmeans.pkl")
    joblib.dump(scaler, models_dir / "scaler.pkl")

    label_df = pd.DataFrame(
        {
            "match_id": feature_df["match_id"].astype(str),
            "cluster_id": labels.astype(int),
        }
    )
    conn.register("_cluster_labels", label_df)
    try:
        conn.execute("BEGIN")
        conn.execute("DROP TABLE IF EXISTS cluster_labels")
        conn.execute("""
            CREATE TABLE cluster_labels (
                match_id VARCHAR PRIMARY KEY,
                cluster_id INTEGER NOT NULL
            )
        """)
        conn.execute("INSERT INTO cluster_labels SELECT match_id, cluster_id FROM _cluster_labels")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.unregister("_cluster_labels")

    print(f"Saved -> {models_dir / 'kmeans.pkl'}")
    print(f"Saved -> {models_dir / 'scaler.pkl'}")
    print(f"Labels written -> DuckDB cluster_labels ({len(labels)} rows)")
    return profile, score


def query_cluster_summary(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Return cluster sizes and feature means; both source tables must be populated."""
    feature_means = ", ".join(
        f"AVG(f.{column}) AS {column}" for column in FEATURE_COLS
    )
    return conn.execute(f"""
        SELECT
            l.cluster_id,
            COUNT(*)::INTEGER AS size,
            {feature_means}
        FROM cluster_labels l
        JOIN feature_matrix f ON f.match_id = l.match_id
        GROUP BY l.cluster_id
        ORDER BY l.cluster_id
    """).df()


def query_gold_trajectories(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Return sufficiently sampled cluster gold curves; labels and timelines are required."""
    return conn.execute("""
        WITH cluster_sizes AS (
            SELECT cluster_id, COUNT(*) AS cluster_size
            FROM cluster_labels
            GROUP BY cluster_id
        ),
        per_minute AS (
            SELECT
                l.cluster_id,
                t.timestamp_min,
                COUNT(*) AS match_count,
                AVG(t.gold)::DOUBLE AS avg_gold
            FROM cluster_labels l
            JOIN match_timelines t ON t.match_id = l.match_id
            GROUP BY l.cluster_id, t.timestamp_min
        )
        SELECT p.cluster_id, p.timestamp_min, p.avg_gold
        FROM per_minute p
        JOIN cluster_sizes s ON s.cluster_id = p.cluster_id
        WHERE p.match_count >= GREATEST(3, ROUND(s.cluster_size * 0.5))
        ORDER BY p.cluster_id ASC, p.timestamp_min ASC
    """).df()


def run_models() -> None:
    """Train and persist clustering artifacts using the project database."""
    with duckdb.connect(str(DB_PATH)) as conn:
        train_and_persist(conn)


if __name__ == "__main__":
    run_models()
