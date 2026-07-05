from __future__ import annotations

import sys
from pathlib import Path

import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_DB = BASE_DIR / "data" / "lol.duckdb"
DEPLOY_DB = BASE_DIR / "data" / "lol_deploy.duckdb"
TABLES = (
    "matches",
    "match_timelines",
    "match_deaths",
    "feature_matrix",
    "cluster_labels",
)

sys.path.insert(0, str(BASE_DIR))

from src.features import ANALYSIS_ROLE, CURRENT_SEASON_START  # noqa: E402


def build_deploy_db() -> dict[str, int]:
    """Rebuild the sanitized, analysis-scoped deployment database."""
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Source database not found: {SOURCE_DB}")

    DEPLOY_DB.unlink(missing_ok=True)
    source_path = str(SOURCE_DB).replace("'", "''")

    try:
        with duckdb.connect(str(DEPLOY_DB)) as conn:
            conn.execute(f"ATTACH '{source_path}' AS source (READ_ONLY)")
            original_ids = conn.execute(
                """
                SELECT match_id
                FROM source.matches
                WHERE game_datetime >= ? AND team_position = ?
                ORDER BY game_datetime
                """,
                [CURRENT_SEASON_START, ANALYSIS_ROLE],
            ).fetchall()
            if not original_ids:
                raise ValueError("No matches found in the current season and role scope.")

            conn.execute("""
                CREATE TEMP TABLE id_map (
                    original_match_id VARCHAR PRIMARY KEY,
                    surrogate_match_id VARCHAR UNIQUE NOT NULL
                )
            """)
            conn.executemany(
                "INSERT INTO id_map VALUES (?, ?)",
                [
                    (match_id, f"GAME_{index:04d}")
                    for index, (match_id,) in enumerate(original_ids, start=1)
                ],
            )

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
                INSERT INTO matches
                SELECT
                    ids.surrogate_match_id,
                    m.game_datetime,
                    m.game_version,
                    m.queue_id,
                    m.game_duration_sec,
                    m.champion_id,
                    m.champion_name,
                    m.team_id,
                    m.team_position,
                    m.lane,
                    m.win,
                    m.kills,
                    m.deaths,
                    m.assists,
                    m.kda,
                    m.cs_total,
                    m.cs_per_min,
                    m.gold_earned,
                    m.damage_dealt_to_champions,
                    m.vision_score,
                    m.opp_champion_name,
                    m.opp_cs_total,
                    m.opp_gold_earned,
                    m.opp_kills,
                    m.opp_deaths,
                    m.opp_assists
                FROM source.matches m
                JOIN id_map ids ON ids.original_match_id = m.match_id
            """)

            conn.execute("""
                CREATE TABLE match_timelines (
                    match_id VARCHAR NOT NULL,
                    timestamp_min INTEGER NOT NULL,
                    gold INTEGER NOT NULL,
                    cs INTEGER NOT NULL,
                    xp INTEGER NOT NULL,
                    kills INTEGER NOT NULL,
                    position_x INTEGER,
                    position_y INTEGER,
                    PRIMARY KEY (match_id, timestamp_min)
                )
            """)
            conn.execute("""
                INSERT INTO match_timelines
                SELECT
                    ids.surrogate_match_id,
                    t.timestamp_min,
                    t.gold,
                    t.cs,
                    t.xp,
                    t.kills,
                    t.position_x,
                    t.position_y
                FROM source.match_timelines t
                JOIN id_map ids ON ids.original_match_id = t.match_id
            """)

            conn.execute("""
                CREATE TABLE match_deaths (
                    match_id VARCHAR NOT NULL,
                    death_number INTEGER NOT NULL,
                    timestamp_ms INTEGER NOT NULL,
                    timestamp_min INTEGER NOT NULL,
                    gold_at_death INTEGER,
                    cs_at_death INTEGER,
                    PRIMARY KEY (match_id, death_number)
                )
            """)
            conn.execute("""
                INSERT INTO match_deaths
                SELECT
                    ids.surrogate_match_id,
                    d.death_number,
                    d.timestamp_ms,
                    d.timestamp_min,
                    d.gold_at_death,
                    d.cs_at_death
                FROM source.match_deaths d
                JOIN id_map ids ON ids.original_match_id = d.match_id
            """)

            conn.execute(
                "CREATE TABLE feature_matrix AS "
                "SELECT * FROM source.feature_matrix WHERE FALSE"
            )
            conn.execute("""
                INSERT INTO feature_matrix
                SELECT ids.surrogate_match_id, f.* EXCLUDE (match_id)
                FROM source.feature_matrix f
                JOIN id_map ids ON ids.original_match_id = f.match_id
            """)

            conn.execute("""
                CREATE TABLE cluster_labels (
                    match_id VARCHAR PRIMARY KEY,
                    cluster_id INTEGER NOT NULL
                )
            """)
            conn.execute("""
                INSERT INTO cluster_labels
                SELECT ids.surrogate_match_id, l.cluster_id
                FROM source.cluster_labels l
                JOIN id_map ids ON ids.original_match_id = l.match_id
            """)

            counts = {
                table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in TABLES
            }
    except Exception:
        DEPLOY_DB.unlink(missing_ok=True)
        raise

    for table, count in counts.items():
        print(f"{table}: {count}")
    print(f"Output: {DEPLOY_DB}")
    return counts


if __name__ == "__main__":
    try:
        build_deploy_db()
    except Exception as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
