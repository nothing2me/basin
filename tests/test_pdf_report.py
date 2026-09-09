from pathlib import Path
from basin_core.data import CachedSource
from basin_core.workspace import Workspace
from basin_core.pdf_report import render_html_report, generate_pdf_report, build_fallback_pdf, find_browser_executable

ROOT = Path(__file__).resolve().parents[1]


def test_fallback_pdf_generation():
    pdf_bytes = build_fallback_pdf("Test Title", "Test Content")
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"BASIN EXECUTIVE TECHNICAL BRIEF" in pdf_bytes
    assert len(pdf_bytes) > 500


def test_render_html_report():
    source = CachedSource()
    sessions = list((ROOT / "local").glob("session-*.json"))
    workspace = Workspace.load(source, sessions[0])
    for sid in workspace.selected:
        workspace.get(sid).review(True, "Accepted for unit test")
    accepted = workspace.exportable()

    html = render_html_report(workspace, accepted)
    assert "BASIN · EXECUTIVE TECHNICAL BRIEF" in html
    assert "The Bottom Line — Executive Overview" in html
    assert "Illustrative Drought Response Reference Framework" in html
    assert "Multi-Tier Rainfall Stress Spectrum & Countdown Matrix" in html
    assert "Scientific Provenance & Verification Scope" in html
    assert workspace.id in html
    assert "omitted: export privacy setting excludes private notes" in html
    assert "Accepted for unit test" not in html

    # Test with include_notes=True
    html_with_notes = render_html_report(workspace, accepted, include_notes=True)
    assert "Accepted for unit test" in html_with_notes


def test_generate_pdf_report(tmp_path):
    source = CachedSource()
    sessions = list((ROOT / "local").glob("session-*.json"))
    workspace = Workspace.load(source, sessions[0])
    for sid in workspace.selected:
        workspace.get(sid).review(True, "Accepted for unit test")
    accepted = workspace.exportable()

    target_pdf = tmp_path / f"BASIN-Executive-Brief-{workspace.id}.pdf"
    pdf_bytes = generate_pdf_report(workspace, accepted, output_path=target_pdf)

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000
    assert target_pdf.exists()
    assert target_pdf.stat().st_size == len(pdf_bytes)
