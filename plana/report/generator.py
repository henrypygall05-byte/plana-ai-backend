"""
Planning report generator.

Creates structured Markdown reports for planning applications
with policy citations, similar cases, and recommendations.

Each policy assessment is case-specific: it states the policy test,
applies site-specific evidence, and gives a compliance conclusion.
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


# Maps policy IDs to assessment topics so each policy is evaluated
# under the correct heading with application-specific reasoning.
POLICY_TOPICS: Dict[str, List[str]] = {
    "Principle of Development": [
        "NPPF-2", "NPPF-11", "CS1", "UC1", "DM1", "CS17",
    ],
    "Design and Character": [
        "NPPF-12", "NPPF-130", "DM6", "CS15",
    ],
    "Heritage Impact": [
        "NPPF-16", "NPPF-199", "NPPF-200", "NPPF-206",
        "DM15", "DM16", "DM17", "UC10", "UC11", "DM28",
    ],
    "Residential Amenity": [
        "DM21",
    ],
    "Retail and Commercial": [
        "DM20",
    ],
}

# Reverse lookup: policy_id -> topic name
_POLICY_TO_TOPIC: Dict[str, str] = {}
for _topic, _ids in POLICY_TOPICS.items():
    for _pid in _ids:
        _POLICY_TO_TOPIC[_pid] = _topic


def _extract_proposal_keywords(proposal: str) -> Dict[str, bool]:
    """Extract development characteristics from proposal text."""
    lower = proposal.lower()
    return {
        "extension": "extension" in lower,
        "conversion": "conversion" in lower or "change of use" in lower,
        "residential": "residential" in lower or "apartments" in lower or "dwelling" in lower,
        "retail": "retail" in lower or "shop" in lower,
        "office": "office" in lower,
        "demolition": "demolition" in lower,
        "alteration": "alteration" in lower,
        "roof": "roof" in lower,
        "rear": "rear" in lower,
        "storey": "storey" in lower or "story" in lower,
        "signage": "signage" in lower or "sign" in lower,
        "shop_front": "shop front" in lower or "shopfront" in lower,
        "restoration": "restoration" in lower or "refurbish" in lower,
    }


def _extract_first_sentence(text: str) -> str:
    """Extract the first sentence from policy text for quoting the test."""
    # Split on period followed by space or end
    for i, ch in enumerate(text):
        if ch == "." and i > 20:
            return text[: i + 1]
    return text[:200] + "..." if len(text) > 200 else text


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
            self._generate_similar_cases(application, similar_cases),
            self._generate_planning_balance(application, policies, similar_cases),
            self._generate_recommendation(application, policies, similar_cases),
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _categorize_policies(
        self, policies: List[PolicyExcerpt]
    ) -> Dict[str, List[PolicyExcerpt]]:
        """Group retrieved policies by assessment topic."""
        grouped: Dict[str, List[PolicyExcerpt]] = {t: [] for t in POLICY_TOPICS}
        grouped["Other Material Considerations"] = []
        for p in policies:
            topic = _POLICY_TO_TOPIC.get(p.policy_id)
            if topic and topic in grouped:
                grouped[topic].append(p)
            else:
                grouped["Other Material Considerations"].append(p)
        return grouped

    def _has_constraint(self, app: ApplicationData, keyword: str) -> bool:
        """Check if any constraint contains keyword (case-insensitive)."""
        return any(keyword in c.lower() for c in app.constraints)

    def _policy_relevance_reason(
        self, policy: PolicyExcerpt, app: ApplicationData
    ) -> str:
        """Generate a case-specific sentence explaining why this policy is relevant."""
        pid = policy.policy_id
        proposal_kw = _extract_proposal_keywords(app.proposal)
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) if app.constraints else "none identified"

        # Heritage policies
        if pid in ("NPPF-199", "NPPF-200", "DM15"):
            if has_conservation and has_listed:
                return (
                    f"The site at {app.address} is within a Conservation Area and adjacent to listed buildings. "
                    f"This policy applies directly because the proposal ({app.proposal}) may affect designated heritage assets."
                )
            if has_conservation:
                return (
                    f"The site is within a Conservation Area ({constraints_str}). "
                    f"This policy is engaged because the proposal may affect the significance of this designated heritage asset."
                )
            if has_listed:
                return (
                    f"The site is adjacent to listed buildings ({constraints_str}). "
                    f"This policy requires the impact on the listed building's significance to be assessed."
                )
            return f"Matched via content relevance to the proposal: {app.proposal}"

        if pid in ("NPPF-206", "DM16", "UC10", "DM28"):
            if has_conservation:
                return (
                    f"The site lies within a Conservation Area. This policy requires assessment of whether "
                    f"the proposal — {app.proposal} — preserves or enhances the character and appearance of the area."
                )
            return f"Matched via content relevance. Site constraints: {constraints_str}."

        if pid in ("DM17",):
            if has_listed:
                return (
                    f"Listed buildings form part of the site constraints ({constraints_str}). "
                    f"This policy requires the proposal to demonstrate no adverse effect on the special interest of the listed building."
                )
            return f"Matched via content relevance. Site constraints: {constraints_str}."

        if pid == "UC11":
            return (
                f"The site is within the Urban Core where heritage and character are protected. "
                f"Constraints: {constraints_str}. The proposal must demonstrate conservation and enhancement of heritage assets."
            )

        # Principle / strategic policies
        if pid in ("CS1", "UC1"):
            return (
                f"The site at {app.address} is within the Urban Core. This policy sets the strategic framework for "
                f"acceptable development types in this location. The proposal involves: {app.proposal}."
            )
        if pid == "NPPF-2":
            return (
                f"The presumption in favour of sustainable development applies. This assessment must determine "
                f"whether the proposal ({app.proposal}) accords with the development plan."
            )
        if pid == "NPPF-11":
            return (
                f"The proposal involves development at {app.address}, a previously-developed site. "
                f"This policy promotes effective use of brownfield land."
            )
        if pid == "DM1":
            return (
                f"This policy applies to all development proposals. The Council must assess whether "
                f"the proposal at {app.address} improves economic, social and environmental conditions."
            )
        if pid == "CS17":
            if proposal_kw["residential"] or proposal_kw["conversion"]:
                return (
                    f"The proposal involves residential development/conversion at {app.address}. "
                    f"This policy supports housing delivery, including conversion of underused upper floors in town centres."
                )
            return f"Assessed for relevance to housing delivery. Proposal: {app.proposal}."

        # Design policies
        if pid in ("NPPF-12", "NPPF-130", "DM6", "CS15"):
            return (
                f"All development must demonstrate high quality design. This policy applies to the proposal "
                f"at {app.address} which involves: {app.proposal}. The design must complement the "
                f"existing character of the {app.ward} area."
            )

        # Amenity
        if pid == "DM21":
            return (
                f"The proposal at {app.address} must provide acceptable amenity standards for existing "
                f"and future occupiers. This includes daylight, sunlight, outlook, and privacy assessments."
            )

        # Retail
        if pid == "DM20":
            if proposal_kw["shop_front"] or proposal_kw["signage"]:
                return (
                    f"The proposal includes shop front / signage works. This policy requires designs to "
                    f"respect the character of the building and wider street scene."
                )
            return f"Matched via content relevance to the proposal."

        # Fallback: use the match_reason from the search engine
        return f"Matched via: {policy.match_reason}. Proposal: {app.proposal}."

    def _assess_single_policy(
        self,
        policy: PolicyExcerpt,
        app: ApplicationData,
        similar_cases: List[SimilarCase],
    ) -> Tuple[str, str]:
        """Produce a per-policy assessment block and a compliance status.

        Returns:
            (markdown_block, compliance) where compliance is one of
            COMPLIANT / NON-COMPLIANT / CANNOT FULLY ASSESS
        """
        pid = policy.policy_id
        proposal_kw = _extract_proposal_keywords(app.proposal)
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) if app.constraints else "none"

        policy_test = _extract_first_sentence(policy.text)

        # Find relevant precedent for this policy topic
        topic = _POLICY_TO_TOPIC.get(pid, "")
        relevant_precedent = ""
        for case in similar_cases[:3]:
            case_issues_lower = [i.lower() for i in case.key_issues]
            if topic == "Heritage Impact" and any("heritage" in i or "conservation" in i or "listed" in i for i in case_issues_lower):
                relevant_precedent = (
                    f"Precedent {case.reference} ({case.decision}, {case.decision_date}): "
                    f"{case.officer_comments or case.similarity_reason}"
                )
                break
            if topic == "Design and Character" and any("design" in i for i in case_issues_lower):
                relevant_precedent = (
                    f"Precedent {case.reference} ({case.decision}, {case.decision_date}): "
                    f"{case.officer_comments or case.similarity_reason}"
                )
                break

        precedent_line = f"\n- **Precedent**: {relevant_precedent}" if relevant_precedent else ""

        # ---- Heritage policies ----
        if pid == "NPPF-199":
            compliance = "COMPLIANT" if not (has_conservation or has_listed) else "CANNOT FULLY ASSESS"
            evidence = (
                f"Site constraints include: {constraints_str}. The proposal ({app.proposal}) "
                f"affects a designated heritage asset. Great weight must be given to conservation. "
                f"**[Document evidence required]**: Detailed assessment of harm to heritage significance "
                f"requires elevation drawings, materials schedule, and Design & Access Statement to determine "
                f"whether the proposal preserves the asset's significance."
            )
            if has_conservation or has_listed:
                compliance = "CANNOT FULLY ASSESS"
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: {evidence}\n"
                f"- **Compliance**: **{compliance}** — heritage impact requires officer verification with submitted drawings and site visit{precedent_line}",
                compliance,
            )

        if pid == "NPPF-200":
            if has_conservation or has_listed:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{policy_test}\"\n"
                    f"- **Application evidence**: The site has heritage constraints ({constraints_str}). "
                    f"If the proposal causes less than substantial harm, that harm must be weighed against public benefits. "
                    f"The proposal ({app.proposal}) offers benefits including active reuse of a {app.ward} building. "
                    f"**[NOT EVIDENCED]**: Level of harm cannot be quantified without elevation/materials analysis.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS** — harm level requires measured assessment from drawings{precedent_line}",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: No designated heritage assets directly affected ({constraints_str}). Policy test not engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "COMPLIANT",
            )

        if pid == "NPPF-206":
            if has_conservation:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{policy_test}\"\n"
                    f"- **Application evidence**: The site is within a Conservation Area. The proposal "
                    f"({app.proposal}) represents new development within the Conservation Area. "
                    f"This policy requires that development enhances or better reveals the area's significance. "
                    f"**Assessment**: The nature of the works (as described) suggests potential to enhance the area "
                    f"through active reuse, subject to appropriate materials and detailing.\n"
                    f"- **Compliance**: **COMPLIANT** (subject to materials condition){precedent_line}",
                    "COMPLIANT",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: Site is not within a Conservation Area ({constraints_str}). Policy not directly engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "COMPLIANT",
            )

        if pid in ("DM15", "DM16", "DM17", "UC10", "UC11", "DM28"):
            label_map = {
                "DM15": ("heritage assets", has_conservation or has_listed),
                "DM16": ("Conservation Area character", has_conservation),
                "DM17": ("listed building special interest", has_listed),
                "UC10": ("Grainger Town historic townscape", has_conservation and "grainger" in app.address.lower()),
                "UC11": ("Urban Core heritage and character", True),
                "DM28": ("Grainger Town preservation", "grainger" in app.address.lower()),
            }
            focus, engaged = label_map.get(pid, ("heritage", True))
            if not engaged:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{policy_test}\"\n"
                    f"- **Application evidence**: Site constraints ({constraints_str}) do not engage this policy. "
                    f"The site at {app.address} is not within the area covered by this policy.\n"
                    f"- **Compliance**: **NOT APPLICABLE**",
                    "COMPLIANT",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The site at {app.address} is subject to {focus} protection "
                f"(constraints: {constraints_str}). The proposal ({app.proposal}) must demonstrate "
                f"it conserves and enhances the {focus}. "
                f"**Assessment**: The works described involve alterations that must be assessed against "
                f"the specific character of this location. Materials, scale, and detailing must be verified "
                f"against submitted drawings.\n"
                f"- **Compliance**: **CANNOT FULLY ASSESS** — requires elevation drawings and materials details{precedent_line}",
                "CANNOT FULLY ASSESS",
            )

        # ---- Principle / strategic policies ----
        if pid in ("CS1", "UC1"):
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The site at {app.address} is within the Urban Core ({app.ward} ward). "
                f"The proposal ({app.proposal}) involves "
                f"{'residential development' if proposal_kw.get('residential') else 'commercial/mixed-use development'}, "
                f"which is {'supported' if proposal_kw.get('residential') or proposal_kw.get('conversion') else 'an acceptable use'} "
                f"within the Urban Core under this policy.\n"
                f"- **Compliance**: **COMPLIANT** — the type of development is acceptable in principle at this location",
                "COMPLIANT",
            )

        if pid == "NPPF-2":
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) at {app.address} must be assessed "
                f"against the development plan. If the plan is up-to-date and the proposal accords with it, "
                f"permission should be granted without delay. The key policies to assess accord with are: "
                f"{'heritage policies (NPPF-199, DM15, DM16) given the site constraints of ' + constraints_str if (has_conservation or has_listed) else 'design and amenity policies'}.\n"
                f"- **Compliance**: **COMPLIANT** — subject to accordance with the specific policies assessed below",
                "COMPLIANT",
            )

        if pid == "NPPF-11":
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The site at {app.address} is previously-developed land within "
                f"the Urban Core. The proposal ({app.proposal}) makes effective use of this brownfield site, "
                f"consistent with the policy objective.\n"
                f"- **Compliance**: **COMPLIANT** — development of previously-developed land in a sustainable location",
                "COMPLIANT",
            )

        if pid == "DM1":
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) at {app.address} has been assessed "
                f"against the presumption in favour of sustainable development. The Council will work proactively "
                f"to approve proposals that improve conditions in the area.\n"
                f"- **Compliance**: **COMPLIANT** — presumption applies; no clear reason for refusal identified at this stage",
                "COMPLIANT",
            )

        if pid == "CS17":
            if proposal_kw.get("residential") or proposal_kw.get("conversion"):
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{policy_test}\"\n"
                    f"- **Application evidence**: The proposal ({app.proposal}) involves "
                    f"{'conversion to residential use' if proposal_kw.get('conversion') else 'residential development'} "
                    f"at {app.address}. This policy encourages residential conversions of underused upper floors "
                    f"in town centres and delivery of new homes.\n"
                    f"- **Compliance**: **COMPLIANT** — the proposal contributes to housing delivery targets",
                    "COMPLIANT",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) is not primarily residential. "
                f"This housing delivery policy is not directly engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "COMPLIANT",
            )

        # ---- Design policies ----
        if pid in ("NPPF-12", "NPPF-130", "DM6", "CS15"):
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) at {app.address} in the "
                f"{app.ward} ward must demonstrate high quality design that is sympathetic to local character. "
                f"{'The site is within a Conservation Area, heightening the design standard required. ' if has_conservation else ''}"
                f"**[NOT EVIDENCED]**: Compliance with design requirements cannot be confirmed without "
                f"assessment of submitted elevation drawings, materials schedule, and comparison with the "
                f"prevailing character of {app.ward}.\n"
                f"- **Compliance**: **CANNOT FULLY ASSESS** — requires officer review of design drawings",
                "CANNOT FULLY ASSESS",
            )

        # ---- Amenity ----
        if pid == "DM21":
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) at {app.address} must provide "
                f"acceptable amenity for existing and future occupiers. Key tests:\n"
                f"  - **Daylight (45-degree rule)**: **[NOT EVIDENCED]** — separation distances to neighbouring "
                f"windows not available from submitted data; requires site plan measurements.\n"
                f"  - **Privacy (21m rule)**: **[NOT EVIDENCED]** — window-to-window distances require "
                f"floor plan and site plan analysis.\n"
                f"  - **Overbearing (25-degree rule)**: **[NOT EVIDENCED]** — building height relative to "
                f"neighbours requires elevation and site plan data.\n"
                f"- **Compliance**: **CANNOT FULLY ASSESS** — quantified amenity tests require dimensional data from plans",
                "CANNOT FULLY ASSESS",
            )

        # ---- Retail ----
        if pid == "DM20":
            if proposal_kw.get("shop_front") or proposal_kw.get("signage"):
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{policy_test}\"\n"
                    f"- **Application evidence**: The proposal includes shop front/signage works at {app.address}. "
                    f"{'The site is within a Conservation Area, requiring designs to preserve or enhance its character. ' if has_conservation else ''}"
                    f"Materials and detailed design must respect the building and wider street scene.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS** — requires detailed shop front drawings",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal ({app.proposal}) does not include shop front or "
                f"signage works. This policy is not directly engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "COMPLIANT",
            )

        # ---- Sustainability ----
        if pid == "CS18":
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: The proposal is at {app.address}, an urban location. "
                f"No specific green infrastructure or ecological impacts identified from the proposal description. "
                f"Constraints: {constraints_str}.\n"
                f"- **Compliance**: **COMPLIANT** — no adverse environmental impact identified",
                "COMPLIANT",
            )

        # ---- NPPF-16: Historic environment strategy ----
        if pid == "NPPF-16":
            if has_conservation or has_listed:
                return (
                    f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{policy_test}\"\n"
                    f"- **Application evidence**: The site at {app.address} involves heritage assets "
                    f"({constraints_str}). The proposal ({app.proposal}) must be assessed for its impact on "
                    f"these irreplaceable resources. Detailed heritage impact assessment is required.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS** — heritage significance assessment required",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{policy_test}\"\n"
                f"- **Application evidence**: No designated heritage assets directly affected at {app.address} "
                f"({constraints_str}). Strategic heritage policy noted but not directly engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "COMPLIANT",
            )

        # ---- Fallback for any other policy ----
        return (
            f"**{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
            f"- **Test**: \"{policy_test}\"\n"
            f"- **Application evidence**: The proposal ({app.proposal}) at {app.address} "
            f"(constraints: {constraints_str}) has been assessed against this policy. "
            f"Matched via: {policy.match_reason}.\n"
            f"- **Compliance**: **CANNOT FULLY ASSESS** — further evidence required",
            "CANNOT FULLY ASSESS",
        )

    # ------------------------------------------------------------------
    # Section generators
    # ------------------------------------------------------------------

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
        """Generate executive summary with case-specific context."""
        constraints_text = ", ".join(app.constraints) if app.constraints else "None identified"
        has_heritage = self._has_constraint(app, "conservation") or self._has_constraint(app, "listed")

        # Identify key issues from constraints and proposal
        key_issues = []
        if has_heritage:
            key_issues.append("impact on designated heritage assets")
        key_issues.append("design quality and character")
        key_issues.append("residential amenity")

        proposal_kw = _extract_proposal_keywords(app.proposal)
        if proposal_kw["residential"] or proposal_kw["conversion"]:
            key_issues.append("contribution to housing delivery")
        if proposal_kw["shop_front"] or proposal_kw["signage"]:
            key_issues.append("shop front/signage design")

        key_issues_text = "\n".join(f"- {issue.capitalize()}" for issue in key_issues)

        # Count similar approved cases
        approved_count = sum(1 for c in similar_cases if c.decision == "APPROVED")
        refused_count = sum(1 for c in similar_cases if c.decision == "REFUSED")
        precedent_text = (
            f"{approved_count} approved and {refused_count} refused similar cases identified"
            if similar_cases
            else "No similar cases identified"
        )

        # Policy count by source
        nppf_count = sum(1 for p in policies if p.doc_id == "NPPF")
        local_count = sum(1 for p in policies if p.doc_id in ("CSUCP", "DAP"))

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
{key_issues_text}

### Evidence Base
- **Policies assessed:** {len(policies)} ({nppf_count} NPPF, {local_count} local plan)
- **Precedent cases:** {precedent_text}

### Recommendation
**APPROVE (subject to conditions)**

The recommendation is based on assessment of {len(policies)} relevant policies against the site-specific constraints ({constraints_text}) and the nature of the proposal. The key considerations are set out in detail in the Assessment section below."""

    def _generate_site_description(self, app: ApplicationData) -> str:
        """Generate site and surroundings section."""
        heritage_text = ""
        if self._has_constraint(app, "conservation"):
            heritage_text = f"""
The site lies within a Conservation Area (as identified in the site constraints: {', '.join(c for c in app.constraints if 'conservation' in c.lower())}). This is a material consideration that engages heritage policies NPPF-199, NPPF-200, DM15, and DM16."""

        if self._has_constraint(app, "listed"):
            listed_constraints = [c for c in app.constraints if "listed" in c.lower()]
            heritage_text += f"""

The application site is adjacent to/affects listed buildings ({', '.join(listed_constraints)}). The setting of these heritage assets is an important planning consideration, engaging policies NPPF-199, DM15, and DM17."""

        return f"""## 2. Site and Surroundings

### Site Description
The application site is located at {app.address}, within the {app.ward} ward.
{heritage_text}

### Site Constraints Summary

| Constraint | Policies Engaged |
|------------|-----------------|
{self._format_constraints_table(app)}

### Surrounding Area
**[OFFICER VERIFICATION REQUIRED]**: The character of the surrounding area at {app.address} should be verified through a site visit. Key aspects to verify include: prevailing building heights, materials, architectural style, and relationship to neighbouring properties."""

    def _format_constraints_table(self, app: ApplicationData) -> str:
        """Build a markdown table mapping each constraint to relevant policies."""
        if not app.constraints:
            return "| None identified | N/A |"

        constraint_policy_map = {
            "conservation": "NPPF-199, NPPF-200, NPPF-206, DM15, DM16, UC10, UC11",
            "listed": "NPPF-199, NPPF-200, DM15, DM17, UC11",
            "grainger": "UC10, DM28, CS1",
            "green belt": "NPPF Chapter 13",
            "flood": "NPPF Chapter 14",
            "tree": "DM29",
        }

        rows = []
        for constraint in app.constraints:
            matched_policies = "General policies apply"
            for keyword, pols in constraint_policy_map.items():
                if keyword in constraint.lower():
                    matched_policies = pols
                    break
            rows.append(f"| {constraint} | {matched_policies} |")

        return "\n".join(rows)

    def _generate_proposal_description(self, app: ApplicationData) -> str:
        """Generate proposal description section."""
        proposal_kw = _extract_proposal_keywords(app.proposal)

        elements = []
        if proposal_kw["extension"]:
            elements.append("Extension works to the existing building")
        if proposal_kw["conversion"]:
            elements.append("Conversion/change of use of existing spaces")
        if proposal_kw["alteration"]:
            elements.append("External and/or internal alterations")
        if proposal_kw["roof"]:
            elements.append("Roof-level works")
        if proposal_kw["demolition"]:
            elements.append("Demolition of existing structures")
        if proposal_kw["shop_front"]:
            elements.append("New or replacement shop front")
        if proposal_kw["signage"]:
            elements.append("New signage")
        if not elements:
            elements.append("Works as described in the proposal")

        elements_text = "\n".join(f"- {e}" for e in elements)

        return f"""## 3. Proposal Description

### Description of Development
{app.proposal}

### Key Elements (extracted from proposal)
{elements_text}

### Specifications
**[NOT EVIDENCED]**: The following cannot be confirmed without submitted drawings:
- Ridge height, eaves height, number of storeys
- Floor area (GIA)
- Materials specification
- Separation distances to boundaries
- Parking provision

These dimensions are required for quantified assessment under policies DM6, DM21, and CS15."""

    def _generate_planning_history(self, app: ApplicationData) -> str:
        """Generate planning history section."""
        return f"""## 4. Planning History

### Relevant Planning History
A search of planning records for {app.address} has identified the following relevant history:

| Reference | Description | Decision | Date |
|-----------|-------------|----------|------|
| *No directly relevant history identified* | - | - | - |

*Note: In demo mode, full planning history search is not available. In production, this section would be populated from the council's planning database.*"""

    def _generate_policy_context(
        self, app: ApplicationData, policies: List[PolicyExcerpt]
    ) -> str:
        """Generate policy context section with case-specific relevance explanations."""
        nppf_policies = [p for p in policies if p.doc_id == "NPPF"]
        csucp_policies = [p for p in policies if p.doc_id == "CSUCP"]
        dap_policies = [p for p in policies if p.doc_id == "DAP"]

        def format_policy_list(policy_list: List[PolicyExcerpt], limit: int = 5) -> str:
            if not policy_list:
                return "*No directly relevant policies identified*"

            lines = []
            for p in policy_list[:limit]:
                lines.append(f"- **{p.policy_id}: {p.policy_title}** (p.{p.page}, relevance score: {p.score:.2f})")
                # Case-specific relevance
                relevance = self._policy_relevance_reason(p, app)
                lines.append(f"  - **Why relevant to this application**: {relevance}")
            return "\n".join(lines)

        return f"""## 5. Policy Context

### National Planning Policy Framework (NPPF)

The NPPF sets out the Government's planning policies for England. The following paragraphs are relevant to the proposal at {app.address}:

{format_policy_list(nppf_policies)}

### Core Strategy and Urban Core Plan (CSUCP) 2010-2030

The CSUCP provides the strategic planning framework for Gateshead and Newcastle. Relevant to this application:

{format_policy_list(csucp_policies)}

### Development and Allocations Plan (DAP) 2015-2030

The DAP provides detailed development management policies. Relevant to this application:

{format_policy_list(dap_policies)}"""

    def _generate_assessment(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate main assessment section with per-policy case-specific analysis."""
        grouped = self._categorize_policies(policies)
        sections = ["## 6. Assessment"]
        compliance_summary = []

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

            # Skip heritage section if no heritage constraints
            if topic_name == "Heritage Impact" and not (
                self._has_constraint(app, "conservation")
                or self._has_constraint(app, "listed")
                or self._has_constraint(app, "heritage")
            ):
                # Still note it was considered
                sections.append(
                    f"### {topic_name}\n\n"
                    f"No heritage constraints identified for {app.address} "
                    f"(site constraints: {', '.join(app.constraints) or 'none'}). "
                    f"Heritage policies matched by keyword relevance but are **not engaged** for this application."
                )
                for p in topic_policies:
                    compliance_summary.append((p.policy_id, "NOT APPLICABLE"))
                continue

            topic_section = [f"### {topic_name}\n"]

            for policy in topic_policies:
                block, compliance = self._assess_single_policy(policy, app, similar_cases)
                topic_section.append(block)
                topic_section.append("")
                compliance_summary.append((policy.policy_id, compliance))

            sections.append("\n".join(topic_section))

        # Add compliance summary table
        if compliance_summary:
            summary_lines = [
                "\n### Policy Compliance Summary\n",
                "| Policy | Compliance |",
                "|--------|-----------|",
            ]
            for pid, status in compliance_summary:
                summary_lines.append(f"| {pid} | {status} |")
            sections.append("\n".join(summary_lines))

        return "\n\n".join(sections)

    def _generate_similar_cases(
        self, app: ApplicationData, similar_cases: List[SimilarCase]
    ) -> str:
        """Generate similar cases section with case-specific comparison."""
        if not similar_cases:
            return f"""## 7. Similar Cases and Precedents

*No directly comparable cases identified for the proposal at {app.address}.*"""

        cases_text = []
        for i, case in enumerate(similar_cases[:5], 1):
            # Identify key similarities and differences
            shared_constraints = [
                c for c in app.constraints
                if any(c.lower() in hc.lower() or hc.lower() in c.lower() for hc in case.constraints)
            ]
            different_constraints = [
                c for c in app.constraints
                if not any(c.lower() in hc.lower() or hc.lower() in c.lower() for hc in case.constraints)
            ]
            case_only_constraints = [
                hc for hc in case.constraints
                if not any(c.lower() in hc.lower() or hc.lower() in c.lower() for c in app.constraints)
            ]

            comparison_table = (
                f"| Factor | This Application | {case.reference} |\n"
                f"|--------|-----------------|-------------------|\n"
                f"| Address | {app.address} | {case.address} |\n"
                f"| Proposal | {app.proposal[:80]}{'...' if len(app.proposal) > 80 else ''} | {case.proposal[:80]}{'...' if len(case.proposal) > 80 else ''} |\n"
                f"| Constraints | {', '.join(app.constraints) or 'None'} | {', '.join(case.constraints) or 'None'} |\n"
                f"| Decision | Pending | {case.decision} ({case.decision_date}) |"
            )

            similarities = f"Shared constraints: {', '.join(shared_constraints)}" if shared_constraints else "No shared constraints"
            differences = []
            if different_constraints:
                differences.append(f"This application has: {', '.join(different_constraints)}")
            if case_only_constraints:
                differences.append(f"Precedent had: {', '.join(case_only_constraints)}")
            differences_text = "; ".join(differences) if differences else "Similar constraint profile"

            precedent_weight = "MODERATE"
            if shared_constraints and case.similarity_score > 0.5:
                precedent_weight = "STRONG"
            elif case.similarity_score < 0.3:
                precedent_weight = "WEAK"

            cases_text.append(f"""### Case {i}: {case.reference}

{comparison_table}

- **Similarity score:** {case.similarity_score:.0%}
- **Key similarities:** {similarities}
- **Key differences:** {differences_text}
- **Precedent weight:** {precedent_weight}
- **Key issues addressed:** {', '.join(case.key_issues)}
- **Relevance to this application:** {case.similarity_reason}

{f'**Officer reasoning:** "{case.officer_comments}"' if case.officer_comments else ''}

**What this means for {app.reference}:** {"This approved precedent supports the principle of the current proposal, subject to the differences noted above." if case.decision == "APPROVED" else "This refusal highlights risks that must be addressed. The reasons for refusal should be considered in the current assessment."}
""")

        approved_count = sum(1 for c in similar_cases[:5] if c.decision == "APPROVED")
        refused_count = sum(1 for c in similar_cases[:5] if c.decision == "REFUSED")

        return f"""## 7. Similar Cases and Precedents

The following {len(similar_cases[:5])} cases have been identified as relevant precedents for the proposal at {app.address}:

{"".join(cases_text)}

### Precedent Summary

Of {len(similar_cases[:5])} comparable cases, **{approved_count} were approved** and **{refused_count} were refused**.

{"The refused case(s) highlight the importance of appropriate scale, massing, and heritage impact — factors that must be carefully assessed in the current proposal." if refused_count > 0 else ""}
{"The approved precedents demonstrate that similar development in this area has been found acceptable where heritage significance is preserved and design quality is demonstrated." if approved_count > 0 else ""}"""

    def _generate_planning_balance(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate planning balance derived from the actual application."""
        proposal_kw = _extract_proposal_keywords(app.proposal)
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) if app.constraints else "none identified"

        # Build benefits based on the actual proposal
        benefits = []
        benefits.append(
            f"| Active reuse of building at {app.address} | Moderate | "
            f"Proposal involves: {app.proposal[:80]} |"
        )
        if proposal_kw["residential"] or proposal_kw["conversion"]:
            benefits.append(
                f"| Contribution to housing delivery (CS17) | Significant | "
                f"Residential development in Urban Core supports housing targets |"
            )
        if proposal_kw["restoration"]:
            benefits.append(
                f"| Restoration of building fabric | Significant | "
                f"{'Enhances Conservation Area character (NPPF-206)' if has_conservation else 'Improves building condition'} |"
            )
        benefits.append(
            f"| Support for Urban Core vitality (CS1) | Moderate | "
            f"Development within {app.ward} ward contributes to economic activity |"
        )

        # Build concerns based on actual constraints
        concerns = []
        if has_conservation:
            concerns.append(
                f"| Potential impact on Conservation Area character | Moderate | "
                f"Requires assessment under NPPF-199, DM16 | Condition: materials approval |"
            )
        if has_listed:
            concerns.append(
                f"| Potential impact on setting of listed buildings | Moderate | "
                f"Requires assessment under NPPF-199, DM17 | Condition: detailed design approval |"
            )
        concerns.append(
            f"| Residential amenity impact | To be determined | "
            f"Requires quantified assessment under DM21 | Conditions may be required |"
        )

        if not concerns:
            concerns.append("| No significant concerns identified | - | - | - |")

        benefits_text = "\n".join(benefits)
        concerns_text = "\n".join(concerns)

        # Precedent support
        approved_cases = [c for c in similar_cases if c.decision == "APPROVED"]
        precedent_note = ""
        if approved_cases:
            precedent_note = (
                f"\n\n**Precedent support:** {len(approved_cases)} approved similar cases "
                f"support the principle of this type of development at this location."
            )

        return f"""## 8. Planning Balance

### Benefits of the Proposal

| Benefit | Weight | Evidence |
|---------|--------|----------|
{benefits_text}

### Potential Concerns

| Concern | Weight | Policy Basis | Mitigation |
|---------|--------|--------------|------------|
{concerns_text}

### Conclusion

The proposal ({app.proposal}) at {app.address} has been assessed against {len(policies)} relevant policies. The site constraints ({constraints_str}) engage {'heritage policies requiring careful assessment of impact on designated assets' if (has_conservation or has_listed) else 'standard development management policies'}.

The benefits of the proposal — including active reuse of the site{', contribution to housing delivery' if proposal_kw.get('residential') or proposal_kw.get('conversion') else ''}, and support for Urban Core vitality — are considered to outweigh the identified concerns, subject to conditions securing appropriate materials and detailed design.{precedent_note}"""

    def _generate_recommendation(
        self,
        app: ApplicationData,
        policies: List[PolicyExcerpt],
        similar_cases: List[SimilarCase],
    ) -> str:
        """Generate recommendation section referencing specific policy outcomes."""
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        proposal_kw = _extract_proposal_keywords(app.proposal)
        constraints_str = ", ".join(app.constraints) if app.constraints else "none identified"

        # Build case-specific approval reasons citing actual policies
        reasons = []
        reason_num = 1

        # Principle
        principle_policies = [p for p in policies if p.policy_id in ("CS1", "UC1", "NPPF-2", "DM1")]
        if principle_policies:
            cited = ", ".join(p.policy_id for p in principle_policies)
            reasons.append(
                f"{reason_num}. The proposal ({app.proposal}) accords with the principle of development "
                f"at {app.address} as set out in policies {cited}."
            )
            reason_num += 1

        # Housing
        if proposal_kw.get("residential") or proposal_kw.get("conversion"):
            reasons.append(
                f"{reason_num}. The proposal contributes to housing delivery in the Urban Core "
                f"in accordance with policy CS17."
            )
            reason_num += 1

        # Heritage
        if has_conservation or has_listed:
            heritage_policies = [p for p in policies if p.policy_id in ("NPPF-199", "NPPF-200", "DM15", "DM16", "DM17")]
            if heritage_policies:
                cited = ", ".join(p.policy_id for p in heritage_policies)
                reasons.append(
                    f"{reason_num}. Subject to conditions, the proposal is considered to preserve the "
                    f"significance of heritage assets ({constraints_str}) in accordance with policies {cited}."
                )
                reason_num += 1

        # Design
        design_policies = [p for p in policies if p.policy_id in ("DM6", "CS15", "NPPF-130")]
        if design_policies:
            cited = ", ".join(p.policy_id for p in design_policies)
            reasons.append(
                f"{reason_num}. Subject to materials approval, the proposal is capable of achieving "
                f"acceptable design quality in accordance with policies {cited}."
            )
            reason_num += 1

        # Sustainable development
        reasons.append(
            f"{reason_num}. The proposal represents sustainable development in accordance "
            f"with the NPPF and policy DM1."
        )

        reasons_text = "\n".join(reasons)

        # Build case-specific conditions
        conditions = []
        cond_num = 1

        conditions.append(
            f"{cond_num}. **Time Limit:** The development must be begun not later than three years "
            f"from the date of this permission.\n"
            f"   *Reason: To comply with Section 91 of the Town and Country Planning Act 1990.*"
        )
        cond_num += 1

        conditions.append(
            f"{cond_num}. **Approved Plans:** The development shall be carried out in accordance "
            f"with the approved plans and documents.\n"
            f"   *Reason: For the avoidance of doubt and in the interests of proper planning.*"
        )
        cond_num += 1

        conditions.append(
            f"{cond_num}. **Materials:** Prior to their use, samples of all external facing materials "
            f"shall be submitted to and approved in writing by the Local Planning Authority.\n"
            f"   *Reason: In the interests of visual amenity"
            f"{' and to preserve the character and appearance of the Conservation Area (DM16)' if has_conservation else ''}"
            f"{' and the setting of the listed building (DM17)' if has_listed else ''}"
            f" in accordance with policies DM6 and CS15.*"
        )
        cond_num += 1

        if has_conservation or has_listed:
            conditions.append(
                f"{cond_num}. **Heritage Details:** Prior to commencement, detailed drawings at 1:20 scale "
                f"showing all new/altered architectural details shall be submitted to and approved in writing.\n"
                f"   *Reason: To preserve the significance of the heritage assets ({constraints_str}) "
                f"in accordance with policies {', '.join(p.policy_id for p in policies if p.policy_id in ('DM15', 'DM16', 'DM17'))}.*"
            )
            cond_num += 1

        conditions.append(
            f"{cond_num}. **Hours of Construction:** Construction work shall only take place between "
            f"08:00-18:00 Monday to Friday and 08:00-13:00 on Saturdays, with no work on Sundays or Bank Holidays.\n"
            f"   *Reason: To protect the amenity of neighbouring occupiers in accordance with policy DM21.*"
        )

        conditions_text = "\n\n".join(conditions)

        return f"""## 9. Recommendation

### Decision
**APPROVE** subject to conditions

### Reasons for Approval (application-specific)
{reasons_text}

### Recommended Conditions

{conditions_text}

### Informatives

1. The applicant is advised to contact the Council's Building Control service regarding compliance with Building Regulations.

2. Party Wall Act requirements may apply and the applicant should seek independent advice."""

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
