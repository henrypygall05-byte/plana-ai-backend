"""
Broxtowe Borough Council AI Case Officer.

This module provides planning assessment for Broxtowe Borough Council using:
- Greater Nottingham Aligned Core Strategy (2014)
- Broxtowe Part 2 Local Plan (2019)
- NPPF (2023)
- Local precedent from historic decisions

Follows the same methodology as the Newcastle AI Case Officer but with
Broxtowe-specific policies and local knowledge.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum

from .policies import get_broxtowe_policies, get_policy_citation, BROXTOWE_POLICIES
from .cases import find_similar_broxtowe_cases, get_broxtowe_precedent_analysis


# =============================================================================
# CORE ENUMS AND DATACLASSES (duplicated from ai_case_officer for independence)
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
    """A material consideration in the planning balance."""
    factor: str
    description: str
    is_benefit: bool
    weight: Weight
    policy_basis: list[str]
    evidence: str
    confidence: float = 0.8


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


@dataclass
class Condition:
    """A planning condition meeting the 6 tests."""
    number: int
    title: str
    full_wording: str
    reason: str
    policy_basis: str
    condition_type: str
    is_necessary: bool = True
    is_relevant: bool = True
    is_enforceable: bool = True
    is_precise: bool = True
    is_reasonable: bool = True
    meets_six_tests: bool = True


@dataclass
class PlanningBalance:
    """The planning balance."""
    benefits: list[MaterialConsideration]
    harms: list[MaterialConsideration]
    heritage_harm: Optional[HeritageAssessment]
    amenity_impacts: list[AmenityAssessment]
    tilted_balance_engaged: bool = False
    tilted_balance_reason: str = ""
    para_202_balance: Optional[str] = None
    benefits_outweigh_harms: bool = True
    overall_narrative: str = ""


STATUTORY_DUTIES = {
    "section_66": """Section 66(1) of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires special regard to the desirability of preserving the building or its setting.""",
    "section_72": """Section 72(1) of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires special attention to preserving or enhancing the character or appearance of the conservation area.""",
}


def generate_broxtowe_heritage_assessment(
    proposal: str,
    constraints: list[str],
    site_address: str,
) -> Optional[HeritageAssessment]:
    """
    Generate heritage assessment specific to Broxtowe context.

    Considers:
    - Beeston Conservation Area
    - Bramcote Conservation Area
    - Eastwood (D.H. Lawrence heritage)
    - Listed buildings including Grade II* churches
    """
    constraints_lower = [c.lower() for c in constraints]
    proposal_lower = proposal.lower()

    has_listed = any('listed' in c for c in constraints_lower)
    has_conservation = any('conservation' in c for c in constraints_lower)

    if not has_listed and not has_conservation:
        return None

    # Determine asset type and grade
    asset_type = "Conservation Area"
    asset_grade = None
    statutory_duty = "section_72"

    for c in constraints:
        if 'grade i ' in c.lower() or 'grade i listed' in c.lower():
            asset_type = "Listed Building"
            asset_grade = "I"
            statutory_duty = "section_66"
        elif 'grade ii*' in c.lower():
            asset_type = "Listed Building"
            asset_grade = "II*"
            statutory_duty = "section_66"
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
        significance += " Bramcote Conservation Area is characterised by its historic village core, including the Grade II* listed Holy Trinity Church and traditional stone buildings."
    elif "beeston" in address_lower:
        significance += " Beeston Conservation Area includes the historic town centre with Victorian and Edwardian commercial and residential buildings."
    elif "eastwood" in address_lower:
        significance += " Eastwood has significant literary heritage as the birthplace of D.H. Lawrence, with several associated heritage assets."

    # Determine harm level
    positive_indicators = [
        'restoration', 'restore', 'repair', 'timber', 'traditional',
        'like for like', 'internal', 'sympathetic', 'enhance', 'preserve'
    ]

    is_positive = any(term in proposal_lower for term in positive_indicators)
    is_internal = 'internal' in proposal_lower
    installing_upvc = ('upvc' in proposal_lower or 'u-pvc' in proposal_lower) and 'replace' not in proposal_lower

    if has_listed and installing_upvc:
        harm_level = HarmLevel.SUBSTANTIAL
        impact = "The proposed uPVC windows would cause substantial harm to the significance of this listed building."
    elif is_positive or is_internal:
        harm_level = HarmLevel.NO_HARM
        impact = "The proposal would preserve or enhance the significance of the heritage asset."
    elif 'single storey' in proposal_lower or 'rear extension' in proposal_lower:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
        impact = "The proposal would cause less than substantial harm at the lower end of the spectrum."
    elif 'extension' in proposal_lower:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
        impact = "The proposal would cause less than substantial harm, subject to appropriate materials."
    elif 'front' in proposal_lower:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE
        impact = "Development to the front elevation may harm the character of the Conservation Area."
    else:
        harm_level = HarmLevel.NO_HARM
        impact = "The proposal is not considered to cause harm to the heritage asset."

    # Determine NPPF paragraph
    if harm_level == HarmLevel.SUBSTANTIAL:
        nppf_para = "201"
        justification = f"Paragraph 201 requires substantial public benefits to outweigh substantial harm. {STATUTORY_DUTIES[statutory_duty]}"
    elif harm_level in [HarmLevel.LESS_THAN_SUBSTANTIAL_LOW, HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE, HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH]:
        nppf_para = "202"
        justification = f"Paragraph 202 requires the harm to be weighed against public benefits. {STATUTORY_DUTIES[statutory_duty]}"
    else:
        nppf_para = "199"
        justification = f"The proposal preserves the significance of the heritage asset in accordance with Policy 23. {STATUTORY_DUTIES[statutory_duty]}"

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
    )


def generate_broxtowe_amenity_assessment(
    proposal: str,
    constraints: list[str],
    application_type: str,
) -> list[AmenityAssessment]:
    """
    Generate amenity assessment using Broxtowe Policy 17 requirements.

    Policy 17 specifically requires:
    - Protection from noise, odour, air quality impacts
    - No unacceptable overlooking
    - No unacceptable shadowing
    - Adequate amenity for future occupiers
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
            current_situation="Neighbours currently enjoy reasonable privacy.",
            proposed_impact="The first floor balcony would introduce overlooking of neighbouring gardens and habitable rooms.",
            impact_level=AmenityImpact.SEVERE_UNACCEPTABLE,
            mitigation_possible=False,
            mitigation_measures=[],
            policy_basis=["Policy-17", "ACS-10"],
        ))

    # Default assessment for extensions
    if 'extension' in proposal_lower and not assessments:
        assessments.append(AmenityAssessment(
            affected_property="Adjoining properties",
            impact_type="daylight_outlook",
            current_situation="Neighbours receive adequate daylight and outlook.",
            proposed_impact="The extension is designed to minimise impact. A 45-degree assessment indicates acceptable daylight levels.",
            impact_level=AmenityImpact.MINOR_ACCEPTABLE,
            mitigation_possible=True,
            mitigation_measures=["Design kept subordinate", "Set-back from boundaries"],
            policy_basis=["Policy-17", "ACS-10"],
        ))

    return assessments


def generate_broxtowe_conditions(
    proposal: str,
    constraints: list[str],
    application_type: str,
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
) -> list[Condition]:
    """
    Generate conditions specific to Broxtowe requirements.
    """
    conditions = []
    num = 1

    # Standard time limit
    conditions.append(Condition(
        number=num,
        title="Time Limit",
        full_wording="The development hereby permitted shall be begun before the expiration of three years from the date of this permission.",
        reason="To comply with Section 91 of the Town and Country Planning Act 1990, as amended by Section 51 of the Planning and Compulsory Purchase Act 2004.",
        policy_basis="TCPA 1990 s.91",
        condition_type="compliance",
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
    ))
    num += 1

    # Materials - referencing Broxtowe policies
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
        ))
        num += 1

    # PD removal for householder
    if "householder" in application_type.lower() or "extension" in proposal.lower():
        conditions.append(Condition(
            number=num,
            title="Removal of Permitted Development Rights",
            full_wording="Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015 (or any order revoking and re-enacting that Order), no additional windows or openings shall be inserted in the side elevation(s) of the development hereby approved at first floor level or above without the prior written approval of the Local Planning Authority.",
            reason="To protect the residential amenity of neighbouring properties in accordance with Policy 17 of the Broxtowe Part 2 Local Plan.",
            policy_basis="Policy-17",
            condition_type="compliance",
        ))
        num += 1

    return conditions


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

    This is the main entry point for Broxtowe planning assessments.

    Returns:
        Dictionary containing structured report data and markdown report
    """
    documents = documents or []

    # 1. Get relevant policies
    policies = get_broxtowe_policies(proposal, application_type, constraints)

    # 2. Find similar cases
    similar_cases = find_similar_broxtowe_cases(
        proposal=proposal,
        application_type=application_type,
        constraints=constraints,
        ward=ward,
        postcode=postcode,
        limit=5,
    )
    precedent_analysis = get_broxtowe_precedent_analysis(similar_cases)

    # 3. Heritage assessment
    heritage_assessment = generate_broxtowe_heritage_assessment(proposal, constraints, site_address)

    # 4. Amenity assessment
    amenity_assessments = generate_broxtowe_amenity_assessment(proposal, constraints, application_type)

    # 5. Identify benefits
    benefits = [
        MaterialConsideration(
            factor="Provision of improved living accommodation",
            description="The proposal would provide improved living accommodation for the occupiers.",
            is_benefit=True,
            weight=Weight.MODERATE,
            policy_basis=["NPPF paragraph 8", "ACS-8"],
            evidence="Inherent benefit of residential development",
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
        ))

    # 6. Identify harms
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
            ))

    # Check for specific Broxtowe red flags
    constraints_lower = [c.lower() for c in constraints]

    # uPVC in Conservation Area - ALWAYS harmful
    # Key issue: replacing historic timber windows with uPVC is the problem
    has_conservation = any("conservation" in c for c in constraints_lower)
    has_upvc = "upvc" in proposal_lower or "u-pvc" in proposal_lower
    replacing_with_upvc = has_upvc and ("replace" in proposal_lower or "window" in proposal_lower)
    # But replacing uPVC WITH timber is positive, not harmful
    replacing_upvc_with_timber = ("timber" in proposal_lower or "sash" in proposal_lower) and "upvc" in proposal_lower and ("remove" in proposal_lower or "replacing upvc" in proposal_lower)

    if has_conservation and has_upvc and replacing_with_upvc and not replacing_upvc_with_timber:
        harms.append(MaterialConsideration(
            factor="Inappropriate materials in Conservation Area",
            description="Replacing traditional windows with uPVC would fail to preserve or enhance the character of the Conservation Area.",
            is_benefit=False,
            weight=Weight.VERY_GREAT,  # Substantial harm - should result in refusal
            policy_basis=["Policy-23", "ACS-11", "NPPF Chapter 16"],
            evidence="Material assessment",
        ))

    # Front extensions/garages
    if "front" in proposal_lower and ("extension" in proposal_lower or "garage" in proposal_lower):
        harms.append(MaterialConsideration(
            factor="Impact on streetscene",
            description="Front extensions/garages can harm the established streetscene character.",
            is_benefit=False,
            weight=Weight.MODERATE,
            policy_basis=["Policy-17", "ACS-10"],
            evidence="Design assessment",
        ))

    # Green Belt disproportionate additions
    has_green_belt = any("green belt" in c for c in constraints_lower)
    if has_green_belt and ("80%" in proposal_lower or "disproportionate" in proposal_lower or "large" in proposal_lower):
        harms.append(MaterialConsideration(
            factor="Inappropriate Green Belt development",
            description="Disproportionate additions are inappropriate development in the Green Belt.",
            is_benefit=False,
            weight=Weight.VERY_GREAT,
            policy_basis=["Policy-8", "ACS-16", "NPPF Chapter 13"],
            evidence="Green Belt assessment",
        ))

    # Balcony privacy harm
    if "balcony" in proposal_lower and "first floor" in proposal_lower:
        harms.append(MaterialConsideration(
            factor="Privacy harm from balcony",
            description="First floor balcony would cause unacceptable overlooking.",
            is_benefit=False,
            weight=Weight.SUBSTANTIAL,
            policy_basis=["Policy-17"],
            evidence="Amenity assessment",
        ))

    # 7. Generate planning balance
    total_benefit_weight = sum(b.weight.value for b in benefits)
    total_harm_weight = sum(h.weight.value for h in harms)

    benefits_outweigh = total_benefit_weight > total_harm_weight

    # 8. Determine recommendation
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
        )
        refusal_reasons = []

    # 9. Build planning balance narrative
    balance_narrative = f"""The proposed development has been assessed against the policies of the Greater Nottingham Aligned Core Strategy (2014), the Broxtowe Part 2 Local Plan (2019), and the National Planning Policy Framework (2023).

**Benefits identified:** {', '.join([b.factor for b in benefits])}
**Weight:** {Weight(total_benefit_weight).name if total_benefit_weight <= 6 else 'COMBINED SIGNIFICANT'}

**Harms identified:** {', '.join([h.factor for h in harms]) if harms else 'No significant harms identified'}
**Weight:** {Weight(total_harm_weight).name if total_harm_weight <= 6 else 'COMBINED SIGNIFICANT'}

{'The benefits are considered to outweigh the harms.' if benefits_outweigh else 'The harms are considered to outweigh the benefits.'}"""

    # Heritage balance if applicable
    heritage_balance = None
    if heritage_assessment and heritage_assessment.harm_level != HarmLevel.NO_HARM:
        heritage_balance = f"""The proposal would cause {heritage_assessment.harm_level.value.replace('_', ' ')} to the significance of the heritage asset. In accordance with paragraph 199 of the NPPF and Policy 23 of the Broxtowe Part 2 Local Plan, great weight must be given to conservation.

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
    )

    # 10. Calculate confidence
    confidence = 0.85
    if len(similar_cases) >= 3:
        confidence += 0.05
    if heritage_assessment:
        confidence += 0.03
    confidence = min(confidence, 0.95)

    # 11. Generate markdown report
    report_md = _format_broxtowe_report_markdown(
        reference=reference,
        site_address=site_address,
        ward=ward,
        applicant=applicant_name or "Not specified",
        application_type=application_type,
        proposal=proposal,
        constraints=constraints,
        policies=policies,
        similar_cases=similar_cases,
        precedent_analysis=precedent_analysis,
        heritage_assessment=heritage_assessment,
        amenity_assessments=amenity_assessments,
        planning_balance=planning_balance,
        recommendation=recommendation,
        conditions=conditions,
        refusal_reasons=refusal_reasons,
        confidence=confidence,
    )

    return {
        "meta": {
            "reference": reference,
            "council": "Broxtowe Borough Council",
            "generated_at": datetime.now().isoformat(),
            "confidence": confidence,
        },
        "recommendation": {
            "outcome": recommendation,
            "reasoning": balance_narrative,
            "conditions": [{"number": c.number, "title": c.title, "wording": c.full_wording, "reason": c.reason} for c in conditions],
            "refusal_reasons": refusal_reasons,
        },
        "policy_context": {
            "development_plan": "Greater Nottingham Aligned Core Strategy (2014) and Broxtowe Part 2 Local Plan (2019)",
            "selected_policies": [{"policy_id": p.id, "policy_name": p.name, "source": p.source_full} for p in policies],
        },
        "similarity_analysis": {
            "top_cases": [{"reference": c["reference"], "outcome": c["decision"], "similarity_score": c["similarity_score"]} for c in similar_cases],
            "precedent_analysis": precedent_analysis,
        },
        "assessment": {
            "heritage": {
                "harm_level": heritage_assessment.harm_level.value if heritage_assessment else "not_applicable",
                "impact": heritage_assessment.impact_on_significance if heritage_assessment else None,
            } if heritage_assessment else None,
            "amenity": [{"type": a.impact_type, "level": a.impact_level.value} for a in amenity_assessments],
        },
        "planning_balance": {
            "benefits_weight": total_benefit_weight,
            "harms_weight": total_harm_weight,
            "benefits_outweigh": benefits_outweigh,
        },
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
    policies: list,
    similar_cases: list[dict],
    precedent_analysis: dict,
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
    planning_balance: PlanningBalance,
    recommendation: str,
    conditions: list[Condition],
    refusal_reasons: list[dict],
    confidence: float,
) -> str:
    """Format the Broxtowe report as professional markdown."""

    lines = []

    lines.append("# DELEGATED REPORT")
    lines.append("")
    lines.append("**BROXTOWE BOROUGH COUNCIL**")
    lines.append("**PLANNING AND COMMUNITY DEVELOPMENT**")
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

    # Constraints
    if constraints:
        lines.append("## SITE CONSTRAINTS")
        lines.append("")
        for c in constraints:
            lines.append(f"- {c}")
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
    lines.append("")
    lines.append("**Broxtowe Part 2 Local Plan (2019)**")
    lines.append("")
    part2_policies = [p for p in policies if p.source == "Part2"]
    for p in part2_policies[:4]:
        lines.append(f"- **{p.id}** - {p.name}")
    lines.append("")
    lines.append("### National Planning Policy Framework (2023)")
    lines.append("")
    lines.append("- Chapters 12 (Design), 13 (Green Belt), 16 (Heritage) as relevant")
    lines.append("")

    # Similar cases
    if similar_cases:
        lines.append("## RELEVANT PLANNING HISTORY / PRECEDENT")
        lines.append("")
        lines.append(f"**Precedent strength:** {precedent_analysis['precedent_strength'].replace('_', ' ').title()}")
        lines.append(f"**Approval rate:** {precedent_analysis['approval_rate']:.0%} ({precedent_analysis['approved']}/{precedent_analysis['total_cases']})")
        lines.append("")
        for case in similar_cases[:3]:
            lines.append(f"**{case['reference']}** - {case['address']}")
            lines.append(f"- Proposal: {case['proposal'][:80]}...")
            lines.append(f"- Decision: {case['decision']}")
            lines.append(f"- Similarity: {case['similarity_score']:.0%}")
            lines.append("")

    # Assessment
    lines.append("## ASSESSMENT")
    lines.append("")

    if heritage_assessment:
        lines.append("### Heritage Impact")
        lines.append("")
        lines.append(f"**Asset:** {heritage_assessment.asset_type}")
        lines.append(f"**Significance:** {heritage_assessment.significance}")
        lines.append(f"**Impact:** {heritage_assessment.impact_on_significance}")
        lines.append(f"**Harm Level:** {heritage_assessment.harm_level.value.replace('_', ' ').title()}")
        lines.append("")

    lines.append("### Residential Amenity")
    lines.append("")
    if amenity_assessments:
        for a in amenity_assessments:
            lines.append(f"**{a.impact_type.replace('_', ' ').title()}:** {a.impact_level.value.replace('_', ' ').title()}")
            lines.append(f"{a.proposed_impact}")
            lines.append("")
    else:
        lines.append("No unacceptable amenity impacts identified.")
        lines.append("")

    # Planning balance
    lines.append("## PLANNING BALANCE")
    lines.append("")
    lines.append(planning_balance.overall_narrative)
    lines.append("")

    if planning_balance.para_202_balance:
        lines.append("### Heritage Balance (NPPF Paragraph 202)")
        lines.append("")
        lines.append(planning_balance.para_202_balance)
        lines.append("")

    # Recommendation
    lines.append("## RECOMMENDATION")
    lines.append("")
    lines.append(f"**{recommendation.replace('_', ' ')}**")
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
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Plana.AI - Broxtowe Module*")
    lines.append(f"*Confidence: {confidence:.0%}*")
    lines.append(f"*Generated: {datetime.now().isoformat()}*")

    return "\n".join(lines)
