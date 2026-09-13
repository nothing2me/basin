"""Safe, typed foundation for user-provided document ingestion, extraction, review, and evidence promotion in BASIN.

Architecture invariants:
- Pure domain logic with no external framework dependencies (no Streamlit, SQLite, subprocess, or heavy parsers).
- Documents are content-addressed by SHA-256; files cannot be mutated in-place.
- Extracted text is unverified source material and cannot automatically become evidence.
- Human review is strictly required before promotion to evidence.
- Claims derived from documents are checked against BASIN prohibited claims boundaries.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse

from basin_core.scientific_contract import validate_report_text_against_prohibited_claims


# -----------------------------------------------------------------------------
# 1. Typed Errors
# -----------------------------------------------------------------------------

class DocumentValidationError(ValueError):
    """Base exception for document ingestion and validation errors."""


class UnsupportedMediaTypeError(DocumentValidationError):
    """Raised when an uploaded document has an unsupported media type or signature."""


class DocumentSizeLimitError(DocumentValidationError):
    """Raised when an uploaded document exceeds byte size limits."""


class DocumentContentLimitError(DocumentValidationError):
    """Raised when an extracted document exceeds page count or character limits."""


class DocumentSecurityError(DocumentValidationError):
    """Raised when a document contains encrypted data, scripts, macros, or malicious structures."""


class InvalidDocumentStateTransitionError(DocumentValidationError):
    """Raised when attempting an illegal document review state transition."""


class DocumentCitationError(DocumentValidationError):
    """Raised when a document evidence citation is missing, invalid, or mismatched."""


class ProhibitedDocumentClaimError(DocumentValidationError):
    """Raised when document-derived claims violate BASIN scientific or regulatory boundaries."""


# -----------------------------------------------------------------------------
# 2. Enums and Classification
# -----------------------------------------------------------------------------

class DocumentState(str, Enum):
    """Lifecycle states for ingested documents."""
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs_review"
    ACCEPTED_AS_EVIDENCE = "accepted_as_evidence"
    REJECTED = "rejected"
    FAILED = "failed"


class PrivacyClassification(str, Enum):
    """Privacy level for document artifacts and metadata."""
    PRIVATE = "private"
    PUBLIC = "public"


class SupportedMediaType(str, Enum):
    """Explicitly supported document MIME types."""
    PDF = "application/pdf"
    PLAIN_TEXT = "text/plain"


# -----------------------------------------------------------------------------
# 3. Limits & Constants
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class DocumentLimits:
    """Bounded limits for document size and text volume."""
    max_file_size_bytes: int = 30 * 1024 * 1024   # 30 MB
    min_file_size_bytes: int = 1
    max_pages: int = 100
    max_total_characters: int = 500_000
    max_characters_per_page: int = 20_000


DOCUMENT_CATCHMENT_DISCLAIMER = (
    "User-provided document evidence represents unverified contextual reference, "
    "not a calibrated catchment model or official policy."
)

# Additional prohibited claim patterns specific to ingested documents
ADDITIONAL_DOCUMENT_PROHIBITED_PATTERNS = (
    (r"\b(official|regulatory|statutory|certified)\s+(approval|endorsement|sanction|adoption)\b",
     "Cannot claim document provides official or regulatory approval."),
    (r"\b(verified|validated)\s+hydrologic\s+validity\b",
     "Cannot claim document establishes verified hydrologic validity."),
    (r"\bcalibrated\s+catchment\s+behavior\b",
     "Cannot claim document establishes calibrated catchment behavior."),
    (r"\bvalidated\s+reservoir\s+inflow\b",
     "Cannot claim document establishes validated reservoir inflow."),
    (r"\b(safe|firm)\s+yield\s+(forecast|determination|guarantee)\b",
     "Cannot claim document determines safe or firm yield."),
    (r"\b(forecast\s+probability|probabilistic\s+forecast)\b",
     "Cannot claim document provides probabilistic forecasts."),
    (r"\badopted\s+restriction\s+policy\b",
     "Cannot claim document represents adopted restriction policy."),
    (r"\b(ignore\s+(all\s+)?previous\s+instructions|system\s+prompt|disregard\s+prior\s+instructions)\b",
     "Document text contains prompt injection or execution directives."),
)


def validate_document_claims(text: str) -> list[str]:
    """Scan document text, reviewer rationale, or confirmed statements for prohibited claims."""
    violations = validate_report_text_against_prohibited_claims(text)
    for pattern, rationale in ADDITIONAL_DOCUMENT_PROHIBITED_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            violations.append(f"Prohibited Document Claim: '{match.group(0)}' - {rationale}")
    return violations


# -----------------------------------------------------------------------------
# 4. Core Value Objects & Models
# -----------------------------------------------------------------------------

def utc_iso_now() -> str:
    """Return current UTC timestamp in standard ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ExtractionBlock:
    """Page-level or section-level text block extracted from a document."""
    document_id: str
    page_number: int       # 1-indexed page number
    block_id: str          # Deterministic identifier
    extracted_text: str
    extraction_status: str # "success", "partial", "failed", "empty"
    warnings: tuple[str, ...] = ()
    digest: str = ""

    def __post_init__(self):
        if not self.digest:
            d = hashlib.sha256(self.extracted_text.encode("utf-8")).hexdigest()
            object.__setattr__(self, "digest", d)
        if self.page_number < 1:
            raise DocumentValidationError("Page number must be >= 1")
        if not self.block_id or not self.block_id.strip():
            raise DocumentValidationError("Block ID must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "page_number": self.page_number,
            "block_id": self.block_id,
            "extracted_text": self.extracted_text,
            "extraction_status": self.extraction_status,
            "warnings": list(self.warnings),
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionBlock:
        return cls(
            document_id=data["document_id"],
            page_number=int(data["page_number"]),
            block_id=data["block_id"],
            extracted_text=data["extracted_text"],
            extraction_status=data["extraction_status"],
            warnings=tuple(data.get("warnings", ())),
            digest=data.get("digest", ""),
        )


@dataclass(frozen=True)
class DocumentReview:
    """Explicit human review record required to promote extraction to evidence."""
    document_id: str
    reviewed_at: str
    reviewer_rationale: str
    reviewed_blocks: tuple[str, ...]
    reviewed_pages: tuple[int, ...]
    source_digest: str
    confirmed_statement: str
    private_note: str = ""

    def __post_init__(self):
        if not self.reviewer_rationale or not self.reviewer_rationale.strip():
            raise DocumentValidationError("Reviewer rationale is mandatory and cannot be empty")
        if not self.confirmed_statement or not self.confirmed_statement.strip():
            raise DocumentValidationError("Confirmed statement is mandatory and cannot be empty")
        if not self.reviewed_blocks:
            raise DocumentValidationError("Review must cite at least one reviewed block ID")
        if not self.reviewed_pages or any(p < 1 for p in self.reviewed_pages):
            raise DocumentValidationError("Review must cite valid page numbers (>= 1)")
        if not self.source_digest or not re.fullmatch(r"[0-9a-f]{64}", self.source_digest):
            raise DocumentValidationError("Source digest must be a valid 64-character hex SHA-256 string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "reviewed_at": self.reviewed_at,
            "reviewer_rationale": self.reviewer_rationale,
            "reviewed_blocks": list(self.reviewed_blocks),
            "reviewed_pages": list(self.reviewed_pages),
            "source_digest": self.source_digest,
            "confirmed_statement": self.confirmed_statement,
            "private_note": self.private_note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentReview:
        return cls(
            document_id=data["document_id"],
            reviewed_at=data["reviewed_at"],
            reviewer_rationale=data["reviewer_rationale"],
            reviewed_blocks=tuple(data["reviewed_blocks"]),
            reviewed_pages=tuple(int(p) for p in data["reviewed_pages"]),
            source_digest=data["source_digest"],
            confirmed_statement=data["confirmed_statement"],
            private_note=data.get("private_note", ""),
        )


@dataclass(frozen=True)
class DocumentIdentity:
    """Immutable identity record for an uploaded document."""
    id: str
    original_filename: str
    media_type: str
    byte_size: int
    sha256: str
    ingested_at: str
    page_count: int | None
    extraction_method: str
    source_provider: str
    privacy: str = PrivacyClassification.PRIVATE.value
    state: str = DocumentState.UPLOADED.value

    def __post_init__(self):
        if not self.id.startswith("doc-"):
            raise DocumentValidationError(f"Document ID must start with 'doc-', got {self.id}")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise DocumentValidationError(f"Invalid SHA-256 digest: {self.sha256}")
        if self.byte_size <= 0:
            raise DocumentValidationError("Byte size must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "media_type": self.media_type,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "ingested_at": self.ingested_at,
            "page_count": self.page_count,
            "extraction_method": self.extraction_method,
            "source_provider": self.source_provider,
            "privacy": self.privacy,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentIdentity:
        return cls(
            id=data["id"],
            original_filename=data["original_filename"],
            media_type=data["media_type"],
            byte_size=int(data["byte_size"]),
            sha256=data["sha256"],
            ingested_at=data["ingested_at"],
            page_count=int(data["page_count"]) if data.get("page_count") is not None else None,
            extraction_method=data["extraction_method"],
            source_provider=data["source_provider"],
            privacy=data.get("privacy", PrivacyClassification.PRIVATE.value),
            state=data.get("state", DocumentState.UPLOADED.value),
        )


@dataclass(frozen=True)
class DocumentRecord:
    """Complete document record containing identity, blocks, review state, and audit data."""
    identity: DocumentIdentity
    blocks: tuple[ExtractionBlock, ...] = ()
    review: DocumentReview | None = None
    state: str = DocumentState.UPLOADED.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "blocks": [b.to_dict() for b in self.blocks],
            "review": self.review.to_dict() if self.review else None,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentRecord:
        return cls(
            identity=DocumentIdentity.from_dict(data["identity"]),
            blocks=tuple(ExtractionBlock.from_dict(b) for b in data.get("blocks", [])),
            review=DocumentReview.from_dict(data["review"]) if data.get("review") else None,
            state=data.get("state", DocumentState.UPLOADED.value),
        )


# -----------------------------------------------------------------------------
# 5. Validation & Sanitization Functions
# -----------------------------------------------------------------------------

REJECTED_EXTENSIONS = frozenset({
    ".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".sh", ".ps1", ".vbs",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz",
    ".py", ".pyc", ".js", ".html", ".htm", ".msi", ".jar", ".bin",
})


def sanitize_filename(filename: str) -> str:
    """Sanitize and validate an uploaded filename. Rejects path traversal and dangerous extensions."""
    if not isinstance(filename, str) or not filename.strip():
        raise DocumentValidationError("Filename cannot be empty")
    
    clean = filename.strip()
    
    if "/" in clean or "\\" in clean or ".." in clean:
        raise DocumentSecurityError(f"Path-like filenames or traversal components are rejected: {clean}")
    
    if len(clean) > 255:
        raise DocumentValidationError("Filename length exceeds 255 characters")
    
    lower = clean.lower()
    for ext in REJECTED_EXTENSIONS:
        if lower.endswith(ext):
            raise UnsupportedMediaTypeError(f"Files with extension '{ext}' are strictly rejected")
    
    if not (lower.endswith(".pdf") or lower.endswith(".txt")):
        raise UnsupportedMediaTypeError(f"Unsupported document extension: {clean}. Only .pdf and .txt are supported.")
    
    return clean


def validate_document_bytes(
    raw: bytes,
    filename: str,
    limits: DocumentLimits = DocumentLimits(),
) -> tuple[SupportedMediaType, int | None]:
    """Validate document raw bytes, magic number signature, security rules, and bounds.
    
    Returns (media_type, estimated_page_count).
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise DocumentValidationError("Document content must be raw bytes")
    
    size = len(raw)
    if size < limits.min_file_size_bytes:
        raise DocumentValidationError("Document is empty (0 bytes)")
    if size > limits.max_file_size_bytes:
        raise DocumentSizeLimitError(
            f"Document size ({size} bytes) exceeds limit of {limits.max_file_size_bytes} bytes (30 MB)"
        )

    if raw.startswith(b"PK\x03\x04"):
        raise UnsupportedMediaTypeError("ZIP archive files are strictly rejected")
    if raw.startswith(b"\x1f\x8b"):
        raise UnsupportedMediaTypeError("GZIP compressed files are strictly rejected")
    if raw.startswith(b"MZ"):
        raise DocumentSecurityError("DOS/Windows PE executable files are strictly rejected")
    if raw.startswith(b"\x7fELF"):
        raise DocumentSecurityError("ELF binary executables are strictly rejected")
    if raw.startswith(b"7z\xbc\xaf\x27\x1c"):
        raise UnsupportedMediaTypeError("7-Zip archive files are strictly rejected")
    if raw.startswith(b"Rar!\x1a\x07"):
        raise UnsupportedMediaTypeError("RAR archive files are strictly rejected")
    if raw.startswith(b"\xca\xfe\xba\xbe") or raw.startswith(b"\xfe\xed\xfa\xce"):
        raise DocumentSecurityError("Binary executable or Java class files are strictly rejected")

    clean_name = sanitize_filename(filename)
    lower_name = clean_name.lower()

    if lower_name.endswith(".pdf"):
        if not raw.startswith(b"%PDF-"):
            raise UnsupportedMediaTypeError("File has .pdf extension but lacks '%PDF-' signature")
        
        if re.search(rb"/Encrypt\b", raw):
            raise DocumentSecurityError("Encrypted or password-protected PDF files are not supported")
        
        if re.search(rb"/(JavaScript|JS|Launch|Action)\b", raw):
            raise DocumentSecurityError("PDF contains active scripts, macros, or launch actions which are prohibited")
        
        page_matches = re.findall(rb"/Type\s*/Page\b", raw)
        page_count = len(page_matches) if page_matches else None
        
        if page_count is not None and page_count > limits.max_pages:
            raise DocumentContentLimitError(
                f"PDF estimated page count ({page_count}) exceeds limit of {limits.max_pages} pages"
            )
        
        return SupportedMediaType.PDF, page_count

    elif lower_name.endswith(".txt"):
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedMediaTypeError("Plain text document must be valid UTF-8") from exc
        
        if "\x00" in decoded:
            raise UnsupportedMediaTypeError("Plain text document cannot contain binary NUL bytes")
        
        return SupportedMediaType.PLAIN_TEXT, 1

    raise UnsupportedMediaTypeError(f"Unsupported document format for '{clean_name}'")


# -----------------------------------------------------------------------------
# 6. Ingestion & Extraction Engine
# -----------------------------------------------------------------------------

def ingest_document(
    raw: bytes,
    filename: str,
    source_provider: str,
    privacy: str = PrivacyClassification.PRIVATE.value,
    limits: DocumentLimits = DocumentLimits(),
) -> DocumentRecord:
    """Ingest an uploaded document, performing strict validation, signature checks, and ID assignment."""
    if not isinstance(source_provider, str) or not source_provider.strip():
        raise DocumentValidationError("Source/provider label is mandatory and cannot be empty")
    
    clean_filename = sanitize_filename(filename)
    media_type, page_count = validate_document_bytes(raw, clean_filename, limits)
    
    digest = hashlib.sha256(raw).hexdigest()
    doc_id = f"doc-{digest}"
    
    identity = DocumentIdentity(
        id=doc_id,
        original_filename=clean_filename,
        media_type=media_type.value,
        byte_size=len(raw),
        sha256=digest,
        ingested_at=utc_iso_now(),
        page_count=page_count,
        extraction_method="unextracted",
        source_provider=source_provider.strip(),
        privacy=privacy,
        state=DocumentState.UPLOADED.value,
    )
    return DocumentRecord(identity=identity, blocks=(), review=None, state=DocumentState.UPLOADED.value)


def extract_plain_text_blocks(
    doc: DocumentRecord,
    text: str,
    limits: DocumentLimits = DocumentLimits(),
) -> DocumentRecord:
    """Extract page-level or paragraph-level blocks from plain text without external dependencies."""
    if doc.state != DocumentState.UPLOADED.value:
        raise InvalidDocumentStateTransitionError(
            f"Cannot extract document in state '{doc.state}'. Must be '{DocumentState.UPLOADED.value}'."
        )

    if not isinstance(text, str):
        raise DocumentValidationError("Text to extract must be a string")
    
    if len(text) > limits.max_total_characters:
        raise DocumentContentLimitError(
            f"Extracted character count ({len(text)}) exceeds maximum allowed ({limits.max_total_characters})"
        )

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    blocks: list[ExtractionBlock] = []
    doc_prefix = doc.identity.sha256[:8]

    if not paragraphs:
        block = ExtractionBlock(
            document_id=doc.identity.id,
            page_number=1,
            block_id=f"blk-{doc_prefix}-p1-1",
            extracted_text="",
            extraction_status="empty",
            warnings=("Document contained no non-empty text blocks",),
        )
        blocks.append(block)
    else:
        for idx, para in enumerate(paragraphs, start=1):
            if len(para) > limits.max_characters_per_page:
                raise DocumentContentLimitError(
                    f"Block {idx} character count ({len(para)}) exceeds maximum per-page limit ({limits.max_characters_per_page})"
                )
            block = ExtractionBlock(
                document_id=doc.identity.id,
                page_number=1,
                block_id=f"blk-{doc_prefix}-p1-{idx}",
                extracted_text=para,
                extraction_status="success",
                warnings=(),
            )
            blocks.append(block)

    identity_dict = doc.identity.to_dict()
    identity_dict["extraction_method"] = "plaintext-v1"
    identity_dict["state"] = DocumentState.EXTRACTED.value
    new_identity = DocumentIdentity.from_dict(identity_dict)

    return DocumentRecord(
        identity=new_identity,
        blocks=tuple(blocks),
        review=None,
        state=DocumentState.EXTRACTED.value,
    )


def extract_pdf_stub_blocks(
    doc: DocumentRecord,
    custom_blocks: list[ExtractionBlock] | None = None,
    limits: DocumentLimits = DocumentLimits(),
) -> DocumentRecord:
    """Model PDF extraction blocks without requiring external parser dependencies.
    
    Accepts explicit custom_blocks (e.g. from tests or subsequent extraction adapters).
    If custom_blocks is None, creates an initial draft extraction record indicating
    that extraction is pending parser configuration.
    """
    if doc.state != DocumentState.UPLOADED.value:
        raise InvalidDocumentStateTransitionError(
            f"Cannot extract document in state '{doc.state}'. Must be '{DocumentState.UPLOADED.value}'."
        )

    doc_prefix = doc.identity.sha256[:8]
    blocks: list[ExtractionBlock] = []

    if custom_blocks is not None:
        total_chars = sum(len(b.extracted_text) for b in custom_blocks)
        if total_chars > limits.max_total_characters:
            raise DocumentContentLimitError(
                f"Total extracted characters ({total_chars}) exceeds limit ({limits.max_total_characters})"
            )
        for b in custom_blocks:
            if len(b.extracted_text) > limits.max_characters_per_page:
                raise DocumentContentLimitError(
                    f"Page {b.page_number} characters ({len(b.extracted_text)}) exceeds limit ({limits.max_characters_per_page})"
                )
            if b.document_id != doc.identity.id:
                raise DocumentValidationError(f"Block document ID mismatch: {b.document_id} vs {doc.identity.id}")
            blocks.append(b)
    else:
        page_num = 1
        block = ExtractionBlock(
            document_id=doc.identity.id,
            page_number=page_num,
            block_id=f"blk-{doc_prefix}-p{page_num}-1",
            extracted_text="[Draft PDF text extraction pending specialized adapter]",
            extraction_status="partial",
            warnings=("PDF parser adapter pending; unverified draft representation",),
        )
        blocks.append(block)

    identity_dict = doc.identity.to_dict()
    identity_dict["extraction_method"] = "pdf-stub-v1" if custom_blocks is None else "custom-adapter-v1"
    identity_dict["state"] = DocumentState.EXTRACTED.value
    new_identity = DocumentIdentity.from_dict(identity_dict)

    return DocumentRecord(
        identity=new_identity,
        blocks=tuple(blocks),
        review=None,
        state=DocumentState.EXTRACTED.value,
    )


# -----------------------------------------------------------------------------
# 7. Review & State Transitions
# -----------------------------------------------------------------------------

def submit_document_for_review(doc: DocumentRecord) -> DocumentRecord:
    """Transition extracted document to 'needs_review'."""
    if doc.state != DocumentState.EXTRACTED.value:
        raise InvalidDocumentStateTransitionError(
            f"Cannot submit for review from state '{doc.state}'. Must be '{DocumentState.EXTRACTED.value}'."
        )
    
    identity_dict = doc.identity.to_dict()
    identity_dict["state"] = DocumentState.NEEDS_REVIEW.value
    new_identity = DocumentIdentity.from_dict(identity_dict)
    
    return DocumentRecord(
        identity=new_identity,
        blocks=doc.blocks,
        review=None,
        state=DocumentState.NEEDS_REVIEW.value,
    )


def review_and_accept_document(
    doc: DocumentRecord,
    reviewer_rationale: str,
    confirmed_statement: str,
    reviewed_block_ids: list[str],
    private_note: str = "",
) -> DocumentRecord:
    """Promote a reviewed document extraction to 'accepted_as_evidence' after validating review rationale and statement."""
    if doc.state not in (DocumentState.NEEDS_REVIEW.value, DocumentState.REJECTED.value):
        raise InvalidDocumentStateTransitionError(
            f"Cannot accept document from state '{doc.state}'. Must be '{DocumentState.NEEDS_REVIEW.value}' or '{DocumentState.REJECTED.value}'."
        )

    statement_violations = validate_document_claims(confirmed_statement)
    if statement_violations:
        raise ProhibitedDocumentClaimError(
            f"Confirmed statement contains prohibited claims: {'; '.join(statement_violations)}"
        )
    rationale_violations = validate_document_claims(reviewer_rationale)
    if rationale_violations:
        raise ProhibitedDocumentClaimError(
            f"Reviewer rationale contains prohibited claims: {'; '.join(rationale_violations)}"
        )

    block_dict = {b.block_id: b for b in doc.blocks}
    if not reviewed_block_ids:
        raise DocumentCitationError("Review must cite at least one valid block ID")
    
    pages: set[int] = set()
    for bid in reviewed_block_ids:
        if bid not in block_dict:
            raise DocumentCitationError(f"Cited block ID '{bid}' not found in document extraction blocks")
        pages.add(block_dict[bid].page_number)

    review = DocumentReview(
        document_id=doc.identity.id,
        reviewed_at=utc_iso_now(),
        reviewer_rationale=reviewer_rationale.strip(),
        reviewed_blocks=tuple(sorted(reviewed_block_ids)),
        reviewed_pages=tuple(sorted(pages)),
        source_digest=doc.identity.sha256,
        confirmed_statement=confirmed_statement.strip(),
        private_note=private_note.strip(),
    )

    identity_dict = doc.identity.to_dict()
    identity_dict["state"] = DocumentState.ACCEPTED_AS_EVIDENCE.value
    new_identity = DocumentIdentity.from_dict(identity_dict)

    return DocumentRecord(
        identity=new_identity,
        blocks=doc.blocks,
        review=review,
        state=DocumentState.ACCEPTED_AS_EVIDENCE.value,
    )


def reject_document(doc: DocumentRecord, rationale: str) -> DocumentRecord:
    """Reject a document extraction."""
    if doc.state not in (DocumentState.NEEDS_REVIEW.value, DocumentState.ACCEPTED_AS_EVIDENCE.value):
        raise InvalidDocumentStateTransitionError(
            f"Cannot reject document from state '{doc.state}'. Must be in review or accepted."
        )
    if not isinstance(rationale, str) or not rationale.strip():
        raise DocumentValidationError("Rejection rationale is required")

    identity_dict = doc.identity.to_dict()
    identity_dict["state"] = DocumentState.REJECTED.value
    new_identity = DocumentIdentity.from_dict(identity_dict)

    return DocumentRecord(
        identity=new_identity,
        blocks=doc.blocks,
        review=None,
        state=DocumentState.REJECTED.value,
    )


# -----------------------------------------------------------------------------
# 8. Evidence Promotion Contract
# -----------------------------------------------------------------------------

def document_to_evidence_record(
    doc: DocumentRecord,
    block_id: str,
    geographic_scope: str = "Local document context (uncalibrated)",
    kind: str = "policy statement",
) -> dict[str, Any]:
    """Convert an accepted document extraction block into a standard BASIN evidence record."""
    if doc.state != DocumentState.ACCEPTED_AS_EVIDENCE.value or doc.review is None:
        raise DocumentValidationError("Only human-accepted document records can be converted to evidence")

    if block_id not in doc.review.reviewed_blocks:
        raise DocumentCitationError(
            f"Block ID '{block_id}' was not included in the accepted review for document {doc.identity.id}"
        )

    block = next((b for b in doc.blocks if b.block_id == block_id), None)
    if block is None:
        raise DocumentCitationError(f"Block ID '{block_id}' not found in document blocks")

    evidence_id = f"doc-ev-{block.digest[:16]}"
    source_locator = f"doc://{doc.identity.id}/page/{block.page_number}"
    
    desc = (
        f"Source: User-provided document '{doc.identity.original_filename}' by '{doc.identity.source_provider}' (unverified). "
        f"Cited page {block.page_number}, block {block.block_id}. "
        f"Confirmed statement: {doc.review.confirmed_statement}. "
        f"Review rationale: {doc.review.reviewer_rationale}. "
        f"Document SHA-256: {doc.identity.sha256}. "
        f"Supporting evidence only; {DOCUMENT_CATCHMENT_DISCLAIMER} User review is not scientific validation."
    )

    return {
        "id": evidence_id,
        "title": f"Document Evidence: {doc.identity.source_provider} (Page {block.page_number})",
        "publisher": doc.identity.source_provider,
        "source_locator": source_locator,
        "source_date": doc.identity.ingested_at[:10],
        "retrieved_at": doc.identity.ingested_at,
        "geographic_scope": geographic_scope,
        "kind": kind if kind in ("policy statement", "user assumption") else "policy statement",
        "units": "",
        "description": desc,
        "review_status": "reviewed for this exercise",
        "private_note": doc.review.private_note,
    }


# -----------------------------------------------------------------------------
# 9. Privacy & Export Filtering
# -----------------------------------------------------------------------------

def filter_documents_for_export(
    records: list[DocumentRecord],
    include_notes: bool = False,
    include_all_states: bool = False,
) -> list[dict[str, Any]]:
    """Filter document records for bundle exports according to consent rules.
    
    - Raw file bytes are NEVER included in export dictionaries.
    - Default export includes only 'accepted_as_evidence' records.
    - Private reviewer notes are excluded unless include_notes is True.
    """
    exported: list[dict[str, Any]] = []
    for rec in records:
        if not include_all_states and rec.state != DocumentState.ACCEPTED_AS_EVIDENCE.value:
            continue
        
        doc_dict = rec.to_dict()
        if not include_notes and doc_dict.get("review"):
            doc_dict["review"]["private_note"] = ""
        exported.append(doc_dict)
    
    return exported
