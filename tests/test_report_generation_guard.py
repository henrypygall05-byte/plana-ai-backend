"""Tests for report generation guard: reports must not be served while
documents are still queued or processing.

Covers:
- GET /api/v1/reports?reference=...           (blocked when docs pending)
- GET /api/v1/reports/by-reference?reference=... (blocked when docs pending)
- Both endpoints return 202 with processing_documents status
- Reports are served normally when all docs are processed
"""

import tempfile
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
    """Create a test client backed by a temporary database."""
    _factory = lambda *a, **kw: tmp_db
    # Patch Database() everywhere it's constructed
    monkeypatch.setattr("plana.storage.database.Database", _factory)
    monkeypatch.setattr("plana.api.routes.documents.Database", _factory)
    monkeypatch.setattr("plana.documents.background.Database", _factory)
    app = create_app()
    return TestClient(app)


@pytest.fixture
def queued_db(tmp_db):
    """Seed with 5 queued documents."""
    for i in range(5):
        tmp_db.save_document(StoredDocument(
            reference="2024/REPORT/001",
            doc_id=f"rdoc_{i}",
            title=f"Report Doc {i}",
            doc_type="plans",
            processing_status="queued",
            extraction_status="queued",
        ))
    return tmp_db


@pytest.fixture
def processing_db(tmp_db):
    """Seed with 3 processed + 2 still processing documents."""
    for i in range(3):
        tmp_db.save_document(StoredDocument(
            reference="2024/REPORT/001",
            doc_id=f"rdoc_done_{i}",
            title=f"Done Doc {i}",
            doc_type="plans",
            processing_status="processed",
            extraction_status="extracted",
            extracted_text_chars=100,
            has_any_content_signal=True,
        ))
    for i in range(2):
        tmp_db.save_document(StoredDocument(
            reference="2024/REPORT/001",
            doc_id=f"rdoc_pending_{i}",
            title=f"Pending Doc {i}",
            doc_type="plans",
            processing_status="processing",
            extraction_status="queued",
        ))
    return tmp_db


@pytest.fixture
def all_processed_db(tmp_db):
    """Seed with all documents processed."""
    for i in range(5):
        tmp_db.save_document(StoredDocument(
            reference="2024/REPORT/001",
            doc_id=f"rdoc_{i}",
            title=f"Report Doc {i}",
            doc_type="plans",
            processing_status="processed",
            extraction_status="extracted",
            extracted_text_chars=50,
            has_any_content_signal=True,
        ))
    return tmp_db


# ===========================================================================
# Report generation blocked when documents are queued
# ===========================================================================


class TestReportBlockedWhileQueued:
    """GET /api/v1/reports returns 202 when documents are actively processing,
    and auto-unblocks URL-less queued docs to prevent infinite 202 loops."""

    def test_reports_auto_unblocks_urlless_queued_docs(self, client, queued_db):
        """URL-less queued docs are auto force-processed so the report can generate."""
        resp = client.get(
            "/api/v1/reports",
            params={"reference": "2024/REPORT/001"},
        )
        # Auto-unblock should have resolved the block — status should NOT be 202
        assert resp.status_code != 202

    def test_reports_by_reference_auto_unblocks(self, client, queued_db):
        """Same auto-unblock via the /by-reference endpoint."""
        resp = client.get(
            "/api/v1/reports/by-reference",
            params={"reference": "2024/REPORT/001"},
        )
        assert resp.status_code != 202

    def test_reports_returns_202_when_partially_processing(self, client, processing_db):
        """Still blocked when docs are actively being processed by the worker."""
        resp = client.get(
            "/api/v1/reports",
            params={"reference": "2024/REPORT/001"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "processing_documents"
        assert data["documents"]["processing"] == 2
        assert data["documents"]["processed"] == 3

    def test_auto_unblocked_docs_become_processed(self, client, queued_db):
        """After auto-unblock, all docs should be in 'processed' state."""
        # Trigger the auto-unblock via report endpoint
        client.get(
            "/api/v1/reports",
            params={"reference": "2024/REPORT/001"},
        )
        # Verify documents were force-processed
        counts = queued_db.get_processing_counts("2024/REPORT/001")
        assert counts["queued"] == 0
        assert counts["processed"] == 5
        assert counts["total"] == 5


# ===========================================================================
# Report generation allowed when all documents are processed
# ===========================================================================


class TestReportAllowedWhenProcessed:
    """Reports should NOT be blocked when queued==0 AND processing==0."""

    def test_reports_not_blocked_when_all_processed(self, client, all_processed_db):
        resp = client.get(
            "/api/v1/reports",
            params={"reference": "2024/REPORT/001"},
        )
        # Should not be 202 — documents are all processed.
        # Will be 404 (no actual report stored) but NOT 202.
        assert resp.status_code != 202

    def test_reports_not_blocked_when_no_documents(self, client, tmp_db):
        resp = client.get(
            "/api/v1/reports",
            params={"reference": "2024/EMPTY/001"},
        )
        # No documents at all → guard should not block.
        assert resp.status_code != 202
