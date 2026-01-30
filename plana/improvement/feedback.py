"""
Feedback processing for continuous improvement.

Handles user feedback storage and mismatch tracking for deterministic
improvement of the assessment pipeline.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from plana.decision_calibration import parse_application_type
from plana.storage import get_database, StoredFeedback, StoredRunLog


@dataclass
class FeedbackStats:
    """Statistics about feedback for a reference or application type."""
    total_feedback: int = 0
    match_count: int = 0
    mismatch_count: int = 0
    match_rate: float = 0.0
    by_decision: Dict[str, int] = None

    def __post_init__(self):
        if self.by_decision is None:
            self.by_decision = {}


def process_feedback(
    reference: str,
    actual_decision: str,
    notes: Optional[str] = None,
    conditions: Optional[List[str]] = None,
    reasons: Optional[List[str]] = None,
) -> Tuple[int, bool]:
    """Process user feedback and track mismatches.

    Args:
        reference: Application reference
        actual_decision: Actual case officer decision
        notes: Optional notes
        conditions: Optional conditions (for approval with conditions)
        reasons: Optional refusal reasons

    Returns:
        Tuple of (feedback_id, is_mismatch)
    """
    db = get_database()

    # Check if we have a previous run for this reference
    run_logs = db.get_run_logs_for_reference(reference, limit=1)
    plana_decision = None
    is_mismatch = False

    if run_logs:
        latest_run = run_logs[0]
        plana_decision = latest_run.calibrated_decision or latest_run.raw_decision

        # Determine if this is a mismatch
        is_mismatch = _is_decision_mismatch(plana_decision, actual_decision)

    # Get existing application
    app = db.get_application(reference)

    # Save feedback
    feedback = StoredFeedback(
        application_id=app.id if app else None,
        reference=reference,
        decision=actual_decision,
        notes=notes,
        conditions_json=json.dumps(conditions) if conditions else None,
        refusal_reasons_json=json.dumps(reasons) if reasons else None,
        actual_decision=actual_decision,
        actual_decision_date=datetime.now().strftime("%Y-%m-%d"),
    )

    feedback_id = db.save_feedback(feedback)

    # If we have a mismatch and run log, update policy weights
    if is_mismatch and run_logs:
        from plana.improvement.reranking import update_weights_from_feedback
        update_weights_from_feedback(
            reference=reference,
            plana_decision=plana_decision,
            actual_decision=actual_decision,
            policy_ids=json.loads(run_logs[0].policy_ids_used or "[]"),
        )

    return feedback_id, is_mismatch


def _is_decision_mismatch(plana_decision: Optional[str], actual_decision: str) -> bool:
    """Check if Plana's decision mismatches the actual decision.

    Partial matches (APPROVE vs APPROVE_WITH_CONDITIONS) are NOT mismatches.

    Args:
        plana_decision: Plana's predicted decision
        actual_decision: Actual case officer decision

    Returns:
        True if this is a mismatch (not partial)
    """
    if not plana_decision:
        return True

    # Normalize decisions
    plana_norm = plana_decision.upper().replace(" ", "_")
    actual_norm = actual_decision.upper().replace(" ", "_")

    # Exact match
    if plana_norm == actual_norm:
        return False

    # Partial match (APPROVE <-> APPROVE_WITH_CONDITIONS)
    approve_variants = {"APPROVE", "APPROVE_WITH_CONDITIONS"}
    if plana_norm in approve_variants and actual_norm in approve_variants:
        return False

    # Any other case is a mismatch
    return True


def get_feedback_stats(reference: Optional[str] = None) -> FeedbackStats:
    """Get feedback statistics.

    Args:
        reference: Optional reference to filter by

    Returns:
        FeedbackStats object
    """
    db = get_database()

    if reference:
        feedback_list = db.get_feedback(reference)
    else:
        feedback_list = db.get_all_feedback(limit=1000)

    stats = FeedbackStats(total_feedback=len(feedback_list))

    # Count by decision
    for fb in feedback_list:
        decision = fb.decision or fb.actual_decision
        if decision:
            stats.by_decision[decision] = stats.by_decision.get(decision, 0) + 1

    # Compare against run logs to calculate match rate
    for fb in feedback_list:
        run_logs = db.get_run_logs_for_reference(fb.reference, limit=1)
        if run_logs:
            plana_decision = run_logs[0].calibrated_decision or run_logs[0].raw_decision
            actual_decision = fb.actual_decision or fb.decision
            if _is_decision_mismatch(plana_decision, actual_decision):
                stats.mismatch_count += 1
            else:
                stats.match_count += 1

    if stats.total_feedback > 0:
        stats.match_rate = stats.match_count / stats.total_feedback

    return stats


def get_mismatch_rate(application_type: str) -> float:
    """Get the mismatch rate for a specific application type.

    Args:
        application_type: Application type code (e.g., HOU, LBC)

    Returns:
        Mismatch rate (0.0 to 1.0)
    """
    db = get_database()

    # Get run logs for this type
    run_logs = db.get_run_logs_by_type(application_type, success_only=True, limit=100)

    if not run_logs:
        return 0.0

    mismatch_count = 0
    total_with_feedback = 0

    for run in run_logs:
        feedback_list = db.get_feedback(run.reference)
        if feedback_list:
            total_with_feedback += 1
            actual_decision = feedback_list[0].actual_decision or feedback_list[0].decision
            plana_decision = run.calibrated_decision or run.raw_decision
            if _is_decision_mismatch(plana_decision, actual_decision):
                mismatch_count += 1

    if total_with_feedback == 0:
        return 0.0

    return mismatch_count / total_with_feedback


def get_feedback_summary() -> Dict[str, any]:
    """Get a summary of feedback data.

    Returns:
        Dictionary with feedback summary
    """
    db = get_database()
    stats = get_feedback_stats()

    # Get mismatch rates by type
    type_rates = {}
    for app_type in ["HOU", "LBC", "DET", "LDC", "DCC", "TPO", "TCA"]:
        rate = get_mismatch_rate(app_type)
        if rate > 0:
            type_rates[app_type] = round(rate * 100, 1)

    return {
        "total_feedback": stats.total_feedback,
        "match_count": stats.match_count,
        "mismatch_count": stats.mismatch_count,
        "match_rate_percent": round(stats.match_rate * 100, 1),
        "by_decision": stats.by_decision,
        "mismatch_rates_by_type": type_rates,
    }
