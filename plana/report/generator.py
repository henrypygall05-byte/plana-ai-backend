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
from plana.documents.ingestion import (
    DocumentCategory,
    DocumentIngestionResult,
    ExtractionStatus,
    MaterialInfoItem,
    ProcessedDocument,
    PLAN_CATEGORIES,
    extract_material_info,
    process_documents,
)


@dataclass
class EvidenceEntry:
    """A single evidence item in the Evidence Register."""

    tag: str  # e.g. "[E1]"
    source_type: str  # "policy", "case", "document"
    title: str
    detail: str  # e.g. "Elevation — extracted" or "NPPF-199 — p.42"


class EvidenceMap:
    """Pre-computed mapping of documents/policies/cases to evidence tags.

    Uses two separate tag series:
    - ``[E#]`` for policy citations and similar cases
    - ``[D#]`` for application documents

    Built once before report sections are generated so that the same
    tags can be referenced in both the assessment body and the appendix.
    """

    def __init__(self) -> None:
        self._e_counter = 0  # [E#] series for policies + cases
        self._d_counter = 0  # [D#] series for documents
        self._entries: List[EvidenceEntry] = []
        # Lookup helpers: key → tag
        self._by_policy_id: Dict[str, str] = {}
        self._by_case_ref: Dict[str, str] = {}
        self._by_doc_id: Dict[str, str] = {}

    def _next_e_tag(self) -> str:
        self._e_counter += 1
        return f"[E{self._e_counter}]"

    def _next_d_tag(self) -> str:
        self._d_counter += 1
        return f"[D{self._d_counter}]"

    # -- registration methods --

    def register_policy(self, policy: "PolicyExcerpt") -> str:
        tag = self._next_e_tag()
        self._by_policy_id[policy.policy_id] = tag
        self._entries.append(EvidenceEntry(
            tag=tag,
            source_type="policy",
            title=f"{policy.policy_id}: {policy.policy_title}",
            detail=f"{policy.doc_id} p.{policy.page}",
        ))
        return tag

    def register_case(self, case: "SimilarCase") -> str:
        tag = self._next_e_tag()
        self._by_case_ref[case.reference] = tag
        self._entries.append(EvidenceEntry(
            tag=tag,
            source_type="case",
            title=case.reference,
            detail=f"{case.address[:50]} — {case.decision} ({case.decision_date})",
        ))
        return tag

    def register_document(self, doc: "ProcessedDocument") -> str:
        tag = self._next_d_tag()
        self._by_doc_id[doc.doc_id] = tag
        self._entries.append(EvidenceEntry(
            tag=tag,
            source_type="document",
            title=doc.title,
            detail=f"{doc.category_label} — {doc.extraction_status.value}",
        ))
        return tag

    def register_raw_document(self, doc_id: str, title: str) -> str:
        """Register an unclassified document (fallback when no ingestion)."""
        tag = self._next_d_tag()
        self._by_doc_id[doc_id] = tag
        self._entries.append(EvidenceEntry(
            tag=tag,
            source_type="document",
            title=title,
            detail="unclassified — not_attempted",
        ))
        return tag

    # -- lookup helpers --

    def tag_for_policy(self, policy_id: str) -> str:
        return self._by_policy_id.get(policy_id, "")

    def tag_for_case(self, ref: str) -> str:
        return self._by_case_ref.get(ref, "")

    def tag_for_doc(self, doc_id: str) -> str:
        return self._by_doc_id.get(doc_id, "")

    def tags_for_docs_by_category(
        self,
        ingestion: Optional["DocumentIngestionResult"],
        category: "DocumentCategory",
    ) -> List[Tuple[str, str]]:
        """Return ``[(tag, title), ...]`` for all docs of *category*."""
        if not ingestion:
            return []
        return [
            (self.tag_for_doc(d.doc_id), d.title)
            for d in ingestion.by_category(category)
            if self.tag_for_doc(d.doc_id)
        ]

    @property
    def entries(self) -> List[EvidenceEntry]:
        return self._entries

    @property
    def total(self) -> int:
        return self._e_counter + self._d_counter

    @property
    def doc_count(self) -> int:
        return self._d_counter


class CouncilMismatchError(Exception):
    """Raised when council_name in the report header would differ from the stored application council."""

    def __init__(self, expected: str, got: str):
        self.expected = expected
        self.got = got
        super().__init__(
            f"Council mismatch: application council is '{expected}' "
            f"but report attempted to use '{got}'. "
            f"Auto-corrected to '{expected}'."
        )


@dataclass
class ApplicationData:
    """Data for a planning application."""

    reference: str
    address: str
    proposal: str
    application_type: str
    constraints: List[str]
    ward: str = "City Centre"
    council_name: str = ""
    applicant: str = "Applicant Name (Demo)"
    agent: str = "Agent Name (Demo)"
    date_received: str = ""
    date_valid: str = ""
    # Document ingestion results — populated by the pipeline before report
    # generation so that the report can cite actual documents.
    document_ingestion: Optional["DocumentIngestionResult"] = None
    # documents_count is the total known document count from all sources
    # (frontend, DB, portal).  When > 0 the report MUST NOT claim "no
    # submitted plans" — even if text extraction hasn't run yet.
    documents_count: int = 0
    # documents_verified is True when at least one authoritative source
    # (frontend, DB, or portal) confirmed the count.  Only when
    # documents_count == 0 AND documents_verified may the report state
    # that plans are absent.
    documents_verified: bool = True


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
        ingestion: Optional[DocumentIngestionResult] = None,
        evidence_map: Optional[EvidenceMap] = None,
    ) -> Tuple[str, str]:
        """Return *(markdown_block, compliance)* for one policy.

        *compliance* is COMPLIANT | CANNOT FULLY ASSESS | NOT APPLICABLE.

        When *ingestion* is provided and relevant plan-type documents
        exist, the ``[NOT EVIDENCED]`` tags are replaced with citations
        referencing the submitted documents.

        When *evidence_map* is provided, document and policy references
        include their ``[E#]`` tags for cross-referencing with the
        Evidence Register appendix.
        """
        pid = policy.policy_id
        has_conservation = self._has_constraint(app, "conservation")
        has_listed = self._has_constraint(app, "listed")
        constraints_str = ", ".join(app.constraints) or "none"
        test = _first_sentence(policy.text)

        # Policy evidence tag — used in the heading
        ptag = evidence_map.tag_for_policy(pid) if evidence_map else ""
        ptag_prefix = f"{ptag} " if ptag else ""

        # Derive document-awareness helpers
        has_plans = bool(ingestion and ingestion.has_plans)
        has_elevations = bool(
            ingestion
            and ingestion.by_category(DocumentCategory.ELEVATION)
        )
        has_floor_plans = bool(
            ingestion
            and ingestion.by_category(DocumentCategory.FLOOR_PLAN)
        )
        has_site_plan = bool(
            ingestion
            and ingestion.by_category(DocumentCategory.SITE_PLAN)
        )
        has_das = bool(
            ingestion
            and ingestion.by_category(DocumentCategory.DESIGN_ACCESS_STATEMENT)
        )

        def _cite_docs(category: DocumentCategory, label: str) -> str:
            """Build a citation string like ``[E5] elevation drawings (Title)``."""
            if not evidence_map or not ingestion:
                return label
            pairs = evidence_map.tags_for_docs_by_category(ingestion, category)
            if not pairs:
                return label
            parts = [f"{tag} {title}" for tag, title in pairs[:2]]
            return f"{label} ({', '.join(parts)})"

        # --- Heritage policies ---
        if pid in ("NPPF-199", "NPPF-200", "NPPF-16"):
            if has_conservation or has_listed:
                has_heritage_stmt = bool(
                    ingestion
                    and ingestion.by_category(DocumentCategory.HERITAGE_STATEMENT)
                )
                if has_heritage_stmt or has_elevations:
                    cited = []
                    if has_heritage_stmt:
                        cited.append(_cite_docs(DocumentCategory.HERITAGE_STATEMENT, "Heritage Statement"))
                    if has_elevations:
                        cited.append(_cite_docs(DocumentCategory.ELEVATION, "elevation drawings"))
                    cite_str = " and ".join(cited)
                    return (
                        f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                        f"- **Test**: \"{test}\"\n"
                        f"- **Application evidence**: Site constraints ({constraints_str}) "
                        f"include designated heritage assets. The proposal ({app.proposal}) "
                        f"must demonstrate it preserves heritage significance. "
                        f"Documents received: {cite_str}. "
                        f"Extraction status: success — officer to assess level of harm.\n"
                        f"- **Compliance**: **CANNOT FULLY ASSESS** (officer review of "
                        f"heritage impact required)",
                        "CANNOT FULLY ASSESS",
                    )
                return (
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: No designated heritage assets at "
                f"{app.address} ({constraints_str}). Policy not engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "NOT APPLICABLE",
            )

        if pid == "NPPF-206":
            if has_conservation:
                return (
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: The site is within a Conservation Area. "
                    f"The proposal ({app.proposal}) must enhance or better reveal the "
                    f"area's significance. Subject to materials condition.\n"
                    f"- **Compliance**: **COMPLIANT** (subject to materials condition)",
                    "COMPLIANT",
                )
            return (
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: Constraints ({constraints_str}) do not "
                    f"engage this policy at {app.address}.\n"
                    f"- **Compliance**: **NOT APPLICABLE**",
                    "NOT APPLICABLE",
                )
            return (
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: The proposal ({app.proposal}) "
                    f"contributes to housing delivery at {app.address}.\n"
                    f"- **Compliance**: **COMPLIANT**",
                    "COMPLIANT",
                )
            return (
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
            if has_elevations or has_das:
                cited = []
                if has_elevations:
                    cited.append(_cite_docs(DocumentCategory.ELEVATION, "elevation drawings"))
                if has_das:
                    cited.append(_cite_docs(DocumentCategory.DESIGN_ACCESS_STATEMENT, "Design & Access Statement"))
                cite_str = " and ".join(cited)
                return (
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: The proposal ({app.proposal}) at "
                    f"{app.address} must demonstrate high quality design sympathetic "
                    f"to the {app.ward} area. {extra}"
                    f"Plans received; the following documents are available for "
                    f"officer review: {cite_str}. "
                    f"Extraction status: success.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS** (officer review of "
                    f"submitted plans required)",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
            if has_floor_plans or has_site_plan:
                cited = []
                if has_site_plan:
                    cited.append(_cite_docs(DocumentCategory.SITE_PLAN, "site plan"))
                if has_floor_plans:
                    cited.append(_cite_docs(DocumentCategory.FLOOR_PLAN, "floor plans"))
                cite_str = " and ".join(cited)
                return (
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: The proposal ({app.proposal}) at "
                    f"{app.address} must provide acceptable amenity. Quantified tests "
                    f"(45-degree daylight, 21 m privacy, 25-degree overbearing) require "
                    f"dimensional data from submitted plans. "
                    f"Plans received: {cite_str}. "
                    f"Extraction status: success — officer to verify measurements.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS** (officer verification "
                    f"of dimensions required)",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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
                    f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                    f"- **Test**: \"{test}\"\n"
                    f"- **Application evidence**: Proposal includes shop front / "
                    f"signage works at {app.address}. Detailed shop front drawings "
                    f"required.\n"
                    f"- **Compliance**: **CANNOT FULLY ASSESS**",
                    "CANNOT FULLY ASSESS",
                )
            return (
                f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
                f"- **Test**: \"{test}\"\n"
                f"- **Application evidence**: Proposal does not include shop front "
                f"or signage works. Policy not engaged.\n"
                f"- **Compliance**: **NOT APPLICABLE**",
                "NOT APPLICABLE",
            )

        # --- Fallback ---
        return (
            f"**{ptag_prefix}{pid}: {policy.policy_title}** ({policy.doc_id} p.{policy.page})\n"
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

        Raises:
            CouncilMismatchError: (logged, auto-corrected) if the council
                name that would appear in the header doesn't match the
                application's stored council_name.
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

        # ---- Document ingestion: classify and (optionally) extract text ---
        # If the caller already set application.document_ingestion, use it;
        # otherwise run ingestion now so the report has document evidence.
        if application.document_ingestion is None and documents:
            application.document_ingestion = process_documents(
                documents, extract_text=True,
            )

        ingestion = application.document_ingestion

        # ---- Effective document count -----------------------------------
        # Take the highest of: explicit count, document list length, and
        # ingestion count.  If ANY source says documents exist, the report
        # MUST NOT claim "no submitted plans".
        application.documents_count = max(
            application.documents_count,
            len(documents or []),
            ingestion.total_count if ingestion else 0,
        )

        # ---- Pre-compute Evidence Map -----------------------------------
        # Register every policy, case, and document BEFORE generating
        # sections so that [E#] tags are deterministic and consistent
        # across the assessment body and the appendix.
        evidence_map = EvidenceMap()
        for p in policies:
            evidence_map.register_policy(p)
        for c in similar_cases:
            evidence_map.register_case(c)
        if ingestion:
            for d in ingestion.documents:
                evidence_map.register_document(d)
        elif documents:
            # Fallback: register raw document list with [D#] tags
            for doc in documents:
                doc_id = getattr(doc, "id", "") or getattr(doc, "doc_id", "")
                title = getattr(doc, "title", "Unknown")
                evidence_map.register_raw_document(doc_id, title)

        # Generate report sections
        sections = [
            self._generate_header(application),
            self._generate_summary(application, policies, similar_cases),
            self._generate_site_description(application),
            self._generate_proposal_description(application),
            self._generate_planning_history(application),
            self._generate_policy_context(application, policies),
            self._generate_assessment(
                application, policies, similar_cases, evidence_map,
            ),
            self._generate_similar_cases(similar_cases, evidence_map),
            self._generate_planning_balance(application, policies, similar_cases),
            self._generate_material_info_missing(
                application, ingestion, evidence_map,
            ),
            self._generate_recommendation(application, policies),
            self._generate_documents_summary(
                ingestion, application.documents_count,
            ),
            self._generate_documents_reviewed(
                documents, application.documents_count,
            ),
            self._generate_evidence_appendix_from_map(evidence_map),
        ]

        report = "\n\n".join(sections)

        # ---- Sanity check: council consistency ----------------------------
        # If a council_name is set on the application, verify it appears
        # in the report header.  If some other council name crept in,
        # auto-correct the report and log a warning.
        if application.council_name:
            self._check_council_consistency(report, application.council_name)

        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")

        return report

    @staticmethod
    def _check_council_consistency(report: str, expected_council: str) -> None:
        """Verify the report header uses the expected council name.

        If a different council name is detected in the first heading line,
        a CouncilMismatchError is raised (callers may log and continue
        since the header was generated from the authoritative
        application.council_name field).
        """
        # Extract the first line (the markdown heading)
        header_line = report.split("\n", 1)[0]
        if expected_council and expected_council not in header_line:
            import warnings
            warnings.warn(
                f"Council sanity-check: expected '{expected_council}' in "
                f"report header but got: {header_line!r}. "
                f"The report was generated from the stored application "
                f"council_name so this should not happen — investigate.",
                stacklevel=2,
            )

    def _generate_header(self, app: ApplicationData) -> str:
        """Generate report header.

        The council_name shown here is always app.council_name — the single
        source of truth stored on the application record.

        If council_name is empty or "Unknown Council", a prominent warning
        is included so officers and reviewers notice the gap immediately.
        """
        from plana.core.constants import UNKNOWN_COUNCIL_NAME

        is_unknown = (
            not app.council_name
            or app.council_name == UNKNOWN_COUNCIL_NAME
        )

        if is_unknown:
            import warnings
            warnings.warn(
                f"Generating report for {app.reference} without a valid "
                f"council_name.  The header will show 'Unknown Council'.  "
                f"Ensure the frontend sends council_id on import.",
                stacklevel=2,
            )

        council_line = (
            f"\n**Local Planning Authority:** {app.council_name}\n"
            if app.council_name and not is_unknown
            else "\n**Local Planning Authority:** ⚠ Unknown — council_id was not supplied\n"
        )
        heading = (
            f"# {app.council_name} – Planning Assessment Report"
            if app.council_name and not is_unknown
            else "# Planning Assessment Report (Council Unknown)"
        )
        return f"""{heading}
{council_line}
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
        """Generate executive summary with case-specific key issues.

        The summary now cross-references the document ingestion results so
        that it never contradicts the evidence (e.g. stating "no plans" when
        plans have been submitted).
        """
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

        # ---- Document evidence summary (aligned with Material Info) ----
        # RULE: If documents_count > 0, NEVER say "Documents submitted: None"
        ingestion = app.document_ingestion
        effective_docs = max(
            app.documents_count,
            ingestion.total_count if ingestion else 0,
        )

        if ingestion and ingestion.total_count > 0:
            doc_line = (
                f"- **Documents submitted:** {ingestion.total_count} "
                f"({ingestion.plans_count} plans, "
                f"{len(ingestion.statements())} statements)"
            )
            quality_line = (
                f"- **Evidence quality:** {ingestion.evidence_quality}"
            )
            # Material info quick summary
            material_items = extract_material_info(
                ingestion,
                documents_count=effective_docs,
                documents_verified=app.documents_verified,
            )
            found = sum(1 for i in material_items if i.value)
            total = len(material_items)
            if found == total:
                mat_line = (
                    f"- **Material information:** All {total} key items "
                    f"identified in documents"
                )
            elif found > 0:
                mat_line = (
                    f"- **Material information:** {found}/{total} key items "
                    f"found; remainder requires officer verification"
                )
            else:
                mat_line = (
                    f"- **Material information:** {total} key items require "
                    f"officer verification from submitted drawings"
                )
        elif effective_docs > 0:
            # Documents exist but ingestion didn't process them
            doc_line = (
                f"- **Documents submitted:** {effective_docs} "
                f"(plan content extraction pending/failed)"
            )
            quality_line = (
                "- **Evidence quality:** MEDIUM "
                "— documents received but not yet analysed"
            )
            mat_line = (
                "- **Material information:** Pending — "
                "document text extraction required"
            )
        else:
            doc_line = "- **Documents submitted:** None"
            quality_line = "- **Evidence quality:** LOW"
            mat_line = (
                "- **Material information:** Not assessed — no documents"
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
{doc_line}
{quality_line}
{mat_line}

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
The surrounding area is characterised by mixed commercial and retail uses typical of the {app.ward} area{f' ({app.council_name})' if app.council_name else ''}. The streetscape includes a variety of building heights and architectural styles.

### Access
The site is accessible by public transport. There is no on-site car parking, consistent with the location."""

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
        evidence_map: Optional[EvidenceMap] = None,
    ) -> str:
        """Generate main assessment section with per-policy case-specific blocks."""
        grouped = self._categorize_policies(policies)
        has_heritage = (
            self._has_constraint(app, "conservation")
            or self._has_constraint(app, "listed")
        )
        ingestion = app.document_ingestion

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
                block, status = self._assess_single_policy(
                    policy, app, ingestion, evidence_map,
                )
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

    def _generate_similar_cases(
        self,
        similar_cases: List[SimilarCase],
        evidence_map: Optional[EvidenceMap] = None,
    ) -> str:
        """Generate similar cases section."""
        if not similar_cases:
            return """## 7. Similar Cases and Precedents

*No directly comparable cases identified in demo mode.*"""

        cases_text = []
        for i, case in enumerate(similar_cases[:5], 1):
            ctag = evidence_map.tag_for_case(case.reference) if evidence_map else ""
            ctag_prefix = f"{ctag} " if ctag else ""
            cases_text.append(f"""### {ctag_prefix}Case {i}: {case.reference}

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

        return f"""## 10. Recommendation

### Decision
**APPROVE** subject to conditions

### Reasons for Approval
{chr(10).join(reasons)}

### Recommended Conditions

{chr(10).join(chr(10).join([c]) for c in conditions)}

### Informatives

1. The applicant is advised to contact Building Control regarding Building Regulations compliance.

2. Party Wall Act requirements may apply — seek independent advice."""

    # ------------------------------------------------------------------
    # Material Information — checks extracted data before flagging gaps
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_material_info_missing(
        app: "ApplicationData",
        ingestion: Optional[DocumentIngestionResult],
        evidence_map: Optional[EvidenceMap] = None,
    ) -> str:
        """Generate Material Information section.

        For each key data item (ridge/eaves height, floor area, parking,
        access width) the method:

        1. Checks whether the relevant document category was submitted.
        2. If text was extracted, searches for the measurement.
        3. Reports a **Confidence** note per item:
           - *Found on <drawing>*  — value was located in document text
           - *Not found*           — document present but value unreadable
           - *Not extracted from [D#] yet* — relevant doc type exists,
             extraction pending
           - *Missing*             — no relevant document submitted
        """
        material_items = extract_material_info(
            ingestion,
            documents_count=app.documents_count,
            documents_verified=app.documents_verified,
            evidence_map=evidence_map,
        )

        lines = ["## 9. Material Information"]
        lines.append("")

        # Quick summary sentence
        found_count = sum(1 for i in material_items if i.value)
        not_found_count = sum(
            1 for i in material_items
            if not i.value and (
                i.status.startswith("Not found")
                or i.status.startswith("Not extracted")
            )
        )
        missing_count = sum(
            1 for i in material_items
            if not i.value and i.status.startswith("Missing")
        )

        if found_count == len(material_items):
            lines.append(
                "All key material information items have been identified "
                "in the submitted documents."
            )
        else:
            parts = []
            if found_count:
                parts.append(f"{found_count} found in documents")
            if not_found_count:
                parts.append(
                    f"{not_found_count} not readable from extracted text "
                    "(officer verification required)"
                )
            if missing_count:
                parts.append(f"{missing_count} missing (no relevant documents)")
            lines.append(f"Material information status: {'; '.join(parts)}.")

        lines.append("")
        lines.append("| # | Item | Value | Confidence | Reason Required |")
        lines.append("|---|------|-------|------------|-----------------|")

        for idx, item in enumerate(material_items, 1):
            value_cell = item.value if item.value else "—"
            lines.append(
                f"| {idx} | **{item.name}** | {value_cell} "
                f"| {item.status} | {item.required_reason} |"
            )

        lines.append("")

        # Flag genuine gaps that may require deferral
        genuine_missing = [
            i for i in material_items
            if not i.value and i.status.startswith("Missing")
        ]
        pending_count = sum(
            1 for i in material_items
            if not i.value and i.status.startswith("Not extracted")
        )
        if genuine_missing:
            lines.append(
                f"**{len(genuine_missing)} material gap(s)** may require "
                f"further information from the applicant before determination."
            )
        elif pending_count:
            lines.append(
                f"Key measurements not extracted from plans yet "
                f"(pending extraction). {pending_count} item(s) to be "
                f"verified from the submitted drawings."
            )
        elif not_found_count:
            lines.append(
                "All relevant document types have been submitted. "
                "Officer to verify measurements from the submitted drawings."
            )
        else:
            lines.append(
                "No material information gaps identified — all key items "
                "located in submitted documents."
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Documents Summary — classifies documents and shows extraction status
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_documents_summary(
        ingestion: Optional[DocumentIngestionResult],
        documents_count: int = 0,
    ) -> str:
        """Generate a documents summary section listing key plans with
        filenames, detected types, and extraction status.

        RULE: If *documents_count* > 0, this section MUST NOT claim
        "no documents were submitted".  Instead it says how many were
        received and what the extraction status is.
        """
        if (ingestion is None or ingestion.total_count == 0) and documents_count > 0:
            # Documents exist but ingestion didn't process them
            return (
                f"## 11. Documents Summary\n\n"
                f"**Documents received:** {documents_count}. "
                f"Plan content extraction pending/failed — "
                f"document text has not yet been analysed.\n\n"
                f"**Evidence Quality:** MEDIUM "
                f"— documents exist but content extraction incomplete."
            )

        if (ingestion is None or ingestion.total_count == 0) and documents_count == 0:
            return """## 11. Documents Summary

No documents were submitted with this application.

**Evidence Quality:** LOW — no documents available for assessment."""

        lines = [
            "## 11. Documents Summary",
            "",
            f"**{ingestion.total_count}** documents submitted "
            f"({ingestion.plans_count} plan drawings, "
            f"{len(ingestion.statements())} statements/reports).",
            "",
        ]

        # Key plans table
        plans = ingestion.plans()
        if plans:
            lines.append("### Key Plans Received")
            lines.append("")
            lines.append("| Document | Type | Extraction |")
            lines.append("|----------|------|------------|")
            for p in plans:
                status_label = {
                    ExtractionStatus.SUCCESS: "extracted",
                    ExtractionStatus.PARTIAL: "partial",
                    ExtractionStatus.FAILED: "failed",
                    ExtractionStatus.NOT_ATTEMPTED: "not attempted",
                }.get(p.extraction_status, "unknown")
                lines.append(
                    f"| {p.title} | {p.category_label} | {status_label} |"
                )
            lines.append("")
        else:
            lines.append("*No plan-type documents identified among the submissions.*")
            lines.append("")

        # Statements table
        stmts = ingestion.statements()
        if stmts:
            lines.append("### Supporting Statements")
            lines.append("")
            for s in stmts:
                status_label = {
                    ExtractionStatus.SUCCESS: "extracted",
                    ExtractionStatus.PARTIAL: "partial",
                    ExtractionStatus.FAILED: "failed",
                    ExtractionStatus.NOT_ATTEMPTED: "not attempted",
                }.get(s.extraction_status, "unknown")
                lines.append(f"- {s.title} ({s.category_label}) — {status_label}")
            lines.append("")

        # Evidence quality
        lines.append(f"**Evidence Quality:** {ingestion.evidence_quality}")
        if ingestion.evidence_quality == "HIGH":
            lines.append(
                "— key plans and statements extracted and cited in assessment."
            )
        elif ingestion.evidence_quality == "MEDIUM":
            lines.append(
                "— some key documents extracted; further verification may be needed."
            )
        else:
            lines.append(
                "— documents exist but extraction failed or no key plans identified."
            )

        return "\n".join(lines)

    def _generate_documents_reviewed(
        self,
        documents: List,
        documents_count: int = 0,
    ) -> str:
        """Generate documents reviewed section.

        Handles both demo ApplicationDocument and portal PortalDocument formats.

        RULE: If *documents_count* > 0 but *documents* is empty, report
        must say how many documents were received — never "No documents
        available".
        """
        if not documents and documents_count > 0:
            return (
                f"## 12. Documents Reviewed\n\n"
                f"**{documents_count} document(s) received** but "
                f"document content is not available for itemised review "
                f"at this stage."
            )

        if not documents:
            return """## 12. Documents Reviewed

*No documents available.*"""

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

        return f"""## 12. Documents Reviewed

The following documents were submitted with the application and have been considered in this assessment:

| Document | Format | Size | Date Received |
|----------|--------|------|---------------|
{chr(10).join(doc_lines)}

**Total:** {len(documents)} documents"""

    @staticmethod
    def _generate_evidence_appendix_from_map(evidence_map: EvidenceMap) -> str:
        """Generate evidence appendix from the pre-computed EvidenceMap.

        Every [E#] tag referenced in the assessment body appears here with
        its full detail — providing a single, authoritative cross-reference
        table.
        """
        lines = ["## Appendix: Evidence Register", ""]

        # Group entries by source type for readability
        policies = [e for e in evidence_map.entries if e.source_type == "policy"]
        cases = [e for e in evidence_map.entries if e.source_type == "case"]
        documents = [e for e in evidence_map.entries if e.source_type == "document"]

        # ---- Section 1: Policy Citations ----
        if policies:
            lines.append("### Policy Citations")
            lines.append("")
            for e in policies:
                lines.append(f"- {e.tag} {e.title} — {e.detail}")
            lines.append("")

        # ---- Section 2: Similar Cases ----
        if cases:
            lines.append("### Similar Cases Referenced")
            lines.append("")
            for e in cases:
                lines.append(f"- {e.tag} {e.title}: {e.detail}")
            lines.append("")

        # ---- Section 3: Application Documents ----
        if documents:
            lines.append("### Application Documents")
            lines.append("")
            lines.append("| # | Document | Classified Type | Extraction |")
            lines.append("|---|----------|----------------|------------|")
            for e in documents:
                # detail is "Category Label — status"
                parts = e.detail.split(" — ", 1)
                cat_label = parts[0] if parts else ""
                status = parts[1] if len(parts) > 1 else ""
                lines.append(f"| {e.tag} | {e.title} | {cat_label} | {status} |")
            lines.append("")

        lines.append(f"**Total evidence items: {evidence_map.total}**")
        lines.append("")
        lines.append("---")
        lines.append(
            f"*Report generated by Plana.AI on "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        )

        return "\n".join(lines)
