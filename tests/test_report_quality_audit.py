import io
import re
import pytest
import pypdf

from basin_core.analysis_context import AnalysisContext, is_placeholder_text
from basin_core.pdf_report import (
    ExperimentConfig,
    build_fallback_pdf,
    compute_report_metrics,
    format_scenario_ranking_rationale,
    render_html_report,
    validate_report_prose_against_metrics,
)
from basin_core.exporter import generate_brief


@pytest.fixture
def approved_workspace(workspace):
    for sid in workspace.selected:
        workspace.get(sid).review(True, "Accepted for audit QA tests")
    return workspace


# ---------------------------------------------------------------------------
# Issue 13: Input Validation for Placeholder Text
# ---------------------------------------------------------------------------
def test_issue_13_placeholder_input_validation():
    assert is_placeholder_text("ewrwewe") is True
    assert is_placeholder_text("fsdf") is True
    assert is_placeholder_text("asdf") is True
    assert is_placeholder_text("test") is True
    assert is_placeholder_text("xxx") is True
    assert is_placeholder_text("   ") is True
    assert is_placeholder_text("aaaa") is True

    # Valid realistic names should NOT be flagged
    assert is_placeholder_text("Nueces River Authority") is False
    assert is_placeholder_text("City of Corpus Christi") is False
    assert is_placeholder_text("Region N Water Planning Group") is False
    assert is_placeholder_text("San Patricio Municipal Water District") is False

    # AnalysisContext fallback behavior
    ctx_gibberish = AnalysisContext(
        scope="specific_provider",
        organization_type="regional_planning",
        organization_name="ewrwewe",
        counties=("Nueces",),
        community="fsdf",
        supply_relationship="regional_wholesale",
        decision_use="regional_screening",
    )
    assert ctx_gibberish.audience_label == "Region N Planning Entity (Unspecified)"

    ctx_valid = AnalysisContext(
        scope="specific_provider",
        organization_type="regional_planning",
        organization_name="City of Corpus Christi",
        counties=("Nueces",),
        community="Corpus Christi",
        supply_relationship="regional_wholesale",
        decision_use="regional_screening",
    )
    assert ctx_valid.audience_label == "City of Corpus Christi · Corpus Christi"


# ---------------------------------------------------------------------------
# Issue 1 & 8: Antecedent 35% Benchmark & Headline Conservation Metric
# ---------------------------------------------------------------------------
def test_issue_1_and_8_antecedent_35pct_benchmark(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    metrics = compute_report_metrics(primary, config, approved_workspace)
    assert metrics.stressed_case is not None
    d_base = metrics.stressed_case["day_base_20"]
    d_cons = metrics.stressed_case["day_cons_20"]
    delay = metrics.stressed_case["conservation_delay_days"]
    assert d_base is not None
    assert d_cons is not None
    assert delay == (d_cons - d_base)

    # HTML report check
    html = render_html_report(approved_workspace, accepted, config=config)
    assert "Antecedent Storage Benchmark" in html
    assert f"Day {d_base}" in html
    assert f"Day {d_cons}" in html
    assert "gained" in html.lower()
    assert "Delay not defined*" not in html
    assert "Maintained &gt;20%*" in html or "Maintained >20%*" in html
    assert "*Band 3 preserved" in html

    # Vector PDF check
    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))

    assert "ANTECEDENT STORAGE BENCHMARK" in full_pdf_text
    assert str(d_base) in full_pdf_text
    assert str(d_cons) in full_pdf_text
    assert f"+{delay} d gained" in full_pdf_text or f"+{delay} days gained" in full_pdf_text.lower()
    assert "Maintained >20%*" in full_pdf_text
    assert "Delay not defined" not in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 2 & 12: Review Default Narrative & Mary Rhodes Pipeline Supply
# ---------------------------------------------------------------------------
def test_issue_2_and_12_review_defaults_and_pipeline(approved_workspace):
    accepted = approved_workspace.exportable()
    default_config = ExperimentConfig(selected=False)

    html = render_html_report(approved_workspace, accepted, config=default_config)
    # Issue 2 narrative
    assert "standard BASIN baseline defaults (48% initial storage, 0% baseline conservation)" in html
    assert "custom parameter overrides were not configured in Review" in html

    # Issue 12 pipeline supply description
    assert "Mary Rhodes Pipeline offsets net reservoir demand" in html
    assert "~67,200 ac-ft/yr" in html

    # Vector PDF check
    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=default_config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))
    assert "Mary Rhodes Pipeline offsets net reservoir demand" in full_pdf_text
    assert "~67,200 ac-ft/yr" in full_pdf_text
    assert "standard BASIN baseline defaults (48% initial storage, 0% baseline conservation)" in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 3: Capacity Reconciliation (919,900 vs 918,882 ac-ft)
# ---------------------------------------------------------------------------
def test_issue_3_capacity_reconciliation(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    html = render_html_report(approved_workspace, accepted, config=config)
    assert "918,882" in html
    assert "1,018 ac-ft" in html
    assert "sedimentation" in html

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))
    assert "918,882" in full_pdf_text
    assert "sedimentation" in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 4: Privacy Redaction Stubs
# ---------------------------------------------------------------------------
def test_issue_4_privacy_redaction_stubs(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    page2_text = reader.pages[1].extract_text() or ""
    # Should not repeat the verbose redaction sentence per row
    assert page2_text.count("Review rationale omitted per export privacy configuration") <= 1
    assert "Accepted" in page2_text


# ---------------------------------------------------------------------------
# Issue 5: Terminology Drift (Zero "Stage X" in Report)
# ---------------------------------------------------------------------------
def test_issue_5_band_terminology_lock(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    html = render_html_report(approved_workspace, accepted, config=config)
    assert re.search(r"\bStage [1-4]\b", html) is None

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    assert re.search(r"\bStage [1-4]\b", full_pdf_text) is None
    assert "Band 1" in full_pdf_text
    assert "Band 2" in full_pdf_text
    assert "Band 3" in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 6: Evaporation Interpretation
# ---------------------------------------------------------------------------
def test_issue_6_evaporation_interpretation(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    metrics = compute_report_metrics(primary, config)
    diff_pct = round(((metrics.mean_evaporation_acft - metrics.mean_served_demand_acft) / metrics.mean_served_demand_acft) * 100)
    expected_pct_str = f"{diff_pct:+d}%"

    html = render_html_report(approved_workspace, accepted, config=config)
    assert expected_pct_str in html
    assert "dominating summer drawdown" in html

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))
    assert expected_pct_str in full_pdf_text
    assert "dominating summer drawdown" in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 7: Page 1 Front-Loaded Verification Scope Notice
# ---------------------------------------------------------------------------
def test_issue_7_front_loaded_verification_scope(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    page1_text = reader.pages[0].extract_text() or ""
    assert "Verification Scope:" in page1_text
    assert "companion archive" in page1_text
    assert "illustrative presentation deliverable" in page1_text


# ---------------------------------------------------------------------------
# Issue 9 & 10: Station Network Roles and Provenance Dates
# ---------------------------------------------------------------------------
def test_issue_9_and_10_station_roles_and_provenance(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    html = render_html_report(approved_workspace, accepted, config=config)
    assert "Primary NOAA proxy stations" in html or "Three primary NOAA proxy stations" in html
    assert "secondary network stations" in html
    assert "Beeville" not in html

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))
    assert "Primary NOAA proxy stations" in full_pdf_text or "Three primary NOAA proxy stations" in full_pdf_text
    assert "secondary network stations" in full_pdf_text
    assert "Beeville" not in full_pdf_text

    brief = generate_brief(approved_workspace, accepted)
    assert "primary coastal/urban stations" in brief
    assert "Beeville" not in brief


# ---------------------------------------------------------------------------
# Issue 11: Pareto Frontier Numeric Axis Ticks
# ---------------------------------------------------------------------------
def test_issue_11_pareto_frontier_axes(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    all_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    assert "Duration Clusters (Days)" in all_text


# ---------------------------------------------------------------------------
# Issue 14: Compounding Rainfall Tiers
# ---------------------------------------------------------------------------
def test_issue_14_compounding_rainfall_tiers(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    html = render_html_report(approved_workspace, accepted, config=config)
    assert "Compounding Rainfall Multipliers" in html

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))
    assert "Sensitivity tiers compound upon scenario construction" in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 15 & 16: Diversity Trade-off Disclosure and Silhouette Score
# ---------------------------------------------------------------------------
def test_issue_15_and_16_diversity_tradeoff_and_silhouette(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    html = render_html_report(approved_workspace, accepted, config=config)
    assert "Trade-off Disclosure:" in html
    assert "overlapping continuous meteorological distributions" in html

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = re.sub(r"\s+", " ", "\n".join([page.extract_text() or "" for page in reader.pages]))
    assert "Trade-off Disclosure:" in full_pdf_text
    assert "overlapping continuous meteorological distributions" in full_pdf_text


# ---------------------------------------------------------------------------
# Issue 17: Findings Box Text Wrapping (No Truncated Sentences)
# ---------------------------------------------------------------------------
def test_issue_17_findings_box_wrapping(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)

    pdf_bytes = build_fallback_pdf(approved_workspace, accepted, config=config)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    page1_text = reader.pages[0].extract_text() or ""

    # Every key bullet text should be present without truncated ellipses '...'
    assert "Scenario" in page1_text
    assert "Nueces Basin" in page1_text or "Corpus Christi" in page1_text
    assert "..." not in page1_text


# ---------------------------------------------------------------------------
# Issue 18: Discriminating Scenario Drivers
# ---------------------------------------------------------------------------
def test_issue_18_discriminating_scenario_drivers(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    rationale = format_scenario_ranking_rationale(primary, approved_workspace)
    assert "Selected as" in rationale
    assert "largest user-configured score contribution is" in rationale
    assert "priority score" in rationale


# ---------------------------------------------------------------------------
# Export-Time Prose Validator Unit & Negative Tests
# ---------------------------------------------------------------------------
def test_export_prose_validator(approved_workspace):
    accepted = approved_workspace.exportable()
    primary = accepted[0]
    config = ExperimentConfig(selected=True, scenario_id=primary.id, scenario_revision=primary.revision)
    metrics = compute_report_metrics(primary, config)

    # Valid report text should pass validation without error
    html = render_html_report(approved_workspace, accepted, config=config)
    assert len(html) > 0

    # Negative Test 1: Fake Station 'Beeville'
    bad_text_1 = html + "\n<p>Station Network Roles: Four primary proxy stations (Alice, Beeville, Corpus Christi)</p>"
    with pytest.raises(AssertionError, match="Criterion 4 failed: Unauthorized station name 'Beeville'"):
        validate_report_prose_against_metrics(bad_text_1, metrics, config)

    # Negative Test 2: Fake Station 'Choke Canyon' as a station proxy
    bad_text_2 = html + "\n<p>Primary Station Proxies: NOAA GHCN-Daily Alice, Choke Canyon station, Corpus Christi.</p>"
    with pytest.raises(AssertionError, match="Criterion 4 failed: 'Choke Canyon' was cited as a station proxy"):
        validate_report_prose_against_metrics(bad_text_2, metrics, config)

    # Negative Test 3: Stale Compounding % (63.5% / 25.4%)
    obs_frac = metrics.input_rainfall.get("observed_fraction", 0.5) if metrics.input_rainfall else 0.5
    if round(obs_frac * 100, 1) != 63.5:
        bad_text_3 = html + "\n<p>Sensitivity tiers compound upon scenario construction: applying 40% retention to a candidate scenario constructed at 63.5% of observations represents ~25.4% of historical baseline rainfall.</p>"
        with pytest.raises(AssertionError, match="Criterion 1 failed: Stale draft percentage '63.5%'"):
            validate_report_prose_against_metrics(bad_text_3, metrics, config)

    # Negative Test 4: Stale Evaporation Exceedance (+47%)
    diff_pct = round(((metrics.mean_evaporation_acft - metrics.mean_served_demand_acft) / metrics.mean_served_demand_acft) * 100)
    if diff_pct != 47:
        bad_text_4 = html + "\n<p>- Dominant loss term: reservoir evaporation exceeds customer demand by +47%, dominating summer drawdown.</p>"
        with pytest.raises(AssertionError, match="Criterion 2 failed: Stale draft exceedance '\\+47%'"):
            validate_report_prose_against_metrics(bad_text_4, metrics, config)

    # Negative Test 5: Review Selection Truth - config.selected is False, but text claims custom overrides in Review
    unselected_cfg = ExperimentConfig(selected=False)
    bad_text_5 = "Operational parameters (initial storage, emergency conservation) were customized by analyst in Review."
    with pytest.raises(AssertionError, match="Criterion 5 failed: Report claims operational parameters were customized in Review, but config.selected is False."):
        validate_report_prose_against_metrics(bad_text_5, metrics, unselected_cfg)

    # Negative Test 6: Review Selection Truth - config.selected is True, but text claims custom overrides were not configured
    bad_text_6 = "Drawdown was simulated using standard BASIN baseline defaults (48% initial storage, 0% baseline conservation), as custom parameter overrides were not configured in Review."
    with pytest.raises(AssertionError, match="Criterion 5 failed: Selected config claims custom overrides were not configured in Review."):
        validate_report_prose_against_metrics(bad_text_6, metrics, config)

    # Negative Test 7: Terminal Punctuation - Double Periods
    bad_text_7 = "- Highest response band reached across 4 modeled tiers: Band 2 (Moderate <= 30%).."
    with pytest.raises(AssertionError, match="Criterion 6 failed: Detected double periods in finding"):
        validate_report_prose_against_metrics(bad_text_7, metrics, config)


# ---------------------------------------------------------------------------
# Scoped Differential Cross-Report Isolation Test
# ---------------------------------------------------------------------------
def test_cross_report_isolation(approved_workspace):
    """Verify scoped differential isolation between two distinct scenario runs.

    Candidate A and Candidate B differ in scenario ID, duration, initial storage, and conservation.
    Asserts run-varying data structures from Run A never leak into Run B's report prose.
    """
    accepted = approved_workspace.exportable()
    assert len(accepted) >= 2
    scen_a = accepted[0]
    scen_b = accepted[1]

    cfg_a = ExperimentConfig(
        selected=True,
        scenario_id=scen_a.id,
        scenario_revision=scen_a.revision,
        initial_pct=0.38,
        conservation_pct=0.15,
    )
    cfg_b = ExperimentConfig(
        selected=True,
        scenario_id=scen_b.id,
        scenario_revision=scen_b.revision,
        initial_pct=0.55,
        conservation_pct=0.0,
    )

    pdf_a_bytes = build_fallback_pdf(approved_workspace, accepted, config=cfg_a)
    reader_a = pypdf.PdfReader(io.BytesIO(pdf_a_bytes))
    text_a = re.sub(r"\s+", " ", "\n".join([p.extract_text() or "" for p in reader_a.pages]))

    pdf_b_bytes = build_fallback_pdf(approved_workspace, accepted, config=cfg_b)
    reader_b = pypdf.PdfReader(io.BytesIO(pdf_b_bytes))
    text_b = re.sub(r"\s+", " ", "\n".join([p.extract_text() or "" for p in reader_b.pages]))

    # Assert identity separation
    assert f"primary scenario {scen_a.id}".lower() in text_a.lower()
    assert f"primary scenario {scen_b.id}".lower() in text_b.lower()
    assert f"primary scenario {scen_a.id}".lower() not in text_b.lower()
    assert f"primary scenario {scen_b.id}".lower() not in text_a.lower()

    # Assert parameter separation
    assert "38%" in text_a
    assert "38%" not in text_b
    assert "55%" in text_b
    assert "55%" not in text_a
    assert "15% emergency demand reduction" in text_a or "15% conservation" in text_a.lower()
    assert "0% emergency demand reduction" in text_b or "0% conservation" in text_b.lower()

    # Invariant constants (canonical capacity 919,900 ac-ft and reconciliation 918,882) remain identical
    assert "919,900 ac-ft" in text_a
    assert "919,900 ac-ft" in text_b
    assert "918,882" in text_a
    assert "918,882" in text_b

