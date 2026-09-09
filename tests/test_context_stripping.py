import io
import zipfile
import pandas as pd
import pytest

from basin_core.exporter import export_bundle, generate_brief
from basin_core.pdf_report import render_html_report, build_fallback_pdf


@pytest.fixture
def approved_workspace(workspace):
    for sid in workspace.selected:
        workspace.get(sid).review(True, "Approved for context stripping test")
    return workspace


def test_shortlist_csv_self_disclaims(approved_workspace):
    """Verify that shortlist.csv contains a dedicated modeling_scope column

    so that if the CSV is opened in Excel or emailed without context,
    it remains self-disclaiming.
    """
    bundle_bytes = export_bundle(approved_workspace)
    with zipfile.ZipFile(io.BytesIO(bundle_bytes)) as archive:
        csv_bytes = archive.read("shortlist.csv")
    
    df = pd.read_csv(io.BytesIO(csv_bytes))
    assert "modeling_scope" in df.columns
    for val in df["modeling_scope"]:
        assert "NOT_A_YIELD_FORECAST" in str(val)
        assert "HISTORICAL_PRECIP_DEFICIT_ONLY" in str(val)


def test_handoff_brief_has_top_non_predictive_banner(approved_workspace):
    """Verify that Hydrologist_Handoff_Brief.md begins with a prominent

    warning banner establishing what the artifact is NOT.
    """
    accepted = approved_workspace.exportable()
    brief_md = generate_brief(approved_workspace, accepted)
    lines = [line.strip() for line in brief_md.splitlines() if line.strip()]
    
    assert lines[0].startswith("> ⚠️ **WHAT THIS ARTIFACT IS NOT:**")
    assert "NOT a hydrologic drought-of-record analysis" in lines[0]
    assert "NOT a safe-yield or delivery forecast" in lines[0]
    assert "NOT validated against actual streamflow" in lines[0]


def test_bundle_readme_has_prominent_warning(approved_workspace):
    """Verify that README.txt in the ZIP bundle begins with a prominent

    warning header.
    """
    bundle_bytes = export_bundle(approved_workspace)
    with zipfile.ZipFile(io.BytesIO(bundle_bytes)) as archive:
        readme_txt = archive.read("README.txt").decode("utf-8")
    
    assert "WARNING: WHAT THIS ARTIFACT IS NOT" in readme_txt
    assert "- NOT a hydrologic drought-of-record analysis" in readme_txt
    assert "- NOT a safe-yield, firm-yield, or delivery forecast" in readme_txt


def test_html_and_fallback_pdf_contain_no_alarmist_styling(approved_workspace):
    """Verify that HTML executive report contains no .badge-danger or .danger styling,

    maintains 11pt/8-9pt neutral KPI styling, and includes universal non-predictive banners.
    """
    accepted = approved_workspace.exportable()
    html = render_html_report(approved_workspace, accepted)
    
    assert "badge-danger" not in html
    assert ".kpi-card.danger" not in html
    assert "WHAT THIS DOCUMENT IS NOT" in html
    assert "Illustrative Depletion Window" in html
    assert "Illustrative Storage Sensitivity Spectrum (Non-Predictive)" in html
    assert "badge-neutral" in html

    # Also check fallback vector PDF
    pdf_bytes = build_fallback_pdf("Test Fallback", "Test Text")
    assert b"WARNING: WHAT THIS ARTIFACT IS NOT" in pdf_bytes
    assert b"Toy Model" in pdf_bytes
