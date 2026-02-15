"""
Report service for generating planning reports.

Provides a clean interface for report generation.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from plana.core.exceptions import ReportGenerationError
from plana.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ReportResult:
    """Result of report generation."""

    reference: str
    content: str
    recommendation: str
    confidence: float
    policies_cited: int
    similar_cases_used: int
    generated_at: datetime
    output_path: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class ReportService:
    """Service for generating planning reports.

    Provides a clean interface for:
    - Report generation
    - Policy citation
    - Similar case integration
    """

    def __init__(self):
        """Initialize the report service."""
        self._logger = get_logger(__name__)

    def generate_report(
        self,
        reference: str,
        address: str,
        proposal: str,
        application_type: str,
        constraints: list[str],
        ward: str = "",
        council_name: str = "",
        policies: Optional[list] = None,
        similar_cases: Optional[list] = None,
        output_path: Optional[Path] = None,
    ) -> ReportResult:
        """Generate a planning report.

        Args:
            reference: Application reference
            address: Site address
            proposal: Proposal description
            application_type: Type of application
            constraints: Site constraints
            ward: Electoral ward
            council_name: Full council display name (e.g. 'Broxtowe Borough Council')
            policies: Relevant policies
            similar_cases: Similar historic cases
            output_path: Optional output path

        Returns:
            ReportResult with generated content
        """
        from plana.decision_calibration import calibrate_decision
        from plana.improvement import get_confidence_adjustment
        from plana.report.generator import ApplicationData, ReportGenerator

        try:
            # Create application data
            app_data = ApplicationData(
                reference=reference,
                address=address,
                proposal=proposal,
                application_type=application_type,
                constraints=constraints,
                ward=ward,
                council_name=council_name,
            )

            # Generate report
            generator = ReportGenerator()
            content = generator.generate_report(app_data, output_path, [])

            # Get calibrated decision
            raw_decision = "APPROVE_WITH_CONDITIONS"
            recommendation = calibrate_decision(reference, raw_decision)
            confidence = get_confidence_adjustment(reference)

            return ReportResult(
                reference=reference,
                content=content,
                recommendation=recommendation,
                confidence=confidence,
                policies_cited=len(policies) if policies else 0,
                similar_cases_used=len(similar_cases) if similar_cases else 0,
                generated_at=datetime.now(),
                output_path=str(output_path) if output_path else None,
                success=True,
            )

        except Exception as e:
            self._logger.error(
                "report_generation_failed",
                reference=reference,
                error=str(e),
            )

            return ReportResult(
                reference=reference,
                content="",
                recommendation="UNKNOWN",
                confidence=0.0,
                policies_cited=0,
                similar_cases_used=0,
                generated_at=datetime.now(),
                success=False,
                error_message=str(e),
            )

    def regenerate_report(
        self,
        reference: str,
        version: int = 1,
        output_path: Optional[Path] = None,
    ) -> ReportResult:
        """Regenerate a report for an existing application.

        Args:
            reference: Application reference
            version: Report version number
            output_path: Optional output path

        Returns:
            ReportResult
        """
        from plana.storage import get_database

        db = get_database()

        # Get stored application
        stored_app = db.get_application(reference)
        if not stored_app:
            return ReportResult(
                reference=reference,
                content="",
                recommendation="UNKNOWN",
                confidence=0.0,
                policies_cited=0,
                similar_cases_used=0,
                generated_at=datetime.now(),
                success=False,
                error_message=f"Application not found: {reference}",
            )

        # Parse constraints
        import json

        try:
            constraints = json.loads(stored_app.constraints_json or "[]")
            constraint_names = [c.get("name", "") for c in constraints]
        except json.JSONDecodeError:
            constraint_names = []

        # Generate new report
        return self.generate_report(
            reference=reference,
            address=stored_app.address,
            proposal=stored_app.proposal,
            application_type=stored_app.application_type or "",
            constraints=constraint_names,
            ward=stored_app.ward or "",
            output_path=output_path,
        )
