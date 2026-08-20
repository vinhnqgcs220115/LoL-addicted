from __future__ import annotations

import json
import warnings
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src import models
from src.models import (
    CENTROID_SNAPSHOT_FILE,
    FEATURE_COLS,
    fit_clusters,
    query_cluster_summary,
    query_gold_trajectories,
    train_and_persist,
)


def _feature_frame() -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for group in range(4):
        for sample in range(3):
            row: dict[str, float | str] = {"match_id": f"match_{group}_{sample}"}
            for index, column in enumerate(FEATURE_COLS):
                row[column] = group * 10.0 + sample * 0.1 + index * 0.01
            rows.append(row)
    return pd.DataFrame(rows)


def _fit_clusters_with_swapped_ids(
    feature_df: pd.DataFrame,
) -> tuple[KMeans, StandardScaler, np.ndarray, float]:
    model, scaler, labels, score = fit_clusters(feature_df)
    permutation = np.array([1, 0, 2, 3])
    # A real renumbering moves the model's own centres with the labels; permuting
    # only the labels would leave the fixture in a state K-Means never produces.
    model.cluster_centers_ = model.cluster_centers_[np.argsort(permutation)]
    return model, scaler, permutation[labels], score


def _create_centroid_snapshot_candidate(
    conn: duckdb.DuckDBPyConnection,
    models_dir: Path,
) -> None:
    with pytest.raises(RuntimeError, match="No named centroid snapshot existed"):
        train_and_persist(conn, models_dir)
    assert (models_dir / CENTROID_SNAPSHOT_FILE).is_file()
    assert not (models_dir / "kmeans.pkl").exists()
    assert not (models_dir / "scaler.pkl").exists()


def test_train_and_persist_writes_artifacts_and_labels(tmp_path: Path) -> None:
    conn = duckdb.connect(":memory:")
    feature_df = _feature_frame()
    conn.register("_feature_fixture", feature_df)
    conn.execute("CREATE TABLE feature_matrix AS SELECT * FROM _feature_fixture")
    conn.unregister("_feature_fixture")

    _create_centroid_snapshot_candidate(conn, tmp_path)
    profile, score = train_and_persist(conn, tmp_path)

    labels = conn.execute(
        "SELECT match_id, cluster_id FROM cluster_labels ORDER BY match_id"
    ).fetchall()
    derived_profile = conn.execute(f"""
        SELECT cluster_id, {", ".join(f"AVG({column}) AS {column}" for column in FEATURE_COLS)}
        FROM feature_matrix
        JOIN cluster_labels USING (match_id)
        GROUP BY cluster_id
        ORDER BY cluster_id
    """).df().set_index("cluster_id")
    model = joblib.load(tmp_path / "kmeans.pkl")
    scaler = joblib.load(tmp_path / "scaler.pkl")

    assert len(labels) == len(feature_df)
    assert len({cluster_id for _, cluster_id in labels}) == 4
    assert list(profile.columns) == FEATURE_COLS
    pd.testing.assert_frame_equal(
        derived_profile,
        profile,
        check_dtype=False,
        check_index_type=False,
    )
    assert 0.0 <= score <= 1.0
    assert model.n_clusters == 4
    assert model.random_state == 42
    assert model.n_init == 20
    assert scaler.n_features_in_ == len(FEATURE_COLS)
    snapshot = json.loads(
        (tmp_path / CENTROID_SNAPSHOT_FILE).read_text(encoding="utf-8")
    )
    assert snapshot["feature_cols"] == FEATURE_COLS
    assert set(snapshot["feature_scales"]) == set(FEATURE_COLS)
    assert set(snapshot["centroids"]) == {"0", "1", "2", "3"}
    conn.close()


def test_fit_clusters_rejects_null_features() -> None:
    feature_df = _feature_frame()
    feature_df.loc[0, "gold_delta"] = None

    with pytest.raises(ValueError, match="NULL values"):
        fit_clusters(feature_df)


def _populated_connection(tmp_path: Path) -> tuple[duckdb.DuckDBPyConnection, pd.DataFrame]:
    conn = duckdb.connect(":memory:")
    feature_df = _feature_frame()
    conn.register("_feature_fixture", feature_df)
    conn.execute("CREATE TABLE feature_matrix AS SELECT * FROM _feature_fixture")
    conn.unregister("_feature_fixture")
    _create_centroid_snapshot_candidate(conn, tmp_path)
    train_and_persist(conn, tmp_path)
    return conn, feature_df


def test_unchanged_retrain_produces_no_binding_warning(tmp_path: Path) -> None:
    conn, _feature_df = _populated_connection(tmp_path)
    snapshot_path = tmp_path / CENTROID_SNAPSHOT_FILE
    original_snapshot = snapshot_path.read_bytes()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        train_and_persist(conn, tmp_path)

    assert caught == []
    assert snapshot_path.read_bytes() == original_snapshot
    conn.close()


def test_renumbered_clusters_are_remapped_not_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A clean renumbering must be undone, not turned into a manual decision.

    K-Means IDs reshuffle whenever the dataset grows, so refusing every
    renumbering meant a decision on essentially every refresh.
    """
    conn, _feature_df = _populated_connection(tmp_path)
    original_labels = conn.execute(
        "SELECT match_id, cluster_id FROM cluster_labels ORDER BY match_id"
    ).fetchall()
    monkeypatch.setattr("src.models.fit_clusters", _fit_clusters_with_swapped_ids)

    train_and_persist(conn, tmp_path)

    remapped_labels = conn.execute(
        "SELECT match_id, cluster_id FROM cluster_labels ORDER BY match_id"
    ).fetchall()
    # The swap is undone, so every game keeps the cluster it was already in.
    assert remapped_labels == original_labels

    # The persisted model predicts named IDs, not this run's raw ones.
    model = joblib.load(tmp_path / "kmeans.pkl")
    scaler = joblib.load(tmp_path / "scaler.pkl")
    features = conn.execute(
        f"SELECT {', '.join(FEATURE_COLS)} FROM feature_matrix ORDER BY match_id"
    ).df()
    predicted = model.predict(scaler.transform(features))
    stored = [cluster_id for _match_id, cluster_id in remapped_labels]
    assert list(predicted) == stored
    conn.close()


def test_ambiguous_binding_still_refuses(tmp_path: Path) -> None:
    """Two clusters nearest the same name is real drift, and must not persist."""
    snapshot_path = tmp_path / CENTROID_SNAPSHOT_FILE
    snapshot_path.write_text(
        json.dumps({
            "feature_cols": FEATURE_COLS,
            "feature_scales": {column: 1.0 for column in FEATURE_COLS},
            "centroids": {
                str(cluster_id): {
                    column: float(cluster_id * 10) for column in FEATURE_COLS
                }
                for cluster_id in range(4)
            },
        }),
        encoding="utf-8",
    )

    # Clusters 0 and 1 both sit on top of named centroid 0.
    profile = pd.DataFrame(
        [
            {column: 0.0 for column in FEATURE_COLS},
            {column: 0.1 for column in FEATURE_COLS},
            {column: 20.0 for column in FEATURE_COLS},
            {column: 30.0 for column in FEATURE_COLS},
        ],
        index=pd.Index([0, 1, 2, 3], name="cluster_id"),
    )
    scaler = StandardScaler()
    scaler.scale_ = np.ones(len(FEATURE_COLS))

    with pytest.warns(RuntimeWarning, match="ambiguous"):
        with pytest.raises(RuntimeError, match="Refusing to persist models or labels"):
            models._align_clusters_to_names(profile, scaler, snapshot_path)


def test_query_cluster_summary_returns_complete_feature_means(tmp_path: Path) -> None:
    conn, _feature_df = _populated_connection(tmp_path)

    summary = query_cluster_summary(conn)

    assert len(summary) == 4
    assert list(summary.columns) == ["cluster_id", "size", *FEATURE_COLS]
    assert not summary.isna().any().any()
    conn.close()


def test_query_gold_trajectories_filters_sparse_cluster_minutes(tmp_path: Path) -> None:
    conn, feature_df = _populated_connection(tmp_path)
    timeline_rows = [
        {
            "match_id": match_id,
            "timestamp_min": minute,
            "gold": 500 + minute * 300,
        }
        for match_id in feature_df["match_id"]
        for minute in range(11)
    ]
    labels = conn.execute(
        "SELECT match_id, cluster_id FROM cluster_labels ORDER BY match_id"
    ).df()
    for match_id in labels.groupby("cluster_id")["match_id"].first():
        timeline_rows.append({"match_id": match_id, "timestamp_min": 11, "gold": 3800})
    timeline_df = pd.DataFrame(timeline_rows)
    conn.register("_timeline_fixture", timeline_df)
    conn.execute("CREATE TABLE match_timelines AS SELECT * FROM _timeline_fixture")
    conn.unregister("_timeline_fixture")

    trajectories = query_gold_trajectories(conn)
    counts = conn.execute("""
        SELECT l.cluster_id, t.timestamp_min, COUNT(*) AS match_count
        FROM cluster_labels l
        JOIN match_timelines t USING (match_id)
        GROUP BY l.cluster_id, t.timestamp_min
    """).df()
    sizes = labels.groupby("cluster_id").size().rename("cluster_size")
    counts = counts.join(sizes, on="cluster_id")
    counts["threshold"] = (counts["cluster_size"] * 0.5).round().clip(lower=3)
    retained = counts.merge(
        trajectories[["cluster_id", "timestamp_min"]],
        on=["cluster_id", "timestamp_min"],
    )

    assert {"cluster_id", "timestamp_min", "avg_gold"} <= set(trajectories.columns)
    assert np.isfinite(trajectories["avg_gold"]).all()
    assert trajectories.groupby("cluster_id")["timestamp_min"].apply(
        lambda minutes: minutes.is_monotonic_increasing
    ).all()
    assert (retained["match_count"] >= retained["threshold"]).all()
    assert (counts["match_count"] < counts["threshold"]).any()
    assert 11 not in trajectories["timestamp_min"].tolist()
    conn.close()
