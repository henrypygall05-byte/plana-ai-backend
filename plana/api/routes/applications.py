"""Application processing endpoints."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid

from plana.api.models import (
    ProcessApplicationRequest,
    ImportApplicationRequest,
    ImportApplicationResponse,
    CaseOutputResponse,
    ApplicationSummaryResponse,
)
from plana.api.services import PipelineService

router = APIRouter()


@router.post("/process", response_model=CaseOutputResponse)
async def process_application(
    request: ProcessApplicationRequest,
    background_tasks: BackgroundTasks,
) -> CaseOutputResponse:
    """Process a planning application and generate a report.

    Args:
        request: Processing request with reference, council_id, mode

    Returns:
        Complete CASE_OUTPUT response
    """
    try:
        service = PipelineService()
        result = await service.process_application(
            reference=request.reference,
            council_id=request.council_id,
            mode=request.mode,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=ImportApplicationResponse)
async def import_application(
    request: ImportApplicationRequest,
) -> ImportApplicationResponse:
    """Import and process a planning application from manual input.

    This endpoint accepts application details directly from the UI,
    finds relevant policies and similar cases, and generates a case officer report.

    No portal fetching is performed - all data comes from the request.

    Args:
        request: Manual application input with all details

    Returns:
        Import response with generated report
    """
    try:
        service = PipelineService()
        result = await service.process_imported_application(request)
        return ImportApplicationResponse(
            status="success",
            message=f"Application {request.reference} processed successfully",
            reference=request.reference,
            report=result,
        )
    except Exception as e:
        return ImportApplicationResponse(
            status="error",
            message=str(e),
            reference=request.reference,
            report=None,
        )


@router.get("/{council_id}/{reference:path}", response_model=ApplicationSummaryResponse)
async def get_application(
    council_id: str,
    reference: str,
) -> ApplicationSummaryResponse:
    """Get application metadata.

    Args:
        council_id: Council identifier
        reference: Application reference (supports slashes e.g. 2024/0930/01/DET)

    Returns:
        Application summary
    """
    try:
        service = PipelineService()
        result = await service.get_application(
            council_id=council_id,
            reference=reference,
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Application not found: {reference}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
