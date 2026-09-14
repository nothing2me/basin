"""Decision-owner and service-area context for a BASIN screening run.

This context explains who the rainfall shortlist is for and targets the station
choices offered for generation. Naming a community still does not assert that a
point gauge or water-system preset represents its source-water catchment.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


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

RAINFALL_TARGETS = {
    "community_area": "Local community / selected county area",
    "source_area": "Water-supply source area (select stations manually)",
    "region_wide": "Region N-wide rainfall context",
}


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
    rainfall_target: str = "community_area"
    modeling_effect: str = "station_targeting"

    def __post_init__(self) -> None:
        if self.scope not in {"region_wide", "specific_provider"}:
            raise ValueError("Analysis scope must be region-wide or a specific provider/community")
        if self.organization_type not in ORGANIZATION_TYPES:
            raise ValueError("Unknown organization type")
        if self.supply_relationship not in SUPPLY_RELATIONSHIPS:
            raise ValueError("Unknown water-source relationship")
        if self.decision_use not in DECISION_USES:
            raise ValueError("Unknown planning use")
        if self.rainfall_target not in RAINFALL_TARGETS:
            raise ValueError("Unknown rainfall evidence target")
        if self.scope == "region_wide" and self.rainfall_target != "region_wide":
            raise ValueError("Region-wide context must use the Region N rainfall target")
        if self.modeling_effect != "station_targeting":
            raise ValueError("Analysis context must use the supported station-targeting contract")
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
            rainfall_target="region_wide",
        )

    @classmethod
    def from_record(cls, record: dict | None) -> "AnalysisContext":
        if record is None:
            return cls.region_wide()
        if not isinstance(record, dict):
            raise ValueError("Invalid analysis context")
        required = {
            "scope", "organization_type", "organization_name", "counties",
            "community", "supply_relationship", "decision_use", "modeling_effect",
        }
        allowed = required | {"rainfall_target"}
        if not required <= set(record) or not set(record) <= allowed:
            raise ValueError("Analysis context fields are missing or unsupported")
        rainfall_target = record.get(
            "rainfall_target", "region_wide" if record["scope"] == "region_wide" else "community_area"
        )
        values = {**record, "counties": tuple(record["counties"]), "rainfall_target": rainfall_target}
        # Saved 2.2 runs used context_only before community targeting was added.
        if values["modeling_effect"] == "context_only":
            values["modeling_effect"] = "station_targeting"
        return cls(**values)

    def record(self) -> dict:
        result = asdict(self)
        result["counties"] = list(self.counties)
        return result

    @property
    def audience_label(self) -> str:
        if self.scope == "region_wide":
            return "Region N planning area"
        place = f" · {self.community}" if self.community else ""
        return f"{self.organization_name}{place}"

    @property
    def county_label(self) -> str:
        return "All 11 Region N counties" if self.counties == REGION_N_COUNTIES else ", ".join(self.counties)
