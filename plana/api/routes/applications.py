"""Application processing endpoints."""

from datetime import datetime
from typing import Optional, List, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid

from plana.api.models import (
    ProcessApplicationRequest,
    ImportApplicationRequest,
    ImportApplicationResponse,
    CaseOutputResponse,
    ApplicationSummaryResponse,
    DocumentProcessingResponse,
)
from plana.api.services import PipelineService
from plana.api.services.pipeline_service import DocumentsProcessingError

router = APIRouter()


@router.post(
    "/process",
    response_model=CaseOutputResponse,
    responses={
        202: {
            "model": DocumentProcessingResponse,
            "description": "Documents are still being extracted",
        },
    },
)
async def process_application(
    request: ProcessApplicationRequest,
    background_tasks: BackgroundTasks,
) -> Union[CaseOutputResponse, JSONResponse]:
    """Process a planning application and generate a report.

    Returns HTTP 202 if documents are still queued for extraction.

    Args:
        request: Processing request with reference, council_id, mode

    Returns:
        Complete CASE_OUTPUT response, or 202 if documents still processing
    """
    try:
        service = PipelineService()
        result = await service.process_application(
            reference=request.reference,
            council_id=request.council_id,
            mode=request.mode,
        )
        return result
    except DocumentsProcessingError as e:
        return JSONResponse(
            status_code=202,
            content=DocumentProcessingResponse(
                status="processing_documents",
                extraction_status=e.extraction_status,
            ).model_dump(),
        )
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
