"""
Two-stage document processing pipeline.

Stage 1 — Text extraction (fast):
    PDF with embedded text → pdf_text
    Image-only / scanned PDF → OCR (tesseract)
    PNG / JPG → OCR
    Stores extracted_text_chars and extract_method.

Stage 2 — Drawing/plan understanding:
    For docs that are plans/drawings, scanned, or have zero extracted text,
    produce a lightweight metadata summary describing the drawing content.
    Stores result in extracted_metadata_json.

The processor also computes per-document flags:
    is_plan_or_drawing  — heuristic from filename + mime + category
    is_scanned          — PDF with no embedded text layer
    has_any_content_signal — True if text, metadata, or vision summary exists
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from plana.documents.ingestion import (
    DocumentCategory,
    ExtractionStatus,
    PLAN_CATEGORIES,
    classify_document,
)


# Mime types and extensions that are images
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".bmp"})
_IMAGE_MIME_PREFIXES = ("image/",)

# Mime types for PDFs
_PDF_EXTENSIONS = frozenset({".pdf"})

# Drawing-indicative filename patterns
_DRAWING_FILENAME_PATTERNS = [
    r"site[\s_-]*plan", r"block[\s_-]*plan", r"location[\s_-]*plan",
    r"floor[\s_-]*plan", r"elevation", r"section",
    r"roof[\s_-]*plan", r"street[\s_-]*scene", r"proposed[\s_-]*plan",
    r"existing[\s_-]*plan", r"cross[\s_-]*section", r"layout",
    r"drawing", r"dwg", r"plan[\s_-]*\d",
]


@dataclass
class DrawingMetadata:
    """Metadata extracted from a drawing/plan document."""

    document_type_guess: str = ""  # e.g. "site plan", "elevations", "floor plan"
    key_labels_found: list = None
    any_dimensions_detected: bool = False
    any_scale_detected: bool = False

    def __post_init__(self):
        if self.key_labels_found is None:
            self.key_labels_found = []

    def to_json(self) -> str:
        return json.dumps({
            "document_type_guess": self.document_type_guess,
            "key_labels_found": self.key_labels_found,
            "any_dimensions_detected": self.any_dimensions_detected,
            "any_scale_detected": self.any_scale_detected,
        })

    @classmethod
    def from_json(cls, raw: str) -> "DrawingMetadata":
        data = json.loads(raw)
        return cls(**data)


def is_plan_or_drawing_heuristic(
    filename: str,
    mime_type: str = "",
    category: Optional[DocumentCategory] = None,
) -> bool:
    """Determine if a document is likely a plan or drawing.

    Uses filename patterns, mime type, and classified category.
    """
    # Category-based (most reliable when classification ran)
    if category and category in PLAN_CATEGORIES:
        return True

    # Filename heuristic
    fn_lower = filename.lower()
    for pattern in _DRAWING_FILENAME_PATTERNS:
        if re.search(pattern, fn_lower):
            return True

    # Image files are often plans/photos
    ext = Path(filename).suffix.lower()
    if ext in _IMAGE_EXTENSIONS:
        return True
    if mime_type and any(mime_type.startswith(p) for p in _IMAGE_MIME_PREFIXES):
        return True

    return False


def detect_scanned_pdf(path: Path) -> bool:
    """Check if a PDF has no embedded text (i.e. it's scanned/image-only).

    Returns True if the PDF exists and has zero extractable text characters
    across all pages.
    """
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return False
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            if len(text) > 20:  # threshold: a few real words
                return False
        return True
    except Exception:
        return False


def extract_drawing_metadata(
    filename: str,
    category: Optional[DocumentCategory] = None,
    extracted_text: str = "",
) -> DrawingMetadata:
    """Produce a lightweight metadata summary for a drawing/plan.

    This is Stage 2 of the processing pipeline.  It analyses available
    signals (filename, category, any extracted text snippets) to produce
    structured metadata about the drawing.

    In production this would call a vision model; here we use heuristics
    to populate the metadata from filename patterns and any OCR text.
    """
    meta = DrawingMetadata()

    # Document type guess from category or filename
    if category and category != DocumentCategory.OTHER:
        meta.document_type_guess = category.value.replace("_", " ")
    else:
        fn_lower = filename.lower()
        type_patterns = [
            (r"site[\s_-]*plan", "site plan"),
            (r"location[\s_-]*plan", "location plan"),
            (r"block[\s_-]*plan", "block plan"),
            (r"floor[\s_-]*plan", "floor plan"),
            (r"ground[\s_-]*floor", "floor plan"),
            (r"first[\s_-]*floor", "floor plan"),
            (r"elevation", "elevations"),
            (r"section", "sections"),
            (r"roof[\s_-]*plan", "roof plan"),
            (r"street[\s_-]*scene", "street scene"),
            (r"drainage|suds", "drainage"),
            (r"bng|biodiversity", "BNG"),
        ]
        for pat, type_name in type_patterns:
            if re.search(pat, fn_lower):
                meta.document_type_guess = type_name
                break

    # Key labels from extracted text (if any)
    if extracted_text:
        text_lower = extracted_text.lower()
        label_patterns = {
            "scale": r"(?:scale|1:\d+|1\s*:\s*\d+)",
            "north arrow": r"north",
            "boundary": r"(?:boundary|red\s*line|site\s*boundary)",
            "proposed": r"proposed",
            "existing": r"existing",
            "dimensions": r"\d+(?:\.\d+)?\s*(?:m|mm|metres?|meters?)",
            "area": r"\d+(?:\.\d+)?\s*(?:sq\.?\s*m|m2|m²|sqm)",
        }
        for label, pat in label_patterns.items():
            if re.search(pat, text_lower):
                meta.key_labels_found.append(label)

        # Dimension detection
        if re.search(r"\d+(?:\.\d+)?\s*(?:m|mm)\b", text_lower):
            meta.any_dimensions_detected = True

        # Scale detection
        if re.search(r"1\s*:\s*\d+", text_lower):
            meta.any_scale_detected = True
    else:
        # Even without text, filename may hint at content
        fn_lower = filename.lower()
        if re.search(r"1[_\s:-]*\d{2,4}", fn_lower):
            meta.any_scale_detected = True

    return meta


# ---- Plan Set Presence Check ----

def check_plan_set_present(
    categories: List[DocumentCategory],
    metadata_guesses: Optional[List[str]] = None,
    filenames: Optional[List[str]] = None,
) -> bool:
    """Determine if a minimal plan set is present.

    A plan set requires:
    - At least one of: site plan OR location plan
    AND
    - At least one of: elevations OR floor plans OR sections

    Detection uses (in priority order):
    1. Classified DocumentCategory values
    2. extracted_metadata_json.document_type_guess values
    3. Filename heuristics
    """
    has_location = False
    has_detail = False

    # --- Check from categories ---
    location_cats = {DocumentCategory.SITE_PLAN, DocumentCategory.LOCATION_PLAN}
    detail_cats = {DocumentCategory.ELEVATION, DocumentCategory.FLOOR_PLAN, DocumentCategory.SECTION_DRAWING}

    for cat in categories:
        if cat in location_cats:
            has_location = True
        if cat in detail_cats:
            has_detail = True

    if has_location and has_detail:
        return True

    # --- Check from metadata guesses ---
    if metadata_guesses:
        for guess in metadata_guesses:
            g = guess.lower()
            if g in ("site plan", "location plan"):
                has_location = True
            if g in ("elevations", "elevation", "floor plan", "sections"):
                has_detail = True

    if has_location and has_detail:
        return True

    # --- Check from filenames ---
    if filenames:
        location_patterns = [r"site[\s_-]*plan", r"location[\s_-]*plan"]
        detail_patterns = [r"elevation", r"floor[\s_-]*plan", r"section"]
        for fn in filenames:
            fn_lower = fn.lower()
            for pat in location_patterns:
                if re.search(pat, fn_lower):
                    has_location = True
            for pat in detail_patterns:
                if re.search(pat, fn_lower):
                    has_detail = True

    return has_location and has_detail
