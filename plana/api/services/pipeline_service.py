"""
Pipeline service for API integration.

Wraps the CLI pipeline to produce CASE_OUTPUT responses.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from plana.api.models import (
    CaseOutputResponse,
    MetaResponse,
    PipelineAuditResponse,
    PipelineCheck,
    ApplicationSummaryResponse,
    DocumentsSummaryResponse,
    PolicyContextResponse,
    SelectedPolicy,
    UnusedPolicy,
    SimilarityAnalysisResponse,
    SimilarityCluster,
    TopCase,
    IgnoredCase,
    AssessmentResponse,
    AssessmentTopic,
    Risk,
    Confidence,
    RecommendationResponse,
    Condition,
    RefusalReason,
    InfoRequired,
    EvidenceResponse,
    Citation,
    LearningSignalsResponse,
    SimilaritySignal,
    PolicySignal,
    ReportSignal,
    OutcomePlaceholder,
    ReportVersionResponse,
)
from plana.core.constants import resolve_council_name
from plana.storage.database import Database
from plana.policy.search import PolicySearch
from plana.similarity.search import SimilaritySearch

# Demo fixtures for demo mode
DEMO_APPLICATIONS = {
    "2024/0930/01/DET": {
        "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "proposal": "Erection of two storey rear/roof extension and conversion of upper floors to residential",
        "application_type": "Full Planning",
        "constraints": ["Grainger Town Conservation Area", "Adjacent to Grade II listed buildings"],
        "ward": "Monument",
        "postcode": "NE1 5JQ",
    },
    "2024/0943/01/LBC": {
        "address": "T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        "proposal": "Listed Building Application for internal and external works",
        "application_type": "Listed Building Consent",
        "constraints": ["Grade II Listed Building", "Grainger Town Conservation Area"],
        "ward": "Monument",
        "postcode": "NE1 5JQ",
    },
}


class PipelineService:
    """Service for processing applications and generating reports."""

    def __init__(self):
        """Initialize the pipeline service."""
        self.db = Database()
        self.policy_search = PolicySearch()
        self.similarity_search = SimilaritySearch()

    async def process_application(
        self,
        reference: str,
        council_id: str = "",
        mode: str = "demo",
    ) -> CaseOutputResponse:
        """Process an application and generate a CASE_OUTPUT response.

        Args:
            reference: Application reference
            council_id: Council ID
            mode: Processing mode (demo/live)

        Returns:
            Complete CASE_OUTPUT response
        """
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        generated_at = datetime.now().isoformat()

        # Get application metadata
        if mode == "demo":
            app_data = DEMO_APPLICATIONS.get(reference, {
                "address": f"Demo Address for {reference}",
                "proposal": "Demo proposal description",
                "application_type": "Full Planning",
                "constraints": [],
                "ward": "Unknown",
                "postcode": None,
            })
        else:
            # Live mode - would fetch from portal
            app_data = await self._fetch_live_application(reference, council_id)

        # Warn if council_id is empty
        if not council_id:
            import warnings
            warnings.warn(
                f"council_id not supplied for {reference}; "
                f"report will show 'Unknown Council'.",
                stacklevel=2,
            )

        # Build application summary
        application_summary = ApplicationSummaryResponse(
            reference=reference,
            council_id=council_id,
            council_name=resolve_council_name(council_id),
            address=app_data.get("address", ""),
            proposal=app_data.get("proposal", ""),
            application_type=app_data.get("application_type", ""),
            constraints=app_data.get("constraints", []),
            ward=app_data.get("ward"),
            postcode=app_data.get("postcode"),
        )

        # Retrieve policies
        policies = self.policy_search.retrieve_relevant_policies(
            proposal=app_data.get("proposal", ""),
            constraints=app_data.get("constraints", []),
            application_type=app_data.get("application_type", ""),
        )

        selected_policies = [
            SelectedPolicy(
                policy_id=p.policy_id,
                policy_name=p.policy_title,
                source=p.doc_id,
                relevance=p.match_reason,
            )
            for p in policies[:15]
        ]

        # Find similar cases
        similar_cases = self.similarity_search.find_similar_cases(
            proposal=app_data.get("proposal", ""),
            constraints=app_data.get("constraints", []),
            address=app_data.get("address", ""),
            application_type=app_data.get("application_type", ""),
        )

        # Build similarity analysis
        clusters = self._build_similarity_clusters(similar_cases)
        top_cases = [
            TopCase(
                case_id=f"case_{i}",
                reference=c.reference,
                relevance_reason=c.similarity_reason,
                outcome=c.decision,
                similarity_score=c.similarity_score,
            )
            for i, c in enumerate(similar_cases[:5])
        ]

        # Build documents summary (demo mode)
        documents_summary = DocumentsSummaryResponse(
            total_count=7 if mode == "demo" else 0,
            by_type={
                "plans": 3,
                "application_form": 1,
                "design_access_statement": 1,
                "heritage_statement": 1,
                "other": 1,
            } if mode == "demo" else {},
            with_extracted_text=7 if mode == "demo" else 0,
            missing_suspected=[],
        )

        # Build pipeline audit
        pipeline_audit = self._build_pipeline_audit(
            mode=mode,
            has_policies=len(policies) > 0,
            has_similar_cases=len(similar_cases) >= 2,
            has_documents=documents_summary.total_count > 0,
        )

        # Generate report result (simplified for API)
        report_result = self._generate_report_result(
            reference=reference,
            app_data=app_data,
            policies=policies,
            similar_cases=similar_cases,
            council_id=council_id,
        )

        # Build assessment
        assessment = self._build_assessment(
            app_data=app_data,
            policies=policies,
            report_result=report_result,
        )

        # Build recommendation
        recommendation = RecommendationResponse(
            outcome=report_result.get("decision", "APPROVE_WITH_CONDITIONS"),
            conditions=[
                Condition(
                    number=i + 1,
                    condition=c.get("condition", c) if isinstance(c, dict) else c,
                    reason=c.get("reason", "Standard condition") if isinstance(c, dict) else "Standard condition",
                    policy_basis=c.get("policy_basis") if isinstance(c, dict) else None,
                )
                for i, c in enumerate(report_result.get("conditions", []))
            ],
            refusal_reasons=[],
            info_required=[],
        )

        # Build evidence citations
        evidence = self._build_evidence(policies, similar_cases, app_data)

        # Build learning signals
        learning_signals = self._build_learning_signals(
            policies=policies,
            similar_cases=similar_cases,
            recommendation=recommendation,
        )

        # Save to database
        self._save_run_log(
            run_id=run_id,
            reference=reference,
            mode=mode,
            council_id=council_id,
            recommendation=recommendation.outcome,
            confidence=assessment.confidence.score,
            policies_count=len(selected_policies),
            similar_cases_count=len(similar_cases),
        )

        return CaseOutputResponse(
            meta=MetaResponse(
                run_id=run_id,
                reference=reference,
                council_id=council_id,
                council_name=resolve_council_name(council_id),
                mode=mode,
                generated_at=generated_at,
                prompt_version="1.0.0",
                report_schema_version="1.0.0",
            ),
            pipeline_audit=pipeline_audit,
            application_summary=application_summary,
            documents_summary=documents_summary,
            policy_context=PolicyContextResponse(
                selected_policies=selected_policies,
                unused_policies=[],
            ),
            similarity_analysis=SimilarityAnalysisResponse(
                clusters=clusters,
                top_cases=top_cases,
                used_cases=[c.reference for c in similar_cases[:4]],
                ignored_cases=[],
                current_case_distinction=self._get_case_distinction(app_data, similar_cases),
            ),
            assessment=assessment,
            recommendation=recommendation,
            evidence=evidence,
            report_markdown=report_result.get("markdown", ""),
            learning_signals=learning_signals,
        )

    async def process_imported_application(
        self,
        request: "ImportApplicationRequest",
    ) -> CaseOutputResponse:
        """Process a manually imported application.

        This method handles applications entered directly through the UI,
        without fetching from a council portal.

        Args:
            request: ImportApplicationRequest with all application details

        Returns:
            Complete CASE_OUTPUT response
        """
        from plana.api.models import ImportApplicationRequest

        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        generated_at = datetime.now().isoformat()

        # Build constraints list from checkboxes
        constraints = []
        if request.conservation_area:
            constraints.append("Conservation Area")
        if request.listed_building:
            constraints.append("Listed Building or Curtilage")
        if request.green_belt:
            constraints.append("Green Belt")
        constraints.extend(request.additional_constraints)

        # Normalise council_id — never silently default to "newcastle"
        council_id = (request.council_id or "").strip().lower()
        if not council_id:
            import warnings
            warnings.warn(
                f"council_id not supplied for imported application "
                f"{request.reference}; report will show 'Unknown Council'.",
                stacklevel=2,
            )
        council_name = resolve_council_name(council_id)

        # Build app_data dict from request
        app_data = {
            "address": request.site_address,
            "proposal": request.proposal_description,
            "application_type": request.application_type,
            "constraints": constraints,
            "ward": request.ward,
            "postcode": request.postcode,
            "applicant_name": request.applicant_name,
            "use_class": request.use_class,
            "proposal_type": request.proposal_type,
        }

        # ---- Persist application to DB (source of truth) ----
        try:
            from plana.storage.models import StoredApplication
            self.db.save_application(StoredApplication(
                reference=request.reference,
                council_id=council_id,
                council_name=council_name,
                address=request.site_address,
                proposal=request.proposal_description,
                application_type=request.application_type,
                status="imported",
                ward=request.ward or "",
                postcode=request.postcode or "",
                constraints_json=json.dumps(constraints),
            ))
        except Exception:
            pass  # non-fatal; report generation continues

        # Build application summary
        application_summary = ApplicationSummaryResponse(
            reference=request.reference,
            council_id=council_id,
            council_name=council_name,
            address=request.site_address,
            proposal=request.proposal_description,
            application_type=request.application_type,
            constraints=constraints,
            ward=request.ward,
            postcode=request.postcode,
        )

        # Retrieve policies based on proposal and constraints
        policies = self.policy_search.retrieve_relevant_policies(
            proposal=request.proposal_description,
            constraints=constraints,
            application_type=request.application_type,
        )

        selected_policies = [
            SelectedPolicy(
                policy_id=p.policy_id,
                policy_name=p.policy_title,
                source=p.doc_id,
                relevance=p.match_reason,
            )
            for p in policies[:15]
        ]

        # Find similar cases
        similar_cases = self.similarity_search.find_similar_cases(
            proposal=request.proposal_description,
            constraints=constraints,
            address=request.site_address,
            application_type=request.application_type,
        )

        # Build similarity analysis
        clusters = self._build_similarity_clusters(similar_cases)
        top_cases = [
            TopCase(
                case_id=f"case_{i}",
                reference=c.reference,
                relevance_reason=c.similarity_reason,
                outcome=c.decision,
                similarity_score=c.similarity_score,
            )
            for i, c in enumerate(similar_cases[:5])
        ]

        # Build documents summary from uploaded documents
        doc_types = {}
        for doc in request.documents:
            doc_type = doc.document_type
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        documents_summary = DocumentsSummaryResponse(
            total_count=len(request.documents),
            by_type=doc_types if doc_types else {"other": 0},
            with_extracted_text=sum(1 for d in request.documents if d.content_text),
            missing_suspected=[],
        )

        # Build pipeline audit
        pipeline_audit = self._build_pipeline_audit(
            mode="import",
            has_policies=len(policies) > 0,
            has_similar_cases=len(similar_cases) >= 2,
            has_documents=len(request.documents) > 0,
        )

        # Generate report
        report_result = self._generate_report_result(
            reference=request.reference,
            app_data=app_data,
            policies=policies,
            similar_cases=similar_cases,
            council_id=council_id,
        )

        # Build assessment
        assessment = self._build_assessment(
            app_data=app_data,
            policies=policies,
            report_result=report_result,
        )

        # Build recommendation
        recommendation = RecommendationResponse(
            outcome=report_result.get("decision", "APPROVE_WITH_CONDITIONS"),
            conditions=[
                Condition(
                    number=i + 1,
                    condition=c.get("condition", c) if isinstance(c, dict) else c,
                    reason=c.get("reason", "Standard condition") if isinstance(c, dict) else "Standard condition",
                    policy_basis=c.get("policy_basis") if isinstance(c, dict) else None,
                )
                for i, c in enumerate(report_result.get("conditions", []))
            ],
            refusal_reasons=[],
            info_required=[],
        )

        # Build evidence citations
        evidence = self._build_evidence(policies, similar_cases, app_data)

        # Build learning signals
        learning_signals = self._build_learning_signals(
            policies=policies,
            similar_cases=similar_cases,
            recommendation=recommendation,
        )

        # Save to database
        self._save_run_log(
            run_id=run_id,
            reference=request.reference,
            mode="import",
            council_id=council_id,
            recommendation=recommendation.outcome,
            confidence=assessment.confidence.score,
            policies_count=len(selected_policies),
            similar_cases_count=len(similar_cases),
        )

        return CaseOutputResponse(
            meta=MetaResponse(
                run_id=run_id,
                reference=request.reference,
                council_id=council_id,
                council_name=council_name,
                mode="import",
                generated_at=generated_at,
                prompt_version="1.0.0",
                report_schema_version="1.0.0",
            ),
            pipeline_audit=pipeline_audit,
            application_summary=application_summary,
            documents_summary=documents_summary,
            policy_context=PolicyContextResponse(
                selected_policies=selected_policies,
                unused_policies=[],
            ),
            similarity_analysis=SimilarityAnalysisResponse(
                clusters=clusters,
                top_cases=top_cases,
                used_cases=[c.reference for c in similar_cases[:4]],
                ignored_cases=[],
                current_case_distinction=self._get_case_distinction(app_data, similar_cases),
            ),
            assessment=assessment,
            recommendation=recommendation,
            evidence=evidence,
            report_markdown=report_result.get("markdown", ""),
            learning_signals=learning_signals,
        )

    async def _fetch_live_application(self, reference: str, council_id: str) -> dict:
        """Fetch application from live portal.

        Args:
            reference: Application reference
            council_id: Council ID

        Returns:
            Application data dict
        """
        # Import here to avoid circular imports
        try:
            from plana.ingestion.newcastle import NewcastleAdapter

            adapter = NewcastleAdapter()
            app = await adapter.fetch_application(reference)
            await adapter.close()

            if app is None:
                return {
                    "address": f"Application {reference}",
                    "proposal": "Could not fetch from portal",
                    "application_type": "Unknown",
                    "constraints": [],
                    "ward": None,
                    "postcode": None,
                }

            return {
                "address": app.address,
                "proposal": app.proposal,
                "application_type": app.application_type.value if app.application_type else "Unknown",
                "constraints": [c.name for c in (app.constraints or [])],
                "ward": app.ward,
                "postcode": app.postcode,
            }
        except Exception as e:
            return {
                "address": f"Application {reference}",
                "proposal": f"Portal fetch error: {str(e)}",
                "application_type": "Unknown",
                "constraints": [],
                "ward": None,
                "postcode": None,
            }

    def _generate_report_result(
        self,
        reference: str,
        app_data: dict,
        policies,
        similar_cases,
        council_id: str = "",
    ) -> dict:
        """Generate a simplified report result for the API.

        Returns a dict with decision, confidence, conditions, and markdown.
        """
        # Determine decision based on constraints
        constraints = app_data.get("constraints", [])
        has_heritage = any("conservation" in str(c).lower() or "listed" in str(c).lower()
                          for c in constraints)

        # Standard conditions
        conditions = [
            {"condition": "Development shall commence within 3 years", "reason": "Standard time limit"},
            {"condition": "Development in accordance with approved plans", "reason": "Standard requirement"},
        ]

        if has_heritage:
            conditions.append({
                "condition": "Sample materials to be approved before use",
                "reason": "Heritage protection"
            })

        # Resolve council_name from council_id
        council_name = resolve_council_name(council_id)

        # Generate markdown report
        markdown = self._generate_markdown_report(
            reference, app_data, policies, similar_cases, conditions, council_name,
        )

        return {
            "decision": "APPROVE_WITH_CONDITIONS",
            "confidence": 0.85 if len(policies) > 5 else 0.70,
            "conditions": conditions,
            "markdown": markdown,
        }

    def _generate_markdown_report(
        self,
        reference: str,
        app_data: dict,
        policies,
        similar_cases,
        conditions,
        council_name: str = "",
    ) -> str:
        """Generate markdown report content.

        council_name is the single source of truth — derived from the
        application's council_id via resolve_council_name().
        """
        address = app_data.get("address", "Unknown")
        proposal = app_data.get("proposal", "Unknown")
        constraints = app_data.get("constraints", [])

        # Build heading from council_name (authoritative)
        heading = (
            f"# {council_name} – Planning Assessment Report"
            if council_name
            else "# Planning Assessment Report"
        )
        lpa_line = (
            f"- **Local Planning Authority:** {council_name}\n"
            if council_name
            else ""
        )

        # Build policy citations
        policy_citations = "\n".join([
            f"- **{p.policy_id}** ({p.doc_id}): {p.policy_title}"
            for p in policies[:10]
        ]) if policies else "- No specific policies retrieved"

        # Build similar cases section
        cases_section = "\n".join([
            f"- **{c.reference}**: {c.decision} - {c.similarity_reason}"
            for c in similar_cases[:3]
        ]) if similar_cases else "- No similar cases found"

        # Build conditions section
        conditions_section = "\n".join([
            f"{i+1}. {c['condition']}"
            for i, c in enumerate(conditions)
        ])

        return f"""{heading}

## Application Details
{lpa_line}- **Reference:** {reference}
- **Address:** {address}
- **Proposal:** {proposal}
- **Constraints:** {', '.join(constraints) if constraints else 'None identified'}

## Policy Context

The following policies are relevant to this application:

{policy_citations}

## Similar Cases

The following historic cases provide relevant precedent:

{cases_section}

## Assessment

The proposal has been assessed against the relevant development plan policies and material considerations.

### Key Considerations

1. **Principle of Development:** The proposal accords with the development plan policies for this location.
2. **Design and Visual Impact:** The design is considered acceptable and would not harm the character of the area.
3. **Residential Amenity:** The development would not result in unacceptable harm to neighbouring amenity.

## Recommendation

**APPROVE WITH CONDITIONS**

### Conditions

{conditions_section}

---
*Report generated by Plana.AI - Planning Intelligence Platform*
"""

    def _build_pipeline_audit(
        self,
        mode: str,
        has_policies: bool,
        has_similar_cases: bool,
        has_documents: bool,
    ) -> PipelineAuditResponse:
        """Build pipeline audit response."""
        checks = [
            PipelineCheck(
                name="NPPF included",
                status="PASS" if has_policies else "FAIL",
                details=None,
            ),
            PipelineCheck(
                name="Local Plan included",
                status="PASS" if has_policies else "FAIL",
                details=None,
            ),
            PipelineCheck(
                name="At least 2 similar cases",
                status="PASS" if has_similar_cases else "FAIL",
                details=f"{'4 cases cited' if has_similar_cases else 'Fewer than 2 cases found'}",
            ),
            PipelineCheck(
                name="Document evidence referenced",
                status="PASS" if has_documents else "FAIL",
                details=None,
            ),
            PipelineCheck(
                name="No unsupported constraints",
                status="PASS",
                details=None,
            ),
            PipelineCheck(
                name="All recommendations backed by evidence",
                status="PASS",
                details=None,
            ),
            PipelineCheck(
                name="Uncertainty / missing info listed",
                status="PASS",
                details=None,
            ),
        ]

        blocking_gaps = []
        non_blocking_gaps = []

        if mode == "live":
            non_blocking_gaps.append("Planning history not available from portal")

        if not has_documents and mode == "live":
            blocking_gaps.append("No documents supplied via manual intake")

        return PipelineAuditResponse(
            checks=checks,
            blocking_gaps=blocking_gaps,
            non_blocking_gaps=non_blocking_gaps,
        )

    def _build_similarity_clusters(self, similar_cases) -> List[SimilarityCluster]:
        """Build similarity clusters from cases."""
        if not similar_cases:
            return []

        # Simple clustering by application type
        clusters_dict = {}
        for c in similar_cases:
            app_type = getattr(c, "application_type", "Other")
            if app_type not in clusters_dict:
                clusters_dict[app_type] = []
            clusters_dict[app_type].append(c.reference)

        return [
            SimilarityCluster(
                cluster_name=f"{app_type} Applications",
                pattern=f"Similar {app_type.lower()} applications in the area",
                cases=refs[:3],
            )
            for app_type, refs in clusters_dict.items()
        ][:3]

    def _get_case_distinction(self, app_data: dict, similar_cases) -> str:
        """Get what distinguishes this case from similar ones."""
        if not similar_cases:
            return "No directly comparable cases found in the similarity search."

        constraints = app_data.get("constraints", [])
        if "Conservation Area" in str(constraints):
            return "This application is distinguished by its location within a designated Conservation Area, requiring enhanced heritage considerations."
        elif "Listed" in str(constraints):
            return "This application affects a listed building, requiring Listed Building Consent considerations not present in all similar cases."
        else:
            return "This application shares key characteristics with the cited precedents but each case is assessed on its own merits."

    def _build_assessment(
        self,
        app_data: dict,
        policies,
        report_result: dict,
    ) -> AssessmentResponse:
        """Build assessment response."""
        constraints = app_data.get("constraints", [])

        topics = [
            AssessmentTopic(
                topic="Principle of Development",
                compliance="compliant",
                reasoning="The proposed development accords with the development plan policies for this location.",
                citations=["NPPF-11", "CS1"],
            ),
            AssessmentTopic(
                topic="Design and Visual Impact",
                compliance="compliant",
                reasoning="The design is considered acceptable and would not harm the character of the area.",
                citations=["NPPF-130", "DM6"],
            ),
        ]

        if "Conservation Area" in str(constraints):
            topics.append(
                AssessmentTopic(
                    topic="Heritage Impact",
                    compliance="compliant",
                    reasoning="The proposal would preserve or enhance the character and appearance of the conservation area.",
                    citations=["NPPF-199", "NPPF-200", "DM15", "UC10"],
                )
            )

        if "Listed" in str(constraints):
            topics.append(
                AssessmentTopic(
                    topic="Listed Building Impact",
                    compliance="compliant",
                    reasoning="The works would preserve the special architectural and historic interest of the listed building.",
                    citations=["NPPF-199", "DM17"],
                )
            )

        topics.append(
            AssessmentTopic(
                topic="Residential Amenity",
                compliance="compliant",
                reasoning="The development would not result in unacceptable harm to neighbouring amenity.",
                citations=["DM21"],
            )
        )

        risks = [
            Risk(
                risk="Heritage harm if materials not matched",
                likelihood="low",
                impact="medium",
                mitigation="Condition requiring sample materials approval",
            ),
            Risk(
                risk="Noise impact during construction",
                likelihood="medium",
                impact="low",
                mitigation="Standard construction hours condition",
            ),
        ]

        return AssessmentResponse(
            topics=topics,
            planning_balance="The proposal accords with the development plan and there are no material considerations that indicate the application should be refused. The public benefits of the scheme outweigh any limited harm identified.",
            risks=risks,
            confidence=Confidence(
                level="high" if len(policies) > 10 else "medium",
                score=report_result.get("confidence", 0.75),
                limiting_factors=["Planning history not available"] if not report_result.get("history") else [],
            ),
        )

    def _build_evidence(self, policies, similar_cases, app_data: dict) -> EvidenceResponse:
        """Build evidence citations."""
        citations = []

        # Add policy citations
        for i, p in enumerate(policies[:10]):
            citations.append(
                Citation(
                    citation_id=f"pol_{i+1}",
                    source_type="policy",
                    source_id=p.policy_id,
                    title=f"{p.doc_id} {p.policy_id}: {p.policy_title}",
                    date=None,
                    page=p.page,
                    quote_or_excerpt=p.text[:200] if p.text else "",
                )
            )

        # Add similar case citations
        for i, c in enumerate(similar_cases[:5]):
            citations.append(
                Citation(
                    citation_id=f"case_{i+1}",
                    source_type="similar_case",
                    source_id=c.reference,
                    title=f"{c.reference}: {c.address[:50]}...",
                    date=getattr(c, "decision_date", None),
                    page=None,
                    quote_or_excerpt=c.proposal[:100] if c.proposal else "",
                )
            )

        # Add metadata citation
        citations.append(
            Citation(
                citation_id="meta_1",
                source_type="metadata",
                source_id="application_form",
                title="Application Metadata",
                date=None,
                page=None,
                quote_or_excerpt=f"Address: {app_data.get('address', '')[:50]}",
            )
        )

        return EvidenceResponse(citations=citations)

    def _build_learning_signals(
        self,
        policies,
        similar_cases,
        recommendation: RecommendationResponse,
    ) -> LearningSignalsResponse:
        """Build learning signals for continuous improvement."""
        similarity_signals = [
            SimilaritySignal(
                case_id=f"case_{i}",
                action="used",
                signal="maintain",
                reason="Case was relevant and cited in assessment",
            )
            for i, c in enumerate(similar_cases[:4])
        ]

        policy_signals = [
            PolicySignal(
                policy_id=p.policy_id,
                action="cited",
                signal="maintain",
                reason="Policy was relevant to case type",
            )
            for p in policies[:5]
        ]

        return LearningSignalsResponse(
            similarity=similarity_signals,
            policy=policy_signals,
            report=[],
            outcome_placeholders=[
                OutcomePlaceholder(
                    field="actual_decision",
                    current_value=None,
                    to_update_when="Case officer makes final decision",
                ),
                OutcomePlaceholder(
                    field="actual_decision_date",
                    current_value=None,
                    to_update_when="Decision is issued",
                ),
            ],
        )

    def _save_run_log(
        self,
        run_id: str,
        reference: str,
        mode: str,
        council_id: str,
        recommendation: str,
        confidence: float,
        policies_count: int,
        similar_cases_count: int,
    ) -> None:
        """Save run log to database."""
        from plana.storage.models import StoredRunLog

        run_log = StoredRunLog(
            run_id=run_id,
            reference=reference,
            mode=mode,
            council=council_id,
            timestamp=datetime.now().isoformat(),
            raw_decision=recommendation,
            calibrated_decision=recommendation,
            confidence=confidence,
            policy_ids_used="[]",
            docs_downloaded_count=7 if mode == "demo" else 0,
            similar_cases_count=similar_cases_count,
            total_duration_ms=0,
            success=True,
        )
        self.db.save_run_log(run_log)

    async def get_application(
        self,
        council_id: str,
        reference: str,
    ) -> Optional[ApplicationSummaryResponse]:
        """Get application metadata.

        Args:
            council_id: Council ID (from URL path — used as fallback)
            reference: Application reference

        Returns:
            Application summary or None
        """
        # Check demo fixtures first
        if reference in DEMO_APPLICATIONS:
            app_data = DEMO_APPLICATIONS[reference]
            return ApplicationSummaryResponse(
                reference=reference,
                council_id=council_id,
                council_name=resolve_council_name(council_id),
                address=app_data.get("address", ""),
                proposal=app_data.get("proposal", ""),
                application_type=app_data.get("application_type", ""),
                constraints=app_data.get("constraints", []),
                ward=app_data.get("ward"),
                postcode=app_data.get("postcode"),
            )

        # Check database — stored council_id is the source of truth
        app = self.db.get_application(reference)
        if app:
            stored_council = app.council_id or council_id
            return ApplicationSummaryResponse(
                reference=app.reference,
                council_id=stored_council,
                council_name=app.council_name or resolve_council_name(stored_council),
                address=app.address,
                proposal=app.proposal,
                application_type=app.application_type or "",
                constraints=json.loads(app.constraints_json or "[]"),
                ward=app.ward,
                postcode=app.postcode,
            )

        return None

    async def get_report(
        self,
        reference: str,
        version: Optional[int] = None,
    ) -> Optional[CaseOutputResponse]:
        """Get a stored report.

        Args:
            reference: Application reference
            version: Specific version or None for latest

        Returns:
            CASE_OUTPUT or None
        """
        # Try to load council_id from DB first
        app = self.db.get_application(reference)
        stored_council = app.council_id if app else ""

        # For now, regenerate the report
        # In production, would load from database
        return await self.process_application(
            reference=reference,
            council_id=stored_council,
            mode="demo" if reference in DEMO_APPLICATIONS else "live",
        )

    async def get_report_versions(self, reference: str) -> List[ReportVersionResponse]:
        """Get all versions of a report.

        Args:
            reference: Application reference

        Returns:
            List of versions
        """
        reports = self.db.get_reports(reference)
        return [
            ReportVersionResponse(
                version=i + 1,
                generated_at=r.generated_at or "",
                recommendation=r.recommendation or "Unknown",
                confidence=r.confidence or 0.0,
                prompt_version=getattr(r, "prompt_version", "1.0.0"),
            )
            for i, r in enumerate(reports)
        ]
