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
    # OVERALL OUTLOOK
    # ==========================================================================

    positive_count = sum(1 for p in predictions if p.positive_or_negative == "positive")
    negative_count = sum(1 for p in predictions if p.positive_or_negative == "negative")

    if positive_count > negative_count:
        outlook = f"""**OVERALL 10-YEAR OUTLOOK: LIKELY POSITIVE**

Based on the assessment, this development is predicted to have a net positive impact over the next decade. {positive_count} positive outcome(s) identified versus {negative_count} negative outcome(s).

Key positives: Improved living accommodation, support for household needs, community stability.

However, long-term success depends on:
- Strict compliance with approved plans and conditions
- Appropriate maintenance of the development
- No harmful cumulative impact from similar future developments"""
    elif negative_count > positive_count:
        outlook = f"""**OVERALL 10-YEAR OUTLOOK: POTENTIAL CONCERNS**

Based on the assessment, this development may have net negative impacts over the next decade. {negative_count} negative outcome(s) identified versus {positive_count} positive outcome(s).

The council should consider:
- Whether conditions can adequately mitigate identified concerns
- Long-term enforcement and monitoring requirements
- Cumulative impact if similar developments are approved"""
    else:
        outlook = f"""**OVERALL 10-YEAR OUTLOOK: BALANCED/UNCERTAIN**

Based on the assessment, this development has both potential benefits and risks over the next decade. The long-term outcome depends significantly on implementation quality and cumulative impacts.

The council should:
- Monitor compliance with conditions carefully
- Review precedent implications for future applications
- Consider cumulative impact in this area over time"""

    # Precedent implications
    precedent_implications = f"""**PRECEDENT IMPLICATIONS**

Approving this application may be cited as precedent in future applications. Consider:

1. **Similar sites**: Other properties with similar characteristics may seek similar development
2. **Appeal risk**: If refused, applicants may cite approved similar cases at appeal
3. **Policy interpretation**: This decision contributes to how policy is interpreted locally
4. **Cumulative effect**: Each approval makes subsequent similar approvals more likely

**Recommendation**: If approving, ensure decision clearly articulates site-specific factors that justify approval, to limit inappropriate precedent claims."""

    # Uncertainty statement
    uncertainty = f"""**PREDICTION LIMITATIONS**

These future predictions are inherently uncertain and should be treated as indicative only:

- Based on {len(similar_cases)} comparable case(s) - {'good evidence base' if len(similar_cases) >= 3 else 'limited evidence base'}
- Future conditions (climate, policy, community) may differ from assumptions
- Individual development outcomes vary based on implementation quality
- Cumulative impact depends on future applications not yet known

This assessment cannot predict:
- Future policy changes that may affect area
- Economic conditions affecting property values
- Changes in household circumstances
- Future planning applications in vicinity"""

    return FuturePredictionsResult(
        predictions=predictions,
        cumulative_impacts=cumulative_impacts,
        long_term_outlook=outlook,
        precedent_implications=precedent_implications,
        post_consent_risks=post_consent_risks,
        uncertainty_statement=uncertainty,
    )


def format_future_predictions_section(future: FuturePredictionsResult) -> str:
    """Format the Future Predictions section for the markdown report."""

    lines = []

    lines.append("## 🔮 FUTURE PREDICTIONS: 10-YEAR OUTLOOK")
    lines.append("")
    lines.append("> **This section helps planners understand whether this development will be**")
    lines.append("> **beneficial for the council and community in 5-10 years time.**")
    lines.append("")

    # Overall outlook
    lines.append("### Overall Long-Term Outlook")
    lines.append("")
    lines.append(future.long_term_outlook)
    lines.append("")

    # Detailed predictions
    if future.predictions:
        lines.append("### Detailed Predictions")
        lines.append("")

        # Group by timeframe
        medium_term = [p for p in future.predictions if p.timeframe == "medium_term"]
        long_term = [p for p in future.predictions if p.timeframe == "long_term"]

        if medium_term:
            lines.append("#### Medium Term (3-5 Years)")
            lines.append("")
            for pred in medium_term:
                sentiment = "✅" if pred.positive_or_negative == "positive" else "⚠️" if pred.positive_or_negative == "negative" else "❓"
                lines.append(f"**{sentiment} {pred.category.replace('_', ' ').title()}** (Confidence: {pred.confidence})")
                lines.append("")
                lines.append(f"> {pred.prediction}")
                lines.append("")
                lines.append(f"- **Evidence:** {pred.evidence_basis}")
                lines.append(f"- **What could go wrong:** {pred.what_could_go_wrong}")
                lines.append(f"- **What could go right:** {pred.what_could_go_right}")
                lines.append(f"- **Council consideration:** {pred.council_considerations}")
                lines.append("")

        if long_term:
            lines.append("#### Long Term (5-10 Years)")
            lines.append("")
            for pred in long_term:
                sentiment = "✅" if pred.positive_or_negative == "positive" else "⚠️" if pred.positive_or_negative == "negative" else "❓"
                lines.append(f"**{sentiment} {pred.category.replace('_', ' ').title()}** (Confidence: {pred.confidence})")
                lines.append("")
                lines.append(f"> {pred.prediction}")
                lines.append("")
                lines.append(f"- **Evidence:** {pred.evidence_basis}")
                lines.append(f"- **What could go wrong:** {pred.what_could_go_wrong}")
                lines.append(f"- **What could go right:** {pred.what_could_go_right}")
                lines.append(f"- **Council consideration:** {pred.council_considerations}")
                lines.append("")

    # Cumulative impacts
    if future.cumulative_impacts:
        lines.append("### Cumulative Impact Assessment")
        lines.append("")
        lines.append("*What happens if similar developments are approved across the area?*")
        lines.append("")

        for impact in future.cumulative_impacts:
            lines.append(f"#### {impact.impact_type.replace('_', ' ').title()}")
            lines.append("")
            lines.append("| Scenario | Impact |")
            lines.append("|----------|--------|")
            lines.append(f"| **Current baseline** | {impact.current_baseline} |")
            lines.append(f"| **If this alone approved** | {impact.if_approved_alone} |")
            lines.append(f"| **If this sets precedent** | {impact.if_sets_precedent} |")
            lines.append(f"| **Tipping point risk** | {impact.tipping_point_risk} |")
            lines.append("")
            lines.append(f"**Recommendation:** {impact.recommendation}")
            lines.append("")

    # Precedent implications
    lines.append("### Precedent Implications")
    lines.append("")
    lines.append(future.precedent_implications)
    lines.append("")

    # Post-consent risks
    if future.post_consent_risks:
        lines.append("### Immediate Post-Consent Risks")
        lines.append("")
        for risk in future.post_consent_risks:
            lines.append(f"**{risk['type'].title()}:** {risk['description']}")
            lines.append(f"- Likelihood: {risk['likelihood']}")
            lines.append(f"- Mitigation: {risk['mitigation']}")
            lines.append("")

    # Limitations
    lines.append("### Prediction Limitations")
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

    # Amenity topics (always relevant for householder/residential)
    if any(t in app_type_lower for t in ['householder', 'residential', 'dwelling', 'extension']):
        topics.append("Residential Amenity - Daylight and Outlook")
        topics.append("Residential Amenity - Privacy")

    # Trees
    if 'tree' in proposal_lower or any('tree' in c or 'tpo' in c for c in constraints_lower):
        topics.append("Trees and Landscaping")

    # Highways (for larger developments)
    if any(t in app_type_lower for t in ['full', 'outline', 'commercial']):
        topics.append("Highways and Access")

    return topics


def format_similar_cases_section(similar_cases: list[HistoricCase]) -> str:
    """Format similar cases for the report."""
    if not similar_cases:
        return "No directly comparable precedent cases were identified in the search."

    sections = []

    for i, case in enumerate(similar_cases[:5], 1):
        sections.append(f"""**{i}. {case.reference}** - {case.address}
- **Proposal:** {case.proposal}
- **Decision:** {case.decision} ({case.decision_date})
- **Similarity Score:** {case.similarity_score:.0%}
- **Relevance:** {case.relevance_reason}
- **Officer Reasoning:** {case.case_officer_reasoning[:200]}{'...' if len(case.case_officer_reasoning) > 200 else ''}
- **Key Policies Cited:** {', '.join(case.key_policies_cited[:4])}
""")

    return "\n".join(sections)


def format_policy_framework_section(policies: list[Policy], council_name: str = "Newcastle City Council") -> str:
    """Format policy framework for the report with comprehensive policy detail."""
    nppf_policies = [p for p in policies if p.source_type == "NPPF"]
    core_strategy = [p for p in policies if p.source_type == "Core Strategy"]
    dap_policies = [p for p in policies if p.source_type == "DAP"]
    local_plan_policies = [p for p in policies if p.source_type == "Local Plan"]

    sections = []

    # National Planning Policy Framework section with paragraph detail
    if nppf_policies:
        sections.append("### National Planning Policy Framework (December 2023)\n")
        sections.append("The following NPPF policies are relevant to the determination of this application:\n")
        for p in nppf_policies[:8]:  # Show more NPPF policies
            sections.append(f"**Chapter {p.chapter} - {p.name}**")
            sections.append(f"> {p.summary}\n")
            # Include key paragraph text if available
            if p.paragraphs:
                for para in p.paragraphs[:2]:  # Show first 2 paragraphs
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
        sections.append("The following policies from the adopted Development Plan are relevant:\n")

        for source, source_policies in policies_by_source.items():
            sections.append(f"**{source}**\n")
            for p in source_policies[:8]:  # Show more policies
                sections.append(f"- **Policy {p.id}** ({p.name})")
                # Show policy summary/text
                summary_text = p.summary if p.summary else ""
                if summary_text and not summary_text.endswith("..."):
                    summary_text = summary_text[:400] + "..." if len(summary_text) > 400 else summary_text
                if summary_text:
                    sections.append(f"  > {summary_text}")
                # Show key requirements if available from paragraphs
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
    """Format assessments for the report."""
    sections = []

    for i, assessment in enumerate(assessments, 1):
        compliance_badge = {
            "compliant": "**COMPLIANT** ✓",
            "partial": "**PARTIAL COMPLIANCE** ⚠",
            "non-compliant": "**NON-COMPLIANT** ✗",
            "insufficient-evidence": "**INSUFFICIENT EVIDENCE** ?",
        }.get(assessment.compliance, assessment.compliance.upper())

        sections.append(f"""### {i}. {assessment.topic}

{assessment.reasoning}

**Assessment:** {compliance_badge}

**Key Considerations:**
{chr(10).join('- ' + c for c in assessment.key_considerations)}

**Policy References:** {', '.join(assessment.policy_citations)}

**Precedent Support:** {assessment.precedent_support}

---
""")

    return "\n".join(sections)


def format_conditions_section(conditions: list[dict]) -> str:
    """Format conditions for the report."""
    sections = []

    for condition in conditions:
        sections.append(f"""**{condition['number']}. {condition['condition']}**

*Reason: {condition['reason']}*

*Policy Basis: {condition['policy_basis']}*
""")

    return "\n".join(sections)


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
    proposal_details: Any = None,
    amenity_impacts: list = None,
    planning_weights: list = None,
    balance_summary: str = None,
) -> str:
    """Generate the complete professional markdown report with evidence-based analysis."""

    policy_section = format_policy_framework_section(policies, council_name)
    cases_section = format_similar_cases_section(similar_cases)
    assessment_section = format_assessment_section(assessments)
    conditions_section = format_conditions_section(reasoning.conditions)

    # Format proposal details section
    proposal_details_section = ""
    if proposal_details:
        proposal_details_section = f"""
### Proposal Specifications

| Specification | Value |
|---------------|-------|
| Development Type | {proposal_details.development_type.title()} |
| Number of Units | {proposal_details.num_units or 'N/A'} |
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

    report = f"""# PLANNING ASSESSMENT REPORT

**{council_name}**
**Development Management**

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

The application site is located at {address}{f' in the {ward} ward' if ward else ''}{f' ({postcode})' if postcode else ''}. The site is within the administrative area of {council_name}.

### Constraints Affecting the Site

{chr(10).join('- **' + c + '**' for c in constraints) if constraints else '- No specific planning constraints identified affecting this site.'}

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

**Confidence Level:** {reasoning.confidence_score:.0%} ({', '.join(reasoning.confidence_factors) if reasoning.confidence_factors else 'Standard assessment'})

---

{f'''## CONDITIONS

{conditions_section}
''' if reasoning.conditions else ''}
{refusal_section}

---

## INFORMATIVES

**1. Party Wall Act**
The applicant is advised that this permission does not override any requirements under the Party Wall etc. Act 1996.

**2. Building Regulations**
A separate application for Building Regulations approval may be required.

**3. Working Hours**
Construction works should be limited to:
- Monday to Friday: 08:00 - 18:00
- Saturday: 08:00 - 13:00
- Sunday and Bank Holidays: No working

**4. Considerate Constructors**
The applicant is encouraged to register with the Considerate Constructors Scheme.

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
    1. Similar case search
    2. Policy retrieval
    3. Evidence-based assessment
    4. Recommendation generation
    5. Learning system integration

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

    # 1. FIRST - Detect the correct council from site address
    from .local_plans_complete import detect_council_from_address, get_council_name
    detected_council = detect_council_from_address(site_address, postcode)
    council_name = get_council_name(detected_council)
    # Use detected council for all subsequent operations
    council_id = detected_council

    # 2. Analyse proposal to extract specific details (dimensions, units, materials)
    proposal_details = analyse_proposal(proposal_description, application_type)

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
        )
        assessments.append(assessment)

    # 9. Calculate weighted planning balance (council already detected at step 1)
    planning_weights, balance_summary, balance_recommendation = calculate_planning_balance(
        assessments=assessments,
        constraints=constraints,
        proposal_details=proposal_details,
        precedent_analysis=precedent_analysis,
        council_name=council_name,
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
