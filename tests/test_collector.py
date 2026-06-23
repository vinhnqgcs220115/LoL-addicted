from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from src import collector


class DummyResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> dict[str, Any] | list[Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_resolve_account_identity_from_summoner_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAME_NAME", raising=False)
    monkeypatch.delenv("RIOT_GAME_NAME", raising=False)
    monkeypatch.delenv("TAG", raising=False)
    monkeypatch.delenv("RIOT_TAG", raising=False)
    monkeypatch.setenv("SUMMONER_NAME", "Myishaa#2946S")

    assert collector._resolve_account_identity() == ("Myishaa", "2946S")


def test_resolve_account_identity_raises_without_riot_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAME_NAME", raising=False)
    monkeypatch.delenv("RIOT_GAME_NAME", raising=False)
    monkeypatch.delenv("SUMMONER_NAME", raising=False)
    monkeypatch.delenv("TAG", raising=False)
    monkeypatch.delenv("RIOT_TAG", raising=False)

    with pytest.raises(ValueError, match="Missing Riot ID"):
        collector._resolve_account_identity()


def test_riot_get_safe_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    responses = [
        DummyResponse(429, headers={"Retry-After": "2"}),
        DummyResponse(200, payload={"ok": True}),
    ]

    def fake_get(*args: Any, **kwargs: Any) -> DummyResponse:
        return responses.pop(0)

    monkeypatch.setenv("RIOT_API_KEY", "test-key")
    monkeypatch.setattr(collector.requests, "get", fake_get)
    monkeypatch.setattr(collector.time, "sleep", sleep_calls.append)

    payload = collector.riot_get_safe("https://example.test/resource")

    assert payload == {"ok": True}
    assert sleep_calls == [1.3, 3.0, 1.3]


def test_riot_get_safe_raises_on_403(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOT_API_KEY", "test-key")
    monkeypatch.setattr(collector.requests, "get", lambda *args, **kwargs: DummyResponse(403))
    monkeypatch.setattr(collector.time, "sleep", lambda *_args: None)

    with pytest.raises(PermissionError, match="developer.riotgames.com"):
        collector.riot_get_safe("https://example.test/resource")


def test_riot_get_safe_raises_not_found_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOT_API_KEY", "test-key")
    monkeypatch.setattr(collector.requests, "get", lambda *args, **kwargs: DummyResponse(404))
    monkeypatch.setattr(collector.time, "sleep", lambda *_args: None)

    with pytest.raises(collector.RiotNotFoundError):
        collector.riot_get_safe("https://example.test/resource")


def test_get_puuid_raises_when_payload_has_no_puuid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collector, "riot_get_safe", lambda url: {"gameName": "Myishaa"})

    with pytest.raises(KeyError, match="PUUID"):
        collector.get_puuid("Myishaa", "2946S")


def test_get_match_ids_raises_on_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collector, "riot_get_safe", lambda url: {"bad": "payload"})

    with pytest.raises(TypeError, match="list of match IDs"):
        collector.get_match_ids("sample-puuid")


def test_get_match_detail_skips_existing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    existing_path = tmp_path / "VN2_existing.json"
    existing_path.write_text(json.dumps({"already": "here"}), encoding="utf-8")

    def fail_if_called(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("riot_get_safe should not be called when the raw file already exists")

    monkeypatch.setattr(collector, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(collector, "riot_get_safe", fail_if_called)

    assert collector.get_match_detail("VN2_existing") is True
    assert json.loads(existing_path.read_text(encoding="utf-8")) == {"already": "here"}


def test_get_match_timeline_returns_false_on_404(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(collector, "RAW_DATA_DIR", tmp_path)

    def raise_not_found(url: str) -> None:
        raise collector.RiotNotFoundError(url)

    monkeypatch.setattr(collector, "riot_get_safe", raise_not_found)

    assert collector.get_match_timeline("VN2_missing") is False
    assert not (tmp_path / "VN2_missing_timeline.json").exists()


def test_run_collection_prints_message_when_no_matches_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(collector, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("PUUID", "some-puuid")
    monkeypatch.setattr(collector, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(collector, "get_match_ids", lambda puuid, count, start_time=None, end_time=None: [])

    collector.run_collection()
    captured = capsys.readouterr()

    assert "No ranked Solo/Duo matches found." in captured.out


def test_get_match_ids_single_page(monkeypatch: pytest.MonkeyPatch) -> None:
    ids = [f"VN2_{i:04d}" for i in range(50)]
    call_count = 0

    def fake_riot_get_safe(url: str) -> list[str]:
        nonlocal call_count
        call_count += 1
        return ids

    monkeypatch.setattr(collector, "riot_get_safe", fake_riot_get_safe)

    result = collector.get_match_ids("test-puuid", count=50)

    assert call_count == 1
    assert len(result) == 50
    assert result == ids


def test_get_match_ids_exact_two_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    page1 = [f"VN2_A{i:03d}" for i in range(100)]
    page2 = [f"VN2_B{i:03d}" for i in range(50)]
    pages = [page1, page2]
    call_count = 0

    def fake_riot_get_safe(url: str) -> list[str]:
        nonlocal call_count
        call_count += 1
        return pages[call_count - 1]

    monkeypatch.setattr(collector, "riot_get_safe", fake_riot_get_safe)

    result = collector.get_match_ids("test-puuid", count=150)

    assert call_count == 2
    assert len(result) == 150
    assert len(set(result)) == 150  # no duplicates


def test_get_match_ids_early_termination_history_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page1 = [f"VN2_A{i:03d}" for i in range(100)]
    page2 = [f"VN2_B{i:03d}" for i in range(100)]
    page3 = [f"VN2_C{i:03d}" for i in range(30)]
    pages = [page1, page2, page3]
    call_count = 0

    def fake_riot_get_safe(url: str) -> list[str]:
        nonlocal call_count
        call_count += 1
        return pages[call_count - 1]

    monkeypatch.setattr(collector, "riot_get_safe", fake_riot_get_safe)

    result = collector.get_match_ids("test-puuid", count=300)

    assert call_count == 3
    assert len(result) == 230


def test_get_match_ids_empty_response_on_first_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(collector, "riot_get_safe", lambda url: [])

    result = collector.get_match_ids("test-puuid", count=100)

    assert result == []


def test_get_match_ids_count_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    def fake_riot_get_safe(url: str) -> list[str]:
        nonlocal call_count
        call_count += 1
        offset = (call_count - 1) * 100
        return [f"VN2_{offset + i:04d}" for i in range(100)]

    monkeypatch.setattr(collector, "riot_get_safe", fake_riot_get_safe)

    result = collector.get_match_ids("test-puuid", count=150)

    assert len(result) == 150
    assert len(set(result)) == 150  # no duplicates


def test_get_match_ids_includes_start_time_in_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_urls: list[str] = []

    def fake_riot_get_safe(url: str) -> list[str]:
        captured_urls.append(url)
        return [f"VN2_{i:04d}" for i in range(10)]

    monkeypatch.setattr(collector, "riot_get_safe", fake_riot_get_safe)

    collector.get_match_ids("test-puuid", count=10, start_time=1736467200)

    assert len(captured_urls) == 1
    assert "startTime=1736467200" in captured_urls[0]


def test_get_match_ids_no_time_params_url_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_urls: list[str] = []

    def fake_riot_get_safe(url: str) -> list[str]:
        captured_urls.append(url)
        return [f"VN2_{i:04d}" for i in range(10)]

    monkeypatch.setattr(collector, "riot_get_safe", fake_riot_get_safe)

    collector.get_match_ids("test-puuid", count=10)

    assert len(captured_urls) == 1
    assert "startTime" not in captured_urls[0]
    assert "endTime" not in captured_urls[0]


def test_riot_get_safe_retries_on_connection_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0

    def fake_get(*args: Any, **kwargs: Any) -> DummyResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise requests.ConnectionError("simulated network failure")
        return DummyResponse(200, payload={"ok": True})

    monkeypatch.setenv("RIOT_API_KEY", "test-key")
    monkeypatch.setattr(collector.requests, "get", fake_get)
    monkeypatch.setattr(collector.time, "sleep", lambda *_: None)

    result = collector.riot_get_safe("https://example.test/resource")
    assert result == {"ok": True}
    assert call_count == 2


def test_riot_get_safe_raises_after_all_retries_on_connection_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def always_fail(*args: Any, **kwargs: Any) -> None:
        raise requests.ConnectionError("persistent failure")

    monkeypatch.setenv("RIOT_API_KEY", "test-key")
    monkeypatch.setattr(collector.requests, "get", always_fail)
    monkeypatch.setattr(collector.time, "sleep", lambda *_: None)

    with pytest.raises(requests.ConnectionError):
        collector.riot_get_safe("https://example.test/resource")
