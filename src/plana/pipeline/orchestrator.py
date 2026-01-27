"""
Main pipeline orchestrator.

Coordinates the end-to-end processing of planning applications:
1. Fetch application data
2. Download and store documents
3. Extract text from documents
4. Index for search/similarity
5. Retrieve relevant policies
6. Find similar historic cases
7. Generate case officer report
8. Output results
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from plana.config import get_settings
from plana.core.models import Application, HistoricCase, Policy, Report
from plana.councils import CouncilRegistry
from plana.councils.base import CouncilPortal
from plana.feedback import FeedbackTracker
from plana.policies import PolicyManager, PolicyRetriever
from plana.processing import DocumentProcessor
from plana.reports import ReportGenerator
from plana.search import SimilaritySearcher, VectorStore
from plana.storage import DocumentStore

logger = structlog.get_logger(__name__)


class PipelineResult:
    """Result of a pipeline run."""

    def __init__(self):
        self.application: Application | None = None
        self.policies: list[Policy] = []
        self.similar_cases: list[HistoricCase] = []
        self.report: Report | None = None
        self.errors: list[str] = []
        self.timings: dict[str, float] = {}
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

    @property
    def success(self) -> bool:
        return self.report is not None and len(self.errors) == 0

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "application_reference": self.application.reference if self.application else None,
            "policies_count": len(self.policies),
            "similar_cases_count": len(self.similar_cases),
            "report_id": self.report.id if self.report else None,
            "errors": self.errors,
            "timings": self.timings,
            "duration_seconds": self.duration_seconds,
        }


class PlanaPipeline:
    """
    Main pipeline orchestrator for Plana.AI.

    This class coordinates the entire processing flow from
    fetching an application to generating a case officer report.

    It is designed to run fully automated without manual intervention.
    """

    def __init__(
        self,
        document_store: DocumentStore | None = None,
        document_processor: DocumentProcessor | None = None,
        policy_manager: PolicyManager | None = None,
        policy_retriever: PolicyRetriever | None = None,
        vector_store: VectorStore | None = None,
        similarity_searcher: SimilaritySearcher | None = None,
        report_generator: ReportGenerator | None = None,
        feedback_tracker: FeedbackTracker | None = None,
    ):
        """Initialize pipeline with components.

        All components are optional - defaults will be created if not provided.
        """
        self.settings = get_settings()

        # Initialize components
        self.document_store = document_store or DocumentStore()
        self.document_processor = document_processor or DocumentProcessor(
            document_store=self.document_store
        )
        self.policy_manager = policy_manager or PolicyManager()
        self.vector_store = vector_store or VectorStore()
        self.policy_retriever = policy_retriever or PolicyRetriever(
            policy_manager=self.policy_manager,
            vector_store=self.vector_store,
        )
        self.similarity_searcher = similarity_searcher or SimilaritySearcher(
            vector_store=self.vector_store
        )
        self.report_generator = report_generator or ReportGenerator()
        self.feedback_tracker = feedback_tracker or FeedbackTracker()

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize pipeline components."""
        if self._initialized:
            return

        logger.info("Initializing Plana pipeline")

        # Load policies
        await self.policy_manager.load_policies()

        # Initialize default policies if none loaded
        if not self.policy_manager.list_policies():
            await self._load_default_policies()

        # Initialize vector store
        await self.vector_store.initialize()

        self._initialized = True
        logger.info("Pipeline initialized")

    async def _load_default_policies(self) -> None:
        """Load default NPPF and Newcastle policies."""
        from plana.policies.manager import (
            DEFAULT_NPPF_POLICIES,
            NEWCASTLE_LOCAL_PLAN_POLICIES,
        )
        from plana.core.models import Policy, PolicyType

        for policy_data in DEFAULT_NPPF_POLICIES:
            policy = Policy(
                id=policy_data["id"],
                policy_type=PolicyType(policy_data["policy_type"]),
                reference=policy_data["reference"],
                title=policy_data["title"],
                content=policy_data["content"],
                summary=policy_data.get("summary"),
                chapter=policy_data.get("chapter"),
            )
            await self.policy_manager.add_policy(policy)

        for policy_data in NEWCASTLE_LOCAL_PLAN_POLICIES:
            policy = Policy(
                id=policy_data["id"],
                policy_type=PolicyType(policy_data["policy_type"]),
                reference=policy_data["reference"],
                title=policy_data["title"],
                content=policy_data["content"],
                summary=policy_data.get("summary"),
                chapter=policy_data.get("chapter"),
                council_id=policy_data.get("council_id"),
            )
            await self.policy_manager.add_policy(policy)

        logger.info("Loaded default policies")

    async def run(
        self,
        reference: str,
        council_id: str = "newcastle",
        force_reprocess: bool = False,
    ) -> PipelineResult:
        """Run the complete pipeline for an application.

        This is the main entry point for fully automated processing.

        Args:
            reference: Application reference number
            council_id: Council identifier
            force_reprocess: Force re-download and re-process

        Returns:
            PipelineResult with all outputs
        """
        result = PipelineResult()
        result.started_at = datetime.utcnow()

        logger.info(
            "Starting pipeline",
            reference=reference,
            council_id=council_id,
        )

        try:
            await self.initialize()

            # Step 1: Fetch application
            start = time.time()
            application = await self._fetch_application(reference, council_id)
            result.timings["fetch_application"] = time.time() - start
            result.application = application

            # Step 2: Process documents
            start = time.time()
            application = await self._process_documents(application, force_reprocess)
            result.timings["process_documents"] = time.time() - start

            # Step 3: Get document texts
            start = time.time()
            document_texts = await self.document_processor.get_all_document_texts(application)
            result.timings["extract_text"] = time.time() - start

            # Step 4: Index application for future similarity search
            start = time.time()
            await self._index_application(application, document_texts)
            result.timings["index_application"] = time.time() - start

            # Step 5: Retrieve relevant policies
            start = time.time()
            policy_matches = await self.policy_retriever.retrieve_relevant_policies(
                application=application,
                max_policies=20,
            )
            policies = [pm.policy for pm in policy_matches]
            result.policies = policies
            result.timings["retrieve_policies"] = time.time() - start

            # Step 6: Find similar cases
            start = time.time()
            similar_cases = await self.similarity_searcher.find_similar_cases(
                application=application,
                max_results=10,
            )
            result.similar_cases = similar_cases
            result.timings["find_similar_cases"] = time.time() - start

            # Step 7: Generate report
            start = time.time()
            report = await self.report_generator.generate_report(
                application=application,
                policies=policies,
                similar_cases=similar_cases,
                document_texts=document_texts,
            )
            result.report = report
            result.timings["generate_report"] = time.time() - start

            # Step 8: Save results
            start = time.time()
            await self._save_results(result)
            result.timings["save_results"] = time.time() - start

            result.completed_at = datetime.utcnow()

            logger.info(
                "Pipeline completed successfully",
                reference=reference,
                duration_seconds=result.duration_seconds,
                report_id=report.id,
            )

        except Exception as e:
            logger.error(
                "Pipeline failed",
                reference=reference,
                error=str(e),
                exc_info=True,
            )
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()

        return result

    async def process_application(
        self,
        reference: str,
        council_id: str = "newcastle",
        force_reprocess: bool = False,
    ) -> Application:
        """Process application without generating report.

        Args:
            reference: Application reference
            council_id: Council ID
            force_reprocess: Force re-download

        Returns:
            Processed application
        """
        await self.initialize()

        application = await self._fetch_application(reference, council_id)
        application = await self._process_documents(application, force_reprocess)
        document_texts = await self.document_processor.get_all_document_texts(application)
        await self._index_application(application, document_texts)

        return application

    async def generate_report(
        self,
        reference: str,
        council_id: str = "newcastle",
    ) -> Report:
        """Generate report for a processed application.

        Args:
            reference: Application reference
            council_id: Council ID

        Returns:
            Generated report
        """
        await self.initialize()

        # Fetch and process application
        application = await self._fetch_application(reference, council_id)
        application = await self._process_documents(application, force_reprocess=False)
        document_texts = await self.document_processor.get_all_document_texts(application)

        # Get policies and similar cases
        policy_matches = await self.policy_retriever.retrieve_relevant_policies(application)
        policies = [pm.policy for pm in policy_matches]

        similar_cases = await self.similarity_searcher.find_similar_cases(application)

        # Generate report
        report = await self.report_generator.generate_report(
            application=application,
            policies=policies,
            similar_cases=similar_cases,
            document_texts=document_texts,
        )

        return report

    async def _fetch_application(
        self, reference: str, council_id: str
    ) -> Application:
        """Fetch application from council portal."""
        portal = CouncilRegistry.get(council_id)
        try:
            application = await portal.fetch_application(reference)
            documents = await portal.fetch_application_documents(reference)
            application.documents = documents
            return application
        finally:
            await portal.close()

    async def _process_documents(
        self, application: Application, force_reprocess: bool
    ) -> Application:
        """Process all documents for an application."""
        portal = CouncilRegistry.get(application.council_id)
        try:
            return await self.document_processor.process_application(
                application=application,
                portal=portal,
                force_reprocess=force_reprocess,
            )
        finally:
            await portal.close()

    async def _index_application(
        self, application: Application, document_texts: dict[str, str]
    ) -> None:
        """Index application for similarity search."""
        # Create summary for embedding
        summary_parts = [
            f"Reference: {application.reference}",
            f"Address: {application.address.full_address}",
            f"Proposal: {application.proposal}",
            f"Type: {application.application_type.value}",
        ]

        if application.constraints:
            constraints = ", ".join(c.constraint_type for c in application.constraints)
            summary_parts.append(f"Constraints: {constraints}")

        # Add document content
        for doc_id, text in list(document_texts.items())[:3]:
            summary_parts.append(f"Document: {text[:500]}")

        summary = "\n".join(summary_parts)

        # Add to vector store
        await self.vector_store.add(
            collection="applications",
            id=application.reference,
            content=summary,
            metadata={
                "council_id": application.council_id,
                "application_type": application.application_type.value,
                "status": application.status.value,
                "postcode": application.address.postcode or "",
            },
        )

        # If decided, add to historic cases for similarity
        if application.is_decided:
            await self.similarity_searcher.add_historic_case(application)

    async def _save_results(self, result: PipelineResult) -> None:
        """Save pipeline results to storage."""
        if not result.application:
            return

        output_dir = self.settings.data_dir / "results" / result.application.council_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save application data
        app_file = output_dir / f"{result.application.reference.replace('/', '_')}.json"
        with open(app_file, "w") as f:
            json.dump(
                {
                    "application": result.application.model_dump(mode="json"),
                    "policies_cited": [p.reference for p in result.policies],
                    "similar_cases": [
                        {
                            "reference": c.application.reference,
                            "score": c.similarity_score,
                        }
                        for c in result.similar_cases
                    ],
                    "report": result.report.model_dump(mode="json") if result.report else None,
                    "timings": result.timings,
                    "processed_at": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
                default=str,
            )

        logger.info(
            "Saved results",
            reference=result.application.reference,
            file=str(app_file),
        )


async def run_pipeline(
    reference: str,
    council_id: str = "newcastle",
    force_reprocess: bool = False,
) -> PipelineResult:
    """Convenience function to run the pipeline.

    Args:
        reference: Application reference
        council_id: Council ID
        force_reprocess: Force reprocessing

    Returns:
        Pipeline result
    """
    pipeline = PlanaPipeline()
    return await pipeline.run(reference, council_id, force_reprocess)
