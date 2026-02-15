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
    MaterialInfoItem,
    ProcessedDocument,
    classify_document,
    extract_material_info,
    process_documents,
    _reclassify_from_content,
)

__all__ = [
    "DocumentManager",
    "ApplicationDocument",
    "DocumentCategory",
    "DocumentIngestionResult",
    "ExtractionStatus",
    "MaterialInfoItem",
    "ProcessedDocument",
    "classify_document",
    "extract_material_info",
    "process_documents",
    "_reclassify_from_content",
]
