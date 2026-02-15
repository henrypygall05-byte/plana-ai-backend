"""
Document management module for planning applications.

Handles listing, downloading, deduplicating,
classifying, and extracting text from submitted planning documents.
"""

from plana.documents.manager import DocumentManager, ApplicationDocument
from plana.documents.ingestion import (
    DocumentCategory,
    DocumentIngestionResult,
    ExtractedPlanningFacts,
    ExtractionStatus,
    MaterialInfoItem,
    ProcessedDocument,
    classify_document,
    extract_material_info,
    extract_planning_facts,
    flag_external_references,
    process_documents,
    _reclassify_from_content,
)

__all__ = [
    "DocumentManager",
    "ApplicationDocument",
    "DocumentCategory",
    "DocumentIngestionResult",
    "ExtractedPlanningFacts",
    "ExtractionStatus",
    "MaterialInfoItem",
    "ProcessedDocument",
    "classify_document",
    "extract_material_info",
    "extract_planning_facts",
    "flag_external_references",
    "process_documents",
    "_reclassify_from_content",
]
