"""Report retrieval endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from plana.api.models import CaseOutputResponse, ReportVersionResponse
from plana.api.services import PipelineService

router = APIRouter()


@router.get("/{reference}", response_model=CaseOutputResponse)
async def get_report(
    reference: str,
    version: Optional[int] = Query(None, description="Specific version number"),
) -> CaseOutputResponse:
    """Get a generated report for an application.

    Args:
        reference: Application reference
        version: Specific version (latest if not specified)

    Returns:
        Complete CASE_OUTPUT response
    """
    try:
        service = PipelineService()
        result = await service.get_report(reference=reference, version=version)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Report not found: {reference}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{reference}/versions", response_model=List[ReportVersionResponse])
async def get_report_versions(reference: str) -> List[ReportVersionResponse]:
    """Get all versions of a report.

    Args:
        reference: Application reference

    Returns:
        List of report versions
    """
    try:
        service = PipelineService()
        versions = await service.get_report_versions(reference=reference)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
