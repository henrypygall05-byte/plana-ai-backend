"""
Document extraction worker.

Polls the database for documents with ``processing_status = 'queued'``,
processes each one (text extraction + classification + drawing metadata),
and marks them ``processed`` or ``failed``.

Run standalone:
    python -m plana.documents.worker          # one-shot (process all then exit)
    python -m plana.documents.worker --loop    # poll continuously

The worker is designed to be safe for a single instance.  For multi-
instance deployments, ``claim_queued_document()`` uses an atomic SQL
UPDATE so two workers cannot claim the same row.
"""

import argparse
import signal
import sys
import time
from pathlib import Path
from typing import Optional

from plana.core.logging import get_logger
from plana.documents.ingestion import (
    ExtractionStatus,
    classify_document,
)
from plana.documents.processor import (
    detect_scanned_pdf,
    extract_drawing_metadata,
    is_plan_or_drawing_heuristic,
)
from plana.storage.database import Database
from plana.storage.models import StoredDocument

logger = get_logger(__name__)

# Default poll interval in seconds when running in --loop mode.
DEFAULT_POLL_INTERVAL = 2.0


def _extract_text(path: Path) -> tuple[str, str]:
    """Extract text from a file on disk.

    Returns ``(text, method)`` where *method* is one of
    ``pdf_text``, ``ocr``, ``text_file``, or ``none``.
    """
    if not path.is_file():
        return "", "none"

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            texts = []
            pages_ok = 0
            for page in reader.pages:
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages_ok += 1
                    texts.append(page_text)
                except Exception:
                    texts.append("")

            full_text = "\n".join(texts)
            coverage = pages_ok / len(reader.pages) if reader.pages else 0

            if coverage > 0:
                return full_text, "pdf_text"

            # OCR fallback for scanned PDFs
            ocr_text, ocr_ok = _ocr_fallback(path)
            if ocr_ok > 0:
                return ocr_text, "ocr"

            return "", "none"
        except Exception:
            return "", "none"

    if suffix in (".txt", ".csv", ".html", ".htm"):
        try:
            return path.read_text(errors="replace"), "text_file"
        except Exception:
            return "", "none"

    if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"):
        ocr_text = _ocr_image(path)
        if ocr_text:
            return ocr_text, "ocr"
        return "", "none"

    return "", "none"


def _ocr_fallback(path: Path) -> tuple[str, int]:
    """OCR fallback for scanned PDFs."""
    try:
        from pdf2image import convert_from_path  # type: ignore[import-untyped]
        import pytesseract  # type: ignore[import-untyped]
    except ImportError:
        return "", 0

    try:
        images = convert_from_path(str(path), dpi=200)
    except Exception:
        return "", 0

    texts: list[str] = []
    pages_ok = 0
    for img in images:
        try:
            page_text = pytesseract.image_to_string(img) or ""
            if page_text.strip():
                pages_ok += 1
            texts.append(page_text)
        except Exception:
            texts.append("")

    return "\n".join(texts), pages_ok


def _ocr_image(path: Path) -> str:
    """OCR a single image file."""
    try:
        import pytesseract  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]
    except ImportError:
        return ""
    try:
        img = Image.open(str(path))
        return pytesseract.image_to_string(img) or ""
    except Exception:
        return ""


def process_one(doc: StoredDocument, db: Database) -> None:
    """Process a single document that has already been claimed.

    1. Classify (category, is_plan_or_drawing, is_scanned).
    2. Extract text (pdf_text / ocr / text_file).
    3. If drawing, produce metadata.
    4. Mark processed or failed.

    Structured log events emitted:
        ``doc_processing_start``  — claimed, beginning work
        ``doc_processing_success`` — extraction complete
        ``doc_processing_fail``   — unrecoverable error (reason stored in DB)
    """
    doc_id = doc.doc_id
    reference = doc.reference
    t_start = time.monotonic()

    logger.info(
        "doc_processing_start",
        reference=reference,
        document_id=doc_id,
        title=doc.title,
        local_path=doc.local_path,
    )

    try:
        # ---- Classification ----
        filename = doc.title or ""
        if doc.url:
            filename = doc.url.rsplit("/", 1)[-1] or filename
        category, _ = classify_document(doc.title, doc.doc_type, filename)

        plan_drawing = doc.is_plan_or_drawing or is_plan_or_drawing_heuristic(
            filename, doc.mime_type, category,
        )

        # ---- Text extraction ----
        local_path = Path(doc.local_path) if doc.local_path else None
        text = ""
        method = "none"
        scanned = False

        if local_path and local_path.is_file():
            text, method = _extract_text(local_path)
            if local_path.suffix.lower() == ".pdf" and method == "none":
                scanned = True
            elif local_path.suffix.lower() == ".pdf" and method == "ocr":
                scanned = True
        elif plan_drawing:
            method = "drawing_only"

        # If no text but it is a plan/drawing, set method to drawing_only
        if not text and plan_drawing and method == "none":
            method = "drawing_only"

        # ---- Drawing metadata (Stage 2) ----
        metadata_json: Optional[str] = None
        if plan_drawing:
            meta = extract_drawing_metadata(filename, category, text)
            metadata_json = meta.to_json()

        has_signal = bool(text) or bool(metadata_json) or plan_drawing

        # ---- Mark processed ----
        db.mark_document_processed(
            doc_id,
            extract_method=method,
            extracted_text_chars=len(text),
            extracted_metadata_json=metadata_json,
            is_plan_or_drawing=plan_drawing,
            is_scanned=scanned,
            has_any_content_signal=has_signal,
        )
        elapsed_ms = round((time.monotonic() - t_start) * 1000, 1)
        logger.info(
            "doc_processing_success",
            reference=reference,
            document_id=doc_id,
            method=method,
            chars=len(text),
            is_drawing=plan_drawing,
            is_scanned=scanned,
            has_signal=has_signal,
            duration_ms=elapsed_ms,
        )

    except Exception as exc:
        elapsed_ms = round((time.monotonic() - t_start) * 1000, 1)
        reason = f"{type(exc).__name__}: {exc}"
        logger.error(
            "doc_processing_fail",
            reference=reference,
            document_id=doc_id,
            error=reason,
            duration_ms=elapsed_ms,
        )
        try:
            db.mark_document_failed(doc_id, reason=reason)
        except Exception as mark_exc:
            logger.error(
                "doc_mark_failed_error",
                reference=reference,
                document_id=doc_id,
                error=str(mark_exc),
            )


def drain_queue(db: Optional[Database] = None) -> int:
    """Process all queued documents until the queue is empty.

    Returns the number of documents processed.
    """
    if db is None:
        db = Database()

    logger.info("worker_drain_start")
    t_start = time.monotonic()
    processed = 0
    failed = 0
    while True:
        doc = db.claim_queued_document()
        if doc is None:
            break
        try:
            process_one(doc, db)
        except Exception:
            failed += 1
        processed += 1

    elapsed_ms = round((time.monotonic() - t_start) * 1000, 1)
    logger.info(
        "worker_drain_complete",
        processed=processed,
        failed=failed,
        duration_ms=elapsed_ms,
    )
    return processed


def run_loop(poll_interval: float = DEFAULT_POLL_INTERVAL) -> None:
    """Run the worker in a continuous polling loop.

    Ctrl-C or SIGTERM will exit gracefully.
    """
    db = Database()
    running = True
    total_processed = 0

    def _stop(signum, frame):
        nonlocal running
        logger.info("worker_shutdown", signal=signum, total_processed=total_processed)
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    logger.info("worker_started", poll_interval=poll_interval, mode="loop")

    while running:
        doc = db.claim_queued_document()
        if doc is None:
            time.sleep(poll_interval)
            continue
        process_one(doc, db)
        total_processed += 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plana document extraction worker",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously (poll for queued docs); "
             "default is one-shot (drain queue then exit).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Poll interval in seconds (default: {DEFAULT_POLL_INTERVAL})",
    )
    args = parser.parse_args()

    if args.loop:
        run_loop(poll_interval=args.interval)
    else:
        count = drain_queue()
        logger.info("worker_drained", processed=count)
        print(f"Processed {count} documents.")


if __name__ == "__main__":
    main()
