from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

from src import processor
from tests.conftest import SAMPLE_MATCH_ID, SAMPLE_PUUID


def test_init_schema_creates_all_tables() -> None:
    conn = duckdb.connect(":memory:")
    try:
        processor.init_schema(conn)
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    finally:
        conn.close()

    assert "matches" in tables
    assert "match_timelines" in tables
    assert "match_deaths" in tables


def test_get_participant_and_id(sample_match: dict[str, object]) -> None:
    participant = processor.get_participant(sample_match, SAMPLE_PUUID)

    assert participant["participantId"] == 8
    assert participant["championName"] == "Fizz"
    assert processor.get_participant_id(sample_match, SAMPLE_PUUID) == 8


def test_get_participant_raises_when_puuid_missing(sample_match: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="was not found"):
        processor.get_participant(sample_match, "missing-puuid")


def test_get_participant_id_raises_when_participant_id_missing(sample_match: dict[str, object]) -> None:
    broken_match = deepcopy(sample_match)
    participant = next(item for item in broken_match["info"]["participants"] if item["puuid"] == SAMPLE_PUUID)
    participant.pop("participantId")

    with pytest.raises(ValueError, match="participantId"):
        processor.get_participant_id(broken_match, SAMPLE_PUUID)


def test_extract_match_row_uses_expected_derived_fields(sample_match: dict[str, object]) -> None:
    row = processor.extract_match_row(sample_match, SAMPLE_PUUID)

    assert row["match_id"] == SAMPLE_MATCH_ID
    assert row["game_version"] == "16.11"
    assert row["champion_name"] == "Fizz"
    assert row["team_position"] == "MIDDLE"
    assert row["lane"] == "MIDDLE"
    assert row["kills"] == 5
    assert row["deaths"] == 7
    assert row["assists"] == 4
    assert row["cs_total"] == 221
    assert row["gold_earned"] == 10976
    assert row["vision_score"] == 13
    assert row["opp_champion_name"] == "Leblanc"
    assert row["opp_cs_total"] == 187
    assert row["opp_gold_earned"] == 15729
    assert row["opp_kills"] == 14
    assert row["opp_deaths"] == 1
    assert row["opp_assists"] == 4
    assert row["win"] is False
    assert row["game_duration_sec"] == 1522
    assert row["kda"] == pytest.approx((5 + 4) / 7)
    assert row["cs_per_min"] == pytest.approx(221 / (1522 / 60))
    assert row["game_datetime"].endswith("+00:00")


def test_extract_match_row_handles_zero_death_kda(zero_death_match: dict[str, object]) -> None:
    row = processor.extract_match_row(zero_death_match, SAMPLE_PUUID)

    assert row["deaths"] == 0
    assert row["kills"] == 7
    assert row["assists"] == 6
    assert row["kda"] == pytest.approx(13.0)


def test_extract_timeline_rows_uses_participant_id(
    sample_match: dict[str, object], sample_timeline: dict[str, object]
) -> None:
    rows = processor.extract_timeline_rows(sample_match, sample_timeline, SAMPLE_PUUID)

    assert len(rows) == 26
    assert rows[0] == {
        "match_id": SAMPLE_MATCH_ID,
        "timestamp_min": 0,
        "gold": 500,
        "cs": 0,
        "xp": 0,
        "kills": 0,
        "position_x": 14321,
        "position_y": 14673,
    }
    assert rows[-1] == {
        "match_id": SAMPLE_MATCH_ID,
        "timestamp_min": 25,
        "gold": 10976,
        "cs": 221,
        "xp": 13381,
        "kills": 5,
        "position_x": 14096,
        "position_y": 13008,
    }


def test_extract_timeline_rows_tolerates_missing_minute_frames(
    sample_match: dict[str, object], gap_timeline: dict[str, object]
) -> None:
    rows = processor.extract_timeline_rows(sample_match, gap_timeline, SAMPLE_PUUID)

    assert len(rows) == 25
    assert 10 not in {row["timestamp_min"] for row in rows}
    assert rows[-1]["timestamp_min"] == 25


def test_extract_timeline_rows_raises_when_frames_is_not_a_list(
    sample_match: dict[str, object], sample_timeline: dict[str, object]
) -> None:
    broken_timeline = deepcopy(sample_timeline)
    broken_timeline["info"]["frames"] = {}

    with pytest.raises(ValueError, match="frames list"):
        processor.extract_timeline_rows(sample_match, broken_timeline, SAMPLE_PUUID)


def test_process_match_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture_dir = Path(__file__).parent / "fixtures"
    (tmp_path / f"{SAMPLE_MATCH_ID}.json").write_text(
        (fixture_dir / "sample_match.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / f"{SAMPLE_MATCH_ID}_timeline.json").write_text(
        (fixture_dir / "sample_match_timeline.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    monkeypatch.setattr(processor, "RAW_DATA_DIR", tmp_path)

    conn = duckdb.connect(":memory:")
    try:
        processor.init_schema(conn)
        processor.process_match(SAMPLE_MATCH_ID, SAMPLE_PUUID, conn)
        processor.process_match(SAMPLE_MATCH_ID, SAMPLE_PUUID, conn)

        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        timeline_count = conn.execute("SELECT COUNT(*) FROM match_timelines").fetchone()[0]
    finally:
        conn.close()

    assert match_count == 1
    assert timeline_count == 26


def test_process_match_skips_when_raw_files_are_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(processor, "RAW_DATA_DIR", tmp_path)

    conn = duckdb.connect(":memory:")
    try:
        processor.init_schema(conn)
        processor.process_match("VN2_missing", SAMPLE_PUUID, conn)

        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        timeline_count = conn.execute("SELECT COUNT(*) FROM match_timelines").fetchone()[0]
    finally:
        conn.close()

    assert match_count == 0
    assert timeline_count == 0


def test_run_pipeline_prints_summary_and_skips_missing_timeline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_dir = Path(__file__).parent / "fixtures"
    raw_dir = tmp_path / "raw"
    db_path = tmp_path / "test.duckdb"
    raw_dir.mkdir()

    valid_match_id = SAMPLE_MATCH_ID
    missing_timeline_match_id = "VN2_missingmatch"

    (raw_dir / f"{valid_match_id}.json").write_text(
        (fixture_dir / "sample_match.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (raw_dir / f"{valid_match_id}_timeline.json").write_text(
        (fixture_dir / "sample_match_timeline.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (raw_dir / f"{missing_timeline_match_id}.json").write_text(
        (fixture_dir / "sample_match.json").read_text(encoding="utf-8").replace(SAMPLE_MATCH_ID, missing_timeline_match_id),
        encoding="utf-8",
    )

    monkeypatch.setattr(processor, "RAW_DATA_DIR", raw_dir)
    monkeypatch.setattr(processor, "DB_PATH", db_path)
    monkeypatch.setenv("PUUID", SAMPLE_PUUID)

    processor.run_pipeline()
    captured = capsys.readouterr()

    assert "Warning: skipping VN2_missingmatch; missing timeline file." in captured.out
    assert "Processed: 1, skipped: 1, matches rows: 1" in captured.out

    conn = duckdb.connect(str(db_path))
    try:
        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        timeline_count = conn.execute("SELECT COUNT(*) FROM match_timelines").fetchone()[0]
    finally:
        conn.close()

    assert match_count == 1
    assert timeline_count == 26


def test_run_pipeline_raises_when_puuid_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(processor, "RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr(processor, "DB_PATH", tmp_path / "test.duckdb")
    monkeypatch.setattr(processor, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("PUUID", raising=False)

    with pytest.raises(ValueError, match="Missing PUUID"):
        processor.run_pipeline()


def _make_minimal_match(match_id: str, puuid: str, participant_id: int) -> dict:
    return {
        "metadata": {"matchId": match_id},
        "info": {
            "participants": [
                {
                    "puuid": puuid,
                    "participantId": participant_id,
                    "championName": "Fizz",
                    "teamId": 100,
                }
            ]
        },
    }


def test_extract_death_rows_basic() -> None:
    match = _make_minimal_match("VN2_TEST", SAMPLE_PUUID, 1)
    timeline = {
        "info": {
            "frames": [
                {
                    "timestamp": 300000,  # minute 5
                    "participantFrames": {
                        "1": {
                            "totalGold": 3000,
                            "minionsKilled": 50,
                            "jungleMinionsKilled": 0,
                            "xp": 2000,
                            "position": {"x": 7500, "y": 7500},
                        }
                    },
                    "events": [
                        {"type": "CHAMPION_KILL", "victimId": 1, "timestamp": 300000}
                    ],
                }
            ]
        }
    }

    rows = processor.extract_death_rows(match, timeline, SAMPLE_PUUID)

    assert len(rows) == 1
    assert rows[0]["death_number"] == 1
    assert rows[0]["timestamp_min"] == 5
    assert rows[0]["gold_at_death"] is not None
    assert isinstance(rows[0]["gold_at_death"], int)


def test_extract_death_rows_no_deaths() -> None:
    match = _make_minimal_match("VN2_TEST", SAMPLE_PUUID, 1)
    timeline = {
        "info": {
            "frames": [
                {
                    "timestamp": 300000,
                    "participantFrames": {
                        "1": {
                            "totalGold": 3000,
                            "minionsKilled": 50,
                            "jungleMinionsKilled": 0,
                            "xp": 2000,
                            "position": {"x": 7500, "y": 7500},
                        }
                    },
                    "events": [
                        # Kill by participant 1 (killerId=1), not a death
                        {"type": "CHAMPION_KILL", "killerId": 1, "victimId": 5, "timestamp": 300000}
                    ],
                }
            ]
        }
    }

    rows = processor.extract_death_rows(match, timeline, SAMPLE_PUUID)

    assert rows == []


def test_extract_death_rows_missing_snapshot() -> None:
    match = _make_minimal_match("VN2_TEST", SAMPLE_PUUID, 1)
    # Only a frame at minute 0; death event at timestamp=420000 (minute 7)
    timeline = {
        "info": {
            "frames": [
                {
                    "timestamp": 0,  # minute 0
                    "participantFrames": {
                        "1": {
                            "totalGold": 500,
                            "minionsKilled": 0,
                            "jungleMinionsKilled": 0,
                            "xp": 0,
                            "position": {"x": 7500, "y": 7500},
                        }
                    },
                    "events": [
                        {"type": "CHAMPION_KILL", "victimId": 1, "timestamp": 420000}
                    ],
                }
            ]
        }
    }

    rows = processor.extract_death_rows(match, timeline, SAMPLE_PUUID)

    assert len(rows) == 1
    assert rows[0]["gold_at_death"] is None
    assert rows[0]["cs_at_death"] is None
