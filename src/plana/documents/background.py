"""
In-process background document worker.

Runs as an asyncio task inside the FastAPI process so document extraction
works even when the standalone ``python -m plana.documents.worker`` service
is not deployed.

Usage (in the app lifespan)::

    from plana.documents.background import start_background_worker, stop_background_worker

    @asynccontextmanager
    async def lifespan(app):
        start_background_worker()
        yield
        await stop_background_worker()
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from plana.core.logging import get_logger
from plana.storage.database import Database

logger = get_logger(__name__)

# Module-level state so health endpoint can inspect it.
_worker_task: Optional[asyncio.Task] = None
_stats = {
    "started_at": None,
    "last_poll_at": None,
    "last_job_completed_at": None,
    "total_processed": 0,
    "total_failed": 0,
    "alive": False,
}

POLL_INTERVAL = 3.0  # seconds


def get_worker_stats() -> dict:
    """Return a snapshot of the background worker's health stats."""
    db = Database()
    try:
        counts = db.get_processing_counts("")  # empty ref = global
    except Exception:
        counts = {}

    # Count total queued across all references
    queue_length = 0
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM documents WHERE processing_status = 'queued'"
            )
            row = cursor.fetchone()
            queue_length = row["cnt"] if row else 0
    except Exception:
        pass

    return {
        **_stats,
        "queue_length": queue_length,
    }


def _process_one_sync(doc, db) -> None:
    """Delegate to the existing worker.process_one (blocking)."""
    from plana.documents.worker import process_one
    process_one(doc, db)


async def _worker_loop() -> None:
    """Async loop that polls for queued documents and processes them."""
    _stats["alive"] = True
    _stats["started_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        "background_worker_started",
        poll_interval=POLL_INTERVAL,
    )

    db = Database()

    while True:
        try:
            _stats["last_poll_at"] = datetime.now(timezone.utc).isoformat()
            doc = db.claim_queued_document()

            if doc is None:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            logger.info(
                "background_worker_claimed",
                reference=doc.reference,
                doc_id=doc.doc_id,
                title=doc.title,
            )

            # Run blocking extraction in a thread so we don't block the
            # event loop (PDF parsing, OCR, etc. are CPU/IO heavy).
            await asyncio.to_thread(_process_one_sync, doc, db)

            _stats["total_processed"] += 1
            _stats["last_job_completed_at"] = datetime.now(timezone.utc).isoformat()

        except asyncio.CancelledError:
            logger.info("background_worker_stopping")
            break
        except Exception as exc:
            _stats["total_failed"] += 1
            logger.error("background_worker_error", error=str(exc))
            await asyncio.sleep(POLL_INTERVAL)

    _stats["alive"] = False
    logger.info(
        "background_worker_stopped",
        total_processed=_stats["total_processed"],
        total_failed=_stats["total_failed"],
    )


def start_background_worker() -> None:
    """Start the background worker as an asyncio task."""
    global _worker_task
    if _worker_task is not None and not _worker_task.done():
        logger.info("background_worker_already_running")
        return

    loop = asyncio.get_event_loop()
    _worker_task = loop.create_task(_worker_loop())
    logger.info("background_worker_task_created")


async def stop_background_worker() -> None:
    """Gracefully cancel the background worker task."""
    global _worker_task
    if _worker_task is None or _worker_task.done():
        return

    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    _worker_task = None


async def kick_queue() -> dict:
    """Idempotent kick: if documents are queued in DB but the worker
    hasn't picked them up, nudge the worker by triggering a drain.

    Returns a summary of what was found / done.
    """
    db = Database()

    # Count orphaned queued documents
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM documents WHERE processing_status = 'queued'"
        )
        row = cursor.fetchone()
        queued_count = row["cnt"] if row else 0

    if queued_count == 0:
        return {"queued_found": 0, "action": "none", "message": "No queued documents"}

    # The background worker is already polling, but if it's not running
    # we can start it or do a synchronous drain.
    global _worker_task
    if _worker_task is None or _worker_task.done():
        start_background_worker()
        return {
            "queued_found": queued_count,
            "action": "worker_restarted",
            "message": f"Found {queued_count} queued docs; restarted background worker",
        }

    # Worker is running — it will pick them up on next poll.
    return {
        "queued_found": queued_count,
        "action": "worker_running",
        "message": f"Found {queued_count} queued docs; worker is active and will process them",
    }
