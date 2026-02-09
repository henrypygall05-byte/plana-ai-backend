"""
Pytest configuration and fixtures for Plana.AI tests.

Provides shared fixtures for database, API client, and test data.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["PLANA_ENVIRONMENT"] = "development"
os.environ["PLANA_DEBUG"] = "true"
os.environ["PLANA_USE_FIXTURES"] = "true"
os.environ["PLANA_REQUIRE_API_KEY"] = "false"
os.environ["PLANA_ENABLE_RATE_LIMITING"] = "false"


# =============================================================================
# Event Loop Configuration
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture(scope="function")
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_plana.db"


@pytest.fixture(scope="function")
def test_database(temp_db_path: Path):
    """Create a fresh test database for each test."""
    from plana.storage.database import Database

    db = Database(db_path=temp_db_path)
    yield db

    # Cleanup is handled by temp directory deletion


@pytest.fixture(scope="function")
def populated_database(test_database):
    """Database with sample data pre-populated."""
    from tests.factories import ApplicationFactory, DocumentFactory, ReportFactory

    # Create sample applications
    apps = [ApplicationFactory.create() for _ in range(5)]
    for app in apps:
        test_database.save_application(app)

    # Create sample documents
    for i, app in enumerate(apps[:3]):
        docs = [DocumentFactory.create(reference=app.reference) for _ in range(2)]
        for doc in docs:
            test_database.save_document(doc)

    # Create sample reports
    for app in apps[:2]:
        report = ReportFactory.create(reference=app.reference)
        test_database.save_report(report)

    yield test_database


# =============================================================================
# API Client Fixtures
# =============================================================================


@pytest.fixture(scope="function")
def api_client() -> Generator[TestClient, None, None]:
    """Create a test client for the API."""
    from plana.api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def authenticated_client(api_client: TestClient) -> TestClient:
    """API client with authentication header."""
    # For tests, we can use a test API key
    api_client.headers["X-API-Key"] = "test_key_for_testing"
    return api_client


# =============================================================================
# Application Data Fixtures
# =============================================================================


@pytest.fixture
def sample_application_data() -> dict:
    """Sample application data for testing."""
    return {
        "reference": "2024/0001/01/DET",
        "council_id": "newcastle",
        "address": "123 Test Street, Newcastle Upon Tyne, NE1 1AA",
        "proposal": "Erection of single storey rear extension",
        "application_type": "householder",
        "status": "pending",
        "constraints": ["Conservation Area"],
        "ward": "Monument",
    }


@pytest.fixture
def sample_demo_applications() -> dict:
    """Demo application fixtures."""
    return {
        "2024/0930/01/DET": {
            "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
            "type": "Full Planning",
            "proposal": "Erection of two storey rear/roof extension",
            "constraints": ["Grainger Town Conservation Area"],
            "ward": "Monument",
        },
        "2024/0943/01/LBC": {
            "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
            "type": "Listed Building Consent",
            "proposal": "Listed Building Application for internal and external works",
            "constraints": ["Grade II Listed Building"],
            "ward": "Monument",
        },
    }


# =============================================================================
# Policy Fixtures
# =============================================================================


@pytest.fixture
def sample_policies() -> list[dict]:
    """Sample policies for testing."""
    return [
        {
            "id": "NPPF-199",
            "doc_id": "NPPF",
            "doc_short_name": "NPPF",
            "doc_title": "National Planning Policy Framework",
            "title": "Conserving Heritage Assets",
            "text": "When considering the impact of a proposed development on heritage assets...",
            "page": 199,
        },
        {
            "id": "DM15",
            "doc_id": "DAP",
            "doc_short_name": "DAP",
            "doc_title": "Development and Allocations Plan",
            "title": "Conservation of Heritage Assets",
            "text": "Development affecting designated heritage assets will be supported...",
            "page": 45,
        },
    ]


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_portal_response():
    """Mock portal HTML response."""
    return """
    <html>
    <body>
        <table>
            <tr>
                <td data-label="Application Reference">2024/0001/01/DET</td>
                <td>
                    <button class="btn btn-info view_application" data-id="12345">View</button>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def mock_application_page():
    """Mock application details page."""
    return """
    <html>
    <body>
        <table>
            <tr><th>Address</th><td>123 Test Street, Newcastle</td></tr>
            <tr><th>Proposal</th><td>Test proposal description</td></tr>
            <tr><th>Status</th><td>Under Consideration</td></tr>
            <tr><th>Type</th><td>Householder Application</td></tr>
        </table>
    </body>
    </html>
    """


# =============================================================================
# Async Fixtures
# =============================================================================


@pytest.fixture
async def async_client() -> AsyncGenerator[TestClient, None]:
    """Async test client."""
    from plana.api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


# =============================================================================
# Cleanup Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield

    # Reset database singleton
    import plana.storage.database as db_module
    db_module._database = None

    # Reset cache singletons
    import plana.core.cache as cache_module
    cache_module._policy_cache = None
    cache_module._similarity_cache = None

    # Reset settings cache
    from plana.config.settings import get_settings
    get_settings.cache_clear()
