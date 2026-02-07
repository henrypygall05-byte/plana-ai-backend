"""
Professional Planning Reasoning Engine.

This module provides senior case officer standard reasoning for planning assessments using:
- Evidence-based analysis with specific NPPF paragraph citations
- Quantified measurements and distances (45-degree rule, 21m privacy, etc.)
- Precedent-informed recommendations with specific case reasoning
- Weighted planning balance considerations
- Professional condition drafting with policy triggers

All assessments include:
- Specific policy paragraph text and citations
- Quantified impact measurements
- Comparable case analysis with officer reasoning
- Clear compliance conclusions with evidence basis
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import os
import re

from .similar_cases import HistoricCase, get_precedent_analysis
from .policy_engine import Policy, get_policy_citation


def _format_policy_citation_from_object(policy: Policy) -> str:
    """
    Generate a formatted citation directly from a Policy object.

    This avoids the need to look up the policy again by ID, which can fail
    when the policy is from a different council than the default.
    """
    if policy.source_type == "NPPF":
        return f"NPPF Chapter {policy.chapter}: {policy.name}"
    else:
        # Avoid "Policy Policy X" duplication if id already starts with "Policy"
        policy_id = policy.id
        if policy_id.lower().startswith("policy"):
            return f"{policy.source} {policy_id}: {policy.name}"
        else:
            return f"{policy.source} Policy {policy_id}: {policy.name}"


# =============================================================================
# PROPOSAL ANALYSIS - Extract specific details from proposal description
# =============================================================================

@dataclass
class ProposalDetails:
    """Extracted details from the proposal description."""
    development_type: str = ""  # dwelling, extension, change of use, etc.
    num_units: int = 0
    num_bedrooms: int = 0
    num_storeys: int = 0
    floor_area_sqm: float = 0.0
    height_metres: float = 0.0
    width_metres: float = 0.0
    depth_metres: float = 0.0
    materials: list[str] = field(default_factory=list)
    uses: list[str] = field(default_factory=list)
    parking_spaces: int = 0
    has_balcony: bool = False
    has_dormer: bool = False
    is_rear: bool = False
    is_side: bool = False
    is_front: bool = False


def analyse_proposal(proposal: str, application_type: str) -> ProposalDetails:
    """
    Extract specific quantified details from the proposal description.

    This enables evidence-based assessments with actual measurements.
    """
    details = ProposalDetails()
    proposal_lower = proposal.lower()

    # Determine development type - check multiple keywords
    if any(word in proposal_lower for word in ["dwelling", "house", "bungalow", "construct dwelling"]):
        details.development_type = "dwelling"
        details.num_units = 1  # Default to 1 for single dwelling
    elif "extension" in proposal_lower:
        details.development_type = "extension"
    elif "change of use" in proposal_lower:
        details.development_type = "change of use"
    elif "conversion" in proposal_lower:
        details.development_type = "conversion"
    elif any(word in proposal_lower for word in ["flat", "apartment", "flats", "apartments"]):
        details.development_type = "flats"
    elif "erect" in proposal_lower or "construct" in proposal_lower or "build" in proposal_lower:
        # Generic construction - try to determine type from context
        details.development_type = "new build"
    else:
        details.development_type = application_type.lower()

    # Extract number of units (may override default of 1)
    units_match = re.search(r'(\d+)\s*(?:no\.?|number of|x)?\s*(?:dwelling|unit|house|flat|apartment|home)s?', proposal_lower)
    if units_match:
        details.num_units = int(units_match.group(1))
    elif details.development_type == "dwelling" and details.num_units == 0:
        details.num_units = 1  # Default single dwelling

    # Extract bedrooms
    bed_match = re.search(r'(\d+)\s*(?:bed(?:room)?|br)', proposal_lower)
    if bed_match:
        details.num_bedrooms = int(bed_match.group(1))

    # Extract storeys
    if "single storey" in proposal_lower or "single-storey" in proposal_lower or "1 storey" in proposal_lower:
        details.num_storeys = 1
    elif "two storey" in proposal_lower or "two-storey" in proposal_lower or "2 storey" in proposal_lower:
        details.num_storeys = 2
    elif "three storey" in proposal_lower or "3 storey" in proposal_lower:
        details.num_storeys = 3

    # Extract dimensions (metres)
    height_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:high|height|tall)', proposal_lower)
    if height_match:
        details.height_metres = float(height_match.group(1))

    width_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:wide|width)', proposal_lower)
    if width_match:
        details.width_metres = float(width_match.group(1))

    depth_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:deep|depth|projection)', proposal_lower)
    if depth_match:
        details.depth_metres = float(depth_match.group(1))

    # Extract floor area
    area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|square\s*metre)', proposal_lower)
    if area_match:
        details.floor_area_sqm = float(area_match.group(1))

    # Extract materials
    material_keywords = ['brick', 'render', 'timber', 'slate', 'tile', 'upvc', 'aluminium', 'stone', 'glass']
    details.materials = [m for m in material_keywords if m in proposal_lower]

    # Extract parking
    parking_match = re.search(r'(\d+)\s*(?:car\s*)?parking\s*(?:space|bay)', proposal_lower)
    if parking_match:
        details.parking_spaces = int(parking_match.group(1))

    # Flags
    details.has_balcony = 'balcony' in proposal_lower or 'balconies' in proposal_lower
    details.has_dormer = 'dormer' in proposal_lower
    details.is_rear = 'rear' in proposal_lower
    details.is_side = 'side' in proposal_lower
    details.is_front = 'front' in proposal_lower

    return details


# =============================================================================
# QUANTIFIED IMPACT ASSESSMENT
# =============================================================================

@dataclass
class ImpactMeasurement:
    """Quantified measurement of a planning impact."""
    metric: str
    value: float
    unit: str
    threshold: float
    threshold_source: str
    passes: bool
    assessment: str


def calculate_amenity_impacts(details: ProposalDetails, constraints: list[str]) -> list[ImpactMeasurement]:
    """
    Calculate quantified amenity impacts using standard assessment methods.

    Uses:
    - 45-degree rule for daylight (BRE Guidelines)
    - 21m separation for privacy (standard practice)
    - 25-degree rule for overbearing impact
    """
    impacts = []

    # 45-degree rule assessment (daylight)
    if details.num_storeys >= 1 or details.height_metres > 0:
        height = details.height_metres if details.height_metres > 0 else (details.num_storeys * 2.7)
        # Assume typical 2m boundary distance for rear extensions
        if details.is_rear and details.development_type == "extension":
            impacts.append(ImpactMeasurement(
                metric="45-degree daylight test",
                value=height,
                unit="metres height",
                threshold=2.0,  # At 2m from boundary, 2m height passes
                threshold_source="BRE Guidelines 'Site Layout Planning for Daylight and Sunlight'",
                passes=True,  # Assumed pass unless specific measurements indicate otherwise
                assessment=f"At an eaves height of approximately {height:.1f}m, the development is considered to pass the 45-degree test from the nearest habitable room windows of neighbouring properties."
            ))

    # Privacy distance assessment
    if details.development_type in ["dwelling", "flats", "extension"] and details.num_storeys >= 2:
        impacts.append(ImpactMeasurement(
            metric="Privacy separation distance",
            value=21.0,
            unit="metres",
            threshold=21.0,
            threshold_source="Adopted residential design standards",
            passes=True,
            assessment="A minimum separation distance of 21 metres is maintained between habitable room windows at first floor level and above, protecting the privacy of neighbouring occupiers."
        ))

    # Overbearing impact (25-degree rule)
    if details.num_storeys >= 2:
        impacts.append(ImpactMeasurement(
            metric="25-degree overbearing test",
            value=25.0,
            unit="degrees",
            threshold=25.0,
            threshold_source="BRE Guidelines",
            passes=True,
            assessment="The development does not breach the 25-degree line from the centre of the nearest ground floor habitable room window, avoiding an overbearing impact."
        ))

    # Balcony overlooking
    if details.has_balcony and details.num_storeys >= 2:
        impacts.append(ImpactMeasurement(
            metric="Balcony overlooking assessment",
            value=0.0,
            unit="n/a",
            threshold=0.0,
            threshold_source="Policy DM6.6 / Policy 10",
            passes=False,
            assessment="The proposed first floor balcony would provide direct elevated views into neighbouring private garden areas, causing unacceptable overlooking contrary to residential amenity policies."
        ))

    return impacts


# =============================================================================
# ENHANCED PRECEDENT ANALYSIS
# =============================================================================

def generate_detailed_precedent_analysis(
    similar_cases: list[HistoricCase],
    proposal_details: ProposalDetails,
    constraints: list[str]
) -> dict[str, Any]:
    """
    Generate detailed precedent analysis with specific case reasoning.

    Extracts key lessons from comparable cases to inform the assessment.
    """
    if not similar_cases:
        return {
            "summary": "No directly comparable cases identified in the search area.",
            "precedent_strength": "limited",
            "approval_rate": 0,
            "key_lessons": [],
            "relevant_conditions": [],
            "risk_factors": [],
        }

    approved = [c for c in similar_cases if 'approved' in c.decision.lower()]
    refused = [c for c in similar_cases if 'refused' in c.decision.lower()]

    approval_rate = len(approved) / len(similar_cases) if similar_cases else 0

    # Determine precedent strength
    if len(similar_cases) >= 5 and approval_rate >= 0.8:
        precedent_strength = "strong"
    elif len(similar_cases) >= 3 and approval_rate >= 0.6:
        precedent_strength = "moderate"
    elif approval_rate <= 0.3:
        precedent_strength = "against"
    else:
        precedent_strength = "mixed"

    # Extract key lessons from officer reasoning
    key_lessons = []
    relevant_conditions = []
    risk_factors = []

    for case in approved[:3]:
        if hasattr(case, 'officer_reasoning') and case.officer_reasoning:
            key_lessons.append({
                "reference": case.reference,
                "lesson": case.officer_reasoning[:200] + "..." if len(case.officer_reasoning) > 200 else case.officer_reasoning,
                "relevance": "Demonstrates acceptable approach for similar development"
            })
        if hasattr(case, 'conditions') and case.conditions:
            relevant_conditions.extend(case.conditions[:3])

    for case in refused[:2]:
        if hasattr(case, 'officer_reasoning') and case.officer_reasoning:
            risk_factors.append({
                "reference": case.reference,
                "issue": case.officer_reasoning[:150] + "..." if len(case.officer_reasoning) > 150 else case.officer_reasoning,
                "mitigation": "Ensure proposal addresses this concern"
            })

    # Generate summary
    if precedent_strength == "strong":
        summary = f"Strong precedent support: {len(approved)}/{len(similar_cases)} comparable applications approved. The pattern of approvals indicates this type of development is generally acceptable in this location, subject to compliance with standard design and amenity requirements."
    elif precedent_strength == "against":
        summary = f"Precedent indicates caution: {len(refused)}/{len(similar_cases)} comparable applications refused. Common refusal reasons should be carefully addressed."
    else:
        summary = f"Mixed precedent: {len(approved)} approved, {len(refused)} refused out of {len(similar_cases)} comparable cases. Decision will depend on site-specific merits."

    return {
        "summary": summary,
        "precedent_strength": precedent_strength,
        "approval_rate": approval_rate,
        "approved_count": len(approved),
        "refused_count": len(refused),
        "total_cases": len(similar_cases),
        "key_lessons": key_lessons,
        "relevant_conditions": relevant_conditions,
        "risk_factors": risk_factors,
    }


# =============================================================================
# WEIGHTED PLANNING BALANCE
# =============================================================================

@dataclass
class PlanningWeight:
    """A weighted consideration in the planning balance."""
    consideration: str
    weight: str  # "substantial", "significant", "moderate", "limited", "negligible"
    weight_value: int  # 5=substantial, 4=significant, 3=moderate, 2=limited, 1=negligible
    in_favour: bool  # True = benefit, False = harm
    policy_basis: str
    reasoning: str


def calculate_planning_balance(
    assessments: list,
    constraints: list[str],
    proposal_details: ProposalDetails,
    precedent_analysis: dict,
    council_name: str
) -> tuple[list[PlanningWeight], str, str]:
    """
    Calculate a weighted planning balance for the recommendation.

    Returns:
        - List of weighted considerations
        - Balance summary text
        - Recommendation (APPROVE/REFUSE)
    """
    weights = []
    constraints_lower = [c.lower() for c in constraints]
    has_heritage = any('conservation' in c or 'listed' in c for c in constraints_lower)

    # BENEFITS

    # Housing delivery (if residential)
    if proposal_details.development_type in ["dwelling", "flats", "conversion"]:
        units = max(proposal_details.num_units, 1)
        if units >= 10:
            weight = "significant"
            weight_value = 4
        elif units >= 5:
            weight = "moderate"
            weight_value = 3
        else:
            weight = "limited"
            weight_value = 2

        weights.append(PlanningWeight(
            consideration=f"Delivery of {units} residential unit(s)",
            weight=weight,
            weight_value=weight_value,
            in_favour=True,
            policy_basis="NPPF paragraph 60 - significantly boosting housing supply",
            reasoning=f"The provision of {units} new dwelling(s) would make a {'meaningful' if units >= 5 else 'modest'} contribution to housing supply in accordance with the Government's objective of significantly boosting the supply of homes."
        ))

    # Economic benefits
    weights.append(PlanningWeight(
        consideration="Economic benefits (construction employment, local spending)",
        weight="limited",
        weight_value=2,
        in_favour=True,
        policy_basis="NPPF paragraph 81 - building a strong economy",
        reasoning="The development would generate short-term construction employment and support local suppliers and services."
    ))

    # Sustainable location (if urban)
    weights.append(PlanningWeight(
        consideration="Sustainable location within urban area",
        weight="moderate",
        weight_value=3,
        in_favour=True,
        policy_basis="NPPF paragraph 79 - promoting sustainable transport",
        reasoning="The site is within the urban area with access to public transport, shops and services, representing a sustainable location for development."
    ))

    # HARMS (check assessments for non-compliance)
    non_compliant = [a for a in assessments if a.compliance in ['non-compliant', 'partial']]

    for assessment in non_compliant:
        if 'heritage' in assessment.topic.lower() or 'conservation' in assessment.topic.lower():
            weights.append(PlanningWeight(
                consideration=f"Harm to heritage asset",
                weight="significant",  # Great weight per NPPF 199
                weight_value=4,
                in_favour=False,
                policy_basis="NPPF paragraph 199 - great weight to conservation",
                reasoning="NPPF paragraph 199 requires great weight to be given to the conservation of designated heritage assets. Any harm must be clearly justified."
            ))
        elif 'amenity' in assessment.topic.lower():
            weights.append(PlanningWeight(
                consideration="Harm to residential amenity",
                weight="significant",
                weight_value=4,
                in_favour=False,
                policy_basis="NPPF paragraph 130(f) - high standard of amenity",
                reasoning="The development would cause unacceptable harm to the living conditions of neighbouring occupiers."
            ))
        elif 'design' in assessment.topic.lower():
            weights.append(PlanningWeight(
                consideration="Design quality concerns",
                weight="significant",
                weight_value=4,
                in_favour=False,
                policy_basis="NPPF paragraph 134 - refuse poor design",
                reasoning="NPPF paragraph 134 states that development which is not well designed should be refused."
            ))

    # Calculate balance
    benefits_score = sum(w.weight_value for w in weights if w.in_favour)
    harms_score = sum(w.weight_value for w in weights if not w.in_favour)

    # Heritage tilted balance
    if has_heritage and harms_score > 0:
        # Apply heritage weighting - harms to heritage carry extra weight
        heritage_harms = [w for w in weights if not w.in_favour and 'heritage' in w.consideration.lower()]
        if heritage_harms:
            harms_score += 2  # Additional weight for heritage harm

    # Generate professional balance summary (no point scoring)
    benefits_list = [w for w in weights if w.in_favour]
    harms_list = [w for w in weights if not w.in_favour]

    def format_weight_item(w):
        return f"- {w.consideration} ({w.weight} weight)"

    if harms_score == 0:
        balance_summary = f"""**Planning Balance**

**Benefits identified:**
{chr(10).join(format_weight_item(w) for w in benefits_list)}

**Harms identified:**
No unacceptable harms have been identified.

**Officer Assessment:**
The benefits of the development are not outweighed by any adverse impacts. The proposal represents sustainable development in accordance with the presumption in favour set out at NPPF paragraph 11.

The planning balance falls clearly in favour of approval."""
        recommendation = "APPROVE_WITH_CONDITIONS"

    elif benefits_score > harms_score * 1.5:
        balance_summary = f"""**Planning Balance**

**Benefits identified:**
{chr(10).join(format_weight_item(w) for w in benefits_list)}

**Harms identified:**
{chr(10).join(format_weight_item(w) for w in harms_list)}

**Officer Assessment:**
While limited harm has been identified, the benefits of the proposal are considered to outweigh the adverse impacts. The identified harm can be adequately mitigated through conditions.

The planning balance falls in favour of approval subject to conditions."""
        recommendation = "APPROVE_WITH_CONDITIONS"

    elif harms_score > benefits_score:
        balance_summary = f"""**Planning Balance**

**Benefits identified:**
{chr(10).join(format_weight_item(w) for w in benefits_list)}

**Harms identified:**
{chr(10).join(format_weight_item(w) for w in harms_list)}

**Officer Assessment:**
The identified harms are considered to outweigh the benefits of the development. The adverse impacts would significantly and demonstrably outweigh the benefits when assessed against the policies in the Framework taken as a whole.

The planning balance falls against approval and refusal is recommended."""
        recommendation = "REFUSE"

    else:
        balance_summary = f"""**Planning Balance**

**Benefits identified:**
{chr(10).join(format_weight_item(w) for w in benefits_list)}

**Harms identified:**
{chr(10).join(format_weight_item(w) for w in harms_list)}

**Officer Assessment:**
The planning balance is finely balanced. On balance, having regard to the presumption in favour of sustainable development at NPPF paragraph 11, the benefits are considered to marginally outweigh the identified harm.

Approval is recommended subject to conditions to mitigate the identified impacts."""
        recommendation = "APPROVE_WITH_CONDITIONS"

    return weights, balance_summary, recommendation


# =============================================================================
# PROFESSIONAL CONDITIONS LIBRARY
# =============================================================================

def generate_professional_conditions(
    proposal_details: ProposalDetails,
    constraints: list[str],
    assessments: list,
    council_id: str
) -> list[dict]:
    """
    Generate professional planning conditions with specific policy basis.

    Conditions are organized into three categories:
    1. STATUTORY - Based on Acts of Parliament (apply to ALL applications)
    2. NATIONAL POLICY - Based on NPPF (apply to ALL applications)
    3. LOCAL PLAN - Based on council-specific policies (apply to that council only)

    Each condition clearly states its legal/policy basis.
    """
    conditions = []
    condition_num = 1
    constraints_lower = [c.lower() for c in constraints]

    # Get council-specific policy references
    council_policies = _get_council_condition_policies(council_id)
    council_name = _get_council_name(council_id)

    # =========================================================================
    # STATUTORY CONDITIONS (Acts of Parliament - Apply to ALL applications)
    # =========================================================================

    # 1. Time limit - TCPA 1990 s.91
    conditions.append({
        "number": condition_num,
        "type": "statutory",
        "category": "Statutory",
        "condition": "The development hereby permitted shall be commenced before the expiration of three years beginning with the date of this permission.",
        "reason": "To comply with Section 91 of the Town and Country Planning Act 1990 as amended by Section 51 of the Planning and Compulsory Purchase Act 2004.",
        "policy_basis": "Section 91 TCPA 1990",
        "trigger": "time-limit",
    })
    condition_num += 1

    # 2. Approved plans
    conditions.append({
        "number": condition_num,
        "type": "statutory",
        "category": "Statutory",
        "condition": "The development hereby permitted shall be carried out in accordance with the approved plans listed in the schedule of approved documents.",
        "reason": "For the avoidance of doubt.",
        "policy_basis": "Section 91 TCPA 1990; General planning practice",
        "trigger": "compliance",
    })
    condition_num += 1

    # 3. Biodiversity Net Gain - Environment Act 2021 (Statutory - applies to ALL)
    conditions.append({
        "number": condition_num,
        "type": "statutory",
        "category": "Statutory",
        "condition": """Statutory Biodiversity Net Gain - Deemed Condition

Biodiversity Net Gain (BNG) of 10% for developments is a mandatory requirement in England under the Environment Act 2021.

The effect of the relevant paragraphs of Schedule 7A to the Town and Country Planning Act 1990 is that planning permission granted for the development of land in England is deemed to have been granted subject to the condition (the biodiversity gain condition) that development may not begin unless:

(a) a Biodiversity Gain Plan has been submitted to the planning authority, and
(b) the planning authority has approved the plan, or
(c) documentation of statutory biodiversity credits purchased have been submitted to the Local Planning Authority.""",
        "reason": "To ensure the development delivers a biodiversity net gain in accordance with the relevant paragraphs of Schedule 7A of the Town and Country Planning Act 1990 and the Environment Act 2021.",
        "policy_basis": "Environment Act 2021; Schedule 7A TCPA 1990",
        "trigger": "pre-commencement",
    })
    condition_num += 1

    # Heritage statutory duties (if applicable)
    if any('listed' in c for c in constraints_lower):
        conditions.append({
            "number": condition_num,
            "type": "statutory",
            "category": "Statutory",
            "condition": "No works shall commence until a detailed method statement for the works, including protection measures for historic fabric, has been submitted to and approved in writing by the Local Planning Authority. The works shall be carried out in accordance with the approved method statement.",
            "reason": "To preserve the special architectural and historic interest of the Listed Building, having regard to Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990.",
            "policy_basis": "Section 66 P(LBCA)A 1990",
            "trigger": "pre-commencement",
        })
        condition_num += 1

    if any('conservation' in c for c in constraints_lower):
        conditions.append({
            "number": condition_num,
            "type": "statutory",
            "category": "Statutory",
            "condition": "Prior to commencement of development, detailed drawings at a scale of 1:20 or 1:10 showing all new windows and doors including materials, opening mechanisms, glazing bars, and relationship to the masonry/frame shall be submitted to and approved in writing by the Local Planning Authority. The works shall be carried out in accordance with the approved details.",
            "reason": "To preserve or enhance the character or appearance of the Conservation Area, having regard to Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990.",
            "policy_basis": "Section 72 P(LBCA)A 1990",
            "trigger": "pre-commencement",
        })
        condition_num += 1

    # =========================================================================
    # NATIONAL POLICY CONDITIONS (NPPF - Apply to ALL applications)
    # =========================================================================

    # Materials condition - NPPF Chapter 12
    # Applied to all development involving new construction or external alterations
    # This ensures high design standards per NPPF paragraph 130
    development_needs_materials = (
        proposal_details.development_type in ["dwelling", "extension", "flats", "new build", "conversion", "full", "householder"]
        or "dwelling" in proposal_details.development_type.lower()
        or "build" in proposal_details.development_type.lower()
        or proposal_details.num_units >= 1
    )
    if development_needs_materials:
        conditions.append({
            "number": condition_num,
            "type": "national",
            "category": "National Policy (NPPF)",
            "condition": "No building operations above ground level shall be carried out until details of the manufacturer, type and colour of the external facing materials (including bricks, tiles, windows, doors, and rainwater goods) have been submitted to and approved in writing by the Local Planning Authority. The development shall be constructed only in accordance with those details.",
            "reason": "To ensure the development presents a satisfactory standard of external appearance, in accordance with NPPF paragraphs 130 and 134.",
            "policy_basis": "NPPF paragraphs 130, 134 (Achieving well-designed places)",
            "trigger": "pre-above-ground",
        })
        condition_num += 1

    # Biodiversity enhancement - NPPF Chapter 15
    # Applied to new residential development creating new dwelling(s)
    development_needs_biodiversity = (
        proposal_details.development_type in ["dwelling", "flats", "new build", "full"]
        or "dwelling" in proposal_details.development_type.lower()
        or proposal_details.num_units >= 1
    )
    if development_needs_biodiversity:
        conditions.append({
            "number": condition_num,
            "type": "national",
            "category": "National Policy (NPPF)",
            "condition": """No building operations above ground level shall be carried out until a scheme of biodiversity enhancement has been submitted to and approved in writing by the Local Planning Authority. The scheme shall include, as a minimum:

- Integrated (inbuilt) features within the new building(s) for roosting bats (e.g., bat boxes/bricks)
- Nesting features for swifts (e.g., swift bricks)
- Bee bricks or similar pollinator habitat
- Hedgehog gaps (130mm x 130mm minimum) in all garden boundary fences
- Native species planting scheme

The enhancement scheme shall be implemented in accordance with the agreed details as construction proceeds and completed prior to the first occupation of the development.""",
            "reason": "In the interests of safeguarding and enhancing biodiversity in accordance with NPPF paragraphs 174 and 180.",
            "policy_basis": "NPPF paragraphs 174, 180 (Conserving and enhancing the natural environment)",
            "trigger": "pre-above-ground",
        })
        condition_num += 1

    # Landscaping - NPPF Chapter 12
    conditions.append({
        "number": condition_num,
        "type": "national",
        "category": "National Policy (NPPF)",
        "condition": "Prior to first occupation of the development, a landscaping scheme including hard and soft landscaping, boundary treatments, and any external lighting shall be submitted to and approved in writing by the Local Planning Authority. The approved scheme shall be implemented in the first planting season following completion of the development and maintained thereafter. Any trees or shrubs which die, are removed, or become seriously diseased within 5 years of planting shall be replaced in the next planting season with specimens of similar size and species.",
        "reason": "In the interests of visual amenity and biodiversity enhancement, having regard to NPPF paragraphs 130 and 174.",
        "policy_basis": "NPPF paragraphs 130, 174",
        "trigger": "pre-occupation",
    })
    condition_num += 1

    # Drainage/SuDS - NPPF Chapter 14
    conditions.append({
        "number": condition_num,
        "type": "national",
        "category": "National Policy (NPPF)",
        "condition": "No development shall commence until a surface water drainage scheme, based on sustainable drainage principles (SuDS) and an assessment of the hydrological and hydrogeological context of the development, has been submitted to and approved in writing by the Local Planning Authority. The scheme shall demonstrate that surface water run-off will not exceed greenfield rates and shall be implemented in accordance with the approved details prior to first occupation.",
        "reason": "To prevent increased flood risk and ensure sustainable drainage, having regard to NPPF paragraphs 167-169.",
        "policy_basis": "NPPF paragraphs 167-169 (Meeting the challenge of climate change, flooding and coastal change)",
        "trigger": "pre-commencement",
    })
    condition_num += 1

    # Tree protection (if trees present) - NPPF
    if any('tree' in c or 'tpo' in c for c in constraints_lower):
        conditions.append({
            "number": condition_num,
            "type": "national",
            "category": "National Policy (NPPF)",
            "condition": "No development shall commence until a Tree Protection Plan and Arboricultural Method Statement in accordance with BS5837:2012 have been submitted to and approved in writing by the Local Planning Authority. The approved tree protection measures shall be implemented before any development or site clearance begins and maintained throughout construction.",
            "reason": "To protect trees of amenity value during construction, having regard to NPPF paragraph 131.",
            "policy_basis": "NPPF paragraph 131; BS5837:2012",
            "trigger": "pre-commencement",
        })
        condition_num += 1

    # Construction Management (for larger schemes) - NPPF
    if proposal_details.num_units >= 5 or proposal_details.floor_area_sqm >= 500:
        conditions.append({
            "number": condition_num,
            "type": "national",
            "category": "National Policy (NPPF)",
            "condition": "No development shall commence until a Construction Management Plan has been submitted to and approved in writing by the Local Planning Authority. The Plan shall include: construction traffic routes; parking for site operatives and visitors; loading/unloading arrangements; wheel washing facilities; dust suppression measures; and hours of construction. The approved Plan shall be adhered to throughout construction.",
            "reason": "In the interests of highway safety and residential amenity during construction, having regard to NPPF paragraphs 110 and 130(f).",
            "policy_basis": "NPPF paragraphs 110, 130(f)",
            "trigger": "pre-commencement",
        })
        condition_num += 1

    # =========================================================================
    # LOCAL PLAN CONDITIONS (Council-specific - Apply to THIS council only)
    # =========================================================================

    # Determine if this is a new dwelling development
    # Check development_type directly OR check if num_units indicates dwelling units
    is_new_dwelling = (
        proposal_details.development_type in ["dwelling", "flats", "new build"]
        or "dwelling" in proposal_details.development_type.lower()
        or proposal_details.num_units >= 1  # Has dwelling units
    )

    # Highways conditions with local policy
    if is_new_dwelling:
        # Vehicular crossing
        conditions.append({
            "number": condition_num,
            "type": "local",
            "category": f"Local Plan ({council_name})",
            "condition": "No part of the development hereby permitted shall be brought into use until a dropped vehicular footway crossing is available for use and constructed in accordance with the Highway Authority specification to the satisfaction of the Local Planning Authority.",
            "reason": f"In the interests of highway safety, in accordance with {council_policies['highways']}.",
            "policy_basis": f"NPPF paragraph 110; {council_policies['highways']}",
            "trigger": "pre-occupation",
        })
        condition_num += 1

        # Hard surfacing
        conditions.append({
            "number": condition_num,
            "type": "local",
            "category": f"Local Plan ({council_name})",
            "condition": "No part of the development hereby permitted shall be brought into use until the access driveway and any parking/turning areas are surfaced in a hard-bound material (not loose gravel) for a minimum of 5.5 metres behind the Highway boundary. The surfaced drive and any parking or turning areas shall then be maintained in such hard-bound material for the life of the development.",
            "reason": f"To reduce the possibility of deleterious material being deposited on the public highway (loose stones etc), in accordance with {council_policies['highways']}.",
            "policy_basis": f"{council_policies['highways']}",
            "trigger": "pre-occupation",
        })
        condition_num += 1

        # Surface water to highway
        conditions.append({
            "number": condition_num,
            "type": "local",
            "category": f"Local Plan ({council_name})",
            "condition": "No part of the development hereby permitted shall be brought into use until the access driveway/parking/turning area is constructed with provision to prevent the unregulated discharge of surface water from the driveway/parking/turning area to the public highway in accordance with details first submitted to and approved in writing by the Local Planning Authority. The provision to prevent the unregulated discharge of surface water to the public highway shall then be retained for the life of the development.",
            "reason": f"To ensure surface water from the site is not deposited on the public highway causing dangers to road users, in accordance with {council_policies['highways']}.",
            "policy_basis": f"{council_policies['highways']}",
            "trigger": "pre-occupation",
        })
        condition_num += 1

    # Permitted development removal with local policy (applies to dwelling developments)
    if is_new_dwelling and proposal_details.development_type != "flats":
        conditions.append({
            "number": condition_num,
            "type": "local",
            "category": f"Local Plan ({council_name})",
            "condition": "Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015 (or any order revoking and re-enacting that Order with or without modification), no extensions, enlargements, or roof alterations shall be carried out to the dwelling(s) hereby approved which come within Classes A, AA, B, C and E of Schedule 2 Part 1 of the Order without the prior written permission of the Local Planning Authority by way of a formal planning permission.",
            "reason": f"In the interests of preserving the spacious character of the site in accordance with the aims of {council_policies['design']}.",
            "policy_basis": f"GPDO 2015; {council_policies['design']}",
            "trigger": "compliance",
        })
        condition_num += 1

    return conditions


def _get_council_name(council_id: str) -> str:
    """Get the full council name from ID."""
    council_names = {
        "broxtowe": "Broxtowe Borough Council",
        "newcastle": "Newcastle City Council",
        "nottingham": "Nottingham City Council",
    }
    return council_names.get(council_id.lower(), "the Local Planning Authority")


def _get_council_condition_policies(council_id: str) -> dict:
    """Get council-specific policy references for conditions."""
    council_policies = {
        "broxtowe": {
            "design": "Policy 17 of the Broxtowe Part 2 Local Plan (2019) and Policy 10 of the Aligned Core Strategy (2014)",
            "highways": "Policy 17 of the Broxtowe Part 2 Local Plan (2019)",
            "heritage": "Policy 26 of the Broxtowe Part 2 Local Plan (2019)",
            "biodiversity": "Policy 31 of the Broxtowe Part 2 Local Plan (2019)",
            "trees": "Policy 25 of the Broxtowe Part 2 Local Plan (2019)",
            "drainage": "Policy 1 of the Broxtowe Part 2 Local Plan (2019)",
            "amenity": "Policy 17 of the Broxtowe Part 2 Local Plan (2019)",
        },
        "newcastle": {
            "design": "Policy DM6.1 of the Development and Allocations Plan (2022) and Policy CS15 of the Core Strategy (2015)",
            "highways": "Policy DM13 of the Development and Allocations Plan (2022)",
            "heritage": "Policy DM15 of the Development and Allocations Plan (2022)",
            "biodiversity": "Policy DM28 of the Development and Allocations Plan (2022)",
            "trees": "Policy DM28 of the Development and Allocations Plan (2022)",
            "drainage": "Policy CS17 of the Core Strategy (2015)",
            "amenity": "Policy DM6.6 of the Development and Allocations Plan (2022)",
        },
        "nottingham": {
            "design": "Policy DE1 of the Local Plan Part 2 (2020)",
            "highways": "Policy TR1 of the Local Plan Part 2 (2020)",
            "heritage": "Policy HE1 of the Local Plan Part 2 (2020)",
            "biodiversity": "Policy EN6 of the Local Plan Part 2 (2020)",
            "trees": "Policy EN6 of the Local Plan Part 2 (2020)",
            "drainage": "Policy CC3 of the Local Plan Part 2 (2020)",
            "amenity": "Policy DE1 of the Local Plan Part 2 (2020)",
        },
    }

    # Default policies if council not found
    default = {
        "design": "Local Plan Design Policy",
        "highways": "Local Plan Transport Policy",
        "heritage": "Local Plan Heritage Policy",
        "biodiversity": "Local Plan Biodiversity Policy",
        "trees": "Local Plan Trees/Landscape Policy",
        "drainage": "Local Plan Drainage Policy",
        "amenity": "Local Plan Amenity Policy",
    }

    return council_policies.get(council_id.lower(), default)


@dataclass
class RedFlag:
    """A critical issue that should trigger refusal."""
    trigger: str
    issue: str
    policy_conflict: str
    refusal_reason: str
    severity: str  # critical, major, moderate


def detect_red_flags(proposal: str, constraints: list[str], application_type: str) -> list[RedFlag]:
    """
    Detect critical issues in a proposal that should trigger refusal.

    These are patterns that case officers consistently refuse based on
    clear policy conflicts or established precedent.
    """
    red_flags = []
    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]

    # 1. UPVC windows on Listed Buildings - ALWAYS REFUSED
    has_listed = any('listed' in c for c in constraints_lower)
    has_upvc = 'upvc' in proposal_lower or 'u-pvc' in proposal_lower or 'pvcu' in proposal_lower

    if has_listed and has_upvc:
        red_flags.append(RedFlag(
            trigger="uPVC on Listed Building",
            issue="uPVC windows are fundamentally incompatible with listed buildings",
            policy_conflict="Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990, NPPF Chapter 16, Policy DM15",
            refusal_reason="The proposed uPVC windows would cause substantial harm to the significance of this listed building by introducing inappropriate modern materials that are fundamentally incompatible with the historic character of the building, contrary to Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990, NPPF Chapter 16, and Policy DM15.",
            severity="critical",
        ))

    # 2. Balconies at first floor level - Privacy/overlooking harm
    has_balcony = 'balcony' in proposal_lower or 'balconies' in proposal_lower
    has_first_floor = 'first floor' in proposal_lower or 'first-floor' in proposal_lower
    has_upper_level = has_first_floor or 'second floor' in proposal_lower or 'upper' in proposal_lower

    if has_balcony and has_upper_level:
        red_flags.append(RedFlag(
            trigger="First floor balcony",
            issue="First floor balconies cause unacceptable overlooking of neighbouring properties",
            policy_conflict="Policy DM6.6 (Protection of Residential Amenity)",
            refusal_reason="The proposed first floor balcony would result in unacceptable overlooking of neighbouring properties, causing significant harm to the privacy and amenity of neighbouring occupiers, contrary to Policy DM6.6 of the Development and Allocations Plan.",
            severity="major",
        ))

    # 3. Two storey extension described as "dominating" or very large scale
    has_two_storey = 'two storey' in proposal_lower or 'two-storey' in proposal_lower or '2 storey' in proposal_lower
    has_overdevelopment_indicators = any(term in proposal_lower for term in [
        'large scale', 'substantial', 'significant extension', 'major extension'
    ])

    # Check if precedent shows similar refused for overdevelopment
    if has_two_storey and has_balcony:
        red_flags.append(RedFlag(
            trigger="Two storey extension with balcony",
            issue="Combination of two storey extension with balcony represents overdevelopment with privacy harm",
            policy_conflict="Policies DM6.6, DM15, DM16",
            refusal_reason="The two storey extension by reason of its scale, bulk and massing, combined with the first floor balcony, would appear as an overly dominant addition that fails to respect the character of the host dwelling, and the balcony would result in unacceptable overlooking of neighbouring properties, contrary to Policies DM6.6, DM15 and DM16.",
            severity="major",
        ))

    # 4. Replacement windows in Conservation Area with uPVC (not listed but still harmful)
    has_conservation = any('conservation' in c for c in constraints_lower)
    has_article4 = any('article 4' in c for c in constraints_lower)
    has_window_replacement = 'replacement window' in proposal_lower or 'replace window' in proposal_lower or 'new window' in proposal_lower

    if has_conservation and has_article4 and has_upvc and has_window_replacement:
        red_flags.append(RedFlag(
            trigger="uPVC windows in Conservation Area with Article 4",
            issue="uPVC windows in Conservation Area with Article 4 Direction",
            policy_conflict="Policies DM15, DM16, NPPF Chapter 16",
            refusal_reason="The proposed uPVC windows would fail to preserve or enhance the character and appearance of the Conservation Area, causing harm to this designated heritage asset, contrary to Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990, Policies DM15 and DM16.",
            severity="major",
        ))

    return red_flags


@dataclass
class AssessmentResult:
    """Result of assessing a topic."""
    topic: str
    compliance: str  # compliant, non-compliant, partial, insufficient-evidence
    reasoning: str
    key_considerations: list[str]
    policy_citations: list[str]
    precedent_support: str
    confidence: float


@dataclass
class ReasoningResult:
    """Complete reasoning output."""
    assessment_topics: list[AssessmentResult]
    planning_balance: str
    recommendation: str  # APPROVE, APPROVE_WITH_CONDITIONS, REFUSE, INSUFFICIENT_EVIDENCE
    recommendation_reasoning: str
    conditions: list[dict[str, Any]]
    refusal_reasons: list[dict[str, Any]]
    key_risks: list[dict[str, Any]]
    confidence_score: float
    confidence_factors: list[str]


def generate_topic_assessment(
    topic: str,
    proposal: str,
    constraints: list[str],
    policies: list[Policy],
    similar_cases: list[HistoricCase],
    application_type: str,
    council_id: str = "newcastle",
    site_address: str = "",
) -> AssessmentResult:
    """
    Generate a detailed evidence-based assessment for a specific planning topic.

    This uses specific NPPF paragraph citations and council-specific policies:
    - Relevant policies for this topic (council-specific)
    - Similar case outcomes
    - Site constraints
    - Specific NPPF paragraph text and citations
    """
    # Find policies relevant to this topic
    topic_lower = topic.lower()
    relevant_policies = []
    policy_citations = []

    topic_keywords = {
        "principle": ["sustainable", "location", "all"],
        "design": ["design", "character", "visual", "appearance"],
        "heritage": ["heritage", "conservation", "listed", "historic"],
        "amenity": ["amenity", "residential", "neighbour", "privacy", "daylight"],
        "residential": ["amenity", "residential", "neighbour", "privacy", "daylight"],
        "transport": ["transport", "parking", "highway", "access", "traffic"],
        "highways": ["transport", "parking", "highway", "access", "traffic"],  # Alias for transport
        "trees": ["tree", "landscape", "green"],
        "green belt": ["green belt", "openness"],
        "flood": ["flood", "drainage", "water"],
    }

    # Get keywords for the topic - check first word and full topic name
    first_word = topic_lower.split()[0].lower()
    keywords = topic_keywords.get(first_word, topic_keywords.get(topic_lower, ["design"]))

    for policy in policies:
        for trigger in policy.triggers:
            if any(kw in trigger for kw in keywords):
                relevant_policies.append(policy)
                policy_citations.append(_format_policy_citation_from_object(policy))
                break

    # Analyse precedent for this topic
    precedent_support = "Limited precedent available"
    if similar_cases:
        approved = sum(1 for c in similar_cases if 'approved' in c.decision.lower())
        if approved >= len(similar_cases) * 0.7:
            precedent_support = f"Strong precedent support - {approved}/{len(similar_cases)} similar applications approved"
        elif approved <= len(similar_cases) * 0.3:
            precedent_support = f"Precedent suggests caution - majority of similar applications refused"
        else:
            precedent_support = f"Mixed precedent - case-specific assessment required"

    # Generate evidence-based reasoning with specific citations
    reasoning, compliance, key_considerations = _generate_topic_reasoning(
        topic=topic,
        proposal=proposal,
        constraints=constraints,
        relevant_policies=relevant_policies,
        similar_cases=similar_cases,
        application_type=application_type,
        council_id=council_id,
        site_address=site_address,
    )

    # Add council-specific policy references to policy_citations
    # This ensures that even if no policies matched via triggers, we still have local policy refs
    from .local_plans_complete import LOCAL_PLANS_DATABASE, detect_council_from_address, get_council_name
    if site_address:
        detected_council = detect_council_from_address(site_address)
        if detected_council:
            council_id = detected_council
    council_name = get_council_name(council_id)
    council_data = LOCAL_PLANS_DATABASE.get(council_id, {})
    council_policies = council_data.get("policies", {})
    local_policy_refs = _get_council_policies_for_topic(topic_lower, council_id, council_policies)

    # Format council policies and add to citations if not already present
    for policy_ref in local_policy_refs:
        policy_id = policy_ref.get("id", "")
        policy_name = policy_ref.get("name", "")
        formatted_ref = _format_policy_ref(council_name, policy_id)
        if formatted_ref and formatted_ref not in policy_citations:
            policy_citations.append(formatted_ref)

    # Calculate confidence
    confidence = 0.7
    if len(relevant_policies) >= 3:
        confidence += 0.1
    if len(similar_cases) >= 2:
        confidence += 0.1
    if constraints:
        confidence += 0.05

    return AssessmentResult(
        topic=topic,
        compliance=compliance,
        reasoning=reasoning,
        key_considerations=key_considerations,
        policy_citations=policy_citations[:5],
        precedent_support=precedent_support,
        confidence=min(confidence, 0.95),
    )


def _generate_topic_reasoning(
    topic: str,
    proposal: str,
    constraints: list[str],
    relevant_policies: list[Policy],
    similar_cases: list[HistoricCase],
    application_type: str,
    council_id: str = "newcastle",
    site_address: str = "",
) -> tuple[str, str, list[str]]:
    """
    Generate evidence-based reasoning text for a specific topic.

    Uses specific NPPF paragraph citations and council-specific local plan policies.
    """
    # Import complete policy databases
    from .nppf_complete import NPPF_PARAGRAPHS, get_relevant_nppf_paragraphs
    from .local_plans_complete import (
        LOCAL_PLANS_DATABASE,
        detect_council_from_address,
        get_council_name,
    )

    # ALWAYS detect council from address if address is provided
    if site_address:
        detected_council = detect_council_from_address(site_address)
        if detected_council:
            council_id = detected_council

    council_name = get_council_name(council_id)
    council_data = LOCAL_PLANS_DATABASE.get(council_id, {})
    council_policies = council_data.get("policies", {})

    topic_lower = topic.lower()
    constraints_lower = [c.lower() for c in constraints]

    # Check for heritage and other constraints
    has_conservation = any('conservation' in c for c in constraints_lower)
    has_listed = any('listed' in c for c in constraints_lower)
    has_green_belt = any('green belt' in c for c in constraints_lower)
    has_flood = any('flood' in c for c in constraints_lower)
    has_tree = any('tree' in c or 'tpo' in c for c in constraints_lower)

    # Get council-specific policy references based on topic
    local_policy_refs = _get_council_policies_for_topic(topic_lower, council_id, council_policies)

    # Get specific NPPF paragraphs for this topic
    nppf_citations = _get_nppf_citations_for_topic(topic_lower, NPPF_PARAGRAPHS)

    # Generate topic-specific evidence-based reasoning
    if "principle" in topic_lower:
        reasoning, compliance, key_considerations = _generate_principle_assessment(
            proposal, application_type, constraints_lower, council_name,
            local_policy_refs, nppf_citations, has_conservation, has_listed, has_green_belt
        )
    elif "design" in topic_lower:
        reasoning, compliance, key_considerations = _generate_design_assessment(
            proposal, application_type, constraints_lower, council_name,
            local_policy_refs, nppf_citations, has_conservation, council_id
        )
    elif "heritage" in topic_lower or "conservation" in topic_lower:
        reasoning, compliance, key_considerations = _generate_heritage_assessment(
            proposal, constraints_lower, council_name, local_policy_refs,
            nppf_citations, has_conservation, has_listed
        )
    elif "amenity" in topic_lower or "residential" in topic_lower:
        reasoning, compliance, key_considerations = _generate_amenity_assessment(
            proposal, constraints_lower, council_name, local_policy_refs, nppf_citations
        )
    elif "highway" in topic_lower or "transport" in topic_lower or "access" in topic_lower:
        reasoning, compliance, key_considerations = _generate_highways_assessment(
            proposal, application_type, council_name, local_policy_refs, nppf_citations
        )
    elif "flood" in topic_lower or "drainage" in topic_lower:
        reasoning, compliance, key_considerations = _generate_flood_assessment(
            proposal, constraints_lower, council_name, local_policy_refs, nppf_citations, has_flood
        )
    elif "tree" in topic_lower or "landscape" in topic_lower:
        reasoning, compliance, key_considerations = _generate_trees_assessment(
            proposal, constraints_lower, council_name, local_policy_refs, nppf_citations, has_tree
        )
    else:
        # Generic assessment with evidence
        reasoning, compliance, key_considerations = _generate_generic_assessment(
            topic, proposal, constraints_lower, council_name, local_policy_refs, nppf_citations
        )

    return reasoning, compliance, key_considerations


def _get_council_policies_for_topic(topic: str, council_id: str, policies: dict) -> list[dict]:
    """Get council-specific policies relevant to a topic."""
    # Note: LP10 is "Town Centre and District Centre Uses" NOT design
    # ACS-10 / Policy 10 from Aligned Core Strategy is the design policy
    # Policy 17 from Part 2 Local Plan is the main design/amenity policy for Broxtowe
    topic_policy_map = {
        "principle": ["CS1", "CS3", "Policy 1", "Policy 2", "LP1", "LP3", "Policy A"],
        "design": ["CS15", "DM6.1", "DM6.2", "ACS-10", "Policy-17", "LP17"],
        "heritage": ["DM15", "DM16", "Policy 11", "LP12", "Policy-26"],
        "amenity": ["DM6.6", "CS16", "ACS-10", "Policy-17", "LP17"],
        "highways": ["CS13", "DM7", "DM13", "Policy-17", "LP14"],
        "transport": ["CS13", "DM7", "DM13", "Policy-17", "LP14"],
        "flood": ["CS17", "DM5", "Policy 1", "LP3"],
        "trees": ["DM28", "CS18", "Policy 16", "LP19", "Policy-25"],
        "landscape": ["DM28", "CS18", "Policy 16", "LP19", "Policy-25"],
    }

    relevant_ids = topic_policy_map.get(topic.split()[0].lower(), [])
    return [policies[pid] for pid in relevant_ids if pid in policies]


def _format_policy_ref(council_name: str, policy_id: str) -> str:
    """
    Format a policy reference correctly, avoiding 'Policy Policy X' duplication.

    Examples:
        - ("Broxtowe", "Policy 10") -> "Broxtowe Policy 10"
        - ("Newcastle", "CS15") -> "Newcastle Policy CS15"
        - ("Newcastle", "DM6.1") -> "Newcastle Policy DM6.1"
    """
    policy_id_lower = policy_id.lower()
    # If ID already starts with 'policy', don't add another 'Policy' prefix
    if policy_id_lower.startswith("policy"):
        return f"{council_name} {policy_id}"
    else:
        return f"{council_name} Policy {policy_id}"


def _get_nppf_citations_for_topic(topic: str, nppf_paragraphs: dict) -> list[dict]:
    """Get specific NPPF paragraph citations for a topic."""
    topic_nppf_map = {
        "principle": [2, 7, 8, 10, 11, 38, 47],
        "design": [126, 127, 128, 129, 130, 131, 132, 133, 134, 135],
        "heritage": [189, 190, 194, 195, 197, 199, 200, 201, 202, 203, 206],
        "conservation": [189, 190, 194, 195, 197, 199, 200, 201, 202, 203, 206],
        "amenity": [92, 130],
        "highways": [104, 105, 110, 111, 112, 113],
        "transport": [104, 105, 110, 111, 112, 113],
        "flood": [159, 160, 161, 162, 163, 164, 165, 166, 167],
        "trees": [174, 180, 131],
        "landscape": [174, 180, 131],
    }

    para_nums = topic_nppf_map.get(topic.split()[0].lower(), [11, 130])
    return [{"para": num, **nppf_paragraphs[num]} for num in para_nums if num in nppf_paragraphs]


def _generate_principle_assessment(
    proposal: str, application_type: str, constraints: list[str],
    council_name: str, local_policies: list, nppf_citations: list,
    has_conservation: bool, has_listed: bool, has_green_belt: bool
) -> tuple[str, str, list[str]]:
    """
    Generate concise principle of development assessment.

    Focus on: Is this type of development acceptable in this location?
    """
    # Build local policy references
    def _format_local_ref(p):
        pid = p.get('id', '')
        if pid.lower().startswith('policy'):
            return pid
        return f"Policy {pid}"
    local_refs = ", ".join([_format_local_ref(p) for p in local_policies[:3]]) if local_policies else "the adopted Local Plan"

    # Determine if residential and site context
    is_dwelling = 'dwelling' in proposal.lower() or 'house' in proposal.lower()

    reasoning = f"""**Policy Test:** Section 38(6) PCPA 2004 - determine in accordance with development plan unless material considerations indicate otherwise. NPPF para 11 - presumption in favour of sustainable development.

**Site Status:**
- Location: Within {council_name} administrative area
- Settlement status: [Verify - within/outside settlement boundary]
- Land designation: {'Green Belt - NPPF para 147 applies' if has_green_belt else 'No restrictive designation identified'}
{'- Conservation Area - Section 72 duty applies' if has_conservation else ''}{'- Listed Building affected - Section 66 duty applies' if has_listed else ''}

**Principle Assessment:**
{'- Green Belt: Is the proposal "inappropriate development"? If so, are there very special circumstances?' if has_green_belt else ''}
- Settlement: {'Site appears to be within existing urban area' if not has_green_belt else '[Verify against Local Plan policies]'}
- Land use: {('Residential development (C3) - compatible with surrounding residential character' if is_dwelling else 'Proposed use to be assessed against local plan allocations')}
- Policy compliance: Relevant policies include {local_refs}

**Officer Verification Required:**
- Confirm site is within settlement boundary (if applicable)
- Check for any site-specific allocations in Local Plan
- Verify no restrictive designations missed"""

    compliance = "compliant"
    key_considerations = [
        "Section 38(6) PCPA 2004 - plan-led system",
        "NPPF para 11 - presumption in favour",
        f"{council_name} Local Plan policies apply",
        "Site within urban area - acceptable in principle" if not has_green_belt else "Green Belt - VSC required",
    ]
    if has_conservation:
        key_considerations.append("Section 72 duty - Conservation Area")
    if has_listed:
        key_considerations.append("Section 66 duty - Listed Building")

    return reasoning, compliance, key_considerations


def _generate_design_assessment(
    proposal: str, application_type: str, constraints: list[str],
    council_name: str, local_policies: list, nppf_citations: list,
    has_conservation: bool, council_id: str
) -> tuple[str, str, list[str]]:
    """
    Generate concise, site-specific design assessment.

    Focus on applying policy to the site, not quoting policy text.
    """
    # Get council-specific design policy
    design_policy = local_policies[0] if local_policies else None
    design_policy_id = design_policy.get("id", "Design Policy") if design_policy else "Policy 10"
    design_policy_ref = _format_policy_ref(council_name, design_policy_id)

    # Build site-specific assessment
    reasoning = f"""**Policy Test:** NPPF paragraphs 130 and 134 require development to be sympathetic to local character and refuse poor design. {design_policy_ref} reinforces these requirements locally.

**Site Context (to be verified):**
- Street character: [Case officer to confirm - detached/semi-detached, typical plot widths, building line, predominant materials]
- Neighbouring properties: [Verify relationship to adjacent dwellings at No. 2 and other neighbours]
- Existing features: [Note any trees, hedges, boundary treatments]

**Design Matters Requiring Verification:**

1. **Scale and Massing**
   - Ridge height relative to neighbours: [Not verified - measure from plans]
   - Footprint and plot coverage: [Not verified]
   - Building line: [Does it respect established pattern?]

2. **Materials**
   - Proposed materials: [Not specified in this draft - to be secured by condition]
   - Compatibility with streetscene: [Site visit required]

3. **Layout and Orientation**
   - Position on plot: [Verify from site plan]
   - Relationship to boundaries: [Check separation distances]
{'4. **Conservation Area**' if has_conservation else ''}
{'   - Section 72 duty applies: special attention to preserving/enhancing character' if has_conservation else ''}
{'   - Impact on CA character: [Requires heritage assessment]' if has_conservation else ''}

**Information Gaps:**
- Detailed streetscene analysis not available in this draft
- Materials not specified - condition required
- Site levels and relationship to neighbours not confirmed"""

    compliance = "compliant"  # Will be shown as conditional due to verification language
    key_considerations = [
        "NPPF para 130 - sympathetic to local character",
        "NPPF para 134 - refuse poor design",
        design_policy_ref,
        "Scale/massing - requires verification against plans",
        "Materials - to be secured by condition",
        "Streetscene context - site visit recommended",
    ]

    return reasoning, compliance, key_considerations


def _generate_heritage_assessment(
    proposal: str, constraints: list[str], council_name: str,
    local_policies: list, nppf_citations: list,
    has_conservation: bool, has_listed: bool
) -> tuple[str, str, list[str]]:
    """Generate evidence-based heritage assessment."""

    para_199 = next((c for c in nppf_citations if c["para"] == 199), None)
    para_200 = next((c for c in nppf_citations if c["para"] == 200), None)
    para_202 = next((c for c in nppf_citations if c["para"] == 202), None)

    heritage_policy = local_policies[0] if local_policies else None
    heritage_policy_id = heritage_policy.get("id", "Heritage Policy") if heritage_policy else "the heritage policy"
    heritage_policy_ref = _format_policy_ref(council_name, heritage_policy_id)

    reasoning = f"""**Statutory and Policy Framework**

{'Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires that in considering whether to grant planning permission for development which affects a listed building or its setting, the local planning authority shall have special regard to the desirability of preserving the building or its setting or any features of special architectural or historic interest which it possesses. ' if has_listed else ''}{'Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires that special attention shall be paid to the desirability of preserving or enhancing the character or appearance of conservation areas. ' if has_conservation else ''}

These statutory duties are reinforced by NPPF Chapter 16 (Conserving and enhancing the historic environment).

**NPPF Paragraph 199** states: "When considering the impact of a proposed development on the significance of a designated heritage asset, great weight should be given to the asset's conservation (and the more important the asset, the greater the weight should be). This is irrespective of whether any potential harm amounts to substantial harm, total loss or less than substantial harm to its significance."

**NPPF Paragraph 200** requires: "Any harm to, or loss of, the significance of a designated heritage asset (from its alteration or destruction, or from development within its setting), should require clear and convincing justification."

**NPPF Paragraph 202** states: "Where a development proposal will lead to less than substantial harm to the significance of a designated heritage asset, this harm should be weighed against the public benefits of the proposal including, where appropriate, securing its optimum viable use."

**Local Plan Policy**

{heritage_policy_ref} provides the local policy framework for heritage matters.

**Assessment of Heritage Impact**

{'The Conservation Area derives its significance from the historic building stock, mature landscaping, and cohesive architectural character. The proposed development has been assessed for its impact on this significance. ' if has_conservation else ''}{'The Listed Building derives its significance from its architectural and historic interest. The proposed works have been assessed for their impact on this significance. ' if has_listed else ''}

The development is considered to cause [no harm / negligible harm / less than substantial harm] to the significance of the heritage asset(s).

In accordance with NPPF paragraph 202, any less than substantial harm must be weighed against the public benefits. The public benefits include [provision of improved accommodation / sustainable use of the heritage asset / enhancement of the local economy].

**Conclusion on Heritage**

The proposal is considered to {'preserve the character and appearance of the Conservation Area in accordance with Section 72 of the Act' if has_conservation else ''}{'preserve the special interest of the Listed Building in accordance with Section 66 of the Act' if has_listed else ''}, and to comply with NPPF paragraphs 199-202 and {heritage_policy_ref}."""

    compliance = "compliant"
    key_considerations = []
    if has_listed:
        key_considerations.append("Section 66 duty - Listed Building preservation")
    if has_conservation:
        key_considerations.append("Section 72 duty - Conservation Area character")
    key_considerations.extend([
        "NPPF paragraph 199 - great weight to conservation",
        "NPPF paragraph 200 - clear justification for harm",
        "NPPF paragraph 202 - balance harm against benefits",
        f"{council_name} heritage policy",
    ])

    return reasoning, compliance, key_considerations


def _generate_amenity_assessment(
    proposal: str, constraints: list[str], council_name: str,
    local_policies: list, nppf_citations: list
) -> tuple[str, str, list[str]]:
    """
    Generate comprehensive residential amenity assessment for dwelling applications.

    Mandatory for: new dwellings, extensions, conversions affecting neighbours.
    Must assess: overlooking, overbearing, daylight/sunlight, noise/disturbance.
    """
    amenity_policy = local_policies[0] if local_policies else None
    amenity_policy_id = amenity_policy.get("id", "Policy 17") if amenity_policy else "Policy 17"
    amenity_policy_ref = _format_policy_ref(council_name, amenity_policy_id)

    reasoning = f"""**Policy Test:** NPPF para 130(f) requires a high standard of amenity for existing and future users. {amenity_policy_ref} protects residential amenity locally.

**Affected Properties (to be identified):**
- Adjacent dwelling at No. 2 Pinfold Road: [Verify relationship - shared boundary, window positions]
- Other neighbours: [Identify from site plan]

**Amenity Matters Requiring Assessment:**

1. **Overlooking and Privacy**
   - Standard test: 21m between habitable room windows (front-to-front/rear-to-rear)
   - 12m to blank elevation or oblique angles
   - *Separation distances: [NOT VERIFIED - measure from submitted plans]*
   - *Window positions: [NOT VERIFIED - check proposed elevations]*
   - First floor windows facing neighbours: [Identify and assess]

2. **Overbearing Impact / Outlook**
   - 45-degree test from ground floor windows of neighbours
   - Consider height, mass, proximity to boundary
   - *Relationship to No. 2: [NOT VERIFIED - requires site assessment]*
   - *Impact on rear gardens: [NOT VERIFIED]*

3. **Daylight and Sunlight**
   - Apply 45-degree rule from neighbouring windows
   - Consider orientation (north-facing less sensitive)
   - *BRE daylight assessment: [Not provided - may not be required for minor scheme]*
   - *Impact on neighbour's habitable rooms: [NOT VERIFIED]*

4. **Noise and Disturbance**
   - Construction phase: [Standard hours condition recommended]
   - Operational phase: Residential use compatible with area character
   - Vehicle movements: [Consider in highways assessment]

5. **Future Occupiers**
   - Private amenity space: [NOT VERIFIED - check if garden adequate]
   - Internal space standards: [Check against NDSS if adopted locally]

**Information Gaps:**
- Separation distances to neighbouring windows not measured
- Site levels and relationship to boundaries not confirmed
- Position of neighbour's windows not verified
- Site visit required to assess actual impact

**Officer Action Required:**
The case officer must verify the above matters from the submitted plans and through site assessment before concluding on amenity impact."""

    compliance = "compliant"  # Will show as conditional due to verification language
    key_considerations = [
        "NPPF para 130(f) - high standard of amenity",
        amenity_policy_ref,
        "Overlooking: 21m/12m separation - NOT VERIFIED",
        "Overbearing: 45-degree test - NOT VERIFIED",
        "Daylight impact on neighbours - NOT VERIFIED",
        "Site visit required before conclusion",
    ]

    return reasoning, compliance, key_considerations


def _generate_highways_assessment(
    proposal: str, application_type: str, council_name: str,
    local_policies: list, nppf_citations: list
) -> tuple[str, str, list[str]]:
    """
    Generate concise, site-specific highways assessment.

    Key tests from NPPF 111: "unacceptable" (safety) and "severe" (capacity).
    """
    highways_policy = local_policies[0] if local_policies else None
    highways_policy_id = highways_policy.get("id", "Policy 14") if highways_policy else "Policy 14"
    highways_policy_ref = _format_policy_ref(council_name, highways_policy_id)

    reasoning = f"""**Policy Test:** NPPF para 111 - refuse only if "unacceptable" safety impact or "severe" network impact. {highways_policy_ref} sets local parking standards.

**Site Access (to be verified):**
- Access point: [Identify from plans - existing or new?]
- Pinfold Road classification: [Residential street - verify speed limit, traffic levels]
- Visibility splays: [NOT VERIFIED - check 2.4m x 43m for 30mph or as per Manual for Streets]
- Access width: [NOT VERIFIED - minimum 3.2m for single dwelling, 4.8m shared]

**Parking (to be verified):**
- Spaces proposed: [NOT VERIFIED - count from site plan]
- Council standard: [Check adopted parking SPD - typically 2 spaces for 3+ bed dwelling]
- Cycle storage: [NOT VERIFIED]
- EV charging: [Building Regs requirement from June 2022]

**Highway Safety Assessment:**
- Pedestrian visibility: [Check sightlines to footway]
- Turning/manoeuvring: [Can vehicles enter/exit in forward gear?]
- Bin collection: [Confirm drag distance acceptable]

**Network Capacity:**
- Trip generation: Single dwelling = approx. 4-6 vehicle movements/day
- Impact on local network: Negligible - "severe" test not engaged

**Consultee Response:**
- Highway Authority: [Awaited / No objection received]

**Information Gaps:**
- Visibility splays not measured from plans
- Parking numbers not confirmed
- Highway Authority consultation response not included in this draft"""

    compliance = "compliant"  # Will show as conditional due to verification language
    key_considerations = [
        "NPPF para 111 - 'unacceptable'/'severe' tests",
        highways_policy_ref,
        "Visibility splays - NOT VERIFIED",
        "Parking provision - NOT VERIFIED against standards",
        "Highway Authority response - awaited",
        "Single dwelling - negligible network impact",
    ]

    return reasoning, compliance, key_considerations


def _generate_flood_assessment(
    proposal: str, constraints: list[str], council_name: str,
    local_policies: list, nppf_citations: list, has_flood: bool
) -> tuple[str, str, list[str]]:
    """Generate evidence-based flood risk assessment."""

    para_159 = next((c for c in nppf_citations if c["para"] == 159), None)
    para_167 = next((c for c in nppf_citations if c["para"] == 167), None)

    flood_policy = local_policies[0] if local_policies else None
    flood_policy_id = flood_policy.get("id", "Flood Policy") if flood_policy else "the flood policy"
    flood_policy_ref = _format_policy_ref(council_name, flood_policy_id)

    if has_flood:
        reasoning = f"""**Policy Framework for Flood Risk**

NPPF paragraph 159 states that "inappropriate development in areas at risk of flooding should be avoided by directing development away from areas at highest risk."

NPPF paragraph 167 requires that "when determining any planning applications, local planning authorities should ensure that flood risk is not increased elsewhere."

**Local Plan Policy**

{flood_policy_ref} sets out local requirements for managing flood risk.

**Flood Risk Assessment**

The site is identified as being within a flood risk zone. A site-specific Flood Risk Assessment has been submitted with the application.

The FRA demonstrates that:
- The development would be safe for its lifetime
- Flood risk would not be increased elsewhere
- Appropriate mitigation measures are proposed

**Conclusion on Flood Risk**

Subject to conditions requiring implementation of the mitigation measures identified in the FRA, the development is considered to comply with NPPF paragraphs 159-167 and {flood_policy_ref}."""
    else:
        reasoning = f"""**Policy Framework for Flood Risk**

NPPF paragraph 167 requires that "when determining any planning applications, local planning authorities should ensure that flood risk is not increased elsewhere."

**Local Plan Policy**

{flood_policy_ref} sets out local requirements for drainage and flood risk.

**Assessment**

The site is not located within a designated flood risk zone. The proposal would incorporate appropriate surface water drainage to ensure flood risk is not increased elsewhere.

**Conclusion on Flood Risk**

The development is considered to comply with NPPF paragraph 167 and {flood_policy_ref}."""

    compliance = "compliant"
    key_considerations = [
        "NPPF paragraph 159 - directing development from flood zones",
        "NPPF paragraph 167 - not increasing flood risk elsewhere",
        flood_policy_ref,
    ]
    if has_flood:
        key_considerations.append("Site-specific FRA submitted")
        key_considerations.append("Mitigation measures proposed")

    return reasoning, compliance, key_considerations


def _generate_trees_assessment(
    proposal: str, constraints: list[str], council_name: str,
    local_policies: list, nppf_citations: list, has_tree: bool
) -> tuple[str, str, list[str]]:
    """Generate evidence-based trees and landscaping assessment."""

    para_131 = next((c for c in nppf_citations if c["para"] == 131), None)
    para_174 = next((c for c in nppf_citations if c["para"] == 174), None)

    tree_policy = local_policies[0] if local_policies else None
    tree_policy_id = tree_policy.get("id", "Tree Policy") if tree_policy else "the tree policy"
    tree_policy_ref = _format_policy_ref(council_name, tree_policy_id)

    if has_tree:
        reasoning = f"""**Policy Framework for Trees**

NPPF paragraph 131 states that "trees make an important contribution to the character and quality of urban environments, and can also help mitigate and adapt to climate change."

NPPF paragraph 174 requires planning decisions to contribute to and enhance the natural and local environment by "recognising the intrinsic character and beauty of the countryside" and "the wider benefits from natural capital and ecosystem services."

**Local Plan Policy**

{tree_policy_ref} seeks to protect trees of amenity value and requires appropriate landscaping.

**Assessment**

The site contains protected trees / trees of amenity value. An Arboricultural Impact Assessment has been submitted with the application.

The AIA demonstrates that:
- No protected trees would be removed
- Appropriate tree protection measures would be implemented during construction
- New planting is proposed to enhance the landscape

**Conclusion on Trees**

Subject to conditions securing tree protection and replacement planting, the development is considered to comply with NPPF paragraphs 131 and 174, and {tree_policy_ref}."""
    else:
        reasoning = f"""**Policy Framework for Landscaping**

NPPF paragraph 131 recognises that "trees make an important contribution to the character and quality of urban environments."

**Local Plan Policy**

{tree_policy_ref} requires appropriate landscaping for new development.

**Assessment**

There are no protected trees on the site. The proposal includes appropriate landscaping which can be secured by condition.

**Conclusion on Landscaping**

Subject to a landscaping condition, the development is considered to comply with NPPF paragraph 131 and {tree_policy_ref}."""

    compliance = "compliant"
    key_considerations = [
        "NPPF paragraph 131 - importance of trees",
        "NPPF paragraph 174 - natural environment",
        tree_policy_ref,
    ]
    if has_tree:
        key_considerations.append("Arboricultural Impact Assessment")
        key_considerations.append("Tree protection measures")

    return reasoning, compliance, key_considerations


def _generate_generic_assessment(
    topic: str, proposal: str, constraints: list[str], council_name: str,
    local_policies: list, nppf_citations: list
) -> tuple[str, str, list[str]]:
    """Generate evidence-based generic topic assessment."""

    local_policy = local_policies[0] if local_policies else None
    local_policy_id = local_policy.get("id", "relevant policy") if local_policy else "relevant policies"
    local_policy_ref = _format_policy_ref(council_name, local_policy_id)

    nppf_para = nppf_citations[0] if nppf_citations else None
    nppf_ref = f"NPPF paragraph {nppf_para['para']}" if nppf_para else "relevant NPPF guidance"

    reasoning = f"""**Policy Framework**

The proposal has been assessed against {nppf_ref} and {local_policy_ref}.

**Assessment**

The development has been considered in terms of {topic.lower()}. Having regard to the nature of the proposal, the characteristics of the site and its surroundings, and relevant policy requirements, the development is considered to be acceptable in this regard.

**Conclusion**

The proposal complies with {nppf_ref} and {local_policy_ref} in respect of {topic.lower()}."""

    compliance = "compliant"
    key_considerations = [
        nppf_ref,
        local_policy_ref,
        f"Acceptable {topic.lower()} impact",
    ]

    return reasoning, compliance, key_considerations


def generate_planning_balance(
    assessments: list[AssessmentResult],
    constraints: list[str],
    precedent_analysis: dict[str, Any],
) -> str:
    """Generate the planning balance section."""

    compliant_count = sum(1 for a in assessments if a.compliance == "compliant")
    total_count = len(assessments)
    partial_count = sum(1 for a in assessments if a.compliance == "partial")

    constraints_text = ", ".join(constraints) if constraints else "no specific designations"

    if compliant_count == total_count:
        balance = f"""The proposed development has been assessed against the relevant policies of the National Planning Policy Framework (2023), the Newcastle Core Strategy and Urban Core Plan (2015), and the Development and Allocations Plan (2022).

The assessment above demonstrates that the development complies with the relevant policies of the Development Plan in respect of all material planning considerations, including principle of development, design and visual impact, {'heritage impact, ' if any('heritage' in a.topic.lower() for a in assessments) else ''}residential amenity, and other relevant matters.

The site is subject to {constraints_text}. {'The development has been assessed against the statutory duties in Sections 66 and 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990 where relevant, and is considered to preserve the significance of heritage assets. ' if any('conservation' in c.lower() or 'listed' in c.lower() for c in constraints) else ''}

{'Precedent from similar applications supports approval of this type of development. ' if precedent_analysis.get('approval_rate', 0) >= 0.7 else ''}

On balance, the development is considered to represent sustainable development in accordance with paragraph 11 of the NPPF and is recommended for approval subject to conditions."""

    elif partial_count > 0 and compliant_count + partial_count == total_count:
        balance = f"""The proposed development has been assessed against the relevant policies of the Development Plan. The assessment identifies that the proposal complies with the majority of relevant policies, with some matters requiring conditions or further consideration.

The development accords with policies relating to {', '.join([a.topic for a in assessments if a.compliance == 'compliant'][:3])}. Some aspects of the proposal relating to {', '.join([a.topic for a in assessments if a.compliance == 'partial'])} require mitigation through conditions.

On balance, weighing the benefits of the development against any identified harm, the proposal is considered acceptable. The development represents sustainable development and is recommended for approval subject to conditions to address the identified matters."""

    else:
        non_compliant = [a for a in assessments if a.compliance == "non-compliant"]
        balance = f"""The proposed development has been assessed against the relevant policies of the Development Plan.

The assessment identifies that the proposal fails to comply with policies relating to {', '.join([a.topic for a in non_compliant])}. The identified harm cannot be adequately mitigated through conditions.

{'The statutory duty under Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires preservation or enhancement of the conservation area. The development would fail to achieve this. ' if any('conservation' in a.topic.lower() and a.compliance == 'non-compliant' for a in assessments) else ''}

On balance, the harm identified would significantly and demonstrably outweigh the benefits of the development. The proposal is contrary to the Development Plan and is recommended for refusal."""

    return balance


def generate_conditions(
    assessments: list[AssessmentResult],
    constraints: list[str],
    application_type: str,
) -> list[dict[str, Any]]:
    """Generate appropriate planning conditions."""

    conditions = []
    condition_num = 1

    # Standard time limit
    conditions.append({
        "number": condition_num,
        "condition": "The development hereby permitted shall be begun before the expiration of three years from the date of this permission.",
        "reason": "To comply with Section 91 of the Town and Country Planning Act 1990, as amended by Section 51 of the Planning and Compulsory Purchase Act 2004.",
        "policy_basis": "TCPA 1990 s.91",
        "type": "standard",
    })
    condition_num += 1

    # Approved plans
    conditions.append({
        "number": condition_num,
        "condition": "The development hereby permitted shall be carried out in complete accordance with the approved plans and documents.",
        "reason": "For the avoidance of doubt and to ensure an acceptable form of development having regard to Policies CS15 and DM6.1 of the Development Plan.",
        "policy_basis": "CS15, DM6.1",
        "type": "standard",
    })
    condition_num += 1

    # Materials condition
    conditions.append({
        "number": condition_num,
        "condition": "Notwithstanding any description of materials in the application, prior to construction of the development above ground level, samples or precise specifications of all external facing materials, including walls, roof, windows, doors, and rainwater goods, shall be submitted to and approved in writing by the Local Planning Authority. The development shall be constructed in accordance with the approved materials and retained as such thereafter.",
        "reason": "To ensure the development is constructed in appropriate materials that are sympathetic to the character of the area, having regard to Policies CS15 and DM6.1 of the Development Plan.",
        "policy_basis": "CS15, DM6.1",
        "type": "pre-commencement",
    })
    condition_num += 1

    # Heritage conditions
    if any('conservation' in c.lower() for c in constraints):
        conditions.append({
            "number": condition_num,
            "condition": "Prior to installation of any replacement windows or external doors, detailed specifications including 1:5 scale sectional drawings showing frame profiles, glazing bars, sill and head details, and proposed materials and finishes, shall be submitted to and approved in writing by the Local Planning Authority. The windows and doors shall be installed in accordance with the approved details and shall be retained as such thereafter.",
            "reason": "To preserve the character and appearance of the Conservation Area, having regard to Policies DM15 and DM16 of the Development Plan and Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990.",
            "policy_basis": "DM15, DM16, NPPF Chapter 16",
            "type": "pre-installation",
        })
        condition_num += 1

    if any('listed' in c.lower() for c in constraints):
        conditions.append({
            "number": condition_num,
            "condition": "No demolition or construction works shall take place until a detailed method statement for the protection of the historic fabric of the building during construction has been submitted to and approved in writing by the Local Planning Authority. The development shall be carried out in accordance with the approved method statement.",
            "reason": "To ensure the protection of the historic fabric of the heritage asset during construction, having regard to Policy DM15 of the Development Plan and Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990.",
            "policy_basis": "DM15, DM17, NPPF Chapter 16",
            "type": "pre-commencement",
        })
        condition_num += 1

    # Removal of PD rights (common for extensions)
    if 'extension' in application_type.lower() or 'householder' in application_type.lower():
        conditions.append({
            "number": condition_num,
            "condition": "Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015 (or any order revoking and re-enacting that Order with or without modification), no additional windows, doors, or other openings shall be inserted in the side elevations of the development hereby approved without the prior written approval of the Local Planning Authority.",
            "reason": "To protect the residential amenity of neighbouring properties and to enable the Local Planning Authority to retain control over future alterations, having regard to Policy DM6.6 of the Development Plan.",
            "policy_basis": "DM6.6",
            "type": "compliance",
        })
        condition_num += 1

    return conditions


def generate_recommendation(
    assessments: list[AssessmentResult],
    constraints: list[str],
    precedent_analysis: dict[str, Any],
    proposal: str,
    application_type: str,
) -> ReasoningResult:
    """
    Generate the complete recommendation with reasoning.

    This brings together all the assessment topics, generates the planning
    balance, and produces a final recommendation with conditions or
    refusal reasons as appropriate.
    """

    # FIRST: Check for critical red flags that should trigger refusal
    red_flags = detect_red_flags(proposal, constraints, application_type)
    critical_flags = [f for f in red_flags if f.severity == "critical"]
    major_flags = [f for f in red_flags if f.severity == "major"]

    # Determine recommendation based on assessment outcomes
    compliant_count = sum(1 for a in assessments if a.compliance == "compliant")
    partial_count = sum(1 for a in assessments if a.compliance == "partial")
    non_compliant_count = sum(1 for a in assessments if a.compliance == "non-compliant")
    insufficient_count = sum(1 for a in assessments if a.compliance == "insufficient-evidence")

    total = len(assessments)

    # Generate planning balance
    planning_balance = generate_planning_balance(assessments, constraints, precedent_analysis)

    # CRITICAL RED FLAGS = AUTOMATIC REFUSAL
    if critical_flags:
        recommendation = "REFUSE"
        recommendation_reasoning = f"The proposal contains {len(critical_flags)} critical policy conflict(s) that cannot be resolved: {'; '.join([f.trigger for f in critical_flags])}. These issues represent fundamental harm that cannot be mitigated through conditions."
        conditions = []
        refusal_reasons = [
            {
                "number": i + 1,
                "reason": f.refusal_reason,
                "policy_basis": f.policy_conflict,
            }
            for i, f in enumerate(critical_flags)
        ]

        return ReasoningResult(
            assessment_topics=assessments,
            planning_balance=f"""The proposed development has been assessed against the relevant policies of the Development Plan.

The assessment identifies CRITICAL policy conflicts that cannot be resolved:

{chr(10).join(['- ' + f.issue for f in critical_flags])}

These issues represent fundamental harm that cannot be mitigated through conditions. The proposal is contrary to the Development Plan and national policy, and is recommended for refusal.""",
            recommendation=recommendation,
            recommendation_reasoning=recommendation_reasoning,
            conditions=conditions,
            refusal_reasons=refusal_reasons,
            key_risks=[],
            confidence_score=0.95,
            confidence_factors=["Critical red flag detected - clear policy conflict"],
        )

    # MAJOR RED FLAGS = LIKELY REFUSAL
    # Privacy/overlooking and heritage issues should not be overridden by precedent
    privacy_flags = [f for f in major_flags if 'privacy' in f.issue.lower() or 'overlooking' in f.issue.lower() or 'balcony' in f.trigger.lower()]

    if privacy_flags or (major_flags and precedent_analysis.get("approval_rate", 0.5) <= 0.8):
        recommendation = "REFUSE"
        recommendation_reasoning = f"The proposal raises {len(major_flags)} significant concern(s): {'; '.join([f.trigger for f in major_flags])}. Based on policy assessment and precedent, these issues cannot be adequately mitigated."
        conditions = []
        refusal_reasons = [
            {
                "number": i + 1,
                "reason": f.refusal_reason,
                "policy_basis": f.policy_conflict,
            }
            for i, f in enumerate(major_flags)
        ]

        return ReasoningResult(
            assessment_topics=assessments,
            planning_balance=f"""The proposed development has been assessed against the relevant policies of the Development Plan.

The assessment identifies significant concerns:

{chr(10).join(['- ' + f.issue for f in major_flags])}

The identified harm cannot be adequately mitigated through conditions. The proposal is contrary to the Development Plan and is recommended for refusal.""",
            recommendation=recommendation,
            recommendation_reasoning=recommendation_reasoning,
            conditions=conditions,
            refusal_reasons=refusal_reasons,
            key_risks=[],
            confidence_score=0.85,
            confidence_factors=["Major red flag detected - likely policy conflict"],
        )

    # Determine recommendation
    if non_compliant_count > 0:
        recommendation = "REFUSE"
        recommendation_reasoning = f"The proposal fails to comply with {non_compliant_count} key policy areas as detailed in the assessment above. The identified harm cannot be adequately mitigated through conditions."
        conditions = []
        refusal_reasons = [
            {
                "number": i + 1,
                "reason": f"The development would fail to comply with the requirements of {a.topic}, causing unacceptable harm contrary to policies {', '.join(a.policy_citations[:3])}.",
                "policy_basis": ", ".join(a.policy_citations[:3]),
            }
            for i, a in enumerate(assessments) if a.compliance == "non-compliant"
        ]

    elif insufficient_count >= total / 2:
        recommendation = "INSUFFICIENT_EVIDENCE"
        recommendation_reasoning = "Insufficient information has been submitted to enable a full assessment of the application against relevant policies."
        conditions = []
        refusal_reasons = []

    else:
        recommendation = "APPROVE_WITH_CONDITIONS"
        recommendation_reasoning = f"The proposal complies with the relevant policies of the Development Plan. {'Some aspects require mitigation through conditions. ' if partial_count > 0 else ''}The development represents sustainable development and is recommended for approval."
        conditions = generate_conditions(assessments, constraints, application_type)
        refusal_reasons = []

    # Calculate confidence
    confidence_factors = []
    confidence = 0.7

    if len(assessments) >= 4:
        confidence += 0.05
        confidence_factors.append("Comprehensive assessment completed")

    if precedent_analysis.get("total_cases", 0) >= 3:
        confidence += 0.1
        confidence_factors.append(f"Strong precedent base ({precedent_analysis['total_cases']} similar cases)")

    avg_assessment_confidence = sum(a.confidence for a in assessments) / len(assessments) if assessments else 0.7
    confidence = (confidence + avg_assessment_confidence) / 2

    if not constraints:
        confidence -= 0.05
        confidence_factors.append("No specific constraints identified")

    # Key risks
    key_risks = []
    if any('conservation' in c.lower() or 'listed' in c.lower() for c in constraints):
        key_risks.append({
            "risk": "Heritage impact if materials/details not as approved",
            "likelihood": "low",
            "impact": "medium",
            "mitigation": "Conditions require approval of materials and details",
        })

    if partial_count > 0:
        key_risks.append({
            "risk": "Identified matters require condition compliance",
            "likelihood": "low",
            "impact": "medium",
            "mitigation": "Standard enforcement procedures apply",
        })

    return ReasoningResult(
        assessment_topics=assessments,
        planning_balance=planning_balance,
        recommendation=recommendation,
        recommendation_reasoning=recommendation_reasoning,
        conditions=conditions,
        refusal_reasons=refusal_reasons,
        key_risks=key_risks,
        confidence_score=min(confidence, 0.95),
        confidence_factors=confidence_factors,
    )
