"""
Feedback data models.

Defines the structure for different types of feedback
used to improve system performance.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Types of feedback that can be recorded."""

    REPORT_EDIT = "report_edit"  # Changes made to generated report
    REPORT_RATING = "report_rating"  # Overall report quality rating
    SECTION_EDIT = "section_edit"  # Changes to specific section
    SIMILARITY_USEFUL = "similarity_useful"  # Similar case was useful
    SIMILARITY_NOT_USEFUL = "similarity_not_useful"  # Similar case was not useful
    POLICY_RELEVANT = "policy_relevant"  # Policy was relevant
    POLICY_NOT_RELEVANT = "policy_not_relevant"  # Policy was not relevant
    POLICY_MISSING = "policy_missing"  # A policy should have been included
    OUTCOME_RECORDED = "outcome_recorded"  # Final decision outcome recorded
    DOCUMENT_CLASSIFICATION = "document_classification"  # Correct document type


class ReportFeedback(BaseModel):
    """Feedback on a generated report."""

    id: str = Field(..., description="Unique feedback ID")
    report_id: str = Field(..., description="Report this feedback is for")
    application_reference: str = Field(..., description="Application reference")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    rating: int | None = Field(
        None, ge=1, le=5, description="Quality rating 1-5"
    )
    original_content: str | None = Field(
        None, description="Original generated content"
    )
    edited_content: str | None = Field(
        None, description="User-edited content"
    )
    section_id: str | None = Field(
        None, description="Section ID if section-specific"
    )
    comments: str | None = Field(None, description="User comments")
    user_id: str | None = Field(None, description="User who provided feedback")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When feedback was created"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimilarityFeedback(BaseModel):
    """Feedback on similar case recommendations."""

    id: str = Field(..., description="Unique feedback ID")
    application_reference: str = Field(..., description="Query application")
    similar_case_reference: str = Field(..., description="Similar case reference")
    was_useful: bool = Field(..., description="Whether case was useful")
    similarity_score: float = Field(..., description="Original similarity score")
    usage_context: str | None = Field(
        None, description="How the case was used"
    )
    user_id: str | None = Field(None, description="User who provided feedback")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyFeedback(BaseModel):
    """Feedback on policy retrieval."""

    id: str = Field(..., description="Unique feedback ID")
    application_reference: str = Field(..., description="Application reference")
    policy_id: str = Field(..., description="Policy ID")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    was_cited_in_final: bool = Field(
        default=False, description="Whether policy was cited in final report"
    )
    relevance_score: float | None = Field(
        None, ge=0, le=1, description="Relevance score"
    )
    comments: str | None = Field(None, description="User comments")
    user_id: str | None = Field(None, description="User who provided feedback")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OutcomeFeedback(BaseModel):
    """Records actual planning decision outcomes."""

    id: str = Field(..., description="Unique feedback ID")
    application_reference: str = Field(..., description="Application reference")
    predicted_outcome: str | None = Field(
        None, description="What the system predicted"
    )
    actual_outcome: str = Field(..., description="Actual decision outcome")
    decision_date: datetime = Field(..., description="Date of decision")
    conditions_count: int | None = Field(
        None, description="Number of conditions if approved"
    )
    refusal_reasons: list[str] | None = Field(
        None, description="Refusal reasons if refused"
    )
    appeal_lodged: bool = Field(default=False, description="Whether appealed")
    appeal_outcome: str | None = Field(None, description="Appeal outcome if appealed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentClassificationFeedback(BaseModel):
    """Feedback on document classification."""

    id: str = Field(..., description="Unique feedback ID")
    document_id: str = Field(..., description="Document ID")
    application_reference: str = Field(..., description="Application reference")
    predicted_type: str = Field(..., description="Predicted document type")
    correct_type: str = Field(..., description="Correct document type")
    user_id: str | None = Field(None, description="User who provided feedback")
    created_at: datetime = Field(default_factory=datetime.utcnow)
