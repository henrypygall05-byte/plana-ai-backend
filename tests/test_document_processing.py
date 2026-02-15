"""
Tests for the document processing pipeline, gating logic, and report wording.

Covers the three required scenarios:
1) Drawings only (text=0, metadata present) → report allowed, not "missing plans"
2) Mix of text PDFs + drawings → report allowed, evidence improved
3) Queued docs → 202 processing_documents
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from plana.api.models import (
    DocumentProcessingResponse,
    DocumentsSummaryResponse,
    ExtractionStatusResponse,
    ProcessingStatusResponse,
)
from plana.core.models import DocumentExtractionStatus
from plana.documents.ingestion import (
    DocumentCategory,
    DocumentIngestionResult,
    ExtractionStatus,
    ProcessedDocument,
    _compute_evidence_quality,
)
from plana.documents.processor import (
    DrawingMetadata,
    check_plan_set_present,
    extract_drawing_metadata,
    is_plan_or_drawing_heuristic,
)
from plana.report.generator import ApplicationData, ReportGenerator
from plana.storage.database import Database
from plana.storage.models import StoredDocument


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    db = Database(db_path)
    yield db
    db_path.unlink(missing_ok=True)


def _make_processed_doc(
    doc_id: str,
    title: str,
    category: DocumentCategory,
    extraction_status: ExtractionStatus = ExtractionStatus.NOT_ATTEMPTED,
    extracted_text: str = "",
    filename: str = "",
) -> ProcessedDocument:
    """Helper to create a ProcessedDocument for testing."""
    return ProcessedDocument(
        doc_id=doc_id,
        title=title,
        filename=filename or f"{title.lower().replace(' ', '_')}.pdf",
        category=category,
        classification_confidence=0.85,
        extraction_status=extraction_status,
        extracted_text=extracted_text,
    )


def _make_ingestion(docs: list[ProcessedDocument]) -> DocumentIngestionResult:
    """Build a DocumentIngestionResult from a list of ProcessedDocuments."""
    result = DocumentIngestionResult(
        documents=docs,
        total_count=len(docs),
        plans_count=sum(1 for d in docs if d.is_plan),
        key_docs_count=sum(1 for d in docs if d.is_key_document),
        extracted_count=sum(
            1 for d in docs
            if d.extraction_status == ExtractionStatus.SUCCESS
        ),
        failed_count=sum(
            1 for d in docs
            if d.extraction_status == ExtractionStatus.FAILED
        ),
    )
    result.evidence_quality = _compute_evidence_quality(result)
    return result


# ===========================================================================
# Test 1: Drawings only (text=0, metadata present)
# → report allowed, NOT "missing plans"
# ===========================================================================


class TestDrawingsOnly:
    """Scenario: All documents are plan drawings with zero extracted text
    but metadata (classification) is present."""

    def test_plan_set_detected_from_drawings(self):
        """Plan set should be detected even with zero extracted text."""
        categories = [
            DocumentCategory.SITE_PLAN,
            DocumentCategory.ELEVATION,
            DocumentCategory.FLOOR_PLAN,
        ]
        assert check_plan_set_present(categories) is True

    def test_evidence_quality_not_low_for_drawings(self):
        """Evidence quality must NOT be LOW when drawings are classified."""
        docs = [
            _make_processed_doc("d1", "Site Plan", DocumentCategory.SITE_PLAN,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d2", "Proposed Elevations", DocumentCategory.ELEVATION,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d3", "Floor Plans", DocumentCategory.FLOOR_PLAN,
                                ExtractionStatus.FAILED),
        ]
        ingestion = _make_ingestion(docs)

        # All extraction failed, but plans are classified → NOT LOW
        assert ingestion.evidence_quality != "LOW"
        assert ingestion.evidence_quality in ("MEDIUM", "HIGH")

    def test_report_not_claims_missing_plans(self):
        """Report must NOT say 'No submitted plans have been provided'
        when drawings exist but text=0."""
        docs = [
            _make_processed_doc("d1", "Site Plan", DocumentCategory.SITE_PLAN,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d2", "Proposed Elevations", DocumentCategory.ELEVATION,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d3", "Ground Floor Plan", DocumentCategory.FLOOR_PLAN,
                                ExtractionStatus.FAILED),
        ]
        ingestion = _make_ingestion(docs)

        summary = ReportGenerator._generate_documents_summary(ingestion, documents_count=3)

        # Must NOT contain "no documents" or "no plan-type"
        assert "No documents were submitted" not in summary
        assert "No submitted plans" not in summary
        # SHOULD mention that text extraction produced limited content
        assert "limited text content" in summary or "Plan set status" in summary
        # Should show plan set as present
        assert "plan drawings" in summary.lower() or "Plan set status" in summary

    def test_material_info_not_claims_plans_missing(self):
        """Material info must NOT list 'Submitted plans missing' when
        plan set is present (even with zero extracted text)."""
        docs = [
            _make_processed_doc("d1", "Site Plan", DocumentCategory.SITE_PLAN,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d2", "Proposed Elevations", DocumentCategory.ELEVATION,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d3", "Floor Plans", DocumentCategory.FLOOR_PLAN,
                                ExtractionStatus.FAILED),
        ]
        ingestion = _make_ingestion(docs)

        app = ApplicationData(
            reference="TEST/001",
            address="1 Test Street",
            proposal="Test proposal",
            application_type="Full Planning",
            constraints=[],
            documents_count=3,
            documents_verified=True,
            document_ingestion=ingestion,
        )

        section = ReportGenerator._generate_material_info_missing(
            app, ingestion, evidence_map=None, planning_facts=None,
        )

        # Must NOT say the LPA cannot lawfully determine due to missing plans
        assert "lawfully determine" not in section
        # Plan set is present — should reference officer verification
        assert "Plan set has been received" in section or "Officer" in section

    def test_drawing_metadata_extraction(self):
        """Drawing metadata should be extractable from filename alone."""
        meta = extract_drawing_metadata(
            "proposed_elevations.pdf",
            DocumentCategory.ELEVATION,
        )
        assert meta.document_type_guess == "elevation"
        assert meta.to_json()  # Should be serializable

    def test_is_plan_or_drawing_heuristic(self):
        """Plan/drawing detection should work for various naming patterns."""
        assert is_plan_or_drawing_heuristic("Site Plan 01.pdf") is True
        assert is_plan_or_drawing_heuristic("PROPOSED_ELEVATIONS.PDF") is True
        assert is_plan_or_drawing_heuristic("floor_plan_ground.pdf") is True
        assert is_plan_or_drawing_heuristic("cover_letter.docx") is False
        assert is_plan_or_drawing_heuristic("photo.png") is True  # image → could be plan
        assert is_plan_or_drawing_heuristic("ecology_report.pdf") is False


# ===========================================================================
# Test 2: Mix of text PDFs + drawings
# → report allowed, evidence improved
# ===========================================================================


class TestMixedDocuments:
    """Scenario: Some documents have extracted text (D&A statement) and
    some are drawings with zero text."""

    def test_evidence_quality_high_for_mixed(self):
        """Evidence quality should be HIGH when plans + statements + some extracted."""
        docs = [
            _make_processed_doc("d1", "Site Plan", DocumentCategory.SITE_PLAN,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d2", "Proposed Elevations", DocumentCategory.ELEVATION,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d3", "Design and Access Statement",
                                DocumentCategory.DESIGN_ACCESS_STATEMENT,
                                ExtractionStatus.SUCCESS,
                                extracted_text="This 2-storey extension..."),
            _make_processed_doc("d4", "Heritage Statement",
                                DocumentCategory.HERITAGE_STATEMENT,
                                ExtractionStatus.SUCCESS,
                                extracted_text="The site is within..."),
            _make_processed_doc("d5", "Floor Plans", DocumentCategory.FLOOR_PLAN,
                                ExtractionStatus.FAILED),
        ]
        ingestion = _make_ingestion(docs)

        # Has plans + statements + 2 key extracted → HIGH
        assert ingestion.evidence_quality == "HIGH"

    def test_plan_set_present_in_mixed(self):
        """Plan set should be detected in mixed document set."""
        categories = [
            DocumentCategory.SITE_PLAN,
            DocumentCategory.ELEVATION,
            DocumentCategory.DESIGN_ACCESS_STATEMENT,
            DocumentCategory.HERITAGE_STATEMENT,
            DocumentCategory.FLOOR_PLAN,
        ]
        assert check_plan_set_present(categories) is True

    def test_report_summary_shows_plan_set_complete(self):
        """Report summary should show plan set as complete."""
        docs = [
            _make_processed_doc("d1", "Site Plan", DocumentCategory.SITE_PLAN,
                                ExtractionStatus.FAILED),
            _make_processed_doc("d2", "Proposed Elevations", DocumentCategory.ELEVATION,
                                ExtractionStatus.PARTIAL,
                                extracted_text="ridge 8.5m"),
            _make_processed_doc("d3", "D&A Statement",
                                DocumentCategory.DESIGN_ACCESS_STATEMENT,
                                ExtractionStatus.SUCCESS,
                                extracted_text="The proposal involves a 2-storey extension"),
        ]
        ingestion = _make_ingestion(docs)

        summary = ReportGenerator._generate_documents_summary(ingestion, documents_count=3)

        assert "Plan set status" in summary
        assert "Complete" in summary
        assert "No documents were submitted" not in summary

    def test_processing_status_ready_mixed(self):
        """Processing status should be ready when all processed."""
        status = DocumentExtractionStatus(
            queued=0, processing=0, processed=5, failed=0, extracted=2,
        )
        assert status.is_ready_for_report is True
        assert status.is_processing is False


# ===========================================================================
# Test 3: Queued docs → 202 processing_documents
# ===========================================================================


class TestQueuedDocuments:
    """Scenario: Documents exist but are still queued/processing."""

    def test_processing_status_not_ready_while_queued(self):
        """is_ready_for_report must be False while docs are queued."""
        status = DocumentExtractionStatus(
            queued=26, processing=0, processed=0, failed=0,
        )
        assert status.is_ready_for_report is False
        assert status.is_processing is True

    def test_processing_status_not_ready_while_processing(self):
        """is_ready_for_report must be False while docs are processing."""
        status = DocumentExtractionStatus(
            queued=10, processing=5, processed=11, failed=0,
        )
        assert status.is_ready_for_report is False
        assert status.is_processing is True

    def test_202_response_shape(self):
        """HTTP 202 response should have the required JSON shape."""
        resp = DocumentProcessingResponse(
            status="processing_documents",
            extraction_status=ExtractionStatusResponse(
                queued=26, extracted=0, failed=0,
            ),
            documents=ProcessingStatusResponse(
                total=26, queued=26, processing=0, processed=0, failed=0,
            ),
        )
        data = resp.model_dump()

        assert data["status"] == "processing_documents"
        assert data["documents"]["total"] == 26
        assert data["documents"]["queued"] == 26
        assert data["documents"]["processed"] == 0
        assert data["documents"]["failed"] == 0

    def test_db_processing_counts_queued(self, tmp_db):
        """DB should report correct processing counts for queued docs."""
        for i in range(5):
            tmp_db.save_document(StoredDocument(
                reference="TEST/Q",
                doc_id=f"doc_{i}",
                title=f"Document {i}",
                doc_type="plans",
                processing_status="queued",
            ))
        counts = tmp_db.get_processing_counts("TEST/Q")
        assert counts["total"] == 5
        assert counts["queued"] == 5
        assert counts["processed"] == 0

    def test_db_processing_counts_mixed(self, tmp_db):
        """DB should report correct processing counts for mixed states."""
        statuses = ["queued", "processing", "processed", "processed", "failed"]
        for i, status in enumerate(statuses):
            tmp_db.save_document(StoredDocument(
                reference="TEST/M",
                doc_id=f"doc_{i}",
                title=f"Document {i}",
                doc_type="plans",
                processing_status=status,
                extracted_text_chars=100 if status == "processed" else 0,
                is_plan_or_drawing=True if i < 3 else False,
                has_any_content_signal=True if status == "processed" else False,
            ))
        counts = tmp_db.get_processing_counts("TEST/M")
        assert counts["total"] == 5
        assert counts["queued"] == 1
        assert counts["processing"] == 1
        assert counts["processed"] == 2
        assert counts["failed"] == 1
        assert counts["total_text_chars"] == 200
        assert counts["with_content_signal"] == 2
        assert counts["plan_drawing_count"] == 3

    def test_ready_after_all_processed(self):
        """Report should be allowed once all docs are processed (even if text=0)."""
        status = DocumentExtractionStatus(
            queued=0, processing=0, processed=5, failed=0, extracted=0,
        )
        assert status.is_ready_for_report is True
        assert status.is_processing is False

    def test_ready_after_all_failed(self):
        """Report should be allowed when all docs failed (nothing queued)."""
        status = DocumentExtractionStatus(
            queued=0, processing=0, processed=0, failed=5, extracted=0,
        )
        assert status.is_ready_for_report is True
        assert status.is_processing is False

    def test_not_ready_with_zero_docs(self):
        """No documents at all → not ready (but also not processing)."""
        status = DocumentExtractionStatus(
            queued=0, processing=0, processed=0, failed=0,
        )
        assert status.is_ready_for_report is False
        assert status.is_processing is False


# ===========================================================================
# Additional edge cases
# ===========================================================================


class TestPlanSetPresence:
    """Plan set presence check edge cases."""

    def test_site_plan_only_not_complete(self):
        assert check_plan_set_present([DocumentCategory.SITE_PLAN]) is False

    def test_elevations_only_not_complete(self):
        assert check_plan_set_present([DocumentCategory.ELEVATION]) is False

    def test_location_and_sections(self):
        assert check_plan_set_present([
            DocumentCategory.LOCATION_PLAN,
            DocumentCategory.SECTION_DRAWING,
        ]) is True

    def test_from_filenames(self):
        assert check_plan_set_present(
            categories=[],
            filenames=["SITE_PLAN_01.pdf", "PROPOSED_ELEVATIONS.pdf"],
        ) is True

    def test_from_metadata_guesses(self):
        assert check_plan_set_present(
            categories=[],
            metadata_guesses=["site plan", "floor plan"],
        ) is True

    def test_unrelated_docs_not_complete(self):
        assert check_plan_set_present([
            DocumentCategory.COVER_LETTER,
            DocumentCategory.PHOTOGRAPH,
            DocumentCategory.OTHER,
        ]) is False


class TestStoredDocumentNewFields:
    """Test that new StoredDocument fields persist correctly."""

    def test_save_and_retrieve_with_new_fields(self, tmp_db):
        """New fields should round-trip through save/get."""
        meta = DrawingMetadata(
            document_type_guess="site plan",
            key_labels_found=["scale", "boundary"],
            any_scale_detected=True,
        )
        doc = StoredDocument(
            reference="TEST/F",
            doc_id="doc_1",
            title="Site Plan",
            doc_type="plans",
            mime_type="application/pdf",
            processing_status="processed",
            extract_method="drawing_only",
            extracted_text_chars=0,
            extracted_metadata_json=meta.to_json(),
            is_plan_or_drawing=True,
            is_scanned=True,
            has_any_content_signal=True,
        )
        tmp_db.save_document(doc)

        docs = tmp_db.get_documents("TEST/F")
        assert len(docs) == 1
        d = docs[0]
        assert d.processing_status == "processed"
        assert d.extract_method == "drawing_only"
        assert d.extracted_text_chars == 0
        assert d.is_plan_or_drawing is True
        assert d.is_scanned is True
        assert d.has_any_content_signal is True
        assert d.mime_type == "application/pdf"

        # Verify metadata round-trip
        loaded_meta = DrawingMetadata.from_json(d.extracted_metadata_json)
        assert loaded_meta.document_type_guess == "site plan"
        assert "scale" in loaded_meta.key_labels_found
        assert loaded_meta.any_scale_detected is True
