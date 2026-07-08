from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from scripts import build_deploy_db


def _create_source_db(path: Path, feature_columns: tuple[str, ...]) -> None:
    with duckdb.connect(str(path)) as conn:
        conn.execute("""
            CREATE TABLE matches (
                match_id VARCHAR PRIMARY KEY,
                game_datetime VARCHAR NOT NULL,
                game_version VARCHAR NOT NULL,
                queue_id INTEGER NOT NULL,
                game_duration_sec INTEGER NOT NULL,
                champion_id INTEGER NOT NULL,
                champion_name VARCHAR NOT NULL,
                team_id INTEGER NOT NULL,
                team_position VARCHAR,
                lane VARCHAR,
                win BOOLEAN NOT NULL,
                kills INTEGER NOT NULL,
                deaths INTEGER NOT NULL,
                assists INTEGER NOT NULL,
                kda DOUBLE NOT NULL,
                cs_total INTEGER NOT NULL,
                cs_per_min DOUBLE NOT NULL,
                gold_earned INTEGER NOT NULL,
                damage_dealt_to_champions INTEGER NOT NULL,
                vision_score INTEGER NOT NULL,
                opp_champion_name VARCHAR,
                opp_cs_total INTEGER,
                opp_gold_earned INTEGER,
                opp_kills INTEGER,
                opp_deaths INTEGER,
                opp_assists INTEGER
            )
        """)
        conn.execute("""
            INSERT INTO matches VALUES (
                'MATCH_1', ?, '16.1', 420, 1800, 1, 'Ahri', 100, ?, 'MID', true,
                5, 1, 4, 9.0, 180, 6.0, 12000, 20000, 30,
                'Orianna', 170, 11000, 2, 4, 3
            )
        """, [build_deploy_db.CURRENT_SEASON_START, build_deploy_db.ANALYSIS_ROLE])
        conn.execute("""
            CREATE TABLE match_timelines (
                match_id VARCHAR,
                timestamp_min INTEGER,
                gold INTEGER,
                cs INTEGER,
                xp INTEGER,
                kills INTEGER,
                position_x INTEGER,
                position_y INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE match_deaths (
                match_id VARCHAR,
                death_number INTEGER,
                timestamp_ms INTEGER,
                timestamp_min INTEGER,
                gold_at_death INTEGER,
                cs_at_death INTEGER
            )
        """)
        column_sql = ", ".join(f'"{column}" VARCHAR' for column in feature_columns)
        value_sql = ", ".join("?" for _ in feature_columns)
        conn.execute(f"CREATE TABLE feature_matrix ({column_sql})")
        conn.execute(
            f"INSERT INTO feature_matrix VALUES ({value_sql})",
            ["MATCH_1" if column == "match_id" else "0" for column in feature_columns],
        )
        conn.execute("""
            CREATE TABLE cluster_labels (
                match_id VARCHAR PRIMARY KEY,
                cluster_id INTEGER NOT NULL
            )
        """)
        conn.execute("INSERT INTO cluster_labels VALUES ('MATCH_1', 0)")


def test_build_deploy_db_rejects_unexpected_feature_matrix_columns(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_db = tmp_path / "source.duckdb"
    deploy_db = tmp_path / "deploy.duckdb"
    _create_source_db(
        source_db,
        (*build_deploy_db.FEATURE_MATRIX_COLUMNS, "unreviewed_metric"),
    )

    monkeypatch.setattr(build_deploy_db, "SOURCE_DB", source_db)
    monkeypatch.setattr(build_deploy_db, "DEPLOY_DB", deploy_db)

    with pytest.raises(ValueError) as excinfo:
        build_deploy_db.build_deploy_db()

    message = str(excinfo.value)
    assert "source.feature_matrix" in message
    assert "missing columns: none" in message
    assert "unexpected columns: unreviewed_metric" in message
    assert not deploy_db.exists()