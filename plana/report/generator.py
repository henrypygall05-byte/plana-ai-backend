"""
Planning report generator.

Creates structured Markdown reports for planning applications
with policy citations, similar cases, and recommendations.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


# ---------------------------------------------------------------------------
# Policy-to-topic mapping — used to group retrieved policies under the
# correct assessment heading so each can be evaluated case-specifically.
# ---------------------------------------------------------------------------
POLICY_TOPICS: Dict[str, List[str]] = {
    "Principle of Development": ["NPPF-2", "NPPF-11", "CS1", "UC1", "DM1", "CS17"],
    "Design and Character": ["NPPF-12", "NPPF-130", "DM6", "CS15"],
    "Heritage Impact": [
        "NPPF-16", "NPPF-199", "NPPF-200", "NPPF-206",
        "DM15", "DM16", "DM17", "UC10", "UC11", "DM28",
    ],
    "Residential Amenity": ["DM21"],
    "Retail and Commercial": ["DM20"],
}

_POLICY_TO_TOPIC: Dict[str, str] = {}
for _topic, _ids in POLICY_TOPICS.items():
    for _pid in _ids:
        _POLICY_TO_TOPIC[_pid] = _topic


def _first_sentence(text: str) -> str:
    """Return the first sentence of *text* (for quoting the policy test)."""
    for i, ch in enumerate(text):
        if ch == "." and i > 20:
            return text[: i + 1]
    return text[:200] + ("..." if len(text) > 200 else "")


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

    # ------------------------------------------------------------------
    # Helpers (used by the assessment methods below)
    # ------------------------------------------------------------------

    @staticmethod
    def _has_constraint(app: "ApplicationData", keyword: str) -> bool:
        """True if any constraint contains *keyword* (case-insensitive)."""
        return any(keyword in c.lower() for c in app.constraints)

    @staticmethod
    def _categorize_policies(
        policies: List[PolicyExcerpt],
    ) -> Dict[str, List[PolicyExcerpt]]:
        """Group policies by assessment topic."""
        grouped: Dict[str, List[PolicyExcerpt]] = {t: [] for t in POLICY_TOPICS}
        grouped["Other Material Considerations"] = []
        for p in policies:
            topic = _POLICY_TO_TOPIC.get(p.policy_id)
            if topic and topic in grouped:
                grouped[topic].append(p)
            else:
                grouped["Other Material Considerations"].append(p)
        return grouped

    def _assess_single_policy(
        self,
        policy: PolicyExcerpt,
        app: "ApplicationData",
    ) -> Tuple[str, str]:
        """Return *(markdown_block, compliance)* for one policy.

        *compliance* is COMPLIANT | CANNOT FULLY ASSESS | NOT APPLICABLE.
        """
        pid = policy.policy_id
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) or "none"
        test = _first_sentence(policy.text)

        # --- Heritage policies ---
        if pid in ("NPPF-199", "NPPF-200", "NPPF-16"):
            if has_conservation or has_listed:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: Site constraints ({constraints_str}) "
                    f"include designated heritage assets. The proposal ({app.proposal}) "
                    f"must demonstrate it preserves heritage significance. "
                    f"**[NOT EVIDENCED]**: Level of harm cannot be quantified without "
                    f"elevation drawings and materials analysis.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS**",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: No designated heritage assets at "
                f"{app.address} ({constraints_str}). Policy not engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "NOT APPLICABLE",
            )

        if pid == "NPPF-206":
            if has_conservation:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: The site is within a Conservation Area. "
                    f"The proposal ({app.proposal}) must enhance or better reveal the "
                    f"area's significance. Subject to materials condition.\n"
                    f"- **Compliance**: **COMPLIANT** (subject to materials condition)",
                    "COMPLIANT",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: Site is not within a Conservation Area "
                f"({constraints_str}). Policy not engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "NOT APPLICABLE",
            )

        if pid in ("DM15", "DM16", "DM17", "UC10", "UC11", "DM28"):
            label_map = {
                "DM15": ("heritage assets", has_conservation or has_listed),
                "DM16": ("Conservation Area character", has_conservation),
                "DM17": ("listed building special interest", has_listed),
                "UC10": ("Grainger Town historic townscape",
                         has_conservation and "grainger" in app.address.lower()),
                "UC11": ("Urban Core heritage and character", True),
                "DM28": ("Grainger Town preservation",
                         "grainger" in app.address.lower()),
            }
            focus, engaged = label_map.get(pid, ("heritage", True))
            if not engaged:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: Constraints ({constraints_str}) do not "
                    f"engage this policy at {app.address}.\n"
                    f"- **Compliance**: **NOT APPLICABLE**",
                    "NOT APPLICABLE",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: {app.address} is subject to {focus} "
                f"protection (constraints: {constraints_str}). The proposal "
                f"({app.proposal}) must conserve and enhance the {focus}. "
                f"Materials, scale, and detailing require verification from drawings.\n"
                f"- **Compliance**: **CANNOT FULLY ASSESS**",
                "CANNOT FULLY ASSESS",
            )

        # --- Principle / strategic ---
        if pid in ("CS1", "UC1", "NPPF-2", "NPPF-11", "DM1"):
            proposal_lower = app.proposal.lower()
            dev_type = (
                "residential development" if any(k in proposal_lower for k in
                    ("residential", "apartment", "dwelling", "conversion")) else
                "commercial/mixed-use development"
            )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: {app.address} is within the Urban Core "
                f"({app.ward} ward). The proposal involves {dev_type}, which is "
                f"acceptable in principle at this location.\n"
                f"- **Compliance**: **COMPLIANT**",
                "COMPLIANT",
            )

        if pid == "CS17":
            proposal_lower = app.proposal.lower()
            is_housing = any(k in proposal_lower for k in
                ("residential", "apartment", "dwelling", "conversion"))
            if is_housing:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: The proposal ({app.proposal}) "
                    f"contributes to housing delivery at {app.address}.\n"
                    f"- **Compliance**: **COMPLIANT**",
                    "COMPLIANT",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: Proposal is not primarily residential; "
                f"housing delivery policy not directly engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "NOT APPLICABLE",
            )

        # --- Design ---
        if pid in ("NPPF-12", "NPPF-130", "DM6", "CS15"):
            extra = ("The site is within a Conservation Area, heightening the "
                     "design standard required. " if has_conservation else "")
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) at "
                f"{app.address} must demonstrate high quality design sympathetic "
                f"to the {app.ward} area. {extra}"
                f"**[NOT EVIDENCED]**: Requires officer review of elevation drawings "
                f"and materials schedule.\n"
                f"- **Compliance**: **CANNOT FULLY ASSESS**",
                "CANNOT FULLY ASSESS",
            )

        # --- Amenity ---
        if pid == "DM21":
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) at "
                f"{app.address} must provide acceptable amenity. Quantified tests "
                f"(45-degree daylight, 21 m privacy, 25-degree overbearing) require "
                f"dimensional data from submitted plans.\n"
                f"- **Compliance**: **CANNOT FULLY ASSESS**",
                "CANNOT FULLY ASSESS",
            )

        # --- Retail ---
        if pid == "DM20":
            proposal_lower = app.proposal.lower()
            if "shop front" in proposal_lower or "signage" in proposal_lower:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: Proposal includes shop front / "
                    f"signage works at {app.address}. Detailed shop front drawings "
                    f"required.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS**",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: Proposal does not include shop front "
                f"or signage works. Policy not engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "NOT APPLICABLE",
            )

        # --- Fallback ---
        return (
            f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
            f"- **Test**: \"{test}\"\n"
            f"- **Application evidence**: Proposal ({app.proposal}) at {app.address} "
            f"(constraints: {constraints_str}). Matched via: {policy.match_reason}.\n"
            f"- **Compliance**: **CANNOT FULLY ASSESS**",
            "CANNOT FULLY ASSESS",
        )

    def generate_report(
        self,
        application: ApplicationData,
        output_path: Optional[Path] = None,
        documents: Optional[List] = None,
    ) -> str:
        """Generate a complete planning assessment report.

        Args:
            application: Application data
            output_path: Optional path to write the report
            documents: Optional list of documents (demo ApplicationDocument or portal PortalDocument).
                      If not provided, demo documents are fetched.

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

        # Use provided documents or fetch demo documents
        if documents is None:
            documents = self.document_manager.list_documents(application.reference)

        # Generate report sections
        sections = [
            self._generate_header(application),
            self._generate_summary(application, policies, similar_cases),
            self._generate_site_description(application),
            self._generate_proposal_description(application),
            self._generate_planning_history(application),
            self._generate_policy_context(application, policies),
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

    def _generate_summary(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate executive summary with case-specific key issues."""
        constraints_text = (
            ", ".join(app.constraints) if app.constraints else "None identified"
        )
        has_heritage = self._has_constraint(app, "conservation") or self._has_constraint(app, "listed")
        proposal_lower = app.proposal.lower()

        key_issues: List[str] = []
        if has_heritage:
            key_issues.append("Impact on designated heritage assets")
        key_issues.append("Design quality and character")
        key_issues.append("Residential amenity")
        if any(k in proposal_lower for k in ("residential", "apartment", "dwelling", "conversion")):
            key_issues.append("Contribution to housing delivery")

        approved = sum(1 for c in similar_cases if c.decision == "APPROVED")
        refused = sum(1 for c in similar_cases if c.decision == "REFUSED")
        precedent = (
            f"{approved} approved, {refused} refused" if similar_cases
            else "None identified"
        )

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

### Key Planning Issues
{chr(10).join(f'- {i}' for i in key_issues)}

### Evidence Base
- **Policies assessed:** {len(policies)}
- **Precedent cases:** {precedent}

### Recommendation
**APPROVE (subject to conditions)**

Based on assessment of {len(policies)} policies against the site constraints ({constraints_text}) and the nature of the proposal. Key considerations are set out in the Assessment section."""

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

    def _generate_policy_context(
        self, app: ApplicationData, policies: List[PolicyExcerpt]
    ) -> str:
        """Generate policy context section with case-specific relevance."""

        nppf_policies = [p for p in policies if p.doc_id == "NPPF"]
        csucp_policies = [p for p in policies if p.doc_id == "CSUCP"]
        dap_policies = [p for p in policies if p.doc_id == "DAP"]

        constraints_str = ", ".join(app.constraints) or "none identified"

        def format_policy_list(policy_list: List[PolicyExcerpt], limit: int = 5) -> str:
            if not policy_list:
                return "*No directly relevant policies identified*"

            lines = []
            for p in policy_list[:limit]:
                lines.append(
                    f"- **{p.policy_id}: {p.policy_title}** "
                    f"(p.{p.page}, score {p.score:.2f})"
                )
                lines.append(
                    f"  - **Why relevant**: {p.match_reason} "
                    f"(site constraints: {constraints_str}; "
                    f"proposal: {app.proposal[:80]}{'...' if len(app.proposal) > 80 else ''})"
                )
            return "\n".join(lines)

        return f"""## 5. Policy Context

### National Planning Policy Framework (NPPF)

The following NPPF paragraphs are relevant to the proposal at {app.address}:

{format_policy_list(nppf_policies)}

### Core Strategy and Urban Core Plan (CSUCP) 2010-2030

Relevant to this application:

{format_policy_list(csucp_policies)}

### Development and Allocations Plan (DAP) 2015-2030

Relevant to this application:

{format_policy_list(dap_policies)}"""

    def _generate_assessment(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate main assessment section with per-policy case-specific blocks."""
        grouped = self._categorize_policies(policies)
        has_heritage = (
            self._has_constraint(app, "conservation")
            or self._has_constraint(app, "listed")
        )

        sections = ["## 6. Assessment"]
        compliance_rows: List[Tuple[str, str]] = []

        for topic_name in [
            "Principle of Development",
            "Design and Character",
            "Heritage Impact",
            "Residential Amenity",
            "Retail and Commercial",
            "Other Material Considerations",
        ]:
            topic_policies = grouped.get(topic_name, [])
            if not topic_policies:
                continue

            # Heritage policies are NOT assessed when no heritage constraints exist
            if topic_name == "Heritage Impact" and not has_heritage:
                sections.append(
                    f"### {topic_name}\n\n"
                    f"No heritage constraints identified for {app.address} "
                    f"(constraints: {', '.join(app.constraints) or 'none'}). "
                    f"Heritage policies matched by keyword but are "
                    f"**not engaged** for this application."
                )
                for p in topic_policies:
                    compliance_rows.append((p.policy_id, "NOT APPLICABLE"))
                continue

            topic_lines = [f"### {topic_name}\n"]
            for policy in topic_policies:
                block, status = self._assess_single_policy(policy, app)
                topic_lines.append(block)
                topic_lines.append("")
                compliance_rows.append((policy.policy_id, status))

            sections.append("\n".join(topic_lines))

        # Compliance summary table
        if compliance_rows:
            rows = ["### Policy Compliance Summary\n",
                    "| Policy | Compliance |", "|--------|-----------|"]
            for pid, status in compliance_rows:
                rows.append(f"| {pid} | {status} |")
            sections.append("\n".join(rows))

        return "\n\n".join(sections)

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
        """Generate planning balance derived from actual proposal + constraints."""
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) or "none identified"
        proposal_lower = app.proposal.lower()
        is_housing = any(k in proposal_lower for k in
            ("residential", "apartment", "dwelling", "conversion"))

        benefits = [f"- Active reuse of building at {app.address}"]
        if is_housing:
            benefits.append("- Contribution to housing delivery (CS17)")
        benefits.append(f"- Support for Urban Core vitality ({app.ward} ward, CS1)")

        concerns = []
        if has_conservation:
            concerns.append(
                "- Potential impact on Conservation Area character "
                "(NPPF-199, DM16) — mitigated by materials condition"
            )
        if has_listed:
            concerns.append(
                "- Potential impact on setting of listed buildings "
                "(NPPF-199, DM17) — mitigated by detailed design condition"
            )
        concerns.append(
            "- Residential amenity impact (DM21) — requires quantified "
            "assessment from plans"
        )

        approved = sum(1 for c in similar_cases if c.decision == "APPROVED")
        precedent = ""
        if approved:
            precedent = (
                f"\n\n**Precedent support:** {approved} approved similar case(s) "
                f"support the principle of this type of development at this location."
            )

        return f"""## 8. Planning Balance

### Benefits of the Proposal
{chr(10).join(benefits)}

### Potential Concerns
{chr(10).join(concerns)}

### Conclusion

The proposal ({app.proposal}) at {app.address} has been assessed against {len(policies)} relevant policies. Site constraints ({constraints_str}) engage {'heritage policies requiring careful assessment of impact on designated assets' if (has_conservation or has_listed) else 'standard development management policies'}.

The benefits — including active reuse of the site{', housing delivery' if is_housing else ''}, and Urban Core vitality — are considered to outweigh the identified concerns, subject to conditions.{precedent}"""

    def _generate_recommendation(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
    ) -> str:
        """Generate recommendation section citing specific policy IDs."""
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) or "none identified"

        # Build reasons referencing actual retrieved policies
        reasons: List[str] = []
        n = 1

        principle = [p.policy_id for p in policies
                     if p.policy_id in ("CS1", "UC1", "NPPF-2", "DM1")]
        if principle:
            reasons.append(
                f"{n}. The proposal accords with the principle of development "
                f"at {app.address} as set out in policies "
                f"{', '.join(principle)}."
            )
            n += 1

        heritage = [p.policy_id for p in policies
                    if p.policy_id in ("NPPF-199", "NPPF-200", "DM15", "DM16", "DM17")]
        if heritage and (has_conservation or has_listed):
            reasons.append(
                f"{n}. Subject to conditions, the proposal preserves the "
                f"significance of heritage assets ({constraints_str}) in "
                f"accordance with policies {', '.join(heritage)}."
            )
            n += 1

        design = [p.policy_id for p in policies
                  if p.policy_id in ("DM6", "CS15", "NPPF-130")]
        if design:
            reasons.append(
                f"{n}. Subject to materials approval, the proposal is capable "
                f"of acceptable design quality per policies "
                f"{', '.join(design)}."
            )
            n += 1

        reasons.append(
            f"{n}. The proposal represents sustainable development in "
            f"accordance with the NPPF."
        )

        # Conditions — only heritage condition when heritage constraints exist
        conditions = [
            "1. **Time Limit:** Development must begin within three years.\n"
            "   *Reason: Section 91, Town and Country Planning Act 1990.*",
            "2. **Approved Plans:** Development in accordance with approved plans.\n"
            "   *Reason: For the avoidance of doubt.*",
        ]
        cond_n = 3

        mat_reason = "In the interests of visual amenity"
        if has_conservation:
            mat_reason += " and to preserve the Conservation Area (DM16)"
        if has_listed:
            mat_reason += " and the setting of the listed building (DM17)"
        conditions.append(
            f"{cond_n}. **Materials:** Samples of external materials to be "
            f"approved before use.\n"
            f"   *Reason: {mat_reason}, per DM6 and CS15.*"
        )
        cond_n += 1

        if has_conservation or has_listed:
            heritage_cited = ", ".join(
                p.policy_id for p in policies
                if p.policy_id in ("DM15", "DM16", "DM17")
            ) or "DM15"
            conditions.append(
                f"{cond_n}. **Heritage Details:** 1:20 scale drawings of "
                f"new/altered architectural details to be approved.\n"
                f"   *Reason: To preserve heritage assets ({constraints_str}) "
                f"per {heritage_cited}.*"
            )
            cond_n += 1

        conditions.append(
            f"{cond_n}. **Hours of Construction:** 08:00-18:00 Mon-Fri, "
            f"08:00-13:00 Sat, none Sun/Bank Holidays.\n"
            f"   *Reason: Amenity of neighbours, per DM21.*"
        )

        return f"""## 9. Recommendation

### Decision
**APPROVE** subject to conditions

### Reasons for Approval
{chr(10).join(reasons)}

### Recommended Conditions

{chr(10).join(chr(10).join([c]) for c in conditions)}

### Informatives

1. The applicant is advised to contact Building Control regarding Building Regulations compliance.

2. Party Wall Act requirements may apply — seek independent advice."""

    def _generate_documents_reviewed(self, documents: List) -> str:
        """Generate documents reviewed section.

        Handles both demo ApplicationDocument and portal PortalDocument formats.
        """
        if not documents:
            return """## 10. Documents Reviewed

*No documents available in demo mode.*"""

        doc_lines = []
        for doc in documents:
            # Handle demo ApplicationDocument (has format, size_kb, date_received)
            if hasattr(doc, 'format') and hasattr(doc, 'size_kb'):
                doc_lines.append(f"| {doc.title} | {doc.format} | {doc.size_kb} KB | {doc.date_received} |")
            # Handle portal PortalDocument (has content_type, size_bytes, date_published)
            elif hasattr(doc, 'content_type') and hasattr(doc, 'size_bytes'):
                fmt = doc.content_type or "Unknown"
                if "/" in fmt:
                    fmt = fmt.split("/")[-1].upper()
                size = f"{doc.size_bytes // 1024} KB" if doc.size_bytes else "Unknown"
                date = doc.date_published or "N/A"
                doc_lines.append(f"| {doc.title} | {fmt} | {size} | {date} |")
            else:
                # Fallback for unknown document types
                title = getattr(doc, 'title', 'Unknown Document')
                doc_lines.append(f"| {title} | - | - | - |")

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
        documents: List,
    ) -> str:
        """Generate evidence appendix with all citations.

        Handles both demo ApplicationDocument and portal PortalDocument formats.
        """
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
            # Handle demo ApplicationDocument
            if hasattr(doc, 'format') and hasattr(doc, 'date_received'):
                lines.append(f"- {doc.title} ({doc.format}) — {doc.date_received}")
            # Handle portal PortalDocument
            elif hasattr(doc, 'content_type') and hasattr(doc, 'date_published'):
                fmt = doc.content_type or "Unknown"
                if "/" in fmt:
                    fmt = fmt.split("/")[-1].upper()
                date = doc.date_published or "N/A"
                lines.append(f"- {doc.title} ({fmt}) — {date}")
            else:
                title = getattr(doc, 'title', 'Unknown Document')
                lines.append(f"- {title}")

        lines.append("")
        lines.append("---")
        lines.append(f"*Report generated by Plana.AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)
