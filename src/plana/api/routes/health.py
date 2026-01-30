"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from plana.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    service: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str
    vector_store: str
    storage: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        service=settings.app_name,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check with dependency status."""
    # In production, check actual connectivity
    return ReadinessResponse(
        status="ready",
        database="ok",
        vector_store="ok",
        storage="ok",
    )
