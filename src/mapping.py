"""Summoner's Rift position mapping utilities."""

import plotly.graph_objects as go

POSITION_X_MIN = 0
POSITION_X_MAX = 14850
POSITION_Y_MIN = 0
POSITION_Y_MAX = 14850


def position_to_fraction(position_x: float, position_y: float) -> tuple[float, float]:
    """Convert a world position to top-left-origin minimap image fractions."""
    if not (
        POSITION_X_MIN <= position_x <= POSITION_X_MAX
        and POSITION_Y_MIN <= position_y <= POSITION_Y_MAX
    ):
        raise ValueError(
            f"position ({position_x}, {position_y}) is outside map bounds "
            f"x=[{POSITION_X_MIN}, {POSITION_X_MAX}], "
            f"y=[{POSITION_Y_MIN}, {POSITION_Y_MAX}]"
        )

    fraction_x = (position_x - POSITION_X_MIN) / (POSITION_X_MAX - POSITION_X_MIN)
    fraction_y = (POSITION_Y_MAX - position_y) / (POSITION_Y_MAX - POSITION_Y_MIN)
    return fraction_x, fraction_y


def add_position_marker(
    figure: go.Figure,
    position_x: float,
    position_y: float,
    color: str,
) -> None:
    """Add a filled circle marker at a world position on a minimap figure."""
    fraction_x, fraction_y = position_to_fraction(position_x, position_y)
    figure.add_scatter(
        x=[fraction_x],
        y=[fraction_y],
        mode="markers",
        marker={"color": color, "size": 8, "symbol": "circle"},
        hoverinfo="skip",
        showlegend=False,
    )
