"""Cross-output consent: private notes and custom data must be gated consistently.

BASIN can produce four artifacts from one workspace: the replay ZIP, the Markdown brief,
and two PDF renderers (browser HTML->PDF and the vector fallback). A reviewer who leaves
review notes private, or who does not consent to sharing custom uploaded data, must get
that decision honored the same way in every output -- and revoking consent after a first
export must actually remove the previously-included content from the next one, not just
hide a stale download button. This uses a synthetic sentinel string rather than any real
private information, per docs/report_device_acceptance.md.
"""
import zipfile
from io import BytesIO

import pytest

from basin_core.exporter import export_bundle
from basin_core.pdf_report import build_fallback_pdf, render_html_report

NOTE_SENTINEL = "PRIVATE-NOTE-SENTINEL-42"
PROVIDER_NOTE_SENTINEL = "PRIVATE-PROVIDER-NOTE-SENTINEL-17"
CUSTOM_RAW = b"date,precipitation\n2024-01-01,1\n2024-01-02,2\n2024-01-04,\n"


def attach_custom(w):
    return w.save_custom_upload(
        CUSTOM_RAW,
        reviewed=True,
        station="Local gauge",
        location="Example town",
        unit="mm",
        provider="Example provider",
        observation_basis="Daily window uncertain",
        reference_station="USW00012924",
        relationship="regional_proxy",
        daily_confirmed=True,
        rationale="Regional context only; catchment suitability remains uncertain",
        scenario_ids=w.selected[:1],
    )


@pytest.fixture
def approved_with_note_and_custom(workspace):
    attach_custom(workspace)  # invalidates review on its linked scenario, so do this first
    workspace.notes = PROVIDER_NOTE_SENTINEL
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, NOTE_SENTINEL)
    return workspace


def zip_contains(payload: bytes, needle: bytes) -> bool:
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        return any(needle in archive.read(name) for name in archive.namelist())


def test_note_consent_is_honored_the_same_way_in_the_zip_and_both_pdf_paths(approved_with_note_and_custom):
    w = approved_with_note_and_custom
    accepted = w.exportable()

    zip_excluded = export_bundle(w, include_notes=False, include_custom=True)
    zip_included = export_bundle(w, include_notes=True, include_custom=True)
    assert not zip_contains(zip_excluded, NOTE_SENTINEL.encode())
    assert zip_contains(zip_included, NOTE_SENTINEL.encode())
    assert not zip_contains(zip_excluded, PROVIDER_NOTE_SENTINEL.encode())
    assert zip_contains(zip_included, PROVIDER_NOTE_SENTINEL.encode())

    html_excluded = render_html_report(w, accepted, include_notes=False)
    html_included = render_html_report(w, accepted, include_notes=True)
    assert NOTE_SENTINEL not in html_excluded
    assert NOTE_SENTINEL in html_included
    assert PROVIDER_NOTE_SENTINEL not in html_excluded
    assert PROVIDER_NOTE_SENTINEL in html_included

    vector_excluded = build_fallback_pdf(w, accepted, include_notes=False)
    vector_included = build_fallback_pdf(w, accepted, include_notes=True)
    assert NOTE_SENTINEL.encode() not in vector_excluded
    assert NOTE_SENTINEL.encode() in vector_included
    assert PROVIDER_NOTE_SENTINEL.encode() not in vector_excluded
    assert PROVIDER_NOTE_SENTINEL.encode() in vector_included


def test_custom_raw_bytes_never_reach_the_zip_or_either_pdf_path(approved_with_note_and_custom):
    """Original custom-upload bytes stay in the local session only. The ZIP already excludes
    them by design (B14) even with consent -- confirmed here alongside the PDF, which has no
    custom-data consent knob at all because it never carries any custom-upload content, raw
    or normalized. Without consent, custom-data export is blocked outright, not silently
    stripped."""
    w = approved_with_note_and_custom
    accepted = w.exportable()

    zip_with_custom = export_bundle(w, include_notes=True, include_custom=True)
    assert not zip_contains(zip_with_custom, CUSTOM_RAW)  # originals never leave the session
    assert zip_contains(zip_with_custom, b"upload_total_mm")  # normalized data is present

    with pytest.raises(ValueError, match="consent"):
        export_bundle(w, include_notes=True, include_custom=False)

    html = render_html_report(w, accepted, include_notes=True)
    vector = build_fallback_pdf(w, accepted, include_notes=True)
    assert CUSTOM_RAW.decode() not in html
    assert CUSTOM_RAW not in vector
    assert "upload_total_mm" not in html
    assert b"upload_total_mm" not in vector


def test_revoking_note_consent_removes_the_sentinel_from_every_freshly_built_output(approved_with_note_and_custom):
    """Regenerating with consent off must not retain anything from an earlier consented build."""
    w = approved_with_note_and_custom
    accepted = w.exportable()

    # First, build with consent on everywhere.
    first_zip = export_bundle(w, include_notes=True, include_custom=True)
    first_html = render_html_report(w, accepted, include_notes=True)
    first_vector = build_fallback_pdf(w, accepted, include_notes=True)
    assert zip_contains(first_zip, NOTE_SENTINEL.encode())
    assert NOTE_SENTINEL in first_html
    assert NOTE_SENTINEL.encode() in first_vector

    # Revoke: a fresh build with consent off must be clean, not a cached/stale artifact.
    revoked_zip = export_bundle(w, include_notes=False, include_custom=True)
    revoked_html = render_html_report(w, accepted, include_notes=False)
    revoked_vector = build_fallback_pdf(w, accepted, include_notes=False)
    assert not zip_contains(revoked_zip, NOTE_SENTINEL.encode())
    assert not zip_contains(revoked_zip, PROVIDER_NOTE_SENTINEL.encode())
    assert NOTE_SENTINEL not in revoked_html
    assert NOTE_SENTINEL.encode() not in revoked_vector
    assert PROVIDER_NOTE_SENTINEL not in revoked_html
    assert PROVIDER_NOTE_SENTINEL.encode() not in revoked_vector
