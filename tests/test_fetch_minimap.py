from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import struct
from typing import Any
import zlib

import pytest
import requests

import scripts.fetch_minimap as minimap


class DummyResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: Any = None,
        content: bytes = b"",
        content_type: str = "application/json",
        json_error: ValueError | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.headers = {"Content-Type": content_type}
        self._json_error = json_error

    def json(self) -> Any:
        if self._json_error is not None:
            raise self._json_error
        return self._payload


class DummySession:
    def __init__(self, responses: list[DummyResponse | Exception]) -> None:
        self.responses = responses
        self.urls: list[str] = []

    def __enter__(self) -> DummySession:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def get(self, url: str, *, timeout: int) -> DummyResponse:
        assert timeout == minimap.REQUEST_TIMEOUT_SECONDS
        self.urls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data)
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)


def _png(width: int = 64, height: int = 64) -> bytes:
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = b"\x00" + (b"\x00\x00\x00\xff" * width)
    pixels = zlib.compress(row * height)
    return (
        minimap.PNG_SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", pixels)
        + _chunk(b"IEND", b"")
    )


def _listing(filename: str) -> list[dict[str, Any]]:
    return [
        {"name": "decoy_base_baron1.png", "type": "file", "size": 1},
        {"name": filename, "type": "file", "size": 2},
    ]


def _metadata(texture_name: str) -> dict[str, Any]:
    return {
        minimap.DEFAULT_SKIN_KEY: {
            "mMinimapBackgroundConfig": {"mDefaultTextureName": texture_name}
        }
    }


def _mock_session(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[DummyResponse | Exception],
) -> DummySession:
    session = DummySession(responses)
    monkeypatch.setattr(minimap.requests, "Session", lambda: session)
    return session


@pytest.mark.parametrize(
    "listing_response",
    [
        DummyResponse(status_code=503),
        DummyResponse(json_error=ValueError("invalid JSON")),
        DummyResponse(payload={"name": "not-a-list"}),
    ],
)
def test_bad_directory_listing_stops_immediately(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    listing_response: DummyResponse,
) -> None:
    session = _mock_session(monkeypatch, [listing_response])

    with pytest.raises(ValueError, match="directory listing"):
        minimap.fetch_minimap(tmp_path / "summoners_rift.png")

    assert session.urls == [minimap.MAP_DIRECTORY_URL]


def test_metadata_selects_case_insensitive_listed_filename(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    filename = "Unexpected Default.PNG"
    image = _png()
    session = _mock_session(
        monkeypatch,
        [
            DummyResponse(payload=_listing(filename)),
            DummyResponse(
                payload=_metadata("ASSETS/Maps/Info/Map11/unexpected default.TeX")
            ),
            DummyResponse(content=image, content_type="image/png"),
        ],
    )
    destination = tmp_path / "summoners_rift.png"
    destination.write_bytes(b"old image")

    minimap.fetch_minimap(destination)

    selected_url = f"{minimap.MAP_ASSET_BASE_URL}Unexpected%20Default.PNG"
    assert session.urls == [
        minimap.MAP_DIRECTORY_URL,
        minimap.MAP_METADATA_URL,
        selected_url,
    ]
    assert destination.read_bytes() == image
    assert not destination.with_suffix(".tmp").exists()
    assert capsys.readouterr().out.splitlines() == [
        f"Selected URL: {selected_url}",
        f"Byte count: {len(image)}",
        "Dimensions: 64x64",
        f"SHA-256: {sha256(image).hexdigest()}",
    ]


def test_non_image_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    filename = "selected.png"
    _mock_session(
        monkeypatch,
        [
            DummyResponse(payload=_listing(filename)),
            DummyResponse(payload=_metadata("selected.tex")),
            DummyResponse(content=b"<html>error</html>", content_type="text/html"),
        ],
    )
    destination = tmp_path / "summoners_rift.png"

    with pytest.raises(ValueError, match="Content-Type"):
        minimap.fetch_minimap(destination)

    assert not destination.exists()
    assert not destination.with_suffix(".tmp").exists()


def test_failed_download_leaves_existing_asset_untouched(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    filename = "selected.png"
    _mock_session(
        monkeypatch,
        [
            DummyResponse(payload=_listing(filename)),
            DummyResponse(payload=_metadata("selected.tex")),
            requests.ConnectionError("network failure"),
        ],
    )
    destination = tmp_path / "summoners_rift.png"
    destination.write_bytes(b"existing asset")

    with pytest.raises(requests.ConnectionError, match="network failure"):
        minimap.fetch_minimap(destination)

    assert destination.read_bytes() == b"existing asset"
    assert not destination.with_suffix(".tmp").exists()
