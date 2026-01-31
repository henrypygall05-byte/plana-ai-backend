"""Report retrieval endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from plana.api.models import CaseOutputResponse, ReportVersionResponse
from plana.api.services import PipelineService

router = APIRouter()


# NOTE: /{reference:path}/versions must come BEFORE /{reference:path}
# to avoid greedy matching by the path parameter
@router.get("/{reference:path}/versions", response_model=List[ReportVersionResponse])
async def get_report_versions(reference: str) -> List[ReportVersionResponse]:
    """Get all versions of a report.

    Args:
        reference: Application reference (supports slashes e.g. 2024/0930/01/DET)

    Returns:
        List of report versions
    """
    try:
        service = PipelineService()
        versions = await service.get_report_versions(reference=reference)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{reference:path}", response_model=CaseOutputResponse)
async def get_report(
    reference: str,
    version: Optional[int] = Query(None, description="Specific version number"),
) -> CaseOutputResponse:
    """Get a generated report for an application.

    Args:
        reference: Application reference (supports slashes e.g. 2024/0930/01/DET)
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
