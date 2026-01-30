"""Tests for Plana.AI REST API."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from plana.api.app import create_app
from plana.api.models import (
    CaseOutputResponse,
    MetaResponse,
    PipelineAuditResponse,
    PipelineCheck,
    ApplicationSummaryResponse,
    DocumentsSummaryResponse,
    PolicyContextResponse,
    SimilarityAnalysisResponse,
    AssessmentResponse,
    Confidence,
    RecommendationResponse,
    EvidenceResponse,
    LearningSignalsResponse,
    HealthResponse,
    FeedbackResponse,
)


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_case_output():
    """Create a mock CASE_OUTPUT response."""
    return CaseOutputResponse(
        meta=MetaResponse(
            run_id="test_run_123",
            reference="2024/0930/01/DET",
            council_id="newcastle",
            mode="demo",
            generated_at=datetime.now().isoformat(),
            prompt_version="1.0.0",
            report_schema_version="1.0.0",
        ),
        pipeline_audit=PipelineAuditResponse(
            checks=[
                PipelineCheck(name="NPPF included", status="PASS"),
                PipelineCheck(name="Local Plan included", status="PASS"),
            ],
            blocking_gaps=[],
            non_blocking_gaps=[],
        ),
        application_summary=ApplicationSummaryResponse(
            reference="2024/0930/01/DET",
            address="86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
            proposal="Erection of two storey rear/roof extension",
            application_type="Full Planning",
            constraints=["Grainger Town Conservation Area"],
            ward="Monument",
            postcode="NE1 5JQ",
        ),
        documents_summary=DocumentsSummaryResponse(
            total_count=7,
            by_type={"plans": 3, "application_form": 1},
            with_extracted_text=7,
        ),
        policy_context=PolicyContextResponse(
            selected_policies=[],
            unused_policies=[],
        ),
        similarity_analysis=SimilarityAnalysisResponse(
            clusters=[],
            top_cases=[],
            used_cases=[],
            ignored_cases=[],
            current_case_distinction="Test distinction",
        ),
        assessment=AssessmentResponse(
            topics=[],
            planning_balance="Test balance",
            risks=[],
            confidence=Confidence(level="high", score=0.85),
        ),
        recommendation=RecommendationResponse(
            outcome="APPROVE_WITH_CONDITIONS",
            conditions=[],
            refusal_reasons=[],
            info_required=[],
        ),
        evidence=EvidenceResponse(citations=[]),
        report_markdown="# Test Report\n\nTest content.",
        learning_signals=LearningSignalsResponse(
            similarity=[],
            policy=[],
            report=[],
            outcome_placeholders=[],
        ),
    )


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert data["database"] == "connected"
        assert "timestamp" in data

    def test_health_check_api_prefix(self, client):
        """Test health check with /api prefix."""
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestApplicationsEndpoint:
    """Tests for applications endpoints."""

    def test_process_application_demo_mode(self, client, mock_case_output):
        """Test processing application in demo mode."""
        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.process_application = AsyncMock(return_value=mock_case_output)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/applications/process",
                json={
                    "reference": "2024/0930/01/DET",
                    "council_id": "newcastle",
                    "mode": "demo",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["reference"] == "2024/0930/01/DET"
            assert data["meta"]["mode"] == "demo"
            assert data["recommendation"]["outcome"] == "APPROVE_WITH_CONDITIONS"

    def test_process_application_validates_mode(self, client):
        """Test that mode validation works."""
        response = client.post(
            "/api/applications/process",
            json={
                "reference": "2024/0001",
                "council_id": "newcastle",
                "mode": "invalid_mode",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_get_application_found(self, client):
        """Test getting application that exists."""
        app_summary = ApplicationSummaryResponse(
            reference="2024-0930-01-DET",
            address="86-92 Grainger Street",
            proposal="Test proposal",
            application_type="Full Planning",
            constraints=["Conservation Area"],
            ward="Monument",
            postcode="NE1 5JQ",
        )

        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_application = AsyncMock(return_value=app_summary)
            mock_service_class.return_value = mock_service

            # URL-encoded reference to avoid path interpretation
            response = client.get("/api/applications/newcastle/2024-0930-01-DET")

            assert response.status_code == 200
            data = response.json()
            assert data["reference"] == "2024-0930-01-DET"
            assert data["address"] == "86-92 Grainger Street"

    def test_get_application_not_found(self, client):
        """Test getting application that doesn't exist."""
        with patch(
            "plana.api.routes.applications.PipelineService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_application = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            response = client.get("/api/applications/newcastle/NONEXISTENT")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestReportsEndpoint:
    """Tests for reports endpoints."""

    def test_get_report(self, client, mock_case_output):
        """Test getting a report."""
        with patch("plana.api.routes.reports.PipelineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_report = AsyncMock(return_value=mock_case_output)
            mock_service_class.return_value = mock_service

            # Use simple reference without slashes
            response = client.get("/api/reports/2024-0930-01-DET")

            assert response.status_code == 200
            data = response.json()
            assert "meta" in data
            assert "report_markdown" in data
            assert "recommendation" in data

    def test_get_report_not_found(self, client):
        """Test getting report that doesn't exist."""
        with patch("plana.api.routes.reports.PipelineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_report = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            response = client.get("/api/reports/NONEXISTENT")

            assert response.status_code == 404

    def test_get_report_versions(self, client):
        """Test getting report versions."""
        from plana.api.models import ReportVersionResponse

        versions = [
            ReportVersionResponse(
                version=1,
                generated_at="2024-01-01T10:00:00",
                recommendation="APPROVE_WITH_CONDITIONS",
                confidence=0.75,
                prompt_version="1.0.0",
            ),
            ReportVersionResponse(
                version=2,
                generated_at="2024-01-02T10:00:00",
                recommendation="APPROVE",
                confidence=0.85,
                prompt_version="1.0.0",
            ),
        ]

        with patch("plana.api.routes.reports.PipelineService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_report_versions = AsyncMock(return_value=versions)
            mock_service_class.return_value = mock_service

            # Use simple reference without slashes
            response = client.get("/api/reports/2024-0001/versions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["version"] == 1
            assert data[1]["version"] == 2


class TestFeedbackEndpoint:
    """Tests for feedback endpoint."""

    def test_submit_feedback_approve(self, client):
        """Test submitting approval feedback."""
        feedback_response = FeedbackResponse(
            feedback_id=1,
            status="success",
            message="Feedback submitted for 2024/0001",
        )

        with patch("plana.api.routes.feedback.FeedbackService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.submit_feedback = AsyncMock(return_value=feedback_response)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/feedback",
                json={
                    "reference": "2024/0001",
                    "decision": "APPROVE",
                    "notes": "Test notes",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["feedback_id"] == 1

    def test_submit_feedback_with_conditions(self, client):
        """Test submitting feedback with conditions."""
        feedback_response = FeedbackResponse(
            feedback_id=2,
            status="success",
            message="Feedback submitted",
        )

        with patch("plana.api.routes.feedback.FeedbackService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.submit_feedback = AsyncMock(return_value=feedback_response)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/feedback",
                json={
                    "reference": "2024/0001",
                    "decision": "APPROVE_WITH_CONDITIONS",
                    "conditions": ["Materials condition", "Hours condition"],
                },
            )

            assert response.status_code == 200

    def test_submit_feedback_refuse(self, client):
        """Test submitting refusal feedback."""
        feedback_response = FeedbackResponse(
            feedback_id=3,
            status="success",
            message="Feedback submitted",
        )

        with patch("plana.api.routes.feedback.FeedbackService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.submit_feedback = AsyncMock(return_value=feedback_response)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/feedback",
                json={
                    "reference": "2024/0001",
                    "decision": "REFUSE",
                    "refusal_reasons": ["Harm to conservation area"],
                },
            )

            assert response.status_code == 200

    def test_submit_feedback_invalid_decision(self, client):
        """Test that invalid decision is rejected."""
        response = client.post(
            "/api/feedback",
            json={
                "reference": "2024/0001",
                "decision": "MAYBE",
            },
        )

        assert response.status_code == 422  # Validation error


class TestAPIModels:
    """Tests for API Pydantic models."""

    def test_case_output_response_serialization(self, mock_case_output):
        """Test that CaseOutputResponse serializes correctly."""
        json_data = mock_case_output.model_dump()

        assert json_data["meta"]["reference"] == "2024/0930/01/DET"
        assert json_data["meta"]["prompt_version"] == "1.0.0"
        assert json_data["recommendation"]["outcome"] == "APPROVE_WITH_CONDITIONS"

    def test_process_request_validation(self):
        """Test ProcessApplicationRequest validation."""
        from plana.api.models import ProcessApplicationRequest

        # Valid request
        request = ProcessApplicationRequest(
            reference="2024/0001",
            council_id="newcastle",
            mode="demo",
        )
        assert request.reference == "2024/0001"
        assert request.mode == "demo"

        # Invalid mode should raise
        with pytest.raises(ValueError):
            ProcessApplicationRequest(
                reference="2024/0001",
                mode="invalid",
            )

    def test_feedback_request_validation(self):
        """Test SubmitFeedbackRequest validation."""
        from plana.api.models import SubmitFeedbackRequest

        # Valid request
        request = SubmitFeedbackRequest(
            reference="2024/0001",
            decision="APPROVE",
        )
        assert request.decision == "APPROVE"

        # Invalid decision should raise
        with pytest.raises(ValueError):
            SubmitFeedbackRequest(
                reference="2024/0001",
                decision="INVALID",
            )


class TestCORSConfiguration:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # FastAPI returns 405 for OPTIONS on health, but CORS should still work
        # Let's test actual request with Origin header
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        # CORS middleware should add headers
        assert "access-control-allow-origin" in response.headers


class TestAppFactory:
    """Tests for FastAPI app factory."""

    def test_create_app_returns_fastapi(self):
        """Test that create_app returns FastAPI instance."""
        from fastapi import FastAPI

        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "Plana.AI API"
        assert app.version == "1.0.0"

    def test_app_has_routes(self):
        """Test that app has all expected routes."""
        app = create_app()

        routes = [r.path for r in app.routes]

        assert "/health" in routes or any("/health" in str(r) for r in app.routes)
        assert any("/api/applications" in str(r.path) for r in app.routes)
        assert any("/api/reports" in str(r.path) for r in app.routes)
        assert any("/api/feedback" in str(r.path) for r in app.routes)
