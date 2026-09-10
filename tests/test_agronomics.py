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


def test_kbdi_boundary_clipping():
    dates = pd.date_range("2023-01-01", periods=10)
    series = pd.Series(0.0, index=dates)

    # Initial value above 800 is clamped to 800
    summary_high = calculate_kbdi(series, initial_kbdi=950.0)
    assert summary_high.initial_kbdi == 950.0
    assert all(0.0 <= val <= 800.0 for val in summary_high.daily_kbdi)

    # Initial value below 0 is clamped to 0
    summary_low = calculate_kbdi(series, initial_kbdi=-50.0)
    assert all(0.0 <= val <= 800.0 for val in summary_low.daily_kbdi)


def test_kbdi_interception_deduction():
    dates = pd.date_range("2023-07-01", periods=3)
    # Day 1: 4 mm (~0.157 in) <= 0.20 in interception threshold
    # Day 2: 25.4 mm (1.00 in) on consecutive day (no interception threshold subtracted)
    # Day 3: 0 mm
    series = pd.Series([4.0, 25.4, 0.0], index=dates)

    summary = calculate_kbdi(series, initial_kbdi=500.0)
    # Day 1 should not reduce KBDI because 0.157 <= 0.20 in
    assert summary.daily_kbdi[0] >= 500.0
    # Day 2 has 1.0 in rain on consecutive day, reducing KBDI by ~100 points
    assert summary.daily_kbdi[1] < summary.daily_kbdi[0] - 80.0


def test_kbdi_illustrative_policy_disclaimer():
    dates = pd.date_range("2022-06-01", periods=15)
    series = pd.Series(0.0, index=dates)
    summary = calculate_kbdi(series, initial_kbdi=580.0)

    assert summary.burn_ban_breached is True
    assert "illustrative decision support" in summary.takeaway
    assert "not an official legal declaration" in summary.takeaway
    assert "Illustrative Burn Ban Trigger" in summary.danger_class


def test_crop_water_deficit_validation_and_custom_kc():
    dates = pd.date_range("2023-05-01", periods=30)
    series = pd.Series(2.0, index=dates)

    # Custom Kc override
    res = calculate_crop_water_deficit(series, crop_name="Custom", custom_kc=1.35)
    assert res["kc"] == 1.35
    assert res["total_etc_in"] > 0

    # Empty series raises ValueError
    with pytest.raises(ValueError, match="empty"):
        calculate_crop_water_deficit(pd.Series(dtype=float))


def test_texas_region_n_eto_normals():
    assert len(TEXAS_REGION_N_ETO_INCHES) == 12
    # Annual ETo should be approximately 58.1 inches (Coastal Bend normals)
    assert 55.0 <= sum(TEXAS_REGION_N_ETO_INCHES.values()) <= 62.0
    # Summer months (June, July, August) should have peak ETo > 6.5 in/month
    for m in (6, 7, 8):
        assert TEXAS_REGION_N_ETO_INCHES[m] >= 6.5

