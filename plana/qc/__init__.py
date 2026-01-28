"""
Quality Control module for Plana.AI.

Measures how often Plana's decisions match real case officer outcomes.
"""

# Default benchmark evaluation set (Newcastle applications)
# Define this first to avoid circular imports
DEFAULT_BENCHMARK_REFS = [
    "2025/2090/01/LDC",
    "2025/1974/01/HOU",
    "2025/1985/01/TCA",
    "2025/1739/01/TPO",
    "2025/1710/01/DET",
    "2025/1617/01/LBC",
    "2025/0890/01/TPO",
    "2025/0486/04/DCC",
    "2023/0899/03/DCC",
    "2021/1622/02/DCC",
]

from plana.qc.scorer import (
    Decision,
    MatchType,
    CaseScore,
    QCMetrics,
    score_case,
    compute_metrics,
)
from plana.qc.report import generate_qc_report
from plana.qc.benchmark import run_benchmark

__all__ = [
    "Decision",
    "MatchType",
    "CaseScore",
    "QCMetrics",
    "score_case",
    "compute_metrics",
    "generate_qc_report",
    "run_benchmark",
    "DEFAULT_BENCHMARK_REFS",
]
