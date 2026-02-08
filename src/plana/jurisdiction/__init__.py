"""
LPA Jurisdiction Enforcement Module.

Provides strict Local Planning Authority boundary enforcement
for planning policy analysis. All policy retrieval and comparable
application searches are filtered by the identified LPA.

Key principles:
- LPA boundaries are treated as hard data partitions
- No cross-authority semantic retrieval is permitted
- NPPF may be used nationally, but all local policy must be authority-specific
- If multiple LPAs are detected, halt and request clarification

Usage:
    from plana.jurisdiction import LPAStrictAnalyzer

    analyzer = LPAStrictAnalyzer()
    result = await analyzer.analyze(application)

    # Or from address directly:
    result = await analyzer.analyze_from_address(
        address="12 Fern Avenue, Jesmond, Newcastle upon Tyne, NE2 2QU",
        proposal="Single storey rear extension",
        constraints=["Conservation Area"]
    )
"""

from plana.jurisdiction.analysis import LPAAnalysisResult, LPAStrictAnalyzer
from plana.jurisdiction.cases_filter import (
    StrictCaseMatch,
    StrictCaseSearch,
    StrictCaseSearchResult,
)
from plana.jurisdiction.policy_filter import (
    StrictPolicyMatch,
    StrictPolicyRetrievalResult,
    StrictPolicyRetriever,
)
from plana.jurisdiction.service import (
    JurisdictionError,
    JurisdictionService,
    LocalPlanInfo,
    LPAIdentificationResult,
    MultipleJurisdictionsError,
    UnknownJurisdictionError,
)

__all__ = [
    # Core service
    "JurisdictionService",
    "JurisdictionError",
    "MultipleJurisdictionsError",
    "UnknownJurisdictionError",
    "LPAIdentificationResult",
    "LocalPlanInfo",
    # Policy filtering
    "StrictPolicyRetriever",
    "StrictPolicyMatch",
    "StrictPolicyRetrievalResult",
    # Case filtering
    "StrictCaseSearch",
    "StrictCaseMatch",
    "StrictCaseSearchResult",
    # Main analyzer
    "LPAStrictAnalyzer",
    "LPAAnalysisResult",
]
