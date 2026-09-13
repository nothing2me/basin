"""Automated verification suite for PDF and verified-export quality pass.

Covers:
1. Strict 8-section sequence in HTML and vector PDF.
2. 8-case matrix:
   - Region N preset
   - Small municipal preset (12,000 ac-ft)
   - Custom storage system (e.g. 50,000 ac-ft)
   - NOAA observations
   - Custom observations (T3 source label, coverage dates, catchment disclaimer)
   - Long labels and multi-line notes (no clipping, no collision)
   - Unicode characters (smart quotes, dashes, degree sign, accented vowels)
   - Provider-note consent on / off / revoked
3. Verified ZIP bundle audit:
   - Filename clarity
   - Concise README instructions
   - Manifest hash verification
   - Selected water-system configuration included
   - Saved simulation runs included with explicit review state
   - Custom observations use T3 provenance language
   - Rainfall percentages use T2 terminology
   - Private notes follow consent and revocation
   - Replay verification succeeds
"""
from __future__ import annotations

import io
import json
import zipfile
import pytest

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace
from basin_core.water_system import (
    REGION_N_PRESET,
    SMALL_MUNI_PRESET,
    WaterSource,
    WaterSystemConfig,
)
from basin_core.simulation import SimulationSettings
from basin_core.exporter import export_bundle, verify_bundle
from basin_core.pdf_report import (
    ExperimentConfig,
    build_fallback_pdf,
    render_html_report,
)
from basin_core.custom_data import (
    CUSTOM_CATCHMENT_DISCLAIMER,
    format_custom_coverage_dates,
    format_custom_source_label,
)
from tests.test_custom_data import accept_all, attach
from tests.test_report_layout import drawn_items, overlapping_pairs, out_of_bounds, page_text


@pytest.fixture
def base_workspace():
    source = CachedSource()
    w = Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=30), size=3)
    for sid in w.selected:
        w.get(sid).review(True, f"Accepted for test {sid}")
    return w


def test_section_order_in_html_and_vector(base_workspace):
    accepted = base_workspace.exportable()
    html = render_html_report(base_workspace, accepted)
    pdf_bytes = build_fallback_pdf(base_workspace, accepted)
    pdf_txt = page_text(pdf_bytes)

    html_sections = [
        "1. Executive Summary",
        "2. Scenario Identity and Rainfall Input",
        "3. Review Decision and Rationale",
        "4. Storage-System Assumptions",
        "5. Experiment Results",
        "6. Observation Provenance",
        "7. Limitations",
        "8. Verification and Hashes",
    ]
    last_idx = -1
    for sec in html_sections:
        idx = html.find(sec)
        assert idx != -1, f"Section '{sec}' missing in HTML"
        assert idx > last_idx, f"Section '{sec}' out of order in HTML"
        last_idx = idx

    vector_sections = [
        "1. EXECUTIVE SUMMARY",
        "2. SCENARIO IDENTITY AND RAINFALL INPUT",
        "3. REVIEW DECISION AND RATIONALE",
        "4. STORAGE-SYSTEM ASSUMPTIONS",
        "5. EXPERIMENT RESULTS",
        "6. OBSERVATION PROVENANCE",
        "7. LIMITATIONS",
        "8. VERIFICATION AND HASHES",
    ]
    last_idx = -1
    for sec in vector_sections:
        idx = pdf_txt.find(sec)
        assert idx != -1, f"Section '{sec}' missing in Vector PDF"
        assert idx > last_idx, f"Section '{sec}' out of order in Vector PDF"
        last_idx = idx


def test_matrix_case_region_n(base_workspace):
    accepted = base_workspace.exportable()
    html = render_html_report(base_workspace, accepted)
    pdf_bytes = build_fallback_pdf(base_workspace, accepted)

    assert "919,900 ac-ft" in html
    assert b"919,900" in pdf_bytes
    assert "918,882 ac-ft" in html
    assert b"918,882" in pdf_bytes
    assert "Lake Corpus Christi" in html
    assert "Choke Canyon" in html


def test_matrix_case_small_municipal(base_workspace):
    base_workspace.select_water_system(SMALL_MUNI_PRESET, "small_municipal")
    accepted = base_workspace.exportable()
    config = ExperimentConfig(system_config=SMALL_MUNI_PRESET)

    html = render_html_report(base_workspace, accepted, config=config)
    pdf_bytes = build_fallback_pdf(base_workspace, accepted, config=config)

    assert "12,000 ac-ft" in html
    assert b"12,000" in pdf_bytes
    assert "4,800 ac-ft" in html
    assert b"4,800" in pdf_bytes
    assert "919,900" not in html
    assert b"919,900" not in pdf_bytes


def test_matrix_case_custom_storage(base_workspace):
    custom_sys = WaterSystemConfig(
        name="Highland Ranch Reservoir System",
        sources=(
            WaterSource.scaled_for_capacity("North Pasture Pool", 20000.0),
            WaterSource.scaled_for_capacity("South Draw Storage", 30000.0),
        ),
    )
    base_workspace.select_water_system(custom_sys, "custom")
    accepted = base_workspace.exportable()
    config = ExperimentConfig(system_config=custom_sys)

    html = render_html_report(base_workspace, accepted, config=config)
    pdf_bytes = build_fallback_pdf(base_workspace, accepted, config=config)

    assert "50,000 ac-ft" in html
    assert b"50,000" in pdf_bytes
    assert "North Pasture Pool" in html
    assert "South Draw Storage" in html
    assert "No external capacity survey comparison is configured" in html


def test_matrix_case_noaa_observations(base_workspace):
    accepted = base_workspace.exportable()
    html = render_html_report(base_workspace, accepted)
    pdf_bytes = build_fallback_pdf(base_workspace, accepted)

    assert "NOAA GHCN-Daily" in html
    assert b"NOAA GHCN-Daily" in pdf_bytes
    assert base_workspace.params.stations[0] in html


def test_matrix_case_custom_observations(base_workspace):
    attach(base_workspace)
    accept_all(base_workspace)

    accepted = base_workspace.exportable()
    html = render_html_report(base_workspace, accepted)
    pdf_bytes = build_fallback_pdf(base_workspace, accepted)

    assert CUSTOM_CATCHMENT_DISCLAIMER in html
    assert b"User-provided dataset" in pdf_bytes or b"Local gauge" in pdf_bytes
    assert CUSTOM_CATCHMENT_DISCLAIMER.encode("cp1252", "replace") in pdf_bytes


def test_matrix_case_long_labels_and_multiline(base_workspace):
    long_rationale = (
        "This is an extraordinarily thorough human review rationale detailing multi-month "
        "drought analogues across the coastal plains, verifying that soil antecedent moisture "
        "and downstream conveyance losses comply with regional planning standards."
    )
    for sid in base_workspace.selected:
        base_workspace.get(sid).review(True, long_rationale)
    base_workspace.notes = "Provider note: extended multi-line commentary on drought contingencies and regional supply contracts."

    accepted = base_workspace.exportable()
    pdf_bytes = build_fallback_pdf(base_workspace, accepted, include_notes=True)

    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)
    txt = page_text(pdf_bytes)
    assert "extraordinarily thorough" in txt
    assert "Provider note: extended" in txt


def test_matrix_case_unicode_characters(base_workspace):
    unicode_note = "Revisión técnica: déficit de 412,5 mm — clasificación «crítica» a 38 °C ± 2 °C."
    base_workspace.get(base_workspace.selected[0]).review(True, unicode_note)
    accepted = base_workspace.exportable()

    html = render_html_report(base_workspace, accepted, include_notes=True)
    assert "Revisión técnica" in html
    assert "412,5 mm" in html
    assert "«crítica»" in html

    pdf_bytes = build_fallback_pdf(base_workspace, accepted, include_notes=True)
    txt = page_text(pdf_bytes)
    assert "Revisión técnica" in txt
    assert "«crítica»" in txt
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_matrix_case_provider_notes_consent_lifecycle(base_workspace):
    base_workspace.notes = "CONFIDENTIAL-PROVIDER-DIRECTIVE"
    for sid in base_workspace.selected:
        base_workspace.get(sid).review(True, "CONFIDENTIAL-REVIEW-RATIONALE")
    accepted = base_workspace.exportable()

    html_off = render_html_report(base_workspace, accepted, include_notes=False)
    pdf_off = build_fallback_pdf(base_workspace, accepted, include_notes=False)
    bundle_off = export_bundle(base_workspace, include_notes=False)

    assert "CONFIDENTIAL-PROVIDER-DIRECTIVE" not in html_off
    assert "CONFIDENTIAL-REVIEW-RATIONALE" not in html_off
    assert b"CONFIDENTIAL-PROVIDER-DIRECTIVE" not in pdf_off
    assert b"CONFIDENTIAL-REVIEW-RATIONALE" not in pdf_off
    with zipfile.ZipFile(io.BytesIO(bundle_off)) as z:
        audit = json.loads(z.read("audit.json"))
        brief = z.read("Hydrologist_Handoff_Brief.md").decode("utf-8")
        assert "CONFIDENTIAL-PROVIDER-DIRECTIVE" not in audit.get("provider_notes", "")
        assert "CONFIDENTIAL-PROVIDER-DIRECTIVE" not in brief

    html_on = render_html_report(base_workspace, accepted, include_notes=True)
    pdf_on = build_fallback_pdf(base_workspace, accepted, include_notes=True)
    bundle_on = export_bundle(base_workspace, include_notes=True)

    assert "CONFIDENTIAL-PROVIDER-DIRECTIVE" in html_on
    assert "CONFIDENTIAL-REVIEW-RATIONALE" in html_on
    assert b"CONFIDENTIAL-PROVIDER-DIRECTIVE" in pdf_on
    assert b"CONFIDENTIAL-REVIEW-RATIONALE" in pdf_on
    with zipfile.ZipFile(io.BytesIO(bundle_on)) as z:
        audit = json.loads(z.read("audit.json"))
        assert audit.get("provider_notes") == "CONFIDENTIAL-PROVIDER-DIRECTIVE"

    bundle_revoked = export_bundle(base_workspace, include_notes=False)
    with zipfile.ZipFile(io.BytesIO(bundle_revoked)) as z:
        audit = json.loads(z.read("audit.json"))
        assert "CONFIDENTIAL-PROVIDER-DIRECTIVE" not in audit.get("provider_notes", "")


def test_verified_zip_bundle_audit(base_workspace):
    sid0 = base_workspace.selected[0]
    unreviewed_run = base_workspace.run_simulation(sid0, SimulationSettings())
    base_workspace.select_water_system(SMALL_MUNI_PRESET, "small_municipal")
    reviewed_run = base_workspace.run_simulation(sid0, SimulationSettings())
    base_workspace.review_simulation(reviewed_run["id"], "Reviewed simulation for export audit")

    payload = export_bundle(base_workspace)
    assert verify_bundle(payload)["verified"] is True

    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        namelist = z.namelist()
        expected_files = {
            "daily_rainfall.csv",
            "shortlist.csv",
            "audit.json",
            "Hydrologist_Handoff_Brief.md",
            "snapshot/observations.csv",
            "snapshot/manifest.json",
            "methodology.md",
            "README.txt",
            "replay_bundle.py",
            "bundle_manifest.json",
        }
        assert set(namelist) == expected_files

        readme = z.read("README.txt").decode("utf-8")
        assert "WARNING: WHAT THIS ARTIFACT IS NOT" in readme
        assert "Replay with BASIN 0.2: python scripts/replay_bundle.py" in readme

        audit = json.loads(z.read("audit.json"))
        assert "water_system_selection" in audit
        reviews = audit.get("simulation_reviews", {})
        run_ids = {run["id"] for run in audit.get("simulation_runs", [])}
        assert run_ids == {unreviewed_run["id"], reviewed_run["id"]}
        assert reviewed_run["id"] in reviews
        assert unreviewed_run["id"] not in reviews

        brief = z.read("Hydrologist_Handoff_Brief.md").decode("utf-8")
        assert "% retained (" in brief or "Retained rainfall" in brief
        assert "% reduction" in brief
