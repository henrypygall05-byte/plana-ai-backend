"""Document status and reprocessing endpoints."""

from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from plana.api.models import (
    DocumentReprocessResponse,
    DocumentStatusDocuments,
    DocumentStatusResponse,
)
from plana.documents.processor import check_plan_set_present
from plana.storage.database import Database
from plana.storage.models import StoredDocument

router = APIRouter()


def _build_status_documents(db: Database, reference: str) -> DocumentStatusDocuments:
    """Build a DocumentStatusDocuments from DB counts + plan set check."""
    counts = db.get_processing_counts(reference)
    docs = db.get_documents(reference)

    # Determine plan set presence from stored document metadata
    from plana.documents.ingestion import classify_document, DocumentCategory

    categories = []
    filenames = []
    metadata_guesses = []
    all_detected_labels = []
    for doc in docs:
        cat, _ = classify_document(doc.title, doc.doc_type, doc.title)
        categories.append(cat)
        filenames.append(doc.title)
        if doc.extracted_metadata_json:
            import json
            try:
                meta = json.loads(doc.extracted_metadata_json)
                guess = meta.get("document_type_guess", "")
                if guess:
                    metadata_guesses.append(guess)
                labels = meta.get("detected_labels", [])
                all_detected_labels.extend(labels)
            except (json.JSONDecodeError, TypeError):
                pass

    plan_set = check_plan_set_present(
        categories=categories,
        metadata_guesses=metadata_guesses or None,
        filenames=filenames,
        all_detected_labels=all_detected_labels or None,
    )

    return DocumentStatusDocuments(
        total=counts["total"],
        queued=counts["queued"],
        processing=counts["processing"],
        processed=counts["processed"],
        failed=counts["failed"],
        total_text_chars=counts["total_text_chars"],
        with_content_signal=counts["with_content_signal"],
        plan_set_present=plan_set,
    )


@router.get(
    "/status",
    response_model=DocumentStatusResponse,
)
async def get_document_status(
    reference: str = Query(
        ...,
        description="Application reference (e.g. 24/00730/FUL)",
    ),
) -> DocumentStatusResponse:
    """Get the processing status of all documents for an application.

    Pass the reference as a query parameter to avoid URL-encoding
    issues with slashes.

    Example: ``GET /api/v1/documents/status?reference=24/00730/FUL``
    """
    db = Database()
    status_docs = _build_status_documents(db, reference)

    if status_docs.total == 0:
        docs_exist = db.get_documents(reference)
        if not docs_exist:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found for reference: {reference}",
            )

    return DocumentStatusResponse(
        reference=reference,
        documents=status_docs,
    )


@router.get("/status/{reference:path}")
async def get_document_status_legacy(reference: str):
    """Legacy path-param route. Returns 400 directing clients to the query-param endpoint."""
    decoded = unquote(reference)
    raise HTTPException(
        status_code=400,
        detail=(
            f"Path-parameter routes do not support references with slashes. "
            f"Use GET /api/v1/documents/status?reference={decoded} instead."
        ),
    )


@router.api_route(
    "/reprocess",
    methods=["GET", "POST"],
)
async def reprocess_documents(
    reference: str = Query(..., description="Application reference"),
    mode: str = Query(
        "all",
        description=(
            "Reset scope: 'all' (default) resets every document; "
            "'stalled' resets only queued+failed docs."
        ),
    ),
) -> JSONResponse:
    """Reset documents for a reference and enqueue them for reprocessing.

    Supports both GET (temporary, for frontend compatibility) and POST
    (preferred).  By default (``mode=all``) every document is reset.
    Use ``mode=stalled`` to only reset documents in ``queued`` or
    ``failed`` state.

    Args:
        reference: Application reference (e.g. ``24/00730/FUL``)
        mode: 'all' (default) or 'stalled'

    Returns:
        JSON with ``status``, ``reference``, and ``documents`` counts.
    """
    db = Database()

    # Check documents exist
    docs = db.get_documents(reference)
    if not docs:
        return JSONResponse(
            status_code=404,
            content={
                "error": "unknown_reference",
                "reference": reference,
            },
        )

    # Reset documents according to mode
    if mode == "all":
        db.reset_documents_for_reference(reference)
    else:
        db.reset_stalled_for_reference(reference)

    # Kick the background worker so it picks up the re-queued docs
    # immediately instead of waiting for the next poll cycle.
    from plana.documents.background import kick_queue
    await kick_queue()

    # Build updated counts
    counts = db.get_processing_counts(reference)

    return JSONResponse(
        status_code=200,
        content={
            "status": "reprocess_enqueued",
            "reference": reference,
            "documents": {
                "total": counts["total"],
                "queued": counts["queued"],
                "processing": counts["processing"],
                "processed": counts["processed"],
                "failed": counts["failed"],
            },
        },
    )


@router.post(
    "/{doc_id}/retry",
    response_model=DocumentReprocessResponse,
)
async def retry_document(doc_id: str) -> DocumentReprocessResponse:
    """Reset a single document and enqueue it for reprocessing.

    Marks the document as 'queued', clears its extracted fields, and
    enqueues a processing job.

    Args:
        doc_id: The document identifier

    Returns:
        Reset count (1) and updated document status for the application
    """
    db = Database()

    # Verify document exists
    doc = db.get_document_by_doc_id(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {doc_id}",
        )

    # Reset single document
    was_reset = db.reset_single_document(doc_id)
    if not was_reset:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset document: {doc_id}",
        )

    # Build updated status for the application this doc belongs to
    status_docs = _build_status_documents(db, doc.reference)

    return DocumentReprocessResponse(
        reference=doc.reference,
        reset_count=1,
        documents=status_docs,
    )


@router.get("/debug")
async def debug_documents(
    reference: str = Query(
        ...,
        description="Application reference (e.g. 24/00730/FUL)",
    ),
) -> dict:
    """Diagnostic endpoint: returns per-document processing state.

    Shows counts (total/queued/processing/processed/failed), a sample of
    up to 10 documents with their id, filename, status, updated_at, and
    fail_reason, plus the oldest queued and oldest processing timestamps.

    Example: ``GET /api/v1/documents/debug?reference=24/00730/FUL``
    """
    db = Database()

    docs = db.get_documents(reference)
    if not docs:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found for reference: {reference}",
        )

    return db.get_documents_debug(reference)
