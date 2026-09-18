"""Decision-owner and service-area context for a BASIN screening run.

This context explains who the rainfall shortlist is for.  It is deliberately
separate from station selection and the optional storage experiment: naming a
community does not assert that the bundled gauges or a water-system preset are
hydrologically representative of that community.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re



REGION_N_COUNTIES = (
    "Aransas", "Bee", "Brooks", "Duval", "Jim Wells", "Kenedy",
    "Kleberg", "Live Oak", "McMullen", "Nueces", "San Patricio",
)

ORGANIZATION_TYPES = {
    "regional_planning": "Regional planning group or agency",
    "municipality": "City or municipality",
    "rural_provider": "Rural water provider / WSC",
    "water_district": "WCID, MUD or other water district",
    "consultant": "Hydrologist, engineer or consultant",
    "other": "Other organization",
}

SUPPLY_RELATIONSHIPS = {
    "regional_wholesale": "Regional reservoir system / wholesale customer",
    "local_surface": "Local surface-water supply",
    "groundwater": "Groundwater supply",
    "mixed": "Mixed supply",
    "unknown": "Unknown or not yet reviewed",
    "multiple": "Multiple systems across Region N",
}

DECISION_USES = {
    "regional_screening": "Regional scenario screening",
    "modeling_request": "Prepare a hydrologist modeling request",
    "drought_plan": "Review a drought contingency plan",
    "infrastructure": "Explore infrastructure stress assumptions",
    "provider_discussion": "Support a provider or board discussion",
    "other": "Other planning use",
}


def is_placeholder_text(text: str | None) -> bool:
    """Detect test/placeholder strings like 'asdf', 'ewrwewe', 'fsdf', or random consonant clusters."""
    if not text or not text.strip():
        return True
    cleaned = re.sub(r"[^a-zA-Z]", "", text).strip().lower()
    if not cleaned:
        return True
    if len(cleaned) < 3:
        return True
    common_placeholders = {
        "asdf", "qwer", "zxcv", "test", "demo", "placeholder", "dummy", "fsdf",
        "ewrwewe", "qwerty", "temp", "sample", "fake", "abcd", "xyz", "foo", "bar",
        "xxx", "yyy", "zzz", "aaa", "bbb",
    }
    if cleaned in common_placeholders:
        return True
    if len(set(cleaned)) == 1:
        return True
    if len(set(cleaned)) <= 2 and len(cleaned) >= 4:
        return True
    # Excessive consonant cluster (5 or more consecutive consonants without vowels)
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", cleaned):
        return True
    return False


@dataclass(frozen=True)
class AnalysisContext:
    """Validated, auditable description of the intended decision context."""

    scope: str
    organization_type: str
    organization_name: str
    counties: tuple[str, ...]
    community: str
    supply_relationship: str
    decision_use: str
    modeling_effect: str = "context_only"

    def __post_init__(self) -> None:
        if self.scope not in {"region_wide", "specific_provider"}:
            raise ValueError("Analysis scope must be region-wide or a specific provider/community")
        if self.organization_type not in ORGANIZATION_TYPES:
            raise ValueError("Unknown organization type")
        if self.supply_relationship not in SUPPLY_RELATIONSHIPS:
            raise ValueError("Unknown water-source relationship")
        if self.decision_use not in DECISION_USES:
            raise ValueError("Unknown planning use")
        if self.modeling_effect != "context_only":
            raise ValueError("Community context cannot alter calculations without a reviewed spatial model")
        name = self.organization_name.strip()
        community = self.community.strip()
        object.__setattr__(self, "organization_name", name)
        object.__setattr__(self, "community", community)
        normalized = tuple(dict.fromkeys(self.counties))
        if not normalized or any(county not in REGION_N_COUNTIES for county in normalized):
            raise ValueError("Choose one or more Region N counties")
        object.__setattr__(self, "counties", normalized)
        if self.scope == "specific_provider" and not name:
            raise ValueError("Enter the city, provider, district or organization name")

    @classmethod
    def region_wide(cls) -> "AnalysisContext":
        return cls(
            scope="region_wide",
            organization_type="regional_planning",
            organization_name="Region N planning area",
            counties=REGION_N_COUNTIES,
            community="",
            supply_relationship="multiple",
            decision_use="regional_screening",
        )

    @classmethod
    def from_record(cls, record: dict | None) -> "AnalysisContext":
        if record is None:
            return cls.region_wide()
        if not isinstance(record, dict):
            raise ValueError("Invalid analysis context")
        expected = {
            "scope", "organization_type", "organization_name", "counties",
            "community", "supply_relationship", "decision_use", "modeling_effect",
        }
        if set(record) != expected:
            raise ValueError("Analysis context fields are missing or unsupported")
        return cls(**{**record, "counties": tuple(record["counties"])})

    def record(self) -> dict:
        result = asdict(self)
        result["counties"] = list(self.counties)
        return result

    @property
    def audience_label(self) -> str:
        if self.scope == "region_wide":
            return "Region N planning area"
        org = self.organization_name
        comm = self.community
        if is_placeholder_text(org):
            org = "Region N Planning Entity (Unspecified)"
        if is_placeholder_text(comm):
            comm = ""
        place = f" · {comm}" if comm else ""
        return f"{org}{place}"

    @property
    def county_label(self) -> str:
        return "All 11 Region N counties" if self.counties == REGION_N_COUNTIES else ", ".join(self.counties)
