from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.archetypes import champion_archetype, is_verdict_eligible
from src.processor import ROAM_WINDOW_COLUMNS

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "lol.duckdb"

LANING_PHASE_END_MIN: int = 14
THROW_GOLD_THRESHOLD: int = 300
MID_LANE_CORRIDOR_WIDTH: int = 2500
ROAM_PHASE_START_MIN: int = 4
ROAM_PHASE_END_MIN: int = 14
CURRENT_SEASON_START: str = "2026-01-10T00:00:00+00:00"
ANALYSIS_ROLE: str = "MIDDLE"
EARLY_DEATH_THRESHOLD_MIN: int = 6    # deaths before this minute are classified as early
TILT_SPIRAL_GAP_MIN: int = 3          # max minutes between deaths to count as a spiral
TILT_WINDOW_GAMES: int = 5            # rolling window size for tilt index
WILSON_Z: float = 1.96                # 95% two-sided normal quantile
WINRATE_GROUPINGS: dict[str, str] = {
    "champion": "champion_name",
    "opponent": "opp_champion_name",
}


def wilson_interval(
    wins: int, games: int, z: float = WILSON_Z
) -> tuple[float, float]:
    """Return the Wilson score interval for a win count.

    Used instead of a fixed win-rate cutoff. A hardcoded threshold such as
    "green at 55%" is an invented gameplay threshold and PRODUCT.md section 12
    forbids one; the interval width is derived from the sample size instead, so
    a two-game matchup cannot produce a confident verdict. Do not replace this
    with a percentage constant.

    Returns (0.0, 1.0) for zero games — maximally uninformative, never clear.
    """
    if games <= 0:
        return (0.0, 1.0)
    proportion = wins / games
    denominator = 1.0 + z * z / games
    center = (proportion + z * z / (2 * games)) / denominator
    half_width = (
        z
        * np.sqrt(proportion * (1.0 - proportion) / games + z * z / (4 * games * games))
        / denominator
    )
    return (max(0.0, center - half_width), min(1.0, center + half_width))


def personal_baseline(conn: duckdb.DuckDBPyConnection) -> float:
    """Return the player's overall win rate within the current analysis scope.

    This is the baseline every matchup and champion verdict is measured against,
    per PRODUCT.md section 4: "+8% above your overall mid-lane baseline". A
    matchup is not good because it beats a coin flip; it is good because it
    beats how the player does in general.
    """
    result = conn.execute(
        """
        SELECT AVG(win::INTEGER)
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
        """,
        [CURRENT_SEASON_START, ANALYSIS_ROLE],
    ).fetchone()[0]
    return float(result) if result is not None else 0.5


def classify_winrate(low: float, high: float, baseline: float) -> str:
    """Classify a win-rate interval against the player's baseline.

    Returns one of the PRODUCT.md section 7 classes. ``Skill-based`` is
    deliberately not emitted: separating "reliably close to baseline" from
    "we simply do not know" requires naming a minimum interesting effect size,
    which PRODUCT.md section 12 makes a user decision. Until that number
    exists, both cases are honestly reported as Uncertain.
    """
    if low > baseline:
        return "Positive"
    if high < baseline:
        return "Negative"
    return "Uncertain"


def games_to_verdict(
    winrate: float, baseline: float, max_games: int = 2000
) -> int | None:
    """Games needed at the observed rate before the interval clears the baseline.

    Turns "Uncertain" from a dead end into a target: it says how much more of
    the same play it would take to know. Returns ``None`` when the observed rate
    sits on the baseline, where no sample size ever separates them, and when the
    answer exceeds ``max_games``.
    """
    if winrate == baseline:
        return None
    for games in range(2, max_games + 1):
        low, high = wilson_interval(round(winrate * games), games)
        if low > baseline or high < baseline:
            return games
    return None


def _add_winrate_interval(
    df: pd.DataFrame, rate_column: str, baseline: float
) -> pd.DataFrame:
    """Attach winrate_lo, winrate_hi, and matchup_class from the Wilson interval."""
    bounds = [
        wilson_interval(round(rate * games), int(games))
        for rate, games in zip(df[rate_column], df["games"], strict=True)
    ]
    df["winrate_lo"] = [low for low, _ in bounds]
    df["winrate_hi"] = [high for _, high in bounds]
    df["matchup_class"] = [
        classify_winrate(low, high, baseline) for low, high in bounds
    ]
    df["games_needed"] = [
        None if matchup_class != "Uncertain" else games_to_verdict(rate, baseline)
        for matchup_class, rate in zip(df["matchup_class"], df[rate_column], strict=True)
    ]
    return df


def champion_winrates(
    conn: duckdb.DuckDBPyConnection, dimension: str
) -> pd.DataFrame:
    """Aggregate win rate by our champion or by opponent champion.

    Pair-level matchup slices are too small to support a verdict; these two
    single-axis groupings are where a defensible one can still exist.

    Columns: name, games, wins, winrate, winrate_lo, winrate_hi, matchup_class,
    games_needed.
    """
    if dimension not in WINRATE_GROUPINGS:
        raise ValueError(
            f"dimension must be one of {sorted(WINRATE_GROUPINGS)}, got {dimension!r}"
        )
    group_column = WINRATE_GROUPINGS[dimension]

    df = conn.execute(f"""
        SELECT
            {group_column} AS name,
            COUNT(*)::INTEGER AS games,
            SUM(win::INTEGER)::INTEGER AS wins
        FROM matches
        WHERE game_datetime >= ?
          AND team_position = ?
          AND {group_column} IS NOT NULL
        GROUP BY {group_column}
        ORDER BY games DESC, name ASC
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    if df.empty:
        return pd.DataFrame(
            columns=["name", "games", "wins", "winrate",
                     "winrate_lo", "winrate_hi", "matchup_class", "games_needed"]
        )

    df["winrate"] = df["wins"] / df["games"]
    return _add_winrate_interval(df, "winrate", personal_baseline(conn))


def opponent_archetype_winrates(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Aggregate win rate by the opponent's champion archetype.

    Archetype buckets are the smallest grouping in this dataset large enough to
    support a verdict; individual matchup pairs run 2-9 games and cannot.
    Build-dependent and unclassified champions are reported as their own rows
    and marked ineligible rather than folded into a bucket they would distort.

    Columns: archetype, games, wins, winrate, winrate_lo, winrate_hi,
    matchup_class, verdict_eligible.
    """
    df = conn.execute(
        """
        SELECT opp_champion_name AS name, win
        FROM matches
        WHERE game_datetime >= ?
          AND team_position = ?
          AND opp_champion_name IS NOT NULL
        """,
        [CURRENT_SEASON_START, ANALYSIS_ROLE],
    ).df()

    columns = ["archetype", "games", "wins", "winrate", "winrate_lo",
               "winrate_hi", "matchup_class", "games_needed", "verdict_eligible"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    df["archetype"] = df["name"].map(champion_archetype)
    grouped = (
        df.groupby("archetype")
        .agg(games=("win", "count"), wins=("win", "sum"))
        .reset_index()
    )
    grouped["wins"] = grouped["wins"].astype(int)
    grouped["winrate"] = grouped["wins"] / grouped["games"]
    grouped = _add_winrate_interval(grouped, "winrate", personal_baseline(conn))

    grouped["verdict_eligible"] = grouped["archetype"].map(is_verdict_eligible)
    # An ineligible grouping is reference only; it must never read as a verdict.
    grouped.loc[~grouped["verdict_eligible"], "matchup_class"] = "Uncertain"

    return grouped.sort_values("games", ascending=False).reset_index(drop=True)[columns]


def _time_bucket(hour: int) -> str:
    """Map an hour of day (0–23) to a named time bucket."""
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 22:
        return "evening"
    return "night"  # covers 23 and 0-5


def death_context(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Return per-death annotations classifying each death by context.

    Joins match_deaths with match_timelines average-gold lookup and matches
    for game-level context. Returns one row per death in the current analysis scope.

    Columns: match_id, death_number, timestamp_min, gold_at_death,
    gold_lead_approx, is_overextension_ahead, is_deficit_fight,
    is_early_death, is_tilt_spiral, is_post_laning_throw.

    Games with zero deaths produce no rows — that is not an error.
    """
    df = conn.execute("""
        SELECT
            d.match_id,
            d.death_number,
            d.timestamp_min,
            d.gold_at_death
        FROM match_deaths d
        JOIN matches m ON m.match_id = d.match_id
        WHERE m.game_datetime >= ?
          AND m.team_position = ?
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    if df.empty:
        return pd.DataFrame(columns=[
            "match_id", "death_number", "timestamp_min", "gold_at_death",
            "gold_lead_approx", "is_overextension_ahead", "is_deficit_fight",
            "is_early_death", "is_tilt_spiral", "is_post_laning_throw",
        ])

    # Average gold per minute within the current season/role scope.
    avg_gold = conn.execute("""
        SELECT mt.timestamp_min, AVG(mt.gold) AS avg_gold
        FROM match_timelines mt
        JOIN matches m ON m.match_id = mt.match_id
        WHERE m.game_datetime >= ?
          AND m.team_position = ?
        GROUP BY mt.timestamp_min
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    df = df.merge(avg_gold, on="timestamp_min", how="left")
    df["gold_lead_approx"] = df["gold_at_death"].fillna(0.0) - df["avg_gold"].fillna(0.0)

    # Gold at the frame closest to minute 14 within the current scope.
    gold_at_min14 = conn.execute("""
        WITH ranked AS (
            SELECT
                mt.match_id,
                mt.gold AS gold_at_min14,
                ROW_NUMBER() OVER (
                    PARTITION BY mt.match_id
                    ORDER BY ABS(mt.timestamp_min - 14)
                ) AS rn
            FROM match_timelines mt
            JOIN matches m ON m.match_id = mt.match_id
            WHERE mt.timestamp_min BETWEEN 12 AND 16
              AND m.game_datetime >= ?
              AND m.team_position = ?
        )
        SELECT match_id, gold_at_min14
        FROM ranked
        WHERE rn = 1
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    player_avg_gold_at_14: float = float(gold_at_min14["gold_at_min14"].mean())
    df = df.merge(gold_at_min14, on="match_id", how="left")

    # is_tilt_spiral: previous death in this game is within 3 minutes
    df = df.sort_values(["match_id", "death_number"]).reset_index(drop=True)
    prev_ts = df.groupby("match_id")["timestamp_min"].shift(1)
    is_tilt_spiral = ((df["timestamp_min"] - prev_ts) <= TILT_SPIRAL_GAP_MIN) & prev_ts.notna()

    result = pd.DataFrame({
        "match_id": df["match_id"],
        "death_number": df["death_number"],
        "timestamp_min": df["timestamp_min"],
        "gold_at_death": df["gold_at_death"],
        "gold_lead_approx": df["gold_lead_approx"].fillna(0.0),
        "is_overextension_ahead": (
            (df["gold_lead_approx"] > THROW_GOLD_THRESHOLD)
            & (df["timestamp_min"] <= LANING_PHASE_END_MIN)
        ),
        "is_deficit_fight": (
            (df["gold_lead_approx"] < -THROW_GOLD_THRESHOLD)
            & (df["timestamp_min"] <= LANING_PHASE_END_MIN)
        ),
        "is_early_death": df["timestamp_min"] < EARLY_DEATH_THRESHOLD_MIN,
        "is_tilt_spiral": is_tilt_spiral.fillna(False),
        "is_post_laning_throw": (
            (df["timestamp_min"] > LANING_PHASE_END_MIN)
            & df["gold_at_min14"].notna()
            & (df["gold_at_min14"] > player_avg_gold_at_14 + THROW_GOLD_THRESHOLD)
        ).fillna(False),
    })

    return result


def is_throw_game(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Classify each game as a throw, comeback, or neutral at the gold-at-14 level.

    Uses the frame closest to minute 14 (between minutes 12–16). Games with no
    frame in that window are excluded from output.

    Columns: match_id, gold_at_14, gold_delta, is_throw, is_comeback.
    """
    gold_df = conn.execute("""
        WITH ranked AS (
            SELECT
                mt.match_id,
                mt.gold AS gold_at_14,
                ROW_NUMBER() OVER (
                    PARTITION BY mt.match_id
                    ORDER BY ABS(mt.timestamp_min - 14)
                ) AS rn
            FROM match_timelines mt
            JOIN matches m ON m.match_id = mt.match_id
            WHERE mt.timestamp_min BETWEEN 12 AND 16
              AND m.game_datetime >= ?
              AND m.team_position = ?
        )
        SELECT match_id, gold_at_14
        FROM ranked
        WHERE rn = 1
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    matches_df = conn.execute(
        """
        SELECT match_id, win
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
        """,
        [CURRENT_SEASON_START, ANALYSIS_ROLE],
    ).df()
    df = matches_df.merge(gold_df, on="match_id", how="inner")

    avg_gold_14: float = float(df["gold_at_14"].mean())
    df["gold_delta"] = df["gold_at_14"] - avg_gold_14
    df["is_throw"] = (df["gold_delta"] >= THROW_GOLD_THRESHOLD) & (~df["win"])
    df["is_comeback"] = (df["gold_delta"] <= -THROW_GOLD_THRESHOLD) & df["win"]

    return df[["match_id", "gold_at_14", "gold_delta", "is_throw", "is_comeback"]]


def roam_timing(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Detect laning-phase roam windows and quantify their CS cost and kill impact.

    Detection uses position data when available: a roam is a contiguous block of
    minutes 4–14 where abs(position_x - position_y) >= MID_LANE_CORRIDOR_WIDTH.
    Requires at least 2 consecutive minutes outside the corridor (single-frame
    noise excluded).

    When position_x is NULL for a game, falls back to CS-drop proxy: any minute
    where CS is more than 1.5 std deviations below the player's expected CS at
    that minute.

    Columns: match_id, roam_start_min, roam_end_min, cs_before, cs_after,
    expected_cs_delta, cs_sacrifice, kills_during_roam, roam_result.
    """
    timeline = conn.execute("""
        SELECT mt.match_id, mt.timestamp_min, mt.cs, mt.kills,
               mt.position_x, mt.position_y
        FROM match_timelines mt
        JOIN matches m ON m.match_id = mt.match_id
        WHERE mt.timestamp_min BETWEEN 3 AND 16
          AND m.game_datetime >= ?
          AND m.team_position = ?
        ORDER BY mt.match_id, mt.timestamp_min
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    # Average CS baseline within the current season/role scope.
    avg_cs_by_min = conn.execute("""
        SELECT
            mt.timestamp_min,
            AVG(mt.cs) AS avg_cs,
            STDDEV(mt.cs) AS std_cs
        FROM match_timelines mt
        JOIN matches m ON m.match_id = mt.match_id
        WHERE mt.timestamp_min BETWEEN 4 AND 14
          AND m.game_datetime >= ?
          AND m.team_position = ?
        GROUP BY mt.timestamp_min
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    avg_cs_per_min_global: float = float(
        conn.execute(
            """
            SELECT AVG(cs_per_min)
            FROM matches
            WHERE game_datetime >= ? AND team_position = ?
            """,
            [CURRENT_SEASON_START, ANALYSIS_ROLE],
        ).fetchone()[0] or 0.0
    )

    results: list[dict] = []

    for match_id, grp in timeline.groupby("match_id"):
        grp = grp.sort_values("timestamp_min").reset_index(drop=True)
        phase = grp[
            (grp["timestamp_min"] >= ROAM_PHASE_START_MIN)
            & (grp["timestamp_min"] <= ROAM_PHASE_END_MIN)
        ].copy()

        if phase.empty:
            continue

        if phase["position_x"].notna().any():
            # Vectorised corridor test — set is_roaming=False where position is NULL
            px = phase["position_x"]
            py = phase["position_y"]
            has_pos = px.notna() & py.notna()
            phase["is_roaming"] = has_pos & (
                (px.fillna(0) - py.fillna(0)).abs() >= MID_LANE_CORRIDOR_WIDTH
            )
        else:
            # CS-drop proxy
            phase = phase.merge(avg_cs_by_min, on="timestamp_min", how="left")
            threshold = phase["avg_cs"] - 1.5 * phase["std_cs"].fillna(0.0)
            phase["is_roaming"] = (phase["cs"] < threshold).fillna(False)

        phase = phase.reset_index(drop=True)
        # Label contiguous is_roaming blocks
        phase["block"] = (phase["is_roaming"] != phase["is_roaming"].shift()).cumsum()

        for _block_id, block in phase[phase["is_roaming"]].groupby("block"):
            if len(block) < 2:
                continue  # single-frame noise — excluded per spec

            roam_start = int(block["timestamp_min"].min())
            roam_end = int(block["timestamp_min"].max())

            # cs_before: CS at roam_start - 1
            before = grp.loc[grp["timestamp_min"] == roam_start - 1, "cs"]
            cs_before = int(before.values[0]) if not before.empty else 0

            # cs_after: CS at roam_end + 1, or last available minute
            after = grp.loc[grp["timestamp_min"] == roam_end + 1, "cs"]
            if not after.empty:
                cs_after = int(after.values[0])
            else:
                last = grp.loc[grp["timestamp_min"] <= roam_end, "cs"]
                cs_after = int(last.values[-1]) if not last.empty else cs_before

            roam_duration = roam_end - roam_start + 1
            expected_cs_delta = roam_duration * avg_cs_per_min_global
            cs_sacrifice = max(0.0, expected_cs_delta - (cs_after - cs_before))

            k_end_s = grp.loc[grp["timestamp_min"] == roam_end, "kills"]
            k_pre_s = grp.loc[grp["timestamp_min"] == roam_start - 1, "kills"]
            k_end = int(k_end_s.values[0]) if not k_end_s.empty else 0
            k_pre = int(k_pre_s.values[0]) if not k_pre_s.empty else 0
            kills_during = max(0, k_end - k_pre)

            results.append({
                "match_id": match_id,
                "roam_start_min": roam_start,
                "roam_end_min": roam_end,
                "cs_before": cs_before,
                "cs_after": cs_after,
                "expected_cs_delta": expected_cs_delta,
                "cs_sacrifice": cs_sacrifice,
                "kills_during_roam": kills_during,
                "roam_result": "impact" if kills_during > 0 else "no_impact",
            })

    if not results:
        return pd.DataFrame(columns=[
            "match_id", "roam_start_min", "roam_end_min", "cs_before", "cs_after",
            "expected_cs_delta", "cs_sacrifice", "kills_during_roam", "roam_result",
        ])

    return pd.DataFrame(results)


def champion_matchup_stats(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Aggregate win-rate, CS, and KDA stats per (our_champion, opponent_champion) pair.

    Filters to matchups with at least 2 games.
    Columns: champion_name, opp_champion_name, games, our_avg_cs, opp_avg_cs,
    cs_diff, gold_diff, our_winrate, winrate_lo, winrate_hi, matchup_class,
    games_needed, our_avg_kda, opp_avg_kda.

    ``gold_diff`` is end-of-game gold against the actual lane opponent — the
    only opponent-anchored gold figure the schema currently carries. Per-minute
    opponent gold requires parsing all ten participantFrames.
    """
    df = conn.execute("""
        SELECT
            champion_name,
            opp_champion_name,
            cs_total,
            opp_cs_total,
            gold_earned,
            opp_gold_earned,
            win,
            kda,
            opp_kills,
            opp_deaths,
            opp_assists
        FROM matches
        WHERE opp_champion_name IS NOT NULL
          AND opp_cs_total IS NOT NULL
          AND game_datetime >= ?
          AND team_position = ?
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    # Opponent KDA computed per row to avoid division issues
    df["opp_kda"] = (df["opp_kills"] + df["opp_assists"]) / df["opp_deaths"].clip(lower=1)

    stats = (
        df.groupby(["champion_name", "opp_champion_name"])
        .agg(
            games=("win", "count"),
            our_avg_cs=("cs_total", "mean"),
            opp_avg_cs=("opp_cs_total", "mean"),
            our_avg_gold=("gold_earned", "mean"),
            opp_avg_gold=("opp_gold_earned", "mean"),
            our_winrate=("win", "mean"),
            our_avg_kda=("kda", "mean"),
            opp_avg_kda=("opp_kda", "mean"),
        )
        .reset_index()
    )
    stats["cs_diff"] = stats["our_avg_cs"] - stats["opp_avg_cs"]
    stats["gold_diff"] = stats["our_avg_gold"] - stats["opp_avg_gold"]

    stats = stats.loc[stats["games"] >= 2].reset_index(drop=True)
    stats = _add_winrate_interval(stats, "our_winrate", personal_baseline(conn))

    return stats[
        [
            "champion_name", "opp_champion_name", "games",
            "our_avg_cs", "opp_avg_cs", "cs_diff", "gold_diff",
            "our_winrate", "winrate_lo", "winrate_hi", "matchup_class",
            "games_needed",
            "our_avg_kda", "opp_avg_kda",
        ]
    ].reset_index(drop=True)


def tilt_index(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Compute rolling 5-game win rate prior to each game as a tilt proxy.

    Uses .shift(1) to exclude the current game result. min_periods=1 allows
    computation from the second game onward. The first game is filled with 0.5
    (neutral — no history). Result is always in [0.0, 1.0] with no NaN.

    Columns: match_id, game_datetime, win, tilt_index.
    """
    df = conn.execute("""
        SELECT match_id, game_datetime, win
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
        ORDER BY game_datetime
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    win_float = df["win"].astype(float)
    df["tilt_index"] = (
        win_float
        .shift(1)
        .rolling(TILT_WINDOW_GAMES, min_periods=1)
        .mean()
        .fillna(0.5)   # first game: no prior history
        .clip(0.0, 1.0)
    )

    return df[["match_id", "game_datetime", "win", "tilt_index"]]


def build_feature_matrix(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Join all feature functions into one row per match and persist to DuckDB.

    Only Season 16 mid-lane rows are included.

    NaN fill strategy (documented per column):
    - tilt_index          : never NaN (rolling fills first game with 0.5)
    - gold_delta          : 0.0  — no min-14 frame → treat as neutral
    - is_throw            : False — no min-14 frame → not a throw
    - is_comeback         : False — no min-14 frame → not a comeback
    - total_deaths        : 0    — no deaths recorded
    - deaths_while_ahead  : 0    — no deaths recorded
    - tilt_spiral_ratio   : 0.0  — no deaths → ratio is zero
    - max_death_streak    : 0    — no deaths → streak is zero
    - total_roams         : 0    — no roams detected
    - avg_cs_sacrifice : 0.0 then log1p-transformed — no roams → log1p(0) = 0
    - roam_impact_rate    : 0.5  — no roams → unknown, treat as neutral
    """
    # Season/role anchor: all merges are left-joined to this scope.
    base_df = conn.execute("""
        SELECT match_id, win, game_datetime, champion_name
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    tilt_df = tilt_index(conn)[["match_id", "tilt_index"]]

    # Temporal features from the already-scoped base frame.
    matches_df = base_df[["match_id", "game_datetime"]].copy()
    matches_df["game_datetime"] = pd.to_datetime(matches_df["game_datetime"], format="ISO8601")
    matches_df["hour_of_day"] = matches_df["game_datetime"].dt.hour
    matches_df["day_of_week"] = matches_df["game_datetime"].dt.dayofweek  # 0 = Monday
    matches_df["is_weekend"] = matches_df["day_of_week"].isin([5, 6])
    matches_df["time_bucket"] = matches_df["hour_of_day"].map(_time_bucket)
    temporal = matches_df[["match_id", "hour_of_day", "day_of_week", "is_weekend", "time_bucket"]]

    throw_df = is_throw_game(conn)[["match_id", "is_throw", "is_comeback", "gold_delta"]]

    dc = death_context(conn)
    if not dc.empty:
        death_agg = (
            dc.groupby("match_id")
            .agg(
                total_deaths=("death_number", "count"),
                deaths_while_ahead=("is_overextension_ahead", "sum"),
                tilt_spiral_count=("is_tilt_spiral", "sum"),
            )
            .reset_index()
        )
        # tilt_spiral_ratio: proportion of deaths that were cascade deaths
        death_agg["tilt_spiral_ratio"] = (
            death_agg["tilt_spiral_count"] / death_agg["total_deaths"].clip(lower=1)
        ).round(4)
        death_agg = death_agg.drop(columns=["tilt_spiral_count"])

        # max_death_streak: longest consecutive run of is_tilt_spiral == True in one game
        dc_s = dc.sort_values(["match_id", "death_number"]).reset_index(drop=True)
        dc_s["_block"] = dc_s.groupby("match_id")["is_tilt_spiral"].transform(
            lambda x: (x != x.shift()).cumsum()
        )
        max_streak = (
            dc_s[dc_s["is_tilt_spiral"]]
            .groupby(["match_id", "_block"])
            .size()
            .reset_index(name="_streak_len")
            .groupby("match_id")["_streak_len"]
            .max()
            .reset_index(name="max_death_streak")
        )
        death_agg = death_agg.merge(max_streak, on="match_id", how="left")
    else:
        death_agg = pd.DataFrame(
            columns=["match_id", "total_deaths", "deaths_while_ahead",
                     "tilt_spiral_ratio", "max_death_streak"]
        )

    roam_df = roam_timing(conn)
    if not roam_df.empty:
        roam_agg = (
            roam_df.assign(is_impact=roam_df["roam_result"] == "impact")
            .groupby("match_id")
            .agg(
                total_roams=("roam_start_min", "count"),
                avg_cs_sacrifice=("cs_sacrifice", "mean"),
                roam_impact_rate=("is_impact", "mean"),
            )
            .reset_index()
        )
    else:
        roam_agg = pd.DataFrame(
            columns=["match_id", "total_roams", "avg_cs_sacrifice", "roam_impact_rate"]
        )

    fm = base_df.merge(tilt_df, on="match_id", how="left")
    fm = fm.merge(temporal, on="match_id", how="left")
    fm = fm.merge(throw_df, on="match_id", how="left")
    fm = fm.merge(death_agg, on="match_id", how="left")
    fm = fm.merge(roam_agg, on="match_id", how="left")

    # Fill NaN — see docstring for rationale per column
    fm["is_throw"] = fm["is_throw"].astype("boolean").fillna(False).astype(bool)
    fm["is_comeback"] = fm["is_comeback"].astype("boolean").fillna(False).astype(bool)
    fm["gold_delta"] = fm["gold_delta"].fillna(0.0)
    fm["total_deaths"] = fm["total_deaths"].fillna(0).astype(int)
    fm["deaths_while_ahead"] = fm["deaths_while_ahead"].fillna(0).astype(int)
    fm["tilt_spiral_ratio"] = fm["tilt_spiral_ratio"].fillna(0.0)
    fm["max_death_streak"] = fm["max_death_streak"].fillna(0).astype(int)
    fm["total_roams"] = fm["total_roams"].astype(float).fillna(0.0).astype(int)
    fm["avg_cs_sacrifice"] = fm["avg_cs_sacrifice"].astype(float).fillna(0.0)
    fm["avg_cs_sacrifice"] = np.log1p(fm["avg_cs_sacrifice"])
    fm["roam_impact_rate"] = fm["roam_impact_rate"].astype(float).fillna(0.5)

    # Persist both derived tables atomically so their roam counts stay aligned.
    conn.register("_fm_register", fm)
    if not roam_df.empty:
        conn.register(
            "_roam_windows_register",
            roam_df[list(ROAM_WINDOW_COLUMNS)],
        )
    conn.execute("BEGIN")
    try:
        if roam_df.empty:
            conn.execute("DELETE FROM roam_windows")
        else:
            # DuckDB cannot delete and reinsert the same primary key in one transaction.
            conn.execute("""
                DELETE FROM roam_windows old
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM _roam_windows_register new
                    WHERE new.match_id = old.match_id
                      AND new.roam_start_min = old.roam_start_min
                      AND new.roam_end_min = old.roam_end_min
                )
            """)
            roam_columns = ", ".join(ROAM_WINDOW_COLUMNS)
            conn.execute(f"""
                INSERT OR REPLACE INTO roam_windows ({roam_columns})
                SELECT {roam_columns}
                FROM _roam_windows_register
            """)
        conn.execute("DROP TABLE IF EXISTS feature_matrix")
        conn.execute("CREATE TABLE feature_matrix AS SELECT * FROM _fm_register")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.unregister("_fm_register")
        if not roam_df.empty:
            conn.unregister("_roam_windows_register")

    return fm


def run_features() -> None:
    """Open DuckDB, build the feature matrix, and print a summary to stdout."""
    with duckdb.connect(str(DB_PATH)) as conn:
        fm = build_feature_matrix(conn)
        print(f"Season filter          : >= {CURRENT_SEASON_START}")
        print(f"Role filter            : {ANALYSIS_ROLE}")
        print(f"Rows in feature_matrix : {len(fm)}")
        print(f"Columns                : {list(fm.columns)}")
        print(f"Throw games            : {int(fm['is_throw'].sum())}")
        print(f"Comeback games         : {int(fm['is_comeback'].sum())}")


if __name__ == "__main__":
    run_features()
