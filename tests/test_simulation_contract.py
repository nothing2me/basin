from copy import deepcopy
import io
import json
import zipfile

import pandas as pd
import pytest

from basin_core.analysis import simulate_stress_spectrum, threshold_text
from basin_core.exporter import export_bundle, verify_bundle, generate_brief
from basin_core.simulation import SimulationSettings, content_hash, is_current, resolve_scenario, validate_run
from basin_core.tools import run_stress_spectrum
from basin_core.workspace import Workspace


@pytest.mark.parametrize("value", [0, .5, 1, 15, 48, 100])
def test_public_percent_units(value):
    settings = SimulationSettings.from_percent(initial_storage_percent=value, conservation_percent=value)
    assert settings.initial_storage_fraction == value / 100
    assert settings.conservation_fraction == value / 100


@pytest.mark.parametrize("value", [True, -1, 101, float("nan"), float("inf"), "48"])
def test_invalid_percent_is_not_guessed_or_clamped(value):
    with pytest.raises(ValueError):
        SimulationSettings.from_percent(initial_storage_percent=value)


def test_rounding_does_not_determine_threshold(monkeypatch):
    frame = pd.DataFrame({"day": [1], "combined_pct": [20.04], "combined_acft": [184347.96]})
    monkeypatch.setattr("basin_core.analysis.simulate_reservoir_drawdown", lambda *a, **k: frame)
    row = simulate_stress_spectrum(pd.DataFrame({"s": [0]}), tiers=(1.,))["summary_table"][0]
    assert row["min_pct"] == 20.0
    assert row["day_stage3_20"] is None
    assert row["survived_critical_20pct"] is True
    for value, expected in [(20.0, 1), (19.96, 1), (20.04, None)]:
        frame["combined_pct"] = value
        row = simulate_stress_spectrum(pd.DataFrame({"s": [0]}), tiers=(1.,))["summary_table"][0]
        assert row["day_stage3_20"] == expected


def test_initial_below_threshold_then_recovery():
    series = pd.DataFrame({"s": [1000., 1000.]}, index=pd.date_range("2001-01-01", periods=2))
    row = simulate_stress_spectrum(series, initial_pct=.2, tiers=(1.,))["summary_table"][0]
    assert row["min_pct"] > 20
    assert row["day_stage3_20"] == 0
    assert not row["survived_critical_20pct"]
    assert "start" in threshold_text(0)


def test_exact_scenario_resolution(workspace):
    scenario = workspace.get(workspace.selected[0])
    assert resolve_scenario(workspace, scenario.id, revision=scenario.revision) is scenario
    with pytest.raises(ValueError, match="No scenario"):
        resolve_scenario(workspace, year=1800)
    with pytest.raises(ValueError, match="revision changed"):
        resolve_scenario(workspace, scenario.id, revision=999)
    with pytest.raises(ValueError, match="Choose an exact"):
        resolve_scenario(workspace)
    year = int(scenario.provenance["source_start"][:4])
    workspace.scenarios = [scenario, deepcopy(scenario)]
    workspace.scenarios[1].id = "OTHER"
    with pytest.raises(ValueError, match="Multiple scenarios"):
        resolve_scenario(workspace, year=year)
    workspace.scenarios = [scenario]
    assert resolve_scenario(workspace, year=year) is scenario
    with pytest.raises(ValueError, match="disagree"):
        resolve_scenario(workspace, scenario.id, year=year + 1)


def test_baselines_and_saved_tool_result(workspace):
    scenario = workspace.get(workspace.selected[0])
    workspace.edit(scenario.id, "Additional rainfall stress", factor=.6)
    selected = workspace.run_simulation(scenario.id, SimulationSettings())
    observed = workspace.run_simulation(scenario.id, SimulationSettings(baseline_kind="observed_window"))
    assert selected["baseline"]["values"] == scenario.series.to_numpy().tolist()
    original = workspace.reference.daily.reindex(scenario.series.index)[list(scenario.series.columns)]
    assert observed["baseline"]["values"] == original.to_numpy().tolist()
    assert selected["id"] != observed["id"]
    validate_run(workspace, selected)
    validate_run(workspace, observed)
    tool = run_stress_spectrum(workspace, scenario_id=scenario.id, initial_storage_pct=48, conservation_pct=.5)
    active = workspace.active_simulation(scenario.id)
    assert tool["summary_table"] == active["results"]["summary_table"]
    assert active["settings"]["conservation_fraction"] == .005
    assert "Historical" not in tool["summary_table"][0]["tier_label"]


def accept_rainfall(workspace):
    for sid in workspace.selected:
        workspace.get(sid).review(True, "Rainfall checked")


def test_reopen_review_export_and_replay(workspace, tmp_path):
    sid = workspace.selected[0]
    run = workspace.run_simulation(sid, SimulationSettings.from_percent(initial_storage_percent=35, conservation_percent=1, pipeline_active=False))
    accept_rainfall(workspace)
    with pytest.raises(ValueError, match="simulation"):
        export_bundle(workspace)
    workspace.review_simulation(run["id"], "Inputs inspected; illustrative limitations understood")
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    assert restored.active_simulation(sid) == run
    assert restored.simulation_reviews == workspace.simulation_reviews
    payload = export_bundle(restored)
    assert verify_bundle(payload)["simulations_replayed"] == 1
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        audit = json.loads(archive.read("audit.json"))
        assert audit["schema_version"] == "2.2"
        assert audit["simulation_runs"][0] == run
    brief = generate_brief(restored, restored.exportable())
    assert "Initial storage 35%; conservation 1%; pipeline available: False" in brief


def test_settings_and_input_changes_require_new_review(workspace, tmp_path):
    sid = workspace.selected[0]
    run = workspace.run_simulation(sid, SimulationSettings())
    workspace.review_simulation(run["id"], "Original settings reviewed")
    accept_rainfall(workspace)
    changed = workspace.run_simulation(sid, SimulationSettings(conservation_fraction=.15))
    assert changed["id"] != run["id"]
    with pytest.raises(ValueError, match="simulation"):
        workspace.exportable()
    workspace.edit(sid, "Changed rainfall", factor=.8)
    assert not is_current(workspace, changed)
    with pytest.raises(ValueError, match="stale"):
        workspace.review_simulation(changed["id"], "Cannot review stale inputs")
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    assert len(restored.simulation_runs) == 2
    assert not is_current(restored, restored.active_simulation(sid))


def test_replay_detects_changed_results_even_with_rehashed_record(workspace):
    run = workspace.run_simulation(workspace.selected[0], SimulationSettings())
    bad = deepcopy(run)
    bad["results"]["summary_table"][0]["day_stage3_20"] = 777
    bad["id"] = "sim-" + content_hash({k: v for k, v in bad.items() if k != "id"})
    with pytest.raises(ValueError, match="Simulation replay"):
        validate_run(workspace, bad)


def test_batch_review_is_atomic_and_version_bound(workspace):
    first, second = workspace.selected[:2]
    tokens = {sid: workspace.review_token(sid) for sid in (first, second)}
    workspace.edit(second, "Changed after review table opened", factor=.9)
    with pytest.raises(ValueError, match="changed"):
        workspace.accept_reviewed(tokens, "Reviewed")
    assert workspace.get(first).status == "unreviewed"
    workspace.accept_reviewed({first: workspace.review_token(first)}, "Checked first only")
    assert workspace.get(first).status == "accepted"
    assert workspace.get(second).status == "unreviewed"
    workspace.get(second).review(False, "Unsuitable")
    with pytest.raises(ValueError, match="rejected"):
        workspace.accept_reviewed({second: workspace.review_token(second)}, "Cannot override rejection")


def test_evidence_change_invalidates_approvals(workspace, tmp_path):
    sid = workspace.selected[0]
    run = workspace.run_simulation(sid, SimulationSettings())
    workspace.review_simulation(run["id"], "Reviewed")
    accept_rainfall(workspace)
    left, right = [e["id"] for e in workspace.evidence[:2]]
    workspace.add_conflict(left, right, "Suitability unresolved", "Different spatial support")
    assert workspace.get(sid).status == "unreviewed"
    assert not is_current(workspace, run)
    Workspace.load(workspace.source, workspace.save(tmp_path))


def test_custom_consent_still_required_with_simulations(workspace):
    sid = workspace.selected[0]
    workspace.save_custom_upload(b"date,precipitation\n2024-01-01,1\n", reviewed=True,
        station="Local", location="Example", unit="mm", provider="Example", observation_basis="Daily",
        reference_station="USW00012924", relationship="regional_proxy", daily_confirmed=True,
        rationale="Suitability remains uncertain", scenario_ids=[sid])
    run = workspace.run_simulation(sid, SimulationSettings())
    workspace.review_simulation(run["id"], "Reviewed comparison limitations")
    accept_rainfall(workspace)
    with pytest.raises(ValueError, match="consent"):
        export_bundle(workspace)
    report = verify_bundle(export_bundle(workspace, include_custom=True))
    assert report["simulations_replayed"] == report["custom_comparisons_replayed"] == 1


def test_conservation_delay_is_bounded_by_both_crossings(workspace):
    run = workspace.run_simulation(workspace.selected[0], SimulationSettings(conservation_fraction=.15))
    for row in run["results"]["conservation_comparison"]:
        before, after = row["no_conservation_day_20"], row["chosen_conservation_day_20"]
        assert row["delay_days"] == (after - before if before is not None and after is not None else None)
    assert set(run["results"]["no_conservation_trajectories"]) == set(run["results"]["trajectories"])
    validate_run(workspace, run)


def test_fallback_routes_explicit_units_or_asks_for_clarification(workspace):
    from basin_ui import fallback_query_route
    sid = workspace.selected[0]
    reply = fallback_query_route(workspace, f"Run spectrum on {sid} with 0.5% conservation and 35% initial storage and no pipeline")
    assert "Reservoir Stress Spectrum" in reply
    settings = workspace.active_simulation(sid)["settings"]
    assert settings["initial_storage_fraction"] == .35
    assert settings["conservation_fraction"] == .005
    assert settings["pipeline_active"] is False
    before = len(workspace.simulation_runs)
    reply = fallback_query_route(workspace, f"Run spectrum on {sid} with 25%")
    assert "Label each percentage" in reply
    assert len(workspace.simulation_runs) == before


def test_pre_banner_packet_layout_still_replays(workspace):
    import hashlib
    accept_rainfall(workspace)
    payload = export_bundle(workspace)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    summary = pd.read_csv(io.BytesIO(files["shortlist.csv"]), float_precision="round_trip")
    files["shortlist.csv"] = summary.drop(columns="modeling_scope").to_csv(index=False).encode()
    files["Hydrologist_Handoff_Brief.md"] = files["Hydrologist_Handoff_Brief.md"].split(b"\n", 2)[2]
    manifest = json.loads(files["bundle_manifest.json"])
    assert manifest["schema_version"] == "2.0"
    for name in manifest["files"]:
        manifest["files"][name] = hashlib.sha256(files[name]).hexdigest()
    files["bundle_manifest.json"] = json.dumps(manifest).encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    assert verify_bundle(output.getvalue())["verified"]


def test_report_projects_the_reviewed_saved_result_without_report_recalculation(workspace, monkeypatch):
    from basin_core.pdf_report import build_fallback_pdf, render_html_report

    run = workspace.run_simulation(
        workspace.selected[0],
        SimulationSettings.from_percent(initial_storage_percent=35, conservation_percent=.5, pipeline_active=False),
    )
    workspace.review_simulation(run["id"], "Reviewed saved inputs and illustrative limits")
    accept_rainfall(workspace)

    def independent_report_calculation_is_forbidden(*args, **kwargs):
        raise AssertionError("saved reports must not calculate a replacement experiment")

    monkeypatch.setattr("basin_core.pdf_report.simulate_stress_spectrum", independent_report_calculation_is_forbidden)
    html = render_html_report(workspace, workspace.exportable())
    assert run["id"] in html
    assert "35% of combined capacity" in html
    assert "0.5% demand reduction" in html
    assert "Assumed unavailable" in html
    assert "Simulation unavailable" not in html
    pdf = build_fallback_pdf(workspace, workspace.exportable())
    assert b"35% of combined capacity" in pdf
    assert b"0.5% demand reduction" in pdf
    assert b"Saved reviewed run" in pdf
