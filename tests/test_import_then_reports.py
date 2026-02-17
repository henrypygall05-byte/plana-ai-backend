"""End-to-end test: import application → reports endpoint.

Reproduces the exact user flow:
1. POST /api/v1/applications/import  → 200 (status=processing)
2. GET  /api/v1/reports?reference=... → should be 202, NOT 404
3. GET  /api/v1/documents/status?reference=... → should show queued docs

This test uses a REAL temp database (no mocking) to catch DB path
and singleton issues that unit tests with mocks would miss.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from plana.storage.database import Database


@pytest.fixture
def shared_db():
    """Create a single temp DB shared by ALL code paths."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    db = Database(db_path)
    yield db
    db_path.unlink(missing_ok=True)


@pytest.fixture
def e2e_client(shared_db):
    """Create a TestClient where every Database() and get_database()
    call returns the SAME shared temp DB instance.

    This reproduces production where all code shares ~/.plana/plana.db.
    """
    import plana.storage.database as db_module

    # Save original
    original_database = db_module._database

    # Force singleton to our shared DB
    db_module._database = shared_db

    # Also patch Database constructor so PipelineService() etc. get the shared DB
    _orig_init = Database.__init__

    def _patched_init(self, db_path=None):
        # Copy the shared DB's attributes instead of creating a new DB
        self.db_path = shared_db.db_path
        self._init_schema()

    with patch.object(Database, "__init__", _patched_init):
        from plana.api.app import create_app
        app = create_app()
        client = TestClient(app)
        yield client

    # Restore
    db_module._database = original_database


class TestLegacyPathRewrite:
    """Verify /api/* rewrites to /api/v1/* transparently."""

    def test_legacy_reports_path_returns_202_not_404(self, e2e_client, shared_db):
        """GET /api/reports (without /v1/) must work via path rewrite."""
        from plana.storage.models import StoredDocument

        for i in range(3):
            shared_db.save_document(StoredDocument(
                reference="LEGACY/PATH/001",
                doc_id=f"legacy_doc_{i}",
                title=f"Legacy Doc {i}",
                doc_type="plans",
                processing_status="queued",
            ))

        # Use /api/reports — NOT /api/v1/reports
        resp = e2e_client.get(
            "/api/reports",
            params={"reference": "LEGACY/PATH/001"},
        )
        print(f"\nLegacy /api/reports response: {resp.status_code}")
        print(f"Body: {resp.json()}")

        assert resp.status_code != 404, (
            f"/api/reports returned 404! The path rewrite middleware is not "
            f"working. Response: {resp.json()}"
        )
        assert resp.status_code == 202

    def test_legacy_documents_status_path(self, e2e_client, shared_db):
        """GET /api/documents/status (without /v1/) must work."""
        from plana.storage.models import StoredDocument

        shared_db.save_document(StoredDocument(
            reference="LEGACY/DOC/001",
            doc_id="ldoc_1",
            title="Test Doc",
            doc_type="plans",
            processing_status="queued",
        ))

        resp = e2e_client.get(
            "/api/documents/status",
            params={"reference": "LEGACY/DOC/001"},
        )
        print(f"\nLegacy /api/documents/status response: {resp.status_code}")

        assert resp.status_code != 404, (
            f"/api/documents/status returned 404! Response: {resp.json()}"
        )

    def test_legacy_import_path(self, e2e_client):
        """POST /api/applications/import (without /v1/) must work."""
        payload = {
            "reference": "LEGACY/IMPORT/001",
            "site_address": "1 Legacy St",
            "proposal_description": "Test proposal",
            "application_type": "Full Planning",
            "council_id": "newcastle",
            "documents": [
                {"filename": "doc.pdf", "document_type": "plans"},
            ],
        }
        resp = e2e_client.post("/api/applications/import", json=payload)
        print(f"\nLegacy /api/applications/import response: {resp.status_code}")

        assert resp.status_code != 404, (
            f"/api/applications/import returned 404! Response: {resp.json()}"
        )
        assert resp.status_code == 200

    def test_health_not_rewritten(self, e2e_client):
        """/health should NOT be rewritten (it's not under /api/)."""
        resp = e2e_client.get("/health")
        assert resp.status_code == 200


IMPORT_PAYLOAD = {
    "reference": "24/00730/FUL",
    "site_address": "1 Test Street, Newcastle upon Tyne NE1 1AA",
    "proposal_description": "Construct dwelling",
    "application_type": "Full Planning",
    "council_id": "newcastle",
    "documents": [
        {"filename": f"Document_{i}.pdf", "document_type": "plans"}
        for i in range(5)
    ],
}


class TestMinimalReportFallback:
    """When all docs are processed but full report gen fails, serve minimal report."""

    def test_minimal_report_after_all_processed(self, e2e_client, shared_db):
        """Reports returns 200 (not perpetual 202) when docs are all processed."""
        from plana.storage.models import StoredDocument, StoredApplication

        # Save application
        shared_db.save_application(StoredApplication(
            reference="MINIMAL/REPORT/001",
            council_id="broxtowe",
            council_name="Broxtowe Borough Council",
            address="1 Test Street",
            proposal="Build a house",
            application_type="Full Planning",
            status="imported",
            ward="",
            postcode="",
            constraints_json="[]",
        ))

        # Save documents that are already processed (worker finished)
        for i in range(3):
            shared_db.save_document(StoredDocument(
                reference="MINIMAL/REPORT/001",
                doc_id=f"min_doc_{i}",
                title=f"Doc {i}.pdf",
                doc_type="plans",
                processing_status="processed",
                extracted_text="",
                extract_method="none",
            ))

        resp = e2e_client.get(
            "/api/v1/reports",
            params={"reference": "MINIMAL/REPORT/001"},
        )
        print(f"\nMinimal report response: {resp.status_code}")
        print(f"Body keys: {list(resp.json().keys())}")

        # Should get 200 with a minimal report, NOT perpetual 202
        assert resp.status_code == 200, (
            f"Expected 200 (minimal report) but got {resp.status_code}: {resp.json()}"
        )
        data = resp.json()
        assert data.get("application_reference") == "MINIMAL/REPORT/001"
        assert data.get("mode") == "minimal"


class TestImportThenReports:
    """The exact user flow that produces 404."""

    def test_import_then_reports_returns_202_not_404(self, e2e_client, shared_db):
        """After import, GET /reports MUST return 202, never 404."""
        # Step 1: Import application
        resp = e2e_client.post(
            "/api/v1/applications/import",
            json=IMPORT_PAYLOAD,
        )
        assert resp.status_code == 200
        import_data = resp.json()
        print(f"\nImport response: status={import_data['status']}")

        # Step 2: Verify documents exist via status endpoint
        status_resp = e2e_client.get(
            "/api/v1/documents/status",
            params={"reference": "24/00730/FUL"},
        )
        print(f"Status response: {status_resp.status_code}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            print(f"  Documents: {status_data['documents']}")

        # Step 3: Verify documents are in DB directly
        docs = shared_db.get_documents("24/00730/FUL")
        print(f"Direct DB query: {len(docs)} documents found")
        for d in docs:
            print(f"  - {d.doc_id}: {d.processing_status}")

        counts = shared_db.get_processing_counts("24/00730/FUL")
        print(f"Processing counts: {counts}")

        # Step 4: THE CRITICAL TEST - reports must NOT return 404
        report_resp = e2e_client.get(
            "/api/v1/reports",
            params={"reference": "24/00730/FUL"},
        )
        print(f"Reports response: {report_resp.status_code}")
        print(f"Reports body: {report_resp.json()}")

        # Accept 200 (report generated) or 202 (documents processing)
        # NEVER 404
        assert report_resp.status_code != 404, (
            f"Reports returned 404! This is the bug. "
            f"DB has {counts['total']} docs ({counts['queued']} queued). "
            f"Response: {report_resp.json()}"
        )
        assert report_resp.status_code in (200, 202), (
            f"Unexpected status {report_resp.status_code}: {report_resp.json()}"
        )

    def test_reports_returns_202_after_manual_doc_insert(self, e2e_client, shared_db):
        """Even without import — manually insert docs, then check reports."""
        from plana.storage.models import StoredDocument

        # Insert documents directly
        for i in range(3):
            shared_db.save_document(StoredDocument(
                reference="TEST/MANUAL/001",
                doc_id=f"manual_doc_{i}",
                title=f"Manual Doc {i}",
                doc_type="plans",
                processing_status="queued",
            ))

        # Verify they're there
        counts = shared_db.get_processing_counts("TEST/MANUAL/001")
        assert counts["total"] == 3
        assert counts["queued"] == 3

        # Reports endpoint must return 202
        resp = e2e_client.get(
            "/api/v1/reports",
            params={"reference": "TEST/MANUAL/001"},
        )
        print(f"\nManual insert reports response: {resp.status_code}")
        print(f"Body: {resp.json()}")

        assert resp.status_code != 404, (
            f"Reports returned 404 for manually inserted docs! "
            f"Response: {resp.json()}"
        )
        assert resp.status_code == 202
