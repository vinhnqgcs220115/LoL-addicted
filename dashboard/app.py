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
    0: "Cluster 0",
    1: "Cluster 1",
    2: "Cluster 2",
    3: "Cluster 3",
}
# TODO: assign names after reviewing notebooks/02_clustering.ipynb

DB_PATH = BASE_DIR / "data" / "lol_deploy.duckdb"
TIME_BUCKET_ORDER = ["morning", "afternoon", "evening", "night"]

st.set_page_config(
    page_title="LoL Ranked Analytics",
    layout="wide",
    page_icon="⚔️",
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
selected_champion = st.sidebar.selectbox(
    "Champion",
    ["All Champions", *champions],
)

overview_tab, champions_tab, patterns_tab = st.tabs(
    [" Overview", " Champions", " Patterns"]
)

with overview_tab:
    st.header("Overview")
    overview = _query_overview(conn, db_cache_key).iloc[0]
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

    st.subheader("Throw and Comeback Summary")
    throw_summary = _query_throw_summary(conn, db_cache_key).iloc[0]
    throws = int(throw_summary["throws"])
    total = int(throw_summary["total"])
    throw_count, comeback_count, throw_rate = st.columns(3)
    throw_count.metric("Throws", f"{throws:,}")
    comeback_count.metric("Comebacks", f"{int(throw_summary['comebacks']):,}")
    throw_rate.metric("Throw Rate", f"{throws / total if total else 0:.1%}")

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
                "opp_champion_name",
                "games",
                "our_winrate",
                "cs_diff",
                "our_avg_kda",
                "opp_avg_kda",
            ]
        ].copy()
        matchup_table["our_winrate"] = matchup_table["our_winrate"] * 100
        matchup_table = matchup_table.rename(
            columns={"our_winrate": "our_winrate (%)"}
        ).round(2)
        st.subheader("Matchups")
        st.dataframe(matchup_table, use_container_width=True)

        st.subheader("CS Advantage vs Win Rate")
        scatter = px.scatter(
            filtered_matchups,
            x="cs_diff",
            y="our_winrate",
            size="games",
            size_max=20,
            color="our_winrate",
            color_continuous_scale="RdBu_r",
            color_continuous_midpoint=0.5,
            hover_name="opp_champion_name",
            hover_data={
                "games": True,
                "our_winrate": ":.1%",
                "cs_diff": ":.2f",
            },
            labels={
                "cs_diff": "CS Advantage (our avg − opponent avg)",
                "our_winrate": "Win Rate",
            },
        )
        scatter.update_yaxes(tickformat=".0%")
        scatter.add_vline(x=0, line_dash="dash")
        scatter.add_hline(y=0.5, line_dash="dash")
        st.plotly_chart(scatter, use_container_width=True)

with patterns_tab:
    st.header("Patterns")
    cluster_summary = _query_clusters(conn, db_cache_key)
    cluster_summary["cluster_name"] = cluster_summary["cluster_id"].map(CLUSTER_NAMES)

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

    st.subheader("Cluster Feature Profile (z-scored per feature)")
    raw_centroids = cluster_summary.set_index("cluster_id")[FEATURE_COLS].astype(float)
    feature_std = raw_centroids.std(axis=0, ddof=0).replace(0, 1)
    normalized_centroids = (raw_centroids - raw_centroids.mean(axis=0)) / feature_std
    heatmap = go.Figure(
        data=go.Heatmap(
            z=normalized_centroids.to_numpy(),
            x=FEATURE_COLS,
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

    st.subheader("Death Context Breakdown")
    deaths = _query_deaths(conn, db_cache_key)
    if deaths.empty:
        st.info("No death data available.")
    else:
        st.caption(f"Total deaths: {len(deaths):,}")
        death_categories = {
            "Early Death": "is_early_death",
            "Overextension": "is_overextension_ahead",
            "Deficit Fight": "is_deficit_fight",
            "Tilt Spiral": "is_tilt_spiral",
            "Post-Laning Throw": "is_post_laning_throw",
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
