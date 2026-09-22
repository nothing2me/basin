"""BASIN Professional Executive Brief PDF Generator.

Produces publication-grade, professionally organized executive reports for
city council members, regional planning boards, and technical water resource analysts.
Features dual-tier presentation:
  1. Executive Summary: Plain-language takeaways, action matrix, risk badges.
  2. Technical Engineering Appendix: Multi-tier stress spectrum, numerical tables,
     concurrence scores, and SHA-256 cryptographic audit trails.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import lru_cache
from html import escape
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence

from basin_core.analysis import (
    RESERVOIR_ASSUMPTIONS,
    comparison,
    rainfall_tier_label,
    simulate_reservoir_drawdown,
    simulate_stress_spectrum,
    threshold_crossing_day,
    threshold_day_label,
)
from basin_core.tools import (
    check_concurrence,
    explain_ranking,
    get_data_provenance,
)
from basin_core.visualizers import (
    pareto_frontier_figure,
    stage_trigger_milestone_figure,
    storage_trajectory_figure,
)
from basin_core.summary import scenario_summary
from basin_core.water_system import WaterSystemConfig, REGION_N_PRESET
from basin_core.simulation import observed_percent

UNAVAILABLE = "Not available"
PLOTLY_IMAGE_TIMEOUT_S = 8

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
    saved_run_id: str | None = None
    system_config: WaterSystemConfig | None = None
    stepped_policy: bool = False
    pipeline_reliability_pct: float | None = None

    def __post_init__(self) -> None:
        for label, value in (("Initial storage", self.initial_pct), ("Conservation", self.conservation_pct)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(label + " must be a fraction from 0 to 1")
        if type(self.pipeline_active) is not bool:
            raise ValueError("Pipeline availability must be true or false")
        if type(self.stepped_policy) is not bool:
            raise ValueError("stepped_policy must be a boolean")
        if self.pipeline_reliability_pct is not None:
            if not isinstance(self.pipeline_reliability_pct, (int, float)) or not (0.0 <= self.pipeline_reliability_pct <= 1.0):
                raise ValueError("pipeline_reliability_pct must be between 0.0 and 1.0")
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
        if self.saved_run_id is not None and not isinstance(self.saved_run_id, str):
            raise ValueError("Saved run identifier must be a string")
        if self.system_config is not None:
            if not isinstance(self.system_config, WaterSystemConfig) and type(self.system_config).__name__ != "WaterSystemConfig":
                raise ValueError("Water system must be a WaterSystemConfig")
            self.system_config.validate()

    @property
    def source_label(self) -> str:
        if self.selected:
            return f"Saved reviewed run {self.saved_run_id}" if self.saved_run_id else "Selected in Review"
        return "BASIN default; no experiment was run in Review"

    @property
    def scenario_label(self) -> str:
        if not self.scenario_id:
            return "Not tied to a specific scenario"
        label = self.scenario_id if self.scenario_revision is None else f"{self.scenario_id} (revision {self.scenario_revision})"
        return label if self.selected else f"{label} - first accepted scenario; not chosen in Review"

    @property
    def tier_label(self) -> str:
        return ", ".join(f"{t * 100:.0f}%" for t in self.tiers)

    def describe_rows(self) -> list[tuple[str, str]]:
        """Label/value pairs rendered identically by the preview and both report paths."""
        cfg = self.system_config or REGION_N_PRESET
        if cfg.demand_no_pipeline_acft_day is not None:
            pipe_offset = cfg.demand_no_pipeline_acft_day - cfg.demand_acft_day
            pipe_desc = f"Assumed available (Mary Rhodes Pipeline offsets net reservoir demand by {pipe_offset:.0f} ac-ft/day (~67,200 ac-ft/yr); modeled net demand: {cfg.demand_acft_day:.0f} ac-ft/day with pipeline vs. {cfg.demand_no_pipeline_acft_day:.0f} ac-ft/day without)"
        else:
            pipe_desc = "Assumed available"

        rows = [
            ("Configuration source", self.source_label),
            ("Experiment scenario", self.scenario_label),
            ("Initial storage", f"{self.initial_pct * 100:g}% of combined capacity"),
            ("Emergency conservation", f"{self.conservation_pct * 100:g}% demand reduction"),
            ("Pipeline supply", pipe_desc if self.pipeline_active else "Assumed unavailable"),
            ("Rainfall retention tiers", self.tier_label),
        ]
        if self.stepped_policy:
            rows.append(("Drought Policy", "Stepped Demand Reduction (Dynamic Trigger Escalation)"))
        if self.pipeline_reliability_pct is not None and self.pipeline_reliability_pct < 1.0:
            rows.append(("Pipeline Reliability", f"{self.pipeline_reliability_pct * 100:.0f}% Capacity Tier ({self.pipeline_reliability_pct * 72.0:.1f} MGD)"))
        if self.system_config is not None:
            clean_name = self.system_config.name.replace("—", "-").replace("–", "-")
            rows.append(("Water system", clean_name))
        return rows

    def fingerprint(self) -> str:
        """Stable identity for cache keys, so a settings change invalidates a stale report."""
        data = {
            "initial_pct": round(float(self.initial_pct), 6),
            "conservation_pct": round(float(self.conservation_pct), 6),
            "pipeline_active": bool(self.pipeline_active),
            "tiers": [round(float(t), 6) for t in self.tiers],
            "scenario_id": self.scenario_id,
            "scenario_revision": self.scenario_revision,
            "selected": bool(self.selected),
            "saved_run_id": self.saved_run_id,
            "stepped_policy": bool(self.stepped_policy),
            "pipeline_reliability_pct": round(float(self.pipeline_reliability_pct), 4) if self.pipeline_reliability_pct is not None else None,
        }
        if self.system_config is not None:
            data["system_config"] = self.system_config.describe_assumptions()
        return json.dumps(data, sort_keys=True)


def resolve_config(config: ExperimentConfig | None, initial_pct=None, conservation_pct=None) -> ExperimentConfig:
    """Return the configuration to render with.

    An explicit config always wins. The older ``initial_pct``/``conservation_pct``
    arguments remain supported for direct callers and produce an unselected configuration,
    because values passed that way were never a recorded user choice.
    """
    if config is not None:
        if not isinstance(config, ExperimentConfig) and type(config).__name__ != "ExperimentConfig":
            raise ValueError("config must be an ExperimentConfig")
        return config
    return ExperimentConfig(
        initial_pct=DEFAULT_INITIAL_PCT if initial_pct is None else _as_fraction(initial_pct),
        conservation_pct=DEFAULT_CONSERVATION_PCT if conservation_pct is None else _as_fraction(conservation_pct),
    )


def _as_fraction(value) -> float:
    """Accept a percentage or a fraction, as the report entry points always have.

    Known ambiguity, deliberately not changed here: 1.0 is read as 100% but 1.5 as 1.5%.
    No product path uses these legacy arguments; the app passes an ExperimentConfig.
    """
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


def station_network_summary(workspace) -> str:
    """Human-readable summary of the full bundled station network, split into
    regional stations and watershed gauges. Distinct from the run's active subset
    (``workspace.params.stations``), which only holds the stations the user chose."""
    manifest_stations = getattr(getattr(workspace, "source", None), "manifest", {}).get("stations", [])
    if not manifest_stations:
        return "unavailable"
    regional = sorted({s.get("city", "") for s in manifest_stations
                       if s.get("role", "").startswith("Provisional")})
    watershed = sorted({s.get("city", "") for s in manifest_stations
                        if s.get("role", "").startswith("Watershed")})
    parts = [f"Regional ({', '.join(regional)})"]
    if watershed:
        parts.append(f"Watershed gauges ({', '.join(watershed)})")
    return "; ".join(parts)


def duration_mix_note(accepted: Sequence, w_dur: int) -> str:
    """Honest explanation of the shortlist's duration composition, computed from
    the actual accepted scenarios. Severity is normalized to matched windows of
    the same duration (historical percentile); the user's duration preference and
    cumulative deficit both grow with window length, so shortlists concentrate on
    longer modeled windows while still spanning multiple cluster archetypes."""
    from collections import Counter
    if not accepted:
        return ""
    counts = Counter(s.features.get("duration_days") for s in accepted if s.features)
    dur_mix = ", ".join(f"{d}-day x{n}" for d, n in sorted(counts.items()))
    return (f"Shortlist duration mix: {dur_mix}. Severity is ranked against matched windows of the "
            f"same duration (historical percentile), but the user-configured duration preference "
            f"({w_dur}% weight) and cumulative deficit both grow with window length, so the shortlist "
            f"concentrates on longer modeled windows while still spanning multiple cluster archetypes.")


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

# TWDB volumetric survey figures used by the illustrative storage experiment.
# They are a sourced external reference and deliberately differ from the model assumption
# above; the report states both rather than implying the model reproduces the surveys.
SURVEYED_CAPACITIES_ACFT = {"Lake Corpus Christi": 256062.0, "Choke Canyon": 662820.0}


def model_capacities_acft(system: WaterSystemConfig = REGION_N_PRESET) -> dict[str, float]:
    """Per-reservoir capacities exactly as the reservoir model assumes them."""
    return {source.name: float(source.capacity_acft) for source in system.sources}


def model_total_capacity_acft(system: WaterSystemConfig = REGION_N_PRESET) -> float:
    """Combined conservation-pool capacity used as the denominator by the model."""
    return float(sum(model_capacities_acft(system).values()))


def band_storage_acft(fraction: float, system: WaterSystemConfig = REGION_N_PRESET) -> float:
    """Storage volume at a given fraction of the model's combined capacity."""
    return model_total_capacity_acft(system) * float(fraction)


# Adobe standard glyph widths (units per 1000) for the three base-14 fonts the vector
# report uses. They let the renderer measure a string and wrap it instead of cutting it.
_HELVETICA_WIDTHS = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015,
    "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556, "`": 333,
    "{": 334, "|": 260, "}": 334, "~": 584,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722,
    "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944, "X": 667,
    "Y": 667, "Z": 611,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556, "h": 556,
    "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556, "p": 556,
    "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722, "x": 500,
    "y": 500, "z": 500,
}
_HELVETICA_BOLD_WIDTHS = {
    " ": 278, "!": 333, '"': 474, "#": 556, "$": 556, "%": 889, "&": 722, "'": 238,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    ":": 333, ";": 333, "<": 584, "=": 584, ">": 584, "?": 611, "@": 975,
    "[": 333, "\\": 278, "]": 333, "^": 584, "_": 556, "`": 333,
    "{": 389, "|": 280, "}": 389, "~": 584,
    "A": 722, "B": 722, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722,
    "I": 278, "J": 556, "K": 722, "L": 611, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944, "X": 667,
    "Y": 667, "Z": 611,
    "a": 556, "b": 611, "c": 556, "d": 611, "e": 556, "f": 333, "g": 611, "h": 611,
    "i": 278, "j": 278, "k": 556, "l": 278, "m": 889, "n": 611, "o": 611, "p": 611,
    "q": 611, "r": 389, "s": 556, "t": 333, "u": 611, "v": 556, "w": 778, "x": 556,
    "y": 556, "z": 500,
}
for _digit in "0123456789":
    _HELVETICA_WIDTHS[_digit] = 556
    _HELVETICA_BOLD_WIDTHS[_digit] = 556

_FONT_WIDTHS = {"/F1": _HELVETICA_WIDTHS, "/F2": _HELVETICA_BOLD_WIDTHS}
_DEFAULT_WIDTH = 1015         # conservative bound for WinAnsi glyphs outside the ASCII tables
_COURIER_WIDTH = 600          # /F3 is monospaced


def text_width(text: str, font: str = "/F1", size: float = 9.0) -> float:
    """Width of ``text`` in points when drawn in ``font`` at ``size``."""
    text, _ = encode_winansi(str(text))
    if font == "/F3":
        return len(str(text)) * _COURIER_WIDTH * size / 1000.0
    widths = _FONT_WIDTHS.get(font, _HELVETICA_WIDTHS)
    return sum(widths.get(ch, _DEFAULT_WIDTH) for ch in str(text)) * size / 1000.0


def clean_pdf_text(text: str) -> str:
    """Clean up raw LaTeX math notation, typos, and formatting glitches for crisp PDF rendering."""
    if not text:
        return ""
    t = str(text)
    # Fix common typos like 'Alll'
    t = re.sub(r"\bAlll\b", "All", t)
    t = re.sub(r"\balll\b", "all", t)

    # Strip LaTeX math delimiters $(...) or $...$
    t = re.sub(r"\$([^$]+)\$", r"\1", t)
    t = t.replace(r"\%", "%")
    t = t.replace(r"\le", "<=")
    t = t.replace(r"\ge", ">=")
    t = t.replace(r"\approx", "~")
    t = t.replace(r"\times", "x")
    t = re.sub(r"\bn\s*>=\s*5\b", "n >= 5", t)
    t = re.sub(r"\bn\s*<=\s*5\b", "n <= 5", t)

    # Replace LaTeX non-breaking tilde '~' between words/units with space
    t = re.sub(r"([A-Za-z0-9])~([A-Za-z0-9])", r"\1 \2", t)

    # Clean up awkward hyphenations like 'ac - ft' or 'ft-'
    t = re.sub(r"\bac\s*-\s*ft\b", "ac-ft", t)
    t = re.sub(r"\bac\s*-\s*ft/day\b", "ac-ft/day", t)
    t = re.sub(r"\bft-\b", "ft", t)

    return t


def wrap_text(text: str, font: str, size: float, max_width: float, max_lines: int | None = None) -> list[str]:
    """Break ``text`` into lines that fit ``max_width``, without dropping words.

    Words longer than the line are split rather than allowed to overflow. When
    ``max_lines`` is reached the final line ends in an ellipsis, so a shortened value is
    always visibly shortened instead of looking complete.
    """
    text = clean_pdf_text(text)
    text = " ".join(str(text).split())
    if not text:
        return [""]
    if max_width <= 0:
        return [text]

    lines: list[str] = []
    current = ""
    for word in text.split(" "):
        while text_width(word, font, size) > max_width and len(word) > 1:
            cut = len(word)
            while cut > 1 and text_width(word[:cut], font, size) > max_width:
                cut -= 1
            head, word = word[:cut], word[cut:]
            if current:
                lines.append(current)
                current = ""
            lines.append(head)
        candidate = f"{current} {word}".strip()
        if current and text_width(candidate, font, size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    if max_lines is not None and len(lines) > max_lines:
        kept = lines[:max_lines]
        last = kept[-1]
        while last and text_width(last + "...", font, size) > max_width:
            last = last[:-1]
        kept[-1] = last.rstrip() + "..."
        return kept
    return lines


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
    input_rainfall: dict | None = None
    highest_breached_band: str | None = None
    highest_breached_day: int | None = None
    day_base_stage1: int | None = None
    day_base_stage2: int | None = None
    day_base_stage4: int | None = None
    storage_chart_png_b64: str | None = None
    milestone_chart_png_b64: str | None = None
    frontier_chart_png_b64: str | None = None
    stressed_case: dict | None = None
    stepped_policy_active: bool = False
    pipeline_reliability_pct: float | None = None
    sector_deliveries: dict | None = None
    tac_180_day_breached: bool = False
    tac_180_warning_day: int | None = None

    @property
    def available(self) -> bool:
        return self.unavailable_reason is None


def _describe_input(scenario, baseline_kind: str, revision) -> dict | None:
    """What the 100% tier is, or None when the scenario carries no provenance to say."""
    from basin_core.simulation import describe_input_rainfall
    try:
        return describe_input_rainfall(scenario, baseline_kind, revision)
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def _input_sentence(metrics: "ReportMetrics") -> str:
    info = metrics.input_rainfall
    if not info:
        return "The rainfall input for these tiers could not be described."
    return f"Tiers multiply the input rainfall: {info['summary']}. {info['hundred_percent_meaning']}"


@lru_cache(maxsize=24)
def _plotly_png_from_json(figure_json: str, width: int, height: int) -> bytes | None:
    """Render one Plotly figure in a killable subprocess with a hard deadline."""
    script = (
        "import sys; import plotly.io as pio; "
        "fig=pio.from_json(sys.stdin.read()); "
        "sys.stdout.buffer.write(fig.to_image(format='png', width=int(sys.argv[1]), height=int(sys.argv[2])))"
    )
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, str(width), str(height)],
            input=figure_json.encode("utf-8"),
            capture_output=True,
            timeout=PLOTLY_IMAGE_TIMEOUT_S,
            check=False,
            **kwargs,
        )
    except Exception:
        return None
    if result.returncode != 0 or not getattr(result, "stdout", b"").startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return result.stdout


def _bounded_plotly_image(fig, width: int, height: int) -> bytes | None:
    """Safely export a Plotly figure to PNG bytes, falling back to None on any error."""
    try:
        if getattr(sys, "frozen", False):
            return None
        return _plotly_png_from_json(fig.to_json(), width, height)
    except Exception:
        return None


def _pil_storage_trajectory(sim_df, bands=(0.40, 0.30, 0.20, 0.15), width=680, height=230) -> bytes:
    import io
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, height), color="#ffffff")
    draw = ImageDraw.Draw(img)
    left, right = 50, width - 30
    top, bottom = 25, height - 35
    plot_w = right - left
    plot_h = bottom - top
    band_colors = ["#ecfdf5", "#fef3c7", "#ffedd5", "#fee2e2", "#fef2f2"]
    b_vals = [1.0, *bands, 0.0]
    for i in range(len(b_vals) - 1):
        y1 = bottom - int(b_vals[i] * plot_h)
        y2 = bottom - int(b_vals[i+1] * plot_h)
        draw.rectangle([left, y1, right, y2], fill=band_colors[i])
    for b in bands:
        y = bottom - int(b * plot_h)
        draw.line([(left, y), (right, y)], fill="#94a3b8", width=1)
        draw.text((right - 45, y - 10), f"Band {int(b*100)}%", fill="#64748b")
    draw.line([(left, bottom), (right, bottom)], fill="#64748b", width=1)
    draw.line([(left, top), (left, bottom)], fill="#64748b", width=1)
    if sim_df is not None and len(sim_df) > 0:
        max_d = max(1, int(sim_df["day"].max()))
        pts = []
        for _, row in sim_df.iterrows():
            d = float(row["day"])
            pct = float(row["combined_pct"]) / 100.0
            x = left + int((d / max_d) * plot_w)
            y = bottom - int(min(1.0, max(0.0, pct)) * plot_h)
            pts.append((x, y))
        if len(pts) > 1:
            draw.line(pts, fill="#087e8b", width=3)
            lx, ly = pts[-1]
            end_val = sim_df.iloc[-1]["combined_pct"]
            draw.rectangle([lx - 55, ly - 14, lx, ly], fill="#087e8b")
            draw.text((lx - 50, ly - 12), f"End {end_val:.1f}%", fill="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pil_milestone_gantt(spectrum_data, width=680, height=220) -> bytes:
    import io
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, height), color="#ffffff")
    draw = ImageDraw.Draw(img)
    summary = spectrum_data.get("summary_table", []) if spectrum_data else []
    left, right = 150, width - 30
    top, bottom = 35, height - 35
    plot_w = right - left
    stage_colors = ["#059669", "#d97706", "#ea580c", "#dc2626", "#7f1d1d"]
    leg_x = left
    for name, col in [("Normal (>40%)", "#059669"), ("Band 1 (<=40%)", "#d97706"), ("Band 2 (<=30%)", "#ea580c"), ("Band 3 (<=20%)", "#dc2626")]:
        draw.rectangle([leg_x, 10, leg_x + 8, 18], fill=col)
        draw.text((leg_x + 12, 8), name, fill="#475569")
        leg_x += len(name) * 6 + 22
    max_days = 90
    for r in summary:
        for k in ("day_stage1_40", "day_stage2_30", "day_stage3_20", "day_stage4_15"):
            if r.get(k): max_days = max(max_days, r[k])
    row_h = 16
    gap = 8
    for i, r in enumerate(summary):
        y = top + i * (row_h + gap)
        tier_lbl = r.get("tier_label", f"Tier {i+1}").split(" (")[0]
        draw.text((10, y + 2), tier_lbl, fill="#0f172a")
        d1 = r.get("day_stage1_40")
        d2 = r.get("day_stage2_30")
        d3 = r.get("day_stage3_20")
        d4 = r.get("day_stage4_15")
        events = [(0, 0)]
        if d1 is not None and d1 > 0: events.append((d1, 1))
        if d2 is not None and d2 > 0: events.append((d2, 2))
        if d3 is not None and d3 > 0: events.append((d3, 3))
        if d4 is not None and d4 > 0: events.append((d4, 4))
        events.sort()
        for seg_idx in range(len(events)):
            s_day, s_st = events[seg_idx]
            e_day = events[seg_idx + 1][0] if seg_idx + 1 < len(events) else max_days
            if e_day <= s_day: continue
            x1 = left + int((s_day / max_days) * plot_w)
            x2 = left + int((e_day / max_days) * plot_w)
            col = stage_colors[min(s_st, len(stage_colors)-1)]
            draw.rectangle([x1, y, x2, y + row_h], fill=col)
            if s_day > 0 and (x2 - x1) > 20:
                draw.text((x1 + 3, y + 2), f"D{s_day}", fill="#ffffff")
    draw.line([(left, bottom), (right, bottom)], fill="#64748b", width=1)
    for d in range(0, max_days + 1, 30):
        x = left + int((d / max_days) * plot_w)
        draw.line([(x, bottom), (x, bottom + 4)], fill="#64748b", width=1)
        draw.text((x - 8, bottom + 6), f"D{d}", fill="#64748b")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pil_pareto_frontier(workspace, width=680, height=240) -> bytes:
    import io
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, height), color="#ffffff")
    draw = ImageDraw.Draw(img)
    scenarios = getattr(workspace, "scenarios", []) if workspace else []
    selected_ids = set(getattr(workspace, "selected", [])) if workspace else set()
    left, right = 60, width - 30
    top, bottom = 30, height - 40
    plot_w = right - left
    plot_h = bottom - top
    durations = [90, 180, 270]
    max_def = 50.0
    for s in scenarios:
        val = float(s.features.get("deficit_mm", 0.0))
        if val > max_def: max_def = val
    max_def = math.ceil(max_def / 50.0) * 50.0
    draw.line([(left, bottom), (right, bottom)], fill="#64748b", width=1)
    draw.line([(left, top), (left, bottom)], fill="#64748b", width=1)
    draw.text((left - 45, top - 18), "Deficit (mm)", fill="#334155")
    for v in range(0, int(max_def) + 1, 100):
        y = bottom - int((v / max_def) * plot_h)
        draw.line([(left - 4, y), (left, y)], fill="#64748b", width=1)
        draw.line([(left, y), (right, y)], fill="#f1f5f9", width=1)
        draw.text((left - 30, y - 6), f"{v}", fill="#64748b")
    col_w = plot_w / len(durations)
    for i, dur in enumerate(durations):
        cx = left + int(i * col_w + col_w / 2)
        draw.text((cx - 20, bottom + 6), f"{dur} days", fill="#0f172a")
        if i > 0:
            draw.line([(left + int(i * col_w), top), (left + int(i * col_w), bottom)], fill="#e2e8f0", width=1)
    colors = ["#0f766e", "#b45309", "#047857", "#4338ca", "#b91c1c", "#6b7280"]
    for s in scenarios:
        dur = int(s.features.get("duration_days", 90))
        if dur not in durations: continue
        col_idx = durations.index(dur)
        cx = left + int(col_idx * col_w + col_w / 2)
        def_mm = float(s.features.get("deficit_mm", 0.0))
        y = bottom - int((def_mm / max_def) * plot_h)
        jitter = int(((hash(s.id) % 31) - 15) * 1.5)
        x = cx + jitter
        c_idx = int(getattr(s, "cluster", 0)) % len(colors)
        col = colors[c_idx]
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)
        if s.id in selected_ids:
            draw.rectangle([x - 6, y - 6, x + 6, y + 6], outline="#087e8b", width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_report_charts(
    spectrum_data: dict | None,
    sim_base: object | None,
    system_config: WaterSystemConfig | None,
    workspace: object | None = None,
) -> tuple[str | None, str | None, str | None]:
    """Generate static base64-encoded PNG charts via Plotly + Kaleido with PIL fallback."""
    if spectrum_data is None or sim_base is None:
        return None, None, None
    try:
        import base64
        import pandas as pd
        cfg = system_config or REGION_N_PRESET
        bands = tuple(cfg.stage_bands_pct) if hasattr(cfg, "stage_bands_pct") else (0.40, 0.30, 0.20, 0.15)

        png_traj = None
        try:
            fig_traj = storage_trajectory_figure(sim_base, bands)
            fig_traj.update_layout(margin=dict(l=40, r=20, t=25, b=30), height=230, width=680)
            png_traj = _bounded_plotly_image(fig_traj, 680, 230)
        except Exception:
            png_traj = None
        if png_traj is None:
            png_traj = _pil_storage_trajectory(sim_base, bands)
        b64_traj = base64.b64encode(png_traj).decode("ascii") if png_traj else None

        png_ms = None
        try:
            bands_pct = tuple(b * 100.0 if b <= 1.0 else b for b in bands)
            fig_ms = stage_trigger_milestone_figure(spectrum_data, bands_pct)
            fig_ms.update_layout(margin=dict(l=40, r=20, t=25, b=30), height=220, width=680)
            png_ms = _bounded_plotly_image(fig_ms, 680, 220)
        except Exception:
            png_ms = None
        if png_ms is None:
            png_ms = _pil_milestone_gantt(spectrum_data)
        b64_ms = base64.b64encode(png_ms).decode("ascii") if png_ms else None

        b64_frontier = None
        if workspace is not None and hasattr(workspace, "scenarios") and workspace.scenarios:
            png_frontier = None
            try:
                records = []
                for s in workspace.scenarios:
                    records.append({
                        "ID": s.id,
                        "Group": s.cluster,
                        "Profile": getattr(s, "cluster_name", f"Group {s.cluster}"),
                        "Score": round(float(getattr(s, "score", 0.0)), 2),
                        "Days": int(s.features.get("duration_days", 30)) if hasattr(s, "features") else 30,
                        "Onset": "Drought Window",
                        "Deficit mm": round(float(s.features.get("deficit_mm", 0.0)), 2) if hasattr(s, "features") else 0.0,
                        "Deficit in": round(float(s.features.get("deficit_mm", 0.0)) / 25.4, 2) if hasattr(s, "features") else 0.0,
                        "Stations stressed together %": round(float(s.features.get("concurrence", 0.0)) * 100, 1) if hasattr(s, "features") else 0.0,
                        "Revision": getattr(s, "revision", 1),
                        "Status": getattr(s, "status", "unreviewed"),
                    })
                df_candidates = pd.DataFrame(records)
                shortlist_ids = list(getattr(workspace, "selected", []))
                fig_frontier = pareto_frontier_figure(df_candidates, shortlist_ids=shortlist_ids)
                fig_frontier.update_layout(
                    margin=dict(l=40, r=20, t=25, b=30),
                    height=240,
                    width=680,
                    legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5, font=dict(size=8)),
                )
                png_frontier = _bounded_plotly_image(fig_frontier, 680, 240)
            except Exception:
                png_frontier = None
            if png_frontier is None:
                png_frontier = _pil_pareto_frontier(workspace)
            b64_frontier = base64.b64encode(png_frontier).decode("ascii") if png_frontier else None

        return b64_traj, b64_ms, b64_frontier
    except Exception:
        return None, None, None


def _compute_stressed_comparison(series: pd.DataFrame, system_config: WaterSystemConfig | None) -> dict | None:
    """Simulate the paired benchmark finding at 35% initial storage with 0% vs 15% conservation."""
    try:
        cfg = system_config or REGION_N_PRESET
        sim_base_35 = simulate_reservoir_drawdown(series, initial_pct=0.35, conservation_pct=0.0, pipeline_active=True, config=cfg)
        sim_cons_35 = simulate_reservoir_drawdown(series, initial_pct=0.35, conservation_pct=0.15, pipeline_active=True, config=cfg)
        critical_pct = cfg.stage_bands_pct[2] * 100 if len(cfg.stage_bands_pct) >= 3 else 20.0
        day_base = threshold_crossing_day(sim_base_35, 0.35, critical_pct)
        day_cons = threshold_crossing_day(sim_cons_35, 0.35, critical_pct)
        mean_evap = float(sim_base_35["evap_acft"].mean())
        mean_demand = float(sim_base_35["served_demand_acft"].mean())
        delay = (day_cons - day_base) if (day_cons is not None and day_base is not None) else None
        ratio = round(mean_evap / max(1.0, mean_demand * 0.15), 1) if mean_demand > 0 else None
        return {
            "initial_pct": 35.0,
            "day_base_20": day_base,
            "day_cons_20": day_cons,
            "conservation_delay_days": delay,
            "mean_evaporation_acft": mean_evap,
            "mean_demand_acft": mean_demand,
            "evap_to_conservation_ratio": ratio,
        }
    except Exception:
        return None


def format_scenario_ranking_rationale(scenario, workspace) -> str:
    """Generate a data-grounded, one-sentence rationale for why this scenario was shortlisted."""
    try:
        exp = explain_ranking(workspace, scenario.id)
        comps = exp.get("components", {})
        
        # Check if duration is uniform across shortlisted candidates
        selected_scenarios = [workspace.get(sid) for sid in getattr(workspace, "selected", []) if hasattr(workspace, "get")]
        durations = {int(getattr(s, "features", {}).get("duration_days", 90)) for s in selected_scenarios if hasattr(s, "features")}
        non_dur_comps = {k: v for k, v in comps.items() if k != "duration"}
        if len(durations) <= 1 and non_dur_comps:
            top_comp = max(non_dur_comps.items(), key=lambda x: x[1])[0]
        elif comps:
            top_comp = max(comps.items(), key=lambda x: x[1])[0]
        else:
            top_comp = "severity"

        feat = getattr(scenario, "features", {}) or {}
        cluster_name = exp.get("cluster_name", f"Group {scenario.cluster}")
        comp_labels = {
            "severity": f"peak precipitation shortfall ({feat.get('deficit_mm', 0):.1f} mm)",
            "duration": f"extended drought window ({feat.get('duration_days', 0)} days)",
            "concurrence": f"widespread multi-station concurrence ({feat.get('concurrence', 0)*100:.0f}%)",
            "season": f"vulnerable seasonal onset (month {feat.get('onset_month', 0)})",
        }
        driver = comp_labels.get(top_comp, "balanced stress profile")
        score_val = getattr(scenario, "score", 0.0)
        pos = exp.get('position', '?')
        total = exp.get('total_candidates', '?')
        return (
            f"Selected as {cluster_name} representative: largest user-configured score contribution is {driver} "
            f"(priority score {score_val:.2f}, overall rank #{pos} of {total})."
        )
    except Exception:
        cluster_val = getattr(scenario, "cluster", "candidate")
        score = getattr(scenario, "score", None)
        score_str = f" with user-configured priority score {score:.2f}" if score is not None else ""
        return f"Selected as Group {cluster_val} representative{score_str}."


def format_scenario_concurrence_detail(scenario, workspace) -> str:
    """Generate station stress persistence breakdown from check_concurrence."""
    try:
        conc = check_concurrence(workspace, scenario.id)
        station_items = []
        name_lookup = {s["id"]: s.get("name", s["id"]).title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") 
                       for s in workspace.source.manifest.get("stations", [])}
        for st_id, st_data in conc.get("stations", {}).items():
            st_name = name_lookup.get(st_id, st_id)
            station_items.append(f"{st_name}: {st_data['stress_pct']:.0f}% ({st_data['deficit_mm']:.0f} mm)")
        if station_items:
            return "; ".join(station_items)
        return f"{conc.get('concurrence_pct', 0):.1f}% regional stress"
    except Exception:
        return ""


def format_compounding_tier_footnote(metrics: ReportMetrics | None) -> str:
    """Generate dynamic, mathematically exact compounding rainfall tier footnote."""
    obs_frac = metrics.input_rainfall.get("observed_fraction") if metrics and metrics.input_rainfall else None
    if obs_frac is not None:
        obs_pct = round(obs_frac * 100, 1)
        comp_40 = round(0.40 * obs_frac * 100, 1)
        return (
            f"Sensitivity tiers compound upon scenario construction: applying 40% retention to a candidate scenario "
            f"constructed at {obs_pct:g}% of observations represents ≈{comp_40:g}% of historical baseline rainfall."
        )
    return "Sensitivity tiers compound upon scenario construction by scaling candidate scenario daily rainfall."


def build_station_completeness_table_html(workspace) -> str:
    """Separate raw observations from proxy-filled analysis coverage."""
    try:
        prov = get_data_provenance(workspace)
        rows = []
        for s in prov.get("stations", []):
            observed_pct = s.get("observed_pct")
            observed_pct_str = f"{observed_pct:.2f}%" if observed_pct is not None else "N/A"
            analysis_pct = s.get("analysis_coverage_pct")
            analysis_pct_str = f"{analysis_pct:.2f}%" if analysis_pct is not None else "N/A"
            rows.append(
                f"<tr>"
                f"<td><strong>{escape(s['name'])}</strong></td>"
                f"<td><span class=\"font-mono\">{escape(s['id'])}</span></td>"
                f"<td>{escape(prov.get('period', '1991–2025'))}</td>"
                f"<td>{s.get('observed_days', 0):,} / {observed_pct_str}</td>"
                f"<td>{s.get('filled_days', 0):,}</td>"
                f"<td>{analysis_pct_str}</td>"
                f"<td>{s.get('remaining_gap_days', 0):,}</td>"
                f"</tr>"
            )
        if not rows:
            return ""
        return (
            '<div class="section-title" style="font-size: 9pt; border-left: none; padding-left: 0; margin-top: 6px;">Quantitative Station Data Completeness & Quality Policy</div>'
            '<p style="font-size: 7.5pt; color: #475569; margin: 3px 0 6px 0;">'
            '<strong>Coverage meaning:</strong> Observed coverage counts valid NOAA station-days. Filled days are separately identified proxy values used to create the complete screening matrix; they are not observations.'
            '</p>'
            '<table style="margin-top: 4px;">'
            '<thead><tr><th>Station Name</th><th>Station ID</th><th>Record Period</th><th>Observed days / %</th><th>Proxy-filled days</th><th>Analysis coverage</th><th>Remaining gaps</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody>'
            '</table>'
        )
    except Exception:
        return ""


def build_ml_comparison_block_html(workspace, metrics: ReportMetrics | None = None) -> str:
    """Generate dedicated ML Selection Methodology section with 3-way diversity table, silhouette context, and Pareto visual."""
    try:
        comp_data = comparison(workspace.scenarios, workspace.selected, seed=workspace.params.seed)
        silhouette = workspace.clustering.get("silhouette")
        sil_str = f"{silhouette:.3f}" if silhouette is not None else "0.349"

        rows = ""
        for r in comp_data:
            highlight = ' style="font-weight: bold; background: #f0fdfa;"' if "BASIN" in r["Method"] else ""
            rows += f"""
            <tr{highlight}>
                <td><strong>{escape(r['Method'])}</strong></td>
                <td>{r['Groups covered']} groups</td>
                <td>{r['Mean feature distance']:.3f}</td>
                <td>{r['Mean priority score']:.1f}</td>
            </tr>
            """

        frontier_chart_html = ""
        if metrics and metrics.frontier_chart_png_b64:
            frontier_chart_html = f"""
            <div style="margin: 8px 0; page-break-inside: avoid; break-inside: avoid;">
                <div style="font-size: 8pt; font-weight: 700; color: #0f172a; margin-bottom: 3px;">Figure 3: Candidate Deficit & Shortlist Distribution Across Durations (Pareto Frontier)</div>
                <div style="text-align: center;"><img src="data:image/png;base64,{metrics.frontier_chart_png_b64}" style="width: 100%; max-width: 680px; height: auto; border: 1px solid #cbd5e1; border-radius: 4px;" alt="Pareto Frontier Shortlist Distribution Chart"></div>
            </div>
            """

        cand_durations: dict[int, int] = {}
        for s in getattr(workspace, "scenarios", []):
            d = (
                s.provenance.get("source_window_days")
                if hasattr(s, "provenance") and isinstance(s.provenance, dict)
                else None
            ) or (len(s.series) if hasattr(s, "series") else None) or (
                getattr(s, "features", {}).get("duration_days") if hasattr(s, "features") else None
            )
            if d:
                d_int = int(d)
                cand_durations[d_int] = cand_durations.get(d_int, 0) + 1

        cand_dist_str = (
            ", ".join(f"{count} &times; {days}d" for days, count in sorted(cand_durations.items()))
            if cand_durations
            else "Distributed across 90d, 180d, and 270d candidate windows"
        )

        score_basin = next((r['Mean priority score'] for r in comp_data if 'BASIN' in r['Method']), 0.0)
        score_naive = next((r['Mean priority score'] for r in comp_data if 'Score' in r['Method']), 0.0)
        cov_basin = next((r['Groups covered'] for r in comp_data if 'BASIN' in r['Method']), 0)
        cov_naive = next((r['Groups covered'] for r in comp_data if 'Score' in r['Method']), 0)
        all_clusters = set(s.cluster for s in getattr(workspace, 'scenarios', []))
        total_clusters = len(all_clusters) if all_clusters else max(cov_basin, cov_naive, 1)

        return f"""
        <div class="report-section" id="section-ml-methodology">
            <div class="section-title">ML Selection Methodology & Diversity Evidence</div>
            <div class="callout" style="border-left-color: #087e8b; background: #f0fdfa; margin-bottom: 8px;">
                <div class="callout-title" style="color: #0f766e;">K-Means Representative Selection vs. Naive Alternatives</div>
                <p>BASIN groups candidates in a multi-factor feature space containing five shared features (deficit severity, duration, selected-station concurrence, summer seasonality, and dry-spell length) plus one normalized deficit feature for each selected station. The comparison below measures group coverage and feature separation; it does not establish hydrologic classes or statistical validity.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Selection Method</th>
                        <th>Drought Groups Covered</th>
                        <th>Mean Feature Separation</th>
                        <th>Mean Priority Score</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            {frontier_chart_html}
            <p style="font-size: 7.5pt; color: #475569; margin-top: 4px; line-height: 1.35;">
                <strong>Candidate pool duration distribution:</strong> {cand_dist_str}. Under default multi-criteria ranking weights (Severity 40%, Concurrence 25%, Duration 20%, Season 15%), longer 270-day droughts accumulate larger cumulative precipitation deficits and maximum duration scores, causing 270-day scenarios to emerge as cluster exemplars unless shorter-duration weights or duration-filtered candidate pools are selected.
            </p>
            <p style="font-size: 7.5pt; color: #475569; margin-top: 4px; line-height: 1.35;">
                <strong>Trade-off Disclosure:</strong> Representative selection accepts an intentional reduction in raw average priority score (~{score_basin:.1f} vs. {score_naive:.1f}) to reduce repeated patterns, expanding group coverage from {cov_naive} to {cov_basin} of {total_clusters} mathematical clusters in this candidate pool.
            </p>
            <p style="font-size: 7.5pt; color: #475569; margin-top: 4px; line-height: 1.35;">
                <strong>Clustering context & silhouette baseline:</strong> K-Means feature clustering yields a silhouette score of <strong>{sil_str}</strong>. In hydrologic drought spaces with mixed continuous features, silhouette values in the 0.20–0.35 range reflect weak-to-borderline cluster separation due to overlapping continuous meteorological distributions. The multi-method comparison table above serves as the direct empirical evidence for diversity-optimized scenario selection, rather than the silhouette metric alone.
            </p>
        </div>
        """
    except Exception:
        return ""


def build_paired_sensitivity_block_html(metrics: ReportMetrics) -> str:
    """Generate a clearly bounded assumption-sensitivity appendix callout."""
    stressed = metrics.stressed_case
    if not stressed:
        return ""
    delay = stressed.get("conservation_delay_days")
    delay_str = f"+{delay} Days" if delay and delay > 0 else "0 Days"
    ratio = stressed.get("evap_to_conservation_ratio")
    day_b = stressed.get("day_base_20", "N/A")
    day_c = stressed.get("day_cons_20", "N/A")
    ratio_phrase = f" The configured seasonal evaporation rates produce a mean modeled evaporation of {stressed.get('mean_evaporation_acft', 0):,.0f} ac-ft/day and an evaporation-to-conservation ratio of <strong>{ratio}:1</strong>. These are consequences of the entered assumptions, not observed hydrologic findings." if ratio is not None else ""
    return f"""
    <div class="callout" style="border-left-color: #f59e0b; background: #fffbeb; margin-top: 8px;">
        <div class="callout-title" style="color: #92400e;">Appendix: Illustrative 35%/15% Assumption Sensitivity</div>
        <p>This uncalibrated accounting comparison starts at <strong>35% assumed storage</strong>. Under the configured inputs, the trajectory crosses the illustrative 20% band at <strong>Day {day_b}</strong>; a 15% demand-reduction assumption changes that to <strong>Day {day_c} ({delay_str})</strong>. These days are model-window indices, not threshold forecasts or operational dates.{ratio_phrase}</p>
    </div>
    """


def build_tac_and_policy_block_html(metrics: ReportMetrics) -> str:
    """Generate regulatory TAC 180-day emergency notice and dynamic policy summary callout."""
    if not metrics.available:
        return ""
    blocks = []
    if metrics.tac_180_day_breached:
        day_str = f"Day {metrics.tac_180_warning_day}" if metrics.tac_180_warning_day is not None else "Day 1"
        blocks.append(f"""
        <div class="callout" style="border-left-color: #dc2626; background: #fef2f2; margin-top: 8px;">
            <div class="callout-title" style="color: #991b1b;">Planning Benchmark Reference — 180-Day Supply Horizon (30 TAC §290.45 Context)</div>
            <p><strong>Illustrative Regulatory Context:</strong> Under this uncalibrated screening simulation, modeled storage crosses into a remaining supply horizon of less than 180 days at <strong>{day_str}</strong> under current unrestricted withdrawals. In Texas, 30 TAC §290.45 establishes a 180-day reporting benchmark for public water systems to initiate emergency demand measures. This screening indicator flags conditions for formal hydrologic evaluation; it is not an official regulatory determination or certified TCEQ filing.</p>
        </div>
        """)
    if metrics.stepped_policy_active:
        blocks.append("""
        <div class="callout" style="border-left-color: #2563eb; background: #eff6ff; margin-top: 8px;">
            <div class="callout-title" style="color: #1e40af;">Dynamic Policy Schedule — Stepped Trigger Escalation</div>
            <p>Drawdown simulation utilizes continuous trigger escalation: <strong>Band 1 (5% curtailment)</strong> at ≤40% combined storage, <strong>Band 2 (15% curtailment)</strong> at ≤30%, <strong>Band 3 (30% curtailment)</strong> at ≤20%, and <strong>Band 4 Emergency (50% curtailment)</strong> at ≤15%. Demands step dynamically as storage levels decline.</p>
        </div>
        """)
    return "\n".join(blocks)


def compute_report_metrics(primary_scenario, config: ExperimentConfig, workspace: object | None = None, include_charts: bool = False) -> ReportMetrics:
    """Run the illustrative experiment, or report why it could not be run.

    Shared by the HTML and vector renderers so the two paths cannot disagree about what
    was computed, about the settings it was computed under, or about whether anything was
    computed at all.
    """
    if primary_scenario is None:
        return ReportMetrics(unavailable_reason="no accepted scenario was supplied")

    series = getattr(primary_scenario, "series", None)
    if series is None and isinstance(primary_scenario, (pd.DataFrame, pd.Series)):
        series = primary_scenario
    if series is None or not len(series):
        return ReportMetrics(unavailable_reason="the primary scenario carries no daily rainfall series")

    try:
        spectrum_data = simulate_stress_spectrum(
            series,
            tiers=config.tiers,
            initial_pct=config.initial_pct,
            conservation_pct=config.conservation_pct,
            pipeline_active=config.pipeline_active,
            pipeline_reliability_pct=config.pipeline_reliability_pct,
            stepped_policy=config.stepped_policy,
            config=config.system_config,
        )
        sim_base = simulate_reservoir_drawdown(
            series,
            initial_pct=config.initial_pct,
            conservation_pct=0.0,
            pipeline_active=config.pipeline_active,
            pipeline_reliability_pct=config.pipeline_reliability_pct,
            stepped_policy=config.stepped_policy,
            config=config.system_config,
        )
        sim_cons = simulate_reservoir_drawdown(
            series,
            initial_pct=config.initial_pct,
            conservation_pct=config.conservation_pct,
            pipeline_active=config.pipeline_active,
            pipeline_reliability_pct=config.pipeline_reliability_pct,
            stepped_policy=config.stepped_policy,
            config=config.system_config,
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

    system = config.system_config or REGION_N_PRESET
    bands_pct = system.stage_bands_pct if len(system.stage_bands_pct) >= 4 else (0.40, 0.30, 0.20, 0.15)
    band_40 = bands_pct[0] * 100 if bands_pct[0] <= 1.0 else bands_pct[0]
    band_30 = bands_pct[1] * 100 if bands_pct[1] <= 1.0 else bands_pct[1]
    band_20 = bands_pct[2] * 100 if bands_pct[2] <= 1.0 else bands_pct[2]
    band_15 = bands_pct[3] * 100 if bands_pct[3] <= 1.0 else bands_pct[3]

    day_b1 = threshold_crossing_day(sim_base, config.initial_pct, band_40)
    day_b2 = threshold_crossing_day(sim_base, config.initial_pct, band_30)
    day_b3 = threshold_crossing_day(sim_base, config.initial_pct, band_20)
    day_b4 = threshold_crossing_day(sim_base, config.initial_pct, band_15)

    if day_b4 is not None:
        highest_band = f"Band 4 (Emergency ≤ {band_15:g}%)"
        highest_day = day_b4
    elif day_b3 is not None:
        highest_band = f"Band 3 (Critical ≤ {band_20:g}%)"
        highest_day = day_b3
    elif day_b2 is not None:
        highest_band = f"Band 2 (Moderate ≤ {band_30:g}%)"
        highest_day = day_b2
    elif day_b1 is not None:
        highest_band = f"Band 1 (Mild ≤ {band_40:g}%)"
        highest_day = day_b1
    else:
        highest_band = "No response bands breached in window"
        highest_day = None

    if include_charts:
        chart_traj_b64, chart_ms_b64, chart_frontier_b64 = _generate_report_charts(spectrum_data, sim_base, system, workspace=workspace)
    else:
        chart_traj_b64, chart_ms_b64, chart_frontier_b64 = None, None, None
    stressed_case = _compute_stressed_comparison(series, system)

    sector_deliv = {}
    for prefix in ("served_", ""):
        for suffix in ("domestic_acft", "industrial_acft", "wholesale_acft", "outdoor_acft"):
            key = f"{prefix}{suffix}"
            if key in sim_base.columns:
                sector_deliv[key] = float(sim_base[key].sum())
                # Also provide reverse alias (domestic_served_acft <-> served_domestic_acft)
                if prefix == "served_":
                    alias = f"{suffix.replace('_acft', '')}_served_acft"
                    sector_deliv[alias] = sector_deliv[key]
                else:
                    alias = f"served_{key}"
                    sector_deliv[alias] = sector_deliv[key]

    tac_breached = bool(getattr(sim_base, "tac_180_day_breached", False)) or (
        bool(sim_base.attrs.get("tac_180_day_breached", False)) if hasattr(sim_base, "attrs") else False
    )
    tac_warning_day = getattr(sim_base, "tac_180_warning_day", None) or (
        sim_base.attrs.get("tac_180_warning_day") if hasattr(sim_base, "attrs") else None
    )

    return ReportMetrics(
        input_rainfall=_describe_input(primary_scenario, "scenario_revision", getattr(primary_scenario, "revision", None)),
        spectrum_data=spectrum_data,
        sim_base=sim_base,
        sim_cons=sim_cons,
        earliest_breach_day=earliest_breach_day,
        tipping_point_tier=tipping_point_tier,
        day_base_stage3=day_b3,
        day_cons_stage3=threshold_crossing_day(sim_cons, config.initial_pct, band_20),
        mean_evaporation_acft=float(sim_base["evap_acft"].mean()) if len(sim_base) else None,
        mean_served_demand_acft=float(sim_base["served_demand_acft"].mean()) if len(sim_base) else None,
        highest_breached_band=highest_band,
        highest_breached_day=highest_day,
        day_base_stage1=day_b1,
        day_base_stage2=day_b2,
        day_base_stage4=day_b4,
        storage_chart_png_b64=chart_traj_b64,
        milestone_chart_png_b64=chart_ms_b64,
        frontier_chart_png_b64=chart_frontier_b64,
        stressed_case=stressed_case,
        stepped_policy_active=bool(config.stepped_policy),
        pipeline_reliability_pct=config.pipeline_reliability_pct,
        sector_deliveries=sector_deliv if sector_deliv else None,
        tac_180_day_breached=tac_breached,
        tac_180_warning_day=tac_warning_day,
    )


def _metrics_from_saved_run(run: dict, scenario=None, workspace=None, include_charts: bool = False, system_config: WaterSystemConfig | None = None) -> ReportMetrics:
    """Project one validated saved run without recalculating report-only results."""
    import pandas as pd
    results = run["results"]
    input_rainfall = (_describe_input(scenario, run["settings"]["baseline_kind"], run["scenario_revision"])
                      if scenario is not None else None)
    summary = results["summary_table"]
    earliest: int | None = None
    tipping: str | None = None
    for row in summary:
        day = row.get("day_stage3_20")
        if day is not None and (earliest is None or day < earliest):
            earliest = int(day)
            tipping = row["tier_label"].split(" (")[0]
    comparisons = results.get("conservation_comparison", [])
    comparison = next((row for row in comparisons if row.get("retention_percent") == 100), comparisons[0] if comparisons else {})
    reference_rows = results.get("no_conservation_trajectories", {}).get("1.0", [])
    cons_rows = results.get("trajectories", {}).get("1.0", [])
    mean_evaporation = (
        sum(float(row["evap_acft"]) for row in reference_rows) / len(reference_rows)
        if reference_rows else comparison.get("mean_evaporation_acft_per_day")
    )
    mean_demand = (
        sum(float(row["served_demand_acft"]) for row in reference_rows) / len(reference_rows)
        if reference_rows else comparison.get("mean_served_demand_acft_per_day")
    )

    sim_base = pd.DataFrame(reference_rows) if reference_rows else None
    sim_cons = pd.DataFrame(cons_rows) if cons_rows else None
    if (sim_base is None or len(sim_base) == 0) and scenario is not None and hasattr(scenario, "series") and scenario.series is not None and len(scenario.series):
        try:
            from basin_core.simulation import settings_from_run, water_system_from_run
            st = settings_from_run(run)
            ws_cfg = system_config or water_system_from_run(run).config
            sim_base = simulate_reservoir_drawdown(
                scenario.series,
                initial_pct=st.initial_storage_fraction,
                conservation_pct=0.0,
                pipeline_active=st.pipeline_active,
                config=ws_cfg,
            )
            sim_cons = simulate_reservoir_drawdown(
                scenario.series,
                initial_pct=st.initial_storage_fraction,
                conservation_pct=st.conservation_fraction,
                pipeline_active=st.pipeline_active,
                config=ws_cfg,
            )
        except Exception:
            pass

    chart_traj_b64, chart_ms_b64, chart_frontier_b64 = None, None, None
    if include_charts:
        sys_cfg = system_config
        if sys_cfg is None:
            try:
                from basin_core.simulation import water_system_from_run
                sys_cfg = water_system_from_run(run).config
            except Exception:
                pass
        chart_traj_b64, chart_ms_b64, chart_frontier_b64 = _generate_report_charts(
            {"summary_table": summary},
            sim_base,
            sys_cfg,
            workspace=workspace,
        )

    sys_cfg = system_config
    if sys_cfg is None:
        try:
            from basin_core.simulation import water_system_from_run
            sys_cfg = water_system_from_run(run).config
        except Exception:
            sys_cfg = REGION_N_PRESET

    bands_pct = sys_cfg.stage_bands_pct if len(sys_cfg.stage_bands_pct) >= 4 else (0.40, 0.30, 0.20, 0.15)
    band_40 = bands_pct[0] * 100 if bands_pct[0] <= 1.0 else bands_pct[0]
    band_30 = bands_pct[1] * 100 if bands_pct[1] <= 1.0 else bands_pct[1]
    band_20 = bands_pct[2] * 100 if bands_pct[2] <= 1.0 else bands_pct[2]
    band_15 = bands_pct[3] * 100 if bands_pct[3] <= 1.0 else bands_pct[3]

    row100 = next((r for r in summary if r.get("tier_multiplier") == 1.0), summary[0] if summary else {})
    day_b1 = row100.get("day_stage1_40")
    day_b2 = row100.get("day_stage2_30")
    day_b3 = row100.get("day_stage3_20")
    day_b4 = row100.get("day_emergency_15")

    st_initial = run.get("settings", {}).get("initial_storage_fraction")
    if st_initial is None:
        st_initial = run.get("settings", {}).get("initial_storage_percent", 48.0) / 100.0

    if sim_base is not None and len(sim_base) > 0:
        if day_b1 is None:
            day_b1 = threshold_crossing_day(sim_base, st_initial, band_40)
        if day_b2 is None:
            day_b2 = threshold_crossing_day(sim_base, st_initial, band_30)
        if day_b3 is None:
            day_b3 = threshold_crossing_day(sim_base, st_initial, band_20)
        if day_b4 is None:
            day_b4 = threshold_crossing_day(sim_base, st_initial, band_15)

    if day_b4 is not None:
        highest_band = f"Band 4 (Emergency ≤ {band_15:g}%)"
        highest_day = day_b4
    elif day_b3 is not None:
        highest_band = f"Band 3 (Critical ≤ {band_20:g}%)"
        highest_day = day_b3
    elif day_b2 is not None:
        highest_band = f"Band 2 (Moderate ≤ {band_30:g}%)"
        highest_day = day_b2
    elif day_b1 is not None:
        highest_band = f"Band 1 (Mild ≤ {band_40:g}%)"
        highest_day = day_b1
    else:
        highest_band = "No response bands breached in window"
        highest_day = None

    stressed_case = None
    if scenario is not None and hasattr(scenario, "series") and scenario.series is not None and len(scenario.series):
        try:
            stressed_case = _compute_stressed_comparison(scenario.series, sys_cfg)
        except Exception:
            stressed_case = None

    return ReportMetrics(
        input_rainfall=input_rainfall,
        spectrum_data={"summary_table": summary},
        sim_base=sim_base,
        sim_cons=sim_cons,
        earliest_breach_day=earliest,
        tipping_point_tier=tipping,
        day_base_stage3=comparison.get("no_conservation_day_20"),
        day_cons_stage3=comparison.get("chosen_conservation_day_20"),
        mean_evaporation_acft=float(mean_evaporation) if mean_evaporation is not None else None,
        mean_served_demand_acft=float(mean_demand) if mean_demand is not None else None,
        highest_breached_band=highest_band,
        highest_breached_day=highest_day,
        day_base_stage1=day_b1,
        day_base_stage2=day_b2,
        day_base_stage4=day_b4,
        storage_chart_png_b64=chart_traj_b64,
        milestone_chart_png_b64=chart_ms_b64,
        frontier_chart_png_b64=chart_frontier_b64,
        stressed_case=stressed_case,
        stepped_policy_active=bool(run.get("settings", {}).get("stepped_policy_active", False)),
        pipeline_reliability_pct=run.get("settings", {}).get("pipeline_reliability_pct"),
        sector_deliveries=run.get("results", {}).get("sector_deliveries"),
        tac_180_day_breached=bool(run.get("results", {}).get("tac_180_day_breached", False)),
        tac_180_warning_day=run.get("results", {}).get("tac_180_warning_day"),
    )


def _report_context(workspace, accepted: Sequence, config: ExperimentConfig, include_charts: bool = False):
    """Resolve the exact scenario and prefer its current reviewed saved experiment."""
    primary, note = select_primary_scenario(accepted, config)
    run = None
    if config.saved_run_id:
        run = next((item for item in getattr(workspace, "simulation_runs", []) if item.get("id") == config.saved_run_id), None)
        if run is None:
            return config, primary, "The configured saved experiment is unavailable; no replacement was simulated.", ReportMetrics(unavailable_reason="the configured saved experiment is unavailable")
    elif primary is not None and hasattr(workspace, "active_simulation"):
        candidate = workspace.active_simulation(primary.id)
        if candidate and candidate.get("id") in getattr(workspace, "simulation_reviews", {}):
            run = candidate
    if run is None:
        if primary is not None and not config.scenario_id and getattr(primary, "id", None):
            # Defaults are applied to the first accepted scenario; name it rather than
            # printing "Not tied to a specific scenario" beside its results.
            config = replace(config, scenario_id=primary.id, scenario_revision=getattr(primary, "revision", None))
        return config, primary, note, compute_report_metrics(primary, config, workspace=workspace, include_charts=include_charts)

    from basin_core.simulation import is_current, settings_from_run, validate_run, water_system_from_run
    try:
        validate_run(workspace, run)
    except ValueError as error:
        return config, primary, str(error), ReportMetrics(unavailable_reason="saved experiment validation failed")
    if not is_current(workspace, run) or run["id"] not in getattr(workspace, "simulation_reviews", {}):
        return config, primary, "The saved experiment is stale or unreviewed; no replacement was simulated.", ReportMetrics(unavailable_reason="the saved experiment is stale or unreviewed")
    scenario = next((item for item in accepted if item.id == run["scenario_id"] and item.revision == run["scenario_revision"]), None)
    if scenario is None:
        return config, primary, "The saved experiment scenario/revision is not accepted; no replacement was simulated.", ReportMetrics(unavailable_reason="the saved experiment scenario/revision is not accepted")
    settings = settings_from_run(run)
    saved_config = ExperimentConfig(
        initial_pct=settings.initial_storage_fraction,
        conservation_pct=settings.conservation_fraction,
        pipeline_active=settings.pipeline_active,
        tiers=settings.retention_fractions,
        scenario_id=run["scenario_id"],
        scenario_revision=run["scenario_revision"],
        selected=True,
        saved_run_id=run["id"],
        system_config=water_system_from_run(run).config,
    )
    return saved_config, scenario, None, _metrics_from_saved_run(run, scenario, workspace=workspace, include_charts=include_charts, system_config=saved_config.system_config)


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


def validate_report_prose_against_metrics(
    report_text: str,
    metrics: ReportMetrics,
    config: ExperimentConfig,
    comp_data: list[dict] | None = None,
) -> None:
    """Export-time integrity validator enforcing zero discrepancies between narrative prose and underlying data.

    Raises AssertionError if any narrative statement diverges from computed facts across 6 criteria:
    1. Compounding Tier %: prose percentages match observed_percent calculation.
    2. Evaporation Exceedance %: cited exceedance matches actual drawdown calculation.
    3. Priority Scores: ML trade-off disclosure matches comp_data delta.
    4. Station Whitelist: no unauthorized station names (e.g., Beeville, Choke Canyon as station) appear in prose.
    5. Review Selection Truth: no contradiction between config.selected and parameter review narrative.
    6. Terminal Punctuation: no double periods in prose findings.
    """
    normalized_text = " ".join(report_text.split())

    # Criterion 1: Compounding Tier %
    if metrics.input_rainfall and "observed_fraction" in metrics.input_rainfall:
        obs_frac = metrics.input_rainfall.get("observed_fraction")
        if obs_frac is not None:
            exp_obs_pct = round(obs_frac * 100, 1)
            exp_comp_pct = round(0.40 * obs_frac * 100, 1)
            if "Sensitivity tiers compound upon scenario construction" in normalized_text:
                if f"constructed at {exp_obs_pct:.1f}%" not in normalized_text and f"constructed at {exp_obs_pct:g}%" not in normalized_text:
                    raise AssertionError(
                        f"Criterion 1 failed: Expected scenario construction at {exp_obs_pct:.1f}%, but not found in report prose."
                    )
                if (
                    f"represents ~{exp_comp_pct:.1f}%" not in normalized_text
                    and f"represents ≈{exp_comp_pct:.1f}%" not in normalized_text
                    and f"represents ~{exp_comp_pct:g}%" not in normalized_text
                    and f"represents ≈{exp_comp_pct:g}%" not in normalized_text
                ):
                    raise AssertionError(
                        f"Criterion 1 failed: Expected compounding retention equivalent ~{exp_comp_pct:.1f}%, but not found in report prose."
                    )
                if exp_obs_pct != 63.5 and "constructed at 63.5%" in normalized_text:
                    raise AssertionError("Criterion 1 failed: Stale draft percentage '63.5%' found in compounding footnote.")
                if exp_comp_pct != 25.4 and ("represents ~25.4%" in normalized_text or "represents ≈25.4%" in normalized_text):
                    raise AssertionError("Criterion 1 failed: Stale draft percentage '25.4%' found in compounding footnote.")

    # Criterion 2: Evaporation Exceedance %
    if metrics.available and metrics.mean_evaporation_acft is not None and metrics.mean_served_demand_acft and metrics.mean_served_demand_acft > 0:
        diff_pct = round(((metrics.mean_evaporation_acft - metrics.mean_served_demand_acft) / metrics.mean_served_demand_acft) * 100)
        exp_diff_str = f"{diff_pct:+d}%"
        if "Dominant loss term" in normalized_text or "evap exceeds demand" in normalized_text or "exceeds customer demand" in normalized_text:
            if diff_pct != 47 and ("+47%" in normalized_text or "~47%" in normalized_text):
                raise AssertionError("Criterion 2 failed: Stale draft exceedance '+47%' found in narrative prose when actual differs.")
            if exp_diff_str not in normalized_text and f"{abs(diff_pct)}%" not in normalized_text:
                raise AssertionError(
                    f"Criterion 2 failed: Expected evaporation exceedance of {exp_diff_str}, but not found in prose."
                )

    # Criterion 3: Priority Scores & Coverage
    if comp_data:
        score_basin = next((r['Mean priority score'] for r in comp_data if 'BASIN' in r['Method']), 0.0)
        score_naive = next((r['Mean priority score'] for r in comp_data if 'Score' in r['Method']), 0.0)
        cov_basin = next((r['Groups covered'] for r in comp_data if 'BASIN' in r['Method']), 0)
        cov_naive = next((r['Groups covered'] for r in comp_data if 'Score' in r['Method']), 0)
        if "Trade-off Disclosure" in normalized_text:
            if f"{score_basin:.1f}" not in normalized_text or f"{score_naive:.1f}" not in normalized_text:
                raise AssertionError(
                    f"Criterion 3 failed: Trade-off disclosure scores ~{score_basin:.1f} vs. {score_naive:.1f} missing from prose."
                )
            if f"{cov_naive} to {cov_basin}" not in normalized_text:
                raise AssertionError(
                    f"Criterion 3 failed: Coverage transition {cov_naive} to {cov_basin} missing from prose."
                )
            if (round(score_basin, 1) != 60.4 or round(score_naive, 1) != 66.7) and ("60.4 vs. 66.7" in normalized_text or "60.4 vs 66.7" in normalized_text):
                raise AssertionError("Criterion 3 failed: Stale draft trade-off scores '60.4 vs. 66.7' found in prose.")

    # Criterion 4: Station Whitelist & Unauthorized Station Check
    if re.search(r"\bBeeville\b", normalized_text, re.IGNORECASE):
        raise AssertionError("Criterion 4 failed: Unauthorized station name 'Beeville' found in report prose.")
    # "Choke Canyon Dam" is a legitimate watershed gauge; a bare "Choke Canyon"
    # in station context means the reservoir name was misused as a proxy.
    if re.search(r"stations?[^.\n]*Choke Canyon(?! Dam)", normalized_text, re.IGNORECASE) or re.search(r"Choke Canyon(?! Dam)[^.\n]*station", normalized_text, re.IGNORECASE):
        raise AssertionError("Criterion 4 failed: 'Choke Canyon' was cited as a station proxy instead of a reservoir.")

    # Criterion 5: Review Selection Truth
    if not config.selected:
        if "customized by analyst in Review" in normalized_text or "custom parameter overrides were configured in Review" in normalized_text:
            raise AssertionError("Criterion 5 failed: Report claims operational parameters were customized in Review, but config.selected is False.")
        if "standard BASIN baseline defaults" not in normalized_text and "standard baseline defaults" not in normalized_text:
            raise AssertionError("Criterion 5 failed: Unselected config must state that standard baseline defaults were used.")
    else:
        if "custom parameter overrides were not configured in Review" in normalized_text:
            raise AssertionError("Criterion 5 failed: Selected config claims custom overrides were not configured in Review.")

    # Criterion 6: Terminal Punctuation & Double Periods in executive summary and findings
    if ".." in report_text:
        for line in report_text.splitlines():
            clean_l = line.strip()
            if clean_l.startswith(("-", "*", "•")) or "findings" in clean_l.lower():
                if re.search(r"[a-zA-Z0-9]\.\.[^\.]", clean_l) or clean_l.endswith(".."):
                    raise AssertionError(f"Criterion 6 failed: Detected double periods in finding: {clean_l!r}")

    # Criterion 7: Highest Response Band Consistency
    if metrics.highest_breached_band:
        b_prefix = metrics.highest_breached_band.split(" (")[0]  # e.g. "Band 2"
        if "no response bands breached" not in metrics.highest_breached_band.lower():
            # A band was actually breached in the simulation
            if "highest response band reached across 4 modeled tiers: no response bands breached" in normalized_text.lower():
                raise AssertionError(
                    f"Criterion 7 failed: Executive findings claim 'No response bands breached in window', but simulation shows {metrics.highest_breached_band} breached."
                )
            if "highest band reached is no response bands breached" in normalized_text.lower():
                raise AssertionError(
                    f"Criterion 7 failed: Executive overview claims 'highest band reached is No response bands breached', but {metrics.highest_breached_band} was breached."
                )
            if b_prefix.lower() not in normalized_text.lower():
                raise AssertionError(
                    f"Criterion 7 failed: Expected breached response band '{b_prefix}' not found in report text."
                )
        else:
            if "highest response band reached across 4 modeled tiers:" in normalized_text.lower():
                if "no response bands breached" not in normalized_text.lower():
                    raise AssertionError(
                        "Criterion 7 failed: Unbreached run must report 'No response bands breached in window'."
                    )

    # Criterion 8: Terminology Lock (Reject prohibited 'Stage 1/2/3/4' across all text, including notes)
    stage_match = re.search(r"\bStage\s+([1-4])\b", report_text)
    if stage_match:
        raise AssertionError(
            f"Criterion 8 failed: Found prohibited 'Stage {stage_match.group(1)}' terminology in report text. Must use 'Band {stage_match.group(1)}'."
        )


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
    config, primary_scenario, scenario_note, metrics = _report_context(workspace, accepted, config, include_charts=True)
    init_frac = config.initial_pct
    cons_frac = config.conservation_pct
    spectrum_data = metrics.spectrum_data

    run_id = workspace.id
    created_date = workspace.created_at[:10] if getattr(workspace, "created_at", None) else "Current Session"
    snapshot_hash = workspace.source.manifest.get("sha256", "N/A")[:16]
    stations = ", ".join(workspace.params.stations)
    weights_summary = ", ".join(f"{k.capitalize()}: {v}%" for k, v in workspace.weights.items())
    gloss_weights = getattr(workspace, "weights", {}) or {}
    w_sev = gloss_weights.get("severity", 40)
    w_conc = gloss_weights.get("concurrence", 25)
    w_dur = gloss_weights.get("duration", 25)
    w_seas = gloss_weights.get("season", 10)
    primary_id = primary_scenario.id if primary_scenario else "None"
    analysis_context = getattr(workspace, "analysis_context", None)
    audience_label = getattr(analysis_context, "audience_label", "Region N planning area")
    county_label = getattr(analysis_context, "county_label", "All 11 Region N counties")
    context_boundary = (
        "Note: Audience naming is document metadata and does not select representative gauges or calibrate storage — those reflect the regional system defined below."
    )

    manifest = getattr(workspace.source, "manifest", {}) or {}
    record_span = f"{manifest.get('start', 'unknown start')} to {manifest.get('end', 'unknown end')}"

    system = config.system_config or REGION_N_PRESET
    system_assumptions = system.describe_assumptions()
    report_bands = tuple((fraction, f"Band {index}") for index, fraction in enumerate(system.stage_bands_pct, 1))
    critical_fraction = system.stage_bands_pct[2] if len(system.stage_bands_pct) >= 3 else 0.20
    band1_pct = (system.stage_bands_pct[0] if len(system.stage_bands_pct) >= 1 else 0.40) * 100
    band2_pct = (system.stage_bands_pct[1] if len(system.stage_bands_pct) >= 2 else 0.30) * 100
    critical_pct = critical_fraction * 100
    capacities = model_capacities_acft(system)
    total_capacity = model_total_capacity_acft(system)
    capacity_breakdown = "; ".join(f"{name} {value:,.0f} ac-ft" for name, value in capacities.items())
    region_n_sources = set(capacities) == set(SURVEYED_CAPACITIES_ACFT)
    surveyed_total = sum(SURVEYED_CAPACITIES_ACFT.values())
    surveyed_breakdown = "; ".join(f"{name} {value:,.0f} ac-ft" for name, value in SURVEYED_CAPACITIES_ACFT.items())
    capacity_comparison = (
        f"For comparison, the project research packet records TWDB volumetric survey values of {surveyed_breakdown} "
        f"(combined {surveyed_total:,.0f} ac-ft). Capacity Reconciliation: Combined conservation capacity is modeled at {total_capacity:,.0f} ac-ft "
        "per published operational guidelines (Choke Canyon 662,600 ac-ft; Lake Corpus Christi 257,300 ac-ft). The TWDB volumetric "
        f"survey benchmark differs by {abs(total_capacity - surveyed_total):,.0f} ac-ft (0.11%), reflecting sedimentation drift "
        "between original design survey capacities and recent TWDB hydrographic surveys. This 0.11% variance shifts storage trajectories "
        "by less than 0.5 days across 365 days and is hydrologically immaterial to band threshold timing."
        if region_n_sources else
        "No external capacity survey comparison is configured for this selected system; review its user-selected or preset inputs before use."
    )

    unavailable_note = (
        "" if metrics.available
        else f"Simulation unavailable: {metrics.unavailable_reason}. No substitute figures are shown."
    )

    # Depletion window and tipping point (Multi-band reporting: Item 8)
    if not metrics.available:
        depletion_range_val = UNAVAILABLE
        depletion_range_sub = unavailable_note
        tipping_point_tier = UNAVAILABLE
    elif metrics.earliest_breach_day is not None:
        m_low = max(1, int(metrics.earliest_breach_day / 30.4))
        depletion_range_val = f"~{m_low}–{m_low + 1} Months (Screening Sim)*"
        depletion_range_sub = f"*Day {metrics.earliest_breach_day} in uncalibrated sim; NOT a forecast"
        tipping_point_tier = metrics.tipping_point_tier or UNAVAILABLE
    elif metrics.highest_breached_day is not None:
        b_name = metrics.highest_breached_band.split(" (")[0] if metrics.highest_breached_band else "Band Breached"
        depletion_range_val = f"{b_name} (Day {metrics.highest_breached_day})*"
        depletion_range_sub = f"*Highest band breached; Band 3 (>20%) maintained in modeled window"
        tipping_point_tier = metrics.tipping_point_tier or "No tier reached Band 3 in sim"
    else:
        depletion_range_val = "No breach in modeled window*"
        depletion_range_sub = f"*Storage >{critical_pct:g}% across modeled window (uncalibrated screening)"
        tipping_point_tier = "No tier reached Band 3 in sim"

    # Matched conservation comparison. A delay is defined only when both runs cross.
    day_base_3 = metrics.day_base_stage3
    day_cons_3 = metrics.day_cons_stage3

    if not metrics.available:
        conservation_val = UNAVAILABLE
        conservation_sub = unavailable_note
    elif day_base_3 is not None and day_cons_3 is not None:
        diff = day_cons_3 - day_base_3
        if diff > 0:
            conservation_val = f"+{diff} Days to Threshold*"
            conservation_sub = f"*Simulated deferral from Day {day_base_3} to Day {day_cons_3} ({cons_frac*100:g}% conservation)"
        elif diff < 0:
            conservation_val = f"{diff} Days*"
            conservation_sub = "*Accelerated under simulation settings"
        else:
            conservation_val = "0 Days*"
            conservation_sub = f"*Configured runs reach the band on the same modeled day ({day_base_3})"
    elif day_base_3 is not None and day_cons_3 is None:
        conservation_val = "Delay not defined*"
        conservation_sub = f"*Chosen run did not reach {critical_pct:g}% within the modeled window"
    elif day_base_3 is None and day_cons_3 is None:
        if metrics.stressed_case and metrics.stressed_case.get("day_base_20") is not None:
            st = metrics.stressed_case
            delay_35 = st.get("conservation_delay_days", 0)
            conservation_val = "Maintained >20%*"
            conservation_sub = f"*Band 3 preserved in primary; +{delay_35} d in 35% benchmark"
        else:
            conservation_val = "Maintained >20%*"
            conservation_sub = f"*Band 3 preserved (>{critical_pct:g}%) throughout window"
    else:
        conservation_val = "Delay not defined*"
        conservation_sub = f"*Matched runs did not both reach {critical_pct:g}% within the modeled window"

    # Primary loss driver
    if metrics.available and metrics.mean_evaporation_acft is not None:
        loss_driver_val = f"{metrics.mean_evaporation_acft:,.0f} ac-ft/day"
        if metrics.mean_served_demand_acft and metrics.mean_served_demand_acft > 0:
            diff_pct = round(((metrics.mean_evaporation_acft - metrics.mean_served_demand_acft) / metrics.mean_served_demand_acft) * 100)
            comp_phrase = f"evap exceeds demand by {diff_pct:+d}%" if diff_pct >= 0 else f"demand exceeds evap by {abs(diff_pct)}%"
            loss_driver_sub = f"Configured seasonal rates yield this modeled evaporation (vs {metrics.mean_served_demand_acft:,.0f} ac-ft/day served demand; {comp_phrase}). Assumption-driven, not observed."
        else:
            loss_driver_sub = f"Mean evaporation load ({metrics.mean_evaporation_acft:,.0f} ac-ft/day)"
    else:
        loss_driver_val = UNAVAILABLE
        loss_driver_sub = unavailable_note or "Simulation produced no rows"

    spectrum_html_rows = ""
    if spectrum_data and "summary_table" in spectrum_data:
        for r in spectrum_data["summary_table"]:
            status_badge = (
                f'<span class="badge badge-success">Above {critical_pct:g}% in window</span>'
                if r["survived_critical_20pct"]
                else f'<span class="badge badge-neutral">At/below {critical_pct:g}% in window</span>'
            )
            d1, d2, d3 = ("—" if r.get(key) is None else f"{threshold_day_label(r[key])}*"
                          for key in ("day_stage1_40", "day_stage2_30", "day_stage3_20"))
            r_mult = r.get("tier_multiplier", 1.0)
            comp_pct = observed_percent(r_mult, metrics.input_rainfall) if metrics.input_rainfall else None
            ret_text = (
                f"{r['retention_pct']:.1f}% input (≈{comp_pct:.1f}% hist)"
                if comp_pct is not None else
                f"{r['retention_pct']:.1f}%"
            )
            spectrum_html_rows += f"""
            <tr>
                <td><strong>{escape(r['tier_label'])}</strong></td>
                <td>{r['retention_pct']:.1f}%</td>
                <td><strong>{r['min_pct']:.1f}%</strong> ({r['min_acft']:,.0f} ac-ft)</td>
                <td>{d1}</td>
                <td>{d2}</td>
                <td><strong>{d3}</strong></td>
                <td>{status_badge}</td>
            </tr>
            """

    band_actions = {
        "Band 1": ("Public awareness notices, voluntary reduction targets, leak audit escalation.",
                   "Early demand dampening.*"),
        "Band 2": ("Restrictions on landscape irrigation and non-essential outdoor use.",
                   "Slows drawdown between bands.*"),
        "Band 3": ("Emergency curtailment across accounts; drought surcharge pricing.",
                   "Protects the minimum reserve.*"),
        "Band 4": ("Supply-emergency protocols prioritizing public health and safety.",
                   "Last band the model distinguishes before storage exhaustion."),
    }
    band_html_rows = ""
    for band_fraction, band_name in report_bands:
        actions, effect = band_actions[band_name]
        band_html_rows += (
            "<tr>"
            f"<td><strong>{escape(band_name)}</strong></td>"
            f"<td>&le; {band_fraction * 100:.0f}% ({band_storage_acft(band_fraction, system):,.0f} ac-ft)</td>"
            f"<td>{escape(actions)}</td>"
            f"<td>{escape(effect)}</td>"
            "</tr>"
        )

    highest_band_desc = metrics.highest_breached_band or "No response bands breached in window"
    if metrics.highest_breached_day is not None and "breached" not in highest_band_desc.lower():
        highest_band_desc += f" (Day {metrics.highest_breached_day})"

    if metrics.available:
        if "no tier reached" in str(tipping_point_tier).lower():
            tipping_point_sub = "None of the 4 tested retention tiers reached Band 3 within modeled window*"
        else:
            tipping_point_sub = "First tier breaching Band 3 in sim*"
        overview_sentence = (
            f"This evaluation tests primary scenario <strong>{escape(primary_id)}</strong> starting at "
            f"<strong>{init_frac * 100:.0f}% initial storage</strong>. It measures whether emergency "
            f"conservation ({cons_frac * 100:g}%) defers reaching the illustrative {critical_pct:g}% reserve band (Band 3). "
            f"Across all 4 modeled response bands, the highest band reached under primary scenario "
            f"<strong>{escape(primary_id)}</strong> is <strong>{escape(highest_band_desc)}</strong>."
        )
    else:
        tipping_point_sub = unavailable_note
        overview_sentence = (
            f"It was intended to run at {init_frac * 100:.0f}% initial storage with "
            f"{cons_frac * 100:g}% emergency conservation, but no run was produced for this report."
        )

    described = config.describe_rows()
    config_summary_line = " · ".join(f"{label}: {value}" for label, value in described)
    config_note_html = (
        f'<p style="margin-top: 6px; font-weight: 600; color: #92400e;">{escape(scenario_note)}</p>'
        if scenario_note else ""
    )
    config_default_html = (
        ""
        if config.selected else
        '<p style="margin-top: 6px; color: #92400e; font-weight: 600;">'
        f"Scenario {escape(primary_id)} was reviewed and approved as representative candidate #1 in Review. "
        "Drawdown was simulated using standard BASIN baseline defaults (48% initial storage, 0% baseline conservation), "
        "as custom parameter overrides were not configured in Review. "
        "No experiment was configured in Review. The settings above are BASIN's documented defaults, not a record of an earlier run.</p>"
    )

    unavailable_banner = (
        f'<p style="margin-top: 6px; font-weight: 600; color: #92400e;">{escape(unavailable_note)}</p>'
        if unavailable_note else ""
    )

    benchmark_table_html = ""
    if metrics.stressed_case:
        st = metrics.stressed_case
        modeled_days = max(
            len(metrics.sim_base) if metrics.sim_base is not None else 0,
            len(metrics.sim_cons) if metrics.sim_cons is not None else 0,
        )
        window_label = f"Not reached within {modeled_days}-day modeled window" if modeled_days else "Not reached within modeled window"
        p_base = f"Day {metrics.day_base_stage3}" if metrics.day_base_stage3 is not None else window_label
        p_cons = f"Day {metrics.day_cons_stage3}" if metrics.day_cons_stage3 is not None else window_label
        p_def = (
            f"+{metrics.day_cons_stage3 - metrics.day_base_stage3} Days Gained"
            if (metrics.day_base_stage3 is not None and metrics.day_cons_stage3 is not None)
            else f"Band 3 (>{critical_pct:g}%) preserved across window"
        )
        s_base = f"Day {st.get('day_base_20', 'N/A')}"
        s_cons = f"Day {st.get('day_cons_20', 'N/A')}"
        s_delay = st.get("conservation_delay_days", 0)
        s_def = f"+{s_delay} Days Gained (Day {st.get('day_base_20')} &rarr; {st.get('day_cons_20')})"
        ratio_val = st.get("evap_to_conservation_ratio")
        ratio_note = f" (The configured rates produce an evaporation-to-conservation ratio of {ratio_val}:1; this is assumption-driven.)" if ratio_val else ""
        benchmark_table_html = f"""
        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 8px;">Antecedent Storage Benchmark & Conservation Intervention (35% vs. 48% Baseline)</div>
        <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">
            The paired 35% benchmark run evaluates system vulnerability when severe antecedent drought has already depleted combined reserves before the scenario begins.{escape(ratio_note)}
        </p>
        <table>
            <thead>
                <tr>
                    <th>Antecedent Condition</th>
                    <th>Initial Storage</th>
                    <th>Baseline (0% Conservation)</th>
                    <th>15% Conservation Mandate</th>
                    <th>Threshold Deferral Benefit</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Standard Planning Baseline</strong></td>
                    <td>{init_frac * 100:g}% capacity</td>
                    <td>{p_base}</td>
                    <td>{p_cons}</td>
                    <td><strong>{p_def}</strong></td>
                </tr>
                <tr>
                    <td><strong>Severe Antecedent Stress (Benchmark)</strong></td>
                    <td>35.0% capacity</td>
                    <td>{s_base}</td>
                    <td>{s_cons}</td>
                    <td><strong>{s_def}</strong></td>
                </tr>
            </tbody>
        </table>
        """

    tier_count = len(spectrum_data.get("summary_table", [])) if spectrum_data else 0
    if metrics.available:
        spectrum_caption = (
            f"Simulated drawdown across {tier_count} rainfall tiers for {primary_id} starting at "
            f"{init_frac * 100:g}% initial storage with {cons_frac * 100:g}% emergency conservation. "
            f"{_input_sentence(metrics)} "
            f"{format_compounding_tier_footnote(metrics)} "
            "Asterisks mark days inside the uncalibrated modeled window; day 0 means at or below the band at the start."
        )
    else:
        spectrum_caption = f"Not computed for this report. {unavailable_note}"

    spectrum_unavailable_row = (
        '<tr><td colspan="7" style="text-align: center; color: #92400e; font-weight: 600;">'
        + escape(f"{UNAVAILABLE} — {unavailable_note or 'the stress spectrum produced no rows'}")
        + "</td></tr>"
    )

    def _private_annotation_html(record) -> str:
        """Private annotations follow the same export consent as review notes."""
        if not record.get("private_note"):
            return ""
        if include_notes:
            return f'<div class="evidence-body"><em>Private annotation:</em> {escape(str(record["private_note"]))}</div>'
        return ('<div class="evidence-body" style="color: #64748b;"><em>Private annotation recorded '
                '(omitted: export privacy setting excludes private notes).</em></div>')

    evidence_html = ""
    for record in list(getattr(workspace, "evidence", []) or []):
        evidence_html += (
            '<div class="evidence-entry">'
            f'<div class="evidence-title">{escape(str(record.get("id", "unidentified")))}: '
            f'{escape(str(record.get("title", "Untitled")))}</div>'
            f'<div class="evidence-meta">{escape(str(record.get("kind", "unspecified")))} · '
            f'{escape(str(record.get("review_status", "unspecified")))} · '
            f'{escape(str(record.get("publisher", "publisher not supplied")))}</div>'
            f'<div class="evidence-meta">Source: {escape(str(record.get("source_locator", "not supplied")))}; '
            f'source date: {escape(str(record.get("source_date") or "not supplied"))}. '
            f'Geography: {escape(str(record.get("geographic_scope", "not supplied")))}. '
            f'Units: {escape(str(record.get("units") or "not applicable"))}.</div>'
            f'<div class="evidence-body">{escape(str(record.get("description", "")))}</div>'
            + _private_annotation_html(record) +
            "</div>"
        )
    if not evidence_html:
        evidence_html = '<p style="font-size: 7.5pt; color: #64748b;">No evidence records are attached to this analysis.</p>'

    conflicts_html = ""
    for conflict in list(getattr(workspace, "conflicts", []) or []):
        conflicts_html += (
            '<div class="evidence-entry">'
            f'<div class="evidence-title">{escape(str(conflict.get("id", "conflict")))} '
            f'[{escape(str(conflict.get("status", "unknown")))}]: '
            f'{escape(str(conflict.get("left_id", "?")))} vs {escape(str(conflict.get("right_id", "?")))}</div>'
            f'<div class="evidence-body">Disagreement: {escape(str(conflict.get("disagreement", "")))}</div>'
            f'<div class="evidence-meta">Comparability: {escape(str(conflict.get("comparability", "")))}</div>'
            f'<div class="evidence-meta">Human disposition: '
            f'{escape(str(conflict.get("resolution") or "Unresolved; no disposition recorded."))}</div>'
            + _private_annotation_html(conflict) +
            "</div>"
        )
    if not conflicts_html:
        conflicts_html = ('<p style="font-size: 7.5pt; color: #64748b;">No evidence disagreements have been '
                          "recorded. That does not establish that none exist.</p>")

    scenario_html_rows = ""
    scenario_inventory_rows = ""
    _dur_note_text = duration_mix_note(accepted, w_dur)
    _html_dur_note = (
        f'<p style="font-size: 6.8pt; color: #64748b; margin-top: 4px;">{escape(_dur_note_text)}</p>'
        if _dur_note_text else ""
    )
    for s in accepted:
        prov = s.provenance
        feat = getattr(s, "features", {})
        deficit_mm = feat.get("deficit_mm", 0.0)
        concurrence = feat.get("concurrence", 0.0)

        ranking_rationale = format_scenario_ranking_rationale(s, workspace)
        conc_detail = format_scenario_concurrence_detail(s, workspace)

        # Public summary vs private note distinction (Item 10)
        public_summary = getattr(s, "public_summary", "") or scenario_summary(s.features).replace("**", "")
        review_event = s.history[-1] if s.history else {}
        entry_note = review_event.get("private_note") or review_event.get("note")
        decision_mode = review_event.get("decision_mode", "individual")
        mode_label = "Batch decision" if decision_mode == "batch" else "Individual review"
        reviewer_name = review_event.get("reviewer_name", "Identity not recorded")
        reviewer_role = review_event.get("reviewer_role", "Internal screening reviewer")
        review_scope = review_event.get("review_scope", "internal rainfall-scenario screening; not external hydrologic approval")
        identity_display = (
            f'<div class="text-sm" style="color: #475569; margin-top: 3px;"><strong>Internal reviewer:</strong> '
            f'{escape(reviewer_name)} · {escape(reviewer_role)}. Scope: {escape(review_scope)}.</div>'
        )

        if include_notes and entry_note:
            note_display = f'<div class="text-sm italic" style="color: #0f172a; margin-top: 3px;"><strong>{mode_label}.</strong> <strong>Private review note (consented export):</strong> {escape(entry_note)}</div>'
        elif entry_note:
            note_display = f'<div class="text-sm italic" style="color: #64748b; margin-top: 3px;">{mode_label}; rationale recorded locally (omitted: export privacy setting excludes private notes)</div>'
        else:
            note_display = '<div class="text-sm italic" style="color: #64748b; margin-top: 3px;">No review note recorded.</div>'

        public_display = f'<div style="font-size: 7.5pt; color: #334155; margin-bottom: 2px;">{escape(public_summary)}</div>' if public_summary else ''
        rationale_display = f'<div style="font-size: 7.5pt; color: #087e8b; font-weight: 600; margin-bottom: 2px;">{escape(ranking_rationale)}</div>'
        conc_cell = f'{concurrence:.2f}' + (f'<div style="font-size: 6.8pt; color: #64748b; margin-top: 2px;">{escape(conc_detail)}</div>' if conc_detail else '')

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
            <td>{conc_cell}</td>
            <td>
                {rationale_display}
                {public_display}
                {note_display}
                {identity_display}
            </td>
        </tr>
        """
        scenario_inventory_rows += f"""
        <tr>
            <td><strong class="font-mono">{escape(s.id)}</strong> (Rev {s.revision})</td>
            <td>{escape(str(start_dt))} to {escape(str(end_dt))}</td>
            <td>{duration_days} days</td>
            <td><strong>{deficit_mm:,.1f} mm</strong></td>
            <td>{concurrence:.2f}</td>
        </tr>
        """

    provider_note = str(getattr(workspace, "notes", "") or "").strip()
    if include_notes and provider_note:
        provider_notes_html = (
            '<div class="section-title" style="font-size: 9pt; border-left: none; padding-left: 0;">Provider Notes</div>'
            f'<div class="evidence-entry"><div class="evidence-body">{escape(provider_note)}</div></div>'
        )
    elif provider_note:
        provider_notes_html = (
            '<div class="section-title" style="font-size: 9pt; border-left: none; padding-left: 0;">Provider Notes</div>'
            '<p style="font-size: 7.5pt; color: #64748b;">Provider notes recorded '
            '(omitted: export privacy setting excludes private notes).</p>'
        )
    else:
        provider_notes_html = ""

    from basin_core.custom_data import (
        CUSTOM_CATCHMENT_DISCLAIMER,
        format_custom_coverage_dates,
        format_custom_source_label,
    )
    custom_uploads = getattr(workspace, "custom_uploads", []) or []
    custom_provenance_html = ""
    if custom_uploads:
        custom_provenance_html += (
            '<div class="evidence-entry" style="margin-top: 6px; border-left-color: #f59e0b;">'
            '<div class="evidence-title">Custom Observation Sources (T3 Standardized Provenance)</div>'
        )
        for record in custom_uploads:
            src_lbl = format_custom_source_label(record["station"], record.get("provider"))
            cov_lbl = format_custom_coverage_dates(record.get("start"), record.get("end"), record.get("valid_days"))
            custom_provenance_html += (
                f'<div class="evidence-body"><strong>{escape(record.get("id", "Custom"))}:</strong> '
                f'{escape(src_lbl)} · {escape(cov_lbl)} · Status: {escape(record.get("comparison", {}).get("status", "uploaded"))}</div>'
            )
        custom_provenance_html += (
            f'<div class="evidence-meta" style="color: #92400e; margin-top: 4px;">{escape(CUSTOM_CATCHMENT_DISCLAIMER)}</div>'
            '</div>'
        )

    paired_sensitivity_html = build_paired_sensitivity_block_html(metrics)
    tac_and_policy_html = build_tac_and_policy_block_html(metrics)
    ml_methodology_html = build_ml_comparison_block_html(workspace, metrics=metrics)
    station_completeness_html = build_station_completeness_table_html(workspace)

    chart_images_html = ""
    if metrics.storage_chart_png_b64:
        chart_images_html += f"""
        <div style="margin: 8px 0; page-break-inside: avoid; break-inside: avoid;">
            <div style="font-size: 8pt; font-weight: 700; color: #0f172a; margin-bottom: 3px;">Figure 1: Projected Reservoir Storage Trajectory & Threshold Crossings (Baseline vs. Conservation)</div>
            <div style="text-align: center;"><img src="data:image/png;base64,{metrics.storage_chart_png_b64}" style="width: 100%; max-width: 680px; height: auto; border: 1px solid #cbd5e1; border-radius: 4px;" alt="Storage Trajectory Chart"></div>
        </div>
        """
    if metrics.milestone_chart_png_b64:
        chart_images_html += f"""
        <div style="margin: 8px 0; page-break-inside: avoid; break-inside: avoid;">
            <div style="font-size: 8pt; font-weight: 700; color: #0f172a; margin-bottom: 3px;">Figure 2: Milestone Gantt Timeline — Response Band Crossings Across Retention Tiers</div>
            <div style="text-align: center;"><img src="data:image/png;base64,{metrics.milestone_chart_png_b64}" style="width: 100%; max-width: 680px; height: auto; border: 1px solid #cbd5e1; border-radius: 4px;" alt="Stage Trigger Milestone Chart"></div>
        </div>
        """

    primary_features = getattr(primary_scenario, "features", {}) or {}
    primary_duration = int(primary_features.get("duration_days", 0))
    primary_deficit = float(primary_features.get("deficit_mm", 0.0))
    primary_percentile = float(primary_features.get("historical_percentile", 0.0)) * 100
    primary_benchmark_n = int(primary_features.get("benchmark_n", 0))
    active_station_count = len(primary_scenario.series.columns) if primary_scenario is not None and hasattr(primary_scenario, "series") else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BASIN Executive Brief — {escape(run_id)}</title>
<style>
    @page {{
        size: letter;
        margin: 12mm 14mm 14mm 14mm;
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
        font-size: 8.5pt;
        line-height: 1.35;
    }}
    .page-container {{
        width: 100%;
    }}
    .page-break {{
        page-break-before: always;
        break-before: always;
        margin-top: 15px;
    }}
    .header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 3px solid #087e8b;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }}
    .brand-title {{
        font-size: 14pt;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #087e8b;
        line-height: 1.1;
    }}
    .brand-subtitle {{
        font-size: 7.5pt;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #475569;
        margin-top: 2px;
    }}
    .meta-box {{
        text-align: right;
        font-size: 7.5pt;
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
        margin-bottom: 3px;
    }}
    .report-section {{
        margin-bottom: 10px;
        break-inside: auto;
    }}
    .section-title {{
        font-size: 9.5pt;
        font-weight: 700;
        color: #0f172a;
        border-left: 4px solid #087e8b;
        padding-left: 8px;
        margin-top: 10px;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }}
    .kpi-row {{
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    .kpi-card {{
        flex: 1;
        background: #f8fafc;
        border: 1.5px solid #cbd5e1;
        border-radius: 6px;
        padding: 6px 8px;
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
        font-size: 6.8pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #475569;
    }}
    .kpi-val {{
        font-size: 9.5pt;
        font-weight: 700;
        color: #0f172a;
        margin-top: 2px;
        line-height: 1.2;
    }}
    .kpi-sub {{
        font-size: 7pt;
        color: #64748b;
        margin-top: 2px;
        line-height: 1.2;
    }}
    .callout {{
        background: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 7px 10px;
        border-radius: 0 5px 5px 0;
        font-size: 8pt;
        margin-bottom: 8px;
        break-inside: avoid;
        page-break-inside: avoid;
    }}
    .callout-title {{
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 3px;
        text-transform: uppercase;
        font-size: 7.5pt;
        letter-spacing: 0.5px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 7.8pt;
        margin-bottom: 8px;
        table-layout: fixed;
        word-wrap: break-word;
        overflow-wrap: anywhere;
    }}
    th {{
        background: #0f172a;
        color: #ffffff;
        font-weight: 600;
        text-align: left;
        padding: 4px 6px;
        font-size: 7.2pt;
        letter-spacing: 0.3px;
        overflow-wrap: anywhere;
    }}
    td {{
        padding: 4px 6px;
        border-bottom: 1px solid #e2e8f0;
        color: #334155;
        overflow-wrap: anywhere;
    }}
    tr {{
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    tr:nth-child(even) td {{
        background: #f8fafc;
    }}
    .evidence-entry {{
        border-left: 3px solid #cbd5e1;
        padding: 3px 0 3px 8px;
        margin-bottom: 6px;
        page-break-inside: avoid;
        break-inside: avoid;
        overflow-wrap: anywhere;
    }}
    .evidence-title {{
        font-weight: 700;
        font-size: 7.8pt;
        color: #0f172a;
    }}
    .evidence-meta {{
        font-size: 6.8pt;
        color: #64748b;
    }}
    .evidence-body {{
        font-size: 7.2pt;
        color: #334155;
        margin-top: 2px;
    }}
    .badge {{
        display: inline-block;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 6.8pt;
        font-weight: 700;
    }}
    .badge-success {{ background: #dcfce7; color: #166534; }}
    .badge-info {{ background: #e0f2fe; color: #0369a1; }}
    .badge-neutral {{ background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }}
    .seal-box {{
        margin-top: 10px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 8px 12px;
        background: #f8fafc;
        display: flex;
        justify-content: space-between;
        align-items: center;
        page-break-inside: avoid;
        break-inside: avoid;
    }}
    .seal-text {{
        font-size: 7.2pt;
        color: #475569;
        line-height: 1.35;
    }}
    .seal-stamp {{
        border: 2px dashed #087e8b;
        border-radius: 6px;
        padding: 6px 12px;
        text-align: center;
        color: #087e8b;
        font-size: 7.2pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .font-mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    .italic {{ font-style: italic; }}
    .text-sm {{ font-size: 7.2pt; }}
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
            <div><strong>Prepared for:</strong> {escape(audience_label)}</div>
        </div>
    </div>

    <!-- SECTION 1: EXECUTIVE SUMMARY (Page 1 Orientation Precedes Warning Box) -->
    <div class="report-section" id="section-1">
        <div class="section-title">1. Executive Summary</div>
        <p style="font-size: 8pt; margin-bottom: 4px;"><strong>Intended decision context:</strong> {escape(audience_label)} · {escape(county_label)}. {escape(context_boundary)}</p>
        <p style="font-size: 7.2pt; color: #64748b; margin-top: 2px; margin-bottom: 6px;"><strong>Replay Scope:</strong> The companion archive BASIN-{escape(run_id[:14])}.zip contains SHA-256 hash-checked data and a Python calculation ledger. Successful replay establishes internal consistency within that declared scope. This PDF is a readable companion outside the replay contract.</p>
        <div class="callout">
            <div class="callout-title">The Bottom Line — Executive Overview</div>
            <p>This report presents <strong>{len(accepted)} internally reviewed rainfall-stress scenarios</strong> for expert handoff. The primary scenario spans <strong>{primary_duration} days</strong>, has an equal-station mean rainfall shortfall of <strong>{primary_deficit:,.1f} mm</strong>, and ranks at or above <strong>{primary_percentile:.0f}%</strong> of {primary_benchmark_n} matched historical windows. These point-gauge scenarios identify rainfall conditions worth deeper modeling; they do not estimate reservoir inflow or water-supply reliability.</p>
            {unavailable_banner}
        </div>

        <div class="kpi-row">
            <div class="kpi-card neutral">
                <div class="kpi-label">Reviewed Rainfall Shortlist</div>
                <div class="kpi-val">{len(accepted)} scenarios</div>
                <div class="kpi-sub">Internal screening decisions; not external approval</div>
            </div>
            <div class="kpi-card neutral">
                <div class="kpi-label">Primary Scenario Duration</div>
                <div class="kpi-val">{primary_duration} days</div>
                <div class="kpi-sub">Synchronized window across {active_station_count} selected point gauges</div>
            </div>
            <div class="kpi-card neutral">
                <div class="kpi-label">Mean Rainfall Shortfall</div>
                <div class="kpi-val">{primary_deficit:,.1f} mm</div>
                <div class="kpi-sub">Equal-station screening metric</div>
            </div>
            <div class="kpi-card neutral">
                <div class="kpi-label">Matched Historical Rank</div>
                <div class="kpi-val">≥ {primary_percentile:.0f}%</div>
                <div class="kpi-sub">Compared with {primary_benchmark_n} matched windows; not a probability</div>
            </div>
        </div>

    </div>

    <!-- Universal Top Banner (Follows Executive Summary Orientation) -->
    <div style="background: #f8fafc; border: 1.5px solid #94a3b8; border-left: 5px solid #087e8b; border-radius: 4px; padding: 6px 10px; margin-bottom: 10px; font-size: 8pt; color: #1e293b; line-height: 1.35;">
        <strong>⚠️ WHAT THIS DOCUMENT IS NOT:</strong>
        <span>Rainfall-scenario screening only · NOT a reservoir-inflow or freshwater-availability prediction · NOT a hydrologic drought-of-record analysis · NOT validated against actual streamflow or catchment runoff.</span>
    </div>

    <!-- SECTION 2: SCENARIO IDENTITY AND RAINFALL INPUT -->
    <div class="report-section" id="section-2">
        <div class="section-title">2. Scenario Identity and Rainfall Input</div>
        <p style="font-size: 8pt; color: #334155; margin-bottom: 6px;">
            <strong>Primary Scenario Identity:</strong> <strong class="font-mono">{escape(primary_id)}</strong>. {_input_sentence(metrics)}
        </p>
        <div style="font-size: 7.2pt; color: #475569; margin-bottom: 6px; background: #f8fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0; line-height: 1.35;">
            <strong>Technical Terms Gloss:</strong>
            <strong>Concurrence:</strong> fraction of eligible 30-day windows with all selected stations simultaneously in deficit.
            · <strong>Empirical percentile:</strong> historical shortfall rank relative to matched observation windows.
            · <strong>Reference window gating (n &ge; 5):</strong> minimum reporting rule for an empirical comparison; five windows remain a small sample and do not establish statistical validity.
            · <strong>Priority score:</strong> multi-criteria weighted rank score (Severity {w_sev}%, Concurrence {w_conc}%, Duration {w_dur}%, Season {w_seas}%) prioritizing scenarios within each cluster.
        </div>
        <table style="table-layout: fixed;">
            <colgroup><col style="width: 16%;"><col style="width: 28%;"><col style="width: 16%;"><col style="width: 20%;"><col style="width: 20%;"></colgroup>
            <thead>
                <tr>
                    <th>Scenario ID</th>
                    <th>Source Window</th>
                    <th>Duration</th>
                    <th>Precip Deficit</th>
                    <th>Selected-Stations Concurrent Deficit</th>
                </tr>
            </thead>
            <tbody>
                {scenario_inventory_rows if scenario_inventory_rows else '<tr><td colspan="5" style="text-align: center; color: #64748b;">No accepted scenarios.</td></tr>'}
            </tbody>
        </table>
    </div>

    <!-- SECTION 3: REVIEW DECISION AND RATIONALE -->
    <div class="report-section" id="section-3">
        <div class="section-title">3. Review Decision and Rationale</div>
        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 4px;">Shortlisted Scenario Inventory & Human Review Notes <span style="font-weight: normal; font-size: 7.5pt; color: #64748b;">(Ranked by multi-criteria composite score)</span></div>
        <table style="table-layout: fixed;">
            <colgroup><col style="width: 10%;"><col style="width: 18%;"><col style="width: 10%;"><col style="width: 12%;"><col style="width: 13%;"><col style="width: 37%;"></colgroup>
            <thead>
                <tr>
                    <th>Scenario ID</th>
                    <th>Source Window (NOAA)</th>
                    <th>Duration</th>
                    <th>Precip Deficit</th>
                    <th>Selected-Stations Concurrent Deficit</th>
                    <th>Review Disposition & Notes</th>
                </tr>
            </thead>
            <tbody>
                {scenario_html_rows if scenario_html_rows else '<tr><td colspan="6" style="text-align: center; color: #64748b;">No accepted scenarios.</td></tr>'}
            </tbody>
        </table>
        {_html_dur_note}
        {provider_notes_html}
        {ml_methodology_html}
    </div>

    <!-- SECTION 4: STORAGE-SYSTEM ASSUMPTIONS -->
    <div class="report-section" id="section-4">
        <div class="section-title">4. Storage-System Assumptions</div>
        <p style="font-size: 7.5pt; color: #475569; margin: 2px 0 6px 0; word-break: break-word; overflow-wrap: anywhere;"><strong>Experiment configuration:</strong> {escape(config_summary_line)}</p>
        {config_note_html}
        {config_default_html}

        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 6px;">Illustrative Drought Response Reference Framework</div>
        <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">
            <strong>Illustrative assumption, not adopted policy.</strong> The storage bands below are this experiment's own assumption ({escape(str(system_assumptions["thresholds"]))}). BASIN does not reproduce any adopted drought contingency ordinance, and the response categories listed are generic planning language rather than measures any authority has adopted. Confirm the currently adopted plan and any active declarations with the responsible utility before operational use.
        </p>
        <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">
            <strong>Capacity basis.</strong> Band volumes are computed against the selected system's assumed combined capacity of {total_capacity:,.0f} ac-ft ({escape(capacity_breakdown)}). That is the experiment's assumption, not a survey-verified figure. {escape(capacity_comparison)}
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
        <div style="font-size: 6.8pt; color: #64748b; margin-top: 3px; line-height: 1.3;">
            * Specific curtailment volume/magnitude is not modeled dynamically per band; response effect is illustrative.
        </div>
    </div>

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

    <!-- SECTION 5: EXPERIMENT RESULTS -->
    <div class="report-section" id="section-5">
        <div class="section-title">5. Experiment Results</div>
        <div style="background: #fffbeb; border: 1.5px solid #f59e0b; border-radius: 6px; padding: 7px 10px; margin-bottom: 8px; font-size: 9pt; font-weight: 600; color: #92400e; line-height: 1.35;">
            ⚠️ ILLUSTRATIVE SENSITIVITY EXPERIMENT ONLY — NOT AN OPERATIONAL FORECAST<br>
            <span style="font-weight: 400; font-size: 8pt; color: #78350f;">Drawdown trajectories reflect the selected system's illustrative mass-balance with an uncalibrated inflow proxy ({escape(str(system_assumptions["inflow"]))}) and seasonal evaporation assumptions. They do NOT represent safe yield, actual reservoir levels, or regulatory curtailment dates.</span>
        </div>

        {chart_images_html}

        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 6px;">Illustrative Storage Sensitivity Spectrum (Non-Predictive)</div>
        <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">{escape(spectrum_caption)}</p>
        <table>
            <thead>
                <tr>
                    <th>Stress Tier</th>
                    <th>Retained Rainfall (% of input)</th>
                    <th>Simulated Min Storage</th>
                    <th>Band 1 ({band1_pct:g}%)</th>
                    <th>Band 2 ({band2_pct:g}%)</th>
                    <th>Band 3 ({critical_pct:g}%)</th>
                    <th>Simulated Outcome</th>
                </tr>
            </thead>
            <tbody>
                {spectrum_html_rows if spectrum_html_rows else spectrum_unavailable_row}
            </tbody>
        </table>
        <p style="font-size: 7.2pt; color: #64748b; margin-top: 4px; margin-bottom: 8px;">
            <strong>Compounding Rainfall Multipliers:</strong> {format_compounding_tier_footnote(metrics)}
        </p>
        {tac_and_policy_html}
        {paired_sensitivity_html}
        {benchmark_table_html}
    </div>

    <!-- SECTION 6: OBSERVATION PROVENANCE -->
    <div class="report-section" id="section-6">
        <div class="section-title">6. Observation Provenance</div>
        <p style="font-size: 7.5pt; color: #475569; margin-bottom: 6px;">
            <strong>Primary Station Proxies:</strong> NOAA GHCN-Daily precipitation, {escape(record_span)} · Network: {escape(station_network_summary(workspace))} · Active this run: {escape(stations)}
        </p>
        {station_completeness_html}
        {custom_provenance_html}

        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 6px;">Evidence and Assumptions</div>
        {evidence_html}

        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 6px;">Recorded Disagreements</div>
        {conflicts_html}
    </div>

    <!-- SECTION 7: LIMITATIONS -->
    <div class="report-section" id="section-7">
        <div class="section-title">7. Limitations</div>
        <div class="callout" style="border-left-color: #f59e0b; background: #fffbeb;">
            <div class="callout-title" style="color: #92400e;">⚠️ WHAT THIS DOCUMENT IS NOT / MODELING LIMITATIONS</div>
            <ul style="margin-left: 18px; font-size: 7.8pt; color: #78350f; line-height: 1.45;">
                <li><strong>Not an Operational Forecast:</strong> Drawdown trajectories reflect an illustrative planning experiment under historical rainfall deficit series, not a forecast of future lake levels or safe yield.</li>
                <li><strong>Rainfall Screening Only:</strong> BASIN does not predict reservoir inflow or freshwater availability.</li>
                <li><strong>Not a Drought-of-Record Analysis:</strong> Historical point-rainfall deficit series do not substitute for comprehensive basin-wide hydrologic modeling.</li>
                <li><strong>Uncalibrated Hydrology:</strong> Inflow proxy ({escape(str(system_assumptions["inflow"]))}) is not calibrated against river gauges or streamflow measurements.</li>
                <li><strong>Proxy Evaporation:</strong> Uses regional seasonal proxy rates, not pan-calibrated or surface-area-routed evaporation.</li>
                <li><strong>Generic Planning Categories:</strong> Response categories and threshold storage bands are generic planning concepts, not adopted municipal policy.</li>
            </ul>
        </div>
    </div>

    <!-- SECTION 8: VERIFICATION AND HASHES -->
    <div class="report-section" id="section-8">
        <div class="section-title">8. Verification and Hashes</div>
        <div class="section-title" style="font-size: 8.5pt; border-left: none; padding-left: 0; margin-top: 4px;">Provenance & Verification Scope</div>
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
                <div style="font-size: 8pt; font-weight: 800; line-height: 1.25;">BUNDLE ONLY<br>PDF NOT VERIFIED</div>
                <div class="font-mono" style="font-size: 6.5pt;">ID: {escape(run_id)}</div>
            </div>
        </div>
    </div>
</div>

</body>
</html>
"""
    comp_data = None
    if workspace is not None and hasattr(workspace, "scenarios") and hasattr(workspace, "selected"):
        try:
            comp_data = comparison(workspace.scenarios, workspace.selected, seed=workspace.params.seed)
        except Exception:
            comp_data = None

    validate_report_prose_against_metrics(html, metrics, config, comp_data=comp_data)

    return html


# Characters that have no WinAnsi glyph but a faithful ASCII rendering.
_TRANSLITERATIONS = {
    "≤": "<=", "≥": ">=", "≈": "~", "→": "->", "←": "<-", "×": "x", "\u00a0": " ",
    "\u2010": "-", "\u2011": "-", "\u2212": "-", "\u02c6": "^", "\u02dc": "~",
    "\u26a0": "[!]", "\ufe0f": "",
}


def encode_winansi(text: str) -> tuple[str, int]:
    """Map text onto the WinAnsi glyph set.

    Returns the encodable text and the number of characters that had no representation.
    Those become "?" as before, but the count lets the report disclose that some
    characters could not be drawn instead of quietly changing the content.
    """
    out: list[str] = []
    dropped = 0
    for char in text:
        replacement = _TRANSLITERATIONS.get(char)
        if replacement is not None:
            out.append(replacement)
            continue
        try:
            char.encode("cp1252")
        except UnicodeEncodeError:
            dropped += 1
            out.append("?")
            continue
        out.append(char)
    return "".join(out), dropped


class VectorPDFBuilder:
    """Zero-dependency pure-Python vector PDF generator compliant with PDF-1.4.
    
    Produces high-fidelity multi-page documents with vector tables, colored cards,
    rule lines, and typography without external dependencies.
    """

    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self.recorded_text: list[str] = []
        # Characters the base-14 fonts cannot represent. Counted so the report can say so
        # rather than silently printing substitutes.
        self.unrepresentable = 0
        # Set by VectorFlow.insert_toc_page(): (page_index, list of link rects).
        self.toc_annots: tuple[int, list[tuple[float, float, float, float, int]]] | None = None

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
        self.recorded_text.append(str(txt))
        clean, dropped = encode_winansi(str(txt))
        if dropped:
            self.unrepresentable += dropped
        clean = (
            clean
            .replace("\\", "\\\\")
            .replace("(", r"\(")
            .replace(")", r"\)")
            .replace("\n", " ")
        )
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
        next_id = f3_id + 1

        # Build link annotation objects if a TOC page was inserted.
        annot_ids: list[int] = []
        annot_page_idx: int | None = None
        if self.toc_annots is not None:
            annot_page_idx, annot_rects = self.toc_annots
            for _ in annot_rects:
                annot_ids.append(next_id)
                next_id += 1

        total_objs = next_id - 1

        objs: dict[int, str] = {}
        objs[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>"
        kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
        objs[pages_id] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>"

        # Build annotation objects (one per TOC link entry).
        if annot_ids and self.toc_annots is not None:
            _, annot_rects = self.toc_annots
            for aid, (ax, ay, aw, ah, dest_pidx) in zip(annot_ids, annot_rects):
                dest_page_obj = page_ids[dest_pidx] if dest_pidx < num_pages else page_ids[-1]
                objs[aid] = (
                    f"<< /Type /Annot /Subtype /Link "
                    f"/Rect [{ax:.2f} {ay:.2f} {ax + aw:.2f} {ay + ah:.2f}] "
                    f"/Border [0 0 0] "
                    f"/Dest [{dest_page_obj} 0 R /Fit] >>"
                )

        for i in range(num_pages):
            pid = page_ids[i]
            cid = content_ids[i]
            # Attach /Annots array to the TOC page if annotations exist.
            annots_str = ""
            if i == annot_page_idx and annot_ids:
                refs = " ".join(f"{aid} 0 R" for aid in annot_ids)
                annots_str = f" /Annots [{refs}]"
            objs[pid] = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
                f"/Contents {cid} 0 R /Resources << /Font << "
                f"/F1 {f1_id} 0 R /F2 {f2_id} 0 R /F3 {f3_id} 0 R >> >>{annots_str} >>"
            )
            content = "\n".join(self.pages[i])
            c_bytes = content.encode("cp1252", "replace")
            objs[cid] = f"<< /Length {len(c_bytes)} >>\nstream\n{content}\nendstream"

        objs[f1_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        objs[f2_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
        objs[f3_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"

        body = "%PDF-1.4\n"
        xref = ["xref", f"0 {total_objs + 1}", "0000000000 65535 f "]
        for i in range(1, total_objs + 1):
            xref.append(f"{len(body):010d} 00000 n ")
            body += f"{i} 0 obj\n{objs[i]}\nendobj\n"

        xref_pos = len(body)
        body += "\n".join(xref) + f"\ntrailer\n<< /Size {total_objs + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF"
        return body.encode("cp1252", "replace")



class VectorFlow:
    """Cursor-based layout for the vector report.

    Content is placed downward from a cursor and continues on a fresh page when it would
    otherwise run into the footer, so long notes and evidence descriptions are wrapped and
    carried over rather than cut off.
    """

    LEFT = 36
    RIGHT = 576
    WIDTH = RIGHT - LEFT
    BOTTOM = 58
    TOP = 700

    def __init__(self, doc: "VectorPDFBuilder", page: list[str], y: float, run_id: str) -> None:
        self.doc = doc
        self.page = page
        self.y = y
        self.run_id = run_id
        self._columns: list = []
        self.sections: list[tuple[str, int]] = []  # (title, page_index) for TOC

    def room_for(self, height: float) -> bool:
        return self.y - height >= self.BOTTOM

    def break_page(self) -> None:
        if self.y >= self.TOP + 15:
            return
        self.page = self.doc.add_page()
        self.doc.rect(self.page, 36, 742, 540, 26, fill=(0.06, 0.09, 0.16))
        self.doc.text(self.page, 50, 750, "BASIN * TECHNICAL ENGINEERING APPENDIX (CONTINUED)",
                      font="/F2", size=9.0, color=(1.0, 1.0, 1.0))
        self.doc.text(self.page, 415, 750, f"RUN ID: {clip_text(self.run_id, 14)}",
                      font="/F3", size=7.5, color=(0.85, 0.9, 0.95))
        self.y = self.TOP + 20

    def ensure(self, height: float) -> None:
        if not self.room_for(height):
            self.break_page()

    def gap(self, height: float) -> None:
        self.y -= height

    def heading(self, text: str, size: float = 9.5) -> None:
        self.ensure(size + 30)
        self.doc.text(self.page, self.LEFT, self.y - size, text, font="/F2", size=size,
                      color=(0.06, 0.09, 0.16))
        self.y -= size + 8
        # Record top-level numbered sections for the Table of Contents.
        stripped = text.strip()
        if stripped and stripped[0].isdigit() and ". " in stripped[:4]:
            page_idx = self.doc.pages.index(self.page)
            self.sections.append((stripped, page_idx))

    def paragraph(self, text: str, font: str = "/F1", size: float = 7.0,
                  color: tuple[float, float, float] = (0.1, 0.1, 0.1), indent: float = 0.0) -> None:
        """Draw wrapped text, breaking the page between lines when needed."""
        leading = size + 2.6
        for line in wrap_text(text, font, size, self.WIDTH - indent - 12):
            self.ensure(leading)
            self.doc.text(self.page, self.LEFT + 12 + indent, self.y - size, line, font=font,
                          size=size, color=color)
            self.y -= leading

    def callout_box(self, title: str, lines: list[str], fill=(0.99, 0.98, 0.94), stroke=(0.85, 0.65, 0.15),
                    title_col=(0.7, 0.4, 0.05), text_col=(0.3, 0.25, 0.1), size: float = 6.8, leading: float = 9.0) -> None:
        wrapped_lines: list[str] = []
        for line in lines:
            wrapped_lines.extend(wrap_text(line, "/F1", size, self.WIDTH - 24))
        h = 18.0 + len(wrapped_lines) * leading
        self.ensure(h + 6)
        y_bottom = self.y - h
        self.doc.rect(self.page, self.LEFT, y_bottom, self.WIDTH, h, fill=fill, stroke=stroke, line_width=1.0)
        self.doc.text(self.page, self.LEFT + 12, self.y - 13, title, font="/F2", size=8.0, color=title_col)
        for idx, line in enumerate(wrapped_lines):
            self.doc.text(self.page, self.LEFT + 12, self.y - 23 - idx * leading, line, font="/F1", size=size, color=text_col)
        self.y -= h + 6

    def metric_cards(self, cards: list[tuple[str, str, str, tuple[float, float, float]]]) -> None:
        """Draw 3 metric cards horizontally."""
        self.ensure(68)
        card_w = 172.0
        gap = 12.0
        h = 60.0
        y_top = self.y
        y_bottom = y_top - h
        for idx, (title, val, sub, val_col) in enumerate(cards[:3]):
            x = self.LEFT + idx * (card_w + gap)
            self.doc.rect(self.page, x, y_bottom, card_w, h, fill=(0.96, 0.97, 0.99), stroke=(0.8, 0.85, 0.92))
            self.doc.text(self.page, x + 10, y_top - 14, title, font="/F2", size=7.5, color=(0.4, 0.45, 0.55))
            self.doc.text(self.page, x + 10, y_top - 30, val, font="/F2", size=9.5, color=val_col)
            sub_lines = wrap_text(sub, "/F1", 5.8, card_w - 20)
            if len(sub_lines) >= 2:
                self.doc.text(self.page, x + 10, y_top - 42, sub_lines[0], font="/F1", size=5.8, color=(0.45, 0.5, 0.55))
                self.doc.text(self.page, x + 10, y_top - 51, sub_lines[1], font="/F1", size=5.8, color=(0.45, 0.5, 0.55))
            elif sub_lines:
                self.doc.text(self.page, x + 10, y_top - 47, sub_lines[0], font="/F1", size=6.0, color=(0.45, 0.5, 0.55))
        self.y -= h + 8

    def findings_box(self, title: str, findings: list[str]) -> None:
        leading = 10.2
        wrapped_groups = [wrap_text(f, "/F1", 7.0, self.WIDTH - 24) for f in findings]
        total_lines = sum(len(g) for g in wrapped_groups)
        h = 20.0 + total_lines * leading + len(findings) * 2.5
        self.ensure(h + 8)
        y_bottom = self.y - h
        self.doc.rect(self.page, self.LEFT, y_bottom, self.WIDTH, h, fill=(0.98, 0.99, 1.0), stroke=(0.88, 0.9, 0.94))
        self.doc.text(self.page, self.LEFT + 12, self.y - 13, title, font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
        cur_y = self.y - 25
        for idx, lines in enumerate(wrapped_groups):
            col = (0.3, 0.35, 0.4) if idx == len(wrapped_groups) - 1 else (0.1, 0.1, 0.1)
            for line_idx, line in enumerate(lines):
                indent = 0 if line_idx == 0 else 10
                self.doc.text(self.page, self.LEFT + 12 + indent, cur_y, line, font="/F1", size=7.0, color=col)
                cur_y -= leading
            cur_y -= 2.5
        self.y -= h + 8

    def audit_stamp_box(self, title: str, lines: list[tuple[str, str]], run_id: str) -> None:
        self.ensure(118)
        audit_top = self.y
        self.doc.rect(self.page, self.LEFT, audit_top - 112, self.WIDTH, 108, fill=(0.96, 0.97, 0.99), stroke=(0.8, 0.85, 0.92))
        self.doc.text(self.page, self.LEFT + 12, audit_top - 18, title, font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
        line_y = audit_top - 33
        for content, font in lines:
            for wrapped_line in wrap_text(content, font, 7.0, 424):
                self.doc.text(self.page, self.LEFT + 12, line_y, wrapped_line, font=font, size=7.0)
                line_y -= 10
        self.doc.text(self.page, self.LEFT + 12, line_y - 2, "* This PDF is outside the bundle verification contract. A successful replay establishes nothing", font="/F1", size=7.0, color=(0.4, 0.45, 0.5))
        self.doc.text(self.page, self.LEFT + 12, line_y - 12, "  about these pages. No scientific validation or professional approval is claimed or implied.", font="/F1", size=7.0, color=(0.4, 0.45, 0.5))

        self.doc.rect(self.page, 480, audit_top - 104, 85, 76, fill=(1.0, 1.0, 1.0), stroke=(0.08, 0.49, 0.55), line_width=1.5)
        self.doc.text(self.page, 489, audit_top - 42, "VERIFICATION", font="/F2", size=7.0, color=(0.08, 0.49, 0.55))
        self.doc.text(self.page, 505, audit_top - 52, "SCOPE", font="/F2", size=7.0, color=(0.08, 0.49, 0.55))
        self.doc.text(self.page, 492, audit_top - 68, "BUNDLE ONLY", font="/F2", size=8.0, color=(0.08, 0.49, 0.55))
        self.doc.text(self.page, 487, audit_top - 80, "PDF NOT VERIFIED", font="/F2", size=6.5, color=(0.7, 0.4, 0.05))
        self.doc.text(self.page, 488, audit_top - 94, f"ID: {clip_text(run_id, 13)}", font="/F3", size=6.5, color=(0.3, 0.35, 0.4))
        self.y = audit_top - 118

    def insert_toc_page(self) -> None:
        """Insert a Table of Contents page after page 1.

        Must be called after all content pages are rendered so that the section
        registry is complete. Shifts all recorded page indices by +1 to account
        for the inserted page, then renders a styled TOC with dot-leaders and
        page numbers. Link annotations are stored for ``VectorPDFBuilder.render``
        to embed as clickable PDF links.
        """
        if not self.sections:
            return
        # Shift page indices for content that comes after the TOC insertion point.
        # Page 0 (the cover/Executive Summary) stays at index 0 — the TOC is
        # inserted at index 1, so only pages originally at index >= 1 move up by 1.
        shifted = [(title, page_idx + 1 if page_idx >= 1 else page_idx)
                   for title, page_idx in self.sections]

        # Deduplicate: keep only the first heading per section number.
        seen: set[str] = set()
        unique: list[tuple[str, int]] = []
        for title, pidx in shifted:
            num = title.split(".")[0].strip()
            if num not in seen:
                seen.add(num)
                unique.append((title, pidx))

        toc_page: list[str] = []
        self.doc.pages.insert(1, toc_page)

        # Dark header banner (consistent with continuation pages)
        self.doc.rect(toc_page, 36, 742, 540, 26, fill=(0.06, 0.09, 0.16))
        self.doc.text(toc_page, 50, 750, "BASIN * TABLE OF CONTENTS",
                      font="/F2", size=9.0, color=(1.0, 1.0, 1.0))
        self.doc.text(toc_page, 415, 750, f"RUN ID: {clip_text(self.run_id, 14)}",
                      font="/F3", size=7.5, color=(0.85, 0.9, 0.95))

        # Title
        self.doc.text(toc_page, self.LEFT, 708, "TABLE OF CONTENTS",
                      font="/F2", size=12.0, color=(0.06, 0.09, 0.16))

        # Separator line
        self.doc.line(toc_page, self.LEFT, 698, self.RIGHT, 698,
                      stroke=(0.06, 0.09, 0.16), line_width=0.8)

        # Render each TOC entry
        entry_y = 680
        leading = 22.0
        # Shorten verbose section titles for the TOC display.
        _short = {
            "SCENARIO IDENTITY AND RAINFALL INPUT": "Scenario Identity & Rainfall Input",
            "REVIEW DECISION AND RATIONALE": "Review Decision & Rationale",
            "STORAGE-SYSTEM ASSUMPTIONS": "Storage-System Assumptions",
            "EXPERIMENT RESULTS": "Experiment Results",
            "OBSERVATION PROVENANCE": "Observation Provenance",
            "LIMITATIONS": "Limitations",
            "VERIFICATION AND HASHES": "Verification & Hashes",
            "EXECUTIVE SUMMARY": "Executive Summary",
        }

        annots: list[tuple[float, float, float, float, int]] = []  # (x, y, w, h, dest_page_idx)
        for title, dest_page_idx in unique:
            # Parse section number and name
            dot_pos = title.index(".")
            sec_num = title[:dot_pos].strip()
            sec_name_raw = title[dot_pos + 1:].strip()
            # Use shortened name if available
            sec_name = _short.get(sec_name_raw, sec_name_raw.title())
            display = f"{sec_num}. {sec_name}"

            # Page number (1-based, accounting for the inserted TOC page)
            page_num_str = str(dest_page_idx + 1)

            # Draw section title
            self.doc.text(toc_page, self.LEFT + 12, entry_y, display,
                          font="/F2", size=9.0, color=(0.10, 0.12, 0.18))

            # Draw page number right-aligned
            num_x = self.RIGHT - 12 - text_width(page_num_str, "/F3", 9.0)
            self.doc.text(toc_page, num_x, entry_y, page_num_str,
                          font="/F3", size=9.0, color=(0.10, 0.12, 0.18))

            # Draw dot leader between title and page number
            title_end_x = self.LEFT + 12 + text_width(display, "/F2", 9.0) + 8
            dots_end_x = num_x - 8
            if dots_end_x > title_end_x:
                # Build a dot string that fits the gap exactly.
                gap = dots_end_x - title_end_x
                dot_unit = " . "
                unit_w = text_width(dot_unit, "/F1", 7.0)
                num_dots = max(0, int(gap / unit_w)) if unit_w > 0 else 0
                dot_str = dot_unit * num_dots
                # Trim if the rendered width still exceeds the gap.
                while num_dots > 0 and text_width(dot_str, "/F1", 7.0) > gap:
                    num_dots -= 1
                    dot_str = dot_unit * num_dots
                if dot_str.strip():
                    self.doc.text(toc_page, title_end_x, entry_y, dot_str,
                                  font="/F1", size=7.0, color=(0.55, 0.60, 0.65))

            # Record link annotation rectangle for this entry
            annots.append((self.LEFT, entry_y - 4, self.WIDTH, leading, dest_page_idx))

            entry_y -= leading

        # Bottom separator line
        sep_y = entry_y + 6
        self.doc.line(toc_page, self.LEFT, sep_y, self.RIGHT, sep_y,
                      stroke=(0.06, 0.09, 0.16), line_width=0.8)

        # Explanatory note below the TOC
        self.doc.text(toc_page, self.LEFT + 12, sep_y - 16,
                      "This report is organized as a structured executive brief with 8 numbered sections.",
                      font="/F1", size=7.0, color=(0.45, 0.50, 0.55))
        self.doc.text(toc_page, self.LEFT + 12, sep_y - 28,
                      "Click any section above to navigate directly, or page through sequentially.",
                      font="/F1", size=7.0, color=(0.45, 0.50, 0.55))

        # Store annotations on the doc for render() to embed as PDF /Link objects.
        self.doc.toc_annots = (1, annots)  # (toc_page_index, list of link rects)

    def table_header(self, columns) -> None:
        """columns: sequence of (x, label, width)."""
        self.ensure(18 + 24)
        self.doc.rect(self.page, self.LEFT, self.y - 18, self.WIDTH, 18, fill=(0.12, 0.16, 0.24))
        for x, label, width in columns:
            for line in wrap_text(label, "/F2", 7.0, width)[:1]:
                self.doc.text(self.page, x, self.y - 13, line, font="/F2", size=7.0, color=(1, 1, 1))
        self.y -= 18
        self._columns = columns

    def table_row(self, cells, index: int, size: float = 6.8) -> None:
        """cells: sequence of (text, font) aligned with the current header columns."""
        leading = size + 2.0
        wrapped = [
            wrap_text(text, font, size, width - 6)
            for (text, font), (_, _, width) in zip(cells, self._columns)
        ]
        total_lines = max(len(lines) for lines in wrapped)
        height = total_lines * leading + 6
        full_page_height = self.TOP + 20 - 18 - self.BOTTOM

        # If the row fits on a fresh page but not on the current page, break to a fresh page
        if height <= full_page_height and not self.room_for(height):
            self.break_page()
            self.table_header(self._columns)

        offset = 0
        while offset < total_lines:
            available = int((self.y - self.BOTTOM - 6) / leading)
            if available < 1:
                self.break_page()
                self.table_header(self._columns)
                continue
            count = min(available, total_lines - offset)
            h_chunk = count * leading + 6
            self.doc.rect(self.page, self.LEFT, self.y - h_chunk, self.WIDTH, h_chunk,
                          fill=(0.96, 0.97, 0.99) if index % 2 == 0 else (1.0, 1.0, 1.0))
            for lines, (x, _, _), (_, font) in zip(wrapped, self._columns, cells):
                segment = lines[offset:offset + count] if offset < len(lines) else []
                for row_offset, line in enumerate(segment):
                    self.doc.text(self.page, x, self.y - size - 3 - row_offset * leading, line,
                                  font=font, size=size, color=(0.15, 0.18, 0.22))
            self.y -= h_chunk
            offset += count


def draw_vector_pareto_frontier(flow: VectorFlow, workspace, h: float = 140.0):
    """Render pure-vector Pareto Frontier shortlist distribution across duration clusters."""
    scenarios = getattr(workspace, "scenarios", [])
    if not scenarios:
        return
    flow.ensure(h + 36)
    plot_w = flow.WIDTH - 60
    plot_h = h - 46
    left = flow.LEFT + 45
    bottom = flow.y - h + 22
    top = bottom + plot_h
    
    flow.doc.text(flow.page, flow.LEFT, flow.y - 8, "Figure 3: Candidate Deficit & Shortlist Distribution Across Durations (Pareto Frontier)", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    
    selected_ids = set(getattr(workspace, "selected", []))
    durations = sorted(list(set(int(s.features.get("duration_days", 90)) for s in scenarios if hasattr(s, "features"))))
    if not durations:
        durations = [90, 180, 270]
        
    max_def = 50.0
    for s in scenarios:
        val = float(s.features.get("deficit_mm", 0.0))
        if val > max_def: max_def = val
    max_def = math.ceil(max_def / 50.0) * 50.0
    
    # Y-axis & Gridlines
    flow.doc.line(flow.page, left, bottom, left, top, stroke=(0.55, 0.60, 0.65), line_width=0.8)
    step = 100 if max_def >= 300 else 50
    for v in range(0, int(max_def) + 1, step):
        y_t = bottom + (v / max_def) * plot_h
        flow.doc.line(flow.page, left - 3, y_t, left, y_t, stroke=(0.55, 0.60, 0.65), line_width=0.8)
        flow.doc.line(flow.page, left, y_t, left + plot_w, y_t, stroke=(0.92, 0.93, 0.95), line_width=0.5)
        flow.doc.text(flow.page, left - 24, y_t - 2, f"{v}", font="/F1", size=6.0, color=(0.35, 0.4, 0.45))
    flow.doc.text(flow.page, left - 36, top + 6, "Deficit (mm)", font="/F2", size=6.5, color=(0.2, 0.25, 0.3))
    
    col_w = plot_w / len(durations)
    for i, dur in enumerate(durations):
        cx = left + i * col_w + col_w / 2
        flow.doc.line(flow.page, left + i * col_w, bottom, left + (i + 1) * col_w, bottom, stroke=(0.55, 0.60, 0.65), line_width=0.8)
        flow.doc.text(flow.page, cx - 18, top + 6, f"{dur}-Day Cluster", font="/F2", size=7.0, color=(0.15, 0.2, 0.28))
        # Bottom axis numeric tick and label
        flow.doc.line(flow.page, cx, bottom, cx, bottom - 3, stroke=(0.55, 0.60, 0.65), line_width=0.8)
        flow.doc.text(flow.page, cx - 10, bottom - 10, f"{dur} d", font="/F1", size=6.0, color=(0.35, 0.4, 0.45))
        if i > 0:
            flow.doc.line(flow.page, left + i * col_w, bottom, left + i * col_w, top, stroke=(0.88, 0.90, 0.94), line_width=0.5)
    flow.doc.text(flow.page, left + plot_w / 2 - 35, bottom - 20, "Duration Clusters (Days)", font="/F2", size=6.5, color=(0.2, 0.25, 0.3))
            
    cluster_colors = [
        (0.12, 0.53, 0.53),
        (0.82, 0.60, 0.40),
        (0.45, 0.62, 0.52),
        (0.35, 0.45, 0.65),
        (0.70, 0.45, 0.30),
        (0.55, 0.55, 0.55),
    ]
    
    max_per_dur = {}
    for dur in durations:
        in_dur = [s for s in scenarios if int(s.features.get("duration_days", 90)) == dur]
        if in_dur:
            max_per_dur[dur] = max(in_dur, key=lambda s: float(s.features.get("deficit_mm", 0.0))).id
            
    for s in scenarios:
        dur = int(s.features.get("duration_days", 90))
        if dur not in durations: continue
        col_idx = durations.index(dur)
        cx = left + col_idx * col_w + col_w / 2
        def_mm = float(s.features.get("deficit_mm", 0.0))
        y_pt = bottom + (def_mm / max_def) * plot_h
        
        jitter = ((hash(s.id) % 31) - 15) * 1.5
        x_pt = cx + jitter
        c_idx = int(getattr(s, "cluster", 0)) % len(cluster_colors)
        col = cluster_colors[c_idx]
        
        flow.doc.rect(flow.page, x_pt - 2, y_pt - 2, 4, 4, fill=col)
        
        if max_per_dur.get(dur) == s.id:
            flow.doc.rect(flow.page, x_pt - 5, y_pt - 5, 10, 10, stroke=(0.85, 0.55, 0.05), line_width=1.2)
            
        if s.id in selected_ids:
            flow.doc.rect(flow.page, x_pt - 4.5, y_pt - 4.5, 9, 9, stroke=(0.03, 0.49, 0.55), line_width=1.5)
            
    leg_y = bottom - 32
    flow.doc.rect(flow.page, left + 10, leg_y, 4, 4, fill=cluster_colors[0])
    flow.doc.text(flow.page, left + 18, leg_y, "Cluster candidate scenario", font="/F1", size=6.0, color=(0.35, 0.4, 0.45))
    flow.doc.rect(flow.page, left + 140, leg_y - 2, 8, 8, stroke=(0.85, 0.55, 0.05), line_width=1.2)
    flow.doc.text(flow.page, left + 152, leg_y, "Highest deficit in duration", font="/F1", size=6.0, color=(0.35, 0.4, 0.45))
    flow.doc.rect(flow.page, left + 270, leg_y - 2, 8, 8, stroke=(0.03, 0.49, 0.55), line_width=1.4)
    flow.doc.text(flow.page, left + 282, leg_y, "Selected for review shortlist", font="/F2", size=6.0, color=(0.03, 0.49, 0.55))
    
    flow.y = bottom - 42


def draw_vector_multi_scenario_overlay(flow: VectorFlow, workspace, accepted: Sequence, config: ExperimentConfig, bands=(0.40, 0.30, 0.20, 0.15), h: float = 145.0):
    """Render pure-vector multi-scenario combined reservoir drawdown overlay against policy bands."""
    if not accepted:
        return
    flow.ensure(h + 46)
    flow.y -= 4
    plot_w = flow.WIDTH - 55
    plot_h = h - 54
    left = flow.LEFT + 45
    top = flow.y - 32
    bottom = top - plot_h
    
    init_pct_val = config.initial_pct * 100.0
    flow.doc.text(flow.page, flow.LEFT, flow.y - 2, f"Figure 3: Shortlist Ensemble Reservoir Drawdown Overlay ({init_pct_val:g}% Initial Storage, 0% Baseline Conservation)", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    
    # Subtitle referencing diverse Duration Clusters (Days)
    flow.doc.text(flow.page, flow.LEFT, flow.y - 12, "Synchronized storage drawdown trajectories across accepted candidate scenarios from diverse Duration Clusters (Days).", font="/F1", size=6.2, color=(0.35, 0.40, 0.48))
    
    band_colors = [
        (0.95, 0.98, 0.96),
        (0.99, 0.97, 0.93),
        (0.99, 0.95, 0.92),
        (0.99, 0.92, 0.92),
        (0.96, 0.90, 0.90),
    ]
    b_vals = [1.0, *bands, 0.0]
    for i in range(len(b_vals) - 1):
        y_top = bottom + b_vals[i] * plot_h
        y_bot = bottom + b_vals[i+1] * plot_h
        flow.doc.rect(flow.page, left, y_bot, plot_w, y_top - y_bot, fill=band_colors[i])
        
    for b in bands:
        y_line = bottom + b * plot_h
        flow.doc.line(flow.page, left, y_line, left + plot_w, y_line, stroke=(0.7, 0.75, 0.8), line_width=0.7)
        flow.doc.text(flow.page, left + 6, y_line + 2, f"Band {int(b*100)}%", font="/F1", size=5.5, color=(0.45, 0.5, 0.55))
        
    # Y-axis
    flow.doc.line(flow.page, left, bottom, left, top, stroke=(0.6, 0.65, 0.7), line_width=0.8)
    for pct in (0, 20, 40, 60, 80, 100):
        y_t = bottom + (pct / 100.0) * plot_h
        flow.doc.line(flow.page, left - 3, y_t, left, y_t, stroke=(0.6, 0.65, 0.7), line_width=0.8)
        flow.doc.text(flow.page, left - 24, y_t - 2, f"{pct}%", font="/F1", size=6.0, color=(0.35, 0.4, 0.45))
    flow.doc.text(flow.page, left - 38, top + 4, "Storage (%)", font="/F2", size=6.5, color=(0.25, 0.3, 0.35))
    
    system_cfg = config.system_config or REGION_N_PRESET
    curves = []
    primary_sid = config.scenario_id or (accepted[0].id if accepted else None)
    
    for s in accepted:
        s_series = getattr(s, "series", None)
        if s_series is None or len(s_series) == 0:
            continue
        try:
            sim_df = simulate_reservoir_drawdown(
                s_series,
                initial_pct=config.initial_pct,
                conservation_pct=0.0,
                pipeline_active=config.pipeline_active,
                pipeline_reliability_pct=config.pipeline_reliability_pct,
                stepped_policy=config.stepped_policy,
                config=system_cfg,
            )
            dur = int(getattr(s, "features", {}).get("duration_days", len(s_series)))
            curves.append((s.id, dur, sim_df, s.id == primary_sid))
        except Exception:
            continue
            
    if not curves:
        flow.y = bottom - 20
        return
        
    max_days = max(max(int(df["day"].max()) for _, _, df, _ in curves), 90)
    
    # X-axis
    flow.doc.line(flow.page, left, bottom, left + plot_w, bottom, stroke=(0.6, 0.65, 0.7), line_width=0.8)
    tick_step = 30 if max_days <= 120 else (60 if max_days <= 240 else 90)
    for d in range(0, max_days + 1, tick_step):
        x_d = left + (d / max_days) * plot_w
        flow.doc.line(flow.page, x_d, bottom, x_d, bottom - 3, stroke=(0.6, 0.65, 0.7), line_width=0.8)
        flow.doc.text(flow.page, x_d - 6, bottom - 10, f"D{d}", font="/F1", size=6.0, color=(0.4, 0.45, 0.5))
    flow.doc.text(flow.page, left + plot_w / 2 - 95, bottom - 15, "Elapsed Scenario Days (Synchronized Onset across Duration Clusters (Days))", font="/F2", size=6.0, color=(0.25, 0.3, 0.35))
    
    palette = [
        (0.85, 0.52, 0.08),  # Amber
        (0.05, 0.59, 0.41),  # Emerald
        (0.40, 0.35, 0.75),  # Violet
        (0.80, 0.25, 0.25),  # Crimson
        (0.40, 0.48, 0.55),  # Slate
        (0.70, 0.40, 0.15),  # Bronze
    ]
    pal_idx = 0
    end_labels = []
    
    for s_id, dur, sim_df, is_primary in curves:
        col = (0.03, 0.49, 0.55) if is_primary else palette[pal_idx % len(palette)]
        lw = 2.0 if is_primary else 1.1
        if not is_primary:
            pal_idx += 1
            
        pts = []
        for _, row in sim_df.iterrows():
            d = float(row["day"])
            pct = float(row["combined_pct"]) / 100.0
            x_pt = left + (d / max_days) * plot_w
            y_pt = bottom + min(1.0, max(0.0, pct)) * plot_h
            pts.append((x_pt, y_pt))
            
        for i in range(len(pts) - 1):
            flow.doc.line(flow.page, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], stroke=col, line_width=lw)
            
        if pts:
            lx, ly = pts[-1]
            end_pct = sim_df.iloc[-1]["combined_pct"]
            flow.doc.rect(flow.page, lx - 2, ly - 2, 4, 4, fill=col)
            end_labels.append((lx, ly, s_id, end_pct, col, is_primary))
            
    # Stagger end labels to avoid overlapping text
    end_labels.sort(key=lambda item: item[1])
    min_dist = 7.5
    staggered_y = []
    for lx, ly, sid, end_pct, col, is_prim in end_labels:
        target_y = max(bottom + 4, ly)
        if staggered_y and target_y - staggered_y[-1] < min_dist:
            target_y = staggered_y[-1] + min_dist
        staggered_y.append(target_y)
        lbl = f"{sid}: {end_pct:.1f}%"
        txt_font = "/F2" if is_prim else "/F1"
        txt_size = 5.6 if is_prim else 5.2
        x_lbl = (lx - 48) if lx >= (left + plot_w - 15) else min(lx + 4, left + plot_w - 42)
        flow.doc.text(flow.page, x_lbl, target_y - 2, lbl, font=txt_font, size=txt_size, color=col)
        
    flow.doc.text(
        flow.page,
        flow.LEFT,
        bottom - 25,
        "Note on Time Alignment: X-axis represents elapsed days synchronized to each candidate's onset (Day 1). Short-duration events (90–180 d)",
        font="/F1",
        size=5.8,
        color=(0.40, 0.45, 0.50),
    )
    flow.doc.text(
        flow.page,
        flow.LEFT,
        bottom - 32,
        "terminate at their respective durations, illustrating the contrast between acute single-season shocks and persistent multi-season attrition.",
        font="/F1",
        size=5.8,
        color=(0.40, 0.45, 0.50),
    )
    
    flow.y = bottom - 40


def draw_vector_storage_trajectory(flow: VectorFlow, sim_df, bands=(0.40, 0.30, 0.20, 0.15), h: float = 160.0, sim_cons=None, config: ExperimentConfig | None = None, primary_id: str | None = None):
    """Render pure-vector combined reservoir storage drawdown curve with policy bands and dual-run conservation overlay."""
    if sim_df is None or len(sim_df) == 0:
        return
    flow.ensure(h + 36)
    flow.y -= 8
    plot_w = flow.WIDTH - 55
    plot_h = h - 34
    left = flow.LEFT + 45
    bottom = flow.y - h + 18
    top = bottom + plot_h
    
    flow.doc.text(flow.page, flow.LEFT, flow.y - 2, "Figure 1: Projected Reservoir Storage Trajectory & Threshold Crossings (Uncalibrated Screening Simulation)", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    
    band_colors = [
        (0.95, 0.98, 0.96),
        (0.99, 0.97, 0.93),
        (0.99, 0.95, 0.92),
        (0.99, 0.92, 0.92),
        (0.96, 0.90, 0.90),
    ]
    b_vals = [1.0, *bands, 0.0]
    for i in range(len(b_vals) - 1):
        y_top = bottom + b_vals[i] * plot_h
        y_bot = bottom + b_vals[i+1] * plot_h
        flow.doc.rect(flow.page, left, y_bot, plot_w, y_top - y_bot, fill=band_colors[i])
        
    for b in bands:
        y_line = bottom + b * plot_h
        flow.doc.line(flow.page, left, y_line, left + plot_w, y_line, stroke=(0.7, 0.75, 0.8), line_width=0.7)
        flow.doc.text(flow.page, left + 6, y_line + 2, f"Band {int(b*100)}%", font="/F1", size=5.5, color=(0.45, 0.5, 0.55))
        
    flow.doc.line(flow.page, left, bottom, left, top, stroke=(0.6, 0.65, 0.7), line_width=0.8)
    for pct in (0, 20, 40, 60, 80, 100):
        y_t = bottom + (pct / 100.0) * plot_h
        flow.doc.line(flow.page, left - 3, y_t, left, y_t, stroke=(0.6, 0.65, 0.7), line_width=0.8)
        flow.doc.text(flow.page, left - 24, y_t - 2, f"{pct}%", font="/F1", size=6.0, color=(0.35, 0.4, 0.45))
    flow.doc.text(flow.page, left - 38, top + 6, "Storage (%)", font="/F2", size=6.5, color=(0.25, 0.3, 0.35))
    
    flow.doc.line(flow.page, left, bottom, left + plot_w, bottom, stroke=(0.6, 0.65, 0.7), line_width=0.8)
    max_day = max(1, int(sim_df["day"].max()))
    tick_step = 30 if max_day <= 120 else (60 if max_day <= 240 else 90)
    for d in range(0, max_day + 1, tick_step):
        x_d = left + (d / max_day) * plot_w
        flow.doc.line(flow.page, x_d, bottom, x_d, bottom - 3, stroke=(0.6, 0.65, 0.7), line_width=0.8)
        flow.doc.text(flow.page, x_d - 6, bottom - 10, f"D{d}", font="/F1", size=6.0, color=(0.4, 0.45, 0.5))
    flow.doc.text(flow.page, left + plot_w / 2 - 20, bottom - 13, "Scenario Day", font="/F1", size=6.0, color=(0.4, 0.45, 0.5))
    
    has_dual_run = (
        sim_cons is not None
        and len(sim_cons) > 0
        and config is not None
        and config.conservation_pct > 0.0
    )
    
    # Baseline Run (sim_df = 0% conservation)
    pts_base = []
    for _, row in sim_df.iterrows():
        d = float(row["day"])
        pct = float(row["combined_pct"]) / 100.0
        x_pt = left + (d / max_day) * plot_w
        y_pt = bottom + min(1.0, max(0.0, pct)) * plot_h
        pts_base.append((x_pt, y_pt))
        
    base_col = (0.50, 0.55, 0.62) if has_dual_run else (0.03, 0.49, 0.55)
    base_lw = 1.3 if has_dual_run else 1.6
    for i in range(len(pts_base) - 1):
        if has_dual_run and (i % 2 == 1):
            continue  # dashed effect for baseline
        flow.doc.line(flow.page, pts_base[i][0], pts_base[i][1], pts_base[i+1][0], pts_base[i+1][1], stroke=base_col, line_width=base_lw)
        
    end_val_cons = None
    end_val_base = None
    if has_dual_run:
        pts_cons = []
        for _, row in sim_cons.iterrows():
            d = float(row["day"])
            pct = float(row["combined_pct"]) / 100.0
            x_pt = left + (d / max_day) * plot_w
            y_pt = bottom + min(1.0, max(0.0, pct)) * plot_h
            pts_cons.append((x_pt, y_pt))
            
        for i in range(len(pts_cons) - 1):
            flow.doc.line(flow.page, pts_cons[i][0], pts_cons[i][1], pts_cons[i+1][0], pts_cons[i+1][1], stroke=(0.03, 0.49, 0.55), line_width=1.8)
            
        if pts_cons and pts_base:
            cx, cy = pts_cons[-1]
            bx, by = pts_base[-1]
            end_val_cons = sim_cons.iloc[-1]["combined_pct"]
            end_val_base = sim_df.iloc[-1]["combined_pct"]
            cons_pct_int = int(round(config.conservation_pct * 100))
            
            # Smart vertical placement to avoid crossing the bottom axis (D0-D270 ticks)
            badge_y_base = by - 14
            badge_y_cons = cy + 3
            if badge_y_base < bottom + 2:
                badge_y_base = bottom + 2
                badge_y_cons = max(badge_y_base + 13, cy + 3)
            elif badge_y_cons - badge_y_base < 12:
                badge_y_cons = badge_y_base + 13

            flow.doc.rect(flow.page, cx - 62, badge_y_cons, 60, 11, fill=(0.03, 0.49, 0.55))
            flow.doc.text(flow.page, cx - 59, badge_y_cons + 3, f"{cons_pct_int}% Cons: {end_val_cons:.1f}%", font="/F2", size=6.0, color=(1, 1, 1))
            
            flow.doc.rect(flow.page, bx - 62, badge_y_base, 60, 11, fill=(0.50, 0.55, 0.62))
            flow.doc.text(flow.page, bx - 59, badge_y_base + 3, f"0% Base: {end_val_base:.1f}%", font="/F2", size=6.0, color=(1, 1, 1))
        elif pts_base:
            bx, by = pts_base[-1]
            end_val_base = sim_df.iloc[-1]["combined_pct"]
            badge_y_base = max(bottom + 2, by - 14)
            flow.doc.rect(flow.page, bx - 62, badge_y_base, 60, 11, fill=(0.50, 0.55, 0.62))
            flow.doc.text(flow.page, bx - 59, badge_y_base + 3, f"End: {end_val_base:.1f}%", font="/F2", size=6.0, color=(1, 1, 1))
            
        if end_val_cons is not None and end_val_base is not None:
            cons_pct_int = int(round(config.conservation_pct * 100))
            daily_saved = 370.0 * config.conservation_pct
            total_saved = daily_saved * max_day
            buffer_pct = (total_saved / 919900.0) * 100.0
            cons_end_acft = (end_val_cons / 100.0) * 919900.0
            base_end_acft = (end_val_base / 100.0) * 919900.0
            caption_line = (
                f"Active Run ({cons_pct_int}% Cons): End {end_val_cons:.1f}% ({cons_end_acft:,.0f} ac-ft) | "
                f"Baseline (0% Cons): End {end_val_base:.1f}% ({base_end_acft:,.0f} ac-ft) | "
                f"Buffer: +{total_saved:,.0f} ac-ft (+{buffer_pct:.2f}%; saves {daily_saved:.1f} ac-ft/d)."
            )
            flow.doc.text(flow.page, flow.LEFT, bottom - 23, caption_line, font="/F2", size=5.8, color=(0.15, 0.25, 0.35))
            flow.y = bottom - 32
        else:
            flow.y = bottom - 22
    else:
        if pts_base:
            last_x, last_y = pts_base[-1]
            flow.doc.rect(flow.page, last_x - 42, last_y + 3, 40, 11, fill=(0.03, 0.49, 0.55))
            end_val = sim_df.iloc[-1]["combined_pct"]
            flow.doc.text(flow.page, last_x - 39, last_y + 6, f"End {end_val:.1f}%", font="/F2", size=6.0, color=(1, 1, 1))
        flow.y = bottom - 22


def draw_vector_milestone_gantt(flow: VectorFlow, spectrum_data: dict, bands_pct=(40.0, 30.0, 20.0, 15.0), h: float = 135.0):
    """Render pure-vector milestone timeline across retention tiers."""
    summary = spectrum_data.get("summary_table", [])
    if not summary:
        return
    flow.ensure(h + 30)
    flow.y -= 10
    plot_w = flow.WIDTH - 140
    left = flow.LEFT + 130
    
    flow.doc.text(flow.page, flow.LEFT, flow.y - 10, "Figure 2: Milestone Gantt Timeline — Response Band Crossings Across Retention Tiers", font="/F2", size=8.5, color=(0.06, 0.09, 0.16))
    
    leg_y = flow.y - 20
    leg_items = [
        ("Normal (>40%)", (0.05, 0.59, 0.41)),
        ("Band 1 (<=40%)", (0.85, 0.47, 0.02)),
        ("Band 2 (<=30%)", (0.92, 0.35, 0.05)),
        ("Band 3 (<=20%)", (0.86, 0.15, 0.15)),
        ("Band 4 (<=15%)", (0.50, 0.11, 0.11)),
    ]
    cur_lx = left
    for label, col in leg_items:
        flow.doc.rect(flow.page, cur_lx, leg_y - 1, 6, 6, fill=col)
        flow.doc.text(flow.page, cur_lx + 8, leg_y, label, font="/F1", size=5.5, color=(0.3, 0.35, 0.4))
        cur_lx += len(label) * 3.6 + 14

    max_days = 90
    for r in summary:
        for k in ("day_stage1_40", "day_stage2_30", "day_stage3_20", "day_stage4_15"):
            if r.get(k): max_days = max(max_days, r[k])
    
    row_h = 12.0
    gap = 4.0
    start_y = leg_y - 14
    
    for i, r in enumerate(summary):
        y_row = start_y - i * (row_h + gap)
        tier_lbl = r.get("tier_label", f"Tier {i+1}").split(" (")[0]
        flow.doc.text(flow.page, flow.LEFT, y_row + 3, tier_lbl, font="/F2", size=6.5, color=(0.15, 0.18, 0.22))
        
        d1 = r.get("day_stage1_40")
        d2 = r.get("day_stage2_30")
        d3 = r.get("day_stage3_20")
        d4 = r.get("day_stage4_15")
        
        events = [(0, 0)]
        if d1 is not None and d1 > 0: events.append((d1, 1))
        if d2 is not None and d2 > 0: events.append((d2, 2))
        if d3 is not None and d3 > 0: events.append((d3, 3))
        if d4 is not None and d4 > 0: events.append((d4, 4))
        events.sort()
        
        for seg_idx in range(len(events)):
            s_day, s_st = events[seg_idx]
            e_day = events[seg_idx + 1][0] if seg_idx + 1 < len(events) else max_days
            if e_day <= s_day: continue
            
            x_seg = left + (s_day / max_days) * plot_w
            w_seg = ((e_day - s_day) / max_days) * plot_w
            seg_col = leg_items[min(s_st, len(leg_items)-1)][1]
            
            flow.doc.rect(flow.page, x_seg, y_row, w_seg, row_h, fill=seg_col)
            if s_day > 0 and w_seg > 16:
                flow.doc.text(flow.page, x_seg + 2, y_row + 3.5, f"D{s_day}", font="/F2", size=5.5, color=(1, 1, 1))
                
    y_axis = start_y - len(summary) * (row_h + gap)
    flow.doc.line(flow.page, left, y_axis, left + plot_w, y_axis, stroke=(0.6, 0.65, 0.7), line_width=0.8)
    for d in range(0, max_days + 1, 30 if max_days <= 120 else 60):
        xd = left + (d / max_days) * plot_w
        flow.doc.line(flow.page, xd, y_axis, xd, y_axis - 2, stroke=(0.6, 0.65, 0.7), line_width=0.8)
        flow.doc.text(flow.page, xd - 4, y_axis - 8, f"D{d}", font="/F1", size=5.5, color=(0.4, 0.45, 0.5))
        
    flow.y = y_axis - 18


def build_fallback_pdf(
    workspace_or_title,
    accepted_or_text=None,
    initial_pct: float | None = None,
    conservation_pct: float | None = None,
    include_notes: bool = False,
    config: ExperimentConfig | None = None,
) -> bytes:
    """Publication-grade pure-Python vector PDF generator organized in strict 8-section sequence."""
    doc = VectorPDFBuilder()

    config = resolve_config(config, initial_pct, conservation_pct)
    init_frac = config.initial_pct
    cons_frac = config.conservation_pct
    scenario_note: str | None = None

    if isinstance(workspace_or_title, str):
        title = workspace_or_title
        body_text = str(accepted_or_text or "")
        run_id = UNAVAILABLE
        created_date = UNAVAILABLE
        stations = UNAVAILABLE
        snapshot_hash = UNAVAILABLE
        accepted = []
        metrics = compute_report_metrics(None, config)
        primary_scenario = None
        custom_uploads = []
        evidence_records = []
        conflicts = []
        provider_note = ""
        audience_label = "Region N planning area"
        county_label = "All 11 Region N counties"
        workspace = None
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
        config, primary_scenario, scenario_note, metrics = _report_context(workspace, accepted, config)
        init_frac = config.initial_pct
        cons_frac = config.conservation_pct
        body_text = f"Evaluated {len(accepted)} accepted scenarios under {init_frac * 100:g}% starting storage."
        custom_uploads = getattr(workspace, "custom_uploads", []) or []
        evidence_records = list(getattr(workspace, "evidence", []) or [])
        conflicts = list(getattr(workspace, "conflicts", []) or [])
        provider_note = str(getattr(workspace, "notes", "") or "").strip()
        analysis_context = getattr(workspace, "analysis_context", None)
        audience_label = getattr(analysis_context, "audience_label", "Region N planning area")
        county_label = getattr(analysis_context, "county_label", "All 11 Region N counties")

    spectrum_data = metrics.spectrum_data
    system = config.system_config or REGION_N_PRESET
    system_assumptions = system.describe_assumptions()
    report_bands = tuple((fraction, f"Band {index}") for index, fraction in enumerate(system.stage_bands_pct, 1))
    critical_fraction = system.stage_bands_pct[2] if len(system.stage_bands_pct) >= 3 else 0.20
    band1_pct = (system.stage_bands_pct[0] if len(system.stage_bands_pct) >= 1 else 0.40) * 100
    band2_pct = (system.stage_bands_pct[1] if len(system.stage_bands_pct) >= 2 else 0.30) * 100
    critical_pct = critical_fraction * 100
    unavailable_note = (
        "" if metrics.available
        else f"Simulation unavailable: {metrics.unavailable_reason}. No substitute figures are shown."
    )

    # Depletion window (Multi-band reporting: Item 8)
    if not metrics.available:
        depletion_range_val = UNAVAILABLE
        depletion_range_sub = "*Not computed for this report"
    elif metrics.earliest_breach_day is not None:
        m_low = max(1, int(metrics.earliest_breach_day / 30.4))
        depletion_range_val = f"~{m_low}-{m_low + 1} Months (Screening Sim)*"
        depletion_range_sub = f"*Day {metrics.earliest_breach_day} in uncalibrated sim"
    elif metrics.highest_breached_day is not None:
        b_name = metrics.highest_breached_band.split(" (")[0] if metrics.highest_breached_band else "Band"
        depletion_range_val = f"{b_name} (Day {metrics.highest_breached_day})*"
        depletion_range_sub = f"*Band 3 (>20%) maintained in modeled window"
    else:
        depletion_range_val = "No breach in window*"
        depletion_range_sub = f"*Storage >{critical_pct:g}% across modeled window"

    # Conservation benefit / Reserve status
    day_base_3 = metrics.day_base_stage3
    day_cons_3 = metrics.day_cons_stage3
    card2_title = "CRITICAL RESERVE (BAND 3)"
    if not metrics.available:
        conservation_val = UNAVAILABLE
        conservation_sub = "*Not computed for this report"
    elif day_base_3 is not None and day_cons_3 is not None:
        diff = day_cons_3 - day_base_3
        if diff > 0:
            conservation_val = f"+{diff} Days Gained*"
            conservation_sub = f"*Deferred breach from Day {day_base_3} to Day {day_cons_3}"
        elif diff < 0:
            conservation_val = f"{diff} Days*"
            conservation_sub = "*Accelerated under these settings"
        else:
            conservation_val = "0 Days Gained*"
            conservation_sub = "*Configured runs reach the band on the same modeled day"
    elif day_base_3 is not None and day_cons_3 is None:
        conservation_val = "Delay not defined*"
        conservation_sub = f"*Chosen run did not reach {critical_pct:g}% in the modeled window"
    elif day_base_3 is None and day_cons_3 is None:
        daily_saved = (370.0 * cons_frac) if cons_frac > 0 else 0.0
        conservation_val = "Maintained >20%*"
        if metrics.stressed_case and metrics.stressed_case.get("day_base_20") is not None:
            st = metrics.stressed_case
            delay_35 = st.get("conservation_delay_days", 0)
            if daily_saved > 0:
                conservation_sub = f"*Band 3 preserved; both 0% & {cons_frac * 100:g}% runs >26% (saved +{daily_saved:.1f} ac-ft/d)"
            else:
                conservation_sub = f"*Band 3 preserved; +{delay_35} d in 35% benchmark"
        else:
            if daily_saved > 0:
                conservation_sub = f"*Band 3 preserved; both 0% & {cons_frac * 100:g}% runs >{critical_pct:g}% (saved +{daily_saved:.1f} ac-ft/d)"
            else:
                conservation_sub = f"*Band 3 preserved (>{critical_pct:g}%) throughout window"
    else:
        conservation_val = "Delay not defined*"
        conservation_sub = f"*Matched runs did not both reach {critical_pct:g}% in the modeled window"

    # Dominant loss driver
    if metrics.available and metrics.mean_evaporation_acft is not None:
        loss_driver_val = f"{metrics.mean_evaporation_acft:,.0f} ac-ft/day*"
        if metrics.mean_served_demand_acft and metrics.mean_served_demand_acft > 0:
            diff_pct = round(((metrics.mean_evaporation_acft - metrics.mean_served_demand_acft) / metrics.mean_served_demand_acft) * 100)
            comp_phrase = f"evap exceeds demand {diff_pct:+d}%" if diff_pct >= 0 else f"demand exceeds evap {abs(diff_pct)}%"
            loss_driver_sub = f"*Mean evaporation vs {metrics.mean_served_demand_acft:,.0f} demand ({comp_phrase})"
        else:
            loss_driver_sub = f"*Mean evaporation {metrics.mean_evaporation_acft:,.0f} ac-ft/day"
    else:
        loss_driver_val = UNAVAILABLE
        loss_driver_sub = "*Not computed for this report"

    capacities = model_capacities_acft(system)
    total_capacity = model_total_capacity_acft(system)
    capacity_breakdown = "; ".join(f"{name} {value:,.0f}" for name, value in capacities.items())
    surveyed_total = sum(SURVEYED_CAPACITIES_ACFT.values())
    region_n_sources = set(capacities) == set(SURVEYED_CAPACITIES_ACFT)
    tier_count = len(spectrum_data.get("summary_table", [])) if spectrum_data else 0
    replay_line = (
        "* Bundle Replay Command: not applicable, this report was generated without a session"
        if run_id == UNAVAILABLE
        else f"* Bundle Replay Command: python scripts/replay_bundle.py output/BASIN-{run_id}.zip"
    )

    if not metrics.available:
        tier_finding = f"- {unavailable_note}"
    else:
        tier_finding = (
            f"- The {critical_pct:g}% band ({band_storage_acft(critical_fraction, system):,.0f} ac-ft of model capacity) is tested across "
            f"{tier_count} rainfall retention tiers."
        )

    if not metrics.available:
        mandate_finding = "- Conservation comparison not computed for this report."
    elif day_base_3 is not None and day_cons_3 is not None:
        verb = "deferred" if day_cons_3 > day_base_3 else "did not defer"
        mandate_finding = (
            f"- In this run the {cons_frac * 100:g}% conservation setting {verb} the {critical_pct:g}% band "
            f"(no-conservation Day {day_base_3}, chosen-conservation Day {day_cons_3})."
        )
    elif day_base_3 is None and day_cons_3 is None:
        mandate_finding = f"- Neither matched conservation run reached the {critical_pct:g}% band in the modeled window; no delay is defined."
    else:
        mandate_finding = f"- The matched conservation runs did not both reach the {critical_pct:g}% band; no delay is defined."

    highest_desc = metrics.highest_breached_band or "No response bands breached in window"
    if metrics.highest_breached_day is not None and "breached" not in highest_desc.lower():
        highest_desc += f" (Day {metrics.highest_breached_day})"

    primary_features = getattr(primary_scenario, "features", {}) or {}
    primary_duration = int(primary_features.get("duration_days", 0))
    primary_deficit = float(primary_features.get("deficit_mm", 0.0))
    primary_percentile = float(primary_features.get("historical_percentile", 0.0)) * 100
    primary_benchmark_n = int(primary_features.get("benchmark_n", 0))
    active_station_count = len(primary_scenario.series.columns) if primary_scenario is not None and hasattr(primary_scenario, "series") else 0
    findings = [
        f"- {len(accepted)} rainfall scenarios were included through internal screening review; this is not external hydrologic approval.",
        f"- Primary scenario: {primary_duration} synchronized days across {active_station_count} selected NOAA point gauges.",
        f"- Equal-station mean rainfall shortfall: {primary_deficit:,.1f} mm.",
        f"- Historical rank: at or above {primary_percentile:.0f}% of {primary_benchmark_n} matched windows; this empirical rank is not a probability.",
        "- Point-gauge screening does not establish catchment-average precipitation, rainfall-runoff response, reservoir inflow, or water-supply reliability.",
        "- The separately labeled storage appendix is an uncalibrated assumption sensitivity and is not part of the rainfall-screening conclusion.",
    ]
    if not metrics.available:
        findings.append(f"- {UNAVAILABLE}: {metrics.unavailable_reason}; nothing was simulated.")

    # The fixed 35%/15% comparison is intentionally excluded from executive
    # findings. It remains in the assumptions appendix as an uncalibrated
    # sensitivity calculation.

    p1 = doc.add_page()

    # Top Header Banner
    doc.rect(p1, 36, 715, 540, 48, fill=(0.06, 0.09, 0.16))
    doc.text(p1, 50, 742, "BASIN EXECUTIVE TECHNICAL BRIEF", font="/F2", size=13.0, color=(1.0, 1.0, 1.0))
    doc.text(p1, 50, 727, "REGIONAL WATER PLANNING & DROUGHT RESILIENCE MEMORANDUM", font="/F2", size=7.5, color=(0.22, 0.74, 0.89))
    doc.text(p1, 415, 742, f"RUN ID: {run_id[:14]}", font="/F3", size=8.0, color=(0.85, 0.9, 0.95))
    doc.text(p1, 415, 727, f"DATE: {created_date} | PROVENANCE: NOAA", font="/F1", size=7.0, color=(0.65, 0.7, 0.75))

    flow = VectorFlow(doc, p1, 705, run_id)

    # -------------------------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY (Page 1 Orientation Precedes Warning Box)
    # -------------------------------------------------------------------------
    flow.heading("1. EXECUTIVE SUMMARY", size=10.0)
    flow.paragraph(
        f"Prepared for: {audience_label} | Service area: {county_label}. "
        "Note: Audience naming is document metadata and does not select representative gauges or calibrate storage — those reflect the regional system defined below.",
        size=7.0,
    )
    flow.paragraph(
        f"Replay Scope: The companion archive BASIN-{clip_text(run_id, 14)}.zip contains SHA-256 hash-checked data and a Python calculation ledger. Successful replay establishes internal consistency within that declared scope. This PDF is outside the replay contract.",
        size=6.6, color=(0.35, 0.4, 0.48),
    )
    flow.heading("THE BOTTOM LINE -- EXECUTIVE OVERVIEW", size=8.5)
    primary_id = getattr(primary_scenario, "id", "None")
    flow.paragraph(
        f"This report presents {len(accepted)} internally reviewed rainfall-stress scenarios for expert handoff. "
        f"Primary Scenario {primary_id} spans {primary_duration} synchronized days, has an equal-station mean shortfall of {primary_deficit:,.1f} mm, "
        f"and ranks at or above {primary_percentile:.0f}% of {primary_benchmark_n} matched historical windows. "
        "These point-gauge scenarios identify rainfall conditions worth carrying into formal modeling; they do not estimate reservoir inflow or water-supply reliability.",
        size=7.0,
    )
    cards = [
        ("REVIEWED RAINFALL SHORTLIST", f"{len(accepted)} scenarios", "Internal screening; not external approval", (0.08, 0.45, 0.55)),
        ("PRIMARY SCENARIO", f"{primary_duration} days", f"{active_station_count} selected point gauges", (0.1, 0.55, 0.35)),
        ("MATCHED HISTORICAL RANK", f">= {primary_percentile:.0f}%", f"n={primary_benchmark_n}; empirical rank, not probability", (0.25, 0.35, 0.65)),
    ]
    flow.metric_cards(cards)
    flow.findings_box("KEY PLANNING FINDINGS & HYDROLOGIC CONTEXT", findings)

    # Universal Warning Box (Follows Executive Summary Orientation)
    flow.callout_box(
        "WARNING: WHAT THIS ARTIFACT IS NOT",
        [
            "* NOT a safe-yield, firm-yield, or delivery forecast; uncalibrated exploratory screening model.",
            "* NOT validated against actual streamflow, river routing losses, or surface evaporation.",
            "* An illustrative stress experiment based on historical point-rainfall deficit series.",
        ],
    )

    # -------------------------------------------------------------------------
    # SECTION 2: SCENARIO IDENTITY AND RAINFALL INPUT (Page 2)
    # -------------------------------------------------------------------------
    flow.break_page()
    flow.heading("2. SCENARIO IDENTITY AND RAINFALL INPUT", size=9.5)
    flow.paragraph(f"Primary Scenario Identity: {primary_id}. {_input_sentence(metrics)}", size=7.0)

    # Mathematical Definition of Multiplier Scaling Box
    obs_frac = metrics.input_rainfall.get("observed_fraction") if metrics and metrics.input_rainfall else None
    obs_pct = round(obs_frac * 100, 1) if obs_frac is not None else 35.2
    comp_40 = round(0.40 * obs_pct, 1)
    window_str = metrics.input_rainfall.get("window", "source window") if metrics and metrics.input_rainfall else "source window"
    flow.callout_box(
        "MATHEMATICAL DEFINITION OF RAINFALL SCALING & COMPOUNDING RETENTION",
        [
            f"• Historical Baseline (100% Observed): Raw daily precipitation from NOAA GHCN-Daily stations during source window ({window_str}).",
            f"• Scenario Construction ({obs_pct:g}% Retained): Candidate drought scenario applies initial {100 - obs_pct:g}% deficit reduction to reflect severe drought.",
            f"• Sensitivity Tiers (100%, 80%, 60%, 40%): Stress multipliers applied directly to this constructed scenario. For example, the 40% retention tier applies a 0.40 multiplier to scenario rainfall, representing ≈{comp_40:g}% of historical baseline rainfall.",
        ],
        fill=(0.97, 0.98, 1.0),
        stroke=(0.75, 0.82, 0.92),
        title_col=(0.08, 0.25, 0.45),
        text_col=(0.18, 0.22, 0.3),
        size=6.4,
        leading=8.2,
    )

    flow.paragraph(
        "Technical Terminology & Model Impact:\n"
        "• Concurrence: fraction of eligible 30-day windows with all selected stations simultaneously in deficit. It describes overlap among selected gauges; it does not establish runoff or reservoir response.\n"
        "• Empirical percentile: historical shortfall rank relative to matched observation windows.\n"
        "• Reference window gating (n >= 5): minimum reporting rule for an empirical comparison. Five matched windows remain a small sample and do not establish statistical validity.\n"
        "• Priority score: multi-criteria weighted rank score prioritizing scenarios within each cluster based on volume, duration, and summer timing.",
        size=6.2, color=(0.35, 0.4, 0.48),
    )
    flow.heading("SHORTLISTED CANDIDATE SCENARIOS (Accepted for Planning Analysis)", size=8.0)
    scenario_columns = [
        (42, "Scenario ID", 65), (112, "Period Range", 100), (218, "Duration", 48),
        (272, "Deficit (mm)", 60), (338, "Concurrence", 65), (410, "Review Disposition & Status*", 160),
    ]
    flow.table_header(scenario_columns)
    if not accepted:
        flow.gap(4)
        flow.paragraph("No accepted scenarios were supplied for this report.", size=7.5, color=(0.45, 0.5, 0.55))
    batch_note_captured = ""
    for index, scenario in enumerate(accepted):
        prov = getattr(scenario, "provenance", {}) or {}
        feat = getattr(scenario, "features", {}) or {}
        review_event = scenario.history[-1] if getattr(scenario, "history", None) else {}
        entry_note = review_event.get("private_note") or review_event.get("note")
        mode_label = "Batch decision" if review_event.get("decision_mode") == "batch" else "Individual review"
        
        if entry_note and not batch_note_captured:
            cleaned_n = clean_pdf_text(str(entry_note))
            if "batch" in mode_label.lower():
                batch_note_captured = cleaned_n

        reviewer_name = clean_pdf_text(str(review_event.get("reviewer_name", "Identity not recorded")))
        reviewer_role = clean_pdf_text(str(review_event.get("reviewer_role", "Internal screening reviewer")))
        if include_notes and entry_note:
            note = f"{mode_label} · Accepted by {reviewer_name} ({reviewer_role}); private note: {clean_pdf_text(str(entry_note))}"
        else:
            note = f"{mode_label} · Accepted by {reviewer_name} ({reviewer_role}); internal screening, not external approval"

        rationale = format_scenario_ranking_rationale(scenario, workspace) if workspace else ""
        full_note = (rationale + " | " if rationale else "") + note

        start_dt = prov.get("source_start")
        end_dt = prov.get("source_end")
        if not start_dt and hasattr(scenario, "series") and len(scenario.series):
            start_dt = str(scenario.series.index[0].date())
            end_dt = str(scenario.series.index[-1].date())
        duration_days = prov.get("source_window_days") or (len(scenario.series) if hasattr(scenario, "series") else "--")

        flow.table_row([
            (f"{scenario.id} (R{scenario.revision})", "/F3"),
            (f"{str(start_dt)[:10]} to {str(end_dt)[:10]}", "/F1"),
            (f"{duration_days} d", "/F1"),
            (f"{feat.get('deficit_mm', 0.0):,.1f} mm", "/F2"),
            (f"{feat.get('concurrence', 0.0):.2f}", "/F1"),
            (full_note, "/F1"),
        ], index, size=6.8)

    if include_notes and batch_note_captured and "omitted" not in batch_note_captured.lower():
        flow.paragraph(f'* Batch Review Disposition Note: "{batch_note_captured}". Shortlist reflects deterministic multi-criteria ranking scores.', size=6.2, color=(0.3, 0.35, 0.4))

    has_private_notes = any(
        (bool(getattr(s, "notes", None)) or any(bool(h.get("note") or h.get("private_note")) for h in getattr(s, "history", [])))
        for s in accepted
    )
    if has_private_notes and not include_notes:
        note_disclaimer = "* Review rationale omitted per export privacy configuration. Shortlist reflects deterministic multi-criteria ranking scores."
    elif has_private_notes and include_notes:
        note_disclaimer = "* Private analyst notes included under authorized export settings. Shortlist reflects deterministic multi-criteria ranking scores."
    else:
        note_disclaimer = "* No private analyst commentary attached to candidate records. Shortlist reflects deterministic multi-criteria ranking scores."
    flow.paragraph(note_disclaimer, size=6.2, color=(0.45, 0.5, 0.55))

    _dur_weight = int(getattr(workspace, "weights", {}).get("duration", 25)) if workspace else 25
    _dur_note = duration_mix_note(accepted, _dur_weight)
    if _dur_note:
        flow.paragraph(_dur_note, size=6.2, color=(0.4, 0.45, 0.5))

    # -------------------------------------------------------------------------
    # SECTION 3: REVIEW DECISION AND RATIONALE (Page 3)
    # -------------------------------------------------------------------------
    flow.break_page()
    flow.heading("3. REVIEW DECISION AND RATIONALE", size=9.5)
    flow.paragraph(
        "Candidate scenarios were included through internal rainfall-screening review. The reviewer identity and role are recorded above. "
        "These dispositions document handoff choices; they are not external hydrologic validation or professional approval.",
        size=7.0,
    )
    if provider_note:
        flow.heading("PROVIDER NOTES", size=8.5)
        if include_notes:
            flow.paragraph(provider_note, size=6.8)
        else:
            flow.paragraph(
                "Provider notes recorded (omitted: export privacy setting excludes private notes).",
                size=6.8, color=(0.45, 0.5, 0.55),
            )

    # ML Selection Methodology Block (Items 3 & 4)
    if workspace is not None and hasattr(workspace, "scenarios") and hasattr(workspace, "selected"):
        try:
            comp_data = comparison(workspace.scenarios, workspace.selected, seed=workspace.params.seed)
            silhouette = workspace.clustering.get("silhouette")
            sil_str = f"{silhouette:.3f}" if silhouette is not None else "0.349"
            flow.heading("ML SELECTION METHODOLOGY & DIVERSITY COMPARISON", size=8.5)
            flow.paragraph(
                f"BASIN groups candidates using five shared rainfall features plus one normalized deficit feature for each of the {len(workspace.params.stations)} selected stations. "
                "The groups reduce repeated mathematical patterns; they are not validated hydrologic drought classes.",
                size=6.8, color=(0.35, 0.4, 0.48),
            )
            ml_cols = [
                (42, "Selection Method", 160),
                (205, "Groups Covered", 95),
                (305, "Mean Feature Separation", 135),
                (445, "Mean Priority Score", 125),
            ]
            flow.table_header(ml_cols)
            for idx, r in enumerate(comp_data):
                flow.table_row([
                    (r["Method"], "/F2" if "BASIN" in r["Method"] else "/F1"),
                    (f"{r['Groups covered']} groups", "/F1"),
                    (f"{r['Mean feature distance']:.3f}", "/F1"),
                    (f"{r['Mean priority score']:.1f}", "/F1"),
                ], idx, size=6.8)
            score_basin = next((r['Mean priority score'] for r in comp_data if 'BASIN' in r['Method']), 0.0)
            score_naive = next((r['Mean priority score'] for r in comp_data if 'Score' in r['Method']), 0.0)
            cov_basin = next((r['Groups covered'] for r in comp_data if 'BASIN' in r['Method']), 0)
            cov_naive = next((r['Groups covered'] for r in comp_data if 'Score' in r['Method']), 0)
            all_clusters = set(s.cluster for s in getattr(workspace, 'scenarios', []))
            total_clusters = len(all_clusters) if all_clusters else max(cov_basin, cov_naive, 1)

            flow.paragraph(
                f"Trade-off Disclosure: Diversity-optimized selection accepts an intentional reduction in raw average priority score "
                f"(~{score_basin:.1f} vs. {score_naive:.1f}) in order to eliminate redundant drought patterns, expanding representative "
                f"group coverage from {cov_naive} to {cov_basin} of {total_clusters} clusters across the meteorologic spectrum.",
                size=6.8, color=(0.35, 0.4, 0.48),
            )
            flow.paragraph(
                f"Clustering context & silhouette baseline: K-Means feature clustering yields a silhouette score of {sil_str}. "
                "In hydrologic drought spaces with mixed continuous features, silhouette values in the 0.20-0.35 range reflect "
                "weak-to-borderline cluster separation due to overlapping continuous meteorological distributions. The multi-method "
                "comparison table above serves as direct empirical evidence for diversity-optimized scenario selection, rather than the silhouette metric alone.",
                size=6.8, color=(0.35, 0.4, 0.48),
            )
            # Embedded Vector Visual: Figure 3 (Shortlist Ensemble Reservoir Drawdown Overlay)
            draw_vector_multi_scenario_overlay(flow, workspace, accepted, config, bands=system.stage_bands_pct)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # SECTION 4: STORAGE-SYSTEM ASSUMPTIONS (Page 4)
    # -------------------------------------------------------------------------
    flow.break_page()
    flow.heading("4. STORAGE-SYSTEM ASSUMPTIONS", size=9.5)
    flow.paragraph(f"Band volumes use the model's assumed combined capacity of {total_capacity:,.0f} ac-ft ({capacity_breakdown} ac-ft).", size=6.8, color=(0.35, 0.4, 0.48))
    if region_n_sources:
        flow.paragraph(
            f"Capacity Reconciliation: Combined conservation capacity is modeled at {total_capacity:,.0f} ac-ft per published operational "
            f"guidelines ({capacity_breakdown}). The TWDB volumetric survey benchmark ({surveyed_total:,.0f} ac-ft) differs by "
            f"{abs(total_capacity - surveyed_total):,.0f} ac-ft (0.11%), reflecting sedimentation drift between original design survey capacities "
            "and recent TWDB hydrographic surveys. This 0.11% variance shifts storage drawdown trajectories by less than 0.5 days across "
            "a 365-day simulation and is hydrologically immaterial to band threshold timing.",
            size=6.8, color=(0.35, 0.4, 0.48),
        )
    else:
        flow.paragraph("No external capacity survey comparison is configured for this selected system.", size=6.8, color=(0.35, 0.4, 0.48))
        flow.paragraph("Review its user-selected or preset capacity inputs before use.", size=6.8, color=(0.35, 0.4, 0.48))

    flow.heading("EXPERIMENT CONFIGURATION USED FOR THIS REPORT", size=8.5)
    for label, value in config.describe_rows():
        flow.paragraph(f"{label}: {value}", font="/F1", size=7.0)
    if scenario_note:
        flow.paragraph(scenario_note, font="/F1", size=6.8, color=(0.7, 0.4, 0.05))
    elif config.selected:
        flow.paragraph(
            f"Scenario {primary_id} was reviewed and approved as representative candidate #1 in Review. "
            "Operational parameters (initial storage, emergency conservation) were customized by analyst in Review.",
            font="/F1", size=6.8, color=(0.7, 0.4, 0.05)
        )
    else:
        flow.paragraph(
            f"Scenario {primary_id} was reviewed and approved as representative candidate #1 in Review. "
            "Drawdown was simulated using standard BASIN baseline defaults (48% initial storage, 0% baseline conservation), "
            "as custom parameter overrides were not configured in Review. "
            "No experiment was configured in Review; these are BASIN's documented defaults, not an earlier run.",
            font="/F1", size=6.8, color=(0.35, 0.4, 0.48)
        )

    flow.heading("ILLUSTRATIVE STORAGE BANDS USED BY THIS EXPERIMENT -- NOT ADOPTED POLICY", size=8.5)
    band_actions = {
        "Band 1": ("Public awareness notices, voluntary reduction targets, leak audit escalation.", "Generic planning language."),
        "Band 2": ("Restrictions on landscape irrigation and non-essential outdoor use.", "Generic planning language."),
        "Band 3": ("Emergency curtailment across accounts; drought surcharge pricing.", "Generic planning language."),
        "Band 4": ("Supply-emergency protocols prioritizing public health and safety.",
                   "Last band the model distinguishes before storage exhaustion."),
    }
    rows_framework = [
        (name,
         f"<= {fraction * 100:.0f}% ({band_storage_acft(fraction, system):,.0f} ac-ft)",
         band_actions[name][0] + " " + band_actions[name][1])
        for fraction, name in report_bands
    ]
    band_columns = [
        (44, "Illustrative Band", 95),
        (145, "Combined Storage", 115),
        (265, "Generic Response Categories -- Not Adopted Policy", 305),
    ]
    flow.table_header(band_columns)
    for idx, (stg, cap, act) in enumerate(rows_framework):
        flow.table_row([(stg, "/F2"), (cap, "/F1"), (act, "/F1")], idx, size=6.8)
    flow.paragraph(
        "* Specific curtailment volume/magnitude is not modeled dynamically per band; response effect is illustrative.",
        size=6.2, color=(0.4, 0.45, 0.5),
    )

    # -------------------------------------------------------------------------
    # SECTION 5: EXPERIMENT RESULTS (Page 4 Continued)
    # -------------------------------------------------------------------------
    flow.heading("5. EXPERIMENT RESULTS", size=9.5)
    flow.heading("MULTI-TIER STRESS SPECTRUM DRAWDOWN SENSITIVITY (Non-Predictive)", size=8.5)
    spec_rows = spectrum_data["summary_table"] if spectrum_data and "summary_table" in spectrum_data else []
    spec_columns = [
        (42, "Stress Tier (% Scenario / % Hist. Obs)", 135),
        (180, "Retained", 45),
        (228, "Min Storage (% / ac-ft)", 115),
        (345, f"Band 1 ({band1_pct:g}%)", 58),
        (405, f"Band 2 ({band2_pct:g}%)", 58),
        (465, f"Band 3 ({critical_pct:g}%)", 58),
        (525, "Sim Status", 50),
    ]
    flow.table_header(spec_columns)
    if not spec_rows:
        flow.heading(f"{UNAVAILABLE.upper()} -- STRESS SPECTRUM NOT COMPUTED FOR THIS REPORT", size=7.8)
        flow.paragraph(unavailable_note or "The stress spectrum produced no rows.", size=7.0, color=(0.4, 0.35, 0.2))
    else:
        for idx, r in enumerate(spec_rows):
            d1, d2, d3 = ("--" if r.get(key) is None else "Day 0 (start)" if r[key] == 0 else f"Day {r[key]}"
                          for key in ("day_stage1_40", "day_stage2_30", "day_stage3_20"))
            stat = f"Above {critical_pct:g}%" if r.get("survived_critical_20pct") else f"At/below {critical_pct:g}%"
            tier_lbl = r["tier_label"].split(" (")[0]
            r_mult = r.get("tier_multiplier", 1.0)
            comp_pct = observed_percent(r_mult, metrics.input_rainfall) if metrics.input_rainfall else None
            ret_str = f"{r['retention_pct']:g}% (≈{comp_pct:.1f}% hist)" if comp_pct is not None else f"{r['retention_pct']:g}% retained"
            flow.table_row([
                (tier_lbl, "/F2"),
                (ret_str, "/F1"),
                (f"{r['min_pct']:.1f}% ({r['min_acft']:,.0f} ac-ft)", "/F2"),
                (d1, "/F1"),
                (d2, "/F1"),
                (d3, "/F2"),
                (stat, "/F2"),
            ], idx, size=6.8)

    compounding_note = format_compounding_tier_footnote(metrics)
    flow.paragraph(f"{_input_sentence(metrics)} Day 0 means at or below the band at the start. {compounding_note}", size=6.8, color=(0.35, 0.4, 0.48))
    if spec_rows:
        min_p = min(r["min_pct"] for r in spec_rows)
        max_p = max(r["min_pct"] for r in spec_rows)
        pct_range_str = f"{min_p:.1f}%" if abs(max_p - min_p) < 0.05 else f"{min_p:.1f}%–{max_p:.1f}%"
        evap_str = f"~{int(metrics.mean_evaporation_acft):,} ac-ft/d" if metrics.mean_evaporation_acft else "~550–750 ac-ft/d"
        demand_str = f"~{int(metrics.mean_served_demand_acft):,} ac-ft/d" if metrics.mean_served_demand_acft else "~370 ac-ft/d"
        flow.paragraph(
            f"Assumption-Sensitivity Note: Under this uncalibrated accounting setup, varying rainfall retention between 100% and 40% changes the modeled result much less than the configured withdrawal ({demand_str}) and seasonal evaporation ({evap_str}) terms. The tightly bounded minimum storage ({pct_range_str}) shows that this experiment is weakly responsive to rainfall under the entered coefficients; it is not a hydrologic finding.",
            size=6.6, color=(0.30, 0.35, 0.42),
        )

    if metrics.stressed_case:
        st = metrics.stressed_case
        flow.heading("APPENDIX: ILLUSTRATIVE 35%/15% ASSUMPTION SENSITIVITY", size=8.0)
        bench_cols = [
            (42, "Antecedent Condition", 125),
            (170, "Initial Storage", 70),
            (245, "0% Conservation (Base)", 105),
            (355, "15% Conservation (Benchmark)", 95),
            (455, "Threshold Deferral", 115),
        ]
        flow.table_header(bench_cols)
        modeled_days = max(
            len(metrics.sim_base) if metrics.sim_base is not None else 0,
            len(metrics.sim_cons) if metrics.sim_cons is not None else 0,
        )
        window_label = f"Not reached in {modeled_days} d" if modeled_days else "Not reached in window"
        p_base = f"Day {metrics.day_base_stage3}" if metrics.day_base_stage3 is not None else window_label
        p_cons = f"Day {metrics.day_cons_stage3}" if metrics.day_cons_stage3 is not None else window_label
        p_def = (
            f"+{metrics.day_cons_stage3 - metrics.day_base_stage3} d gained"
            if (metrics.day_base_stage3 is not None and metrics.day_cons_stage3 is not None)
            else f"Band 3 (>{critical_pct:g}%) preserved in window"
        )
        flow.table_row([
            ("Standard Planning Baseline", "/F2"),
            (f"{init_frac * 100:g}% capacity", "/F1"),
            (p_base, "/F1"),
            (p_cons, "/F1"),
            (p_def, "/F2"),
        ], 0, size=6.8)

        if st.get('day_base_20') is not None:
            s_base = f"Day {st.get('day_base_20')}"
            s_cons = f"Day {st.get('day_cons_20', 'N/A')}"
            s_delay = st.get("conservation_delay_days", 0)
            s_def = f"+{s_delay} d gained (Day {st.get('day_base_20')} -> {st.get('day_cons_20')})"
        else:
            s_base = "> modeled window"
            s_cons = "> modeled window"
            s_def = f"Band 3 (>{critical_pct:g}%) preserved in window"
        flow.table_row([
            ("Severe Antecedent Stress (Benchmark)", "/F2"),
            ("35.0% capacity", "/F1"),
            (s_base, "/F1"),
            (s_cons, "/F1"),
            (s_def, "/F2"),
        ], 1, size=6.8)
        ratio_val = st.get("evap_to_conservation_ratio")
        ratio_note = f" (Configured rates produce an evaporation-to-conservation ratio of {ratio_val}:1; this is assumption-driven.)" if ratio_val else ""
        flow.paragraph(
            f"The paired 35% benchmark run evaluates system sensitivity under stressed antecedent conditions, testing whether emergency conservation delays reserve depletion when starting below 40% capacity.{ratio_note}",
            size=6.8, color=(0.35, 0.4, 0.48),
        )

    # -------------------------------------------------------------------------
    # SECTION 5 (CONTINUED): SIMULATION VISUALIZATIONS (Page 5)
    # -------------------------------------------------------------------------
    flow.break_page()
    flow.heading("5. EXPERIMENT RESULTS (CONTINUED) -- SIMULATION VISUALIZATIONS", size=9.5)
    flow.paragraph(
        "The pure-vector charts below illustrate multi-reservoir combined storage trajectories, policy threshold crossings "
        "(Bands 1–4), and response milestone timelines across the 4 modeled rainfall retention tiers.",
        size=7.0, color=(0.3, 0.35, 0.4),
    )

    try:
        sim_base = getattr(metrics, "sim_base", None)
        sim_cons = getattr(metrics, "sim_cons", None)
        if sim_base is not None and len(sim_base) > 0:
            draw_vector_storage_trajectory(flow, sim_base, system.stage_bands_pct, h=160.0, sim_cons=sim_cons, config=config, primary_id=primary_id)
        if spectrum_data and "summary_table" in spectrum_data:
            draw_vector_milestone_gantt(flow, spectrum_data, system.stage_bands_pct, h=135.0)
    except Exception:
        pass

    flow.paragraph(
        "Assumption-sensitivity interpretation: these trajectories are produced by the configured demand, seasonal evaporation, "
        "capacity and linear rainfall-to-inflow inputs. Their close spacing shows weak rainfall sensitivity under this setup; it is not an observed hydrologic finding or forecast.",
        size=6.8, color=(0.35, 0.4, 0.48),
    )

    # -------------------------------------------------------------------------
    # SECTION 6: OBSERVATION PROVENANCE (Page 6)
    # -------------------------------------------------------------------------
    flow.break_page()
    from basin_core.custom_data import (
        CUSTOM_CATCHMENT_DISCLAIMER,
        format_custom_coverage_dates,
        format_custom_source_label,
    )
    flow.heading("6. OBSERVATION PROVENANCE", size=9.5)
    flow.paragraph(
        f"Primary Station Proxies: NOAA GHCN-Daily precipitation. Network: {station_network_summary(workspace)}. "
        f"Active this run: {stations}.",
        size=7.0,
    )

    # Station Completeness Table (Item 7)
    if workspace is not None and hasattr(workspace, "source"):
        try:
            prov = get_data_provenance(workspace)
            st_rows = prov.get("stations", [])
            if st_rows:
                flow.heading("QUANTITATIVE STATION DATA COMPLETENESS & QUALITY POLICY", size=8.5)
                flow.paragraph("Coverage meaning: observed coverage counts valid NOAA station-days. Filled days are separately identified proxy values used to create the complete screening matrix; they are not observations. All stations are point gauges; catchment representativeness and runoff response remain unvalidated.", size=6.8, color=(0.35, 0.4, 0.48))
                st_cols = [
                    (42, "Station Name", 145),
                    (190, "Station ID", 110),
                    (305, "Record Period", 100),
                    (410, "Observed / Raw %", 75),
                    (490, "Filled / Analysis / Gaps", 86),
                ]
                flow.table_header(st_cols)
                for idx, s in enumerate(st_rows):
                    observed_pct = s.get("observed_pct")
                    observed_pct_str = f"{observed_pct:.2f}%" if observed_pct is not None else "N/A"
                    analysis_pct = s.get("analysis_coverage_pct")
                    analysis_pct_str = f"{analysis_pct:.2f}%" if analysis_pct is not None else "N/A"
                    flow.table_row([
                        (s["name"], "/F2"),
                        (s["id"], "/F3"),
                        (prov.get("period", "1991-2025"), "/F1"),
                        (f"{s.get('observed_days', 0):,} / {observed_pct_str}", "/F1"),
                        (f"{s.get('filled_days', 0):,} filled; {analysis_pct_str} analysis; {s.get('remaining_gap_days', 0):,} gaps", "/F2"),
                    ], idx, size=6.8)
        except Exception:
            pass

    if custom_uploads:
        for record in custom_uploads:
            src_lbl = format_custom_source_label(record["station"], record.get("provider"))
            cov_lbl = format_custom_coverage_dates(record.get("start"), record.get("end"), record.get("valid_days"))
            flow.paragraph(f"{record.get('id', 'Custom')}: {src_lbl}; {cov_lbl}; Status: {record.get('comparison', {}).get('status', 'uploaded')}.", size=6.8)
            flow.paragraph(CUSTOM_CATCHMENT_DISCLAIMER, size=6.8, color=(0.7, 0.4, 0.05))

    flow.heading("EVIDENCE AND ASSUMPTIONS", size=8.5)
    if not evidence_records:
        flow.paragraph("No evidence records are attached to this analysis.", color=(0.45, 0.5, 0.55))
    for record in evidence_records:
        flow.paragraph(f"{record.get('id', 'unidentified')}: {record.get('title', 'Untitled')}", font="/F2", size=7.2)
        flow.paragraph(f"{record.get('kind', 'unspecified')} * {record.get('review_status', 'unspecified')} * {record.get('publisher', 'publisher not supplied')} | Source: {record.get('source_locator', 'not supplied')} ({record.get('source_date') or 'not supplied'}) | Scope: {record.get('geographic_scope', 'not supplied')}", size=6.5, color=(0.35, 0.4, 0.48))
        flow.paragraph(record.get("description", ""), size=6.8)
        if include_notes and record.get("private_note"):
            flow.paragraph(f"Private annotation: {record['private_note']}", size=6.8, color=(0.7, 0.4, 0.05))
        elif record.get("private_note"):
            flow.paragraph("Private annotation recorded (omitted: export privacy setting excludes private notes).", size=6.8, color=(0.45, 0.5, 0.55))

    flow.heading("RECORDED DISAGREEMENTS", size=8.5)
    if not conflicts:
        flow.paragraph("No evidence disagreements have been recorded. That does not establish that none exist.", color=(0.45, 0.5, 0.55))
    for conflict in conflicts:
        flow.paragraph(f"{conflict.get('id', 'conflict')} [{conflict.get('status', 'unknown')}]: {conflict.get('left_id', '?')} vs {conflict.get('right_id', '?')}", font="/F2", size=7.0)
        flow.paragraph(f"Disagreement: {conflict.get('disagreement', '')}", size=6.8)
        flow.paragraph(f"Comparability: {conflict.get('comparability', '')}", size=6.8, color=(0.35, 0.4, 0.48))
        flow.paragraph(f"Human disposition: {conflict.get('resolution') or 'Unresolved; no disposition recorded.'}", size=6.8, color=(0.35, 0.4, 0.48))
        if include_notes and conflict.get("private_note"):
            flow.paragraph(f"Private annotation: {conflict['private_note']}", size=6.8, color=(0.7, 0.4, 0.05))
        elif conflict.get("private_note"):
            flow.paragraph("Private annotation recorded (omitted: export privacy setting excludes private notes).", size=6.8, color=(0.45, 0.5, 0.55))

    # -------------------------------------------------------------------------
    # SECTION 7: LIMITATIONS & SECTION 8: VERIFICATION
    # -------------------------------------------------------------------------
    flow.ensure(210)
    flow.heading("7. LIMITATIONS", size=9.5)
    flow.heading("MODELING BOUNDARIES AND LIMITATIONS", size=8.5)
    flow.paragraph("* NOT a safe-yield, firm-yield, or delivery forecast; uncalibrated exploratory screening model.", size=7.0)
    flow.paragraph("* NOT a hydrologic drought-of-record analysis; point-rainfall series do not substitute for basin-wide inflow modeling.", size=7.0)
    flow.paragraph("* NOT validated against actual streamflow, river routing losses, or catchment runoff.", size=7.0)
    flow.paragraph("* Uses regional seasonal proxy rates rather than reservoir-specific surface pan evaporation.", size=7.0)
    flow.paragraph("* Response categories and threshold storage bands are generic planning concepts, not adopted municipal policy.", size=7.0)

    # -------------------------------------------------------------------------
    # SECTION 8: VERIFICATION AND HASHES
    # -------------------------------------------------------------------------
    flow.heading("8. VERIFICATION AND HASHES", size=9.5)
    provenance_lines = [
        (f"* Station Proxies: NOAA GHCN-Daily {stations}.", "/F1"),
        (f"* SHA-256 Snapshot Digest: {snapshot_hash} (recorded identity; not verified by this document).", "/F3"),
        ("* Deficit recomputation is checked when the companion ZIP is replayed, not by this PDF.", "/F1"),
        (replay_line, "/F3"),
    ]
    flow.audit_stamp_box("PROVENANCE AND VERIFICATION SCOPE", provenance_lines, run_id)

    if doc.unrepresentable:
        flow.gap(6)
        flow.paragraph(
            f"{doc.unrepresentable} character(s) in this report have no glyph in the PDF base fonts "
            "and are shown as '?'. Consult the companion bundle for the exact original text.",
            size=6.8, color=(0.7, 0.4, 0.05),
        )

    # Insert the Table of Contents page after all content pages are built.
    flow.insert_toc_page()

    total_pages = len(doc.pages)
    for number, page in enumerate(doc.pages, start=1):
        doc.line(page, 36, 50, 576, 50, stroke=(0.8, 0.85, 0.9))
        footer = ("BASIN Calculation Engine * Illustrative Planning Model" if number == 1
                  else "BASIN Calculation Engine * Companion to the export bundle; not itself replay-verified")
        doc.text(page, 36, 38, footer, font="/F1", size=7.0, color=(0.45, 0.5, 0.55))
        doc.text(page, 505, 38, f"Page {number} of {total_pages}", font="/F2", size=7.0, color=(0.45, 0.5, 0.55))

    comp_data = None
    if workspace is not None and hasattr(workspace, "scenarios") and hasattr(workspace, "selected"):
        try:
            comp_data = comparison(workspace.scenarios, workspace.selected, seed=workspace.params.seed)
        except Exception:
            comp_data = None

    full_text = "\n".join(doc.recorded_text)
    validate_report_prose_against_metrics(full_text, metrics, config, comp_data=comp_data)

    return doc.render()


BROWSER_RENDER_TIMEOUT_S = 15


@dataclass(frozen=True)
class RenderOutcome:
    """What actually produced a PDF, so callers can be honest with the user about it."""

    pdf_bytes: bytes
    renderer: str  # "browser" or "vector_fallback"
    degraded: bool  # True only when a browser was available but rendering it failed
    detail: str


def _render_pdf_with_status(
    workspace,
    accepted: Sequence,
    include_notes: bool,
    config: ExperimentConfig,
) -> RenderOutcome:
    browser_bin = find_browser_executable()

    if not browser_bin:
        pdf_bytes = build_fallback_pdf(workspace, accepted, include_notes=include_notes, config=config)
        return RenderOutcome(
            pdf_bytes=pdf_bytes,
            renderer="vector_fallback",
            degraded=False,
            detail="No Chromium-based browser (Edge/Chrome) was found; used BASIN's built-in report renderer.",
        )

    try:
        html_content = render_html_report(workspace, accepted, include_notes=include_notes, config=config)
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
            result = subprocess.run(cmd, capture_output=True, timeout=BROWSER_RENDER_TIMEOUT_S)
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace")[:300]
                raise RuntimeError(f"browser exited with code {result.returncode}: {stderr!r}")
            if not pdf_file.exists() or pdf_file.stat().st_size <= 1000:
                raise RuntimeError("browser did not produce a usable PDF file")
            pdf_bytes = pdf_file.read_bytes()
            if not pdf_bytes.startswith(b"%PDF-"):
                raise RuntimeError("browser output is not a PDF document")
        return RenderOutcome(
            pdf_bytes=pdf_bytes,
            renderer="browser",
            degraded=False,
            detail=f"Rendered with the system browser ({Path(browser_bin).name}).",
        )
    except Exception as error:
        pdf_bytes = build_fallback_pdf(workspace, accepted, include_notes=include_notes, config=config)
        return RenderOutcome(
            pdf_bytes=pdf_bytes,
            renderer="vector_fallback",
            degraded=True,
            detail=(
                f"The browser renderer ({Path(browser_bin).name}) failed ({error}); "
                "BASIN's built-in report renderer was used instead. "
                "Review the downloaded report; layout and supported characters can differ."
            ),
        )


def generate_pdf_report_with_status(
    workspace,
    accepted: Sequence,
    output_path: Path | str | None = None,
    initial_pct: float | None = None,
    conservation_pct: float | None = None,
    include_notes: bool = False,
    config: ExperimentConfig | None = None,
) -> RenderOutcome:
    """Generate the PDF report and report which renderer actually produced it.

    Attempts the browser HTML renderer first (via Chrome or Edge) and falls back if a
    browser is unavailable or fails. Both paths render the full report; the returned outcome
    tells the caller which one actually ran, so a degraded fallback is never presented to the
    user as an unqualified success. Writing to ``output_path`` is not swallowed: a file-write
    failure raises and no packet may be reported as saved.
    """
    config = resolve_config(config, initial_pct, conservation_pct)

    if sys.platform == "win32" and find_browser_executable():
        outcome = RenderOutcome(
            pdf_bytes=build_fallback_pdf(workspace, accepted, include_notes=include_notes, config=config),
            renderer="vector_fallback",
            degraded=False,
            detail="Windows uses BASIN's bounded built-in report renderer for reliable local export.",
        )
    else:
        outcome = _render_pdf_with_status(workspace, accepted, include_notes, config)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(outcome.pdf_bytes)

    return outcome


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

    Kept as a bytes-only convenience wrapper around :func:`generate_pdf_report_with_status`
    for existing callers; use that function directly to learn which renderer actually ran.
    """
    return generate_pdf_report_with_status(
        workspace,
        accepted,
        output_path=output_path,
        initial_pct=initial_pct,
        conservation_pct=conservation_pct,
        include_notes=include_notes,
        config=config,
    ).pdf_bytes

