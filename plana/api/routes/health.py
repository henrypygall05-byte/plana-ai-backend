"""Health check endpoints."""

import os
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
    """Background document-processing worker diagnostic endpoint.

    Returns the exact state of the asyncio worker task, its PID,
    timing information, loop counters, and error state.  Designed
    to be the first thing you hit when documents are stuck.
    """
    from plana.documents.background import get_worker_stats, _worker_task

    stats = get_worker_stats()

    # worker_task_running reflects the ACTUAL asyncio task state,
    # not a flag that the worker loop set — it cannot lie.
    task_running = _worker_task is not None and not _worker_task.done()

    # Detect uvicorn worker count hint
    workers_env = os.environ.get("WEB_CONCURRENCY", "")
    if workers_env:
        uvicorn_hint = f"WEB_CONCURRENCY={workers_env}"
    else:
        uvicorn_hint = "WEB_CONCURRENCY not set (default 1 worker)"

    return {
        "server_pid": os.getpid(),
        "worker_pid": stats.get("pid"),
        "worker_task_running": task_running,
        "worker_started_at": stats.get("started_at"),
        "last_heartbeat_at": stats.get("last_heartbeat_at"),
        "last_claim_at": stats.get("last_claim_at"),
        "last_processed_at": stats.get("last_processed_at"),
        "loop_iterations": stats.get("loop_iterations", 0),
        "consecutive_errors": stats.get("consecutive_errors", 0),
        "last_error": stats.get("last_error"),
        "uvicorn_workers_hint": uvicorn_hint,
        # bonus context
        "queue_depth": stats.get("queue_length", 0),
        "total_processed": stats.get("total_processed", 0),
        "total_failed": stats.get("total_failed", 0),
    }
