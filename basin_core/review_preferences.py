"""Display preferences and presentation modes for the Review page.

These choices decide which Review tools appear first. They are a presentation record
only: nothing here feeds a calculation, a ranking weight, a simulation input, a review
decision, custom-data inclusion or private-note consent. ``ExperimentConfig`` remains the
numerical record and is deliberately kept separate from this one.

Preferences are stored beside a saved run rather than inside its audited record, so
showing or hiding a panel can never change an exported bundle's digests. A run saved
before this feature existed simply has no preferences file and falls back to defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Literal

from basin_core.workspace import session_dir

PREFERENCES_VERSION = 1

GOALS: dict[str, dict[str, str]] = {
    "compare": {
        "label": "Compare rainfall scenarios",
        "help": "Put the rainfall record and its historical comparison first.",
    },
    "storage": {
        "label": "Explore an illustrative storage scenario",
        "help": "Put the optional, uncalibrated storage experiment and its assumptions first.",
    },
    "operations": {
        "label": "Assess agricultural & wildfire risk",
        "help": "Put crop irrigation deficits, wildfire stress (KBDI) and evidence first.",
    },
    "handoff": {
        "label": "Prepare a reviewed handoff",
        "help": "Put review decisions, edits and export readiness first.",
    },
}

DATA_SOURCES: dict[str, dict[str, str]] = {
    "regional": {
        "label": "Bundled regional observations",
        "help": "The included NOAA station snapshot.",
    },
    "own": {
        "label": "My rainfall data",
        "help": "You will add a CSV in Step 1. Choosing this uploads and validates nothing on its own.",
    },
    "example": {
        "label": "Not sure — start with an example",
        "help": "Open a prepared example run to look around first.",
    },
}

# Presentation modes. Backward-compatible serialized values ("guided" and "technical")
# map directly to Simple View and Advanced View.
PRESENTATION_MODES: dict[str, dict[str, str]] = {
    "simple": {
        "label": "Simple View",
        "serialized_guidance": "guided",
        "help": "Focused layout for quick scenario decisions. Limitations and disclosures remain visible.",
    },
    "advanced": {
        "label": "Advanced View",
        "serialized_guidance": "technical",
        "help": "Complete access to all technical tools, detailed hydrographs, and agronomic diagnostics.",
    },
}

# Preserved for backward compatibility with serialized session records and existing callers.
GUIDANCE: dict[str, dict[str, str]] = {
    "guided": {
        "label": "Simple View",
        "help": "Focused layout for quick scenario decisions. Limitations and disclosures remain visible.",
    },
    "technical": {
        "label": "Advanced View",
        "help": "Complete access to all technical tools, detailed hydrographs, and agronomic diagnostics.",
    },
}

# Canonical Review tab order, used whenever no focus applies.
TAB_KEYS: tuple[str, ...] = ("storage", "agronomics", "rainfall", "edits", "provenance")

TAB_LABELS: dict[str, str] = {
    "storage": "🌊 Storage Drawdown & Water System",
    "agronomics": "🌾 Agronomics & Wildfire Risk",
    "rainfall": "🌧️ Rainfall Deficit & Historical Context",
    "edits": "✏️ Edit Rainfall & Refine Shortlist",
    "provenance": "📋 Evidence & Daily Values",
}

# Which tools lead for each goal. "provenance" leads in every focus on purpose: source
# identity, evidence and stated limitations must not be demoted by a display choice.
FOCUS_PRIMARY: dict[str, tuple[str, ...]] = {
    "compare": ("rainfall", "provenance"),
    "storage": ("storage", "provenance"),
    "operations": ("agronomics", "provenance"),
    "handoff": ("edits", "provenance"),
}

# Shown as text next to the summary. Never applied automatically: changing a display
# focus must not rerank scenarios or move a shortlist.
SUGGESTED_WEIGHT_PRESET: dict[str, str] = {
    "compare": "Illustrative regional planner",
    "storage": "Illustrative emergency planner",
    "operations": "Illustrative rural provider",
    "handoff": "Illustrative rural provider",
}

GUIDED_TAB_NOTES: dict[str, str] = {
    "storage": "Optional experiment. Storage results are illustrative and are excluded from the verified packet.",
    "agronomics": "Cross-sector operational impacts: crop irrigation deficit (ETc) and soil-dryness wildfire stress (KBDI).",
    "rainfall": "The rainfall record for this scenario and how it compares with matched historical windows.",
    "edits": "Change rainfall content or swap a shortlist entry. Edits clear an existing acceptance.",
    "provenance": "Where the numbers come from: cited evidence, daily values and revision history.",
}


# -- Typed Mappings for Review Panes and Technical Details -----------------------------

PanePlacement = Literal["primary", "secondary", "expander", "hidden"]
DetailPlacement = Literal["primary", "expander", "advanced_only", "tooltip"]


@dataclass(frozen=True)
class PanePresentation:
    """Defines presentation layout and placement for a top-level Review pane."""

    key: str
    label: str
    simple_placement: PanePlacement
    advanced_placement: PanePlacement
    description: str
    is_mandatory_disclosure: bool = False


@dataclass(frozen=True)
class TechnicalDetail:
    """Defines presentation placement for specific technical tools and data views."""

    key: str
    pane_key: str
    title: str
    simple_placement: DetailPlacement
    advanced_placement: DetailPlacement
    reason: str
    is_mandatory_disclosure: bool = False


PANE_PRESENTATIONS: dict[str, PanePresentation] = {
    "rainfall": PanePresentation(
        key="rainfall",
        label=TAB_LABELS["rainfall"],
        simple_placement="primary",
        advanced_placement="primary",
        description="Rainfall deficit comparison against historical reference benchmarks.",
        is_mandatory_disclosure=False,
    ),
    "provenance": PanePresentation(
        key="provenance",
        label=TAB_LABELS["provenance"],
        simple_placement="primary",
        advanced_placement="primary",
        description="Source evidence, observation lineage, daily values, and mandatory catchment disclaimers.",
        is_mandatory_disclosure=True,
    ),
    "storage": PanePresentation(
        key="storage",
        label=TAB_LABELS["storage"],
        simple_placement="secondary",
        advanced_placement="primary",
        description="Optional, illustrative reservoir drawdown simulation under assumed conditions.",
        is_mandatory_disclosure=False,
    ),
    "agronomics": PanePresentation(
        key="agronomics",
        label=TAB_LABELS["agronomics"],
        simple_placement="secondary",
        advanced_placement="primary",
        description="Crop water deficit (ETc) and Keetch-Byram Drought Index (KBDI) operational estimates.",
        is_mandatory_disclosure=False,
    ),
    "edits": PanePresentation(
        key="edits",
        label=TAB_LABELS["edits"],
        simple_placement="secondary",
        advanced_placement="primary",
        description="Rainfall scaling, CSV replacement, and scenario candidate swapping.",
        is_mandatory_disclosure=False,
    ),
}

TECHNICAL_DETAILS: dict[str, TechnicalDetail] = {
    # Rainfall pane details
    "rainfall_comparison_chart": TechnicalDetail(
        key="rainfall_comparison_chart",
        pane_key="rainfall",
        title="Rainfall Reference Chart",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Core visual comparison of scenario rainfall vs historical reference.",
    ),
    "rainfall_totals_summary": TechnicalDetail(
        key="rainfall_totals_summary",
        pane_key="rainfall",
        title="Scenario vs Reference Totals",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Immediate numerical difference for review decision.",
    ),
    "rainfall_historical_concurrence": TechnicalDetail(
        key="rainfall_historical_concurrence",
        pane_key="rainfall",
        title="Historical Stress Concurrence",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Statistical persistence frequency across multi-station windows.",
    ),
    "rainfall_historical_benchmark": TechnicalDetail(
        key="rainfall_historical_benchmark",
        pane_key="rainfall",
        title="1991–2020 Historical Benchmark",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Largest shortfall benchmark from standard 30-year climate baseline.",
    ),
    "rainfall_extended_2025_benchmark": TechnicalDetail(
        key="rainfall_extended_2025_benchmark",
        pane_key="rainfall",
        title="1991–2025 Extended Benchmark",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Extended 35-year reference window including 2022 drought.",
    ),
    "rainfall_ranking_score": TechnicalDetail(
        key="rainfall_ranking_score",
        pane_key="rainfall",
        title="Candidate Ranking Score Breakdown",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Multivariate scoring formula breakdown according to user weights.",
    ),
    # Storage pane details
    "storage_pool_snapshot": TechnicalDetail(
        key="storage_pool_snapshot",
        pane_key="storage",
        title="Reservoir Storage Snapshot",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Visual breakdown of reservoir levels and capacities.",
    ),
    "storage_drawdown_trajectory": TechnicalDetail(
        key="storage_drawdown_trajectory",
        pane_key="storage",
        title="Combined Pool Drawdown Trajectory",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Simulated time-series of reservoir drawdown across the scenario.",
    ),
    "storage_custom_system_builder": TechnicalDetail(
        key="storage_custom_system_builder",
        pane_key="storage",
        title="Custom Water System Setup",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Detailed multi-source capacity, dead pool, and demand editing.",
    ),
    "storage_stress_spectrum": TechnicalDetail(
        key="storage_stress_spectrum",
        pane_key="storage",
        title="Stress Spectrum Sensitivity Analysis",
        simple_placement="advanced_only",
        advanced_placement="primary",
        reason="Exploratory multi-duration stress testing across duration ranges.",
    ),
    "storage_daily_sim_table": TechnicalDetail(
        key="storage_daily_sim_table",
        pane_key="storage",
        title="Daily Simulation Balance Table",
        simple_placement="advanced_only",
        advanced_placement="primary",
        reason="Day-by-day inflow, evaporation, release, and spill ledger.",
    ),
    # Agronomics pane details
    "agronomics_crop_takeaway": TechnicalDetail(
        key="agronomics_crop_takeaway",
        pane_key="agronomics",
        title="Crop Irrigation Deficit Takeaway",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Executive operational summary of crop irrigation gaps.",
    ),
    "agronomics_monthly_table": TechnicalDetail(
        key="agronomics_monthly_table",
        pane_key="agronomics",
        title="Monthly Crop ET & Rainfall Breakdown",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Month-by-month agricultural water balance dataframe.",
    ),
    "agronomics_kbdi_burn_ban": TechnicalDetail(
        key="agronomics_kbdi_burn_ban",
        pane_key="agronomics",
        title="KBDI Wildfire Danger & Burn Ban Trigger",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Peak KBDI score and illustrative burn ban threshold breach status.",
    ),
    "agronomics_kbdi_tuning_slider": TechnicalDetail(
        key="agronomics_kbdi_tuning_slider",
        pane_key="agronomics",
        title="Initial KBDI Soil Dryness Slider",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Adjusting assumed starting soil moisture deficit.",
    ),
    # Edits pane details
    "edits_scale_multiplier": TechnicalDetail(
        key="edits_scale_multiplier",
        pane_key="edits",
        title="Uniform Rainfall Multiplier",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Proportional scaling of all daily rainfall values.",
    ),
    "edits_csv_replacement": TechnicalDetail(
        key="edits_csv_replacement",
        pane_key="edits",
        title="CSV Replacement Upload",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Uploading alternative daily time-series from custom CSV.",
    ),
    "edits_candidate_swap": TechnicalDetail(
        key="edits_candidate_swap",
        pane_key="edits",
        title="Candidate Shortlist Swap",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Replacing shortlisted candidate with unselected candidate.",
    ),
    # Provenance pane details
    "provenance_mandatory_disclosures": TechnicalDetail(
        key="provenance_mandatory_disclosures",
        pane_key="provenance",
        title="Mandatory Limitations & Catchment Disclaimers",
        simple_placement="primary",
        advanced_placement="primary",
        reason="Statutory and methodological boundaries; mandatory in both modes.",
        is_mandatory_disclosure=True,
    ),
    "provenance_source_metadata": TechnicalDetail(
        key="provenance_source_metadata",
        pane_key="provenance",
        title="Observation Source & Lineage",
        simple_placement="primary",
        advanced_placement="primary",
        reason="NOAA/custom source attribution, coverage dates, and retention percentages.",
    ),
    "provenance_daily_value_editor": TechnicalDetail(
        key="provenance_daily_value_editor",
        pane_key="provenance",
        title="Cell-Level Daily Value Editor",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Direct cell editing of individual day rainfall amounts.",
    ),
    "provenance_raw_audit_json": TechnicalDetail(
        key="provenance_raw_audit_json",
        pane_key="provenance",
        title="Raw Audit & Cryptographic Digests",
        simple_placement="advanced_only",
        advanced_placement="primary",
        reason="SHA-256 digests, raw feature vectors, and component scores.",
    ),
    "provenance_revision_history": TechnicalDetail(
        key="provenance_revision_history",
        pane_key="provenance",
        title="Scenario Revision Event Trail",
        simple_placement="expander",
        advanced_placement="primary",
        reason="Chronological log of edits, rationales, and review timestamps.",
    ),
}


def _coerce(value, options: dict, fallback: str) -> str:
    return value if isinstance(value, str) and value in options else fallback


@dataclass(frozen=True)
class ReviewPreferences:
    """A versioned, validated record of Review display choices and presentation mode."""

    goal: str = "compare"
    data_source: str = "regional"
    guidance: str = "guided"
    configured: bool = False
    dismissed: bool = False
    show_all_tools: bool = False
    version: int = PREFERENCES_VERSION

    def __init__(
        self,
        goal: str = "compare",
        data_source: str = "regional",
        guidance: str = "guided",
        configured: bool = False,
        dismissed: bool = False,
        show_all_tools: bool = False,
        version: int = PREFERENCES_VERSION,
        *,
        mode: str | None = None,
    ) -> None:
        if mode is not None:
            if mode in ("simple", "guided"):
                guidance = "guided"
            elif mode in ("advanced", "technical"):
                guidance = "technical"
            else:
                raise ValueError(f"Unknown presentation mode: {mode!r}")

        if guidance in ("simple", "guided"):
            resolved_guidance = "guided"
        elif guidance in ("advanced", "technical"):
            resolved_guidance = "technical"
        else:
            resolved_guidance = guidance

        if goal not in GOALS:
            raise ValueError(f"Unknown Review goal: {goal!r}")
        if data_source not in DATA_SOURCES:
            raise ValueError(f"Unknown data source: {data_source!r}")
        if resolved_guidance not in GUIDANCE:
            raise ValueError(f"Unknown guidance level: {guidance!r}")
        for name, val in [("configured", configured), ("dismissed", dismissed), ("show_all_tools", show_all_tools)]:
            if type(val) is not bool:
                raise ValueError(f"{name} must be true or false")
        if type(version) is not int or version < 1:
            raise ValueError("version must be a positive integer")

        object.__setattr__(self, "goal", goal)
        object.__setattr__(self, "data_source", data_source)
        object.__setattr__(self, "guidance", resolved_guidance)
        object.__setattr__(self, "configured", configured)
        object.__setattr__(self, "dismissed", dismissed)
        object.__setattr__(self, "show_all_tools", show_all_tools)
        object.__setattr__(self, "version", version)

    # -- presentation ---------------------------------------------------------------
    @property
    def simple(self) -> bool:
        """True when in Simple View."""
        return self.guidance in ("guided", "simple")

    @property
    def advanced(self) -> bool:
        """True when in Advanced View."""
        return self.guidance in ("technical", "advanced")

    @property
    def mode(self) -> str:
        """Presentation mode string ('simple' or 'advanced')."""
        return "simple" if self.simple else "advanced"

    @property
    def presentation_label(self) -> str:
        """User-facing label for the active presentation mode."""
        return PRESENTATION_MODES[self.mode]["label"]

    @property
    def guided(self) -> bool:
        """Backward compatibility alias for simple."""
        return self.simple

    @property
    def technical(self) -> bool:
        """Backward compatibility alias for advanced."""
        return self.advanced

    @property
    def needs_setup(self) -> bool:
        """True until the reader either answers the questions or skips them."""
        return not self.configured and not self.dismissed

    def pane_placement(self, pane_key: str) -> PanePlacement:
        """Determine placement of a Review pane in the current mode."""
        if pane_key not in PANE_PRESENTATIONS:
            raise KeyError(f"Unknown Review pane: {pane_key!r}")
        if self.advanced:
            return PANE_PRESENTATIONS[pane_key].advanced_placement
        if self.show_all_tools:
            return "primary"
        if self.configured:
            return "primary" if pane_key in FOCUS_PRIMARY.get(self.goal, ()) else "secondary"
        return PANE_PRESENTATIONS[pane_key].simple_placement

    def detail_placement(self, detail_key: str) -> DetailPlacement:
        """Determine placement of a technical detail in the current mode."""
        if detail_key not in TECHNICAL_DETAILS:
            raise KeyError(f"Unknown technical detail: {detail_key!r}")
        return (
            TECHNICAL_DETAILS[detail_key].simple_placement
            if self.simple
            else TECHNICAL_DETAILS[detail_key].advanced_placement
        )

    def is_detail_visible(self, detail_key: str) -> bool:
        """Whether a technical detail is visible in the current mode."""
        placement = self.detail_placement(detail_key)
        if placement == "hidden":
            return False
        if self.simple and placement == "advanced_only":
            return False
        return True

    def primary_panes(self) -> tuple[str, ...]:
        """Bounded set of primary Review panes for the active mode.

        In Simple View, this is bounded to at most 2 tabs to keep cognitive load low
        for first-time reviewers. In Advanced View, every Review tool is primary, with
        the reader's selected focus leading.
        """
        if self.show_all_tools:
            return TAB_KEYS
        if self.configured:
            primary = tuple(k for k in TAB_KEYS if k in FOCUS_PRIMARY.get(self.goal, ()))
            if self.advanced:
                secondary = tuple(k for k in TAB_KEYS if k not in primary)
                return primary + secondary
            return primary
        if self.advanced:
            return TAB_KEYS
        return ("rainfall", "provenance")

    def secondary_panes(self) -> tuple[str, ...]:
        """Panes relegated to secondary navigation or the expander."""
        if self.advanced or self.show_all_tools:
            return ()
        primary = set(self.primary_panes())
        return tuple(k for k in TAB_KEYS if k not in primary)

    def summary(self) -> str:
        if not self.configured:
            return "Showing all Review tools (setup skipped)."
        return " · ".join([
            GOALS[self.goal]["label"],
            DATA_SOURCES[self.data_source]["label"],
            PRESENTATION_MODES[self.mode]["label"],
        ])

    def describe_rows(self) -> list[tuple[str, str]]:
        return [
            ("Goal", GOALS[self.goal]["label"]),
            ("Data", DATA_SOURCES[self.data_source]["label"]),
            ("View", PRESENTATION_MODES[self.mode]["label"]),
        ]

    def tab_layout(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Return ``(leading, under_more_tools)`` tab keys.

        Every tab always appears in exactly one of the two groups: a focus reorders the
        Review page, it never removes a tool.
        """
        if self.show_all_tools or not self.configured:
            return TAB_KEYS, ()
        primary = tuple(key for key in TAB_KEYS if key in FOCUS_PRIMARY[self.goal])
        secondary = tuple(key for key in TAB_KEYS if key not in primary)
        return primary, secondary

    def suggested_preset(self) -> str | None:
        """A ranking preset this focus pairs with. Advisory only; never auto-applied."""
        return SUGGESTED_WEIGHT_PRESET.get(self.goal) if self.configured else None

    # -- persistence ----------------------------------------------------------------
    def to_record(self) -> dict:
        return {
            "version": self.version,
            "goal": self.goal,
            "data_source": self.data_source,
            "guidance": self.guidance,
            "mode": self.mode,
            "configured": self.configured,
            "dismissed": self.dismissed,
            "show_all_tools": self.show_all_tools,
        }

    @classmethod
    def from_record(cls, record) -> "ReviewPreferences":
        """Build from a stored record, tolerating older, partial or damaged files.

        Unknown, foreign, or malformed values fall back to defaults rather than raising,
        so a run saved by an older version of BASIN still opens cleanly, and unknown
        mode values safely fall back to Simple View.
        """
        if not isinstance(record, dict):
            return cls()
        if type(record.get("version", PREFERENCES_VERSION)) is not int or record.get("version", PREFERENCES_VERSION) != PREFERENCES_VERSION:
            return cls()
        for name in ("configured", "dismissed", "show_all_tools"):
            if name in record and type(record[name]) is not bool:
                return cls()

        # Determine guidance / mode with safe fallback to Simple View ("guided")
        mode_val = record.get("mode")
        guidance_val = record.get("guidance")

        if mode_val in ("advanced", "technical") or (mode_val is None and guidance_val in ("advanced", "technical")):
            resolved_guidance = "technical"
        else:
            # Default or fallback for ("simple", "guided", missing, unknown, malformed)
            resolved_guidance = "guided"

        return cls(
            goal=_coerce(record.get("goal"), GOALS, "compare"),
            data_source=_coerce(record.get("data_source"), DATA_SOURCES, "regional"),
            guidance=resolved_guidance,
            configured=record.get("configured") is True,
            dismissed=record.get("dismissed") is True,
            show_all_tools=record.get("show_all_tools") is True,
            version=PREFERENCES_VERSION,
        )

    def replace(self, **changes) -> "ReviewPreferences":
        if "mode" in changes:
            m = changes.pop("mode")
            if m in ("simple", "guided"):
                changes["guidance"] = "guided"
            elif m in ("advanced", "technical"):
                changes["guidance"] = "technical"
            else:
                raise ValueError(f"Unknown presentation mode: {m!r}")
        if changes.get("guidance") in ("simple", "guided"):
            changes["guidance"] = "guided"
        elif changes.get("guidance") in ("advanced", "technical"):
            changes["guidance"] = "technical"
        return replace(self, **changes)


def preferences_path(workspace_id: str, directory: Path | None = None) -> Path:
    """Sidecar file for one run. Kept out of the audited record on purpose."""
    base = Path(directory) if directory is not None else session_dir()
    return base / f"review-prefs-{workspace_id}.json"


def load_preferences(workspace_id: str, directory: Path | None = None) -> ReviewPreferences:
    """Read stored preferences, falling back to defaults for any unreadable file."""
    path = preferences_path(workspace_id, directory)
    try:
        return ReviewPreferences.from_record(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return ReviewPreferences()


def save_preferences(workspace_id: str, preferences: ReviewPreferences,
                     directory: Path | None = None) -> Path | None:
    """Write preferences beside the run. Never raises: display state is not worth a crash."""
    path = preferences_path(workspace_id, directory)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(preferences.to_record(), indent=2), encoding="utf-8")
        temporary.replace(path)
        return path
    except OSError:
        return None
