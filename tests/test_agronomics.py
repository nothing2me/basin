import numpy as np
import pandas as pd
import pytest

from basin_core.agronomics import (
    CROP_COEFFICIENTS,
    TEXAS_REGION_N_ETO_INCHES,
    calculate_crop_water_deficit,
    calculate_kbdi,
    KBDISummary,
)


def test_crop_water_deficit_calculation():
    dates = pd.date_range("2022-05-01", periods=90)
    # 0.5 mm rain per day (~0.02 in/day)
    series = pd.Series(0.5, index=dates)

    res = calculate_crop_water_deficit(series, crop_name="Cotton (mid-season peak)")

    assert res["crop_name"] == "Cotton (mid-season peak)"
    assert res["kc"] == 1.10
    assert res["total_days"] == 90
    assert res["total_rain_in"] > 0
    assert res["total_etc_in"] > res["total_rain_in"]
    assert res["irrigation_gap_in"] > 0
    assert len(res["monthly_summary"]) == 3  # May, June, July
    assert "Cotton" in res["takeaway"]
    assert "irrigation deficit" in res["takeaway"]


def test_crop_water_deficit_multistation_dataframe():
    dates = pd.date_range("2023-06-01", periods=60)
    df = pd.DataFrame({
        "StationA": [1.0] * 60,
        "StationB": [2.0] * 60,
    }, index=dates)

    res = calculate_crop_water_deficit(df, crop_name="Grain Sorghum (flowering)")
    assert res["kc"] == 1.05
    assert res["total_days"] == 60
    assert res["total_rain_mm"] == pytest.approx(90.0, 0.1)


def test_kbdi_burn_ban_breach():
    # 180 days with zero rain starting at 450 KBDI should easily breach 600
    dates = pd.date_range("2022-05-01", periods=180)
    series = pd.Series(0.0, index=dates)

    summary = calculate_kbdi(series, initial_kbdi=450.0)

    assert isinstance(summary, KBDISummary)
    assert summary.burn_ban_breached is True
    assert summary.burn_ban_day is not None
    assert summary.peak_kbdi > 600.0
    assert "burn-ban threshold" in summary.takeaway
    assert len(summary.daily_kbdi) == 180


def test_kbdi_wet_conditions():
    # 60 days with frequent heavy rain starting at 300 KBDI
    dates = pd.date_range("2023-04-01", periods=60)
    series = pd.Series(15.0, index=dates)  # 15 mm (~0.59 in) every day

    summary = calculate_kbdi(series, initial_kbdi=300.0)

    assert summary.burn_ban_breached is False
    assert summary.final_kbdi < 200.0
    assert "Low" in summary.danger_class or "Moderate" in summary.danger_class
