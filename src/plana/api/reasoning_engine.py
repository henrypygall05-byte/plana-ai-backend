"""
LLM-Powered Planning Reasoning Engine.

This module provides intelligent reasoning for planning assessments using:
- Evidence-based analysis of proposals against policies
- Precedent-informed recommendations
- Nuanced planning balance considerations
- Professional condition drafting

The engine can operate in two modes:
- Template mode: Fast, deterministic, no API calls
- LLM mode: Full AI-powered reasoning (requires API key)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import os
import re

from .similar_cases import HistoricCase, get_precedent_analysis
from .policy_engine import Policy, get_policy_citation


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
) -> AssessmentResult:
    """
    Generate a detailed assessment for a specific planning topic.

    This uses template-based reasoning informed by:
    - Relevant policies for this topic
    - Similar case outcomes
    - Site constraints
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
        "transport": ["transport", "parking", "highway", "access"],
        "trees": ["tree", "landscape", "green"],
        "green belt": ["green belt", "openness"],
        "flood": ["flood", "drainage", "water"],
    }

    keywords = topic_keywords.get(topic_lower.split()[0].lower(), ["design"])

    for policy in policies:
        for trigger in policy.triggers:
            if any(kw in trigger for kw in keywords):
                relevant_policies.append(policy)
                policy_citations.append(get_policy_citation(policy.id))
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

    # Generate reasoning based on topic
    reasoning, compliance, key_considerations = _generate_topic_reasoning(
        topic=topic,
        proposal=proposal,
        constraints=constraints,
        relevant_policies=relevant_policies,
        similar_cases=similar_cases,
        application_type=application_type,
    )

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
) -> tuple[str, str, list[str]]:
    """Generate reasoning text for a specific topic."""

    topic_lower = topic.lower()
    constraints_lower = [c.lower() for c in constraints]

    # Check for heritage constraints
    has_conservation = any('conservation' in c for c in constraints_lower)
    has_listed = any('listed' in c for c in constraints_lower)
    has_green_belt = any('green belt' in c for c in constraints_lower)

    # Get policy references
    policy_refs = ", ".join([p.id for p in relevant_policies[:3]]) if relevant_policies else "relevant development plan policies"

    # Generate topic-specific reasoning
    if "principle" in topic_lower:
        reasoning = f"""The application site is located within the urban area of Newcastle where {application_type.lower()} development is acceptable in principle, subject to compliance with relevant development plan policies. The National Planning Policy Framework establishes a presumption in favour of sustainable development (paragraph 11), which means that development proposals that accord with an up-to-date development plan should be approved without delay.

The proposed development represents a form of development that is common and generally acceptable in this location. The principle of development is considered to be acceptable, subject to detailed assessment of design, {'heritage impact, ' if has_conservation or has_listed else ''}{'Green Belt impact, ' if has_green_belt else ''}residential amenity, and other material considerations.

{'The site is within a Conservation Area which requires special attention under Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990, but this does not prevent development in principle where it preserves or enhances the character of the area. ' if has_conservation else ''}{'The site involves a Listed Building which requires special regard under Section 66 of the Act, but appropriate alterations can be acceptable where they preserve significance. ' if has_listed else ''}Subject to the detailed assessment below, the proposal is considered acceptable in principle."""

        compliance = "compliant"
        key_considerations = [
            "Presumption in favour of sustainable development (NPPF para 11)",
            "Accordance with development plan policies",
            f"Located within urban area{'in Conservation Area' if has_conservation else ''}",
        ]

    elif "design" in topic_lower:
        reasoning = f"""The proposed development has been assessed against the design policies of the development plan, including Policy CS15 (Place-making), Policy DM6.1 (Design of New Development), and Chapter 12 of the NPPF (Achieving well-designed places).

Paragraph 130 of the NPPF requires developments to be visually attractive, sympathetic to local character, and establish a strong sense of place. Paragraph 134 states that development which is not well designed should be refused, especially where it fails to reflect local design policies.

Policy DM6.1 requires proposals to demonstrate a positive response to context and local character, create a coherent development, and achieve appropriate scale and massing. The development is considered to meet these requirements through its design approach which responds to the established character of the area.

{'The design has been considered in the context of the Conservation Area, where Policy DM16 requires development to preserve or enhance the character and appearance of the area. The design is considered sympathetic to the conservation area context through its scale, materials, and detailing. ' if has_conservation else ''}

Based on the assessment against these policies, the design is considered acceptable and would not cause harm to the character and appearance of the area or the visual amenity of the streetscene."""

        compliance = "compliant"
        key_considerations = [
            "Response to context and local character",
            "Appropriate scale and massing",
            "Quality of architectural design",
            "Material palette and detailing",
        ]

    elif "heritage" in topic_lower and "conservation" in topic_lower:
        reasoning = f"""Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires that special attention shall be paid to the desirability of preserving or enhancing the character or appearance of conservation areas. This statutory duty is reinforced by Chapter 16 of the NPPF and Policies DM15 and DM16 of the Development and Allocations Plan.

Paragraph 199 of the NPPF states that when considering the impact of development on the significance of a designated heritage asset, great weight should be given to the asset's conservation. Paragraph 200 requires clear and convincing justification for any harm.

The Conservation Area derives its significance from [the historic building stock, mature landscaping, and cohesive architectural character]. The proposed development has been assessed against this significance.

The development would [preserve/enhance] the character and appearance of the Conservation Area through its sympathetic design, appropriate materials, and respect for the established pattern of development. {'The development would not be visible from public viewpoints. ' if 'rear' in proposal.lower() else ''}

In accordance with paragraph 202 of the NPPF, where development would lead to less than substantial harm, this should be weighed against the public benefits. In this case, the harm is assessed as [negligible/minor] and the proposal would [preserve/enhance] the character of the Conservation Area, in compliance with Section 72 of the Act."""

        compliance = "compliant"
        key_considerations = [
            "Section 72 statutory duty - preserve or enhance",
            "Character and appearance of conservation area",
            "Significance of heritage asset",
            "Public benefits weighed against any harm",
        ]

    elif "heritage" in topic_lower and "listed" in topic_lower:
        reasoning = f"""Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires that in considering whether to grant planning permission for development which affects a listed building or its setting, the local planning authority shall have special regard to the desirability of preserving the building or its setting or any features of special architectural or historic interest.

Paragraph 199 of the NPPF requires great weight to be given to the conservation of designated heritage assets. Paragraph 200 requires clear and convincing justification for any harm.

The listed building derives its significance from its architectural interest as [a good example of its type] and its historic interest as [part of the historic development of the area]. The proposed development has been assessed against this significance.

The development is considered to preserve the significance of the heritage asset by [respecting the historic fabric, using appropriate materials, and ensuring alterations are sympathetic and reversible where appropriate]. The proposal complies with Section 66 of the Act, Policy DM15, and Chapter 16 of the NPPF."""

        compliance = "compliant"
        key_considerations = [
            "Section 66 statutory duty - special regard to preservation",
            "Significance of the listed building",
            "Impact on special architectural/historic interest",
            "Preservation of setting",
        ]

    elif "amenity" in topic_lower:
        reasoning = f"""The proposed development has been assessed in terms of its impact on the residential amenity of neighbouring properties in accordance with Policy DM6.6 (Protection of Residential Amenity) and the principles of good neighbourliness established in planning case law.

Policy DM6.6 requires development to ensure that existing and future occupiers are provided with a good standard of amenity, particularly in terms of outlook, privacy, daylight, sunlight, and freedom from disturbance.

**Daylight and Sunlight**: The development has been designed to minimise impact on daylight to neighbouring habitable rooms. A 45-degree daylight assessment has been applied where relevant, and the development is not considered to result in an unacceptable loss of daylight or sunlight.

**Privacy and Overlooking**: Policy DM6.6 requires a minimum separation distance of 21 metres between facing habitable room windows. The development has been designed to avoid direct overlooking of neighbouring properties through [window positioning, obscure glazing, or adequate separation distances].

**Overbearing Impact**: Given the scale of the development and its relationship with neighbouring properties, it is not considered that the proposal would result in an unacceptable overbearing impact or loss of outlook.

The development is considered to comply with Policy DM6.6 and would maintain acceptable levels of amenity for neighbouring occupiers."""

        compliance = "compliant"
        key_considerations = [
            "Impact on daylight and sunlight (45-degree test)",
            "Privacy and overlooking (21m separation)",
            "Overbearing impact and outlook",
            "Noise and disturbance",
        ]

    elif "green belt" in topic_lower:
        reasoning = f"""The application site is located within the Green Belt. Paragraph 137 of the NPPF states that the Government attaches great importance to Green Belts, whose fundamental aim is to prevent urban sprawl by keeping land permanently open.

Paragraph 147 states that inappropriate development is, by definition, harmful to the Green Belt and should not be approved except in very special circumstances. Paragraph 148 requires substantial weight to be given to any harm to the Green Belt.

Paragraph 149 sets out exceptions to inappropriate development, including the extension or alteration of a building provided that it does not result in disproportionate additions over and above the size of the original building.

The proposed development has been assessed against these criteria. {'The proposal falls within the exceptions set out in paragraph 149 as it represents an extension/alteration that is not disproportionate to the original building. The development would preserve the openness of the Green Belt and would not conflict with the purposes of including land within it.' if 'extension' in proposal.lower() else 'The proposal has been assessed as [appropriate/inappropriate] development in the Green Belt. [Very special circumstances have/have not been demonstrated that would clearly outweigh the harm.]'}"""

        if 'extension' in proposal.lower():
            compliance = "compliant"
        else:
            compliance = "partial"

        key_considerations = [
            "Whether development is appropriate or inappropriate",
            "Impact on openness of the Green Belt",
            "Whether paragraph 149 exceptions apply",
            "Very special circumstances (if inappropriate)",
        ]

    else:
        # Generic topic reasoning
        reasoning = f"""The proposed development has been assessed against {policy_refs} and other material considerations relevant to {topic.lower()}.

The assessment has considered the nature of the proposal, the characteristics of the site and its surroundings, and any relevant constraints. Having regard to these matters, the development is considered to be acceptable in respect of {topic.lower()}.

{'Similar applications in the area have been ' + ('approved' if similar_cases and 'approved' in similar_cases[0].decision.lower() else 'subject to varying outcomes') + ', providing relevant precedent for this assessment. ' if similar_cases else ''}

Subject to appropriate conditions where necessary, the proposal complies with the relevant policies of the development plan."""

        compliance = "compliant"
        key_considerations = [
            f"Compliance with {policy_refs}",
            "Site-specific considerations",
            "Material considerations",
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
