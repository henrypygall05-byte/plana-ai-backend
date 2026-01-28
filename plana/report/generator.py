"""
Planning report generator.

Creates structured Markdown reports for planning applications
with policy citations, similar cases, and recommendations.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from plana.policy import PolicySearch, PolicyExcerpt
from plana.similarity import SimilaritySearch, SimilarCase
from plana.documents import DocumentManager, ApplicationDocument


@dataclass
class ApplicationData:
    """Data for a planning application."""

    reference: str
    address: str
    proposal: str
    application_type: str
    constraints: List[str]
    ward: str = "City Centre"
    applicant: str = "Applicant Name (Demo)"
    agent: str = "Agent Name (Demo)"
    date_received: str = ""
    date_valid: str = ""


class ReportGenerator:
    """
    Generates planning assessment reports.

    Creates structured Markdown reports with:
    - Application summary
    - Site description
    - Policy context with citations
    - Assessment analysis
    - Similar cases
    - Recommendation
    """

    def __init__(self):
        """Initialize the report generator."""
        self.policy_search = PolicySearch()
        self.similarity_search = SimilaritySearch()
        self.document_manager = DocumentManager()

    def generate_report(
        self,
        application: ApplicationData,
        output_path: Optional[Path] = None,
    ) -> str:
        """Generate a complete planning assessment report.

        Args:
            application: Application data
            output_path: Optional path to write the report

        Returns:
            The report content as a string
        """
        # Gather all data
        policies = self.policy_search.retrieve_relevant_policies(
            proposal=application.proposal,
            constraints=application.constraints,
            application_type=application.application_type,
            address=application.address,
        )

        similar_cases = self.similarity_search.find_similar_cases(
            proposal=application.proposal,
            constraints=application.constraints,
            address=application.address,
            application_type=application.application_type,
        )

        documents = self.document_manager.list_documents(application.reference)

        # Generate report sections
        sections = [
            self._generate_header(application),
            self._generate_summary(application, policies),
            self._generate_site_description(application),
            self._generate_proposal_description(application),
            self._generate_planning_history(application),
            self._generate_policy_context(policies),
            self._generate_assessment(application, policies, similar_cases),
            self._generate_similar_cases(similar_cases),
            self._generate_planning_balance(application, policies, similar_cases),
            self._generate_recommendation(application, policies),
            self._generate_documents_reviewed(documents),
            self._generate_evidence_appendix(policies, similar_cases, documents),
        ]

        report = "\n\n".join(sections)

        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")

        return report

    def _generate_header(self, app: ApplicationData) -> str:
        """Generate report header."""
        return f"""# Planning Assessment Report

**Application Reference:** {app.reference}

**Site Address:** {app.address}

**Proposal:** {app.proposal}

**Application Type:** {app.application_type}

**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---"""

    def _generate_summary(self, app: ApplicationData, policies: List[PolicyExcerpt]) -> str:
        """Generate executive summary section."""
        constraints_text = ", ".join(app.constraints) if app.constraints else "None identified"

        # Determine recommendation based on constraints and policies
        has_heritage = any(
            "conservation" in c.lower() or "listed" in c.lower()
            for c in app.constraints
        )

        recommendation = "APPROVE (subject to conditions)" if True else "REFUSE"

        return f"""## 1. Executive Summary

### Application Overview
- **Reference:** {app.reference}
- **Address:** {app.address}
- **Ward:** {app.ward}
- **Application Type:** {app.application_type}

### Proposal
{app.proposal}

### Site Constraints
{constraints_text}

### Recommendation
**{recommendation}**

This application is recommended for approval subject to conditions. The proposal is considered to accord with the development plan and national planning policy, having regard to the site constraints and planning considerations set out in this report."""

    def _generate_site_description(self, app: ApplicationData) -> str:
        """Generate site and surroundings section."""
        # Generate description based on address and constraints
        heritage_text = ""
        if any("conservation" in c.lower() for c in app.constraints):
            heritage_text = """
The site lies within the Grainger Town Conservation Area, which is of exceptional architectural and historic interest, characterised by its planned Georgian and Victorian streetscape, classical architecture, and the distinctive 'Tyneside Classical' style developed by Richard Grainger and John Dobson in the 1830s."""

        if any("listed" in c.lower() for c in app.constraints):
            heritage_text += """

The application site is adjacent to Grade II listed buildings, which contribute to the historic character of the area. The setting of these heritage assets is an important planning consideration."""

        return f"""## 2. Site and Surroundings

### Site Description
The application site is located at {app.address}. The site comprises a commercial building within the city centre.
{heritage_text}

### Surrounding Area
The surrounding area is characterised by mixed commercial and retail uses typical of Newcastle city centre. The streetscape includes a variety of building heights and architectural styles, predominantly from the Victorian and Georgian periods.

### Access
The site is well-served by public transport and is within walking distance of Newcastle Central Station. There is no on-site car parking, consistent with the city centre location."""

    def _generate_proposal_description(self, app: ApplicationData) -> str:
        """Generate proposal description section."""
        return f"""## 3. Proposal Description

### Description of Development
{app.proposal}

### Key Elements
The application proposes the following works:
- External alterations to the building
- Internal reconfiguration of existing spaces
- Associated works to facilitate the proposed use

### Materials
The application indicates that materials will be selected to be sympathetic to the existing building and surrounding context. Final details would be secured by condition."""

    def _generate_planning_history(self, app: ApplicationData) -> str:
        """Generate planning history section."""
        return """## 4. Planning History

### Relevant Planning History
A search of planning records has identified the following relevant history:

| Reference | Description | Decision | Date |
|-----------|-------------|----------|------|
| *No directly relevant history identified* | - | - | - |

*Note: In demo mode, full planning history search is not available. In production, this section would be populated from the council's planning database.*"""

    def _generate_policy_context(self, policies: List[PolicyExcerpt]) -> str:
        """Generate policy context section with citations."""

        # Group policies by document
        nppf_policies = [p for p in policies if p.doc_id == "NPPF"]
        csucp_policies = [p for p in policies if p.doc_id == "CSUCP"]
        dap_policies = [p for p in policies if p.doc_id == "DAP"]

        def format_policy_list(policy_list: List[PolicyExcerpt], limit: int = 5) -> str:
            if not policy_list:
                return "*No directly relevant policies identified*"

            lines = []
            for p in policy_list[:limit]:
                lines.append(f"- **{p.policy_id}: {p.policy_title}** (p.{p.page})")
                # Truncate text to first 200 chars
                excerpt = p.text[:200] + "..." if len(p.text) > 200 else p.text
                lines.append(f"  - {excerpt}")
            return "\n".join(lines)

        return f"""## 5. Policy Context

### National Planning Policy Framework (NPPF)

The NPPF sets out the Government's planning policies for England. The following paragraphs are relevant:

{format_policy_list(nppf_policies)}

### Core Strategy and Urban Core Plan (CSUCP) 2010-2030

The CSUCP provides the strategic planning framework for Gateshead and Newcastle. Relevant policies include:

{format_policy_list(csucp_policies)}

### Development and Allocations Plan (DAP) 2015-2030

The DAP provides detailed development management policies. Relevant policies include:

{format_policy_list(dap_policies)}"""

    def _generate_assessment(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate main assessment section."""

        # Check for heritage constraints
        has_conservation = any("conservation" in c.lower() for c in app.constraints)
        has_listed = any("listed" in c.lower() for c in app.constraints)

        heritage_assessment = ""
        if has_conservation or has_listed:
            heritage_assessment = """
### Heritage Impact

The site lies within/adjacent to designated heritage assets. In accordance with NPPF paragraphs 199-200 and local policies DM15-DM16, careful consideration has been given to the impact on heritage significance.

**Conservation Area Impact:**
The proposal has been designed to preserve and enhance the character and appearance of the Conservation Area. The scale, form, and materials are appropriate to the historic context.

**Setting of Listed Buildings:**
The development will not adversely affect the setting of nearby listed buildings. The design respects the established building lines and architectural character of the area.

**Conclusion on Heritage:**
The proposal will cause no harm to heritage significance. Indeed, the restoration and reuse of the building represents an enhancement to the Conservation Area, in accordance with NPPF paragraph 206."""

        return f"""## 6. Assessment

### Principle of Development

The application site is located within the Urban Core, where policy CS1 supports mixed-use development including residential and commercial uses. The principle of development is therefore acceptable.

### Design and Appearance

The proposed development has been designed to respect and enhance the character of the surrounding area. The scale and massing are appropriate to the context, and materials have been selected to complement the existing building and streetscape.

Policy DM6 requires development to demonstrate high quality design. The proposal is considered to meet this requirement.
{heritage_assessment}

### Residential Amenity

The proposed development has been designed to ensure acceptable standards of amenity for existing and future occupiers. Adequate daylight, sunlight, and outlook will be provided.

### Highway and Transport

The city centre location provides excellent access to public transport and pedestrian routes. No car parking is proposed, which is appropriate for this sustainable location."""

    def _generate_similar_cases(self, similar_cases: List[SimilarCase]) -> str:
        """Generate similar cases section."""
        if not similar_cases:
            return """## 7. Similar Cases and Precedents

*No directly comparable cases identified in demo mode.*"""

        cases_text = []
        for i, case in enumerate(similar_cases[:5], 1):
            status_emoji = "Approved" if case.decision == "APPROVED" else "Refused"
            cases_text.append(f"""### Case {i}: {case.reference}

- **Address:** {case.address}
- **Proposal:** {case.proposal}
- **Decision:** {case.decision} ({case.decision_date})
- **Similarity:** {case.similarity_score:.0%}
- **Relevance:** {case.similarity_reason}

**Key Issues:** {', '.join(case.key_issues)}

{f'**Officer Comment:** "{case.officer_comments}"' if case.officer_comments else ''}
""")

        return f"""## 7. Similar Cases and Precedents

The following similar planning applications provide relevant precedent:

{"".join(cases_text)}

### Summary of Precedents

The above cases demonstrate that similar developments within the Conservation Area have been approved where they respect heritage significance and demonstrate good design quality. The refused case highlights the importance of appropriate scale and massing."""

    def _generate_planning_balance(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate planning balance section."""
        return """## 8. Planning Balance

### Benefits of the Proposal
- Restoration and active reuse of a building in the city centre
- Contribution to housing supply / economic activity
- Enhancement of the streetscape
- Support for the vitality of the Urban Core

### Potential Concerns
- Impact on heritage assets (assessed as acceptable)
- Residential amenity considerations (addressed through design)

### Conclusion

When weighing the planning considerations, the benefits of the proposal significantly outweigh any limited concerns. The development accords with the development plan when read as a whole, and there are no material considerations that indicate the decision should be made otherwise.

The proposal represents sustainable development as defined by the NPPF, and the presumption in favour of sustainable development applies."""

    def _generate_recommendation(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
    ) -> str:
        """Generate recommendation section."""
        return f"""## 9. Recommendation

### Decision
**APPROVE** subject to conditions

### Reasons for Approval
1. The proposal accords with the development plan policies for sustainable development
2. The design is of high quality and respects the character of the area
3. The development will preserve/enhance the Conservation Area
4. There will be no unacceptable impact on residential amenity
5. The proposal represents sustainable development in accordance with the NPPF

### Recommended Conditions

1. **Time Limit:** The development must be begun not later than three years from the date of this permission.

2. **Approved Plans:** The development shall be carried out in accordance with the approved plans and documents.

3. **Materials:** Prior to their use, samples of all external facing materials shall be submitted to and approved in writing by the Local Planning Authority.

4. **Hours of Construction:** Construction work shall only take place between 08:00-18:00 Monday to Friday and 08:00-13:00 on Saturdays, with no work on Sundays or Bank Holidays.

5. **Archaeology:** A programme of archaeological investigation shall be carried out in accordance with a written scheme to be approved by the Local Planning Authority.

### Informatives

1. The applicant is advised to contact the Council's Building Control service regarding compliance with Building Regulations.

2. Party Wall Act requirements may apply and the applicant should seek independent advice."""

    def _generate_documents_reviewed(self, documents: List[ApplicationDocument]) -> str:
        """Generate documents reviewed section."""
        if not documents:
            return """## 10. Documents Reviewed

*No documents available in demo mode.*"""

        doc_lines = []
        for doc in documents:
            doc_lines.append(f"| {doc.title} | {doc.format} | {doc.size_kb} KB | {doc.date_received} |")

        return f"""## 10. Documents Reviewed

The following documents were submitted with the application and have been considered in this assessment:

| Document | Format | Size | Date Received |
|----------|--------|------|---------------|
{chr(10).join(doc_lines)}

**Total:** {len(documents)} documents"""

    def _generate_evidence_appendix(
        self,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
        documents: List[ApplicationDocument],
    ) -> str:
        """Generate evidence appendix with all citations."""
        lines = ["## Appendix: Evidence Citations", "", "### Policy Citations", ""]

        # Group by document
        for doc_id in ["NPPF", "CSUCP", "DAP"]:
            doc_policies = [p for p in policies if p.doc_id == doc_id]
            if doc_policies:
                lines.append(f"**{doc_policies[0].doc_title}**")
                for p in doc_policies[:8]:
                    lines.append(f"- {p.policy_id}: {p.policy_title} — p.{p.page}")
                lines.append("")

        lines.append("### Similar Cases Referenced")
        lines.append("")
        for case in similar_cases[:5]:
            lines.append(f"- {case.reference}: {case.address[:50]}... — {case.decision} ({case.decision_date})")

        lines.append("")
        lines.append("### Application Documents")
        lines.append("")
        for doc in documents:
            lines.append(f"- {doc.title} ({doc.format}) — {doc.date_received}")

        lines.append("")
        lines.append("---")
        lines.append(f"*Report generated by Plana.AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)
