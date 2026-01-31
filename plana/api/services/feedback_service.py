"""
Feedback service for API integration.

Handles user feedback submission for continuous improvement.
"""

import json
from datetime import datetime
from typing import List

from plana.api.models import FeedbackResponse
from plana.storage.database import Database
from plana.storage.models import StoredFeedback


class FeedbackService:
    """Service for handling user feedback."""

    def __init__(self):
        """Initialize the feedback service."""
        self.db = Database()

    async def submit_feedback(
        self,
        reference: str,
        decision: str,
        notes: str = None,
        conditions: List[str] = None,
        refusal_reasons: List[str] = None,
    ) -> FeedbackResponse:
        """Submit feedback for an application.

        Args:
            reference: Application reference
            decision: User's decision (APPROVE, APPROVE_WITH_CONDITIONS, REFUSE)
            notes: Additional notes
            conditions: Conditions if approving
            refusal_reasons: Reasons if refusing

        Returns:
            Feedback confirmation
        """
        feedback = StoredFeedback(
            reference=reference,
            decision=decision,
            notes=notes,
            conditions_json=json.dumps(conditions or []),
            refusal_reasons_json=json.dumps(refusal_reasons or []),
            actual_decision=decision,
            actual_decision_date=datetime.now().strftime("%Y-%m-%d"),
            submitted_by="api_user",
        )

        feedback_id = self.db.save_feedback(feedback)

        # Update policy weights based on feedback
        await self._update_policy_weights(reference, decision)

        return FeedbackResponse(
            feedback_id=feedback_id,
            status="success",
            message=f"Feedback submitted for {reference}",
        )

    async def _update_policy_weights(self, reference: str, decision: str) -> None:
        """Update policy weights based on feedback.

        This implements the continuous improvement loop by adjusting
        policy relevance weights based on user feedback.

        Args:
            reference: Application reference
            decision: User's decision
        """
        # Placeholder for continuous improvement loop
        # In production, would:
        # 1. Get the last run for this reference
        # 2. Compare user decision with Plana's prediction
        # 3. Update policy weights based on match/mismatch
        pass

    def _decisions_match(self, plana_decision: str, user_decision: str) -> bool:
        """Check if decisions match (exact or partial).

        Args:
            plana_decision: Plana's recommendation
            user_decision: User's decision

        Returns:
            True if decisions match
        """
        if not plana_decision or not user_decision:
            return False

        # Normalize
        plana = plana_decision.upper().replace("_", " ")
        user = user_decision.upper().replace("_", " ")

        # Exact match
        if plana == user:
            return True

        # Partial match (both approve variants)
        if "APPROVE" in plana and "APPROVE" in user:
            return True

        return False
