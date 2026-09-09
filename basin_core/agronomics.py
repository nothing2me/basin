"""Agronomic water balance and wildfire drought index (KBDI) calculations.

Provides:
- Texas Reference Evapotranspiration (ETo) based on Texas ET Network (Texas A&M AgriLife).
- Crop Water Demand (ETc = ETo * Kc) and irrigation deficit calculations for regional staple crops.
- Keetch-Byram Drought Index (KBDI) tracking cumulative soil moisture deficit (0–800) and
  county burn ban danger thresholds (> 600).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Any
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Texas Coastal Bend / South Texas Reference ET (ETo) Normals (Texas ET Network)
# Long-term monthly averages in inches for Corpus Christi / Nueces & surrounding counties.
# ---------------------------------------------------------------------------

TEXAS_REGION_N_ETO_INCHES: dict[int, float] = {
    1: 2.20,   # Jan
    2: 2.80,   # Feb
    3: 4.20,   # Mar
    4: 5.30,   # Apr
    5: 6.20,   # May
    6: 7.10,   # Jun
    7: 7.60,   # Jul
    8: 7.40,   # Aug
    9: 5.60,   # Sep
    10: 4.50,  # Oct
    11: 3.00,  # Nov
    12: 2.20,  # Dec
}

ANNUAL_ETO_INCHES = sum(TEXAS_REGION_N_ETO_INCHES.values())  # 58.1 inches (~1476 mm)

# Standard regional crop coefficients (Kc) for South Texas / Coastal Bend
CROP_COEFFICIENTS: dict[str, dict[str, Any]] = {
    "Cotton (mid-season peak)": {
        "kc": 1.10,
        "description": "Peak boll development & flowering (June–August)",
        "critical_months": (6, 7, 8),
    },
    "Grain Sorghum (flowering)": {
        "kc": 1.05,
        "description": "Grain filling & boot stage (May–July)",
        "critical_months": (5, 6, 7),
    },
    "Corn (silking / blister)": {
        "kc": 1.15,
        "description": "Peak reproductive stage (May–June)",
        "critical_months": (5, 6),
    },
    "Pasture / Coastal Bermuda": {
        "kc": 0.85,
        "description": "Warm-season perennial grazing/hay",
        "critical_months": (4, 5, 6, 7, 8, 9),
    },
    "General Row Crop (season mean)": {
        "kc": 0.95,
        "description": "Average regional row crop demand",
        "critical_months": tuple(range(1, 13)),
    },
}


def get_daily_eto_inches(month: int, days_in_month: int) -> float:
    """Return average daily reference ET (inches) for a given month."""
    monthly_in = TEXAS_REGION_N_ETO_INCHES.get(month, 4.5)
    return monthly_in / max(1, days_in_month)


def calculate_crop_water_deficit(
    scenario_rainfall_series: pd.Series | pd.DataFrame,
    crop_name: str = "Cotton (mid-season peak)",
    custom_kc: float | None = None,
) -> dict[str, Any]:
    """Calculate crop water demand (ETc) and the net irrigation deficit under a scenario.

    Parameters:
        scenario_rainfall_series: Daily rainfall series (index must be pd.DatetimeIndex).
                                  Values in mm (standard BASIN internal unit).
        crop_name: Key in CROP_COEFFICIENTS or custom label.
        custom_kc: Optional override for crop coefficient Kc.

    Returns:
        Dictionary with total rain, crop ET, net irrigation deficit, and monthly breakdown.
    """
    if isinstance(scenario_rainfall_series, pd.DataFrame):
        # Average across columns if multiple stations
        daily_rain_mm = scenario_rainfall_series.mean(axis=1)
    else:
        daily_rain_mm = scenario_rainfall_series.copy()

    if daily_rain_mm.empty:
        raise ValueError("Rainfall series cannot be empty")

    crop_meta = CROP_COEFFICIENTS.get(crop_name, {
        "kc": custom_kc or 1.0,
        "description": "Custom crop profile",
        "critical_months": tuple(range(1, 13)),
    })
    kc = custom_kc if custom_kc is not None else crop_meta["kc"]

    dates = pd.to_datetime(daily_rain_mm.index)
    daily_rain_in = daily_rain_mm / 25.4

    daily_rows = []
    for dt, rain_in, rain_mm in zip(dates, daily_rain_in, daily_rain_mm):
        m = dt.month
        days_in_m = calendar.monthrange(dt.year, m)[1]
        eto_in = get_daily_eto_inches(m, days_in_m)
        etc_in = eto_in * kc
        deficit_in = max(0.0, etc_in - rain_in)
        daily_rows.append({
            "date": dt,
            "rain_in": rain_in,
            "rain_mm": rain_mm,
            "eto_in": eto_in,
            "etc_in": etc_in,
            "deficit_in": deficit_in,
        })

    df = pd.DataFrame(daily_rows)

    total_rain_in = float(df["rain_in"].sum())
    total_rain_mm = float(df["rain_mm"].sum())
    total_eto_in = float(df["eto_in"].sum())
    total_etc_in = float(df["etc_in"].sum())
    total_deficit_in = float(df["deficit_in"].sum())
    total_deficit_mm = total_deficit_in * 25.4
    acre_inches = total_deficit_in  # 1 acre-inch = 1 inch applied over 1 acre

    # Monthly breakdown
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
    monthly_summary = []
    for period, grp in df.groupby("month"):
        m_dt = period.to_timestamp()
        m_rain_in = float(grp["rain_in"].sum())
        m_etc_in = float(grp["etc_in"].sum())
        m_def_in = float(grp["deficit_in"].sum())
        monthly_summary.append({
            "month_label": m_dt.strftime("%b %Y"),
            "days": len(grp),
            "rain_in": round(m_rain_in, 2),
            "etc_in": round(m_etc_in, 2),
            "irrigation_deficit_in": round(m_def_in, 2),
            "adequacy_pct": round((m_rain_in / m_etc_in * 100.0) if m_etc_in > 0 else 100.0, 1),
        })

    # Plain language takeaway
    if total_deficit_in > 10.0:
        severity = "severe crop moisture stress"
    elif total_deficit_in > 5.0:
        severity = "moderate crop moisture deficit requiring supplemental irrigation"
    else:
        severity = "mild moisture deficit manageable with conserved soil moisture"

    takeaway = (
        f"For **{crop_name}** (Kc = {kc:.2f}), scenario rainfall covers only "
        f"**{total_rain_in:.2f} in** of the estimated **{total_etc_in:.2f} in** total crop water demand, "
        f"creating an irrigation deficit of **{total_deficit_in:.2f} in/acre ({total_deficit_mm:.1f} mm)** — {severity}."
    )

    return {
        "crop_name": crop_name,
        "kc": kc,
        "total_days": len(df),
        "total_rain_in": round(total_rain_in, 2),
        "total_rain_mm": round(total_rain_mm, 1),
        "total_eto_in": round(total_eto_in, 2),
        "total_etc_in": round(total_etc_in, 2),
        "irrigation_gap_in": round(total_deficit_in, 2),
        "irrigation_gap_mm": round(total_deficit_mm, 1),
        "acre_inches_per_acre": round(acre_inches, 2),
        "monthly_summary": monthly_summary,
        "takeaway": takeaway,
    }


# ---------------------------------------------------------------------------
# Keetch-Byram Drought Index (KBDI)
# Standard soil moisture deficiency index (0–800) used by Texas A&M Forest Service
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KBDISummary:
    initial_kbdi: float
    peak_kbdi: float
    final_kbdi: float
    peak_day: int
    burn_ban_breached: bool
    burn_ban_day: int | None
    danger_class: str
    takeaway: str
    daily_kbdi: list[float]


def calculate_kbdi(
    scenario_rainfall_series: pd.Series | pd.DataFrame,
    initial_kbdi: float = 400.0,
    annual_rain_in: float = 32.0,  # Regional average annual rainfall (South Texas)
) -> KBDISummary:
    """Calculate the Keetch-Byram Drought Index (KBDI) trajectory across a scenario.

    KBDI ranges from 0 (saturated soil) to 800 (maximum drought / complete depletion).
    County burn bans in Texas are typically enacted when KBDI exceeds 600.

    Parameters:
        scenario_rainfall_series: Daily rainfall in mm.
        initial_kbdi: Starting KBDI (0–800), default 400 (moderate pre-drought condition).
        annual_rain_in: Regional normal annual precipitation in inches (~32 in for Region N).

    Returns:
        KBDISummary with peak, final, burn ban breach status, and daily trajectory.
    """
    if isinstance(scenario_rainfall_series, pd.DataFrame):
        daily_rain_mm = scenario_rainfall_series.mean(axis=1)
    else:
        daily_rain_mm = scenario_rainfall_series.copy()

    if daily_rain_mm.empty:
        raise ValueError("Rainfall series cannot be empty")

    dates = pd.to_datetime(daily_rain_mm.index)
    daily_rain_in = (daily_rain_mm / 25.4).to_numpy()

    kbdi = float(np.clip(initial_kbdi, 0.0, 800.0))
    kbdi_history: list[float] = []

    consecutive_rain_days = 0
    burn_ban_day: int | None = None

    for day_idx, (dt, p_in) in enumerate(zip(dates, daily_rain_in), start=1):
        # 1. Net rainfall deduction
        if p_in > 0:
            if consecutive_rain_days == 0:
                # First day of rain: subtract 0.20 in interception threshold
                net_rain = max(0.0, p_in - 0.20)
            else:
                net_rain = p_in
            consecutive_rain_days += 1
            kbdi = max(0.0, kbdi - (net_rain * 100.0))
        else:
            consecutive_rain_days = 0

        # 2. Daily drought factor / evaporative moisture loss
        # Monthly mean daily temp approximation for South Texas (°F)
        m = dt.month
        temp_f = {1: 57, 2: 61, 3: 67, 4: 74, 5: 80, 6: 85, 7: 87, 8: 88, 9: 83, 10: 76, 11: 66, 12: 59}.get(m, 75)
        # Standard Keetch-Byram drought factor formula (hundredths of inch per day)
        numerator = (800.0 - kbdi) * (0.968 * np.exp(0.0486 * temp_f) - 8.30)
        denominator = 1.0 + 10.88 * np.exp(-0.0441 * annual_rain_in)
        dQ = (numerator / denominator) * 0.001

        kbdi = min(800.0, kbdi + max(0.0, dQ))
        kbdi_history.append(round(kbdi, 1))

        if burn_ban_day is None and kbdi >= 600.0:
            burn_ban_day = day_idx

    peak_kbdi = float(max(kbdi_history))
    final_kbdi = float(kbdi_history[-1])
    peak_day = kbdi_history.index(peak_kbdi) + 1

    if peak_kbdi >= 700:
        danger_class = "Extreme (700–800)"
    elif peak_kbdi >= 600:
        danger_class = "Severe (600–700) · County Burn Ban Threshold"
    elif peak_kbdi >= 400:
        danger_class = "High (400–600)"
    elif peak_kbdi >= 200:
        danger_class = "Moderate (200–400)"
    else:
        danger_class = "Low (0–200)"

    if burn_ban_day is not None:
        takeaway = (
            f"Soil moisture depletes steadily, driving KBDI to breach the **600 burn-ban threshold on Day {burn_ban_day}** "
            f"and peaking at **{peak_kbdi:.0f}** ({danger_class}) on Day {peak_day}. "
            f"High wildfire risk and mandatory agricultural burn restrictions would be expected."
        )
    elif peak_kbdi >= 500:
        takeaway = (
            f"KBDI reaches a high of **{peak_kbdi:.0f}** ({danger_class}) on Day {peak_day}, "
            "approaching county burn-ban triggers but staying below mandatory restriction levels."
        )
    else:
        takeaway = (
            f"KBDI peaks at **{peak_kbdi:.0f}** ({danger_class}), indicating adequate soil moisture retention "
            "and low-to-moderate wildfire danger."
        )

    return KBDISummary(
        initial_kbdi=initial_kbdi,
        peak_kbdi=peak_kbdi,
        final_kbdi=final_kbdi,
        peak_day=peak_day,
        burn_ban_breached=burn_ban_day is not None,
        burn_ban_day=burn_ban_day,
        danger_class=danger_class,
        takeaway=takeaway,
        daily_kbdi=kbdi_history,
    )
