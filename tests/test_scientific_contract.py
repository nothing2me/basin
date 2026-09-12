"""Automated verification suite for BASIN scientific contracts and audit rules.

Tests:
1. Catchment weighting contract invariants and weighted precipitation calculations.
2. Reservoir Elevation-Area-Capacity (EAC) hypsometry bounds and monotonicity.
3. Inflow routing and runoff transformation contract validations.
4. TWDB Quadrangle evaporation calibration and net loss evaluations.
5. Hydrologic calibration benchmarks (NSE, KGE, PBIAS) and threshold gates.
6. Professional review and engineering licensing boundary assertions.
7. Prohibited claims validator scanning for forbidden affirmative statements.
8. Canonical Region N preset contracts (Lake Corpus Christi, Choke Canyon, Quad 811).
"""
from __future__ import annotations

import pytest

from basin_core.scientific_contract import (
    ApprovalStatus,
    CatchmentWeightingContract,
    CalibrationBenchmarkContract,
    EvaporationCalibrationContract,
    InflowRoutingContract,
    ProfessionalApprovalContract,
    ReservoirEACContract,
    RunoffMethod,
    StationWeight,
    WeightingMethod,
    validate_report_text_against_prohibited_claims,
    CCR_EAC_CONTRACT,
    LCC_EAC_CONTRACT,
    REGION_N_CATCHMENT_CONTRACT,
    TWDB_QUAD_811_EVAP_CONTRACT,
)


# -----------------------------------------------------------------------------
# 1. Catchment Weighting Contract Tests
# -----------------------------------------------------------------------------

def test_catchment_weighting_normalization():
    sw1 = StationWeight("S1", "Station 1", 28.0, -97.0, 0.40)
    sw2 = StationWeight("S2", "Station 2", 28.5, -97.5, 0.60)
    contract = CatchmentWeightingContract(
        catchment_id="TEST_BASIN",
        catchment_name="Test Basin",
        total_area_sqmi=1000.0,
        method=WeightingMethod.THIESSEN_POLYGON,
        station_weights=(sw1, sw2),
    )
    assert contract.total_area_sqmi == 1000.0
    # Weighted average: 0.40 * 10 + 0.60 * 20 = 4 + 12 = 16.0 mm
    weighted = contract.weighted_rainfall_mm({"S1": 10.0, "S2": 20.0})
    assert weighted == pytest.approx(16.0)


def test_catchment_weighting_rejects_non_unitary_sum():
    sw1 = StationWeight("S1", "Station 1", 28.0, -97.0, 0.40)
    sw2 = StationWeight("S2", "Station 2", 28.5, -97.5, 0.40)  # sums to 0.80 != 1.0
    with pytest.raises(ValueError, match="Station weights must sum to 1.0"):
        CatchmentWeightingContract(
            catchment_id="INVALID",
            catchment_name="Invalid",
            total_area_sqmi=500.0,
            method=WeightingMethod.THIESSEN_POLYGON,
            station_weights=(sw1, sw2),
        )


def test_station_weight_rejects_out_of_range():
    with pytest.raises(ValueError, match="Station weight must be in"):
        StationWeight("S1", "Station 1", 28.0, -97.0, 1.25)
    with pytest.raises(ValueError, match="Station weight must be in"):
        StationWeight("S1", "Station 1", 28.0, -97.0, -0.10)


# -----------------------------------------------------------------------------
# 2. Reservoir EAC Hypsometry Tests
# -----------------------------------------------------------------------------

def test_reservoir_eac_hypsometry_monotonic_and_bounded():
    eac = ReservoirEACContract(
        reservoir_name="Test Lake",
        twdb_survey_date="2020-01",
        vertical_datum="NGVD29",
        conservation_capacity_acft=100000.0,
        conservation_elevation_ft=100.0,
        conservation_area_acres=10000.0,
    )
    # Area at 0 storage is 0
    assert eac.surface_area_acres(0.0) == 0.0
    # Area at full capacity is 10,000 acres
    assert eac.surface_area_acres(100000.0) == pytest.approx(10000.0)

    # Monotonicity check
    s_half = 50000.0
    area_half = eac.surface_area_acres(s_half)
    assert 0.0 < area_half < 10000.0
    assert area_half == pytest.approx(10000.0 * (0.5 ** (2.0 / 3.0)))


def test_reservoir_eac_polynomial_evaluation():
    # Hypothetical quadratic: Area(S) = 100 + 0.05*S + 0.0000001*S^2
    eac = ReservoirEACContract(
        reservoir_name="Poly Lake",
        twdb_survey_date="2022-06",
        vertical_datum="NAVD88",
        conservation_capacity_acft=50000.0,
        conservation_elevation_ft=150.0,
        conservation_area_acres=5000.0,
        area_poly_coeffs=(100.0, 0.05, 1e-7, 0.0),
    )
    area = eac.surface_area_acres(20000.0)
    expected = 100.0 + 0.05 * 20000.0 + 1e-7 * (20000.0 ** 2)
    assert area == pytest.approx(expected)


# -----------------------------------------------------------------------------
# 3. Inflow Routing Contract Tests
# -----------------------------------------------------------------------------

def test_inflow_routing_contract_scs():
    routing = InflowRoutingContract(
        method=RunoffMethod.SCS_CURVE_NUMBER,
        baseflow_acft_day=25.0,
        curve_number=75.0,
        lag_days=3,
        attenuation_factor=0.85,
    )
    assert routing.curve_number == 75.0
    assert routing.lag_days == 3


def test_inflow_routing_contract_validation():
    with pytest.raises(ValueError, match="SCS method requires curve_number in"):
        InflowRoutingContract(
            method=RunoffMethod.SCS_CURVE_NUMBER,
            baseflow_acft_day=10.0,
            curve_number=20.0,  # below 30
        )
    with pytest.raises(ValueError, match="Rational method requires runoff_coefficient"):
        InflowRoutingContract(
            method=RunoffMethod.RATIONAL_RUNOFF_COEFFICIENT,
            baseflow_acft_day=10.0,
            runoff_coefficient=1.5,  # above 1.0
        )


# -----------------------------------------------------------------------------
# 4. Evaporation Calibration Contract Tests
# -----------------------------------------------------------------------------

def test_evaporation_calibration_net_depth():
    monthly_evap = {m: 6.0 for m in range(1, 13)}
    contract = EvaporationCalibrationContract(
        quadrangle_id=811,
        pan_coefficient=0.75,
        monthly_gross_pan_evap_inches=monthly_evap,
    )
    # Month 7: Gross pan = 6.0 in, K_pan = 0.75 -> Gross lake = 4.5 in.
    # Direct rain = 1.5 in -> Net monthly = 4.5 - 1.5 = 3.0 in.
    # Daily net depth for 30 days = 3.0 / 30 = 0.10 in/day
    daily_net = contract.net_evaporation_depth_inches(month=7, precipitation_inches=1.5, days_in_month=30)
    assert daily_net == pytest.approx(0.10)


# -----------------------------------------------------------------------------
# 5. Calibration Benchmark Contract Tests
# -----------------------------------------------------------------------------

def test_calibration_benchmark_metrics_perfect_fit():
    benchmark = CalibrationBenchmarkContract(
        calibration_period_start="1991-01-01",
        calibration_period_end="2010-12-31",
        validation_period_start="2011-01-01",
        validation_period_end="2015-12-31",
        target_reservoir="Lake Corpus Christi",
    )
    obs = [100.0, 120.0, 110.0, 95.0, 80.0, 85.0, 90.0, 105.0, 115.0, 130.0]
    fit = benchmark.evaluate_fit(obs, obs)
    assert fit["nse"] == 1.0
    assert fit["kge"] == 1.0
    assert fit["pbias_pct"] == 0.0
    assert fit["passes_calibration"] is True


def test_calibration_benchmark_metrics_poor_fit():
    benchmark = CalibrationBenchmarkContract(
        calibration_period_start="1991-01-01",
        calibration_period_end="2010-12-31",
        validation_period_start="2011-01-01",
        validation_period_end="2015-12-31",
        target_reservoir="Choke Canyon",
    )
    obs = [100.0, 120.0, 110.0, 95.0, 80.0, 85.0, 90.0, 105.0, 115.0, 130.0]
    sim = [50.0, 55.0, 60.0, 45.0, 40.0, 42.0, 48.0, 52.0, 58.0, 65.0]  # ~50% underprediction
    fit = benchmark.evaluate_fit(obs, sim)
    assert fit["nse"] < 0.0
    assert fit["pbias_pct"] < -40.0
    assert fit["passes_calibration"] is False


# -----------------------------------------------------------------------------
# 6. Professional Review & Licensing Boundary Tests
# -----------------------------------------------------------------------------

def test_professional_approval_contract_unreviewed():
    app = ProfessionalApprovalContract(status=ApprovalStatus.UNREVIEWED)
    assert app.status == ApprovalStatus.UNREVIEWED
    assert app.reviewer_name is None


def test_professional_approval_contract_licensed():
    app = ProfessionalApprovalContract(
        status=ApprovalStatus.LICENSED_ENGINEER_REVIEWED,
        reviewer_name="Jane Doe, PE",
        license_type="Texas Professional Engineer (PE)",
        license_number="TX-123456",
        review_date="2026-09-12",
        scope_notes="Reviewed Region N hydrologic mass balance calculations.",
    )
    assert app.status == ApprovalStatus.LICENSED_ENGINEER_REVIEWED
    assert app.license_number == "TX-123456"


def test_professional_approval_contract_rejects_missing_license():
    with pytest.raises(ValueError, match="Licensed review requires reviewer_name"):
        ProfessionalApprovalContract(
            status=ApprovalStatus.LICENSED_ENGINEER_REVIEWED,
            reviewer_name="Jane Doe",
            # missing license_type and license_number
        )


# -----------------------------------------------------------------------------
# 7. Prohibited Claims Validator Tests
# -----------------------------------------------------------------------------

def test_prohibited_claims_validator_catches_violations():
    dirty_text_1 = "This software generates an official water forecast for city council."
    violations_1 = validate_report_text_against_prohibited_claims(dirty_text_1)
    assert len(violations_1) >= 1
    assert "official water forecast" in violations_1[0].lower()

    dirty_text_2 = "BASIN gives a guaranteed Day Zero date for municipal planning."
    violations_2 = validate_report_text_against_prohibited_claims(dirty_text_2)
    assert len(violations_2) >= 1
    assert "guaranteed day zero" in violations_2[0].lower()

    dirty_text_3 = "This engine replaces the TCEQ WAM Run 3 simulation model."
    violations_3 = validate_report_text_against_prohibited_claims(dirty_text_3)
    assert len(violations_3) >= 1
    assert "tceq wam" in violations_3[0].lower()

    dirty_text_4 = "In this analysis, scaling rainfall equals scaling drought severity."
    violations_4 = validate_report_text_against_prohibited_claims(dirty_text_4)
    assert len(violations_4) >= 1
    assert "scaling drought severity" in violations_4[0].lower()


def test_prohibited_claims_validator_passes_legitimate_scientific_text():
    clean_text = (
        "BASIN provides illustrative screening scenarios for comparative stress evaluation. "
        "Projected threshold crossings depend on configured assumptions and do not constitute "
        "official regulatory forecasts. Results should be reviewed by professional hydrologists."
    )
    violations = validate_report_text_against_prohibited_claims(clean_text)
    assert violations == []


# -----------------------------------------------------------------------------
# 8. Canonical Presets Invariant Verification
# -----------------------------------------------------------------------------

def test_canonical_region_n_presets_valid():
    # LCC contract checks
    assert LCC_EAC_CONTRACT.reservoir_name == "Lake Corpus Christi"
    assert LCC_EAC_CONTRACT.conservation_capacity_acft == 256339.0
    assert LCC_EAC_CONTRACT.dead_storage_acft == 75000.0

    # CCR contract checks
    assert CCR_EAC_CONTRACT.reservoir_name == "Choke Canyon Reservoir"
    assert CCR_EAC_CONTRACT.conservation_capacity_acft == 663400.0

    # Catchment weights sum to 1.0
    assert sum(sw.weight for sw in REGION_N_CATCHMENT_CONTRACT.station_weights) == pytest.approx(1.0)

    # Quad 811 covers 12 calendar months with realistic pan coefficient
    assert len(TWDB_QUAD_811_EVAP_CONTRACT.monthly_gross_pan_evap_inches) == 12
    assert 0.65 <= TWDB_QUAD_811_EVAP_CONTRACT.pan_coefficient <= 0.80
