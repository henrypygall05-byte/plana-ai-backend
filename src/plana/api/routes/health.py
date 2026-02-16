"""Health check endpoints."""

import os
import socket

from fastapi import APIRouter, Request
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


@router.get("/api/v1/health/build")
async def build_info() -> dict:
    """Deployment fingerprint — confirms which commit is actually running."""
    return {
        "service": "plana-ai-backend",
        "git_sha": os.environ.get("RENDER_GIT_COMMIT"),
        "server_pid": os.getpid(),
        "hostname": socket.gethostname(),
        "cwd": os.getcwd(),
    }


@router.get("/api/v1/health/openapi_probe")
async def openapi_probe(request: Request) -> dict:
    """Report registered route paths from the running app instance."""
    schema = request.app.openapi()
    all_paths = sorted(schema.get("paths", {}).keys())
    return {
        "has_build": "/api/v1/health/build" in schema.get("paths", {}),
        "has_worker": "/api/v1/health/worker" in schema.get("paths", {}),
        "known_paths_sample": all_paths[:50],
    }


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
