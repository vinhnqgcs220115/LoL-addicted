import base64
import html
import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.features import (  # noqa: E402
    ANALYSIS_ROLE,
    CURRENT_SEASON_START,
    champion_matchup_stats,
    death_context,
)
from src.models import (  # noqa: E402
    FEATURE_COLS,
    query_cluster_summary,
    query_gold_trajectories,
)

CLUSTER_NAMES: dict[int, str] = {
    0: "Behind & Spiraling",
    1: "Ahead but Overextending",
    2: "Clean Games",
    3: "Cluster 3 (insufficient data)",
}
CLUSTER_DESCRIPTIONS: dict[str, str] = {
    "Behind & Spiraling": "falling behind early and struggling to recover",
    "Ahead but Overextending": (
        "building a lead, then taking risks that put it back in play"
    ),
    "Clean Games": "efficient, with few compounding mistakes",
}
CLUSTER_CARD_STATS: dict[str, tuple[tuple[str, str, bool], ...]] = {
    "Behind & Spiraling": (
        ("gold_delta", "Gold delta vs personal baseline", True),
        ("tilt_spiral_ratio", "Repeat-death streak", True),
    ),
    "Ahead but Overextending": (
        ("gold_delta", "Gold delta vs personal baseline", True),
        ("deaths_while_ahead", "Deaths while ahead", True),
    ),
    "Clean Games": (
        ("total_deaths", "Total deaths", False),
        ("tilt_spiral_ratio", "Repeat-death streak", True),
    ),
}

DB_PATH = BASE_DIR / "data" / "lol_deploy.duckdb"
CHAMPION_ICON_DIR = BASE_DIR / "assets" / "champion_icons"
CHAMPION_ICONS = {
    path.stem: path for path in CHAMPION_ICON_DIR.glob("*.png") if path.is_file()
}
WIN_RATE_CLEAR_MAJORITY = 0.55
WIN_RATE_CLEAR_MINORITY = 0.45
TIME_BUCKET_ORDER = ["morning", "afternoon", "evening", "night"]
PROXY_LABEL_NOTE = (
    "Proxy labels use single-player timeline data; they are not confirmed "
    "team-state gameplay events."
)
FEATURE_DISPLAY_NAMES = {
    "gold_delta": "Gold delta vs personal baseline",
    "total_deaths": "Total deaths",
    "deaths_while_ahead": "Deaths while ahead (proxy)",
    "tilt_spiral_ratio": "Close-repeat death share (proxy)",
    "max_death_streak": "Max close-repeat death streak (proxy)",
    "total_roams": "Detected roams (proxy)",
    "avg_cs_sacrifice": "Avg CS sacrifice (roam proxy)",
    "roam_impact_rate": "Kill impact rate (roam proxy)",
    "tilt_index": "Recent win rate (tilt proxy)",
}
MATCHUP_TABLE_CSS = """
.matchup-table-wrap {
    max-height: 420px;
    overflow: auto;
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-radius: 0.5rem;
}
.matchup-table {
    width: 100%;
    border-collapse: collapse;
}
.matchup-table th,
.matchup-table td {
    padding: 0.45rem 0.6rem;
    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    vertical-align: middle;
    white-space: nowrap;
}
.matchup-table th {
    position: sticky;
    top: 0;
    z-index: 1;
    background: var(--background-color, white);
    text-align: left;
}
.matchup-table th:nth-child(n+3),
.matchup-table td:nth-child(n+3) {
    text-align: right;
}
.matchup-champion {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}
.matchup-champion img {
    width: 28px;
    height: 28px;
    border-radius: 4px;
}
.matchup-win-rate {
    display: inline-block;
    min-width: 4.25rem;
    padding: 0.15rem 0.45rem;
    border: 1px solid;
    border-radius: 999px;
    text-align: center;
    font-weight: 600;
}
.matchup-win-rate-majority {
    background: rgba(34, 197, 94, 0.2);
    border-color: rgba(34, 197, 94, 0.6);
}
.matchup-win-rate-minority {
    background: rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.6);
}
.matchup-win-rate-neutral {
    background: rgba(107, 114, 128, 0.2);
    border-color: rgba(107, 114, 128, 0.6);
}
"""
CLUSTER_CARD_CSS = """
.cluster-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin: 0.5rem 0 1.25rem;
}
.cluster-card {
    padding: 1rem;
    border: 1px solid rgba(128, 128, 128, 0.28);
    border-radius: 0.75rem;
    background: rgba(128, 128, 128, 0.04);
}
.cluster-card h3 {
    margin: 0 0 0.25rem;
    font-size: 1.05rem;
}
.cluster-card-size {
    font-size: 0.85rem;
    opacity: 0.7;
}
.cluster-card-description {
    min-height: 3rem;
    margin: 0.75rem 0 1rem;
}
.cluster-stat + .cluster-stat {
    margin-top: 0.85rem;
}
.cluster-stat-heading {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.3rem;
    font-size: 0.8rem;
}
.cluster-stat-heading strong {
    white-space: nowrap;
}
.cluster-stat-track {
    height: 0.45rem;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(128, 128, 128, 0.2);
}
.cluster-stat-fill {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: var(--primary-color, #4f46e5);
}
.cluster-stat-fill-negative {
    margin-left: auto;
    background: #ef4444;
}
.cluster-card-insufficient {
    border-style: dashed;
    background: rgba(128, 128, 128, 0.07);
}
.cluster-card-insufficient p {
    opacity: 0.7;
}
"""

st.set_page_config(
    page_title="LoL Ranked Analytics",
    layout="wide",
    page_icon="⚔️",
)


@st.cache_data
def _champion_icon_uri(champion_name: str) -> str | None:
    icon_path = CHAMPION_ICONS.get(champion_name)
    if icon_path is None:
        return None
    encoded_icon = base64.b64encode(icon_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_icon}"


def _champion_cell(champion_name: str) -> str:
    icon_uri = _champion_icon_uri(champion_name)
    icon = (
        f'<img src="{icon_uri}" width="28" height="28" alt="" loading="lazy">'
        if icon_uri
        else ""
    )
    return f'<span class="matchup-champion">{icon}{html.escape(champion_name)}</span>'


def _win_rate_chip(win_rate: float) -> str:
    if win_rate >= WIN_RATE_CLEAR_MAJORITY:
        tone = "majority"
    elif win_rate <= WIN_RATE_CLEAR_MINORITY:
        tone = "minority"
    else:
        tone = "neutral"
    return (
        f'<span class="matchup-win-rate matchup-win-rate-{tone}">'
        f"{win_rate:.1%}</span>"
    )


def _cluster_cards(cluster_summary: pd.DataFrame) -> str:
    cards = []
    for cluster in cluster_summary.itertuples(index=False):
        cluster_name = str(cluster.cluster_name)
        size = int(cluster.size)
        stats = CLUSTER_CARD_STATS.get(cluster_name)
        if stats is None:
            cards.append(
                '<article class="cluster-card cluster-card-insufficient">'
                f"<h3>{html.escape(cluster_name)}</h3>"
                f"<p>Not enough data yet &mdash; {size:,} games, "
                "too few to characterize.</p></article>"
            )
            continue

        stat_rows = []
        for feature, label, is_proxy in stats:
            feature_max = float(cluster_summary[feature].max())
            relative_pct = float(getattr(cluster, feature)) / feature_max * 100
            bar_width = min(abs(relative_pct), 100.0)
            negative_class = (
                " cluster-stat-fill-negative" if relative_pct < 0 else ""
            )
            percent_label = f"{abs(relative_pct):.1f}% of max"
            if relative_pct < 0:
                percent_label = f"&minus;{percent_label}"
            proxy_marker = "&asymp; " if is_proxy else ""
            stat_rows.append(
                '<div class="cluster-stat">'
                '<div class="cluster-stat-heading">'
                f"<span>{proxy_marker}{html.escape(label)}</span>"
                f"<strong>{percent_label}</strong></div>"
                '<div class="cluster-stat-track" aria-hidden="true">'
                f'<span class="cluster-stat-fill{negative_class}" '
                f'style="width:{bar_width:.1f}%"></span></div></div>'
            )

        cards.append(
            '<article class="cluster-card">'
            f"<h3>{html.escape(cluster_name)}</h3>"
            f'<div class="cluster-card-size">{size:,} games</div>'
            '<p class="cluster-card-description">'
            f"{html.escape(CLUSTER_DESCRIPTIONS[cluster_name])}.</p>"
            f"{''.join(stat_rows)}</article>"
        )

    return (
        f"<style>{CLUSTER_CARD_CSS}</style>"
        f'<div class="cluster-card-grid">{"".join(cards)}</div>'
    )


@st.cache_resource
def _get_connection(db_cache_key: tuple[int, int]) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


def _db_cache_key() -> tuple[int, int]:
    stat = DB_PATH.stat()
    return stat.st_mtime_ns, stat.st_size


@st.cache_data
def _query_overview(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return _conn.execute(
        """
        SELECT
            COUNT(*)::INTEGER AS total_games,
            AVG(win::INTEGER)::DOUBLE AS win_rate,
            AVG(kda)::DOUBLE AS avg_kda,
            AVG(cs_per_min)::DOUBLE AS avg_cs_per_min
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
        """,
        [CURRENT_SEASON_START, ANALYSIS_ROLE],
    ).df()


@st.cache_data
def _query_patch_stats(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return _conn.execute(
        """
        SELECT
            game_version,
            COUNT(*)::INTEGER AS games,
            AVG(win::INTEGER)::DOUBLE AS win_rate
        FROM matches
        WHERE game_datetime >= ? AND team_position = ?
        GROUP BY game_version
        ORDER BY
            TRY_CAST(SPLIT_PART(game_version, '.', 1) AS INTEGER),
            TRY_CAST(SPLIT_PART(game_version, '.', 2) AS INTEGER)
        """,
        [CURRENT_SEASON_START, ANALYSIS_ROLE],
    ).df()


@st.cache_data
def _query_time_stats(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return _conn.execute("""
        SELECT
            time_bucket,
            COUNT(*)::INTEGER AS games,
            AVG(win::INTEGER)::DOUBLE AS win_rate
        FROM feature_matrix
        GROUP BY time_bucket
    """).df()


@st.cache_data
def _query_throw_summary(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return _conn.execute("""
        SELECT
            COALESCE(SUM(is_throw::INTEGER), 0)::INTEGER AS throws,
            COALESCE(SUM(is_comeback::INTEGER), 0)::INTEGER AS comebacks,
            COUNT(*)::INTEGER AS total
        FROM feature_matrix
    """).df()


@st.cache_data
def _query_matchups(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return champion_matchup_stats(_conn)


@st.cache_data
def _query_clusters(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return query_cluster_summary(_conn)


@st.cache_data
def _query_trajectories(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return query_gold_trajectories(_conn)


@st.cache_data
def _query_deaths(
    _conn: duckdb.DuckDBPyConnection, db_cache_key: tuple[int, int]
) -> pd.DataFrame:
    return death_context(_conn)


db_cache_key = _db_cache_key()
conn = _get_connection(db_cache_key)
matchups = _query_matchups(conn, db_cache_key)

st.sidebar.title("LoL Ranked Analytics")
st.sidebar.caption(
    f"All data is Season 16 mid-lane only ({ANALYSIS_ROLE}, >= {CURRENT_SEASON_START})."
)
champions = sorted(matchups["champion_name"].dropna().unique().tolist())
st.sidebar.markdown("**Champion**")
champion_filter, selected_icon = st.sidebar.columns([5, 1])
selected_champion = champion_filter.selectbox(
    "Champion",
    ["All Champions", *champions],
    label_visibility="collapsed",
)
if selected_champion != "All Champions":
    selected_icon_path = CHAMPION_ICONS.get(selected_champion)
    if selected_icon_path is not None:
        selected_icon.image(str(selected_icon_path), width=28)
cluster_summary = _query_clusters(conn, db_cache_key)
cluster_summary["cluster_name"] = cluster_summary["cluster_id"].map(CLUSTER_NAMES)

overview_tab, champions_tab, patterns_tab = st.tabs(
    [" Overview", " Champions", " Patterns"]
)

with overview_tab:
    st.header("Overview")
    overview = _query_overview(conn, db_cache_key).iloc[0]
    dominant_cluster = cluster_summary.loc[cluster_summary["size"].idxmax()]
    cluster_name = str(dominant_cluster["cluster_name"])
    dominant_pct = dominant_cluster["size"] / cluster_summary["size"].sum()
    description = CLUSTER_DESCRIPTIONS.get(
        cluster_name, "not enough data exists to describe this pattern reliably"
    )
    st.info(
        f"You've played {int(overview['total_games']):,} ranked mid games this season "
        f"and won {float(overview['win_rate']):.1%} of them. Most of your games \u2014 "
        f"{dominant_pct:.1%} \u2014 fall into the '{cluster_name}' pattern: {description}."
    )
    total_games, win_rate, avg_kda, avg_cs = st.columns(4)
    total_games.metric("Total Games", f"{int(overview['total_games']):,}")
    win_rate.metric("Win Rate", f"{float(overview['win_rate']):.1%}")
    avg_kda.metric("Avg KDA", f"{float(overview['avg_kda']):.2f}")
    avg_cs.metric("Avg CS/min", f"{float(overview['avg_cs_per_min']):.1f}")

    st.subheader("Win Rate by Patch")
    patch_stats = _query_patch_stats(conn, db_cache_key)
    patch_figure = px.bar(
        patch_stats,
        x="win_rate",
        y="game_version",
        orientation="h",
        custom_data=["games"],
        labels={"win_rate": "Win Rate", "game_version": "Patch"},
    )
    patch_figure.update_traces(
        hovertemplate=(
            "Patch %{y}<br>Win Rate %{x:.1%}<br>Games %{customdata[0]}<extra></extra>"
        )
    )
    patch_figure.update_xaxes(tickformat=".0%", range=[0, 1])
    patch_figure.update_yaxes(
        type="category",
        categoryorder="array",
        categoryarray=patch_stats["game_version"].tolist(),
    )
    st.plotly_chart(patch_figure, use_container_width=True)

    st.subheader("Performance by Time of Day")
    time_stats = _query_time_stats(conn, db_cache_key)
    count_column, rate_column = st.columns(2)
    with count_column:
        count_figure = px.bar(
            time_stats,
            x="time_bucket",
            y="games",
            category_orders={"time_bucket": TIME_BUCKET_ORDER},
            labels={"time_bucket": "Time of Day", "games": "Games"},
        )
        st.plotly_chart(count_figure, use_container_width=True)
    with rate_column:
        rate_figure = px.bar(
            time_stats,
            x="time_bucket",
            y="win_rate",
            category_orders={"time_bucket": TIME_BUCKET_ORDER},
            labels={"time_bucket": "Time of Day", "win_rate": "Win Rate"},
        )
        rate_figure.update_yaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(rate_figure, use_container_width=True)

    st.subheader("Estimated Throw and Comeback Summary")
    st.caption(PROXY_LABEL_NOTE)
    throw_summary = _query_throw_summary(conn, db_cache_key).iloc[0]
    throws = int(throw_summary["throws"])
    total = int(throw_summary["total"])
    throw_count, comeback_count, throw_rate = st.columns(3)
    throw_count.metric("Estimated Throws", f"{throws:,}")
    comeback_count.metric(
        "Estimated Comebacks", f"{int(throw_summary['comebacks']):,}"
    )
    throw_rate.metric("Estimated Throw Rate", f"{throws / total if total else 0:.1%}")

with champions_tab:
    st.header("Champions")
    if matchups.empty:
        st.info("Opponent data is unavailable for the current analysis scope.")
    else:
        filtered_matchups = matchups
        if selected_champion != "All Champions":
            filtered_matchups = matchups[matchups["champion_name"] == selected_champion]

        matchup_table = filtered_matchups[
            [
                "champion_name",
                "opp_champion_name",
                "games",
                "our_winrate",
                "cs_diff",
                "our_avg_kda",
                "opp_avg_kda",
            ]
        ].rename(
            columns={
                "champion_name": "Your Champion",
                "opp_champion_name": "Opponent",
                "games": "Games",
                "our_winrate": "Win Rate",
                "cs_diff": "CS Diff",
                "our_avg_kda": "Your Avg KDA",
                "opp_avg_kda": "Opponent Avg KDA",
            }
        )
        st.subheader("Matchups")
        st.caption(
            "Win-rate chips: green at 55% or higher, red at 45% or lower, "
            "and gray between them."
        )
        matchup_html = matchup_table.to_html(
            index=False,
            border=0,
            escape=False,
            classes="matchup-table",
            formatters={
                "Your Champion": _champion_cell,
                "Opponent": _champion_cell,
                "Games": "{:,.0f}".format,
                "Win Rate": _win_rate_chip,
                "CS Diff": "{:.2f}".format,
                "Your Avg KDA": "{:.2f}".format,
                "Opponent Avg KDA": "{:.2f}".format,
            },
        )
        st.html(
            f"<style>{MATCHUP_TABLE_CSS}</style>"
            f'<div class="matchup-table-wrap">{matchup_html}</div>',
        )

        st.subheader("CS Advantage vs Win Rate")
        scatter = px.scatter(
            filtered_matchups,
            x="cs_diff",
            y="our_winrate",
            size="games",
            size_max=20,
            color="games",
            color_continuous_scale="Blues",
            hover_name="opp_champion_name",
            hover_data={
                "games": True,
                "our_winrate": ":.1%",
                "cs_diff": ":.2f",
            },
            labels={
                "cs_diff": "CS Advantage (our avg − opponent avg)",
                "our_winrate": "Win Rate",
                "games": "Games Played",
            },
        )
        scatter.update_yaxes(tickformat=".0%")
        scatter.add_vline(x=0, line_dash="dash")
        scatter.add_hline(y=0.5, line_dash="dash")
        st.plotly_chart(scatter, use_container_width=True)

with patterns_tab:
    st.header("Patterns")

    st.subheader("Cluster Distribution")
    distribution = px.bar(
        cluster_summary,
        x="cluster_name",
        y="size",
        text="size",
        labels={"cluster_name": "Cluster", "size": "Games"},
    )
    distribution.update_traces(textposition="outside")
    st.plotly_chart(distribution, use_container_width=True)

    st.html(_cluster_cards(cluster_summary))

    with st.expander("View full statistical breakdown", expanded=False):
        st.subheader("Cluster Feature Profile (z-scored per feature)")
        st.caption(PROXY_LABEL_NOTE)
        raw_centroids = cluster_summary.set_index("cluster_id")[FEATURE_COLS].astype(float)
        feature_std = raw_centroids.std(axis=0, ddof=0).replace(0, 1)
        normalized_centroids = (raw_centroids - raw_centroids.mean(axis=0)) / feature_std
        heatmap = go.Figure(
            data=go.Heatmap(
                z=normalized_centroids.to_numpy(),
                x=[FEATURE_DISPLAY_NAMES.get(feature, feature) for feature in FEATURE_COLS],
                y=[CLUSTER_NAMES[int(cluster_id)] for cluster_id in raw_centroids.index],
                text=raw_centroids.to_numpy(),
                texttemplate="%{text:.2f}",
                colorscale="RdBu_r",
                colorbar={"title": "z-score"},
            )
        )
        heatmap.update_layout(title="Cluster Feature Profile (z-scored per feature)")
        st.plotly_chart(heatmap, use_container_width=True)

    st.subheader("Average Gold Trajectory by Cluster")
    trajectories = _query_trajectories(conn, db_cache_key)
    trajectories["cluster_name"] = trajectories["cluster_id"].map(CLUSTER_NAMES)
    trajectory_figure = px.line(
        trajectories,
        x="timestamp_min",
        y="avg_gold",
        color="cluster_name",
        labels={
            "timestamp_min": "Game Minute",
            "avg_gold": "Average Total Gold",
            "cluster_name": "Cluster",
        },
    )
    st.plotly_chart(trajectory_figure, use_container_width=True)
    present_clusters = set(trajectories["cluster_id"].astype(int))
    missing_clusters = [
        name for cluster_id, name in CLUSTER_NAMES.items() if cluster_id not in present_clusters
    ]
    if missing_clusters:
        st.caption(
            f"{', '.join(missing_clusters)} excluded due to insufficient sample size per minute."
        )

    st.subheader("Estimated Death Context Breakdown")
    st.caption(PROXY_LABEL_NOTE)
    deaths = _query_deaths(conn, db_cache_key)
    if deaths.empty:
        st.info("No death data available.")
    else:
        st.caption(f"Total deaths: {len(deaths):,}")
        death_categories = {
            "Early Death": "is_early_death",
            "Overextension (proxy)": "is_overextension_ahead",
            "Deficit Fight (proxy)": "is_deficit_fight",
            "Tilt Spiral": "is_tilt_spiral",
            "Post-Laning Throw (proxy)": "is_post_laning_throw",
        }
        death_counts = pd.DataFrame(
            {
                "category": death_categories.keys(),
                "deaths": [int(deaths[column].sum()) for column in death_categories.values()],
            }
        )
        death_figure = px.bar(
            death_counts,
            x="deaths",
            y="category",
            orientation="h",
            text="deaths",
            labels={"deaths": "Deaths", "category": "Context"},
        )
        death_figure.update_yaxes(
            categoryorder="array",
            categoryarray=list(reversed(death_categories)),
        )
        st.plotly_chart(death_figure, use_container_width=True)
