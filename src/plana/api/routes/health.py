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


@router.get("/api/v1/health/worker")
async def worker_health() -> dict:
    """Background document-processing worker health.

    Returns worker_running, queue_depth, last_job_at, and processing
    stats so operators can confirm documents are being consumed.
    """
    import os
    from plana.documents.background import get_worker_stats

    stats = get_worker_stats()
    return {
        "worker_running": stats.get("alive", False),
        "queue_depth": stats.get("queue_length", 0),
        "last_job_at": stats.get("last_job_completed_at"),
        "started_at": stats.get("started_at"),
        "last_poll_at": stats.get("last_poll_at"),
        "total_processed": stats.get("total_processed", 0),
        "total_failed": stats.get("total_failed", 0),
        "last_error": stats.get("last_error"),
        "consecutive_errors": stats.get("consecutive_errors", 0),
        "worker_pid": stats.get("pid"),
        "server_pid": os.getpid(),
    }
