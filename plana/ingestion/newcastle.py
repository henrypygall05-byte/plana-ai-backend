"""
Newcastle City Council planning portal adapter.

Implements the CouncilAdapter interface for Newcastle's planning portal.

Portal: https://portal.newcastle.gov.uk/planning/

Note: As of 2025, the portal uses Idox software with WAF protection
that blocks automated CLI access with HTTP 406 (IDX002 error).
This adapter is designed to work when the portal allows automated
access, but currently requires browser-based access.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional
from urllib.parse import urlencode, urljoin, urlparse

from plana.ingestion.base import (
    ApplicationDetails,
    ApplicationStatus,
    ApplicationType,
    Constraint,
    CouncilAdapter,
    PortalAccessError,
    PortalDocument,
)

# Optional dependencies for live mode
_LIVE_DEPS_AVAILABLE = False
_LIVE_DEPS_ERROR = None

try:
    import httpx
    from bs4 import BeautifulSoup
    _LIVE_DEPS_AVAILABLE = True
except ImportError as e:
    _LIVE_DEPS_ERROR = str(e)


def _check_live_deps() -> None:
    """Raise helpful ImportError if live dependencies are missing."""
    if not _LIVE_DEPS_AVAILABLE:
        raise ImportError(
            "Live mode requires extra dependencies. "
            "Install with: pip install -e '.[live]'"
        )


def is_idox_waf_block(response_text: str, status_code: int) -> bool:
    """Check if response indicates Idox WAF blocking.

    Args:
        response_text: HTTP response body
        status_code: HTTP status code

    Returns:
        True if this is an Idox WAF block (IDX002 error)
    """
    if status_code != 406:
        return False

    # Check for Idox error page indicators
    idox_indicators = [
        "IDX002",
        "Idox",
        "Error (IDX",
        "idoxgroup.com",
        "contact the Idox service desk",
    ]

    for indicator in idox_indicators:
        if indicator in response_text:
            return True

    return False


class NewcastleAdapter(CouncilAdapter):
    """
    Adapter for Newcastle City Council's planning portal.

    Portal URL: https://portal.newcastle.gov.uk/planning/

    IMPORTANT: The Newcastle portal currently blocks automated CLI access
    with HTTP 406 (Idox IDX002 error code). This is a WAF/CDN protection
    that requires browser-like access. The adapter will fail with a clear
    error message explaining this limitation.

    When portal access is available, implements:
    - Rate limiting (min 1 second between requests)
    - Retry with exponential backoff
    - Proper User-Agent
    - Response caching
    """

    # Current portal URL (portal.newcastle.gov.uk replaced publicaccess.newcastle.gov.uk)
    BASE_URL = "https://portal.newcastle.gov.uk"
    PLANNING_PATH = "/planning"

    # Old Idox endpoints (for reference - DO NOT USE)
    # The old publicaccess.newcastle.gov.uk domain is DEAD (returns 403)
    _LEGACY_BASE_URL = "https://publicaccess.newcastle.gov.uk/online-applications"  # DO NOT USE

    # Rate limiting
    MIN_REQUEST_INTERVAL = 1.0  # seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2.0  # exponential backoff multiplier

    # Request settings
    TIMEOUT = 30.0
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def __init__(self):
        """Initialize the Newcastle adapter."""
        _check_live_deps()

        self._last_request_time = 0
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: dict = {}

    def get_search_url(self, reference: str) -> str:
        """Build the search URL for a reference.

        Args:
            reference: Application reference number

        Returns:
            Full search URL for the portal
        """
        # Newcastle portal search endpoint
        return f"{self.BASE_URL}{self.PLANNING_PATH}/search.do?action=simple&searchCriteria.reference={reference}"

    def get_portal_url(self, reference: str) -> str:
        """Get the portal URL for display purposes.

        Args:
            reference: Application reference number

        Returns:
            URL to display to users
        """
        return f"{self.BASE_URL}{self.PLANNING_PATH}/index.html"

    @property
    def council_id(self) -> str:
        return "newcastle"

    @property
    def council_name(self) -> str:
        return "Newcastle City Council"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.9",
                },
                follow_redirects=True,
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            await asyncio.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    async def _fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL with retry and rate limiting.

        Args:
            url: URL to fetch

        Returns:
            Response text or None if not found (404)

        Raises:
            PortalAccessError: If access is blocked (403/406) or other HTTP error persists
        """
        client = await self._get_client()
        last_status_code = None
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                await self._rate_limit()
                response = await client.get(url)
                last_status_code = response.status_code

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    return None
                elif response.status_code == 406:
                    # Check for Idox WAF block (IDX002)
                    if is_idox_waf_block(response.text, response.status_code):
                        raise PortalAccessError(
                            "Portal blocked automated access (Idox IDX002)",
                            url=url,
                            status_code=406,
                        )
                    # Other 406 errors - retry
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = self.RETRY_BACKOFF ** (attempt + 1)
                        await asyncio.sleep(wait_time)
                    else:
                        raise PortalAccessError(
                            "Portal rejected request (406 Not Acceptable)",
                            url=url,
                            status_code=406,
                        )
                elif response.status_code == 403:
                    # Bot protection - wait longer and retry
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = self.RETRY_BACKOFF ** (attempt + 2)
                        await asyncio.sleep(wait_time)
                    else:
                        raise PortalAccessError(
                            "Portal blocked automated access (403 Forbidden)",
                            url=url,
                            status_code=403,
                        )
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = self.RETRY_BACKOFF ** (attempt + 1)
                        await asyncio.sleep(wait_time)
                    else:
                        raise PortalAccessError(
                            "Portal temporarily unavailable",
                            url=url,
                            status_code=response.status_code,
                        )
                else:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = self.RETRY_BACKOFF ** (attempt + 1)
                        await asyncio.sleep(wait_time)
                    else:
                        raise PortalAccessError(
                            f"HTTP error {response.status_code}",
                            url=url,
                            status_code=response.status_code,
                        )

            except httpx.TimeoutException as e:
                last_error = str(e)
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF ** (attempt + 1)
                    await asyncio.sleep(wait_time)
            except httpx.HTTPError as e:
                last_error = str(e)
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF ** (attempt + 1)
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        if last_status_code:
            raise PortalAccessError(
                f"Failed after {self.MAX_RETRIES} retries",
                url=url,
                status_code=last_status_code,
            )
        elif last_error:
            raise PortalAccessError(
                f"Connection failed: {last_error}",
                url=url,
            )

        return None

    def _parse_reference(self, reference: str) -> str:
        """Normalize application reference format."""
        # Newcastle format: YYYY/NNNN/NN/XXX
        return reference.strip().upper()

    def _parse_status(self, status_text: str) -> ApplicationStatus:
        """Parse status text to ApplicationStatus enum."""
        status_lower = status_text.lower()

        if "pending" in status_lower:
            return ApplicationStatus.PENDING
        elif "valid" in status_lower:
            return ApplicationStatus.VALIDATED
        elif "consideration" in status_lower or "progress" in status_lower:
            return ApplicationStatus.UNDER_CONSIDERATION
        elif "awaiting" in status_lower:
            return ApplicationStatus.AWAITING_DECISION
        elif "granted" in status_lower or "approved" in status_lower:
            if "condition" in status_lower:
                return ApplicationStatus.APPROVED_WITH_CONDITIONS
            return ApplicationStatus.APPROVED
        elif "refused" in status_lower or "reject" in status_lower:
            return ApplicationStatus.REFUSED
        elif "withdrawn" in status_lower:
            return ApplicationStatus.WITHDRAWN
        elif "appeal" in status_lower:
            return ApplicationStatus.APPEAL

        return ApplicationStatus.UNKNOWN

    def _parse_application_type(self, type_text: str) -> ApplicationType:
        """Parse application type text to ApplicationType enum."""
        type_lower = type_text.lower()

        if "householder" in type_lower:
            return ApplicationType.HOUSEHOLDER
        elif "listed building" in type_lower:
            return ApplicationType.LISTED_BUILDING
        elif "conservation" in type_lower:
            return ApplicationType.CONSERVATION_AREA
        elif "outline" in type_lower:
            return ApplicationType.OUTLINE
        elif "reserved" in type_lower:
            return ApplicationType.RESERVED_MATTERS
        elif "change of use" in type_lower:
            return ApplicationType.CHANGE_OF_USE
        elif "advert" in type_lower:
            return ApplicationType.ADVERTISEMENT
        elif "tree" in type_lower:
            return ApplicationType.TREE_WORKS
        elif "prior" in type_lower:
            return ApplicationType.PRIOR_NOTIFICATION
        elif "lawful" in type_lower or "certificate" in type_lower:
            return ApplicationType.LAWFUL_DEVELOPMENT
        elif "discharge" in type_lower or "condition" in type_lower:
            return ApplicationType.DISCHARGE_CONDITIONS
        elif "full" in type_lower:
            return ApplicationType.FULL

        return ApplicationType.OTHER

    def _extract_postcode(self, address: str) -> Optional[str]:
        """Extract postcode from address string."""
        # UK postcode pattern
        pattern = r"[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}"
        match = re.search(pattern, address.upper())
        return match.group(0) if match else None

    async def fetch_application(self, reference: str) -> Optional[ApplicationDetails]:
        """Fetch application details from the portal.

        Args:
            reference: Application reference number

        Returns:
            ApplicationDetails or None if not found

        Raises:
            PortalAccessError: If portal blocks access (406/403) or is unavailable (5xx)
        """
        reference = self._parse_reference(reference)

        # Build search URL using the current portal
        search_url = self.get_search_url(reference)

        html = await self._fetch_with_retry(search_url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Find application link in search results
        app_link = None
        for link in soup.find_all("a", href=True):
            if "applicationDetails.do" in link["href"]:
                app_link = link["href"]
                break

        if not app_link:
            # Try direct URL construction
            return await self._fetch_application_direct(reference)

        # Fetch application details page
        details_url = urljoin(f"{self.BASE_URL}{self.PLANNING_PATH}/", app_link)
        details_html = await self._fetch_with_retry(details_url)
        if not details_html:
            return None

        return self._parse_application_page(details_html, reference, details_url)

    async def _fetch_application_direct(self, reference: str) -> Optional[ApplicationDetails]:
        """Try to fetch application using alternative URL patterns."""
        # Some portals allow direct reference lookup
        alt_url = f"{self.BASE_URL}{self.PLANNING_PATH}/applicationDetails.do"
        params = {"keyVal": reference.replace("/", "")}
        full_url = f"{alt_url}?{urlencode(params)}"

        html = await self._fetch_with_retry(full_url)
        if html and "Application not found" not in html:
            return self._parse_application_page(html, reference, full_url)

        return None

    def _parse_application_page(
        self, html: str, reference: str, url: str
    ) -> Optional[ApplicationDetails]:
        """Parse application details from HTML page."""
        soup = BeautifulSoup(html, "html.parser")

        def get_field(label: str) -> Optional[str]:
            """Extract field value by label text."""
            # Try table cell format
            for th in soup.find_all(["th", "td"]):
                if label.lower() in th.get_text().lower():
                    next_td = th.find_next_sibling("td")
                    if next_td:
                        return next_td.get_text(strip=True)

            # Try definition list format
            for dt in soup.find_all("dt"):
                if label.lower() in dt.get_text().lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)

            # Try span with class format
            for span in soup.find_all("span", class_=re.compile(r".*value.*", re.I)):
                prev = span.find_previous(["span", "label"])
                if prev and label.lower() in prev.get_text().lower():
                    return span.get_text(strip=True)

            return None

        # Extract key fields
        address = get_field("address") or get_field("site") or get_field("location") or ""
        proposal = get_field("proposal") or get_field("description") or ""
        status_text = get_field("status") or ""
        type_text = get_field("type") or get_field("application type") or ""

        if not address and not proposal:
            return None

        # Parse constraints
        constraints = []
        constraints_section = soup.find(string=re.compile(r"constraint", re.I))
        if constraints_section:
            parent = constraints_section.find_parent()
            if parent:
                for li in parent.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        constraints.append(Constraint(
                            constraint_type=self._categorize_constraint(text),
                            name=text,
                        ))

        # Extract key from URL
        portal_key = None
        if "keyVal=" in url:
            match = re.search(r"keyVal=([^&]+)", url)
            if match:
                portal_key = match.group(1)

        return ApplicationDetails(
            reference=reference,
            council_id=self.council_id,
            address=address,
            proposal=proposal,
            application_type=self._parse_application_type(type_text),
            status=self._parse_status(status_text),
            date_received=get_field("received") or get_field("date received"),
            date_validated=get_field("validated") or get_field("valid date"),
            decision_date=get_field("decision") or get_field("decision date"),
            target_date=get_field("target") or get_field("determination date"),
            applicant_name=get_field("applicant"),
            agent_name=get_field("agent"),
            ward=get_field("ward"),
            parish=get_field("parish"),
            postcode=self._extract_postcode(address),
            decision=get_field("decision") if "grant" in (get_field("decision") or "").lower() or "refuse" in (get_field("decision") or "").lower() else None,
            decision_level=get_field("decision level") or get_field("delegated"),
            portal_url=url,
            portal_key=portal_key,
            fetched_at=datetime.now(),
            constraints=constraints,
        )

    def _categorize_constraint(self, constraint_text: str) -> str:
        """Categorize a constraint by its text."""
        text_lower = constraint_text.lower()

        if "conservation" in text_lower:
            return "conservation_area"
        elif "listed" in text_lower:
            return "listed_building"
        elif "flood" in text_lower:
            return "flood_zone"
        elif "green belt" in text_lower:
            return "green_belt"
        elif "tree" in text_lower or "tpo" in text_lower:
            return "tree_preservation_order"
        elif "sssi" in text_lower:
            return "sssi"
        elif "ancient" in text_lower:
            return "ancient_woodland"

        return "other"

    async def fetch_documents(self, reference: str) -> List[PortalDocument]:
        """Fetch list of documents for an application.

        Args:
            reference: Application reference number

        Returns:
            List of PortalDocument objects
        """
        reference = self._parse_reference(reference)

        # First get the application to find the portal key
        app = await self.fetch_application(reference)
        if not app or not app.portal_key:
            return []

        # Fetch documents tab
        docs_url = f"{self.BASE_URL}{self.PLANNING_PATH}/applicationDetails.do"
        params = {
            "activeTab": "documents",
            "keyVal": app.portal_key,
        }
        full_url = f"{docs_url}?{urlencode(params)}"

        html = await self._fetch_with_retry(full_url)
        if not html:
            return []

        return self._parse_documents_page(html, reference)

    def _parse_documents_page(self, html: str, reference: str) -> List[PortalDocument]:
        """Parse documents list from HTML page."""
        soup = BeautifulSoup(html, "html.parser")
        documents = []

        # Find document table or list
        doc_links = soup.find_all("a", href=re.compile(r"documentfiles|viewDocument"))

        for i, link in enumerate(doc_links):
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or not href:
                continue

            # Get document URL
            doc_url = urljoin(f"{self.BASE_URL}{self.PLANNING_PATH}/", href)

            # Try to get date from parent row
            date_published = None
            parent_row = link.find_parent("tr")
            if parent_row:
                date_cells = parent_row.find_all("td")
                for cell in date_cells:
                    text = cell.get_text(strip=True)
                    if re.match(r"\d{2}/\d{2}/\d{4}", text):
                        date_published = text
                        break

            # Guess document type from title
            doc_type = self._categorize_document(title)

            documents.append(PortalDocument(
                id=f"{reference}_{i:03d}",
                title=title,
                doc_type=doc_type,
                url=doc_url,
                date_published=date_published,
            ))

        return documents

    def _categorize_document(self, title: str) -> str:
        """Categorize document by its title."""
        title_lower = title.lower()

        if "application form" in title_lower:
            return "application_form"
        elif "design" in title_lower and "access" in title_lower:
            return "design_access_statement"
        elif "heritage" in title_lower:
            return "heritage_statement"
        elif "plan" in title_lower and ("floor" in title_lower or "proposed" in title_lower):
            return "plans"
        elif "elevation" in title_lower:
            return "elevations"
        elif "site" in title_lower and "plan" in title_lower:
            return "site_plan"
        elif "location" in title_lower:
            return "location_plan"
        elif "flood" in title_lower:
            return "flood_assessment"
        elif "tree" in title_lower:
            return "tree_report"
        elif "ecology" in title_lower or "biodiversity" in title_lower:
            return "ecology_report"
        elif "transport" in title_lower or "travel" in title_lower:
            return "transport_statement"
        elif "noise" in title_lower:
            return "noise_assessment"
        elif "contamination" in title_lower or "ground" in title_lower:
            return "contamination_report"
        elif "decision" in title_lower or "notice" in title_lower:
            return "decision_notice"
        elif "consultation" in title_lower or "response" in title_lower:
            return "consultation_response"

        return "other"

    async def download_document(
        self, document: PortalDocument, dest_dir: str
    ) -> Optional[str]:
        """Download a document to local storage.

        Args:
            document: Document to download
            dest_dir: Destination directory

        Returns:
            Local file path or None if download failed
        """
        client = await self._get_client()
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)

        for attempt in range(self.MAX_RETRIES):
            try:
                await self._rate_limit()

                async with client.stream("GET", document.url) as response:
                    if response.status_code != 200:
                        continue

                    # Get content type
                    content_type = response.headers.get("content-type", "")
                    document.content_type = content_type

                    # Determine file extension
                    ext = self._get_extension(content_type, document.title)

                    # Create safe filename
                    safe_title = re.sub(r"[^\w\s-]", "_", document.title)[:50]
                    filename = f"{document.id}_{safe_title}{ext}"
                    filepath = dest_path / filename

                    # Download with hash calculation
                    hasher = hashlib.md5()
                    total_bytes = 0

                    with open(filepath, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            hasher.update(chunk)
                            total_bytes += len(chunk)

                    document.content_hash = hasher.hexdigest()
                    document.size_bytes = total_bytes
                    document.local_path = str(filepath)

                    return str(filepath)

            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF ** (attempt + 1)
                    await asyncio.sleep(wait_time)

        return None

    def _get_extension(self, content_type: str, title: str) -> str:
        """Determine file extension from content type or title."""
        content_type_map = {
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.ms-excel": ".xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        }

        for ct, ext in content_type_map.items():
            if ct in content_type.lower():
                return ext

        # Try title
        title_lower = title.lower()
        for ext in [".pdf", ".doc", ".docx", ".jpg", ".png"]:
            if ext in title_lower:
                return ext

        return ".pdf"  # Default

    async def search_applications(
        self,
        postcode: Optional[str] = None,
        address: Optional[str] = None,
        ward: Optional[str] = None,
        status: Optional[ApplicationStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        max_results: int = 50,
    ) -> List[ApplicationDetails]:
        """Search for applications.

        Args:
            postcode: Filter by postcode
            address: Filter by address text
            ward: Filter by ward name
            status: Filter by status
            date_from: Applications received from this date
            date_to: Applications received to this date
            max_results: Maximum results to return

        Returns:
            List of ApplicationDetails
        """
        search_url = f"{self.BASE_URL}{self.PLANNING_PATH}/advancedSearchResults.do"

        params = {"action": "firstPage"}
        if address:
            params["searchCriteria.address"] = address
        if postcode:
            params["searchCriteria.postcode"] = postcode
        if ward:
            params["searchCriteria.ward"] = ward
        if date_from:
            params["searchCriteria.receivedDateStart"] = date_from.strftime("%d/%m/%Y")
        if date_to:
            params["searchCriteria.receivedDateEnd"] = date_to.strftime("%d/%m/%Y")

        full_url = f"{search_url}?{urlencode(params)}"
        html = await self._fetch_with_retry(full_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Find application links in search results
        for link in soup.find_all("a", href=re.compile(r"applicationDetails\.do")):
            if len(results) >= max_results:
                break

            href = link.get("href", "")
            ref_match = re.search(r"(\d{4}/\d+/\d+/\w+)", link.get_text())
            if ref_match:
                reference = ref_match.group(1)
                app = await self.fetch_application(reference)
                if app:
                    results.append(app)

        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
