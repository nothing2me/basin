"""BASIN Professional Executive Brief PDF Generator.

Produces publication-grade, professionally organized executive reports for
city council members, regional planning boards, and technical water resource analysts.
Features dual-tier presentation:
  1. Executive Summary: Plain-language takeaways, action matrix, risk badges.
  2. Technical Engineering Appendix: Multi-tier stress spectrum, numerical tables,
     concurrence scores, and SHA-256 cryptographic audit trails.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence

from basin_core.analysis import (
    RESERVOIR_ASSUMPTIONS,
    simulate_reservoir_drawdown,
    simulate_stress_spectrum,
)

UNAVAILABLE = "Not available"

# BASIN's documented defaults. These are the values the simulator itself defaults to, so a
# report generated without a Review experiment reports the model's own starting point
# rather than a figure that looks like somebody's earlier choice.
DEFAULT_INITIAL_PCT = 0.48
DEFAULT_CONSERVATION_PCT = 0.0
DEFAULT_PIPELINE_ACTIVE = True
DEFAULT_TIERS: tuple[float, ...] = (1.0, 0.8, 0.6, 0.4)


@dataclass(frozen=True)
class ExperimentConfig:
    """The exact experiment settings a report was generated from.

    One instance is threaded through the preview, the vector report and the HTML report so
    the three cannot disagree about what was run. ``selected`` is true only when a person
    chose these values in Review; a default configuration says so rather than presenting
    BASIN's defaults as though they were a previous experiment.
    """

    initial_pct: float = DEFAULT_INITIAL_PCT
    conservation_pct: float = DEFAULT_CONSERVATION_PCT
    pipeline_active: bool = DEFAULT_PIPELINE_ACTIVE
    tiers: tuple[float, ...] = DEFAULT_TIERS
    scenario_id: str | None = None
    scenario_revision: int | None = None
    selected: bool = False

    def __post_init__(self) -> None:
        for label, value in (("Initial storage", self.initial_pct), ("Conservation", self.conservation_pct)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(label + " must be a fraction from 0 to 1")
        if type(self.pipeline_active) is not bool:
            raise ValueError("Pipeline availability must be true or false")
        tiers = tuple(float(t) for t in self.tiers)
        if not tiers or any(not math.isfinite(t) or t <= 0 for t in tiers):
            raise ValueError("Rainfall tiers must be a nonempty sequence of positive multipliers")
        object.__setattr__(self, "tiers", tiers)
        if self.scenario_revision is not None and (
            isinstance(self.scenario_revision, bool) or not isinstance(self.scenario_revision, int)
        ):
            raise ValueError("Scenario revision must be an integer")
        if self.scenario_id is not None and not isinstance(self.scenario_id, str):
            raise ValueError("Scenario identifier must be a string")

    @property
    def source_label(self) -> str:
        if self.selected:
            return "Selected in Review"
        return "BASIN default; no experiment was run in Review"

    @property
    def scenario_label(self) -> str:
        if not self.scenario_id:
            return "Not tied to a specific scenario"
        if self.scenario_revision is None:
            return self.scenario_id
        return f"{self.scenario_id} (revision {self.scenario_revision})"

    @property
    def tier_label(self) -> str:
        return ", ".join(f"{t * 100:.0f}%" for t in self.tiers)

    def describe_rows(self) -> list[tuple[str, str]]:
        """Label/value pairs rendered identically by the preview and both report paths."""
        return [
            ("Configuration source", self.source_label),
            ("Experiment scenario", self.scenario_label),
            ("Initial storage", f"{self.initial_pct * 100:.0f}% of combined capacity"),
            ("Emergency conservation", f"{self.conservation_pct * 100:.0f}% demand reduction"),
            ("Pipeline supply", "Assumed available" if self.pipeline_active else "Assumed unavailable"),
            ("Rainfall retention tiers", self.tier_label),
        ]

    def fingerprint(self) -> str:
        """Stable identity for cache keys, so a settings change invalidates a stale report."""
        return json.dumps(
            {
                "initial_pct": round(float(self.initial_pct), 6),
                "conservation_pct": round(float(self.conservation_pct), 6),
                "pipeline_active": bool(self.pipeline_active),
                "tiers": [round(float(t), 6) for t in self.tiers],
                "scenario_id": self.scenario_id,
                "scenario_revision": self.scenario_revision,
                "selected": bool(self.selected),
            },
            sort_keys=True,
        )


def resolve_config(config: ExperimentConfig | None, initial_pct=None, conservation_pct=None) -> ExperimentConfig:
    """Return the configuration to render with.

    An explicit config always wins. The older ``initial_pct``/``conservation_pct``
    arguments remain supported for direct callers and produce an unselected configuration,
    because values passed that way were never a recorded user choice.
    """
    if config is not None:
        if not isinstance(config, ExperimentConfig):
            raise ValueError("config must be an ExperimentConfig")
        return config
    return ExperimentConfig(
        initial_pct=DEFAULT_INITIAL_PCT if initial_pct is None else _as_fraction(initial_pct),
        conservation_pct=DEFAULT_CONSERVATION_PCT if conservation_pct is None else _as_fraction(conservation_pct),
    )


def _as_fraction(value) -> float:
    """Accept a percentage or a fraction, as the report entry points always have."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Storage and conservation settings must be finite numbers")
    return float(value) / 100.0 if value > 1.0 else float(value)


def report_state_token(workspace_id, accepted: Sequence, include_notes: bool,
                       include_custom: bool, config: ExperimentConfig) -> str:
    """Identity of everything a generated report depends on.

    Any change to the workspace, the accepted scenarios or their revisions, either consent
    flag, or the experiment settings produces a different token. Callers cache a generated
    report against its token and discard it when the token moves, so a stale report cannot
    remain available for download.
    """
    return json.dumps(
        {
            "workspace": workspace_id,
            "accepted": [[getattr(x, "id", None), getattr(x, "revision", None)] for x in accepted],
            "notes_consent": bool(include_notes),
            "custom_consent": bool(include_custom),
            "config": config.fingerprint(),
        },
        sort_keys=True,
    )


def select_primary_scenario(accepted: Sequence, config: ExperimentConfig):
    """Pick the scenario the experiment was configured on, without substituting silently.

    Returns ``(scenario, note)``. The note is non-empty whenever the report could not use
    the configured scenario, so the discrepancy is stated rather than hidden.
    """
    if not accepted:
        return None, None
    if not config.scenario_id:
        return accepted[0], None

    for scenario in accepted:
        if getattr(scenario, "id", None) == config.scenario_id:
            revision = getattr(scenario, "revision", None)
            if config.scenario_revision is not None and revision != config.scenario_revision:
                return None, (
                    f"The experiment was configured on {config.scenario_id} revision "
                    f"{config.scenario_revision}; the accepted revision is {revision}. "
                    "Reconfigure the experiment in Review; no replacement was simulated."
                )
            return scenario, None

    return None, (
        f"The experiment was configured on {config.scenario_id}, which is not among this "
        "report's accepted scenarios. Reconfigure in Review; no replacement was simulated."
    )


# Illustrative combined-storage bands. These mirror the bands the simulator applies in
# basin_core.analysis.simulate_reservoir_drawdown; tests/test_pdf_report.py pins them to
# the model's actual stage_num output so the report cannot drift away from the model.
ILLUSTRATIVE_BANDS: tuple[tuple[float, str], ...] = (
    (0.40, "Band 1"),
    (0.30, "Band 2"),
    (0.20, "Band 3"),
    (0.15, "Band 4"),
)

# TWDB volumetric survey figures recorded in research/incoming/BASIN_Research_Packet.md.
# They are a sourced external reference and deliberately differ from the model assumption
# above; the report states both rather than implying the model reproduces the surveys.
SURVEYED_CAPACITIES_ACFT = {"Lake Corpus Christi": 256062.0, "Choke Canyon": 662820.0}


def model_capacities_acft() -> dict[str, float]:
    """Per-reservoir capacities exactly as the reservoir model assumes them."""
    return {str(k): float(v) for k, v in RESERVOIR_ASSUMPTIONS["capacities_acft"].items()}


def model_total_capacity_acft() -> float:
    """Combined conservation-pool capacity used as the denominator by the model."""
    return float(sum(model_capacities_acft().values()))


def band_storage_acft(fraction: float) -> float:
    """Storage volume at a given fraction of the model's combined capacity."""
    return model_total_capacity_acft() * float(fraction)


def clip_text(text: str, limit: int) -> str:
    """Shorten text for fixed-width vector cells, marking that it was shortened."""
    text = str(text)
    return text if len(text) <= limit else text[: max(0, limit - 3)].rstrip() + "..."


@dataclass(frozen=True)
class ReportMetrics:
    """Facts computed from the illustrative reservoir experiment, for report rendering.

    ``unavailable_reason`` is set whenever the simulation could not be computed. Renderers
    must show an explicit unavailable state in that case; they must never substitute
    example or placeholder numbers, which would be indistinguishable from real results.
    """

    spectrum_data: dict | None = None
    sim_base: object | None = None
    sim_cons: object | None = None
    unavailable_reason: str | None = None
    earliest_breach_day: int | None = None
    tipping_point_tier: str | None = None
    day_base_stage3: int | None = None
    day_cons_stage3: int | None = None
    mean_evaporation_acft: float | None = None
    mean_served_demand_acft: float | None = None

    @property
    def available(self) -> bool:
        return self.unavailable_reason is None


def compute_report_metrics(primary_scenario, config: ExperimentConfig) -> ReportMetrics:
    """Run the illustrative experiment, or report why it could not be run.

    Shared by the HTML and vector renderers so the two paths cannot disagree about what
    was computed, about the settings it was computed under, or about whether anything was
    computed at all.
    """
    if primary_scenario is None:
        return ReportMetrics(unavailable_reason="no accepted scenario was supplied")

    series = getattr(primary_scenario, "series", None)
    if series is None or not len(series):
        return ReportMetrics(unavailable_reason="the primary scenario carries no daily rainfall series")

    try:
        spectrum_data = simulate_stress_spectrum(
            series,
            tiers=config.tiers,
            initial_pct=config.initial_pct,
            conservation_pct=config.conservation_pct,
            pipeline_active=config.pipeline_active,
        )
        sim_base = simulate_reservoir_drawdown(
            series,
            initial_pct=config.initial_pct,
            conservation_pct=0.0,
            pipeline_active=config.pipeline_active,
        )
        sim_cons = simulate_reservoir_drawdown(
            series,
            initial_pct=config.initial_pct,
            conservation_pct=config.conservation_pct,
            pipeline_active=config.pipeline_active,
        )
    except Exception as exc:
        return ReportMetrics(unavailable_reason=f"the simulation raised {type(exc).__name__}")

    earliest_breach_day: int | None = None
    tipping_point_tier: str | None = None
    for row in spectrum_data.get("summary_table", []):
        day3 = row.get("day_stage3_20")
        if day3 is not None and (earliest_breach_day is None or day3 < earliest_breach_day):
            earliest_breach_day = day3
            tipping_point_tier = row["tier_label"].split(" (")[0]

    def first_stage3(sim) -> int | None:
        return next((int(r["day"]) for _, r in sim.iterrows() if r["combined_pct"] <= 20.0), None)

    return ReportMetrics(
        spectrum_data=spectrum_data,
        sim_base=sim_base,
        sim_cons=sim_cons,
        earliest_breach_day=earliest_breach_day,
        tipping_point_tier=tipping_point_tier,
        day_base_stage3=first_stage3(sim_base),
        day_cons_stage3=first_stage3(sim_cons),
        mean_evaporation_acft=float(sim_base["evap_acft"].mean()) if len(sim_base) else None,
        mean_served_demand_acft=float(sim_base["served_demand_acft"].mean()) if len(sim_base) else None,
    )


def find_browser_executable() -> str | None:
    """Find a Chromium-based browser (Edge, Chrome, Chromium) for headless PDF rendering."""
    env_browser = os.environ.get("BASIN_BROWSER_PATH")
    if env_browser and Path(env_browser).exists():
        return env_browser

    candidates: list[str] = []

    if sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        prog_64 = os.environ.get("ProgramFiles", r"C:\Program Files")

        candidates.extend([
            rf"{prog_x86}\Microsoft\Edge\Application\msedge.exe",
            rf"{prog_64}\Microsoft\Edge\Application\msedge.exe",
            rf"{local_app}\Microsoft\Edge\Application\msedge.exe",
            rf"{prog_x86}\Google\Chrome\Application\chrome.exe",
            rf"{prog_64}\Google\Chrome\Application\chrome.exe",
            rf"{local_app}\Google\Chrome\Application\chrome.exe",
        ])
    elif sys.platform == "darwin":
        candidates.extend([
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ])
    else:
        for binary in ("msedge", "google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
            found = shutil.which(binary)
            if found:
                candidates.append(found)

    for path_str in candidates:
        p = Path(path_str)
        if p.exists() and p.is_file():
            return str(p.resolve())

    for name in ("msedge.exe", "msedge", "chrome.exe", "chrome", "google-chrome", "chromium"):
        found = shutil.which(name)
        if found:
            return found

    return None


def render_html_report(
    workspace,
    accepted: Sequence,
    initial_pct: float | None = None,
    conservation_pct: float | None = None,
    include_notes: bool = False,
    config: ExperimentConfig | None = None,
) -> str:
    """Build a professional, print-optimized HTML report ready for PDF rendering."""
    config = resolve_config(config, initial_pct, conservation_pct)
    init_frac = config.initial_pct
    cons_frac = config.conservation_pct

    primary_scenario, scenario_note = select_primary_scenario(accepted, config)
    metrics = compute_report_metrics(primary_scenario, config)
    spectrum_data = metrics.spectrum_data

    run_id = workspace.id
    created_date = workspace.created_at[:10] if getattr(workspace, "created_at", None) else "Current Session"
    snapshot_hash = workspace.source.manifest.get("sha256", "N/A")[:16]
    stations = ", ".join(workspace.params.stations)
    weights_summary = ", ".join(f"{k.capitalize()}: {v}%" for k, v in workspace.weights.items())
    primary_id = primary_scenario.id if primary_scenario else "None"

    manifest = getattr(workspace.source, "manifest", {}) or {}
    record_span = f"{manifest.get('start', 'unknown start')} to {manifest.get('end', 'unknown end')}"

    capacities = model_capacities_acft()
    total_capacity = model_total_capacity_acft()
    capacity_breakdown = "; ".join(f"{name} {value:,.0f} ac-ft" for name, value in capacities.items())
    surveyed_total = sum(SURVEYED_CAPACITIES_ACFT.values())
    surveyed_breakdown = "; ".join(f"{name} {value:,.0f} ac-ft" for name, value in SURVEYED_CAPACITIES_ACFT.items())

    unavailable_note = (
        "" if metrics.available
        else f"Simulation unavailable: {metrics.unavailable_reason}. No substitute figures are shown."
    )

    # Depletion window and tipping point
    if not metrics.available:
        depletion_range_val = UNAVAILABLE
        depletion_range_sub = unavailable_note
        tipping_point_tier = UNAVAILABLE
    elif metrics.earliest_breach_day is not None:
        m_low = max(1, int(metrics.earliest_breach_day / 30.4))
        depletion_range_val = f"~{m_low}–{m_low + 1} Months (Toy Model)*"
        depletion_range_sub = f"*Day {metrics.earliest_breach_day} in uncalibrated sim; NOT a forecast"
        tipping_point_tier = metrics.tipping_point_tier or UNAVAILABLE
    else:
        depletion_range_val = "No breach in modeled window*"
        depletion_range_sub = "*Storage >20% across modeled window (toy model)"
        tipping_point_tier = "No tier reached Stage 3 in sim"

    # Conservation mandate impact, measured as the difference between baseline and mandate runs
    day_base_3 = metrics.day_base_stage3
    day_cons_3 = metrics.day_cons_stage3

    if not metrics.available:
        conservation_val = UNAVAILABLE
        conservation_sub = unavailable_note
    elif day_base_3 is not None and day_cons_3 is not None:
        diff = day_cons_3 - day_base_3
        if diff > 0:
            conservation_val = f"+{diff} Days Gained*"
            conservation_sub = f"*Simulated deferral from Day {day_base_3} to Day {day_cons_3} ({cons_frac*100:.0f}% mandate)"
        elif diff < 0:
            conservation_val = f"{diff} Days*"
            conservation_sub = "*Accelerated under simulation settings"
        else:
            conservation_val = "0 Days*"
            conservation_sub = f"*Evaporation dominates at Day {day_base_3}"
    elif day_base_3 is not None and day_cons_3 is None:
        conservation_val = "Trigger Averted in Sim*"
        conservation_sub = "*Storage maintained >20% across entire modeled window"
    elif day_base_3 is None and day_cons_3 is None:
        conservation_val = "Buffer Intact*"
        conservation_sub = "*Storage remains >20% in baseline and conservation"
    else:
        conservation_val = "Threshold not reached in baseline*"
        conservation_sub = "*Baseline stayed above 20% while the mandate run did not"

    # Primary loss driver
    if metrics.available and metrics.mean_evaporation_acft is not None:
        loss_driver_val = f"{metrics.mean_evaporation_acft:,.0f} ac-ft/day"
        loss_driver_sub = f"Mean evaporation load (vs {metrics.mean_served_demand_acft:,.0f} ac-ft/day demand)"
    else:
        loss_driver_val = UNAVAILABLE
        loss_driver_sub = unavailable_note or "Simulation produced no rows"

    spectrum_html_rows = ""
    if spectrum_data and "summary_table" in spectrum_data:
        for r in spectrum_data["summary_table"]:
            status_badge = (
                '<span class="badge badge-success">Resilient in Sim</span>'
                if r["survived_critical_20pct"]
                else '<span class="badge badge-neutral">Simulated Trigger</span>'
            )
            d1 = f"Day {r['day_stage1_40']}*" if r.get("day_stage1_40") else "—"
            d2 = f"Day {r['day_stage2_30']}*" if r.get("day_stage2_30") else "—"
            d3 = f"Day {r['day_stage3_20']}*" if r.get("day_stage3_20") else "—"
            spectrum_html_rows += f"""
            <tr>
                <td><strong>{escape(r['tier_label'])}</strong></td>
                <td>{r['retention_pct']}%</td>
                <td><strong>{r['min_pct']:.1f}%</strong> ({r['min_acft']:,.0f} ac-ft)</td>
                <td>{d1}</td>
                <td>{d2}</td>
                <td><strong>{d3}</strong></td>
                <td>{status_badge}</td>
            </tr>
            """

    band_actions = {
        "Band 1": ("Public awareness notices, voluntary reduction targets, leak audit escalation.",
                   "Early demand dampening. Magnitude not modeled."),
        "Band 2": ("Restrictions on landscape irrigation and non-essential outdoor use.",
                   "Slows drawdown between bands. Magnitude not modeled."),
        "Band 3": ("Emergency curtailment across accounts; drought surcharge pricing.",
                   "Protects the minimum reserve. Magnitude not modeled."),
        "Band 4": ("Supply-emergency protocols prioritizing public health and safety.",
                   "Last band the model distinguishes before storage exhaustion."),
    }
    band_html_rows = ""
    for band_fraction, band_name in ILLUSTRATIVE_BANDS:
        actions, effect = band_actions[band_name]
        band_html_rows += (
            "<tr>"
            f"<td><strong>{escape(band_name)}</strong></td>"
            f"<td>&le; {band_fraction * 100:.0f}% ({band_storage_acft(band_fraction):,.0f} ac-ft)</td>"
            f"<td>{escape(actions)}</td>"
            f"<td>{escape(effect)}</td>"
            "</tr>"
        )

    if metrics.available:
        tipping_point_sub = "First tier breaching Stage 3 in sim*"
        overview_sentence = (
            f"Derived using primary scenario <strong>{escape(primary_id)}</strong> at "
            f"<strong>{init_frac * 100:.0f}% initial storage</strong>, it evaluates whether emergency "
            f"conservation ({cons_frac * 100:.0f}%) defers breaching the illustrative 20% reserve band (Stage 3)."
        )
    else:
        tipping_point_sub = unavailable_note
        overview_sentence = (
            f"It was intended to run at {init_frac * 100:.0f}% initial storage with "
            f"{cons_frac * 100:.0f}% emergency conservation, but no run was produced for this report."
        )

    # A compact single line: the print layout is two pages and a full table here pushes the
    # drought-band section onto a third. The app preview renders the same values as a table.
    described = config.describe_rows()
    config_summary_line = " · ".join(f"{label}: {value}" for label, value in described)
    config_note_html = (
        f'<p style="margin-top: 6px; font-weight: 600; color: #92400e;">{escape(scenario_note)}</p>'
        if scenario_note else ""
    )
    config_default_html = (
        ""
        if config.selected else
        '<p style="margin-top: 6px; color: #92400e; font-weight: 600;">No experiment was configured in Review. '
        'The settings above are BASIN\'s documented defaults, not a record of an earlier run.</p>'
    )

    unavailable_banner = (
        f'<p style="margin-top: 6px; font-weight: 600; color: #92400e;">{escape(unavailable_note)}</p>'
        if unavailable_note else ""
    )

    tier_count = len(spectrum_data.get("summary_table", [])) if spectrum_data else 0
    if metrics.available:
        spectrum_caption = (
            f"Simulated drawdown across {tier_count} rainfall tiers for {primary_id} starting at "
            f"{init_frac * 100:.0f}% initial storage with {cons_frac * 100:.0f}% emergency conservation. "
            "Asterisks mark days inside the uncalibrated modeled window."
        )
    else:
        spectrum_caption = f"Not computed for this report. {unavailable_note}"

    spectrum_unavailable_row = (
        '<tr><td colspan="7" style="text-align: center; color: #92400e; font-weight: 600;">'
        + escape(f"{UNAVAILABLE} — {unavailable_note or 'the stress spectrum produced no rows'}")
        + "</td></tr>"
    )

    scenario_html_rows = ""
    for s in accepted:
        prov = s.provenance
        feat = getattr(s, "features", {})
        deficit_mm = feat.get("deficit_mm", 0.0)
        concurrence = feat.get("concurrence", 0.0)

        # Privacy gate: omit private review notes unless explicitly opted in
        entry_note = (s.history[-1].get("private_note") or s.history[-1].get("note")) if s.history else None
        if include_notes and entry_note:
            note = entry_note
        elif entry_note:
            note = "Review note recorded (omitted: export privacy setting excludes private notes)"
        else:
            note = "No review note recorded."

        start_dt = prov.get("source_start")
        end_dt = prov.get("source_end")
        if not start_dt and hasattr(s, "series") and len(s.series):
            start_dt = str(s.series.index[0].date())
            end_dt = str(s.series.index[-1].date())
        duration_days = prov.get("source_window_days") or (len(s.series) if hasattr(s, "series") else "—")

        scenario_html_rows += f"""
        <tr>
            <td><strong class="font-mono">{escape(s.id)}</strong> (Rev {s.revision})</td>
            <td>{escape(str(start_dt))} to {escape(str(end_dt))}</td>
            <td>{duration_days} days</td>
            <td><strong>{deficit_mm:,.1f} mm</strong></td>
            <td>{concurrence:.2f}</td>
            <td class="text-sm italic">{escape(note)}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BASIN Executive Brief — {escape(run_id)}</title>
<style>
    @page {{
        size: letter;
        margin: 14mm 14mm 16mm 14mm;
        @bottom-right {{
            content: "Page " counter(page) " of " counter(pages);
            font-size: 8pt;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #64748b;
        }}
    }}
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #0f172a;
        background: #ffffff;
        font-size: 9pt;
        line-height: 1.45;
    }}
    .page-container {{
        width: 100%;
    }}
    .page-break {{
        page-break-before: always;
        margin-top: 15px;
    }}

    .header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 3px solid #087e8b;
        padding-bottom: 10px;
        margin-bottom: 14px;
    }}
    .brand-title {{
        font-size: 16pt;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #087e8b;
        line-height: 1.1;
    }}
    .brand-subtitle {{
        font-size: 8.5pt;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #475569;
        margin-top: 3px;
    }}
    .meta-box {{
        text-align: right;
        font-size: 8pt;
        color: #64748b;
    }}
    .meta-badge {{
        display: inline-block;
        background: #f1f5f9;
        color: #334155;
        font-weight: 700;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 7.5pt;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    .section-title {{
        font-size: 11pt;
        font-weight: 700;
        color: #0f172a;
        border-left: 4px solid #087e8b;
        padding-left: 8px;
        margin-top: 14px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }}

    .kpi-row {{
        display: flex;
        gap: 10px;
        margin-bottom: 12px;
    }}
    .kpi-card {{
        flex: 1;
        background: #f8fafc;
        border: 1.5px solid #cbd5e1;
        border-radius: 6px;
        padding: 9px 10px;
        text-align: center;
    }}
    .kpi-card.neutral {{
        background: #f8fafc;
        border-color: #cbd5e1;
    }}
    .kpi-card.warning {{
        background: #fffbeb;
        border-color: #fde68a;
    }}
    .kpi-label {{
        font-size: 7pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #475569;
    }}
    .kpi-card.warning .kpi-label {{ color: #92400e; }}
    .kpi-val {{
        font-size: 11pt;
        font-weight: 700;
        color: #0f172a;
        margin-top: 3px;
        line-height: 1.2;
    }}
    .kpi-sub {{
        font-size: 8pt;
        color: #64748b;
        margin-top: 3px;
        line-height: 1.25;
    }}

    .callout {{
        background: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 8.5pt;
        margin-bottom: 12px;
    }}
    .callout-title {{
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 4px;
        text-transform: uppercase;
        font-size: 7.5pt;
        letter-spacing: 0.5px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 8pt;
        margin-bottom: 12px;
    }}
    th {{
        background: #0f172a;
        color: #ffffff;
        font-weight: 600;
        text-align: left;
        padding: 5px 8px;
        font-size: 7.5pt;
        letter-spacing: 0.3px;
    }}
    td {{
        padding: 5px 8px;
        border-bottom: 1px solid #e2e8f0;
        color: #334155;
    }}
    tr:nth-child(even) td {{
        background: #f8fafc;
    }}

    .badge {{
        display: inline-block;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 7pt;
        font-weight: 700;
    }}
    .badge-success {{ background: #dcfce7; color: #166534; }}
    .badge-info {{ background: #e0f2fe; color: #0369a1; }}
    .badge-neutral {{ background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }}

    .seal-box {{
        margin-top: 15px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 10px 14px;
        background: #f8fafc;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .seal-text {{
        font-size: 7.5pt;
        color: #475569;
        line-height: 1.4;
    }}
    .seal-stamp {{
        border: 2px dashed #087e8b;
        border-radius: 6px;
        padding: 8px 16px;
        text-align: center;
        color: #087e8b;
        font-size: 7.5pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .font-mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    .italic {{ font-style: italic; }}
    .text-sm {{ font-size: 7.5pt; }}
</style>
</head>
<body>

<div class="page-container">
    <div class="header-bar">
        <div>
            <div class="brand-title">BASIN · EXECUTIVE TECHNICAL BRIEF</div>
            <div class="brand-subtitle">Coastal Bend Regional Water Supply Vulnerability Assessment</div>
        </div>
        <div class="meta-box">
            <div><span class="meta-badge">Companion Brief · Illustrative Simulation</span></div>
            <div><strong>Run ID:</strong> <span class="font-mono">{escape(run_id)}</span></div>
            <div><strong>Date:</strong> {escape(created_date)} · NOAA GHCN-Daily</div>
        </div>
    </div>

    <!-- Universal Top-of-Page Banner (Page 1) -->
    <div style="background: #f8fafc; border: 1.5px solid #94a3b8; border-left: 5px solid #087e8b; border-radius: 4px; padding: 8px 12px; margin-bottom: 12px; font-size: 8.5pt; color: #1e293b; line-height: 1.35;">
        <strong>⚠️ WHAT THIS DOCUMENT IS NOT:</strong>
        <span>NOT a hydrologic drought-of-record analysis · NOT a safe-yield or delivery forecast · NOT validated against actual streamflow or catchment runoff.</span>
    </div>

    <div class="callout">
        <div class="callout-title">The Bottom Line — Executive Overview</div>
        <p>This report presents human-reviewed rainfall stress scenarios and an <strong>illustrative reservoir drawdown experiment</strong> across the reservoirs the model represents ({escape(capacity_breakdown)}; combined <strong>{total_capacity:,.0f} ac-ft</strong>). {overview_sentence} <em>This simulation is an exploratory sensitivity tool, not an operational delivery forecast.</em></p>
        {unavailable_banner}
    </div>

    <p style="font-size: 7.5pt; color: #475569; margin: 2px 0 8px 0;"><strong>Experiment configuration:</strong> {escape(config_summary_line)}</p>
    {config_note_html}
    {config_default_html}

    <div class="kpi-row">
        <div class="kpi-card neutral">
            <div class="kpi-label">Illustrative Depletion Window (Stage 3)</div>
            <div class="kpi-val">{depletion_range_val}</div>
            <div class="kpi-sub">{depletion_range_sub}</div>
        </div>
        <div class="kpi-card neutral">
            <div class="kpi-label">Simulated Tipping Point Tier</div>
            <div class="kpi-val" style="font-size: 10.5pt; margin-top: 3px;">{escape(tipping_point_tier)}</div>
            <div class="kpi-sub">{escape(tipping_point_sub)}</div>
        </div>
        <div class="kpi-card neutral">
            <div class="kpi-label">Simulated Mandate Impact</div>
            <div class="kpi-val">{conservation_val}</div>
            <div class="kpi-sub">{conservation_sub}</div>
        </div>
        <div class="kpi-card neutral">
            <div class="kpi-label">Modeled Loss Driver</div>
            <div class="kpi-val" style="font-size: 10.5pt; margin-top: 3px;">{loss_driver_val}</div>
            <div class="kpi-sub">{loss_driver_sub}</div>
        </div>
    </div>

    <div class="section-title">Illustrative Drought Response Reference Framework</div>
    <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">
        <strong>Illustrative assumption, not adopted policy.</strong> The storage bands below are this experiment's own assumption ({escape(str(RESERVOIR_ASSUMPTIONS["thresholds"]))}). BASIN does not reproduce any adopted drought contingency ordinance, and the response categories listed are generic planning language rather than measures any authority has adopted. Confirm the currently adopted plan and any active declarations with the responsible utility before operational use.
    </p>
    <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">
        <strong>Capacity basis.</strong> Band volumes are computed against the model's assumed combined conservation-pool capacity of {total_capacity:,.0f} ac-ft ({escape(capacity_breakdown)}). That is the experiment's assumption, not a survey-verified figure. For comparison, the project research packet records TWDB volumetric survey values of {escape(surveyed_breakdown)} (combined {surveyed_total:,.0f} ac-ft). Reconciling the model assumption with the surveys is open work; this report does not claim the two agree.
    </p>
    <table>
        <thead>
            <tr>
                <th style="width: 22%;">Illustrative Band</th>
                <th style="width: 26%;">Combined Storage (model capacity)</th>
                <th style="width: 32%;">Generic Response Categories</th>
                <th style="width: 20%;">Intended Effect</th>
            </tr>
        </thead>
        <tbody>
            {band_html_rows}
        </tbody>
    </table>

    <div class="page-break"></div>

    <div class="header-bar" style="margin-top: 5px;">
        <div>
            <div class="brand-title" style="font-size: 13pt;">TECHNICAL APPENDIX · QUANTITATIVE STRESS SPECTRUM</div>
            <div class="brand-subtitle">Illustrative Storage Sensitivity & Scientific Provenance</div>
        </div>
        <div class="meta-box">
            <div><strong>Snapshot SHA-256:</strong> <span class="font-mono">{escape(snapshot_hash)}...</span></div>
        </div>
    </div>

    <!-- Page 2 Equal-Prominence Matrix Callout -->
    <div style="background: #fffbeb; border: 1.5px solid #f59e0b; border-radius: 6px; padding: 9px 12px; margin-bottom: 10px; font-size: 9.5pt; font-weight: 600; color: #92400e; line-height: 1.4;">
        ⚠️ ILLUSTRATIVE SENSITIVITY EXPERIMENT ONLY — NOT AN OPERATIONAL FORECAST<br>
        <span style="font-weight: 400; font-size: 8.5pt; color: #78350f;">Drawdown trajectories reflect an illustrative two-pool mass-balance with an uncalibrated inflow proxy ({escape(str(RESERVOIR_ASSUMPTIONS["inflow"]))}) and a fixed seasonal evaporation assumption. They do NOT represent safe yield, actual reservoir levels, or regulatory curtailment dates.</span>
    </div>

    <div class="section-title">Illustrative Storage Sensitivity Spectrum (Non-Predictive)</div>
    <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">{escape(spectrum_caption)}</p>
    <table>
        <thead>
            <tr>
                <th>Stress Tier</th>
                <th>Rainfall Retention</th>
                <th>Simulated Min Storage</th>
                <th>Stage 1 (40%)</th>
                <th>Stage 2 (30%)</th>
                <th>Stage 3 (20%)</th>
                <th>Simulated Outcome</th>
            </tr>
        </thead>
        <tbody>
            {spectrum_html_rows if spectrum_html_rows else spectrum_unavailable_row}
        </tbody>
    </table>

    <div class="section-title">Shortlisted Scenario Inventory & Human Review Notes</div>
    <table>
        <thead>
            <tr>
                <th>Scenario ID</th>
                <th>Source Window (NOAA GHCN-Daily)</th>
                <th>Duration</th>
                <th>Precip Deficit</th>
                <th>Concurrence</th>
                <th>Review Disposition & Notes</th>
            </tr>
        </thead>
        <tbody>
            {scenario_html_rows if scenario_html_rows else '<tr><td colspan="6" style="text-align: center; color: #64748b;">No accepted scenarios.</td></tr>'}
        </tbody>
    </table>

    <div class="section-title">Provenance & Verification Scope</div>
    <div class="seal-box">
        <div class="seal-text">
            <div><strong>Data Source:</strong> NOAA GHCN-Daily precipitation, {escape(record_span)} · Stations: {escape(stations)}</div>
            <div><strong>Shortlist Weights:</strong> {escape(weights_summary)}</div>
            <div><strong>What SHA-256 verification covers:</strong> the companion ZIP data bundle (daily_rainfall.csv, shortlist.csv, audit.json, snapshot), when that bundle is replayed. docs/verification_scope.md states the contract.</div>
            <div><strong>What it does not cover:</strong> <strong>this PDF is outside that contract.</strong> It is generated separately, is not part of the bundle inventory or its hashes, and a successful bundle replay establishes nothing about the figures or wording on these pages. No scientific validation or professional approval is claimed or implied.</div>
            <div><strong>Modeling Boundary:</strong> Reservoir drawdown is an illustrative planning experiment; point rainfall records are proxies and do not establish basin-wide calibrated inflow.</div>
            <div><strong>Bundle Replay Command:</strong> <span class="font-mono text-sm">python scripts/replay_bundle.py output/BASIN-{escape(run_id)}.zip</span></div>
        </div>
        <div class="seal-stamp">
            <div>VERIFICATION SCOPE</div>
            <div style="font-size: 8.5pt; font-weight: 800; line-height: 1.25;">BUNDLE ONLY<br>PDF NOT VERIFIED</div>
            <div class="font-mono" style="font-size: 6.5pt;">ID: {escape(run_id)}</div>
        </div>
    </div>
</div>

</body>
</html>
"""
    return html


class VectorPDFBuilder:
    """Zero-dependency pure-Python vector PDF generator compliant with PDF-1.4.
    
    Produces high-fidelity multi-page documents with vector tables, colored cards,
    rule lines, and typography without external dependencies.
    """

    def __init__(self) -> None:
        self.pages: list[list[str]] = []

    def add_page(self) -> list[str]:
        page: list[str] = []
        self.pages.append(page)
        return page

    def rect(
        self,
        page: list[str],
        x: float,
        y: float,
        w: float,
        h: float,
        fill: tuple[float, float, float] | None = None,
        stroke: tuple[float, float, float] | None = None,
        line_width: float = 1.0,
    ) -> None:
        ops: list[str] = []
        if stroke:
            ops.append(f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG {line_width:.2f} w")
        if fill:
            ops.append(f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re")
        if fill and stroke:
            ops.append("B")
        elif fill:
            ops.append("f")
        elif stroke:
            ops.append("S")
        page.append(" ".join(ops))

    def line(
        self,
        page: list[str],
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: tuple[float, float, float] = (0.8, 0.85, 0.9),
        line_width: float = 0.5,
    ) -> None:
        page.append(f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG {line_width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(
        self,
        page: list[str],
        x: float,
        y: float,
        txt: str,
        font: str = "/F1",
        size: float = 9.0,
        color: tuple[float, float, float] = (0.1, 0.1, 0.1),
    ) -> None:
        clean = (
            str(txt)
            .replace("–", "-")
            .replace("—", "--")
            .replace("·", "*")
            .replace("≤", "<=")
            .replace("≥", ">=")
            .replace("\\", "\\\\")
            .replace("(", r"\(")
            .replace(")", r"\)")
            .replace("\n", " ")
        )
        clean = clean.encode("latin1", "replace").decode("latin1")
        op = f"BT {font} {size:.1f} Tf {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm ({clean}) Tj ET"
        page.append(op)

    def render(self) -> bytes:
        num_pages = len(self.pages)
        if num_pages == 0:
            self.add_page()
            num_pages = 1

        catalog_id = 1
        pages_id = 2
        page_ids = [3 + i for i in range(num_pages)]
        content_ids = [3 + num_pages + i for i in range(num_pages)]
        f1_id = 3 + 2 * num_pages
        f2_id = f1_id + 1
        f3_id = f1_id + 2
        total_objs = f3_id

        objs: dict[int, str] = {}
        objs[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>"
        kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
        objs[pages_id] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>"

        for i in range(num_pages):
            pid = page_ids[i]
            cid = content_ids[i]
            objs[pid] = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Contents {cid} 0 R /Resources << /Font << "
                f"/F1 {f1_id} 0 R /F2 {f2_id} 0 R /F3 {f3_id} 0 R >> >> >>"
            )
            content = "\n".join(self.pages[i])
            c_bytes = content.encode("latin1")
            objs[cid] = f"<< /Length {len(c_bytes)} >>\nstream\n{content}\nendstream"

        objs[f1_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        objs[f2_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
        objs[f3_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"

        body = "%PDF-1.4\n"
        xref = ["xref", f"0 {total_objs + 1}", "0000000000 65535 f "]
        for i in range(1, total_objs + 1):
            xref.append(f"{len(body):010d} 00000 n ")
            body += f"{i} 0 obj\n{objs[i]}\nendobj\n"

        xref_pos = len(body)
        body += "\n".join(xref) + f"\ntrailer\n<< /Size {total_objs + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF"
        return body.encode("latin1")


def build_fallback_pdf(
    workspace_or_title,
    accepted_or_text=None,
    initial_pct: float | None = None,
    conservation_pct: float | None = None,
    include_notes: bool = False,
    config: ExperimentConfig | None = None,
) -> bytes:
    """Publication-grade pure-Python vector PDF generator.
    
    Renders the complete BASIN Executive Technical Brief with executive takeaways,
    multi-tier stress spectrum drawdown tables, approved scenario features,
    and cryptographic audit signatures. Supports both object and string inputs.
    """
    doc = VectorPDFBuilder()

    # Determine input mode (Workspace object vs Title string)
    config = resolve_config(config, initial_pct, conservation_pct)
    init_frac = config.initial_pct
    cons_frac = config.conservation_pct
    scenario_note: str | None = None

    if isinstance(workspace_or_title, str):
        # Title/body mode carries no session. Nothing about a run, snapshot or simulation
        # can be stated here, so every such field reports an explicit unavailable state.
        title = workspace_or_title
        body_text = str(accepted_or_text or "")
        run_id = UNAVAILABLE
        created_date = UNAVAILABLE
        stations = UNAVAILABLE
        snapshot_hash = UNAVAILABLE
        accepted = []
        metrics = compute_report_metrics(None, config)
    else:
        workspace = workspace_or_title
        accepted = list(accepted_or_text or [])
        run_id = str(workspace.id)
        created_date = workspace.created_at[:10] if getattr(workspace, "created_at", None) else UNAVAILABLE
        station_ids = list(getattr(getattr(workspace, "params", None), "stations", None) or [])
        stations = ", ".join(str(x) for x in station_ids) if station_ids else UNAVAILABLE
        manifest = getattr(getattr(workspace, "source", None), "manifest", None) or {}
        snapshot_hash = str(manifest.get("sha256", ""))[:16] or UNAVAILABLE
        title = f"BASIN Executive Technical Brief -- {run_id}"
        body_text = f"Evaluated {len(accepted)} accepted scenarios under {init_frac * 100:.0f}% starting storage."
        primary_scenario, scenario_note = select_primary_scenario(accepted, config)
        metrics = compute_report_metrics(primary_scenario, config)

    spectrum_data = metrics.spectrum_data
    unavailable_note = (
        "" if metrics.available
        else f"Simulation unavailable: {metrics.unavailable_reason}. No substitute figures are shown."
    )

    # Depletion window
    if not metrics.available:
        depletion_range_val = UNAVAILABLE
        depletion_range_sub = "*Not computed for this report"
    elif metrics.earliest_breach_day is not None:
        m_low = max(1, int(metrics.earliest_breach_day / 30.4))
        depletion_range_val = f"~{m_low}-{m_low + 1} Months (Toy Model)*"
        depletion_range_sub = f"*Day {metrics.earliest_breach_day} in uncalibrated sim"
    else:
        depletion_range_val = "No breach in window*"
        depletion_range_sub = "*Storage >20% across modeled window"

    # Conservation benefit
    day_base_3 = metrics.day_base_stage3
    day_cons_3 = metrics.day_cons_stage3
    if not metrics.available:
        conservation_val = UNAVAILABLE
        conservation_sub = "*Not computed for this report"
    elif day_base_3 is not None and day_cons_3 is not None:
        diff = day_cons_3 - day_base_3
        if diff > 0:
            conservation_val = f"+{diff} Days Gained*"
            conservation_sub = f"*Deferred Day {day_base_3} to Day {day_cons_3}"
        elif diff < 0:
            conservation_val = f"{diff} Days*"
            conservation_sub = "*Accelerated under these settings"
        else:
            conservation_val = "0 Days*"
            conservation_sub = "*Evaporation dominates storage"
    elif day_base_3 is not None and day_cons_3 is None:
        conservation_val = "Trigger Averted*"
        conservation_sub = "*Storage maintained above 20%"
    elif day_base_3 is None and day_cons_3 is None:
        conservation_val = "Buffer Intact*"
        conservation_sub = "*Threshold not breached in window"
    else:
        conservation_val = "Baseline Above 20%*"
        conservation_sub = "*Mandate run breached, baseline did not"

    # Dominant loss driver
    if metrics.available and metrics.mean_evaporation_acft is not None:
        loss_driver_val = f"{metrics.mean_evaporation_acft:,.0f} ac-ft/day*"
        loss_driver_sub = f"*Mean evaporation vs {metrics.mean_served_demand_acft:,.0f} demand"
    else:
        loss_driver_val = UNAVAILABLE
        loss_driver_sub = "*Not computed for this report"

    capacities = model_capacities_acft()
    total_capacity = model_total_capacity_acft()
    capacity_breakdown = "; ".join(f"{name} {value:,.0f}" for name, value in capacities.items())
    surveyed_total = sum(SURVEYED_CAPACITIES_ACFT.values())
    tier_count = len(spectrum_data.get("summary_table", [])) if spectrum_data else 0
    replay_line = (
        "* Bundle Replay Command: not applicable, this report was generated without a session"
        if run_id == UNAVAILABLE
        else f"* Bundle Replay Command: python scripts/replay_bundle.py output/BASIN-{run_id}.zip"
    )

    # ==========================================
    # PAGE 1: EXECUTIVE BRIEF & FRAMEWORK
    # ==========================================
    p1 = doc.add_page()

    # Top Header Banner
    doc.rect(p1, 36, 715, 540, 48, fill=(0.06, 0.09, 0.16))
    doc.text(p1, 50, 742, "BASIN EXECUTIVE TECHNICAL BRIEF", font="/F2", size=13.0, color=(1.0, 1.0, 1.0))
    doc.text(p1, 50, 727, "REGIONAL WATER PLANNING & DROUGHT RESILIENCE MEMORANDUM", font="/F2", size=7.5, color=(0.22, 0.74, 0.89))
    doc.text(p1, 415, 742, f"RUN ID: {run_id[:14]}", font="/F3", size=8.0, color=(0.85, 0.9, 0.95))
    doc.text(p1, 415, 727, f"DATE: {created_date} | PROVENANCE: NOAA", font="/F1", size=7.0, color=(0.65, 0.7, 0.75))

    # Warning Box: Non-Predictive Toy Model Disclaimer
    doc.rect(p1, 36, 642, 540, 60, fill=(0.99, 0.98, 0.94), stroke=(0.85, 0.65, 0.15), line_width=1.0)
    doc.text(p1, 48, 686, "WARNING: WHAT THIS ARTIFACT IS NOT", font="/F2", size=8.5, color=(0.7, 0.4, 0.05))
    doc.text(p1, 48, 672, "* NOT a safe-yield, firm-yield, or delivery forecast; uncalibrated toy planning model.", font="/F1", size=7.5, color=(0.3, 0.25, 0.1))
    doc.text(p1, 48, 660, "* NOT validated against actual streamflow, river routing losses, or surface evaporation.", font="/F1", size=7.5, color=(0.3, 0.25, 0.1))
    doc.text(p1, 48, 648, "* An illustrative stress experiment based on historical point-rainfall deficit series.", font="/F1", size=7.5, color=(0.3, 0.25, 0.1))

    # Section 1: Executive Overview Bottom Line
    doc.text(p1, 36, 622, "THE BOTTOM LINE -- EXECUTIVE OVERVIEW", font="/F2", size=10.0, color=(0.06, 0.09, 0.16))

    # 3 Metric Cards
    doc.rect(p1, 36, 548, 172, 64, fill=(0.96, 0.97, 0.99), stroke=(0.8, 0.85, 0.92))
    doc.text(p1, 46, 597, "ILLUSTRATIVE DEPLETION", font="/F2", size=7.5, color=(0.4, 0.45, 0.55))
    doc.text(p1, 46, 578, depletion_range_val, font="/F2", size=9.5, color=(0.08, 0.45, 0.55))
    doc.text(p1, 46, 558, depletion_range_sub[:34], font="/F1", size=6.5, color=(0.45, 0.5, 0.55))

    doc.rect(p1, 220, 548, 172, 64, fill=(0.96, 0.97, 0.99), stroke=(0.8, 0.85, 0.92))
    doc.text(p1, 230, 597, "CONSERVATION BENEFIT", font="/F2", size=7.5, color=(0.4, 0.45, 0.55))
    doc.text(p1, 230, 578, conservation_val, font="/F2", size=9.5, color=(0.1, 0.55, 0.35))
    doc.text(p1, 230, 558, conservation_sub[:34], font="/F1", size=6.5, color=(0.45, 0.5, 0.55))

    doc.rect(p1, 404, 548, 172, 64, fill=(0.96, 0.97, 0.99), stroke=(0.8, 0.85, 0.92))
    doc.text(p1, 414, 597, "DOMINANT LOSS DRIVER", font="/F2", size=7.5, color=(0.4, 0.45, 0.55))
    doc.text(p1, 414, 578, loss_driver_val, font="/F2", size=9.5, color=(0.75, 0.25, 0.2))
    doc.text(p1, 414, 558, loss_driver_sub[:34], font="/F1", size=6.5, color=(0.45, 0.5, 0.55))

    # Narrative Findings Box
    doc.rect(p1, 36, 424, 540, 110, fill=(0.98, 0.99, 1.0), stroke=(0.88, 0.9, 0.94))
    doc.text(p1, 48, 518, "KEY PLANNING FINDINGS & HYDROLOGIC CONTEXT", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    if not metrics.available:
        tier_finding = f"- {unavailable_note}"
    else:
        tier_finding = (
            f"- The 20% band ({band_storage_acft(0.20):,.0f} ac-ft of model capacity) is tested across "
            f"{tier_count} rainfall retention tiers; see page 2."
        )

    if not metrics.available:
        mandate_finding = "- Conservation effect not computed for this report."
    elif day_base_3 is not None and day_cons_3 is not None:
        verb = "deferred" if day_cons_3 > day_base_3 else "did not defer"
        mandate_finding = (
            f"- In this run the {cons_frac * 100:.0f}% mandate {verb} the 20% band "
            f"(baseline Day {day_base_3}, mandate Day {day_cons_3})."
        )
    elif day_base_3 is None and day_cons_3 is None:
        mandate_finding = "- Neither the baseline nor the mandate run reached the 20% band in the modeled window."
    else:
        mandate_finding = "- Baseline and mandate runs disagreed on reaching the 20% band; see page 2."

    findings = [
        f"- Combined storage across the model's reservoirs: {total_capacity:,.0f} ac-ft "
        f"({capacity_breakdown} ac-ft).",
        (f"- Tested under initial storage of {init_frac * 100:.0f}%, with {cons_frac * 100:.0f}% emergency demand reduction modeled."
         if metrics.available else
         f"- Requested settings were {init_frac * 100:.0f}% initial storage and {cons_frac * 100:.0f}% emergency demand reduction; nothing was simulated."),
        f"- Multi-station drought proxy reconstructed from NOAA GHCN-Daily stations: {clip_text(stations, 60)}.",
        tier_finding,
        mandate_finding,
        f"- {clip_text(body_text, 110)}",
    ]
    for offset, finding in enumerate(findings):
        colour = (0.3, 0.35, 0.4) if offset == len(findings) - 1 else (0.1, 0.1, 0.1)
        doc.text(p1, 48, 502 - offset * 13, clip_text(finding, 132), font="/F1", size=7.2, color=colour)

    # Drought Contingency Plan Reference Framework
    doc.text(p1, 36, 400, "ILLUSTRATIVE STORAGE BANDS USED BY THIS EXPERIMENT -- NOT ADOPTED POLICY", font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
    y_tbl = 382
    doc.rect(p1, 36, y_tbl - 18, 540, 18, fill=(0.08, 0.49, 0.55))
    doc.text(p1, 44, y_tbl - 13, "ILLUSTRATIVE BAND", font="/F2", size=7.5, color=(1, 1, 1))
    doc.text(p1, 150, y_tbl - 13, "COMBINED STORAGE", font="/F2", size=7.5, color=(1, 1, 1))
    doc.text(p1, 260, y_tbl - 13, "GENERIC RESPONSE CATEGORIES -- NOT ADOPTED BY ANY AUTHORITY", font="/F2", size=7.5, color=(1, 1, 1))

    band_actions = {
        "Band 1": ("Public awareness notices, voluntary reduction targets, leak audit escalation.",
                   "Generic planning language; effect on storage is not quantified here."),
        "Band 2": ("Restrictions on landscape irrigation and non-essential outdoor use.",
                   "Generic planning language; effect on storage is not quantified here."),
        "Band 3": ("Emergency curtailment across accounts; drought surcharge pricing.",
                   "Generic planning language; effect on storage is not quantified here."),
        "Band 4": ("Supply-emergency protocols prioritizing public health and safety.",
                   "Last band the model distinguishes before storage exhaustion."),
    }
    rows_framework = [
        (name,
         f"<= {fraction * 100:.0f}% ({band_storage_acft(fraction):,.0f} ac-ft)",
         band_actions[name][0],
         band_actions[name][1])
        for fraction, name in ILLUSTRATIVE_BANDS
    ]

    for idx, (stg, cap, act1, act2) in enumerate(rows_framework):
        y_r = y_tbl - 44 - (idx * 28)
        bg = (0.96, 0.97, 0.99) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        doc.rect(p1, 36, y_r, 540, 26, fill=bg)
        doc.text(p1, 44, y_r + 14, stg, font="/F2", size=7.5)
        doc.text(p1, 150, y_r + 14, cap, font="/F1", size=7.5)
        doc.text(p1, 260, y_r + 15, act1, font="/F1", size=6.8)
        doc.text(p1, 260, y_r + 5, act2, font="/F1", size=6.8)

    doc.text(p1, 36, 236, f"Band volumes use the model's assumed combined capacity of {total_capacity:,.0f} ac-ft ({capacity_breakdown} ac-ft).", font="/F1", size=6.8, color=(0.35, 0.4, 0.48))
    doc.text(p1, 36, 226, f"That is this experiment's assumption, not a survey-verified figure: the project research packet records TWDB volumetric", font="/F1", size=6.8, color=(0.35, 0.4, 0.48))
    doc.text(p1, 36, 216, f"survey values summing to {surveyed_total:,.0f} ac-ft. Reconciling the two is open work; this report does not claim they agree.", font="/F1", size=6.8, color=(0.35, 0.4, 0.48))

    # Experiment configuration actually used for every simulated figure in this report
    doc.rect(p1, 36, 96, 540, 108, fill=(0.98, 0.99, 1.0), stroke=(0.8, 0.85, 0.92))
    doc.text(p1, 48, 192, "EXPERIMENT CONFIGURATION USED FOR THIS REPORT", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    for row_index, (label, value) in enumerate(config.describe_rows()):
        row_y = 178 - row_index * 12
        doc.text(p1, 48, row_y, clip_text(label, 34), font="/F2", size=7.0, color=(0.35, 0.4, 0.48))
        doc.text(p1, 210, row_y, clip_text(value, 78), font="/F1", size=7.0)

    if scenario_note:
        doc.text(p1, 48, 104, clip_text(scenario_note, 130), font="/F1", size=6.8, color=(0.7, 0.4, 0.05))
    elif not config.selected:
        doc.text(p1, 48, 104, "No experiment was configured in Review; these are BASIN's documented defaults, not an earlier run.", font="/F1", size=6.8, color=(0.7, 0.4, 0.05))

    # Page 1 Footer
    doc.line(p1, 36, 50, 576, 50, stroke=(0.8, 0.85, 0.9))
    doc.text(p1, 36, 38, "BASIN Calculation Engine * Illustrative Planning Model", font="/F1", size=7.0, color=(0.45, 0.5, 0.55))
    doc.text(p1, 525, 38, "Page 1 of 2", font="/F2", size=7.0, color=(0.45, 0.5, 0.55))

    # ==========================================
    # PAGE 2: TECHNICAL APPENDIX & AUDIT
    # ==========================================
    p2 = doc.add_page()

    # Top Header Banner
    doc.rect(p2, 36, 715, 540, 48, fill=(0.06, 0.09, 0.16))
    doc.text(p2, 50, 742, "BASIN * TECHNICAL ENGINEERING APPENDIX", font="/F2", size=13.0, color=(1.0, 1.0, 1.0))
    doc.text(p2, 50, 727, "NUMERICAL SENSITIVITY SPECTRUM & SHORTLIST AUDIT", font="/F2", size=7.5, color=(0.22, 0.74, 0.89))
    doc.text(p2, 415, 742, f"RUN ID: {run_id[:14]}", font="/F3", size=8.0, color=(0.85, 0.9, 0.95))
    doc.text(p2, 415, 727, f"ACCEPTED: {len(accepted)} Scenarios", font="/F1", size=7.5, color=(0.65, 0.7, 0.75))

    # Section 1: Multi-Tier Stress Spectrum Drawdown Sensitivity
    doc.text(p2, 36, 692, "MULTI-TIER STRESS SPECTRUM DRAWDOWN SENSITIVITY (Non-Predictive)", font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
    y_spec = 672
    doc.rect(p2, 36, y_spec - 18, 540, 18, fill=(0.08, 0.49, 0.55))
    doc.text(p2, 42, y_spec - 13, "Stress Tier", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 135, y_spec - 13, "Retention", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 190, y_spec - 13, "Min Storage (% / ac-ft)", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 315, y_spec - 13, "Stage 1 (40%)", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 385, y_spec - 13, "Stage 2 (30%)", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 455, y_spec - 13, "Stage 3 (20%)", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 520, y_spec - 13, "Sim Status", font="/F2", size=7.0, color=(1, 1, 1))

    spec_rows = spectrum_data["summary_table"] if spectrum_data and "summary_table" in spectrum_data else []

    if not spec_rows:
        # No example or placeholder rows: an empty spectrum is reported as unavailable so a
        # reader can never mistake illustrative filler for a computed result.
        doc.rect(p2, 36, y_spec - 58, 540, 40, fill=(0.99, 0.96, 0.92), stroke=(0.85, 0.65, 0.15))
        doc.text(p2, 42, y_spec - 32, f"{UNAVAILABLE.upper()} -- STRESS SPECTRUM NOT COMPUTED FOR THIS REPORT", font="/F2", size=8.0, color=(0.7, 0.4, 0.05))
        doc.text(p2, 42, y_spec - 46, clip_text(unavailable_note or "The stress spectrum produced no rows.", 118), font="/F1", size=7.0, color=(0.4, 0.35, 0.2))

    for idx, r in enumerate(spec_rows[:4]):
        y_r = y_spec - 38 - (idx * 20)
        bg = (0.96, 0.97, 0.99) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        doc.rect(p2, 36, y_r, 540, 20, fill=bg)
        d1 = f"Day {r['day_stage1_40']}" if r.get("day_stage1_40") else "--"
        d2 = f"Day {r['day_stage2_30']}" if r.get("day_stage2_30") else "--"
        d3 = f"Day {r['day_stage3_20']}" if r.get("day_stage3_20") else "--"
        stat = "Resilient" if r.get("survived_critical_20pct") else "Triggered"
        stat_col = (0.1, 0.55, 0.35) if r.get("survived_critical_20pct") else (0.75, 0.25, 0.2)

        doc.text(p2, 42, y_r + 6, r["tier_label"].split(" (")[0][:18], font="/F2", size=7.0)
        doc.text(p2, 135, y_r + 6, f"{r['retention_pct']}%", font="/F1", size=7.0)
        doc.text(p2, 190, y_r + 6, f"{r['min_pct']:.1f}% ({r['min_acft']:,.0f} ac-ft)", font="/F2", size=7.0)
        doc.text(p2, 315, y_r + 6, d1, font="/F1", size=7.0)
        doc.text(p2, 385, y_r + 6, d2, font="/F1", size=7.0)
        doc.text(p2, 455, y_r + 6, d3, font="/F2", size=7.0)
        doc.text(p2, 520, y_r + 6, stat, font="/F2", size=7.0, color=stat_col)

    # Section 2: Approved Candidate Scenarios Table
    y_cand = 535
    doc.text(p2, 36, y_cand + 15, "SHORTLISTED CANDIDATE SCENARIOS (Accepted for Planning Analysis)", font="/F2", size=9.5, color=(0.06, 0.09, 0.16))
    doc.rect(p2, 36, y_cand - 18, 540, 18, fill=(0.12, 0.16, 0.24))
    doc.text(p2, 42, y_cand - 13, "Scenario ID", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 115, y_cand - 13, "Period Range", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 220, y_cand - 13, "Duration", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 275, y_cand - 13, "Deficit (mm)", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 345, y_cand - 13, "Concurrence", font="/F2", size=7.0, color=(1, 1, 1))
    doc.text(p2, 410, y_cand - 13, "Review Disposition & Note", font="/F2", size=7.0, color=(1, 1, 1))

    scen_rows = accepted if accepted else []
    if not scen_rows:
        doc.text(p2, 42, y_cand - 32, "No accepted scenarios were supplied for this report.", font="/F1", size=7.5, color=(0.45, 0.5, 0.55))
    for idx, s in enumerate(scen_rows[:6]):
        y_r = y_cand - 38 - (idx * 20)
        bg = (0.96, 0.97, 0.99) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        doc.rect(p2, 36, y_r, 540, 20, fill=bg)

        prov = getattr(s, "provenance", {})
        feat = getattr(s, "features", {})
        deficit_mm = feat.get("deficit_mm", 0.0)
        concurrence = feat.get("concurrence", 0.0)

        entry_note = (s.history[-1].get("private_note") or s.history[-1].get("note")) if getattr(s, "history", None) else None
        if include_notes and entry_note:
            note = str(entry_note)
        elif entry_note:
            note = "Review recorded (private note omitted per export privacy)"
        else:
            note = "Accepted candidate scenario"

        start_dt = prov.get("source_start")
        end_dt = prov.get("source_end")
        if not start_dt and hasattr(s, "series") and len(s.series):
            start_dt = str(s.series.index[0].date())
            end_dt = str(s.series.index[-1].date())
        duration_days = prov.get("source_window_days") or (len(s.series) if hasattr(s, "series") else "--")
        period_str = f"{str(start_dt)[:7]} to {str(end_dt)[:7]}"

        doc.text(p2, 42, y_r + 6, f"{s.id} (R{s.revision})", font="/F3", size=6.8)
        doc.text(p2, 115, y_r + 6, period_str, font="/F1", size=6.8)
        doc.text(p2, 220, y_r + 6, f"{duration_days} d", font="/F1", size=6.8)
        doc.text(p2, 275, y_r + 6, f"{deficit_mm:,.1f} mm", font="/F2", size=6.8)
        doc.text(p2, 345, y_r + 6, f"{concurrence:.2f}", font="/F1", size=6.8)
        doc.text(p2, 410, y_r + 6, clip_text(note, 35), font="/F1", size=6.5, color=(0.3, 0.35, 0.4))

    # Section 3: Scientific Provenance & Cryptographic Audit Trail
    y_aud = 275
    doc.rect(p2, 36, y_aud - 100, 540, 95, fill=(0.96, 0.97, 0.99), stroke=(0.8, 0.85, 0.92))
    doc.text(p2, 48, y_aud - 20, "PROVENANCE AND VERIFICATION SCOPE", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    doc.text(p2, 48, y_aud - 35, f"* Station Proxies: NOAA GHCN-Daily {clip_text(stations, 70)}.", font="/F1", size=7.0)
    doc.text(p2, 48, y_aud - 48, f"* SHA-256 Snapshot Digest: {snapshot_hash} (recorded identity; not verified by this document).", font="/F3", size=7.0)
    doc.text(p2, 48, y_aud - 61, "* Deficit recomputation is checked when the companion ZIP is replayed, not by this PDF.", font="/F1", size=7.0)
    doc.text(p2, 48, y_aud - 74, replay_line, font="/F3", size=7.0)
    doc.text(p2, 48, y_aud - 87, "* This PDF is outside the bundle verification contract. A successful replay establishes nothing", font="/F1", size=7.0, color=(0.4, 0.45, 0.5))
    doc.text(p2, 48, y_aud - 97, "  about these pages. No scientific validation or professional approval is claimed or implied.", font="/F1", size=7.0, color=(0.4, 0.45, 0.5))

    # Verification Scope Stamp
    doc.rect(p2, 480, y_aud - 92, 85, 76, fill=(1.0, 1.0, 1.0), stroke=(0.08, 0.49, 0.55), line_width=1.5)
    doc.text(p2, 489, y_aud - 30, "VERIFICATION", font="/F2", size=7.0, color=(0.08, 0.49, 0.55))
    doc.text(p2, 505, y_aud - 40, "SCOPE", font="/F2", size=7.0, color=(0.08, 0.49, 0.55))
    doc.text(p2, 492, y_aud - 56, "BUNDLE ONLY", font="/F2", size=8.0, color=(0.08, 0.49, 0.55))
    doc.text(p2, 487, y_aud - 68, "PDF NOT VERIFIED", font="/F2", size=6.5, color=(0.7, 0.4, 0.05))
    doc.text(p2, 488, y_aud - 82, f"ID: {clip_text(run_id, 13)}", font="/F3", size=6.5, color=(0.3, 0.35, 0.4))

    # Page 2 Footer
    doc.line(p2, 36, 50, 576, 50, stroke=(0.8, 0.85, 0.9))
    doc.text(p2, 36, 38, "BASIN Calculation Engine * Companion to the export bundle; not itself replay-verified", font="/F1", size=7.0, color=(0.45, 0.5, 0.55))
    doc.text(p2, 525, 38, "Page 2 of 2", font="/F2", size=7.0, color=(0.45, 0.5, 0.55))

    return doc.render()


def generate_pdf_report(
    workspace,
    accepted: Sequence,
    output_path: Path | str | None = None,
    initial_pct: float | None = None,
    conservation_pct: float | None = None,
    include_notes: bool = False,
    config: ExperimentConfig | None = None,
) -> bytes:
    """Generate a publication-grade PDF report.

    Renders a complete, professional multi-page vector PDF containing executive takeaways,
    4-tier stress spectrum sensitivity tables, shortlisted scenario features, and SHA-256
    cryptographic audit trails.
    """
    config = resolve_config(config, initial_pct, conservation_pct)
    browser_bin = find_browser_executable()
    pdf_bytes: bytes | None = None

    if browser_bin and sys.platform != "win32":
        html_content = render_html_report(
            workspace,
            accepted,
            include_notes=include_notes,
            config=config,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            html_file = tmp_path / f"report_{workspace.id}.html"
            pdf_file = tmp_path / f"report_{workspace.id}.pdf"
            html_file.write_text(html_content, encoding="utf-8")

            cmd = [
                browser_bin,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_file.resolve()}",
                str(html_file.resolve())
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=2)
                if pdf_file.exists() and pdf_file.stat().st_size > 1000:
                    pdf_bytes = pdf_file.read_bytes()
            except Exception:
                pdf_bytes = None

    if pdf_bytes is None:
        pdf_bytes = build_fallback_pdf(
            workspace,
            accepted,
            include_notes=include_notes,
            config=config,
        )

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(pdf_bytes)

    return pdf_bytes

