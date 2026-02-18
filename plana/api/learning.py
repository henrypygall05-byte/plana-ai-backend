"""
Continuous Learning and Improvement System.

Tracks:
- Predicted vs actual outcomes
- Case officer corrections
- Policy citation effectiveness
- Similar case relevance feedback

Uses this data to:
- Improve recommendation accuracy
- Refine policy weighting
- Improve similar case ranking
- Generate accuracy reports
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json
import os
from pathlib import Path


@dataclass
class PredictionRecord:
    """Record of a prediction made by the system."""
    run_id: str
    reference: str
    council_id: str
    timestamp: str
    predicted_outcome: str  # APPROVE, APPROVE_WITH_CONDITIONS, REFUSE
    predicted_confidence: float
    key_policies_cited: list[str]
    similar_cases_used: list[str]
    actual_outcome: str | None = None
    actual_date: str | None = None
    was_correct: bool | None = None
    officer_corrections: list[dict] = field(default_factory=list)


@dataclass
class FeedbackRecord:
    """Feedback from case officer on a report."""
    run_id: str
    reference: str
    timestamp: str
    feedback_type: str  # correction, enhancement, error
    section: str | None
    original_text: str | None
    corrected_text: str | None
    reason: str | None
    policy_feedback: list[dict] = field(default_factory=list)
    case_feedback: list[dict] = field(default_factory=list)


@dataclass
class AccuracyMetrics:
    """System accuracy metrics."""
    total_predictions: int
    outcomes_recorded: int
    correct_predictions: int
    accuracy_rate: float
    approval_accuracy: float
    refusal_accuracy: float
    average_confidence: float
    most_effective_policies: list[str]
    most_relevant_cases: list[str]


class LearningSystem:
    """
    Manages continuous learning and improvement.

    Stores prediction records and feedback in JSON files for simplicity.
    In production, this would use a proper database.
    """

    def __init__(self, data_dir: str = "./data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.predictions_file = self.data_dir / "predictions.json"
        self.feedback_file = self.data_dir / "feedback.json"
        self.metrics_file = self.data_dir / "metrics.json"

    def record_prediction(
        self,
        run_id: str,
        reference: str,
        council_id: str,
        predicted_outcome: str,
        predicted_confidence: float,
        key_policies: list[str],
        similar_cases: list[str],
    ) -> PredictionRecord:
        """Record a new prediction."""
        record = PredictionRecord(
            run_id=run_id,
            reference=reference,
            council_id=council_id,
            timestamp=datetime.now().isoformat(),
            predicted_outcome=predicted_outcome,
            predicted_confidence=predicted_confidence,
            key_policies_cited=key_policies,
            similar_cases_used=similar_cases,
        )

        # Load existing predictions
        predictions = self._load_predictions()
        predictions.append(self._record_to_dict(record))

        # Save updated predictions
        self._save_predictions(predictions)

        return record

    def record_actual_outcome(
        self,
        reference: str,
        actual_outcome: str,
        actual_date: str,
    ) -> bool:
        """Record the actual outcome for a prediction."""
        predictions = self._load_predictions()

        updated = False
        for pred in predictions:
            if pred["reference"] == reference and pred["actual_outcome"] is None:
                pred["actual_outcome"] = actual_outcome
                pred["actual_date"] = actual_date

                # Check if prediction was correct
                predicted = pred["predicted_outcome"]
                if "APPROVE" in predicted and "APPROVE" in actual_outcome:
                    pred["was_correct"] = True
                elif predicted == "REFUSE" and actual_outcome == "REFUSE":
                    pred["was_correct"] = True
                else:
                    pred["was_correct"] = False

                updated = True
                break

        if updated:
            self._save_predictions(predictions)

        return updated

    def record_feedback(
        self,
        run_id: str,
        reference: str,
        feedback_type: str,
        section: str | None = None,
        original_text: str | None = None,
        corrected_text: str | None = None,
        reason: str | None = None,
        policy_feedback: list[dict] | None = None,
        case_feedback: list[dict] | None = None,
    ) -> FeedbackRecord:
        """Record case officer feedback on a report."""
        record = FeedbackRecord(
            run_id=run_id,
            reference=reference,
            timestamp=datetime.now().isoformat(),
            feedback_type=feedback_type,
            section=section,
            original_text=original_text,
            corrected_text=corrected_text,
            reason=reason,
            policy_feedback=policy_feedback or [],
            case_feedback=case_feedback or [],
        )

        # Load existing feedback
        feedback = self._load_feedback()
        feedback.append(self._feedback_to_dict(record))

        # Save updated feedback
        self._save_feedback(feedback)

        return record

    def get_accuracy_metrics(self) -> AccuracyMetrics:
        """Calculate current accuracy metrics."""
        predictions = self._load_predictions()

        total = len(predictions)
        with_outcomes = [p for p in predictions if p.get("actual_outcome") is not None]
        correct = [p for p in with_outcomes if p.get("was_correct") == True]

        # Calculate approval accuracy
        approval_predictions = [p for p in with_outcomes if "APPROVE" in p.get("predicted_outcome", "")]
        approval_correct = [p for p in approval_predictions if p.get("was_correct") == True]

        # Calculate refusal accuracy
        refusal_predictions = [p for p in with_outcomes if p.get("predicted_outcome") == "REFUSE"]
        refusal_correct = [p for p in refusal_predictions if p.get("was_correct") == True]

        # Calculate average confidence
        confidences = [p.get("predicted_confidence", 0.7) for p in predictions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.7

        # Find most effective policies (cited in correct predictions)
        policy_effectiveness = {}
        for pred in correct:
            for policy in pred.get("key_policies_cited", []):
                policy_effectiveness[policy] = policy_effectiveness.get(policy, 0) + 1

        most_effective = sorted(policy_effectiveness.items(), key=lambda x: x[1], reverse=True)[:5]

        # Find most relevant cases
        case_relevance = {}
        for pred in correct:
            for case in pred.get("similar_cases_used", []):
                case_relevance[case] = case_relevance.get(case, 0) + 1

        most_relevant = sorted(case_relevance.items(), key=lambda x: x[1], reverse=True)[:5]

        return AccuracyMetrics(
            total_predictions=total,
            outcomes_recorded=len(with_outcomes),
            correct_predictions=len(correct),
            accuracy_rate=len(correct) / len(with_outcomes) if with_outcomes else 0,
            approval_accuracy=len(approval_correct) / len(approval_predictions) if approval_predictions else 0,
            refusal_accuracy=len(refusal_correct) / len(refusal_predictions) if refusal_predictions else 0,
            average_confidence=avg_confidence,
            most_effective_policies=[p for p, _ in most_effective],
            most_relevant_cases=[c for c, _ in most_relevant],
        )

    def get_policy_weight_adjustments(self) -> dict[str, float]:
        """
        Calculate suggested policy weight adjustments based on feedback.

        Returns a dict of policy_id -> adjustment factor (>1 = increase weight, <1 = decrease)
        """
        feedback = self._load_feedback()
        predictions = self._load_predictions()

        adjustments = {}

        # Analyse policy feedback
        for fb in feedback:
            for policy_fb in fb.get("policy_feedback", []):
                policy_id = policy_fb.get("policy_id")
                signal = policy_fb.get("signal", "maintain")

                if policy_id:
                    current = adjustments.get(policy_id, 1.0)
                    if signal == "more-relevant":
                        adjustments[policy_id] = current * 1.1
                    elif signal == "less-relevant":
                        adjustments[policy_id] = current * 0.9
                    else:
                        adjustments[policy_id] = current

        # Adjust based on prediction accuracy
        for pred in predictions:
            if pred.get("was_correct") == True:
                for policy in pred.get("key_policies_cited", []):
                    current = adjustments.get(policy, 1.0)
                    adjustments[policy] = current * 1.02  # Small boost for correct predictions
            elif pred.get("was_correct") == False:
                for policy in pred.get("key_policies_cited", []):
                    current = adjustments.get(policy, 1.0)
                    adjustments[policy] = current * 0.98  # Small reduction for incorrect

        return adjustments

    def get_similar_case_ranking_adjustments(self) -> dict[str, float]:
        """
        Calculate suggested ranking adjustments for similar cases.

        Returns a dict of case_reference -> adjustment factor
        """
        feedback = self._load_feedback()
        predictions = self._load_predictions()

        adjustments = {}

        # Analyse case feedback
        for fb in feedback:
            for case_fb in fb.get("case_feedback", []):
                case_id = case_fb.get("case_id")
                signal = case_fb.get("signal", "maintain")

                if case_id:
                    current = adjustments.get(case_id, 1.0)
                    if signal == "rank-higher":
                        adjustments[case_id] = current * 1.15
                    elif signal == "rank-lower":
                        adjustments[case_id] = current * 0.85
                    else:
                        adjustments[case_id] = current

        # Adjust based on prediction accuracy
        for pred in predictions:
            if pred.get("was_correct") == True:
                for case in pred.get("similar_cases_used", []):
                    current = adjustments.get(case, 1.0)
                    adjustments[case] = current * 1.05
            elif pred.get("was_correct") == False:
                for case in pred.get("similar_cases_used", []):
                    current = adjustments.get(case, 1.0)
                    adjustments[case] = current * 0.95

        return adjustments

    def generate_weekly_report(self) -> dict[str, Any]:
        """Generate a weekly accuracy and improvement report."""
        metrics = self.get_accuracy_metrics()
        policy_adjustments = self.get_policy_weight_adjustments()
        case_adjustments = self.get_similar_case_ranking_adjustments()

        return {
            "report_date": datetime.now().isoformat(),
            "period": "weekly",
            "accuracy_metrics": {
                "total_predictions": metrics.total_predictions,
                "outcomes_recorded": metrics.outcomes_recorded,
                "correct_predictions": metrics.correct_predictions,
                "accuracy_rate": f"{metrics.accuracy_rate:.1%}",
                "approval_accuracy": f"{metrics.approval_accuracy:.1%}",
                "refusal_accuracy": f"{metrics.refusal_accuracy:.1%}",
                "average_confidence": f"{metrics.average_confidence:.1%}",
            },
            "top_performing_policies": metrics.most_effective_policies,
            "most_relevant_precedents": metrics.most_relevant_cases,
            "suggested_improvements": {
                "policies_to_weight_higher": [
                    p for p, adj in policy_adjustments.items() if adj > 1.05
                ],
                "policies_to_weight_lower": [
                    p for p, adj in policy_adjustments.items() if adj < 0.95
                ],
                "cases_to_rank_higher": [
                    c for c, adj in case_adjustments.items() if adj > 1.05
                ],
            },
        }

    def _load_predictions(self) -> list[dict]:
        """Load predictions from file."""
        if self.predictions_file.exists():
            with open(self.predictions_file, "r") as f:
                return json.load(f)
        return []

    def _save_predictions(self, predictions: list[dict]) -> None:
        """Save predictions to file."""
        with open(self.predictions_file, "w") as f:
            json.dump(predictions, f, indent=2)

    def _load_feedback(self) -> list[dict]:
        """Load feedback from file."""
        if self.feedback_file.exists():
            with open(self.feedback_file, "r") as f:
                return json.load(f)
        return []

    def _save_feedback(self, feedback: list[dict]) -> None:
        """Save feedback to file."""
        with open(self.feedback_file, "w") as f:
            json.dump(feedback, f, indent=2)

    def _record_to_dict(self, record: PredictionRecord) -> dict:
        """Convert PredictionRecord to dict."""
        return {
            "run_id": record.run_id,
            "reference": record.reference,
            "council_id": record.council_id,
            "timestamp": record.timestamp,
            "predicted_outcome": record.predicted_outcome,
            "predicted_confidence": record.predicted_confidence,
            "key_policies_cited": record.key_policies_cited,
            "similar_cases_used": record.similar_cases_used,
            "actual_outcome": record.actual_outcome,
            "actual_date": record.actual_date,
            "was_correct": record.was_correct,
            "officer_corrections": record.officer_corrections,
        }

    def _feedback_to_dict(self, record: FeedbackRecord) -> dict:
        """Convert FeedbackRecord to dict."""
        return {
            "run_id": record.run_id,
            "reference": record.reference,
            "timestamp": record.timestamp,
            "feedback_type": record.feedback_type,
            "section": record.section,
            "original_text": record.original_text,
            "corrected_text": record.corrected_text,
            "reason": record.reason,
            "policy_feedback": record.policy_feedback,
            "case_feedback": record.case_feedback,
        }


# Global learning system instance
_learning_system: LearningSystem | None = None


def get_learning_system() -> LearningSystem:
    """Get the global learning system instance."""
    global _learning_system
    if _learning_system is None:
        _learning_system = LearningSystem()
    return _learning_system
