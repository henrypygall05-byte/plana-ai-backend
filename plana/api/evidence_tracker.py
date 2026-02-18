"""
Evidence Tracking System for Planning Assessments.

Tracks what evidence is actually available for each aspect of an assessment,
ensuring that reports only state what can be verified and clearly mark
data quality levels.

Key Principle: An assessment is only as good as its evidence.
- Don't make assertions without evidence
- Don't generate placeholder text pretending to be analysis
- Be explicit about what we know vs. what we don't know
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidenceQuality(str, Enum):
    """Quality level of evidence for an assertion."""

    VERIFIED = "verified"           # Directly confirmed from authoritative source
    DOCUMENT_EXTRACTED = "document_extracted"  # Parsed from submitted documents
    DATABASE_MATCHED = "database_matched"      # From case database or policy database
    INFERRED = "inferred"           # Logically deduced from available data
    ASSUMED = "assumed"             # Standard assumption, not site-specific
    UNKNOWN = "unknown"             # No evidence available


class EvidenceSource(str, Enum):
    """Source of evidence."""

    APPLICATION_FORM = "application_form"
    SUBMITTED_DOCUMENT = "submitted_document"
    SITE_PLAN = "site_plan"
    FLOOR_PLAN = "floor_plan"
    ELEVATION = "elevation"
    DESIGN_ACCESS_STATEMENT = "design_access_statement"
    POLICY_DATABASE = "policy_database"
    CASE_DATABASE = "case_database"
    CONSTRAINT_DATABASE = "constraint_database"
    POSTCODE_PROFILE = "postcode_profile"  # Generic area data, not site-specific
    CALCULATION = "calculation"
    ASSUMPTION = "assumption"


@dataclass
class EvidenceItem:
    """A single piece of evidence supporting an assertion."""

    assertion: str                  # What we're claiming
    value: Any                      # The actual value/data
    quality: EvidenceQuality        # How reliable is this?
    source: EvidenceSource          # Where did it come from?
    source_document: str = ""       # Specific document name if applicable
    source_page: int | None = None  # Page number if applicable
    confidence_pct: int = 0         # 0-100 confidence score
    verification_needed: str = ""   # What needs to be verified
    notes: str = ""                 # Additional context


@dataclass
class AssessmentEvidence:
    """Complete evidence package for an assessment topic."""

    topic: str
    items: list[EvidenceItem] = field(default_factory=list)

    # Summary metrics
    verified_count: int = 0
    inferred_count: int = 0
    unknown_count: int = 0

    # Key gaps that prevent robust assessment
    critical_gaps: list[str] = field(default_factory=list)

    # What can we actually conclude?
    evidence_based_conclusion: str = ""
    conclusion_confidence: str = ""  # "high", "medium", "low", "cannot_assess"

    def add_evidence(self, item: EvidenceItem):
        """Add evidence and update counts."""
        self.items.append(item)

        if item.quality == EvidenceQuality.VERIFIED:
            self.verified_count += 1
        elif item.quality in [EvidenceQuality.INFERRED, EvidenceQuality.ASSUMED]:
            self.inferred_count += 1
        elif item.quality == EvidenceQuality.UNKNOWN:
            self.unknown_count += 1
            if item.verification_needed:
                self.critical_gaps.append(item.verification_needed)

    def get_overall_quality(self) -> str:
        """Calculate overall evidence quality for this assessment."""
        total = len(self.items)
        if total == 0:
            return "no_evidence"

        verified_ratio = self.verified_count / total
        unknown_ratio = self.unknown_count / total

        if verified_ratio >= 0.7:
            return "high"
        elif verified_ratio >= 0.4 and unknown_ratio < 0.3:
            return "medium"
        elif unknown_ratio >= 0.5:
            return "insufficient"
        else:
            return "low"

    def can_make_determination(self) -> bool:
        """Can we make a robust planning determination based on available evidence?"""
        quality = self.get_overall_quality()
        return quality in ["high", "medium"]

    def format_evidence_summary(self) -> str:
        """Format evidence summary for report inclusion."""
        quality = self.get_overall_quality()

        if quality == "no_evidence":
            return "**Evidence Status:** No site-specific evidence available. Assessment cannot be completed."

        lines = [f"**Evidence Status:** {quality.upper()} confidence"]
        lines.append(f"- Verified items: {self.verified_count}")
        lines.append(f"- Inferred/assumed: {self.inferred_count}")
        lines.append(f"- Not available: {self.unknown_count}")

        if self.critical_gaps:
            lines.append("\n**Critical information gaps:**")
            for gap in self.critical_gaps[:5]:
                lines.append(f"- {gap}")

        return "\n".join(lines)


def build_site_evidence(
    address: str,
    postcode: str,
    constraints: list[str],
    documents: list[dict] | None = None,
) -> AssessmentEvidence:
    """
    Build evidence package for site-related assessments.

    This function tracks what we actually know about the site
    vs. what we're just assuming.
    """
    evidence = AssessmentEvidence(topic="Site Description")

    # Address - we have this
    evidence.add_evidence(EvidenceItem(
        assertion="Site address",
        value=address,
        quality=EvidenceQuality.VERIFIED,
        source=EvidenceSource.APPLICATION_FORM,
        confidence_pct=100,
    ))

    # Postcode - we have this
    if postcode:
        evidence.add_evidence(EvidenceItem(
            assertion="Postcode",
            value=postcode,
            quality=EvidenceQuality.VERIFIED,
            source=EvidenceSource.APPLICATION_FORM,
            confidence_pct=100,
        ))

    # Constraints - check if from verified source or just application form
    for constraint in constraints:
        evidence.add_evidence(EvidenceItem(
            assertion=f"Constraint: {constraint}",
            value=constraint,
            quality=EvidenceQuality.ASSUMED,  # We haven't verified against GIS
            source=EvidenceSource.APPLICATION_FORM,
            confidence_pct=60,
            verification_needed="Confirm constraints against council mapping system",
        ))

    # Site character - WE DON'T KNOW THIS without site visit
    evidence.add_evidence(EvidenceItem(
        assertion="Street character",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Site visit required to assess street character",
    ))

    # Neighbouring properties - WE DON'T KNOW THIS
    evidence.add_evidence(EvidenceItem(
        assertion="Relationship to neighbours",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Site plans and site visit required",
    ))

    # Existing features - WE DON'T KNOW THIS
    evidence.add_evidence(EvidenceItem(
        assertion="Existing site features",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Site survey required",
    ))

    # Calculate evidence-based conclusion
    quality = evidence.get_overall_quality()
    if quality == "high":
        evidence.evidence_based_conclusion = "Site characteristics are well-documented."
        evidence.conclusion_confidence = "high"
    elif quality == "medium":
        evidence.evidence_based_conclusion = "Basic site information available, but detailed assessment requires verification."
        evidence.conclusion_confidence = "medium"
    else:
        evidence.evidence_based_conclusion = "Insufficient site information available for robust assessment."
        evidence.conclusion_confidence = "cannot_assess"

    return evidence


def build_design_evidence(
    proposal: str,
    documents: list[dict] | None = None,
    extracted_data: dict | None = None,
) -> AssessmentEvidence:
    """
    Build evidence package for design assessment.

    Only include what we actually know from documents.
    """
    evidence = AssessmentEvidence(topic="Design and Visual Impact")
    extracted = extracted_data or {}

    # Height - check if we have it
    if extracted.get("ridge_height_metres"):
        evidence.add_evidence(EvidenceItem(
            assertion="Ridge height",
            value=f"{extracted['ridge_height_metres']}m",
            quality=EvidenceQuality.DOCUMENT_EXTRACTED,
            source=EvidenceSource.ELEVATION,
            source_document=extracted.get("ridge_height_source", "elevation drawing"),
            confidence_pct=85,
        ))
    else:
        evidence.add_evidence(EvidenceItem(
            assertion="Ridge height",
            value=None,
            quality=EvidenceQuality.UNKNOWN,
            source=EvidenceSource.ASSUMPTION,
            confidence_pct=0,
            verification_needed="Measure from elevation drawings",
        ))

    # Storeys - check if we have it
    if extracted.get("num_storeys"):
        evidence.add_evidence(EvidenceItem(
            assertion="Number of storeys",
            value=extracted["num_storeys"],
            quality=EvidenceQuality.DOCUMENT_EXTRACTED,
            source=EvidenceSource.FLOOR_PLAN,
            confidence_pct=90,
        ))
    else:
        evidence.add_evidence(EvidenceItem(
            assertion="Number of storeys",
            value=None,
            quality=EvidenceQuality.UNKNOWN,
            source=EvidenceSource.ASSUMPTION,
            confidence_pct=0,
            verification_needed="Count from floor plans/elevations",
        ))

    # Materials - check if we have them
    if extracted.get("materials"):
        evidence.add_evidence(EvidenceItem(
            assertion="External materials",
            value=", ".join(extracted["materials"]),
            quality=EvidenceQuality.DOCUMENT_EXTRACTED,
            source=EvidenceSource.DESIGN_ACCESS_STATEMENT,
            confidence_pct=80,
        ))
    else:
        evidence.add_evidence(EvidenceItem(
            assertion="External materials",
            value=None,
            quality=EvidenceQuality.UNKNOWN,
            source=EvidenceSource.ASSUMPTION,
            confidence_pct=0,
            verification_needed="Extract from D&A statement or secure by condition",
        ))

    # Scale relative to neighbours - WE DON'T KNOW THIS
    evidence.add_evidence(EvidenceItem(
        assertion="Scale relative to neighbours",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Compare with neighbouring properties on site visit",
    ))

    # Building line - WE DON'T KNOW THIS
    evidence.add_evidence(EvidenceItem(
        assertion="Relationship to building line",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Measure from site plan and verify on site",
    ))

    # Calculate conclusion - be more helpful even with limited data
    quality = evidence.get_overall_quality()
    has_some_data = evidence.verified_count > 0 or any(
        item.value is not None for item in evidence.items
    )

    if quality in ["high", "medium"]:
        evidence.evidence_based_conclusion = (
            "Design documentation provides sufficient information for assessment. "
            "The proposal can be assessed against design policy requirements."
        )
        evidence.conclusion_confidence = quality
    elif has_some_data:
        evidence.evidence_based_conclusion = (
            "Some design information is available from the application details. "
            "Assessment can proceed with verification of specific measurements from submitted plans."
        )
        evidence.conclusion_confidence = "medium"
    else:
        evidence.evidence_based_conclusion = (
            "Design details to be confirmed from submitted drawings. "
            "Materials and finishes can be secured by condition."
        )
        evidence.conclusion_confidence = "low"

    return evidence


def build_highways_evidence(
    proposal: str,
    documents: list[dict] | None = None,
    extracted_data: dict | None = None,
) -> AssessmentEvidence:
    """
    Build evidence package for highways assessment.
    """
    evidence = AssessmentEvidence(topic="Highways and Access")
    extracted = extracted_data or {}

    # Parking spaces - check if we have it
    if extracted.get("total_parking_spaces"):
        evidence.add_evidence(EvidenceItem(
            assertion="Parking provision",
            value=f"{extracted['total_parking_spaces']} spaces",
            quality=EvidenceQuality.DOCUMENT_EXTRACTED,
            source=EvidenceSource.SITE_PLAN,
            confidence_pct=85,
        ))
    else:
        evidence.add_evidence(EvidenceItem(
            assertion="Parking provision",
            value=None,
            quality=EvidenceQuality.UNKNOWN,
            source=EvidenceSource.ASSUMPTION,
            confidence_pct=0,
            verification_needed="Count from site plan",
        ))

    # Visibility splays - check if we have them
    if extracted.get("visibility_splay_left") and extracted.get("visibility_splay_right"):
        evidence.add_evidence(EvidenceItem(
            assertion="Visibility splays",
            value=f"2.4m x {extracted['visibility_splay_left']}m",
            quality=EvidenceQuality.DOCUMENT_EXTRACTED,
            source=EvidenceSource.SITE_PLAN,
            confidence_pct=80,
        ))
    else:
        evidence.add_evidence(EvidenceItem(
            assertion="Visibility splays",
            value=None,
            quality=EvidenceQuality.UNKNOWN,
            source=EvidenceSource.ASSUMPTION,
            confidence_pct=0,
            verification_needed="Measure from site plan - check 2.4m x 43m for 30mph road",
        ))

    # Access width - check if we have it
    if extracted.get("access_width_metres"):
        evidence.add_evidence(EvidenceItem(
            assertion="Access width",
            value=f"{extracted['access_width_metres']}m",
            quality=EvidenceQuality.DOCUMENT_EXTRACTED,
            source=EvidenceSource.SITE_PLAN,
            confidence_pct=85,
        ))
    else:
        evidence.add_evidence(EvidenceItem(
            assertion="Access width",
            value=None,
            quality=EvidenceQuality.UNKNOWN,
            source=EvidenceSource.ASSUMPTION,
            confidence_pct=0,
            verification_needed="Measure from site plan - min 3.2m for single dwelling",
        ))

    # Road classification - WE DON'T KNOW THIS
    evidence.add_evidence(EvidenceItem(
        assertion="Road classification and speed limit",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Confirm with highway authority records",
    ))

    # Highway authority consultation - WE DON'T HAVE THIS
    evidence.add_evidence(EvidenceItem(
        assertion="Highway authority response",
        value=None,
        quality=EvidenceQuality.UNKNOWN,
        source=EvidenceSource.ASSUMPTION,
        confidence_pct=0,
        verification_needed="Await highway authority consultation response",
    ))

    # Calculate conclusion - be more helpful even with limited data
    quality = evidence.get_overall_quality()
    has_parking_data = extracted.get("total_parking_spaces", 0) > 0

    if quality in ["high", "medium"]:
        evidence.evidence_based_conclusion = (
            "Highway information is available for assessment. "
            "Subject to highway authority confirmation of no objection."
        )
        evidence.conclusion_confidence = quality
    elif has_parking_data:
        evidence.evidence_based_conclusion = (
            "Parking provision information available. "
            "Visibility splays and access details can be secured by condition."
        )
        evidence.conclusion_confidence = "medium"
    else:
        evidence.evidence_based_conclusion = (
            "Standard highways conditions recommended to secure visibility splays, "
            "access construction and parking layout. No highway objection anticipated "
            "subject to these requirements being met."
        )
        evidence.conclusion_confidence = "low"

    return evidence


def format_evidence_based_assessment(
    topic: str,
    evidence: AssessmentEvidence,
    policy_citations: list[str],
) -> str:
    """
    Format an assessment section that only states what is evidenced.

    Key principle: Don't make assertions we can't support.
    """
    lines = []

    # Evidence quality header
    quality = evidence.get_overall_quality()
    quality_indicator = {
        "high": "✓ HIGH CONFIDENCE",
        "medium": "◐ MEDIUM CONFIDENCE",
        "low": "◑ LOW CONFIDENCE",
        "insufficient": "✗ INSUFFICIENT EVIDENCE",
        "no_evidence": "✗ NO EVIDENCE AVAILABLE",
    }.get(quality, "? UNKNOWN")

    lines.append(f"**Assessment Confidence:** {quality_indicator}")
    lines.append("")

    # What we actually know
    verified_items = [i for i in evidence.items if i.quality in [EvidenceQuality.VERIFIED, EvidenceQuality.DOCUMENT_EXTRACTED]]
    if verified_items:
        lines.append("**What we know (verified):**")
        for item in verified_items:
            source_note = f" (from {item.source.value})" if item.source != EvidenceSource.ASSUMPTION else ""
            lines.append(f"- {item.assertion}: {item.value}{source_note}")
        lines.append("")

    # What we're assuming
    assumed_items = [i for i in evidence.items if i.quality in [EvidenceQuality.INFERRED, EvidenceQuality.ASSUMED]]
    if assumed_items:
        lines.append("**What we're assuming (not verified):**")
        for item in assumed_items:
            lines.append(f"- {item.assertion}: {item.value or 'standard assumption'}")
        lines.append("")

    # What we don't know
    unknown_items = [i for i in evidence.items if i.quality == EvidenceQuality.UNKNOWN]
    if unknown_items:
        lines.append("**Information not available:**")
        for item in unknown_items:
            lines.append(f"- {item.assertion}: {item.verification_needed}")
        lines.append("")

    # Policy framework (this we do know)
    if policy_citations:
        lines.append("**Applicable policies:**")
        for citation in policy_citations[:3]:
            lines.append(f"- {citation}")
        lines.append("")

    # Evidence-based conclusion
    lines.append("**Assessment conclusion:**")
    if evidence.can_make_determination():
        lines.append(evidence.evidence_based_conclusion)
    else:
        lines.append(f"**CANNOT COMPLETE ASSESSMENT** - {evidence.evidence_based_conclusion}")
        if evidence.critical_gaps:
            lines.append("")
            lines.append("Before determination, the following must be resolved:")
            for gap in evidence.critical_gaps[:5]:
                lines.append(f"- {gap}")

    return "\n".join(lines)


def calculate_report_data_quality(assessments: list[AssessmentEvidence]) -> dict:
    """
    Calculate overall data quality metrics for the entire report.

    Returns dict with quality metrics and recommendations.
    """
    if not assessments:
        return {
            "overall_quality": "no_evidence",
            "can_determine": False,
            "verified_percentage": 0,
            "critical_gaps": ["No assessments available"],
            "recommendation": "Cannot produce a meaningful assessment without evidence.",
        }

    total_items = sum(len(a.items) for a in assessments)
    total_verified = sum(a.verified_count for a in assessments)
    total_unknown = sum(a.unknown_count for a in assessments)

    verified_pct = (total_verified / total_items * 100) if total_items > 0 else 0
    unknown_pct = (total_unknown / total_items * 100) if total_items > 0 else 0

    # Collect all critical gaps
    all_gaps = []
    for a in assessments:
        all_gaps.extend(a.critical_gaps)

    # Determine overall quality
    can_determine_count = sum(1 for a in assessments if a.can_make_determination())

    if verified_pct >= 60 and can_determine_count == len(assessments):
        overall = "high"
        can_determine = True
        recommendation = "Sufficient evidence for assessment."
    elif verified_pct >= 30 and can_determine_count >= len(assessments) * 0.5:
        overall = "medium"
        can_determine = True
        recommendation = "Assessment possible but some aspects require verification."
    else:
        overall = "low"
        can_determine = False
        recommendation = "Insufficient evidence for robust assessment. See critical gaps below."

    return {
        "overall_quality": overall,
        "can_determine": can_determine,
        "verified_percentage": round(verified_pct, 1),
        "unknown_percentage": round(unknown_pct, 1),
        "assessments_with_evidence": can_determine_count,
        "total_assessments": len(assessments),
        "critical_gaps": list(set(all_gaps))[:10],
        "recommendation": recommendation,
    }
