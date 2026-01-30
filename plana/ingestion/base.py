"""
Base interfaces for council portal adapters.

Defines the contract that all council adapters must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class PortalAccessError(Exception):
    """Exception raised when portal access fails.

    Attributes:
        url: The URL that failed
        status_code: HTTP status code (if available)
        message: Error message
    """

    def __init__(self, message: str, url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        self.message = message
        super().__init__(message)

    def __str__(self):
        parts = [self.message]
        if self.url:
            parts.append(f"URL: {self.url}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        return " | ".join(parts)


class ApplicationStatus(Enum):
    """Planning application status."""

    PENDING = "pending"
    VALIDATED = "validated"
    UNDER_CONSIDERATION = "under_consideration"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    APPEAL = "appeal"
    UNKNOWN = "unknown"


class ApplicationType(Enum):
    """Planning application type."""

    FULL = "full"
    HOUSEHOLDER = "householder"
    LISTED_BUILDING = "listed_building"
    CONSERVATION_AREA = "conservation_area"
    OUTLINE = "outline"
    RESERVED_MATTERS = "reserved_matters"
    CHANGE_OF_USE = "change_of_use"
    ADVERTISEMENT = "advertisement"
    TREE_WORKS = "tree_works"
    PRIOR_NOTIFICATION = "prior_notification"
    LAWFUL_DEVELOPMENT = "lawful_development"
    DISCHARGE_CONDITIONS = "discharge_conditions"
    OTHER = "other"


@dataclass
class PortalDocument:
    """A document from the planning portal."""

    id: str
    title: str
    doc_type: str
    url: str
    date_published: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    local_path: Optional[str] = None
    content_hash: Optional[str] = None


@dataclass
class Constraint:
    """A site constraint."""

    constraint_type: str
    name: str
    description: Optional[str] = None


@dataclass
class ApplicationDetails:
    """Full details of a planning application."""

    reference: str
    council_id: str
    address: str
    proposal: str
    application_type: ApplicationType
    status: ApplicationStatus

    # Dates
    date_received: Optional[str] = None
    date_validated: Optional[str] = None
    decision_date: Optional[str] = None
    target_date: Optional[str] = None

    # Parties
    applicant_name: Optional[str] = None
    agent_name: Optional[str] = None

    # Location
    ward: Optional[str] = None
    parish: Optional[str] = None
    postcode: Optional[str] = None
    easting: Optional[float] = None
    northing: Optional[float] = None

    # Constraints
    constraints: List[Constraint] = field(default_factory=list)

    # Decision details
    decision: Optional[str] = None
    decision_level: Optional[str] = None  # Delegated, Committee, etc.

    # Portal metadata
    portal_url: Optional[str] = None
    portal_key: Optional[str] = None  # Internal key used by portal

    # Timestamps
    fetched_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "reference": self.reference,
            "council_id": self.council_id,
            "address": self.address,
            "proposal": self.proposal,
            "application_type": self.application_type.value,
            "status": self.status.value,
            "date_received": self.date_received,
            "date_validated": self.date_validated,
            "decision_date": self.decision_date,
            "target_date": self.target_date,
            "applicant_name": self.applicant_name,
            "agent_name": self.agent_name,
            "ward": self.ward,
            "parish": self.parish,
            "postcode": self.postcode,
            "easting": self.easting,
            "northing": self.northing,
            "constraints": [
                {"type": c.constraint_type, "name": c.name, "description": c.description}
                for c in self.constraints
            ],
            "decision": self.decision,
            "decision_level": self.decision_level,
            "portal_url": self.portal_url,
            "portal_key": self.portal_key,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }


class CouncilAdapter(ABC):
    """Abstract base class for council portal adapters.

    Implementations must handle:
    - Fetching application details by reference
    - Fetching document lists
    - Downloading documents
    - Searching for applications
    """

    @property
    @abstractmethod
    def council_id(self) -> str:
        """Return the council identifier."""
        pass

    @property
    @abstractmethod
    def council_name(self) -> str:
        """Return the full council name."""
        pass

    @abstractmethod
    async def fetch_application(self, reference: str) -> Optional[ApplicationDetails]:
        """Fetch application details by reference number.

        Args:
            reference: Application reference number

        Returns:
            ApplicationDetails or None if not found
        """
        pass

    @abstractmethod
    async def fetch_documents(self, reference: str) -> List[PortalDocument]:
        """Fetch list of documents for an application.

        Args:
            reference: Application reference number

        Returns:
            List of PortalDocument objects
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    async def close(self) -> None:
        """Clean up resources. Override if needed."""
        pass
