"""Report retrieval endpoints."""

from typing import List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query

from plana.api.models import CaseOutputResponse, ReportVersionResponse
from plana.api.services import PipelineService

router = APIRouter()


# --- Query-param endpoints (preferred) ---


@router.get("/by-reference", response_model=CaseOutputResponse)
async def get_report_by_reference(
    reference: str = Query(..., description="Application reference (e.g. 24/00730/FUL)"),
    version: Optional[int] = Query(None, description="Specific version number"),
) -> CaseOutputResponse:
    """Get a generated report for an application.

    Pass the reference as a query parameter to avoid URL-encoding
    issues with slashes.

    Example: ``GET /api/v1/reports/by-reference?reference=24/00730/FUL``
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


@router.get("/by-reference/versions", response_model=List[ReportVersionResponse])
async def get_report_versions_by_reference(
    reference: str = Query(..., description="Application reference (e.g. 24/00730/FUL)"),
) -> List[ReportVersionResponse]:
    """Get all versions of a report.

    Pass the reference as a query parameter to avoid URL-encoding
    issues with slashes.

    Example: ``GET /api/v1/reports/by-reference/versions?reference=24/00730/FUL``
    """
    try:
        service = PipelineService()
        versions = await service.get_report_versions(reference=reference)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Legacy path-param routes (return 400 with migration hint) ---


# NOTE: /{reference:path}/versions must come BEFORE /{reference:path}
# to avoid greedy matching by the path parameter
@router.get("/{reference:path}/versions")
async def get_report_versions_legacy(reference: str):
    """Legacy path-param route. Returns 400 directing clients to the query-param endpoint."""
    decoded = unquote(reference)
    raise HTTPException(
        status_code=400,
        detail=(
            f"Path-parameter routes do not support references with slashes. "
            f"Use GET /api/v1/reports/by-reference/versions?reference={decoded} instead."
        ),
    )


@router.get("/{reference:path}")
async def get_report_legacy(reference: str):
    """Legacy path-param route. Returns 400 directing clients to the query-param endpoint."""
    decoded = unquote(reference)
    raise HTTPException(
        status_code=400,
        detail=(
            f"Path-parameter routes do not support references with slashes. "
            f"Use GET /api/v1/reports/by-reference?reference={decoded} instead."
        ),
    )
