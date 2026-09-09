"""Water system configuration for reservoir drawdown simulation.

Parameterizes reservoir capacity, inflow sensitivity, evaporation, and demand
so rural water districts, farm operators, and municipal systems can simulate
drawdown on their own infrastructure rather than fixed regional constants.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class WaterSource:
    """An individual water storage facility (reservoir, lake, pond, or tank)."""
    name: str
    capacity_acft: float
    inflow_base_acft: float = 30.0
    inflow_sensitivity: float = 45.0  # ac-ft per mm of mean station rainfall
    evap_summer_acft: float = 750.0  # June–September potential evap (ac-ft/day)
    evap_winter_acft: float = 380.0  # October–May potential evap (ac-ft/day)

    def validate(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("WaterSource name must be a non-empty string")
        if not isinstance(self.capacity_acft, (int, float)) or not math.isfinite(self.capacity_acft) or self.capacity_acft <= 0:
            raise ValueError(f"WaterSource '{self.name}' capacity must be a positive number")
        for attr in ("inflow_base_acft", "inflow_sensitivity", "evap_summer_acft", "evap_winter_acft"):
            val = getattr(self, attr)
            if not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0:
                raise ValueError(f"WaterSource '{self.name}' {attr} must be a non-negative number")

    @classmethod
    def scaled_for_capacity(cls, name: str, capacity_acft: float,
                            inflow_base_acft: float | None = None,
                            inflow_sensitivity: float | None = None,
                            evap_summer_acft: float | None = None,
                            evap_winter_acft: float | None = None) -> WaterSource:
        """Create a WaterSource with defaults scaled to capacity via area-capacity power law (Cap^0.65)."""
        scale = (capacity_acft / 919300.0) ** 0.65
        default_inflow_base = max(0.5, round(30.0 * scale, 1)) if inflow_base_acft is None else float(inflow_base_acft)
        default_inflow_sens = max(0.5, round(45.0 * scale, 1)) if inflow_sensitivity is None else float(inflow_sensitivity)
        default_evap_s = max(1.0, round(750.0 * scale, 1)) if evap_summer_acft is None else float(evap_summer_acft)
        default_evap_w = max(0.5, round(380.0 * scale, 1)) if evap_winter_acft is None else float(evap_winter_acft)
        return cls(
            name=name,
            capacity_acft=float(capacity_acft),
            inflow_base_acft=default_inflow_base,
            inflow_sensitivity=default_inflow_sens,
            evap_summer_acft=default_evap_s,
            evap_winter_acft=default_evap_w,
        )


@dataclass(frozen=True)
class WaterSystemConfig:
    """Configurable multi-pool or single-pool water system."""
    name: str
    sources: tuple[WaterSource, ...]
    demand_acft_day: float = 370.0
    demand_no_pipeline_acft_day: float | None = 554.0
    stage_bands_pct: tuple[float, ...] = (0.40, 0.30, 0.20, 0.15)
    allocation_threshold_pct: float = 0.20
    allocation_primary_fraction: float = 0.65
    allocation_secondary_fraction: float = 0.15
    use_smooth_evap: bool = False
    use_eac_scaling: bool = False

    def validate(self) -> None:
        if not self.name:
            raise ValueError("WaterSystemConfig name must be a non-empty string")
        if not self.sources:
            raise ValueError("WaterSystemConfig must have at least one WaterSource")
        for s in self.sources:
            s.validate()
        if not isinstance(self.demand_acft_day, (int, float)) or not math.isfinite(self.demand_acft_day) or self.demand_acft_day < 0:
            raise ValueError("demand_acft_day must be a non-negative number")
        if self.demand_no_pipeline_acft_day is not None:
            if not isinstance(self.demand_no_pipeline_acft_day, (int, float)) or not math.isfinite(self.demand_no_pipeline_acft_day) or self.demand_no_pipeline_acft_day < 0:
                raise ValueError("demand_no_pipeline_acft_day must be a non-negative number")
        for b in self.stage_bands_pct:
            if not isinstance(b, (int, float)) or not 0 <= b <= 1:
                raise ValueError("stage_bands_pct values must be between 0 and 1")

    @property
    def total_capacity_acft(self) -> float:
        return sum(s.capacity_acft for s in self.sources)

    def describe_assumptions(self) -> dict:
        caps_dict = {s.name: s.capacity_acft for s in self.sources}
        thresholds_str = ", ".join(f"{b * 100:.0f}%" for b in self.stage_bands_pct)
        return {
            "model_version": "parameterized-balance-1",
            "system_name": self.name,
            "scope": "Uncalibrated multi-pool experiment; no forecast or official restriction dates. Excluded from session evidence packets and replay verification.",
            "capacities_acft": caps_dict,
            "total_capacity_acft": self.total_capacity_acft,
            "inflow": f"Sum of source inflows ({sum(s.inflow_base_acft for s in self.sources):.0f} base + {sum(s.inflow_sensitivity for s in self.sources):.0f} × mean rainfall mm/day); illustrative coefficient, no catchment calibration",
            "evaporation": f"Potential loss {sum(s.evap_summer_acft for s in self.sources):.0f} ac-ft/day in June–September, {sum(s.evap_winter_acft for s in self.sources):.0f} otherwise; illustrative seasonal assumption",
            "demand": f"Requested {self.demand_acft_day:.0f} ac-ft/day" + (f" with pipeline ({self.demand_no_pipeline_acft_day:.0f} without)" if self.demand_no_pipeline_acft_day is not None else "") + "; conservation reduces this request",
            "allocation": "Inflow proportional to capacities; evaporation proportional to available water; demand served from available pools; excess spills",
            "thresholds": f"Illustrative combined-storage bands at {thresholds_str}; not current official policy",
            "time_step": "Daily: add inflow, serve available evaporation and demand, spill excess. Rows report end-of-day storage.",
        }


REGION_N_PRESET = WaterSystemConfig(
    name="Region N (Corpus Christi system — illustrative)",
    sources=(
        WaterSource("Lake Corpus Christi", 257300.0, inflow_base_acft=30.0, inflow_sensitivity=45.0, evap_summer_acft=750.0, evap_winter_acft=380.0),
        WaterSource("Choke Canyon", 662600.0, inflow_base_acft=0.0, inflow_sensitivity=0.0, evap_summer_acft=0.0, evap_winter_acft=0.0),
    ),
    demand_acft_day=370.0,
    demand_no_pipeline_acft_day=554.0,
    allocation_threshold_pct=0.20,
    allocation_primary_fraction=0.65,
    allocation_secondary_fraction=0.15,
)

SMALL_MUNI_PRESET = WaterSystemConfig(
    name="Small Municipal District (single reservoir)",
    sources=(
        WaterSource("Municipal Reservoir", 12000.0, inflow_base_acft=2.0, inflow_sensitivity=5.0, evap_summer_acft=30.0, evap_winter_acft=15.0),
    ),
    demand_acft_day=15.0,
    demand_no_pipeline_acft_day=None,
    stage_bands_pct=(0.40, 0.30, 0.20, 0.15),
)

RURAL_FARM_PRESET = WaterSystemConfig(
    name="Rural Farm / WCID Pond System",
    sources=(
        WaterSource("Irrigation Pond", 1500.0, inflow_base_acft=0.5, inflow_sensitivity=1.5, evap_summer_acft=5.0, evap_winter_acft=2.0),
    ),
    demand_acft_day=3.5,
    demand_no_pipeline_acft_day=None,
    stage_bands_pct=(0.40, 0.30, 0.20, 0.15),
)

SYSTEM_PRESETS: dict[str, WaterSystemConfig] = {
    "Region N (Corpus Christi — 2 reservoirs)": REGION_N_PRESET,
    "Small Municipal District (12k ac-ft)": SMALL_MUNI_PRESET,
    "Rural Farm Pond (1.5k ac-ft)": RURAL_FARM_PRESET,
}
