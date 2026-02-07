"""
Report templates and section definitions.

Defines the structure of case officer-style planning reports.
"""

from dataclasses import dataclass, field
from enum import Enum


class ReportSectionType(str, Enum):
    """Types of report sections."""

    SITE_DESCRIPTION = "site_description"
    PROPOSAL = "proposal"
    PLANNING_HISTORY = "planning_history"
    POLICY_CONTEXT = "policy_context"
    CONSULTATION = "consultation"
    ASSESSMENT = "assessment"
    DESIGN = "design"
    HERITAGE = "heritage"
    AMENITY = "amenity"
    TRANSPORT = "transport"
    ENVIRONMENT = "environment"
    OTHER_MATTERS = "other_matters"
    PLANNING_BALANCE = "planning_balance"
    RECOMMENDATION = "recommendation"
    CONDITIONS = "conditions"


@dataclass
class SectionTemplate:
    """Template for a report section."""

    section_type: ReportSectionType
    title: str
    prompt_template: str
    order: int
    required: bool = True
    depends_on: list[ReportSectionType] = field(default_factory=list)


@dataclass
class ReportTemplate:
    """Complete report template with all sections."""

    template_id: str
    version: str
    name: str
    description: str
    sections: list[SectionTemplate]

    @classmethod
    def case_officer_standard(cls) -> "ReportTemplate":
        """Get the standard case officer report template."""
        return cls(
            template_id="case_officer_standard",
            version="1.0.0",
            name="Case Officer Report",
            description="Standard case officer delegated report format",
            sections=[
                SectionTemplate(
                    section_type=ReportSectionType.SITE_DESCRIPTION,
                    title="Site and Surroundings",
                    order=1,
                    prompt_template="""Describe the application site and its surroundings based on the available information.

Include:
- Site location and address
- Existing use and buildings
- Character of surrounding area
- Relevant site constraints (conservation area, listed buildings, flood zone, etc.)

Application details:
{application_summary}

Site constraints:
{constraints}

Keep the description factual and relevant to planning considerations.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.PROPOSAL,
                    title="The Proposal",
                    order=2,
                    prompt_template="""Describe the proposed development based on the application details and submitted documents.

Include:
- Nature and scale of the development
- Key design features
- Any relevant phasing or conditions sought

Application proposal:
{proposal}

Document summaries:
{document_summaries}

Be specific about what is proposed, using information from the submitted documents where available.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.PLANNING_HISTORY,
                    title="Planning History",
                    order=3,
                    prompt_template="""Summarize relevant planning history for the site and any similar nearby applications.

Previous applications:
{planning_history}

Similar cases:
{similar_cases}

Highlight any applications that are particularly relevant to the current proposal and their outcomes.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.POLICY_CONTEXT,
                    title="Policy Context",
                    order=4,
                    prompt_template="""Set out the relevant planning policy framework for assessing this application.

Include:
- Relevant NPPF chapters and paragraphs
- Relevant Local Plan policies
- Any relevant supplementary planning documents

Relevant policies:
{policies}

Summarize the key policy requirements that apply to this development.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.CONSULTATION,
                    title="Consultation Responses",
                    order=5,
                    required=False,
                    prompt_template="""Summarize consultation responses received.

Include:
- Statutory consultee responses
- Internal consultee comments
- Public representations (summary of key issues raised)

Consultation information:
{consultation}

Where no specific information is available, note that consultation responses are awaited or not yet available.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.ASSESSMENT,
                    title="Assessment",
                    order=6,
                    prompt_template="""Introduce the main planning issues to be assessed for this application.

Based on the proposal and policy context, identify the key planning issues:

Application summary:
{application_summary}

Key policies:
{policies}

List the main assessment topics that will be covered in the following sections.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.DESIGN,
                    title="Design and Visual Impact",
                    order=7,
                    prompt_template="""Assess the design quality and visual impact of the proposal.

Consider:
- Scale, form, and massing
- Materials and architectural detailing
- Relationship to surrounding buildings and streetscape
- Quality of public realm (where relevant)

Proposal details:
{proposal}

Relevant policies (design):
{design_policies}

Design documents:
{design_documents}

Assess against relevant design policies and guidance.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.HERITAGE,
                    title="Heritage Impact",
                    order=8,
                    required=False,  # Only if heritage constraints
                    prompt_template="""Assess the impact on heritage assets.

Consider:
- Impact on listed buildings (if applicable)
- Impact on conservation area character (if applicable)
- Archaeological implications
- Significance of affected heritage assets
- Justification for any harm identified

Heritage constraints:
{heritage_constraints}

Relevant policies (heritage):
{heritage_policies}

Heritage documents:
{heritage_documents}

Apply the statutory tests and NPPF framework for heritage assessment.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.AMENITY,
                    title="Residential Amenity",
                    order=9,
                    required=True,  # Amenity assessment is essential for all residential/householder applications
                    prompt_template="""Assess the impact on residential amenity.

Consider:
- Privacy and overlooking (21m separation between habitable room windows)
- Daylight and sunlight (45-degree rule from BRE Guidelines)
- Noise and disturbance during construction and occupation
- Outlook and sense of enclosure (25-degree overbearing test)
- Living conditions for future occupiers (garden size, internal space standards)

Proposal details:
{proposal}

Relevant policies (amenity):
{amenity_policies}

Assess impacts on both existing and future residents. Reference specific measurements and tests where applicable.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.TRANSPORT,
                    title="Highways and Access",
                    order=10,
                    prompt_template="""Assess highways and access implications.

Consider:
- Highway safety and visibility splays
- Parking provision against adopted standards
- Cycle parking and sustainable transport modes
- Impact on local highway network capacity
- Servicing and deliveries

Apply the NPPF paragraph 111 test: development should only be prevented or refused on highways grounds if there would be an unacceptable impact on highway safety, or the residual cumulative impacts on the road network would be severe.

Proposal details:
{proposal}

Transport documents:
{transport_documents}

Relevant policies (transport):
{transport_policies}

Assess against NPPF Chapter 9 (Promoting sustainable transport) and local highways policies.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.ENVIRONMENT,
                    title="Environmental Considerations",
                    order=11,
                    required=False,
                    prompt_template="""Assess environmental considerations where relevant.

Consider:
- Ecology and biodiversity
- Trees and landscaping
- Flood risk and drainage
- Contaminated land
- Air quality and noise

Environmental constraints:
{environmental_constraints}

Environmental documents:
{environmental_documents}

Relevant policies (environment):
{environmental_policies}

Address relevant environmental matters based on site constraints and proposal type.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.OTHER_MATTERS,
                    title="Other Material Considerations",
                    order=12,
                    required=False,
                    prompt_template="""Address any other material planning considerations.

This may include:
- Community Infrastructure Levy
- Planning obligations (S106)
- Climate change and sustainability
- Any other site-specific matters

Application details:
{application_summary}

Address any remaining material considerations not covered in previous sections.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.PLANNING_BALANCE,
                    title="Planning Balance",
                    order=13,
                    prompt_template="""Weigh up the planning considerations and reach a balanced conclusion.

Previous assessment sections:
{previous_sections}

Key benefits:
- [List benefits identified]

Key concerns:
- [List any adverse impacts or policy conflicts]

Apply the relevant planning balance test based on the policy framework:
- For heritage harm: apply NPPF paragraph 199-202 balance
- For other cases: consider accordance with development plan as a whole

Reach a reasoned conclusion on the overall planning balance.""",
                    depends_on=[
                        ReportSectionType.DESIGN,
                        ReportSectionType.AMENITY,
                    ],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.RECOMMENDATION,
                    title="Recommendation",
                    order=14,
                    prompt_template="""Provide the planning recommendation.

Based on the assessment:
{planning_balance}

State clearly:
1. Whether the application should be APPROVED or REFUSED
2. The main reasons for the recommendation
3. Reference to key policies that support the decision

If recommending approval, note that conditions should be attached.
If recommending refusal, state the proposed refusal reasons clearly.""",
                    depends_on=[ReportSectionType.PLANNING_BALANCE],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.CONDITIONS,
                    title="Recommended Conditions",
                    order=15,
                    required=False,  # Only if recommending approval
                    prompt_template="""List recommended planning conditions.

For an approval, include:
1. Standard time limit condition
2. Approved plans condition
3. Any pre-commencement conditions with justification
4. Other conditions addressing identified impacts

Application type: {application_type}
Key issues to address: {key_issues}

Conditions should:
- Be necessary
- Be relevant to planning
- Be relevant to the development
- Be enforceable
- Be precise
- Be reasonable

Provide condition wording and reason for each.""",
                    depends_on=[ReportSectionType.RECOMMENDATION],
                ),
            ],
        )
