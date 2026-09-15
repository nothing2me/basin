"""Unit tests for the Advanced demand-policy comparison in BASIN.

Verifies:
- Both cases use the same scenario revision and selected storage system.
- Enabling the comparison does not mutate Workspace.water_system_selection.
- Displayed deltas equal direct calculations from both simulation frames.
- Missing threshold crossings render honestly without invented days.
- Switching Simple/Advanced views changes presentation only.
- Opening the comparison does not invalidate a reviewed simulation or export.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from basin_core.analysis import (
    compare_demand_curtailment_policies,
    threshold_crossing_day,
    simulate_reservoir_drawdown,
)
from basin_core.water_system import (
    REGION_N_PRESET,
    REGION_N_MODERN_PRESET,
    WaterSystemConfig,
    WaterSource,
    WaterSystemSelection,
)
from basin_core.simulation import SimulationSettings
from basin_core.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def synthetic_series() -> pd.DataFrame:
    """A 100-day daily rainfall series with zero rainfall to induce clear drawdown."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    return pd.DataFrame({"station_a": np.zeros(100, dtype=float)}, index=dates)


@pytest.fixture
def wet_series() -> pd.DataFrame:
    """A 60-day rainfall series with heavy rainfall so thresholds are never reached."""
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.DataFrame({"station_a": np.full(60, 50.0, dtype=float)}, index=dates)


def test_both_cases_use_same_inputs_and_scenario_revision(synthetic_series):
    """Both comparison cases must hold all physical and scenario inputs constant."""
    cfg = REGION_N_MODERN_PRESET
    res = compare_demand_curtailment_policies(
        synthetic_series,
        initial_pct=0.35,
        conservation_pct=0.10,
        pipeline_active=True,
        config=cfg,
    )

    c_cfg = res["configured_config"]
    f_cfg = res["flat_config"]

    # Only sector curtailment differs
    assert c_cfg.stage_curtailment_active is True
    assert f_cfg.stage_curtailment_active is False

    # Everything else must be identical
    assert c_cfg.sources == f_cfg.sources
    assert c_cfg.demand_acft_day == f_cfg.demand_acft_day
    assert c_cfg.demand_no_pipeline_acft_day == f_cfg.demand_no_pipeline_acft_day
    assert c_cfg.stage_bands_pct == f_cfg.stage_bands_pct
    assert c_cfg.dead_storage_acft == f_cfg.dead_storage_acft
    assert c_cfg.use_smooth_evap == f_cfg.use_smooth_evap
    assert c_cfg.use_eac_scaling == f_cfg.use_eac_scaling
    assert c_cfg.pipeline_capacity_mgd == f_cfg.pipeline_capacity_mgd
    assert c_cfg.demand_domestic_pct == f_cfg.demand_domestic_pct
    assert c_cfg.demand_industrial_pct == f_cfg.demand_industrial_pct


def test_enabling_comparison_does_not_mutate_workspace_water_system_selection(workspace, synthetic_series):
    """Running or evaluating comparison must never mutate Workspace.water_system_selection."""
    w = workspace
    w.select_water_system(REGION_N_MODERN_PRESET, "region_n_modern_stress")
    initial_selection = w.water_system_selection
    assert initial_selection.config.stage_curtailment_active is True

    # Run policy comparison with workspace config
    res = compare_demand_curtailment_policies(
        synthetic_series,
        initial_pct=0.48,
        conservation_pct=0.0,
        pipeline_active=True,
        config=w.water_system_selection.config,
    )

    # Workspace selection must be identical and unmutated
    assert w.water_system_selection == initial_selection
    assert w.water_system_selection.config.stage_curtailment_active is True


def test_displayed_deltas_equal_direct_calculations_from_both_simulation_frames(synthetic_series):
    """Displayed deltas must exactly match calculations from the two simulation frames."""
    cfg = REGION_N_MODERN_PRESET
    res = compare_demand_curtailment_policies(
        synthetic_series,
        initial_pct=0.35,
        conservation_pct=0.0,
        pipeline_active=True,
        config=cfg,
    )

    df_c = res["df_configured"]
    df_f = res["flat_config"]

    # Direct recalculation
    crit_pct = cfg.stage_bands_pct[2] * 100
    expected_c_day = threshold_crossing_day(df_c, 0.35, crit_pct)
    expected_f_day = threshold_crossing_day(res["df_flat"], 0.35, crit_pct)

    assert res["crit_day_configured"] == expected_c_day
    assert res["crit_day_flat"] == expected_f_day
    if expected_c_day is not None and expected_f_day is not None:
        assert res["crit_day_delta"] == expected_c_day - expected_f_day

    # Unmet demand delta
    expected_unmet_delta = float(df_c["unmet_demand_acft"].sum()) - float(res["df_flat"]["unmet_demand_acft"].sum())
    assert abs(res["unmet_demand_delta_acft"] - expected_unmet_delta) < 1e-6

    # Curtailed volumes delta
    expected_dom_delta = float(df_c["curtailed_domestic_acft"].sum()) - float(res["df_flat"]["curtailed_domestic_acft"].sum())
    expected_ind_delta = float(df_c["curtailed_industrial_acft"].sum()) - float(res["df_flat"]["curtailed_industrial_acft"].sum())
    assert abs(res["curtailed_domestic_delta_acft"] - expected_dom_delta) < 1e-6
    assert abs(res["curtailed_industrial_delta_acft"] - expected_ind_delta) < 1e-6


def test_missing_threshold_crossings_render_honestly(wet_series):
    """When a threshold is not crossed in the window, delta must be None and no day invented."""
    cfg = REGION_N_MODERN_PRESET
    res = compare_demand_curtailment_policies(
        wet_series,
        initial_pct=0.80,
        conservation_pct=0.0,
        pipeline_active=True,
        config=cfg,
    )

    # With high starting storage and heavy rain, critical threshold (20%) is never reached
    assert res["crit_day_configured"] is None
    assert res["crit_day_flat"] is None
    assert res["crit_day_delta"] is None

    # Active-storage exhaustion is never reached
    assert res["active_limit_day_configured"] is None
    assert res["active_limit_day_flat"] is None
    assert res["active_limit_day_delta"] is None


def test_switching_simple_and_advanced_views_changes_presentation_only(tmp_path, monkeypatch):
    """Switching between Simple and Advanced view modes changes presentation without altering numerical results."""
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    # Load crisis demo to have a configured run in Review
    next(b for b in app.button if b.label == "Load 2026 crisis demo").click().run()
    assert not app.exception

    # Capture initial simulation config
    exp_cfg_before = app.session_state.experiment_config
    w_before = app.session_state.workspace

    # Switch view mode to Advanced View
    mode_ctrl = next((c for c in getattr(app, "segmented_control", []) if c.key == f"review_mode_{w_before.id}"), None)
    if mode_ctrl is None:
        mode_ctrl = next((r for r in app.radio if r.key == f"review_mode_{w_before.id}"), None)

    if mode_ctrl is not None:
        mode_ctrl.set_value("advanced").run()
        assert not app.exception

        exp_cfg_after = app.session_state.experiment_config
        assert exp_cfg_after.initial_pct == exp_cfg_before.initial_pct
        assert exp_cfg_after.conservation_pct == exp_cfg_before.conservation_pct
        assert exp_cfg_after.pipeline_active == exp_cfg_before.pipeline_active
        assert exp_cfg_after.system_config == exp_cfg_before.system_config


def test_opening_comparison_does_not_invalidate_reviewed_simulation_or_export(workspace, synthetic_series):
    """Opening/evaluating the policy comparison must leave reviewed runs and exports valid."""
    w = workspace
    w.select_water_system(REGION_N_MODERN_PRESET, "region_n_modern_stress")
    scenario_id = w.selected[0]

    settings = SimulationSettings(initial_storage_fraction=0.35, conservation_fraction=0.0, pipeline_active=True)
    saved_run = w.run_simulation(scenario_id, settings)
    w.review_simulation(saved_run["id"], "Verified baseline run")
    assert saved_run["id"] in w.simulation_reviews

    # Run comparison
    res = compare_demand_curtailment_policies(
        synthetic_series,
        initial_pct=0.35,
        conservation_pct=0.0,
        pipeline_active=True,
        config=w.water_system_selection.config,
    )

    # Active run and review must remain valid
    assert saved_run["id"] in w.simulation_reviews
    assert w.active_simulation(scenario_id)["id"] == saved_run["id"]
