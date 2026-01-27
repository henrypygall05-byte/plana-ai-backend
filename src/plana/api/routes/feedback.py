"""Feedback endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from plana.feedback import FeedbackTracker, FeedbackType

router = APIRouter()


class ReportFeedbackRequest(BaseModel):
    """Request to submit report feedback."""

    report_id: str
    application_reference: str
    rating: int | None = Field(None, ge=1, le=5)
    section_id: str | None = None
    original_content: str | None = None
    edited_content: str | None = None
    comments: str | None = None


class SimilarityFeedbackRequest(BaseModel):
    """Request to submit similarity feedback."""

    application_reference: str
    similar_case_reference: str
    was_useful: bool
    similarity_score: float
    usage_context: str | None = None


class PolicyFeedbackRequest(BaseModel):
    """Request to submit policy feedback."""

    application_reference: str
    policy_id: str
    was_relevant: bool
    was_cited_in_final: bool = False
    comments: str | None = None


class OutcomeFeedbackRequest(BaseModel):
    """Request to record actual outcome."""

    application_reference: str
    actual_outcome: str
    decision_date: datetime
    predicted_outcome: str | None = None
    conditions_count: int | None = None
    refusal_reasons: list[str] | None = None


class FeedbackStatsResponse(BaseModel):
    """Feedback statistics response."""

    report_stats: dict[str, Any]
    outcome_accuracy: dict[str, Any]


@router.post("/report")
async def submit_report_feedback(
    request: ReportFeedbackRequest,
) -> dict[str, str]:
    """Submit feedback on a generated report.

    Args:
        request: Report feedback
    """
    tracker = FeedbackTracker()

    feedback_type = FeedbackType.REPORT_RATING
    if request.edited_content:
        feedback_type = FeedbackType.SECTION_EDIT if request.section_id else FeedbackType.REPORT_EDIT

    await tracker.record_report_feedback(
        report_id=request.report_id,
        application_reference=request.application_reference,
        feedback_type=feedback_type,
        rating=request.rating,
        original_content=request.original_content,
        edited_content=request.edited_content,
        section_id=request.section_id,
        comments=request.comments,
    )

    return {"status": "recorded", "message": "Feedback recorded successfully"}


@router.post("/similarity")
async def submit_similarity_feedback(
    request: SimilarityFeedbackRequest,
) -> dict[str, str]:
    """Submit feedback on similar case usefulness.

    Args:
        request: Similarity feedback
    """
    tracker = FeedbackTracker()

    await tracker.record_similarity_feedback(
        application_reference=request.application_reference,
        similar_case_reference=request.similar_case_reference,
        was_useful=request.was_useful,
        similarity_score=request.similarity_score,
        usage_context=request.usage_context,
    )

    return {"status": "recorded", "message": "Feedback recorded successfully"}


@router.post("/policy")
async def submit_policy_feedback(
    request: PolicyFeedbackRequest,
) -> dict[str, str]:
    """Submit feedback on policy relevance.

    Args:
        request: Policy feedback
    """
    tracker = FeedbackTracker()

    feedback_type = (
        FeedbackType.POLICY_RELEVANT if request.was_relevant else FeedbackType.POLICY_NOT_RELEVANT
    )

    await tracker.record_policy_feedback(
        application_reference=request.application_reference,
        policy_id=request.policy_id,
        feedback_type=feedback_type,
        was_cited_in_final=request.was_cited_in_final,
        comments=request.comments,
    )

    return {"status": "recorded", "message": "Feedback recorded successfully"}


@router.post("/outcome")
async def record_outcome(
    request: OutcomeFeedbackRequest,
) -> dict[str, str]:
    """Record actual planning decision outcome.

    Args:
        request: Outcome details
    """
    tracker = FeedbackTracker()

    await tracker.record_outcome(
        application_reference=request.application_reference,
        actual_outcome=request.actual_outcome,
        decision_date=request.decision_date,
        predicted_outcome=request.predicted_outcome,
        conditions_count=request.conditions_count,
        refusal_reasons=request.refusal_reasons,
    )

    return {"status": "recorded", "message": "Outcome recorded successfully"}


@router.get("/stats")
async def get_feedback_stats() -> FeedbackStatsResponse:
    """Get feedback statistics."""
    tracker = FeedbackTracker()

    report_stats = await tracker.get_report_feedback_stats()
    outcome_accuracy = await tracker.get_outcome_accuracy()

    return FeedbackStatsResponse(
        report_stats=report_stats,
        outcome_accuracy=outcome_accuracy,
    )
