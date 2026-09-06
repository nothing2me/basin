import numpy as np
import pandas as pd
import pytest
from basin_core.analysis import simulate_reservoir_drawdown, label_profile


@pytest.mark.parametrize("rain, initial", [(0, 0), (0, .48), (100, .48), (100, 1), (1000, 0), (0, 1)])
def test_explicit_daily_water_conservation(rain, initial):
    series = pd.DataFrame({"station": [rain] * 365}, index=pd.date_range("2001-01-01", periods=365))
    sim = simulate_reservoir_drawdown(series, initial)
    np.testing.assert_allclose(sim.combined_acft, sim.beginning_acft + sim.inflow_acft - sim.evap_acft - sim.served_demand_acft - sim.spill_acft, atol=1e-8)
    np.testing.assert_allclose(sim.demand_acft, sim.served_demand_acft + sim.unmet_demand_acft, atol=1e-8)
    np.testing.assert_allclose(sim.potential_evap_acft, sim.evap_acft + sim.unmet_evap_acft, atol=1e-8)
    assert sim.combined_pct.between(0, 100).all()
    assert sim.lcc_acft.between(0, 257300).all() and sim.ccr_acft.between(0, 662600).all()
    if rain == 100 and initial == .48: assert sim.iloc[0].combined_acft > .48 * 919900
    if rain == 100 and initial == 1: assert sim.spill_acft.sum() > 0
    if rain == 0 and initial == 0: assert sim.unmet_demand_acft.sum() > 0


@pytest.mark.parametrize("kwargs", [{"initial_pct": -1}, {"initial_pct": 1.1}, {"initial_pct": float('nan')}, {"conservation_pct": -1}, {"conservation_pct": float('inf')}, {"conservation_pct": 1.1}, {"pipeline_active": "yes"}])
def test_invalid_reservoir_settings(kwargs):
    series = pd.DataFrame({"s": [0.]}, index=pd.date_range("2001-01-01", periods=1))
    with pytest.raises(ValueError): simulate_reservoir_drawdown(series, **kwargs)


@pytest.mark.parametrize("values", [[-1], [float('nan')], [float('inf')], []])
def test_invalid_reservoir_rainfall(values):
    series = pd.DataFrame({"s": values}, index=pd.date_range("2001-01-01", periods=len(values)))
    with pytest.raises(ValueError): simulate_reservoir_drawdown(series)


def test_conservation_and_pipeline_experiment():
    series = pd.DataFrame({"s": [0.] * 365}, index=pd.date_range("2001-01-01", periods=365))
    baseline = simulate_reservoir_drawdown(series)
    conserved = simulate_reservoir_drawdown(series, conservation_pct=.3)
    unavailable = simulate_reservoir_drawdown(series, pipeline_active=False)
    assert conserved.iloc[-1].combined_acft > baseline.iloc[-1].combined_acft > unavailable.iloc[-1].combined_acft
    assert "Station Stress" in label_profile(np.array([.9, .5, .9, .5, .2]), 1)
