"""Tests for core domain models."""

import pytest
from datetime import date

from plana.core.models import (
    Address,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    ApplicationType,
    Constraint,
    DocumentType,
    GeoLocation,
    Policy,
    PolicyType,
    Report,
    ReportSection,
)


class TestAddress:
    """Tests for Address model."""

    def test_create_basic_address(self):
        """Test creating a basic address."""
        address = Address(full_address="123 Grey Street, Newcastle, NE1 6EE")
        assert address.full_address == "123 Grey Street, Newcastle, NE1 6EE"
        assert address.postcode is None

    def test_create_full_address(self):
        """Test creating an address with all fields."""
        address = Address(
            full_address="123 Grey Street, Newcastle upon Tyne, NE1 6EE",
            address_line_1="123 Grey Street",
            town="Newcastle upon Tyne",
            postcode="NE1 6EE",
            ward="Monument",
            location=GeoLocation(latitude=54.9783, longitude=-1.6178),
        )
        assert address.postcode == "NE1 6EE"
        assert address.ward == "Monument"
        assert address.location.latitude == 54.9783


class TestApplication:
    """Tests for Application model."""

    def test_create_application(self, sample_application):
        """Test creating an application."""
        app = sample_application
        assert app.reference == "2026/0101/01/NPA"
        assert app.council_id == "newcastle"
        assert app.application_type == ApplicationType.HOUSEHOLDER

    def test_is_decided(self):
        """Test is_decided computed property."""
        app = Application(
            reference="2026/0101/01/NPA",
            council_id="newcastle",
            address=Address(full_address="123 Test St"),
            proposal="Test proposal",
            status=ApplicationStatus.APPROVED,
        )
        assert app.is_decided is True
        assert app.is_approved is True

        app.status = ApplicationStatus.UNDER_REVIEW
        assert app.is_decided is False
        assert app.is_approved is False

    def test_is_approved(self):
        """Test is_approved for different statuses."""
        app = Application(
            reference="2026/0101/01/NPA",
            council_id="newcastle",
            address=Address(full_address="123 Test St"),
            proposal="Test proposal",
            status=ApplicationStatus.APPROVED_WITH_CONDITIONS,
        )
        assert app.is_approved is True

        app.status = ApplicationStatus.REFUSED
        assert app.is_approved is False


class TestApplicationDocument:
    """Tests for ApplicationDocument model."""

    def test_create_document(self):
        """Test creating a document."""
        doc = ApplicationDocument(
            id="doc1",
            application_reference="2026/0101/01/NPA",
            title="Location Plan",
            document_type=DocumentType.LOCATION_PLAN,
            file_type="pdf",
            source_url="https://example.com/doc.pdf",
        )
        assert doc.id == "doc1"
        assert doc.is_pdf is True
        assert doc.is_image is False

    def test_is_image(self):
        """Test is_image for different file types."""
        doc = ApplicationDocument(
            id="doc1",
            application_reference="2026/0101/01/NPA",
            title="Photo",
            file_type="jpg",
            source_url="https://example.com/photo.jpg",
        )
        assert doc.is_image is True
        assert doc.is_pdf is False


class TestPolicy:
    """Tests for Policy model."""

    def test_create_policy(self):
        """Test creating a policy."""
        policy = Policy(
            id="nppf-12",
            policy_type=PolicyType.NPPF,
            reference="NPPF-12",
            title="Achieving well-designed places",
            content="Good design is key...",
        )
        assert policy.reference == "NPPF-12"
        assert policy.is_current is True

    def test_superseded_policy(self):
        """Test superseded policy."""
        policy = Policy(
            id="old-policy",
            policy_type=PolicyType.LOCAL_PLAN,
            reference="OLD1",
            title="Old Policy",
            content="Content",
            superseded_date=date(2024, 1, 1),
        )
        assert policy.is_current is False


class TestReport:
    """Tests for Report model."""

    def test_create_report(self):
        """Test creating a report."""
        from datetime import datetime

        sections = [
            ReportSection(
                section_id="s1",
                title="Site and Surroundings",
                content="The site is located...",
                order=1,
            ),
            ReportSection(
                section_id="s2",
                title="The Proposal",
                content="The proposal seeks...",
                order=2,
            ),
        ]

        report = Report(
            id="report1",
            application_reference="2026/0101/01/NPA",
            template_version="1.0.0",
            prompt_version="1.0.0",
            sections=sections,
            generated_at=datetime.utcnow(),
        )

        assert report.id == "report1"
        assert len(report.sections) == 2

    def test_full_content(self):
        """Test full_content property."""
        from datetime import datetime

        sections = [
            ReportSection(
                section_id="s1",
                title="Introduction",
                content="Welcome",
                order=1,
            ),
            ReportSection(
                section_id="s2",
                title="Conclusion",
                content="The end",
                order=2,
            ),
        ]

        report = Report(
            id="r1",
            application_reference="2026/0101/01/NPA",
            template_version="1.0",
            prompt_version="1.0",
            sections=sections,
            generated_at=datetime.utcnow(),
        )

        content = report.full_content
        assert "## Introduction" in content
        assert "## Conclusion" in content
        assert "Welcome" in content
