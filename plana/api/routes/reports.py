"""Report retrieval endpoints.

Supports two storage backends:
1. ``_demo_reports`` — in-memory dict populated by the import endpoint.
2. ``PipelineService.get_report()`` — database-backed report generation.

Both query-parameter and legacy path-parameter URL forms are accepted.
"""

from typing import Any, List, Optional, Union
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from plana.api.models import (
    CaseOutputResponse,
    DocumentProcessingResponse,
    ReportVersionResponse,
)
from plana.api.services import PipelineService
from plana.api.services.pipeline_service import DocumentsProcessingError
from plana.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# In-memory store populated by the import endpoint
# ---------------------------------------------------------------------------

_demo_reports: dict[str, "ReportResponse"] = {}


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
    recommendation: str | None = None
    generated_at: str
    generation_time_seconds: float | None = None
    mode: str = "live"
    demo_reference_used: str | None = None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _normalize_ref(ref: str) -> str:
    """Normalize a reference for lookup — decode URL-encoding and uppercase."""
    return unquote(ref).strip().upper()


def _lookup_demo_report(reference: str) -> Optional[ReportResponse]:
    """Check the in-memory demo store for a report."""
    normalized = _normalize_ref(reference)
    return _demo_reports.get(normalized)


async def _get_report(
    reference: str,
    version: Optional[int] = None,
) -> Any:
    """Fetch the report from demo store first, then PipelineService.

    Returns 202 if documents are still being processed.
    """
    # 1. Check in-memory store (populated by import endpoint)
    demo = _lookup_demo_report(reference)
    if demo is not None:
        return demo

    # 2. Fall through to PipelineService (database-backed)
    try:
        service = PipelineService()
        result = await service.get_report(reference=reference, version=version)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {reference}",
            )
        return result
    except HTTPException:
        raise
    except DocumentsProcessingError as e:
        return JSONResponse(
            status_code=202,
            content=DocumentProcessingResponse(
                status="processing_documents",
                extraction_status=e.extraction_status,
                documents=e.processing_status,
            ).model_dump(),
        )
    except Exception as e:
        logger.error("get_report_error", reference=reference, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Query-param endpoints (preferred)
# ---------------------------------------------------------------------------


@router.get("", response_model=CaseOutputResponse)
async def get_report_root(
    reference: str = Query(
        ..., description="Application reference (e.g. 24/00730/FUL)"
    ),
    version: Optional[int] = Query(None, description="Specific version number"),
):
    """Get a generated report for an application.

    Example: ``GET /api/v1/reports?reference=24/00730/FUL``
    """
    return await _get_report(reference=reference, version=version)


@router.get("/by-reference", response_model=CaseOutputResponse)
async def get_report_by_reference(
    reference: str = Query(
        ..., description="Application reference (e.g. 24/00730/FUL)"
    ),
    version: Optional[int] = Query(None, description="Specific version number"),
):
    """Get a generated report for an application.

    Example: ``GET /api/v1/reports/by-reference?reference=24/00730/FUL``
    """
    return await _get_report(reference=reference, version=version)


@router.get("/by-reference/versions", response_model=List[ReportVersionResponse])
async def get_report_versions_by_reference(
    reference: str = Query(
        ..., description="Application reference (e.g. 24/00730/FUL)"
    ),
):
    """Get all versions of a report.

    Example: ``GET /api/v1/reports/by-reference/versions?reference=24/00730/FUL``
    """
    demo = _lookup_demo_report(reference)
    if demo is not None:
        return [
            {
                "version": demo.version,
                "generated_at": demo.generated_at,
                "recommendation": demo.recommendation,
            }
        ]

    try:
        service = PipelineService()
        return await service.get_report_versions(reference=reference)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Legacy path-param routes — serve reports if found
# ---------------------------------------------------------------------------


@router.get("/{reference:path}/versions")
async def get_report_versions_legacy(reference: str):
    """Legacy path-param versions route."""
    decoded = unquote(reference)
    normalized = decoded.strip().upper()

    if normalized in _demo_reports:
        report = _demo_reports[normalized]
        return [
            {
                "version": report.version,
                "generated_at": report.generated_at,
                "recommendation": report.recommendation,
            }
        ]
    return []


@router.get("/{reference:path}")
async def get_report_legacy(reference: str):
    """Legacy path-param report retrieval.

    Checks in-memory store first, then falls through to PipelineService.
    """
    decoded = unquote(reference)
    return await _get_report(reference=decoded)
