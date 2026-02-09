"""
Shared Evidence Constants and Core Types for Planning Assessments.

This module defines the single source of truth for:
- Evidence quality tags used throughout reports
- Confidence levels (unified across all modules)
- Core enums shared between ai_case_officer, reasoning_engine, evidence_tracker, and councils
- Evidence source citation helpers

OPAQUE PRODUCT PRINCIPLE:
Every output of this system must be transparent and traceable. These constants
ensure consistent tagging across all modules so the officer can always identify:
- What evidence exists and where it came from
- What evidence is missing and what impact that has
- What measurements are needed before conclusions can be drawn
- What consultation responses are still awaited
"""

from enum import Enum


# =============================================================================
# EVIDENCE TAGS — Used inline in all report text
# =============================================================================
# These MUST be used consistently across ALL modules. Do not invent new tags.

class EvidenceTag:
    """Standardised evidence tags for inline use in report text.

    Usage:
        f"{EvidenceTag.REQUIRED} The ridge height must be confirmed from elevation drawings."
        f"{EvidenceTag.VERIFY} Separation distance of 18.5m measured from site plan SP-01."
    """

    REQUIRED = "[EVIDENCE REQUIRED]"
    """Data not available — must be obtained before assessment can be completed."""

    VERIFY = "[VERIFY]"
    """Data present but requires officer confirmation (e.g. from site visit)."""

    MEASUREMENT = "[MEASUREMENT REQUIRED]"
    """Specific measurement needed from submitted plans before test can be applied."""

    AWAITING = "[AWAITING RESPONSE]"
    """Consultation response not yet received — do not fabricate a response."""

    NOT_CONSULTED = "[NOT CONSULTED]"
    """Consultee not consulted because constraint/trigger not present."""

    SITE_VISIT = "[SITE VISIT REQUIRED]"
    """Information can only be obtained from a site visit."""

    NOT_EVIDENCED = "[NOT EVIDENCED]"
    """Claim made without supporting evidence — used as a warning."""


# =============================================================================
# CONFIDENCE LEVELS — Unified across all modules
# =============================================================================

class ConfidenceLevel(str, Enum):
    """Unified confidence level used across all assessment modules.

    Replaces:
    - float confidence (0.0-1.0) in ai_case_officer.py
    - ConfidenceLevel enum in councils/broxtowe/case_officer.py
    - str confidence in evidence_tracker.py and report_generator.py
    """

    HIGH = "high"
    """70%+ of data points verified from authoritative sources."""

    MEDIUM = "medium"
    """40-69% of data points verified; some inferred or assumed."""

    LOW = "low"
    """<40% verified; significant data gaps but some assessment possible."""

    CANNOT_ASSESS = "cannot_assess"
    """Critical data missing — no determination possible without further information."""

    @property
    def score(self) -> float:
        """Numeric score for calculations (0.0 to 1.0)."""
        return {
            ConfidenceLevel.HIGH: 0.85,
            ConfidenceLevel.MEDIUM: 0.60,
            ConfidenceLevel.LOW: 0.40,
            ConfidenceLevel.CANNOT_ASSESS: 0.15,
        }[self]

    @staticmethod
    def from_score(score: float) -> "ConfidenceLevel":
        """Convert numeric score to confidence level."""
        if score >= 0.70:
            return ConfidenceLevel.HIGH
        elif score >= 0.45:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.CANNOT_ASSESS

    @staticmethod
    def from_evidence_counts(verified: int, total: int, unknown: int = 0) -> "ConfidenceLevel":
        """Calculate confidence from evidence item counts."""
        if total == 0:
            return ConfidenceLevel.CANNOT_ASSESS
        verified_ratio = verified / total
        unknown_ratio = unknown / total if total > 0 else 0
        if verified_ratio >= 0.7:
            return ConfidenceLevel.HIGH
        elif verified_ratio >= 0.4 and unknown_ratio < 0.3:
            return ConfidenceLevel.MEDIUM
        elif unknown_ratio >= 0.5:
            return ConfidenceLevel.CANNOT_ASSESS
        else:
            return ConfidenceLevel.LOW


# =============================================================================
# CORE PLANNING ENUMS — Single definition, imported everywhere
# =============================================================================

class HarmLevel(str, Enum):
    """Heritage harm levels per NPPF paragraphs 199-202.

    Used by: ai_case_officer, councils/broxtowe/case_officer, reasoning_engine.
    """

    NO_HARM = "no_harm"
    NEGLIGIBLE = "negligible"
    LESS_THAN_SUBSTANTIAL_LOW = "less_than_substantial_low"
    LESS_THAN_SUBSTANTIAL_MODERATE = "less_than_substantial_moderate"
    LESS_THAN_SUBSTANTIAL_HIGH = "less_than_substantial_high"
    SUBSTANTIAL = "substantial"
    TOTAL_LOSS = "total_loss"


class AmenityImpact(str, Enum):
    """Residential amenity impact levels.

    Used by: ai_case_officer, councils/broxtowe/case_officer.
    """

    NO_IMPACT = "no_impact"
    MINOR_ACCEPTABLE = "minor_acceptable"
    MODERATE_MITIGATABLE = "moderate_mitigatable"
    SIGNIFICANT_HARMFUL = "significant_harmful"
    SEVERE_UNACCEPTABLE = "severe_unacceptable"


class Weight(int, Enum):
    """Weight to be given to material considerations in the planning balance.

    Per NPPF paragraph 199, heritage assets carry great/very great weight.
    Used by: ai_case_officer, councils/broxtowe/case_officer.
    """

    NO_WEIGHT = 0
    LIMITED = 1
    MODERATE = 2
    SIGNIFICANT = 3
    SUBSTANTIAL = 4
    GREAT = 5
    VERY_GREAT = 6  # Reserved for heritage assets per NPPF 199


# =============================================================================
# EVIDENCE SOURCE CITATION HELPERS
# =============================================================================

def cite_source(source_type: str, detail: str = "") -> str:
    """Generate a consistent source citation string.

    Args:
        source_type: One of 'application_form', 'proposal_text', 'document',
                     'constraints', 'site_plan', 'elevation', 'floor_plan',
                     'das', 'policy', 'precedent', 'site_visit', 'calculation'.
        detail: Specific detail (e.g. document name, page number, quoted text).

    Returns:
        Formatted citation string like "(source: application form)"

    Examples:
        cite_source("proposal_text", "two storey rear extension")
        -> "(source: proposal text — 'two storey rear extension')"

        cite_source("document", "Elevation Drawing EL-01, page 2")
        -> "(source: Elevation Drawing EL-01, page 2)"
    """
    if source_type == "proposal_text" and detail:
        return f"(source: proposal text — '{detail}')"
    elif detail:
        return f"(source: {detail})"
    else:
        labels = {
            "application_form": "application form",
            "proposal_text": "proposal text",
            "constraints": "constraints data",
            "site_visit": "site visit",
            "calculation": "calculation",
        }
        label = labels.get(source_type, source_type)
        return f"(source: {label})"
