"""
Feedback tracking and storage.

Collects and stores feedback for system improvement.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from plana.config import get_settings
from plana.feedback.models import (
    DocumentClassificationFeedback,
    FeedbackType,
    OutcomeFeedback,
    PolicyFeedback,
    ReportFeedback,
    SimilarityFeedback,
)

logger = structlog.get_logger(__name__)


class FeedbackTracker:
    """
    Tracks and stores feedback for system improvement.

    Stores feedback in JSON files for pilot phase.
    Production would use a database.
    """

    def __init__(self, storage_path: Path | None = None):
        """Initialize feedback tracker.

        Args:
            storage_path: Path to store feedback files
        """
        settings = get_settings()
        self.storage_path = storage_path or settings.data_dir / "feedback"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory caches for aggregation
        self._similarity_scores: dict[str, list[float]] = {}
        self._policy_relevance: dict[str, list[bool]] = {}

    async def record_report_feedback(
        self,
        report_id: str,
        application_reference: str,
        feedback_type: FeedbackType,
        rating: int | None = None,
        original_content: str | None = None,
        edited_content: str | None = None,
        section_id: str | None = None,
        comments: str | None = None,
        user_id: str | None = None,
    ) -> ReportFeedback:
        """Record feedback on a generated report.

        Args:
            report_id: Report ID
            application_reference: Application reference
            feedback_type: Type of feedback
            rating: Quality rating 1-5
            original_content: Original content
            edited_content: Edited content
            section_id: Section ID if applicable
            comments: User comments
            user_id: User ID

        Returns:
            Created feedback record
        """
        feedback = ReportFeedback(
            id=str(uuid.uuid4()),
            report_id=report_id,
            application_reference=application_reference,
            feedback_type=feedback_type,
            rating=rating,
            original_content=original_content,
            edited_content=edited_content,
            section_id=section_id,
            comments=comments,
            user_id=user_id,
        )

        await self._save_feedback("report", feedback.model_dump())

        logger.info(
            "Recorded report feedback",
            report_id=report_id,
            feedback_type=feedback_type.value,
        )

        return feedback

    async def record_similarity_feedback(
        self,
        application_reference: str,
        similar_case_reference: str,
        was_useful: bool,
        similarity_score: float,
        usage_context: str | None = None,
        user_id: str | None = None,
    ) -> SimilarityFeedback:
        """Record feedback on similar case usefulness.

        Args:
            application_reference: Query application
            similar_case_reference: Similar case
            was_useful: Whether case was useful
            similarity_score: Original score
            usage_context: How case was used
            user_id: User ID

        Returns:
            Created feedback record
        """
        feedback = SimilarityFeedback(
            id=str(uuid.uuid4()),
            application_reference=application_reference,
            similar_case_reference=similar_case_reference,
            was_useful=was_useful,
            similarity_score=similarity_score,
            usage_context=usage_context,
            user_id=user_id,
        )

        await self._save_feedback("similarity", feedback.model_dump())

        # Update aggregation
        key = similar_case_reference
        if key not in self._similarity_scores:
            self._similarity_scores[key] = []
        self._similarity_scores[key].append(1.0 if was_useful else 0.0)

        logger.info(
            "Recorded similarity feedback",
            application=application_reference,
            similar_case=similar_case_reference,
            was_useful=was_useful,
        )

        return feedback

    async def record_policy_feedback(
        self,
        application_reference: str,
        policy_id: str,
        feedback_type: FeedbackType,
        was_cited_in_final: bool = False,
        relevance_score: float | None = None,
        comments: str | None = None,
        user_id: str | None = None,
    ) -> PolicyFeedback:
        """Record feedback on policy relevance.

        Args:
            application_reference: Application reference
            policy_id: Policy ID
            feedback_type: Type of feedback
            was_cited_in_final: Whether policy was cited in final report
            relevance_score: Relevance score
            comments: User comments
            user_id: User ID

        Returns:
            Created feedback record
        """
        feedback = PolicyFeedback(
            id=str(uuid.uuid4()),
            application_reference=application_reference,
            policy_id=policy_id,
            feedback_type=feedback_type,
            was_cited_in_final=was_cited_in_final,
            relevance_score=relevance_score,
            comments=comments,
            user_id=user_id,
        )

        await self._save_feedback("policy", feedback.model_dump())

        # Update aggregation
        if policy_id not in self._policy_relevance:
            self._policy_relevance[policy_id] = []
        self._policy_relevance[policy_id].append(was_cited_in_final)

        logger.info(
            "Recorded policy feedback",
            application=application_reference,
            policy_id=policy_id,
            feedback_type=feedback_type.value,
        )

        return feedback

    async def record_outcome(
        self,
        application_reference: str,
        actual_outcome: str,
        decision_date: datetime,
        predicted_outcome: str | None = None,
        conditions_count: int | None = None,
        refusal_reasons: list[str] | None = None,
    ) -> OutcomeFeedback:
        """Record actual planning decision outcome.

        Args:
            application_reference: Application reference
            actual_outcome: Actual decision
            decision_date: Date of decision
            predicted_outcome: What system predicted
            conditions_count: Number of conditions if approved
            refusal_reasons: Refusal reasons if refused

        Returns:
            Created feedback record
        """
        feedback = OutcomeFeedback(
            id=str(uuid.uuid4()),
            application_reference=application_reference,
            predicted_outcome=predicted_outcome,
            actual_outcome=actual_outcome,
            decision_date=decision_date,
            conditions_count=conditions_count,
            refusal_reasons=refusal_reasons,
        )

        await self._save_feedback("outcome", feedback.model_dump())

        logger.info(
            "Recorded outcome",
            application=application_reference,
            predicted=predicted_outcome,
            actual=actual_outcome,
        )

        return feedback

    async def record_document_classification_feedback(
        self,
        document_id: str,
        application_reference: str,
        predicted_type: str,
        correct_type: str,
        user_id: str | None = None,
    ) -> DocumentClassificationFeedback:
        """Record feedback on document classification.

        Args:
            document_id: Document ID
            application_reference: Application reference
            predicted_type: Predicted type
            correct_type: Correct type
            user_id: User ID

        Returns:
            Created feedback record
        """
        feedback = DocumentClassificationFeedback(
            id=str(uuid.uuid4()),
            document_id=document_id,
            application_reference=application_reference,
            predicted_type=predicted_type,
            correct_type=correct_type,
            user_id=user_id,
        )

        await self._save_feedback("document_classification", feedback.model_dump())

        logger.info(
            "Recorded document classification feedback",
            document_id=document_id,
            predicted=predicted_type,
            correct=correct_type,
        )

        return feedback

    async def _save_feedback(self, feedback_type: str, data: dict[str, Any]) -> None:
        """Save feedback to file storage."""
        # Create directory for feedback type
        type_dir = self.storage_path / feedback_type
        type_dir.mkdir(exist_ok=True)

        # Save with timestamp-based filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{data.get('id', 'unknown')}.json"
        filepath = type_dir / filename

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def get_similarity_boost(self, case_reference: str) -> float:
        """Get similarity score boost based on feedback.

        Args:
            case_reference: Historic case reference

        Returns:
            Boost factor (0.8 to 1.2)
        """
        scores = self._similarity_scores.get(case_reference, [])
        if not scores:
            return 1.0

        # Calculate average usefulness
        avg_useful = sum(scores) / len(scores)

        # Return boost factor
        return 0.8 + (0.4 * avg_useful)

    async def get_policy_relevance_boost(self, policy_id: str) -> float:
        """Get policy relevance boost based on feedback.

        Args:
            policy_id: Policy ID

        Returns:
            Boost factor (0.8 to 1.2)
        """
        citations = self._policy_relevance.get(policy_id, [])
        if not citations:
            return 1.0

        # Calculate citation rate
        citation_rate = sum(1 for c in citations if c) / len(citations)

        # Return boost factor
        return 0.8 + (0.4 * citation_rate)

    async def get_report_feedback_stats(
        self, application_reference: str | None = None
    ) -> dict[str, Any]:
        """Get statistics on report feedback.

        Args:
            application_reference: Filter by application

        Returns:
            Statistics dictionary
        """
        report_dir = self.storage_path / "report"
        if not report_dir.exists():
            return {"total": 0, "avg_rating": None}

        ratings = []
        edit_count = 0

        for filepath in report_dir.glob("*.json"):
            with open(filepath) as f:
                data = json.load(f)

            if application_reference and data.get("application_reference") != application_reference:
                continue

            if data.get("rating"):
                ratings.append(data["rating"])

            if data.get("edited_content"):
                edit_count += 1

        return {
            "total": len(ratings) + edit_count,
            "avg_rating": sum(ratings) / len(ratings) if ratings else None,
            "edit_count": edit_count,
            "rating_count": len(ratings),
        }

    async def get_outcome_accuracy(self) -> dict[str, Any]:
        """Get accuracy of outcome predictions.

        Returns:
            Accuracy statistics
        """
        outcome_dir = self.storage_path / "outcome"
        if not outcome_dir.exists():
            return {"total": 0, "accuracy": None}

        correct = 0
        total = 0

        for filepath in outcome_dir.glob("*.json"):
            with open(filepath) as f:
                data = json.load(f)

            if data.get("predicted_outcome") and data.get("actual_outcome"):
                total += 1
                predicted = data["predicted_outcome"].lower()
                actual = data["actual_outcome"].lower()

                # Normalize outcomes
                if "approv" in predicted and "approv" in actual:
                    correct += 1
                elif "refus" in predicted and "refus" in actual:
                    correct += 1

        return {
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else None,
        }
