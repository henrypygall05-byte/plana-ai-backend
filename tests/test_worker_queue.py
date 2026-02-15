"""Tests for background document worker, system endpoints, and document persistence.

Covers:
- Document persistence during import (queued vs processed)
- Background worker consuming queued documents
- GET  /api/v1/system/worker_health
- POST /api/v1/system/kick_queue
- GET  /api/v1/documents/status?reference=24/00730/FUL  (end-to-end with worker)
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from plana.api.app import create_app
from plana.storage.database import Database
from plana.storage.models import StoredDocument


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db():
    """Create a temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    db = Database(db_path)
    yield db
    db_path.unlink(missing_ok=True)


@pytest.fixture
def client(tmp_db, monkeypatch):
    """Create a test client with all Database() calls returning the temp DB."""
    monkeypatch.setattr(
        "plana.api.routes.documents.Database",
        lambda *a, **kw: tmp_db,
    )
    # Patch the background module's Database so health/kick use tmp_db
    monkeypatch.setattr(
        "plana.documents.background.Database",
        lambda *a, **kw: tmp_db,
    )
    app = create_app()
    return TestClient(app)


# ===========================================================================
# Document persistence from import
# ===========================================================================


class TestDocumentPersistence:
    """Documents from import must be saved to the DB."""

    def test_persist_documents_with_content_text(self, tmp_db):
        """Documents with content_text should be stored as 'processed'."""
        from plana.api.services.pipeline_service import PipelineService
        from plana.api.models import ImportApplicationRequest

        # Patch PipelineService.db to use our temp db
        svc = PipelineService.__new__(PipelineService)
        svc.db = tmp_db
        svc.policy_search = None
        svc.similarity_search = None

        class MockDoc:
            filename = "Design_and_Access_Statement.pdf"
            document_type = "statement"
            content_text = "This is a design and access statement with substantial text content."

        class MockRequest:
            reference = "24/00730/FUL"
            documents = [MockDoc()]

        svc._persist_imported_documents(MockRequest())

        docs = tmp_db.get_documents("24/00730/FUL")
        assert len(docs) == 1
        assert docs[0].processing_status == "processed"
        assert docs[0].extraction_status == "extracted"
        assert docs[0].extract_method == "inline_text"
        assert docs[0].extracted_text_chars > 0
        assert docs[0].has_any_content_signal is True

    def test_persist_documents_without_content_text(self, tmp_db):
        """Documents without content_text should be stored as 'queued'."""
        from plana.api.services.pipeline_service import PipelineService

        svc = PipelineService.__new__(PipelineService)
        svc.db = tmp_db
        svc.policy_search = None
        svc.similarity_search = None

        class MockDoc:
            filename = "PROPOSED_ELEVATIONS-1527200.pdf"
            document_type = "plans"
            content_text = None

        class MockRequest:
            reference = "24/00730/FUL"
            documents = [MockDoc()]

        svc._persist_imported_documents(MockRequest())

        docs = tmp_db.get_documents("24/00730/FUL")
        assert len(docs) == 1
        assert docs[0].processing_status == "queued"
        assert docs[0].extraction_status == "queued"
        assert docs[0].extract_method == "none"
        assert docs[0].extracted_text_chars == 0

    def test_persist_mixed_documents(self, tmp_db):
        """Mix of docs with/without content should have correct statuses."""
        from plana.api.services.pipeline_service import PipelineService

        svc = PipelineService.__new__(PipelineService)
        svc.db = tmp_db
        svc.policy_search = None
        svc.similarity_search = None

        class TextDoc:
            filename = "Statement.pdf"
            document_type = "statement"
            content_text = "Some extracted text."

        class DrawingDoc:
            filename = "Elevations.pdf"
            document_type = "plans"
            content_text = None

        class EmptyDoc:
            filename = "Form.pdf"
            document_type = "other"
            content_text = ""

        class MockRequest:
            reference = "24/00730/FUL"
            documents = [TextDoc(), DrawingDoc(), EmptyDoc()]

        svc._persist_imported_documents(MockRequest())

        docs = tmp_db.get_documents("24/00730/FUL")
        assert len(docs) == 3

        by_status = {}
        for d in docs:
            by_status.setdefault(d.processing_status, 0)
            by_status[d.processing_status] += 1

        assert by_status["processed"] == 1  # TextDoc
        assert by_status["queued"] == 2  # DrawingDoc + EmptyDoc

    def test_persist_is_idempotent(self, tmp_db):
        """Calling persist twice with the same docs should upsert, not duplicate."""
        from plana.api.services.pipeline_service import PipelineService

        svc = PipelineService.__new__(PipelineService)
        svc.db = tmp_db
        svc.policy_search = None
        svc.similarity_search = None

        class MockDoc:
            filename = "Plan.pdf"
            document_type = "plans"
            content_text = None

        class MockRequest:
            reference = "24/00730/FUL"
            documents = [MockDoc()]

        svc._persist_imported_documents(MockRequest())
        svc._persist_imported_documents(MockRequest())

        docs = tmp_db.get_documents("24/00730/FUL")
        assert len(docs) == 1  # upsert, not duplicate


# ===========================================================================
# Background worker claim + process
# ===========================================================================


class TestBackgroundWorkerClaim:
    """The background worker should claim and process queued documents."""

    def test_claim_queued_document(self, tmp_db):
        """claim_queued_document should atomically claim a queued doc."""
        tmp_db.save_document(StoredDocument(
            reference="24/00730/FUL",
            doc_id="test_doc_1",
            title="Test.pdf",
            doc_type="plans",
            processing_status="queued",
        ))

        doc = tmp_db.claim_queued_document()
        assert doc is not None
        assert doc.doc_id == "test_doc_1"
        assert doc.processing_status == "processing"

        # Second claim should return None (no more queued docs)
        doc2 = tmp_db.claim_queued_document()
        assert doc2 is None

    def test_claim_skips_processed_docs(self, tmp_db):
        """Already processed docs should not be claimed."""
        tmp_db.save_document(StoredDocument(
            reference="24/00730/FUL",
            doc_id="processed_doc",
            title="Done.pdf",
            doc_type="plans",
            processing_status="processed",
        ))

        doc = tmp_db.claim_queued_document()
        assert doc is None

    def test_process_one_marks_processed(self, tmp_db):
        """process_one should mark a document as processed."""
        from plana.documents.worker import process_one

        tmp_db.save_document(StoredDocument(
            reference="24/00730/FUL",
            doc_id="worker_doc",
            title="NoFile.pdf",
            doc_type="plans",
            processing_status="processing",
            local_path="/nonexistent/path.pdf",
        ))

        doc = tmp_db.get_document_by_doc_id("worker_doc")
        process_one(doc, tmp_db)

        updated = tmp_db.get_document_by_doc_id("worker_doc")
        assert updated.processing_status in ("processed", "failed")


# ===========================================================================
# System endpoints
# ===========================================================================


class TestSystemEndpoints:
    """Tests for /api/v1/system/ endpoints."""

    def test_worker_health_returns_200(self, client, tmp_db):
        resp = client.get("/api/v1/system/worker_health")
        assert resp.status_code == 200
        data = resp.json()
        assert "queue_length" in data
        assert "alive" in data
        assert "total_processed" in data

    def test_worker_health_shows_queue_length(self, client, tmp_db):
        """Queue length should reflect actual queued documents."""
        for i in range(3):
            tmp_db.save_document(StoredDocument(
                reference="24/00730/FUL",
                doc_id=f"health_doc_{i}",
                title=f"Doc{i}.pdf",
                doc_type="plans",
                processing_status="queued",
            ))

        resp = client.get("/api/v1/system/worker_health")
        assert resp.status_code == 200
        assert resp.json()["queue_length"] == 3

    def test_kick_queue_returns_200(self, client, tmp_db):
        resp = client.post("/api/v1/system/kick_queue")
        assert resp.status_code == 200
        data = resp.json()
        assert "queued_found" in data
        assert "action" in data

    def test_kick_queue_with_queued_docs(self, client, tmp_db):
        """Kick should report queued docs found."""
        for i in range(5):
            tmp_db.save_document(StoredDocument(
                reference="24/00730/FUL",
                doc_id=f"kick_doc_{i}",
                title=f"KickDoc{i}.pdf",
                doc_type="plans",
                processing_status="queued",
            ))

        resp = client.post("/api/v1/system/kick_queue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["queued_found"] == 5

    def test_kick_queue_no_queued_docs(self, client, tmp_db):
        """Kick with empty queue should return action=none."""
        resp = client.post("/api/v1/system/kick_queue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["queued_found"] == 0
        assert data["action"] == "none"


# ===========================================================================
# End-to-end: status shows correct counts after persistence
# ===========================================================================


class TestEndToEndStatus:
    """After importing docs, status endpoint shows correct counts."""

    def test_status_after_persist(self, client, tmp_db):
        """After persisting docs, the status endpoint should show them."""
        # Simulate what import does: persist 3 docs (1 processed, 2 queued)
        tmp_db.save_document(StoredDocument(
            reference="24/00730/FUL",
            doc_id="e2e_text",
            title="Statement.pdf",
            doc_type="statement",
            processing_status="processed",
            extraction_status="extracted",
            extract_method="inline_text",
            extracted_text_chars=500,
            has_any_content_signal=True,
        ))
        tmp_db.save_document(StoredDocument(
            reference="24/00730/FUL",
            doc_id="e2e_plans",
            title="Proposed Plans.pdf",
            doc_type="plans",
            processing_status="queued",
        ))
        tmp_db.save_document(StoredDocument(
            reference="24/00730/FUL",
            doc_id="e2e_elev",
            title="Elevations.pdf",
            doc_type="plans",
            processing_status="queued",
        ))

        resp = client.get(
            "/api/v1/documents/status",
            params={"reference": "24/00730/FUL"},
        )
        assert resp.status_code == 200
        data = resp.json()

        docs = data["documents"]
        assert docs["total"] == 3
        assert docs["processed"] == 1
        assert docs["queued"] == 2
        assert docs["total_text_chars"] == 500
