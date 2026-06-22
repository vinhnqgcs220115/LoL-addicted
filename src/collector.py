from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = BASE_DIR / ".env"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

ACCOUNT_BASE_URL = "https://asia.api.riotgames.com"
# Reserved for Summoner-v4 / League-v4 (rank, LP) — Stretch Goal: pro comparison
SUMMONER_BASE_URL = "https://vn1.api.riotgames.com"
MATCH_BASE_URL = "https://sea.api.riotgames.com"

QUEUE_RANKED_SOLO = 420
REQUEST_DELAY_SECONDS = 1.3
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_MATCH_COUNT = 500

JsonPayload = dict[str, Any] | list[Any]

load_dotenv(DOTENV_PATH)


class RiotNotFoundError(RuntimeError):
    """Raised when the Riot API returns HTTP 404."""


def _get_api_key() -> str:
    api_key = os.getenv("RIOT_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing RIOT_API_KEY in .env.")
    return api_key


def _get_retry_after_seconds(header_value: str | None) -> float:
    if not header_value:
        return 1.0

    try:
        return max(float(header_value), 0.0)
    except ValueError:
        return 1.0


def _save_raw(path: Path, payload: JsonPayload) -> None:
    """Write payload atomically via a .tmp file. Raises FileExistsError
    if path already exists — raw files are write-once and immutable after saving."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"{path.name} already exists; raw files are write-once.")
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        tmp.rename(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _resolve_account_identity() -> tuple[str, str]:
    game_name = (
        os.getenv("GAME_NAME", "").strip()
        or os.getenv("RIOT_GAME_NAME", "").strip()
        or os.getenv("SUMMONER_NAME", "").strip()
    )
    tag = os.getenv("TAG", "").strip() or os.getenv("RIOT_TAG", "").strip()

    if "#" in game_name:
        parsed_name, parsed_tag = game_name.split("#", 1)
        game_name = parsed_name.strip()
        tag = tag or parsed_tag.strip()

    if not game_name or not tag:
        raise ValueError(
            "Missing Riot ID. Set PUUID, or provide SUMMONER_NAME as game_name#tag, or set GAME_NAME and TAG in .env."
        )

    return game_name, tag


def _detail_path(match_id: str) -> Path:
    return RAW_DATA_DIR / f"{match_id}.json"


def _timeline_path(match_id: str) -> Path:
    return RAW_DATA_DIR / f"{match_id}_timeline.json"


def riot_get_safe(url: str, max_retries: int = 3) -> JsonPayload:
    """Fetch JSON from the Riot API with retry handling for rate limits."""

    headers = {"X-Riot-Token": _get_api_key()}

    for attempt in range(1, max_retries + 1):
        time.sleep(REQUEST_DELAY_SECONDS)
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException:
            if attempt == max_retries:
                raise
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        if response.status_code == 429:
            if attempt == max_retries:
                response.raise_for_status()

            retry_after_seconds = _get_retry_after_seconds(response.headers.get("Retry-After"))
            time.sleep(retry_after_seconds + 1)
            continue

        if response.status_code == 403:
            raise PermissionError(
                "Riot API key was rejected (403). Regenerate it at developer.riotgames.com and update .env."
            )

        if response.status_code == 404:
            raise RiotNotFoundError(f"Riot API resource not found: {url}")

        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, (dict, list)):
            raise TypeError(f"Unexpected Riot API payload type: {type(payload).__name__}")

        return payload

    raise RuntimeError(f"Failed to fetch Riot API resource after {max_retries} attempts: {url}")


def get_puuid(game_name: str, tag: str) -> str:
    """Fetch and persist the PUUID for the supplied Riot account."""

    url = (
        f"{ACCOUNT_BASE_URL}/riot/account/v1/accounts/by-riot-id/"
        f"{quote(game_name, safe='')}/{quote(tag, safe='')}"
    )
    payload = riot_get_safe(url)

    if not isinstance(payload, dict) or "puuid" not in payload:
        raise KeyError("PUUID was not present in the Riot account response.")

    puuid = str(payload["puuid"])
    set_key(str(DOTENV_PATH), "PUUID", puuid, quote_mode="never")
    os.environ["PUUID"] = puuid
    return puuid


def get_match_ids(
    puuid: str,
    count: int = DEFAULT_MATCH_COUNT,
    start_time: int | None = None,
    end_time: int | None = None,
) -> list[str]:
    """Fetch recent ranked Solo/Duo match IDs for a player, paginating as needed."""

    all_ids: list[str] = []
    start = 0

    while len(all_ids) < count:
        batch_size = min(100, count - len(all_ids))
        url = (
            f"{MATCH_BASE_URL}/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids"
            f"?start={start}&count={batch_size}&queue={QUEUE_RANKED_SOLO}&type=ranked"
        )
        if start_time is not None:
            url += f"&startTime={start_time}"
        if end_time is not None:
            url += f"&endTime={end_time}"
        payload = riot_get_safe(url)

        if not isinstance(payload, list):
            raise TypeError("Expected a list of match IDs from the Riot API.")

        batch = [str(match_id) for match_id in payload]
        if not batch:
            break

        all_ids.extend(batch)
        start += len(batch)

        if len(batch) < batch_size:
            break

    return list(dict.fromkeys(all_ids))[:count]


def get_match_detail(match_id: str) -> bool:
    """Fetch and persist one raw match payload if it is not already on disk."""

    raw_path = _detail_path(match_id)
    if raw_path.exists():
        return True

    url = f"{MATCH_BASE_URL}/lol/match/v5/matches/{quote(match_id, safe='')}"

    try:
        payload = riot_get_safe(url)
    except RiotNotFoundError:
        print(f"Missing match detail for {match_id}")
        return False

    if not isinstance(payload, dict):
        raise TypeError("Expected a match-detail object from the Riot API.")

    try:
        _save_raw(raw_path, payload)
    except FileExistsError:
        return True

    return True


def get_match_timeline(match_id: str) -> bool:
    """Fetch and persist one raw match timeline payload if it is not already on disk."""

    raw_path = _timeline_path(match_id)
    if raw_path.exists():
        return True

    url = f"{MATCH_BASE_URL}/lol/match/v5/matches/{quote(match_id, safe='')}/timeline"

    try:
        payload = riot_get_safe(url)
    except RiotNotFoundError:
        print(f"Missing match timeline for {match_id}")
        return False

    if not isinstance(payload, dict):
        raise TypeError("Expected a match-timeline object from the Riot API.")

    try:
        _save_raw(raw_path, payload)
    except FileExistsError:
        return True

    return True


def run_collection(
    count: int = DEFAULT_MATCH_COUNT,
    start_time: int | None = None,
    end_time: int | None = None,
) -> None:
    """Collect match details and timelines for the configured Riot account."""

    load_dotenv(DOTENV_PATH)

    puuid = os.getenv("PUUID", "").strip()
    if not puuid:
        game_name, tag = _resolve_account_identity()
        puuid = get_puuid(game_name, tag)

    match_ids = get_match_ids(puuid, count=count, start_time=start_time, end_time=end_time)
    total_matches = len(match_ids)

    if total_matches == 0:
        print("No ranked Solo/Duo matches found.")
        return

    for index, match_id in enumerate(match_ids, start=1):
        had_detail = _detail_path(match_id).exists()
        had_timeline = _timeline_path(match_id).exists()
        detail_ok = get_match_detail(match_id)
        timeline_ok = get_match_timeline(match_id)

        if detail_ok and timeline_ok:
            status = "skipped" if had_detail and had_timeline else "saved"
        elif detail_ok:
            status = "timeline missing"
        elif timeline_ok:
            status = "detail missing"
        else:
            status = "missing"

        print(f"[{index}/{total_matches}] {match_id} - {status}")


if __name__ == "__main__":
    run_collection()