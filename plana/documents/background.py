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
import traceback
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
    "last_heartbeat_at": None,
    "last_claim_at": None,
    "last_processed_at": None,
    "total_processed": 0,
    "total_failed": 0,
    "consecutive_errors": 0,
    "loop_iterations": 0,
    "last_error": None,
    "pid": None,
    "alive": False,
}

POLL_INTERVAL = 3.0  # seconds
HEARTBEAT_INTERVAL = 30.0  # seconds


def get_worker_stats() -> dict:
    """Return a snapshot of the background worker's health stats."""
    global _worker_task

    # Detect if the task object is done (crashed or cancelled)
    # even though _stats["alive"] might be stale.
    task_alive = _worker_task is not None and not _worker_task.done()

    db = Database()

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
    _stats["alive"] = True
    _stats["started_at"] = datetime.now(timezone.utc).isoformat()
    _stats["consecutive_errors"] = 0
    _stats["loop_iterations"] = 0

    logger.info(
        "worker_started",
        pid=os.getpid(),
        poll_interval=POLL_INTERVAL,
    )

    db = Database()
    last_heartbeat = time.monotonic()

    # On startup, recover any documents stuck in 'processing' from a
    # previous crash/redeploy.
    try:
        recovered = db.recover_stale_processing()
        if recovered:
            logger.info("background_worker_recovered_stale", count=recovered)
    except Exception as exc:
        logger.warning("background_worker_recovery_error", error=str(exc))

    while True:
        try:
            now_mono = time.monotonic()
            now_utc = datetime.now(timezone.utc).isoformat()

            _stats["loop_iterations"] += 1
            _stats["last_poll_at"] = now_utc

            # Periodic heartbeat log (every 30s)
            if now_mono - last_heartbeat >= HEARTBEAT_INTERVAL:
                last_heartbeat = now_mono
                _stats["last_heartbeat_at"] = now_utc
                logger.info(
                    "worker_heartbeat",
                    pid=os.getpid(),
                    loop_iterations=_stats["loop_iterations"],
                    total_processed=_stats["total_processed"],
                    total_failed=_stats["total_failed"],
                    consecutive_errors=_stats["consecutive_errors"],
                    queue_length=get_worker_stats().get("queue_length", 0),
                )

            doc = db.claim_next_document()

            if doc is None:
                _stats["consecutive_errors"] = 0
                await asyncio.sleep(POLL_INTERVAL)
                continue

            _stats["last_claim_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                "doc_claimed",
                doc_id=doc.doc_id,
                filename=doc.title,
                reference=doc.reference,
            )

            # Run blocking extraction in a thread so we don't block the
            # event loop (PDF parsing, OCR, etc. are CPU/IO heavy).
            await asyncio.to_thread(_process_one_sync, doc, db)

            _stats["total_processed"] += 1
            _stats["consecutive_errors"] = 0
            _stats["last_processed_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                "doc_processed",
                doc_id=doc.doc_id,
                filename=doc.title,
                reference=doc.reference,
            )

        except asyncio.CancelledError:
            logger.info("background_worker_stopping")
            break
        except Exception as exc:
            _stats["total_failed"] += 1
            _stats["consecutive_errors"] += 1
            _stats["last_error"] = f"{type(exc).__name__}: {exc}"

            # Log doc_failed if we have a doc context, else generic worker_error
            tb = traceback.format_exc()
            if 'doc' in dir() and doc is not None:
                logger.error(
                    "doc_failed",
                    doc_id=getattr(doc, "doc_id", "unknown"),
                    filename=getattr(doc, "title", "unknown"),
                    reference=getattr(doc, "reference", "unknown"),
                    error=str(exc),
                    traceback=tb,
                )
            else:
                logger.error(
                    "worker_error",
                    error=str(exc),
                    traceback=tb,
                    consecutive_errors=_stats["consecutive_errors"],
                )

            # Back off more on repeated failures to avoid tight error loops
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

    Safe to call multiple times — restarts the worker if it crashed.
    """
    global _worker_task
    if _worker_task is not None and not _worker_task.done():
        logger.info("background_worker_already_running")
        return

    if _worker_task is not None and _worker_task.done():
        # Worker crashed — log the exception before restarting.
        exc = _worker_task.exception() if not _worker_task.cancelled() else None
        logger.warning(
            "background_worker_restarting_after_crash",
            previous_error=str(exc) if exc else "cancelled",
        )

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
    """Idempotent kick: recover stale docs, ensure worker is running.

    1. Recover documents stuck in ``processing`` (crashed worker).
    2. Count remaining queued documents.
    3. (Re)start the worker if it's not running.

    Returns a summary of what was found / done.
    """
    db = Database()

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
