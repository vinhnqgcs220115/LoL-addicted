from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from scripts import build_deploy_db
from src import processor


def _create_source_db(path: Path, feature_columns: tuple[str, ...]) -> None:
    """Build a source database using the real schema.

    The schema is taken from ``processor.init_schema`` rather than restated
    here. A hand-copied version silently drifts the moment a column is added,
    which is exactly how this fixture broke when the timeline gained the
    opponent columns.
    """
    with duckdb.connect(str(path)) as conn:
        processor.init_schema(conn)

        conn.execute(
            f"""
            INSERT INTO matches ({", ".join(processor.MATCH_COLUMNS)})
            VALUES ({", ".join("?" for _ in processor.MATCH_COLUMNS)})
            """,
            [
                "MATCH_1", "test-puuid", build_deploy_db.CURRENT_SEASON_START,
                "16.1", 420, 1800, 1, "Ahri", 100,
                build_deploy_db.ANALYSIS_ROLE, "MID", True,
                5, 1, 4, 9.0, 180, 6.0, 12000, 20000, 30,
                "Orianna", 170, 11000, 2, 4, 3,
            ],
        )
        conn.execute(
            """
            INSERT INTO roam_windows
                (match_id, roam_start_min, roam_end_min, kills_during_roam, roam_result)
            VALUES ('MATCH_1', 5, 6, 1, 'impact')
            """
        )
        conn.execute(
            """
            INSERT INTO match_events
                (match_id, event_number, timestamp_ms, timestamp_min, event_type,
                 position_x, position_y, player_involvement, is_player_team, detail)
            VALUES ('MATCH_1', 1, 300000, 5, 'CHAMPION_KILL',
                    6550, 7187, 'actor', true, NULL)
            """
        )
        # An event with no player involvement and no objective type must not be
        # published; the deployment snapshot only carries what a view can use.
        conn.execute(
            """
            INSERT INTO match_events
                (match_id, event_number, timestamp_ms, timestamp_min, event_type,
                 position_x, position_y, player_involvement, is_player_team, detail)
            VALUES ('MATCH_1', 2, 360000, 6, 'TURRET_PLATE_DESTROYED',
                    100, 200, NULL, false, NULL)
            """
        )

        # init_schema does not create feature_matrix; features.py does.
        conn.execute("DROP TABLE IF EXISTS feature_matrix")
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


def test_build_deploy_db_copies_roam_windows_with_surrogate_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_db = tmp_path / "source.duckdb"
    deploy_db = tmp_path / "deploy.duckdb"
    _create_source_db(source_db, build_deploy_db.FEATURE_MATRIX_COLUMNS)

    monkeypatch.setattr(build_deploy_db, "SOURCE_DB", source_db)
    monkeypatch.setattr(build_deploy_db, "DEPLOY_DB", deploy_db)

    counts = build_deploy_db.build_deploy_db()
    with duckdb.connect(str(deploy_db), read_only=True) as conn:
        rows = conn.execute("""
            SELECT match_id, roam_start_min, roam_end_min, kills_during_roam, roam_result
            FROM roam_windows
        """).fetchall()

    assert counts["roam_windows"] == 1
    assert rows == [("GAME_0001", 5, 6, 1, "impact")]


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


def test_build_deploy_db_publishes_only_usable_events(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Events nothing can read are left in the source database."""
    source_path = tmp_path / "source.duckdb"
    deploy_path = tmp_path / "deploy.duckdb"
    _create_source_db(source_path, build_deploy_db.FEATURE_MATRIX_COLUMNS)
    monkeypatch.setattr(build_deploy_db, "SOURCE_DB", source_path)
    monkeypatch.setattr(build_deploy_db, "DEPLOY_DB", deploy_path)

    build_deploy_db.build_deploy_db()

    with duckdb.connect(str(deploy_path), read_only=True) as conn:
        events = conn.execute(
            "SELECT event_type, player_involvement FROM match_events"
        ).fetchall()

    # The player's kill is published; the unrelated plate is not.
    assert events == [("CHAMPION_KILL", "actor")]


def test_build_deploy_db_carries_the_opponent_timeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The opponent columns must survive into the deployed snapshot.

    They are the whole point of the reparse: without them the dashboard is back
    to comparing the player against their own average.
    """
    source_path = tmp_path / "source.duckdb"
    deploy_path = tmp_path / "deploy.duckdb"
    _create_source_db(source_path, build_deploy_db.FEATURE_MATRIX_COLUMNS)
    with duckdb.connect(str(source_path)) as conn:
        conn.execute(
            """
            INSERT INTO match_timelines
                (match_id, timestamp_min, gold, cs, xp, level, kills,
                 position_x, position_y, opp_gold, opp_cs, opp_xp, opp_level,
                 opp_position_x, opp_position_y, team_gold, enemy_team_gold)
            VALUES ('MATCH_1', 14, 6000, 120, 7000, 11, 2,
                    7000, 7100, 5200, 105, 6400, 10, 8000, 8100, 30000, 28000)
            """
        )
    monkeypatch.setattr(build_deploy_db, "SOURCE_DB", source_path)
    monkeypatch.setattr(build_deploy_db, "DEPLOY_DB", deploy_path)

    build_deploy_db.build_deploy_db()

    with duckdb.connect(str(deploy_path), read_only=True) as conn:
        row = conn.execute(
            """
            SELECT gold - opp_gold, cs - opp_cs, xp - opp_xp, level - opp_level,
                   team_gold - enemy_team_gold
            FROM match_timelines WHERE timestamp_min = 14
            """
        ).fetchone()

    assert row == (800, 15, 600, 1, 2000)
