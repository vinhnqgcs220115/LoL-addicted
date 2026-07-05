from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_MATCH_ID = "VN2_1424864796"
SAMPLE_PUUID = "y4E9BsASYNK7Sgq8pr-D2X7Jg8CFHaKH8IgZEoAkKvN0O-QamyDYmJJcNUWKMln0-x0hv6PROsuePg"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def sample_match() -> dict[str, Any]:
    return _load_json(FIXTURES_DIR / "sample_match.json")


@pytest.fixture
def sample_timeline() -> dict[str, Any]:
    return _load_json(FIXTURES_DIR / "sample_match_timeline.json")


@pytest.fixture
def zero_death_match(sample_match: dict[str, Any]) -> dict[str, Any]:
    raw_match = deepcopy(sample_match)
    participant = next(item for item in raw_match["info"]["participants"] if item["puuid"] == SAMPLE_PUUID)
    participant["deaths"] = 0
    participant["kills"] = 7
    participant["assists"] = 6
    return raw_match


@pytest.fixture
def gap_timeline(sample_timeline: dict[str, Any]) -> dict[str, Any]:
    raw_timeline = deepcopy(sample_timeline)
    frames = raw_timeline["info"]["frames"]
    minute_ten_index = next(
        index
        for index, frame in enumerate(frames)
        if isinstance(frame, dict) and int(int(frame.get("timestamp", 0)) // 60000) == 10
    )
    frames.pop(minute_ten_index)
    return raw_timeline