import pandas as pd
import pytest

from basin_core.analysis import RESERVOIR_ASSUMPTIONS, simulate_reservoir_drawdown
from basin_core.pdf_report import (
    ILLUSTRATIVE_BANDS,
    UNAVAILABLE,
    band_storage_acft,
    build_fallback_pdf,
    compute_report_metrics,
    find_browser_executable,
    generate_pdf_report,
    model_total_capacity_acft,
    render_html_report,
)

# Values the report used to hard-code or substitute. None of them may reappear in output.
FABRICATED_VECTOR_STRINGS = [
    b"963,600",          # capacity that never matched the model's 919,900
    b"385,440", b"289,080", b"192,720",   # bands derived from that wrong capacity
    b"AUDIT-CERTIFIED", b"f9a1b2c3d4e5f6a7",
    b"~4-5 Months", b"+32 Days Gained", b"1,280 ac-ft",
    b"Tier 1: Full Inflow", b"Tier 3: 60% Retained",
    b"350,718", b"271,735", b"187,884", b"135,868",
]

# Wording that implied the PDF itself had been independently verified.
UNVERIFIED_CLAIM_STRINGS = [
    b"VERIFIED 256",
    b"DATA PASS",
    b"CRYPTOGRAPHIC AUDIT VERIFICATION",
    b"certified unaltered",
    b"Verified Export Bundle Companion",
    b"All candidate deficits match recomputed zero-fill sums",
]

# Policy and benefit assertions that no source in this repository supports.
UNSUPPORTED_POLICY_STRINGS = [
    b"City Code Ch. 55",
    b"Approved 2025 Revision",
    b"Approved June 2026 Revision",
    b"MGD",
    b"MANDATED ACTIONS",
    b"Hydrologist Note",
    b"669,186",
    b"256,339",
]


@pytest.fixture
def approved(workspace):
    """An isolated reviewed workspace built from the fixture, not a saved local session."""
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "Accepted for unit test")
    return workspace


class _SeriesLessScenario:
    """Stands in for an accepted scenario whose daily rainfall series is missing."""

    id = "SCN-EMPTY"
    revision = 1
    provenance: dict = {}
    features: dict = {}
    history: list = []
    series = pd.DataFrame()


def test_fallback_pdf_generation():
    pdf_bytes = build_fallback_pdf("Test Title", "Test Content")
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"BASIN EXECUTIVE TECHNICAL BRIEF" in pdf_bytes
    assert b"WARNING: WHAT THIS ARTIFACT IS NOT" in pdf_bytes
    # Title/body mode has no session, so it must say so rather than show example figures.
    assert UNAVAILABLE.encode() in pdf_bytes
    assert len(pdf_bytes) > 500


def test_render_html_report(approved):
    accepted = approved.exportable()

    html = render_html_report(approved, accepted)
    assert "BASIN · EXECUTIVE TECHNICAL BRIEF" in html
    assert "WHAT THIS DOCUMENT IS NOT" in html
    assert "The Bottom Line — Executive Overview" in html
    assert "Illustrative Drought Response Reference Framework" in html
    assert "Illustrative Storage Sensitivity Spectrum (Non-Predictive)" in html
    assert "Illustrative Depletion Window" in html
    assert "badge-danger" not in html
    assert "Provenance & Verification Scope" in html
    assert approved.id in html
    assert "omitted: export privacy setting excludes private notes" in html
    assert "Accepted for unit test" not in html

    html_with_notes = render_html_report(approved, accepted, include_notes=True)
    assert "Accepted for unit test" in html_with_notes


def test_generate_pdf_report(approved, tmp_path):
    accepted = approved.exportable()
    target_pdf = tmp_path / f"BASIN-Executive-Brief-{approved.id}.pdf"
    pdf_bytes = generate_pdf_report(approved, accepted, output_path=target_pdf)

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000
    assert target_pdf.exists()
    assert target_pdf.stat().st_size == len(pdf_bytes)


# --------------------------------------------------------------------------------------
# Model-derived capacity
# --------------------------------------------------------------------------------------

def test_declared_capacities_match_the_simulator():
    """The assumptions dict the report reads must match what the simulator actually uses."""
    series = pd.DataFrame({"s": [0.0] * 3}, index=pd.date_range("2001-01-01", periods=3))
    full = simulate_reservoir_drawdown(series, initial_pct=1.0)
    # Day 1 beginning storage is the pools at 100%, before any inflow or loss is applied.
    assert full.iloc[0].beginning_acft == pytest.approx(model_total_capacity_acft())
    assert model_total_capacity_acft() == pytest.approx(919900.0)


@pytest.mark.parametrize("initial_pct, expected_band", [(0.50, 0), (0.35, 1), (0.25, 2), (0.18, 3), (0.10, 4)])
def test_illustrative_bands_match_the_simulator(initial_pct, expected_band):
    """The band table the report prints must match the bands the model assigns."""
    series = pd.DataFrame({"s": [0.0]}, index=pd.date_range("2001-01-01", periods=1))
    sim = simulate_reservoir_drawdown(series, initial_pct=initial_pct)
    assert int(sim.iloc[0].stage_num) == expected_band
    assert [f for f, _ in ILLUSTRATIVE_BANDS] == [0.40, 0.30, 0.20, 0.15]


def test_band_volumes_are_derived_from_total_capacity():
    for fraction, _ in ILLUSTRATIVE_BANDS:
        assert band_storage_acft(fraction) == pytest.approx(model_total_capacity_acft() * fraction)
    assert band_storage_acft(0.40) == pytest.approx(367960.0)
    assert band_storage_acft(0.20) == pytest.approx(183980.0)


def test_reports_follow_the_model_assumptions_when_they_change(approved, monkeypatch):
    """Capacity must be read from the model, not restated in the report as a constant."""
    monkeypatch.setitem(
        RESERVOIR_ASSUMPTIONS, "capacities_acft", {"Pool A": 100000.0, "Pool B": 400000.0}
    )
    accepted = approved.exportable()

    html = render_html_report(approved, accepted)
    assert "500,000 ac-ft" in html
    assert "919,900" not in html

    pdf_bytes = build_fallback_pdf(approved, accepted)
    assert b"500,000" in pdf_bytes
    assert b"200,000" in pdf_bytes  # the 40% band of the patched capacity
    assert b"919,900" not in pdf_bytes


def test_no_stale_capacity_constants_in_either_path(approved):
    accepted = approved.exportable()
    html = render_html_report(approved, accepted)
    pdf_bytes = build_fallback_pdf(approved, accepted)

    assert "919,900 ac-ft" in html
    assert b"919,900" in pdf_bytes
    for stale in FABRICATED_VECTOR_STRINGS:
        assert stale not in pdf_bytes, stale
        assert stale.decode() not in html, stale


# --------------------------------------------------------------------------------------
# Missing simulation data
# --------------------------------------------------------------------------------------

def test_metrics_report_why_the_simulation_is_unavailable():
    assert compute_report_metrics(None, 0.48, 0.15).unavailable_reason == "no accepted scenario was supplied"
    empty = compute_report_metrics(_SeriesLessScenario(), 0.48, 0.15)
    assert not empty.available
    assert "no daily rainfall series" in empty.unavailable_reason
    assert empty.spectrum_data is None


def test_simulation_failure_is_reported_not_substituted(approved, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("simulation exploded")

    monkeypatch.setattr("basin_core.pdf_report.simulate_stress_spectrum", boom)
    accepted = approved.exportable()

    metrics = compute_report_metrics(accepted[0], 0.48, 0.15)
    assert metrics.unavailable_reason == "the simulation raised RuntimeError"

    pdf_bytes = build_fallback_pdf(approved, accepted)
    assert b"STRESS SPECTRUM NOT COMPUTED FOR THIS REPORT" in pdf_bytes
    assert UNAVAILABLE.encode() in pdf_bytes
    for stale in FABRICATED_VECTOR_STRINGS:
        assert stale not in pdf_bytes, stale

    html = render_html_report(approved, accepted)
    assert "Simulation unavailable" in html
    assert UNAVAILABLE in html


@pytest.mark.parametrize("accepted", [[], [_SeriesLessScenario()]])
def test_missing_simulation_shows_explicit_unavailable_state(approved, accepted):
    pdf_bytes = build_fallback_pdf(approved, accepted)
    assert b"STRESS SPECTRUM NOT COMPUTED FOR THIS REPORT" in pdf_bytes
    assert UNAVAILABLE.encode() in pdf_bytes
    for stale in FABRICATED_VECTOR_STRINGS:
        assert stale not in pdf_bytes, stale

    html = render_html_report(approved, accepted)
    assert "Simulation unavailable" in html
    assert "No substitute figures are shown." in html
    # Captions and narrative must not describe a run that did not happen.
    assert "no run was produced for this report" in html
    assert "Derived using primary scenario" not in html
    assert "First tier breaching Stage 3 in sim" not in html


def test_settings_are_not_described_as_tested_when_nothing_ran(approved):
    """Settings echoed back must not imply a simulation was performed with them."""
    assert b"nothing was simulated" in build_fallback_pdf(approved, [])
    assert b"Tested under initial storage" not in build_fallback_pdf(approved, [])
    assert b"Tested under initial storage" in build_fallback_pdf(approved, approved.exportable())


# --------------------------------------------------------------------------------------
# Truthful verification wording
# --------------------------------------------------------------------------------------

def test_vector_report_scopes_verification_to_the_bundle(approved):
    pdf_bytes = build_fallback_pdf(approved, approved.exportable())

    assert b"PROVENANCE AND VERIFICATION SCOPE" in pdf_bytes
    assert b"PDF NOT VERIFIED" in pdf_bytes
    assert b"BUNDLE ONLY" in pdf_bytes
    assert b"outside the bundle verification contract" in pdf_bytes
    assert b"No scientific validation or professional approval is claimed" in pdf_bytes
    for claim in UNVERIFIED_CLAIM_STRINGS:
        assert claim not in pdf_bytes, claim


def test_html_report_scopes_verification_to_the_bundle(approved):
    html = render_html_report(approved, approved.exportable())

    assert "this PDF is outside that contract" in html
    assert "establishes nothing about the figures or wording on these pages" in html
    assert "No scientific validation or professional approval is claimed or implied." in html
    for claim in UNVERIFIED_CLAIM_STRINGS:
        assert claim.decode() not in html, claim


def test_reports_do_not_assert_unsupported_policy_or_benefits(approved):
    accepted = approved.exportable()
    html = render_html_report(approved, accepted)
    pdf_bytes = build_fallback_pdf(approved, accepted)

    for claim in UNSUPPORTED_POLICY_STRINGS:
        assert claim not in pdf_bytes, claim
        assert claim.decode() not in html, claim

    # Illustrative bands and sourced survey figures must be distinguishable.
    assert b"NOT ADOPTED POLICY" in pdf_bytes
    assert "not adopted policy" in html
    assert "918,882 ac-ft" in html          # TWDB figures recorded in the research packet
    assert "not a survey-verified figure" in html


def test_private_notes_stay_opt_in_in_the_vector_path(approved):
    for identifier in approved.selected:
        approved.get(identifier).review(True, "PRIVATE-SENTINEL")
    accepted = approved.exportable()

    assert b"PRIVATE-SENTINEL" not in build_fallback_pdf(approved, accepted)
    assert b"PRIVATE-SENTINEL" in build_fallback_pdf(approved, accepted, include_notes=True)
    assert "PRIVATE-SENTINEL" not in render_html_report(approved, accepted)
    assert "PRIVATE-SENTINEL" in render_html_report(approved, accepted, include_notes=True)


def test_find_browser_executable_returns_path_or_none():
    found = find_browser_executable()
    assert found is None or isinstance(found, str)


def test_short_unbreached_window_does_not_claim_six_months(approved):
    accepted = approved.exportable()
    primary = accepted[0]
    original = primary.series
    try:
        primary.series = original.iloc[:30].copy()
        html = render_html_report(approved, accepted, initial_pct=1.0)
        pdf = build_fallback_pdf(approved, accepted, initial_pct=1.0)
        assert 'No breach in modeled window' in html
        assert b'No breach in window' in pdf
        assert '>6 Mo' not in html and b'>6 Mo' not in pdf
    finally:
        primary.series = original
