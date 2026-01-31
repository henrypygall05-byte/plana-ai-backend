"""Application management endpoints."""

import uuid
from datetime import datetime
from typing import Any, Literal

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from plana.config import get_settings
from plana.core.models import Application, ApplicationStatus, ApplicationType
from plana.councils import CouncilRegistry
from plana.councils.base import ApplicationNotFoundError, CouncilPortalError
from plana.councils.fixtures import DEMO_APPLICATIONS

router = APIRouter()
logger = structlog.get_logger(__name__)


# Default demo reference to use when user's reference isn't in fixtures
DEFAULT_DEMO_REFERENCE = "2024/0930/01/DET"


class ApplicationResponse(BaseModel):
    """Application response model."""

    reference: str
    council_id: str
    address: str
    proposal: str
    application_type: str
    status: str
    received_date: str | None
    decision_date: str | None
    case_officer: str | None
    documents_count: int
    source_url: str | None

    @classmethod
    def from_application(cls, app: Application) -> "ApplicationResponse":
        return cls(
            reference=app.reference,
            council_id=app.council_id,
            address=app.address.full_address,
            proposal=app.proposal,
            application_type=app.application_type.value,
            status=app.status.value,
            received_date=app.received_date.isoformat() if app.received_date else None,
            decision_date=app.decision_date.isoformat() if app.decision_date else None,
            case_officer=app.case_officer,
            documents_count=len(app.documents),
            source_url=app.source_url,
        )


class ApplicationDetailResponse(BaseModel):
    """Detailed application response."""

    application: dict[str, Any]
    documents: list[dict[str, Any]]
    constraints: list[dict[str, Any]]


class SearchRequest(BaseModel):
    """Application search request."""

    postcode: str | None = None
    address: str | None = None
    ward: str | None = None
    date_from: str | None = Field(None, description="YYYY-MM-DD")
    date_to: str | None = Field(None, description="YYYY-MM-DD")
    status: str | None = None
    application_type: str | None = None
    max_results: int = Field(default=20, le=100)


class ProcessRequest(BaseModel):
    """Request to process an application."""

    reference: str
    council_id: str = "newcastle"
    force_reprocess: bool = False
    mode: Literal["live", "demo"] = "live"


class ProcessResponse(BaseModel):
    """Response from processing an application."""

    status: str
    message: str
    reference: str
    mode: str
    demo_reference_used: str | None = None
    application: dict[str, Any] | None = None
    documents: list[dict[str, Any]] | None = None
    constraints: list[dict[str, Any]] | None = None


def _get_demo_application_data(reference: str) -> tuple[dict[str, Any], str]:
    """Get demo application data, falling back to default if reference not found.

    Args:
        reference: User-provided reference

    Returns:
        Tuple of (application_data, actual_reference_used)
    """
    # Normalize reference format
    normalized = reference.strip().upper()

    # Try to find exact match
    if normalized in DEMO_APPLICATIONS:
        return DEMO_APPLICATIONS[normalized], normalized

    # Fall back to default demo reference
    logger.info(
        "Reference not in demo fixtures, using default",
        requested=reference,
        using=DEFAULT_DEMO_REFERENCE,
    )
    return DEMO_APPLICATIONS[DEFAULT_DEMO_REFERENCE], DEFAULT_DEMO_REFERENCE


def _build_demo_response(
    reference: str,
    council_id: str,
    demo_data: dict[str, Any],
    actual_ref: str,
) -> ProcessResponse:
    """Build a demo mode response with full application details."""
    # Build application dict
    application = {
        "reference": actual_ref,
        "council_id": council_id,
        "address": demo_data["address"]["full_address"],
        "postcode": demo_data["address"].get("postcode"),
        "ward": demo_data["address"].get("ward"),
        "proposal": demo_data["proposal"],
        "application_type": demo_data["application_type"],
        "status": demo_data["status"],
        "received_date": demo_data.get("received_date"),
        "decision_date": demo_data.get("decision_date"),
    }

    # Build documents list
    documents = [
        {
            "id": doc["id"],
            "title": doc["title"],
            "type": doc["type"],
            "file_type": doc.get("file_type", "pdf"),
        }
        for doc in demo_data.get("documents", [])
    ]

    # Build constraints list
    constraints = [
        {
            "constraint_type": c["constraint_type"],
            "name": c["name"],
        }
        for c in demo_data.get("constraints", [])
    ]

    return ProcessResponse(
        status="ready",
        message=f"Application prepared for report generation (demo mode)",
        reference=reference,
        mode="demo",
        demo_reference_used=actual_ref if actual_ref != reference.strip().upper() else None,
        application=application,
        documents=documents,
        constraints=constraints,
    )


@router.get("/{council_id}/{reference}")
async def get_application(
    council_id: str,
    reference: str,
) -> ApplicationDetailResponse:
    """Fetch a planning application by reference.

    Args:
        council_id: Council identifier (e.g., 'newcastle')
        reference: Application reference number
    """
    try:
        portal = CouncilRegistry.get(council_id)
        application = await portal.fetch_application(reference)
        documents = await portal.fetch_application_documents(reference)
        application.documents = documents
        await portal.close()

        return ApplicationDetailResponse(
            application=application.model_dump(mode="json"),
            documents=[d.model_dump(mode="json") for d in documents],
            constraints=[c.model_dump(mode="json") for c in application.constraints],
        )

    except ApplicationNotFoundError:
        logger.warning("Application not found", reference=reference, council_id=council_id)
        raise HTTPException(status_code=404, detail=f"Application {reference} not found")
    except CouncilPortalError as e:
        logger.error("Council portal error", error=str(e), reference=reference)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error fetching application", reference=reference)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search")
async def search_applications(
    request: SearchRequest,
    council_id: str = Query(default="newcastle"),
) -> list[ApplicationResponse]:
    """Search for planning applications.

    Args:
        request: Search criteria
        council_id: Council to search
    """
    try:
        portal = CouncilRegistry.get(council_id)
        applications = await portal.search_applications(
            postcode=request.postcode,
            address=request.address,
            ward=request.ward,
            date_from=request.date_from,
            date_to=request.date_to,
            status=request.status,
            application_type=request.application_type,
            max_results=request.max_results,
        )
        await portal.close()

        return [ApplicationResponse.from_application(app) for app in applications]

    except CouncilPortalError as e:
        logger.error("Council portal error during search", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during search")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process", response_model=ProcessResponse)
async def process_application(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
) -> ProcessResponse:
    """Start processing an application.

    This fetches the application, downloads documents,
    extracts text, and prepares for report generation.

    In demo mode, returns fixture data without calling external services.

    Args:
        request: Processing request
        background_tasks: FastAPI background tasks
    """
    logger.info(
        "Processing application",
        reference=request.reference,
        council_id=request.council_id,
        mode=request.mode,
    )

    # Demo mode - use fixture data
    if request.mode == "demo":
        try:
            demo_data, actual_ref = _get_demo_application_data(request.reference)
            return _build_demo_response(
                reference=request.reference,
                council_id=request.council_id,
                demo_data=demo_data,
                actual_ref=actual_ref,
            )
        except Exception as e:
            logger.exception("Error in demo mode processing")
            raise HTTPException(
                status_code=500,
                detail="Failed to load demo application data",
            )

    # Live mode - validate and process
    try:
        portal = CouncilRegistry.get(request.council_id)
        if not portal.validate_reference(request.reference):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reference format: {request.reference}",
            )
    except ValueError as e:
        logger.warning("Invalid council ID", council_id=request.council_id)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error validating reference")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Start processing in background
    async def process_task():
        try:
            from plana.pipeline import PlanaPipeline

            pipeline = PlanaPipeline()
            await pipeline.process_application(
                reference=request.reference,
                council_id=request.council_id,
                force_reprocess=request.force_reprocess,
            )
        except Exception as e:
            logger.exception(
                "Background processing failed",
                reference=request.reference,
            )

    background_tasks.add_task(process_task)

    return ProcessResponse(
        status="processing",
        message=f"Processing started for {request.reference}",
        reference=request.reference,
        mode="live",
    )


@router.get("/councils")
async def list_councils() -> list[dict[str, str]]:
    """List available councils."""
    try:
        councils = []
        for council_id in CouncilRegistry.list_councils():
            portal = CouncilRegistry.get(council_id)
            councils.append({
                "id": council_id,
                "name": portal.council_name,
                "base_url": portal.portal_base_url,
            })
        return councils
    except Exception as e:
        logger.exception("Error listing councils")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/demo")
async def list_demo_applications() -> list[dict[str, Any]]:
    """List available demo applications for testing."""
    demos = []
    for ref, data in DEMO_APPLICATIONS.items():
        demos.append({
            "reference": ref,
            "address": data["address"]["full_address"],
            "proposal": data["proposal"][:100] + "..." if len(data["proposal"]) > 100 else data["proposal"],
            "application_type": data["application_type"],
            "documents_count": len(data.get("documents", [])),
        })
    return demos
