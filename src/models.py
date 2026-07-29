from __future__ import annotations

import json
import warnings
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
CENTROID_SNAPSHOT_FILE = "cluster_centroids.json"


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


def _guard_cluster_name_binding(
    profile: pd.DataFrame,
    scaler: StandardScaler,
    snapshot_path: Path,
) -> None:
    expected_ids = list(range(N_CLUSTERS))
    current_profile = profile.copy()
    current_profile.index = current_profile.index.astype(int)
    if sorted(current_profile.index.tolist()) != expected_ids:
        raise ValueError(
            f"Expected centroid profiles for cluster IDs {expected_ids}, "
            f"got {sorted(current_profile.index.tolist())}."
        )
    current_centroids = current_profile.loc[expected_ids, FEATURE_COLS].to_numpy(
        dtype=float
    )

    if not snapshot_path.exists():
        snapshot = {
            "feature_cols": FEATURE_COLS,
            "feature_scales": {
                column: float(scale)
                for column, scale in zip(FEATURE_COLS, scaler.scale_, strict=True)
            },
            "centroids": {
                str(cluster_id): {
                    column: float(current_profile.loc[cluster_id, column])
                    for column in FEATURE_COLS
                }
                for cluster_id in expected_ids
            },
        }
        snapshot_path.write_text(
            json.dumps(snapshot, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            f"No named centroid snapshot existed. Candidate saved to {snapshot_path}. "
            "Refusing to persist models or labels; review it, then rerun."
        )

    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        expected_keys = {str(cluster_id) for cluster_id in expected_ids}
        if snapshot["feature_cols"] != FEATURE_COLS:
            raise ValueError("feature_cols do not match FEATURE_COLS")
        if set(snapshot["centroids"]) != expected_keys:
            raise ValueError(f"centroid IDs must be {sorted(expected_keys)}")
        if set(snapshot["feature_scales"]) != set(FEATURE_COLS):
            raise ValueError("feature_scales do not match FEATURE_COLS")
        if any(
            set(snapshot["centroids"][cluster_id]) != set(FEATURE_COLS)
            for cluster_id in expected_keys
        ):
            raise ValueError("centroid features do not match FEATURE_COLS")

        named_centroids = np.asarray(
            [
                [
                    snapshot["centroids"][str(cluster_id)][column]
                    for column in FEATURE_COLS
                ]
                for cluster_id in expected_ids
            ],
            dtype=float,
        )
        feature_scales = np.asarray(
            [snapshot["feature_scales"][column] for column in FEATURE_COLS],
            dtype=float,
        )
        if not np.isfinite(named_centroids).all():
            raise ValueError("centroids contain non-finite values")
        if not np.isfinite(feature_scales).all() or (feature_scales <= 0).any():
            raise ValueError("feature_scales must be finite and positive")
    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid centroid snapshot at {snapshot_path}: {exc}") from exc

    distances = np.linalg.norm(
        (
            current_centroids[:, np.newaxis, :]
            - named_centroids[np.newaxis, :, :]
        )
        / feature_scales,
        axis=2,
    )
    nearest_ids = distances.argmin(axis=1)
    nearest_distances = distances.min(axis=1)
    same_id_distances = distances.diagonal()
    drifted_ids = [
        cluster_id
        for cluster_id in expected_ids
        if nearest_distances[cluster_id] < same_id_distances[cluster_id]
    ]
    if drifted_ids:
        details = "; ".join(
            f"cluster_id {cluster_id} is closest to named cluster_id "
            f"{nearest_ids[cluster_id]} (standardized distance "
            f"{nearest_distances[cluster_id]:.3f}) instead of its own named "
            f"centroid (distance {same_id_distances[cluster_id]:.3f}, margin "
            f"{same_id_distances[cluster_id] - nearest_distances[cluster_id]:.3f})"
            for cluster_id in drifted_ids
        )
        message = (
            f"Cluster name binding drift detected: {details}. Refusing to persist "
            "models or labels; review the cluster names and centroid snapshot."
        )
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        raise RuntimeError(message)

    print(f"Named centroid binding verified -> {snapshot_path}")


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
    _guard_cluster_name_binding(
        profile,
        scaler,
        models_dir / CENTROID_SNAPSHOT_FILE,
    )
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
