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


def test_dead_storage_and_day_zero_behavior():
    cfg = WaterSystemConfig(
        name="Dead Storage Test",
        sources=(WaterSource("Reservoir", 10000.0, inflow_base_acft=0.0, inflow_sensitivity=0.0, evap_summer_acft=0.0, evap_winter_acft=0.0),),
        demand_acft_day=100.0,
        dead_storage_acft=2000.0,
    )
    # Start at 2200 ac-ft (22%) with 0 rain
    series = pd.DataFrame({"station": [0.0] * 5}, index=pd.date_range("2024-01-01", periods=5))
    sim = simulate_reservoir_drawdown(series, initial_pct=0.22, config=cfg)
    # Day 1: 2200 -> serves 100 -> 2100 (active=100)
    # Day 2: 2100 -> serves 100 -> 2000 (active=0)
    # Day 3: 2000 -> serves 0 (active=0) -> unmet=100 -> Day Zero!
    # Day 4: 2000 -> serves 0 -> unmet=100 -> Day Zero!
    assert sim.iloc[0]["combined_acft"] == 2100.0
    assert sim.iloc[1]["combined_acft"] == 2000.0
    assert sim.iloc[2]["combined_acft"] == 2000.0
    assert sim.iloc[2]["served_demand_acft"] == 0.0
    assert sim.iloc[2]["unmet_demand_acft"] == 100.0
    assert bool(sim.iloc[2]["is_day_zero"]) is True
    assert (sim["combined_acft"] >= 2000.0).all()
    np.testing.assert_allclose(sim.balance_error_acft, 0.0, atol=1e-8)


def test_multi_sector_hierarchical_curtailment():
    cfg = WaterSystemConfig(
        name="Sector Curtailment System",
        sources=(WaterSource("Pool", 10000.0, inflow_base_acft=0.0, inflow_sensitivity=0.0, evap_summer_acft=0.0, evap_winter_acft=0.0),),
        demand_acft_day=100.0,
        demand_domestic_pct=40.0,
        demand_industrial_pct=50.0,
        demand_outdoor_pct=10.0,
        stage_curtailment_active=True,
        dead_storage_acft=500.0,
    )
    series = pd.DataFrame({"station": [0.0] * 4}, index=pd.date_range("2024-01-01", periods=4))
    # Test at 35% (Stage 1: outdoor cut 15%)
    sim1 = simulate_reservoir_drawdown(series.iloc[:1], initial_pct=0.35, config=cfg)
    assert sim1.iloc[0]["curtailed_outdoor_acft"] == pytest.approx(1.5, abs=1e-3)
    assert sim1.iloc[0]["curtailed_domestic_acft"] == 0.0
    assert sim1.iloc[0]["curtailed_industrial_acft"] == 0.0

    # Test at 15% (Stage 3: outdoor 100% cut, domestic 10% cut)
    sim3 = simulate_reservoir_drawdown(series.iloc[:1], initial_pct=0.15, config=cfg)
    assert sim3.iloc[0]["curtailed_outdoor_acft"] == pytest.approx(10.0, abs=1e-3)
    assert sim3.iloc[0]["curtailed_domestic_acft"] == pytest.approx(4.0, abs=1e-3)
    assert sim3.iloc[0]["curtailed_industrial_acft"] == 0.0  # protected

    # Test at 8% (Stage 4: outdoor 100% cut, domestic 20% cut, industrial 30% cut)
    sim4 = simulate_reservoir_drawdown(series.iloc[:1], initial_pct=0.08, config=cfg)
    assert sim4.iloc[0]["curtailed_outdoor_acft"] == pytest.approx(10.0, abs=1e-3)
    assert sim4.iloc[0]["curtailed_domestic_acft"] == pytest.approx(8.0, abs=1e-3)
    assert sim4.iloc[0]["curtailed_industrial_acft"] == pytest.approx(15.0, abs=1e-3)
    np.testing.assert_allclose(sim4.balance_error_acft, 0.0, atol=1e-8)


def test_region_n_modern_preset_simulation():
    from basin_core.water_system import REGION_N_MODERN_PRESET
    REGION_N_MODERN_PRESET.validate()
    assert REGION_N_MODERN_PRESET.dead_storage_acft == 75000.0
    assert REGION_N_MODERN_PRESET.pipeline_capacity_mgd == 72.0

    series = pd.DataFrame({"station": [1.0] * 60}, index=pd.date_range("2024-01-01", periods=60))
    spec = simulate_stress_spectrum(series, tiers=(1.0, 0.5), initial_pct=0.48, config=REGION_N_MODERN_PRESET)
    assert len(spec["summary_table"]) == 2
    for r in spec["summary_table"]:
        assert "day_dead_storage" in r
        assert "day_zero" in r
    df = spec["tier_results"][1.0]["df"]
    assert "active_storage_acft" in df.columns
    assert (df["combined_acft"] >= 75000.0).all() or df["is_day_zero"].any()
    np.testing.assert_allclose(df.balance_error_acft, 0.0, atol=1e-8)


def test_tceq_emergency_order_estuary_pass_through():
    cfg = WaterSystemConfig(
        name="TCEQ Order System",
        sources=(WaterSource("Lake", 10000.0, inflow_base_acft=10.0, inflow_sensitivity=20.0),),
        demand_acft_day=10.0,
        estuary_order_active=True,
        estuary_threshold_pct=0.50,
    )
    # Above 50%: pass-through occurs
    series_wet = pd.DataFrame({"station": [5.0]}, index=pd.date_range("2024-01-01", periods=1))
    sim_above = simulate_reservoir_drawdown(series_wet, initial_pct=0.60, config=cfg)
    assert sim_above.iloc[0]["estuary_pass_through_acft"] > 0.0

    # Below 50%: pass-through suspended (retained in storage)
    sim_below = simulate_reservoir_drawdown(series_wet, initial_pct=0.40, config=cfg)
    assert sim_below.iloc[0]["estuary_pass_through_acft"] == 0.0
    np.testing.assert_allclose(sim_below.balance_error_acft, 0.0, atol=1e-8)


def test_extreme_custom_stress_inputs():
    # Extreme 365-day total zero rain test
    cfg = WaterSystemConfig(
        name="Extreme Test",
        sources=(WaterSource("Lake", 50000.0, inflow_base_acft=5.0, inflow_sensitivity=10.0),),
        demand_acft_day=50.0,
        dead_storage_acft=5000.0,
        stage_curtailment_active=True,
    )
    series_zero = pd.DataFrame({"station": [0.0] * 365}, index=pd.date_range("2024-01-01", periods=365))
    sim_zero = simulate_reservoir_drawdown(series_zero, initial_pct=0.30, config=cfg)
    assert len(sim_zero) == 365
    np.testing.assert_allclose(sim_zero.balance_error_acft, 0.0, atol=1e-8)

    # Extreme 300 mm deluge spike test (spill conservation)
    series_deluge = pd.DataFrame({"station": [300.0] * 5}, index=pd.date_range("2024-01-01", periods=5))
    sim_deluge = simulate_reservoir_drawdown(series_deluge, initial_pct=0.95, config=cfg)
    assert (sim_deluge["spill_acft"] > 0).any()
    assert (sim_deluge["combined_acft"] <= 50000.0).all()
    np.testing.assert_allclose(sim_deluge.balance_error_acft, 0.0, atol=1e-8)

