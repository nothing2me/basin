import pytest
import calendar
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from basin_core.data import CachedSource
from basin_core.workspace import Workspace
from basin_core.engine import ScenarioParams
from basin_core.analysis import simulate_stress_spectrum, simulate_reservoir_drawdown
from basin_core.visualizers import (
    pareto_frontier_figure,
    stage_trigger_milestone_figure,
    drought_anomaly_matrix_figure,
)


@pytest.fixture
def workspace():
    source = CachedSource()
    stations = [s["id"] for s in source.manifest["stations"]]
    params = ScenarioParams(stations=stations, seed=22)
    return Workspace(source, params, 6)


def make_view(w):
    return pd.DataFrame([{"ID": s.id, "Group": s.cluster, "Profile": getattr(s, "cluster_name", f"Group {s.cluster}"),
                          "Score": round(s.score, 2),
                          "Days": s.features["duration_days"], "Onset": calendar.month_abbr[s.features["onset_month"]],
                          "Deficit mm": round(s.features["deficit_mm"], 2),
                          "Deficit in": round(s.features["deficit_mm"] / 25.4, 2),
                          "Stations stressed together %": round(s.features["concurrence"] * 100, 1),
                          "How unusual vs history %": round(s.features["historical_percentile"] * 100, 1),
                          "Dry spell days": s.features["max_dry_days"],
                          "Revision": s.revision, "Status": s.status,
                          "Selected for review": s.id in w.selected} for s in w.scenarios])


def test_pareto_frontier_figure_structure(workspace):
    view = make_view(workspace)
    fig = pareto_frontier_figure(view, workspace.selected)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 3

    trace_names = [t.name for t in fig.data if getattr(t, "name", None)]
    assert any("Pareto" in n for n in trace_names)
    assert any("Selected for review" in n for n in trace_names)

    pareto_trace = next(t for t in fig.data if "Pareto" in (t.name or ""))
    assert pareto_trace.line.dash == "dash"

    shortlist_trace = next(t for t in fig.data if "Selected for review" in (t.name or ""))
    assert len(shortlist_trace.x) == len(workspace.selected)


def test_pareto_frontier_empty_shortlist(workspace):
    view = make_view(workspace)
    fig = pareto_frontier_figure(view, [])
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if getattr(t, "name", None)]
    assert any("Pareto" in n for n in trace_names)


def test_stage_trigger_milestone_multitier(workspace):
    sc = workspace.get(workspace.selected[0])
    spec = simulate_stress_spectrum(sc.series, initial_pct=0.35, conservation_pct=0.15, pipeline_active=True)

    fig = stage_trigger_milestone_figure(spec)
    assert isinstance(fig, go.Figure)
    assert fig.layout.barmode == "overlay"
    assert fig.layout.height == 230

    for trace in fig.data:
        assert trace.orientation == "h"
        assert trace.customdata is not None


def test_stage_trigger_milestone_singletier(workspace):
    sc = workspace.get(workspace.selected[0])
    sim_df = simulate_reservoir_drawdown(sc.series, initial_pct=0.48, conservation_pct=0.0, pipeline_active=True)

    spec = {"tier_results": {1.0: {"df": sim_df}}}
    fig = stage_trigger_milestone_figure(spec)

    assert isinstance(fig, go.Figure)
    assert fig.layout.height == 130
    assert any(trace.y[0] == "Scenario Timeline" for trace in fig.data)


def test_drought_anomaly_matrix_figure(workspace):
    source = workspace.source
    stations = [s["id"] for s in source.manifest["stations"]]
    obs = source.select(stations)

    fig = drought_anomaly_matrix_figure(obs, title_prefix="Catchment composite")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Heatmap)

    heatmap = fig.data[0]
    assert len(heatmap.x) == 12
    assert len(heatmap.y) == 35
    assert heatmap.zmin == -100
    assert heatmap.zmax == 150

    single_obs = source.select([stations[0]])
    fig_single = drought_anomaly_matrix_figure(single_obs, title_prefix="Single station")
    assert isinstance(fig_single, go.Figure)
    assert len(fig_single.data[0].x) == 12
