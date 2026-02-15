"""
Tests for the document extraction worker.

Verifies the full lifecycle: queued → processing → processed / failed.
"""

import json
import tempfile
from pathlib import Path

import pytest

from plana.storage.database import Database
from plana.storage.models import StoredDocument


@pytest.fixture()
def tmp_db(tmp_path):
    """Provide a fresh, migrated SQLite database for each test."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    yield db


def _make_doc(reference: str, doc_id: str, **overrides) -> StoredDocument:
    return StoredDocument(
        application_id=1,
        reference=reference,
        doc_id=doc_id,
        title=overrides.pop("title", f"Doc {doc_id}"),
        doc_type=overrides.pop("doc_type", "PDF"),
        processing_status="queued",
        extraction_status="queued",
        **overrides,
    )


# ---------- Database claim / mark methods ----------


class TestClaimQueuedDocument:
    """Tests for the atomic claim_queued_document() method."""

    def test_claims_one_queued_doc(self, tmp_db):
        tmp_db.save_document(_make_doc("REF/1", "d1"))
        tmp_db.save_document(_make_doc("REF/1", "d2"))

        claimed = tmp_db.claim_queued_document()
        assert claimed is not None
        assert claimed.processing_status == "processing"
        assert claimed.doc_id in ("d1", "d2")

    def test_returns_none_when_empty(self, tmp_db):
        assert tmp_db.claim_queued_document() is None

    def test_does_not_double_claim(self, tmp_db):
        tmp_db.save_document(_make_doc("REF/1", "only"))

        first = tmp_db.claim_queued_document()
        assert first is not None

        second = tmp_db.claim_queued_document()
        assert second is None  # no more queued

    def test_skips_already_processing(self, tmp_db):
        doc = _make_doc("REF/1", "busy")
        doc.processing_status = "processing"
        tmp_db.save_document(doc)

        assert tmp_db.claim_queued_document() is None

    def test_skips_already_processed(self, tmp_db):
        doc = _make_doc("REF/1", "done")
        doc.processing_status = "processed"
        tmp_db.save_document(doc)

        assert tmp_db.claim_queued_document() is None


class TestMarkDocumentProcessed:

    def test_mark_processed(self, tmp_db):
        tmp_db.save_document(_make_doc("REF/1", "d1"))
        tmp_db.mark_document_processed(
            "d1",
            extract_method="pdf_text",
            extracted_text_chars=500,
            is_plan_or_drawing=False,
            is_scanned=False,
            has_any_content_signal=True,
        )
        doc = tmp_db.get_document_by_doc_id("d1")
        assert doc.processing_status == "processed"
        assert doc.extraction_status == "extracted"
        assert doc.extract_method == "pdf_text"
        assert doc.extracted_text_chars == 500
        assert doc.has_any_content_signal is True

    def test_mark_processed_with_metadata(self, tmp_db):
        tmp_db.save_document(_make_doc("REF/1", "d2"))
        meta = json.dumps({"document_type_guess": "site plan"})
        tmp_db.mark_document_processed(
            "d2",
            extract_method="drawing_only",
            extracted_text_chars=0,
            extracted_metadata_json=meta,
            is_plan_or_drawing=True,
            is_scanned=False,
            has_any_content_signal=True,
        )
        doc = tmp_db.get_document_by_doc_id("d2")
        assert doc.is_plan_or_drawing is True
        assert doc.extracted_metadata_json == meta


class TestMarkDocumentFailed:

    def test_mark_failed(self, tmp_db):
        tmp_db.save_document(_make_doc("REF/1", "d1"))
        tmp_db.mark_document_failed("d1")
        doc = tmp_db.get_document_by_doc_id("d1")
        assert doc.processing_status == "failed"
        assert doc.extraction_status == "failed"


# ---------- Worker process_one ----------


class TestProcessOne:
    """Tests for the worker's process_one() function."""

    def test_processes_text_file(self, tmp_db, tmp_path):
        # Create a real text file to extract from
        txt = tmp_path / "design_statement.txt"
        txt.write_text("This is a design and access statement for the proposal.")

        doc = _make_doc(
            "REF/1", "txt1",
            title="Design and Access Statement.txt",
            local_path=str(txt),
            mime_type="text/plain",
        )
        tmp_db.save_document(doc)
        doc.processing_status = "processing"  # simulate claim

        from plana.documents.worker import process_one
        process_one(doc, tmp_db)

        result = tmp_db.get_document_by_doc_id("txt1")
        assert result.processing_status == "processed"
        assert result.extracted_text_chars > 0
        assert result.has_any_content_signal is True

    def test_processes_missing_file_as_drawing(self, tmp_db):
        doc = _make_doc(
            "REF/1", "plan1",
            title="Site Plan - Proposed.pdf",
            local_path="/nonexistent/path/site_plan.pdf",
            mime_type="application/pdf",
        )
        tmp_db.save_document(doc)
        doc.processing_status = "processing"

        from plana.documents.worker import process_one
        process_one(doc, tmp_db)

        result = tmp_db.get_document_by_doc_id("plan1")
        assert result.processing_status == "processed"
        assert result.is_plan_or_drawing is True
        assert result.extract_method == "drawing_only"
        assert result.extracted_metadata_json is not None

    def test_processes_image_file_as_drawing(self, tmp_db, tmp_path):
        img = tmp_path / "elevation.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        doc = _make_doc(
            "REF/1", "img1",
            title="Proposed Elevation.png",
            local_path=str(img),
            mime_type="image/png",
        )
        tmp_db.save_document(doc)
        doc.processing_status = "processing"

        from plana.documents.worker import process_one
        process_one(doc, tmp_db)

        result = tmp_db.get_document_by_doc_id("img1")
        assert result.processing_status == "processed"
        assert result.is_plan_or_drawing is True


# ---------- drain_queue integration ----------


class TestDrainQueue:
    """Integration test: queue several documents, drain them all."""

    def test_drains_all_queued(self, tmp_db, tmp_path):
        # Create real files
        for i in range(4):
            f = tmp_path / f"doc_{i}.txt"
            f.write_text(f"Document number {i} content.")
            tmp_db.save_document(_make_doc(
                "REF/DRAIN", f"drain_{i}",
                title=f"Document {i}.txt",
                local_path=str(f),
            ))

        from plana.documents.worker import drain_queue
        count = drain_queue(tmp_db)
        assert count == 4

        # All should be processed
        counts = tmp_db.get_processing_counts("REF/DRAIN")
        assert counts["queued"] == 0
        assert counts["processed"] == 4

    def test_drain_empty_queue(self, tmp_db):
        from plana.documents.worker import drain_queue
        count = drain_queue(tmp_db)
        assert count == 0

    def test_drain_skips_already_processed(self, tmp_db, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("already done")
        doc = _make_doc("REF/SKIP", "skip1", local_path=str(f))
        doc.processing_status = "processed"
        tmp_db.save_document(doc)

        # Queue one new doc
        f2 = tmp_path / "new.txt"
        f2.write_text("new content")
        tmp_db.save_document(_make_doc(
            "REF/SKIP", "skip2",
            title="New.txt",
            local_path=str(f2),
        ))

        from plana.documents.worker import drain_queue
        count = drain_queue(tmp_db)
        assert count == 1  # only the queued one

        counts = tmp_db.get_processing_counts("REF/SKIP")
        assert counts["queued"] == 0
        assert counts["processed"] == 2


class TestProcessingCountsAfterWorker:
    """Verify that get_processing_counts reflects worker transitions."""

    def test_counts_transition(self, tmp_db, tmp_path):
        f = tmp_path / "report.txt"
        f.write_text("Planning statement content here.")

        tmp_db.save_document(_make_doc(
            "REF/CNT", "cnt1",
            title="Planning Statement.txt",
            local_path=str(f),
        ))
        tmp_db.save_document(_make_doc(
            "REF/CNT", "cnt2",
            title="Elevation.png",
            local_path="/nonexistent.png",
            mime_type="image/png",
        ))

        # Before: all queued
        before = tmp_db.get_processing_counts("REF/CNT")
        assert before["total"] == 2
        assert before["queued"] == 2
        assert before["processed"] == 0

        from plana.documents.worker import drain_queue
        drain_queue(tmp_db)

        # After: all processed
        after = tmp_db.get_processing_counts("REF/CNT")
        assert after["queued"] == 0
        assert after["processed"] == 2


class TestReprocessThenWorker:
    """End-to-end: process docs, reprocess them, worker processes again."""

    def test_full_cycle(self, tmp_db, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("content")

        tmp_db.save_document(_make_doc(
            "REF/CYCLE", "cyc1",
            title="Doc.txt",
            local_path=str(f),
        ))

        from plana.documents.worker import drain_queue

        # First pass
        drain_queue(tmp_db)
        counts = tmp_db.get_processing_counts("REF/CYCLE")
        assert counts["processed"] == 1

        # Reprocess (simulates the /reprocess endpoint)
        tmp_db.reset_documents_for_reference("REF/CYCLE")
        counts = tmp_db.get_processing_counts("REF/CYCLE")
        assert counts["queued"] == 1
        assert counts["processed"] == 0

        # Second pass
        drain_queue(tmp_db)
        counts = tmp_db.get_processing_counts("REF/CYCLE")
        assert counts["queued"] == 0
        assert counts["processed"] == 1
