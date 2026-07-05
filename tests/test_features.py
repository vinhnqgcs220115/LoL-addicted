from __future__ import annotations

import duckdb

from src import processor
from src.features import (
    build_feature_matrix,
    champion_matchup_stats,
    death_context,
    is_throw_game,
    roam_timing,
    tilt_index,
)

S15_DATETIME = "2025-12-15T12:00:00+00:00"  # before CURRENT_SEASON_START
S16_DATETIME_A = "2026-01-15T12:00:00+00:00"  # after CURRENT_SEASON_START
S16_DATETIME_B = "2026-02-01T12:00:00+00:00"
S16_DATETIME_C = "2026-02-15T12:00:00+00:00"
S16_DATETIME_D = "2026-03-01T12:00:00+00:00"


def _make_conn() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection with minimal schema and fixture data."""
    conn = duckdb.connect(":memory:")
    processor.init_schema(conn)

    # --- Season 15 match (should be excluded by season filter) ---
    conn.execute("""
        INSERT INTO matches VALUES (
            'S15_MATCH', 'puuid1', ?, '15.24', 420,
            1800, 1, 'Zed', 100, 'MIDDLE', 'MID', true,
            5, 2, 3, 4.0, 180, 6.0, 12000, 20000, 30,
            'Viktor', 160, 11000, 2, 3, 1
        )
    """, [S15_DATETIME])

    # --- Season 16 matches ---
    s16_rows = [
        ("S16_A", S16_DATETIME_A, True,  "Zed",    5, 2, 3, 180),
        ("S16_B", S16_DATETIME_B, False, "Zed",    4, 5, 2, 160),
        ("S16_C", S16_DATETIME_C, True,  "Katarina", 6, 1, 4, 200),
        ("S16_D", S16_DATETIME_D, False, "Zed",    3, 4, 5, 140),
    ]
    for match_id, dt, win, champ, k, d, a, cs in s16_rows:
        kda = (k + a) / max(d, 1)
        conn.execute("""
            INSERT INTO matches VALUES (
                ?, 'puuid1', ?, '16.1', 420,
                1800, 1, ?, 100, 'MIDDLE', 'MID', ?,
                ?, ?, ?, ?, ?, 6.0, 12000, 20000, 30,
                'Viktor', 150, 11000, 2, 3, 1
            )
        """, [match_id, dt, champ, win, k, d, a, kda, cs])

    # --- Timelines for S16 matches (minutes 0–20) ---
    for match_id in ("S15_MATCH", "S16_A", "S16_B", "S16_C", "S16_D"):
        for minute in range(21):
            gold = 500 + minute * 250
            cs = minute * 8
            conn.execute("""
                INSERT INTO match_timelines VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [match_id, minute, gold, cs, minute * 100, 0, 7500 + minute * 10, 7500 + minute * 10])

    # --- Deaths for S16_A: 4 deaths, deaths 2/3/4 are consecutive (tilt spiral) ---
    # death 1: minute 5 (no previous → not tilt spiral)
    # death 2: minute 7 (gap 2 → tilt spiral)
    # death 3: minute 9 (gap 2 → tilt spiral)
    # death 4: minute 11 (gap 2 → tilt spiral)
    conn.execute("INSERT INTO match_deaths VALUES ('S16_A', 1, 300000, 5, 2750, 40)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_A', 2, 420000, 7, 3250, 56)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_A', 3, 540000, 9, 3750, 72)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_A', 4, 660000, 11, 4250, 88)")

    # --- Deaths for S16_B: 5 deaths, deaths 4/5 are consecutive ---
    conn.execute("INSERT INTO match_deaths VALUES ('S16_B', 1, 180000, 3, 2000, 24)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_B', 2, 480000, 8, 3500, 64)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_B', 3, 720000, 12, 4500, 96)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_B', 4, 840000, 14, 5000, 112)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_B', 5, 900000, 15, 5250, 120)")

    # S16_C: no deaths — tests zero-death handling
    # S16_D: 2 deaths far apart — no tilt spiral
    conn.execute("INSERT INTO match_deaths VALUES ('S16_D', 1, 180000, 3, 2000, 24)")
    conn.execute("INSERT INTO match_deaths VALUES ('S16_D', 2, 900000, 15, 5000, 120)")

    return conn


def test_build_feature_matrix_season_filter() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    assert "S15_MATCH" not in fm["match_id"].values
    s16_ids = {"S16_A", "S16_B", "S16_C", "S16_D"}
    assert s16_ids == set(fm["match_id"].values)


def test_analytics_exclude_non_mid_matches() -> None:
    conn = _make_conn()
    conn.execute("""
        INSERT INTO matches VALUES (
            'S16_BOTTOM', 'puuid1', ?, '16.1', 420,
            1800, 1, 'Zed', 100, 'BOTTOM', 'BOTTOM', true,
            5, 2, 3, 4.0, 180, 6.0, 12000, 20000, 30,
            'Viktor', 160, 11000, 2, 3, 1
        )
    """, [S16_DATETIME_D])

    fm = build_feature_matrix(conn)
    matchups = champion_matchup_stats(conn)
    conn.close()

    assert "S16_BOTTOM" not in fm["match_id"].values
    zed_matchup = matchups[
        (matchups["champion_name"] == "Zed")
        & (matchups["opp_champion_name"] == "Viktor")
    ].iloc[0]
    assert zed_matchup["games"] == 3


def test_is_throw_game_uses_current_mid_scope() -> None:
    conn = _make_conn()
    result = is_throw_game(conn)
    conn.close()

    assert set(result["match_id"]) == {"S16_A", "S16_B", "S16_C", "S16_D"}
    assert result["gold_delta"].eq(0.0).all()


def test_tilt_index_uses_only_prior_current_season_mid_games() -> None:
    conn = _make_conn()
    result = tilt_index(conn)
    conn.close()

    assert list(result["match_id"]) == ["S16_A", "S16_B", "S16_C", "S16_D"]
    assert list(result["tilt_index"].round(4)) == [0.5, 1.0, 0.5, 0.6667]


def test_roam_timing_detects_two_minute_mid_roam() -> None:
    conn = _make_conn()
    conn.execute("""
        UPDATE match_timelines
        SET position_x = 12000, position_y = 7000
        WHERE match_id = 'S16_A' AND timestamp_min IN (5, 6)
    """)
    result = roam_timing(conn)
    conn.close()

    roam = result[result["match_id"] == "S16_A"].iloc[0]
    assert roam["roam_start_min"] == 5
    assert roam["roam_end_min"] == 6


def test_build_feature_matrix_has_pass_through_columns() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    for col in ("win", "game_datetime", "champion_name"):
        assert col in fm.columns, f"Missing column: {col}"
        assert fm[col].isna().sum() == 0, f"NaN in column: {col}"


def test_tilt_spiral_ratio_bounds() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    assert "tilt_spiral_ratio" in fm.columns
    assert fm["tilt_spiral_ratio"].isna().sum() == 0
    assert (fm["tilt_spiral_ratio"] >= 0.0).all()
    assert (fm["tilt_spiral_ratio"] <= 1.0).all()


def test_tilt_spiral_ratio_zero_deaths() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    # S16_C has no deaths
    row = fm[fm["match_id"] == "S16_C"].iloc[0]
    assert row["tilt_spiral_ratio"] == 0.0
    assert row["max_death_streak"] == 0


def test_max_death_streak_consecutive_count() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    row = fm[fm["match_id"] == "S16_A"].iloc[0]
    assert row["max_death_streak"] == 3


def test_no_nan_in_feature_matrix() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    nan_cols = [col for col in fm.columns if fm[col].isna().any()]
    assert nan_cols == [], f"Columns with NaN: {nan_cols}"


def test_death_context_excludes_s15_deaths() -> None:
    conn = _make_conn()
    conn.execute("INSERT INTO match_deaths VALUES ('S15_MATCH', 1, 300000, 5, 2750, 40)")
    result = death_context(conn)
    conn.close()

    assert "S15_MATCH" not in result["match_id"].values


def test_avg_cs_sacrifice_is_log_transformed() -> None:
    conn = _make_conn()
    fm = build_feature_matrix(conn)
    conn.close()

    assert fm["avg_cs_sacrifice"].min() >= 0
    assert fm["avg_cs_sacrifice"].max() < 5   # log1p(61.4) ≈ 4.12; raw 61.4 would fail this
    assert fm["avg_cs_sacrifice"].isna().sum() == 0
