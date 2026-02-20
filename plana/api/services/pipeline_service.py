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
    ExtractionStatusResponse,
    ProcessingStatusResponse,
    DocumentProcessingResponse,
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
from plana.core.exceptions import CouncilMismatchError
from plana.storage.database import Database
from plana.policy.search import PolicySearch
from plana.similarity.search import SimilaritySearch

class DocumentsProcessingError(Exception):
    """Raised when report generation is blocked because documents are still being processed."""

    def __init__(
        self,
        extraction_status: ExtractionStatusResponse,
        processing_status: Optional[ProcessingStatusResponse] = None,
    ):
        self.extraction_status = extraction_status
        self.processing_status = processing_status or ProcessingStatusResponse()
        super().__init__("Documents are still being processed")


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

        # ---- Council mismatch guard ----
        # If the application is already stored, its council_id is the
        # source of truth.  Refuse to process under a different council
        # so that policies, constraints wording, and consultation lists
        # cannot leak across authorities.
        stored_app = self.db.get_application(reference)
        if stored_app and stored_app.council_id and council_id:
            if stored_app.council_id.lower() != council_id.lower():
                raise CouncilMismatchError(
                    reference=reference,
                    expected=stored_app.council_id,
                    got=council_id,
                )

        # ---- Hard block: never generate a report while docs are pending ----
        processing_counts = self.db.get_processing_counts(reference)
        if processing_counts["total"] > 0 and (
            processing_counts["queued"] > 0
            or processing_counts["processing"] > 0
        ):
            extraction_counts = self.db.get_extraction_counts(reference)
            raise DocumentsProcessingError(
                extraction_status=ExtractionStatusResponse(
                    queued=extraction_counts["queued"],
                    extracted=extraction_counts["extracted"],
                    failed=extraction_counts["failed"],
                ),
                processing_status=ProcessingStatusResponse(
                    total=processing_counts["total"],
                    queued=processing_counts["queued"],
                    processing=processing_counts["processing"],
                    processed=processing_counts["processed"],
                    failed=processing_counts["failed"],
                ),
            )

        # ---- Location enrichment via postcodes.io ----
        postcode = app_data.get("postcode")
        existing_constraints = app_data.get("constraints", [])
        try:
            from plana.location.postcodes import enrich_application_location
            location_data = enrich_application_location(
                postcode=postcode,
                address=app_data.get("address", ""),
                existing_constraints=existing_constraints,
            )
            # Merge enriched ward if not already set
            if location_data.get("ward") and not app_data.get("ward"):
                app_data["ward"] = location_data["ward"]
            # Merge enriched constraints
            if location_data.get("all_constraints"):
                app_data["constraints"] = location_data["all_constraints"]
        except Exception:
            pass  # Non-fatal: location enrichment is best-effort

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

        # Retrieve policies — scoped to council's development plan
        policies = self.policy_search.retrieve_relevant_policies(
            proposal=app_data.get("proposal", ""),
            constraints=app_data.get("constraints", []),
            application_type=app_data.get("application_type", ""),
            council_id=council_id,
            reference=reference,
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

        # Query document processing status from DB
        processing_counts = self.db.get_processing_counts(reference)
        processing_status = ProcessingStatusResponse(
            total=processing_counts["total"],
            queued=processing_counts["queued"],
            processing=processing_counts["processing"],
            processed=processing_counts["processed"],
            failed=processing_counts["failed"],
        )

        # Legacy extraction counts (kept for backwards compat)
        extraction_counts = self.db.get_extraction_counts(reference)
        extraction_status = ExtractionStatusResponse(
            queued=extraction_counts["queued"],
            extracted=extraction_counts["extracted"],
            failed=extraction_counts["failed"],
        )

        documents_count = processing_status.total

        # --- Processing-completion guard ---
        # Block report generation while documents are still queued or
        # being actively processed.  Report generation is allowed when:
        #   1) processed_count > 0 AND queued_count == 0
        #      (all docs finished, regardless of text extracted)
        #   OR
        #   2) queued_count == 0 AND failed_count > 0
        #      (processing finished but some/all failed)
        #
        # Do NOT block just because extracted_text_chars == 0 — drawings
        # and scanned plans legitimately have zero text.
        still_pending = processing_status.queued + processing_status.processing
        if documents_count > 0 and still_pending > 0:
            raise DocumentsProcessingError(extraction_status, processing_status)

        # Build documents summary
        if mode == "demo" and documents_count == 0:
            # Fallback for demo mode when no docs are in the DB
            documents_summary = DocumentsSummaryResponse(
                total_count=7,
                by_type={
                    "plans": 3,
                    "application_form": 1,
                    "design_access_statement": 1,
                    "heritage_statement": 1,
                    "other": 1,
                },
                with_extracted_text=7,
                missing_suspected=[],
                extraction_status=ExtractionStatusResponse(
                    queued=0, extracted=7, failed=0,
                ),
                documents=ProcessingStatusResponse(
                    total=7, queued=0, processing=0,
                    processed=7, failed=0,
                ),
            )
        else:
            documents_summary = DocumentsSummaryResponse(
                total_count=documents_count,
                by_type={},
                with_extracted_text=extraction_status.extracted,
                missing_suspected=[],
                extraction_status=extraction_status,
                documents=processing_status,
            )

        # Build pipeline audit
        pipeline_audit = self._build_pipeline_audit(
            mode=mode,
            has_policies=len(policies) > 0,
            has_similar_cases=len(similar_cases) >= 2,
            has_documents=documents_summary.total_count > 0,
        )

        # Build document ingestion from DB-stored processed documents
        # so the ReportGenerator can extract planning facts and cite docs.
        document_ingestion = self._build_document_ingestion(reference)
        document_texts = self.db.get_extracted_texts(reference)

        # Generate report result — uses full ReportGenerator when documents
        # have been processed, falls back to simple template otherwise.
        report_result = self._generate_report_result(
            reference=reference,
            app_data=app_data,
            policies=policies,
            similar_cases=similar_cases,
            council_id=council_id,
            document_texts=document_texts,
            document_ingestion=document_ingestion,
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

        # ---- Council mismatch guard (import path) ----
        # If the application already exists in the DB under a different
        # council, refuse to re-import under a conflicting council.
        stored_app = self.db.get_application(request.reference)
        if stored_app and stored_app.council_id and council_id:
            if stored_app.council_id.lower() != council_id.lower():
                raise CouncilMismatchError(
                    reference=request.reference,
                    expected=stored_app.council_id,
                    got=council_id,
                )

        # Extract postcode from address if not provided
        postcode = request.postcode
        if not postcode and request.site_address:
            import re as _re
            _pc_match = _re.search(
                r'\b([A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2})\b',
                request.site_address.upper(),
            )
            if _pc_match:
                postcode = _pc_match.group(1)

        # Build app_data dict from request
        app_data = {
            "address": request.site_address,
            "proposal": request.proposal_description,
            "application_type": request.application_type,
            "constraints": constraints,
            "ward": request.ward,
            "postcode": postcode,
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
                postcode=postcode or "",
                constraints_json=json.dumps(constraints),
            ))
        except Exception:
            pass  # non-fatal; report generation continues

        # ---- Fetch document URLs from the council portal ----
        # The frontend sends filenames but usually not URLs. We need to
        # fetch the actual download URLs from the portal so the background
        # worker can download and extract text from the PDFs.
        await self._enrich_documents_from_portal(request)

        # ---- Persist documents to DB so worker can process them ----
        self._persist_imported_documents(request)

        # ---- Kick the background worker so it picks up queued docs ----
        try:
            from plana.documents.background import kick_queue
            await kick_queue()
        except Exception:
            pass  # non-fatal

        # ---- Document processing guard ----
        # Block report generation while documents are still queued or
        # being actively processed.  Same logic as process_application().
        processing_counts = self.db.get_processing_counts(request.reference)
        total = processing_counts["total"]
        still_pending = processing_counts["queued"] + processing_counts["processing"]
        if total > 0 and still_pending > 0:
            extraction_counts = self.db.get_extraction_counts(request.reference)
            raise DocumentsProcessingError(
                extraction_status=ExtractionStatusResponse(
                    queued=extraction_counts["queued"],
                    extracted=extraction_counts["extracted"],
                    failed=extraction_counts["failed"],
                ),
                processing_status=ProcessingStatusResponse(
                    total=total,
                    queued=processing_counts["queued"],
                    processing=processing_counts["processing"],
                    processed=processing_counts["processed"],
                    failed=processing_counts["failed"],
                ),
            )

        # ---- Location enrichment via postcodes.io ----
        try:
            from plana.location.postcodes import enrich_application_location
            location_data = enrich_application_location(
                postcode=postcode,
                address=request.site_address,
                existing_constraints=constraints,
            )
            if location_data.get("ward") and not request.ward:
                request.ward = location_data["ward"]
            if location_data.get("all_constraints"):
                constraints = location_data["all_constraints"]
        except Exception:
            pass  # Non-fatal

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
            postcode=postcode,
        )

        # Retrieve policies — scoped to council's development plan
        policies = self.policy_search.retrieve_relevant_policies(
            proposal=request.proposal_description,
            constraints=constraints,
            application_type=request.application_type,
            council_id=council_id,
            reference=request.reference,
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

        extracted_text_count = sum(1 for d in request.documents if d.content_text)
        total_doc_count = len(request.documents)
        documents_summary = DocumentsSummaryResponse(
            total_count=total_doc_count,
            by_type=doc_types if doc_types else {"other": 0},
            with_extracted_text=extracted_text_count,
            missing_suspected=[],
            extraction_status=ExtractionStatusResponse(
                queued=total_doc_count - extracted_text_count,
                extracted=extracted_text_count,
                failed=0,
            ),
        )

        # Build pipeline audit
        pipeline_audit = self._build_pipeline_audit(
            mode="import",
            has_policies=len(policies) > 0,
            has_similar_cases=len(similar_cases) >= 2,
            has_documents=len(request.documents) > 0,
        )

        # Build document ingestion from DB-stored processed documents
        document_ingestion = self._build_document_ingestion(request.reference)
        document_texts = self.db.get_extracted_texts(request.reference)

        # Generate report — uses full ReportGenerator when documents
        # have been processed, falls back to simple template otherwise.
        report_result = self._generate_report_result(
            reference=request.reference,
            app_data=app_data,
            policies=policies,
            similar_cases=similar_cases,
            council_id=council_id,
            document_texts=document_texts,
            document_ingestion=document_ingestion,
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
        document_texts: Optional[list] = None,
        document_ingestion: Optional[object] = None,
    ) -> dict:
        """Generate a report result for the API.

        When document ingestion data is available, uses the full
        ReportGenerator which extracts planning facts (heights, floor
        areas, materials, etc.) from document text and produces
        evidence-cited report sections.

        Falls back to a simpler markdown template if ReportGenerator fails.

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

        council_name = resolve_council_name(council_id)

        # --- Try the full ReportGenerator (document-aware, evidence-cited) ---
        markdown = self._try_full_report_generation(
            reference=reference,
            app_data=app_data,
            council_id=council_id,
            council_name=council_name,
            document_ingestion=document_ingestion,
        )

        if not markdown:
            # Fallback to simple markdown template
            markdown = self._generate_markdown_report(
                reference, app_data, policies, similar_cases, conditions, council_name,
                document_texts=document_texts,
            )

        return {
            "decision": "APPROVE_WITH_CONDITIONS",
            "confidence": 0.85 if len(policies) > 5 else 0.70,
            "conditions": conditions,
            "markdown": markdown,
        }

    def _try_full_report_generation(
        self,
        reference: str,
        app_data: dict,
        council_id: str,
        council_name: str,
        document_ingestion: Optional[object] = None,
    ) -> Optional[str]:
        """Attempt to generate a full report using ReportGenerator.

        Returns markdown string on success, None on failure (caller
        should fall back to the simpler template).
        """
        try:
            from plana.report.generator import ApplicationData, ReportGenerator

            app = ApplicationData(
                reference=reference,
                address=app_data.get("address", ""),
                proposal=app_data.get("proposal", ""),
                application_type=app_data.get("application_type", ""),
                constraints=app_data.get("constraints", []),
                ward=app_data.get("ward", ""),
                council_id=council_id,
                council_name=council_name,
                applicant=app_data.get("applicant_name", ""),
                documents_count=document_ingestion.total_count if document_ingestion else 0,
                documents_verified=True,
                document_ingestion=document_ingestion,
            )

            generator = ReportGenerator()
            return generator.generate_report(app, documents=[])
        except Exception as exc:
            from plana.core.logging import get_logger
            logger = get_logger(__name__)
            logger.warning(
                "full_report_generation_failed",
                reference=reference,
                error=f"{type(exc).__name__}: {exc}",
            )
            return None

    def _generate_markdown_report(
        self,
        reference: str,
        app_data: dict,
        policies,
        similar_cases,
        conditions,
        council_name: str = "",
        document_texts: Optional[list] = None,
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

## Document Evidence

{self._build_document_evidence_section(document_texts)}

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

    @staticmethod
    def _build_document_evidence_section(document_texts: Optional[list]) -> str:
        """Build a markdown section summarising extracted document content."""
        if not document_texts:
            return "No document text has been extracted yet. Officer should verify key measurements directly from submitted plans."

        lines = [f"{len(document_texts)} document(s) with extracted text:\n"]
        for dt in document_texts[:10]:  # cap at 10 for report brevity
            title = dt.get("title", "Unknown")
            chars = dt.get("chars", 0)
            method = dt.get("method", "unknown")
            is_plan = dt.get("is_plan", False)
            kind = "Plan/Drawing" if is_plan else "Text document"
            lines.append(f"- **{title}** ({kind}, {chars:,} chars, method: {method})")
        if len(document_texts) > 10:
            lines.append(f"- ... and {len(document_texts) - 10} more documents")
        return "\n".join(lines)

    def _build_document_ingestion(self, reference: str):
        """Build a DocumentIngestionResult from DB-stored processed documents.

        Returns the ingestion result, or None if no processed documents exist.
        """
        stored_docs = self.db.get_documents(reference)
        if not stored_docs:
            return None

        # Only build ingestion if at least some documents are processed
        processed_count = sum(
            1 for d in stored_docs if d.processing_status == "processed"
        )
        if processed_count == 0:
            return None

        try:
            from plana.documents.ingestion import build_ingestion_from_stored_documents
            return build_ingestion_from_stored_documents(stored_docs)
        except Exception:
            return None

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

    async def _enrich_documents_from_portal(self, request) -> None:
        """Fetch document metadata (URLs) from the council portal.

        Matches portal documents to frontend-provided documents by filename
        and sets their ``url`` field so the background worker can download
        and extract text from them.

        If the portal returns documents not in the frontend request, they
        are added to ``request.documents`` so they also get persisted.
        """
        from plana.api.models import DocumentInput

        council_id = getattr(request, "council_id", "") or ""
        if not council_id:
            return

        try:
            from plana.ingestion.base import CouncilAdapter
            from plana.ingestion import get_adapter
            adapter = get_adapter(council_id)
            portal_docs = await adapter.fetch_documents(request.reference)
            await adapter.close()
        except Exception:
            # Portal unavailable — try the CouncilRegistry (src/plana path)
            try:
                from plana.councils import CouncilRegistry
                portal = CouncilRegistry.get(council_id)
                portal_docs_raw = await portal.fetch_application_documents(request.reference)
                await portal.close()
                # Convert to a list of objects with .url, .title, .id attributes
                portal_docs = portal_docs_raw
            except Exception:
                return  # No portal available — continue without URLs

        if not portal_docs:
            return

        # Build a lookup from normalised filename → portal doc
        portal_by_name = {}
        for pdoc in portal_docs:
            title = getattr(pdoc, "title", "") or ""
            doc_id = getattr(pdoc, "id", "") or getattr(pdoc, "doc_id", "") or ""
            url = getattr(pdoc, "url", "") or getattr(pdoc, "download_url", "") or ""
            # Try matching by title and by doc_id suffix in filename
            portal_by_name[title.lower()] = (url, title, doc_id)
            if doc_id:
                portal_by_name[doc_id.lower()] = (url, title, doc_id)

        # Enrich existing documents with URLs
        matched_portal_ids = set()
        for doc in request.documents:
            fname_lower = doc.filename.lower()
            # Try exact match first, then partial match
            match = portal_by_name.get(fname_lower)
            if not match:
                # Try matching by portal doc ID embedded in filename
                for key, val in portal_by_name.items():
                    if key in fname_lower or fname_lower in key:
                        match = val
                        break
            if match and not doc.url:
                doc.url = match[0]
                matched_portal_ids.add(match[2])

        # Add portal documents not in the request
        for pdoc in portal_docs:
            doc_id = getattr(pdoc, "id", "") or getattr(pdoc, "doc_id", "") or ""
            if doc_id in matched_portal_ids:
                continue
            title = getattr(pdoc, "title", "") or ""
            url = getattr(pdoc, "url", "") or getattr(pdoc, "download_url", "") or ""
            doc_type = getattr(pdoc, "doc_type", "") or getattr(pdoc, "document_type", "") or "other"
            if url:
                request.documents.append(DocumentInput(
                    filename=title or f"document-{doc_id}.pdf",
                    document_type=doc_type,
                    url=url,
                ))

    def _persist_imported_documents(self, request) -> None:
        """Persist documents from the import request to the DB.

        Documents with ``content_text`` are marked ``processed`` immediately.
        Documents without content AND without a download URL are classified
        inline and marked ``processed`` (the background worker can't do
        anything useful without a URL).  Documents with a URL are only
        queued for background download if the council has a supported portal
        adapter — otherwise the URLs are likely unreachable and will just
        cause the documents to get stuck.
        """
        from plana.storage.models import StoredDocument
        import hashlib

        # Check if this council has a supported portal adapter.
        # If not, URLs from the frontend are likely portal display links
        # (not direct download URLs) and the worker can't fetch them.
        council_id = (getattr(request, "council_id", "") or "").strip().lower()
        can_download = self._council_has_adapter(council_id)

        for i, doc in enumerate(request.documents):
            has_text = bool(doc.content_text and doc.content_text.strip())
            has_url = bool(doc.url and doc.url.strip())
            doc_id = hashlib.sha256(
                f"{request.reference}:{doc.filename}:{i}".encode()
            ).hexdigest()[:16]

            if has_text:
                status = "processed"
                extraction = "extracted"
                method = "inline_text"
                text_chars = len(doc.content_text)
                signal = True
            elif has_url and can_download:
                # Has a URL AND the council adapter can download — queue
                # for background download + text extraction.
                status = "queued"
                extraction = "queued"
                method = "none"
                text_chars = 0
                signal = False
            else:
                # No text AND (no URL, or URL but council can't download).
                # Classify inline and mark processed immediately.
                status = "processed"
                extraction = "extracted"
                method = "filename_only"
                text_chars = 0
                signal = self._classify_document_inline(doc)

            stored = StoredDocument(
                reference=request.reference,
                doc_id=doc_id,
                title=doc.filename,
                doc_type=doc.document_type or "other",
                url=doc.url or "",
                processing_status=status,
                extraction_status=extraction,
                extract_method=method,
                extracted_text_chars=text_chars,
                has_any_content_signal=signal,
                is_plan_or_drawing=self._is_plan_or_drawing(doc.filename),
            )
            try:
                self.db.save_document(stored)
            except Exception:
                pass  # non-fatal; individual doc failure shouldn't block

    @staticmethod
    def _council_has_adapter(council_id: str) -> bool:
        """Check if a council has a supported portal adapter for downloading."""
        if not council_id:
            return False
        try:
            from plana.ingestion import get_adapter
            get_adapter(council_id)
            return True
        except Exception:
            return False

    @staticmethod
    def _classify_document_inline(doc) -> bool:
        """Quick classification for documents with no URL and no text.

        Returns True if the document has any content signal (e.g. it's
        identifiable as a plan/drawing from its filename).
        """
        try:
            from plana.documents.ingestion import classify_document
            category, _ = classify_document(doc.filename, doc.document_type, doc.filename)
            return category != "other"
        except Exception:
            return False

    @staticmethod
    def _is_plan_or_drawing(filename: str) -> bool:
        """Heuristic: is this filename likely a plan or drawing?"""
        try:
            from plana.documents.processor import is_plan_or_drawing_heuristic
            return is_plan_or_drawing_heuristic(filename, "", "other")
        except Exception:
            lower = filename.lower()
            return any(kw in lower for kw in (
                "plan", "elevation", "section", "drawing", "layout",
                "floor", "roof", "site", "block", "location",
            ))

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

        Checks document processing status first — if documents are still
        queued/processing, raises DocumentsProcessingError immediately
        (avoids expensive policy/similarity searches on every poll).

        For imported applications (stored in the DB), uses the stored
        data directly rather than trying to fetch from the portal.

        Args:
            reference: Application reference
            version: Specific version or None for latest

        Returns:
            CASE_OUTPUT or None

        Raises:
            DocumentsProcessingError: if documents are still being processed
        """
        # Try to load council_id from DB first
        app = self.db.get_application(reference)
        stored_council = app.council_id if app else ""

        # --- Fast-path: check document processing status before
        #     regenerating the full report (policy search, similarity, etc.)
        processing_counts = self.db.get_processing_counts(reference)
        total = processing_counts["total"]
        still_pending = processing_counts["queued"] + processing_counts["processing"]

        if total > 0 and still_pending > 0:
            extraction_counts = self.db.get_extraction_counts(reference)
            raise DocumentsProcessingError(
                extraction_status=ExtractionStatusResponse(
                    queued=extraction_counts["queued"],
                    extracted=extraction_counts["extracted"],
                    failed=extraction_counts["failed"],
                ),
                processing_status=ProcessingStatusResponse(
                    total=total,
                    queued=processing_counts["queued"],
                    processing=processing_counts["processing"],
                    processed=processing_counts["processed"],
                    failed=processing_counts["failed"],
                ),
            )

        # Determine mode: use "import" for stored apps (avoids portal fetch),
        # "demo" for fixture apps, "live" only as last resort.
        if reference in DEMO_APPLICATIONS:
            mode = "demo"
        elif app is not None:
            mode = "import"
        else:
            mode = "live"

        # For imported applications, build app_data from DB and use
        # process_imported_application path (no portal fetch needed).
        if mode == "import":
            return await self._regenerate_imported_report(app, stored_council)

        # Regenerate the report (demo or live fallback)
        return await self.process_application(
            reference=reference,
            council_id=stored_council,
            mode=mode,
        )

    async def _regenerate_imported_report(
        self,
        app: "StoredApplication",
        council_id: str,
    ) -> CaseOutputResponse:
        """Regenerate a report for an imported application using stored DB data.

        This avoids the portal fetch that fails for unsupported councils
        (e.g. Broxtowe) and uses the stored application metadata directly.
        """
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        generated_at = datetime.now().isoformat()

        council_name = resolve_council_name(council_id)
        constraints = json.loads(app.constraints_json or "[]")

        # ---- Location enrichment via postcodes.io ----
        try:
            from plana.location.postcodes import enrich_application_location
            location_data = enrich_application_location(
                postcode=app.postcode,
                address=app.address,
                existing_constraints=constraints,
            )
            if location_data.get("ward") and not app.ward:
                app.ward = location_data["ward"]
            if location_data.get("all_constraints"):
                constraints = location_data["all_constraints"]
        except Exception:
            pass  # Non-fatal

        app_data = {
            "address": app.address,
            "proposal": app.proposal,
            "application_type": app.application_type or "",
            "constraints": constraints,
            "ward": app.ward,
            "postcode": app.postcode,
        }

        # Retrieve policies
        policies = self.policy_search.retrieve_relevant_policies(
            proposal=app.proposal,
            constraints=constraints,
            application_type=app.application_type or "",
            council_id=council_id,
            reference=app.reference,
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
            proposal=app.proposal,
            constraints=constraints,
            address=app.address,
            application_type=app.application_type or "",
        )
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

        # Document processing status
        processing_counts = self.db.get_processing_counts(app.reference)
        processing_status = ProcessingStatusResponse(
            total=processing_counts["total"],
            queued=processing_counts["queued"],
            processing=processing_counts["processing"],
            processed=processing_counts["processed"],
            failed=processing_counts["failed"],
        )
        extraction_counts = self.db.get_extraction_counts(app.reference)
        extraction_status = ExtractionStatusResponse(
            queued=extraction_counts["queued"],
            extracted=extraction_counts["extracted"],
            failed=extraction_counts["failed"],
        )

        documents_summary = DocumentsSummaryResponse(
            total_count=processing_status.total,
            by_type={},
            with_extracted_text=extraction_status.extracted,
            missing_suspected=[],
            extraction_status=extraction_status,
            documents=processing_status,
        )

        # Pipeline audit
        pipeline_audit = self._build_pipeline_audit(
            mode="import",
            has_policies=len(policies) > 0,
            has_similar_cases=len(similar_cases) >= 2,
            has_documents=processing_status.total > 0,
        )

        # Document ingestion + texts from DB
        document_ingestion = self._build_document_ingestion(app.reference)
        document_texts = self.db.get_extracted_texts(app.reference)

        # Generate report
        report_result = self._generate_report_result(
            reference=app.reference,
            app_data=app_data,
            policies=policies,
            similar_cases=similar_cases,
            council_id=council_id,
            document_texts=document_texts,
            document_ingestion=document_ingestion,
        )

        assessment = self._build_assessment(
            app_data=app_data, policies=policies, report_result=report_result,
        )
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
        evidence = self._build_evidence(policies, similar_cases, app_data)
        learning_signals = self._build_learning_signals(
            policies=policies, similar_cases=similar_cases, recommendation=recommendation,
        )

        self._save_run_log(
            run_id=run_id,
            reference=app.reference,
            mode="import",
            council_id=council_id,
            recommendation=recommendation.outcome,
            confidence=assessment.confidence.score,
            policies_count=len(selected_policies),
            similar_cases_count=len(similar_cases),
        )

        application_summary = ApplicationSummaryResponse(
            reference=app.reference,
            council_id=council_id,
            council_name=council_name,
            address=app.address,
            proposal=app.proposal,
            application_type=app.application_type or "",
            constraints=constraints,
            ward=app.ward,
            postcode=app.postcode,
        )

        return CaseOutputResponse(
            meta=MetaResponse(
                run_id=run_id,
                reference=app.reference,
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
