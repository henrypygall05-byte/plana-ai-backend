"""Application management endpoints."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from plana.config import get_settings
from plana.core.models import Application, ApplicationStatus, ApplicationType
from plana.councils import CouncilRegistry
from plana.councils.base import ApplicationNotFoundError, CouncilPortalError

router = APIRouter()


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
        raise HTTPException(status_code=404, detail=f"Application {reference} not found")
    except CouncilPortalError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process")
async def process_application(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Start processing an application.

    This fetches the application, downloads documents,
    extracts text, and prepares for report generation.

    Args:
        request: Processing request
        background_tasks: FastAPI background tasks
    """
    from plana.pipeline import PlanaPipeline

    # Validate reference
    try:
        portal = CouncilRegistry.get(request.council_id)
        if not portal.validate_reference(request.reference):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reference format: {request.reference}",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Start processing in background
    async def process_task():
        pipeline = PlanaPipeline()
        await pipeline.process_application(
            reference=request.reference,
            council_id=request.council_id,
            force_reprocess=request.force_reprocess,
        )

    background_tasks.add_task(process_task)

    return {
        "status": "processing",
        "message": f"Processing started for {request.reference}",
        "reference": request.reference,
    }


@router.get("/councils")
async def list_councils() -> list[dict[str, str]]:
    """List available councils."""
    councils = []
    for council_id in CouncilRegistry.list_councils():
        portal = CouncilRegistry.get(council_id)
        councils.append({
            "id": council_id,
            "name": portal.council_name,
            "base_url": portal.portal_base_url,
        })
    return councils
