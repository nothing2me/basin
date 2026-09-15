"""Unit and integration tests for advanced hydrology enhancements.

Covers the 5 enhancements recommended by the hydrologist review:
1. Dynamic stepped policy simulation across regulatory trigger stages.
2. Elevation-Area-Capacity (EAC) surface area shrinkage for evaporation.
3. Sector-disaggregated demand modeling (domestic, industrial, wholesale, outdoor).
4. 180-Day Statutory Emergency Horizon indicator (TAC Title 30 §290.41).
5. Conditional / tiered pipeline import reliability (Mary Rhodes / Lake Texana tiers).
"""
import numpy as np
import pandas as pd
import pytest

from basin_core.analysis import (
    simulate_reservoir_drawdown,
    simulate_stress_spectrum,
    threshold_crossing_day,
)
from basin_core.simulation import SimulationSettings, calculate
from basin_core.water_system import (
    REGION_N_PRESET,
    REGION_N_MODERN_PRESET,
    WaterSource,
    WaterSystemConfig,
)
from basin_core.pdf_report import (
    ExperimentConfig,
    compute_report_metrics,
    render_html_report,
    build_fallback_pdf,
)


@pytest.fixture
def dry_series():
    """90 consecutive days of zero rainfall."""
    dates = pd.date_range("2024-05-01", periods=90)
    return pd.DataFrame({"station_1": [0.0] * 90, "station_2": [0.0] * 90}, index=dates)


@pytest.fixture
def long_dry_series():
    """365 consecutive days of zero rainfall."""
    dates = pd.date_range("2024-01-01", periods=365)
    return pd.DataFrame({"station_1": [0.0] * 365}, index=dates)


# ======================================================================================
# 1. Dynamic Stepped Policy Simulation
# ======================================================================================

def test_stepped_policy_escalation(dry_series):
    """Conservation percentage should escalate dynamically as storage breaches trigger bands."""
    # Start at 42% storage, so it crosses 40% (Stage 1), 30% (Stage 2), etc.
    df = simulate_reservoir_drawdown(
        dry_series,
        initial_pct=0.42,
        conservation_pct=0.0,
        pipeline_active=True,
        stepped_policy=True,
        config=REGION_N_PRESET,
    )
    assert df["stepped_policy_active"].all()
    assert "effective_conservation_pct" in df.columns

    # Day 1: starting at 42% (>40%), stage is 0 -> 0% conservation
    assert df["effective_conservation_pct"].iloc[0] == 0.0

    # Later days: once storage starts the day <= 40%, effective_conservation_pct should escalate to 5%
    stage1_active = df[df["effective_conservation_pct"] >= 0.05]
    assert len(stage1_active) > 0
    # Storage when 5% was enacted should be <= 40%
    assert stage1_active["combined_pct"].iloc[0] <= 40.0


def test_custom_policy_schedule(dry_series):
    """Custom policy schedule should be respected when passed."""
    custom_sched = {0: 0.0, 1: 0.10, 2: 0.20, 3: 0.35, 4: 0.60}
    df = simulate_reservoir_drawdown(
        dry_series,
        initial_pct=0.35,  # <= 40% (Stage 1)
        stepped_policy=True,
        policy_schedule=custom_sched,
        config=REGION_N_PRESET,
    )
    # Day 1 starts at 35% -> Stage 1 -> 10%
    assert df["effective_conservation_pct"].iloc[0] == pytest.approx(0.10)


def test_stepped_policy_validation(dry_series):
    """Invalid stepped_policy parameters should raise ValueError."""
    with pytest.raises(ValueError, match="stepped_policy"):
        simulate_reservoir_drawdown(dry_series, stepped_policy="yes")
    with pytest.raises(ValueError, match="policy_schedule"):
        simulate_reservoir_drawdown(dry_series, stepped_policy=True, policy_schedule="not_a_dict")
    with pytest.raises(ValueError, match="policy_schedule"):
        simulate_reservoir_drawdown(dry_series, stepped_policy=True, policy_schedule={-1: 0.1})
    with pytest.raises(ValueError, match="policy_schedule"):
        simulate_reservoir_drawdown(dry_series, stepped_policy=True, policy_schedule={1: 1.5})


# ======================================================================================
# 2. EAC Surface Area Evaporation Shrinkage
# ======================================================================================

def test_eac_surface_area_tracking(dry_series):
    """Simulation with use_eac_scaling should record eac_scale and surface_area_acres."""
    df_eac = simulate_reservoir_drawdown(
        dry_series,
        initial_pct=0.35,
        use_eac_scaling=True,
        config=REGION_N_PRESET,
    )
    assert "eac_scale" in df_eac.columns
    assert "surface_area_acres" in df_eac.columns
    assert (df_eac["eac_scale"] > 0).all()
    assert (df_eac["surface_area_acres"] > 0).all()

    # As storage draws down, surface area and eac_scale should contract
    assert df_eac["eac_scale"].iloc[-1] <= df_eac["eac_scale"].iloc[0]
    assert df_eac["surface_area_acres"].iloc[-1] <= df_eac["surface_area_acres"].iloc[0]

    # Mass balance must remain strictly conserved
    np.testing.assert_allclose(df_eac["balance_error_acft"], 0.0, atol=1e-8)


def test_eac_evaporation_attenuation(dry_series):
    """EAC scaling should reduce potential evaporation compared to unscaled fixed evaporation."""
    df_flat = simulate_reservoir_drawdown(dry_series, initial_pct=0.30, use_eac_scaling=False)
    df_eac = simulate_reservoir_drawdown(dry_series, initial_pct=0.30, use_eac_scaling=True)

    # At 30% storage, EAC scale is (0.30)^0.65 ~ 0.457, so daily evap is less than flat evap
    assert df_eac["evap_acft"].mean() < df_flat["evap_acft"].mean()


# ======================================================================================
# 3. Sector-Disaggregated Demand Modeling
# ======================================================================================

def test_wholesale_sector_config():
    """WaterSystemConfig should support demand_wholesale_pct and validate 100% sum."""
    cfg = WaterSystemConfig(
        name="Industrial & Wholesale District",
        sources=(WaterSource("Primary Lake", 100000.0),),
        demand_domestic_pct=30.0,
        demand_industrial_pct=50.0,
        demand_wholesale_pct=15.0,
        demand_outdoor_pct=5.0,
    )
    cfg.validate()
    assert cfg.demand_wholesale_pct == 15.0

    # Sector percentages that don't sum to 100 must fail
    with pytest.raises(ValueError, match="sum to 100"):
        WaterSystemConfig(
            name="Bad Sum",
            sources=(WaterSource("Lake", 10000.0),),
            demand_domestic_pct=40.0,
            demand_industrial_pct=50.0,
            demand_wholesale_pct=20.0,  # 40+50+20+10 = 120
            demand_outdoor_pct=10.0,
        ).validate()


def test_sector_deliveries_in_simulation(dry_series):
    """Simulation DataFrame should track deliveries and curtailments for all sectors."""
    cfg = WaterSystemConfig(
        name="Multi-Sector District",
        sources=(WaterSource("Main Pool", 200000.0),),
        demand_acft_day=100.0,
        demand_domestic_pct=35.0,
        demand_industrial_pct=45.0,
        demand_wholesale_pct=15.0,
        demand_outdoor_pct=5.0,
        stage_curtailment_active=True,
    )
    df = simulate_reservoir_drawdown(dry_series, initial_pct=0.50, config=cfg)
    for col in (
        "served_domestic_acft", "served_industrial_acft",
        "served_wholesale_acft", "served_outdoor_acft",
        "curtailed_domestic_acft", "curtailed_industrial_acft",
        "curtailed_wholesale_acft", "curtailed_outdoor_acft",
    ):
        assert col in df.columns

    # Delivered sector amounts must sum to served_demand_acft
    sector_sum = df["served_domestic_acft"] + df["served_industrial_acft"] + df["served_wholesale_acft"] + df["served_outdoor_acft"]
    np.testing.assert_allclose(sector_sum, df["served_demand_acft"], atol=1e-8)


# ======================================================================================
# 4. 180-Day Statutory Emergency Horizon Indicator
# ======================================================================================

def test_tac_180_day_trigger_detection(long_dry_series):
    """Under severe drought that drains pool within 180 days, tac_180_day_breached must be True."""
    # Small reservoir with high demand will drain quickly
    cfg = WaterSystemConfig(
        name="Vulnerable Muni",
        sources=(WaterSource("Small Lake", 20000.0),),
        demand_acft_day=200.0,  # 20,000 * 0.50 = 10,000 ac-ft / 200 = 50 days to zero
        demand_no_pipeline_acft_day=None,
    )
    spec = simulate_stress_spectrum(long_dry_series, tiers=(1.0,), initial_pct=0.50, config=cfg)
    row = spec["summary_table"][0]
    assert row["day_zero"] is not None
    assert row["day_zero"] <= 180
    assert row["tac_180_day_breached"] is True
    assert row["tac_180_warning_day"] is not None
    assert "EMERGENCY" in row["tac_180_status"]


def test_tac_180_day_compliance(dry_series):
    """Under ample storage where supply lasts beyond 180 days, tac_180_day_breached must be False."""
    # Region N at 80% with 90 days duration: does not breach zero
    spec = simulate_stress_spectrum(dry_series, tiers=(1.0,), initial_pct=0.80, config=REGION_N_PRESET)
    row = spec["summary_table"][0]
    assert row["tac_180_day_breached"] is False
    assert row["tac_180_warning_day"] is None
    assert "Adequate" in row["tac_180_status"]


# ======================================================================================
# 5. Conditional / Tiered Pipeline Import Reliability
# ======================================================================================

def test_tiered_pipeline_reliability(dry_series):
    """Continuous pipeline reliability should smoothly interpolate reservoir demand draft."""
    # Region N defaults: demand_with_pipeline = 370, demand_no_pipeline = 554. Yield = 184.
    df_100 = simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=1.0)
    df_70 = simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=0.70)
    df_50 = simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=0.50)
    df_0 = simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=0.0)

    # Day 1 demand requests:
    # 100%: 370 ac-ft/day
    # 70%: 554 - 184 * 0.70 = 425.2 ac-ft/day
    # 50%: 554 - 184 * 0.50 = 462.0 ac-ft/day
    # 0%: 554 ac-ft/day
    assert df_100["demand_acft"].iloc[0] == pytest.approx(370.0)
    assert df_70["demand_acft"].iloc[0] == pytest.approx(425.2)
    assert df_50["demand_acft"].iloc[0] == pytest.approx(462.0)
    assert df_0["demand_acft"].iloc[0] == pytest.approx(554.0)

    # End storage: higher pipeline reliability should yield higher remaining storage
    assert df_100["combined_acft"].iloc[-1] > df_70["combined_acft"].iloc[-1]
    assert df_70["combined_acft"].iloc[-1] > df_50["combined_acft"].iloc[-1]
    assert df_50["combined_acft"].iloc[-1] > df_0["combined_acft"].iloc[-1]


def test_pipeline_reliability_validation(dry_series):
    """Invalid pipeline_reliability_pct values must raise ValueError."""
    with pytest.raises(ValueError, match="Pipeline reliability"):
        simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=1.5)
    with pytest.raises(ValueError, match="Pipeline reliability"):
        simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=-0.1)
    with pytest.raises(ValueError, match="Pipeline reliability"):
        simulate_reservoir_drawdown(dry_series, pipeline_reliability_pct=True)


# ======================================================================================
# 6. Integration: Reports & Simulation Settings
# ======================================================================================

def test_simulation_settings_and_calculate(dry_series):
    """SimulationSettings with stepped_policy and pipeline_reliability_pct should execute cleanly."""
    settings = SimulationSettings.from_percent(
        initial_storage_percent=38.0,
        conservation_percent=15.0,
        stepped_policy=True,
        pipeline_reliability_percent=70.0,
    )
    assert settings.stepped_policy is True
    assert settings.pipeline_reliability_pct == pytest.approx(0.70)

    res = calculate(dry_series, settings, REGION_N_PRESET)
    assert "summary_table" in res
    assert "trajectories" in res
    assert res["summary_table"][0]["stepped_policy_active"] is True
    assert res["summary_table"][0]["pipeline_reliability_pct"] == pytest.approx(0.70)


def test_experiment_config_and_report_metrics(dry_series):
    """ReportMetrics should populate TAC and sector data when run from ExperimentConfig."""
    class MockScenario:
        series = dry_series
        revision = 1
        id = "TEST-SCEN"

    cfg = ExperimentConfig(
        initial_pct=0.38,
        conservation_pct=0.15,
        stepped_policy=True,
        pipeline_reliability_pct=0.70,
    )
    metrics = compute_report_metrics(MockScenario(), cfg)
    assert metrics.available
    assert metrics.stepped_policy_active is True
    assert metrics.pipeline_reliability_pct == pytest.approx(0.70)
    assert metrics.sector_deliveries is not None
    assert "domestic_served_acft" in metrics.sector_deliveries
    assert hasattr(metrics, "tac_180_day_breached")
