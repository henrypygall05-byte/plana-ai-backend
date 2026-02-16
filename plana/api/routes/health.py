"""Health check endpoints."""

import os
import socket
from datetime import datetime

from fastapi import APIRouter, Query

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


@router.get("/api/v1/health/build")
async def build_info() -> dict:
    """Return the exact code version and environment identity.

    Use this to confirm which commit is actually running after a deploy.
    """
    return {
        "version": "1.0.0",
        "git_sha": os.environ.get("RENDER_GIT_COMMIT"),
        "render_service_name": os.environ.get("RENDER_SERVICE_NAME"),
        "render_instance_id": os.environ.get("RENDER_INSTANCE_ID"),
        "hostname": socket.gethostname(),
        "cwd": os.getcwd(),
    }


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

    # DB identity — proves API handler + background worker see the same file
    from plana.storage.database import Database
    db = Database()
    db_path = str(db.db_path)
    db_exists = db.db_path.exists()
    db_size_bytes = db.db_path.stat().st_size if db_exists else 0

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
        # DB identity
        "db_path": db_path,
        "db_exists": db_exists,
        "db_size_bytes": db_size_bytes,
        # environment identity
        "cwd": os.getcwd(),
        "hostname": socket.gethostname(),
        "render_service_name": os.environ.get("RENDER_SERVICE_NAME"),
        "render_instance_id": os.environ.get("RENDER_INSTANCE_ID"),
        "git_sha": os.environ.get("RENDER_GIT_COMMIT"),
        # bonus context
        "queue_depth": stats.get("queue_length", 0),
        "total_processed": stats.get("total_processed", 0),
        "total_failed": stats.get("total_failed", 0),
    }


@router.get("/api/v1/health/reference_exists")
async def reference_exists(
    reference: str = Query(..., description="Application reference to check"),
) -> dict:
    """Check whether a reference exists in the DB and return doc status counts.

    This is a diagnostic endpoint to prove the API handler can see
    the same data the UI / worker sees.
    """
    from plana.storage.database import Database

    db = Database()
    docs = db.get_documents(reference)

    if not docs:
        return {
            "reference": reference,
            "exists": False,
            "doc_counts": None,
        }

    counts = db.get_processing_counts(reference)
    return {
        "reference": reference,
        "exists": True,
        "doc_counts": {
            "total": counts["total"],
            "queued": counts["queued"],
            "processing": counts["processing"],
            "processed": counts["processed"],
            "failed": counts["failed"],
        },
    }
