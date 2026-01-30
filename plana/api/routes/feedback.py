"""Feedback submission endpoint."""

from fastapi import APIRouter, HTTPException

from plana.api.models import SubmitFeedbackRequest, FeedbackResponse
from plana.api.services import FeedbackService

router = APIRouter()


@router.post("", response_model=FeedbackResponse)
@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(request: SubmitFeedbackRequest) -> FeedbackResponse:
    """Submit feedback for an application.

    Args:
        request: Feedback submission request

    Returns:
        Feedback confirmation
    """
    try:
        service = FeedbackService()
        result = await service.submit_feedback(
            reference=request.reference,
            decision=request.decision,
            notes=request.notes,
            conditions=request.conditions or [],
            refusal_reasons=request.refusal_reasons or [],
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
