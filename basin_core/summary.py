"""Plain-language scenario summaries for non-hydrologist stakeholders.

Provides deterministic, templated plain-English explanations of scenario
stress levels, historical rarity, multi-station concurrency, and reservoir
outcomes for water board members, farm operators, and council officials.
"""
from __future__ import annotations
import pandas as pd


def scenario_summary(features: dict, station_names: dict[str, str] | None = None) -> str:
    """Generate a clear, 2-3 sentence plain-language interpretation of scenario rainfall metrics."""
    duration = features.get("duration_days", 0)
    deficit = features.get("deficit_mm", 0.0)
    percentile = features.get("historical_percentile", 0.0)
    concurrence = features.get("concurrence", 0.0)
    benchmark_n = features.get("benchmark_n", 0)
    beyond = features.get("beyond_rainfall_reference", False)
    dry_spell = features.get("max_dry_days", 0)

    if percentile >= 0.95 or beyond:
        rarity = "an exceptionally rare deficit"
    elif percentile >= 0.80:
        rarity = "a severe drought run"
    elif percentile >= 0.60:
        rarity = "a moderate drought deficit"
    else:
        rarity = "a deficit within typical historical variation"

    deficit_in = deficit / 25.4
    summary_parts = [
        f"This **{duration}-day scenario** produces an average rainfall deficit of **{deficit:,.1f} mm ({deficit_in:,.2f} in)** across monitored stations — "
        f"{rarity} (exceeding **{percentile * 100:.0f}%** of {benchmark_n} comparable historical windows)."
    ]

    if concurrence >= 0.40:
        summary_parts.append(
            f"Crucially, all monitored stations experience drought stress simultaneously in **{concurrence * 100:.0f}%** of eligible 30-day windows, "
            "pointing to regional, multi-basin supply stress rather than an isolated dry pocket."
        )
    elif concurrence > 0:
        summary_parts.append(
            f"Stations experience concurrent drought stress in **{concurrence * 100:.0f}%** of 30-day windows."
        )
    else:
        summary_parts.append(
            "Rainfall reductions are localized; stations rarely hit threshold deficits in the same 30-day window."
        )

    if dry_spell >= 30:
        summary_parts.append(f"The longest continuous dry spell (< 1 mm/day) lasts **{dry_spell} days**.")

    return " ".join(summary_parts)


def reservoir_summary(sim_df: pd.DataFrame, system_name: str = "the regional system",
                      critical_pct: float | None = None,
                      stage_bands_pct: tuple[float, ...] | None = None) -> str:
    """Generate a 1-2 sentence plain-language operational takeaway from simulation drawdown."""
    if sim_df is None or sim_df.empty:
        return "No simulation data available."

    bands = stage_bands_pct if stage_bands_pct is not None else (0.40, 0.30, 0.20, 0.15)
    s1_pct = bands[0] * 100 if len(bands) >= 1 else 40.0
    s2_pct = bands[1] * 100 if len(bands) >= 2 else 30.0
    crit_val = critical_pct if critical_pct is not None else (bands[2] * 100 if len(bands) >= 3 else 20.0)

    final_pct = float(sim_df["combined_pct"].iloc[-1])
    min_pct = float(sim_df["combined_pct"].min())
    days = len(sim_df)

    b40 = next((int(r["day"]) for _, r in sim_df.iterrows() if r["combined_pct"] <= s1_pct), None)
    b30 = next((int(r["day"]) for _, r in sim_df.iterrows() if r["combined_pct"] <= s2_pct), None)
    b20 = next((int(r["day"]) for _, r in sim_df.iterrows() if r["combined_pct"] <= crit_val), None)

    if b20 is not None:
        return (
            f"Under these assumed inputs for **{system_name}**, combined storage breaches the critical **{crit_val:.0f}% emergency band on Day {b20}** "
            f"and reaches a low of **{min_pct:.1f}%**, signaling potential emergency curtailments."
        )
    elif b30 is not None:
        return (
            f"Storage drops into Stage 2 restrictions (**{s2_pct:.0f}% band**) on **Day {b30}**, but stays above critical emergency levels, "
            f"bottoming out at **{min_pct:.1f}%** and ending at **{final_pct:.1f}%** after {days} days."
        )
    elif b40 is not None:
        return (
            f"Storage enters voluntary conservation (**Stage 1 / {s1_pct:.0f}% band**) on **Day {b40}**, bottoming out at **{min_pct:.1f}%** "
            f"and finishing the scenario at **{final_pct:.1f}%**."
        )
    else:
        return (
            f"Storage remains above Stage 1 restriction thresholds throughout the entire {days}-day window, "
            f"reaching a low of **{min_pct:.1f}%** and ending at **{final_pct:.1f}%**."
        )
