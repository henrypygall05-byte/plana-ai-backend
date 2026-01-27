"""
Newcastle City Council planning portal integration.

This module implements the CouncilPortal interface for Newcastle City Council's
planning portal. This is the pilot implementation for Plana.AI.

Newcastle uses the Idox/Uniform planning portal system.
"""

import asyncio
import re
from datetime import date, datetime
from typing import AsyncIterator
from urllib.parse import urlencode, urljoin

import httpx
import structlog
from bs4 import BeautifulSoup, Tag

from plana.councils.base import (
    ApplicationNotFoundError,
    CouncilPortal,
    CouncilPortalError,
)
from plana.core.models import (
    Address,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    ApplicationType,
    DocumentType,
    GeoLocation,
)

logger = structlog.get_logger(__name__)


class NewcastlePortal(CouncilPortal):
    """
    Newcastle City Council planning portal implementation.

    Newcastle uses the Idox/Uniform portal system. This implementation
    handles the specific HTML structure and URL patterns of their portal.
    """

    @property
    def portal_base_url(self) -> str:
        return "https://publicaccess.newcastle.gov.uk/online-applications"

    @property
    def council_name(self) -> str:
        return "Newcastle City Council"

    def _build_application_url(self, reference: str) -> str:
        """Build URL for application details page."""
        params = urlencode({"applicationNumber": reference})
        return f"{self.portal_base_url}/applicationDetails.do?{params}"

    def _build_documents_url(self, reference: str) -> str:
        """Build URL for application documents page."""
        params = urlencode({"applicationNumber": reference})
        return f"{self.portal_base_url}/documents.do?{params}"

    def _build_search_url(self, **kwargs) -> str:
        """Build URL for search results."""
        params = {
            "searchType": "Application",
            "searchBy": "any",
            "sortOrder": "RECEIVED_DESC",
        }

        if kwargs.get("postcode"):
            params["postcodeSearch"] = kwargs["postcode"]
        if kwargs.get("address"):
            params["addressSearch"] = kwargs["address"]
        if kwargs.get("date_from"):
            params["receivedDateFrom"] = kwargs["date_from"]
        if kwargs.get("date_to"):
            params["receivedDateTo"] = kwargs["date_to"]
        if kwargs.get("ward"):
            params["wardSearch"] = kwargs["ward"]
        if kwargs.get("status"):
            params["statusSearch"] = kwargs["status"]

        return f"{self.portal_base_url}/search.do?{urlencode(params)}"

    def validate_reference(self, reference: str) -> bool:
        """Validate Newcastle reference format.

        Newcastle references typically follow: YYYY/NNNN/NN/XXX
        Example: 2026/0101/01/NPA
        """
        pattern = r"^\d{4}/\d{4}/\d{2}/[A-Z]{2,4}$"
        return bool(re.match(pattern, reference.strip().upper()))

    def normalize_reference(self, reference: str) -> str:
        """Normalize reference to uppercase."""
        return reference.strip().upper()

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date from portal format."""
        if not date_str:
            return None

        date_str = date_str.strip()
        formats = ["%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d %B %Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        logger.warning("Could not parse date", date_str=date_str)
        return None

    def _parse_status(self, status_str: str | None) -> ApplicationStatus:
        """Parse application status from portal text."""
        if not status_str:
            return ApplicationStatus.UNKNOWN

        status_str = status_str.lower().strip()
        status_map = {
            "pending consideration": ApplicationStatus.UNDER_REVIEW,
            "pending decision": ApplicationStatus.AWAITING_DECISION,
            "under consideration": ApplicationStatus.UNDER_REVIEW,
            "awaiting decision": ApplicationStatus.AWAITING_DECISION,
            "granted": ApplicationStatus.APPROVED,
            "approved": ApplicationStatus.APPROVED,
            "conditionally approved": ApplicationStatus.APPROVED_WITH_CONDITIONS,
            "approved with conditions": ApplicationStatus.APPROVED_WITH_CONDITIONS,
            "refused": ApplicationStatus.REFUSED,
            "rejected": ApplicationStatus.REFUSED,
            "withdrawn": ApplicationStatus.WITHDRAWN,
            "appeal lodged": ApplicationStatus.APPEALED,
            "appeal in progress": ApplicationStatus.APPEALED,
            "registered": ApplicationStatus.PENDING,
            "received": ApplicationStatus.PENDING,
        }

        for key, value in status_map.items():
            if key in status_str:
                return value

        return ApplicationStatus.UNKNOWN

    def _parse_application_type(self, type_str: str | None) -> ApplicationType:
        """Parse application type from portal text."""
        if not type_str:
            return ApplicationType.OTHER

        type_str = type_str.lower()
        type_map = {
            "full planning": ApplicationType.FULL,
            "full application": ApplicationType.FULL,
            "outline": ApplicationType.OUTLINE,
            "reserved matters": ApplicationType.RESERVED_MATTERS,
            "householder": ApplicationType.HOUSEHOLDER,
            "listed building": ApplicationType.LISTED_BUILDING,
            "conservation area": ApplicationType.CONSERVATION_AREA,
            "change of use": ApplicationType.CHANGE_OF_USE,
            "advertisement": ApplicationType.ADVERTISEMENT,
            "prior approval": ApplicationType.PRIOR_APPROVAL,
            "prior notification": ApplicationType.PRIOR_APPROVAL,
            "lawful development": ApplicationType.LAWFUL_DEVELOPMENT,
            "certificate of lawfulness": ApplicationType.LAWFUL_DEVELOPMENT,
            "discharge of conditions": ApplicationType.DISCHARGE_CONDITIONS,
            "variation of condition": ApplicationType.VARIATION_CONDITIONS,
            "tree": ApplicationType.TREE_WORKS,
            "tpo": ApplicationType.TREE_WORKS,
            "demolition": ApplicationType.DEMOLITION,
            "environmental impact": ApplicationType.ENVIRONMENTAL_IMPACT,
            "eia": ApplicationType.ENVIRONMENTAL_IMPACT,
        }

        for key, value in type_map.items():
            if key in type_str:
                return value

        return ApplicationType.OTHER

    def _classify_document_type(self, title: str, description: str = "") -> DocumentType:
        """Classify document type based on title and description."""
        text = f"{title} {description}".lower()

        patterns = {
            DocumentType.APPLICATION_FORM: [
                "application form",
                "application for",
            ],
            DocumentType.LOCATION_PLAN: [
                "location plan",
                "site location",
                "os plan",
            ],
            DocumentType.SITE_PLAN: [
                "site plan",
                "block plan",
                "site layout",
            ],
            DocumentType.FLOOR_PLAN: [
                "floor plan",
                "ground floor",
                "first floor",
                "layout plan",
                "floorplan",
            ],
            DocumentType.ELEVATION: [
                "elevation",
                "elevations",
                "front elevation",
                "rear elevation",
                "side elevation",
            ],
            DocumentType.SECTION: [
                "section",
                "sections",
                "cross section",
            ],
            DocumentType.DESIGN_ACCESS_STATEMENT: [
                "design and access",
                "design & access",
                "d&a statement",
                "das",
            ],
            DocumentType.HERITAGE_STATEMENT: [
                "heritage statement",
                "heritage impact",
                "historic building",
            ],
            DocumentType.FLOOD_RISK_ASSESSMENT: [
                "flood risk",
                "fra",
                "drainage strategy",
                "suds",
            ],
            DocumentType.ECOLOGY_REPORT: [
                "ecology",
                "ecological",
                "biodiversity",
                "bat survey",
                "bird survey",
                "great crested newt",
                "protected species",
            ],
            DocumentType.TRANSPORT_ASSESSMENT: [
                "transport assessment",
                "transport statement",
                "travel plan",
                "traffic",
                "highways",
                "parking",
            ],
            DocumentType.NOISE_ASSESSMENT: [
                "noise assessment",
                "noise impact",
                "acoustic",
            ],
            DocumentType.AIR_QUALITY_ASSESSMENT: [
                "air quality",
                "aq assessment",
                "emissions",
            ],
            DocumentType.ARBORICULTURAL_REPORT: [
                "arboricultural",
                "tree survey",
                "tree report",
                "aia",
            ],
            DocumentType.ARCHAEOLOGICAL_ASSESSMENT: [
                "archaeological",
                "archaeology",
                "heritage asset",
            ],
            DocumentType.CONTAMINATION_REPORT: [
                "contamination",
                "contaminated land",
                "ground investigation",
                "geotechnical",
            ],
            DocumentType.ENERGY_STATEMENT: [
                "energy statement",
                "sustainability",
                "carbon",
                "renewable",
            ],
            DocumentType.PLANNING_STATEMENT: [
                "planning statement",
                "planning support",
            ],
            DocumentType.CASE_OFFICER_REPORT: [
                "officer report",
                "delegated report",
                "committee report",
            ],
            DocumentType.DECISION_NOTICE: [
                "decision notice",
                "planning permission",
                "approval notice",
                "refusal notice",
            ],
            DocumentType.CONSULTATION_RESPONSE: [
                "consultation response",
                "consultee",
            ],
            DocumentType.PUBLIC_COMMENT: [
                "public comment",
                "representation",
                "objection",
                "support letter",
            ],
            DocumentType.PHOTOGRAPH: [
                "photograph",
                "photo",
                "image",
            ],
        }

        for doc_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text:
                    return doc_type

        return DocumentType.OTHER

    async def fetch_application(self, reference: str) -> Application:
        """Fetch application details from Newcastle portal."""
        reference = self.normalize_reference(reference)
        logger.info("Fetching application", reference=reference, council=self.council_id)

        url = self._build_application_url(reference)
        html = await self._fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        # Check if application exists
        if "no results" in html.lower() or "application not found" in html.lower():
            raise ApplicationNotFoundError(f"Application {reference} not found")

        # Parse application details
        details = self._extract_details_from_soup(soup)

        # Parse address
        address_text = details.get("address", "")
        address = Address(
            full_address=address_text,
            postcode=self._extract_postcode(address_text),
            ward=details.get("ward"),
        )

        # Build application object
        application = Application(
            reference=reference,
            council_id=self.council_id,
            address=address,
            proposal=details.get("proposal", ""),
            application_type=self._parse_application_type(details.get("application_type")),
            status=self._parse_status(details.get("status")),
            received_date=self._parse_date(details.get("received_date")),
            validated_date=self._parse_date(details.get("validated_date")),
            consultation_end_date=self._parse_date(details.get("consultation_end")),
            target_decision_date=self._parse_date(details.get("target_date")),
            decision_date=self._parse_date(details.get("decision_date")),
            decision=details.get("decision"),
            case_officer=details.get("case_officer"),
            applicant_name=details.get("applicant"),
            agent_name=details.get("agent"),
            source_url=url,
            fetched_at=datetime.utcnow(),
            metadata={"raw_details": details},
        )

        logger.info(
            "Fetched application",
            reference=reference,
            status=application.status.value,
        )
        return application

    def _extract_details_from_soup(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract key-value details from application page."""
        details = {}

        # Try common Idox portal structures
        # Structure 1: Table rows with th/td
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower().replace(":", "")
                value = cells[1].get_text(strip=True)
                details[self._normalize_label(label)] = value

        # Structure 2: Definition lists
        for dl in soup.find_all("dl"):
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds):
                label = dt.get_text(strip=True).lower().replace(":", "")
                value = dd.get_text(strip=True)
                details[self._normalize_label(label)] = value

        # Structure 3: Labeled spans/divs
        for container in soup.find_all(class_=re.compile(r"(detail|field|row)")):
            label_elem = container.find(class_=re.compile(r"(label|key|name)"))
            value_elem = container.find(class_=re.compile(r"(value|data)"))
            if label_elem and value_elem:
                label = label_elem.get_text(strip=True).lower().replace(":", "")
                value = value_elem.get_text(strip=True)
                details[self._normalize_label(label)] = value

        return details

    def _normalize_label(self, label: str) -> str:
        """Normalize field labels to consistent keys."""
        label = label.lower().strip()
        mappings = {
            "application number": "reference",
            "reference": "reference",
            "site address": "address",
            "address": "address",
            "location": "address",
            "proposal": "proposal",
            "description": "proposal",
            "development": "proposal",
            "application type": "application_type",
            "type": "application_type",
            "status": "status",
            "current status": "status",
            "decision": "decision",
            "received": "received_date",
            "date received": "received_date",
            "registered": "received_date",
            "validated": "validated_date",
            "valid date": "validated_date",
            "consultation expiry": "consultation_end",
            "neighbour expiry": "consultation_end",
            "target date": "target_date",
            "determination date": "target_date",
            "decision date": "decision_date",
            "date of decision": "decision_date",
            "case officer": "case_officer",
            "planning officer": "case_officer",
            "applicant name": "applicant",
            "applicant": "applicant",
            "agent name": "agent",
            "agent": "agent",
            "ward": "ward",
            "parish": "parish",
        }
        return mappings.get(label, label.replace(" ", "_"))

    def _extract_postcode(self, address: str) -> str | None:
        """Extract postcode from address string."""
        pattern = r"[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}"
        match = re.search(pattern, address.upper())
        return match.group(0) if match else None

    async def fetch_application_documents(
        self, reference: str
    ) -> list[ApplicationDocument]:
        """Fetch document list for a Newcastle application."""
        reference = self.normalize_reference(reference)
        logger.info("Fetching documents", reference=reference)

        url = self._build_documents_url(reference)
        html = await self._fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        documents = []

        # Parse document table
        doc_table = soup.find("table", id=re.compile(r"document", re.I))
        if not doc_table:
            doc_table = soup.find("table", class_=re.compile(r"document", re.I))
        if not doc_table:
            # Try finding any table with document links
            for table in soup.find_all("table"):
                if table.find("a", href=re.compile(r"\.(pdf|jpg|png)", re.I)):
                    doc_table = table
                    break

        if doc_table:
            for row in doc_table.find_all("tr")[1:]:  # Skip header
                doc = self._parse_document_row(row, reference)
                if doc:
                    documents.append(doc)

        # Also check for document links outside tables
        for link in soup.find_all("a", href=re.compile(r"\.(pdf|jpg|jpeg|png|gif|tiff?)$", re.I)):
            if not any(d.source_url == link.get("href") for d in documents):
                doc = self._parse_document_link(link, reference)
                if doc:
                    documents.append(doc)

        logger.info(
            "Found documents",
            reference=reference,
            count=len(documents),
        )
        return documents

    def _parse_document_row(
        self, row: Tag, reference: str
    ) -> ApplicationDocument | None:
        """Parse a document table row."""
        cells = row.find_all("td")
        if not cells:
            return None

        # Find link
        link = row.find("a", href=True)
        if not link:
            return None

        href = link.get("href", "")
        if not href:
            return None

        # Make absolute URL
        if not href.startswith("http"):
            href = urljoin(self.portal_base_url, href)

        # Extract title
        title = link.get_text(strip=True)
        if not title:
            title = cells[0].get_text(strip=True) if cells else "Unknown"

        # Extract file type
        file_type = "pdf"  # Default
        ext_match = re.search(r"\.([a-zA-Z0-9]+)$", href.lower())
        if ext_match:
            file_type = ext_match.group(1)

        # Extract description and date from other cells
        description = ""
        pub_date = None

        for cell in cells[1:]:
            text = cell.get_text(strip=True)
            if self._parse_date(text):
                pub_date = self._parse_date(text)
            elif text and not description:
                description = text

        # Create unique ID
        doc_id = f"{reference}_{len(title)}_{hash(href) % 10000}"

        return ApplicationDocument(
            id=doc_id,
            application_reference=reference,
            title=title,
            document_type=self._classify_document_type(title, description),
            description=description or None,
            file_type=file_type,
            source_url=href,
            published_date=pub_date,
        )

    def _parse_document_link(
        self, link: Tag, reference: str
    ) -> ApplicationDocument | None:
        """Parse a standalone document link."""
        href = link.get("href", "")
        if not href:
            return None

        if not href.startswith("http"):
            href = urljoin(self.portal_base_url, href)

        title = link.get_text(strip=True) or "Unknown Document"

        file_type = "pdf"
        ext_match = re.search(r"\.([a-zA-Z0-9]+)$", href.lower())
        if ext_match:
            file_type = ext_match.group(1)

        doc_id = f"{reference}_{hash(href) % 100000}"

        return ApplicationDocument(
            id=doc_id,
            application_reference=reference,
            title=title,
            document_type=self._classify_document_type(title),
            file_type=file_type,
            source_url=href,
        )

    async def download_document(
        self, document: ApplicationDocument
    ) -> AsyncIterator[bytes]:
        """Download document content as stream."""
        logger.info(
            "Downloading document",
            doc_id=document.id,
            title=document.title,
        )

        client = await self.get_client()

        async with client.stream("GET", document.source_url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=8192):
                yield chunk

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
        """Search for applications on Newcastle portal."""
        logger.info(
            "Searching applications",
            postcode=postcode,
            address=address,
            ward=ward,
        )

        url = self._build_search_url(
            postcode=postcode,
            address=address,
            ward=ward,
            date_from=date_from,
            date_to=date_to,
            status=status,
        )

        html = await self._fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        applications = []
        references = []

        # Find search results
        results_table = soup.find("table", id=re.compile(r"result", re.I))
        if not results_table:
            results_table = soup.find("table", class_=re.compile(r"result", re.I))

        if results_table:
            for row in results_table.find_all("tr")[1:]:  # Skip header
                link = row.find("a", href=re.compile(r"applicationDetails", re.I))
                if link:
                    ref_text = link.get_text(strip=True)
                    if ref_text and self.validate_reference(ref_text):
                        references.append(ref_text)
                        if len(references) >= max_results:
                            break

        # Also look for reference links in other structures
        for link in soup.find_all("a", href=re.compile(r"applicationDetails", re.I)):
            ref_text = link.get_text(strip=True)
            if ref_text and self.validate_reference(ref_text):
                if ref_text not in references:
                    references.append(ref_text)
                if len(references) >= max_results:
                    break

        # Fetch full details for each (with delay)
        for ref in references[:max_results]:
            try:
                app = await self.fetch_application(ref)
                applications.append(app)
                await asyncio.sleep(self.settings.council.request_delay_seconds)
            except CouncilPortalError as e:
                logger.warning("Failed to fetch application", reference=ref, error=str(e))

        logger.info("Search complete", result_count=len(applications))
        return applications
