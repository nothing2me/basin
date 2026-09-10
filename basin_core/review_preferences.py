"""Display preferences for the Review page.

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

GUIDANCE: dict[str, dict[str, str]] = {
    "guided": {
        "label": "Guided explanations",
        "help": "Add short orientation notes. A presentation preference, not a measure of expertise.",
    },
    "technical": {
        "label": "Technical detail",
        "help": "Skip the orientation notes. Limitations and disclosures are shown either way.",
    },
}

# Canonical Review tab order, used whenever no focus applies.
TAB_KEYS: tuple[str, ...] = ("storage", "agronomics", "rainfall", "edits", "provenance")

TAB_LABELS: dict[str, str] = {
    "storage": "💧 Storage Drawdown & Water System",
    "agronomics": "🌾 Crop Irrigation & Wildfire Risk",
    "rainfall": "📈 Rainfall Deficit & Historical Context",
    "edits": "✏️ Edit Rainfall & Refine Shortlist",
    "provenance": "📋 Source Evidence & Daily Values",
}

# Which tools lead for each goal. "provenance" leads in every focus on purpose: source
# identity, evidence and stated limitations must not be demoted by a display choice.
FOCUS_PRIMARY: dict[str, tuple[str, ...]] = {
    "compare": ("rainfall", "provenance"),
    "storage": ("storage", "provenance"),
    "handoff": ("edits", "provenance"),
}

# Shown as text next to the summary. Never applied automatically: changing a display
# focus must not rerank scenarios or move a shortlist.
SUGGESTED_WEIGHT_PRESET: dict[str, str] = {
    "compare": "Illustrative regional planner",
    "storage": "Illustrative emergency planner",
    "handoff": "Illustrative rural provider",
}

GUIDED_TAB_NOTES: dict[str, str] = {
    "storage": "Optional experiment. Storage results are illustrative and are excluded from the verified packet.",
    "agronomics": "Illustrative agronomic indicators derived from the same rainfall record.",
    "rainfall": "The rainfall record for this scenario and how it compares with matched historical windows.",
    "edits": "Change rainfall content or swap a shortlist entry. Edits clear an existing acceptance.",
    "provenance": "Where the numbers come from: cited evidence, daily values and revision history.",
}


def _coerce(value, options: dict, fallback: str) -> str:
    return value if isinstance(value, str) and value in options else fallback


@dataclass(frozen=True)
class ReviewPreferences:
    """A versioned, validated record of Review display choices."""

    goal: str = "compare"
    data_source: str = "regional"
    guidance: str = "guided"
    configured: bool = False
    dismissed: bool = False
    show_all_tools: bool = False
    version: int = PREFERENCES_VERSION

    def __post_init__(self) -> None:
        if self.goal not in GOALS:
            raise ValueError(f"Unknown Review goal: {self.goal!r}")
        if self.data_source not in DATA_SOURCES:
            raise ValueError(f"Unknown data source: {self.data_source!r}")
        if self.guidance not in GUIDANCE:
            raise ValueError(f"Unknown guidance level: {self.guidance!r}")
        for name in ("configured", "dismissed", "show_all_tools"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be true or false")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("version must be a positive integer")

    # -- presentation ---------------------------------------------------------------
    @property
    def guided(self) -> bool:
        return self.guidance == "guided"

    @property
    def needs_setup(self) -> bool:
        """True until the reader either answers the questions or skips them."""
        return not self.configured and not self.dismissed

    def summary(self) -> str:
        if not self.configured:
            return "Showing all Review tools (setup skipped)."
        return " · ".join([
            GOALS[self.goal]["label"],
            DATA_SOURCES[self.data_source]["label"],
            GUIDANCE[self.guidance]["label"],
        ])

    def describe_rows(self) -> list[tuple[str, str]]:
        return [
            ("Goal", GOALS[self.goal]["label"]),
            ("Data", DATA_SOURCES[self.data_source]["label"]),
            ("Guidance", GUIDANCE[self.guidance]["label"]),
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
            "configured": self.configured,
            "dismissed": self.dismissed,
            "show_all_tools": self.show_all_tools,
        }

    @classmethod
    def from_record(cls, record) -> "ReviewPreferences":
        """Build from a stored record, tolerating older, partial or damaged files.

        Unknown or missing values fall back to defaults rather than raising, so a run
        saved by an older version of BASIN still opens.
        """
        if not isinstance(record, dict):
            return cls()
        return cls(
            goal=_coerce(record.get("goal"), GOALS, "compare"),
            data_source=_coerce(record.get("data_source"), DATA_SOURCES, "regional"),
            guidance=_coerce(record.get("guidance"), GUIDANCE, "guided"),
            configured=bool(record.get("configured", False)),
            dismissed=bool(record.get("dismissed", False)),
            show_all_tools=bool(record.get("show_all_tools", False)),
            version=PREFERENCES_VERSION,
        )

    def replace(self, **changes) -> "ReviewPreferences":
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
