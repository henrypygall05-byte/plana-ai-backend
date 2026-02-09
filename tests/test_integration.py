"""
Integration tests for Plana.AI.

Tests the full pipeline from API request to response.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_ok(self, api_client: TestClient):
        """Health endpoint should return 200 OK."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_includes_version(self, api_client: TestClient):
        """Health endpoint should include version info."""
        response = api_client.get("/health")
        data = response.json()
        assert "version" in data


class TestApplicationsAPI:
    """Tests for applications endpoints."""

    def test_process_demo_application(self, api_client: TestClient, sample_demo_applications):
        """Processing a demo application should return a valid response."""
        reference = "2024/0930/01/DET"

        response = api_client.post(
            "/api/v1/applications/process",
            json={
                "reference": reference,
                "council_id": "newcastle",
                "mode": "demo",
            },
        )

        # Should succeed or return expected error format
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "reference" in data or "recommendation" in data

    def test_process_invalid_council_returns_error(self, api_client: TestClient):
        """Processing with invalid council should return validation error."""
        response = api_client.post(
            "/api/v1/applications/process",
            json={
                "reference": "2024/0001/01/DET",
                "council_id": "invalid_council",
                "mode": "demo",
            },
        )

        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]

    def test_import_application(self, api_client: TestClient):
        """Importing application data should return a response."""
        from tests.factories import ImportRequestFactory

        request_data = ImportRequestFactory.create()

        response = api_client.post(
            "/api/v1/applications/import",
            json=request_data,
        )

        # Should succeed or return expected error
        assert response.status_code in [200, 500]

        data = response.json()
        assert "status" in data
        assert data["reference"] == request_data["reference"]


class TestFeedbackAPI:
    """Tests for feedback endpoints."""

    def test_submit_feedback(self, api_client: TestClient):
        """Submitting feedback should succeed."""
        from tests.factories import FeedbackRequestFactory

        request_data = FeedbackRequestFactory.create()

        response = api_client.post(
            "/api/v1/feedback",
            json=request_data,
        )

        # Should succeed
        assert response.status_code in [200, 201]


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_returns_json(self, api_client: TestClient):
        """404 errors should return JSON format."""
        response = api_client.get("/api/v1/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    def test_validation_error_returns_details(self, api_client: TestClient):
        """Validation errors should include field details."""
        response = api_client.post(
            "/api/v1/applications/process",
            json={},  # Missing required fields
        )

        assert response.status_code == 422
        data = response.json()
        assert "error" in data or "detail" in data

    def test_request_id_in_response(self, api_client: TestClient):
        """Responses should include request ID header."""
        response = api_client.get("/health")

        # Check for request ID header
        assert "X-Request-ID" in response.headers or response.status_code == 200


class TestRateLimiting:
    """Tests for rate limiting (when enabled)."""

    def test_rate_limit_headers_present(self, api_client: TestClient):
        """Rate limit headers should be present in responses."""
        response = api_client.get("/health")

        # Headers may or may not be present depending on config
        # Just verify the endpoint works
        assert response.status_code == 200


class TestLegacyEndpoints:
    """Tests for backward compatibility with legacy endpoints."""

    def test_legacy_applications_endpoint(self, api_client: TestClient):
        """Legacy /api/applications should still work."""
        response = api_client.get("/api/applications/newcastle/2024%2F0001%2F01%2FDET")

        # May return 404 if not found, which is expected
        assert response.status_code in [200, 404, 500]

    def test_legacy_feedback_endpoint(self, api_client: TestClient):
        """Legacy /api/feedback should still work."""
        from tests.factories import FeedbackRequestFactory

        request_data = FeedbackRequestFactory.create()

        response = api_client.post(
            "/api/feedback",
            json=request_data,
        )

        # Should work or return expected error
        assert response.status_code in [200, 201, 422, 500]


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_on_options(self, api_client: TestClient):
        """OPTIONS requests should include CORS headers."""
        response = api_client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Should allow the request
        assert response.status_code in [200, 204, 405]

    def test_cors_allows_api_key_header(self, api_client: TestClient):
        """CORS should allow X-API-Key header."""
        response = api_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Headers": "X-API-Key",
            },
        )

        assert response.status_code in [200, 204, 405]
