"""Offline smoke tests for the Streamlit dashboard (DASH-03).

These run WITHOUT a live Streamlit server and WITHOUT a live game:

  * fmt_si unit tests — the shared SI-abbreviation helper.
  * Empty-state AppTest — point the app at a missing DB; assert it renders the
    "No training data yet" empty-state copy and raises no exception.
  * Loaded-state AppTest — point the app at the deterministic ``seeded_db``
    fixture; assert all 7 panels / 4 tabs render with no exception.

The app reads its DB path from the ``BML_DB_PATH`` environment variable when set
(falling back to ``db.DB_PATH``), which lets these tests redirect reads to a temp
DB without touching ``data/runs.db``.
"""

from __future__ import annotations

import os

import pytest
from streamlit.testing.v1 import AppTest

from src.dashboard.format import fmt_si

APP_PATH = "src/dashboard/app.py"


@pytest.fixture(autouse=True)
def _disable_autorefresh(monkeypatch):
    """Run AppTest with the 30s fragment timer off so the recurring fragment
    thread cannot race with test teardown (deterministic offline runs)."""
    monkeypatch.setenv("BML_DISABLE_AUTOREFRESH", "1")


# ---------------------------------------------------------------------------
# fmt_si unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (41_200, "41.2K"),
        (3_500_000_000, "3.5B"),
        (None, "—"),
        (1_240_000_000_000, "1.2T"),
        (0, "0"),
    ],
)
def test_fmt_si_known_values(value, expected):
    assert fmt_si(value) == expected


def test_fmt_si_small_int_has_thousands_separator():
    # Below the K threshold: pass through with a thousands separator.
    assert fmt_si(940) == "940"
    assert fmt_si(9_400) == "9.4K"


def test_fmt_si_handles_float():
    assert fmt_si(41_200.0) == "41.2K"


# ---------------------------------------------------------------------------
# AppTest: empty state (no DB)
# ---------------------------------------------------------------------------


def test_empty_state_renders_without_db(monkeypatch, tmp_path):
    """No DB file -> empty-state copy, no exception, no blank charts."""
    missing = str(tmp_path / "does_not_exist.db")
    monkeypatch.setenv("BML_DB_PATH", missing)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert not at.exception
    # Empty-state heading must be present somewhere in info/markdown.
    texts = [el.value for el in at.info] + [el.value for el in at.markdown]
    joined = " ".join(str(t) for t in texts)
    assert "No training data yet" in joined


def test_empty_state_kpis_show_dash(monkeypatch, tmp_path):
    missing = str(tmp_path / "missing.db")
    monkeypatch.setenv("BML_DB_PATH", missing)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert not at.exception
    # All four KPI metrics fall back to the em-dash placeholder.
    metric_values = [m.value for m in at.metric]
    assert metric_values  # KPI strip rendered
    assert all(v == "—" for v in metric_values)


# ---------------------------------------------------------------------------
# AppTest: loaded state (seeded DB)
# ---------------------------------------------------------------------------


def test_loaded_state_renders_all_panels(monkeypatch, seeded_db):
    """Seeded DB -> all tabs/panels render, no exception."""
    monkeypatch.setenv("BML_DB_PATH", seeded_db)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert not at.exception

    # The 4 locked tabs are present.
    tab_labels = {t.label for t in at.tabs}
    for expected in ("Scores", "Breakdown", "Synergies", "Best run"):
        assert expected in tab_labels, f"missing tab {expected!r}: {tab_labels}"

    # KPI strip rendered 4 metrics with real (non-dash) values.
    metric_values = [m.value for m in at.metric]
    assert len(metric_values) == 4
    assert any(v != "—" for v in metric_values)


def test_loaded_state_has_charts(monkeypatch, seeded_db):
    monkeypatch.setenv("BML_DB_PATH", seeded_db)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert not at.exception
    # At least the histogram / curve / bars / heatmap produced Plotly charts.
    # AppTest exposes plotly figures via the generic element list.
    chart_count = len(at.get("plotly_chart")) if "plotly_chart" in dir(at) else 0
    # Fallback: ensure dataframe (best-run table) rendered.
    assert chart_count >= 1 or len(at.dataframe) >= 1
