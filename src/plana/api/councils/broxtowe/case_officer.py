"""
Broxtowe Borough Council AI Case Officer.

This module provides planning assessment for Broxtowe Borough Council using:
- Greater Nottingham Aligned Core Strategy (2014)
- Broxtowe Part 2 Local Plan (2019)
- NPPF (2023)
- Local precedent from historic decisions

IMPORTANT DISCLAIMER:
This tool is designed to support, not replace, professional planning judgement.
All outputs should be reviewed by a qualified planning officer before use.
The system may contain biases from training data and historic decisions.

Follows principles:
1. Explainability - All conclusions cite policies and precedent
2. Designed Friction - Flags complex/contentious cases requiring officer judgement
3. Spatial Awareness - Location affects policy interpretation
4. Outcome Awareness - Considers post-consent risks
5. Uncertainty Disclosure - Explicitly states limitations and data gaps
6. Professional Respect - Supports decision-making, does not decide
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum

from .policies import get_broxtowe_policies, get_policy_citation, BROXTOWE_POLICIES
from .cases import find_similar_broxtowe_cases, get_broxtowe_precedent_analysis


# =============================================================================
# CONFIDENCE AND UNCERTAINTY FRAMEWORK
# =============================================================================

class ConfidenceLevel(Enum):
    """Confidence levels for assessments."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConfidenceAssessment:
    """
    Structured confidence assessment with explicit reasoning.

    Used to help officers understand reliability of AI conclusions.
    """
    level: ConfidenceLevel
    score: float  # 0.0 to 1.0
    reasoning: str
    limiting_factors: list[str]
    data_gaps: list[str]
    comparable_cases_found: int
    policy_clarity: str  # "clear", "ambiguous", "conflicting"

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score": self.score,
            "reasoning": self.reasoning,
            "limiting_factors": self.limiting_factors,
            "data_gaps": self.data_gaps,
            "comparable_cases": self.comparable_cases_found,
            "policy_clarity": self.policy_clarity,
        }


@dataclass
class UncertaintyDisclosure:
    """
    Explicit disclosure of limitations and potential biases.

    For transparency in planning appeals, committee meetings, and legal challenges.
    """
    data_limitations: list[str]
    potential_biases: list[str]
    incomplete_information: list[str]
    assumptions_made: list[str]
    areas_requiring_officer_judgement: list[str]

    def to_dict(self) -> dict:
        return {
            "data_limitations": self.data_limitations,
            "potential_biases": self.potential_biases,
            "incomplete_information": self.incomplete_information,
            "assumptions_made": self.assumptions_made,
            "requires_officer_judgement": self.areas_requiring_officer_judgement,
        }


# =============================================================================
# CASE COMPLEXITY AND FRICTION FRAMEWORK
# =============================================================================

class CaseComplexity(Enum):
    """Classification of case complexity for designed friction."""
    ROUTINE = "routine"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_CONTENTIOUS = "highly_contentious"


@dataclass
class FrictionFlag:
    """
    A flag indicating where reflection is needed over speed.

    These flags deliberately slow down the assessment process where
    professional judgement is critical.
    """
    category: str  # "contentious", "complex", "policy_conflict", "spatial", "precedent"
    issue: str
    why_flagged: str
    officer_action_required: str
    cannot_resolve_through_policy: bool = False


@dataclass
class CaseClassification:
    """
    Classification of whether case is routine or requires deeper reflection.
    """
    complexity: CaseComplexity
    is_routine: bool
    friction_flags: list[FrictionFlag]
    requires_committee: bool
    requires_site_visit: bool
    reasoning: str

    def to_dict(self) -> dict:
        return {
            "complexity": self.complexity.value,
            "is_routine": self.is_routine,
            "friction_flags": [
                {
                    "category": f.category,
                    "issue": f.issue,
                    "why_flagged": f.why_flagged,
                    "action_required": f.officer_action_required,
                    "cannot_resolve_through_policy": f.cannot_resolve_through_policy,
                }
                for f in self.friction_flags
            ],
            "requires_committee": self.requires_committee,
            "requires_site_visit": self.requires_site_visit,
            "reasoning": self.reasoning,
        }


# =============================================================================
# SPATIAL AWARENESS FRAMEWORK
# =============================================================================

@dataclass
class SpatialContext:
    """
    Location-based policy context.

    Planning is fundamentally a spatial activity - this captures how
    location affects policy interpretation.
    """
    ward: str
    postcode: str
    area_character: str
    designated_constraints: list[str]
    policy_zones: list[str]
    spatial_policy_implications: list[dict]  # {policy, implication, reasoning}
    incomplete_spatial_info: list[str]

    def to_dict(self) -> dict:
        return {
            "ward": self.ward,
            "postcode": self.postcode,
            "area_character": self.area_character,
            "designated_constraints": self.designated_constraints,
            "policy_zones": self.policy_zones,
            "spatial_implications": self.spatial_policy_implications,
            "incomplete_spatial_info": self.incomplete_spatial_info,
        }


# =============================================================================
# OUTCOME AWARENESS FRAMEWORK
# =============================================================================

@dataclass
class PostConsentRisk:
    """
    A risk that may materialise after planning consent is granted.

    Goes beyond policy compliance to consider likely real-world outcomes.
    """
    risk_type: str  # "traffic", "drainage", "biodiversity", "enforcement", "delivery"
    description: str
    likelihood: str  # "likely", "possible", "unlikely"
    evidence_basis: str
    similar_cases_with_issue: list[str]
    suggested_mitigation: str
    monitoring_recommended: bool


@dataclass
class OutcomeAwareness:
    """
    Forward-looking assessment of likely outcomes beyond policy compliance.
    """
    post_consent_risks: list[PostConsentRisk]
    conditions_from_similar_cases: list[dict]
    delivery_concerns: list[str]
    monitoring_gaps: list[str]
    uncertainty_statement: str

    def to_dict(self) -> dict:
        return {
            "post_consent_risks": [
                {
                    "type": r.risk_type,
                    "description": r.description,
                    "likelihood": r.likelihood,
                    "evidence": r.evidence_basis,
                    "similar_cases": r.similar_cases_with_issue,
                    "mitigation": r.suggested_mitigation,
                    "monitoring_recommended": r.monitoring_recommended,
                }
                for r in self.post_consent_risks
            ],
            "conditions_from_similar_cases": self.conditions_from_similar_cases,
            "delivery_concerns": self.delivery_concerns,
            "monitoring_gaps": self.monitoring_gaps,
            "uncertainty_statement": self.uncertainty_statement,
        }


# =============================================================================
# EXPLAINABILITY FRAMEWORK
# =============================================================================

@dataclass
class PolicyExplanation:
    """
    Explicit explanation of why a policy applies and how it's interpreted.
    """
    policy_id: str
    policy_name: str
    why_relevant: str  # "This policy applies because..."
    interpretation: str
    weight_given: str
    location_factor: str  # How location affects interpretation


@dataclass
class PrecedentExplanation:
    """
    Explicit explanation of precedent relevance.
    """
    case_reference: str
    why_similar: str  # "This proposal is similar to [case] because..."
    key_differences: list[str]
    outcome_relevance: str
    confidence_in_comparison: ConfidenceLevel
    caveats: list[str]


# =============================================================================
# CORE ENUMS AND DATACLASSES
# =============================================================================

class HarmLevel(Enum):
    """Heritage harm levels per NPPF paragraphs 201-202."""
    NO_HARM = "no_harm"
    NEGLIGIBLE = "negligible"
    LESS_THAN_SUBSTANTIAL_LOW = "less_than_substantial_low"
    LESS_THAN_SUBSTANTIAL_MODERATE = "less_than_substantial_moderate"
    LESS_THAN_SUBSTANTIAL_HIGH = "less_than_substantial_high"
    SUBSTANTIAL = "substantial"
    TOTAL_LOSS = "total_loss"


class AmenityImpact(Enum):
    """Residential amenity impact levels."""
    NO_IMPACT = "no_impact"
    MINOR_ACCEPTABLE = "minor_acceptable"
    MODERATE_MITIGATABLE = "moderate_mitigatable"
    SIGNIFICANT_HARMFUL = "significant_harmful"
    SEVERE_UNACCEPTABLE = "severe_unacceptable"


class Weight(Enum):
    """Weight to be given to material considerations."""
    NO_WEIGHT = 0
    LIMITED = 1
    MODERATE = 2
    SIGNIFICANT = 3
    SUBSTANTIAL = 4
    GREAT = 5
    VERY_GREAT = 6


@dataclass
class MaterialConsideration:
    """A material consideration in the planning balance with full explainability."""
    factor: str
    description: str
    is_benefit: bool
    weight: Weight
    policy_basis: list[str]
    evidence: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_reasoning: str = ""
    why_this_weight: str = ""  # Explicit reasoning for weight given


@dataclass
class HeritageAssessment:
    """Assessment of heritage impact per NPPF Chapter 16."""
    asset_type: str
    asset_grade: Optional[str]
    significance: str
    impact_on_significance: str
    harm_level: HarmLevel
    justification: str
    public_benefits: list[str]
    nppf_paragraph: str
    statutory_duty: str
    weight_to_harm: Weight = Weight.VERY_GREAT
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    limitations: list[str] = field(default_factory=list)


@dataclass
class AmenityAssessment:
    """Assessment of residential amenity impact."""
    affected_property: str
    impact_type: str
    current_situation: str
    proposed_impact: str
    impact_level: AmenityImpact
    mitigation_possible: bool
    mitigation_measures: list[str]
    policy_basis: list[str]
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    requires_site_visit: bool = False
    assessment_limitations: str = ""


@dataclass
class Condition:
    """A planning condition meeting the 6 tests."""
    number: int
    title: str
    full_wording: str
    reason: str
    policy_basis: str
    condition_type: str
    precedent_source: str = ""  # Reference to similar case where condition was used
    is_necessary: bool = True
    is_relevant: bool = True
    is_enforceable: bool = True
    is_precise: bool = True
    is_reasonable: bool = True
    meets_six_tests: bool = True


@dataclass
class PlanningBalance:
    """The planning balance with full transparency."""
    benefits: list[MaterialConsideration]
    harms: list[MaterialConsideration]
    heritage_harm: Optional[HeritageAssessment]
    amenity_impacts: list[AmenityAssessment]
    tilted_balance_engaged: bool = False
    tilted_balance_reason: str = ""
    para_202_balance: Optional[str] = None
    benefits_outweigh_harms: bool = True
    overall_narrative: str = ""
    officer_judgement_areas: list[str] = field(default_factory=list)


STATUTORY_DUTIES = {
    "section_66": """Section 66(1) of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires special regard to the desirability of preserving the building or its setting.""",
    "section_72": """Section 72(1) of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires special attention to preserving or enhancing the character or appearance of the conservation area.""",
}


# =============================================================================
# SPATIAL CONTEXT ASSESSMENT
# =============================================================================

def assess_spatial_context(
    site_address: str,
    ward: str,
    postcode: str,
    constraints: list[str],
) -> SpatialContext:
    """
    Assess the spatial context of the site.

    This function explicitly considers how location affects policy interpretation,
    acknowledging that planning is fundamentally a spatial activity.
    """
    address_lower = site_address.lower()
    constraints_lower = [c.lower() for c in constraints]

    # Determine area character based on location
    area_character = "Urban residential area"
    if "beeston" in address_lower:
        area_character = "Beeston is a major district centre with Victorian/Edwardian character, significant student population due to University of Nottingham proximity, and a mix of residential and commercial uses."
    elif "stapleford" in address_lower:
        area_character = "Stapleford is a traditional market town with industrial heritage, predominantly residential with a historic centre."
    elif "eastwood" in address_lower:
        area_character = "Eastwood has significant literary heritage as D.H. Lawrence's birthplace. The area has historic character with some industrial legacy."
    elif "bramcote" in address_lower:
        area_character = "Bramcote is a semi-rural suburb with historic village core. Characterised by larger plots and mature landscaping."
    elif "kimberley" in address_lower:
        area_character = "Kimberley is a former mining town with a compact centre and surrounding residential areas."
    elif "chilwell" in address_lower:
        area_character = "Chilwell is a residential suburb with mix of housing ages, including inter-war and post-war estates."
    elif "attenborough" in address_lower:
        area_character = "Attenborough has significant ecological constraints due to proximity to Attenborough Nature Reserve (SSSI). Predominantly low-density residential."
    elif "nuthall" in address_lower:
        area_character = "Nuthall is a semi-rural village within Green Belt, with a historic core and modern residential development."

    # Identify policy zones
    policy_zones = []
    if any("green belt" in c for c in constraints_lower):
        policy_zones.append("Green Belt (Policy 8, ACS-16)")
    if any("conservation" in c for c in constraints_lower):
        policy_zones.append("Conservation Area (Policy 23, ACS-11)")
    if any("flood" in c for c in constraints_lower):
        policy_zones.append("Flood Zone (Policy 1, ACS-1)")
    if any("sssi" in c for c in constraints_lower) or "attenborough" in address_lower:
        policy_zones.append("Near SSSI/Nature Reserve (Policy 31, ACS-17)")

    # Build spatial policy implications
    spatial_implications = []

    if "beeston" in address_lower:
        spatial_implications.append({
            "policy": "ACS-6",
            "implication": "District Centre policies apply",
            "reasoning": "This policy is relevant due to the site's location within Beeston District Centre boundary, where intensification may be supported.",
        })

    if any("conservation" in c for c in constraints_lower):
        spatial_implications.append({
            "policy": "Policy-23",
            "implication": "Conservation Area policies require preservation or enhancement",
            "reasoning": "This policy applies because the site is within a designated Conservation Area. Any development must preserve or enhance the character and appearance of the area.",
        })

    if any("green belt" in c for c in constraints_lower):
        spatial_implications.append({
            "policy": "Policy-8, NPPF Chapter 13",
            "implication": "Strict Green Belt controls apply",
            "reasoning": "This policy is relevant due to the site's location within the Nottingham-Derby Green Belt. Development is inappropriate unless it falls within exceptions at NPPF paragraph 149-150.",
        })

    # Identify incomplete spatial information
    incomplete_info = []
    if not constraints:
        incomplete_info.append("No constraint data provided - site may have designations not captured")
    if not any("flood" in c for c in constraints_lower):
        incomplete_info.append("Flood risk zone not confirmed - Environment Agency data should be checked")
    if "attenborough" in address_lower and not any("sssi" in c for c in constraints_lower):
        incomplete_info.append("Site near Attenborough Nature Reserve - ecological constraints should be verified")

    return SpatialContext(
        ward=ward,
        postcode=postcode,
        area_character=area_character,
        designated_constraints=constraints,
        policy_zones=policy_zones,
        spatial_policy_implications=spatial_implications,
        incomplete_spatial_info=incomplete_info,
    )


# =============================================================================
# CASE CLASSIFICATION AND FRICTION
# =============================================================================

def classify_case_complexity(
    proposal: str,
    constraints: list[str],
    similar_cases: list[dict],
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
) -> CaseClassification:
    """
    Classify case complexity to introduce appropriate friction.

    This function deliberately identifies where speed should be sacrificed
    for deeper professional reflection.
    """
    friction_flags = []
    requires_committee = False
    requires_site_visit = False

    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]

    # Check for contentious elements
    if any("green belt" in c for c in constraints_lower):
        friction_flags.append(FrictionFlag(
            category="policy_conflict",
            issue="Green Belt development",
            why_flagged="Green Belt policy is a key national policy constraint. Local decisions in Green Belt are frequently challenged at appeal.",
            officer_action_required="Verify whether proposal falls within NPPF paragraph 149-150 exceptions. Consider whether very special circumstances exist.",
            cannot_resolve_through_policy=False,
        ))
        requires_site_visit = True

    if heritage_assessment and heritage_assessment.harm_level in [
        HarmLevel.SUBSTANTIAL,
        HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH,
        HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE,
    ]:
        friction_flags.append(FrictionFlag(
            category="contentious",
            issue="Heritage harm identified",
            why_flagged=f"Harm level assessed as {heritage_assessment.harm_level.value.replace('_', ' ')}. Heritage decisions are frequently subject to appeal and legal challenge.",
            officer_action_required="Verify harm assessment through site visit. Consider whether public benefits are sufficient. Check Conservation Officer views.",
            cannot_resolve_through_policy=heritage_assessment.harm_level == HarmLevel.SUBSTANTIAL,
        ))
        requires_committee = heritage_assessment.harm_level == HarmLevel.SUBSTANTIAL
        requires_site_visit = True

    # Amenity contentious cases
    severe_amenity = any(
        a.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE
        for a in amenity_assessments
    )
    if severe_amenity:
        friction_flags.append(FrictionFlag(
            category="contentious",
            issue="Severe amenity impact identified",
            why_flagged="Amenity impacts are subjective and site-specific. Neighbour objections may raise issues not captured in application data.",
            officer_action_required="Site visit essential to verify impact. Consider neighbour representations carefully.",
            cannot_resolve_through_policy=True,
        ))
        requires_site_visit = True

    # Limited precedent
    if len(similar_cases) < 2:
        friction_flags.append(FrictionFlag(
            category="precedent",
            issue="Limited comparable cases",
            why_flagged="Fewer than 2 comparable cases found. Assessment relies more heavily on policy interpretation than established practice.",
            officer_action_required="Consider whether unique site circumstances warrant deviation from standard approach.",
            cannot_resolve_through_policy=False,
        ))

    # Conflicting precedent
    if similar_cases:
        approvals = sum(1 for c in similar_cases if c.get("decision", "").lower() in ["approved", "approve"])
        refusals = len(similar_cases) - approvals
        if approvals > 0 and refusals > 0:
            friction_flags.append(FrictionFlag(
                category="precedent",
                issue="Conflicting precedent",
                why_flagged=f"Mixed decisions in similar cases ({approvals} approved, {refusals} refused). This suggests case-specific factors are determinative.",
                officer_action_required="Examine distinguishing features of approved vs refused cases. Identify which precedent is most relevant.",
                cannot_resolve_through_policy=True,
            ))

    # Complex proposals
    complex_keywords = ["mixed use", "change of use", "subdivision", "demolition", "replacement dwelling"]
    if any(kw in proposal_lower for kw in complex_keywords):
        friction_flags.append(FrictionFlag(
            category="complex",
            issue="Complex proposal type",
            why_flagged="This proposal type involves multiple policy considerations and potential impacts that require careful assessment.",
            officer_action_required="Ensure all relevant technical consultees have been consulted.",
            cannot_resolve_through_policy=False,
        ))

    # Determine overall complexity
    if any(f.cannot_resolve_through_policy for f in friction_flags):
        complexity = CaseComplexity.HIGHLY_CONTENTIOUS
        is_routine = False
    elif len(friction_flags) >= 3:
        complexity = CaseComplexity.COMPLEX
        is_routine = False
    elif len(friction_flags) >= 1:
        complexity = CaseComplexity.MODERATE
        is_routine = False
    else:
        complexity = CaseComplexity.ROUTINE
        is_routine = True

    reasoning = f"Case classified as {complexity.value}. "
    if is_routine:
        reasoning += "This case appears suitable for delegated decision with AI support. Standard policy interpretation applies."
    else:
        reasoning += f"{len(friction_flags)} friction flag(s) identified requiring officer attention. "
        if any(f.cannot_resolve_through_policy for f in friction_flags):
            reasoning += "Some issues cannot be resolved through policy interpretation alone - professional judgement is essential."

    return CaseClassification(
        complexity=complexity,
        is_routine=is_routine,
        friction_flags=friction_flags,
        requires_committee=requires_committee,
        requires_site_visit=requires_site_visit,
        reasoning=reasoning,
    )


# =============================================================================
# OUTCOME AWARENESS
# =============================================================================

def assess_post_consent_outcomes(
    proposal: str,
    constraints: list[str],
    similar_cases: list[dict],
    application_type: str,
) -> OutcomeAwareness:
    """
    Assess likely post-consent outcomes and risks.

    Goes beyond policy compliance to consider what actually happens
    after permission is granted.
    """
    risks = []
    conditions_from_similar = []
    delivery_concerns = []
    monitoring_gaps = []

    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]

    # Traffic and parking risks
    if "dwelling" in proposal_lower or "residential" in application_type.lower():
        risks.append(PostConsentRisk(
            risk_type="traffic",
            description="Increased traffic and parking demand from new residential use",
            likelihood="likely",
            evidence_basis="Residential development generates additional vehicle movements",
            similar_cases_with_issue=[],
            suggested_mitigation="Parking provision condition, cycle storage requirement",
            monitoring_recommended=False,
        ))

    # Drainage risks
    if "extension" in proposal_lower or "new" in proposal_lower:
        risks.append(PostConsentRisk(
            risk_type="drainage",
            description="Increased surface water runoff from additional impermeable surfaces",
            likelihood="possible",
            evidence_basis="Building extensions increase impermeable area",
            similar_cases_with_issue=[],
            suggested_mitigation="Sustainable drainage condition, permeable paving requirement",
            monitoring_recommended=False,
        ))

    # Flood zone specific risks
    if any("flood" in c for c in constraints_lower):
        risks.append(PostConsentRisk(
            risk_type="drainage",
            description="Flood risk to property and potential increase in flood risk elsewhere",
            likelihood="possible",
            evidence_basis="Site located within identified flood risk area",
            similar_cases_with_issue=[],
            suggested_mitigation="Flood Risk Assessment condition, finished floor levels condition",
            monitoring_recommended=True,
        ))
        monitoring_gaps.append("Limited monitoring data on flood events affecting similar developments in this area")

    # Biodiversity risks
    if "attenborough" in proposal_lower.replace(" ", "") or any("sssi" in c for c in constraints_lower):
        risks.append(PostConsentRisk(
            risk_type="biodiversity",
            description="Potential impact on designated ecological sites",
            likelihood="possible",
            evidence_basis="Proximity to SSSI/Nature Reserve",
            similar_cases_with_issue=[],
            suggested_mitigation="Construction Environmental Management Plan, timing restrictions",
            monitoring_recommended=True,
        ))
        delivery_concerns.append("Historically, biodiversity mitigation measures have been difficult to enforce and monitor")

    # Heritage enforcement risks
    if any("conservation" in c for c in constraints_lower) or any("listed" in c for c in constraints_lower):
        risks.append(PostConsentRisk(
            risk_type="enforcement",
            description="Risk of unauthorised works or deviation from approved materials",
            likelihood="possible",
            evidence_basis="Heritage works require careful supervision to ensure compliance",
            similar_cases_with_issue=[],
            suggested_mitigation="Pre-commencement materials condition, site supervision during sensitive works",
            monitoring_recommended=True,
        ))

    # Extract conditions from similar cases
    for case in similar_cases:
        if case.get("decision", "").lower() in ["approved", "approve"]:
            conditions_from_similar.append({
                "case_reference": case.get("reference", "Unknown"),
                "conditions_noted": case.get("conditions", "Standard conditions applied"),
                "relevance": "Similar proposal type and constraints",
            })

    # Build uncertainty statement
    uncertainty = "Outcome predictions are inherently uncertain. "
    uncertainty += f"This assessment is based on {len(similar_cases)} comparable case(s). "
    if len(similar_cases) < 3:
        uncertainty += "Limited comparable cases means post-consent outcomes are harder to predict. "
    if monitoring_gaps:
        uncertainty += "Monitoring data is limited for comparable developments in this area."

    return OutcomeAwareness(
        post_consent_risks=risks,
        conditions_from_similar_cases=conditions_from_similar,
        delivery_concerns=delivery_concerns,
        monitoring_gaps=monitoring_gaps,
        uncertainty_statement=uncertainty,
    )


# =============================================================================
# CONFIDENCE ASSESSMENT
# =============================================================================

def assess_confidence(
    similar_cases: list[dict],
    constraints: list[str],
    heritage_assessment: Optional[HeritageAssessment],
    friction_flags: list[FrictionFlag],
) -> ConfidenceAssessment:
    """
    Generate explicit confidence assessment with reasoning.

    This ensures officers understand the reliability of AI conclusions.
    """
    score = 0.7  # Base confidence
    limiting_factors = []
    data_gaps = []

    # Adjust for comparable cases
    if len(similar_cases) >= 5:
        score += 0.15
    elif len(similar_cases) >= 3:
        score += 0.10
    elif len(similar_cases) >= 1:
        score += 0.05
    else:
        score -= 0.10
        limiting_factors.append("No comparable cases found in local database")
        data_gaps.append("Historic decision data for this proposal type")

    # Adjust for clear constraints
    if constraints:
        score += 0.05
    else:
        score -= 0.10
        data_gaps.append("Site constraint information not provided")

    # Adjust for heritage complexity
    if heritage_assessment:
        if heritage_assessment.harm_level in [HarmLevel.NO_HARM, HarmLevel.NEGLIGIBLE]:
            score += 0.05
        elif heritage_assessment.harm_level == HarmLevel.SUBSTANTIAL:
            score -= 0.15
            limiting_factors.append("Substantial heritage harm assessment requires Conservation Officer input")

    # Adjust for friction flags
    if len(friction_flags) > 2:
        score -= 0.10
        limiting_factors.append("Multiple contentious issues reduce assessment certainty")

    # Check for policy conflicts
    conflicting = any(f.category == "policy_conflict" for f in friction_flags)
    if conflicting:
        score -= 0.10
        limiting_factors.append("Policy conflicts identified - interpretation may vary")
        policy_clarity = "conflicting"
    elif len(friction_flags) > 0:
        policy_clarity = "ambiguous"
    else:
        policy_clarity = "clear"

    # Clamp score
    score = max(0.3, min(0.95, score))

    # Determine level
    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.6:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW

    # Build reasoning
    reasoning = f"Confidence is {level.value} (score: {score:.0%}). "
    if level == ConfidenceLevel.HIGH:
        reasoning += "Strong precedent support and clear policy framework. "
    elif level == ConfidenceLevel.MEDIUM:
        reasoning += "Some uncertainty in assessment due to limited comparables or policy ambiguity. "
    else:
        reasoning += "Significant uncertainty - officer review essential. "

    if limiting_factors:
        reasoning += f"Key limitations: {'; '.join(limiting_factors)}."

    return ConfidenceAssessment(
        level=level,
        score=score,
        reasoning=reasoning,
        limiting_factors=limiting_factors,
        data_gaps=data_gaps,
        comparable_cases_found=len(similar_cases),
        policy_clarity=policy_clarity,
    )


# =============================================================================
# UNCERTAINTY DISCLOSURE
# =============================================================================

def generate_uncertainty_disclosure(
    similar_cases: list[dict],
    constraints: list[str],
    documents: list[dict],
    spatial_context: SpatialContext,
) -> UncertaintyDisclosure:
    """
    Generate explicit disclosure of limitations and biases.

    For transparency in appeals, committee, and legal challenge.
    """
    data_limitations = [
        "Assessment based on text description only - physical site inspection not performed",
        "Supporting documents not reviewed in detail by AI system",
    ]

    if len(similar_cases) < 3:
        data_limitations.append(f"Only {len(similar_cases)} comparable case(s) found - precedent analysis may be incomplete")

    if not documents:
        data_limitations.append("No supporting documents provided for review")

    potential_biases = [
        "Historic decision data may reflect past policy interpretations that have since evolved",
        "Training data may underrepresent certain application types or areas",
        "Similarity matching may not capture all relevant site-specific factors",
    ]

    incomplete_information = spatial_context.incomplete_spatial_info.copy()
    if not constraints:
        incomplete_information.append("Site constraints not fully specified")

    assumptions_made = [
        "Assumes application description accurately represents proposed development",
        "Assumes no material changes to relevant planning policies since database update",
        "Assumes neighbour consultation responses align with typical patterns for this area",
    ]

    officer_judgement_areas = [
        "Visual impact assessment - requires site inspection",
        "Impact on specific neighbours - requires detailed knowledge of site relationships",
        "Weight to be given to third-party representations",
        "Overall planning balance - AI provides analysis but officer makes final judgement",
    ]

    return UncertaintyDisclosure(
        data_limitations=data_limitations,
        potential_biases=potential_biases,
        incomplete_information=incomplete_information,
        assumptions_made=assumptions_made,
        areas_requiring_officer_judgement=officer_judgement_areas,
    )


# =============================================================================
# HERITAGE ASSESSMENT
# =============================================================================

def generate_broxtowe_heritage_assessment(
    proposal: str,
    constraints: list[str],
    site_address: str,
) -> Optional[HeritageAssessment]:
    """
    Generate heritage assessment specific to Broxtowe context.

    With explicit confidence levels and limitations.
    """
    constraints_lower = [c.lower() for c in constraints]
    proposal_lower = proposal.lower()

    has_listed = any('listed' in c for c in constraints_lower)
    has_conservation = any('conservation' in c for c in constraints_lower)

    if not has_listed and not has_conservation:
        return None

    limitations = [
        "Heritage significance assessment based on text description - site inspection recommended",
        "Conservation Officer input not available in this assessment",
    ]

    # Determine asset type and grade
    asset_type = "Conservation Area"
    asset_grade = None
    statutory_duty = "section_72"
    confidence = ConfidenceLevel.MEDIUM

    for c in constraints:
        if 'grade i ' in c.lower() or 'grade i listed' in c.lower():
            asset_type = "Listed Building"
            asset_grade = "I"
            statutory_duty = "section_66"
            limitations.append("Grade I listed buildings have highest significance - specialist advice essential")
        elif 'grade ii*' in c.lower():
            asset_type = "Listed Building"
            asset_grade = "II*"
            statutory_duty = "section_66"
            limitations.append("Grade II* listed buildings have high significance - Conservation Officer input recommended")
        elif 'grade ii' in c.lower() or 'listed' in c.lower():
            asset_type = "Listed Building"
            asset_grade = "II"
            statutory_duty = "section_66"

    # Build significance description with Broxtowe context
    address_lower = site_address.lower()

    if asset_grade:
        significance = f"This Grade {asset_grade} listed building is of special interest warranting every effort to preserve it."
    else:
        significance = "The Conservation Area derives its significance from its historic townscape and architectural character."

    # Add Broxtowe-specific context
    if "bramcote" in address_lower:
        significance += " Bramcote Conservation Area is characterised by its historic village core, including the Grade II* listed Holy Trinity Church and traditional stone buildings. This context is relevant because development must respect the established character and materials palette of the area."
    elif "beeston" in address_lower:
        significance += " Beeston Conservation Area includes the historic town centre with Victorian and Edwardian commercial and residential buildings. This context is relevant because the area has a distinctive urban grain that should be preserved."
    elif "eastwood" in address_lower:
        significance += " Eastwood has significant literary heritage as the birthplace of D.H. Lawrence, with several associated heritage assets. This context is relevant because the Council has a particular interest in preserving the literary associations of the area."
    else:
        limitations.append("Specific Conservation Area character not fully captured - local knowledge may be required")

    # Determine harm level with confidence
    positive_indicators = [
        'restoration', 'restore', 'repair', 'timber', 'traditional',
        'like for like', 'internal', 'sympathetic', 'enhance', 'preserve'
    ]

    is_positive = any(term in proposal_lower for term in positive_indicators)
    is_internal = 'internal' in proposal_lower
    installing_upvc = ('upvc' in proposal_lower or 'u-pvc' in proposal_lower) and not ('remove' in proposal_lower or 'replacing upvc' in proposal_lower)

    if has_listed and installing_upvc:
        harm_level = HarmLevel.SUBSTANTIAL
        impact = "The proposed uPVC windows would cause substantial harm to the significance of this listed building. This assessment is made because uPVC is an inappropriate material that fails to preserve the special interest of the listed building."
        confidence = ConfidenceLevel.HIGH
    elif is_positive or is_internal:
        harm_level = HarmLevel.NO_HARM
        impact = "The proposal would preserve or enhance the significance of the heritage asset. This assessment is made because the works are sympathetic/internal and would not adversely affect significance."
        confidence = ConfidenceLevel.HIGH
    elif 'front' in proposal_lower and ('extension' in proposal_lower or 'elevation' in proposal_lower or 'shopfront' in proposal_lower):
        # Front elevation changes are more impactful - check BEFORE generic extensions
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE
        impact = "Development to the front elevation may harm the character of the Conservation Area. This assessment is made because front elevations are prominent in the streetscene and contribute to area character."
        confidence = ConfidenceLevel.MEDIUM
        limitations.append("Front elevation impact is highly site-specific - Conservation Officer input recommended")
    elif 'single storey' in proposal_lower or 'rear extension' in proposal_lower:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
        impact = "The proposal would cause less than substantial harm at the lower end of the spectrum. This assessment is made because single storey rear additions typically have limited impact on significance, being subordinate and to the rear."
        confidence = ConfidenceLevel.MEDIUM
        limitations.append("Harm level may vary depending on site-specific visibility and design")
    elif 'extension' in proposal_lower:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
        impact = "The proposal would cause less than substantial harm, subject to appropriate materials. This assessment is made because extensions can affect setting but impact depends on design and materials."
        confidence = ConfidenceLevel.MEDIUM
    else:
        harm_level = HarmLevel.NO_HARM
        impact = "The proposal is not considered to cause harm to the heritage asset. This assessment is made because no harmful elements are identified, but site inspection may reveal additional considerations."
        confidence = ConfidenceLevel.LOW
        limitations.append("Harm assessment uncertain without site inspection")

    # Determine NPPF paragraph
    if harm_level == HarmLevel.SUBSTANTIAL:
        nppf_para = "201"
        justification = f"NPPF Paragraph 201 applies because substantial harm is identified. This paragraph requires substantial public benefits to outweigh substantial harm, or the tests at 201(a)-(d) to be met. {STATUTORY_DUTIES[statutory_duty]}"
    elif harm_level in [HarmLevel.LESS_THAN_SUBSTANTIAL_LOW, HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE, HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH]:
        nppf_para = "202"
        justification = f"NPPF Paragraph 202 applies because less than substantial harm is identified. This paragraph requires the harm to be weighed against the public benefits of the proposal. {STATUTORY_DUTIES[statutory_duty]}"
    else:
        nppf_para = "199"
        justification = f"NPPF Paragraph 199 applies because no harm is identified. This paragraph requires great weight to be given to conservation of heritage assets. The proposal preserves the significance in accordance with Policy 23. {STATUTORY_DUTIES[statutory_duty]}"

    return HeritageAssessment(
        asset_type=asset_type,
        asset_grade=asset_grade,
        significance=significance,
        impact_on_significance=impact,
        harm_level=harm_level,
        justification=justification,
        public_benefits=[],
        nppf_paragraph=nppf_para,
        statutory_duty=statutory_duty,
        weight_to_harm=Weight.VERY_GREAT,
        confidence=confidence,
        limitations=limitations,
    )


# =============================================================================
# AMENITY ASSESSMENT
# =============================================================================

def generate_broxtowe_amenity_assessment(
    proposal: str,
    constraints: list[str],
    application_type: str,
) -> list[AmenityAssessment]:
    """
    Generate amenity assessment using Broxtowe Policy 17 requirements.

    With explicit confidence and limitations.
    """
    assessments = []
    proposal_lower = proposal.lower()

    # Check for privacy concerns
    has_balcony = 'balcony' in proposal_lower
    has_first_floor = 'first floor' in proposal_lower or 'two storey' in proposal_lower

    if has_balcony and has_first_floor:
        assessments.append(AmenityAssessment(
            affected_property="Neighbouring residential properties",
            impact_type="privacy",
            current_situation="Neighbours currently enjoy reasonable privacy (assumed based on typical residential context).",
            proposed_impact="The first floor balcony would introduce overlooking of neighbouring gardens and habitable rooms. This assessment is made because elevated external amenity space provides direct views into neighbouring property that would not otherwise exist.",
            impact_level=AmenityImpact.SEVERE_UNACCEPTABLE,
            mitigation_possible=False,
            mitigation_measures=[],
            policy_basis=["Policy-17", "ACS-10"],
            confidence=ConfidenceLevel.HIGH,
            requires_site_visit=True,
            assessment_limitations="Actual impact depends on separation distances and existing boundary treatment - site visit required",
        ))

    # Default assessment for extensions
    if 'extension' in proposal_lower and not assessments:
        assessments.append(AmenityAssessment(
            affected_property="Adjoining properties",
            impact_type="daylight_outlook",
            current_situation="Neighbours receive adequate daylight and outlook (assumed).",
            proposed_impact="The extension is designed to minimise impact. A 45-degree assessment would typically indicate acceptable daylight levels for this type of development.",
            impact_level=AmenityImpact.MINOR_ACCEPTABLE,
            mitigation_possible=True,
            mitigation_measures=["Design kept subordinate", "Set-back from boundaries"],
            policy_basis=["Policy-17", "ACS-10"],
            confidence=ConfidenceLevel.MEDIUM,
            requires_site_visit=True,
            assessment_limitations="This assessment is limited by lack of site-specific information. Actual daylight/sunlight impact requires technical assessment and site inspection.",
        ))

    return assessments


# =============================================================================
# CONDITIONS
# =============================================================================

def generate_broxtowe_conditions(
    proposal: str,
    constraints: list[str],
    application_type: str,
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
    similar_cases: list[dict],
) -> list[Condition]:
    """
    Generate conditions with precedent references where available.
    """
    conditions = []
    num = 1

    # Find precedent for conditions
    approved_cases = [c for c in similar_cases if c.get("decision", "").lower() in ["approved", "approve"]]
    precedent_ref = approved_cases[0]["reference"] if approved_cases else ""

    # Standard time limit
    conditions.append(Condition(
        number=num,
        title="Time Limit",
        full_wording="The development hereby permitted shall be begun before the expiration of three years from the date of this permission.",
        reason="To comply with Section 91 of the Town and Country Planning Act 1990, as amended by Section 51 of the Planning and Compulsory Purchase Act 2004.",
        policy_basis="TCPA 1990 s.91",
        condition_type="compliance",
        precedent_source="Standard condition",
    ))
    num += 1

    # Approved plans
    conditions.append(Condition(
        number=num,
        title="Approved Plans",
        full_wording="The development hereby permitted shall be carried out in complete accordance with the approved plans listed in the schedule attached to this decision notice.",
        reason="For the avoidance of doubt and in the interests of proper planning in accordance with Policy 17 of the Broxtowe Part 2 Local Plan.",
        policy_basis="Policy-17",
        condition_type="compliance",
        precedent_source="Standard condition",
    ))
    num += 1

    # Materials
    constraints_lower = [c.lower() for c in constraints]
    has_heritage = any("conservation" in c or "listed" in c for c in constraints_lower)

    if has_heritage:
        conditions.append(Condition(
            number=num,
            title="Materials",
            full_wording="""Notwithstanding any description of materials in the application, no development above damp proof course level shall take place until samples or precise specifications of all external facing materials have been submitted to and approved in writing by the Local Planning Authority. The materials shall include:
(a) Facing bricks (including mortar colour and pointing style);
(b) Roof tiles/slates;
(c) Windows and doors (including 1:20 scale drawings);
(d) Rainwater goods;
(e) Any other external materials.
The development shall be constructed in accordance with the approved materials and retained as such thereafter.""",
            reason="To ensure the development preserves or enhances the character of the Conservation Area/setting of the listed building in accordance with Policy 23 of the Broxtowe Part 2 Local Plan, Policy 11 of the Aligned Core Strategy, and Chapter 16 of the NPPF.",
            policy_basis="Policy-23, ACS-11, NPPF Chapter 16",
            condition_type="pre-commencement",
            precedent_source=precedent_ref or "Standard heritage condition",
        ))
        num += 1
    else:
        conditions.append(Condition(
            number=num,
            title="Materials",
            full_wording="The external materials used in the construction of the development hereby permitted shall match those of the existing building unless otherwise agreed in writing by the Local Planning Authority.",
            reason="To ensure a satisfactory standard of external appearance in accordance with Policy 17 of the Broxtowe Part 2 Local Plan and Policy 10 of the Aligned Core Strategy.",
            policy_basis="Policy-17, ACS-10",
            condition_type="compliance",
            precedent_source="Standard condition",
        ))
        num += 1

    # Green Belt condition
    if any("green belt" in c for c in constraints_lower):
        conditions.append(Condition(
            number=num,
            title="Restriction on Use",
            full_wording="The building(s) hereby permitted shall be used only for the purpose(s) specified in this permission and for no other purpose, including any other purpose within the same Use Class.",
            reason="To protect the openness of the Green Belt in accordance with Policy 8 of the Broxtowe Part 2 Local Plan, Policy 16 of the Aligned Core Strategy, and the NPPF.",
            policy_basis="Policy-8, ACS-16, NPPF Chapter 13",
            condition_type="compliance",
            precedent_source="Standard Green Belt condition",
        ))
        num += 1

    # PD removal
    if "householder" in application_type.lower() or "extension" in proposal.lower():
        conditions.append(Condition(
            number=num,
            title="Removal of Permitted Development Rights",
            full_wording="Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015 (or any order revoking and re-enacting that Order), no additional windows or openings shall be inserted in the side elevation(s) of the development hereby approved at first floor level or above without the prior written approval of the Local Planning Authority.",
            reason="To protect the residential amenity of neighbouring properties in accordance with Policy 17 of the Broxtowe Part 2 Local Plan.",
            policy_basis="Policy-17",
            condition_type="compliance",
            precedent_source=precedent_ref or "Standard amenity condition",
        ))
        num += 1

    return conditions


# =============================================================================
# MAIN REPORT GENERATION
# =============================================================================

def generate_broxtowe_report(
    reference: str,
    site_address: str,
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str,
    postcode: str,
    applicant_name: str | None = None,
    documents: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Generate a complete case officer report for Broxtowe Borough Council.

    This report follows six key principles:
    1. Explainability - All conclusions cite policies and precedent with explicit reasoning
    2. Designed Friction - Flags complex/contentious cases requiring officer judgement
    3. Spatial Awareness - Location affects policy interpretation
    4. Outcome Awareness - Considers post-consent risks
    5. Uncertainty Disclosure - Explicitly states limitations and data gaps
    6. Professional Respect - Supports decision-making, does not decide

    Returns:
        Dictionary containing structured report data and markdown report
    """
    documents = documents or []

    # 1. Assess spatial context
    spatial_context = assess_spatial_context(site_address, ward, postcode, constraints)

    # 2. Get relevant policies
    policies = get_broxtowe_policies(proposal, application_type, constraints)

    # 3. Find similar cases
    similar_cases = find_similar_broxtowe_cases(
        proposal=proposal,
        application_type=application_type,
        constraints=constraints,
        ward=ward,
        postcode=postcode,
        limit=5,
    )
    precedent_analysis = get_broxtowe_precedent_analysis(similar_cases)

    # 4. Heritage assessment
    heritage_assessment = generate_broxtowe_heritage_assessment(proposal, constraints, site_address)

    # 5. Amenity assessment
    amenity_assessments = generate_broxtowe_amenity_assessment(proposal, constraints, application_type)

    # 6. Classify case complexity (DESIGNED FRICTION)
    case_classification = classify_case_complexity(
        proposal=proposal,
        constraints=constraints,
        similar_cases=similar_cases,
        heritage_assessment=heritage_assessment,
        amenity_assessments=amenity_assessments,
    )

    # 7. Assess post-consent outcomes
    outcome_awareness = assess_post_consent_outcomes(
        proposal=proposal,
        constraints=constraints,
        similar_cases=similar_cases,
        application_type=application_type,
    )

    # 8. Identify benefits with explicit reasoning
    benefits = [
        MaterialConsideration(
            factor="Provision of improved living accommodation",
            description="The proposal would provide improved living accommodation for the occupiers.",
            is_benefit=True,
            weight=Weight.MODERATE,
            policy_basis=["NPPF paragraph 8", "ACS-8"],
            evidence="Inherent benefit of residential development",
            confidence=ConfidenceLevel.HIGH,
            confidence_reasoning="Well-established planning benefit",
            why_this_weight="Moderate weight because this is a personal benefit to occupiers rather than a wider public benefit.",
        ),
    ]

    if "extension" in proposal.lower() or "bedroom" in proposal.lower():
        benefits.append(MaterialConsideration(
            factor="Support for family housing needs",
            description="The development would support the changing needs of the household.",
            is_benefit=True,
            weight=Weight.LIMITED,
            policy_basis=["ACS-8", "Policy-15"],
            evidence="Social sustainability benefit",
            confidence=ConfidenceLevel.MEDIUM,
            confidence_reasoning="Benefit assumed based on proposal type",
            why_this_weight="Limited weight because this is a private benefit without evidence of specific housing need.",
        ))

    # 9. Identify harms with explicit reasoning
    harms = []
    proposal_lower = proposal.lower()

    if heritage_assessment and heritage_assessment.harm_level != HarmLevel.NO_HARM:
        harm_weights = {
            HarmLevel.SUBSTANTIAL: Weight.VERY_GREAT,
            HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH: Weight.SUBSTANTIAL,
            HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE: Weight.SIGNIFICANT,
            HarmLevel.LESS_THAN_SUBSTANTIAL_LOW: Weight.LIMITED,
            HarmLevel.NEGLIGIBLE: Weight.NO_WEIGHT,
        }
        heritage_weight = harm_weights.get(heritage_assessment.harm_level, Weight.MODERATE)

        harms.append(MaterialConsideration(
            factor="Harm to heritage asset",
            description=heritage_assessment.impact_on_significance,
            is_benefit=False,
            weight=heritage_weight,
            policy_basis=["Policy-23", "ACS-11", "NPPF paragraphs 199-202"],
            evidence="Heritage impact assessment",
            confidence=heritage_assessment.confidence,
            confidence_reasoning=f"Confidence {heritage_assessment.confidence.value} due to: {'; '.join(heritage_assessment.limitations[:2])}",
            why_this_weight=f"Weight of {heritage_weight.name} given because NPPF paragraph 199 requires great weight to conservation. Harm level assessed as {heritage_assessment.harm_level.value.replace('_', ' ')}.",
        ))

    for amenity in amenity_assessments:
        if amenity.impact_level in [AmenityImpact.SIGNIFICANT_HARMFUL, AmenityImpact.SEVERE_UNACCEPTABLE]:
            harms.append(MaterialConsideration(
                factor=f"Harm to residential amenity ({amenity.impact_type})",
                description=amenity.proposed_impact,
                is_benefit=False,
                weight=Weight.SUBSTANTIAL if amenity.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE else Weight.SIGNIFICANT,
                policy_basis=["Policy-17"],
                evidence="Amenity impact assessment",
                confidence=amenity.confidence,
                confidence_reasoning=amenity.assessment_limitations,
                why_this_weight=f"Weight given because Policy 17 requires protection of residential amenity. Impact level assessed as {amenity.impact_level.value.replace('_', ' ')}.",
            ))

    # Check for specific red flags
    constraints_lower = [c.lower() for c in constraints]

    # uPVC in Conservation Area
    has_conservation = any("conservation" in c for c in constraints_lower)
    has_upvc = "upvc" in proposal_lower or "u-pvc" in proposal_lower
    replacing_with_upvc = has_upvc and ("replace" in proposal_lower or "window" in proposal_lower)
    replacing_upvc_with_timber = ("timber" in proposal_lower or "sash" in proposal_lower) and "upvc" in proposal_lower and ("remove" in proposal_lower or "replacing upvc" in proposal_lower)

    if has_conservation and has_upvc and replacing_with_upvc and not replacing_upvc_with_timber:
        harms.append(MaterialConsideration(
            factor="Inappropriate materials in Conservation Area",
            description="Replacing traditional windows with uPVC would fail to preserve or enhance the character of the Conservation Area. This policy applies because uPVC is an inappropriate modern material that erodes the historic character of Conservation Areas.",
            is_benefit=False,
            weight=Weight.VERY_GREAT,
            policy_basis=["Policy-23", "ACS-11", "NPPF Chapter 16"],
            evidence="Material assessment",
            confidence=ConfidenceLevel.HIGH,
            confidence_reasoning="Clear policy position on inappropriate materials in Conservation Areas",
            why_this_weight="Very great weight because this represents fundamental harm to Conservation Area character contrary to statutory duty under Section 72.",
        ))

    # Balcony privacy harm
    if "balcony" in proposal_lower and "first floor" in proposal_lower:
        harms.append(MaterialConsideration(
            factor="Privacy harm from balcony",
            description="First floor balcony would cause unacceptable overlooking. This assessment is made because elevated external amenity space introduces direct views into neighbouring property.",
            is_benefit=False,
            weight=Weight.SUBSTANTIAL,
            policy_basis=["Policy-17"],
            evidence="Amenity assessment",
            confidence=ConfidenceLevel.MEDIUM,
            confidence_reasoning="Assessment limited by lack of site-specific separation distances",
            why_this_weight="Substantial weight because overlooking from elevated amenity space typically cannot be mitigated.",
        ))

    # 10. Generate planning balance
    total_benefit_weight = sum(b.weight.value for b in benefits)
    total_harm_weight = sum(h.weight.value for h in harms)
    benefits_outweigh = total_benefit_weight > total_harm_weight

    # Areas requiring officer judgement
    officer_judgement_areas = [
        "Final assessment of visual impact on streetscene",
        "Weight to be given to any third-party representations",
    ]
    if not case_classification.is_routine:
        officer_judgement_areas.extend([f.officer_action_required for f in case_classification.friction_flags])

    # 11. Determine recommendation
    if not benefits_outweigh:
        recommendation = "REFUSE"
        conditions = []
        refusal_reasons = []

        for harm in harms:
            if harm.weight.value >= Weight.SUBSTANTIAL.value:
                refusal_reasons.append({
                    "number": len(refusal_reasons) + 1,
                    "reason": f"The proposed development would cause {harm.factor.lower()}. {harm.description} This is contrary to {', '.join(harm.policy_basis)}.",
                    "policy_basis": ", ".join(harm.policy_basis),
                })
    else:
        recommendation = "APPROVE_WITH_CONDITIONS"
        conditions = generate_broxtowe_conditions(
            proposal=proposal,
            constraints=constraints,
            application_type=application_type,
            heritage_assessment=heritage_assessment,
            amenity_assessments=amenity_assessments,
            similar_cases=similar_cases,
        )
        refusal_reasons = []

    # 12. Assess confidence
    confidence_assessment = assess_confidence(
        similar_cases=similar_cases,
        constraints=constraints,
        heritage_assessment=heritage_assessment,
        friction_flags=case_classification.friction_flags,
    )

    # 13. Generate uncertainty disclosure
    uncertainty_disclosure = generate_uncertainty_disclosure(
        similar_cases=similar_cases,
        constraints=constraints,
        documents=documents,
        spatial_context=spatial_context,
    )

    # 14. Build planning balance narrative with explicit reasoning
    balance_narrative = f"""**Assessment Framework**

This assessment has been conducted against:
- Greater Nottingham Aligned Core Strategy (2014)
- Broxtowe Part 2 Local Plan (2019)
- National Planning Policy Framework (2023)

**Benefits Identified**
"""
    for b in benefits:
        balance_narrative += f"\n- **{b.factor}** (Weight: {b.weight.name})\n"
        balance_narrative += f"  - {b.description}\n"
        balance_narrative += f"  - Why this weight: {b.why_this_weight}\n"
        balance_narrative += f"  - Policy basis: {', '.join(b.policy_basis)}\n"
        balance_narrative += f"  - Confidence: {b.confidence.value}\n"

    balance_narrative += "\n**Harms Identified**\n"
    if harms:
        for h in harms:
            balance_narrative += f"\n- **{h.factor}** (Weight: {h.weight.name})\n"
            balance_narrative += f"  - {h.description}\n"
            balance_narrative += f"  - Why this weight: {h.why_this_weight}\n"
            balance_narrative += f"  - Policy basis: {', '.join(h.policy_basis)}\n"
            balance_narrative += f"  - Confidence: {h.confidence.value}\n"
    else:
        balance_narrative += "\nNo significant harms identified.\n"

    balance_narrative += f"""
**Planning Balance Conclusion**

Total benefit weight: {total_benefit_weight} | Total harm weight: {total_harm_weight}

{'The benefits are considered to outweigh the harms.' if benefits_outweigh else 'The harms are considered to outweigh the benefits.'}

**Officer Judgement Required**

This assessment provides analysis to support decision-making. The following areas require officer judgement:
"""
    for area in officer_judgement_areas:
        balance_narrative += f"- {area}\n"

    # Heritage balance
    heritage_balance = None
    if heritage_assessment and heritage_assessment.harm_level != HarmLevel.NO_HARM:
        heritage_balance = f"""**Heritage Balance Assessment**

Asset: {heritage_assessment.asset_type}{f' (Grade {heritage_assessment.asset_grade})' if heritage_assessment.asset_grade else ''}
Harm Level: {heritage_assessment.harm_level.value.replace('_', ' ').title()}

NPPF Paragraph {heritage_assessment.nppf_paragraph} applies because: {heritage_assessment.justification}

**Limitations of this heritage assessment:**
{chr(10).join(f'- {l}' for l in heritage_assessment.limitations)}

{'The public benefits are considered to outweigh this harm.' if benefits_outweigh else 'The harm is not outweighed by the public benefits.'}"""

    planning_balance = PlanningBalance(
        benefits=benefits,
        harms=harms,
        heritage_harm=heritage_assessment,
        amenity_impacts=amenity_assessments,
        tilted_balance_engaged=False,
        tilted_balance_reason="",
        para_202_balance=heritage_balance,
        benefits_outweigh_harms=benefits_outweigh,
        overall_narrative=balance_narrative,
        officer_judgement_areas=officer_judgement_areas,
    )

    # 15. Generate markdown report
    report_md = _format_broxtowe_report_markdown(
        reference=reference,
        site_address=site_address,
        ward=ward,
        applicant=applicant_name or "Not specified",
        application_type=application_type,
        proposal=proposal,
        constraints=constraints,
        spatial_context=spatial_context,
        policies=policies,
        similar_cases=similar_cases,
        precedent_analysis=precedent_analysis,
        heritage_assessment=heritage_assessment,
        amenity_assessments=amenity_assessments,
        planning_balance=planning_balance,
        recommendation=recommendation,
        conditions=conditions,
        refusal_reasons=refusal_reasons,
        case_classification=case_classification,
        confidence_assessment=confidence_assessment,
        uncertainty_disclosure=uncertainty_disclosure,
        outcome_awareness=outcome_awareness,
    )

    return {
        "meta": {
            "reference": reference,
            "council": "Broxtowe Borough Council",
            "generated_at": datetime.now().isoformat(),
            "confidence": confidence_assessment.to_dict(),
            "version": "2.0",
            "principles": [
                "Explainability",
                "Designed Friction",
                "Spatial Awareness",
                "Outcome Awareness",
                "Uncertainty Disclosure",
                "Professional Respect",
            ],
        },
        "case_classification": case_classification.to_dict(),
        "spatial_context": spatial_context.to_dict(),
        "recommendation": {
            "outcome": recommendation,
            "reasoning": balance_narrative,
            "conditions": [{"number": c.number, "title": c.title, "wording": c.full_wording, "reason": c.reason, "precedent": c.precedent_source} for c in conditions],
            "refusal_reasons": refusal_reasons,
            "officer_judgement_required": officer_judgement_areas,
        },
        "policy_context": {
            "development_plan": "Greater Nottingham Aligned Core Strategy (2014) and Broxtowe Part 2 Local Plan (2019)",
            "selected_policies": [{"policy_id": p.id, "policy_name": p.name, "source": p.source_full} for p in policies],
            "spatial_implications": spatial_context.spatial_policy_implications,
        },
        "similarity_analysis": {
            "top_cases": [{"reference": c["reference"], "outcome": c["decision"], "similarity_score": c["similarity_score"]} for c in similar_cases],
            "precedent_analysis": precedent_analysis,
            "confidence_in_precedent": "high" if len(similar_cases) >= 3 else "medium" if len(similar_cases) >= 1 else "low",
        },
        "assessment": {
            "heritage": {
                "harm_level": heritage_assessment.harm_level.value if heritage_assessment else "not_applicable",
                "impact": heritage_assessment.impact_on_significance if heritage_assessment else None,
                "confidence": heritage_assessment.confidence.value if heritage_assessment else None,
                "limitations": heritage_assessment.limitations if heritage_assessment else [],
            } if heritage_assessment else None,
            "amenity": [{"type": a.impact_type, "level": a.impact_level.value, "confidence": a.confidence.value, "limitations": a.assessment_limitations} for a in amenity_assessments],
        },
        "planning_balance": {
            "benefits_weight": total_benefit_weight,
            "harms_weight": total_harm_weight,
            "benefits_outweigh": benefits_outweigh,
            "officer_judgement_areas": officer_judgement_areas,
        },
        "outcome_awareness": outcome_awareness.to_dict(),
        "uncertainty_disclosure": uncertainty_disclosure.to_dict(),
        "report_markdown": report_md,
    }


def _format_broxtowe_report_markdown(
    reference: str,
    site_address: str,
    ward: str,
    applicant: str,
    application_type: str,
    proposal: str,
    constraints: list[str],
    spatial_context: SpatialContext,
    policies: list,
    similar_cases: list[dict],
    precedent_analysis: dict,
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
    planning_balance: PlanningBalance,
    recommendation: str,
    conditions: list[Condition],
    refusal_reasons: list[dict],
    case_classification: CaseClassification,
    confidence_assessment: ConfidenceAssessment,
    uncertainty_disclosure: UncertaintyDisclosure,
    outcome_awareness: OutcomeAwareness,
) -> str:
    """Format the Broxtowe report as professional markdown with full explainability."""

    lines = []

    lines.append("# DELEGATED REPORT")
    lines.append("")
    lines.append("**BROXTOWE BOROUGH COUNCIL**")
    lines.append("**PLANNING AND COMMUNITY DEVELOPMENT**")
    lines.append("")

    # IMPORTANT NOTICE
    lines.append("> **IMPORTANT:** This report is generated by AI to support planning officer decision-making.")
    lines.append("> It does not replace professional judgement. All conclusions should be verified.")
    lines.append(f"> **Confidence Level:** {confidence_assessment.level.value.upper()} ({confidence_assessment.score:.0%})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Case Classification Banner
    if not case_classification.is_routine:
        lines.append(f"## ⚠️ CASE CLASSIFICATION: {case_classification.complexity.value.upper()}")
        lines.append("")
        lines.append(case_classification.reasoning)
        lines.append("")
        if case_classification.friction_flags:
            lines.append("### Issues Requiring Officer Attention")
            lines.append("")
            for flag in case_classification.friction_flags:
                lines.append(f"**{flag.category.title()}: {flag.issue}**")
                lines.append(f"- Why flagged: {flag.why_flagged}")
                lines.append(f"- Action required: {flag.officer_action_required}")
                if flag.cannot_resolve_through_policy:
                    lines.append(f"- ⚠️ *This issue cannot be resolved through policy interpretation alone*")
                lines.append("")
        if case_classification.requires_committee:
            lines.append("**→ COMMITTEE REFERRAL MAY BE APPROPRIATE**")
            lines.append("")
        if case_classification.requires_site_visit:
            lines.append("**→ SITE VISIT RECOMMENDED BEFORE DETERMINATION**")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Application details
    lines.append("## APPLICATION DETAILS")
    lines.append("")
    lines.append("| Field | Details |")
    lines.append("|-------|---------|")
    lines.append(f"| **Reference** | {reference} |")
    lines.append(f"| **Site Address** | {site_address} |")
    lines.append(f"| **Ward** | {ward} |")
    lines.append(f"| **Applicant** | {applicant} |")
    lines.append(f"| **Application Type** | {application_type} |")
    lines.append(f"| **Date of Report** | {datetime.now().strftime('%d %B %Y')} |")
    lines.append("")

    # Proposal
    lines.append("## PROPOSAL")
    lines.append("")
    lines.append(proposal)
    lines.append("")

    # Spatial Context
    lines.append("## SITE CONTEXT AND SPATIAL ANALYSIS")
    lines.append("")
    lines.append(f"**Area Character:** {spatial_context.area_character}")
    lines.append("")

    if constraints:
        lines.append("### Site Constraints")
        lines.append("")
        for c in constraints:
            lines.append(f"- {c}")
        lines.append("")

    if spatial_context.policy_zones:
        lines.append("### Policy Zones Affecting This Site")
        lines.append("")
        for zone in spatial_context.policy_zones:
            lines.append(f"- {zone}")
        lines.append("")

    if spatial_context.spatial_policy_implications:
        lines.append("### How Location Affects Policy Interpretation")
        lines.append("")
        for impl in spatial_context.spatial_policy_implications:
            lines.append(f"**{impl['policy']}:** {impl['implication']}")
            lines.append(f"- *{impl['reasoning']}*")
            lines.append("")

    if spatial_context.incomplete_spatial_info:
        lines.append("### ⚠️ Incomplete Spatial Information")
        lines.append("")
        for info in spatial_context.incomplete_spatial_info:
            lines.append(f"- {info}")
        lines.append("")

    # Policy framework
    lines.append("## RELEVANT PLANNING POLICY")
    lines.append("")
    lines.append("### Development Plan")
    lines.append("")
    lines.append("**Greater Nottingham Aligned Core Strategy (2014)**")
    lines.append("")
    acs_policies = [p for p in policies if p.source == "ACS"]
    for p in acs_policies[:4]:
        lines.append(f"- **{p.id}** - {p.name}")
        lines.append(f"  - *This policy applies because: {p.text[:100]}...*")
    lines.append("")
    lines.append("**Broxtowe Part 2 Local Plan (2019)**")
    lines.append("")
    part2_policies = [p for p in policies if p.source == "Part2"]
    for p in part2_policies[:4]:
        lines.append(f"- **{p.id}** - {p.name}")
        lines.append(f"  - *This policy applies because: {p.text[:100]}...*")
    lines.append("")
    lines.append("### National Planning Policy Framework (2023)")
    lines.append("")
    lines.append("- Chapters 12 (Design), 13 (Green Belt), 16 (Heritage) as relevant")
    lines.append("")

    # Similar cases with explicit reasoning
    if similar_cases:
        lines.append("## RELEVANT PLANNING HISTORY / PRECEDENT")
        lines.append("")
        lines.append(f"**Precedent strength:** {precedent_analysis['precedent_strength'].replace('_', ' ').title()}")
        lines.append(f"**Approval rate:** {precedent_analysis['approval_rate']:.0%} ({precedent_analysis['approved']}/{precedent_analysis['total_cases']})")
        lines.append("")

        for case in similar_cases[:3]:
            lines.append(f"### {case['reference']}")
            lines.append(f"**Address:** {case['address']}")
            lines.append(f"**Proposal:** {case['proposal'][:100]}...")
            lines.append(f"**Decision:** {case['decision']}")
            lines.append(f"**Similarity:** {case['similarity_score']:.0%}")
            lines.append("")
            lines.append(f"*This proposal is similar to {case['reference']} because: Both involve {application_type.lower()} development in similar area context.*")
            lines.append("")
            lines.append("**Key differences to consider:**")
            lines.append("- Site-specific factors may differ")
            lines.append("- Policy context may have changed since decision")
            lines.append("")
    else:
        lines.append("## RELEVANT PLANNING HISTORY / PRECEDENT")
        lines.append("")
        lines.append("**⚠️ Limited Comparable Cases**")
        lines.append("")
        lines.append("No closely comparable cases found in the database. This assessment relies more heavily on policy interpretation. Officer judgement is particularly important in the absence of clear precedent.")
        lines.append("")

    # Assessment
    lines.append("## ASSESSMENT")
    lines.append("")

    if heritage_assessment:
        lines.append("### Heritage Impact Assessment")
        lines.append("")
        lines.append(f"**Asset:** {heritage_assessment.asset_type}{f' (Grade {heritage_assessment.asset_grade})' if heritage_assessment.asset_grade else ''}")
        lines.append(f"**Confidence:** {heritage_assessment.confidence.value}")
        lines.append("")
        lines.append(f"**Significance:** {heritage_assessment.significance}")
        lines.append("")
        lines.append(f"**Impact Assessment:** {heritage_assessment.impact_on_significance}")
        lines.append("")
        lines.append(f"**Harm Level:** {heritage_assessment.harm_level.value.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Policy Basis:** {heritage_assessment.justification}")
        lines.append("")
        if heritage_assessment.limitations:
            lines.append("**Assessment Limitations:**")
            for lim in heritage_assessment.limitations:
                lines.append(f"- {lim}")
            lines.append("")

    lines.append("### Residential Amenity Assessment")
    lines.append("")
    if amenity_assessments:
        for a in amenity_assessments:
            lines.append(f"**{a.impact_type.replace('_', ' ').title()}**")
            lines.append(f"- Impact Level: {a.impact_level.value.replace('_', ' ').title()}")
            lines.append(f"- Confidence: {a.confidence.value}")
            lines.append(f"- Assessment: {a.proposed_impact}")
            if a.assessment_limitations:
                lines.append(f"- *Limitation: {a.assessment_limitations}*")
            if a.requires_site_visit:
                lines.append(f"- **Site visit recommended to verify this assessment**")
            lines.append("")
    else:
        lines.append("No unacceptable amenity impacts identified based on available information.")
        lines.append("")
        lines.append("*Note: Amenity assessment is limited by lack of site-specific information. Site visit may reveal additional considerations.*")
        lines.append("")

    # Planning balance
    lines.append("## PLANNING BALANCE")
    lines.append("")
    lines.append(planning_balance.overall_narrative)
    lines.append("")

    if planning_balance.para_202_balance:
        lines.append(planning_balance.para_202_balance)
        lines.append("")

    # Post-Consent Considerations
    if outcome_awareness.post_consent_risks:
        lines.append("## POST-CONSENT CONSIDERATIONS")
        lines.append("")
        lines.append("*Beyond policy compliance, the following outcomes should be considered:*")
        lines.append("")
        for risk in outcome_awareness.post_consent_risks:
            lines.append(f"### {risk.risk_type.title()} Risk")
            lines.append(f"- **Description:** {risk.description}")
            lines.append(f"- **Likelihood:** {risk.likelihood}")
            lines.append(f"- **Evidence:** {risk.evidence_basis}")
            lines.append(f"- **Suggested mitigation:** {risk.suggested_mitigation}")
            if risk.monitoring_recommended:
                lines.append(f"- **Monitoring recommended**")
            lines.append("")

        if outcome_awareness.delivery_concerns:
            lines.append("### Delivery Concerns")
            for concern in outcome_awareness.delivery_concerns:
                lines.append(f"- *{concern}*")
            lines.append("")

        lines.append(f"**Uncertainty:** {outcome_awareness.uncertainty_statement}")
        lines.append("")

    # Uncertainty Disclosure
    lines.append("## LIMITATIONS AND UNCERTAINTY DISCLOSURE")
    lines.append("")
    lines.append("*This assessment should be treated with appropriate caution due to the following:*")
    lines.append("")

    lines.append("### Data Limitations")
    for lim in uncertainty_disclosure.data_limitations:
        lines.append(f"- {lim}")
    lines.append("")

    lines.append("### Potential Sources of Bias")
    for bias in uncertainty_disclosure.potential_biases:
        lines.append(f"- {bias}")
    lines.append("")

    if uncertainty_disclosure.incomplete_information:
        lines.append("### Incomplete Information")
        for info in uncertainty_disclosure.incomplete_information:
            lines.append(f"- {info}")
        lines.append("")

    lines.append("### Areas Requiring Officer Judgement")
    for area in uncertainty_disclosure.areas_requiring_officer_judgement:
        lines.append(f"- {area}")
    lines.append("")

    # Recommendation
    lines.append("## RECOMMENDATION")
    lines.append("")
    lines.append(f"**{recommendation.replace('_', ' ')}**")
    lines.append("")
    lines.append(f"**Confidence:** {confidence_assessment.level.value.upper()} ({confidence_assessment.score:.0%})")
    lines.append("")
    lines.append(f"*{confidence_assessment.reasoning}*")
    lines.append("")

    if recommendation == "REFUSE":
        lines.append("### Reasons for Refusal")
        lines.append("")
        for r in refusal_reasons:
            lines.append(f"**{r['number']}.** {r['reason']}")
            lines.append("")
    else:
        lines.append("### Conditions")
        lines.append("")
        for c in conditions:
            lines.append(f"**{c.number}. {c.title}**")
            lines.append("")
            lines.append(c.full_wording)
            lines.append("")
            lines.append(f"*Reason: {c.reason}*")
            if c.precedent_source:
                lines.append(f"*Precedent: {c.precedent_source}*")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## STATEMENT OF PROFESSIONAL RESPECT")
    lines.append("")
    lines.append("This report is provided to inform and support professional planning judgement.")
    lines.append("The planning officer is the decision-maker. This AI system:")
    lines.append("")
    lines.append("- Surfaces issues for consideration")
    lines.append("- Cites relevant policy and precedent")
    lines.append("- Identifies areas of uncertainty")
    lines.append("- Does **not** make the final decision")
    lines.append("")
    lines.append("The assessment may be scrutinised at planning appeal, committee, or legal challenge.")
    lines.append("All conclusions should be verified against current policy and site conditions.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Plana.AI - Broxtowe Module v2.0*")
    lines.append(f"*Confidence: {confidence_assessment.level.value.upper()} ({confidence_assessment.score:.0%})*")
    lines.append(f"*Generated: {datetime.now().isoformat()}*")

    return "\n".join(lines)
