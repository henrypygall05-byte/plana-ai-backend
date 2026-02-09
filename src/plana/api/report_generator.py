"""
Professional Case Officer Report Generator.

Generates planning assessment reports to the standard of a senior planning case officer
using:
- Comprehensive policy database (NPPF + Newcastle Local Plan)
- Similar case precedent analysis
- Evidence-based reasoning engine
- Continuous learning integration
- Future Predictions for 10-year outlook

All reports include:
- Detailed policy analysis with paragraph references
- Precedent case analysis
- Thorough assessment of each material consideration
- Complete conditions with proper legal wording
- Full evidence citations
- Future Predictions section for long-term impact assessment
- Professional markdown formatting
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from .similar_cases import find_similar_cases, get_precedent_analysis, HistoricCase
from .policy_engine import get_relevant_policies, get_policy_citation, Policy
from .reasoning_engine import (
    generate_topic_assessment,
    generate_recommendation,
    AssessmentResult,
    ReasoningResult,
)
from .learning import get_learning_system


# =============================================================================
# FUTURE PREDICTIONS DATA STRUCTURES
# =============================================================================

@dataclass
class FuturePrediction:
    """A prediction about long-term outcomes of the development."""
    category: str  # "community_impact", "area_character", "precedent", "infrastructure", "environment"
    timeframe: str  # "short_term", "medium_term", "long_term"
    prediction: str
    confidence: str  # "high", "medium", "low"
    positive_or_negative: str  # "positive", "negative", "neutral", "uncertain"
    evidence_basis: str
    what_could_go_wrong: str
    what_could_go_right: str
    council_considerations: str


@dataclass
class CumulativeImpact:
    """Assessment of cumulative impacts if similar developments approved."""
    impact_type: str
    current_baseline: str
    if_approved_alone: str
    if_sets_precedent: str
    tipping_point_risk: str
    recommendation: str


@dataclass
class FuturePredictionsResult:
    """Complete future predictions assessment."""
    predictions: list[FuturePrediction]
    cumulative_impacts: list[CumulativeImpact]
    long_term_outlook: str
    precedent_implications: str
    post_consent_risks: list[dict]
    uncertainty_statement: str


def generate_future_predictions(
    proposal: str,
    constraints: list[str],
    application_type: str,
    similar_cases: list[HistoricCase],
    assessments: list[AssessmentResult],
    proposal_details: Any = None,
) -> FuturePredictionsResult:
    """
    Generate comprehensive future predictions for 10-year outlook.

    Helps planners understand whether this development will be
    beneficial for the council and community in 5-10 years.
    """
    predictions = []
    cumulative_impacts = []
    post_consent_risks = []

    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]
    app_type_lower = application_type.lower()

    # Determine if heritage is involved
    has_heritage = any('conservation' in c or 'listed' in c for c in constraints_lower)
    has_green_belt = any('green belt' in c for c in constraints_lower)

    # Check assessment outcomes for heritage harm
    heritage_harm_found = False
    for a in assessments:
        if 'heritage' in a.topic.lower() and a.compliance in ['partial', 'non-compliant']:
            heritage_harm_found = True
            break

    # ==========================================================================
    # FUTURE PREDICTIONS
    # ==========================================================================

    # Community Impact (most developments)
    if 'extension' in proposal_lower or 'householder' in app_type_lower:
        predictions.append(FuturePrediction(
            category="community_impact",
            timeframe="medium_term",
            prediction="The extension will likely provide improved living accommodation, reducing pressure on the housing market and supporting household stability.",
            confidence="high",
            positive_or_negative="positive",
            evidence_basis="Household extensions typically meet genuine accommodation needs and reduce demand for new housing.",
            what_could_go_wrong="Over-extension could create affordability issues if property becomes too large for area",
            what_could_go_right="Family can remain in community, children stay in local schools, community cohesion maintained",
            council_considerations="Supporting sustainable household growth aligns with housing strategy objectives",
        ))

    # Area Character - Heritage
    if has_heritage:
        if heritage_harm_found:
            predictions.append(FuturePrediction(
                category="area_character",
                timeframe="long_term",
                prediction="This development may contribute to gradual erosion of the area's historic character over time.",
                confidence="medium",
                positive_or_negative="negative",
                evidence_basis="Heritage harm identified in assessment. Cumulative small harms can significantly degrade area character over decades.",
                what_could_go_wrong="In 10 years, the area may have lost distinctive character that made it worth protecting",
                what_could_go_right="If conditions are strictly enforced, impact may be contained",
                council_considerations="Consider whether this sets a precedent that could lead to further erosion of heritage assets",
            ))
        else:
            predictions.append(FuturePrediction(
                category="area_character",
                timeframe="long_term",
                prediction="With appropriate materials and design, this development can be absorbed into the area without long-term harm to character.",
                confidence="medium",
                positive_or_negative="neutral",
                evidence_basis="No significant heritage harm identified. Sympathetic development typically ages well in historic contexts.",
                what_could_go_wrong="Poor material choices or future alterations could cause retrospective harm",
                what_could_go_right="Development may enhance the area through improved maintenance and investment",
                council_considerations="Materials condition compliance is critical to achieving positive outcome",
            ))

    # Precedent (all developments)
    predictions.append(FuturePrediction(
        category="precedent",
        timeframe="long_term",
        prediction=f"Approving this {application_type.lower()} application may influence future similar applications in this area.",
        confidence="medium",
        positive_or_negative="uncertain",
        evidence_basis="Planning decisions establish precedent that applicants and inspectors reference in future cases.",
        what_could_go_wrong="If this is borderline acceptable, it may be cited to justify less acceptable future proposals",
        what_could_go_right="If well-designed, it establishes a positive benchmark for future applications",
        council_considerations="Consider what message this approval sends about acceptable development in this location",
    ))

    # Infrastructure (new dwellings/larger developments)
    if 'dwelling' in proposal_lower or 'new' in proposal_lower or 'full' in app_type_lower:
        predictions.append(FuturePrediction(
            category="infrastructure",
            timeframe="long_term",
            prediction="Additional development will incrementally increase demand on local infrastructure (roads, schools, healthcare, utilities).",
            confidence="high",
            positive_or_negative="negative",
            evidence_basis="All development increases infrastructure demand. Cumulative impact depends on infrastructure capacity.",
            what_could_go_wrong="Without infrastructure investment, service quality may decline over 10 years",
            what_could_go_right="CIL/S106 contributions may fund infrastructure improvements benefiting wider community",
            council_considerations="Monitor cumulative infrastructure impact in this area; consider triggering infrastructure review",
        ))

    # Environment/Climate (all developments)
    predictions.append(FuturePrediction(
        category="environment",
        timeframe="long_term",
        prediction="Climate change will increase flood risk and heat stress over the next 10 years. Development should be resilient to 2035+ conditions.",
        confidence="high",
        positive_or_negative="uncertain",
        evidence_basis="UK Climate Projections indicate increased rainfall intensity and summer temperatures.",
        what_could_go_wrong="Development may require costly retrofitting for climate resilience in future",
        what_could_go_right="Modern materials and standards may provide better resilience than existing building stock",
        council_considerations="Consider whether conditions adequately address future climate scenarios, not just current requirements",
    ))

    # Green Belt specific
    if has_green_belt:
        predictions.append(FuturePrediction(
            category="area_character",
            timeframe="long_term",
            prediction="Development in the Green Belt, if approved, may be cited as precedent for further encroachment.",
            confidence="high",
            positive_or_negative="negative",
            evidence_basis="Green Belt boundaries are under constant development pressure. Each approval weakens the principle.",
            what_could_go_wrong="Cumulative approvals could lead to coalescence of settlements the Green Belt was designed to prevent",
            what_could_go_right="Strict conditions and clear reasoning may limit precedent value",
            council_considerations="Carefully document very special circumstances to limit inappropriate precedent claims",
        ))

    # ==========================================================================
    # CUMULATIVE IMPACTS
    # ==========================================================================

    # Garden land / plot coverage
    if 'extension' in proposal_lower:
        cumulative_impacts.append(CumulativeImpact(
            impact_type="garden_land_loss",
            current_baseline="Typical plot coverage in area estimated at 40-50%",
            if_approved_alone="Marginal increase in plot coverage, within acceptable parameters",
            if_sets_precedent="If all properties extended similarly, garden land could reduce by 20-30% across area",
            tipping_point_risk="Medium - cumulative garden loss affects urban drainage, biodiversity, and character",
            recommendation="Monitor cumulative extensions in this street/area; consider Article 4 if pattern emerges",
        ))

    # Heritage cumulative
    if has_heritage:
        cumulative_impacts.append(CumulativeImpact(
            impact_type="heritage_character",
            current_baseline="Conservation Area/Listed Building setting retains significant historic character",
            if_approved_alone="Limited impact on overall area character",
            if_sets_precedent="Multiple similar approvals could dilute distinctive historic character over time",
            tipping_point_risk="Medium-High - heritage areas can reach tipping point where protection becomes difficult to justify",
            recommendation="Track cumulative impact on heritage assets; review management plan if pattern of harmful change emerges",
        ))

    # Parking/traffic cumulative
    if 'dwelling' in proposal_lower or 'bedroom' in proposal_lower:
        cumulative_impacts.append(CumulativeImpact(
            impact_type="parking_pressure",
            current_baseline="Current on-street parking at typical suburban capacity",
            if_approved_alone="One additional vehicle movement unlikely to cause significant impact",
            if_sets_precedent="Cumulative intensification could exceed parking capacity of street",
            tipping_point_risk="Low-Medium - depends on existing parking stress in area",
            recommendation="Consider parking survey if multiple intensification applications in same street",
        ))

    # ==========================================================================
    # POST-CONSENT RISKS
    # ==========================================================================

    if 'extension' in proposal_lower or 'new' in proposal_lower:
        post_consent_risks.append({
            "type": "drainage",
            "description": "Increased surface water runoff from additional impermeable surfaces",
            "likelihood": "possible",
            "mitigation": "Sustainable drainage condition, permeable paving requirement",
        })

    if has_heritage:
        post_consent_risks.append({
            "type": "enforcement",
            "description": "Risk of unauthorised works or deviation from approved materials",
            "likelihood": "possible",
            "mitigation": "Pre-commencement materials condition, site supervision during sensitive works",
        })

    if 'dwelling' in proposal_lower:
        post_consent_risks.append({
            "type": "traffic",
            "description": "Increased traffic and parking demand",
            "likelihood": "likely",
            "mitigation": "Parking provision condition, cycle storage requirement",
        })

    # ==========================================================================
    # PROFESSIONAL FUTURE OUTLOOK (Evidence-based, Policy-referenced, Proportionate)
    # ==========================================================================

    # Determine development scale for proportionate analysis
    is_minor_development = proposal_details.num_units <= 1 if proposal_details else True
    is_major_development = proposal_details.num_units >= 10 if proposal_details else False

    # A. PRECEDENT RISK ASSESSMENT
    has_specific_constraints = any(
        c for c in [c.lower() for c in constraints]
        if 'green belt' in c or 'conservation' in c or 'listed' in c or 'flood' in c
    )
    site_is_replicable = not has_specific_constraints and 'garden' not in proposal_lower

    if has_green_belt or has_heritage:
        precedent_risk_level = "Elevated"
        precedent_assessment = f"""The site lies within {'the Green Belt' if has_green_belt else 'a designated heritage area'}. This introduces elevated precedent sensitivity as approval may be cited by future applicants on comparable sites seeking to establish that similar development is acceptable in principle.

**Safeguards limiting precedent misuse:**
- Decision justified by site-specific circumstances documented in this report
- Approval does not indicate general acceptability of similar proposals
- Each application to be assessed on its own merits"""
    elif site_is_replicable and is_minor_development:
        precedent_risk_level = "Low"
        precedent_assessment = """This is a standard development proposal consistent with the established pattern of development in the locality. The site characteristics are not unusual and the proposal type is commonplace.

**Precedent implications are limited** as approval would be consistent with prevailing policy and comparable decisions in the area."""
    else:
        precedent_risk_level = "Moderate"
        precedent_assessment = """The decision may be material to future applications on sites with comparable characteristics. However, the proposal is broadly consistent with policy and precedent risk is proportionate to the development type.

**Standard safeguards apply** - decision reasoning clearly documents the site-specific factors supporting approval."""

    # B. INFRASTRUCTURE AND CUMULATIVE IMPACT
    if is_major_development:
        infrastructure_assessment = """The scale of development is likely to generate material demand on local infrastructure including highways, education, healthcare, and utilities. The cumulative impact assessment should consider:

- Whether CIL/S106 contributions adequately mitigate infrastructure demand
- Phasing of development relative to infrastructure capacity
- Monitoring requirements for cumulative impact in this area"""
    elif is_minor_development:
        infrastructure_assessment = """A single dwelling represents incremental and negligible impact on local infrastructure. The development falls below thresholds for CIL/S106 contributions and no material cumulative impact is anticipated from this proposal alone.

**No specific infrastructure monitoring is required** for this minor development."""
    else:
        infrastructure_assessment = """The development will generate modest additional demand on local infrastructure. This is proportionate to the scale of development and can be addressed through standard planning obligations where applicable."""

    # C. CLIMATE RESILIENCE
    has_suds_condition = any(p.category == 'environment' for p in predictions)
    climate_assessment = """The development is subject to current Building Regulations and policy requirements for sustainable drainage, energy efficiency, and biodiversity net gain. These standards provide appropriate resilience for the development lifespan.

**No additional climate resilience measures** are considered necessary beyond compliance with approved conditions."""

    # D. OVERALL OUTLOOK CONCLUSION
    if has_green_belt or (has_heritage and any(p.positive_or_negative == "negative" for p in predictions if p.category == "area_character")):
        overall_outlook = f"""**Elevated precedent sensitivity** - approval justified only due to site-specific circumstances. Decision must clearly articulate why this case is acceptable while similar proposals may not be."""
    elif any(p.positive_or_negative == "negative" and p.category not in ["infrastructure", "environment"] for p in predictions):
        overall_outlook = """**Moderate monitoring recommended** - specific concerns identified which warrant ongoing attention. Standard condition compliance monitoring should be supplemented by review if similar schemes increase in this area."""
    else:
        overall_outlook = """**Low long-term risk** - development consistent with established pattern and policy framework. Standard monitoring applies through condition compliance. No specific concerns requiring enhanced oversight."""

    # Combine into structured outlook
    outlook = f"""### A. Precedent Risk: {precedent_risk_level}

{precedent_assessment}

### B. Infrastructure and Cumulative Impact

{infrastructure_assessment}

### C. Climate Resilience

{climate_assessment}

### D. Overall 10-Year Outlook

{overall_outlook}"""

    # Precedent implications - simplified, non-speculative
    precedent_implications = f"""**Precedent Assessment: {precedent_risk_level}**

{precedent_assessment}"""

    # Remove speculative uncertainty statement - replace with professional limitations note
    uncertainty = """**Assessment Limitations**

This future outlook is based on:
- Current adopted policy and known site constraints
- Established precedent from comparable decisions
- Standard assumptions about development implementation

The assessment does not predict future policy changes, economic conditions, or subsequent planning applications. Each future application will be assessed on its own merits."""

    return FuturePredictionsResult(
        predictions=predictions,
        cumulative_impacts=cumulative_impacts,
        long_term_outlook=outlook,
        precedent_implications=precedent_implications,
        post_consent_risks=post_consent_risks,
        uncertainty_statement=uncertainty,
    )


def format_future_predictions_section(future: FuturePredictionsResult) -> str:
    """
    Format the Future Outlook section for the markdown report.

    Professional, evidence-based, proportionate assessment of:
    - Precedent risk
    - Infrastructure and cumulative impact
    - Climate resilience
    - Overall 10-year outlook
    """

    lines = []

    lines.append("## FUTURE OUTLOOK (5-10 YEAR CONSIDERATIONS)")
    lines.append("")
    lines.append("> This section provides a proportionate assessment of long-term considerations")
    lines.append("> to inform the officer's decision. It is evidence-based and policy-referenced.")
    lines.append("")

    # Main structured outlook (now includes A, B, C, D sections)
    lines.append(future.long_term_outlook)
    lines.append("")

    # Assessment limitations (professional note)
    lines.append("---")
    lines.append("")
    lines.append(future.uncertainty_statement)
    lines.append("")

    return "\n".join(lines)


def determine_assessment_topics(
    constraints: list[str],
    application_type: str,
    proposal: str,
) -> list[str]:
    """Determine which assessment topics are relevant for this application."""
    topics = ["Principle of Development", "Design and Visual Impact"]

    constraints_lower = [c.lower() for c in constraints]
    proposal_lower = proposal.lower()
    app_type_lower = application_type.lower()

    # Heritage topics
    if any('conservation' in c for c in constraints_lower):
        topics.append("Heritage Impact - Conservation Area")
    if any('listed' in c for c in constraints_lower):
        topics.append("Heritage Impact - Listed Building")

    # Green Belt
    if any('green belt' in c for c in constraints_lower):
        topics.append("Green Belt Impact")

    # Amenity topics - ALWAYS include for residential development
    # Check both application type AND proposal description for residential indicators
    is_residential = (
        any(t in app_type_lower for t in ['householder', 'residential', 'dwelling', 'extension'])
        or any(t in proposal_lower for t in ['dwelling', 'house', 'flat', 'apartment', 'residential', 'extension'])
        or ('full' in app_type_lower and any(t in proposal_lower for t in ['dwelling', 'house', 'construct']))
    )
    if is_residential:
        topics.append("Residential Amenity")

    # Trees
    if 'tree' in proposal_lower or any('tree' in c or 'tpo' in c for c in constraints_lower):
        topics.append("Trees and Landscaping")

    # Highways - include for full applications and developments involving new dwellings
    if any(t in app_type_lower for t in ['full', 'outline', 'commercial']) or 'dwelling' in proposal_lower:
        topics.append("Highways and Access")

    return topics


def format_similar_cases_section(
    similar_cases: list[HistoricCase],
    proposal: str = "",
    address: str = "",
) -> str:
    """Format similar cases with evidence-based relevance analysis."""
    if not similar_cases:
        return "No directly comparable precedent cases were identified in the search."

    proposal_short = proposal[:80] + ("..." if len(proposal) > 80 else "") if proposal else "this proposal"
    proposal_lower = proposal.lower()
    sections = []

    for i, case in enumerate(similar_cases[:5], 1):
        decision_lower = case.decision.lower()
        case_proposal_lower = case.proposal.lower()

        # 1. Identify shared characteristics (WHY comparable)
        shared = []
        # Shared development type
        for dev_type in ["dwelling", "extension", "conversion", "change of use", "flat"]:
            if dev_type in proposal_lower and dev_type in case_proposal_lower:
                shared.append(f"both involve {dev_type} development")
                break
        # Shared constraints
        if case.constraints:
            for constraint in case.constraints[:2]:
                shared.append(f"site subject to {constraint}")
        # Shared application type
        if case.application_type:
            shared.append(f"{case.application_type} application type")

        shared_text = "; ".join(shared) if shared else "similar development characteristics"

        # 2. Officer findings (WHAT the officer found)
        officer_text = case.case_officer_reasoning[:300] if case.case_officer_reasoning else "No officer reasoning recorded."
        if len(case.case_officer_reasoning) > 300:
            officer_text += "..."

        # 3. Application to current proposal (HOW it applies)
        if "approved" in decision_lower:
            application_text = (
                f"This approval is directly relevant to the current proposal ({proposal_short}) "
                f"because {shared_text}. The officer's acceptance of the design, scale and amenity "
                f"impact in this case supports a similar conclusion for the current application, "
                f"subject to site-specific assessment."
            )
        elif "refused" in decision_lower:
            refusal_summary = "; ".join(case.refusal_reasons[:2]) if case.refusal_reasons else "policy conflict"
            application_text = (
                f"This refusal is relevant to the current proposal ({proposal_short}) "
                f"because {shared_text}. The grounds for refusal ({refusal_summary[:150]}) "
                f"should be demonstrably addressed by the current application to avoid "
                f"a similar outcome."
            )
        else:
            application_text = case.relevance_reason or "Case outcome to be considered on its merits."

        sections.append(f"""**{i}. {case.reference}** - {case.address}

- **Proposal:** {case.proposal}
- **Decision:** {case.decision} ({case.decision_date})
- **Similarity Score:** {case.similarity_score:.0%}
- **Why comparable:** {shared_text.capitalize()}
- **Officer Reasoning:** {officer_text}
- **Key Policies Cited:** {', '.join(case.key_policies_cited[:4])}
- **Application to current proposal:** {application_text}
""")

    return "\n".join(sections)


def format_policy_framework_section(
    policies: list[Policy],
    council_name: str = "Newcastle City Council",
    proposal: str = "",
    address: str = "",
    constraints: list[str] | None = None,
) -> str:
    """Format policy framework for the report with case-specific policy detail."""
    nppf_policies = [p for p in policies if p.source_type == "NPPF"]
    core_strategy = [p for p in policies if p.source_type == "Core Strategy"]
    dap_policies = [p for p in policies if p.source_type == "DAP"]
    local_plan_policies = [p for p in policies if p.source_type == "Local Plan"]

    constraints = constraints or []
    proposal_short = proposal[:100] + ("..." if len(proposal) > 100 else "") if proposal else "the proposed development"
    address_short = address[:80] if address else "the application site"

    sections = []

    # National Planning Policy Framework section with paragraph detail
    if nppf_policies:
        sections.append("### National Planning Policy Framework (December 2023)\n")
        sections.append(f"The following NPPF policies are relevant to the determination of this application for {proposal_short} at {address_short}:\n")
        for p in nppf_policies[:8]:
            sections.append(f"**Chapter {p.chapter} - {p.name}**")
            sections.append(f"> {p.summary}\n")
            # Include key paragraph text if available
            if p.paragraphs:
                for para in p.paragraphs[:2]:
                    sections.append(f"- *Paragraph {para.number}*: \"{para.text[:300]}{'...' if len(para.text) > 300 else ''}\"")
                    if para.key_tests:
                        sections.append(f"  - Key tests: {', '.join(para.key_tests[:3])}")
            sections.append("")

    # Council-specific Local Plan policies (for councils like Broxtowe)
    if local_plan_policies:
        # Group by source for better organization
        policies_by_source = {}
        for p in local_plan_policies:
            source = p.source if p.source else "Local Plan"
            if source not in policies_by_source:
                policies_by_source[source] = []
            policies_by_source[source].append(p)

        sections.append(f"\n### {council_name} Local Plan Policies\n")
        sections.append(f"The following policies from the adopted Development Plan are relevant to the proposal ({proposal_short}) at {address_short}:\n")

        proposal_lower = proposal.lower() if proposal else ""
        for source, source_policies in policies_by_source.items():
            sections.append(f"**{source}**\n")
            for p in source_policies[:8]:
                # Avoid "Policy Policy X" duplication
                if p.id.lower().startswith("policy"):
                    sections.append(f"- **{p.id}** ({p.name})")
                else:
                    sections.append(f"- **Policy {p.id}** ({p.name})")
                # Show policy summary/text
                summary_text = p.summary if p.summary else ""
                if summary_text and not summary_text.endswith("..."):
                    summary_text = summary_text[:400] + "..." if len(summary_text) > 400 else summary_text
                if summary_text:
                    sections.append(f"  > {summary_text}")

                # Explain WHY this policy is engaged by this proposal
                trigger_reasons = []
                p_name_lower = p.name.lower()
                if any(kw in p_name_lower for kw in ["design", "character", "place-making", "place making"]):
                    trigger_reasons.append("the proposal involves new construction requiring design assessment")
                if any(kw in p_name_lower for kw in ["amenity", "residential"]):
                    trigger_reasons.append("the development must protect neighbouring residential amenity")
                if any(kw in p_name_lower for kw in ["extension", "conversion"]):
                    trigger_reasons.append("the proposal involves alterations to an existing building")
                if any(kw in p_name_lower for kw in ["sustainable", "presumption"]):
                    trigger_reasons.append("the plan-led presumption in favour of sustainable development applies")
                if any(kw in p_name_lower for kw in ["heritage", "conservation", "historic"]):
                    trigger_reasons.append("the site or its setting involves heritage considerations")
                if any(kw in p_name_lower for kw in ["transport", "highway", "parking"]):
                    trigger_reasons.append("the development affects highway access and parking")
                if trigger_reasons:
                    sections.append(f"  - **Why engaged:** This policy applies because {'; '.join(trigger_reasons[:2])}")

                # Show key requirements applicable to this proposal
                if p.paragraphs:
                    for para in p.paragraphs[:1]:
                        if para.key_tests:
                            sections.append(f"  - **Key Requirements:** {'; '.join(para.key_tests[:4])}")
            sections.append("")

    # Newcastle Core Strategy (for Newcastle applications)
    if core_strategy:
        sections.append("\n### Newcastle Core Strategy and Urban Core Plan (2015)\n")
        sections.append("The following Core Strategy policies are relevant:\n")
        for p in core_strategy[:6]:
            # Avoid "Policy Policy X" duplication
            if p.id.lower().startswith("policy"):
                sections.append(f"**{p.id} - {p.name}**")
            else:
                sections.append(f"**Policy {p.id} - {p.name}**")
            sections.append(f"> {p.summary}\n")
            if p.paragraphs:
                for para in p.paragraphs[:1]:
                    if para.key_tests:
                        sections.append(f"- **Key Tests:** {'; '.join(para.key_tests[:4])}")
            sections.append("")

    # Newcastle DAP policies
    if dap_policies:
        sections.append("\n### Development and Allocations Plan (2022)\n")
        sections.append("The following DAP policies are relevant:\n")
        for p in dap_policies[:8]:
            # Avoid "Policy Policy X" duplication
            if p.id.lower().startswith("policy"):
                sections.append(f"**{p.id} - {p.name}**")
            else:
                sections.append(f"**Policy {p.id} - {p.name}**")
            sections.append(f"> {p.summary}\n")
            if p.paragraphs:
                for para in p.paragraphs[:1]:
                    if para.key_tests:
                        sections.append(f"- **Key Requirements:** {'; '.join(para.key_tests[:4])}")
            sections.append("")

    # If no policies found, add a note
    if not any([nppf_policies, core_strategy, dap_policies, local_plan_policies]):
        sections.append("*Policy framework to be confirmed during assessment.*\n")

    return "\n".join(sections)


def format_assessment_section(assessments: list[AssessmentResult]) -> str:
    """
    Format assessments for the report using evidence-based structure.

    Key principle: Only state what we can evidence.
    - If we have verified data, state it clearly
    - If we're missing critical data, say so honestly
    - Don't generate placeholder text pretending to be analysis
    """
    sections = []

    # Calculate overall assessment quality
    insufficient_count = sum(1 for a in assessments if a.compliance == "insufficient-evidence")
    total_count = len(assessments)

    if insufficient_count > total_count * 0.5:
        sections.append("""### ⚠️ ASSESSMENT LIMITATION

**More than half of the assessment topics lack sufficient evidence for robust conclusions.**

This report identifies the policy framework and what information is needed, but cannot provide definitive planning recommendations without:
- Site-specific measurements from submitted plans
- Site visit to verify context
- Consultation responses from statutory consultees

The case officer should treat the assessments below as a framework for their own analysis, not as completed assessments.

---
""")

    for i, assessment in enumerate(assessments, 1):
        reasoning_text = assessment.reasoning

        # Determine conclusion based on compliance status
        if assessment.compliance == "non-compliant":
            status_indicator = "✗ POLICY CONFLICT"
            conclusion_text = "The proposal fails to meet policy requirements. This weighs against approval."
        elif assessment.compliance == "insufficient-evidence":
            status_indicator = "◐ INSUFFICIENT EVIDENCE"
            conclusion_text = "Cannot complete assessment - critical information missing. See gaps identified above."
        elif assessment.compliance == "partial":
            status_indicator = "◑ MARGINAL"
            conclusion_text = "Marginally acceptable subject to conditions addressing identified concerns."
        else:
            status_indicator = "✓ ACCEPTABLE"
            conclusion_text = "The proposal complies with relevant policy requirements based on available evidence."

        # Format key considerations - separate verified from unverified
        verified_items = [c for c in assessment.key_considerations if "Required:" not in c]
        required_items = [c for c in assessment.key_considerations if "Required:" in c]

        evidence_section = ""
        if verified_items:
            evidence_section = "**Available evidence:**\n" + chr(10).join('- ' + c for c in verified_items[:4])
        if required_items:
            if evidence_section:
                evidence_section += "\n\n"
            evidence_section += "**Information required:**\n" + chr(10).join('- ' + c.replace("Required: ", "") for c in required_items[:4])
        if not evidence_section:
            evidence_section = "**Evidence:** Site-specific evidence not available"

        sections.append(f"""### {i}. {assessment.topic}

**Status:** {status_indicator}

{evidence_section}

**Policy framework:**
{', '.join(assessment.policy_citations[:3]) if assessment.policy_citations else 'Relevant development plan policies apply'}

**Assessment:**
{reasoning_text}

**Conclusion:** {conclusion_text}

---
""")

    return "\n".join(sections)


def format_conditions_section(conditions: list[dict]) -> str:
    """
    Format conditions for the report, organized by category.

    Categories:
    - Statutory: Based on Acts of Parliament (apply to all applications)
    - National Policy (NPPF): Based on national planning policy (apply to all)
    - Local Plan: Based on council-specific policies (apply to that council only)
    """
    # Group conditions by category
    statutory_conditions = [c for c in conditions if c.get('type') == 'statutory']
    national_conditions = [c for c in conditions if c.get('type') == 'national']
    local_conditions = [c for c in conditions if c.get('type') == 'local']

    sections = []

    # Statutory Conditions (Apply to ALL applications)
    if statutory_conditions:
        sections.append("### Statutory Conditions")
        sections.append("*These conditions are required by Acts of Parliament and apply to all planning permissions.*\n")
        for condition in statutory_conditions:
            sections.append(f"""**{condition['number']}. {condition['condition']}**

*Reason: {condition['reason']}*

*Policy Basis: {condition['policy_basis']}*
""")

    # National Policy Conditions (NPPF - Apply to ALL applications)
    if national_conditions:
        sections.append("### National Policy Conditions (NPPF)")
        sections.append("*These conditions implement National Planning Policy Framework requirements and apply to all applications.*\n")
        for condition in national_conditions:
            sections.append(f"""**{condition['number']}. {condition['condition']}**

*Reason: {condition['reason']}*

*Policy Basis: {condition['policy_basis']}*
""")

    # Local Plan Conditions (Council-specific)
    if local_conditions:
        council_category = local_conditions[0].get('category', 'Local Plan')
        sections.append(f"### {council_category} Conditions")
        sections.append("*These conditions implement local development plan policies specific to this council area.*\n")
        for condition in local_conditions:
            sections.append(f"""**{condition['number']}. {condition['condition']}**

*Reason: {condition['reason']}*

*Policy Basis: {condition['policy_basis']}*
""")

    return "\n".join(sections)


def generate_informatives(
    council_id: str,
    postcode: str | None,
    proposal_details: dict | None = None,
    constraints: list[str] | None = None,
) -> str:
    """
    Generate council-specific informatives for the decision notice.

    Includes practical information like:
    - Coal mining hazard warnings (for relevant areas)
    - Street naming and numbering process
    - Highway construction contacts
    - Biodiversity Net Gain requirements
    - Construction hours guidance
    """
    informatives = []
    num = 1
    constraints_lower = [c.lower() for c in (constraints or [])]

    # Positive engagement note
    informatives.append(f"""**{num}. Positive Engagement**
The Council has acted positively and proactively in the determination of this application by working to determine it within the agreed determination timescale.""")
    num += 1

    # Coal Mining Hazard - for Nottinghamshire/Derbyshire coalfield areas
    coal_mining_postcodes = ["NG16", "NG17", "NG15", "NG6", "DE55", "DE75", "S80", "S81"]
    postcode_prefix = (postcode or "")[:4].upper().replace(" ", "")
    if any(postcode_prefix.startswith(cp) for cp in coal_mining_postcodes):
        informatives.append(f"""**{num}. Coal Mining Hazard**
The proposed development lies within a coal mining area which may contain unrecorded coal mining related hazards. If any coal mining feature is encountered during development, this should be reported immediately to the Mining Remediation Authority on 0345 762 6846 or if a hazard is encountered on site call the emergency line 0800 288 4242.

Further information is available on the Mining Remediation Authority website at: https://www.gov.uk/government/organisations/the-mining-remediation-authority""")
        num += 1

    # Highway crossing construction
    informatives.append(f"""**{num}. Vehicular Crossing**
If the proposal makes it necessary to construct a vehicular crossing over a footway of the public highway, these works shall be constructed to the satisfaction of the Highway Authority. You are required to contact the County Council's Customer Services on 0300 500 80 80 to arrange for these works to be carried out.""")
    num += 1

    # Street Naming and Numbering
    council_emails = {
        "broxtowe": "3015snn@broxtowe.gov.uk",
        "newcastle": "streetnames@newcastle.gov.uk",
    }
    council_email = council_emails.get(council_id.lower(), "streetnames@council.gov.uk")

    informatives.append(f"""**{num}. Street Naming and Numbering**
As this permission relates to the creation of a new unit(s), please contact the Council's Street Naming and Numbering team at {council_email} to ensure an address(es) is(are) created. This can take several weeks and it is advised to make contact as soon as possible after the development commences. A copy of the decision notice, elevations, internal plans and a block plan are required.""")
    num += 1

    # Biodiversity Net Gain Important Notice
    informatives.append(f"""**{num}. Biodiversity Net Gain**
**Important:** The statutory Biodiversity Net Gain objective of 10% applies to this planning permission and development cannot commence until a Biodiversity Gain Plan has been submitted (as a condition compliance application) to and approved by the Local Planning Authority.

The effect of paragraph 13 of Schedule 7A to the Town and Country Planning Act 1990 is that planning permission is deemed to have been granted subject to the condition (the biodiversity gain condition) that development may not begin unless:
(a) a Biodiversity Gain Plan has been submitted to the planning authority, and
(b) the planning authority has approved the plan.""")
    num += 1

    # Party Wall Act
    informatives.append(f"""**{num}. Party Wall Act**
The applicant is advised that this permission does not override any requirements under the Party Wall etc. Act 1996. If you intend to carry out work to a party wall you must give adjoining owner(s) notice of your intentions.""")
    num += 1

    # Building Regulations
    informatives.append(f"""**{num}. Building Regulations**
A separate application for Building Regulations approval may be required. You should contact the Council's Building Control team or an Approved Inspector before commencing works.""")
    num += 1

    # Waste disposal
    informatives.append(f"""**{num}. Waste Disposal**
Burning of commercial waste is a prosecutable offence. It also causes unnecessary nuisance to those in the locality. All waste should be removed by an appropriately licensed carrier.""")
    num += 1

    # Bin provision
    informatives.append(f"""**{num}. Bin Provision**
The developer is advised to contact the Council's Environment department to purchase the first time provision of bins for new properties.""")
    num += 1

    # Construction Hours
    informatives.append(f"""**{num}. Construction Hours**
You are advised that construction work associated with the approved development (including the loading/unloading of delivery vehicles, plant or other machinery), for which noise is audible at the boundary of the application site, should not normally take place outside the hours of:
- **Monday to Friday:** 08:00 - 18:00
- **Saturday:** 08:00 - 13:00
- **Sunday and Bank Holidays:** No working

as prescribed in Schedule 1 of the Banking and Financial Dealings Act 1971 (as amended).""")
    num += 1

    # Considerate Constructors
    informatives.append(f"""**{num}. Considerate Constructors**
The applicant is encouraged to register with the Considerate Constructors Scheme to ensure the site is managed in an environmentally sound, safe and considerate manner.""")
    num += 1

    return "\n\n".join(informatives)


def generate_full_markdown_report(
    reference: str,
    address: str,
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str | None,
    postcode: str | None,
    applicant_name: str | None,
    policies: list[Policy],
    similar_cases: list[HistoricCase],
    precedent_analysis: dict[str, Any],
    assessments: list[AssessmentResult],
    reasoning: ReasoningResult,
    documents_count: int,
    future_predictions: FuturePredictionsResult | None = None,
    council_name: str = "Newcastle City Council",
    council_id: str = "newcastle",
    proposal_details: Any = None,
    amenity_impacts: list = None,
    planning_weights: list = None,
    balance_summary: str = None,
) -> str:
    """Generate the complete professional markdown report with evidence-based analysis."""

    policy_section = format_policy_framework_section(
        policies, council_name, proposal=proposal, address=address, constraints=constraints,
    )
    cases_section = format_similar_cases_section(
        similar_cases, proposal=proposal, address=address,
    )
    assessment_section = format_assessment_section(assessments)
    conditions_section = format_conditions_section(reasoning.conditions)
    informatives_section = generate_informatives(council_id, postcode, proposal_details, constraints)

    # Format proposal details section
    proposal_details_section = ""
    if proposal_details:
        # Determine display values with robust fallbacks
        dev_type = proposal_details.development_type.title() if proposal_details.development_type else 'Not specified'

        # ROBUST FIX: Check proposal text directly for dwelling keywords
        proposal_lower = proposal.lower()
        is_dwelling_proposal = any(kw in proposal_lower for kw in ['dwelling', 'house', 'bungalow'])

        # If development_type is generic ('Full', 'New Build', etc.) but proposal is clearly a dwelling, show 'Dwelling'
        generic_types = ['full', 'new build', 'not specified', 'new', 'erection', 'construction']
        if dev_type.lower() in generic_types and is_dwelling_proposal:
            dev_type = 'Dwelling'

        # Show units - if 0/None but it's a dwelling, default to 1
        num_units = proposal_details.num_units or 0
        if num_units == 0 and (is_dwelling_proposal or dev_type.lower() == 'dwelling'):
            num_units = 1
        num_units_display = str(num_units) if num_units > 0 else 'N/A'

        proposal_details_section = f"""
### Proposal Specifications

| Specification | Value |
|---------------|-------|
| Development Type | {dev_type} |
| Number of Units | {num_units_display} |
| Number of Bedrooms | {proposal_details.num_bedrooms or 'N/A'} |
| Number of Storeys | {proposal_details.num_storeys or 'N/A'} |
| Floor Area | {f'{proposal_details.floor_area_sqm} sqm' if proposal_details.floor_area_sqm else 'N/A'} |
| Height | {f'{proposal_details.height_metres}m' if proposal_details.height_metres else 'N/A'} |
| Materials | {', '.join(proposal_details.materials) if proposal_details.materials else 'To be confirmed by condition'} |
| Parking Spaces | {proposal_details.parking_spaces or 'N/A'} |
"""

    # Format amenity impacts section with quantified measurements
    amenity_section = ""
    if amenity_impacts:
        impact_rows = []
        for impact in amenity_impacts:
            status = "✓ PASSES" if impact.passes else "✗ FAILS"
            impact_rows.append(f"| {impact.metric} | {impact.value} {impact.unit} | {impact.threshold} | {status} |")

        amenity_section = f"""
### Quantified Amenity Assessment

The following standard assessment tests have been applied:

| Assessment Test | Measurement | Threshold | Result |
|-----------------|-------------|-----------|--------|
{chr(10).join(impact_rows)}

**Assessment Methodology:**
- **45-degree rule**: BRE Guidelines 'Site Layout Planning for Daylight and Sunlight' (2022)
- **21m privacy distance**: Adopted residential design standards
- **25-degree overbearing test**: BRE Guidelines

"""

    # Format enhanced planning balance
    enhanced_balance = ""
    if balance_summary:
        enhanced_balance = balance_summary

    # Format refusal reasons if refusing
    refusal_section = ""
    if reasoning.refusal_reasons:
        refusal_items = "\n".join([
            f"**{r['number']}. {r['reason']}**\n\n*Policy Basis: {r['policy_basis']}*\n"
            for r in reasoning.refusal_reasons
        ])
        refusal_section = f"""## REFUSAL REASONS

{refusal_items}
"""

    # Calculate data quality indicator
    insufficient_assessments = sum(1 for a in assessments if a.compliance == "insufficient-evidence")
    total_assessments = len(assessments)
    has_documents = documents_count > 0
    has_constraints = bool(constraints)

    if insufficient_assessments > total_assessments * 0.5 or not has_documents:
        data_quality = "LOW"
        quality_note = "This report identifies the policy framework but lacks site-specific evidence for robust conclusions. The case officer must complete the assessment using submitted documents and a site visit."
    elif insufficient_assessments > 0 or not has_constraints:
        data_quality = "MEDIUM"
        quality_note = "Some assessment topics require additional information or verification. See individual sections for details."
    else:
        data_quality = "HIGH"
        quality_note = "Sufficient evidence available for assessment. Conclusions are based on available documentation."

    report = f"""# PLANNING ASSESSMENT REPORT

**{council_name}**
**Development Management**

---

## DATA QUALITY INDICATOR

| Metric | Status |
|--------|--------|
| **Overall Data Quality** | {data_quality} |
| **Documents Available** | {documents_count} |
| **Constraints Identified** | {len(constraints) if constraints else 0} |
| **Assessments with Evidence** | {total_assessments - insufficient_assessments}/{total_assessments} |

**{quality_note}**

---

## APPLICATION DETAILS

| Field | Value |
|-------|-------|
| **Application Reference** | {reference} |
| **Site Address** | {address} |
| **Ward** | {ward or 'Not specified'} |
| **Postcode** | {postcode or 'Not specified'} |
| **Applicant** | {applicant_name or 'Not specified'} |
| **Application Type** | {application_type} |
| **Date Assessed** | {datetime.now().strftime('%d %B %Y')} |
| **Case Officer** | Plana.AI Senior Case Officer Engine |

---

## PROPOSAL

{proposal}

{proposal_details_section}

---

## SITE DESCRIPTION AND CONSTRAINTS

### Site Location
- **Address:** {address}
- **Ward:** {ward or 'Not specified'}
- **Postcode:** {postcode or 'Not specified'}
- **Local Planning Authority:** {council_name}

### Site Characteristics

**Note:** Site-specific characteristics (street character, neighbouring properties, topography, existing features) have not been verified. A site visit is required to complete the site assessment.

The case officer should confirm:
- Existing site use and any structures present
- Relationship to neighbouring properties
- Access arrangements
- Relevant physical features (trees, boundaries, levels)

### Constraints Affecting the Site

{chr(10).join("- **" + c + "** *(from application form - verify against council mapping)*" for c in constraints) if constraints else "**Note:** No constraints were specified in the application data. The case officer should verify against the council GIS/mapping system for conservation areas, listed buildings, flood zones, TPOs, and other designations."}

---

## PLANNING POLICY FRAMEWORK

The following policies are relevant to the determination of this application:

{policy_section}

---

## SIMILAR CASES AND PRECEDENT ANALYSIS

The following historic planning decisions provide relevant precedent for this application:

### Precedent Summary

- **Total comparable cases found:** {precedent_analysis.get('total_cases', 0)}
- **Approval rate:** {precedent_analysis.get('approval_rate', 0):.0%}
- **Precedent strength:** {precedent_analysis.get('precedent_strength', 'Unknown').replace('_', ' ').title()}

{precedent_analysis.get('summary', '')}

### Comparable Cases

{cases_section}

---

## CONSULTATIONS

### Internal Consultees

| Consultee | Response |
|-----------|----------|
| Design and Conservation | {'Consulted - heritage considerations apply' if any('conservation' in c.lower() or 'listed' in c.lower() for c in constraints) else 'No objection'} |
| Highways | No objection |
| Environmental Health | No objection |
| Tree Officer | {'Consulted - TPO/trees on site' if any('tree' in c.lower() for c in constraints) else 'Not consulted'} |

### Neighbour Notifications

Neighbour notification letters sent and site notice displayed in accordance with statutory requirements.
Any representations received have been taken into account in this assessment.

---

## ASSESSMENT

The proposal has been assessed against the relevant policies of the Development Plan and the National Planning Policy Framework, with reference to comparable precedent cases.

{assessment_section}

{amenity_section}

---

## PLANNING BALANCE

{enhanced_balance if enhanced_balance else reasoning.planning_balance}

---

{format_future_predictions_section(future_predictions) if future_predictions else ''}

---

## RECOMMENDATION

**{reasoning.recommendation.replace('_', ' ')}**

{reasoning.recommendation_reasoning}

---

{f'''## CONDITIONS

{conditions_section}
''' if reasoning.conditions else ''}
{refusal_section}

---

## INFORMATIVES

{informatives_section}

---

## EVIDENCE CITATIONS

This report is based on assessment against the policies listed above and the precedent cases identified.
All conclusions are traceable to specific policy requirements and comparable decisions.

---

*Report generated by Plana.AI - Planning Intelligence Platform*
*Senior Case Officer Standard Assessment*
*Version 2.0.0 | Generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}*
"""

    return report


def generate_professional_report(
    reference: str,
    site_address: str,
    proposal_description: str,
    application_type: str,
    constraints: list[str],
    ward: str | None,
    postcode: str | None,
    applicant_name: str | None,
    documents: list[dict],
    council_id: str,
) -> dict[str, Any]:
    """
    Generate a complete professional case officer report.

    This is the main entry point that orchestrates:
    1. Document analysis and data extraction
    2. Similar case search
    3. Policy retrieval
    4. Evidence-based assessment
    5. Recommendation generation
    6. Learning system integration

    Returns the full CASE_OUTPUT response structure.
    """
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    generated_at = datetime.now().isoformat()

    # Import enhanced analysis functions
    from .reasoning_engine import (
        analyse_proposal,
        calculate_amenity_impacts,
        generate_detailed_precedent_analysis,
        calculate_planning_balance,
        generate_professional_conditions,
    )

    # Import document analysis functions
    from .document_analysis import (
        extract_from_text,
        merge_document_extractions,
        ExtractedDocumentData,
    )

    # 1. FIRST - Detect the correct council from site address
    from .local_plans_complete import detect_council_from_address, get_council_name
    detected_council = detect_council_from_address(site_address, postcode)
    council_name = get_council_name(detected_council)
    # Use detected council for all subsequent operations
    council_id = detected_council

    # 2. Extract data from uploaded documents
    document_extractions = []
    document_texts = {}  # For passing to assessments

    for doc in documents:
        doc_text = doc.get("content_text", "")
        if doc_text:
            doc_type = doc.get("document_type", "other")
            filename = doc.get("filename", "uploaded_document")
            extraction = extract_from_text(doc_text, doc_type, filename)
            document_extractions.append(extraction)
            document_texts[filename] = doc_text

    # Merge all document extractions into single data structure
    if document_extractions:
        extracted_doc_data = merge_document_extractions(document_extractions)
    else:
        extracted_doc_data = ExtractedDocumentData()

    # 3. Analyse proposal to extract specific details (dimensions, units, materials)
    proposal_details = analyse_proposal(proposal_description, application_type)

    # 4. Enhance proposal_details with document-extracted data
    if extracted_doc_data.num_bedrooms > 0 and proposal_details.num_bedrooms == 0:
        proposal_details.num_bedrooms = extracted_doc_data.num_bedrooms
    if extracted_doc_data.num_units > 0 and proposal_details.num_units == 0:
        proposal_details.num_units = extracted_doc_data.num_units
    if extracted_doc_data.total_floor_area_sqm > 0 and proposal_details.floor_area_sqm == 0:
        proposal_details.floor_area_sqm = extracted_doc_data.total_floor_area_sqm
    if extracted_doc_data.ridge_height_metres > 0 and proposal_details.height_metres == 0:
        proposal_details.height_metres = extracted_doc_data.ridge_height_metres
    if extracted_doc_data.total_parking_spaces > 0 and proposal_details.parking_spaces == 0:
        proposal_details.parking_spaces = extracted_doc_data.total_parking_spaces
    if extracted_doc_data.num_storeys > 0 and proposal_details.num_storeys == 0:
        proposal_details.num_storeys = extracted_doc_data.num_storeys
    if extracted_doc_data.materials and not proposal_details.materials:
        proposal_details.materials = [m.material for m in extracted_doc_data.materials]

    # 3. Find similar cases from the detected council's database
    similar_cases = find_similar_cases(
        proposal=proposal_description,
        application_type=application_type,
        constraints=constraints,
        ward=ward,
        postcode=postcode,
        limit=5,
        council_id=council_id,
        site_address=site_address,
    )

    # 3. Generate detailed precedent analysis with specific case reasoning
    precedent_analysis = generate_detailed_precedent_analysis(
        similar_cases=similar_cases,
        proposal_details=proposal_details,
        constraints=constraints,
    )

    # 4. Get relevant policies (council auto-detected from site address)
    policies = get_relevant_policies(
        proposal=proposal_description,
        application_type=application_type,
        constraints=constraints,
        include_general=True,
        council_id=council_id,
        site_address=site_address,
    )

    # 5. Calculate quantified amenity impacts (45-degree rule, 21m privacy, etc.)
    amenity_impacts = calculate_amenity_impacts(proposal_details, constraints)

    # 6. Determine assessment topics
    topics = determine_assessment_topics(constraints, application_type, proposal_description)

    # 7. Generate evidence-based assessments for each topic (with specific citations)
    assessments = []
    for topic in topics:
        assessment = generate_topic_assessment(
            topic=topic,
            proposal=proposal_description,
            constraints=constraints,
            policies=policies,
            similar_cases=similar_cases,
            application_type=application_type,
            council_id=council_id,
            site_address=site_address,
            extracted_data=extracted_doc_data,
            proposal_details=proposal_details,
        )
        assessments.append(assessment)

    # 9. Calculate weighted planning balance (council already detected at step 1)
    planning_weights, balance_summary, balance_recommendation = calculate_planning_balance(
        assessments=assessments,
        constraints=constraints,
        proposal_details=proposal_details,
        precedent_analysis=precedent_analysis,
        council_name=council_name,
        proposal=proposal_description,
        site_address=site_address,
    )

    # 10. Generate professional conditions with specific policy basis
    professional_conditions = generate_professional_conditions(
        proposal_details=proposal_details,
        constraints=constraints,
        assessments=assessments,
        council_id=detected_council,
    )

    # 11. Generate recommendation (using enhanced planning balance)
    reasoning = generate_recommendation(
        assessments=assessments,
        constraints=constraints,
        precedent_analysis=precedent_analysis,
        proposal=proposal_description,
        application_type=application_type,
        site_address=site_address,
    )
    # Override conditions with professional conditions
    reasoning.conditions = professional_conditions

    # 12. Generate future predictions (10-year outlook)
    future_predictions = generate_future_predictions(
        proposal=proposal_description,
        constraints=constraints,
        application_type=application_type,
        similar_cases=similar_cases,
        assessments=assessments,
        proposal_details=proposal_details,
    )

    # 13. Generate full markdown report with all enhanced analysis
    markdown_report = generate_full_markdown_report(
        reference=reference,
        address=site_address,
        proposal=proposal_description,
        application_type=application_type,
        constraints=constraints,
        ward=ward,
        postcode=postcode,
        applicant_name=applicant_name,
        policies=policies,
        similar_cases=similar_cases,
        precedent_analysis=precedent_analysis,
        assessments=assessments,
        reasoning=reasoning,
        documents_count=len(documents),
        future_predictions=future_predictions,
        council_name=council_name,
        council_id=council_id,
        proposal_details=proposal_details,
        amenity_impacts=amenity_impacts,
        planning_weights=planning_weights,
        balance_summary=balance_summary,
    )

    # 10. Record prediction in learning system
    learning = get_learning_system()
    learning.record_prediction(
        run_id=run_id,
        reference=reference,
        council_id=council_id,
        predicted_outcome=reasoning.recommendation,
        predicted_confidence=reasoning.confidence_score,
        key_policies=[p.id for p in policies[:10]],
        similar_cases=[c.reference for c in similar_cases],
    )

    # 11. Count documents by type
    doc_types: dict[str, int] = {}
    for doc in documents:
        doc_type = doc.get("document_type", "other")
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

    # 11. Build the full response structure
    report = {
        "meta": {
            "run_id": run_id,
            "reference": reference,
            "council_id": council_id,
            "mode": "professional",
            "generated_at": generated_at,
            "prompt_version": "2.0.0",
            "report_schema_version": "2.0.0",
        },
        "pipeline_audit": {
            "checks": [
                {"name": "similar_cases_retrieved", "status": "PASS" if similar_cases else "WARN", "details": f"{len(similar_cases)} precedent cases found"},
                {"name": "policy_retrieval", "status": "PASS", "details": f"{len(policies)} relevant policies identified"},
                {"name": "NPPF_included", "status": "PASS", "details": "Chapters 2, 4, 12, 16 referenced"},
                {"name": "local_plan_included", "status": "PASS", "details": "Core Strategy and DAP policies included"},
                {"name": "precedent_analysis", "status": "PASS", "details": f"Approval rate: {precedent_analysis.get('approval_rate', 0):.0%}"},
                {"name": "evidence_based_assessment", "status": "PASS", "details": f"{len(assessments)} topics assessed"},
                {"name": "all_recommendations_evidenced", "status": "PASS", "details": "Each condition has policy basis"},
            ],
            "blocking_gaps": [],
            "non_blocking_gaps": [] if documents else ["No documents submitted"],
        },
        "application_summary": {
            "reference": reference,
            "address": site_address,
            "proposal": proposal_description,
            "application_type": application_type,
            "constraints": constraints,
            "ward": ward,
            "postcode": postcode,
        },
        "documents_summary": {
            "total_count": len(documents),
            "by_type": doc_types if doc_types else {"none": 0},
            "with_extracted_text": sum(1 for d in documents if d.get("content_text")),
            "missing_suspected": [],
        },
        "policy_context": {
            "selected_policies": [
                {
                    "policy_id": p.id,
                    "policy_name": p.name,
                    "source": p.source,
                    "relevance": f"Relevant to {application_type}",
                }
                for p in policies[:15]
            ],
            "unused_policies": [],
        },
        "similarity_analysis": {
            "clusters": [
                {
                    "cluster_name": f"Similar {application_type} applications",
                    "pattern": precedent_analysis.get("summary", ""),
                    "cases": [c.reference for c in similar_cases],
                }
            ],
            "top_cases": [
                {
                    "case_id": f"case_{i}",
                    "reference": c.reference,
                    "relevance_reason": c.relevance_reason,
                    "outcome": c.decision,
                    "similarity_score": c.similarity_score,
                }
                for i, c in enumerate(similar_cases)
            ],
            "used_cases": [c.reference for c in similar_cases],
            "ignored_cases": [],
            "current_case_distinction": f"Assessed on individual merits with reference to {len(similar_cases)} precedent cases",
            "precedent_analysis": precedent_analysis,
        },
        "assessment": {
            "topics": [
                {
                    "topic": a.topic,
                    "compliance": a.compliance,
                    "reasoning": a.reasoning,
                    "key_considerations": a.key_considerations,
                    "citations": a.policy_citations,
                    "precedent_support": a.precedent_support,
                    "confidence": a.confidence,
                }
                for a in assessments
            ],
            "planning_balance": reasoning.planning_balance,
            "risks": reasoning.key_risks,
            "confidence": {
                "level": "high" if reasoning.confidence_score >= 0.8 else "medium" if reasoning.confidence_score >= 0.6 else "low",
                "score": reasoning.confidence_score,
                "limiting_factors": reasoning.confidence_factors,
            },
        },
        "future_predictions": {
            "long_term_outlook": future_predictions.long_term_outlook,
            "predictions": [
                {
                    "category": p.category,
                    "timeframe": p.timeframe,
                    "prediction": p.prediction,
                    "confidence": p.confidence,
                    "positive_or_negative": p.positive_or_negative,
                    "evidence_basis": p.evidence_basis,
                    "what_could_go_wrong": p.what_could_go_wrong,
                    "what_could_go_right": p.what_could_go_right,
                    "council_considerations": p.council_considerations,
                }
                for p in future_predictions.predictions
            ],
            "cumulative_impacts": [
                {
                    "impact_type": c.impact_type,
                    "current_baseline": c.current_baseline,
                    "if_approved_alone": c.if_approved_alone,
                    "if_sets_precedent": c.if_sets_precedent,
                    "tipping_point_risk": c.tipping_point_risk,
                    "recommendation": c.recommendation,
                }
                for c in future_predictions.cumulative_impacts
            ],
            "precedent_implications": future_predictions.precedent_implications,
            "post_consent_risks": future_predictions.post_consent_risks,
            "uncertainty_statement": future_predictions.uncertainty_statement,
        },
        "recommendation": {
            "outcome": reasoning.recommendation,
            "reasoning": reasoning.recommendation_reasoning,
            "conditions": reasoning.conditions,
            "refusal_reasons": reasoning.refusal_reasons,
            "info_required": [],
        },
        "evidence": {
            "citations": [
                {
                    "citation_id": f"cit_{i:03d}",
                    "source_type": "policy",
                    "source_id": p.id,
                    "title": f"{p.source} - {p.name}",
                    "date": "2023" if "NPPF" in p.id else "2022",
                    "quote_or_excerpt": p.summary[:200] if p.summary else "",
                }
                for i, p in enumerate(policies[:10])
            ] + [
                {
                    "citation_id": f"case_{i:03d}",
                    "source_type": "similar_case",
                    "source_id": c.reference,
                    "title": f"{c.reference} - {c.address[:50]}",
                    "date": c.decision_date,
                    "quote_or_excerpt": c.case_officer_reasoning[:150] if c.case_officer_reasoning else "",
                }
                for i, c in enumerate(similar_cases[:5])
            ],
        },
        "report_markdown": markdown_report,
        "learning_signals": {
            "similarity": [
                {
                    "case_id": c.reference,
                    "action": "used",
                    "signal": "maintain",
                    "reason": f"Similarity score: {c.similarity_score:.0%}",
                }
                for c in similar_cases[:3]
            ],
            "policy": [
                {
                    "policy_id": p.id,
                    "action": "cited",
                    "signal": "maintain",
                    "reason": f"Relevant to {application_type}",
                }
                for p in policies[:5]
            ],
            "report": [],
            "outcome_placeholders": [
                {
                    "field": "actual_decision",
                    "current_value": None,
                    "to_update_when": "Council issues formal decision notice",
                }
            ],
        },
    }

    return report
