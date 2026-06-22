from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = BASE_DIR / ".env"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "lol.duckdb"

MATCH_COLUMNS = (
    "match_id",
    "puuid",
    "game_datetime",
    "game_version",
    "queue_id",
    "game_duration_sec",
    "champion_id",
    "champion_name",
    "team_id",
    "team_position",
    "lane",
    "win",
    "kills",
    "deaths",
    "assists",
    "kda",
    "cs_total",
    "cs_per_min",
    "gold_earned",
    "damage_dealt_to_champions",
    "vision_score",
    "opp_champion_name",
    "opp_cs_total",
    "opp_gold_earned",
    "opp_kills",
    "opp_deaths",
    "opp_assists",
)

TIMELINE_COLUMNS = (
    "match_id",
    "timestamp_min",
    "gold",
    "cs",
    "xp",
    "kills",
    "position_x",
    "position_y",
)

DEATH_COLUMNS = (
    "match_id",
    "death_number",
    "timestamp_ms",
    "timestamp_min",
    "gold_at_death",
    "cs_at_death",
)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise TypeError(f"Expected a JSON object in {path.name}.")

    return payload


def _to_iso8601(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).isoformat()


def _parse_game_version(raw_game_version: str) -> str:
    version_parts = raw_game_version.split(".")
    if len(version_parts) < 2:
        return raw_game_version
    return ".".join(version_parts[:2])


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the DuckDB schema for match-level and per-minute timeline data."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            match_id VARCHAR PRIMARY KEY,
            puuid VARCHAR NOT NULL,
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
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS match_timelines (
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
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS match_deaths (
            match_id VARCHAR NOT NULL,
            death_number INTEGER NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            timestamp_min INTEGER NOT NULL,
            gold_at_death INTEGER,
            cs_at_death INTEGER,
            PRIMARY KEY (match_id, death_number)
        )
        """
    )


def get_participant(raw_match: dict[str, Any], puuid: str) -> dict[str, Any]:
    """Return the participant payload for the configured player."""

    participants = raw_match.get("info", {}).get("participants", [])
    if not isinstance(participants, list):
        raise ValueError("Match payload does not contain a participants list.")

    for participant in participants:
        if isinstance(participant, dict) and participant.get("puuid") == puuid:
            return participant

    raise ValueError(f"PUUID {puuid} was not found in match participants.")


def get_participant_id(raw_match: dict[str, Any], puuid: str) -> int:
    """Return the Riot participantId for the configured player."""

    participant = get_participant(raw_match, puuid)
    participant_id = participant.get("participantId")
    if participant_id is None:
        raise ValueError("Participant payload does not contain participantId.")
    return int(participant_id)


def get_opponent_mid(raw_match: dict[str, Any], puuid: str) -> dict[str, Any] | None:
    """Return the opponent mid laner participant, or None if not found."""

    our_participant = get_participant(raw_match, puuid)
    our_team_id = int(our_participant.get("teamId", 0))
    participants = raw_match.get("info", {}).get("participants", [])

    for participant in participants:
        if not isinstance(participant, dict):
            continue
        if int(participant.get("teamId", 0)) == our_team_id:
            continue
        pos = participant.get("individualPosition", "") or participant.get("teamPosition", "")
        if pos == "MIDDLE":
            return participant

    return None


def extract_match_row(raw_match: dict[str, Any], puuid: str) -> dict[str, Any]:
    """Flatten one raw match payload into a row for the matches table."""

    metadata = raw_match["metadata"]
    info = raw_match["info"]
    participant = get_participant(raw_match, puuid)

    kills = int(participant.get("kills", 0))
    deaths = int(participant.get("deaths", 0))
    assists = int(participant.get("assists", 0))
    cs_total = int(participant.get("totalMinionsKilled", 0)) + int(participant.get("neutralMinionsKilled", 0))
    game_duration_sec = int(info.get("gameDuration", 0))
    duration_minutes = game_duration_sec / 60 if game_duration_sec > 0 else 0.0
    cs_per_min = cs_total / duration_minutes if duration_minutes else 0.0
    team_position = participant.get("teamPosition") or participant.get("individualPosition")

    return {
        "match_id": str(metadata["matchId"]),
        "puuid": puuid,
        "game_datetime": _to_iso8601(int(info["gameCreation"])),
        "game_version": _parse_game_version(str(info["gameVersion"])),
        "queue_id": int(info.get("queueId", 0)),
        "game_duration_sec": game_duration_sec,
        "champion_id": int(participant.get("championId", 0)),
        "champion_name": str(participant["championName"]),
        "team_id": int(participant.get("teamId", 0)),
        "team_position": str(team_position) if team_position else None,
        "lane": str(participant.get("lane", "")) or None,
        "win": bool(participant["win"]),
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda": (kills + assists) / max(deaths, 1),
        "cs_total": cs_total,
        "cs_per_min": cs_per_min,
        "gold_earned": int(participant.get("goldEarned", 0)),
        "damage_dealt_to_champions": int(participant.get("totalDamageDealtToChampions", 0)),
        "vision_score": int(participant.get("visionScore", 0)),
        **_extract_opp_fields(raw_match, puuid),
    }


def _extract_opp_fields(raw_match: dict[str, Any], puuid: str) -> dict[str, Any]:
    """Extract opponent mid laner fields; returns NULL-valued dict if not found."""

    opp = get_opponent_mid(raw_match, puuid)
    if opp is None:
        return {
            "opp_champion_name": None,
            "opp_cs_total": None,
            "opp_gold_earned": None,
            "opp_kills": None,
            "opp_deaths": None,
            "opp_assists": None,
        }
    opp_cs = int(opp.get("totalMinionsKilled", 0)) + int(opp.get("neutralMinionsKilled", 0))
    return {
        "opp_champion_name": str(opp["championName"]),
        "opp_cs_total": opp_cs,
        "opp_gold_earned": int(opp.get("goldEarned", 0)),
        "opp_kills": int(opp.get("kills", 0)),
        "opp_deaths": int(opp.get("deaths", 0)),
        "opp_assists": int(opp.get("assists", 0)),
    }


def extract_timeline_rows(
    raw_match: dict[str, Any], raw_timeline: dict[str, Any], puuid: str
) -> list[dict[str, Any]]:
    """Extract one per-minute timeline row for the configured player."""

    match_id = str(raw_match["metadata"]["matchId"])
    participant_id = get_participant_id(raw_match, puuid)
    participant_key = str(participant_id)
    frames = raw_timeline.get("info", {}).get("frames", [])

    if not isinstance(frames, list):
        raise ValueError("Timeline payload does not contain a frames list.")

    timeline_rows_by_minute: dict[int, dict[str, Any]] = {}
    kills_so_far = 0

    for frame in frames:
        if not isinstance(frame, dict):
            continue

        events = frame.get("events", [])
        if isinstance(events, list):
            kills_so_far += sum(
                1
                for event in events
                if isinstance(event, dict)
                and event.get("type") == "CHAMPION_KILL"
                and event.get("killerId") == participant_id
            )

        participant_frames = frame.get("participantFrames", {})
        if not isinstance(participant_frames, dict):
            continue

        participant_frame = participant_frames.get(participant_key)
        if not isinstance(participant_frame, dict):
            continue

        timestamp_min = int(int(frame.get("timestamp", 0)) // 60000)
        position = participant_frame.get("position")
        pos_x: int | None = int(position["x"]) if isinstance(position, dict) and "x" in position else None
        pos_y: int | None = int(position["y"]) if isinstance(position, dict) and "y" in position else None
        # Riot can emit a final end-of-game frame inside the current minute bucket.
        # Keep the latest snapshot so we still return one row per minute.
        timeline_rows_by_minute[timestamp_min] = {
            "match_id": match_id,
            "timestamp_min": timestamp_min,
            "gold": int(participant_frame.get("totalGold", 0)),
            "cs": int(participant_frame.get("minionsKilled", 0))
            + int(participant_frame.get("jungleMinionsKilled", 0)),
            "xp": int(participant_frame.get("xp", 0)),
            "kills": kills_so_far,
            "position_x": pos_x,
            "position_y": pos_y,
        }

    return [timeline_rows_by_minute[timestamp_min] for timestamp_min in sorted(timeline_rows_by_minute)]


def extract_death_rows(
    raw_match: dict[str, Any],
    raw_timeline: dict[str, Any],
    puuid: str,
) -> list[dict[str, Any]]:
    """Extract one row per death of the configured player from timeline events."""

    match_id = str(raw_match["metadata"]["matchId"])
    participant_id = get_participant_id(raw_match, puuid)
    frames = raw_timeline.get("info", {}).get("frames", [])

    if not isinstance(frames, list):
        return []

    # Build per-minute lookup from raw frames for gold/cs at time of death.
    participant_key = str(participant_id)
    minute_snapshot: dict[int, dict[str, int]] = {}
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        participant_frames = frame.get("participantFrames", {})
        if not isinstance(participant_frames, dict):
            continue
        pf = participant_frames.get(participant_key)
        if not isinstance(pf, dict):
            continue
        ts_min = int(int(frame.get("timestamp", 0)) // 60000)
        minute_snapshot[ts_min] = {
            "gold": int(pf.get("totalGold", 0)),
            "cs": int(pf.get("minionsKilled", 0)) + int(pf.get("jungleMinionsKilled", 0)),
        }

    death_rows: list[dict[str, Any]] = []
    death_number = 0

    for frame in frames:
        if not isinstance(frame, dict):
            continue
        for event in frame.get("events", []):
            if not isinstance(event, dict):
                continue
            if event.get("type") != "CHAMPION_KILL":
                continue
            if event.get("victimId") != participant_id:
                continue

            death_number += 1
            timestamp_ms = int(event.get("timestamp", 0))
            timestamp_min = timestamp_ms // 60000
            snapshot = minute_snapshot.get(timestamp_min)
            death_rows.append({
                "match_id": match_id,
                "death_number": death_number,
                "timestamp_ms": timestamp_ms,
                "timestamp_min": timestamp_min,
                "gold_at_death": snapshot["gold"] if snapshot else None,
                "cs_at_death": snapshot["cs"] if snapshot else None,
            })

    return death_rows


def process_match(match_id: str, puuid: str, conn: duckdb.DuckDBPyConnection) -> None:
    """Parse and insert one match and its timeline into DuckDB."""

    match_path = RAW_DATA_DIR / f"{match_id}.json"
    timeline_path = RAW_DATA_DIR / f"{match_id}_timeline.json"

    if not match_path.exists() or not timeline_path.exists():
        print(f"Warning: skipping {match_id}; missing raw match or timeline file.")
        return

    raw_match = _load_json(match_path)
    raw_timeline = _load_json(timeline_path)

    match_row = extract_match_row(raw_match, puuid)
    timeline_rows = extract_timeline_rows(raw_match, raw_timeline, puuid)
    death_rows = extract_death_rows(raw_match, raw_timeline, puuid)

    match_placeholders = ", ".join("?" for _ in MATCH_COLUMNS)
    timeline_placeholders = ", ".join("?" for _ in TIMELINE_COLUMNS)

    conn.execute("BEGIN")
    try:
        conn.execute(
            f"INSERT OR IGNORE INTO matches ({', '.join(MATCH_COLUMNS)}) VALUES ({match_placeholders})",
            [match_row[column] for column in MATCH_COLUMNS],
        )

        if timeline_rows:
            conn.executemany(
                f"INSERT OR IGNORE INTO match_timelines ({', '.join(TIMELINE_COLUMNS)}) VALUES ({timeline_placeholders})",
                [[row[column] for column in TIMELINE_COLUMNS] for row in timeline_rows],
            )

        if death_rows:
            death_placeholders = ", ".join("?" for _ in DEATH_COLUMNS)
            conn.executemany(
                f"INSERT OR IGNORE INTO match_deaths ({', '.join(DEATH_COLUMNS)}) VALUES ({death_placeholders})",
                [[row[column] for column in DEATH_COLUMNS] for row in death_rows],
            )

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def run_pipeline() -> None:
    """Load all collected raw files into DuckDB."""

    load_dotenv(DOTENV_PATH)
    puuid = os.getenv("PUUID", "").strip()

    if not puuid:
        raise ValueError("Missing PUUID in .env. Run collection first or add PUUID manually.")

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    match_files = sorted(
        path for path in RAW_DATA_DIR.glob("*.json") if not path.name.endswith("_timeline.json")
    )

    processed = 0
    skipped = 0

    with duckdb.connect(str(DB_PATH)) as conn:
        init_schema(conn)

        for match_file in match_files:
            match_id = match_file.stem
            timeline_path = RAW_DATA_DIR / f"{match_id}_timeline.json"

            if not timeline_path.exists():
                print(f"Warning: skipping {match_id}; missing timeline file.")
                skipped += 1
                continue

            try:
                process_match(match_id, puuid, conn)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                print(f"Warning: failed to process {match_id}: {exc}")
                skipped += 1
                continue

            processed += 1

        row_count = int(conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0])

    print(f"Processed: {processed}, skipped: {skipped}, matches rows: {row_count}")


if __name__ == "__main__":
    run_pipeline()