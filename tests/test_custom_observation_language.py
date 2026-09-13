"""Automated verification of custom-observation source and date language (Task T3).

Tests:
1. Source identity language formatting (format_custom_source_label).
2. Record coverage date range formatting (format_custom_coverage_dates).
3. Catchment disclaimer constant (CUSTOM_CATCHMENT_DISCLAIMER).
4. Prohibited claims validation rejecting assertions of official/verified/certified status for custom data.
5. Backward compatibility with legacy saved evidence records while enforcing new canonical format.
6. RainfallPreview helper properties (source_label, coverage_label).
7. Exporter brief custom evidence section includes unverified source language, date bounds, and catchment disclaimer.
"""
from __future__ import annotations

import pytest

from basin_core.custom_data import (
    CUSTOM_CATCHMENT_DISCLAIMER,
    format_custom_source_label,
    format_custom_coverage_dates,
    evidence_record,
    _legacy_evidence_record,
    validate_links,
)
from basin_core.uploads import preview_rainfall
from basin_core.scientific_contract import validate_report_text_against_prohibited_claims
from basin_core.exporter import generate_brief
from tests.test_custom_data import accept_all, attach


# -----------------------------------------------------------------------------
# 1. Source Identity Formatting
# -----------------------------------------------------------------------------

def test_format_custom_source_label():
    # Both station and provider
    assert format_custom_source_label("Oso Bay Gauge", "Nueces River Authority") == (
        "User-provided dataset 'Oso Bay Gauge' by 'Nueces River Authority' (unverified)"
    )
    # Station only
    assert format_custom_source_label("Oso Bay Gauge") == (
        "User-provided dataset 'Oso Bay Gauge' (unverified)"
    )
    # Provider only
    assert format_custom_source_label(None, "Nueces River Authority") == (
        "User-provided dataset by 'Nueces River Authority' (unverified)"
    )
    # Empty / None
    assert format_custom_source_label(None, None) == "User-provided dataset (unverified)"
    assert format_custom_source_label("", "   ") == "User-provided dataset (unverified)"
    # Whitespace stripping
    assert format_custom_source_label("  Station 1  ", "  City Dept  ") == (
        "User-provided dataset 'Station 1' by 'City Dept' (unverified)"
    )


# -----------------------------------------------------------------------------
# 2. Record Coverage Date Formatting
# -----------------------------------------------------------------------------

def test_format_custom_coverage_dates():
    # Bounded range with count
    assert format_custom_coverage_dates("2024-01-01", "2024-01-31", 31) == (
        "Coverage: 2024-01-01 to 2024-01-31 (31 daily records)."
    )
    # Bounded range with 1 record count
    assert format_custom_coverage_dates("2024-01-01", "2024-01-02", 1) == (
        "Coverage: 2024-01-01 to 2024-01-02 (1 record)."
    )
    # Bounded range without count
    assert format_custom_coverage_dates("2024-01-01", "2024-01-31") == (
        "Coverage: 2024-01-01 to 2024-01-31."
    )
    # Single date
    assert format_custom_coverage_dates("2024-01-01", "2024-01-01") == (
        "Coverage: Single date 2024-01-01 (1 record)."
    )
    assert format_custom_coverage_dates("2024-01-01", "2024-01-01", 1) == (
        "Coverage: Single date 2024-01-01 (1 record)."
    )
    # Missing / None
    assert format_custom_coverage_dates(None, None) == "Coverage: Date range unavailable."
    assert format_custom_coverage_dates("None", "2024-01-01") == "Coverage: Date range unavailable."
    assert format_custom_coverage_dates("", "") == "Coverage: Date range unavailable."


# -----------------------------------------------------------------------------
# 3. Disclaimer Constant
# -----------------------------------------------------------------------------

def test_custom_catchment_disclaimer_content():
    assert CUSTOM_CATCHMENT_DISCLAIMER == "Custom data represents unverified local observations, not a calibrated catchment model."


# -----------------------------------------------------------------------------
# 4. Prohibited Claims Enforcement
# -----------------------------------------------------------------------------

def test_prohibited_claims_rejects_unsupported_status_assertions():
    bad_texts = [
        "This is an official station for Corpus Christi water supply.",
        "Data obtained from a verified source.",
        "Using certified data to project municipal shortages.",
        "Custom rainfall record verified by noaa for calibration.",
        "The sensor network is certified by usgs standards.",
    ]
    for text in bad_texts:
        violations = validate_report_text_against_prohibited_claims(text)
        assert len(violations) > 0, f"Expected prohibited claim violation for: {text}"
        assert any("official, verified, or certified" in v for v in violations)


def test_compliant_custom_language_passes_prohibited_claims():
    good_text = (
        f"Source: User-provided dataset 'Local Gauge A' (unverified). "
        f"Coverage: 2024-01-01 to 2024-03-31 (90 daily records). "
        f"{CUSTOM_CATCHMENT_DISCLAIMER}"
    )
    violations = validate_report_text_against_prohibited_claims(good_text)
    assert violations == [], f"Unexpected violations for compliant text: {violations}"


# -----------------------------------------------------------------------------
# 5. RainfallPreview Property Helpers
# -----------------------------------------------------------------------------

def test_rainfall_preview_properties():
    csv_bytes = b"date,precipitation\n2024-01-01,5.0\n2024-01-02,0.0\n2024-01-03,12.5\n"
    preview = preview_rainfall(csv_bytes, "City Tank Gauge", "Corpus Christi", "mm")
    assert preview.source_label == "User-provided dataset 'City Tank Gauge' (unverified)"
    assert preview.coverage_label == "Coverage: 2024-01-01 to 2024-01-03 (3 daily records)."


# -----------------------------------------------------------------------------
# 6. Backward Compatibility & Link Validation
# -----------------------------------------------------------------------------

def test_backward_compatibility_with_legacy_evidence_record(workspace):
    from copy import deepcopy

    attach(workspace)
    record = workspace.custom_uploads[0]
    
    # New evidence record matches current evidence_record function
    current_rec = evidence_record(record)
    assert "User-provided dataset" in current_rec["title"]
    assert CUSTOM_CATCHMENT_DISCLAIMER in current_rec["description"]
    assert "Coverage: " in current_rec["description"]

    # Legacy evidence record matches old format
    legacy_rec = _legacy_evidence_record(record)
    assert legacy_rec["title"] == "Custom rainfall comparison: " + record["station"]
    assert "User-provided dataset" not in legacy_rec["title"]

    # validate_links should succeed with both current and legacy evidence records
    # 1. With current record
    validate_links(workspace.custom_uploads, workspace.evidence_refs, [current_rec], workspace.scenarios)

    # 2. With legacy record (backward compatibility)
    validate_links(workspace.custom_uploads, workspace.evidence_refs, [legacy_rec], workspace.scenarios)

    # 3. Tampered record fails
    tampered_rec = deepcopy(legacy_rec)
    tampered_rec["description"] = "Tampered description"
    with pytest.raises(ValueError, match="Custom evidence description differs from saved data"):
        validate_links(workspace.custom_uploads, workspace.evidence_refs, [tampered_rec], workspace.scenarios)


# -----------------------------------------------------------------------------
# 7. Exporter Brief Verification
# -----------------------------------------------------------------------------

def test_exporter_brief_contains_custom_observation_language(workspace):
    attach(workspace)
    accept_all(workspace)
    brief = generate_brief(workspace, workspace.exportable())
    
    assert "## Custom rainfall evidence" in brief
    assert CUSTOM_CATCHMENT_DISCLAIMER in brief
    assert "User-provided dataset" in brief
    assert "Coverage:" in brief
    assert "(unverified)" in brief
