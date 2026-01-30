"""Tests for council portal integrations."""

import pytest

from plana.councils import CouncilRegistry, NewcastlePortal
from plana.councils.base import CouncilPortal


class TestCouncilRegistry:
    """Tests for CouncilRegistry."""

    def test_get_newcastle(self):
        """Test getting Newcastle portal."""
        portal = CouncilRegistry.get("newcastle")
        assert isinstance(portal, NewcastlePortal)
        assert portal.council_id == "newcastle"

    def test_get_case_insensitive(self):
        """Test registry is case insensitive."""
        portal = CouncilRegistry.get("NEWCASTLE")
        assert isinstance(portal, NewcastlePortal)

    def test_get_unknown_council(self):
        """Test getting unknown council raises error."""
        with pytest.raises(ValueError) as exc_info:
            CouncilRegistry.get("unknown")
        assert "not registered" in str(exc_info.value)

    def test_list_councils(self):
        """Test listing available councils."""
        councils = CouncilRegistry.list_councils()
        assert "newcastle" in councils

    def test_is_registered(self):
        """Test checking if council is registered."""
        assert CouncilRegistry.is_registered("newcastle") is True
        assert CouncilRegistry.is_registered("unknown") is False


class TestNewcastlePortal:
    """Tests for NewcastlePortal."""

    @pytest.fixture
    def portal(self):
        """Create Newcastle portal."""
        return NewcastlePortal("newcastle")

    def test_portal_properties(self, portal):
        """Test portal properties."""
        assert portal.council_id == "newcastle"
        assert portal.council_name == "Newcastle City Council"
        assert "newcastle.gov.uk" in portal.portal_base_url

    def test_validate_reference_valid(self, portal):
        """Test validating correct reference formats."""
        assert portal.validate_reference("2026/0101/01/NPA") is True
        assert portal.validate_reference("2025/1234/01/FUL") is True

    def test_validate_reference_invalid(self, portal):
        """Test validating incorrect reference formats."""
        assert portal.validate_reference("invalid") is False
        assert portal.validate_reference("2026-0101-01-NPA") is False
        assert portal.validate_reference("") is False

    def test_normalize_reference(self, portal):
        """Test reference normalization."""
        assert portal.normalize_reference("2026/0101/01/npa") == "2026/0101/01/NPA"
        assert portal.normalize_reference("  2026/0101/01/NPA  ") == "2026/0101/01/NPA"

    def test_parse_status(self, portal):
        """Test status parsing."""
        from plana.core.models import ApplicationStatus

        assert portal._parse_status("Granted") == ApplicationStatus.APPROVED
        assert portal._parse_status("Refused") == ApplicationStatus.REFUSED
        assert portal._parse_status("Pending consideration") == ApplicationStatus.UNDER_REVIEW
        assert portal._parse_status("Unknown status") == ApplicationStatus.UNKNOWN

    def test_parse_application_type(self, portal):
        """Test application type parsing."""
        from plana.core.models import ApplicationType

        assert portal._parse_application_type("Full planning") == ApplicationType.FULL
        assert portal._parse_application_type("Householder") == ApplicationType.HOUSEHOLDER
        assert portal._parse_application_type("Listed Building") == ApplicationType.LISTED_BUILDING
        assert portal._parse_application_type("Unknown") == ApplicationType.OTHER

    def test_classify_document_type(self, portal):
        """Test document type classification."""
        from plana.core.models import DocumentType

        assert portal._classify_document_type("Location Plan") == DocumentType.LOCATION_PLAN
        assert portal._classify_document_type("Design and Access Statement") == DocumentType.DESIGN_ACCESS_STATEMENT
        assert portal._classify_document_type("Flood Risk Assessment") == DocumentType.FLOOD_RISK_ASSESSMENT
        assert portal._classify_document_type("Random Document") == DocumentType.OTHER

    def test_extract_postcode(self, portal):
        """Test postcode extraction."""
        assert portal._extract_postcode("123 Grey Street, Newcastle, NE1 6EE") == "NE1 6EE"
        assert portal._extract_postcode("Address without postcode") is None

    def test_parse_date(self, portal):
        """Test date parsing."""
        from datetime import date

        assert portal._parse_date("15 Jan 2026") == date(2026, 1, 15)
        assert portal._parse_date("15/01/2026") == date(2026, 1, 15)
        assert portal._parse_date("2026-01-15") == date(2026, 1, 15)
        assert portal._parse_date("invalid") is None
        assert portal._parse_date(None) is None
