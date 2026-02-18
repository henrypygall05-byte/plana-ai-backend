"""
Deterministic policy re-ranking for continuous improvement.

Uses feedback data to adjust policy weights and confidence levels
without any ML training - purely deterministic heuristics.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from plana.decision_calibration import parse_application_type
from plana.storage import get_database, StoredPolicyWeight


# Default confidence by application type — calibrated from professional
# standards: LBC cases are inherently complex (statutory duty S66/S72),
# while DCC cases are near-automatic.
DEFAULT_CONFIDENCE = {
    "HOU": 0.78,  # Householder - generally predictable but balcony/amenity cases vary
    "LBC": 0.60,  # Listed Building - highest complexity, S66 duty, specialist expertise needed
    "DET": 0.72,  # Full Planning (Newcastle code) - moderate complexity
    "FUL": 0.72,  # Full Planning (standard code) - moderate complexity
    "LDC": 0.88,  # Lawful Development - clear legal test (is it PD or not)
    "DCC": 0.92,  # Discharge of Conditions - near-automatic if conditions met
    "TPO": 0.55,  # Tree Preservation - highly variable, arborist-dependent
    "TCA": 0.55,  # Trees in Conservation - highly variable
    "OUT": 0.65,  # Outline - principle only, but contentious site allocations
    "REM": 0.80,  # Reserved Matters - principle already established
    "ADV": 0.82,  # Advertisement Consent - straightforward criteria
    "COU": 0.68,  # Change of Use - depends heavily on local context
}

DEFAULT_CONFIDENCE_FALLBACK = 0.70


def get_policy_boost(
    policy_id: str,
    application_type: str,
) -> float:
    """Get the boost factor for a policy based on historical performance.

    Args:
        policy_id: Policy identifier
        application_type: Application type code

    Returns:
        Boost factor (1.0 = no boost, >1.0 = boosted, <1.0 = demoted)
    """
    db = get_database()
    weight = db.get_policy_weight(policy_id, application_type)

    if weight is None:
        return 1.0

    return weight.weight


def get_confidence_adjustment(
    reference: str,
    base_confidence: float = 0.75,
) -> float:
    """Get confidence adjustment based on historical data.

    Adjusts confidence down when there have been mismatches for similar
    application types.

    Args:
        reference: Application reference
        base_confidence: Base confidence level

    Returns:
        Adjusted confidence (0.0 to 1.0)
    """
    app_type = parse_application_type(reference)

    # Start with type-specific default
    confidence = DEFAULT_CONFIDENCE.get(app_type, DEFAULT_CONFIDENCE_FALLBACK)

    # Get mismatch rate for this type
    from plana.improvement.feedback import get_mismatch_rate
    mismatch_rate = get_mismatch_rate(app_type)

    # Reduce confidence based on mismatch rate
    # Every 10% mismatch rate reduces confidence by 5%
    confidence_reduction = mismatch_rate * 0.5
    adjusted = confidence - confidence_reduction

    # Clamp to reasonable range
    return max(0.4, min(0.95, adjusted))


def rerank_policies(
    policies: List[Any],
    reference: str,
) -> List[Any]:
    """Re-rank policies based on historical performance.

    Boosts policies that have appeared in correct predictions for this
    application type. Uses deterministic heuristics, no ML.

    Args:
        policies: List of policy objects (must have 'id' or 'policy_id' attribute)
        reference: Application reference

    Returns:
        Re-ranked list of policies
    """
    app_type = parse_application_type(reference)

    # Get boosts for each policy
    ranked = []
    for policy in policies:
        policy_id = getattr(policy, 'id', None) or getattr(policy, 'policy_id', None)
        if policy_id is None:
            # Try dict access
            if isinstance(policy, dict):
                policy_id = policy.get('id') or policy.get('policy_id')

        if policy_id:
            boost = get_policy_boost(str(policy_id), app_type)
        else:
            boost = 1.0

        ranked.append((policy, boost))

    # Sort by boost (descending), maintaining original order for equal boosts
    ranked.sort(key=lambda x: -x[1])

    return [p for p, _ in ranked]


def update_weights_from_feedback(
    reference: str,
    plana_decision: str,
    actual_decision: str,
    policy_ids: List[str],
) -> None:
    """Update policy weights based on feedback.

    If Plana matched the actual decision, boost the policies used.
    If Plana missed, reduce the weight of policies used.

    Args:
        reference: Application reference
        plana_decision: Plana's decision
        actual_decision: Actual case officer decision
        policy_ids: List of policy IDs used in the decision
    """
    app_type = parse_application_type(reference)
    db = get_database()

    # Determine if this was a match
    is_match = _is_match(plana_decision, actual_decision)

    # Update each policy's weight
    for policy_id in policy_ids:
        db.increment_policy_match(policy_id, app_type, is_match)


def _is_match(plana_decision: str, actual_decision: str) -> bool:
    """Check if decisions match (including partial matches).

    Args:
        plana_decision: Plana's decision
        actual_decision: Actual decision

    Returns:
        True if match or partial match
    """
    plana_norm = plana_decision.upper().replace(" ", "_")
    actual_norm = actual_decision.upper().replace(" ", "_")

    # Exact match
    if plana_norm == actual_norm:
        return True

    # Partial match (APPROVE <-> APPROVE_WITH_CONDITIONS)
    approve_variants = {"APPROVE", "APPROVE_WITH_CONDITIONS"}
    if plana_norm in approve_variants and actual_norm in approve_variants:
        return True

    return False


def get_policy_weight_summary(application_type: str) -> Dict[str, Any]:
    """Get summary of policy weights for an application type.

    Args:
        application_type: Application type code

    Returns:
        Dictionary with weight statistics
    """
    db = get_database()
    weights = db.get_policy_weights_for_type(application_type)

    if not weights:
        return {
            "application_type": application_type,
            "total_policies": 0,
            "boosted_policies": 0,
            "demoted_policies": 0,
            "top_policies": [],
        }

    boosted = [w for w in weights if w.weight > 1.0]
    demoted = [w for w in weights if w.weight < 1.0]

    return {
        "application_type": application_type,
        "total_policies": len(weights),
        "boosted_policies": len(boosted),
        "demoted_policies": len(demoted),
        "top_policies": [
            {
                "policy_id": w.policy_id,
                "weight": round(w.weight, 2),
                "matches": w.match_count,
                "mismatches": w.mismatch_count,
            }
            for w in weights[:10]
        ],
    }


def calculate_similar_case_boost(
    similar_cases: List[Any],
    reference: str,
) -> List[Tuple[Any, float]]:
    """Calculate boost factors for similar cases.

    Cases with correct feedback get boosted (gradated by feedback count),
    those with mismatches get demoted.  Uses a graduated scale instead
    of binary 1.2/0.8 to better reflect confidence in the boost.

    Args:
        similar_cases: List of similar case objects
        reference: Current application reference

    Returns:
        List of (case, boost_factor) tuples
    """
    db = get_database()
    app_type = parse_application_type(reference)

    boosted_cases = []
    for case in similar_cases:
        # Get case reference
        case_ref = getattr(case, 'reference', None)
        if case_ref is None and isinstance(case, dict):
            case_ref = case.get('reference')

        if not case_ref:
            boosted_cases.append((case, 1.0))
            continue

        # Check if we have feedback for this case
        feedback_list = db.get_feedback(case_ref)
        if not feedback_list:
            boosted_cases.append((case, 1.0))
            continue

        # Check if the case's run matched the feedback
        run_logs = db.get_run_logs_for_reference(case_ref, limit=1)
        if not run_logs:
            boosted_cases.append((case, 1.0))
            continue

        plana_decision = run_logs[0].calibrated_decision or run_logs[0].raw_decision
        actual_decision = feedback_list[0].actual_decision or feedback_list[0].decision

        # Graduated boost based on feedback count (more feedback = more confidence)
        feedback_count = len(feedback_list)

        if _is_match(plana_decision, actual_decision):
            # Graduated boost: 1.1 for 1 feedback, up to 1.3 for 5+
            boost = min(1.3, 1.05 + (feedback_count * 0.05))
            boosted_cases.append((case, boost))
        else:
            # Graduated demotion: 0.9 for 1 mismatch, down to 0.7 for 5+
            demotion = max(0.7, 0.95 - (feedback_count * 0.05))
            boosted_cases.append((case, demotion))

    # Sort by boost factor (highest first)
    boosted_cases.sort(key=lambda x: -x[1])

    return boosted_cases
