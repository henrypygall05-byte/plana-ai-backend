"""Tests for the document-processing guard on report generation.

Ensures that:
- POST /api/v1/applications/import returns 202 when documents are
  still queued or processing (report NOT generated).
- POST /api/v1/applications/import returns 200 with a report when
  documents have finished processing (queued==0, processed>0).
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
    """Verify that /import blocks report generation while docs are queued."""

    def test_import_returns_202_when_documents_queued(self, client):
        """If documents are still queued, return 202 — do NOT generate a report."""
        error = DocumentsProcessingError(
            extraction_status=ExtractionStatusResponse(queued=26, extracted=0, failed=0),
            processing_status=ProcessingStatusResponse(
                total=26, queued=26, processing=0, processed=0, failed=0,
            ),
        )

        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_cls:
            mock_service = MagicMock()
            mock_service.process_imported_application = AsyncMock(side_effect=error)
            mock_cls.return_value = mock_service

            resp = client.post("/api/v1/applications/import", json=IMPORT_PAYLOAD)

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "processing_documents"
        assert data["reference"] == "24/00730/FUL"
        docs = data["documents"]
        assert docs["total"] == 26
        assert docs["queued"] == 26
        assert docs["processed"] == 0

    def test_import_returns_202_when_documents_processing(self, client):
        """If documents are actively being processed, return 202."""
        error = DocumentsProcessingError(
            extraction_status=ExtractionStatusResponse(queued=5, extracted=15, failed=0),
            processing_status=ProcessingStatusResponse(
                total=26, queued=5, processing=6, processed=15, failed=0,
            ),
        )

        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_cls:
            mock_service = MagicMock()
            mock_service.process_imported_application = AsyncMock(side_effect=error)
            mock_cls.return_value = mock_service

            resp = client.post("/api/v1/applications/import", json=IMPORT_PAYLOAD)

        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "processing_documents"
        assert data["documents"]["queued"] == 5
        assert data["documents"]["processing"] == 6

    def test_import_returns_200_when_documents_processed(
        self, client, mock_case_output
    ):
        """Once all documents are processed, return 200 with the report."""
        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_cls:
            mock_service = MagicMock()
            mock_service.process_imported_application = AsyncMock(
                return_value=mock_case_output,
            )
            mock_cls.return_value = mock_service

            resp = client.post("/api/v1/applications/import", json=IMPORT_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["reference"] == "24/00730/FUL"
        assert data["report"] is not None

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
