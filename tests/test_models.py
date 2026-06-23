from __future__ import annotations

from pathlib import Path

import duckdb
import joblib
import pandas as pd
import pytest

from src.models import FEATURE_COLS, fit_clusters, train_and_persist


def _feature_frame() -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for group in range(4):
        for sample in range(3):
            row: dict[str, float | str] = {"match_id": f"match_{group}_{sample}"}
            for index, column in enumerate(FEATURE_COLS):
                row[column] = group * 10.0 + sample * 0.1 + index * 0.01
            rows.append(row)
    return pd.DataFrame(rows)


def test_train_and_persist_writes_artifacts_and_labels(tmp_path: Path) -> None:
    conn = duckdb.connect(":memory:")
    feature_df = _feature_frame()
    conn.register("_feature_fixture", feature_df)
    conn.execute("CREATE TABLE feature_matrix AS SELECT * FROM _feature_fixture")
    conn.unregister("_feature_fixture")

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
    pd.testing.assert_frame_equal(derived_profile, profile, check_dtype=False)
    assert 0.0 <= score <= 1.0
    assert model.n_clusters == 4
    assert model.random_state == 42
    assert model.n_init == 20
    assert scaler.n_features_in_ == len(FEATURE_COLS)
    conn.close()


def test_fit_clusters_rejects_null_features() -> None:
    feature_df = _feature_frame()
    feature_df.loc[0, "gold_delta"] = None

    with pytest.raises(ValueError, match="NULL values"):
        fit_clusters(feature_df)
