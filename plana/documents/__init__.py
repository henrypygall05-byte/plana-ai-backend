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
from plana.documents.processor import (
    DrawingMetadata,
    check_plan_set_present,
    detect_scanned_pdf,
    extract_drawing_metadata,
    is_plan_or_drawing_heuristic,
)

__all__ = [
    "DocumentManager",
    "ApplicationDocument",
    "DocumentCategory",
    "DocumentIngestionResult",
    "DrawingMetadata",
    "ExtractedPlanningFacts",
    "ExtractionStatus",
    "MaterialInfoItem",
    "ProcessedDocument",
    "check_plan_set_present",
    "classify_document",
    "detect_scanned_pdf",
    "extract_drawing_metadata",
    "extract_material_info",
    "extract_planning_facts",
    "flag_external_references",
    "is_plan_or_drawing_heuristic",
    "process_documents",
    "_reclassify_from_content",
]
