from __future__ import annotations

import plotly.graph_objects as go
import pytest

from scripts.fetch_minimap import MAP_ASSET_BASE_URL
from src.mapping import add_position_marker, position_to_fraction


def test_base_positions_land_on_expected_minimap_corners() -> None:
    assert position_to_fraction(362, 135) == pytest.approx((0.02437710, 0.99090909))
    assert position_to_fraction(14321, 14673) == pytest.approx((0.96437710, 0.01191919))


def test_position_marker_uses_expected_minimap_fraction() -> None:
    figure = go.Figure()

    add_position_marker(figure, 362, 135, "#123456")

    marker = figure.data[0]
    assert marker.x == pytest.approx((0.02437710,))
    assert marker.y == pytest.approx((0.99090909,))
    assert marker.mode == "markers"
    assert marker.marker.color == "#123456"
    assert marker.marker.symbol == "circle"


@pytest.mark.parametrize(
    ("position_x", "position_y"),
    [(-1, 0), (14851, 0), (0, -1), (0, 14851)],
)
def test_out_of_bounds_position_raises(position_x: int, position_y: int) -> None:
    with pytest.raises(ValueError, match="outside map bounds"):
        position_to_fraction(position_x, position_y)


def test_minimap_source_url_uses_community_dragon() -> None:
    assert MAP_ASSET_BASE_URL.startswith("https://raw.communitydragon.org/")
    assert "ddragon.leagueoflegends.com" not in MAP_ASSET_BASE_URL
