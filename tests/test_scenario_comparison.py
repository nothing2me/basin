import pytest
import pandas as pd
import plotly.graph_objects as go

from basin_core.data import CachedSource
from basin_core.workspace import Workspace
from basin_core.engine import ScenarioParams
from basin_core.analysis import build_shortlist_scorecard
from basin_core.visualizers import (
    shortlist_cumulative_deficit_figure,
    multi_scenario_storage_figure,
)


@pytest.fixture
def workspace():
    source = CachedSource()
    stations = [s["id"] for s in source.manifest["stations"]]
    params = ScenarioParams(stations=stations, seed=22)
    return Workspace(source, params, 6)


def test_shortlist_cumulative_deficit_figure_structure(workspace):
    fig = shortlist_cumulative_deficit_figure(workspace, unit="in")
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.title.text == "Cumulative Rainfall Deficit (in)"
    assert fig.layout.xaxis.title.text == "Scenario Timeline (Elapsed Days)"

    # Verify traces: Envelope, Mean line, plus 6 scenarios
    trace_names = [t.name for t in fig.data]
    assert "Shortlist Range (Min–Max)" in trace_names
    assert "Shortlist Average Deficit" in trace_names
    for s_id in workspace.selected:
        assert any(s_id in name for name in trace_names)

    # Verify metric units switch
    fig_mm = shortlist_cumulative_deficit_figure(workspace, unit="mm")
    assert fig_mm.layout.yaxis.title.text == "Cumulative Rainfall Deficit (mm)"


def test_shortlist_cumulative_deficit_empty():
    fig = shortlist_cumulative_deficit_figure(None)
    assert isinstance(fig, go.Figure)
    assert len(fig.layout.annotations) > 0


def test_multi_scenario_storage_figure_structure(workspace):
    fig = multi_scenario_storage_figure(workspace, initial_pct=0.48, unit="us")
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.title.text == "Combined Reservoir Storage (% Capacity)"
    assert fig.layout.xaxis.title.text == "Simulation Timeline (Elapsed Days)"

    # Verify horizontal threshold annotations exist
    annotation_texts = [a.text for a in fig.layout.annotations]
    assert any("Stage 1" in t for t in annotation_texts)
    assert any("Stage 2" in t for t in annotation_texts)


def test_build_shortlist_scorecard_columns_and_rows(workspace):
    scorecard = build_shortlist_scorecard(workspace, unit="us")
    assert isinstance(scorecard, pd.DataFrame)
    assert len(scorecard) == len(workspace.selected)

    expected_cols = [
        "Scenario ID",
        "Historical Window",
        "Duration (days)",
        "Total Deficit (in)",
        "Deficit Rate (in/mo)",
        "Station Concurrence",
        "Historical Rarity",
        "Stage 2 (30%) Breach",
        "Stage 3 (20%) Breach",
        "Min Storage",
        "End Storage",
        "Ranking Score",
        "Status",
    ]
    for col in expected_cols:
        assert col in scorecard.columns, f"Missing expected column: {col}"

    for _, row in scorecard.iterrows():
        assert row["Duration (days)"] in (30, 60, 90, 180, 270, 365)
        assert row["Total Deficit (in)"] >= 0.0
        assert "%" in row["Station Concurrence"]
        assert "%" in row["Historical Rarity"]
