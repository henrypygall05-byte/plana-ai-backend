"""Pytest configuration and fixtures."""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from plana.config import Settings
from plana.core.models import (
    Address,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    ApplicationType,
    DocumentType,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Create test settings with temporary directories."""
    return Settings(
        debug=True,
        data_dir=tmp_path / "data",
        logs_dir=tmp_path / "logs",
        prompts_dir=tmp_path / "prompts",
        storage={"backend": "local", "local_path": tmp_path / "documents"},
        vector_store={"backend": "chroma", "chroma_persist_path": tmp_path / "chroma"},
    )


@pytest.fixture
def sample_application() -> Application:
    """Create a sample application for testing."""
    return Application(
        reference="2026/0101/01/NPA",
        council_id="newcastle",
        address=Address(
            full_address="123 Grey Street, Newcastle upon Tyne, NE1 6EE",
            postcode="NE1 6EE",
            ward="Monument",
        ),
        proposal="Erection of two-storey rear extension and alterations to existing dwelling",
        application_type=ApplicationType.HOUSEHOLDER,
        status=ApplicationStatus.UNDER_REVIEW,
    )


@pytest.fixture
def sample_documents() -> list[ApplicationDocument]:
    """Create sample documents for testing."""
    return [
        ApplicationDocument(
            id="doc1",
            application_reference="2026/0101/01/NPA",
            title="Application Form",
            document_type=DocumentType.APPLICATION_FORM,
            file_type="pdf",
            source_url="https://example.com/doc1.pdf",
        ),
        ApplicationDocument(
            id="doc2",
            application_reference="2026/0101/01/NPA",
            title="Location Plan",
            document_type=DocumentType.LOCATION_PLAN,
            file_type="pdf",
            source_url="https://example.com/doc2.pdf",
        ),
        ApplicationDocument(
            id="doc3",
            application_reference="2026/0101/01/NPA",
            title="Design and Access Statement",
            document_type=DocumentType.DESIGN_ACCESS_STATEMENT,
            file_type="pdf",
            source_url="https://example.com/doc3.pdf",
        ),
    ]
