"""Automated verification of rainfall percentage terminology (Task T2).

Tests:
1. Canonical formatting functions (format_retained_rainfall, format_rainfall_reduction, format_rainfall_dual_explanation).
2. Edge cases: 0%, 100%, fractional percentages (e.g. 37.5%), and multipliers > 1.0.
3. Parameter validation (rejecting negative, inf, nan).
4. Dual explanation (retained % + reduction complement).
5. Exporter and PDF report outputs: confirming no bare or ambiguous percentage labels remain.
6. Scientific contract prohibited claims validator catching isolated rainfall percentages.
"""
from __future__ import annotations

import math
import pytest

from basin_core.summary import (
    format_retained_rainfall,
    format_rainfall_reduction,
    format_rainfall_dual_explanation,
)
from basin_core.simulation import SimulationSettings, describe_input_rainfall
from basin_core.scientific_contract import validate_report_text_against_prohibited_claims
from basin_core.exporter import generate_brief
from basin_core.pdf_report import ExperimentConfig, render_html_report, build_fallback_pdf


# -----------------------------------------------------------------------------
# 1. Canonical Formatting Functions Unit Tests
# -----------------------------------------------------------------------------

def test_format_retained_rainfall():
    assert format_retained_rainfall(0.70) == "70% of observed rainfall"
    assert format_retained_rainfall(1.0) == "100% of observed rainfall"
    assert format_retained_rainfall(0.0) == "0% of observed rainfall"
    assert format_retained_rainfall(0.375) == "37.5% of observed rainfall"
    assert format_retained_rainfall(0.70, baseline="selected scenario rainfall") == "70% of selected scenario rainfall"
    assert format_retained_rainfall(70.0, is_fraction=False) == "70% of observed rainfall"
    assert format_retained_rainfall(37.5, is_fraction=False) == "37.5% of observed rainfall"


def test_format_rainfall_reduction():
    assert format_rainfall_reduction(0.30) == "30% reduction from observed rainfall"
    assert format_rainfall_reduction(0.0) == "0% reduction from observed rainfall"
    assert format_rainfall_reduction(1.0) == "100% reduction from observed rainfall"
    assert format_rainfall_reduction(0.625) == "62.5% reduction from observed rainfall"
    assert format_rainfall_reduction(0.30, baseline="input rainfall") == "30% reduction from input rainfall"
    assert format_rainfall_reduction(30.0, is_fraction=False) == "30% reduction from observed rainfall"


def test_format_rainfall_dual_explanation():
    # Standard retained with reduction complement
    assert format_rainfall_dual_explanation(0.70) == "70% of observed rainfall (30% reduction from observed rainfall)"
    assert format_rainfall_dual_explanation(70.0, is_fraction=False) == "70% of observed rainfall (30% reduction from observed rainfall)"
    
    # Boundary 100% (0% reduction)
    assert format_rainfall_dual_explanation(1.0) == "100% of observed rainfall (0% reduction)"
    assert format_rainfall_dual_explanation(100.0, is_fraction=False) == "100% of observed rainfall (0% reduction)"
    
    # Boundary 0% (100% reduction)
    assert format_rainfall_dual_explanation(0.0) == "0% of observed rainfall (100% reduction from observed rainfall)"
    assert format_rainfall_dual_explanation(0.0, is_fraction=False) == "0% of observed rainfall (100% reduction from observed rainfall)"
    
    # Fractional values
    assert format_rainfall_dual_explanation(0.375) == "37.5% of observed rainfall (62.5% reduction from observed rainfall)"
    
    # Increase (> 100%)
    assert format_rainfall_dual_explanation(1.10) == "110% of observed rainfall (10% increase over observed rainfall)"
    assert format_rainfall_dual_explanation(125.0, is_fraction=False) == "125% of observed rainfall (25% increase over observed rainfall)"
    
    # Custom baseline
    assert format_rainfall_dual_explanation(0.80, baseline="input rainfall") == "80% of input rainfall (20% reduction from input rainfall)"


def test_formatting_functions_reject_invalid_inputs():
    for fn in (format_retained_rainfall, format_rainfall_reduction, format_rainfall_dual_explanation):
        with pytest.raises(ValueError, match="finite non-negative number"):
            fn(-0.1)
        with pytest.raises(ValueError, match="finite non-negative number"):
            fn(float("nan"))
        with pytest.raises(ValueError, match="finite non-negative number"):
            fn(float("inf"))


# -----------------------------------------------------------------------------
# 2. Simulation and Provenance Output Checks
# -----------------------------------------------------------------------------

def test_describe_input_rainfall_includes_reduction_complement(workspace):
    scenario = workspace.get(workspace.selected[0])
    desc = describe_input_rainfall(scenario)
    assert "constructed at" in desc["summary"]
    assert "of observed rainfall" in desc["summary"]
    assert "reduction" in desc["summary"]


# -----------------------------------------------------------------------------
# 3. Exported Brief and PDF Report Terminology
# -----------------------------------------------------------------------------

def test_brief_table_and_conservation_use_retained_and_reduction(workspace):
    sid = workspace.selected[0]
    workspace.get(sid).review(True, "Accept for brief test")
    run = workspace.run_simulation(sid, SimulationSettings())
    workspace.review_simulation(run["id"], "Reviewed simulation")
    
    brief = generate_brief(workspace, [workspace.get(sid)])
    # Table header
    assert "| Retained rainfall (% of baseline) | Minimum storage | Final storage | At/below 20% |" in brief
    # Table rows
    assert "% retained (" in brief
    assert "% reduction)" in brief
    # Conservation comparison
    assert "% of observed rainfall (" in brief
    assert "% reduction from observed)" in brief


def test_pdf_report_spectrum_uses_retained_and_reduction(workspace):
    sid = workspace.selected[0]
    workspace.get(sid).review(True, "Accept for report test")
    accepted = [workspace.get(sid)]
    
    config = ExperimentConfig(selected=True, scenario_id=sid, scenario_revision=accepted[0].revision, tiers=(1.0, 0.5))
    html = render_html_report(workspace, accepted, config=config)
    
    assert "Retained Rainfall (% of input)" in html
    assert "50% of input rainfall (50% reduction)" in html


def test_tier_label_on_experiment_config():
    config = ExperimentConfig(tiers=(1.0, 0.8, 0.6, 0.4))
    assert config.tier_label == "100%, 80%, 60%, 40%"
    assert ("Rainfall retention tiers", "100%, 80%, 60%, 40%") in config.describe_rows()


# -----------------------------------------------------------------------------
# 4. Prohibited Claim Patterns for Isolated Rainfall Percentages
# -----------------------------------------------------------------------------

def test_prohibited_claims_rejects_isolated_rainfall_percentage():
    # Permitted explicit forms
    assert not validate_report_text_against_prohibited_claims("The scenario uses 70% of observed rainfall.")
    assert not validate_report_text_against_prohibited_claims("A 30% reduction from observed rainfall was applied.")
    assert not validate_report_text_against_prohibited_claims("Testing 70% retained rainfall.")
    assert not validate_report_text_against_prohibited_claims("Tested 80% rainfall tier.")
    assert not validate_report_text_against_prohibited_claims("Evaluated 90-day rainfall window.")

    # Prohibited bare/isolated forms
    v1 = validate_report_text_against_prohibited_claims("Simulation results under Rainfall: 70%.")
    assert len(v1) >= 1
    assert any("Rainfall percentage must state baseline" in msg for msg in v1)

    v2 = validate_report_text_against_prohibited_claims("This run uses a 70% rainfall model.")
    assert len(v2) >= 1
    assert any("Rainfall percentage must state baseline" in msg for msg in v2)
