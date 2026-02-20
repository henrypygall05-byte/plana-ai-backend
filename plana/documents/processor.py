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

# Title-block drawing-type patterns detected from extracted text / OCR.
# Each pattern maps to a normalised label used by check_plan_set_present.
_TEXT_DRAWING_TYPE_PATTERNS: list[tuple[str, str]] = [
    # Plan types
    (r"location\s*plan", "location plan"),
    (r"site\s*(?:plan|layout)", "site plan"),
    (r"block\s*plan", "block plan"),
    (r"floor\s*plan", "floor plan"),
    (r"ground\s*floor\s*(?:plan|layout)?", "floor plan"),
    (r"first\s*floor\s*(?:plan|layout)?", "floor plan"),
    (r"second\s*floor\s*(?:plan|layout)?", "floor plan"),
    (r"proposed\s*(?:plan|layout)\b", "floor plan"),
    (r"existing\s*(?:plan|layout)\b", "floor plan"),
    # Elevations
    (r"proposed\s*elevation", "elevations"),
    (r"existing\s*elevation", "elevations"),
    (r"front\s*elevation", "elevations"),
    (r"rear\s*elevation", "elevations"),
    (r"side\s*elevation", "elevations"),
    (r"(?:north|south|east|west)\s*elevation", "elevations"),
    (r"elevation\s*(?:drawing|detail|[a-z])", "elevations"),
    # Other drawings
    (r"street\s*scene", "street scene"),
    (r"cross[\s_-]*section", "sections"),
    (r"section\s*(?:drawing|detail|[a-z][\s_-][a-z])", "sections"),
    (r"roof\s*plan", "roof plan"),
    (r"garage\s*(?:plan|elevation|drawing)", "floor plan"),
    # Non-plan document types detected from text content
    (r"design\s*(?:and|&)\s*access\s*statement", "design_access_statement"),
    (r"heritage\s*(?:statement|assessment|impact)", "heritage_statement"),
    (r"planning\s*statement", "planning_statement"),
    (r"flood\s*risk\s*assessment", "flood_risk_assessment"),
    (r"arboricultural\s*(?:report|survey|assessment|impact)", "arboricultural_report"),
    (r"ecological?\s*(?:report|survey|assessment|appraisal)", "ecology_report"),
    (r"transport\s*(?:assessment|statement)", "transport_assessment"),
    (r"noise\s*(?:assessment|survey|report)", "noise_report"),
    (r"contamination\s*(?:report|assessment)", "contamination_report"),
    (r"bat\s*(?:survey|report)", "ecology_report"),
    (r"biodiversity\s*(?:net\s*gain|report|assessment)", "bng_report"),
    (r"structural\s*(?:report|survey|engineer)", "structural_report"),
    (r"energy\s*(?:statement|assessment)", "energy_statement"),
    (r"application\s*form", "application_form"),
    (r"(?:form|certificate)\s*(?:a|b|c|d)\b", "application_form"),
]


@dataclass
class DrawingMetadata:
    """Metadata extracted from a drawing/plan document."""

    document_type_guess: str = ""  # e.g. "site plan", "elevations", "floor plan"
    key_labels_found: list = None
    any_dimensions_detected: bool = False
    any_scale_detected: bool = False
    detected_labels: list = None   # Drawing-type labels detected from text content
    scale_found: str = ""          # Actual scale string e.g. "1:500"
    # Extracted actual measurements
    extracted_dimensions: list = None  # list of (value, unit, context) tuples
    ridge_height_m: Optional[float] = None
    eaves_height_m: Optional[float] = None
    depth_m: Optional[float] = None
    width_m: Optional[float] = None
    floor_area_sqm: Optional[float] = None

    def __post_init__(self):
        if self.key_labels_found is None:
            self.key_labels_found = []
        if self.detected_labels is None:
            self.detected_labels = []
        if self.extracted_dimensions is None:
            self.extracted_dimensions = []

    def to_json(self) -> str:
        return json.dumps({
            "document_type_guess": self.document_type_guess,
            "key_labels_found": self.key_labels_found,
            "any_dimensions_detected": self.any_dimensions_detected,
            "any_scale_detected": self.any_scale_detected,
            "detected_labels": self.detected_labels,
            "scale_found": self.scale_found,
            "extracted_dimensions": self.extracted_dimensions,
            "ridge_height_m": self.ridge_height_m,
            "eaves_height_m": self.eaves_height_m,
            "depth_m": self.depth_m,
            "width_m": self.width_m,
            "floor_area_sqm": self.floor_area_sqm,
        })

    @classmethod
    def from_json(cls, raw: str) -> "DrawingMetadata":
        data = json.loads(raw)
        return cls(
            document_type_guess=data.get("document_type_guess", ""),
            key_labels_found=data.get("key_labels_found", []),
            any_dimensions_detected=data.get("any_dimensions_detected", False),
            any_scale_detected=data.get("any_scale_detected", False),
            detected_labels=data.get("detected_labels", []),
            scale_found=data.get("scale_found", ""),
            extracted_dimensions=data.get("extracted_dimensions", []),
            ridge_height_m=data.get("ridge_height_m"),
            eaves_height_m=data.get("eaves_height_m"),
            depth_m=data.get("depth_m"),
            width_m=data.get("width_m"),
            floor_area_sqm=data.get("floor_area_sqm"),
        )


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

        # Dimension detection and actual extraction
        if re.search(r"\d+(?:\.\d+)?\s*(?:m|mm)\b", text_lower):
            meta.any_dimensions_detected = True

        # Extract actual dimension values with context
        for dm in re.finditer(
            r'(?:(\w[\w\s]{0,20}?)\s*(?:=|:|-|of)\s*)?(\d+(?:\.\d+)?)\s*(m|mm|metres?)\b',
            text_lower,
        ):
            context = (dm.group(1) or "").strip()
            val = float(dm.group(2))
            unit = dm.group(3)
            if unit in ('mm',):
                val = val / 1000.0
            meta.extracted_dimensions.append((val, 'm', context))

        # Ridge height
        rmatch = re.search(r'ridge\s*(?:height)?\s*(?:=|:|-|of)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', text_lower)
        if rmatch:
            meta.ridge_height_m = float(rmatch.group(1))

        # Eaves height
        ematch = re.search(r'eaves?\s*(?:height)?\s*(?:=|:|-|of)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', text_lower)
        if ematch:
            meta.eaves_height_m = float(ematch.group(1))

        # Depth/projection
        dmatch = re.search(r'(?:depth|projection)\s*(?:=|:|-|of)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', text_lower)
        if dmatch:
            meta.depth_m = float(dmatch.group(1))

        # Width
        wmatch = re.search(r'width\s*(?:=|:|-|of)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', text_lower)
        if wmatch:
            meta.width_m = float(wmatch.group(1))

        # Floor area
        fmatch = re.search(r'(?:floor\s*area|floorspace|gfa|gia)\s*(?:=|:|-|of)?\s*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|m2|m²|sqm)', text_lower)
        if fmatch:
            meta.floor_area_sqm = float(fmatch.group(1))

        # Scale detection — capture actual scale string
        scale_match = re.search(r"1\s*:\s*(\d+)", text_lower)
        if scale_match:
            meta.any_scale_detected = True
            meta.scale_found = f"1:{scale_match.group(1)}"

        # Title-block drawing-type detection from text content
        seen_labels: set[str] = set()
        for pat, label in _TEXT_DRAWING_TYPE_PATTERNS:
            if label not in seen_labels and re.search(pat, text_lower):
                meta.detected_labels.append(label)
                seen_labels.add(label)

        # Sheet numbering detection
        if re.search(
            r"(?:sheet|drawing|dwg)\s*(?:no\.?|number|num\.?)?\s*\d+",
            text_lower,
        ):
            if "sheet_numbered" not in seen_labels:
                meta.detected_labels.append("sheet_numbered")

        # Infer document_type_guess from text when filename gave no clue
        if not meta.document_type_guess and meta.detected_labels:
            # Use the first detected drawing-type label (highest-priority match)
            for lbl in meta.detected_labels:
                if lbl != "sheet_numbered":
                    meta.document_type_guess = lbl
                    break
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
    all_detected_labels: Optional[List[str]] = None,
) -> bool:
    """Determine if a minimal plan set is present.

    A plan set requires **all three legs**:

    1. **Location leg** — at least one of: location plan OR block plan
    2. **Site leg** — at least one: site plan
    3. **Detail leg** — at least one of: elevations OR floor plans OR sections

    Detection uses (in priority order):

    1. Classified ``DocumentCategory`` values
    2. ``extracted_metadata_json.document_type_guess`` values
    3. Filename heuristics
    4. ``detected_labels`` from text-content / OCR analysis
    """
    has_location = False   # location plan OR block plan
    has_site = False       # site plan
    has_detail = False     # elevations OR floor plans OR sections

    # --- Check from categories ---
    location_cats = {DocumentCategory.LOCATION_PLAN, DocumentCategory.BLOCK_PLAN}
    site_cats = {DocumentCategory.SITE_PLAN}
    detail_cats = {
        DocumentCategory.ELEVATION,
        DocumentCategory.FLOOR_PLAN,
        DocumentCategory.SECTION_DRAWING,
    }

    for cat in categories:
        if cat in location_cats:
            has_location = True
        if cat in site_cats:
            has_site = True
        if cat in detail_cats:
            has_detail = True

    if has_location and has_site and has_detail:
        return True

    # --- Check from metadata guesses ---
    if metadata_guesses:
        for guess in metadata_guesses:
            g = guess.lower()
            if g in ("location plan", "block plan"):
                has_location = True
            if g == "site plan":
                has_site = True
            if g in ("elevations", "elevation", "floor plan", "sections"):
                has_detail = True

    if has_location and has_site and has_detail:
        return True

    # --- Check from filenames ---
    if filenames:
        location_patterns = [r"location[\s_-]*plan", r"block[\s_-]*plan"]
        site_patterns = [r"site[\s_-]*(?:plan|layout)"]
        detail_patterns = [r"elevation", r"floor[\s_-]*plan", r"section"]
        for fn in filenames:
            fn_lower = fn.lower()
            for pat in location_patterns:
                if re.search(pat, fn_lower):
                    has_location = True
            for pat in site_patterns:
                if re.search(pat, fn_lower):
                    has_site = True
            for pat in detail_patterns:
                if re.search(pat, fn_lower):
                    has_detail = True

    if has_location and has_site and has_detail:
        return True

    # --- Check from detected labels (text-content / OCR analysis) ---
    if all_detected_labels:
        for label in all_detected_labels:
            lbl = label.lower()
            if lbl in ("location plan", "block plan"):
                has_location = True
            if lbl == "site plan":
                has_site = True
            if lbl in ("elevations", "floor plan", "sections"):
                has_detail = True

    return has_location and has_site and has_detail
