"""
Base classes and interfaces for council portal integrations.

This module defines the abstract interface that all council-specific implementations
must follow, enabling multi-council support without code changes.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from plana.config import get_settings
from plana.core.models import Application, ApplicationDocument

logger = structlog.get_logger(__name__)


class CouncilPortalError(Exception):
    """Base exception for council portal errors."""

    pass


class ApplicationNotFoundError(CouncilPortalError):
    """Raised when an application cannot be found."""

    pass


class RateLimitError(CouncilPortalError):
    """Raised when rate limited by council portal."""

    pass


class CouncilPortal(ABC):
    """
    Abstract base class for council planning portal integrations.

    Each council portal implementation must provide methods to:
    - Search for applications
    - Fetch application details
    - List and download documents
    - Parse portal-specific data formats

    This abstraction allows the system to scale to multiple councils
    without rewriting core logic.
    """

    def __init__(self, council_id: str):
        """Initialize the council portal.

        Args:
            council_id: Unique identifier for this council
        """
        self.council_id = council_id
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    @property
    @abstractmethod
    def portal_base_url(self) -> str:
        """Base URL for the council's planning portal."""
        pass

    @property
    @abstractmethod
    def council_name(self) -> str:
        """Human-readable name of the council."""
        pass

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with appropriate settings."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.council.request_timeout_seconds),
                headers={
                    "User-Agent": self.settings.council.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.5",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _fetch_page(self, url: str) -> str:
        """Fetch a page with retry logic.

        Args:
            url: URL to fetch

        Returns:
            Page content as string

        Raises:
            CouncilPortalError: If fetch fails after retries
        """
        client = await self.get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ApplicationNotFoundError(f"Page not found: {url}")
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limited by {self.council_name}")
            raise CouncilPortalError(f"HTTP error {e.response.status_code}: {url}")
        except httpx.RequestError as e:
            raise CouncilPortalError(f"Request failed: {e}")

    @abstractmethod
    async def fetch_application(self, reference: str) -> Application:
        """Fetch a planning application by reference number.

        Args:
            reference: The application reference number (e.g., '2026/0101/01/NPA')

        Returns:
            Application object with metadata

        Raises:
            ApplicationNotFoundError: If application cannot be found
            CouncilPortalError: If fetch fails
        """
        pass

    @abstractmethod
    async def fetch_application_documents(
        self, reference: str
    ) -> list[ApplicationDocument]:
        """Fetch document list for a planning application.

        Args:
            reference: The application reference number

        Returns:
            List of ApplicationDocument objects with metadata

        Raises:
            ApplicationNotFoundError: If application cannot be found
            CouncilPortalError: If fetch fails
        """
        pass

    @abstractmethod
    async def download_document(
        self, document: ApplicationDocument
    ) -> AsyncIterator[bytes]:
        """Download a document's content as a stream.

        Args:
            document: The document to download

        Yields:
            Chunks of document content

        Raises:
            CouncilPortalError: If download fails
        """
        pass

    @abstractmethod
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
        """Search for planning applications.

        Args:
            postcode: Filter by postcode
            address: Filter by address text
            ward: Filter by ward name
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            status: Filter by status
            application_type: Filter by application type
            max_results: Maximum number of results

        Returns:
            List of matching applications
        """
        pass

    def validate_reference(self, reference: str) -> bool:
        """Validate that a reference number is correctly formatted.

        Args:
            reference: Reference number to validate

        Returns:
            True if valid format, False otherwise
        """
        # Default implementation - subclasses can override
        return bool(reference and len(reference) > 0)

    def normalize_reference(self, reference: str) -> str:
        """Normalize a reference number to canonical format.

        Args:
            reference: Reference number to normalize

        Returns:
            Normalized reference number
        """
        # Default implementation - subclasses can override
        return reference.strip().upper()


class CouncilRegistry:
    """Registry of available council portal implementations."""

    _councils: dict[str, type[CouncilPortal]] = {}

    @classmethod
    def register(cls, council_id: str, portal_class: type[CouncilPortal]) -> None:
        """Register a council portal implementation.

        Args:
            council_id: Unique identifier for the council
            portal_class: The portal implementation class
        """
        cls._councils[council_id.lower()] = portal_class
        logger.info("Registered council portal", council_id=council_id)

    @classmethod
    def get(cls, council_id: str) -> CouncilPortal:
        """Get a council portal instance.

        Args:
            council_id: The council identifier

        Returns:
            Initialized CouncilPortal instance

        Raises:
            ValueError: If council is not registered
        """
        council_id = council_id.lower()
        if council_id not in cls._councils:
            available = list(cls._councils.keys())
            raise ValueError(
                f"Council '{council_id}' not registered. Available: {available}"
            )
        return cls._councils[council_id](council_id)

    @classmethod
    def list_councils(cls) -> list[str]:
        """List all registered council IDs."""
        return list(cls._councils.keys())

    @classmethod
    def is_registered(cls, council_id: str) -> bool:
        """Check if a council is registered."""
        return council_id.lower() in cls._councils
