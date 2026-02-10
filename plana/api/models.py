"""
Pydantic models for API request/response schemas.

These models match the CASE_OUTPUT schema for Loveable integration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


# ============ Request Models ============

class ProcessApplicationRequest(BaseModel):
    """Request to process an application."""

    reference: str = Field(..., description="Application reference number")
    council_id: str = Field(default="newcastle", description="Council ID")
    mode: str = Field(default="demo", pattern="^(demo|live)$", description="Processing mode")


class DocumentInput(BaseModel):
    """Document input for manual import."""

    filename: str = Field(..., description="Document filename")
    document_type: str = Field(default="other", description="Type: application_form, plans, design_access_statement, heritage_statement, other")
    content_text: Optional[str] = Field(None, description="Extracted text content (if available)")


class ImportApplicationRequest(BaseModel):
    """Request to import and process an application manually.

    This allows users to input application details directly from their UI
    without fetching from a council portal.
    """

    # Required fields
    reference: str = Field(..., description="Application reference number (e.g., 24/03459/FUL)")
    site_address: str = Field(..., description="Full site address")
    # Accept both field names — frontend may send 'proposal' or 'proposal_description'
    proposal_description: str = Field(default="", description="Full description of the proposed development")
    proposal: Optional[str] = Field(None, exclude=True, description="Alias for proposal_description")

    # Optional metadata
    applicant_name: Optional[str] = Field(None, description="Applicant name")
    application_type: str = Field(
        default="Full Planning",
        description="Type: Full Planning, Householder, Listed Building, Outline, Reserved Matters, etc."
    )
    use_class: Optional[str] = Field(None, description="Use class (e.g., C3 Dwelling, E Commercial)")
    proposal_type: Optional[str] = Field(None, description="Short proposal type (e.g., Two-storey rear extension)")

    # Site designations/constraints (checkboxes in UI)
    conservation_area: bool = Field(default=False, description="Is site in a Conservation Area?")
    listed_building: bool = Field(default=False, description="Is site a Listed Building or in its curtilage?")
    green_belt: bool = Field(default=False, description="Is site in Green Belt?")
    additional_constraints: List[str] = Field(default_factory=list, description="Any additional constraints")

    # Location info
    council_id: str = Field(default="newcastle", description="Council ID")
    ward: Optional[str] = Field(None, description="Ward name")
    postcode: Optional[str] = Field(None, description="Site postcode")

    # Documents (optional - can be added later)
    documents: List[DocumentInput] = Field(default_factory=list, description="Uploaded documents")

    @model_validator(mode="before")
    @classmethod
    def resolve_proposal_field(cls, data):
        """Accept 'proposal' as alias for 'proposal_description'."""
        if isinstance(data, dict):
            pd = data.get("proposal_description", "")
            p = data.get("proposal", "")
            pt = data.get("proposal_type", "")
            if not pd and p:
                data["proposal_description"] = p
            elif not pd and pt:
                data["proposal_description"] = pt
        return data


class ImportApplicationResponse(BaseModel):
    """Response from importing an application."""

    status: str = Field(..., description="Status: success, error")
    message: str = Field(..., description="Status message")
    reference: str = Field(..., description="Application reference")
    report: Optional["CaseOutputResponse"] = Field(None, description="Generated report if successful")


class SubmitFeedbackRequest(BaseModel):
    """Request to submit feedback."""

    reference: str = Field(..., description="Application reference")
    decision: str = Field(..., pattern="^(APPROVE|APPROVE_WITH_CONDITIONS|REFUSE)$")
    notes: Optional[str] = Field(None, description="Additional notes")
    conditions: Optional[List[str]] = Field(default_factory=list, description="Conditions if approving")
    refusal_reasons: Optional[List[str]] = Field(default_factory=list, description="Reasons if refusing")


# ============ Response Models (CASE_OUTPUT Schema) ============

class MetaResponse(BaseModel):
    """Meta information about the report."""

    run_id: str
    reference: str
    council_id: str
    mode: str
    generated_at: str
    prompt_version: str = "1.0.0"
    report_schema_version: str = "1.0.0"


class PipelineCheck(BaseModel):
    """Individual pipeline check result."""

    name: str
    status: str  # PASS or FAIL
    details: Optional[str] = None


class PipelineAuditResponse(BaseModel):
    """Pipeline audit results."""

    checks: List[PipelineCheck]
    blocking_gaps: List[str] = Field(default_factory=list)
    non_blocking_gaps: List[str] = Field(default_factory=list)


class ApplicationSummaryResponse(BaseModel):
    """Application summary."""

    reference: str
    address: str
    proposal: str
    application_type: str
    constraints: List[str] = Field(default_factory=list)
    ward: Optional[str] = None
    postcode: Optional[str] = None


class DocumentsSummaryResponse(BaseModel):
    """Documents summary."""

    total_count: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    with_extracted_text: int = 0
    missing_suspected: List[str] = Field(default_factory=list)


class SelectedPolicy(BaseModel):
    """A policy that was selected for the report."""

    policy_id: str
    policy_name: str
    source: str
    relevance: str


class UnusedPolicy(BaseModel):
    """A policy that was retrieved but not used."""

    policy_id: str
    reason_unused: str


class PolicyContextResponse(BaseModel):
    """Policy context."""

    selected_policies: List[SelectedPolicy] = Field(default_factory=list)
    unused_policies: List[UnusedPolicy] = Field(default_factory=list)


class SimilarityCluster(BaseModel):
    """A cluster of similar cases."""

    cluster_name: str
    pattern: str
    cases: List[str] = Field(default_factory=list)


class TopCase(BaseModel):
    """A top similar case."""

    case_id: str
    reference: str
    relevance_reason: str
    outcome: Optional[str] = None
    similarity_score: float = 0.0


class IgnoredCase(BaseModel):
    """A case that was ignored."""

    case_id: str
    reason_ignored: str


class SimilarityAnalysisResponse(BaseModel):
    """Similarity analysis results."""

    clusters: List[SimilarityCluster] = Field(default_factory=list)
    top_cases: List[TopCase] = Field(default_factory=list)
    used_cases: List[str] = Field(default_factory=list)
    ignored_cases: List[IgnoredCase] = Field(default_factory=list)
    current_case_distinction: str = ""


class AssessmentTopic(BaseModel):
    """Assessment of a specific topic."""

    topic: str
    compliance: str  # compliant, non-compliant, partial, insufficient-evidence
    reasoning: str
    citations: List[str] = Field(default_factory=list)


class Risk(BaseModel):
    """A risk item."""

    risk: str
    likelihood: str  # low, medium, high
    impact: str  # low, medium, high
    mitigation: str


class Confidence(BaseModel):
    """Confidence assessment."""

    level: str  # low, medium, high
    score: float = 0.0
    limiting_factors: List[str] = Field(default_factory=list)


class AssessmentResponse(BaseModel):
    """Assessment results."""

    topics: List[AssessmentTopic] = Field(default_factory=list)
    planning_balance: str = ""
    risks: List[Risk] = Field(default_factory=list)
    confidence: Confidence = Field(default_factory=lambda: Confidence(level="medium", score=0.75))


class Condition(BaseModel):
    """A planning condition."""

    number: int
    condition: str
    reason: str
    policy_basis: Optional[str] = None


class RefusalReason(BaseModel):
    """A refusal reason."""

    number: int
    reason: str
    policy_basis: str


class InfoRequired(BaseModel):
    """Information required before determination."""

    item: str
    why_needed: str
    impact_if_missing: str


class RecommendationResponse(BaseModel):
    """Recommendation."""

    outcome: str  # APPROVE, APPROVE_WITH_CONDITIONS, REFUSE, INSUFFICIENT_EVIDENCE
    conditions: List[Condition] = Field(default_factory=list)
    refusal_reasons: List[RefusalReason] = Field(default_factory=list)
    info_required: List[InfoRequired] = Field(default_factory=list)


class Citation(BaseModel):
    """An evidence citation."""

    citation_id: str
    source_type: str  # document, policy, similar_case, metadata
    source_id: str
    title: str
    date: Optional[str] = None
    page: Optional[int] = None
    quote_or_excerpt: str = ""


class EvidenceResponse(BaseModel):
    """Evidence citations."""

    citations: List[Citation] = Field(default_factory=list)


class SimilaritySignal(BaseModel):
    """Similarity learning signal."""

    case_id: str
    action: str  # used, ignored
    signal: str  # rank-higher, rank-lower, maintain
    reason: str


class PolicySignal(BaseModel):
    """Policy learning signal."""

    policy_id: str
    action: str  # cited, unused
    signal: str  # more-relevant, less-relevant, maintain
    reason: str


class ReportSignal(BaseModel):
    """Report structure learning signal."""

    improvement: str
    section: Optional[str] = None


class OutcomePlaceholder(BaseModel):
    """Outcome placeholder for future update."""

    field: str
    current_value: Optional[str] = None
    to_update_when: str


class LearningSignalsResponse(BaseModel):
    """Learning signals for continuous improvement."""

    similarity: List[SimilaritySignal] = Field(default_factory=list)
    policy: List[PolicySignal] = Field(default_factory=list)
    report: List[ReportSignal] = Field(default_factory=list)
    outcome_placeholders: List[OutcomePlaceholder] = Field(default_factory=list)


class CaseOutputResponse(BaseModel):
    """Complete CASE_OUTPUT response for Loveable."""

    meta: MetaResponse
    pipeline_audit: PipelineAuditResponse
    application_summary: ApplicationSummaryResponse
    documents_summary: DocumentsSummaryResponse
    policy_context: PolicyContextResponse
    similarity_analysis: SimilarityAnalysisResponse
    assessment: AssessmentResponse
    recommendation: RecommendationResponse
    evidence: EvidenceResponse
    report_markdown: str
    learning_signals: LearningSignalsResponse


class ReportVersionResponse(BaseModel):
    """Report version summary."""

    version: int
    generated_at: str
    recommendation: str
    confidence: float
    prompt_version: str


class FeedbackResponse(BaseModel):
    """Feedback submission response."""

    feedback_id: int
    status: str
    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    timestamp: str
