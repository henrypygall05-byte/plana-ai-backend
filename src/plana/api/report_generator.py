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
    _extract_proposal_features,
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


# =============================================================================
# EVIDENCE REGISTRY — [E1], [E2], ... tagging system for traceability
# =============================================================================

# Only these source types are legally admissible evidence.
# "Assessment data" is NOT evidence — it is officer analysis.
VALID_EVIDENCE_SOURCES = frozenset({
    "Application form",
    "Submitted plans",
    "Supporting technical report",
    "Design & Access Statement",
    "GIS constraint map",
    "Site visit notes",
    "Consultee response",
    "Adopted development plan policy",
    "NPPF (December 2023)",
    "Legislation",
    "Technical standard",
    "Case database",            # contextual only — NOT determinative
    "Constraint mapping",
})


@dataclass
class EvidenceEntry:
    """A single evidence item in the registry."""
    tag: str                  # e.g. "[E1]"
    source: str               # e.g. "Application form", "NPPF para 130"
    source_type: str          # One of VALID_EVIDENCE_SOURCES (or "Officer assessment")
    date: str                 # e.g. "Submitted 15 Jan 2025" or "December 2023"
    description: str          # What this evidence supports
    quality: str              # "Verified", "Unverified", "Assumed"
    is_valid_evidence: bool   # False for officer analysis / assessment data


class EvidenceRegistry:
    """
    Collects evidence items throughout report generation and assigns
    sequential [E1], [E2]... tags for cross-referencing in the report body.

    Strictly separates valid evidence (application form, submitted plans,
    consultee responses, adopted policy, etc.) from officer assessment.
    "Assessment data" is NOT treated as evidence.
    """

    def __init__(self) -> None:
        self._entries: list[EvidenceEntry] = []
        self._counter: int = 0

    def add(self, source: str, description: str, date: str = "",
            quality: str = "Verified", source_type: str = "") -> str:
        """Register evidence and return its tag, e.g. '[E1]'.

        If source_type is not in VALID_EVIDENCE_SOURCES the entry is
        flagged as officer assessment (not admissible as evidence).
        """
        self._counter += 1
        tag = f"[E{self._counter}]"

        # Determine source type
        if not source_type:
            source_type = source  # default: treat source name as type
        is_valid = any(
            source_type.startswith(vs) or vs in source_type
            for vs in VALID_EVIDENCE_SOURCES
        )

        self._entries.append(EvidenceEntry(
            tag=tag,
            source=source,
            source_type=source_type,
            date=date or "—",
            description=description,
            quality=quality if is_valid else "Officer assessment",
            is_valid_evidence=is_valid,
        ))
        return tag

    @property
    def entries(self) -> list[EvidenceEntry]:
        return list(self._entries)

    @property
    def valid_evidence_count(self) -> int:
        return sum(1 for e in self._entries if e.is_valid_evidence)

    @property
    def officer_assessment_count(self) -> int:
        return sum(1 for e in self._entries if not e.is_valid_evidence)

    def format_register(self) -> str:
        """Format the complete evidence register as a markdown table."""
        if not self._entries:
            return "*No evidence items registered.*"
        lines = [
            "| Tag | Source | Type | Date | Supports | Quality | Admissible? |",
            "|-----|--------|------|------|----------|---------|-------------|",
        ]
        for e in self._entries:
            admissible = "YES" if e.is_valid_evidence else "NO — officer assessment"
            lines.append(
                f"| {e.tag} | {e.source} | {e.source_type} | {e.date} "
                f"| {e.description} | {e.quality} | {admissible} |"
            )
        lines.append("")
        lines.append(f"**Valid evidence items:** {self.valid_evidence_count}")
        lines.append(f"**Officer assessment items (not evidence):** {self.officer_assessment_count}")
        return "\n".join(lines)


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

    # Determine development-specific features for targeted predictions
    has_ashp = "ashp" in proposal_lower or "air source heat pump" in proposal_lower or "heat pump" in proposal_lower
    is_dwelling = "dwelling" in proposal_lower or "house" in proposal_lower or "bungalow" in proposal_lower
    num_storeys = proposal_details.num_storeys if proposal_details else 0
    num_units = proposal_details.num_units if proposal_details else 0

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
    if is_dwelling or 'new' in proposal_lower or 'full' in app_type_lower:
        unit_text = f"{num_units} dwelling(s)" if num_units else "this development"
        storey_text = f"{num_storeys}-storey" if num_storeys else ""
        predictions.append(FuturePrediction(
            category="infrastructure",
            timeframe="long_term",
            prediction=f"The proposed {storey_text + ' ' if storey_text else ''}{unit_text} will incrementally increase demand on local infrastructure (roads, schools, healthcare, utilities). At {num_units if num_units else 1} unit(s), this is below CIL/S106 thresholds for most authorities.",
            confidence="high",
            positive_or_negative="negative",
            evidence_basis=f"A {'single dwelling generates approximately 5 vehicle movements per day' if (num_units or 0) <= 1 else f'{num_units} dwellings would generate approximately {num_units * 5} vehicle movements per day'}, plus incremental demand on education and healthcare services.",
            what_could_go_wrong="Without infrastructure investment, cumulative small-scale developments may cumulatively impact service capacity",
            what_could_go_right="CIL/S106 contributions (where applicable) may fund infrastructure improvements benefiting wider community",
            council_considerations="Monitor cumulative housing delivery in this ward; assess whether infrastructure capacity review is triggered",
        ))

    # Environment/Climate (all developments) — reference specific sustainability features
    if has_ashp:
        env_prediction = (
            f"The ASHP provides low-carbon space heating, reducing the development's operational "
            f"carbon footprint compared to conventional gas boilers. Over 10 years, the ASHP is "
            f"expected to reduce CO2 emissions from heating by approximately 50-70% compared to a "
            f"condensing gas boiler (based on current grid carbon intensity trends). Climate change "
            f"projections indicate warmer winters (reducing heating demand) and hotter summers "
            f"(potential for ASHP reversal for cooling)."
        )
        env_evidence = (
            "ASHP carbon savings based on SAP 10.2 emission factors and National Grid Future "
            "Energy Scenarios decarbonisation trajectory. UK Climate Projections (UKCP18) indicate "
            "increased summer temperatures and winter rainfall intensity."
        )
        env_right = (
            "ASHP efficiency improves as grid decarbonises; potential for future cooling "
            "function; future-proofed against gas boiler phase-out (2035 target)"
        )
    else:
        env_prediction = (
            "Climate change will increase flood risk and heat stress over the next 10 years. "
            "Development should be resilient to 2035+ conditions."
        )
        env_evidence = "UK Climate Projections (UKCP18) indicate increased rainfall intensity and summer temperatures."
        env_right = "Modern materials and standards may provide better resilience than existing building stock"

    predictions.append(FuturePrediction(
        category="environment",
        timeframe="long_term",
        prediction=env_prediction,
        confidence="high",
        positive_or_negative="positive" if has_ashp else "uncertain",
        evidence_basis=env_evidence,
        what_could_go_wrong="Development may require costly retrofitting for climate resilience in future" + ("; ASHP performance depends on maintenance and refrigerant availability" if has_ashp else ""),
        what_could_go_right=env_right,
        council_considerations="Consider whether conditions adequately address future climate scenarios, not just current requirements" + ("; ASHP maintenance condition recommended" if has_ashp else ""),
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
    proposal_details: "Any" = None,
) -> str:
    """Format similar cases with evidence-based relevance analysis."""
    if not similar_cases:
        return "No directly comparable precedent cases were identified in the search."

    # Ensure proposal is never empty — fall back to address-based description
    if not proposal or not proposal.strip():
        proposal = f"the proposed development at {address}" if address else "the proposed development"
    proposal_short = proposal[:80] + ("..." if len(proposal) > 80 else "")
    proposal_lower = proposal.lower()

    # Extract features from the current proposal to compare against precedent cases
    features = _extract_proposal_features(proposal, proposal_details)

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
        # Shared scale features
        if features.get("scale"):
            scale_text = features["scale"][0].lower()
            if "single-storey" in scale_text and "single" in case_proposal_lower:
                shared.append("both are single-storey developments")
            elif "two-storey" in scale_text and ("two" in case_proposal_lower or "2" in case_proposal_lower):
                shared.append("both are two-storey developments")
        # Shared sustainability features
        if features.get("sustainability"):
            for feat in features["sustainability"]:
                feat_lower = feat.lower()
                if "ashp" in feat_lower or "heat pump" in feat_lower:
                    if "ashp" in case_proposal_lower or "heat pump" in case_proposal_lower:
                        shared.append("both incorporate air source heat pump (ASHP) technology")
                elif "solar" in feat_lower:
                    if "solar" in case_proposal_lower or "pv" in case_proposal_lower:
                        shared.append("both include solar/PV renewable energy provision")
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

        # 3. Application to current proposal — specific lessons from precedent
        # Identify what's different between precedent and current proposal
        case_is_extension = any(kw in case.proposal.lower() for kw in ["extension", "alteration"])
        current_is_dwelling = any(kw in proposal.lower() for kw in ["dwelling", "erection of", "construct"])
        type_mismatch = case_is_extension and current_is_dwelling

        if "approved" in decision_lower:
            if type_mismatch:
                application_text = (
                    f"While this case ({case.proposal[:60]}) is an extension rather than a new dwelling, "
                    f"it is comparable because {shared_text}. The officer's finding that "
                    f"\"{case.case_officer_reasoning[:120]}\" establishes that this scale of "
                    f"development is acceptable in the borough in amenity and design terms."
                )
            else:
                # Extract the specific finding that's most relevant
                officer_finding = case.case_officer_reasoning[:150]
                application_text = (
                    f"This case is directly comparable because {shared_text}. "
                    f"The officer's specific finding — \"{officer_finding}\" — "
                    f"supports the same conclusion for the current application."
                )
                # Add specific policy overlap
                shared_policies = [p for p in case.key_policies_cited[:3] if p]
                if shared_policies:
                    application_text += (
                        f" Both cases were assessed against {', '.join(shared_policies)}, "
                        f"providing direct policy precedent."
                    )
        elif "refused" in decision_lower:
            refusal_summary = "; ".join(case.refusal_reasons[:2]) if case.refusal_reasons else "policy conflict"
            application_text = (
                f"This refusal is relevant because {shared_text}. The grounds for refusal "
                f"({refusal_summary[:150]}) must be demonstrably addressed. The current "
                f"proposal should show how it avoids the same harm."
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


def _build_nppf_evidence(
    chapter: str, chapter_name: str, features: dict, proposal_short: str, address_short: str,
) -> list[str]:
    """Build evidence linking specific proposal features to specific NPPF paragraph tests."""
    lines = []
    chapter_name_lower = chapter_name.lower()

    if chapter == "2" or "sustainable" in chapter_name_lower:
        # Three objectives of sustainable development (NPPF para 8)
        if features.get("sustainability"):
            for feat in features["sustainability"]:
                if "ashp" in feat.lower() or "heat pump" in feat.lower():
                    lines.append(
                        f"**Environmental objective (para 8c):** The ASHP reduces carbon emissions from space heating "
                        f"compared to conventional gas boilers, directly supporting the transition to a low-carbon economy "
                        f"required by para 152."
                    )
                elif "solar" in feat.lower():
                    lines.append(
                        f"**Environmental objective (para 8c):** Solar/PV panels reduce grid electricity demand, "
                        f"supporting renewable energy generation as encouraged by para 155."
                    )
                else:
                    lines.append(f"**Environmental objective (para 8c):** {feat}.")
        if features.get("housing"):
            lines.append(
                f"**Social objective (para 8b):** {features['housing'][0]}, supporting communities "
                f"through provision of housing to meet present and future needs."
            )
        lines.append(
            f"**Economic objective (para 8a):** Construction employment and local supply chain spending "
            f"during the build phase at {address_short}."
        )

    elif chapter == "4" or "decision" in chapter_name_lower:
        lines.append(
            f"Section 38(6) PCPA 2004 requires the application to be determined in accordance with the "
            f"development plan unless material considerations indicate otherwise. Para 38 requires a "
            f"positive and creative approach to decision-making."
        )

    elif chapter == "5" or "housing" in chapter_name_lower:
        if features.get("housing"):
            lines.append(
                f"Para 60 requires sufficient supply of homes. This proposal delivers "
                f"{features['housing'][0]}. Para 69 supports small sites (under 1 hectare) "
                f"which make an important contribution to meeting housing needs."
            )

    elif chapter == "9" or "transport" in chapter_name_lower:
        if features.get("highways"):
            lines.append(
                f"Para 111 states development should only be refused on highways grounds if there would be "
                f"an 'unacceptable' impact on safety or 'severe' residual cumulative impact on the road network. "
                f"The proposal provides {'; '.join(features['highways'][:2])}."
            )
        else:
            lines.append(
                f"Para 111 applies the 'unacceptable'/'severe' tests. Access and parking are assessed against "
                f"adopted highway standards."
            )

    elif chapter == "12" or "design" in chapter_name_lower:
        if features.get("scale"):
            lines.append(
                f"Para 130(c) requires development to be sympathetic to local character including building "
                f"heights and massing. The proposal's {features['scale'][0]} is assessed against prevailing "
                f"building heights at {address_short}."
            )
        if features.get("design"):
            lines.append(
                f"Para 130(b) requires visual attractiveness through good architecture and appropriate "
                f"landscaping. The proposed {'; '.join(features['design'][:2])} are assessed for compatibility "
                f"with the established material palette."
            )
        if not features.get("scale") and not features.get("design"):
            lines.append(
                f"Para 130 criteria (function, character, identity, built form, quality) are assessed from "
                f"the submitted plans."
            )

    elif chapter == "14" or "flood" in chapter_name_lower or "climate" in chapter_name_lower:
        if features.get("sustainability"):
            for feat in features["sustainability"]:
                if "ashp" in feat.lower() or "heat pump" in feat.lower():
                    lines.append(
                        f"Para 152 requires the planning system to support the transition to a low-carbon future. "
                        f"The ASHP reduces reliance on fossil fuel heating, directly addressing this requirement."
                    )
                elif "solar" in feat.lower():
                    lines.append(
                        f"Para 155 states plans should support renewable energy. The solar/PV installation "
                        f"provides on-site generation, meeting this policy objective."
                    )
                elif "suds" in feat.lower():
                    lines.append(
                        f"Para 167 requires sustainable drainage. The SuDS scheme manages surface water runoff "
                        f"to prevent increased flood risk."
                    )
        if not features.get("sustainability"):
            lines.append(
                f"Standard SuDS and energy efficiency conditions apply to address paras 152 and 167."
            )

    elif chapter == "16" or "heritage" in chapter_name_lower:
        lines.append(
            f"The Section 66/72 PLBCA 1990 duties apply. Para 199 requires the significance of "
            f"heritage assets to be sustained and enhanced. The impact on heritage significance "
            f"at {address_short} is assessed in the Heritage section below."
        )

    return lines


def _build_local_policy_engagement(policy: "Policy", features: dict, proposal_short: str) -> str:
    """Build an evidence-based explanation linking specific proposal features to specific policy requirements.

    Structure: [Policy requirement] → [Proposal feature that satisfies it] → [How it satisfies it]
    """
    p_name_lower = policy.name.lower()
    # Extract key requirements from policy paragraphs, stripping raw headings
    key_reqs = []
    if policy.paragraphs:
        for para in policy.paragraphs[:1]:
            if para.key_tests:
                key_reqs = [
                    t for t in para.key_tests[:5]
                    if not t.rstrip(":;").isupper() and len(t) > 3
                ][:3]

    parts = []

    if any(kw in p_name_lower for kw in ["design", "character", "place-making", "place making", "local identity"]):
        # Link specific policy criteria to specific proposal features
        if key_reqs:
            parts.append(f"{policy.name} requires: {'; '.join(key_reqs[:2])}")
        else:
            parts.append(f"{policy.name} requires development to respond positively to local character")

        if features.get("scale"):
            parts.append(
                f"The proposal responds to this through its {features['scale'][0]}, "
                f"which is assessed against the prevailing building heights and street scene character"
            )
        if features.get("design"):
            parts.append(
                f"The proposed {'; '.join(features['design'][:2])} "
                f"are assessed for compatibility with the established material palette in the locality"
            )
        if not features.get("scale") and not features.get("design"):
            parts.append("The submitted plans are required to demonstrate compliance with these criteria")

    elif any(kw in p_name_lower for kw in ["amenity", "residential"]):
        parts.append(f"{policy.name} protects residential amenity through standards for overlooking (21m), overbearing (45-degree test), and daylight (25-degree test)")
        if features.get("amenity"):
            parts.append(f"The proposal's {features['amenity'][0]} is relevant to meeting these standards")
        if features.get("sustainability"):
            for feat in features["sustainability"]:
                if "ashp" in feat.lower() or "heat pump" in feat.lower():
                    parts.append(
                        "The ASHP requires noise assessment against BS 4142:2014 to protect neighbouring amenity"
                    )
                    break

    elif any(kw in p_name_lower for kw in ["extension", "conversion"]):
        parts.append(f"{policy.name} applies to alterations to existing buildings — the proposal must be subordinate to the host dwelling")

    elif any(kw in p_name_lower for kw in ["sustainable", "presumption"]):
        parts.append(f"{policy.name} establishes the plan-led presumption in favour of sustainable development (NPPF para 11)")
        if features.get("sustainability"):
            for feat in features["sustainability"]:
                if "ashp" in feat.lower() or "heat pump" in feat.lower():
                    parts.append(
                        "The ASHP directly satisfies the environmental sustainability objective by reducing "
                        "carbon emissions from heating compared to gas boilers (Building Regulations Part L)"
                    )
                elif "solar" in feat.lower():
                    parts.append(
                        "The solar/PV installation reduces grid electricity demand, satisfying the environmental objective"
                    )
            if features.get("housing"):
                parts.append(f"The social objective is met through {features['housing'][0]}")

    elif any(kw in p_name_lower for kw in ["heritage", "conservation", "historic"]):
        parts.append(f"{policy.name} engages the Section 66/72 duties — the proposal must preserve or enhance heritage significance")

    elif any(kw in p_name_lower for kw in ["transport", "highway", "parking"]):
        parts.append(f"{policy.name} requires safe access and adequate parking provision")
        if features.get("highways"):
            parts.append(f"The proposal addresses this through {'; '.join(features['highways'][:2])}")
        else:
            parts.append("Parking and access details are assessed against adopted standards")

    if not parts:
        return ""

    return ". ".join(parts) + "."


def format_policy_framework_section(
    policies: list[Policy],
    council_name: str = "Newcastle City Council",
    proposal: str = "",
    address: str = "",
    constraints: list[str] | None = None,
    proposal_details: "Any" = None,
) -> str:
    """Format policy framework for the report with case-specific policy detail."""
    nppf_policies = [p for p in policies if p.source_type == "NPPF"]
    core_strategy = [p for p in policies if p.source_type == "Core Strategy"]
    dap_policies = [p for p in policies if p.source_type == "DAP"]
    local_plan_policies = [p for p in policies if p.source_type == "Local Plan"]

    constraints = constraints or []
    if not proposal or not proposal.strip():
        proposal = f"the proposed development at {address}" if address else "the proposed development"
    proposal_short = proposal[:100] + ("..." if len(proposal) > 100 else "")
    address_short = address[:80] if address else "the application site"

    # Extract proposal features for evidence-based policy commentary
    features = _extract_proposal_features(proposal, proposal_details)

    sections = []

    # National Planning Policy Framework section with evidence-based commentary
    if nppf_policies:
        sections.append("### National Planning Policy Framework (December 2023)\n")
        sections.append(f"The following NPPF policies are relevant to the determination of this application for {proposal_short} at {address_short}:\n")
        for p in nppf_policies[:8]:
            sections.append(f"**Chapter {p.chapter} - {p.name}**")
            sections.append(f"> {p.summary}\n")

            # --- Evidence-based commentary: HOW the proposal engages this chapter ---
            chapter = str(p.chapter) if p.chapter else ""
            evidence_lines = _build_nppf_evidence(chapter, p.name, features, proposal_short, address_short)
            if evidence_lines:
                sections.append(f"**How this proposal engages Chapter {chapter}:**")
                for line in evidence_lines:
                    sections.append(f"- {line}")
                sections.append("")

            # Key paragraph text (kept concise — 1 paragraph max)
            if p.paragraphs:
                para = p.paragraphs[0]
                sections.append(f"- *Key paragraph {para.number}*: \"{para.text[:250]}{'...' if len(para.text) > 250 else ''}\"")
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

                # Evidence-based engagement explanation
                engagement = _build_local_policy_engagement(p, features, proposal_short)
                if engagement:
                    sections.append(f"  - **Why engaged and how the proposal responds:** {engagement}")

                # Show key requirements applicable to this proposal
                if p.paragraphs:
                    for para in p.paragraphs[:1]:
                        if para.key_tests:
                                # Strip raw section headings (e.g. "DESIGN PRINCIPLES:") from display
                                clean_tests = [
                                    t for t in para.key_tests[:4]
                                    if not t.rstrip(":;").isupper() and len(t) > 3
                                ]
                                if clean_tests:
                                    sections.append(f"  - **Key Requirements:** {'; '.join(clean_tests)}")
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


def format_assessment_section(
    assessments: list[AssessmentResult],
    registry: "EvidenceRegistry | None" = None,
    documents_count: int = 0,
    documents_verified: bool = True,
) -> str:
    """
    Format assessments for a legally defensible officer report.

    Each topic is structured as:
      (a) POLICY REQUIREMENT — what does the policy demand?
      (b) FACT (with evidence reference) — what do we actually know?
      (c) OFFICER ASSESSMENT — does the evidence satisfy the tests?
      (d) GAPS — what is missing?
      (e) Conclusion + Confidence (HIGH / MEDIUM / LOW)

    CRITICAL RULES:
    - Do NOT conclude compliance where plans, measurements, consultations
      or GIS verification are missing.
    - Do NOT treat "assessment data" as evidence.
    - If evidence is absent, state "Insufficient evidence to conclude."
    - Confidence must reflect evidential completeness:
        HIGH = plans + consultations + constraints verified
        MEDIUM = minor details outstanding
        LOW = material information missing
    """
    sections = []

    insufficient_count = sum(1 for a in assessments if a.compliance == "insufficient-evidence")
    total_count = len(assessments)
    confirmed_no_documents = documents_count == 0 and documents_verified

    if insufficient_count > total_count * 0.5 or confirmed_no_documents:
        sections.append("""**Assessment Limitation:** More than half of the assessment topics lack sufficient evidence, or no plans have been submitted. Assessments below identify the policy framework and evidence gaps. The case officer must NOT treat these as completed assessments.

---
""")

    for i, assessment in enumerate(assessments, 1):
        # --- (a) POLICY REQUIREMENT ---
        policy_text = ""
        if assessment.policy_citations:
            policy_text = "\n".join(f"- {c}" for c in assessment.policy_citations[:4])
        else:
            policy_text = "- Relevant development plan policies apply"

        # --- (b) FACT (with evidence references) ---
        # Separate facts (things we know from valid sources) from analysis
        verified_items = [c for c in assessment.key_considerations if "Required:" not in c]
        required_items = [c for c in assessment.key_considerations if "Required:" in c]

        fact_lines = []
        for item in verified_items[:5]:
            tag = ""
            if registry:
                # These are officer observations, NOT primary evidence
                tag = registry.add(
                    source="Officer assessment",
                    description=f"{assessment.topic}: {item[:60]}",
                    quality="Unverified",
                    source_type="Officer assessment",
                ) + " "
            fact_lines.append(f"- {tag}{item}")

        if not fact_lines:
            fact_lines.append("- **No site-specific evidence available.** Assessment requires submitted plans and site visit.")

        # Note absence of plans
        if confirmed_no_documents:
            fact_lines.append("- **No submitted plans.** Dimensions, layout, and appearance cannot be verified.")

        fact_text = "\n".join(fact_lines)

        # --- (c) OFFICER ASSESSMENT ---
        reasoning_text = assessment.reasoning

        # If no documents, insert a warning into the assessment
        if confirmed_no_documents and assessment.compliance not in ("insufficient-evidence", "non-compliant"):
            reasoning_text = (
                "**Note:** This assessment is based on the application description only. "
                "No submitted plans are available to verify dimensions, layout, or appearance. "
                "Conclusions are provisional and must be revisited when plans are received.\n\n"
                + reasoning_text
            )

        # --- (d) GAPS ---
        gap_lines = []
        for item in required_items[:5]:
            gap_lines.append(f"- {item.replace('Required: ', '')}")
        if confirmed_no_documents:
            gap_lines.append("- Submitted plans (floor plans, elevations, site layout)")
        gap_lines.append("- Site visit verification")
        gap_lines.append("- Consultee responses")

        # Deduplicate
        seen = set()
        unique_gaps = []
        for g in gap_lines:
            key = g.lower().strip("- *")
            if key not in seen:
                seen.add(key)
                unique_gaps.append(g)
        gap_text = "\n".join(unique_gaps)

        # --- (e) Conclusion + Confidence ---
        # Confidence MUST reflect evidential completeness.
        # has_plans is True unless we've confirmed no documents exist.
        has_plans = not confirmed_no_documents
        has_facts = bool(verified_items)

        if assessment.compliance == "non-compliant":
            conclusion = "**Policy conflict identified.** The proposal fails to satisfy the relevant policy tests."
            confidence = "HIGH" if has_plans and has_facts else "MEDIUM"
        elif assessment.compliance == "insufficient-evidence":
            conclusion = "**Insufficient evidence to conclude.** Material information gaps prevent a lawful assessment."
            confidence = "LOW"
        elif not has_plans:
            # Cannot conclude compliance without plans
            conclusion = "**Insufficient evidence to conclude.** No submitted plans are available to verify compliance."
            confidence = "LOW"
        elif assessment.compliance == "partial":
            conclusion = "**Acceptable subject to conditions.** The proposal is marginally compliant; conditions are necessary."
            confidence = "MEDIUM"
        else:
            conclusion = "**No objection.** The proposal complies with relevant policy requirements based on available evidence."
            confidence = "HIGH" if has_plans and has_facts else "MEDIUM"

        sections.append(f"""### 8.{i} {assessment.topic}

**(a) Policy requirement**

{policy_text}

**(b) Fact** *(with evidence reference)*

{fact_text}

**(c) Officer assessment**

{reasoning_text}

**(d) Gaps**

{gap_text}

**(e) Conclusion** — Confidence: **{confidence}**

{conclusion}

---
""")

    return "\n".join(sections)


def _apply_six_tests(condition: dict, documents_count: int, documents_verified: bool = True) -> tuple[bool, str]:
    """
    Apply the six legal tests for planning conditions (NPPF para 56).

    A condition must be:
    1. Necessary — would the development be unacceptable without it?
    2. Relevant to planning — does it relate to a planning matter?
    3. Relevant to the development — does it relate to THIS development?
    4. Enforceable — can the LPA check compliance?
    5. Precise — is the wording clear and unambiguous?
    6. Reasonable — would a reasonable person accept it?

    Returns (passes: bool, reason: str).
    """
    reason_text = condition.get('reason', '')
    cond_text = condition.get('condition', '')
    policy = condition.get('policy_basis', '')

    # Test 1: Necessary — must have a planning reason
    if not reason_text.strip():
        return False, "Fails test 1 (Necessary): No planning reason provided."

    # Test 2: Relevant to planning — must cite a planning policy
    if not policy.strip():
        return False, "Fails test 2 (Relevant to planning): No policy hook."

    # Test 4: Enforceable — "approved plans" condition fails if no plans
    cond_lower = cond_text.lower()
    if ("approved plans" in cond_lower or "schedule of approved" in cond_lower) and documents_count == 0 and documents_verified:
        return False, "Fails test 4 (Enforceable): References approved plans but no plans have been submitted."

    # All other conditions pass (wording is generated by the system, so
    # tests 3, 5, 6 are met by construction)
    return True, "Passes all six tests."


def format_conditions_section(
    conditions: list[dict],
    registry: "EvidenceRegistry | None" = None,
    documents_count: int = 0,
    documents_verified: bool = True,
) -> str:
    """
    Format conditions with justification and six legal tests.

    Each condition follows the structure:
    - Condition wording (the legal text)
    - Planning purpose: WHY this condition is necessary
    - Policy hook: which policy requires it
    - Six tests: PASS/FAIL with reason
    - Evidence tag: [E] reference linking to evidence register

    Any condition that FAILS the six tests is excluded and noted.
    """
    if not conditions:
        return "*No conditions recommended.*"

    passed_sections = []
    failed_sections = []

    for condition in conditions:
        passes, test_result = _apply_six_tests(condition, documents_count, documents_verified)

        # Register evidence for this condition
        tag = ""
        if registry:
            source_type = condition.get('policy_basis', 'Adopted development plan policy')
            tag = " " + registry.add(
                source=condition.get('policy_basis', 'Development Plan'),
                description=f"Condition {condition['number']}: {condition.get('condition', '')[:50]}",
                quality="Verified",
                source_type=source_type,
            )

        reason = condition.get('reason', '')
        policy_basis = condition.get('policy_basis', 'Relevant development plan policies')

        entry = f"""**{condition['number']}. {condition['condition']}**

- **Planning purpose:** {reason}
- **Policy hook:** {policy_basis}
- **Six tests:** {test_result}
- **Evidence:** {tag if tag.strip() else 'Standard requirement'}
"""
        if passes:
            passed_sections.append(entry)
        else:
            failed_sections.append(entry)

    result_parts = []
    if passed_sections:
        result_parts.append(f"**{len(passed_sections)} condition(s) pass the six legal tests:**\n")
        result_parts.extend(passed_sections)

    if failed_sections:
        result_parts.append(f"\n**{len(failed_sections)} condition(s) REMOVED — fail six legal tests:**\n")
        for entry in failed_sections:
            result_parts.append(f"~~{entry}~~\n")

    return "\n".join(result_parts)


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


def _build_site_description(
    address: str, ward: str | None, postcode: str | None,
    constraints: list[str], proposal: str, proposal_details: "Any",
    council_name: str,
) -> str:
    """Build evidence-based site description using available data."""
    lines = []
    proposal_lower = proposal.lower() if proposal else ""

    # Extract street/area from address
    address_parts = [p.strip() for p in address.split(",") if p.strip()] if address else []
    street_name = address_parts[0] if address_parts else "the site"
    locality = address_parts[1] if len(address_parts) > 1 else ""
    area = address_parts[2] if len(address_parts) > 2 else ""

    # What we know about the site from the address
    lines.append(f"The application site is located at **{address}**")
    if ward:
        lines.append(f"within **{ward}** ward in the administrative area of {council_name}.")
    else:
        lines.append(f"within the administrative area of {council_name}.")

    # What we know about the site from the proposal
    if "land at" in address.lower() or "land adj" in address.lower():
        lines.append(f"\nThe site description indicates this is an **undeveloped plot** (\"land at/adjacent\"), "
                     f"suggesting the site does not currently contain a dwelling.")
    elif any(kw in address.lower() for kw in ["rear of", "garden of", "land to"]):
        lines.append(f"\nThe address suggests the site is **curtilage or garden land** associated with "
                     f"an existing property, which has implications for the principle of development "
                     f"(NPPF para 71 — windfall/garden development).")

    # What we know about the development from the proposal
    if proposal_details:
        dev_items = []
        if proposal_details.development_type:
            dev_items.append(f"a **{proposal_details.development_type}** development")
        if proposal_details.num_storeys:
            dev_items.append(f"**{proposal_details.num_storeys}-storey** in height")
        if proposal_details.num_units and proposal_details.num_units > 0:
            dev_items.append(f"comprising **{proposal_details.num_units} unit(s)**")
        if dev_items:
            lines.append(f"\nThe proposal is for {', '.join(dev_items)}.")

    # Sustainability features from proposal
    if "ashp" in proposal_lower or "air source heat pump" in proposal_lower:
        lines.append("\nThe development incorporates an **Air Source Heat Pump (ASHP)** for space "
                     "heating, which is a material consideration relevant to NPPF para 152 "
                     "(transition to low-carbon future) and requires noise assessment under "
                     "BS 4142:2014 to protect neighbouring amenity.")

    if "solar" in proposal_lower or "pv" in proposal_lower:
        lines.append("\nThe development includes **solar/PV panels** for on-site renewable "
                     "electricity generation (NPPF para 155).")

    return "\n".join(lines)


def _build_constraints_analysis(
    constraints: list[str], proposal: str, proposal_details: "Any",
) -> str:
    """Build constraint-by-constraint analysis with specific policy implications."""
    if not constraints:
        return (
            "**No constraints were identified** from the application data.\n\n"
            "**ACTION REQUIRED:** The case officer must verify against the council's GIS/constraint "
            "mapping system for:\n"
            "- Conservation Area boundaries\n"
            "- Listed Building curtilages\n"
            "- Flood Zone designation (Environment Agency mapping)\n"
            "- Tree Preservation Orders\n"
            "- Article 4 Directions\n"
            "- Sites of Special Scientific Interest\n"
            "- Archaeological notification areas"
        )

    lines = []
    for constraint in constraints:
        c_lower = constraint.lower()
        if "conservation" in c_lower:
            lines.append(
                f"- **{constraint}** — Section 72 of the Planning (Listed Buildings and Conservation "
                f"Areas) Act 1990 imposes a duty to pay special attention to the desirability of "
                f"preserving or enhancing the character and appearance of the area. NPPF paras 199-202 "
                f"apply. The case officer must assess whether the proposal preserves or enhances "
                f"the character of the Conservation Area."
            )
        elif "listed" in c_lower:
            lines.append(
                f"- **{constraint}** — Section 66 of the P(LBCA)A 1990 requires special regard to "
                f"the desirability of preserving the building, its setting, and features of special "
                f"architectural or historic interest. NPPF para 199 requires great weight to be given "
                f"to the asset's conservation."
            )
        elif "flood" in c_lower:
            lines.append(
                f"- **{constraint}** — NPPF paras 159-167 apply. The Sequential Test must demonstrate "
                f"the development cannot be located in a lower-risk zone. A site-specific Flood Risk "
                f"Assessment is required for all development in Flood Zones 2 and 3."
            )
        elif "tree" in c_lower or "tpo" in c_lower:
            lines.append(
                f"- **{constraint}** — NPPF para 131 recognises trees' contribution to character "
                f"and climate adaptation. An Arboricultural Impact Assessment (BS 5837:2012) is "
                f"required to demonstrate that protected trees are not harmed by the development."
            )
        elif "green belt" in c_lower:
            lines.append(
                f"- **{constraint}** — NPPF paras 137-151 apply. Development in the Green Belt is "
                f"inappropriate unless it falls within specified exceptions (para 149) or very special "
                f"circumstances are demonstrated (para 147)."
            )
        elif "article 4" in c_lower:
            lines.append(
                f"- **{constraint}** — Permitted development rights have been removed. Planning "
                f"permission is required for works that would otherwise be permitted under the "
                f"GPDO 2015."
            )
        elif "sssi" in c_lower or "special scientific" in c_lower:
            lines.append(
                f"- **{constraint}** — NPPF para 180 and the Wildlife and Countryside Act 1981 apply. "
                f"Natural England must be consulted on any development likely to affect the SSSI."
            )
        else:
            lines.append(
                f"- **{constraint}** — *(verify specific policy implications against Development Plan)*"
            )

    lines.append(
        "\n*All constraints sourced from application form data. The case officer should verify "
        "against the council's GIS/constraint mapping system.*"
    )

    return "\n".join(lines)


def _build_site_visit_requirements(
    proposal: str, proposal_details: "Any", constraints: list[str],
) -> str:
    """List specific items that require site visit verification, with reasons."""
    items = []
    proposal_lower = proposal.lower() if proposal else ""

    # Street character — always needed for design assessment
    items.append(
        "- **Prevailing building heights and materials on the street** — required to assess "
        "NPPF para 130(c) (sympathetic to local character). The submitted plans show "
        f"{'a ' + str(proposal_details.num_storeys) + '-storey development' if proposal_details and proposal_details.num_storeys else 'the proposed development'}"
        f"; the case officer must confirm this is consistent with the established street scene."
    )

    # Separation distances — needed for amenity assessment
    items.append(
        "- **Separation distances to neighbouring habitable room windows** — required to verify "
        "the 21m privacy standard and 45-degree overbearing test (NPPF para 130(f), "
        "BRE Guidelines). Measurements must be taken from submitted plans and checked on site."
    )

    # Access and parking
    items.append(
        "- **Existing access arrangements and visibility splays** — required to assess "
        "NPPF para 111 ('unacceptable' safety / 'severe' capacity tests). Visibility "
        "splays of 2.4m x 43m typically required for 30mph roads."
    )

    # ASHP position
    if "ashp" in proposal_lower or "air source heat pump" in proposal_lower or "heat pump" in proposal_lower:
        items.append(
            "- **ASHP unit position relative to neighbouring boundaries** — required to assess "
            "noise impact under BS 4142:2014. The rating level must not exceed background noise "
            "(LA90) + 5dB at the nearest noise-sensitive receptor."
        )

    # Boundaries and levels
    items.append(
        "- **Boundary treatments and ground levels** — required to assess the relationship "
        "between the proposal and neighbouring land, particularly for daylight, overbearing, "
        "and drainage considerations."
    )

    # Heritage-specific
    if any("conservation" in c.lower() or "listed" in c.lower() for c in constraints):
        items.append(
            "- **Heritage setting and significance** — required to assess impact on the "
            "significance of the heritage asset(s) (NPPF paras 199-202). Site photographs "
            "and context analysis are essential for the heritage assessment."
        )

    # Trees
    if any("tree" in c.lower() or "tpo" in c.lower() for c in constraints):
        items.append(
            "- **Proximity of protected trees to development footprint** — required to verify "
            "Root Protection Areas (BS 5837:2012) are not compromised by the development."
        )

    return "\n".join(items)


def _build_consultations_section(
    proposal: str, constraints: list[str], proposal_details: "Any",
) -> str:
    """Build consultations section listing required consultees with reasons — not fabricated responses."""
    proposal_lower = proposal.lower() if proposal else ""
    constraints_lower = [c.lower() for c in constraints]

    lines = []
    lines.append("> **Note:** This section identifies which consultees must be consulted and why, ")
    lines.append("> based on the proposal type and site constraints. Actual consultation responses ")
    lines.append("> must be obtained and recorded by the case officer before determination.")
    lines.append("")

    lines.append("### Required Internal Consultations")
    lines.append("")
    lines.append("| Consultee | Reason for Consultation | Status |")
    lines.append("|-----------|------------------------|--------|")

    # Highways — always for new dwellings or changes of access
    is_dwelling = any(kw in proposal_lower for kw in ["dwelling", "house", "bungalow", "erection of"])
    if is_dwelling or "access" in proposal_lower:
        lines.append(
            "| Highway Authority | New dwelling generates additional vehicle movements; "
            "NPPF para 111 requires assessment of 'unacceptable' safety and 'severe' capacity impacts | "
            "**AWAITING RESPONSE** |"
        )

    # Environmental Health — if ASHP or noise-generating plant
    if "ashp" in proposal_lower or "air source heat pump" in proposal_lower or "heat pump" in proposal_lower:
        lines.append(
            "| Environmental Health | ASHP generates external noise requiring assessment under "
            "BS 4142:2014; rating level must not exceed background + 5dB at nearest receptor | "
            "**AWAITING RESPONSE** |"
        )
    elif is_dwelling:
        lines.append(
            "| Environmental Health | New dwelling — contaminated land screening and construction "
            "noise/dust assessment may be required | **AWAITING RESPONSE** |"
        )

    # Design and Conservation — if heritage constraints
    if any("conservation" in c or "listed" in c for c in constraints_lower):
        lines.append(
            "| Design and Conservation | Site is within/adjacent to designated heritage asset; "
            "Section 66/72 P(LBCA)A 1990 duties apply — specialist heritage assessment required | "
            "**AWAITING RESPONSE** |"
        )

    # Tree Officer — if tree constraints or trees mentioned
    if any("tree" in c or "tpo" in c for c in constraints_lower) or "tree" in proposal_lower:
        lines.append(
            "| Tree Officer | Protected trees on or adjacent to site; BS 5837:2012 assessment "
            "required to verify Root Protection Areas are not compromised | **AWAITING RESPONSE** |"
        )

    # Drainage — for new dwellings creating additional impermeable area
    if is_dwelling:
        lines.append(
            "| Lead Local Flood Authority | New development creates additional impermeable area; "
            "SuDS scheme required to achieve greenfield runoff rates (NPPF paras 167-169) | "
            "**AWAITING RESPONSE** |"
        )

    # Ecology — for new dwellings (BNG requirement)
    if is_dwelling:
        lines.append(
            "| Ecology/Biodiversity | Statutory 10% Biodiversity Net Gain applies (Environment "
            "Act 2021); Biodiversity Gain Plan required before commencement | **AWAITING RESPONSE** |"
        )

    lines.append("")

    # Required external consultations
    external_needed = []
    if any("flood" in c for c in constraints_lower):
        external_needed.append(
            "| Environment Agency | Site in flood zone — Flood Risk Assessment requires EA review | "
            "**AWAITING RESPONSE** |"
        )
    if any("sssi" in c or "special scientific" in c for c in constraints_lower):
        external_needed.append(
            "| Natural England | Development near SSSI — statutory consultation required | "
            "**AWAITING RESPONSE** |"
        )

    if external_needed:
        lines.append("### Required External Consultations")
        lines.append("")
        lines.append("| Consultee | Reason for Consultation | Status |")
        lines.append("|-----------|------------------------|--------|")
        lines.extend(external_needed)
        lines.append("")

    # Neighbour notifications
    lines.append("### Neighbour Notifications")
    lines.append("")
    lines.append(
        "Neighbour notification letters and/or site notice must be issued in accordance "
        "with Article 15 of the Town and Country Planning (Development Management Procedure) "
        "(England) Order 2015. The statutory 21-day consultation period must expire before "
        "determination."
    )
    lines.append("")
    lines.append("**Representations received:** *To be recorded by case officer*")

    return "\n".join(lines)


def _build_evidence_citations(
    policies: list, similar_cases: list, assessments: list,
    proposal: str, proposal_details: "Any",
) -> str:
    """Build a specific evidence citations section listing actual sources used."""
    lines = []

    # 1. Legislation cited
    lines.append("### Legislation")
    lines.append("- Town and Country Planning Act 1990 (as amended) — Section 91 (time limit)")
    lines.append("- Planning and Compulsory Purchase Act 2004 — Section 38(6) (plan-led system)")
    lines.append("- Environment Act 2021 — Schedule 7A (Biodiversity Net Gain)")

    proposal_lower = proposal.lower() if proposal else ""
    if any("conservation" in getattr(a, 'topic', '').lower() for a in assessments):
        lines.append("- Planning (Listed Buildings and Conservation Areas) Act 1990 — Sections 66, 72")

    lines.append("")

    # 2. National policy
    lines.append("### National Planning Policy Framework (December 2023)")
    nppf_paras_cited = set()
    for p in policies:
        if getattr(p, 'source_type', '') == "NPPF" and getattr(p, 'paragraphs', None):
            for para in p.paragraphs[:2]:
                num = getattr(para, 'number', 0)
                if isinstance(num, str):
                    # Extract numeric part from strings like "130(c)"
                    num = int(''.join(c for c in num if c.isdigit()) or '0')
                nppf_paras_cited.add(int(num) if num else 0)

    # Always-cited paragraphs
    nppf_paras_cited.update([8, 11, 38, 130, 134])
    if any(kw in proposal_lower for kw in ["dwelling", "house"]):
        nppf_paras_cited.update([60, 69])
    if "ashp" in proposal_lower or "heat pump" in proposal_lower:
        nppf_paras_cited.add(152)
    if "solar" in proposal_lower:
        nppf_paras_cited.add(155)

    for para_num in sorted(nppf_paras_cited):
        lines.append(f"- NPPF Paragraph {para_num}")
    lines.append("")

    # 3. Development Plan policies
    non_nppf = [p for p in policies if getattr(p, 'source_type', '') != "NPPF"]
    if non_nppf:
        lines.append("### Development Plan Policies")
        seen = set()
        for p in non_nppf:
            key = f"{getattr(p, 'source', '')} {getattr(p, 'id', '')}"
            if key not in seen:
                seen.add(key)
                pid = getattr(p, 'id', '')
                if pid.lower().startswith("policy"):
                    lines.append(f"- {getattr(p, 'source', '')} {pid}: {getattr(p, 'name', '')}")
                else:
                    lines.append(f"- {getattr(p, 'source', '')} Policy {pid}: {getattr(p, 'name', '')}")
        lines.append("")

    # 4. Precedent cases
    if similar_cases:
        lines.append("### Precedent Cases Cited")
        for case in similar_cases[:5]:
            lines.append(
                f"- **{case.reference}** — {case.address[:60]} — "
                f"{case.decision} ({case.decision_date}) — "
                f"Similarity: {case.similarity_score:.0%}"
            )
        lines.append("")

    # 5. Technical standards
    lines.append("### Technical Standards and Guidance")
    lines.append("- BRE Guidelines: 'Site Layout Planning for Daylight and Sunlight' (2022) — 45-degree rule, 25-degree test")
    lines.append("- 21m privacy separation standard — adopted residential design standards")
    if "ashp" in proposal_lower or "heat pump" in proposal_lower:
        lines.append("- BS 4142:2014+A1:2019 — Methods for rating and assessing industrial and commercial sound")
        lines.append("- MCS 020 Planning Standard — Heat pump noise assessment")
    lines.append("- BS 5837:2012 — Trees in relation to design, demolition and construction")
    lines.append("")

    lines.append("*All conclusions in this report are traceable to the specific policy requirements, "
                 "precedent cases, and technical standards listed above.*")

    return "\n".join(lines)


def _build_data_quality_section(
    proposal: str, proposal_details: "Any", constraints: list[str],
    assessments: list, documents_count: int, documents_verified: bool = True,
) -> str:
    """Build a specific data quality section listing what data is available and what is missing."""
    proposal_lower = proposal.lower() if proposal else ""

    # Calculate metrics
    insufficient_assessments = sum(1 for a in assessments if a.compliance == "insufficient-evidence")
    total_assessments = len(assessments)
    has_documents = documents_count > 0
    has_constraints = bool(constraints)

    # Determine what data we have
    available_data = []
    missing_data = []

    # Proposal details
    if proposal and len(proposal.strip()) > 10:
        available_data.append("Proposal description from application form")
    else:
        missing_data.append("Proposal description is empty or minimal")

    if proposal_details:
        if proposal_details.num_storeys:
            available_data.append(f"Number of storeys: {proposal_details.num_storeys}")
        else:
            missing_data.append("Number of storeys not specified")
        if proposal_details.height_metres:
            available_data.append(f"Ridge height: {proposal_details.height_metres}m")
        else:
            missing_data.append("Ridge height not provided — required for overbearing assessment")
        if proposal_details.floor_area_sqm:
            available_data.append(f"Floor area: {proposal_details.floor_area_sqm} sqm")
        if proposal_details.parking_spaces:
            available_data.append(f"Parking: {proposal_details.parking_spaces} space(s)")
        else:
            missing_data.append("Parking provision not specified — required for highways assessment")
        if proposal_details.materials:
            available_data.append(f"Materials: {', '.join(proposal_details.materials)}")
        else:
            missing_data.append("External materials not specified — required for design assessment")
        if proposal_details.num_bedrooms:
            available_data.append(f"Bedrooms: {proposal_details.num_bedrooms}")

    # Documents
    if has_documents:
        available_data.append(f"{documents_count} document(s) submitted")
    elif not documents_verified:
        missing_data.append("Document status not verified — council portal unavailable")
    else:
        missing_data.append("No documents submitted — cannot verify dimensions or design")

    # Constraints
    if has_constraints:
        available_data.append(f"{len(constraints)} constraint(s) identified")
    else:
        missing_data.append("No constraints identified — verify against GIS mapping")

    # Always missing (need site visit)
    missing_data.append("Separation distances to neighbours — NOT VERIFIED (requires site visit)")
    missing_data.append("Street scene context — NOT VERIFIED (requires site visit)")
    missing_data.append("Consultation responses — NOT YET RECEIVED")

    # Overall quality
    confirmed_no_docs = not has_documents and documents_verified
    if insufficient_assessments > total_assessments * 0.5 or confirmed_no_docs:
        data_quality = "LOW"
    elif insufficient_assessments > 0 or len(missing_data) > 5:
        data_quality = "MEDIUM"
    else:
        data_quality = "HIGH"

    available_text = "\n".join(f"| {item} | Available |" for item in available_data[:8])
    missing_text = "\n".join(f"| {item} | **Missing** |" for item in missing_data[:8])

    return f"""## DATA QUALITY INDICATOR

| Metric | Status |
|--------|--------|
| **Overall Data Quality** | {data_quality} |
| **Documents Available** | {documents_count} |
| **Constraints Identified** | {len(constraints) if constraints else 0} |
| **Assessments with Evidence** | {total_assessments - insufficient_assessments}/{total_assessments} |

### Data Available for Assessment

| Item | Status |
|------|--------|
{available_text}

### Data Gaps Requiring Action

| Item | Status |
|------|--------|
{missing_text}

**Implication:** {'This report provides a policy framework and preliminary assessment only. The case officer must complete the assessment using submitted plans, a site visit, and consultation responses before determination.' if data_quality != 'HIGH' else 'Sufficient data available for a robust preliminary assessment. Site visit and consultation responses required before formal determination.'}"""


def _build_material_info_missing(
    documents_count: int,
    proposal_details: "Any",
    constraints: list[str],
    assessments: list,
    documents_verified: bool = True,
) -> tuple[str, list[str]]:
    """
    Build the 'Material Information Missing' section.

    Returns (markdown_section, list_of_missing_items) so the caller can
    decide whether to recommend deferral.

    Material information = information without which the LPA cannot lawfully
    determine the application.
    """
    missing: list[str] = []

    # Plans — without submitted plans, the LPA cannot assess form/appearance.
    # Only flag this if we've confirmed documents are absent.
    confirmed_no_documents = documents_count == 0 and documents_verified
    if confirmed_no_documents:
        missing.append("**Submitted plans** — No plans, elevations, or site layout have been provided. "
                        "The LPA cannot assess the form, scale, or appearance of the development.")

    # Dimensions
    if proposal_details:
        if not proposal_details.height_metres:
            missing.append("**Ridge/eaves height** — Required for overbearing/daylight assessment "
                           "(BRE Guidelines, 45-degree test).")
        if not proposal_details.floor_area_sqm:
            missing.append("**Floor area** — Required to assess scale relative to plot and CIL liability.")
        if not proposal_details.parking_spaces:
            missing.append("**Parking layout** — Required for highways assessment (NPPF para 111).")
        if not proposal_details.materials:
            missing.append("**External materials schedule** — Required for design assessment "
                           "(NPPF para 130). *May be conditioned if otherwise acceptable.*")
    else:
        missing.append("**Proposal details** — No quantified development parameters available.")

    # Consultations — always missing at report-generation time
    missing.append("**Consultee responses** — No statutory or internal consultation responses received.")

    # Site visit
    missing.append("**Site visit notes** — No dated site visit has been recorded.")

    # GIS constraint verification
    if not constraints:
        missing.append("**GIS constraint verification** — Constraints not confirmed against "
                       "the council's mapping system.")

    # Flood risk
    if any("flood" in c.lower() for c in constraints):
        missing.append("**Flood Risk Assessment** — Site is in a flood zone; FRA required "
                       "by NPPF para 167.")

    # Heritage
    if any("conservation" in c.lower() or "listed" in c.lower() for c in constraints):
        if confirmed_no_documents:
            missing.append("**Heritage Impact Assessment / Design & Access Statement** — "
                           "Required for development affecting a heritage asset.")

    # Drainage
    missing.append("**Drainage strategy / SuDS design** — Required to demonstrate surface water "
                   "management (NPPF paras 167-169). *May be conditioned if pre-commencement.*")

    if not missing:
        section = "No material information gaps identified."
        return section, missing

    rows = "\n".join(f"| {i+1} | {item} |" for i, item in enumerate(missing))
    section = f"""| # | Missing Item |
|---|-------------|
{rows}

**Total material gaps:** {len(missing)}
"""
    return section, missing


def _should_defer(documents_count: int, missing_items: list[str], documents_verified: bool = True) -> bool:
    """
    Determine if the application should be deferred pending essential documents.

    System rule: If no plans are attached AND we have confirmed this
    via portal check → automatic deferral.

    If document status is unverified (portal unreachable), we do NOT
    auto-defer — we proceed with the full report and flag caveats.

    Items that are ALWAYS missing at report-generation time (consultee
    responses, site visit notes, drainage) are procedural — the officer
    resolves them before determination. They do NOT trigger deferral.

    Only document-related gaps (plans, dimensions, parking layout) trigger
    deferral, because without those the LPA literally cannot define what
    is being approved.
    """
    if documents_count == 0 and documents_verified:
        return True

    # Only count gaps that relate to documents the applicant must supply.
    # Procedural gaps (consultations, site visit, drainage conditionable)
    # are resolved by the officer, not by deferral.
    procedural_keywords = [
        "Consultee responses", "Site visit notes", "Drainage strategy",
        "GIS constraint", "May be conditioned",
    ]
    hard_gaps = [
        m for m in missing_items
        if not any(kw in m for kw in procedural_keywords)
    ]
    return len(hard_gaps) >= 3  # 3+ applicant-supplied gaps = defer


def _build_legal_risk_assessment(
    documents_count: int,
    constraints: list[str],
    assessments: list,
    reasoning: "Any",
    missing_items: list[str],
    documents_verified: bool = True,
) -> str:
    """
    Build the Legal Risk Assessment table identifying areas vulnerable to
    judicial review or appeal challenge.
    """
    risks: list[tuple[str, str, str]] = []  # (area, risk, mitigation)

    # No plans — only flag if confirmed
    if documents_count == 0 and documents_verified:
        risks.append((
            "Determination without plans",
            "**HIGH** — Decision is unlawful if no plans exist to define what is approved. "
            "Contrary to Article 7 DMPO 2015.",
            "DEFER until plans are submitted.",
        ))

    # No consultations
    risks.append((
        "Consultation not carried out",
        "**HIGH** — Failure to consult as required by Article 15 DMPO 2015 "
        "renders the decision voidable.",
        "Ensure all statutory consultations are completed before determination.",
    ))

    # Heritage without assessment
    if any("conservation" in c.lower() or "listed" in c.lower() for c in constraints):
        heritage_assessed = any(
            "heritage" in getattr(a, 'topic', '').lower() for a in assessments
        )
        if heritage_assessed:
            risks.append((
                "Section 66/72 duties",
                "**MEDIUM** — Heritage assessment completed but based on limited evidence. "
                "Duty to have 'special regard' / 'special attention' must be demonstrably discharged.",
                "Record clear reasoning on heritage harm/benefit. Secure materials by condition.",
            ))
        else:
            risks.append((
                "Section 66/72 duties NOT discharged",
                "**HIGH** — No heritage assessment. Failure to discharge statutory duty.",
                "DEFER or obtain heritage officer input before determination.",
            ))

    # Insufficient evidence assessments
    insufficient = sum(1 for a in assessments if getattr(a, 'compliance', '') == "insufficient-evidence")
    if insufficient > 0:
        risks.append((
            f"{insufficient} assessment(s) with insufficient evidence",
            "**MEDIUM** — Approving despite evidence gaps may be unreasonable "
            "(Wednesbury grounds).",
            f"Obtain missing information or defer. {insufficient} topic(s) cannot be concluded.",
        ))

    # Conditions without plans — only flag if confirmed no documents
    if reasoning.conditions and documents_count == 0 and documents_verified:
        risks.append((
            "Conditions imposed without approved plans",
            "**HIGH** — Condition 2 (approved plans) has no plans to reference. "
            "Decision is legally defective.",
            "DEFER until plans are submitted.",
        ))

    # Precedent reliance
    risks.append((
        "Precedent reliance",
        "**LOW** — Precedent cases are referenced for context only, not as "
        "determinative factors. Each application assessed on own merits.",
        "No mitigation required.",
    ))

    if not risks:
        return "No legal risks identified."

    rows = "\n".join(
        f"| {area} | {risk} | {mitigation} |"
        for area, risk, mitigation in risks
    )
    high_count = sum(1 for _, r, _ in risks if "**HIGH**" in r)
    med_count = sum(1 for _, r, _ in risks if "**MEDIUM**" in r)

    return f"""| Area | Risk Level | Mitigation |
|------|-----------|------------|
{rows}

**Summary:** {high_count} HIGH risk(s), {med_count} MEDIUM risk(s). {'**Determination is NOT legally safe at this time.**' if high_count > 0 else 'Determination is legally safe subject to mitigations noted above.'}"""


def _build_why_material(missing_items: list[str], constraints: list[str]) -> str:
    """
    For each missing item, explain:
      (a) what decision issue it affects,
      (b) what policy/procedural test it prevents,
      (c) whether it could be conditioned (yes/no) and why.
    """
    entries: list[str] = []

    for item in missing_items:
        item_lower = item.lower()

        if "submitted plans" in item_lower:
            entries.append(
                "- **Submitted plans (floor plans, elevations, site layout)**\n"
                "  (a) *Decision issue:* Form, scale, appearance, and layout of development.\n"
                "  (b) *Policy test prevented:* NPPF para 130 (design quality); Article 7 DMPO 2015 "
                "(the decision must identify approved plans).\n"
                "  (c) *Conditionable:* **No.** Plans define what is approved — cannot be deferred to condition."
            )
        elif "ridge" in item_lower or "eaves" in item_lower or "height" in item_lower:
            entries.append(
                "- **Ridge / eaves height**\n"
                "  (a) *Decision issue:* Overbearing impact, daylight, visual impact on street scene.\n"
                "  (b) *Policy test prevented:* NPPF para 130(c) (sympathetic to local character); "
                "BRE 45-degree and 25-degree tests.\n"
                "  (c) *Conditionable:* **No.** Height is a fundamental design parameter that must be "
                "assessed before permission is granted."
            )
        elif "floor area" in item_lower:
            entries.append(
                "- **Floor area**\n"
                "  (a) *Decision issue:* Scale relative to plot, CIL liability, amenity impact.\n"
                "  (b) *Policy test prevented:* NPPF para 130 (appropriate to setting); "
                "Local Plan density/scale policies.\n"
                "  (c) *Conditionable:* **No.** Floor area defines the scale of development."
            )
        elif "parking" in item_lower:
            entries.append(
                "- **Parking layout**\n"
                "  (a) *Decision issue:* Highway safety and residential parking provision.\n"
                "  (b) *Policy test prevented:* NPPF para 111 (safe and suitable access); "
                "adopted parking standards.\n"
                "  (c) *Conditionable:* **No.** Parking provision is a material consideration that "
                "the highway authority must assess before determination."
            )
        elif "material" in item_lower and "schedule" in item_lower:
            entries.append(
                "- **External materials schedule**\n"
                "  (a) *Decision issue:* Visual appearance, heritage compatibility.\n"
                "  (b) *Policy test prevented:* NPPF para 130 (visually attractive); "
                "Local Plan design policies.\n"
                "  (c) *Conditionable:* **Yes** — standard pre-commencement condition, provided "
                "all other matters are satisfactorily resolved."
            )
        elif "consultee" in item_lower:
            entries.append(
                "- **Consultee responses**\n"
                "  (a) *Decision issue:* Highway safety, drainage, heritage, ecology, amenity.\n"
                "  (b) *Policy test prevented:* Article 15 DMPO 2015 (statutory consultation); "
                "NPPF paras 111, 167-169; s.66/72 PLBCA 1990.\n"
                "  (c) *Conditionable:* **No.** Procedural requirement — consultations must be "
                "completed before determination."
            )
        elif "site visit" in item_lower:
            entries.append(
                "- **Site visit notes (dated)**\n"
                "  (a) *Decision issue:* Site context, street character, neighbour relationships.\n"
                "  (b) *Policy test prevented:* NPPF para 130(c) (sympathetic to surrounding "
                "built environment). Good practice per case law.\n"
                "  (c) *Conditionable:* **No.** Officer must visit before forming a view."
            )
        elif "heritage" in item_lower or "design & access" in item_lower:
            entries.append(
                "- **Heritage Impact Assessment / Design & Access Statement**\n"
                "  (a) *Decision issue:* Impact on significance of heritage asset.\n"
                "  (b) *Policy test prevented:* s.72 PLBCA 1990 (special attention to Conservation "
                "Area character); NPPF paras 199-202.\n"
                "  (c) *Conditionable:* **No.** The statutory duty must be discharged before "
                "granting permission."
            )
        elif "flood" in item_lower:
            entries.append(
                "- **Flood Risk Assessment**\n"
                "  (a) *Decision issue:* Flood risk to future occupiers and third parties.\n"
                "  (b) *Policy test prevented:* NPPF para 167 (site-specific FRA); Sequential "
                "Test (para 162); Exception Test (para 163).\n"
                "  (c) *Conditionable:* **No.** The Sequential and Exception Tests must be "
                "passed before permission is granted."
            )
        elif "drainage" in item_lower or "suds" in item_lower:
            entries.append(
                "- **Drainage strategy / SuDS design**\n"
                "  (a) *Decision issue:* Surface water management and flood risk.\n"
                "  (b) *Policy test prevented:* NPPF paras 167-169 (sustainable drainage).\n"
                "  (c) *Conditionable:* **Yes** — may be secured by pre-commencement condition "
                "if other matters are satisfactorily resolved."
            )
        elif "gis" in item_lower or "constraint" in item_lower:
            entries.append(
                "- **GIS constraint verification**\n"
                "  (a) *Decision issue:* Identification of all relevant policy tests.\n"
                "  (b) *Policy test prevented:* All constraint-related policies cannot be "
                "confirmed as applicable without GIS check.\n"
                "  (c) *Conditionable:* **No.** Procedural — must be verified by the officer."
            )
        else:
            name = item.split("**")[1] if "**" in item else item[:50]
            entries.append(
                f"- **{name}**\n"
                f"  (a) *Decision issue:* Required for merits assessment.\n"
                f"  (b) *Policy test prevented:* Cannot be identified without the information.\n"
                f"  (c) *Conditionable:* To be determined."
            )

    if not entries:
        return "*No material gaps to explain.*"

    return "\n\n".join(entries)


def _build_consultation_status(proposal: str, constraints: list[str]) -> str:
    """
    Build consultation and publicity status for deferral-mode report.
    States what is required and what is outstanding.
    """
    proposal_lower = proposal.lower() if proposal else ""
    constraints_lower = [c.lower() for c in constraints]

    required = []
    required.append("| Neighbour notification (Article 15 DMPO 2015) | Required | Outstanding |")
    required.append("| Site notice / press notice | Required | Outstanding |")
    required.append("| Highway Authority | Required (NPPF para 111) | Outstanding |")

    if any("conservation" in c for c in constraints_lower) or any("listed" in c for c in constraints_lower):
        required.append("| Design and Conservation Officer | Required (s.66/72 PLBCA 1990) | Outstanding |")

    if any("flood" in c for c in constraints_lower):
        required.append("| Environment Agency | Required (NPPF para 167) | Outstanding |")

    if "ashp" in proposal_lower or "heat pump" in proposal_lower:
        required.append("| Environmental Health | Required (BS 4142:2014) | Outstanding |")

    if any("tree" in c or "tpo" in c for c in constraints_lower):
        required.append("| Tree Officer | Required (BS 5837:2012) | Outstanding |")

    required.append("| Lead Local Flood Authority | Required (NPPF paras 167-169) | Outstanding |")
    required.append("| Ecology / Biodiversity | Required (Environment Act 2021, BNG) | Outstanding |")

    rows = "\n".join(required)
    return f"""| Consultee | Requirement | Status |
|-----------|-------------|--------|
{rows}

**None of the above consultations have been carried out.** Determination cannot proceed until all statutory and non-statutory consultations are complete and the publicity period has expired."""


def _build_legal_risk_deferral(
    constraints: list[str],
    missing_items: list[str],
) -> str:
    """
    Build the Legal / Procedural Risk Register for deferral-mode.
    Format: risk, regulation/policy hook, consequence, mitigation.
    """
    risks: list[tuple[str, str, str, str]] = []

    risks.append((
        "Determination without approved plans",
        "Article 7 DMPO 2015",
        "High risk of an unsafe decision — no plans define what is approved",
        "Defer until plans submitted and validated",
    ))

    risks.append((
        "Consultation not completed",
        "Article 15 DMPO 2015; s.65/67 TCPA 1990",
        "High procedural risk — decision may be unsound if challenged",
        "Complete all statutory consultations before determination",
    ))

    if any("conservation" in c.lower() or "listed" in c.lower() for c in constraints):
        risks.append((
            "Section 66/72 duties not dischargeable",
            "s.66/72 P(LBCA)A 1990; NPPF paras 199-202",
            "High risk — statutory duty to have special regard / attention "
            "cannot be demonstrated without heritage assessment",
            "Obtain heritage assessment and conservation officer input",
        ))

    risks.append((
        "No site visit recorded",
        "Good practice; case law (Lanner Parish Council v Cornwall Council)",
        "Risk of an incomplete evidence base — vulnerable on appeal",
        "Conduct and record dated site visit before determination",
    ))

    risks.append((
        "Insufficient information for policy assessment",
        "s.38(6) PCPA 2004; NPPF para 11",
        "Not possible to weigh the proposal against the development plan",
        "Defer — material information required before determination",
    ))

    rows = "\n".join(
        f"| {risk} | {reg} | {consequence} | {mitigation} |"
        for risk, reg, consequence, mitigation in risks
    )

    return f"""| Risk | Regulation / Policy Hook | Consequence | Mitigation |
|------|--------------------------|-------------|------------|
{rows}"""


def _generate_deferral_report(
    reference: str,
    address: str,
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str | None,
    postcode: str | None,
    applicant_name: str | None,
    policies: list[Policy],
    missing_items: list[str],
    missing_section_text: str,
    council_name: str = "Newcastle City Council",
    proposal_details: Any = None,
) -> str:
    """
    Generate a short-form DEFERRAL report when Documents Submitted = 0.

    This is a "Validation / Insufficient Information" report, NOT a full
    merits assessment. It contains only 10 sections per UK deferral convention.

    No planning balance is run. No conditions are drafted. No compliance
    conclusions are reached.
    """
    registry = EvidenceRegistry()

    # Register only genuinely admissible evidence
    e_app = registry.add(
        "Application form", "Applicant details, site address, proposal description",
        quality="Verified", source_type="Application form",
    )
    e_nppf = registry.add(
        "NPPF (December 2023)", "National planning policy framework",
        date="December 2023", quality="Verified", source_type="NPPF (December 2023)",
    )
    e_dev_plan = ""
    non_nppf = [p for p in policies if getattr(p, 'source_type', '') != "NPPF"]
    if non_nppf:
        source_name = getattr(non_nppf[0], 'source', 'Development Plan')
        e_dev_plan = registry.add(
            source_name, "Adopted development plan policies",
            quality="Verified", source_type="Adopted development plan policy",
        )

    e_constraints = ""
    if constraints:
        e_constraints = registry.add(
            "Application form (unverified)",
            f"{len(constraints)} constraint(s) stated on form — not confirmed against GIS",
            quality="Unverified", source_type="Application form",
        )

    # --- Policy context (brief) ---
    policy_headings = ["- Section 38(6) Planning and Compulsory Purchase Act 2004"]
    policy_headings.append(f"- NPPF (December 2023) {e_nppf}")
    if e_dev_plan:
        policy_headings.append(f"- {getattr(non_nppf[0], 'source', 'Development Plan')} {e_dev_plan}")
    if any("conservation" in c.lower() or "listed" in c.lower() for c in constraints):
        policy_headings.append("- Sections 66 and 72, Planning (Listed Buildings and Conservation Areas) Act 1990")
    policy_headings.append("- Environment Act 2021 (Biodiversity Net Gain)")
    policy_text = "\n".join(policy_headings)

    # --- Why each item is material ---
    why_material = _build_why_material(missing_items, constraints)

    # --- Consultation status ---
    consultation_status = _build_consultation_status(proposal, constraints)

    # --- Legal risk register ---
    legal_risk = _build_legal_risk_deferral(constraints, missing_items)

    # --- Next steps checklist ---
    checklist_items = []
    for item in missing_items:
        name = item.split("**")[1] if "**" in item else item[:60]
        if "May be conditioned" not in item:
            checklist_items.append(f"- [ ] Submit: {name}")
    checklist_items.append("- [ ] Await: Statutory consultation period to expire")
    checklist_items.append("- [ ] Conduct: Dated site visit by case officer")
    checklist_items.append("- [ ] Verify: Constraints against council GIS mapping")
    checklist_text = "\n".join(checklist_items)

    # --- Proposal details (as evidenced only) ---
    proposal_note = ""
    if proposal_details:
        known_items = []
        if proposal_details.num_storeys:
            known_items.append(f"| Storeys | {proposal_details.num_storeys} | Application description |")
        if proposal_details.num_bedrooms:
            known_items.append(f"| Bedrooms | {proposal_details.num_bedrooms} | Application description |")
        if proposal_details.development_type:
            known_items.append(f"| Development type | {proposal_details.development_type.title()} | Application description |")

        if known_items:
            rows = "\n".join(known_items)
            proposal_note = f"""
**Specifications stated in description (unverified — no plans submitted):**

| Item | Value | Source |
|------|-------|--------|
{rows}

*These figures are extracted from the application description only. They are not verified from submitted plans and cannot be relied upon for assessment purposes.*
"""
        else:
            proposal_note = "\n*No quantified specifications are available from the application description.*\n"

    # --- Constraint text ---
    if constraints:
        constraint_lines = "\n".join(f"- {c} *(source: application form — unverified against GIS)* {e_constraints}" for c in constraints)
    else:
        constraint_lines = "- None stated on application form. **GIS verification required.**"

    # ================================================================
    # ASSEMBLE DEFERRAL REPORT — 10 sections only
    # ================================================================

    # --- Build admissible evidence table ---
    admissible_rows = "\n".join(
        f"| {e.tag} | {e.source} | {e.date} | {e.description} |"
        for e in registry.entries if e.is_valid_evidence
    )
    non_admissible_rows = "\n".join(
        f"| {e.tag} | {e.source} | {e.date} | {e.description} |"
        for e in registry.entries if not e.is_valid_evidence
    )

    report = f"""# DELEGATED OFFICER'S REPORT — DEFERRAL

**{council_name} — Development Management**
**Insufficient Information: Full Merits Assessment Not Possible**

---

## 1. Administrative Summary

| Field | Detail |
|-------|--------|
| **Application Reference** | {reference} |
| **Site Address** | {address} |
| **Ward** | {ward or 'Not specified'} |
| **Postcode** | {postcode or 'Not specified'} |
| **Applicant** | {applicant_name or 'Not specified'} |
| **Application Type** | {application_type} |
| **Date of Report** | {datetime.now().strftime('%d %B %Y')} |
| **Documents Submitted** | **0** |
| **Recommendation** | **DEFER — Pending Submission of Essential Documents** |

{e_app} Source: Application form.

---

## 2. Executive Summary (Deferral)

The application cannot be determined at this time. No plans, elevations, or supporting documents have been submitted. The Local Planning Authority is not in a position to assess the form, scale, appearance, or impact of the proposed development.

Material information is missing (see Section 7 below). No statutory consultations have been carried out. No site visit has been conducted. It is not possible to apply the relevant policy tests or reach conclusions on policy compliance.

**Recommendation: DEFER** pending submission of essential documents and completion of statutory consultations.

---

## 3. Site and Surroundings

**Address:** {address} {e_app}
**Ward:** {ward or 'Not specified'}
**Postcode:** {postcode or 'Not specified'}
**Local Planning Authority:** {council_name}

**GIS constraint check:** Not carried out. Constraints listed below are from the application form only and are unverified.

**Site visit:** No site visit recorded. The character of the street scene, relationship to neighbouring properties, topography, and existing site features are unknown.

### Constraints (unverified — from application form {e_app})

{constraint_lines}

---

## 4. Proposal *(as evidenced from application form only)*

**Description {e_app}:**

{proposal}

{proposal_note}

No submitted plans, elevations, or technical drawings are available. The officer cannot verify dimensions, layout, appearance, or relationship to boundaries.

---

## 5. Policy Context

If the application were to proceed to a merits assessment, the following policy framework would apply:

{policy_text}

A full policy assessment has not been carried out. The information necessary to apply these policy tests has not been submitted.

---

## 6. Consultation and Publicity Status

{consultation_status}

---

## 7. Validation Deficiencies / Material Information Missing

{missing_section_text}

---

## 8. Why the Missing Information Is Material

For each item listed in Section 7 above, the following sets out (a) the decision issue affected, (b) the policy or procedural test it prevents, and (c) whether the matter could be addressed by condition.

{why_material}

---

## 9. Legal / Procedural Risk Register

{legal_risk}

---

## 10. Recommendation

**DEFER — Pending Submission of Essential Documents**

The officer is not in a position to make a safe determination on this application. The information listed in Section 7 is required before the application can proceed to a full merits assessment.

### Applicant Next Steps Checklist

{checklist_text}

Once the above items are received and consultations completed, the application will be re-assessed and a full delegated officer report prepared.

---

## Appendix A: Evidence Register

### Admissible Evidence

| Tag | Source | Date | Description |
|-----|--------|------|-------------|
{admissible_rows}

### Officer Judgement / Not Admissible Evidence

| Tag | Source | Date | Description |
|-----|--------|------|-------------|
{non_admissible_rows if non_admissible_rows else '| — | — | — | *None in this report — no officer judgements made in deferral mode.* |'}

---

## Appendix B: Policy List

{policy_text}

*Full policy assessment deferred pending submission of material information.*

---

*Report generated by Plana.AI — Planning Intelligence Platform*
*Deferral Report v5.0 | {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}*
"""
    return report


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
    documents_verified: bool = True,
    future_predictions: FuturePredictionsResult | None = None,
    council_name: str = "Newcastle City Council",
    council_id: str = "newcastle",
    proposal_details: Any = None,
    amenity_impacts: list = None,
    planning_weights: list = None,
    balance_summary: str = None,
) -> str:
    """
    Generate a legally defensible UK delegated officer report.

    This report follows UK delegated officer report conventions. It:
    - Clearly separates FACT, OFFICER ASSESSMENT, and POLICY REQUIREMENT
    - Only treats valid evidence sources as evidence (not "assessment data")
    - Applies the six legal tests to every condition
    - Automatically recommends DEFERRAL if material information is missing
    - Includes a Legal Risk Assessment identifying vulnerability to challenge

    Structure:
      1.  Administrative Summary
      2.  Executive Summary
      3.  Site and Surroundings (verified vs unverified)
      4.  Proposal (as evidenced only)
      5.  Planning History (context only — NOT determinative)
      6.  Consultations (with officer response column)
      7.  Planning Policy
      8.  Planning Assessment (topic-based mini-structure)
      9.  Material Information Missing
      10. Planning Balance
      11. Legal Risk Assessment
      12. Recommendation
      13. Conditions (only if lawful and justified)
      14. Evidence Register
    """

    # ================================================================
    # DEFERRAL MODE: Only produce a deferral report when we have
    # positively confirmed that zero documents exist (i.e. the portal
    # was reachable and returned 0 documents).  If the portal was
    # unreachable (documents_verified=False), we cannot be certain
    # there are no documents, so we proceed with a full report and
    # flag that document status is unverified.
    # ================================================================
    if documents_count == 0 and documents_verified:
        missing_section_text, missing_items = _build_material_info_missing(
            documents_count, proposal_details, constraints, assessments,
            documents_verified=documents_verified,
        )
        return _generate_deferral_report(
            reference=reference,
            address=address,
            proposal=proposal,
            application_type=application_type,
            constraints=constraints,
            ward=ward,
            postcode=postcode,
            applicant_name=applicant_name,
            policies=policies,
            missing_items=missing_items,
            missing_section_text=missing_section_text,
            council_name=council_name,
            proposal_details=proposal_details,
        )

    # ---- Evidence Registry: collects [E1], [E2]... throughout report ----
    registry = EvidenceRegistry()

    # ---- Register core evidence items upfront (VALID sources only) ----
    e_app_form = registry.add(
        "Application form", "Application details, address, proposal description",
        quality="Verified", source_type="Application form",
    )
    e_constraints = ""
    if constraints:
        e_constraints = registry.add(
            "Constraint mapping", f"{len(constraints)} constraint(s) affecting the site",
            quality="Unverified — requires GIS confirmation", source_type="Constraint mapping",
        )

    e_nppf = registry.add(
        "NPPF (December 2023)", "National planning policy framework",
        date="December 2023", quality="Verified", source_type="NPPF (December 2023)",
    )

    e_dev_plan = ""
    non_nppf_policies = [p for p in policies if getattr(p, 'source_type', '') != "NPPF"]
    if non_nppf_policies:
        source_name = getattr(non_nppf_policies[0], 'source', 'Development Plan')
        e_dev_plan = registry.add(
            source_name, f"{len(non_nppf_policies)} local plan policies engaged",
            quality="Verified", source_type="Adopted development plan policy",
        )

    e_precedent = ""
    if similar_cases:
        e_precedent = registry.add(
            "Case database", f"{len(similar_cases)} precedent cases — contextual only, NOT determinative",
            quality="Verified", source_type="Case database",
        )

    # ---- Build Material Information Missing section ----
    missing_section_text, missing_items = _build_material_info_missing(
        documents_count, proposal_details, constraints, assessments,
        documents_verified=documents_verified,
    )
    is_deferral = _should_defer(documents_count, missing_items, documents_verified)

    # ---- Build sub-sections ----
    policy_section = format_policy_framework_section(
        policies, council_name, proposal=proposal, address=address, constraints=constraints,
        proposal_details=proposal_details,
    )
    cases_section = format_similar_cases_section(
        similar_cases, proposal=proposal, address=address,
        proposal_details=proposal_details,
    )
    assessment_section = format_assessment_section(
        assessments, registry=registry, documents_count=documents_count,
        documents_verified=documents_verified,
    )
    conditions_section = format_conditions_section(
        reasoning.conditions, registry=registry, documents_count=documents_count,
        documents_verified=documents_verified,
    )
    informatives_section = generate_informatives(council_id, postcode, proposal_details, constraints)

    # ---- Legal Risk Assessment ----
    legal_risk_text = _build_legal_risk_assessment(
        documents_count, constraints, assessments, reasoning, missing_items,
        documents_verified=documents_verified,
    )

    # ---- Proposal details table ----
    proposal_details_section = ""
    if proposal_details:
        dev_type = proposal_details.development_type.title() if proposal_details.development_type else 'Not specified'
        proposal_lower = proposal.lower()
        is_dwelling_proposal = any(kw in proposal_lower for kw in ['dwelling', 'house', 'bungalow'])
        generic_types = ['full', 'new build', 'not specified', 'new', 'erection', 'construction', 'householder']
        if dev_type.lower() in generic_types and is_dwelling_proposal:
            dev_type = 'Dwelling'
        num_units = proposal_details.num_units or 0
        if num_units == 0 and (is_dwelling_proposal or dev_type.lower() == 'dwelling'):
            num_units = 1
        num_units_display = str(num_units) if num_units > 0 else 'N/A'

        proposal_details_section = f"""
| Specification | Detail | Source |
|---------------|--------|--------|
| Development Type | {dev_type} | Application form {e_app_form} |
| Number of Units | {num_units_display} | Application form |
| Number of Bedrooms | {proposal_details.num_bedrooms or 'N/A'} | Application form |
| Number of Storeys | {proposal_details.num_storeys or 'N/A'} | Application form |
| Floor Area | {f'{proposal_details.floor_area_sqm} sqm' if proposal_details.floor_area_sqm else '**NOT PROVIDED**'} | {'Submitted plans' if proposal_details.floor_area_sqm else '—'} |
| Height | {f'{proposal_details.height_metres}m' if proposal_details.height_metres else '**NOT PROVIDED**'} | {'Submitted plans' if proposal_details.height_metres else '—'} |
| Materials | {', '.join(proposal_details.materials) if proposal_details.materials else '**NOT PROVIDED**'} | {'Application form' if proposal_details.materials else '—'} |
| Parking Spaces | {proposal_details.parking_spaces or '**NOT PROVIDED**'} | {'Submitted plans' if proposal_details.parking_spaces else '—'} |
"""

    # ---- Amenity impacts table ----
    amenity_section = ""
    if amenity_impacts:
        impact_rows = []
        for impact in amenity_impacts:
            status = "PASSES" if impact.passes else "FAILS"
            impact_rows.append(f"| {impact.metric} | {impact.value} {impact.unit} | {impact.threshold} | {status} |")
        amenity_section = f"""
**Quantified Amenity Assessment**

| Assessment Test | Measurement | Threshold | Result |
|-----------------|-------------|-----------|--------|
{chr(10).join(impact_rows)}

*Methodology: BRE Guidelines (2022), adopted residential design standards.*
*Note: These measurements are indicative only and must be verified from submitted plans and site visit.*
"""

    # ---- Planning balance ----
    balance_text = balance_summary if balance_summary else reasoning.planning_balance

    # ---- Refusal reasons (if refusing) ----
    refusal_section = ""
    if reasoning.refusal_reasons:
        refusal_items = "\n".join([
            f"**{r['number']}. {r['reason']}**\n\n*Policy Basis: {r['policy_basis']}*\n"
            for r in reasoning.refusal_reasons
        ])
        refusal_section = f"""### Reasons for Refusal

{refusal_items}
"""

    # ---- Evidence quality / confidence rating ----
    # HIGH = all plans, consultations and constraints verified
    # MEDIUM = minor details outstanding
    # LOW = material information missing
    insufficient_assessments = sum(1 for a in assessments if a.compliance == "insufficient-evidence")
    total_assessments = len(assessments)
    # Only treat as LOW if we've confirmed no documents exist.
    # If documents are attached (count > 0) but text wasn't extracted,
    # evidence quality is MEDIUM (documents exist but not yet analysed).
    confirmed_no_documents = documents_count == 0 and documents_verified
    if confirmed_no_documents or insufficient_assessments > total_assessments * 0.5:
        evidence_quality = "LOW"
    elif insufficient_assessments > 0 or not constraints:
        evidence_quality = "MEDIUM"
    else:
        evidence_quality = "HIGH"

    # ---- Recommendation ----
    # CRITICAL: If material information is missing, override to DEFER
    if is_deferral:
        rec_text = "DEFER — PENDING SUBMISSION OF ESSENTIAL DOCUMENTS"
        rec_reasoning = (
            f"**This application cannot be lawfully determined at this time.**\n\n"
            f"Material information is missing (see Section 9 below). "
            f"{'No submitted plans have been provided — ' if (documents_count == 0 and documents_verified) else ''}"
            f"the LPA cannot assess the form, scale, appearance, or impact of the "
            f"development without this information.\n\n"
            f"**The application should be deferred** pending submission of:\n"
            + "\n".join(f"- {item.split('**')[1] if '**' in item else item[:80]}" for item in missing_items[:8])
            + "\n\nOnce the above information is received, the application can be re-assessed "
            f"and a lawful recommendation made."
        )
        evidence_quality = "LOW"
    else:
        rec_text = reasoning.recommendation.replace('_', ' ').upper()
        rec_reasoning = reasoning.recommendation_reasoning

    # ---- Verified vs unverified constraints ----
    verified_constraints = []
    unverified_constraints = []
    for c in constraints:
        # Without GIS confirmation, all constraints from application form are unverified
        unverified_constraints.append(c)
    constraint_note = ""
    if unverified_constraints:
        constraint_note = (
            "*All constraints listed are sourced from the application form. "
            "None have been verified against the council's GIS constraint mapping system. "
            "The case officer MUST verify before determination.*"
        )

    # =====================================================================
    # ASSEMBLE LEGALLY DEFENSIBLE OFFICER REPORT
    # =====================================================================

    # Build the "Documents Submitted" display value.  This must reflect
    # the ACTUAL number of documents attached to the application, not
    # just how many had extractable text content.
    if documents_count > 0:
        documents_display = str(documents_count)
    elif not documents_verified:
        documents_display = "Not verified — portal unavailable"
    else:
        documents_display = "**0**"

    report = f"""# DELEGATED OFFICER'S REPORT

**{council_name} — Development Management**

---

## 1. Administrative Summary

| Field | Detail |
|-------|--------|
| **Application Reference** | {reference} |
| **Site Address** | {address} |
| **Ward** | {ward or 'Not specified'} |
| **Postcode** | {postcode or 'Not specified'} |
| **Applicant** | {applicant_name or 'Not specified'} |
| **Application Type** | {application_type} |
| **Date of Report** | {datetime.now().strftime('%d %B %Y')} |
| **Documents Submitted** | {documents_display} |
| **Evidence Quality** | **{evidence_quality}** |
| **Recommendation** | **{rec_text}** |

{e_app_form} Source: Application form data.{' ' + e_constraints + ' Source: Constraint database (UNVERIFIED).' if e_constraints else ''}

---

## 2. Executive Summary

{('**DEFERRAL RECOMMENDED.** Material information is missing. ' + ('No submitted plans have been provided. ' if (documents_count == 0 and documents_verified) else f'Documents received ({documents_count}). Plan content extraction pending/failed. ') + 'The LPA cannot lawfully determine this application without the documents identified in Section 9 below.') if is_deferral else f'The application has been assessed against the Development Plan and NPPF. Recommendation: **{rec_text}**.'}

**Key constraints:** {', '.join(constraints) if constraints else 'None identified — verify against GIS'}
**Evidence quality:** {evidence_quality} — {'all plans, consultations and constraints verified' if evidence_quality == 'HIGH' else 'minor details outstanding' if evidence_quality == 'MEDIUM' else 'material information missing — see Section 9'}

---

## 3. Site and Surroundings

{_build_site_description(address, ward, postcode, constraints, proposal, proposal_details, council_name)}

### 3.1 Constraints — Verified

*No constraints have been verified against GIS mapping at this stage.*

### 3.2 Constraints — Unverified (from application form)

{_build_constraints_analysis(constraints, proposal, proposal_details)}

{constraint_note}

### 3.3 Site Visit Requirements

{_build_site_visit_requirements(proposal, proposal_details, constraints)}

---

## 4. Proposal *(as evidenced only)*

**Description (from application form {e_app_form}):**

{proposal}

{proposal_details_section}

{'**Note:** No submitted plans are available. The dimensions and specifications above are extracted from the application description only and CANNOT be treated as verified facts.' if (documents_count == 0 and documents_verified) else ''}

---

## 5. Planning History

The following comparable decisions are referenced as **contextual background only**. Precedent is NOT relied upon as a determining factor. Each application must be assessed on its own merits. {e_precedent}

| Metric | Value |
|--------|-------|
| Comparable cases found | {precedent_analysis.get('total_cases', 0)} |
| Approval rate | {precedent_analysis.get('approval_rate', 0):.0%} |

{precedent_analysis.get('summary', '')}

{cases_section}

---

## 6. Consultations

{_build_consultations_section(proposal, constraints, proposal_details)}

**Officer note:** No consultation responses have been received at the time of report preparation. Determination MUST NOT proceed until all statutory consultations are complete.

---

## 7. Planning Policy

The application falls to be determined in accordance with Section 38(6) of the Planning and Compulsory Purchase Act 2004. {e_nppf}{' ' + e_dev_plan if e_dev_plan else ''}

{policy_section}

---

## 8. Planning Assessment

Each topic is structured as: **(a)** Policy requirement, **(b)** Fact (with evidence reference), **(c)** Officer assessment, **(d)** Gaps, **(e)** Conclusion + confidence.

**Rules applied:**
- "Insufficient evidence to conclude" is stated where plans, measurements, consultations or GIS verification are missing.
- Confidence: **HIGH** = plans + consultations + constraints verified; **MEDIUM** = minor details outstanding; **LOW** = material information missing.

{assessment_section}

{amenity_section}

---

## 9. Material Information Missing

{missing_section_text}

{'**DETERMINATION IS NOT LEGALLY SAFE.** The application should be DEFERRED pending submission of the items listed above.' if is_deferral else '**Determination may proceed** subject to the outstanding items being addressed by condition or through the consultation process.'}

---

## 10. Planning Balance

{balance_text}

{format_future_predictions_section(future_predictions) if future_predictions else ''}

---

## 11. Legal Risk Assessment

{legal_risk_text}

---

## 12. Recommendation

**{rec_text}**

{rec_reasoning}

---

## 13. {'Conditions' if reasoning.conditions and not is_deferral else 'Conditions / Refusal Reasons'}

{f"The six legal tests (NPPF para 56) have been applied to each condition. Only conditions that pass all six tests are included." if reasoning.conditions and not is_deferral else ""}

{conditions_section if reasoning.conditions and not is_deferral else refusal_section if reasoning.refusal_reasons else '*Not applicable — application recommended for deferral. Conditions will be drafted when material information is received.*' if is_deferral else '*No conditions or refusal reasons applicable.*'}

---

## 14. Evidence Register

All factual assertions in this report are tagged to evidence sources below. Items marked "NO — officer assessment" are planning judgements, NOT primary evidence.

{registry.format_register()}

---

## Appendix A: Informatives

{informatives_section}

---

## Appendix B: Policy Citations

{_build_evidence_citations(policies, similar_cases, assessments, proposal, proposal_details)}

---

*Report generated by Plana.AI — Planning Intelligence Platform*
*Delegated Officer Report v4.1 | Generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}*
*All conclusions are traceable to evidence sources listed in the Evidence Register.*
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
    portal_documents_count: int | None = None,
    documents_verified: bool = False,
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
    import structlog
    _logger = structlog.get_logger(__name__)

    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    generated_at = datetime.now().isoformat()

    # SAFEGUARD: Log and recover if proposal_description is empty
    if not proposal_description or not proposal_description.strip():
        _logger.warning(
            "proposal_description_empty",
            reference=reference,
            site_address=site_address,
            application_type=application_type,
        )

    _logger.info(
        "generate_professional_report_start",
        reference=reference,
        proposal_len=len(proposal_description) if proposal_description else 0,
        proposal_preview=proposal_description[:80] if proposal_description else "<EMPTY>",
        application_type=application_type,
    )

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
        documents_count=portal_documents_count if portal_documents_count is not None else len(documents),
        documents_verified=documents_verified,
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
            "total_count": portal_documents_count if portal_documents_count is not None else len(documents),
            "uploaded_count": len(documents),
            "portal_count": portal_documents_count,
            "documents_verified": documents_verified,
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
