"""Balatro ML — Training Monitor (DASH-03).

A local, single-user, read-only Streamlit dashboard for monitoring RL training.
The full visual/interaction contract is LOCKED by 03-UI-SPEC.md — this module
implements it verbatim:

  * Wide layout, header + freshness caption, st.divider() section breaks.
  * Panel 7 KPI strip (st.metric x4) + a 4-tab body (Scores / Breakdown /
    Synergies / Best run) holding the other 6 panels (Plotly).
  * One @st.fragment(run_every="30s") wraps the KPI strip + tabs so only the
    data region re-runs each tick. Each query wrapper is @st.cache_data(ttl=30).
  * Dark theme (.streamlit/config.toml) + Balatro Gold #F0A500 accent reserved
    for score-bearing marks. Panel 1 uses log X, Panel 2 log Y.
  * Empty / partial / error states per the States Contract — never a blank chart,
    never a whole-page crash.

Reads go ONLY through src/dashboard/db.py's parameterized read-only query
methods (no SQL is built here — threats T-03-07/T-03-08). The DB path is
db.DB_PATH (data/runs.db); BML_DB_PATH overrides it for offline tests.
"""

from __future__ import annotations

import datetime as _dt
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import db
from src.dashboard.format import fmt_si

ACCENT = "#F0A500"
BG = "#0E1117"
CHART_MARGIN = dict(t=40, r=16, b=40, l=56)


def _si_log_ticks(values) -> tuple[list[float], list[str]]:
    """SI tick positions + labels spanning a series, for a log axis.

    Returns decade tick values (powers of 10 covering the data range) and their
    fmt_si labels (e.g. 1K, 10K, 100K) so log axes read in SI, not raw ints.
    """
    import math

    vals = [v for v in values if v is not None and v > 0]
    if not vals:
        return [], []
    lo = math.floor(math.log10(min(vals)))
    hi = math.ceil(math.log10(max(vals)))
    ticks = [10**p for p in range(lo, hi + 1)]
    return ticks, [fmt_si(t) for t in ticks]

EMPTY_HEADING = "No training data yet"
EMPTY_BODY = (
    "Run `uv run python scripts/seed_dashboard.py` to seed the database with 50 "
    "random-agent games, then this dashboard will populate automatically."
)
EMPTY_BEST_RUN = (
    "No completed runs yet — the best-run breakdown appears once at least one "
    "game finishes."
)
ERROR_COPY = (
    "Couldn't read the metrics database at data/runs.db. Confirm the seed script "
    "has run and the schema matches src/dashboard/db.py, then refresh."
)


def _db_path() -> str:
    """Resolve the DB path (BML_DB_PATH override -> db.DB_PATH default)."""
    return os.environ.get("BML_DB_PATH") or db.DB_PATH


def _db_exists(path: str) -> bool:
    """True only when the DB file is actually on disk (read-only open needs it)."""
    return os.path.exists(path)


# Auto-refresh cadence. Production: the locked 30s timer (UI-SPEC § Interaction).
# Offline tests set BML_DISABLE_AUTOREFRESH=1 so AppTest does not spawn the
# recurring fragment thread (which races with test teardown); the fragment
# itself is unchanged.
_RUN_EVERY = None if os.environ.get("BML_DISABLE_AUTOREFRESH") == "1" else "30s"


# ---------------------------------------------------------------------------
# Cached read wrappers — one per panel, each opens a read-only connection and
# closes it. @st.cache_data(ttl=30) keys on the resolved path so a refresh
# re-reads SQLite at most once per interval, never per panel.
# ---------------------------------------------------------------------------


def _read(fn, path: str):
    conn = db.connect(path, read_only=True)
    try:
        return fn(conn)
    finally:
        conn.close()


@st.cache_data(ttl=30)
def load_runs(path: str) -> pd.DataFrame:
    return _read(db.get_all_runs, path)


@st.cache_data(ttl=30)
def load_deck_stake(path: str) -> pd.DataFrame:
    return _read(db.get_deck_stake_stats, path)


@st.cache_data(ttl=30)
def load_hand_types(path: str) -> pd.DataFrame:
    return _read(db.get_hand_type_counts, path)


@st.cache_data(ttl=30)
def load_cooccurrence(path: str) -> pd.DataFrame:
    return _read(db.get_joker_cooccurrence, path)


@st.cache_data(ttl=30)
def load_throughput(path: str) -> dict:
    return _read(db.get_throughput, path)


@st.cache_data(ttl=30)
def load_best_run(path: str):
    # Tuple (dict|None, DataFrame) — cache_data handles the tuple fine.
    return _read(db.get_best_run, path)


# ---------------------------------------------------------------------------
# Panels (filled in Task 2). Each returns early with a per-panel st.info when
# its data is empty so we never render a blank chart (partial-state contract).
# ---------------------------------------------------------------------------


def panel_kpis(path: str) -> None:
    """Panel 7: throughput KPI strip (st.metric x4)."""
    try:
        tp = load_throughput(path)
    except Exception:
        tp = {"games": 0, "win_rate": None, "best_score": None, "games_per_hr": None}

    games = tp.get("games") or 0
    cols = st.columns(4, gap="medium")

    if not games:
        for col, label in zip(
            cols, ("Games/hr", "Total games", "Win rate", "Best score")
        ):
            col.metric(label, "—")
        return

    gph = tp.get("games_per_hr")
    win_rate = tp.get("win_rate")
    best = tp.get("best_score")

    cols[0].metric("Games/hr", f"{int(round(gph)):,}" if gph else "—")
    cols[1].metric("Total games", f"{games:,}")
    cols[2].metric(
        "Win rate", f"{win_rate * 100:.1f}%" if win_rate is not None else "—"
    )
    cols[3].metric("Best score", fmt_si(best))


def panel_histogram(path: str) -> None:
    """Panel 1: score-distribution histogram, log X, accent bars."""
    df = load_runs(path)
    df = df.dropna(subset=["final_score"]) if not df.empty else df
    st.subheader("Score distribution")
    if df.empty:
        st.info(EMPTY_HEADING)
        return
    fig = px.histogram(
        df,
        x="final_score",
        log_x=True,
        color_discrete_sequence=[ACCENT],
    )
    fig.update_layout(
        margin=CHART_MARGIN,
        title=dict(text="Final score distribution", font=dict(size=16)),
        font=dict(size=13),
    )
    ticks, labels = _si_log_ticks(df["final_score"])
    fig.update_xaxes(
        title_text="Final score (log scale)", tickvals=ticks, ticktext=labels
    )
    fig.update_yaxes(title_text="Runs")
    st.plotly_chart(fig, use_container_width=True)


def panel_learning_curve(path: str) -> None:
    """Panel 2: learning curve — faint raw points + bold accent rolling mean, log Y."""
    df = load_runs(path)
    df = df.dropna(subset=["final_score"]) if not df.empty else df
    st.subheader("Learning curve")
    if df.empty:
        st.info(EMPTY_HEADING)
        return
    df = df.reset_index(drop=True)
    df["game"] = range(1, len(df) + 1)
    window = max(1, min(20, len(df) // 5 or 1))
    df["rolling"] = df["final_score"].rolling(window, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["game"],
            y=df["final_score"],
            mode="markers",
            name="Run score",
            marker=dict(color="rgba(200,200,200,0.35)", size=5),
            hovertemplate="Game %{x}<br>Score %{y:,}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["game"],
            y=df["rolling"],
            mode="lines",
            name=f"Rolling mean ({window})",
            line=dict(color=ACCENT, width=3),
            hovertemplate="Game %{x}<br>Mean %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        margin=CHART_MARGIN,
        title=dict(text="Score over games", font=dict(size=16)),
        font=dict(size=13),
    )
    ticks, labels = _si_log_ticks(df["final_score"])
    fig.update_xaxes(title_text="Game")
    fig.update_yaxes(
        type="log", title_text="Score (log scale)", tickvals=ticks, ticktext=labels
    )
    st.plotly_chart(fig, use_container_width=True)


def panel_deck_stake(path: str) -> None:
    """Panel 3: per-deck & per-stake mean score, colored by stake (1->8)."""
    df = load_deck_stake(path)
    st.subheader("Per-deck & per-stake performance")
    if df.empty:
        st.info(EMPTY_HEADING)
        return
    df = df.copy()
    df["stake"] = df["stake"].astype(int)
    fig = px.bar(
        df,
        x="deck",
        y="avg_score",
        color="stake",
        barmode="group",
        color_continuous_scale="Cividis",
        range_color=[1, 8],
        hover_data={"n": True, "avg_score": ":,.0f"},
    )
    fig.update_layout(
        margin=CHART_MARGIN,
        title=dict(text="Mean score by deck & stake", font=dict(size=16)),
        font=dict(size=13),
        coloraxis_colorbar=dict(title="Stake"),
    )
    fig.update_xaxes(title_text="Deck")
    fig.update_yaxes(title_text="Mean final score")
    st.plotly_chart(fig, use_container_width=True)


def panel_hand_types(path: str) -> None:
    """Panel 6: hand-type usage frequency, horizontal bars sorted desc, accent."""
    df = load_hand_types(path)
    st.subheader("Hand-type usage frequency")
    if df.empty:
        st.info(EMPTY_HEADING)
        return
    df = df.sort_values("n", ascending=True)  # ascending so largest is on top
    fig = px.bar(
        df,
        x="n",
        y="hand_type",
        orientation="h",
        color_discrete_sequence=[ACCENT],
    )
    fig.update_layout(
        margin=CHART_MARGIN,
        title=dict(text="Hands played by type", font=dict(size=16)),
        font=dict(size=13),
    )
    fig.update_xaxes(title_text="Count")
    fig.update_yaxes(title_text="Hand type")
    st.plotly_chart(fig, use_container_width=True)


def panel_heatmap(path: str) -> None:
    """Panel 4: joker-synergy co-occurrence heatmap (dark -> #F0A500)."""
    df = load_cooccurrence(path)
    st.subheader("Joker synergies")
    if df.empty:
        st.info(EMPTY_HEADING)
        return
    # Pivot the j1<j2 long form into a square symmetric matrix.
    jokers = sorted(set(df["j1"]).union(set(df["j2"])))
    matrix = pd.DataFrame(0, index=jokers, columns=jokers, dtype=float)
    for _, row in df.iterrows():
        matrix.at[row["j1"], row["j2"]] = row["cooccur"]
        matrix.at[row["j2"], row["j1"]] = row["cooccur"]

    fig = px.imshow(
        matrix,
        color_continuous_scale=[[0.0, BG], [1.0, ACCENT]],
        labels=dict(x="Joker", y="Joker", color="Co-occurrences"),
        aspect="auto",
    )
    fig.update_layout(
        margin=CHART_MARGIN,
        title=dict(text="Joker co-occurrence (top-scoring runs)", font=dict(size=16)),
        font=dict(size=13),
    )
    st.plotly_chart(fig, use_container_width=True)


def panel_best_run(path: str) -> None:
    """Panel 5: best-run hand-by-hand table + per-hand score bar."""
    best, hands = load_best_run(path)
    st.subheader("Best run — hand by hand")
    if best is None or hands.empty:
        st.info(EMPTY_BEST_RUN)
        return

    st.caption(
        f"Deck {best.get('deck')} · stake {best.get('stake')} · "
        f"final score {fmt_si(best.get('final_score'))}"
    )
    view = hands[["hand_index", "ante", "hand_type", "chips", "mult", "score"]].copy()
    max_score = int(view["score"].max() or 1) or 1
    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "hand_index": st.column_config.NumberColumn("Hand"),
            "ante": st.column_config.NumberColumn("Ante"),
            "hand_type": st.column_config.TextColumn("Hand type"),
            "chips": st.column_config.NumberColumn("Chips", format="%d"),
            "mult": st.column_config.NumberColumn("Mult", format="%d"),
            "score": st.column_config.ProgressColumn(
                "Score",
                format="%d",
                min_value=0,
                max_value=max_score,
            ),
        },
    )

    bar = view.dropna(subset=["score"])
    if not bar.empty:
        fig = px.bar(
            bar,
            x="hand_index",
            y="score",
            color_discrete_sequence=[ACCENT],
        )
        fig.update_layout(
            margin=CHART_MARGIN,
            title=dict(text="Score per hand", font=dict(size=16)),
            font=dict(size=13),
        )
        fig.update_xaxes(title_text="Hand index")
        fig.update_yaxes(title_text="Score")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Data-region fragment — the only thing the 30s timer re-runs.
# ---------------------------------------------------------------------------


@st.fragment(run_every=_RUN_EVERY)
def data_region() -> None:
    path = _db_path()
    now = _dt.datetime.now().strftime("%H:%M:%S")
    st.caption(f"Last refreshed {now} · auto-refreshing every 30s")

    # Missing DB file is the EMPTY state (the seed script hasn't run yet),
    # not an error — render dashes + the seed instructions and stop.
    if not _db_exists(path):
        panel_kpis(path)
        st.divider()
        st.info(EMPTY_HEADING)
        st.markdown(EMPTY_BODY)
        return

    # File exists but the read failed -> genuine ERROR state.
    try:
        runs = load_runs(path)
    except Exception:
        st.error(ERROR_COPY)
        # KPI strip still renders dashes so the page shell stays intact.
        panel_kpis(path)
        return

    panel_kpis(path)
    st.divider()

    if runs.empty:
        st.info(EMPTY_HEADING)
        st.markdown(EMPTY_BODY)
        return

    tab_scores, tab_breakdown, tab_synergies, tab_best = st.tabs(
        ["Scores", "Breakdown", "Synergies", "Best run"]
    )
    with tab_scores:
        panel_histogram(path)
        panel_learning_curve(path)
    with tab_breakdown:
        panel_deck_stake(path)
        panel_hand_types(path)
    with tab_synergies:
        panel_heatmap(path)
    with tab_best:
        panel_best_run(path)


def main() -> None:
    st.set_page_config(page_title="Balatro ML — Training Monitor", layout="wide")
    st.title("Balatro ML — Training Monitor")
    st.divider()
    data_region()


main()
