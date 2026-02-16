"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter

from plana.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(
        status="ok",
        version="1.0.0",
        database="connected",
        timestamp=datetime.now().isoformat(),
    )


@router.get("/api/v1/health/worker")
async def worker_health() -> dict:
    """Background document-processing worker health.

    Returns worker_running, queue_depth, last_job_at, and processing
    stats so operators can confirm documents are being consumed.
    """
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
    }
