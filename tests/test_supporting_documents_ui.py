"""Tests for Supporting Documents UI and document-evidence lifecycle."""
import base64
import hashlib
import io
import json
import zipfile
from types import SimpleNamespace
import pytest
from streamlit.testing.v1 import AppTest

from basin_core.document_ingestion import (
    DOCUMENT_CATCHMENT_DISCLAIMER,
    DocumentState,
    DocumentSecurityError,
    DocumentSizeLimitError,
    DocumentValidationError,
    ProhibitedDocumentClaimError,
)
from basin_core.workspace import Workspace
from basin_core.exporter import export_bundle


SAMPLE_PLAINTEXT_REPORT = (
    "City of Corpus Christi Drought Contingency Plan Excerpt.\n"
    "Section 4.1 Stage 2 curtailment schedule:\n"
    "Stage 2 mandatory target: 10% reduction across municipal and industrial accounts.\n"
    "Watering restricted to designated days only."
)

SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page >>\nendobj\n%%EOF"
)


def _find_doc(workspace: Workspace, doc_id: str):
    return next((d for d in workspace.documents if d.identity.id == doc_id), None)


def test_supporting_documents_panel_no_workspace():
    """Verify panel safely warns user when workspace is not yet initialized."""
    app = AppTest.from_string(
        "import streamlit as st\n"
        "from app import supporting_documents_panel\n"
        "supporting_documents_panel(None)\n",
        default_timeout=30,
    ).run()
    assert not app.exception
    assert any("Start an analysis" in info.value for info in app.info)
    assert any("unverified context" in caption.value for caption in app.caption)


def test_document_lifecycle_end_to_end_in_workspace(workspace):
    """Verify the full 4-step lifecycle: Ingest -> Extract -> Submit -> Review & Accept."""
    # Step 1: Ingest
    raw = SAMPLE_PLAINTEXT_REPORT.encode("utf-8")
    doc = workspace.ingest_document(
        raw=raw,
        filename="drought_plan.txt",
        provider="Corpus Christi Water",
        privacy="private",
    )
    assert doc.state == DocumentState.UPLOADED.value
    assert doc.identity.original_filename == "drought_plan.txt"
    assert doc.identity.source_provider == "Corpus Christi Water"
    assert doc.identity.privacy == "private"
    assert doc.identity.sha256 == hashlib.sha256(raw).hexdigest()

    # Step 2: Extract
    extracted_doc = workspace.extract_document(doc.identity.id)
    assert extracted_doc.state == DocumentState.EXTRACTED.value
    assert len(extracted_doc.blocks) >= 1
    block_id = extracted_doc.blocks[0].block_id
    assert "Stage 2 mandatory target" in extracted_doc.blocks[0].extracted_text

    # Step 3: Submit for review
    submitted_doc = workspace.submit_document_for_review(doc.identity.id)
    assert submitted_doc.state == DocumentState.NEEDS_REVIEW.value

    # Prohibited claim attempt fails closed
    with pytest.raises(ProhibitedDocumentClaimError):
        workspace.review_and_accept_document(
            doc_id=doc.identity.id,
            reviewer_rationale="This document establishes verified hydrologic validity.",
            confirmed_statement="This document provides official approval of firm yield.",
            reviewed_block_ids=[block_id],
            scenario_ids=workspace.selected[:1],
        )

    # State remains NEEDS_REVIEW after prohibited claim rejection
    assert _find_doc(workspace, doc.identity.id).state == DocumentState.NEEDS_REVIEW.value

    # Step 4: Valid review and acceptance
    target_scenario = workspace.selected[0]
    accepted_doc, records = workspace.review_and_accept_document(
        doc_id=doc.identity.id,
        reviewer_rationale="Verified against municipal drought plan stage 2 definitions.",
        confirmed_statement="Corpus Christi Stage 2 target is 10% reduction.",
        reviewed_block_ids=[block_id],
        scenario_ids=[target_scenario],
        private_note="Internal reviewer check.",
    )
    assert accepted_doc.state == DocumentState.ACCEPTED_AS_EVIDENCE.value
    assert accepted_doc.review is not None
    assert accepted_doc.review.confirmed_statement == "Corpus Christi Stage 2 target is 10% reduction."
    assert block_id in accepted_doc.review.reviewed_blocks

    # Check evidence association
    scenario_evidence_ids = workspace.evidence_refs.get(target_scenario, [])
    assert any(
        any(e["id"] == eid and e.get("source_locator", "").startswith(f"doc://{doc.identity.id}/") for e in workspace.evidence)
        for eid in scenario_evidence_ids
    )

    # Revocation / Rejection
    revoked_doc = workspace.reject_document(doc.identity.id, rationale="Evidence superseded.")
    assert revoked_doc.state == DocumentState.REJECTED.value
    scenario_evidence_ids_after = workspace.evidence_refs.get(target_scenario, [])
    assert not any(
        any(e["id"] == eid and e.get("source_locator", "").startswith(f"doc://{doc.identity.id}/") for e in workspace.evidence)
        for eid in scenario_evidence_ids_after
    )


def test_supporting_documents_ui_rendering_and_interaction(workspace, monkeypatch):
    """Test the Streamlit UI elements for supporting documents panel."""
    # Pre-populate with an uploaded document
    doc = workspace.ingest_document(
        raw=SAMPLE_PLAINTEXT_REPORT.encode("utf-8"),
        filename="curtailment_guidelines.txt",
        provider="City Utility",
        privacy="public",
    )

    app = AppTest.from_string(
        "import streamlit as st\n"
        "from app import supporting_documents_panel\n"
        "supporting_documents_panel(st.session_state.workspace)\n",
        default_timeout=30,
    )
    app.session_state.workspace = workspace
    app.run()
    assert not app.exception

    # Section 1 & 2 presence
    assert any("Supporting Documents & Cited Evidence" in m.value for m in app.markdown)
    assert any("Document Catalog" in m.value for m in app.markdown)

    # Check extract button is present when document is in UPLOADED state
    extract_btn_key = f"btn_extract_{doc.identity.id}"
    btn_extract = app.button(key=extract_btn_key)
    assert btn_extract is not None
    assert btn_extract.label == "Extract text blocks"

    # Click extract button
    btn_extract.click().run()
    assert not app.exception
    assert _find_doc(workspace, doc.identity.id).state == DocumentState.EXTRACTED.value

    # Check submit for review button is now present
    submit_btn_key = f"btn_submit_rev_{doc.identity.id}"
    btn_submit = app.button(key=submit_btn_key)
    assert btn_submit is not None
    assert btn_submit.label == "Submit document for review"

    # Click submit for review
    btn_submit.click().run()
    assert not app.exception
    assert _find_doc(workspace, doc.identity.id).state == DocumentState.NEEDS_REVIEW.value

    # Check review form elements
    accept_btn_key = f"btn_accept_{doc.identity.id}"
    reject_btn_key = f"btn_reject_{doc.identity.id}"
    assert app.button(key=accept_btn_key) is not None
    assert app.button(key=reject_btn_key) is not None

    # Missing rationale & confirmed statement should show error
    app.button(key=accept_btn_key).click().run()
    assert not app.exception
    assert any("required" in err.value.lower() for err in app.error)

    # Provide valid confirmed statement and rationale
    stmt_key = f"confirmed_stmt_{doc.identity.id}"
    rat_key = f"rationale_{doc.identity.id}"
    app.text_area(key=stmt_key).set_value("Stage 2 requires 10% curtailment.").run()
    app.text_area(key=rat_key).set_value("Factual policy excerpt for scenario review context.").run()
    app.button(key=accept_btn_key).click().run()
    assert not app.exception
    assert _find_doc(workspace, doc.identity.id).state == DocumentState.ACCEPTED_AS_EVIDENCE.value

    # Verify Accepted view renders success checkmark and revoke button
    assert any("Accepted as Evidence" in s.value for s in app.success)
    revoke_btn_key = f"btn_revoke_{doc.identity.id}"
    btn_revoke = app.button(key=revoke_btn_key)
    assert btn_revoke is not None

    # Click revoke button
    btn_revoke.click().run()
    assert not app.exception
    assert _find_doc(workspace, doc.identity.id).state == DocumentState.REJECTED.value


def test_duplicate_document_upload_deduplication(workspace):
    """Uploading the identical document retains deterministic ID and prevents conflicting copies."""
    raw = b"Unique document content for deduplication check."
    doc1 = workspace.ingest_document(raw=raw, filename="doc1.txt", provider="Prov A")
    with pytest.raises(ValueError, match="already ingested"):
        workspace.ingest_document(raw=raw, filename="doc2.txt", provider="Prov B")

    assert len(workspace.documents) == 1
    assert workspace.documents[0].identity.id == doc1.identity.id


def test_security_and_limit_enforcement(workspace):
    """Unsupported extensions, encrypted files, and oversized files fail closed."""
    # Unsupported extension
    with pytest.raises(DocumentValidationError):
        workspace.ingest_document(raw=b"data", filename="script.py", provider="Test")

    # Script/macro rejection
    with pytest.raises(DocumentSecurityError):
        workspace.ingest_document(
            raw=b"%PDF-1.4\n/JavaScript (alert(1))\n%%EOF",
            filename="malicious.pdf",
            provider="Test",
        )

    # Size limit
    huge_data = b"x" * (31 * 1024 * 1024)
    with pytest.raises(DocumentSizeLimitError):
        workspace.ingest_document(raw=huge_data, filename="huge.txt", provider="Test")


def test_save_restore_preserves_document_state_and_citations(workspace, tmp_path):
    """Workspace save/restore preserves document record, blocks, review, and evidence."""
    raw = SAMPLE_PLAINTEXT_REPORT.encode("utf-8")
    doc = workspace.ingest_document(raw=raw, filename="plan.txt", provider="City", privacy="public")
    extracted_doc = workspace.extract_document(doc.identity.id)
    workspace.submit_document_for_review(doc.identity.id)
    block_id = extracted_doc.blocks[0].block_id
    workspace.review_and_accept_document(
        doc_id=doc.identity.id,
        reviewer_rationale="Valid drought policy excerpt.",
        confirmed_statement="Stage 2 targets 10% reduction.",
        reviewed_block_ids=[block_id],
        scenario_ids=workspace.selected[:1],
        private_note="Internal reviewer notes.",
    )

    saved_file = workspace.save(tmp_path)

    restored = Workspace.load(workspace.source, saved_file)
    restored_doc = _find_doc(restored, doc.identity.id)
    assert restored_doc is not None
    assert restored_doc.state == DocumentState.ACCEPTED_AS_EVIDENCE.value
    assert restored_doc.identity.privacy == "public"
    assert restored_doc.review is not None
    assert restored_doc.review.confirmed_statement == "Stage 2 targets 10% reduction."
    assert restored_doc.review.private_note == "Internal reviewer notes."
    assert any(e.get("source_locator", "").startswith(f"doc://{doc.identity.id}/page/") for e in restored.evidence)
    assert any(block_id in e.get("description", "") for e in restored.evidence)


def test_export_bundle_excludes_private_raw_bytes_and_unreviewed_documents(workspace, tmp_path):
    """Unreviewed documents and private raw bytes are excluded from public export bundles."""
    # Accepted private document
    raw_priv = b"Private municipal memo on water curtailment."
    doc_priv = workspace.ingest_document(raw=raw_priv, filename="private_memo.txt", provider="City", privacy="private")
    extracted_priv = workspace.extract_document(doc_priv.identity.id)
    workspace.submit_document_for_review(doc_priv.identity.id)
    workspace.review_and_accept_document(
        doc_id=doc_priv.identity.id,
        reviewer_rationale="Private background context.",
        confirmed_statement="Internal target noted.",
        reviewed_block_ids=[extracted_priv.blocks[0].block_id],
        scenario_ids=workspace.selected[:1],
    )

    # Unreviewed uploaded document
    raw_unrev = b"Unreviewed background report."
    doc_unrev = workspace.ingest_document(raw=raw_unrev, filename="unreviewed.txt", provider="Consultant", privacy="public")

    # Accept shortlisted scenarios to allow export
    for sid in workspace.selected:
        workspace.get(sid).review(True, "Rainfall checked")

    zip_bytes = export_bundle(workspace, include_notes=False)
    assert zip_bytes is not None

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        namelist = z.namelist()
        audit = json.loads(z.read("audit.json"))
        # Unreviewed document must not have an entry in documents/
        assert not any("unreviewed.txt" in name for name in namelist)
        # Private raw file must not be included
        assert not any("private_memo.txt" in name for name in namelist)
        assert "document_originals" not in audit
