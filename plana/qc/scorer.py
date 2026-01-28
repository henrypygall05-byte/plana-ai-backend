"""
QC scoring logic for Plana.AI.

Implements scoring rules for comparing Plana decisions against actual case officer decisions.
"""

import csv
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Decision(Enum):
    """Valid decision types."""

    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    REFUSE = "REFUSE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, value: str) -> "Decision":
        """Parse decision from string (case-insensitive, with normalization)."""
        if not value:
            return cls.UNKNOWN

        normalized = value.strip().upper().replace(" ", "_").replace("-", "_")

        # Handle common variations
        if normalized in ("APPROVE", "APPROVED", "GRANT", "GRANTED"):
            return cls.APPROVE
        elif normalized in (
            "APPROVE_WITH_CONDITIONS",
            "APPROVED_WITH_CONDITIONS",
            "GRANT_WITH_CONDITIONS",
            "CONDITIONAL",
            "CONDITIONAL_APPROVAL",
        ):
            return cls.APPROVE_WITH_CONDITIONS
        elif normalized in ("REFUSE", "REFUSED", "REJECT", "REJECTED"):
            return cls.REFUSE

        return cls.UNKNOWN


class MatchType(Enum):
    """Type of match between Plana and actual decision."""

    EXACT = "exact"
    PARTIAL = "partial"
    MISS = "miss"


@dataclass
class CaseScore:
    """Score for a single case."""

    reference: str
    plana_decision: Decision
    actual_decision: Decision
    match_type: MatchType
    score: float
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "reference": self.reference,
            "plana_decision": self.plana_decision.value,
            "actual_decision": self.actual_decision.value,
            "match_type": self.match_type.value,
            "score": self.score,
            "notes": self.notes,
        }


@dataclass
class QCMetrics:
    """Aggregate QC metrics."""

    total_cases: int
    exact_matches: int
    partial_matches: int
    misses: int
    total_score: float
    qc_percentage: float
    case_scores: List[CaseScore] = field(default_factory=list)
    confusion_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_cases": self.total_cases,
            "exact_matches": self.exact_matches,
            "partial_matches": self.partial_matches,
            "misses": self.misses,
            "total_score": self.total_score,
            "qc_percentage": self.qc_percentage,
            "case_scores": [cs.to_dict() for cs in self.case_scores],
            "confusion_matrix": self.confusion_matrix,
        }


def score_case(
    reference: str,
    plana_decision: Decision,
    actual_decision: Decision,
) -> CaseScore:
    """
    Score a single case comparison.

    Scoring Rules:
    - Exact Match (1.0): Plana decision == actual decision
    - Partial Match (0.5): APPROVE <-> APPROVE_WITH_CONDITIONS
    - Miss (0.0): APPROVE vs REFUSE, REFUSE vs APPROVE, UNKNOWN

    Args:
        reference: Application reference number
        plana_decision: Plana's decision
        actual_decision: Actual case officer decision

    Returns:
        CaseScore with match type and score
    """
    # Handle unknown decisions
    if plana_decision == Decision.UNKNOWN or actual_decision == Decision.UNKNOWN:
        return CaseScore(
            reference=reference,
            plana_decision=plana_decision,
            actual_decision=actual_decision,
            match_type=MatchType.MISS,
            score=0.0,
            notes="Unknown or missing decision",
        )

    # Exact match
    if plana_decision == actual_decision:
        return CaseScore(
            reference=reference,
            plana_decision=plana_decision,
            actual_decision=actual_decision,
            match_type=MatchType.EXACT,
            score=1.0,
            notes="Exact match",
        )

    # Partial match: APPROVE <-> APPROVE_WITH_CONDITIONS
    approval_types = {Decision.APPROVE, Decision.APPROVE_WITH_CONDITIONS}
    if plana_decision in approval_types and actual_decision in approval_types:
        return CaseScore(
            reference=reference,
            plana_decision=plana_decision,
            actual_decision=actual_decision,
            match_type=MatchType.PARTIAL,
            score=0.5,
            notes="Partial match (approval types differ)",
        )

    # Miss: APPROVE/APPROVE_WITH_CONDITIONS vs REFUSE
    if plana_decision in approval_types and actual_decision == Decision.REFUSE:
        return CaseScore(
            reference=reference,
            plana_decision=plana_decision,
            actual_decision=actual_decision,
            match_type=MatchType.MISS,
            score=0.0,
            notes="Plana approved but officer refused",
        )

    if plana_decision == Decision.REFUSE and actual_decision in approval_types:
        return CaseScore(
            reference=reference,
            plana_decision=plana_decision,
            actual_decision=actual_decision,
            match_type=MatchType.MISS,
            score=0.0,
            notes="Plana refused but officer approved",
        )

    # Default miss
    return CaseScore(
        reference=reference,
        plana_decision=plana_decision,
        actual_decision=actual_decision,
        match_type=MatchType.MISS,
        score=0.0,
        notes="Decision mismatch",
    )


def compute_metrics(case_scores: List[CaseScore]) -> QCMetrics:
    """
    Compute aggregate QC metrics from individual case scores.

    Args:
        case_scores: List of CaseScore objects

    Returns:
        QCMetrics with aggregate statistics
    """
    total_cases = len(case_scores)
    if total_cases == 0:
        return QCMetrics(
            total_cases=0,
            exact_matches=0,
            partial_matches=0,
            misses=0,
            total_score=0.0,
            qc_percentage=0.0,
            case_scores=[],
            confusion_matrix={},
        )

    exact_matches = sum(1 for cs in case_scores if cs.match_type == MatchType.EXACT)
    partial_matches = sum(1 for cs in case_scores if cs.match_type == MatchType.PARTIAL)
    misses = sum(1 for cs in case_scores if cs.match_type == MatchType.MISS)
    total_score = sum(cs.score for cs in case_scores)
    qc_percentage = (total_score / total_cases) * 100

    # Build confusion matrix
    # Rows = actual decision, Cols = Plana decision
    decisions = [Decision.APPROVE, Decision.APPROVE_WITH_CONDITIONS, Decision.REFUSE, Decision.UNKNOWN]
    confusion_matrix = {
        actual.value: {plana.value: 0 for plana in decisions}
        for actual in decisions
    }

    for cs in case_scores:
        actual_key = cs.actual_decision.value
        plana_key = cs.plana_decision.value
        confusion_matrix[actual_key][plana_key] += 1

    return QCMetrics(
        total_cases=total_cases,
        exact_matches=exact_matches,
        partial_matches=partial_matches,
        misses=misses,
        total_score=total_score,
        qc_percentage=qc_percentage,
        case_scores=case_scores,
        confusion_matrix=confusion_matrix,
    )


def load_gold_file(path: Path) -> Dict[str, Decision]:
    """
    Load gold standard decisions from CSV file.

    Expected format:
    reference,actual_decision

    Args:
        path: Path to gold CSV file

    Returns:
        Dictionary mapping reference to Decision
    """
    gold = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reference = row.get("reference", "").strip()
            decision_str = row.get("actual_decision", "").strip()
            if reference:
                gold[reference] = Decision.from_string(decision_str)
    return gold


def load_results_file(path: Path) -> Dict[str, Decision]:
    """
    Load Plana evaluation results from CSV file.

    Expected format (from plana evaluate):
    reference,decision,status,...

    Args:
        path: Path to results CSV file

    Returns:
        Dictionary mapping reference to Decision
    """
    results = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reference = row.get("reference", "").strip()
            decision_str = row.get("decision", "").strip()
            if reference:
                results[reference] = Decision.from_string(decision_str)
    return results


def run_qc(
    gold_path: Path,
    results_path: Path,
) -> QCMetrics:
    """
    Run QC comparison between gold standard and Plana results.

    Args:
        gold_path: Path to gold standard CSV
        results_path: Path to Plana results CSV

    Returns:
        QCMetrics with all scores and statistics
    """
    gold = load_gold_file(gold_path)
    results = load_results_file(results_path)

    # Score each case in gold file
    case_scores = []
    for reference, actual_decision in gold.items():
        plana_decision = results.get(reference, Decision.UNKNOWN)
        case_score = score_case(reference, plana_decision, actual_decision)
        case_scores.append(case_score)

    return compute_metrics(case_scores)
