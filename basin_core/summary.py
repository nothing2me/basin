"""Plain-language scenario summaries for non-hydrologist stakeholders.

Provides deterministic, templated plain-English explanations of scenario
stress levels, historical rarity, multi-station concurrency, and reservoir
outcomes for water board members, farm operators, and council officials.
"""
from __future__ import annotations
import math
import pandas as pd


def format_retained_rainfall(
    fraction_or_pct: float,
    baseline: str = "observed rainfall",
    *,
    is_fraction: bool = True,
) -> str:
    """Format retained rainfall, explicitly identifying baseline.

    Args:
        fraction_or_pct: The retained proportion (e.g. 0.70 or 70.0).
        baseline: The reference baseline name (default "observed rainfall").
        is_fraction: True if input is [0, 1] fraction, False if [0, 100] percentage.

    Returns:
        Formatted string, e.g. "70% of observed rainfall" or "37.5% of observed rainfall".
    """
    if not math.isfinite(fraction_or_pct) or fraction_or_pct < 0:
        raise ValueError("Rainfall fraction or percentage must be a finite non-negative number")
    pct = round(fraction_or_pct * 100 if is_fraction else fraction_or_pct, 1)
    return f"{pct:g}% of {baseline}"


def format_rainfall_reduction(
    fraction_or_pct: float,
    baseline: str = "observed rainfall",
    *,
    is_fraction: bool = True,
) -> str:
    """Format rainfall reduction, explicitly identifying baseline.

    Args:
        fraction_or_pct: The reduction proportion (e.g. 0.30 or 30.0).
        baseline: The reference baseline name (default "observed rainfall").
        is_fraction: True if input is [0, 1] fraction, False if [0, 100] percentage.

    Returns:
        Formatted string, e.g. "30% reduction from observed rainfall".
    """
    if not math.isfinite(fraction_or_pct) or fraction_or_pct < 0:
        raise ValueError("Rainfall fraction or percentage must be a finite non-negative number")
    pct = round(fraction_or_pct * 100 if is_fraction else fraction_or_pct, 1)
    return f"{pct:g}% reduction from {baseline}"


def format_rainfall_dual_explanation(
    retained_fraction_or_pct: float,
    baseline: str = "observed rainfall",
    *,
    is_fraction: bool = True,
) -> str:
    """Format both retained rainfall and its complementary reduction.

    Args:
        retained_fraction_or_pct: The retained proportion (e.g. 0.70 or 70.0).
        baseline: The reference baseline name (default "observed rainfall").
        is_fraction: True if input is [0, 1] fraction, False if [0, 100] percentage.

    Returns:
        Formatted dual explanation, e.g.:
        0.70 -> "70% of observed rainfall (30% reduction from observed rainfall)"
        1.00 -> "100% of observed rainfall (0% reduction)"
        0.00 -> "0% of observed rainfall (100% reduction from observed rainfall)"
        1.10 -> "110% of observed rainfall (10% increase over observed rainfall)"
    """
    if not math.isfinite(retained_fraction_or_pct) or retained_fraction_or_pct < 0:
        raise ValueError("Rainfall fraction or percentage must be a finite non-negative number")
    ret_pct = round(retained_fraction_or_pct * 100 if is_fraction else retained_fraction_or_pct, 1)
    if ret_pct == 100.0:
        return f"{ret_pct:g}% of {baseline} (0% reduction)"
    elif ret_pct < 100.0:
        red_pct = round(100.0 - ret_pct, 1)
        return f"{ret_pct:g}% of {baseline} ({red_pct:g}% reduction from {baseline})"
    else:
        inc_pct = round(ret_pct - 100.0, 1)
        return f"{ret_pct:g}% of {baseline} ({inc_pct:g}% increase over {baseline})"


def scenario_summary(features: dict, station_names: dict[str, str] | None = None,
                     unit_system: str = "us") -> str:
    """Generate a clear, 2-3 sentence plain-language interpretation of scenario rainfall metrics."""
    duration = features.get("duration_days", 0)
    deficit = features.get("deficit_mm", 0.0)
    percentile = features.get("historical_percentile", 0.0)
    concurrence = features.get("concurrence", 0.0)
    benchmark_n = features.get("benchmark_n", 0)
    dry_spell = features.get("max_dry_days", 0)
    station_count = len(features.get("station_deficits_mm", {})) or len(station_names or {})

    deficit_in = deficit / 25.4
    if unit_system == "metric":
        deficit_fmt = f"**{deficit:,.1f} mm ({deficit_in:,.2f} in)**"
    else:
        deficit_fmt = f"**{deficit_in:,.2f} in ({deficit:,.1f} mm)**"

    summary_parts = [
        f"This **{duration}-day scenario** has a net rainfall shortfall of {deficit_fmt}, averaged equally across the selected stations."
    ]
    if benchmark_n >= 5:
        summary_parts.append(
            f"The shortfall equals or exceeds **{percentile * 100:.0f}%** of {benchmark_n} historical comparison windows; "
            "this is a sample comparison, not a drought probability."
        )
    else:
        summary_parts.append(
            f"Only {benchmark_n} historical comparison windows are available; this small sample does not support a rarity claim."
        )

    eligible = features.get("eligible_concurrence_days")
    if eligible == 0:
        summary_parts.append("No eligible 30-day windows are available for the station-stress comparison.")
    elif station_count == 1:
        summary_parts.append(
            f"The selected station exceeds its rainfall-stress threshold in **{concurrence * 100:.0f}%** of eligible 30-day windows; "
            "this measures persistence at one station."
        )
    else:
        summary_parts.append(
            f"All selected stations exceed their rainfall-stress thresholds together in **{concurrence * 100:.0f}%** of eligible 30-day windows. "
            "Station rainfall alone does not establish basin-wide water-supply conditions."
        )

    if dry_spell >= 30:
        summary_parts.append(f"The longest run below 1 mm/day at any selected station lasts **{dry_spell} days**.")

    return " ".join(summary_parts)


def reservoir_summary(sim_df: pd.DataFrame, system_name: str = "the regional system",
                      critical_pct: float | None = None,
                      stage_bands_pct: tuple[float, ...] | None = None,
                      initial_pct: float | None = None) -> str:
    """Describe modeled storage relative to illustrative bands without policy inference."""
    if sim_df is None or sim_df.empty:
        return "No simulation data available."

    bands = stage_bands_pct if stage_bands_pct is not None else (0.40, 0.30, 0.20, 0.15)
    s1_pct = bands[0] * 100 if len(bands) >= 1 else 40.0
    s2_pct = bands[1] * 100 if len(bands) >= 2 else 30.0
    crit_val = critical_pct if critical_pct is not None else (bands[2] * 100 if len(bands) >= 3 else 20.0)

    final_pct = float(sim_df["combined_pct"].iloc[-1])
    min_pct = float(sim_df["combined_pct"].min())
    days = len(sim_df)

    def first_at_or_below(threshold: float) -> int | None:
        if initial_pct is not None and initial_pct * 100 <= threshold:
            return 0
        return next((int(r["day"]) for _, r in sim_df.iterrows() if r["combined_pct"] <= threshold), None)

    b40 = first_at_or_below(s1_pct)
    b30 = first_at_or_below(s2_pct)
    b20 = first_at_or_below(crit_val)

    if b20 is not None:
        return (
            f"Under these assumed inputs for **{system_name}**, combined storage first reaches the illustrative "
            f"**{crit_val:.0f}% band on Day {b20}** and reaches a low of **{min_pct:.1f}%**. "
            "The experiment assigns no operational action to that band."
        )
    elif b30 is not None:
        return (
            f"Storage first reaches the illustrative **{s2_pct:.0f}% band on Day {b30}**, stays above the "
            f"{crit_val:.0f}% band, reaches a low of **{min_pct:.1f}%**, and ends at **{final_pct:.1f}%** after {days} days."
        )
    elif b40 is not None:
        return (
            f"Storage first reaches the illustrative **{s1_pct:.0f}% band on Day {b40}**, reaches a low of **{min_pct:.1f}%**, "
            f"and ends at **{final_pct:.1f}%**. No response action is encoded."
        )
    else:
        return (
            f"Storage stays above all illustrative bands throughout the {days}-day window, "
            f"reaching a low of **{min_pct:.1f}%** and ending at **{final_pct:.1f}%**."
        )


MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def classify_drought_typology(features: dict) -> dict[str, str]:
    """Classify the hydrologic drought typology from physical scenario features."""
    duration = features.get("duration_days", 90)
    onset = features.get("onset_month", 4)
    concurrence = features.get("concurrence", 0.0)
    dry_spell = features.get("max_dry_days", 0)
    percentile = features.get("historical_percentile", 0.5)

    # Typology Archetype
    if duration <= 90:
        if dry_spell >= 35:
            archetype = "Acute Flash Drought & Dry Run"
        else:
            archetype = "Seasonal Pulse Deficit"
    elif duration <= 210:
        if onset in (4, 5, 6):
            archetype = "Compound Spring-Summer Drought"
        elif onset in (7, 8, 9):
            archetype = "Acute Summer Heatwave Drought"
        else:
            archetype = "Multi-Season Catchment Deficit"
    else:
        archetype = "Chronic Multi-Year Drought"

    # Primary Loss Driver
    if onset in (5, 6, 7, 8) or features.get("high_priority_season_fraction", 0.0) > 0.5:
        primary_driver = "Evaporative Drawdown & Baseflow Starvation"
    elif onset in (3, 4, 5):
        primary_driver = "Spring Inflow & Storage Refill Failure"
    elif onset in (9, 10, 11):
        primary_driver = "Fall Baseflow Recession & Soil Desiccation"
    else:
        primary_driver = "Winter Baseflow Suppression"

    # Spatial Pattern
    if concurrence >= 0.65:
        spatial_pattern = "Synchronous Basin-Wide Inflow Failure"
    elif concurrence >= 0.35:
        spatial_pattern = "Regional Tributary Stress"
    else:
        spatial_pattern = "Localized Coastal Runoff Disconnect"

    # Inflow Vulnerability Tag
    if percentile >= 0.90 and concurrence >= 0.50:
        vulnerability = "Critical Inflow Starvation"
    elif percentile >= 0.75:
        vulnerability = "Elevated Regional Drawdown"
    else:
        vulnerability = "Moderate Operational Stress"

    return {
        "archetype": archetype,
        "primary_driver": primary_driver,
        "spatial_pattern": spatial_pattern,
        "vulnerability": vulnerability,
        "onset_name": MONTH_NAMES.get(onset, f"Month {onset}"),
    }


def draft_engineering_review_note(scenario, workspace=None) -> str:
    """Format an audit-grade, professional engineering review note for the scenario."""
    f = getattr(scenario, "features", {})
    duration = f.get("duration_days", 90)
    deficit_mm = f.get("deficit_mm", 0.0)
    deficit_in = deficit_mm / 25.4
    pct = f.get("historical_percentile", 0.0) * 100
    conc = f.get("concurrence", 0.0) * 100
    dry_spell = f.get("max_dry_days", 0)
    typo = classify_drought_typology(f)
    onset_name = typo["onset_name"]

    system_name = "regional storage"
    if workspace is not None:
        wss = getattr(workspace, "water_system_selection", None)
        if wss and hasattr(wss, "config") and hasattr(wss.config, "name"):
            system_name = wss.config.name

    lines = [
        f"[Engineering Assessment] Shortlisted as representative {typo['archetype'].lower()}.",
        f"• Physical profile: {duration}-day window ({onset_name} onset) with {deficit_in:.2f} in ({deficit_mm:.1f} mm) basin shortfall (≥{pct:.0f}% historical severity) and {conc:.0f}% station concurrence.",
        f"• Catchment impact: {dry_spell}-day dry spell suppresses tributary baseflow into upstream storage under {system_name}, coinciding with {typo['primary_driver'].lower()}.",
        f"• Modeling intent: Hand off to hydrologic modeling (HEC-HMS / Texas WAM) to evaluate storage resilience and conservation trigger timing under {typo['spatial_pattern'].lower()}."
    ]
    return "\n".join(lines)


def generate_scenario_interpretation(scenario, workspace=None, use_llm: bool = True) -> dict:
    """Generate plain-language operational narrative explaining the scenario outside raw numbers."""
    import logging
    logger = logging.getLogger(__name__)

    f = getattr(scenario, "features", {})
    duration = f.get("duration_days", 90)
    deficit_mm = f.get("deficit_mm", 0.0)
    deficit_in = deficit_mm / 25.4
    pct = f.get("historical_percentile", 0.0) * 100
    conc = f.get("concurrence", 0.0) * 100
    dry_spell = f.get("max_dry_days", 0)
    typo = classify_drought_typology(f)
    onset_name = typo["onset_name"]

    system_name = "Choke Canyon Reservoir + Lake Corpus Christi"
    if workspace is not None:
        wss = getattr(workspace, "water_system_selection", None)
        if wss and hasattr(wss, "config") and hasattr(wss.config, "name"):
            system_name = wss.config.name

    # Deterministic grounded narrative paragraphs explaining physical/operational meaning
    p1 = (
        f"This scenario represents a **{typo['archetype'].lower()}** beginning in **{onset_name}** spanning {duration} days. "
        f"Outside of the raw {deficit_in:.2f}-inch rainfall shortfall, the critical physical dynamic is **{typo['spatial_pattern'].lower()}**: "
        f"with **{conc:.0f}% station concurrence**, rainfall suppression is synchronized across the upper Nueces/Frio headwaters (San Antonio/Victoria) "
        f"and the coastal bend (Corpus Christi). Rather than isolated dry patches, tributary streamflows are starved simultaneously, "
        f"preventing regional runoff from reaching mainstem reservoir pools."
    )

    if dry_spell >= 30:
        dry_text = f"An extended dry spell of **{dry_spell} consecutive days** (< 1 mm/day) desiccates the soil mantle into an impermeable crust, impairing future infiltration efficiency and exacerbating agricultural drought."
    else:
        dry_text = f"Intermittent low-volume precipitation events punctuate the record, but remain insufficient to satisfy soil moisture deficits or generate measurable reservoir inflow."

    p2 = (
        f"From an operational water management perspective, the primary risk driver is **{typo['primary_driver'].lower()}**. "
        f"Because this shortfall intersects peak summer evaporation demand (often exceeding 0.35 inches/day in South Texas), "
        f"combined storage under **{system_name}** faces accelerated drawdown without inflow replenishment. {dry_text} "
        f"Screening this scenario ensures water planners and hydrologists evaluate whether municipal conservation triggers (Stage 2 / Stage 3) "
        f"must be enacted earlier to protect critical reserves against compound tributary failure."
    )

    narrative = f"{p1}\n\n{p2}"
    engine_used = "deterministic"

    # Optional local Qwen refinement if runtime is ready
    if use_llm:
        try:
            from basin_core.qwen_runtime import get_qwen_client
            client = get_qwen_client()
            if getattr(client, "status", None) == "ready":
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are the BASIN Senior Hydrologist. Synthesize a concise 2-paragraph operational and hydrologic interpretation "
                            "of the provided rainfall drought scenario. Explain what this scenario means physically and operationally outside the raw numbers: "
                            "focus on seasonal timing, tributary inflow starvation, evaporative drawdown, and reservoir risk. Do not hallucinate or change numbers."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Scenario: {getattr(scenario, 'id', 'B-001')}\n"
                            f"Duration: {duration} days, Onset: {onset_name}\n"
                            f"Net Shortfall: {deficit_in:.2f} in ({deficit_mm:.1f} mm), Historical Percentile: {pct:.0f}%\n"
                            f"Concurrence: {conc:.0f}%, Longest Dry Run: {dry_spell} days\n"
                            f"Typology: {typo['archetype']}, Spatial Pattern: {typo['spatial_pattern']}\n"
                            f"Primary Loss Driver: {typo['primary_driver']}, Water System: {system_name}"
                        )
                    }
                ]
                resp = client.generate(messages, temperature=0.2, max_tokens=350, timeout=5.0)
                content = resp.get("content", "").strip()
                if content and not resp.get("cancelled") and len(content) > 100:
                    narrative = content
                    engine_used = "qwen"
        except Exception as ex:
            logger.debug("Qwen inference skipped for scenario narrative: %s", ex)

    draft_note = draft_engineering_review_note(scenario, workspace)

    return {
        "typology": typo["archetype"],
        "primary_driver": typo["primary_driver"],
        "spatial_pattern": typo["spatial_pattern"],
        "vulnerability": typo["vulnerability"],
        "narrative": narrative,
        "draft_note": draft_note,
        "engine": engine_used,
    }


def attach_scenario_ai_interpretations(scenarios: list, workspace=None, use_llm: bool = True) -> None:
    """Attach AI operational narratives and draft engineering notes to scenarios."""
    for s in scenarios:
        if not getattr(s, "ai_narrative", ""):
            interp = generate_scenario_interpretation(s, workspace, use_llm=use_llm)
            s.ai_narrative = interp["narrative"]
            s.ai_draft_note = interp["draft_note"]
            s.ai_typology = interp["typology"]

