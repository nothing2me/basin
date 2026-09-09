import numpy as np
import pandas as pd
import pytest
from basin_core.water_system import (
    WaterSource,
    WaterSystemConfig,
    REGION_N_PRESET,
    SMALL_MUNI_PRESET,
    RURAL_FARM_PRESET,
    SYSTEM_PRESETS,
)
from basin_core.analysis import simulate_reservoir_drawdown, simulate_stress_spectrum


def test_water_source_validation():
    with pytest.raises(ValueError, match="name"):
        WaterSource("", 1000.0).validate()
    with pytest.raises(ValueError, match="capacity"):
        WaterSource("Tank", -50.0).validate()
    with pytest.raises(ValueError, match="capacity"):
        WaterSource("Tank", 0.0).validate()
    with pytest.raises(ValueError, match="inflow_base_acft"):
        WaterSource("Tank", 100.0, inflow_base_acft=-1.0).validate()
    with pytest.raises(ValueError, match="evap_summer_acft"):
        WaterSource("Tank", 100.0, evap_summer_acft=-5.0).validate()


def test_water_system_config_validation():
    with pytest.raises(ValueError, match="name"):
        WaterSystemConfig("", (WaterSource("A", 100.0),)).validate()
    with pytest.raises(ValueError, match="at least one"):
        WaterSystemConfig("Empty", ()).validate()
    with pytest.raises(ValueError, match="demand_acft_day"):
        WaterSystemConfig("Sys", (WaterSource("A", 100.0),), demand_acft_day=-10.0).validate()
    with pytest.raises(ValueError, match="demand_no_pipeline_acft_day"):
        WaterSystemConfig("Sys", (WaterSource("A", 100.0),), demand_no_pipeline_acft_day=-10.0).validate()
    with pytest.raises(ValueError, match="stage_bands_pct"):
        WaterSystemConfig("Sys", (WaterSource("A", 100.0),), stage_bands_pct=(1.5, 0.3)).validate()


def test_presets_validity():
    for name, preset in SYSTEM_PRESETS.items():
        preset.validate()
        desc = preset.describe_assumptions()
        assert desc["system_name"] == preset.name
        assert desc["total_capacity_acft"] == preset.total_capacity_acft
        assert len(desc["capacities_acft"]) == len(preset.sources)


def test_single_source_mass_balance():
    # Small farm pond with 1 source
    series = pd.DataFrame({"station": [10.0] * 180}, index=pd.date_range("2024-01-01", periods=180))
    sim = simulate_reservoir_drawdown(series, initial_pct=0.60, conservation_pct=0.10, config=RURAL_FARM_PRESET)

    assert len(sim) == 180
    assert "source_0_acft" in sim.columns
    assert "source_0_pct" in sim.columns
    assert sim["source_0_name"].iloc[0] == "Irrigation Pond"
    np.testing.assert_allclose(
        sim.combined_acft,
        sim.beginning_acft + sim.inflow_acft - sim.evap_acft - sim.served_demand_acft - sim.spill_acft,
        atol=1e-8,
    )
    assert sim.combined_pct.between(0, 100).all()
    assert (sim.balance_error_acft.abs() < 1e-8).all()


def test_three_source_system():
    # Custom 3-reservoir system
    sources = (
        WaterSource("North Lake", 50000.0, inflow_base_acft=10.0, inflow_sensitivity=15.0),
        WaterSource("South Lake", 30000.0, inflow_base_acft=5.0, inflow_sensitivity=10.0),
        WaterSource("East Tank", 10000.0, inflow_base_acft=2.0, inflow_sensitivity=5.0),
    )
    cfg = WaterSystemConfig("Tri-Reservoir District", sources, demand_acft_day=80.0)
    series = pd.DataFrame({"station": [0.0] * 90}, index=pd.date_range("2024-05-01", periods=90))
    sim = simulate_reservoir_drawdown(series, initial_pct=0.75, config=cfg)

    assert sim["combined_acft"].iloc[0] < 90000.0 * 0.75  # Demand + evap draws down
    assert (sim["source_0_acft"] >= 0).all()
    assert (sim["source_1_acft"] >= 0).all()
    assert (sim["source_2_acft"] >= 0).all()
    np.testing.assert_allclose(
        sim.combined_acft,
        sim.beginning_acft + sim.inflow_acft - sim.evap_acft - sim.served_demand_acft - sim.spill_acft,
        atol=1e-8,
    )


def test_custom_stress_spectrum():
    series = pd.DataFrame({"station": [5.0] * 120}, index=pd.date_range("2024-03-01", periods=120))
    spec = simulate_stress_spectrum(series, tiers=(1.0, 0.7, 0.4), initial_pct=0.50, config=SMALL_MUNI_PRESET)

    assert len(spec["summary_table"]) == 3
    assert spec["config"] == SMALL_MUNI_PRESET
    for row in spec["summary_table"]:
        assert "min_pct" in row
        assert "status" in row


def test_smooth_evaporation_and_eac_scaling():
    series = pd.DataFrame({"station": [2.0] * 365}, index=pd.date_range("2024-01-01", periods=365))
    custom_cfg = WaterSystemConfig(
        name="Dynamic EAC District",
        sources=(WaterSource.scaled_for_capacity("Main Lake", 50000.0),),
        demand_acft_day=25.0,
        use_smooth_evap=True,
        use_eac_scaling=True,
    )
    sim = simulate_reservoir_drawdown(series, initial_pct=0.70, config=custom_cfg)
    assert len(sim) == 365
    np.testing.assert_allclose(
        sim.combined_acft,
        sim.beginning_acft + sim.inflow_acft - sim.evap_acft - sim.served_demand_acft - sim.spill_acft,
        atol=1e-8,
    )
    # January evap must be lower than July evap due to smooth seasonal curve
    jan_evap = sim.iloc[15]["evap_acft"]
    jul_evap = sim.iloc[200]["evap_acft"]
    assert jul_evap > jan_evap
