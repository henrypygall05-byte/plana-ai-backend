"""
Pipeline service for processing planning applications.

Extracts the core processing logic from the CLI for reuse.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from plana.core.constants import (
    ConfidenceConfig,
    PolicySearchConfig,
    SimilarityThresholds,
    resolve_council_name,
)
from plana.core.exceptions import (
    PortalError,
    ProcessingError,
    ReferenceNotFoundError,
)
from plana.core.logging import PipelineLogger, get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of pipeline processing."""

    reference: str
    decision: str
    confidence: float
    policies_count: int
    similar_cases_count: int
    documents_count: int
    report_path: Optional[str] = None
    report_content: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ApplicationContext:
    """Context for processing an application."""

    reference: str
    address: str
    proposal: str
    application_type: str
    constraints: list[str]
    ward: str
    council_id: str = "newcastle"
    mode: str = "demo"


class PipelineService:
    """Service for running the application processing pipeline.

    Provides a clean interface for:
    - Demo mode processing (fixture data)
    - Live mode processing (portal fetch)
    - Report generation
    - Result storage
    """

    def __init__(self):
        """Initialize the pipeline service."""
        self._logger = get_logger(__name__)

    async def process_demo(
        self,
        reference: str,
        output_path: Optional[Path] = None,
    ) -> PipelineResult:
        """Process an application in demo mode.

        Args:
            reference: Application reference
            output_path: Optional path for report output

        Returns:
            PipelineResult with processing outcomes
        """
        from plana.cli import DEMO_APPLICATIONS

        start_time = datetime.now()
        pipeline_logger = PipelineLogger(reference, mode="demo")

        if reference not in DEMO_APPLICATIONS:
            raise ReferenceNotFoundError(reference)

        app_data = DEMO_APPLICATIONS[reference]

        try:
            # Create application context
            context = ApplicationContext(
                reference=reference,
                address=app_data["address"],
                proposal=app_data["proposal"],
                application_type=app_data["type"],
                constraints=app_data.get("constraints", []),
                ward=app_data.get("ward", "City Centre"),
                mode="demo",
            )

            # Process through pipeline
            result = await self._run_pipeline(context, output_path, pipeline_logger)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.duration_ms = duration_ms

            pipeline_logger.pipeline_completed(True, duration_ms)
            return result

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            pipeline_logger.pipeline_completed(False, duration_ms, error=str(e))

            return PipelineResult(
                reference=reference,
                decision="UNKNOWN",
                confidence=0.0,
                policies_count=0,
                similar_cases_count=0,
                documents_count=0,
                success=False,
                error_message=str(e),
                duration_ms=duration_ms,
            )

    async def process_live(
        self,
        reference: str,
        council_id: str = "newcastle",
        output_path: Optional[Path] = None,
    ) -> PipelineResult:
        """Process an application in live mode.

        Args:
            reference: Application reference
            council_id: Council identifier
            output_path: Optional path for report output

        Returns:
            PipelineResult with processing outcomes
        """
        from plana.ingestion import get_adapter

        start_time = datetime.now()
        pipeline_logger = PipelineLogger(reference, mode="live")

        try:
            # Get portal adapter
            adapter = get_adapter(council_id)

            pipeline_logger.step_started("fetch_metadata")

            # Fetch application details
            app_details = await adapter.fetch_application(reference)

            if not app_details:
                await adapter.close()
                raise ReferenceNotFoundError(reference)

            pipeline_logger.step_completed("fetch_metadata", 0)

            # Create context from portal data
            context = ApplicationContext(
                reference=reference,
                address=app_details.address,
                proposal=app_details.proposal,
                application_type=app_details.application_type.value,
                constraints=[c.name for c in app_details.constraints],
                ward=app_details.ward or "Unknown",
                council_id=council_id,
                mode="live",
            )

            # Fetch documents
            pipeline_logger.step_started("fetch_documents")
            documents = await adapter.fetch_documents(reference)
            pipeline_logger.step_completed("fetch_documents", 0, count=len(documents))

            await adapter.close()

            # Process through pipeline
            result = await self._run_pipeline(context, output_path, pipeline_logger)
            result.documents_count = len(documents)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.duration_ms = duration_ms

            pipeline_logger.pipeline_completed(True, duration_ms)
            return result

        except ReferenceNotFoundError:
            raise
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            pipeline_logger.pipeline_completed(False, duration_ms, error=str(e))

            if "blocked" in str(e).lower() or "WAF" in str(e):
                raise PortalError(str(e))

            return PipelineResult(
                reference=reference,
                decision="UNKNOWN",
                confidence=0.0,
                policies_count=0,
                similar_cases_count=0,
                documents_count=0,
                success=False,
                error_message=str(e),
                duration_ms=duration_ms,
            )

    async def _run_pipeline(
        self,
        context: ApplicationContext,
        output_path: Optional[Path],
        pipeline_logger: PipelineLogger,
    ) -> PipelineResult:
        """Run the core processing pipeline.

        Args:
            context: Application context
            output_path: Optional output path
            pipeline_logger: Logger for step tracking

        Returns:
            PipelineResult
        """
        from plana.decision_calibration import calibrate_decision
        from plana.improvement import get_confidence_adjustment, rerank_policies
        from plana.policy import PolicySearch
        from plana.similarity import SimilaritySearch

        # Retrieve policies
        pipeline_logger.step_started("retrieve_policies")
        policy_search = PolicySearch()
        policies = policy_search.retrieve_relevant_policies(
            proposal=context.proposal,
            constraints=context.constraints,
            application_type=context.application_type,
            address=context.address,
        )
        policies = rerank_policies(policies, context.reference)
        pipeline_logger.step_completed("retrieve_policies", 0, count=len(policies))

        # Find similar cases
        pipeline_logger.step_started("find_similar")
        similarity_search = SimilaritySearch()
        similar_cases = similarity_search.find_similar_cases(
            proposal=context.proposal,
            constraints=context.constraints,
            address=context.address,
            application_type=context.application_type,
        )
        pipeline_logger.step_completed("find_similar", 0, count=len(similar_cases))

        # Generate report
        pipeline_logger.step_started("generate_report")
        from plana.report.generator import ApplicationData, ReportGenerator
        from plana.documents.ingestion import process_documents as ingest_docs

        # Run document ingestion if documents were fetched
        doc_ingestion = ingest_docs(
            context.documents, extract_text=True,
        ) if getattr(context, "documents", None) else None

        app_data = ApplicationData(
            reference=context.reference,
            address=context.address,
            proposal=context.proposal,
            application_type=context.application_type,
            constraints=context.constraints,
            ward=context.ward,
            council_name=resolve_council_name(context.council_id),
            document_ingestion=doc_ingestion,
        )

        generator = ReportGenerator()
        report = generator.generate_report(app_data, output_path, [])

        # Get decision
        raw_decision = "APPROVE_WITH_CONDITIONS"
        calibrated_decision = calibrate_decision(context.reference, raw_decision)
        confidence = get_confidence_adjustment(context.reference)

        pipeline_logger.step_completed(
            "generate_report", 0, decision=calibrated_decision
        )

        return PipelineResult(
            reference=context.reference,
            decision=calibrated_decision,
            confidence=confidence,
            policies_count=len(policies),
            similar_cases_count=len(similar_cases),
            documents_count=0,
            report_path=str(output_path) if output_path else None,
            report_content=report,
            success=True,
        )

    async def process(
        self,
        reference: str,
        council_id: str = "newcastle",
        mode: str = "auto",
        output_path: Optional[Path] = None,
    ) -> PipelineResult:
        """Process an application with automatic mode detection.

        Args:
            reference: Application reference
            council_id: Council identifier
            mode: Processing mode (demo, live, auto)
            output_path: Optional output path

        Returns:
            PipelineResult
        """
        from plana.cli import DEMO_APPLICATIONS

        # Determine effective mode
        if mode == "auto":
            if reference in DEMO_APPLICATIONS:
                mode = "demo"
            else:
                mode = "live"

        if mode == "demo":
            return await self.process_demo(reference, output_path)
        else:
            return await self.process_live(reference, council_id, output_path)
