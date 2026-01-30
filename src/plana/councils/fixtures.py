"""
Fixture-based portal for offline development and testing.

Provides pre-captured application data so developers can test
the full pipeline without live portal access.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import AsyncIterator

import structlog

from plana.config import get_settings
from plana.councils.base import ApplicationNotFoundError, CouncilPortal
from plana.core.models import (
    Address,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    ApplicationType,
    Constraint,
    DocumentType,
)

logger = structlog.get_logger(__name__)


# Built-in fixture data for demo purposes
DEMO_APPLICATIONS = {
    "2024/0930/01/DET": {
        "reference": "2024/0930/01/DET",
        "address": {
            "full_address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
            "postcode": "NE1 5JQ",
            "ward": "Monument",
        },
        "proposal": "Erection of two storey rear/roof extension and conversion of upper floors to create a mixed use development with retention of retail at ground/basement levels and delivery of 188 units of serviced accommodation (Class C1) with ancillary facilities including conference suite, business suites, cinema room, golf simulator, gym, games area, atrium and wellness retreat.",
        "application_type": "full",
        "status": "under_review",
        "received_date": "2024-06-15",
        "constraints": [
            {"constraint_type": "conservation_area", "name": "Grainger Town Conservation Area"},
            {"constraint_type": "listed_building_setting", "name": "Adjacent to Grade II listed buildings"},
        ],
        "documents": [
            {"id": "doc1", "title": "Application Form", "type": "application_form", "file_type": "pdf"},
            {"id": "doc2", "title": "Location Plan", "type": "location_plan", "file_type": "pdf"},
            {"id": "doc3", "title": "Design and Access Statement", "type": "design_access_statement", "file_type": "pdf"},
            {"id": "doc4", "title": "Heritage Impact Assessment", "type": "heritage_statement", "file_type": "pdf"},
            {"id": "doc5", "title": "Proposed Floor Plans", "type": "floor_plan", "file_type": "pdf"},
            {"id": "doc6", "title": "Proposed Elevations", "type": "elevation", "file_type": "pdf"},
        ],
    },
    "2024/0943/01/LBC": {
        "reference": "2024/0943/01/LBC",
        "address": {
            "full_address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
            "postcode": "NE1 5JQ",
            "ward": "Monument",
        },
        "proposal": "Listed Building Application for internal and external works including insertion of ground floor shop frontage entrances, internal alterations to facilitate change of use, and associated works.",
        "application_type": "listed_building",
        "status": "under_review",
        "received_date": "2024-06-15",
        "constraints": [
            {"constraint_type": "listed_building", "name": "Grade II Listed Building"},
            {"constraint_type": "conservation_area", "name": "Grainger Town Conservation Area"},
        ],
        "documents": [
            {"id": "doc1", "title": "Listed Building Application Form", "type": "application_form", "file_type": "pdf"},
            {"id": "doc2", "title": "Heritage Statement", "type": "heritage_statement", "file_type": "pdf"},
            {"id": "doc3", "title": "Schedule of Works", "type": "other", "file_type": "pdf"},
        ],
    },
    "2024/0300/01/LBC": {
        "reference": "2024/0300/01/LBC",
        "address": {
            "full_address": "155-159 Grainger Street, Newcastle Upon Tyne, NE1 5AE",
            "postcode": "NE1 5AE",
            "ward": "Monument",
        },
        "proposal": "Listed Building Consent for alterations to elevations including new shopfront, re-located entrance doors, enclosed staircase with 3 rooflights, air conditioning units, and internal alterations including replacing goods lift with passenger lift and creating meeting/training rooms.",
        "application_type": "listed_building",
        "status": "approved",
        "received_date": "2024-02-20",
        "decision_date": "2024-05-15",
        "constraints": [
            {"constraint_type": "listed_building", "name": "Grade II Listed Building"},
            {"constraint_type": "conservation_area", "name": "Grainger Town Conservation Area"},
        ],
        "documents": [
            {"id": "doc1", "title": "Application Form", "type": "application_form", "file_type": "pdf"},
            {"id": "doc2", "title": "Heritage Impact Assessment", "type": "heritage_statement", "file_type": "pdf"},
            {"id": "doc3", "title": "Proposed Plans", "type": "floor_plan", "file_type": "pdf"},
        ],
    },
    "2025/0015/01/DET": {
        "reference": "2025/0015/01/DET",
        "address": {
            "full_address": "Southern Area of Town Moor, Grandstand Road, Newcastle Upon Tyne, NE2 3NH",
            "postcode": "NE2 3NH",
            "ward": "South Jesmond",
        },
        "proposal": "Installation and repair of land drainage and construction of a Sustainable Drainage System (SuDS) with landscaping works including creation of wetland areas and native planting.",
        "application_type": "full",
        "status": "under_review",
        "received_date": "2025-01-10",
        "constraints": [
            {"constraint_type": "green_space", "name": "Town Moor"},
            {"constraint_type": "flood_zone", "name": "Flood Zone 2"},
        ],
        "documents": [
            {"id": "doc1", "title": "Application Form", "type": "application_form", "file_type": "pdf"},
            {"id": "doc2", "title": "Drainage Strategy", "type": "flood_risk_assessment", "file_type": "pdf"},
            {"id": "doc3", "title": "Ecological Assessment", "type": "ecology_report", "file_type": "pdf"},
            {"id": "doc4", "title": "Site Plan", "type": "site_plan", "file_type": "pdf"},
        ],
    },
    "2023/1500/01/HOU": {
        "reference": "2023/1500/01/HOU",
        "address": {
            "full_address": "42 Jesmond Road, Newcastle Upon Tyne, NE2 1NL",
            "postcode": "NE2 1NL",
            "ward": "Jesmond",
        },
        "proposal": "Single storey rear extension and loft conversion with rear dormer window.",
        "application_type": "householder",
        "status": "approved",
        "received_date": "2023-10-05",
        "decision_date": "2023-12-01",
        "constraints": [],
        "documents": [
            {"id": "doc1", "title": "Application Form", "type": "application_form", "file_type": "pdf"},
            {"id": "doc2", "title": "Existing and Proposed Plans", "type": "floor_plan", "file_type": "pdf"},
            {"id": "doc3", "title": "Elevations", "type": "elevation", "file_type": "pdf"},
        ],
    },
}

# Sample document content for testing
SAMPLE_DOCUMENT_CONTENT = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Sample Document) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000206 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF
"""


class FixturePortal(CouncilPortal):
    """
    Fixture-based portal for offline development.

    Uses pre-captured data instead of live portal access.
    Toggle with PLANA_USE_FIXTURES=true environment variable.
    """

    def __init__(self, council_id: str, fixtures_path: Path | None = None):
        """Initialize fixture portal.

        Args:
            council_id: Council identifier
            fixtures_path: Path to custom fixtures directory
        """
        super().__init__(council_id)
        self.fixtures_path = fixtures_path or (get_settings().data_dir / "fixtures" / council_id)
        self._applications = dict(DEMO_APPLICATIONS)
        self._load_custom_fixtures()

    def _load_custom_fixtures(self) -> None:
        """Load any custom fixtures from disk."""
        if not self.fixtures_path.exists():
            return

        for fixture_file in self.fixtures_path.glob("*.json"):
            try:
                with open(fixture_file) as f:
                    data = json.load(f)
                    if "reference" in data:
                        self._applications[data["reference"]] = data
                        logger.debug("Loaded fixture", reference=data["reference"])
            except Exception as e:
                logger.warning("Failed to load fixture", file=str(fixture_file), error=str(e))

    @property
    def portal_base_url(self) -> str:
        return "https://fixtures.local/planning"

    @property
    def council_name(self) -> str:
        return f"{self.council_id.title()} (Fixtures)"

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    async def fetch_application(self, reference: str) -> Application:
        """Fetch application from fixtures."""
        reference = self.normalize_reference(reference)
        logger.info("Fetching from fixtures", reference=reference)

        if reference not in self._applications:
            raise ApplicationNotFoundError(f"No fixture for application {reference}")

        data = self._applications[reference]

        # Build constraints
        constraints = [
            Constraint(
                constraint_type=c["constraint_type"],
                name=c["name"],
            )
            for c in data.get("constraints", [])
        ]

        # Build address
        addr_data = data["address"]
        address = Address(
            full_address=addr_data["full_address"],
            postcode=addr_data.get("postcode"),
            ward=addr_data.get("ward"),
        )

        # Build application
        return Application(
            reference=reference,
            council_id=self.council_id,
            address=address,
            proposal=data["proposal"],
            application_type=ApplicationType(data["application_type"]),
            status=ApplicationStatus(data["status"]),
            received_date=self._parse_date(data.get("received_date")),
            decision_date=self._parse_date(data.get("decision_date")),
            constraints=constraints,
            source_url=f"{self.portal_base_url}/{reference}",
            fetched_at=datetime.utcnow(),
        )

    async def fetch_application_documents(
        self, reference: str
    ) -> list[ApplicationDocument]:
        """Fetch document list from fixtures."""
        reference = self.normalize_reference(reference)

        if reference not in self._applications:
            raise ApplicationNotFoundError(f"No fixture for application {reference}")

        data = self._applications[reference]
        documents = []

        for doc_data in data.get("documents", []):
            doc = ApplicationDocument(
                id=doc_data["id"],
                application_reference=reference,
                title=doc_data["title"],
                document_type=DocumentType(doc_data["type"]),
                file_type=doc_data.get("file_type", "pdf"),
                source_url=f"{self.portal_base_url}/documents/{doc_data['id']}.{doc_data.get('file_type', 'pdf')}",
            )
            documents.append(doc)

        return documents

    async def download_document(
        self, document: ApplicationDocument
    ) -> AsyncIterator[bytes]:
        """Return sample document content."""
        # Check for real fixture file
        doc_file = self.fixtures_path / "documents" / f"{document.id}.{document.file_type}"
        if doc_file.exists():
            content = doc_file.read_bytes()
            yield content
            return

        # Return sample PDF content
        yield SAMPLE_DOCUMENT_CONTENT

    async def search_applications(
        self,
        *,
        postcode: str | None = None,
        address: str | None = None,
        ward: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        application_type: str | None = None,
        max_results: int = 100,
    ) -> list[Application]:
        """Search fixtures."""
        results = []

        for ref, data in self._applications.items():
            # Apply filters
            if postcode:
                app_postcode = data["address"].get("postcode", "")
                if postcode.upper() not in app_postcode.upper():
                    continue

            if address:
                app_address = data["address"]["full_address"]
                if address.lower() not in app_address.lower():
                    continue

            if ward:
                app_ward = data["address"].get("ward", "")
                if ward.lower() not in app_ward.lower():
                    continue

            # Fetch full application
            app = await self.fetch_application(ref)
            results.append(app)

            if len(results) >= max_results:
                break

        return results

    def validate_reference(self, reference: str) -> bool:
        """Validate reference format."""
        import re
        pattern = r"^\d{4}/\d{4}/\d{2}/[A-Z]{2,4}$"
        return bool(re.match(pattern, reference.strip().upper()))

    def normalize_reference(self, reference: str) -> str:
        """Normalize reference."""
        return reference.strip().upper()


def save_fixture(application: Application, fixtures_path: Path) -> None:
    """Save an application as a fixture for future offline use.

    Args:
        application: Application to save
        fixtures_path: Directory to save fixtures
    """
    fixtures_path.mkdir(parents=True, exist_ok=True)

    # Convert to fixture format
    fixture_data = {
        "reference": application.reference,
        "address": {
            "full_address": application.address.full_address,
            "postcode": application.address.postcode,
            "ward": application.address.ward,
        },
        "proposal": application.proposal,
        "application_type": application.application_type.value,
        "status": application.status.value,
        "received_date": application.received_date.isoformat() if application.received_date else None,
        "decision_date": application.decision_date.isoformat() if application.decision_date else None,
        "constraints": [
            {"constraint_type": c.constraint_type, "name": c.name}
            for c in application.constraints
        ],
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "type": d.document_type.value,
                "file_type": d.file_type,
            }
            for d in application.documents
        ],
    }

    # Save fixture
    ref_safe = application.reference.replace("/", "_")
    fixture_file = fixtures_path / f"{ref_safe}.json"

    with open(fixture_file, "w") as f:
        json.dump(fixture_data, f, indent=2)

    logger.info("Saved fixture", reference=application.reference, file=str(fixture_file))
