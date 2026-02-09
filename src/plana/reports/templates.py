"""
Report templates and section definitions.

v2.0 - Evidence-based report structure with quantified assessments.

Defines the structure of case officer-style planning reports.
"""

from dataclasses import dataclass, field
from enum import Enum


class ReportSectionType(str, Enum):
    """Types of report sections."""

    DATA_QUALITY = "data_quality"  # v2.0 - Data quality indicator
    SPECIFICATIONS = "specifications"  # v2.0 - Extracted specifications
    SITE_DESCRIPTION = "site_description"
    PROPOSAL = "proposal"
    PLANNING_HISTORY = "planning_history"
    POLICY_CONTEXT = "policy_context"
    SIMILAR_CASES = "similar_cases"  # v2.0 - Separate similar cases section
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
        """Get the standard case officer report template - v2.0 evidence-based."""
        return cls(
            template_id="case_officer_standard",
            version="2.0.0",
            name="Case Officer Report",
            description="Evidence-based case officer delegated report format v2.0",
            sections=[
                SectionTemplate(
                    section_type=ReportSectionType.DATA_QUALITY,
                    title="Data Quality Indicator",
                    order=0,
                    prompt_template="""Generate a data quality summary table based on the extracted data.

{report_quality}

Format as a clear indicator of what evidence is available and what gaps exist.
This helps the case officer understand the reliability of the assessment.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.SPECIFICATIONS,
                    title="Proposal Specifications",
                    order=1,
                    prompt_template="""Present the extracted specifications from submitted documents in a table format.

## EXTRACTED SPECIFICATIONS

Based on analysis of submitted documents, the following specifications have been identified:

{application_summary}

For each specification, indicate:
- The value (with units where applicable)
- The source document
- The confidence level (Verified/Measured/Inferred/Not Found)

If specifications are missing, clearly state what information is required.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.SITE_DESCRIPTION,
                    title="Site and Surroundings",
                    order=2,
                    prompt_template="""Describe the application site and its surroundings based on the available information.

IMPORTANT: Only state what is EVIDENCED. Mark assumptions clearly.

Include with citations:
- Site location and address [VERIFIED from application form]
- Existing use and buildings [STATE SOURCE or mark as requiring site visit]
- Character of surrounding area [STATE SOURCE or mark as requiring verification]
- Relevant site constraints [LIST with source - council GIS, application form, or assumed]

Application details:
{application_summary}

Site constraints:
{constraints}

Evidence assessments:
{evidence_assessments}

DO NOT make generic statements about "pleasant residential area" without evidence.
If site character is unknown, state: "Site character requires verification by site visit."

Keep the description factual and cite sources for all factual claims.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.PROPOSAL,
                    title="The Proposal",
                    order=3,
                    prompt_template="""Describe the proposed development based on the application details and submitted documents.

IMPORTANT: Use EXTRACTED SPECIFICATIONS - do not use generic descriptions.

Include with specific measurements:
- Number of units/bedrooms (cite source document)
- Floor area in m² (cite source)
- Building height - ridge and eaves (cite elevation drawing reference)
- Number of storeys (cite source)
- Materials proposed (cite DAS or elevation annotations)
- Parking provision (cite site plan)

Application proposal:
{proposal}

Extracted specifications:
{application_summary}

Document summaries:
{document_summaries}

If any key specification is missing, state clearly:
"[SPECIFICATION] not specified in submitted documents - clarification required."

Be specific using actual measurements, not generic descriptions.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.PLANNING_HISTORY,
                    title="Planning History",
                    order=4,
                    prompt_template="""Summarize relevant planning history for the site.

## SITE HISTORY
[List any previous applications on this specific site with reference, proposal, and outcome]

Previous applications:
{planning_history}

If no site history: "No relevant planning history identified for this site."
""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.SIMILAR_CASES,
                    title="Similar Cases and Precedent Analysis",
                    order=5,
                    prompt_template="""Analyse similar cases to establish precedent context.

## PRECEDENT SUMMARY
Total comparable cases found: [X]
Approval rate: [Y]%
Precedent strength: [STRONG / MODERATE / WEAK]

## CASE COMPARISON MATRIX

| Factor | This Application | Case 1 | Case 2 | Case 3 |
|--------|-----------------|--------|--------|--------|
| Reference | [Current ref] | [Ref] | [Ref] | [Ref] |
| Development type | [Type] | [Type] | [Type] | [Type] |
| Site area (m²) | [Area or Unknown] | [Area] | [Area] | [Area] |
| Building height | [Height or Unknown] | [Height] | [Height] | [Height] |
| Constraints | [List] | [List] | [List] | [List] |
| Outcome | Pending | [Outcome] | [Outcome] | [Outcome] |
| Similarity score | - | [X]% | [Y]% | [Z]% |

## DETAILED CASE ANALYSIS

{similar_cases}

## PRECEDENT WEIGHT ASSESSMENT

For each case, assess:
- **STRONG**: Same street/estate, same development type, same constraints, recent decision (<3 years)
- **MODERATE**: Same ward, similar development type, comparable site
- **WEAK**: Different area, different scale, or old decision (>5 years)
- **DISTINGUISHABLE**: Key material difference means precedent doesn't apply

## PRECEDENT CONCLUSIONS

[Explain what the precedent cases indicate for this application]
[If mixed precedent, explain which is more relevant and why]
[If distinguishable, explain the key differences]

DO NOT use generic phrases like "shows acceptable approach" without explaining the specific relevance.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.POLICY_CONTEXT,
                    title="Policy Context",
                    order=6,
                    prompt_template="""Set out the relevant planning policy framework for assessing this application.

## POLICY FRAMEWORK

For each policy, quote the SPECIFIC TEST that applies to this development:

### National Planning Policy Framework (NPPF)

| Chapter | Paragraph | Key Test | Application to This Case |
|---------|-----------|----------|-------------------------|
| [Chapter] | [Para] | "[Quote the test]" | [How it applies] |

### Local Plan Policies

| Policy | Key Requirement | Relevance |
|--------|----------------|-----------|
| [Policy ref] | "[Quote the requirement]" | [Why relevant to this proposal] |

Relevant policies:
{policies}

For each policy cited, you MUST:
1. Quote the specific test/requirement (not just the policy title)
2. Explain why it is relevant to this specific proposal
3. Identify what evidence is needed to assess compliance

DO NOT list policies without explaining the specific requirements.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.CONSULTATION,
                    title="Consultation Responses",
                    order=7,
                    required=False,
                    prompt_template="""Summarize consultation responses received.

## INTERNAL CONSULTEES

| Consultee | Response | Key Comments |
|-----------|----------|--------------|
| Highways | [Received/Awaited] | [Summary or "No objection"] |
| Environmental Health | [Received/Awaited] | [Summary or "No objection"] |
| Tree Officer | [Received/Awaited] | [Summary or "No objection"] |
| Conservation | [Received/Awaited] | [Summary or "N/A"] |

## STATUTORY CONSULTEES
[List any statutory consultees and their responses]

## PUBLIC REPRESENTATIONS
Number received: [X]
Objections: [X]
Support: [X]
Neutral: [X]

Key issues raised:
- [Issue 1] - [Addressed in section X]
- [Issue 2] - [Addressed in section X]

Consultation information:
{consultation}

Note: If consultation responses are awaited, state clearly which are outstanding.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.ASSESSMENT,
                    title="Assessment",
                    order=8,
                    prompt_template="""Introduce the main planning issues to be assessed for this application.

## KEY PLANNING ISSUES

Based on the proposal type, site constraints, and policy framework, the following key issues require assessment:

1. **Principle of Development** - Is the development acceptable in principle?
2. **Design and Visual Impact** - Is the design appropriate for the context?
3. **Residential Amenity** - What impact on neighbouring properties?
4. **Highways and Parking** - Is access safe and parking adequate?
5. [Additional issues based on constraints]

## EVIDENCE SUMMARY

{evidence_assessments}

## DATA QUALITY NOTE

{report_quality}

Application summary:
{application_summary}

The following sections assess each issue against policy requirements using available evidence.""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.DESIGN,
                    title="Design and Visual Impact",
                    order=9,
                    prompt_template="""Assess the design quality and visual impact of the proposal.

## DESIGN ASSESSMENT

### Scale and Massing
| Measurement | This Proposal | Typical for Area | Source | Assessment |
|-------------|---------------|------------------|--------|------------|
| Ridge height | [X]m | [Y]m | [Elevation ref] | [Appropriate/Excessive] |
| Eaves height | [X]m | [Y]m | [Elevation ref] | [Appropriate/Excessive] |
| Storeys | [X] | [Y] | [Plan ref] | [Appropriate/Excessive] |
| Building width | [X]m | [Y]m | [Plan ref] | [Appropriate/Excessive] |
| Plot coverage | [X]% | [Y]% | [Calculated] | [Appropriate/Excessive] |

### Materials
| Element | Proposed | Local Character | Match |
|---------|----------|-----------------|-------|
| Walls | [Material from docs] | [Predominant in area] | [Yes/No/To verify] |
| Roof | [Material from docs] | [Predominant in area] | [Yes/No/To verify] |
| Windows | [Material from docs] | [Predominant in area] | [Yes/No/To verify] |

### Relationship to Context
- Building line: [Measurement from site plan, or "requires verification"]
- Spacing to neighbours: [Measurement or "requires verification"]
- Street scene impact: [Assessment based on evidence]

## EVIDENCE STATUS
{evidence_assessments}

## POLICY FRAMEWORK
{design_policies}

## CONCLUSION
- **Status:** [ACCEPTABLE / UNACCEPTABLE / INSUFFICIENT EVIDENCE]
- **Confidence:** [HIGH / MEDIUM / LOW]

Design documents:
{design_documents}

DO NOT conclude "acceptable design" without citing specific measurements and comparisons.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.HERITAGE,
                    title="Heritage Impact",
                    order=10,
                    required=False,
                    prompt_template="""Assess the impact on heritage assets.

## HERITAGE ASSETS AFFECTED

| Asset | Type | Grade/Status | Distance | Relationship |
|-------|------|--------------|----------|--------------|
| [Name] | [Listed Building/Conservation Area/SAM] | [Grade I/II*/II] | [X]m | [Within/Adjacent/Setting] |

Heritage constraints:
{heritage_constraints}

## STATUTORY FRAMEWORK

For **Listed Buildings** (within setting):
- S.66 Planning (Listed Buildings and Conservation Areas) Act 1990: "special regard to the desirability of preserving the building or its setting"

For **Conservation Areas**:
- S.72: "special attention shall be paid to the desirability of preserving or enhancing the character or appearance"

## SIGNIFICANCE ASSESSMENT

[Identify the significance of the heritage asset - what makes it special?]
[Source: Listing description / Conservation Area Appraisal / Heritage Statement]

## IMPACT ASSESSMENT

| Aspect | Impact | Level of Harm | Justification |
|--------|--------|---------------|---------------|
| Setting | [Description] | [No harm/Less than substantial/Substantial] | [Evidence] |
| Views | [Description] | [No harm/Less than substantial/Substantial] | [Evidence] |
| Character | [Description] | [No harm/Less than substantial/Substantial] | [Evidence] |

## NPPF BALANCE (if harm identified)

If less than substantial harm (NPPF 202):
- Public benefits: [List with weight]
- Whether benefits outweigh harm: [Yes/No]

## CONCLUSION
- **Status:** [ACCEPTABLE / UNACCEPTABLE / INSUFFICIENT EVIDENCE]
- **Statutory duty discharged:** [Yes/No]

Heritage documents:
{heritage_documents}

Relevant policies (heritage):
{heritage_policies}""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.AMENITY,
                    title="Residential Amenity",
                    order=11,
                    required=True,
                    prompt_template="""Assess the impact on residential amenity using QUANTIFIED TESTS.

## REQUIRED QUANTIFIED ASSESSMENTS

### 1. Privacy and Overlooking
**Standard:** 21m separation between facing habitable room windows; 12m side-to-side

| Relationship | Measurement | Standard | Result |
|-------------|-------------|----------|--------|
| To north neighbour | [Extract from site plan or state "NOT MEASURED"] | 21m | [PASS/FAIL/CANNOT ASSESS] |
| To south neighbour | [Extract from site plan or state "NOT MEASURED"] | 21m | [PASS/FAIL/CANNOT ASSESS] |
| To east neighbour | [Extract from site plan or state "NOT MEASURED"] | 21m | [PASS/FAIL/CANNOT ASSESS] |
| To west neighbour | [Extract from site plan or state "NOT MEASURED"] | 21m | [PASS/FAIL/CANNOT ASSESS] |

### 2. Daylight (45-Degree Rule - BRE Guidelines)
**Test:** Draw 45° line from centre of nearest ground floor window. If proposal breaches this plane, potential daylight impact.

Calculation:
- Distance to nearest affected window: [X]m (source: site plan)
- Proposed building height at that point: [Y]m (source: elevation)
- 45° plane height at building location: [X]m (equals distance)
- Result: [Proposal height Y is BELOW/ABOVE 45° plane - PASS/FAIL]

### 3. Overbearing (25-Degree Rule)
**Test:** From centre of nearest neighbour window at 2m height, if proposal subtends >25° vertically, potential overbearing.

Calculation:
- Distance to nearest window: [X]m
- Height of proposal above 2m: [Y-2]m
- Angle: arctan((Y-2)/X) = [Z]°
- Result: [Z]° is [BELOW/ABOVE] 25° threshold - [PASS/FAIL]

### 4. Living Conditions for Future Occupiers
- Garden size: [X]m² (minimum 50m² for houses, 25m² for flats typically)
- Internal floor area: [X]m² vs NDSS minimum for [Y]-bed dwelling
- Private amenity space orientation: [N/S/E/W] - [Good/Poor] for sunlight

## EVIDENCE STATUS
{evidence_assessments}

## POLICY FRAMEWORK
{amenity_policies}

## ASSESSMENT CONCLUSION
Based on the quantified tests above, conclude:
- **Status:** [ACCEPTABLE / UNACCEPTABLE / INSUFFICIENT EVIDENCE]
- **Confidence:** [HIGH / MEDIUM / LOW]
- **Verification Required:** [List items needing site visit confirmation]

If measurements are not available from documents, state clearly:
"Separation distances cannot be verified from submitted plans. Site visit and scaled plan measurement required before determination."

DO NOT conclude "acceptable" without completing the quantified tests above.""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.TRANSPORT,
                    title="Highways and Access",
                    order=10,
                    prompt_template="""Assess highways and access implications using QUANTIFIED STANDARDS.

## NPPF PARAGRAPH 111 TEST
Development should only be prevented or refused on highways grounds if:
1. There would be an "unacceptable" impact on highway safety, OR
2. The residual cumulative impacts on the road network would be "severe"

## PARKING ASSESSMENT

### Local Parking Standards
| Dwelling Size | Standard Requirement | Proposed | Compliance |
|--------------|---------------------|----------|------------|
| 1-2 bedroom | 1.5 spaces | [X] | [COMPLIANT/SHORTFALL] |
| 3 bedroom | 2 spaces | [X] | [COMPLIANT/SHORTFALL] |
| 4+ bedroom | 2-3 spaces | [X] | [COMPLIANT/SHORTFALL] |

**This proposal:** [X]-bedroom dwelling requiring [Y] spaces. [Z] spaces proposed.
**Result:** [COMPLIANT / SHORTFALL OF N SPACES]

## ACCESS ASSESSMENT

| Standard | Requirement | Proposed | Source | Compliance |
|----------|-------------|----------|--------|------------|
| Access width (single dwelling) | 3.2m minimum | [X]m | [Site plan ref] | [COMPLIANT/SHORTFALL] |
| Access width (multiple dwellings) | 4.8m minimum | [X]m | [Site plan ref] | [COMPLIANT/SHORTFALL] |
| Visibility splay (30mph) | 2.4m x 43m | [X]m x [Y]m | [Site plan ref] | [COMPLIANT/SHORTFALL] |
| Visibility splay (40mph) | 2.4m x 120m | [X]m x [Y]m | [Site plan ref] | [COMPLIANT/SHORTFALL] |

## HIGHWAY AUTHORITY CONSULTATION
[State whether highway authority response received, and summarise their comments]

## EVIDENCE STATUS
{evidence_assessments}

## POLICY FRAMEWORK
{transport_policies}

## NETWORK IMPACT ASSESSMENT
A single dwelling typically generates 4-6 vehicle movements per day.
[State whether this engages the NPPF "severe" test for network capacity]

## ASSESSMENT CONCLUSION
- **Status:** [ACCEPTABLE / UNACCEPTABLE / INSUFFICIENT EVIDENCE]
- **Confidence:** [HIGH / MEDIUM / LOW]
- **Verification Required:** [List items needing highway authority input]

If measurements not available: "Access width and visibility splays cannot be verified. Scaled site plan measurement required."

Transport documents:
{transport_documents}""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.ENVIRONMENT,
                    title="Environmental Considerations",
                    order=12,
                    required=False,
                    prompt_template="""Assess environmental considerations where relevant.

## ENVIRONMENTAL CONSTRAINTS

| Constraint | Status | Source | Implication |
|------------|--------|--------|-------------|
| Flood Zone | [Zone 1/2/3a/3b or N/A] | [EA mapping] | [FRA required?] |
| SSSI | [Within Xm or N/A] | [NE records] | [Consultation required?] |
| TPO | [Yes/No] | [Council records] | [Survey required?] |
| Contamination | [Suspected/Not suspected] | [Historical use] | [Investigation required?] |

Environmental constraints:
{environmental_constraints}

## BIODIVERSITY NET GAIN (Mandatory from 2024)

Statutory requirement: 10% biodiversity net gain
Current site value: [To be calculated/See ecology report]
Proposed value: [To be calculated]
Net change: [+X% or "BNG Plan condition required"]

## FLOOD RISK AND DRAINAGE

If in Flood Zone 1: "Site is in Flood Zone 1 (low risk). No FRA required for minor development."
If in Flood Zone 2/3: [Summarise FRA and sequential/exception tests]

## TREES AND LANDSCAPING

[Only if TPO or significant trees identified]

## CONCLUSION
- **Status:** [ACCEPTABLE / UNACCEPTABLE / INSUFFICIENT EVIDENCE]

Environmental documents:
{environmental_documents}

Relevant policies (environment):
{environmental_policies}""",
                    depends_on=[ReportSectionType.POLICY_CONTEXT],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.OTHER_MATTERS,
                    title="Other Material Considerations",
                    order=13,
                    required=False,
                    prompt_template="""Address any other material planning considerations.

## CIL/PLANNING OBLIGATIONS

CIL Liability: [Yes/No/Exempt]
[If liable, state rate and estimated charge]

S106 Required: [Yes/No]
[If yes, list heads of terms]

## SUSTAINABILITY

[Address any sustainability considerations if relevant to proposal scale]

## PUBLIC REPRESENTATIONS

[If not covered in consultation section, address key public concerns here]

Application details:
{application_summary}""",
                ),
                SectionTemplate(
                    section_type=ReportSectionType.PLANNING_BALANCE,
                    title="Planning Balance",
                    order=14,
                    prompt_template="""Weigh up the planning considerations and reach a balanced conclusion.

## ASSESSMENT SUMMARY

| Topic | Status | Confidence | Weight in Balance |
|-------|--------|------------|-------------------|
| Principle | [Acceptable/Unacceptable/Insufficient] | [High/Medium/Low] | [Significant/Moderate/Limited] |
| Design | [Acceptable/Unacceptable/Insufficient] | [High/Medium/Low] | [Significant/Moderate/Limited] |
| Amenity | [Acceptable/Unacceptable/Insufficient] | [High/Medium/Low] | [Significant/Moderate/Limited] |
| Highways | [Acceptable/Unacceptable/Insufficient] | [High/Medium/Low] | [Significant/Moderate/Limited] |
| [Other] | [Status] | [Confidence] | [Weight] |

## BENEFITS

| Benefit | Weight | Evidence |
|---------|--------|----------|
| Housing delivery | [Significant/Moderate/Limited] | [Contribution to housing supply] |
| Economic | [Significant/Moderate/Limited] | [Construction jobs, local spending] |
| [Other] | [Weight] | [Evidence] |

## HARMS

| Harm | Weight | Evidence | Can be Mitigated? |
|------|--------|----------|-------------------|
| [Harm if any] | [Significant/Moderate/Limited] | [Evidence] | [Yes - by condition/No] |

## PLANNING BALANCE

Previous assessment sections:
{previous_sections}

**Applicable Balance Test:**
- [ ] Standard balance (S.38(6) - accord with development plan)
- [ ] Tilted balance (NPPF para 11d - no 5YHLS)
- [ ] Heritage balance (NPPF para 202 - less than substantial harm)

**Conclusion:**
[Clear statement of whether benefits outweigh harms, with reasons]

## DATA QUALITY CAVEAT

{report_quality}

[If low quality: "This balance is provisional pending verification of [items]. The case officer should review before final determination."]""",
                    depends_on=[
                        ReportSectionType.DESIGN,
                        ReportSectionType.AMENITY,
                    ],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.RECOMMENDATION,
                    title="Recommendation",
                    order=15,
                    prompt_template="""Provide the planning recommendation.

## RECOMMENDATION

Based on the assessment:
{planning_balance}

### Data Quality Check
- Documents analysed: [X]
- Evidence confidence: [HIGH/MEDIUM/LOW]
- Critical gaps: [List or "None"]

### Decision

**[APPROVE WITH CONDITIONS / REFUSE / DEFER FOR INFORMATION]**

### Justification

[2-3 sentences explaining the recommendation with policy references]

### Key Policies

The proposal [accords with / conflicts with]:
- [Policy 1]: [Reason]
- [Policy 2]: [Reason]

### If Recommending Approval:
Subject to conditions below, the proposal is acceptable.

### If Recommending Refusal:
See refusal reasons below.

### If Recommending Deferral:
The following information is required before determination:
1. [Item 1] - needed for [assessment topic]
2. [Item 2] - needed for [assessment topic]""",
                    depends_on=[ReportSectionType.PLANNING_BALANCE],
                ),
                SectionTemplate(
                    section_type=ReportSectionType.CONDITIONS,
                    title="Recommended Conditions",
                    order=16,
                    required=False,
                    prompt_template="""List recommended planning conditions.

## STATUTORY CONDITIONS

1. **Time Limit**
   The development hereby permitted shall be commenced before the expiration of three years from the date of this permission.
   *Reason: To comply with Section 91 of the Town and Country Planning Act 1990.*
   *Policy Basis: Statutory requirement*

2. **Approved Plans**
   The development shall be carried out in accordance with the following approved plans: [LIST]
   *Reason: For the avoidance of doubt.*
   *Policy Basis: General planning practice*

3. **Biodiversity Net Gain (BNG)**
   Development may not begin until a Biodiversity Gain Plan has been submitted to and approved by the Local Planning Authority.
   *Reason: Statutory requirement under Environment Act 2021.*
   *Policy Basis: Schedule 7A TCPA 1990*

## POLICY-BASED CONDITIONS

[Add conditions addressing specific issues identified in assessment]

Format each condition as:
**[Number]. [Title]**
[Condition wording]
*Reason: [Why needed]*
*Policy Basis: [Policy reference]*
*Trigger: [Before commencement / Before occupation / Within X months]*

## CONDITION TESTS (6 tests from NPPF Annex A)

All conditions above have been checked against:
- Necessary
- Relevant to planning
- Relevant to the development
- Enforceable
- Precise
- Reasonable

Application type: {application_type}
Key issues to address: {key_issues}""",
                    depends_on=[ReportSectionType.RECOMMENDATION],
                ),
            ],
        )
