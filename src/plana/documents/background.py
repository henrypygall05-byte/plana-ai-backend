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
import os
import time
from datetime import datetime, timezone
from typing import Optional

from plana.core.logging import get_logger
from plana.storage.database import Database, get_database

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
    "last_error": None,
    "consecutive_errors": 0,
    "pid": None,
}

POLL_INTERVAL = 3.0  # seconds


def get_worker_stats() -> dict:
    """Return a snapshot of the background worker's health stats."""
    global _worker_task

    # Detect if the task object is done (crashed or cancelled)
    # even though _stats["alive"] might be stale.
    task_alive = _worker_task is not None and not _worker_task.done()

    db = get_database()
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
        "alive": task_alive,  # override with actual task state
        "queue_length": queue_length,
    }


def _process_one_sync(doc, db) -> None:
    """Delegate to the existing worker.process_one (blocking)."""
    from plana.documents.worker import process_one
    process_one(doc, db)


async def _worker_loop() -> None:
    """Async loop that polls for queued documents and processes them."""
    _stats["pid"] = os.getpid()
    _stats["started_at"] = datetime.now(timezone.utc).isoformat()
    _stats["alive"] = True
    _stats["consecutive_errors"] = 0

    logger.info(
        "background_worker_started",
        pid=os.getpid(),
        poll_interval=POLL_INTERVAL,
    )

    # Database init inside try so we can log and retry on failure.
    try:
        db = get_database()
    except Exception as exc:
        logger.error("background_worker_db_init_failed", error=str(exc))
        _stats["alive"] = False
        _stats["last_error"] = f"DB init failed: {exc}"
        raise

    # On startup, recover any documents stuck in 'processing' from a
    # previous crash/redeploy.
    try:
        recovered = db.recover_stale_processing()
        if recovered:
            logger.info("background_worker_recovered_stale", count=recovered)
    except Exception as exc:
        logger.warning("background_worker_recovery_error", error=str(exc))

    doc = None  # initialise so except handler never hits NameError
    while True:
        try:
            _stats["last_poll_at"] = datetime.now(timezone.utc).isoformat()
            doc = db.claim_queued_document()

            if doc is None:
                _stats["consecutive_errors"] = 0
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
            _stats["consecutive_errors"] = 0
            _stats["last_job_completed_at"] = datetime.now(timezone.utc).isoformat()

        except asyncio.CancelledError:
            logger.info("background_worker_stopping")
            break
        except Exception as exc:
            _stats["total_failed"] += 1
            _stats["consecutive_errors"] += 1
            _stats["last_error"] = f"{type(exc).__name__}: {exc}"

            # If process_one raised, the document is stuck in 'processing'.
            # Mark it failed so it doesn't block the queue.
            if doc is not None:
                try:
                    db.mark_document_failed(
                        doc.doc_id,
                        reason=f"Worker error: {type(exc).__name__}: {exc}",
                    )
                    logger.warning(
                        "background_worker_marked_failed",
                        doc_id=doc.doc_id,
                        error=str(exc),
                    )
                except Exception:
                    pass

            logger.error(
                "background_worker_error",
                error=str(exc),
                consecutive_errors=_stats["consecutive_errors"],
            )

            # Back off on repeated failures to avoid tight error loops.
            backoff = min(POLL_INTERVAL * _stats["consecutive_errors"], 30.0)
            await asyncio.sleep(backoff)

    _stats["alive"] = False
    logger.info(
        "background_worker_stopped",
        total_processed=_stats["total_processed"],
        total_failed=_stats["total_failed"],
    )


def start_background_worker() -> None:
    """Start the background worker as an asyncio task.

    Safe to call from sync code inside an async context (e.g. lifespan).
    """
    global _worker_task
    if _worker_task is not None and not _worker_task.done():
        logger.info("background_worker_already_running", pid=os.getpid())
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    _worker_task = loop.create_task(_worker_loop(), name="plana-document-worker")
    logger.info(
        "background_worker_task_created",
        pid=os.getpid(),
        task_name=_worker_task.get_name(),
    )


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
    """Idempotent kick: recover stale docs, ensure worker is running.

    1. Recover documents stuck in ``processing`` (crashed worker).
    2. Count remaining queued documents.
    3. (Re)start the worker if it's not running.

    Returns a summary of what was found / done.
    """
    db = get_database()

    # 1. Recover documents stuck in 'processing' from a previous crash.
    recovered = 0
    try:
        recovered = db.recover_stale_processing()
        if recovered:
            logger.info("kick_queue_recovered_stale", count=recovered)
    except Exception:
        pass

    # 2. Count queued documents (including any just recovered).
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM documents WHERE processing_status = 'queued'"
        )
        row = cursor.fetchone()
        queued_count = row["cnt"] if row else 0

    if queued_count == 0 and recovered == 0:
        return {"queued_found": 0, "recovered": 0, "action": "none", "message": "No queued documents"}

    # 3. Ensure the background worker is running.
    global _worker_task
    if _worker_task is None or _worker_task.done():
        # Log why the previous task died, if applicable.
        if _worker_task is not None and _worker_task.done():
            exc = _worker_task.exception() if not _worker_task.cancelled() else None
            logger.warning(
                "kick_queue_worker_was_dead",
                exception=str(exc) if exc else "cancelled",
            )
        start_background_worker()
        return {
            "queued_found": queued_count,
            "recovered": recovered,
            "action": "worker_restarted",
            "message": f"Found {queued_count} queued docs (recovered {recovered}); restarted background worker",
        }

    # Worker is running — it will pick them up on next poll.
    return {
        "queued_found": queued_count,
        "recovered": recovered,
        "action": "worker_running",
        "message": f"Found {queued_count} queued docs (recovered {recovered}); worker is active",
    }
