from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
MINIMAP_PATH = BASE_DIR / "assets" / "map" / "summoners_rift.png"
MAP_DIRECTORY_URL = (
    "https://raw.communitydragon.org/json/latest/game/assets/maps/info/map11/"
)
MAP_METADATA_URL = (
    "https://raw.communitydragon.org/latest/game/data/maps/shipping/map11/"
    "map11.bin.json"
)
MAP_ASSET_BASE_URL = (
    "https://raw.communitydragon.org/latest/game/assets/maps/info/map11/"
)
DEFAULT_SKIN_KEY = "Maps/Shipping/Map11/MapSkins/Default"
REQUEST_TIMEOUT_SECONDS = 30
MIN_IMAGE_DIMENSION = 64
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _get_200(
    session: requests.Session,
    url: str,
    label: str,
) -> requests.Response:
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise ValueError(f"{label} returned HTTP {response.status_code}; expected 200.")
    return response


def _get_json(session: requests.Session, url: str, label: str) -> Any:
    response = _get_200(session, url, label)
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError(f"{label} did not return valid JSON.") from exc


def _listed_files(payload: Any) -> list[str]:
    if not isinstance(payload, list):
        raise ValueError("CommunityDragon map11 directory listing has an unexpected format.")

    files: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise ValueError(
                "CommunityDragon map11 directory listing has an unexpected format."
            )
        name = entry.get("name")
        entry_type = entry.get("type")
        if not isinstance(name, str) or not isinstance(entry_type, str):
            raise ValueError(
                "CommunityDragon map11 directory listing has an unexpected format."
            )
        if entry_type == "file":
            files.append(name)

    if not files:
        raise ValueError("CommunityDragon map11 directory listing contains no files.")
    return files


def _default_minimap_filename(metadata: Any, listed_files: list[str]) -> str:
    try:
        texture_name = metadata[DEFAULT_SKIN_KEY]["mMinimapBackgroundConfig"][
            "mDefaultTextureName"
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "CommunityDragon map11 metadata has no default minimap texture."
        ) from exc

    if not isinstance(texture_name, str):
        raise ValueError("CommunityDragon map11 default minimap texture is not a string.")

    texture_path = PurePosixPath(texture_name)
    if texture_path.suffix.casefold() != ".tex":
        raise ValueError("CommunityDragon default minimap texture is not a .tex file.")

    expected_name = texture_path.with_suffix(".png").name
    matches = [
        filename
        for filename in listed_files
        if filename.casefold() == expected_name.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Default minimap {expected_name!r} was not found exactly once in the "
            "CommunityDragon map11 directory listing."
        )
    return matches[0]


def _png_dimensions(content: bytes) -> tuple[int, int]:
    if not content:
        raise ValueError("CommunityDragon minimap response was empty.")
    if (
        len(content) < 24
        or not content.startswith(PNG_SIGNATURE)
        or content[12:16] != b"IHDR"
    ):
        raise ValueError("CommunityDragon minimap response is not a valid PNG.")

    width = int.from_bytes(content[16:20], "big")
    height = int.from_bytes(content[20:24], "big")
    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        raise ValueError(
            f"CommunityDragon minimap dimensions are too small: {width}x{height}."
        )
    return width, height


def _atomic_replace(destination: Path, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(destination)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def fetch_minimap(destination: Path = MINIMAP_PATH) -> None:
    """Download and atomically replace the current default Summoner's Rift minimap."""
    with requests.Session() as session:
        listing = _get_json(
            session,
            MAP_DIRECTORY_URL,
            "CommunityDragon map11 directory listing",
        )
        listed_files = _listed_files(listing)
        metadata = _get_json(
            session,
            MAP_METADATA_URL,
            "CommunityDragon map11 metadata",
        )
        filename = _default_minimap_filename(metadata, listed_files)
        source_url = f"{MAP_ASSET_BASE_URL}{quote(filename, safe='')}"
        image_response = _get_200(
            session,
            source_url,
            "CommunityDragon minimap image",
        )

        content_type = image_response.headers.get("Content-Type", "")
        if content_type.partition(";")[0].strip().casefold() != "image/png":
            raise ValueError(
                f"CommunityDragon minimap returned Content-Type {content_type!r}; "
                "expected image/png."
            )
        content = image_response.content
        if not isinstance(content, bytes):
            raise ValueError("CommunityDragon minimap response was not binary content.")
        width, height = _png_dimensions(content)

    _atomic_replace(destination, content)
    print(f"Selected URL: {source_url}")
    print(f"Byte count: {len(content)}")
    print(f"Dimensions: {width}x{height}")
    print(f"SHA-256: {sha256(content).hexdigest()}")


if __name__ == "__main__":
    try:
        fetch_minimap()
    except (OSError, ValueError, requests.RequestException) as exc:
        raise SystemExit(f"Minimap fetch failed: {exc}") from None
