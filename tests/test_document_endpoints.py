"""Tests for document status and reprocessing endpoints.

Covers:
- GET  /api/v1/documents/status/{reference}
- POST /api/v1/documents/reprocess?reference=...
- POST /api/v1/documents/{doc_id}/retry
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from plana.api.app import create_app
from plana.storage.database import Database, get_database
from plana.storage.models import StoredDocument


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db():
    """Create a temporary database and patch get_database to use it."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    db = Database(db_path)
    yield db
    db_path.unlink(missing_ok=True)


@pytest.fixture
def client(tmp_db, monkeypatch):
    """Create a test client backed by a temporary database."""
    # Patch Database() constructor calls in the routes to return our temp DB
    monkeypatch.setattr(
        "plana.api.routes.documents.Database",
        lambda *a, **kw: tmp_db,
    )
    app = create_app()
    return TestClient(app)


@pytest.fixture
def seeded_db(tmp_db):
    """Seed the temp database with test documents."""
    docs = [
        StoredDocument(
            reference="2024/TEST/001",
            doc_id="doc_site_plan",
            title="Site Plan",
            doc_type="plans",
            processing_status="processed",
            extraction_status="extracted",
            extract_method="pdf_text",
            extracted_text_chars=150,
            is_plan_or_drawing=True,
            has_any_content_signal=True,
        ),
        StoredDocument(
            reference="2024/TEST/001",
            doc_id="doc_elevations",
            title="Proposed Elevations",
            doc_type="plans",
            processing_status="processed",
            extraction_status="failed",
            extract_method="drawing_only",
            extracted_text_chars=0,
            is_plan_or_drawing=True,
            has_any_content_signal=False,
        ),
        StoredDocument(
            reference="2024/TEST/001",
            doc_id="doc_das",
            title="Design and Access Statement",
            doc_type="statement",
            processing_status="processed",
            extraction_status="extracted",
            extract_method="pdf_text",
            extracted_text_chars=5000,
            is_plan_or_drawing=False,
            has_any_content_signal=True,
        ),
        StoredDocument(
            reference="2024/TEST/001",
            doc_id="doc_failed",
            title="Corrupted File",
            doc_type="other",
            processing_status="failed",
            extraction_status="failed",
            extract_method="none",
            extracted_text_chars=0,
            is_plan_or_drawing=False,
            has_any_content_signal=False,
        ),
    ]
    for doc in docs:
        tmp_db.save_document(doc)
    return tmp_db


@pytest.fixture
def queued_db(tmp_db):
    """Seed the temp database with all-queued documents."""
    for i in range(5):
        tmp_db.save_document(StoredDocument(
            reference="2024/QUEUE/001",
            doc_id=f"qdoc_{i}",
            title=f"Document {i}",
            doc_type="plans",
            processing_status="queued",
            extraction_status="queued",
        ))
    return tmp_db


# ===========================================================================
# GET /api/v1/documents/status/{reference}
# ===========================================================================


class TestGetDocumentStatus:
    """Tests for the document status endpoint."""

    def test_returns_status_for_existing_docs(self, client, seeded_db):
        resp = client.get("/api/v1/documents/status/2024/TEST/001")
        assert resp.status_code == 200
        data = resp.json()

        assert data["reference"] == "2024/TEST/001"
        docs = data["documents"]
        assert docs["total"] == 4
        assert docs["processed"] == 3
        assert docs["failed"] == 1
        assert docs["queued"] == 0
        assert docs["processing"] == 0
        assert docs["total_text_chars"] == 5150
        assert docs["with_content_signal"] == 2
        assert docs["plan_set_present"] is True

    def test_returns_404_for_missing_reference(self, client, tmp_db):
        resp = client.get("/api/v1/documents/status/NONEXISTENT/REF")
        assert resp.status_code == 404
        assert "No documents found" in resp.json()["message"]

    def test_returns_queued_status(self, client, queued_db):
        resp = client.get("/api/v1/documents/status/2024/QUEUE/001")
        assert resp.status_code == 200
        data = resp.json()

        docs = data["documents"]
        assert docs["total"] == 5
        assert docs["queued"] == 5
        assert docs["processed"] == 0
        assert docs["failed"] == 0
        assert docs["plan_set_present"] is False

    def test_legacy_route_works(self, client, seeded_db):
        """Legacy /api/documents/ prefix should also work."""
        resp = client.get("/api/documents/status/2024/TEST/001")
        assert resp.status_code == 200
        assert resp.json()["reference"] == "2024/TEST/001"


# ===========================================================================
# POST /api/v1/documents/reprocess?reference=...
# ===========================================================================


class TestReprocessDocuments:
    """Tests for the batch reprocess endpoint."""

    def test_reprocess_resets_all_documents(self, client, seeded_db):
        resp = client.post(
            "/api/v1/documents/reprocess",
            params={"reference": "2024/TEST/001"},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["reference"] == "2024/TEST/001"
        assert data["reset_count"] == 4

        # All documents should now be queued
        docs = data["documents"]
        assert docs["total"] == 4
        assert docs["queued"] == 4
        assert docs["processed"] == 0
        assert docs["failed"] == 0

    def test_reprocess_clears_extracted_fields(self, client, seeded_db):
        """After reprocess, extracted fields should be cleared."""
        client.post(
            "/api/v1/documents/reprocess",
            params={"reference": "2024/TEST/001"},
        )

        # Verify in DB directly
        all_docs = seeded_db.get_documents("2024/TEST/001")
        for doc in all_docs:
            assert doc.processing_status == "queued"
            assert doc.extraction_status == "queued"
            assert doc.extract_method == "none"
            assert doc.extracted_text_chars == 0
            assert doc.extracted_metadata_json is None
            assert doc.has_any_content_signal is False

    def test_reprocess_preserves_is_plan_or_drawing(self, client, seeded_db):
        """is_plan_or_drawing should NOT be cleared by reprocess
        (it's derived from filename/category, not extraction)."""
        client.post(
            "/api/v1/documents/reprocess",
            params={"reference": "2024/TEST/001"},
        )
        all_docs = seeded_db.get_documents("2024/TEST/001")
        plan_docs = [d for d in all_docs if d.is_plan_or_drawing]
        # Site Plan and Elevations were flagged as plans
        assert len(plan_docs) == 2

    def test_reprocess_returns_404_for_missing_reference(self, client, tmp_db):
        resp = client.post(
            "/api/v1/documents/reprocess",
            params={"reference": "NONEXISTENT/REF"},
        )
        assert resp.status_code == 404
        assert "No documents found" in resp.json()["message"]

    def test_reprocess_returns_updated_status(self, client, seeded_db):
        """After reprocess, text chars and content signal should be zero."""
        resp = client.post(
            "/api/v1/documents/reprocess",
            params={"reference": "2024/TEST/001"},
        )
        docs = resp.json()["documents"]
        assert docs["total_text_chars"] == 0
        assert docs["with_content_signal"] == 0


# ===========================================================================
# POST /api/v1/documents/{doc_id}/retry
# ===========================================================================


class TestRetryDocument:
    """Tests for the single document retry endpoint."""

    def test_retry_resets_single_document(self, client, seeded_db):
        resp = client.post("/api/v1/documents/doc_failed/retry")
        assert resp.status_code == 200
        data = resp.json()

        assert data["reference"] == "2024/TEST/001"
        assert data["reset_count"] == 1

    def test_retry_only_affects_target_document(self, client, seeded_db):
        """Only the targeted document should be reset, others untouched."""
        client.post("/api/v1/documents/doc_failed/retry")

        all_docs = seeded_db.get_documents("2024/TEST/001")
        doc_map = {d.doc_id: d for d in all_docs}

        # doc_failed should be reset
        assert doc_map["doc_failed"].processing_status == "queued"
        assert doc_map["doc_failed"].extraction_status == "queued"

        # Others should be unchanged
        assert doc_map["doc_site_plan"].processing_status == "processed"
        assert doc_map["doc_das"].processing_status == "processed"
        assert doc_map["doc_elevations"].processing_status == "processed"

    def test_retry_returns_full_application_status(self, client, seeded_db):
        """Retry should return updated status for the entire application."""
        resp = client.post("/api/v1/documents/doc_failed/retry")
        docs = resp.json()["documents"]

        # 3 processed + 1 reset to queued
        assert docs["total"] == 4
        assert docs["processed"] == 3
        assert docs["queued"] == 1
        assert docs["failed"] == 0

    def test_retry_returns_404_for_missing_doc(self, client, tmp_db):
        resp = client.post("/api/v1/documents/nonexistent_doc/retry")
        assert resp.status_code == 404
        assert "Document not found" in resp.json()["message"]

    def test_retry_clears_extracted_fields(self, client, seeded_db):
        """After retry, the single document's extracted fields should be cleared."""
        client.post("/api/v1/documents/doc_das/retry")

        all_docs = seeded_db.get_documents("2024/TEST/001")
        doc_map = {d.doc_id: d for d in all_docs}

        # doc_das had 5000 chars — should now be 0
        assert doc_map["doc_das"].extracted_text_chars == 0
        assert doc_map["doc_das"].extract_method == "none"
        assert doc_map["doc_das"].has_any_content_signal is False


# ===========================================================================
# Database method unit tests
# ===========================================================================


class TestDatabaseMethods:
    """Direct tests for the new database methods."""

    def test_get_document_by_doc_id(self, seeded_db):
        doc = seeded_db.get_document_by_doc_id("doc_site_plan")
        assert doc is not None
        assert doc.title == "Site Plan"
        assert doc.reference == "2024/TEST/001"
        assert doc.is_plan_or_drawing is True

    def test_get_document_by_doc_id_missing(self, seeded_db):
        doc = seeded_db.get_document_by_doc_id("nonexistent")
        assert doc is None

    def test_reset_documents_for_reference(self, seeded_db):
        count = seeded_db.reset_documents_for_reference("2024/TEST/001")
        assert count == 4

        docs = seeded_db.get_documents("2024/TEST/001")
        for d in docs:
            assert d.processing_status == "queued"
            assert d.extraction_status == "queued"
            assert d.extracted_text_chars == 0
            assert d.has_any_content_signal is False

    def test_reset_documents_for_missing_reference(self, seeded_db):
        count = seeded_db.reset_documents_for_reference("NONEXISTENT")
        assert count == 0

    def test_reset_single_document(self, seeded_db):
        was_reset = seeded_db.reset_single_document("doc_das")
        assert was_reset is True

        doc = seeded_db.get_document_by_doc_id("doc_das")
        assert doc.processing_status == "queued"
        assert doc.extracted_text_chars == 0

        # Other docs untouched
        site = seeded_db.get_document_by_doc_id("doc_site_plan")
        assert site.processing_status == "processed"
        assert site.extracted_text_chars == 150

    def test_reset_single_document_missing(self, seeded_db):
        was_reset = seeded_db.reset_single_document("nonexistent")
        assert was_reset is False
