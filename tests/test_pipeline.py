import io
import json
import socket
import zipfile

import numpy as np
import pandas as pd
import pytest

from basin_core.analysis import WeightedSumRanking, shortlist, COMMUNITY_PRESETS, simulate_reservoir_drawdown
from basin_core.data import CachedSource
from basin_core.engine import Reference, ScenarioGenerator, ScenarioParams
from basin_core.exporter import export_bundle, verify_bundle
from basin_core.workspace import Workspace
from scripts.fetch_noaa import parse_dly


def test_parser_flags_units_and_missing():
    cells = ["00123   ", "-9999   ", "00010 X ", "00000P  ", "00000T  "] + ["00000   "] * 26
    raw = ("USW00012924" + "2001" + "01" + "PRCP" + "".join(cells)).encode()
    rows = parse_dly(raw, "USW00012924")
    assert rows.precip_mm.iloc[0] == 12.3
    assert rows.precip_mm.iloc[1:4].isna().all()
    assert rows.precip_mm.iloc[4] == 0


def test_corrupt_snapshot(source):
    with pytest.raises(ValueError, match="checksum"):
        CachedSource(raw=source.raw + b"x", manifest=source.manifest)


@pytest.mark.parametrize("overrides", [{"durations": ()}, {"months": (13,)}, {"retention_min": -1}, {"retention_max": float("nan")}, {"seed": -1}, {"candidates": 1001}, {"stations": ()}])
def test_parameters_rejected(source, overrides):
    params = {"stations": tuple(source.daily.columns), **overrides}
    with pytest.raises(ValueError):
        ScenarioGenerator(source, ScenarioParams(**params))


def test_generation_determinism_and_synchronized_source(source):
    params = ScenarioParams(tuple(source.daily.columns), candidates=20)
    a, _ = ScenarioGenerator(source, params).generate()
    b, _ = ScenarioGenerator(source, params).generate()
    assert [s.digest() for s in a] == [s.digest() for s in b]
    for s in a:
        p = s.provenance
        observed = source.select(list(params.stations)).loc[p["source_start"]:p["source_end"]]
        np.testing.assert_allclose(s.series, observed * pd.Series(p["retention_by_station"]))
        assert not s.series.isna().any().any()


def test_missing_window_excluded(source):
    ref = Reference(source, list(source.daily.columns))
    ref.daily.loc["2001-01-15", ref.stations[0]] = np.nan
    assert "2001-01-01" not in [w["start"] for w in ref.windows(1, 90)]


def test_feature_boundaries_and_fixed_reference(source):
    ref = Reference(source, list(source.daily.columns))
    dates = pd.date_range("2001-07-01", periods=90)
    dry = pd.DataFrame(0.0, index=dates, columns=ref.stations)
    features = ref.features(dry)
    assert features["eligible_concurrence_days"] == 61
    assert features["max_dry_days"] == 90
    assert features["high_priority_season_fraction"] == 1
    expected_deficit = ref.expected(dates).sum(axis=0).mean()
    assert features["deficit_mm"] == pytest.approx(expected_deficit)
    assert features["historical_percentile"] == 1
    wet = dry + 1000
    assert ref.features(wet)["deficit_mm"] == 0
    assert ref.features(wet)["concurrence"] == 0
    dry.iloc[4, 0] = np.nan
    with pytest.raises(ValueError, match="complete"):
        ref.features(dry)


def test_weights_components_and_references(workspace):
    s = workspace.scenarios[0]
    before = s.features.copy()
    WeightedSumRanking().apply(workspace.scenarios, {"severity": 0, "duration": 1, "concurrence": 0, "season": 0})
    assert s.score == pytest.approx(100 * s.features["duration_days"] / 365)
    assert s.score == pytest.approx(sum(s.components.values()))
    assert s.features == before
    with pytest.raises(ValueError):
        WeightedSumRanking().apply(workspace.scenarios, dict.fromkeys(workspace.weights, 0))


def test_diverse_selection_representatives(workspace):
    selected = [workspace.get(i) for i in shortlist(workspace.scenarios, 3)]
    assert len({s.cluster for s in selected}) == workspace.clustering["groups"]
    for s in selected:
        assert s.score == max(x.score for x in workspace.scenarios if x.cluster == s.cluster)


def test_review_revision_replay_privacy_and_rejection(workspace):
    with pytest.raises(ValueError, match="Review"):
        export_bundle(workspace)
    s = workspace.get(workspace.selected[0])
    old = s.series.copy()
    s.review(True, "PRIVATE-SENTINEL")
    workspace.edit(s.id, "PRIVATE-SENTINEL", factor=0.5)
    np.testing.assert_allclose(s.series, old * 0.5)
    assert s.revision == 2 and s.status == "unreviewed" and s.approved_revision is None
    workspace.notes = "PRIVATE-SENTINEL"
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "PRIVATE-SENTINEL")
    rejected = workspace.get(workspace.selected[-1])
    rejected.review(False, "PRIVATE-SENTINEL")
    payload = export_bundle(workspace)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert not any(b"PRIVATE-SENTINEL" in archive.read(n) for n in archive.namelist())
        assert rejected.id.encode() not in archive.read("daily_rainfall.csv")
        assert rejected.id.encode() in archive.read("audit.json")
        assert "Hydrologist_Handoff_Brief.md" in archive.namelist()
        brief = archive.read("Hydrologist_Handoff_Brief.md").decode("utf-8")
        assert "Engineering Specification" in brief
        assert "Net Deficit (in)" in brief
        assert "Texas Water Availability Models" in brief
        assert "Community Priority Configuration" in brief
    assert verify_bundle(payload)["scenarios_replayed"] == 2
    with zipfile.ZipFile(io.BytesIO(export_bundle(workspace, True))) as archive:
        assert b"PRIVATE-SENTINEL" in archive.read("audit.json")


def test_cluster_profiling_and_community_presets(workspace):
    assert "group_profiles" in workspace.clustering
    for cluster_id, profile_name in workspace.clustering["group_profiles"].items():
        assert isinstance(profile_name, str) and len(profile_name) > 0
    for s in workspace.scenarios:
        assert hasattr(s, "cluster_name")
        assert s.cluster_name == workspace.clustering["group_profiles"][s.cluster]
    
    assert "Rural Water District (Nueces County WCID #3)" in COMMUNITY_PRESETS
    rural = COMMUNITY_PRESETS["Rural Water District (Nueces County WCID #3)"]
    assert rural["season"] == 50
    workspace.rerank(rural)
    assert workspace.weights == rural


def test_reservoir_drawdown_simulation(workspace):
    s = workspace.scenarios[0]
    sim = simulate_reservoir_drawdown(s.series, initial_pct=0.48)
    assert len(sim) == len(s.series)
    assert "combined_pct" in sim.columns
    assert "stage" in sim.columns
    assert sim.iloc[0]["combined_pct"] == pytest.approx(47.9, abs=0.2)
    # Storage should be within valid physical limits
    assert (sim["lcc_acft"] >= 0).all() and (sim["ccr_acft"] >= 0).all()
    assert (sim["combined_pct"] <= 100).all()


def test_custom_replacement_and_atomic_invalid_edit(workspace):
    s = workspace.get(workspace.selected[0])
    digest = s.digest()
    invalid = s.series.copy()
    invalid.iloc[0, 0] = -1
    with pytest.raises(ValueError):
        workspace.edit(s.id, "bad replacement", replacement=invalid)
    assert s.digest() == digest and s.revision == 1
    replacement = s.series * 0.9
    workspace.edit(s.id, "custom replacement", replacement=replacement)
    assert s.revision == 2 and s.status == "unreviewed"
    for identifier in workspace.selected:
        workspace.get(identifier).review(True)
    assert verify_bundle(export_bundle(workspace))["verified"]


def test_cannot_mutate_approved_rainfall(workspace):
    for identifier in workspace.selected:
        workspace.get(identifier).review(True)
    workspace.get(workspace.selected[0]).series.iloc[0, 0] += 1
    with pytest.raises(ValueError, match="changed"):
        export_bundle(workspace)


def test_roundtrip_saved_session(workspace, tmp_path):
    s = workspace.get(workspace.selected[0])
    s.review(True, "private local note")
    workspace.notes = "Provider note"
    path = workspace.save(tmp_path)
    restored = Workspace.load(workspace.source, path)
    assert restored.selected == workspace.selected
    assert restored.notes == workspace.notes
    assert restored.get(s.id).history == s.history
    assert restored.get(s.id).digest() == s.digest()


def test_offline_pipeline(source, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected network connection")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    w = Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=10), size=3)
    for identifier in w.selected:
        w.get(identifier).review(True)
    assert verify_bundle(export_bundle(w))["verified"]


def test_reservoir_drawdown_climate_and_datacenter(workspace):
    from basin_core.analysis import simulate_reservoir_drawdown
    series = workspace.get(workspace.selected[0]).series

    base_sim = simulate_reservoir_drawdown(series, initial_pct=0.48)
    assert not base_sim.empty
    assert "combined_pct" in base_sim.columns
    base_end_pct = base_sim.iloc[-1]["combined_pct"]

    warm_sim = simulate_reservoir_drawdown(series, initial_pct=0.48, temp_anomaly_c=2.0)
    warm_end_pct = warm_sim.iloc[-1]["combined_pct"]
    assert warm_end_pct < base_end_pct
    assert warm_sim.iloc[0]["evap_acft"] > base_sim.iloc[0]["evap_acft"]

    dc_sim = simulate_reservoir_drawdown(series, initial_pct=0.48, data_center_mgd=10.0)
    dc_end_pct = dc_sim.iloc[-1]["combined_pct"]
    assert dc_end_pct < base_end_pct
    assert dc_sim.iloc[0]["datacenter_acft"] > 0

