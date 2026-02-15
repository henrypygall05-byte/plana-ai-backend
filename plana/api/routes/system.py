"""System administration endpoints.

Worker health monitoring and queue management.
"""

from fastapi import APIRouter

from plana.documents.background import get_worker_stats, kick_queue

router = APIRouter()


@router.get("/worker_health")
async def worker_health() -> dict:
    """Check the background document worker's health.

    Returns queue length, worker alive status, and last job timestamp.
    """
    return get_worker_stats()


@router.post("/kick_queue")
async def kick_queue_endpoint() -> dict:
    """Idempotent kick: ensure queued documents are being processed.

    If the background worker is stopped, restarts it.
    If it's running, returns the current queue length.
    Safe to call repeatedly.
    """
    return await kick_queue()
