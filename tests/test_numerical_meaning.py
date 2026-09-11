"""Hand-calculable regressions for what BASIN's numbers mean on each surface.

Each fixture states its arithmetic so a reviewer can check it without running the model.
They pin interpretation and labelling; they do not establish scientific validity.
"""
from copy import deepcopy
import re
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from basin_core import tools
from basin_core.agronomics import calculate_crop_water_deficit
from basin_core.analysis import (rainfall_tier_label, simulate_reservoir_drawdown, simulate_stress_spectrum,
                                 threshold_crossing_day, threshold_day_label)
from basin_core.assistant import render_tool_result, run_tool_directly, semantic_query_route, validate_tool_args
from basin_core.pdf_report import ExperimentConfig, build_fallback_pdf, compute_report_metrics, render_html_report
from basin_core.simulation import (SimulationSettings, content_hash, describe_input_rainfall, observed_percent,
                                   validate_run)
from basin_core.visualizers import stage_trigger_milestone_figure
from basin_core.water_system import REGION_N_PRESET, WaterSource, WaterSystemConfig


def tank(capacity: float, inflow_per_mm: float = 0.0, demand: float = 0.0) -> WaterSystemConfig:
    """One pool with no base inflow and no evaporation, so storage is simple addition."""
    return WaterSystemConfig("Hand-check tank", (WaterSource("Tank", capacity, inflow_base_acft=0.0,
                             inflow_sensitivity=inflow_per_mm, evap_summer_acft=0.0, evap_winter_acft=0.0),),
                             demand_acft_day=demand, demand_no_pipeline_acft_day=None)


def daily(values, start="2001-01-01") -> pd.DataFrame:
    return pd.DataFrame({"s": [float(v) for v in values]}, index=pd.date_range(start, periods=len(values)))


def vector_text(pdf_bytes: bytes) -> str:
    """Drawn text of a vector PDF with string escaping undone (parentheses are escaped)."""
    drawn = []
    for line in pdf_bytes.decode("latin1").splitlines():
        match = re.search(r"Tm \((.*)\) Tj ET$", line)
        if match:
            drawn.append(match.group(1).replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\"))
    return " ".join(drawn)


def stub_scenario(retention: dict, history=()) -> SimpleNamespace:
    edits = [e for e in history if e["action"] in ("scale", "replace")]
    return SimpleNamespace(id="B-900", revision=1 + len(edits), history=list(history),
                           provenance={"source_start": "2011-04-01", "source_end": "2011-06-29",
                                       "retention_by_station": retention})


@pytest.fixture
def accepted(workspace):
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "Rainfall checked for the numerical-meaning fixture")
    return workspace


# --------------------------------------------------------------------------------------
# 1. A transformed scenario: 100% is the scenario revision, not the historical record
# --------------------------------------------------------------------------------------

def test_input_rainfall_multiple_is_hand_calculable():
    """Constructed at 50%, then scaled by 0.8: the input is 0.5 x 0.8 = 40% of observed.
    A 50% tier of that input is 0.5 x 0.4 = 20% of observed rainfall."""
    scenario = stub_scenario({"A": 0.5, "B": 0.5}, [{"action": "scale", "factor": 0.8, "revision": 2}])
    current = describe_input_rainfall(scenario)
    assert current["observed_fraction"] == pytest.approx(0.4)
    assert observed_percent(0.5, current) == 20.0
    assert "constructed at 50% of observed rainfall" in current["summary"]
    assert "revision 2 scaled rainfall by 0.8" in current["summary"]
    assert "not the unmodified historical record" in current["hundred_percent_meaning"]

    # The same scenario described at revision 1 excludes the later edit.
    assert describe_input_rainfall(scenario, revision=1)["observed_fraction"] == 0.5

    # No single multiple exists for station-specific retention or a CSV replacement.
    uneven = describe_input_rainfall(stub_scenario({"A": 0.5, "B": 1.0}))
    assert uneven["observed_fraction"] is None and "A 50%, B 100%" in uneven["summary"]
    assert observed_percent(0.5, uneven) is None
    replaced = stub_scenario({"A": 0.5, "B": 0.5}, [{"action": "replace", "factor": None, "revision": 2}])
    assert describe_input_rainfall(replaced)["observed_fraction"] is None

    observed = describe_input_rainfall(scenario, "observed_window")
    assert observed["observed_fraction"] == 1.0
    assert observed["hundred_percent_meaning"] == "100% is the unmodified observed window."


def test_transformed_workspace_scenario_is_not_presented_as_historical(workspace):
    scenario = workspace.get(workspace.selected[0])
    retention = list(scenario.provenance["retention_by_station"].values())
    assert len(set(retention)) == 1, "fixture uses all-station retention"
    workspace.edit(scenario.id, "Halve rainfall for the fixture", factor=0.5)

    # The described multiple really is what the series contains.
    p = scenario.provenance
    observed = workspace.reference.daily.loc[p["source_start"]:p["source_end"], list(scenario.series.columns)]
    assert np.allclose(scenario.series.to_numpy(), observed.to_numpy() * retention[0] * 0.5)
    expected_observed = round(retention[0] * 0.5 * 100, 1)

    data = tools.run_stress_spectrum(workspace, scenario_id=scenario.id, initial_storage_pct=48)
    assert data["input_rainfall"]["observed_fraction"] == pytest.approx(retention[0] * 0.5)
    rendered = render_tool_result("run_stress_spectrum", data)
    assert f"revision {scenario.revision}" in rendered
    assert "not the unmodified historical record" in rendered
    assert f"| 100% of input rainfall | {expected_observed:g}% |" in rendered
    lowered = rendered.lower()
    for claim in ("historical baseline", "survived", "catastrophic", "breached"):
        assert claim not in lowered, claim

    # The observed-window experiment on the same scenario says it is unmodified observations.
    observed_run = tools.run_stress_spectrum(workspace, scenario_id=scenario.id, baseline_kind="observed_window")
    rendered_observed = render_tool_result("run_stress_spectrum", observed_run)
    assert "unmodified NOAA observations" in rendered_observed
    assert "| 100% of input rainfall | 100% |" in rendered_observed


# --------------------------------------------------------------------------------------
# 2. A non-default rainfall tier
# --------------------------------------------------------------------------------------

def test_non_default_tiers_are_labelled_and_computed_by_hand():
    """1,000 ac-ft pool at 50%, 10 ac-ft inflow per mm, 30 ac-ft/day demand, 1 mm/day.
    100%: 500 + 10 - 30 = 480, 460, 440.  50%: +5 -> 475, 450, 425.  25%: +2.5 -> 472.5, 445, 417.5."""
    spec = simulate_stress_spectrum(daily([1, 1, 1]), tiers=(1.0, 0.5, 0.25), initial_pct=0.5,
                                    config=tank(1000, inflow_per_mm=10, demand=30))
    labels = [row["tier_label"] for row in spec["summary_table"]]
    assert labels == ["100% of input rainfall", "50% of input rainfall (50% reduction)",
                      "25% of input rainfall (75% reduction)"]
    for multiplier, expected in ((1.0, [480, 460, 440]), (0.5, [475, 450, 425]), (0.25, [472.5, 445, 417.5])):
        assert spec["tier_results"][multiplier]["df"]["combined_acft"].tolist() == expected
        assert spec["tier_results"][multiplier]["metrics"]["day_stage1_40"] is None

    # Float percentages are rounded, not truncated (int(0.29 * 100) is 28).
    assert rainfall_tier_label(0.29) == "29% of input rainfall (71% reduction)"
    assert rainfall_tier_label(1.1) == "110% of input rainfall (10% increase)"
    two_tier = simulate_stress_spectrum(daily([1, 1]), tiers=(1.0, 0.29), initial_pct=0.5, config=tank(1000, 10, 30))
    unlabelled = {m: {"df": r["df"]} for m, r in two_tier["tier_results"].items()}
    names = {trace.y[0] for trace in stage_trigger_milestone_figure({"tier_results": unlabelled}).data}
    assert "29% of input rainfall (71% reduction)" in names


def test_saved_non_default_tiers_use_the_same_labels(workspace):
    run = workspace.run_simulation(workspace.selected[0], SimulationSettings(retention_fractions=(1.0, 0.5, 0.25)))
    assert [r["tier_label"] for r in run["results"]["summary_table"]] == [
        "100% of input rainfall", "50% of input rainfall (50% reduction)", "25% of input rainfall (75% reduction)"]
    validate_run(workspace, run)


# --------------------------------------------------------------------------------------
# 3. An absent requested year, and other inputs that must not be assumed
# --------------------------------------------------------------------------------------

def test_absent_year_returns_no_rows_and_never_substitutes(workspace):
    start_years = sorted({int(s.provenance["source_start"][:4]) for s in workspace.scenarios})
    absent = next(y for y in range(1991, 2026) if y not in start_years)
    data = tools.find_scenarios_by_year(workspace, absent)
    assert data["total_matches"] == 0 and data["scenarios"] == []
    assert data["available_start_years"] == start_years
    rendered = render_tool_result("find_scenarios_by_year", data)
    assert "No other year was substituted" in rendered and "| **B-" not in rendered

    present = start_years[0]
    matched = tools.find_scenarios_by_year(workspace, present)["scenarios"]
    assert matched and all(row["source_start"].startswith(f"{present}-") for row in matched)


@pytest.mark.parametrize("year", [201, "2011", 2011.0, True, None])
def test_year_must_be_an_exact_four_digit_integer(workspace, year):
    """Old code matched by string prefix, so 201 returned every 2010-2019 window."""
    with pytest.raises((ValueError, TypeError)):
        tools.find_scenarios_by_year(workspace, year)


def test_router_asks_instead_of_assuming_year_station_dates_group_or_scenario(workspace):
    cases = {
        "Show me recent drought scenarios": "source start year",
        "Show daily rainfall observations for station USW00012924": "no period is assumed",
        "What was the daily rainfall in 2011?": "name a station",
        "Describe the drought profile group": "group number",
        "Explain the ranking score": "scenario ID",
        "Compare scenarios": "2 scenario IDs",
    }
    for question, expected in cases.items():
        reply = semantic_query_route(workspace, question)
        assert "Please clarify" in reply and expected in reply, (question, reply)
    assert "No drought profile group 0" in semantic_query_route(workspace, "What defines drought group 0?")


def test_direct_tool_runner_never_invents_inputs(workspace):
    """The input-free runner used to send 2011 dates, group 0 and empty experiment settings."""
    from basin_ui import direct_tool_arguments

    for name in ("query_rainfall", "find_scenarios_by_year", "run_sensitivity",
                 "test_reservoir_infrastructure", "run_stress_spectrum"):
        assert direct_tool_arguments(workspace, name) is None, name
    args, described = direct_tool_arguments(workspace, "describe_cluster")
    assert args["cluster_id"] in {s.cluster for s in workspace.scenarios} and "group" in described
    args, described = direct_tool_arguments(workspace, "describe_scenario")
    assert described == f" for {args['scenario_id']} (first shortlisted scenario)"


def test_year_errors_state_the_bundled_record_period(workspace):
    with pytest.raises(ValueError, match="covers 1991–2025"):
        tools.run_stress_spectrum(workspace, year=1990)
    with pytest.raises(ValueError, match=r"\(1991–2025\)"):
        validate_tool_args(workspace, "find_scenarios_by_year", {"year": 1990})


def test_query_rainfall_dates_are_explicit(workspace):
    station = workspace.source.manifest["stations"][0]["id"]
    one_day = tools.query_rainfall(workspace, station, "2011-05-01", "2011-05-01")
    assert one_day["calendar_days"] == 1
    for start, end in (("2011", "2011-12-31"), ("2011-02-30", "2011-03-01"), ("2011-06-01", "2011-05-01")):
        with pytest.raises(ValueError):
            tools.query_rainfall(workspace, station, start, end)


# --------------------------------------------------------------------------------------
# 4. Invalid or ambiguous percentages
# --------------------------------------------------------------------------------------

def test_fractional_initial_storage_is_refused_not_read_as_percent(workspace):
    sid = workspace.selected[0]
    # What the old validator allowed through: the tool reads 0.48 as 0.48%, not 48%.
    assert SimulationSettings.from_percent(initial_storage_percent=0.48).initial_storage_fraction == pytest.approx(0.0048)
    with pytest.raises(ValueError, match="ambiguous"):
        validate_tool_args(workspace, "run_stress_spectrum", {"scenario_id": sid, "initial_storage_pct": 0.48})
    with pytest.raises(ValueError, match="ambiguous"):
        validate_tool_args(workspace, "run_stress_spectrum", {"scenario_id": sid, "initial_storage_pct": 1})

    reply = run_tool_directly(workspace, "run_stress_spectrum", {"scenario_id": sid, "initial_storage_pct": 48})
    assert "Initial storage: **48%**" in reply
    assert workspace.active_simulation(sid)["settings"]["initial_storage_fraction"] == pytest.approx(0.48)


@pytest.mark.parametrize("weights", [{"severity": 150}, {"duration": -5}, {"season": True}, {"concurrence": float("nan")}])
def test_sensitivity_weights_outside_0_to_100_are_refused(workspace, weights):
    with pytest.raises(ValueError):
        tools.run_sensitivity(workspace, **weights)


def test_unlabelled_or_misattributed_percentages_are_not_guessed(workspace):
    sid = workspace.selected[0]
    before = len(workspace.simulation_runs)
    assert "Label each percentage" in semantic_query_route(workspace, f"Run spectrum on {sid} with 25%")
    assert len(workspace.simulation_runs) == before

    # Old router: the word "conservation" made the first percentage (35) the conservation value.
    semantic_query_route(workspace, f"Run spectrum on {sid} at 35% initial storage with conservation")
    settings = workspace.active_simulation(sid)["settings"]
    assert settings["initial_storage_fraction"] == pytest.approx(0.35)
    assert settings["conservation_fraction"] == 0.0

    # Listing the standard tiers is not a setting.
    assert "Reservoir Stress Spectrum" in semantic_query_route(workspace, f"Test 100%, 80%, 60%, 40% rainfall tiers for {sid}")


# --------------------------------------------------------------------------------------
# 5. Threshold equality and day 0
# --------------------------------------------------------------------------------------

def test_threshold_boundary_is_inclusive_everywhere():
    """100 ac-ft pool at 25%, 5 ac-ft/day demand, no inflow: 25 -> 20.0 -> 15.0 -> 10.0.
    40% and 30%: already at or below at the start (day 0). 20%: day 1. 15%: day 2."""
    series = daily([0, 0, 0])
    sim = simulate_reservoir_drawdown(series, initial_pct=0.25, config=tank(100, demand=5))
    assert sim["combined_pct"].tolist() == [20.0, 15.0, 10.0]
    # Bands match the crossing rule at equality (the old strict rule gave 2 and 3).
    assert sim["stage_num"].tolist() == [3, 4, 4]

    row = simulate_stress_spectrum(series, tiers=(1.0,), initial_pct=0.25, config=tank(100, demand=5))["summary_table"][0]
    assert (row["day_stage1_40"], row["day_stage2_30"], row["day_stage3_20"], row["day_emergency_15"]) == (0, 0, 1, 2)
    assert row["survived_critical_20pct"] is False and row["status"] == "At or below 20% in window"

    # 0.1 ac-ft less demand leaves 20.1% on day 1, which is not a crossing.
    just_above = simulate_stress_spectrum(daily([0, 0]), tiers=(1.0,), initial_pct=0.25, config=tank(1000, demand=49))
    assert just_above["tier_results"][1.0]["df"]["combined_pct"].iloc[0] == pytest.approx(20.1)
    assert just_above["summary_table"][0]["day_stage3_20"] == 2

    # The timeline legend puts exactly 40% in the 40% band too.
    flat = {"tier_results": {1.0: {"df": pd.DataFrame({"day": [1, 2], "combined_pct": [40.0, 40.0]})}}}
    assert {t.name for t in stage_trigger_milestone_figure(flat).data} == {"Above 30% to 40%"}


def test_day_zero_is_rendered_as_a_crossing_by_the_assistant():
    spec = simulate_stress_spectrum(daily([0, 0, 0]), tiers=(1.0,), initial_pct=0.25, config=tank(100, demand=5))
    data = {**spec, "scenario_id": "HAND", "scenario_revision": 1, "source_start": "2001-01-01",
            "source_end": "2001-01-03", "simulation_id": "sim-hand", "_snapshot": "hand",
            "input_rainfall": describe_input_rainfall(stub_scenario({"s": 1.0}), "observed_window")}
    rendered = render_tool_result("run_stress_spectrum", data)
    assert "| Day 0 (at/below at start) | Day 0 (at/below at start) | Day 1 | Day 2 |" in rendered
    assert threshold_day_label(None) == "Not reached in window"

    row = spec["summary_table"][0]
    reservoir = render_tool_result("test_reservoir_infrastructure", {
        **data, "rainfall_reduction_pct": 0, "retention_pct": 100.0, "observed_pct": 100.0,
        "initial_pct": 25.0, "initial_acft": 25.0, "conservation_pct": 0.0,
        **{k: row[k] for k in ("final_pct", "final_acft", "min_pct", "min_acft", "survived_critical_20pct")},
        "day_band1_40pct": 0, "day_band2_30pct": 0, "day_band3_20pct": 1, "day_band4_15pct": 2})
    assert "40% band: Day 0 (at/below at start)" in reservoir and "reached the assumed 20% band on **day 1**" in reservoir


def test_reachable_day_zero_is_shown_in_both_report_paths(accepted):
    """The Review screen offers 35% initial storage, which is already at or below 40% at the start.
    Old reports printed an absent value there; old app metrics reported the first row, day 1."""
    workspace = accepted
    scenario = workspace.get(workspace.selected[0])
    config = ExperimentConfig(initial_pct=0.35, scenario_id=scenario.id, scenario_revision=scenario.revision, selected=True)
    row = compute_report_metrics(scenario, config).spectrum_data["summary_table"][0]
    assert row["day_stage1_40"] == 0
    sim = simulate_reservoir_drawdown(scenario.series, initial_pct=0.35)
    assert threshold_crossing_day(sim, 0.35, 40.0) == 0 and int(sim["day"].iloc[0]) == 1

    exported = workspace.exportable()
    assert "Day 0 (at/below at start)*" in render_html_report(workspace, exported, config=config)
    assert "Day 0 (start)" in vector_text(build_fallback_pdf(workspace, exported, config=config))


# --------------------------------------------------------------------------------------
# Same selected inputs, same numbers: app calculation, deterministic tool, report
# --------------------------------------------------------------------------------------

def test_ui_tool_and_report_agree_on_the_same_selected_inputs(accepted):
    workspace = accepted
    scenario = workspace.get(workspace.selected[0])

    ui = simulate_stress_spectrum(scenario.series, initial_pct=0.35, conservation_pct=0.2, pipeline_active=True,
                                  config=REGION_N_PRESET)["summary_table"]
    tool = tools.run_stress_spectrum(workspace, scenario_id=scenario.id, initial_storage_pct=35, conservation_pct=20)["summary_table"]
    config = ExperimentConfig(initial_pct=0.35, conservation_pct=0.2, scenario_id=scenario.id,
                              scenario_revision=scenario.revision, selected=True, system_config=REGION_N_PRESET)
    metrics = compute_report_metrics(scenario, config)
    report = metrics.spectrum_data["summary_table"]

    fields = ("tier_label", "retention_pct", "min_pct", "min_acft", "final_pct", "final_acft",
              "day_stage1_40", "day_stage2_30", "day_stage3_20", "day_emergency_15", "status")
    assert len(ui) == len(tool) == len(report) == 4
    for a, b, c in zip(ui, tool, report):
        assert [a[f] for f in fields] == [b[f] for f in fields] == [c[f] for f in fields]

    # The tool left an unreviewed saved run, which correctly blocks export; the report is
    # rendered from the accepted scenarios directly and so computes from the same inputs.
    html = render_html_report(workspace, [workspace.get(i) for i in workspace.selected], config=config)
    assert f"scenario {scenario.id} revision {scenario.revision}" in html
    assert metrics.input_rainfall["hundred_percent_meaning"] in html
    for row in report:
        if row["day_stage3_20"] is not None:
            assert f"{threshold_day_label(row['day_stage3_20'])}*" in html


def test_default_report_names_the_scenario_it_computed(accepted):
    workspace = accepted
    exported = workspace.exportable()
    first = exported[0]
    html = render_html_report(workspace, exported)
    assert f"{first.id} (revision {first.revision}) - first accepted scenario; not chosen in Review" in html
    assert "Not tied to a specific scenario" not in html


# --------------------------------------------------------------------------------------
# Saved-run compatibility, demand units and depth labels
# --------------------------------------------------------------------------------------

def test_runs_saved_under_the_previous_threshold_rules_are_refused(workspace):
    run = workspace.run_simulation(workspace.selected[0], SimulationSettings())
    old = deepcopy(run)
    old["threshold_version"] = "inclusive-daily-endpoints-with-day-zero-1"
    old["id"] = "sim-" + content_hash({k: v for k, v in old.items() if k != "id"})
    with pytest.raises(ValueError, match="Unsupported simulation version"):
        validate_run(workspace, old)


def test_custom_system_demand_is_not_replaced_by_the_regional_no_pipeline_default():
    """A 12 ac-ft/day custom pool left with the dataclass default requested 554 ac-ft/day
    once pipeline supply was unchecked, about 46 times the entered demand."""
    pool = (WaterSource.scaled_for_capacity("Pool", 8000.0),)
    series = daily([0])
    inherited = WaterSystemConfig("Custom", pool, demand_acft_day=12.0)
    explicit = WaterSystemConfig("Custom", pool, demand_acft_day=12.0, demand_no_pipeline_acft_day=None)
    assert simulate_reservoir_drawdown(series, pipeline_active=False, config=inherited)["demand_acft"].iloc[0] == 554.0
    assert simulate_reservoir_drawdown(series, pipeline_active=False, config=explicit)["demand_acft"].iloc[0] == 12.0


def test_irrigation_depth_is_not_labelled_per_acre():
    takeaway = calculate_crop_water_deficit(daily([0.0] * 30, start="2011-07-01"))["takeaway"]
    assert "in/acre" not in takeaway and "acre-inches per acre" in takeaway
