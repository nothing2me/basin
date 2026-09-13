import pytest

from basin_core.assistant import (
    TEMPLATES,
    render_tool_result,
    run_tool_directly,
)
from basin_core.tools import (
    TOOL_FUNCTIONS,
    TOOL_REGISTRY,
    check_concurrence,
    check_export_readiness,
    compare_scenarios,
    describe_cluster,
    describe_scenario,
    explain_ranking,
    find_scenarios_by_year,
    get_data_provenance,
    query_rainfall,
    run_sensitivity,
    summarize_evidence,
    test_reservoir_infrastructure as tool_test_reservoir_infrastructure,
    run_stress_spectrum as tool_run_stress_spectrum,
)
from basin_core.assistant import semantic_query_route


def test_tool_registry_has_thirteen_tools():
    assert len(TOOL_FUNCTIONS) == 13
    assert len(TOOL_REGISTRY) == 13
    for fn in TOOL_FUNCTIONS:
        assert fn.__name__ in TOOL_REGISTRY


def test_describe_scenario(workspace):
    sid = workspace.selected[0]
    data = describe_scenario(workspace, sid)
    assert data["id"] == sid
    assert "duration_days" in data
    assert "deficit_mm" in data
    assert "concurrence_pct" in data
    assert "percentile_pct" in data
    assert "score" in data
    assert "_snapshot" in data

    rendered = render_tool_result("describe_scenario", data)
    assert sid in rendered
    assert str(data["duration_days"]) in rendered
    assert "Station suitability is provisional" in rendered


def test_compare_scenarios(workspace):
    id1, id2 = workspace.selected[0], workspace.selected[1]
    data = compare_scenarios(workspace, id1, id2)
    assert id1 in data["scenarios"]
    assert id2 in data["scenarios"]
    assert "deltas" in data
    assert "deficit_delta_mm" in data["deltas"]

    rendered = render_tool_result("compare_scenarios", data)
    assert id1 in rendered
    assert id2 in rendered
    assert "Differences show measurement deltas" in rendered


def test_explain_ranking(workspace):
    sid = workspace.selected[0]
    data = explain_ranking(workspace, sid)
    assert data["id"] == sid
    assert "score" in data
    assert "position" in data
    assert "components" in data
    assert "weights" in data

    rendered = render_tool_result("explain_ranking", data)
    assert sid in rendered
    assert str(data["score"]) in rendered
    assert "ranking priorities set by the user" in rendered


def test_query_rainfall(workspace):
    station_id = workspace.source.manifest["stations"][0]["id"]
    data = query_rainfall(workspace, station_id, "2011-01-01", "2011-06-30")
    assert data["station_id"] == station_id
    assert data["valid_days"] > 0
    assert data["total_mm"] >= 0
    assert "monthly_totals" in data

    rendered = render_tool_result("query_rainfall", data)
    assert station_id in rendered
    assert str(data["valid_days"]) in rendered
    assert "point observations, not catchment-averaged" in rendered


def test_check_concurrence(workspace):
    sid = workspace.selected[0]
    data = check_concurrence(workspace, sid)
    assert data["id"] == sid
    assert "concurrence_pct" in data
    assert "stations" in data
    assert len(data["stations"]) > 0

    rendered = render_tool_result("check_concurrence", data)
    assert sid in rendered
    assert "75th-percentile rolling deficit" in rendered


def test_run_sensitivity(workspace):
    data = run_sensitivity(workspace, duration=80, severity=20)
    assert data["weights_after"]["duration"] == 80
    assert data["weights_after"]["severity"] == 20
    assert "top_movers" in data

    rendered = render_tool_result("run_sensitivity", data)
    assert "Duration" in rendered
    assert "preview only" in rendered


def test_summarize_evidence(workspace):
    sid = workspace.selected[0]
    data = summarize_evidence(workspace, sid)
    assert data["scenario_id"] == sid
    assert "evidence_count" in data
    assert "conflict_count" in data

    rendered = render_tool_result("summarize_evidence", data)
    assert sid in rendered
    assert "Evidence types and applicability are analyst declarations" in rendered


def test_describe_cluster(workspace):
    data = describe_cluster(workspace, 1)
    assert data["cluster_id"] == 1
    assert "member_count" in data
    assert data["member_count"] > 0
    assert "centroid_percentile" in data

    rendered = render_tool_result("describe_cluster", data)
    assert "Group 0" in rendered or "Drought profile" in rendered
    assert "KMeans groups describe feature patterns" in rendered


def test_check_export_readiness(workspace):
    data = check_export_readiness(workspace)
    assert "ready" in data
    assert "selected_count" in data
    assert "blockers" in data

    rendered = render_tool_result("check_export_readiness", data)
    assert "Export readiness" in rendered
    assert "Export checks internal consistency" in rendered


def test_get_data_provenance(workspace):
    data = get_data_provenance(workspace)
    assert data["source"] == "NOAA NCEI GHCN-Daily"
    assert "snapshot_sha256" in data
    assert data["station_count"] == 3

    rendered = render_tool_result("get_data_provenance", data)
    assert "NOAA NCEI GHCN-Daily" in rendered
    assert "Airport stations are provisional regional proxies" in rendered


def test_find_scenarios_by_year(workspace):
    data = find_scenarios_by_year(workspace, 2011)
    assert data["year"] == 2011
    assert "total_matches" in data
    assert isinstance(data["scenarios"], list)
    rendered = render_tool_result("find_scenarios_by_year", data)
    assert "2011" in rendered
    assert "Historical source dates indicate" in rendered


def test_test_reservoir_infrastructure(workspace):
    data = tool_test_reservoir_infrastructure(workspace, scenario_id=workspace.selected[0], rainfall_reduction_pct=20.0)
    assert data["rainfall_reduction_pct"] == 20.0
    assert "min_pct" in data
    assert "survived_critical_20pct" in data
    assert "scenario_id" in data
    rendered = render_tool_result("test_reservoir_infrastructure", data)
    assert "Reservoir Infrastructure Stress Test" in rendered
    assert "Lowest point reached" in rendered
    assert "Illustrative simulation of **Region N" in rendered


def test_run_stress_spectrum(workspace):
    data = tool_run_stress_spectrum(workspace, scenario_id=workspace.selected[0])
    assert "tiers" in data
    assert len(data["tiers"]) == 4
    rendered = render_tool_result("run_stress_spectrum", data)
    assert "Reservoir Stress Spectrum" in rendered
    assert "Evaluated tier outcomes" in rendered or "Tipping Point Analysis" in rendered
    assert "Illustrative simulation of **Region N" in rendered


def test_all_templates_render_and_have_disclaimers(workspace):
    assert len(TEMPLATES) == 13
    sid = workspace.selected[0]
    sample_calls = [
        ("describe_scenario", describe_scenario(workspace, sid)),
        ("compare_scenarios", compare_scenarios(workspace, sid, workspace.selected[1])),
        ("explain_ranking", explain_ranking(workspace, sid)),
        ("query_rainfall", query_rainfall(workspace, workspace.source.manifest["stations"][0]["id"], "2015-01-01", "2015-03-31")),
        ("check_concurrence", check_concurrence(workspace, sid)),
        ("run_sensitivity", run_sensitivity(workspace, duration=90)),
        ("summarize_evidence", summarize_evidence(workspace, sid)),
        ("describe_cluster", describe_cluster(workspace, min(s.cluster for s in workspace.scenarios))),
        ("check_export_readiness", check_export_readiness(workspace)),
        ("get_data_provenance", get_data_provenance(workspace)),
        ("find_scenarios_by_year", find_scenarios_by_year(workspace, 2011)),
        ("test_reservoir_infrastructure", tool_test_reservoir_infrastructure(workspace, scenario_id=workspace.selected[0], rainfall_reduction_pct=20.0)),
        ("run_stress_spectrum", tool_run_stress_spectrum(workspace, scenario_id=workspace.selected[0])),
    ]
    for name, data in sample_calls:
        rendered = render_tool_result(name, data)
        assert len(rendered) > 50, f"Template {name} produced empty or short output"
        assert "⚠️" in rendered or "Source:" in rendered, f"Template {name} missing verification disclaimer"


def test_semantic_query_route(workspace):
    r1 = semantic_query_route(workspace, "Is this ready to export?")
    assert "Export readiness" in r1

    # Without IDs or values the router asks; it no longer answers for the first shortlisted
    # scenarios or previews an unchanged weight set.
    first, second = workspace.selected[:2]
    r2 = semantic_query_route(workspace, "Compare scenarios")
    assert "Please clarify" in r2 and "Scenario comparison" not in r2
    assert "Scenario comparison" in semantic_query_route(workspace, f"Compare scenarios {first} and {second}")

    r3 = semantic_query_route(workspace, "What is the station stress?")
    assert "Please clarify" in r3 and "Station stress analysis" not in r3
    assert "Station stress analysis" in semantic_query_route(workspace, f"What is the station stress in {first}?")

    r4 = semantic_query_route(workspace, "Sensitivity of weights")
    assert "Please clarify" in r4 and "Sensitivity test" not in r4
    assert "Sensitivity test" in semantic_query_route(workspace, "Sensitivity of the duration weight to 40")

    r5 = semantic_query_route(workspace, "Where does this data come from?")
    assert "NOAA NCEI GHCN-Daily" in r5

    r6 = semantic_query_route(workspace, "Can our infrastructure survive a 2011-style event if rainfall is even 20% lower?")
    assert "2011" in r6
    assert "Multiple scenarios match" in r6 or "Reservoir Infrastructure Stress Test" in r6

    r7 = semantic_query_route(workspace, "Find scenarios in 2011")
    assert "2011" in r7

    r8 = semantic_query_route(workspace, "Run stress spectrum sweep on 2011")
    assert "2011" in r8
    assert "Multiple scenarios match" in r8 or "Reservoir Stress Spectrum" in r8


def test_run_tool_directly(workspace):
    out = run_tool_directly(workspace, "describe_cluster", {"cluster_id": 1})
    assert "Group 1" in out


def test_invalid_tool_inputs(workspace):
    with pytest.raises(ValueError):
        describe_scenario(workspace, "NON_EXISTENT_ID")

    with pytest.raises(ValueError):
        query_rainfall(workspace, "INVALID_STATION", "2020-01-01", "2020-02-01")

    with pytest.raises(ValueError):
        run_sensitivity(workspace, severity=0, duration=0, concurrence=0, season=0)
