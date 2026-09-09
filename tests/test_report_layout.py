"""Layout and isolation guarantees for the generated reports.

Covers B17.3: tests run without any saved local session, and long or non-ASCII text is
wrapped and paginated rather than silently truncated or drawn outside the page.
"""
import re

import pytest

from basin_core.pdf_report import (
    ExperimentConfig,
    VectorFlow,
    build_fallback_pdf,
    encode_winansi,
    render_html_report,
    text_width,
    wrap_text,
)
from basin_core.workspace import session_dir

LONG_NOTE = (
    "Reviewed against the district drought-of-record narrative: this analogue understates "
    "late-summer reservoir evaporation because the 1991-2025 station window omits the "
    "1950s drought, and the reviewer wants the catchment representativeness question "
    "settled before any of these numbers are quoted to the council or used for planning."
)
LONG_DESCRIPTION = (
    "Volumetric survey coverage differs between the two reservoirs and the sedimentation "
    "rate assumed here is an interpolation, not a measurement. A supersededcontinuousidentifier"
    "WithNoSpacesAtAllThatMustStillWrapWithinItsColumnRatherThanRunOffThePage is included "
    "deliberately so the renderer has to break inside a word. " * 2
)
NON_ASCII_NOTE = "Revisión del hidrólogo: déficit de 403,8 mm — señalado como «provisional» ± 5 %."


@pytest.fixture
def approved(workspace):
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "Accepted for unit test")
    return workspace


def drawn_items(pdf_bytes: bytes):
    """Every drawn string as (page, x, y, size, font, text), decoded from the PDF."""
    raw = pdf_bytes.decode("cp1252", "replace")
    items = []
    for page_number, stream in enumerate(re.findall(r"stream\n(.*?)\nendstream", raw, re.S), start=1):
        for line in stream.splitlines():
            match = re.search(
                r"BT (/F\d) ([\d.]+) Tf [\d.]+ [\d.]+ [\d.]+ rg 1 0 0 1 ([\d.]+) ([\d.]+) Tm \((.*)\) Tj ET$",
                line,
            )
            if match:
                font, size, x, y, text = match.groups()
                text = text.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
                items.append((page_number, float(x), float(y), float(size), font, text))
    return items


def page_text(pdf_bytes: bytes) -> str:
    return " ".join(item[5] for item in drawn_items(pdf_bytes))


def page_count(pdf_bytes: bytes) -> int:
    return len(re.findall(rb"/Type /Page[^s]", pdf_bytes))


def overlapping_pairs(pdf_bytes: bytes):
    """Text drawn on the same baseline whose horizontal extents collide."""
    collisions = []
    items = drawn_items(pdf_bytes)
    by_line = {}
    for page, x, y, size, font, text in items:
        by_line.setdefault((page, round(y, 1)), []).append((x, size, font, text))
    for (page, y), row in by_line.items():
        row.sort()
        for (x1, s1, f1, t1), (x2, _, _, t2) in zip(row, row[1:]):
            if t1.strip() and t2.strip() and x1 + text_width(t1, f1, s1) > x2 + 0.5:
                collisions.append((page, y, t1, t2))
    return collisions


def out_of_bounds(pdf_bytes: bytes):
    """Text that starts outside the margins or runs past the right edge or the footer."""
    bad = []
    for page, x, y, size, font, text in drawn_items(pdf_bytes):
        if not text.strip():
            continue
        if x < 30 or y < 30 or y > 780 or x + text_width(text, font, size) > 580:
            bad.append((page, x, y, text))
    return bad


def test_the_geometry_checks_actually_catch_bad_layout():
    """Guard against the collision and margin assertions below passing vacuously."""
    from basin_core.pdf_report import VectorPDFBuilder

    doc = VectorPDFBuilder()
    page = doc.add_page()
    doc.text(page, 42, 400, "A left hand cell long enough to run past its column", font="/F1", size=8)
    doc.text(page, 120, 400, "RIGHT", font="/F1", size=8)
    doc.text(page, 500, 300, "A string starting near the right edge that overruns the page", font="/F1", size=8)
    pdf_bytes = doc.render()

    collisions = overlapping_pairs(pdf_bytes)
    assert collisions and collisions[0][3] == "RIGHT"
    assert out_of_bounds(pdf_bytes)


# --------------------------------------------------------------------------------------
# Isolation from real user sessions
# --------------------------------------------------------------------------------------

def test_tests_never_touch_the_real_session_directory(isolated_sessions, tmp_path):
    """The suite must not read or write the developer's local/ analyses."""
    assert session_dir() == isolated_sessions
    assert session_dir().name != "local"
    assert "Documents" not in str(session_dir()) or str(isolated_sessions) in str(session_dir())


def test_saving_a_workspace_stays_inside_the_isolated_directory(workspace, isolated_sessions):
    saved = workspace.save()
    assert saved.parent == isolated_sessions
    assert saved.exists()


def test_reports_build_without_any_saved_session(approved, isolated_sessions):
    """A clean checkout has no local/ at all; report generation must not depend on one."""
    assert not list(isolated_sessions.glob("session-*.json"))
    pdf_bytes = build_fallback_pdf(approved, approved.exportable())
    assert pdf_bytes.startswith(b"%PDF-")
    assert "BASIN EXECUTIVE TECHNICAL BRIEF" in page_text(pdf_bytes)


# --------------------------------------------------------------------------------------
# Measurement and wrapping
# --------------------------------------------------------------------------------------

def test_text_width_tracks_the_font():
    assert text_width("iii", "/F1", 10) < text_width("MMM", "/F1", 10)
    assert text_width("Hello", "/F2", 10) > text_width("Hello", "/F1", 10)
    # Courier is monospaced.
    assert text_width("iii", "/F3", 10) == pytest.approx(text_width("MMM", "/F3", 10))
    assert text_width("", "/F1", 10) == 0


def test_wrapping_keeps_every_word_and_fits_the_width():
    lines = wrap_text(LONG_NOTE, "/F1", 6.8, 160)
    assert len(lines) > 1
    for line in lines:
        assert text_width(line, "/F1", 6.8) <= 160
    assert " ".join(lines).split() == LONG_NOTE.split()


def test_unbreakable_words_are_split_not_overflowed():
    lines = wrap_text("X" * 200, "/F1", 7.0, 60)
    assert len(lines) > 1
    for line in lines:
        assert text_width(line, "/F1", 7.0) <= 60
    assert "".join(lines) == "X" * 200


def test_capped_wrapping_marks_that_it_shortened():
    lines = wrap_text(LONG_NOTE, "/F1", 6.8, 160, max_lines=2)
    assert len(lines) == 2
    assert lines[-1].endswith("...")


def test_winansi_encoding_keeps_latin_text_and_counts_what_it_cannot_draw():
    encoded, dropped = encode_winansi("Revisión — déficit ≤ 5")
    assert "Revisión" in encoded
    assert "—" in encoded
    assert "<=" in encoded
    assert dropped == 0

    encoded, dropped = encode_winansi("漢字 ✓")
    assert dropped == 3
    assert encoded.count("?") == 3


# --------------------------------------------------------------------------------------
# Long, absent, plentiful and non-ASCII content in the vector path
# --------------------------------------------------------------------------------------

def test_no_accepted_scenarios_renders_cleanly(approved):
    pdf_bytes = build_fallback_pdf(approved, [])
    text = page_text(pdf_bytes)
    assert "No accepted scenarios were supplied for this report." in text
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_several_scenarios_all_appear(approved):
    accepted = approved.exportable()
    assert len(accepted) >= 3
    pdf_bytes = build_fallback_pdf(approved, accepted)
    text = page_text(pdf_bytes)
    for scenario in accepted:
        assert f"{scenario.id} (R{scenario.revision})" in text
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_many_scenarios_paginate_rather_than_being_dropped(workspace):
    """The old table stopped after six rows; every accepted scenario must now appear."""
    workspace.selected = list(workspace.selected)
    for identifier in [s.id for s in workspace.scenarios[:12]]:
        if identifier not in workspace.selected:
            workspace.selected.append(identifier)
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "Accepted for pagination test")
    accepted = workspace.exportable()
    assert len(accepted) > 6

    pdf_bytes = build_fallback_pdf(workspace, accepted)
    text = page_text(pdf_bytes)
    for scenario in accepted:
        assert f"{scenario.id} (R{scenario.revision})" in text, scenario.id
    assert page_count(pdf_bytes) >= 3
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_long_review_notes_are_wrapped_not_truncated(approved):
    for identifier in approved.selected:
        approved.get(identifier).review(True, LONG_NOTE)
    accepted = approved.exportable()

    pdf_bytes = build_fallback_pdf(approved, accepted, include_notes=True)
    text = " ".join(page_text(pdf_bytes).split())
    assert LONG_NOTE in text
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_long_evidence_descriptions_are_wrapped_not_truncated(approved):
    record = dict(approved.evidence[0])
    record["id"] = "long-description-record"
    record["title"] = "A deliberately long supporting record"
    record["description"] = LONG_DESCRIPTION
    approved.add_evidence(record, [approved.selected[0]])
    for identifier in approved.selected:
        approved.get(identifier).review(True, "Re-accepted after evidence change")

    pdf_bytes = build_fallback_pdf(approved, approved.exportable())
    text = " ".join(page_text(pdf_bytes).split())
    assert "long-description-record" in text
    assert "A deliberately long supporting record" in text
    # The unbroken token is split across lines, so check its head and tail both survive.
    assert "supersededcontinuous" in text
    assert "RunOffThePage" in text
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_non_ascii_text_survives_in_the_vector_path(approved):
    for identifier in approved.selected:
        approved.get(identifier).review(True, NON_ASCII_NOTE)
    pdf_bytes = build_fallback_pdf(approved, approved.exportable(), include_notes=True)
    text = page_text(pdf_bytes)
    assert "Revisión del hidrólogo" in text
    assert "señalado" in text
    assert "«provisional»" in text
    assert not overlapping_pairs(pdf_bytes)
    assert not out_of_bounds(pdf_bytes)


def test_unrenderable_characters_are_disclosed(approved):
    for identifier in approved.selected:
        approved.get(identifier).review(True, "Reviewed 漢字 ✓")
    pdf_bytes = build_fallback_pdf(approved, approved.exportable(), include_notes=True)
    text = page_text(pdf_bytes)
    assert "have no glyph in the PDF base fonts" in text
    assert "Consult the companion bundle for the exact original text." in text


def test_pages_are_numbered_against_the_real_total(approved):
    pdf_bytes = build_fallback_pdf(approved, approved.exportable())
    total = page_count(pdf_bytes)
    text = page_text(pdf_bytes)
    for number in range(1, total + 1):
        assert f"Page {number} of {total}" in text
    assert f"Page {total + 1} of" not in text


def test_continuation_pages_are_labelled(workspace):
    for identifier in [s.id for s in workspace.scenarios[:12]]:
        if identifier not in workspace.selected:
            workspace.selected.append(identifier)
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, LONG_NOTE)
    pdf_bytes = build_fallback_pdf(workspace, workspace.exportable(), include_notes=True)
    assert "TECHNICAL ENGINEERING APPENDIX (CONTINUED)" in page_text(pdf_bytes)


# --------------------------------------------------------------------------------------
# The HTML path carries the same content
# --------------------------------------------------------------------------------------

def test_html_carries_long_notes_and_evidence_in_full(approved):
    record = dict(approved.evidence[0])
    record["id"] = "html-long-record"
    record["description"] = LONG_DESCRIPTION
    approved.add_evidence(record, [approved.selected[0]])
    for identifier in approved.selected:
        approved.get(identifier).review(True, LONG_NOTE)

    html = render_html_report(approved, approved.exportable(), include_notes=True)
    assert LONG_NOTE in html
    assert "html-long-record" in html
    assert LONG_DESCRIPTION.split(".")[0] in html
    # Long unbroken tokens must wrap inside their box rather than overflow it.
    assert "overflow-wrap: anywhere" in html
    assert '<table style="table-layout: fixed;">' in html
    assert '<col style="width: 37%;">' in html


def test_html_handles_no_scenarios_and_no_evidence(workspace):
    workspace.evidence = []
    workspace.conflicts = []
    html = render_html_report(workspace, [])
    assert "No accepted scenarios." in html
    assert "No evidence records are attached to this analysis." in html
    assert "No evidence disagreements have been recorded." in html


def test_html_escapes_non_ascii_review_notes(approved):
    for identifier in approved.selected:
        approved.get(identifier).review(True, NON_ASCII_NOTE)
    html = render_html_report(approved, approved.exportable(), include_notes=True)
    assert "Revisión del hidrólogo" in html
    assert "«provisional»" in html


# --------------------------------------------------------------------------------------
# Privacy is preserved by the new sections
# --------------------------------------------------------------------------------------

def test_evidence_private_annotations_stay_opt_in(approved):
    record = dict(approved.evidence[0])
    record["id"] = "private-annotation-record"
    record["private_note"] = "PRIVATE-EVIDENCE-SENTINEL"
    approved.add_evidence(record, [approved.selected[0]])
    for identifier in approved.selected:
        approved.get(identifier).review(True, "Re-accepted")
    accepted = approved.exportable()

    assert "PRIVATE-EVIDENCE-SENTINEL" not in page_text(build_fallback_pdf(approved, accepted))
    assert "PRIVATE-EVIDENCE-SENTINEL" in page_text(build_fallback_pdf(approved, accepted, include_notes=True))
    assert "PRIVATE-EVIDENCE-SENTINEL" not in render_html_report(approved, accepted)
    assert "PRIVATE-EVIDENCE-SENTINEL" in render_html_report(approved, accepted, include_notes=True)

    omitted = page_text(build_fallback_pdf(approved, accepted))
    assert "Private annotation recorded" in omitted


def test_conflict_private_notes_stay_opt_in(approved):
    conflict_id = approved.add_conflict(
        approved.evidence[0]["id"], approved.evidence[1]["id"],
        "Survey vintages disagree", "Different measurement years", "PRIVATE-CONFLICT-SENTINEL",
    )
    assert conflict_id
    accepted = approved.exportable()

    assert "PRIVATE-CONFLICT-SENTINEL" not in page_text(build_fallback_pdf(approved, accepted))
    assert "PRIVATE-CONFLICT-SENTINEL" in page_text(build_fallback_pdf(approved, accepted, include_notes=True))
    assert "PRIVATE-CONFLICT-SENTINEL" not in render_html_report(approved, accepted)
    assert "PRIVATE-CONFLICT-SENTINEL" in render_html_report(approved, accepted, include_notes=True)


def test_accuracy_and_settings_fixes_survive(approved):
    """The earlier tasks' guarantees must still hold after the layout work."""
    accepted = approved.exportable()
    config = ExperimentConfig(initial_pct=0.35, conservation_pct=0.30, pipeline_active=False,
                              scenario_id=accepted[0].id, scenario_revision=accepted[0].revision,
                              selected=True)
    text = page_text(build_fallback_pdf(approved, accepted, config=config))

    assert "919,900" in text and "963,600" not in text
    assert "PDF NOT VERIFIED" in text
    assert "35% of combined capacity" in text
    assert "30% demand reduction" in text
    assert "Assumed unavailable" in text
    assert "VERIFIED 256" not in text


def test_flow_starts_a_new_page_instead_of_overrunning_the_footer():
    from basin_core.pdf_report import VectorPDFBuilder

    doc = VectorPDFBuilder()
    page = doc.add_page()
    flow = VectorFlow(doc, page, 120, "run-id")
    assert len(doc.pages) == 1
    flow.paragraph(LONG_NOTE * 3, size=7.0)
    assert len(doc.pages) > 1
    assert flow.y > VectorFlow.BOTTOM - 10


def test_single_review_row_can_continue_across_multiple_pages(approved):
    note = "START-MULTIPAGE " + (LONG_NOTE + " ") * 30 + "END-MULTIPAGE"
    accepted = approved.exportable()
    accepted[0].review(True, note)
    pdf_bytes = build_fallback_pdf(approved, accepted, include_notes=True)
    text = " ".join(page_text(pdf_bytes).split())
    assert "START-MULTIPAGE" in text and "END-MULTIPAGE" in text
    note_column = " ".join(item[5] for item in drawn_items(pdf_bytes)
                           if item[1] == 410 and item[3] == 6.8)
    assert note_column.count(LONG_NOTE) == 30
    assert page_count(pdf_bytes) > 4
    assert not out_of_bounds(pdf_bytes)
    assert not overlapping_pairs(pdf_bytes)


def test_width_accounts_for_rendered_transliterations_and_wide_punctuation():
    assert text_width("→", "/F1", 9) == text_width("->", "/F1", 9)
    # An em dash is 1000 font units, not the former default of 556.
    assert text_width("—", "/F1", 10) >= 10
    assert text_width("W", "/F1", 10) == pytest.approx(9.44)
