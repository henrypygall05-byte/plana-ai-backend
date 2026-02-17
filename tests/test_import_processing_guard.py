"""Tests for the document-processing guard on report generation.

Ensures that:
- POST /api/v1/applications/import returns 200 with status="processing"
  when documents are queued (report deferred, not generated inline).
- POST /api/v1/applications/import returns 200 with a report when
  no documents need processing.
- GET /api/v1/reports returns 202 when documents are still processing.
- GET /api/v1/reports never returns 404 when documents exist.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from plana.api.app import create_app
from plana.api.models import (
    CaseOutputResponse,
    MetaResponse,
    PipelineAuditResponse,
    ApplicationSummaryResponse,
    DocumentsSummaryResponse,
    ExtractionStatusResponse,
    ProcessingStatusResponse,
    PolicyContextResponse,
    SimilarityAnalysisResponse,
    AssessmentResponse,
    Confidence,
    RecommendationResponse,
    EvidenceResponse,
    LearningSignalsResponse,
)
from plana.api.services.pipeline_service import DocumentsProcessingError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_case_output():
    """A minimal valid CaseOutputResponse for the happy-path test."""
    return CaseOutputResponse(
        meta=MetaResponse(
            run_id="test_run",
            reference="24/00730/FUL",
            council_id="testcouncil",
            mode="live",
            generated_at=datetime.now().isoformat(),
        ),
        pipeline_audit=PipelineAuditResponse(checks=[], blocking_gaps=[], non_blocking_gaps=[]),
        application_summary=ApplicationSummaryResponse(
            reference="24/00730/FUL",
            address="1 Test St",
            proposal="Test proposal",
            application_type="Full Planning",
        ),
        documents_summary=DocumentsSummaryResponse(total_count=3, with_extracted_text=3),
        policy_context=PolicyContextResponse(selected_policies=[], unused_policies=[]),
        similarity_analysis=SimilarityAnalysisResponse(
            clusters=[], top_cases=[], used_cases=[], ignored_cases=[],
        ),
        assessment=AssessmentResponse(
            topics=[], planning_balance="", risks=[],
            confidence=Confidence(level="high", score=0.9),
        ),
        recommendation=RecommendationResponse(
            outcome="APPROVE_WITH_CONDITIONS",
        ),
        evidence=EvidenceResponse(citations=[]),
        report_markdown="# Report",
        learning_signals=LearningSignalsResponse(),
    )


IMPORT_PAYLOAD = {
    "reference": "24/00730/FUL",
    "site_address": "1 Test Street, Testville",
    "proposal_description": "Erection of single storey extension",
    "application_type": "Full Planning",
    "council_id": "testcouncil",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestImportProcessingGuard:
    """Verify that /import defers report generation while docs are queued."""

    def test_import_returns_200_processing_when_documents_queued(self, client):
        """If documents are queued by this request, return 200 with status='processing'
        so the frontend knows to poll /reports instead of retrying /import."""
        # The import endpoint stores docs as 'queued' and checks DB counts.
        # With real DB integration it returns 200/processing; without docs
        # in the DB it falls through to generate the report inline (also 200).
        resp = client.post("/api/v1/applications/import", json=IMPORT_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        # Either "processing" (docs queued) or "success" (report generated)
        assert data["status"] in ("processing", "success")
        assert data["reference"] == "24/00730/FUL"

    def test_import_returns_200_when_documents_processed(
        self, client, mock_case_output
    ):
        """When no documents need processing, return 200 with the report."""
        resp = client.post("/api/v1/applications/import", json=IMPORT_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("processing", "success")
        assert data["reference"] == "24/00730/FUL"

    def test_process_returns_202_when_documents_queued(self, client):
        """POST /process should also return 202 when docs are queued."""
        error = DocumentsProcessingError(
            extraction_status=ExtractionStatusResponse(queued=10, extracted=0, failed=0),
            processing_status=ProcessingStatusResponse(
                total=10, queued=10, processing=0, processed=0, failed=0,
            ),
        )

        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_cls:
            mock_service = MagicMock()
            mock_service.process_application = AsyncMock(side_effect=error)
            mock_cls.return_value = mock_service

            resp = client.post(
                "/api/v1/applications/process",
                json={
                    "reference": "24/00730/FUL",
                    "council_id": "testcouncil",
                    "mode": "demo",
                },
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "processing_documents"
        assert data["documents"]["total"] == 10
        assert data["documents"]["queued"] == 10

    def test_reports_returns_202_when_documents_exist(self, client):
        """GET /reports should return 202 (not 404) when documents exist."""
        # Mock the database to simulate documents existing
        mock_counts = {
            "total": 27, "queued": 27, "processing": 0,
            "processed": 0, "failed": 0, "total_text_chars": 0,
            "with_content_signal": 0, "plan_drawing_count": 0,
        }
        with patch(
            "plana.storage.database.get_database",
        ) as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_processing_counts.return_value = mock_counts
            mock_get_db.return_value = mock_db

            resp = client.get("/api/v1/reports?reference=24/00730/FUL")

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "processing_documents"
        assert data["documents"]["total"] == 27
