"""Scientific contract specifications for hydrologic modeling extensions in BASIN.

Defines the formal data contracts, physical units, boundary invariants, and validation
rules required BEFORE implementing:
1. Catchment weighting (spatial sub-basin and precipitation station weights).
2. Reservoir Elevation-Area-Capacity (EAC) curves and surface area scaling.
3. Inflow routing and rainfall-runoff transformation.
4. Calibrated net reservoir evaporation (TWDB quadrangle pan evaporation).
5. Calibration and split-sample validation benchmarks (NSE, KGE, PBIAS).
6. Professional Engineering (PE) / Certified Professional Hydrologist (PH) review tokens.
7. Prohibited claims validator for UI displays and exported reports.

NOTE: This module defines contracts and validators without altering current calculations.
Uncalibrated models MUST NEVER be presented as scientifically validated or regulatory forecasts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
import re
from typing import Any


# -----------------------------------------------------------------------------
# Physical Conversion Constants
# -----------------------------------------------------------------------------

ACRE_FEET_PER_CFS_DAY = 1.983471   # 1 cfs sustained for 24h = 1.983471 ac-ft
ACRE_INCHES_PER_ACRE_FOOT = 12.0   # 1 acre * 1 foot = 12 acre-inches
SQ_MILES_TO_ACRES = 640.0          # 1 sq mile = 640 acres
MM_PER_INCH = 25.4                 # exact definition


# -----------------------------------------------------------------------------
# 1. Catchment Weighting Contract
# -----------------------------------------------------------------------------

class WeightingMethod(str, Enum):
    EQUAL_STATION_LEGACY = "equal_station_legacy"
    THIESSEN_POLYGON = "thiessen_polygon"
    ISOHYETAL = "isohyetal"
    PRISM_GRID_AREA_WEIGHTED = "prism_grid_area_weighted"


@dataclass(frozen=True)
class StationWeight:
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    weight: float
    drainage_area_sqmi: float | None = None

    def __post_init__(self):
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"Station weight must be in [0, 1], got {self.weight}")
        if self.drainage_area_sqmi is not None and self.drainage_area_sqmi < 0.0:
            raise ValueError("Drainage area cannot be negative")


@dataclass(frozen=True)
class CatchmentWeightingContract:
    catchment_id: str
    catchment_name: str
    total_area_sqmi: float
    method: WeightingMethod
    station_weights: tuple[StationWeight, ...]
    upstream_gauges: tuple[str, ...] = ()  # USGS NWIS Station IDs

    def __post_init__(self):
        if self.total_area_sqmi <= 0.0:
            raise ValueError(f"Total catchment area must be positive, got {self.total_area_sqmi}")
        if not self.station_weights:
            raise ValueError("Catchment weighting requires at least one station weight")
        total_weight = sum(sw.weight for sw in self.station_weights)
        if not math.isclose(total_weight, 1.0, rel_tol=1e-4, abs_tol=1e-4):
            raise ValueError(f"Station weights must sum to 1.0 (got {total_weight:.6f})")

    def weighted_rainfall_mm(self, station_measurements_mm: dict[str, float]) -> float:
        """Calculate weighted catchment rainfall in millimeters."""
        total = 0.0
        for sw in self.station_weights:
            if sw.station_id not in station_measurements_mm:
                raise KeyError(f"Missing measurement for station {sw.station_id}")
            total += sw.weight * float(station_measurements_mm[sw.station_id])
        return total


# -----------------------------------------------------------------------------
# 2. Reservoir Elevation-Area-Capacity (EAC) Contract
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class ReservoirEACContract:
    reservoir_name: str
    twdb_survey_date: str
    vertical_datum: str  # e.g., "NGVD29", "NAVD88"
    conservation_capacity_acft: float
    conservation_elevation_ft: float
    conservation_area_acres: float
    dead_storage_acft: float = 0.0
    # Polynomial coefficients for Area in acres as f(Storage in ac-ft):
    # Area(S) = a0 + a1*S + a2*S^2 + a3*S^3
    area_poly_coeffs: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    def __post_init__(self):
        if self.conservation_capacity_acft <= 0:
            raise ValueError("Conservation capacity must be positive")
        if self.conservation_area_acres <= 0:
            raise ValueError("Conservation area must be positive")
        if self.dead_storage_acft < 0 or self.dead_storage_acft >= self.conservation_capacity_acft:
            raise ValueError("Dead storage must be non-negative and less than capacity")

    def surface_area_acres(self, storage_acft: float) -> float:
        """Evaluate water surface area in acres from current storage in acre-feet."""
        s = max(0.0, min(float(storage_acft), self.conservation_capacity_acft))
        if s <= 0.0:
            return 0.0
        # If polynomial coefficients are not provided, fallback to standard sub-linear power law
        a0, a1, a2, a3 = self.area_poly_coeffs
        if a0 == a1 == a2 == a3 == 0.0:
            # Conservative standard geometric approximation: Area scales with (Storage/Cap)^(2/3)
            return self.conservation_area_acres * ((s / self.conservation_capacity_acft) ** (2.0 / 3.0))
        area = a0 + a1 * s + a2 * (s ** 2) + a3 * (s ** 3)
        return max(0.0, min(area, self.conservation_area_acres * 1.25))


# -----------------------------------------------------------------------------
# 3. Inflow Routing & Runoff Transformation Contract
# -----------------------------------------------------------------------------

class RunoffMethod(str, Enum):
    SCS_CURVE_NUMBER = "scs_curve_number"
    RATIONAL_RUNOFF_COEFFICIENT = "rational_runoff_coefficient"
    EMPIRICAL_SENSITIVITY_LEGACY = "empirical_sensitivity_legacy"


@dataclass(frozen=True)
class InflowRoutingContract:
    method: RunoffMethod
    baseflow_acft_day: float
    runoff_coefficient: float | None = None  # C in Q = C*P*A
    curve_number: float | None = None       # CN in SCS method (30 - 100)
    lag_days: int = 0                       # Hydrologic travel time delay
    attenuation_factor: float = 1.0         # Hydrograph dispersion (0 < factor <= 1)

    def __post_init__(self):
        if self.baseflow_acft_day < 0.0:
            raise ValueError("Baseflow cannot be negative")
        if self.lag_days < 0:
            raise ValueError("Lag days cannot be negative")
        if not (0.0 < self.attenuation_factor <= 1.0):
            raise ValueError("Attenuation factor must be in (0, 1]")
        if self.method == RunoffMethod.RATIONAL_RUNOFF_COEFFICIENT:
            if self.runoff_coefficient is None or not (0.0 <= self.runoff_coefficient <= 1.0):
                raise ValueError("Rational method requires runoff_coefficient in [0, 1]")
        elif self.method == RunoffMethod.SCS_CURVE_NUMBER:
            if self.curve_number is None or not (30.0 <= self.curve_number <= 100.0):
                raise ValueError("SCS method requires curve_number in [30, 100]")


# -----------------------------------------------------------------------------
# 4. Evaporation Calibration Contract (TWDB Quadrangle Net Evaporation)
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class EvaporationCalibrationContract:
    quadrangle_id: int                    # e.g., TWDB Quad 711 or 811
    pan_coefficient: float                # Typically 0.70 - 0.77 for Central/South Texas
    monthly_gross_pan_evap_inches: dict[int, float]  # Months 1..12
    units: str = "inches_per_month"

    def __post_init__(self):
        if not (0.50 <= self.pan_coefficient <= 1.00):
            raise ValueError(f"Pan coefficient {self.pan_coefficient} outside expected hydrologic range [0.50, 1.00]")
        if set(self.monthly_gross_pan_evap_inches.keys()) != set(range(1, 13)):
            raise ValueError("Evaporation table must contain all 12 calendar months")
        for m, val in self.monthly_gross_pan_evap_inches.items():
            if val < 0.0 or val > 20.0:
                raise ValueError(f"Monthly evaporation for month {m} ({val} in) is unrealistic")

    def net_evaporation_depth_inches(self, month: int, precipitation_inches: float, days_in_month: int = 30) -> float:
        """Net Evaporation = (Gross Pan Evap * K_pan) - Direct Precipitation on reservoir surface."""
        gross_pan = self.monthly_gross_pan_evap_inches[month]
        gross_lake = gross_pan * self.pan_coefficient
        net_monthly = gross_lake - float(precipitation_inches)
        return net_monthly / max(1, days_in_month)


# -----------------------------------------------------------------------------
# 5. Calibration & Validation Benchmarking Contract
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationBenchmarkContract:
    calibration_period_start: str
    calibration_period_end: str
    validation_period_start: str
    validation_period_end: str
    target_reservoir: str
    min_nse_threshold: float = 0.65       # Nash-Sutcliffe Efficiency target
    min_kge_threshold: float = 0.70       # Kling-Gupta Efficiency target
    max_pbias_pct_threshold: float = 10.0 # Percent Volume Bias tolerance

    def evaluate_fit(self, observed: list[float], simulated: list[float]) -> dict[str, float | bool]:
        """Compute standard hydrologic goodness-of-fit metrics."""
        if len(observed) != len(simulated) or len(observed) < 10:
            raise ValueError("Observed and simulated series must have identical length >= 10")
        obs_arr = [float(v) for v in observed]
        sim_arr = [float(v) for v in simulated]
        mean_obs = sum(obs_arr) / len(obs_arr)

        denom = sum((o - mean_obs) ** 2 for o in obs_arr)
        num = sum((o - s) ** 2 for o, s in zip(obs_arr, sim_arr))
        nse = 1.0 - (num / denom) if denom > 1e-9 else float("-inf")

        sum_obs = sum(obs_arr)
        pbias = 100.0 * sum(s - o for o, s in zip(obs_arr, sim_arr)) / sum_obs if sum_obs > 1e-9 else float("inf")

        # KGE formulation
        var_obs = sum((o - mean_obs) ** 2 for o in obs_arr) / len(obs_arr)
        mean_sim = sum(sim_arr) / len(sim_arr)
        var_sim = sum((s - mean_sim) ** 2 for s in sim_arr) / len(sim_arr)
        sd_obs = math.sqrt(var_obs) if var_obs > 0 else 1e-9
        sd_sim = math.sqrt(var_sim) if var_sim > 0 else 1e-9

        cov = sum((o - mean_obs) * (s - mean_sim) for o, s in zip(obs_arr, sim_arr)) / len(obs_arr)
        r = cov / (sd_obs * sd_sim) if (sd_obs * sd_sim) > 0 else 0.0
        alpha = sd_sim / sd_obs
        beta = mean_sim / mean_obs if mean_obs > 0 else 1.0
        kge = 1.0 - math.sqrt((r - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2)

        passes_calibration = bool(
            nse >= self.min_nse_threshold and
            kge >= self.min_kge_threshold and
            abs(pbias) <= self.max_pbias_pct_threshold
        )

        return {
            "nse": round(nse, 4),
            "kge": round(kge, 4),
            "pbias_pct": round(pbias, 2),
            "passes_calibration": passes_calibration,
        }


# -----------------------------------------------------------------------------
# 6. Professional Review & Licensing Boundary Contract
# -----------------------------------------------------------------------------

class ApprovalStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    PROVISIONAL_EXPLORATORY = "provisional_exploratory"
    LICENSED_ENGINEER_REVIEWED = "licensed_engineer_reviewed"


@dataclass(frozen=True)
class ProfessionalApprovalContract:
    status: ApprovalStatus
    reviewer_name: str | None = None
    license_type: str | None = None       # e.g., "Texas Professional Engineer (PE)", "Certified Professional Hydrologist (PH)"
    license_number: str | None = None
    review_date: str | None = None
    scope_notes: str | None = None
    tamper_hash: str | None = None

    def __post_init__(self):
        if self.status == ApprovalStatus.LICENSED_ENGINEER_REVIEWED:
            if not self.reviewer_name or not self.license_number or not self.license_type:
                raise ValueError("Licensed review requires reviewer_name, license_type, and license_number")


# -----------------------------------------------------------------------------
# 7. Prohibited Claims Registry and Text Validator
# -----------------------------------------------------------------------------

PROHIBITED_CLAIM_PATTERNS = [
    # Prohibits claiming uncalibrated experiments are official forecasts
    (r"\b(official|regulatory|statutory|certified)\s+water\s+forecast\b", "Cannot claim BASIN outputs are official/regulatory forecasts."),
    # Prohibits claiming exact statutory Day Zero certainty without disclaimer
    (r"\bguaranteed\s+(day\s+zero|dry\s+pipe)\s+date\b", "Cannot claim guaranteed Day Zero dates; models are illustrative screening tools."),
    # Prohibits claiming equivalence to statutory state models (TCEQ WAM Run 3)
    (r"\b(replaces?|substitutes?\s+for)\s+(the\s+)?(tceq\s+)?(nueces\s+)?wam\b", "Cannot claim BASIN replaces or substitutes for official TCEQ WAM models."),
    # Prohibits claiming engineering certification without a verified PE token
    (r"\b(licensed|certified)\s+by\s+(professional\s+engineers?|pe|hydrologists?)\b", "Cannot claim engineering certification unless signed off with valid PE credentials."),
    # Prohibits claiming 1:1 drought severity equivalence from rainfall scaling
    (r"\bscaling\s+rainfall\s+(equals|is\s+identical\s+to)\s+scaling\s+drought\s+severity\b", "Scaling rainfall retention does not scale hydrologic drought severity 1:1."),
    # Prohibits claiming user-provided custom data is official, verified, or certified
    (r"(?<!not\s)(?<!never\s)\b(official\s+station|verified\s+source|certified\s+data|verified\s+by\s+noaa|certified\s+by\s+usgs)\b", "Custom data must not be described as official, verified, or certified."),
    # Prohibits isolated or undefined rainfall percentage claims
    (r"\b(?:rainfall:\s*\d+%(?!\s*(?:retained|reduction|of))|\b\d+%\s*rainfall\b(?!\s*(?:tier|of|retained|reduction|window|shortfall|deficit)))", "Rainfall percentage must state baseline and whether it represents retained rainfall or reduction."),
]


def validate_report_text_against_prohibited_claims(text: str) -> list[str]:
    """Scan report, narrative, or UI text for scientifically prohibited affirmative claims."""
    violations: list[str] = []
    for pattern, rationale in PROHIBITED_CLAIM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            violations.append(f"Prohibited Claim Detected: '{match.group(0)}' - {rationale}")
    return violations


# -----------------------------------------------------------------------------
# Canonical Preset Contract Instances for Texas Region N
# -----------------------------------------------------------------------------

# TWDB 2016 Survey for Lake Corpus Christi (Conservation: 256,339 ac-ft @ 94.0 ft NGVD29, 19,748 acres)
LCC_EAC_CONTRACT = ReservoirEACContract(
    reservoir_name="Lake Corpus Christi",
    twdb_survey_date="2016-03",
    vertical_datum="NGVD29",
    conservation_capacity_acft=256339.0,
    conservation_elevation_ft=94.0,
    conservation_area_acres=19748.0,
    dead_storage_acft=75000.0,
)

# TWDB 2012 Survey for Choke Canyon Reservoir (Conservation: 663,400 ac-ft @ 220.5 ft MSL, 25,690 acres)
CCR_EAC_CONTRACT = ReservoirEACContract(
    reservoir_name="Choke Canyon Reservoir",
    twdb_survey_date="2012-08",
    vertical_datum="NGVD29",
    conservation_capacity_acft=663400.0,
    conservation_elevation_ft=220.5,
    conservation_area_acres=25690.0,
    dead_storage_acft=0.0,
)

# Region N Lower Nueces Catchment Weighting Contract (USGS Gauges: 08211000 Nueces nr Mathis, 08206900 Frio nr Tilden)
REGION_N_CATCHMENT_CONTRACT = CatchmentWeightingContract(
    catchment_id="TX_REGION_N_NUECES_FRIO",
    catchment_name="Nueces-Frio River Basin above Lake Corpus Christi and Choke Canyon",
    total_area_sqmi=22146.0,  # 16,656 sq mi (Nueces) + 5,490 sq mi (Frio)
    method=WeightingMethod.THIESSEN_POLYGON,
    station_weights=(
        StationWeight(station_id="USW00012924", station_name="Corpus Christi Intl AP", latitude=27.77, longitude=-97.51, weight=0.25, drainage_area_sqmi=5536.0),
        StationWeight(station_id="USW00012921", station_name="San Antonio Intl AP", latitude=29.53, longitude=-98.47, weight=0.50, drainage_area_sqmi=11073.0),
        StationWeight(station_id="USW00012935", station_name="Victoria Regional AP", latitude=28.85, longitude=-96.92, weight=0.25, drainage_area_sqmi=5537.0),
    ),
    upstream_gauges=("08211000", "08206900"),
)

# TWDB Quadrangle 811 (South Texas / Nueces Basin) Gross Evaporation Normals (inches/month)
TWDB_QUAD_811_EVAP_CONTRACT = EvaporationCalibrationContract(
    quadrangle_id=811,
    pan_coefficient=0.72,
    monthly_gross_pan_evap_inches={
        1: 2.85, 2: 3.42, 3: 5.10, 4: 6.25, 5: 7.20, 6: 8.50,
        7: 9.30, 8: 9.10, 9: 7.20, 10: 5.80, 11: 3.90, 12: 2.90,
    },
)
