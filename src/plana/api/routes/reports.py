"""Report generation and management endpoints."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class GenerateReportRequest(BaseModel):
    """Request to generate a report."""

    application_reference: str
    council_id: str = "newcastle"
    include_similar_cases: bool = True
    max_similar_cases: int = Field(default=5, le=10)


class ReportSectionResponse(BaseModel):
    """Report section response."""

    section_id: str
    title: str
    content: str
    order: int


class ReportResponse(BaseModel):
    """Report response model."""

    id: str
    application_reference: str
    version: int
    sections: list[ReportSectionResponse]
    recommendation: str | None
    generated_at: str
    generation_time_seconds: float | None


class ReportSummaryResponse(BaseModel):
    """Summary report response."""

    id: str
    application_reference: str
    version: int
    recommendation: str | None
    sections_count: int
    generated_at: str


@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Generate a case officer report for an application.

    This is an async operation - the report is generated in the background.

    Args:
        request: Report generation request
    """
    from plana.pipeline import PlanaPipeline

    async def generate_task():
        pipeline = PlanaPipeline()
        await pipeline.generate_report(
            reference=request.application_reference,
            council_id=request.council_id,
        )

    background_tasks.add_task(generate_task)

    return {
        "status": "generating",
        "message": f"Report generation started for {request.application_reference}",
        "reference": request.application_reference,
    }


@router.get("/{application_reference}")
async def get_report(
    application_reference: str,
    version: int | None = Query(None, description="Specific version"),
) -> ReportResponse:
    """Get a generated report for an application.

    Args:
        application_reference: Application reference
        version: Specific version (latest if not specified)
    """
    # In production, would load from database
    raise HTTPException(
        status_code=404,
        detail=f"No report found for {application_reference}",
    )


@router.get("/{application_reference}/versions")
async def list_report_versions(
    application_reference: str,
) -> list[ReportSummaryResponse]:
    """List all report versions for an application.

    Args:
        application_reference: Application reference
    """
    # In production, would load from database
    return []


@router.get("/{application_reference}/section/{section_id}")
async def get_report_section(
    application_reference: str,
    section_id: str,
) -> ReportSectionResponse:
    """Get a specific section of a report.

    Args:
        application_reference: Application reference
        section_id: Section ID
    """
    raise HTTPException(
        status_code=404,
        detail="Section not found",
    )


@router.post("/{application_reference}/regenerate")
async def regenerate_report(
    application_reference: str,
    section_id: str | None = Query(None, description="Regenerate specific section"),
    background_tasks: BackgroundTasks = None,
) -> dict[str, str]:
    """Regenerate a report or specific section.

    Args:
        application_reference: Application reference
        section_id: Section to regenerate (all if not specified)
    """
    return {
        "status": "regenerating",
        "message": f"Regeneration started for {application_reference}",
    }
