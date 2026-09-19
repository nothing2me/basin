import pytest
import calendar
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from basin_core.data import CachedSource
from basin_core.workspace import Workspace
from basin_core.engine import ScenarioParams
from basin_core.analysis import simulate_stress_spectrum, simulate_reservoir_drawdown, build_shortlist_scorecard
from basin_core.visualizers import (
    rainfall_reference_figure,
    rainfall_shortfall_figure,
    stage_trigger_milestone_figure,
    storage_trajectory_figure,
    drought_anomaly_matrix_figure,
    shortlist_cumulative_deficit_figure,
    multi_scenario_storage_figure,
)


def test_station_reference_chart_keeps_reference_and_scenario_distinct():
    dates = pd.date_range("2001-01-01", periods=35)
    scenario = pd.Series(1.0, index=dates)
    reference = pd.Series(3.0, index=dates)
    fig = rainfall_reference_figure(scenario, reference)
    assert list(fig.data[0].y) == list(range(3, 106, 3))
    assert list(fig.data[1].y) == list(range(1, 36))
    assert fig.data[0].name == "Historical monthly reference"
    daily = rainfall_reference_figure(scenario, reference, "Daily rainfall")
    assert set(daily.data[0].y) == {3.0}
    assert set(daily.data[1].y) == {1.0}
    deficit = rainfall_reference_figure(scenario, reference, "30-day deficit")
    assert all(pd.isna(y) for y in deficit.data[0].y[:29])
    assert list(deficit.data[0].y[29:]) == [60.0] * 6


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


def test_shortfall_panels_preserve_scenario_values_and_selection(workspace):
    view = make_view(workspace)
    fig = rainfall_shortfall_figure(view, workspace.selected, workspace.selected[0])
    candidates = [t for t in fig.data if t.legendgroup.startswith("profile-")]
    plotted = {d[0]: (x, y, d[6]) for t in candidates for x, y, d in zip(t.x, t.y, t.customdata)}
    assert len(plotted) == len(view)
    for _, row in view.iterrows():
        assert plotted[row.ID][1:] == (row["Deficit mm"], row.Days)
    for t in fig.data:
        if t.legendgroup in {"shortlist", "focus", "maximum"}:
            for x, y, d in zip(t.x, t.y, t.customdata):
                assert (x, y, d[6]) == plotted[d[0]]
    selected = {d[0] for t in fig.data if t.legendgroup == "shortlist" for d in t.customdata}
    assert selected == set(workspace.selected)
    assert sum(len(t.text) for t in fig.data if t.text is not None) == 1
    yaxes = [fig.layout[k] for k in fig.layout if k.startswith("yaxis")]
    assert len({tuple(axis.range) for axis in yaxes}) == 1


def test_shortfall_panels_unit_in(workspace):
    view = make_view(workspace)
    fig_in = rainfall_shortfall_figure(view, workspace.selected, workspace.selected[0], unit="in")
    candidates = [t for t in fig_in.data if t.legendgroup.startswith("profile-")]
    plotted = {d[0]: (x, y, d[6]) for t in candidates for x, y, d in zip(t.x, t.y, t.customdata)}
    for _, row in view.iterrows():
        assert plotted[row.ID][1:] == (row["Deficit in"], row.Days)
    yaxes = [fig_in.layout[k] for k in fig_in.layout if k.startswith("yaxis")]
    titles = [axis.title.text for axis in yaxes if getattr(axis, "title", None) and getattr(axis.title, "text", None)]
    assert "Total rainfall deficit (in)" in titles


def test_shortfall_offsets_are_stable_and_maxima_are_per_duration(workspace):
    view = make_view(workspace)
    # Equal deficits must remain separately selectable. A later duration can have
    # a smaller maximum and still needs a maximum marker in its own panel.
    view["Deficit mm"] = 1000 / view["Days"]
    first = rainfall_shortfall_figure(view, [])
    shuffled = rainfall_shortfall_figure(view.sample(frac=1, random_state=3), [])
    def locations(fig):
        return {d[0]: (t.xaxis, x, y) for t in fig.data if t.legendgroup.startswith("profile-")
                for x, y, d in zip(t.x, t.y, t.customdata)}
    assert locations(first) == locations(shuffled)
    assert len(set(locations(first).values())) == len(view)
    maxima = {d[0] for t in first.data if t.legendgroup == "maximum" for d in t.customdata}
    assert maxima == set(view.ID)  # All tied maxima are represented.
    assert not any(t.legendgroup == "shortlist" or "lines" in t.mode for t in first.data)


def test_shortfall_empty_and_multiple_duration_layouts(workspace):
    assert rainfall_shortfall_figure(pd.DataFrame()).layout.annotations
    view = make_view(workspace).head(6).copy()
    view["Days"] = [30, 60, 90, 180, 270, 365]
    view["Group"] = 0
    for count in (1, 4, 6):
        fig = rainfall_shortfall_figure(view.head(count), colorblind=True)
        assert len([key for key in fig.layout if key.startswith("yaxis")]) == count
        profiles = [t for t in fig.data if t.legendgroup.startswith("profile-")]
        assert len({(t.marker.color, t.marker.symbol) for t in profiles}) == 1


def test_stage_trigger_milestone_multitier(workspace):
    sc = workspace.get(workspace.selected[0])
    spec = simulate_stress_spectrum(sc.series, initial_pct=0.35, conservation_pct=0.15, pipeline_active=True)

    fig = stage_trigger_milestone_figure(spec)
    assert isinstance(fig, go.Figure)
    assert fig.layout.barmode == "overlay"
    assert fig.layout.height == 280
    assert fig.layout.margin.t >= 70
    assert fig.layout.margin.b >= 60

    for trace in fig.data:
        assert trace.orientation == "h"
        assert trace.customdata is not None


def test_stage_trigger_milestone_singletier(workspace):
    sc = workspace.get(workspace.selected[0])
    sim_df = simulate_reservoir_drawdown(sc.series, initial_pct=0.48, conservation_pct=0.0, pipeline_active=True)

    spec = {"tier_results": {1.0: {"df": sim_df}}}
    fig = stage_trigger_milestone_figure(spec)

    assert isinstance(fig, go.Figure)
    assert fig.layout.height == 220
    assert fig.layout.margin.l == 45
    assert fig.layout.xaxis.title.text == "Scenario day"
    assert fig.layout.yaxis.showticklabels is False
    assert any(trace.y[0] == "Scenario Timeline" for trace in fig.data)


def test_simple_storage_trajectory_uses_same_result_without_animation(workspace):
    sc = workspace.get(workspace.selected[0])
    sim_df = simulate_reservoir_drawdown(sc.series, initial_pct=0.48,
                                         conservation_pct=0.0, pipeline_active=True)
    fig = storage_trajectory_figure(sim_df)
    assert fig.frames == ()
    assert fig.layout.updatemenus == ()
    assert list(fig.data[0].y) == list(sim_df["combined_pct"])
    assert fig.data[1].text[0] == f"End {sim_df.iloc[-1]['combined_pct']:.1f}%"
    assert fig.layout.height < 500


def test_drought_anomaly_matrix_figure(workspace):
    source = workspace.source
    stations = [s["id"] for s in source.manifest["stations"]]
    obs = source.select(stations)

    fig = drought_anomaly_matrix_figure(obs, title_prefix="Selected-station average")
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


def test_shortlist_cumulative_deficit_figure(workspace):
    fig_in = shortlist_cumulative_deficit_figure(workspace, unit="in")
    assert isinstance(fig_in, go.Figure)
    assert fig_in.layout.yaxis.title.text == "Cumulative Rainfall Deficit (in)"
    # Has envelope, average line, plus scenario traces
    trace_names = [t.name for t in fig_in.data]
    assert "Shortlist Range (Min–Max)" in trace_names
    assert "Shortlist Average Deficit" in trace_names
    assert any(s_id in name for name in trace_names for s_id in workspace.selected)

    fig_mm = shortlist_cumulative_deficit_figure(workspace, unit="mm")
    assert fig_mm.layout.yaxis.title.text == "Cumulative Rainfall Deficit (mm)"


def test_multi_scenario_storage_figure(workspace):
    fig = multi_scenario_storage_figure(workspace, initial_pct=0.48)
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.title.text == "Combined Reservoir Storage (% Capacity)"
    # Selected scenario traces should be present
    trace_names = [t.name for t in fig.data]
    assert any(s_id in name for name in trace_names for s_id in workspace.selected)


def test_build_shortlist_scorecard(workspace):
    scorecard = build_shortlist_scorecard(workspace, unit="us")
    assert isinstance(scorecard, pd.DataFrame)
    assert len(scorecard) == len(workspace.selected)
    assert "Scenario ID" in scorecard.columns
    assert "Historical Window" in scorecard.columns
    assert "Duration (days)" in scorecard.columns
    assert "Total Deficit (in)" in scorecard.columns
    assert "Station Concurrence" in scorecard.columns
    assert "Historical Rarity" in scorecard.columns
    assert "Stage 2 (30%) Breach" in scorecard.columns
    assert "Stage 3 (20%) Breach" in scorecard.columns
    assert "Ranking Score" in scorecard.columns

