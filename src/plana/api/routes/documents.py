"""Document management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from plana.processing import DocumentProcessor
from plana.storage import DocumentStore

router = APIRouter()


class DocumentResponse(BaseModel):
    """Document response model."""

    id: str
    application_reference: str
    title: str
    document_type: str
    file_type: str
    source_url: str
    storage_path: str | None
    text_extracted: bool
    page_count: int | None


class TextExtractionResponse(BaseModel):
    """Text extraction response."""

    document_id: str
    text: str
    word_count: int
    extraction_method: str | None


@router.get("/{application_reference}")
async def list_documents(
    application_reference: str,
) -> list[DocumentResponse]:
    """List documents for an application.

    Args:
        application_reference: Application reference
    """
    store = DocumentStore()
    keys = await store.list_documents(application_reference=application_reference)

    # This would typically come from a database
    # For now, return empty list - documents tracked in application
    return []


@router.get("/{application_reference}/{document_id}/text")
async def get_document_text(
    application_reference: str,
    document_id: str,
) -> TextExtractionResponse:
    """Get extracted text for a document.

    Args:
        application_reference: Application reference
        document_id: Document ID
    """
    # In production, would look up document and get text
    raise HTTPException(
        status_code=404,
        detail="Document not found or text not extracted",
    )


@router.post("/{application_reference}/{document_id}/extract")
async def extract_document_text(
    application_reference: str,
    document_id: str,
) -> TextExtractionResponse:
    """Extract text from a document.

    Args:
        application_reference: Application reference
        document_id: Document ID
    """
    # Would trigger text extraction
    raise HTTPException(
        status_code=404,
        detail="Document not found",
    )
