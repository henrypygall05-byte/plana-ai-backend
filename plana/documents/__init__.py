"""
Document management module for planning applications.

Handles listing, downloading, deduplicating,
classifying, and extracting text from submitted planning documents.
"""

from plana.documents.manager import DocumentManager, ApplicationDocument
from plana.documents.ingestion import (
    DocumentCategory,
    DocumentIngestionResult,
    ExtractionStatus,
    ProcessedDocument,
    classify_document,
    process_documents,
)

__all__ = [
    "DocumentManager",
    "ApplicationDocument",
    "DocumentCategory",
    "DocumentIngestionResult",
    "ExtractionStatus",
    "ProcessedDocument",
    "classify_document",
    "process_documents",
]
