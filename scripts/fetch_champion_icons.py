from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import duckdb
import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DEPLOY_DB = BASE_DIR / "data" / "lol_deploy.duckdb"
ICON_DIR = BASE_DIR / "assets" / "champion_icons"
VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
CDN_URL = "https://ddragon.leagueoflegends.com/cdn"
REQUEST_TIMEOUT_SECONDS = 30

CHAMPION_QUERY = """
    SELECT DISTINCT champion_name FROM matches
    UNION SELECT DISTINCT opp_champion_name FROM matches
"""


def build_icon_mapping(
    stored_names: Iterable[str],
    champion_payload: dict[str, Any],
) -> tuple[dict[str, str], list[str]]:
    """Map stored champion names to Data Dragon image filenames."""
    champion_data = champion_payload.get("data")
    if not isinstance(champion_data, dict):
        raise ValueError("Data Dragon champion response has no data object.")

    candidates: dict[str, set[str]] = {}
    for champion in champion_data.values():
        if not isinstance(champion, dict):
            continue
        image = champion.get("image")
        if not isinstance(image, dict) or not isinstance(image.get("full"), str):
            continue
        for key in (champion.get("id"), champion.get("name")):
            if isinstance(key, str):
                candidates.setdefault(key, set()).add(image["full"])

    mapping: dict[str, str] = {}
    unmapped: list[str] = []
    for stored_name in sorted(set(stored_names)):
        images = candidates.get(stored_name, set())
        if len(images) == 1:
            mapping[stored_name] = next(iter(images))
        else:
            unmapped.append(stored_name)

    return mapping, unmapped


def fetch_champion_icons() -> None:
    """Download missing champion icons required by the deployment database."""
    with duckdb.connect(str(DEPLOY_DB), read_only=True) as conn:
        stored_names = [
            name for (name,) in conn.execute(CHAMPION_QUERY).fetchall() if name is not None
        ]

    ICON_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0

    with requests.Session() as session:
        versions_response = session.get(VERSIONS_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        versions_response.raise_for_status()
        versions = versions_response.json()
        if not isinstance(versions, list) or not versions or not isinstance(versions[0], str):
            raise ValueError("Data Dragon returned no usable version.")
        version = versions[0]

        champion_response = session.get(
            f"{CDN_URL}/{version}/data/en_US/champion.json",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        champion_response.raise_for_status()
        champion_payload = champion_response.json()
        if not isinstance(champion_payload, dict):
            raise ValueError("Data Dragon champion response is not an object.")

        mapping, unmapped = build_icon_mapping(stored_names, champion_payload)
        for stored_name in unmapped:
            print(f"Could not map champion: {stored_name}", file=sys.stderr)
        failed += len(unmapped)

        for stored_name, image_name in mapping.items():
            destination = ICON_DIR / f"{stored_name}.png"
            if destination.exists():
                skipped += 1
                continue

            temporary = destination.with_suffix(".tmp")
            try:
                response = session.get(
                    f"{CDN_URL}/{version}/img/champion/{quote(image_name, safe='')}",
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                temporary.write_bytes(response.content)
                temporary.rename(destination)
                downloaded += 1
            except (OSError, requests.RequestException) as exc:
                temporary.unlink(missing_ok=True)
                failed += 1
                print(f"Could not fetch champion {stored_name}: {exc}", file=sys.stderr)

    print(f"Data Dragon version: {version}")
    print(
        f"Champions: {len(stored_names)}; downloaded: {downloaded}; "
        f"skipped: {skipped}; failed: {failed}"
    )


if __name__ == "__main__":
    try:
        fetch_champion_icons()
    except (OSError, ValueError, duckdb.Error, requests.RequestException) as exc:
        raise SystemExit(f"Champion icon fetch failed: {exc}") from None
