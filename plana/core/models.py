"""
Core domain models for Plana.AI planning intelligence platform.

These models represent the fundamental entities in the planning application domain.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class ApplicationStatus(str, Enum):
    """Status of a planning application."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    APPEALED = "appealed"
    UNKNOWN = "unknown"


class ApplicationType(str, Enum):
    """Type of planning application."""

    FULL = "full"
    OUTLINE = "outline"
    RESERVED_MATTERS = "reserved_matters"
    HOUSEHOLDER = "householder"
    LISTED_BUILDING = "listed_building"
    CONSERVATION_AREA = "conservation_area"
    CHANGE_OF_USE = "change_of_use"
    ADVERTISEMENT = "advertisement"
    PRIOR_APPROVAL = "prior_approval"
    LAWFUL_DEVELOPMENT = "lawful_development"
    DISCHARGE_CONDITIONS = "discharge_conditions"
    VARIATION_CONDITIONS = "variation_conditions"
    TREE_WORKS = "tree_works"
    DEMOLITION = "demolition"
    ENVIRONMENTAL_IMPACT = "environmental_impact"
    OTHER = "other"


class DocumentType(str, Enum):
    """Type of planning document."""

    APPLICATION_FORM = "application_form"
    LOCATION_PLAN = "location_plan"
    SITE_PLAN = "site_plan"
    FLOOR_PLAN = "floor_plan"
    ELEVATION = "elevation"
    SECTION = "section"
    DESIGN_ACCESS_STATEMENT = "design_access_statement"
    HERITAGE_STATEMENT = "heritage_statement"
    FLOOD_RISK_ASSESSMENT = "flood_risk_assessment"
    ECOLOGY_REPORT = "ecology_report"
    TRANSPORT_ASSESSMENT = "transport_assessment"
    NOISE_ASSESSMENT = "noise_assessment"
    AIR_QUALITY_ASSESSMENT = "air_quality_assessment"
    ARBORICULTURAL_REPORT = "arboricultural_report"
    ARCHAEOLOGICAL_ASSESSMENT = "archaeological_assessment"
    CONTAMINATION_REPORT = "contamination_report"
    ENERGY_STATEMENT = "energy_statement"
    VIABILITY_ASSESSMENT = "viability_assessment"
    PLANNING_STATEMENT = "planning_statement"
    CASE_OFFICER_REPORT = "case_officer_report"
    DECISION_NOTICE = "decision_notice"
    CONSULTATION_RESPONSE = "consultation_response"
    PUBLIC_COMMENT = "public_comment"
    APPEAL_DOCUMENT = "appeal_document"
    PHOTOGRAPH = "photograph"
    OTHER = "other"


class PolicyType(str, Enum):
    """Type of planning policy."""

    NPPF = "nppf"  # National Planning Policy Framework
    LOCAL_PLAN = "local_plan"
    SUPPLEMENTARY_PLANNING_DOCUMENT = "spd"
    NEIGHBOURHOOD_PLAN = "neighbourhood_plan"
    NATIONAL_GUIDANCE = "national_guidance"
    OTHER = "other"


class Constraint(BaseModel):
    """A planning constraint affecting a site."""

    constraint_type: str = Field(..., description="Type of constraint (e.g., 'conservation_area')")
    name: str = Field(..., description="Name of the constraint")
    description: str | None = Field(None, description="Description of constraint implications")
    buffer_distance_meters: float | None = Field(
        None, description="Distance from site to constraint if applicable"
    )
    source: str | None = Field(None, description="Source of constraint data")
    verified_date: date | None = Field(None, description="Date constraint was verified")


class GeoLocation(BaseModel):
    """Geographic location with coordinates."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    easting: float | None = Field(None, description="OS Grid easting")
    northing: float | None = Field(None, description="OS Grid northing")


class Address(BaseModel):
    """Structured address for a planning site."""

    full_address: str = Field(..., description="Complete address string")
    address_line_1: str | None = None
    address_line_2: str | None = None
    town: str | None = None
    county: str | None = None
    postcode: str | None = None
    ward: str | None = Field(None, description="Electoral ward")
    parish: str | None = Field(None, description="Parish if applicable")
    location: GeoLocation | None = None


class ApplicationDocument(BaseModel):
    """A document associated with a planning application."""

    id: str = Field(..., description="Unique document identifier")
    application_reference: str = Field(..., description="Parent application reference")
    title: str = Field(..., description="Document title")
    document_type: DocumentType = Field(
        default=DocumentType.OTHER, description="Classified document type"
    )
    description: str | None = Field(None, description="Document description")
    file_type: str = Field(..., description="File extension (pdf, jpg, png, etc.)")
    file_size_bytes: int | None = Field(None, description="File size in bytes")
    source_url: str = Field(..., description="Original source URL")
    storage_path: str | None = Field(None, description="Local or object storage path")
    checksum: str | None = Field(None, description="SHA-256 hash for deduplication")
    published_date: date | None = Field(None, description="Date document was published")
    downloaded_at: datetime | None = Field(None, description="When document was downloaded")
    text_extracted: bool = Field(default=False, description="Whether text has been extracted")
    text_storage_path: str | None = Field(None, description="Path to extracted text")
    page_count: int | None = Field(None, description="Number of pages for PDFs")
    classification_confidence: float | None = Field(
        None, ge=0, le=1, description="Confidence of document type classification"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @computed_field
    @property
    def is_image(self) -> bool:
        """Check if document is an image file."""
        return self.file_type.lower() in ("jpg", "jpeg", "png", "gif", "tiff", "bmp")

    @computed_field
    @property
    def is_pdf(self) -> bool:
        """Check if document is a PDF."""
        return self.file_type.lower() == "pdf"


class DocumentExtractionStatus(BaseModel):
    """Tracks the extraction progress of documents for an application."""

    queued: int = Field(default=0, description="Documents waiting for extraction")
    extracted: int = Field(default=0, description="Documents successfully extracted")
    failed: int = Field(default=0, description="Documents that failed extraction")

    @computed_field
    @property
    def is_ready_for_report(self) -> bool:
        """Check if extraction state allows report generation.

        Report generation is allowed when:
        - At least one document has been extracted, OR
        - No documents are queued and at least one failed (all attempted)
        """
        if self.extracted > 0:
            return True
        if self.queued == 0 and self.failed > 0:
            return True
        return False

    @computed_field
    @property
    def is_processing(self) -> bool:
        """Check if documents are still being processed.

        True when documents exist, none extracted, none failed, some queued.
        """
        total = self.queued + self.extracted + self.failed
        return (
            total > 0
            and self.extracted == 0
            and self.failed == 0
            and self.queued > 0
        )


class Application(BaseModel):
    """A planning application with full metadata."""

    reference: str = Field(..., description="Planning application reference number")
    council_id: str = Field(..., description="Council identifier (e.g., 'newcastle')")
    address: Address = Field(..., description="Site address")
    proposal: str = Field(..., description="Proposal description")
    application_type: ApplicationType = Field(
        default=ApplicationType.OTHER, description="Type of application"
    )
    status: ApplicationStatus = Field(
        default=ApplicationStatus.UNKNOWN, description="Current status"
    )
    extraction_status: DocumentExtractionStatus = Field(
        default_factory=DocumentExtractionStatus,
        description="Document extraction progress",
    )
    received_date: date | None = Field(None, description="Date application was received")
    validated_date: date | None = Field(None, description="Date application was validated")
    consultation_end_date: date | None = Field(None, description="End of consultation period")
    target_decision_date: date | None = Field(None, description="Target date for decision")
    decision_date: date | None = Field(None, description="Actual decision date")
    decision: str | None = Field(None, description="Decision outcome text")
    case_officer: str | None = Field(None, description="Assigned case officer name")
    applicant_name: str | None = Field(None, description="Applicant name")
    agent_name: str | None = Field(None, description="Agent name if applicable")
    constraints: list[Constraint] = Field(default_factory=list, description="Site constraints")
    documents: list[ApplicationDocument] = Field(
        default_factory=list, description="Associated documents"
    )
    source_url: str | None = Field(None, description="URL to application on council portal")
    fetched_at: datetime | None = Field(None, description="When data was last fetched")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @computed_field
    @property
    def is_decided(self) -> bool:
        """Check if application has received a decision."""
        return self.status in (
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.REFUSED,
            ApplicationStatus.WITHDRAWN,
        )

    @computed_field
    @property
    def is_approved(self) -> bool:
        """Check if application was approved."""
        return self.status in (
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
        )


class Policy(BaseModel):
    """A planning policy document or section."""

    id: str = Field(..., description="Unique policy identifier")
    policy_type: PolicyType = Field(..., description="Type of policy")
    reference: str = Field(..., description="Policy reference code")
    title: str = Field(..., description="Policy title")
    content: str = Field(..., description="Full policy text content")
    summary: str | None = Field(None, description="Brief summary of policy intent")
    chapter: str | None = Field(None, description="Chapter or section name")
    council_id: str | None = Field(
        None, description="Council ID if local policy, None for national"
    )
    effective_date: date | None = Field(None, description="Date policy came into effect")
    superseded_date: date | None = Field(None, description="Date policy was superseded")
    source_url: str | None = Field(None, description="Source URL for policy")
    embedding_id: str | None = Field(None, description="ID in vector store")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def is_current(self) -> bool:
        """Check if policy is currently in effect."""
        return self.superseded_date is None


class HistoricCase(BaseModel):
    """A historic planning case used for similarity comparison."""

    application: Application = Field(..., description="The historic application")
    similarity_score: float = Field(
        ..., ge=0, le=1, description="Similarity score to query application"
    )
    similarity_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of similarity by factor (location, type, etc.)",
    )
    relevance_notes: str | None = Field(
        None, description="Notes on why this case is relevant"
    )
    was_useful: bool | None = Field(
        None, description="Feedback on whether case was useful in report"
    )


class ReportSection(BaseModel):
    """A section of a generated planning report."""

    section_id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in markdown")
    order: int = Field(..., description="Order in report")
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to supporting evidence (document IDs, policy IDs)",
    )
    confidence: float | None = Field(
        None, ge=0, le=1, description="Confidence in section content"
    )


class Report(BaseModel):
    """A generated case officer-style planning report."""

    id: str = Field(..., description="Unique report identifier")
    application_reference: str = Field(..., description="Application this report is for")
    version: int = Field(default=1, description="Report version number")
    template_version: str = Field(..., description="Template version used")
    prompt_version: str = Field(..., description="Prompt version used")
    sections: list[ReportSection] = Field(..., description="Report sections")
    policies_cited: list[str] = Field(
        default_factory=list, description="Policy IDs cited in report"
    )
    historic_cases_cited: list[str] = Field(
        default_factory=list, description="Historic case references cited"
    )
    documents_referenced: list[str] = Field(
        default_factory=list, description="Document IDs referenced"
    )
    recommendation: str | None = Field(
        None, description="Overall recommendation (approve/refuse/defer)"
    )
    recommendation_confidence: float | None = Field(
        None, ge=0, le=1, description="Confidence in recommendation"
    )
    generated_at: datetime = Field(..., description="When report was generated")
    generation_time_seconds: float | None = Field(
        None, description="Time taken to generate report"
    )
    model_used: str | None = Field(None, description="AI model used for generation")
    total_tokens_used: int | None = Field(None, description="Total tokens consumed")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def full_content(self) -> str:
        """Get full report content as markdown."""
        return "\n\n".join(
            f"## {section.title}\n\n{section.content}"
            for section in sorted(self.sections, key=lambda s: s.order)
        )
