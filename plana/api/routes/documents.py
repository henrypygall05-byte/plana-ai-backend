"""Document status and reprocessing endpoints."""

from fastapi import APIRouter, HTTPException, Query

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
            except (json.JSONDecodeError, TypeError):
                pass

    plan_set = check_plan_set_present(
        categories=categories,
        metadata_guesses=metadata_guesses or None,
        filenames=filenames,
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
    "/status/{reference:path}",
    response_model=DocumentStatusResponse,
)
async def get_document_status(reference: str) -> DocumentStatusResponse:
    """Get the processing status of all documents for an application.

    Args:
        reference: Application reference (supports slashes e.g. 2024/0930/01/DET)

    Returns:
        Document processing status with counts and plan set presence
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


@router.post(
    "/reprocess",
    response_model=DocumentReprocessResponse,
)
async def reprocess_documents(
    reference: str = Query(..., description="Application reference"),
) -> DocumentReprocessResponse:
    """Reset all documents for a reference and enqueue them for reprocessing.

    Marks all documents as 'queued', clears extracted fields (text chars,
    metadata, content signal), and enqueues processing jobs for each.

    Args:
        reference: Application reference

    Returns:
        Reset count and updated document status
    """
    db = Database()

    # Check documents exist
    docs = db.get_documents(reference)
    if not docs:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found for reference: {reference}",
        )

    # Reset all documents to queued
    reset_count = db.reset_documents_for_reference(reference)

    # Build updated status
    status_docs = _build_status_documents(db, reference)

    return DocumentReprocessResponse(
        reference=reference,
        reset_count=reset_count,
        documents=status_docs,
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
