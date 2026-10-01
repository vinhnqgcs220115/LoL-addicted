from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from src import processor
from src.features import (
    _direction_survives_one_more_game,
    build_feature_matrix,
    champion_matchup_stats,
    binomial_significance,
    classify_winrate,
    champion_archetype_matchups,
    champion_pool,
    core_champions,
    death_context,
    games_to_verdict,
    archetype_winrates,
    pocket_picks,
    is_throw_game,
    roam_timing,
    tilt_index,
    wilson_interval,
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
                INSERT INTO match_timelines
                    (match_id, timestamp_min, gold, cs, xp, kills,
                     position_x, position_y, opp_gold, opp_cs, opp_xp,
                     team_gold, enemy_team_gold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                match_id, minute, gold, cs, minute * 100, 0,
                7500 + minute * 10, 7500 + minute * 10,
                # Opponent trails slightly; S16_B's team is behind at 14 so the
                # throw and comeback definitions have something real to read.
                gold - 200, max(cs - 5, 0), minute * 95,
                gold * 5, (gold * 5) + (2000 if match_id == "S16_B" else -2000),
            ])

    # --- Deaths for S16_A: 4 deaths, deaths 2/3/4 are consecutive (tilt spiral) ---
    # death 1: minute 5 (no previous → not tilt spiral)
    # death 2: minute 7 (gap 2 → tilt spiral)
    # death 3: minute 9 (gap 2 → tilt spiral)
    # death 4: minute 11 (gap 2 → tilt spiral)
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_A', 1, 300000, 5, 2750, 40)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_A', 2, 420000, 7, 3250, 56)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_A', 3, 540000, 9, 3750, 72)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_A', 4, 660000, 11, 4250, 88)")

    # --- Deaths for S16_B: 5 deaths, deaths 4/5 are consecutive ---
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_B', 1, 180000, 3, 2000, 24)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_B', 2, 480000, 8, 3500, 64)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_B', 3, 720000, 12, 4500, 96)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_B', 4, 840000, 14, 5000, 112)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_B', 5, 900000, 15, 5250, 120)")

    # S16_C: no deaths — tests zero-death handling
    # S16_D: 2 deaths far apart — no tilt spiral
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_D', 1, 180000, 3, 2000, 24)")
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S16_D', 2, 900000, 15, 5000, 120)")

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


def test_build_feature_matrix_persists_roam_windows() -> None:
    conn = _make_conn()
    conn.execute("""
        UPDATE match_timelines
        SET position_x = 12000, position_y = 7000,
            kills = CASE WHEN timestamp_min = 6 THEN 1 ELSE kills END
        WHERE match_id = 'S16_A' AND timestamp_min IN (5, 6)
    """)

    fm = build_feature_matrix(conn)
    build_feature_matrix(conn)
    rows = conn.execute("""
        SELECT match_id, roam_start_min, roam_end_min, kills_during_roam, roam_result
        FROM roam_windows
        ORDER BY match_id, roam_start_min
    """).fetchall()
    conn.execute("""
        UPDATE match_timelines
        SET position_x = 7500 + timestamp_min * 10,
            position_y = 7500 + timestamp_min * 10,
            kills = 0
        WHERE match_id = 'S16_A' AND timestamp_min IN (5, 6)
    """)
    refreshed_fm = build_feature_matrix(conn)
    remaining_rows = conn.execute("SELECT COUNT(*) FROM roam_windows").fetchone()[0]
    conn.close()

    assert rows == [("S16_A", 5, 6, 1, "impact")]
    assert len(rows) == int(fm["total_roams"].sum())
    assert remaining_rows == 0
    assert int(refreshed_fm["total_roams"].sum()) == 0


def test_roam_timing_uses_cs_drop_when_position_missing() -> None:
    conn = _make_conn()
    conn.execute("""
        INSERT INTO matches VALUES (
            'S16_E', 'puuid1', ?, '16.1', 420,
            1800, 1, 'Zed', 100, 'MIDDLE', 'MID', true,
            5, 2, 3, 4.0, 180, 6.0, 12000, 20000, 30,
            'Viktor', 160, 11000, 2, 3, 1
        )
    """, [S16_DATETIME_D])
    for minute in range(21):
        conn.execute("""
            INSERT INTO match_timelines
                    (match_id, timestamp_min, gold, cs, xp, kills,
                     position_x, position_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            "S16_E",
            minute,
            500 + minute * 250,
            minute * 8,
            minute * 100,
            0,
            7500 + minute * 10,
            7500 + minute * 10,
        ])
    conn.execute("""
        UPDATE match_timelines
        SET position_x = NULL, position_y = NULL
        WHERE match_id = 'S16_A'
    """)
    conn.execute("""
        UPDATE match_timelines
        SET cs = 0
        WHERE match_id = 'S16_A' AND timestamp_min IN (5, 6)
    """)

    result = roam_timing(conn)
    conn.close()

    roams = result[result["match_id"] == "S16_A"]
    assert len(roams) == 1
    roam = roams.iloc[0]
    assert roam["roam_start_min"] == 5
    assert roam["roam_end_min"] == 6
    assert roam["roam_result"] == "no_impact"


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
    conn.execute("INSERT INTO match_deaths (match_id, death_number, timestamp_ms, timestamp_min, gold_at_death, cs_at_death) VALUES ('S15_MATCH', 1, 300000, 5, 2750, 40)")
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


def test_wilson_interval_widens_as_samples_shrink() -> None:
    """A small sample must not produce a narrow, confident-looking interval."""
    low_small, high_small = wilson_interval(2, 2)
    low_large, high_large = wilson_interval(60, 100)

    assert (high_small - low_small) > (high_large - low_large)
    # 2/2 cannot exclude the baseline; 60/100 can.
    assert low_small < 0.5 < high_small
    assert low_large > 0.5

    # Degenerate input stays maximally uninformative rather than raising.
    assert wilson_interval(0, 0) == (0.0, 1.0)
    # Bounds never escape [0, 1] even at the extremes.
    for wins, games in [(0, 8), (8, 8), (1, 3)]:
        low, high = wilson_interval(wins, games)
        assert 0.0 <= low <= high <= 1.0


def test_classify_winrate_uses_baseline_not_coin_flip() -> None:
    """A verdict is measured against the player's own baseline, not 50%."""
    baseline = 0.60

    # 40 of 100 beats a coin flip but is well below this player's baseline.
    assert classify_winrate(40, 100, baseline) == "Negative"
    assert classify_winrate(80, 100, baseline) == "Positive"
    # Sitting on the baseline is never a verdict, at any sample size.
    assert classify_winrate(60, 100, baseline) == "Uncertain"
    assert classify_winrate(0, 0, baseline) == "Uncertain"


def test_a_perfect_tiny_record_is_not_a_verdict() -> None:
    """4-0 must not clear a ~51% baseline; one loss would reverse it.

    The Wilson interval is a normal approximation and is anti-conservative here:
    it put the lower bound a thousandth above the baseline and rendered a
    verdict. The exact binomial test is what withholds it.
    """
    baseline = 0.509

    assert classify_winrate(4, 4, baseline) == "Uncertain"
    assert binomial_significance(4, 4, baseline) > 0.05
    # A real record at the same rate direction still clears.
    assert classify_winrate(15, 20, baseline) == "Positive"
    assert binomial_significance(15, 20, baseline) < 0.05
    # And the losing side behaves symmetrically.
    assert classify_winrate(2, 11, baseline) == "Negative"


def test_games_to_verdict_scales_with_the_gap_to_baseline() -> None:
    """A near-baseline rate needs far more games than an extreme one."""
    baseline = 0.50

    near = games_to_verdict(0.55, baseline)
    far = games_to_verdict(0.90, baseline)
    assert near is not None and far is not None
    assert near > far

    # A rate sitting exactly on the baseline never separates, at any sample size.
    assert games_to_verdict(0.50, baseline) is None
    # Works in both directions.
    assert games_to_verdict(0.10, baseline) is not None


def test_opponent_archetype_winrates_holds_out_build_dependent() -> None:
    """A build-dependent champion gets its own row and never carries a verdict."""
    conn = _make_conn()
    conn.execute("""
        INSERT INTO matches VALUES (
            'S16_SYLAS', 'puuid1', ?, '16.1', 420,
            1800, 1, 'Zoe', 100, 'MIDDLE', 'MID', true,
            5, 2, 3, 4.0, 180, 6.0, 12000, 20000, 30,
            'Sylas', 150, 11000, 2, 3, 1
        )
    """, [S16_DATETIME_D])
    frame = archetype_winrates(conn, "opponent")
    conn.close()

    by_archetype = frame.set_index("archetype")
    assert "Build-dependent" in by_archetype.index
    assert not bool(by_archetype.loc["Build-dependent", "verdict_eligible"])
    assert by_archetype.loc["Build-dependent", "matchup_class"] == "Uncertain"
    assert int(by_archetype.loc["Build-dependent", "games"]) == 1
    # Sylas must not have been folded into a real archetype bucket.
    assert int(by_archetype.loc["Control Mages", "games"]) == 4


def test_projection_is_withheld_when_one_game_would_undo_it() -> None:
    """A games-needed projection reads as a promise; do not make one from noise."""
    baseline = 0.513

    # 1/1 at 100%: a single loss drops it to 50%, below baseline. Not projectable.
    assert not _direction_survives_one_more_game(1.0, 1, baseline)
    # 0/1 at 0%: one game is not a rate at all.
    assert not _direction_survives_one_more_game(0.0, 1, baseline)
    # 51/114 at 44.7%: one win moves it to 45.2%, still clearly below.
    assert _direction_survives_one_more_game(0.447, 114, baseline)
    # A rate sitting on the baseline has no direction to preserve.
    assert not _direction_survives_one_more_game(baseline, 50, baseline)


def test_core_champions_is_derived_from_usage_not_a_game_count() -> None:
    """The "rarely played" line comes from the player's own pool, not a constant."""
    pool = pd.DataFrame(
        {
            "champion_name": ["Main", "Second", "Rare", "Rarer"],
            "games": [60, 25, 10, 5],
        }
    )
    # 100 games total; Main alone already covers 60%, so it is the whole core.
    assert core_champions(pool, coverage=0.5) == {"Main"}
    # Raising the bar pulls the next champion in rather than changing a threshold.
    assert core_champions(pool, coverage=0.8) == {"Main", "Second"}
    assert core_champions(pd.DataFrame(columns=["champion_name", "games"])) == set()


def test_pocket_picks_never_recommends_a_single_game_outlier() -> None:
    """A 1/1 champion is the exact case CLAUDE.md ("Sample size gates claims") forbids promoting."""
    conn = _make_conn()
    # One extra champion, played once, won once: a 100% win rate on no evidence.
    conn.execute("""
        INSERT INTO matches VALUES (
            'S16_ONEOFF', 'puuid1', ?, '16.1', 420,
            1800, 1, 'Galio', 100, 'MIDDLE', 'MID', true,
            5, 2, 3, 4.0, 180, 6.0, 12000, 20000, 30,
            'Viktor', 150, 11000, 2, 3, 1
        )
    """, [S16_DATETIME_D])
    picks = pocket_picks(conn)
    conn.close()

    galio = picks[picks["champion_name"] == "Galio"]
    assert not galio.empty
    assert galio.iloc[0]["label"] == "Insufficient Data"
    assert "Potential Pocket Pick" not in set(picks["label"])


def test_champion_pool_reports_per_minute_economy() -> None:
    """The pool answers *how* a champion performs, not only whether it won."""
    conn = _make_conn()
    pool = champion_pool(conn)
    conn.close()

    zed = pool[pool["champion_name"] == "Zed"].iloc[0]
    assert int(zed["games"]) == 3
    assert int(zed["wins"]) + int(zed["losses"]) == int(zed["games"])
    # 12000 gold over a 1800s game is 400 gold per minute.
    assert zed["gold_per_min"] == pytest.approx(400.0)
    assert zed["avg_duration_min"] == pytest.approx(30.0)
    assert zed["archetype"] == "Assassins"


def test_champion_archetype_matchups_drops_ineligible_opponents() -> None:
    """Build-dependent opponents cannot carry a champion-into-archetype verdict."""
    conn = _make_conn()
    conn.execute("""
        INSERT INTO matches VALUES (
            'S16_FLEX', 'puuid1', ?, '16.1', 420,
            1800, 1, 'Zed', 100, 'MIDDLE', 'MID', true,
            5, 2, 3, 4.0, 180, 6.0, 12000, 20000, 30,
            'Sylas', 150, 11000, 2, 3, 1
        )
    """, [S16_DATETIME_D])
    frame = champion_archetype_matchups(conn)
    conn.close()

    assert "Build-dependent" not in set(frame["archetype"])
    assert not frame.empty


def test_throw_and_comeback_use_a_real_team_lead() -> None:
    """A throw is a team lead lost, not a better-than-usual personal start."""
    conn = _make_conn()
    throws = is_throw_game(conn)
    conn.close()

    by_match = throws.set_index("match_id")
    # S16_B's team is behind at 14 and the game is a loss: neither label applies.
    assert not bool(by_match.loc["S16_B", "is_throw"])
    assert not bool(by_match.loc["S16_B", "is_comeback"])
    # S16_A's team is ahead at 14 and the game is a win: a lead kept.
    assert not bool(by_match.loc["S16_A", "is_throw"])
    # S16_D's team is ahead at 14 and the game is a loss: that is the throw.
    assert bool(by_match.loc["S16_D", "is_throw"])

    # The real lane differential is carried through, not the self-referential one.
    assert "lane_gold_diff_14" in throws.columns
    assert float(by_match.loc["S16_A", "lane_gold_diff_14"]) == 200.0


def test_death_context_reads_real_evidence() -> None:
    """Position, killer and the opponent's gold replace the own-average proxy."""
    conn = _make_conn()
    conn.execute(
        """
        UPDATE match_deaths SET position_x = 12000, position_y = 3000,
               killer_champion = 'Viktor', assist_count = 0,
               opp_gold_at_death = 5000
        WHERE match_id = 'S16_A' AND death_number = 1
        """
    )
    deaths = death_context(conn)
    conn.close()

    row = deaths[
        (deaths["match_id"] == "S16_A") & (deaths["death_number"] == 1)
    ].iloc[0]
    # Viktor is S16_A's listed opponent, so this is a lane death, fought solo.
    assert bool(row["killed_by_laner"])
    assert bool(row["is_solo_death"])
    # Far off the mid diagonal, on the bottom side of the map.
    assert row["death_zone"] == "bot side"
    assert bool(row["context_known"])
    # Behind the opponent in gold at that minute: 2750 against 5000.
    assert float(row["lane_gold_diff"]) == -2250.0
    assert bool(row["is_deficit_fight"])
