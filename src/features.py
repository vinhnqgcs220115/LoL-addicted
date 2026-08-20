from __future__ import annotations

import math
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
MAP_DIAGONAL_SUM: int = 14870      # x + y at the midpoint of Summoner's Rift
BLUE_TEAM_ID: int = 100
ROAM_PHASE_START_MIN: int = 4
ROAM_PHASE_END_MIN: int = 14
CURRENT_SEASON_START: str = "2026-01-10T00:00:00+00:00"
ANALYSIS_ROLE: str = "MIDDLE"
EARLY_DEATH_THRESHOLD_MIN: int = 6    # deaths before this minute are classified as early
TILT_SPIRAL_GAP_MIN: int = 3          # max minutes between deaths to count as a spiral
TILT_WINDOW_GAMES: int = 5            # rolling window size for tilt index
WILSON_Z: float = 1.96                # 95% two-sided normal quantile
SIGNIFICANCE_ALPHA: float = 0.05      # one-sided, matching the 95% interval
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


def binomial_significance(wins: int, games: int, baseline: float) -> float:
    """One-sided exact binomial p-value for a record against the baseline.

    Used for the verdict instead of asking whether the Wilson interval excludes
    the baseline. Wilson is a normal approximation and is anti-conservative at
    small samples with extreme proportions: a 4-0 record produced an interval
    whose lower bound cleared a 50.9% baseline by a thousandth, which rendered
    as a verdict that a single loss would reverse. The exact test gives that
    record p = 0.067 and withholds it, while keeping 15-5 at p = 0.025.

    The interval is still computed and displayed -- it communicates precision.
    This decides.
    """
    if games <= 0:
        return 1.0
    if not 0.0 < baseline < 1.0:
        return 1.0
    terms = (
        range(wins, games + 1)
        if wins / games > baseline
        else range(0, wins + 1)
    )
    # Computed in log space: math.comb on a few hundred trials returns integers
    # too large to multiply by a float.
    log_n = math.lgamma(games + 1)
    log_p, log_q = math.log(baseline), math.log1p(-baseline)
    total = 0.0
    for i in terms:
        log_term = (
            log_n - math.lgamma(i + 1) - math.lgamma(games - i + 1)
            + i * log_p + (games - i) * log_q
        )
        total += math.exp(log_term)
    return min(total, 1.0)


def classify_winrate(wins: int, games: int, baseline: float) -> str:
    """Classify a record against the player's baseline.

    Returns one of the PRODUCT.md section 7 classes. ``Skill-based`` is
    deliberately not emitted: separating "reliably close to baseline" from
    "we simply do not know" requires naming a minimum interesting effect size,
    which PRODUCT.md section 12 makes a user decision. Until that number
    exists, both cases are honestly reported as Uncertain.
    """
    if games <= 0:
        return "Uncertain"
    rate = wins / games
    if rate == baseline:
        return "Uncertain"
    if binomial_significance(wins, games, baseline) >= SIGNIFICANCE_ALPHA:
        return "Uncertain"
    return "Positive" if rate > baseline else "Negative"


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
    # Deliberately the interval, not the exact test: this is an estimate of how
    # much more play would settle the question, and running the exact test for
    # every candidate sample size would make the search quadratic.
    for games in range(2, max_games + 1):
        low, high = wilson_interval(round(winrate * games), games)
        if low > baseline or high < baseline:
            return games
    return None


def _direction_survives_one_more_game(
    winrate: float, games: int, baseline: float
) -> bool:
    """Whether one more game of the opposite result would flip the direction.

    A projection reads as a promise ("4 more games and you will know"), so it is
    only worth stating when the direction it projects is not an artifact of a
    single game. This is a stability test, not a minimum sample size: it invents
    no cutoff, it just refuses to extrapolate from a rate that one result undoes.
    """
    if games < 2 or winrate == baseline:
        return False
    wins = round(winrate * games)
    # Add one game of the result that would pull the rate back toward baseline.
    opposite_wins = wins if winrate > baseline else wins + 1
    shifted = opposite_wins / (games + 1)
    return (shifted > baseline) == (winrate > baseline) and shifted != baseline


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
        classify_winrate(round(rate * games), int(games), baseline)
        for rate, games in zip(df[rate_column], df["games"], strict=True)
    ]
    df["games_needed"] = [
        None
        if matchup_class != "Uncertain"
        or not _direction_survives_one_more_game(rate, int(games), baseline)
        else games_to_verdict(rate, baseline)
        for matchup_class, rate, games in zip(
            df["matchup_class"], df[rate_column], df["games"], strict=True
        )
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


ARCHETYPE_SIDES: dict[str, str] = {
    "own": "champion_name",
    "opponent": "opp_champion_name",
}
CORE_POOL_COVERAGE: float = 0.5
POCKET_PICK_LABELS: tuple[str, ...] = (
    "Potential Pocket Pick",
    "Matchup-specific Pocket Pick",
    "Emerging Pick",
    "Insufficient Data",
)


def archetype_winrates(conn: duckdb.DuckDBPyConnection, side: str) -> pd.DataFrame:
    """Aggregate win rate by champion archetype, for our champion or the opponent's.

    Archetype buckets are the smallest grouping in this dataset large enough to
    support a verdict; individual matchup pairs run 2-9 games and cannot.
    Build-dependent and unclassified champions are reported as their own rows
    and marked ineligible rather than folded into a bucket they would distort.

    Columns: archetype, games, wins, winrate, winrate_lo, winrate_hi,
    matchup_class, games_needed, verdict_eligible.
    """
    if side not in ARCHETYPE_SIDES:
        raise ValueError(f"side must be one of {sorted(ARCHETYPE_SIDES)}, got {side!r}")
    column = ARCHETYPE_SIDES[side]

    df = conn.execute(f"""
        SELECT {column} AS name, win
        FROM matches
        WHERE game_datetime >= ?
          AND team_position = ?
          AND {column} IS NOT NULL
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

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


def champion_pool(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Per-champion performance for every champion played in the current scope.

    Answers "which champions actually work for me, and how": the rate with its
    interval, plus the per-minute economy and lane numbers that say *how* a
    champion performs rather than only whether it won.

    Columns: champion_name, archetype, games, wins, losses, winrate, winrate_lo,
    winrate_hi, matchup_class, games_needed, avg_kda, cs_per_min, gold_per_min,
    damage_per_min, avg_duration_min, cs_diff, gold_diff.
    """
    df = conn.execute("""
        SELECT
            champion_name,
            COUNT(*)::INTEGER AS games,
            SUM(win::INTEGER)::INTEGER AS wins,
            AVG(kda)::DOUBLE AS avg_kda,
            AVG(cs_per_min)::DOUBLE AS cs_per_min,
            AVG(gold_earned * 60.0 / NULLIF(game_duration_sec, 0))::DOUBLE AS gold_per_min,
            AVG(damage_dealt_to_champions * 60.0 / NULLIF(game_duration_sec, 0))::DOUBLE
                AS damage_per_min,
            AVG(game_duration_sec / 60.0)::DOUBLE AS avg_duration_min,
            AVG(cs_total - opp_cs_total)::DOUBLE AS cs_diff,
            AVG(gold_earned - opp_gold_earned)::DOUBLE AS gold_diff
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
        GROUP BY champion_name
        ORDER BY games DESC, champion_name ASC
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    columns = ["champion_name", "archetype", "games", "wins", "losses", "winrate",
               "winrate_lo", "winrate_hi", "matchup_class", "games_needed",
               "avg_kda", "cs_per_min", "gold_per_min", "damage_per_min",
               "avg_duration_min", "cs_diff", "gold_diff"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    df["losses"] = df["games"] - df["wins"]
    df["winrate"] = df["wins"] / df["games"]
    df["archetype"] = df["champion_name"].map(champion_archetype)
    df = _add_winrate_interval(df, "winrate", personal_baseline(conn))
    return df[columns]


def core_champions(pool: pd.DataFrame, coverage: float = CORE_POOL_COVERAGE) -> set[str]:
    """Return the smallest set of champions covering ``coverage`` of all games.

    "Rarely played" only means something relative to what the player actually
    mains, so the line is derived from their own usage rather than set to a game
    count. With ``coverage`` at one half this is the set of champions making up
    the majority of their games.
    """
    if pool.empty:
        return set()
    ordered = pool.sort_values("games", ascending=False)
    target = ordered["games"].sum() * coverage
    running = ordered["games"].cumsum()
    # Include the champion that crosses the line, not only those strictly under it.
    return set(ordered.loc[running - ordered["games"] < target, "champion_name"])


def champion_archetype_matchups(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Win rate for each (our champion, opponent archetype) pair.

    One level finer than `archetype_winrates` and one level coarser than a
    champion-versus-champion pair, which is where a matchup verdict can still
    exist. Ineligible opponent groupings are excluded outright.

    Columns: champion_name, archetype, games, wins, winrate, winrate_lo,
    winrate_hi, matchup_class, games_needed.
    """
    df = conn.execute("""
        SELECT champion_name, opp_champion_name, win
        FROM matches
        WHERE game_datetime >= ?
          AND team_position = ?
          AND opp_champion_name IS NOT NULL
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    columns = ["champion_name", "archetype", "games", "wins", "winrate",
               "winrate_lo", "winrate_hi", "matchup_class", "games_needed"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    df["archetype"] = df["opp_champion_name"].map(champion_archetype)
    df = df[df["archetype"].map(is_verdict_eligible)]
    if df.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        df.groupby(["champion_name", "archetype"])
        .agg(games=("win", "count"), wins=("win", "sum"))
        .reset_index()
    )
    grouped["wins"] = grouped["wins"].astype(int)
    grouped["winrate"] = grouped["wins"] / grouped["games"]
    grouped = _add_winrate_interval(grouped, "winrate", personal_baseline(conn))
    return grouped.sort_values("games", ascending=False).reset_index(drop=True)[columns]


def pocket_picks(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Label rarely-played champions by how far the evidence for them actually goes.

    A pocket pick is a champion outside the core pool that outperforms the
    player's baseline. The label reports the strength of the evidence, so a
    small-sample outlier lands on `Insufficient Data` instead of becoming a
    recommendation -- PRODUCT.md section 6 forbids the latter explicitly.

    Columns: champion_name, archetype, games, wins, winrate, winrate_lo,
    winrate_hi, label, evidence.
    """
    pool = champion_pool(conn)
    columns = ["champion_name", "archetype", "games", "wins", "winrate",
               "winrate_lo", "winrate_hi", "label", "evidence"]
    if pool.empty:
        return pd.DataFrame(columns=columns)

    baseline = personal_baseline(conn)
    core = core_champions(pool)
    positive_matchups = champion_archetype_matchups(conn)
    positive_matchups = positive_matchups[
        positive_matchups["matchup_class"] == "Positive"
    ]

    rows = []
    for champion in pool[~pool["champion_name"].isin(core)].itertuples(index=False):
        if champion.winrate <= baseline:
            continue

        strong = positive_matchups[
            positive_matchups["champion_name"] == champion.champion_name
        ]
        if champion.matchup_class == "Positive":
            label = "Potential Pocket Pick"
            evidence = "Win rate clears your baseline on its own."
        elif not strong.empty:
            best = strong.iloc[0]
            label = "Matchup-specific Pocket Pick"
            evidence = (
                f"Clears your baseline against {best['archetype']} "
                f"({int(best['wins'])} of {int(best['games'])} games)."
            )
        elif _direction_survives_one_more_game(
            champion.winrate, int(champion.games), baseline
        ):
            label = "Emerging Pick"
            evidence = "Above your baseline, and one loss would not reverse that."
        else:
            label = "Insufficient Data"
            evidence = "Too few games; a single result would flip the direction."

        rows.append({
            "champion_name": champion.champion_name,
            "archetype": champion.archetype,
            "games": int(champion.games),
            "wins": int(champion.wins),
            "winrate": champion.winrate,
            "winrate_lo": champion.winrate_lo,
            "winrate_hi": champion.winrate_hi,
            "label": label,
            "evidence": evidence,
        })

    if not rows:
        return pd.DataFrame(columns=columns)

    result = pd.DataFrame(rows)
    order = {label: index for index, label in enumerate(POCKET_PICK_LABELS)}
    result["_rank"] = result["label"].map(order)
    return (
        result.sort_values(["_rank", "games"], ascending=[True, False])
        .drop(columns="_rank")
        .reset_index(drop=True)[columns]
    )


def _time_bucket(hour: int) -> str:
    """Map an hour of day (0–23) to a named time bucket."""
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 22:
        return "evening"
    return "night"  # covers 23 and 0-5


DEATH_ZONE_MID: str = "mid lane"
DEATH_ZONE_TOP: str = "top side"
DEATH_ZONE_BOT: str = "bot side"
DEATH_ZONE_UNKNOWN: str = "unknown"


def death_context(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Annotate every death with what the timeline actually recorded.

    Rebuilt on the reparsed data. Where a death was, who got it, whether anyone
    helped, and how the player stood against their lane opponent at that minute
    are all real now; before the reparse none of them existed and the categories
    compared the player to their own season average instead.

    Columns: match_id, death_number, timestamp_min, gold_at_death,
    opp_gold_at_death, lane_gold_diff, killed_by_laner, killer_champion,
    is_solo_death, death_zone, in_enemy_half, phase, is_early_death,
    is_tilt_spiral, is_overextension_ahead, is_deficit_fight,
    is_post_laning_throw, context_known.

    Games with zero deaths produce no rows — that is not an error.
    """
    df = conn.execute("""
        SELECT
            d.match_id,
            d.death_number,
            d.timestamp_min,
            d.gold_at_death,
            d.opp_gold_at_death,
            d.position_x,
            d.position_y,
            d.killer_champion,
            d.assist_count,
            m.opp_champion_name,
            m.team_id
        FROM match_deaths d
        JOIN matches m ON m.match_id = d.match_id
        WHERE m.game_datetime >= ?
          AND m.team_position = ?
        ORDER BY d.match_id, d.death_number
    """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).df()

    columns = [
        "match_id", "death_number", "timestamp_min", "gold_at_death",
        "opp_gold_at_death", "lane_gold_diff", "killed_by_laner",
        "killer_champion", "is_solo_death", "death_zone", "in_enemy_half",
        "phase", "is_early_death", "is_tilt_spiral", "is_overextension_ahead",
        "is_deficit_fight", "is_post_laning_throw", "context_known",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    # Lane standing at the moment of death, against the actual opponent.
    lane_gold_diff = df["gold_at_death"] - df["opp_gold_at_death"]

    offset_from_mid = (df["position_x"] - df["position_y"]).abs()
    has_position = df["position_x"].notna() & df["position_y"].notna()
    death_zone = pd.Series(DEATH_ZONE_UNKNOWN, index=df.index, dtype=object)
    in_corridor = has_position & (offset_from_mid < MID_LANE_CORRIDOR_WIDTH)
    death_zone[in_corridor] = DEATH_ZONE_MID
    # Above the mid diagonal is the top side of the map, below it the bottom.
    death_zone[has_position & ~in_corridor & (df["position_y"] > df["position_x"])] = (
        DEATH_ZONE_TOP
    )
    death_zone[has_position & ~in_corridor & (df["position_y"] <= df["position_x"])] = (
        DEATH_ZONE_BOT
    )

    # Blue side spawns at the low corner, red side at the high corner, so which
    # half a position sits in depends on which team the player was on.
    position_sum = df["position_x"] + df["position_y"]
    is_blue = df["team_id"] == BLUE_TEAM_ID
    in_enemy_half = pd.Series(pd.NA, index=df.index, dtype="boolean")
    in_enemy_half[has_position & is_blue] = position_sum > MAP_DIAGONAL_SUM
    in_enemy_half[has_position & ~is_blue] = position_sum < MAP_DIAGONAL_SUM

    killed_by_laner = (
        df["killer_champion"].notna()
        & df["opp_champion_name"].notna()
        & (df["killer_champion"] == df["opp_champion_name"])
    )

    phase = pd.Series("post-laning", index=df.index, dtype=object)
    phase[df["timestamp_min"] < LANING_PHASE_END_MIN] = "laning"
    phase[df["timestamp_min"] < EARLY_DEATH_THRESHOLD_MIN] = "early"

    previous_timestamp = df.groupby("match_id")["timestamp_min"].shift(1)
    is_tilt_spiral = (
        (df["timestamp_min"] - previous_timestamp) <= TILT_SPIRAL_GAP_MIN
    ) & previous_timestamp.notna()

    known_standing = lane_gold_diff.notna()

    result = pd.DataFrame({
        "match_id": df["match_id"],
        "death_number": df["death_number"],
        "timestamp_min": df["timestamp_min"],
        "gold_at_death": df["gold_at_death"],
        "opp_gold_at_death": df["opp_gold_at_death"],
        "lane_gold_diff": lane_gold_diff,
        "killed_by_laner": killed_by_laner,
        "killer_champion": df["killer_champion"],
        "is_solo_death": df["assist_count"].fillna(0) == 0,
        "death_zone": death_zone,
        "in_enemy_half": in_enemy_half,
        "phase": phase,
        "is_early_death": df["timestamp_min"] < EARLY_DEATH_THRESHOLD_MIN,
        "is_tilt_spiral": is_tilt_spiral.fillna(False),
        # Ahead of, or behind, the actual lane opponent when it happened. These
        # two kept their names but no longer compare the player to themselves.
        "is_overextension_ahead": (
            known_standing
            & (lane_gold_diff > THROW_GOLD_THRESHOLD)
            & (df["timestamp_min"] <= LANING_PHASE_END_MIN)
        ).fillna(False),
        "is_deficit_fight": (
            known_standing
            & (lane_gold_diff < -THROW_GOLD_THRESHOLD)
            & (df["timestamp_min"] <= LANING_PHASE_END_MIN)
        ).fillna(False),
        # Died after laning while the lane was still won.
        "is_post_laning_throw": (
            known_standing
            & (df["timestamp_min"] > LANING_PHASE_END_MIN)
            & (lane_gold_diff > 0)
        ).fillna(False),
        # A death classified without position or killer is reported, not guessed.
        "context_known": has_position & df["killer_champion"].notna(),
    })

    return result[columns].reset_index(drop=True)


def is_throw_game(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Classify each game by whether a real team lead at minute 14 was kept.

    A throw is the team being ahead and losing anyway; a comeback is the
    reverse. Both are measured on ``team_gold - enemy_team_gold`` at the frame
    closest to minute 14, which the reparse made available. The previous
    definition compared the player's own gold to their own season average, so a
    "throw" only meant a better-than-usual start that still lost.

    The boundary is zero — genuinely ahead or genuinely behind. No lead size is
    invented, which PRODUCT.md section 12 forbids.

    ``gold_delta`` is retained unchanged because it is a model feature in
    ``src/models.py::FEATURE_COLS``; changing it would redefine the clusters.

    Columns: match_id, gold_at_14, gold_delta, team_lead_14, lane_gold_diff_14,
    is_throw, is_comeback.
    """
    gold_df = conn.execute("""
        WITH ranked AS (
            SELECT
                mt.match_id,
                mt.gold AS gold_at_14,
                mt.team_gold - mt.enemy_team_gold AS team_lead_14,
                mt.gold - mt.opp_gold AS lane_gold_diff_14,
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
        SELECT match_id, gold_at_14, team_lead_14, lane_gold_diff_14
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
    team_lead = df["team_lead_14"].fillna(0.0)
    df["is_throw"] = (team_lead > 0) & (~df["win"])
    df["is_comeback"] = (team_lead < 0) & df["win"]

    return df[[
        "match_id", "gold_at_14", "gold_delta", "team_lead_14",
        "lane_gold_diff_14", "is_throw", "is_comeback",
    ]]


def roam_timing(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Detect laning-phase roam windows and quantify their CS cost and kill impact.

    Detection uses position data when available: a roam is a contiguous block of
    minutes 4–14 where abs(position_x - position_y) >= MID_LANE_CORRIDOR_WIDTH.

    A single frame is enough. Riot samples the timeline once per minute and a mid
    roam takes 30 to 60 seconds, so requiring two consecutive minutes discarded
    the typical roam: on this dataset it cut detection from 308 games to 81.

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

    # Minutes in which the player assisted a kill, from the parsed event stream.
    participation: dict[str, list[int]] = {}
    try:
        assist_rows = conn.execute("""
            SELECT e.match_id, e.timestamp_min
            FROM match_events e
            JOIN matches m ON m.match_id = e.match_id
            WHERE e.event_type = 'CHAMPION_KILL'
              AND e.player_involvement = 'assist'
              AND m.game_datetime >= ?
              AND m.team_position = ?
        """, [CURRENT_SEASON_START, ANALYSIS_ROLE]).fetchall()
    except duckdb.CatalogException:
        # Databases built before the event reparse have no match_events table.
        assist_rows = []
    for row_match_id, minute in assist_rows:
        participation.setdefault(row_match_id, []).append(int(minute))

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

            # A mid laner collapsing on a side lane usually gets the assist, not
            # the kill. Counting only kills scored every such roam as a failure.
            window = participation.get(match_id, [])
            assists_during = sum(
                1 for minute in window if roam_start <= minute <= roam_end
            )

            results.append({
                "match_id": match_id,
                "roam_start_min": roam_start,
                "roam_end_min": roam_end,
                "cs_before": cs_before,
                "cs_after": cs_after,
                "expected_cs_delta": expected_cs_delta,
                "cs_sacrifice": cs_sacrifice,
                "kills_during_roam": kills_during,
                "assists_during_roam": assists_during,
                "roam_result": (
                    "impact" if (kills_during + assists_during) > 0 else "no_impact"
                ),
            })

    if not results:
        return pd.DataFrame(columns=[
            "match_id", "roam_start_min", "roam_end_min", "cs_before", "cs_after",
            "expected_cs_delta", "cs_sacrifice", "kills_during_roam",
            "assists_during_roam", "roam_result",
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
