"""
Document ingestion pipeline for planning applications.

Classifies documents by type (site plan, elevations, floor plans, etc.)
using filename and doc_type heuristics, extracts text from PDFs, and
produces ProcessedDocument records that feed into the evidence register
and report generator.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class DocumentCategory(str, Enum):
    """Classified document type for planning assessment purposes."""

    APPLICATION_FORM = "application_form"
    SITE_PLAN = "site_plan"
    BLOCK_PLAN = "block_plan"
    LOCATION_PLAN = "location_plan"
    FLOOR_PLAN = "floor_plan"
    ELEVATION = "elevation"
    SECTION_DRAWING = "section_drawing"
    ROOF_PLAN = "roof_plan"
    DESIGN_ACCESS_STATEMENT = "design_access_statement"
    HERITAGE_STATEMENT = "heritage_statement"
    PLANNING_STATEMENT = "planning_statement"
    FLOOD_RISK_ASSESSMENT = "flood_risk_assessment"
    ECOLOGY_REPORT = "ecology_report"
    TRANSPORT_ASSESSMENT = "transport_assessment"
    ARBORICULTURAL_REPORT = "arboricultural_report"
    NOISE_ASSESSMENT = "noise_assessment"
    BNG_REPORT = "bng_report"
    CONTAMINATION_REPORT = "contamination_report"
    ENERGY_STATEMENT = "energy_statement"
    STRUCTURAL_REPORT = "structural_report"
    DRAINAGE_STRATEGY = "drainage_strategy"
    COVER_LETTER = "cover_letter"
    PHOTOGRAPH = "photograph"
    OTHER = "other"


class ExtractionStatus(str, Enum):
    """Status of text extraction from a document."""

    SUCCESS = "success"
    PARTIAL = "partial"  # Some pages extracted, others failed
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"  # Not a text-bearing format


# ---- Filename → category classification rules ----
# Order matters: first match wins.  Patterns are matched against the
# lowercased title and filename.
_CLASSIFICATION_RULES: list[tuple[str, DocumentCategory]] = [
    # Plans
    (r"site\s*(?:plan|layout)", DocumentCategory.SITE_PLAN),
    (r"block\s*plan", DocumentCategory.BLOCK_PLAN),
    (r"location\s*plan", DocumentCategory.LOCATION_PLAN),
    (r"floor\s*plan", DocumentCategory.FLOOR_PLAN),
    (r"proposed\s*plan", DocumentCategory.FLOOR_PLAN),
    (r"existing\s*plan", DocumentCategory.FLOOR_PLAN),
    (r"ground\s*floor", DocumentCategory.FLOOR_PLAN),
    (r"first\s*floor", DocumentCategory.FLOOR_PLAN),
    (r"second\s*floor", DocumentCategory.FLOOR_PLAN),
    (r"roof\s*plan", DocumentCategory.ROOF_PLAN),
    (r"elevation", DocumentCategory.ELEVATION),
    (r"section\s*(?:drawing|detail|plan)?", DocumentCategory.SECTION_DRAWING),
    # Statements
    (r"design\s*(?:and|&)\s*access", DocumentCategory.DESIGN_ACCESS_STATEMENT),
    (r"d\s*(?:&|and)\s*a\s*statement", DocumentCategory.DESIGN_ACCESS_STATEMENT),
    (r"heritage\s*(?:impact|statement|assessment)", DocumentCategory.HERITAGE_STATEMENT),
    (r"planning\s*statement", DocumentCategory.PLANNING_STATEMENT),
    # Technical reports
    (r"flood\s*risk", DocumentCategory.FLOOD_RISK_ASSESSMENT),
    (r"ecology|ecological|biodiversity(?!.*net\s*gain)", DocumentCategory.ECOLOGY_REPORT),
    (r"(?:biodiversity|bng)\s*(?:net\s*gain|metric|assessment)", DocumentCategory.BNG_REPORT),
    (r"transport|traffic|highway", DocumentCategory.TRANSPORT_ASSESSMENT),
    (r"arboricultural|tree\s*(?:survey|report)", DocumentCategory.ARBORICULTURAL_REPORT),
    (r"noise", DocumentCategory.NOISE_ASSESSMENT),
    (r"contaminat|geo[\-\s]*(?:environmental|technical)", DocumentCategory.CONTAMINATION_REPORT),
    (r"energy\s*statement|sustainability", DocumentCategory.ENERGY_STATEMENT),
    (r"structur", DocumentCategory.STRUCTURAL_REPORT),
    (r"drain|suds|surface\s*water", DocumentCategory.DRAINAGE_STRATEGY),
    (r"cover(?:ing)?\s*letter", DocumentCategory.COVER_LETTER),
    # Application form
    (r"application\s*form", DocumentCategory.APPLICATION_FORM),
    # Photos
    (r"photo", DocumentCategory.PHOTOGRAPH),
]

# Which categories count as "plan-type" documents.
PLAN_CATEGORIES = frozenset({
    DocumentCategory.SITE_PLAN,
    DocumentCategory.BLOCK_PLAN,
    DocumentCategory.LOCATION_PLAN,
    DocumentCategory.FLOOR_PLAN,
    DocumentCategory.ELEVATION,
    DocumentCategory.SECTION_DRAWING,
    DocumentCategory.ROOF_PLAN,
})

# Which categories count as "key" documents for evidence quality.
KEY_DOCUMENT_CATEGORIES = PLAN_CATEGORIES | frozenset({
    DocumentCategory.DESIGN_ACCESS_STATEMENT,
    DocumentCategory.HERITAGE_STATEMENT,
    DocumentCategory.PLANNING_STATEMENT,
})


@dataclass
class ProcessedDocument:
    """A document that has been classified and (optionally) text-extracted."""

    doc_id: str
    title: str
    filename: str
    category: DocumentCategory
    classification_confidence: float  # 0.0–1.0
    extraction_status: ExtractionStatus = ExtractionStatus.NOT_ATTEMPTED
    extracted_text: str = ""
    page_count: int = 0
    extraction_confidence: float = 0.0
    size_display: str = ""
    date_received: str = ""
    # Quick summary of what was found in the text (populated after extraction)
    text_summary: str = ""

    @property
    def is_plan(self) -> bool:
        return self.category in PLAN_CATEGORIES

    @property
    def is_key_document(self) -> bool:
        return self.category in KEY_DOCUMENT_CATEGORIES

    @property
    def category_label(self) -> str:
        """Human-readable category label."""
        return self.category.value.replace("_", " ").title()


@dataclass
class DocumentIngestionResult:
    """Aggregate result of processing all documents for an application."""

    documents: List[ProcessedDocument] = field(default_factory=list)
    total_count: int = 0
    plans_count: int = 0
    key_docs_count: int = 0
    extracted_count: int = 0
    failed_count: int = 0
    evidence_quality: str = "LOW"  # LOW, MEDIUM, HIGH

    @property
    def has_plans(self) -> bool:
        return self.plans_count > 0

    @property
    def has_key_documents(self) -> bool:
        return self.key_docs_count > 0

    def by_category(self, category: DocumentCategory) -> List[ProcessedDocument]:
        return [d for d in self.documents if d.category == category]

    def plans(self) -> List[ProcessedDocument]:
        return [d for d in self.documents if d.is_plan]

    def key_documents(self) -> List[ProcessedDocument]:
        return [d for d in self.documents if d.is_key_document]

    def statements(self) -> List[ProcessedDocument]:
        return [
            d for d in self.documents
            if d.category in {
                DocumentCategory.DESIGN_ACCESS_STATEMENT,
                DocumentCategory.HERITAGE_STATEMENT,
                DocumentCategory.PLANNING_STATEMENT,
            }
        ]


def classify_document(title: str, doc_type: str = "", filename: str = "") -> tuple[DocumentCategory, float]:
    """Classify a document by its title, declared doc_type, and filename.

    Returns (category, confidence) where confidence is 0.0–1.0.
    """
    text = f"{title} {doc_type} {filename}".lower().strip()

    for pattern, category in _CLASSIFICATION_RULES:
        if re.search(pattern, text):
            # Higher confidence if the match is in the title (most reliable)
            confidence = 0.85 if re.search(pattern, title.lower()) else 0.65
            return category, confidence

    return DocumentCategory.OTHER, 0.3


def process_documents(
    documents: list,
    extract_text: bool = False,
) -> DocumentIngestionResult:
    """Classify and optionally extract text from a list of documents.

    Accepts either ApplicationDocument (demo) or PortalDocument (live) objects.

    Args:
        documents: List of document objects (ApplicationDocument or PortalDocument).
        extract_text: If True, attempt PDF text extraction for documents
                     with a ``local_path`` on disk.  Requires ``pypdf``.

    Returns:
        DocumentIngestionResult with classified documents and aggregate stats.
    """
    result = DocumentIngestionResult()
    result.total_count = len(documents)

    for doc in documents:
        title = getattr(doc, "title", "Unknown")
        doc_id = getattr(doc, "id", "") or getattr(doc, "doc_id", "")
        doc_type = getattr(doc, "doc_type", "")
        local_path = getattr(doc, "local_path", None)

        # Build filename from available attributes
        if hasattr(doc, "filename"):
            filename = doc.filename
        elif hasattr(doc, "url") and doc.url:
            filename = doc.url.rsplit("/", 1)[-1]
        else:
            filename = title

        # Size display
        if hasattr(doc, "size_kb"):
            size_display = f"{doc.size_kb} KB"
        elif hasattr(doc, "size_bytes") and doc.size_bytes:
            size_display = f"{doc.size_bytes // 1024} KB"
        else:
            size_display = ""

        # Date
        date_received = (
            getattr(doc, "date_received", None)
            or getattr(doc, "date_published", None)
            or ""
        )

        # Classify
        category, confidence = classify_document(title, doc_type, filename)

        processed = ProcessedDocument(
            doc_id=doc_id,
            title=title,
            filename=filename,
            category=category,
            classification_confidence=confidence,
            size_display=size_display,
            date_received=date_received,
        )

        # Attempt text extraction if requested and file exists
        if extract_text and local_path and Path(local_path).is_file():
            processed = _extract_text_from_file(processed, Path(local_path))

        # Second-pass: reclassify OTHER docs using extracted text content
        if processed.category == DocumentCategory.OTHER and processed.extracted_text:
            processed = _reclassify_from_content(processed)

        result.documents.append(processed)

    # Calculate aggregate statistics
    result.plans_count = sum(1 for d in result.documents if d.is_plan)
    result.key_docs_count = sum(1 for d in result.documents if d.is_key_document)
    result.extracted_count = sum(
        1 for d in result.documents
        if d.extraction_status == ExtractionStatus.SUCCESS
    )
    result.failed_count = sum(
        1 for d in result.documents
        if d.extraction_status == ExtractionStatus.FAILED
    )

    # Determine evidence quality
    result.evidence_quality = _compute_evidence_quality(result)

    return result


def _ocr_extract_pages(path: Path) -> tuple[str, int]:
    """Attempt OCR on a PDF using pdf2image + pytesseract.

    Returns ``(text, pages_ok)`` — empty string and 0 if the OCR
    libraries are not installed.
    """
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


def _extract_text_from_file(
    processed: ProcessedDocument, path: Path,
) -> ProcessedDocument:
    """Extract text from a local file (PDF or text).

    For PDFs the native text layer is tried first (``pypdf``).  If that
    yields no usable text (scanned PDFs), an OCR fallback via
    ``pdf2image`` + ``pytesseract`` is attempted when the libraries are
    available.
    """
    try:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            texts = []
            pages_ok = 0
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages_ok += 1
                    texts.append(page_text)
                except Exception:
                    texts.append("")

            full_text = "\n".join(texts)
            processed.page_count = len(reader.pages)
            coverage = pages_ok / len(reader.pages) if reader.pages else 0

            # ---- OCR fallback for scanned PDFs ----
            if coverage == 0:
                ocr_text, ocr_ok = _ocr_extract_pages(path)
                if ocr_ok > 0:
                    full_text = ocr_text
                    pages_ok = ocr_ok
                    coverage = ocr_ok / processed.page_count if processed.page_count else 0

            processed.extraction_confidence = min(1.0, coverage + 0.2)

            if coverage >= 0.3:
                processed.extracted_text = full_text
                processed.extraction_status = ExtractionStatus.SUCCESS
            elif coverage > 0:
                processed.extracted_text = full_text
                processed.extraction_status = ExtractionStatus.PARTIAL
            else:
                processed.extraction_status = ExtractionStatus.FAILED

        elif suffix in (".txt", ".csv", ".html", ".htm"):
            text = path.read_text(errors="replace")
            processed.extracted_text = text
            processed.page_count = 1
            processed.extraction_status = ExtractionStatus.SUCCESS
            processed.extraction_confidence = 1.0
        else:
            processed.extraction_status = ExtractionStatus.NOT_ATTEMPTED

    except Exception:
        processed.extraction_status = ExtractionStatus.FAILED

    return processed


# ---- Content-based reclassification ----
# When classify_document() returns OTHER, a second pass scans extracted text
# for keywords that indicate a specific category.  Patterns are ordered by
# specificity; first match wins.
_CONTENT_CLASSIFICATION_RULES: list[tuple[str, DocumentCategory]] = [
    # BNG / biodiversity net gain (must match before ecology)
    (r"biodiversity\s*net\s*gain|bng\s*metric|bng\s*assessment", DocumentCategory.BNG_REPORT),
    # Ecology
    (r"ecology|ecological\s*survey|protected\s*species|bat\s*survey", DocumentCategory.ECOLOGY_REPORT),
    # Heritage
    (r"heritage\s*(?:impact|significance|assessment)|listed\s*building\s*consent", DocumentCategory.HERITAGE_STATEMENT),
    # Design & Access
    (r"design\s*(?:and|&)\s*access|character\s*(?:of\s*)?the\s*area|design\s*principles", DocumentCategory.DESIGN_ACCESS_STATEMENT),
    # Planning statement
    (r"planning\s*statement|policy\s*compliance|development\s*plan", DocumentCategory.PLANNING_STATEMENT),
    # Flood risk
    (r"flood\s*risk|flood\s*zone|sequential\s*test|exception\s*test", DocumentCategory.FLOOD_RISK_ASSESSMENT),
    # Elevations (content mentions ridge/eaves/elevation views)
    (r"(?:proposed|existing)\s*elevation|ridge\s*height|eaves\s*height|front\s*elevation|rear\s*elevation", DocumentCategory.ELEVATION),
    # Floor plans
    (r"(?:ground|first|second)\s*floor\s*(?:plan|layout)|gross\s*internal\s*area|gia\b", DocumentCategory.FLOOR_PLAN),
    # Site plan
    (r"site\s*(?:plan|layout|boundary)|red\s*(?:line|boundary)|application\s*site", DocumentCategory.SITE_PLAN),
    # Transport
    (r"transport\s*(?:assessment|statement)|trip\s*(?:generation|rate)|parking\s*survey", DocumentCategory.TRANSPORT_ASSESSMENT),
    # Drainage
    (r"drainage\s*strategy|suds|surface\s*water\s*management", DocumentCategory.DRAINAGE_STRATEGY),
    # Arboricultural
    (r"arboricultural|tree\s*survey|tree\s*protection\s*plan", DocumentCategory.ARBORICULTURAL_REPORT),
    # Noise
    (r"noise\s*(?:impact|assessment|survey)|acoustic", DocumentCategory.NOISE_ASSESSMENT),
    # Contamination
    (r"contamination|geo[\-\s]*(?:environmental|technical)|phase\s*[12i]\s*(?:report|investigation)", DocumentCategory.CONTAMINATION_REPORT),
]


def _reclassify_from_content(processed: ProcessedDocument) -> ProcessedDocument:
    """Re-examine an OTHER-classified document using its extracted text.

    If a keyword match is found in the first 3 000 characters of the
    extracted text, the category and confidence are updated.  This is a
    cheap heuristic — it does NOT override a confident filename-based
    classification.
    """
    if processed.category != DocumentCategory.OTHER:
        return processed
    if not processed.extracted_text:
        return processed

    sample = processed.extracted_text[:3000].lower()
    for pattern, category in _CONTENT_CLASSIFICATION_RULES:
        if re.search(pattern, sample):
            processed.category = category
            # Content-based matches are less certain than filename matches
            processed.classification_confidence = max(
                processed.classification_confidence, 0.55,
            )
            break

    return processed


@dataclass
class ExtractedPlanningFacts:
    """Planning facts parsed from submitted PDF text layers.

    Each field is ``None`` when extraction was not attempted or the
    value could not be found.  The ``*_source`` companion stores the
    title of the document the value was read from.
    """

    ridge_height_m: Optional[str] = None
    ridge_height_source: str = ""
    eaves_height_m: Optional[str] = None
    eaves_height_source: str = ""
    floor_area_sqm: Optional[str] = None
    floor_area_source: str = ""
    storeys: Optional[str] = None
    storeys_source: str = ""
    parking_spaces: Optional[str] = None
    parking_source: str = ""
    access_width_m: Optional[str] = None
    access_width_source: str = ""

    @property
    def has_any(self) -> bool:
        return any([
            self.ridge_height_m, self.eaves_height_m,
            self.floor_area_sqm, self.storeys,
            self.parking_spaces, self.access_width_m,
        ])


# Filename-based priority order for searching extracted text.
# Documents earlier in this list are searched first so that
# "Proposed Elevations" beats "Design and Access Statement" for
# ridge/eaves height, etc.
_SEARCH_PRIORITY: list[DocumentCategory] = [
    DocumentCategory.ELEVATION,
    DocumentCategory.FLOOR_PLAN,
    DocumentCategory.SITE_PLAN,
    DocumentCategory.BLOCK_PLAN,
    DocumentCategory.SECTION_DRAWING,
    DocumentCategory.ROOF_PLAN,
    DocumentCategory.LOCATION_PLAN,
    DocumentCategory.DESIGN_ACCESS_STATEMENT,
    DocumentCategory.PLANNING_STATEMENT,
]


def _prioritised_docs(
    ingestion: "DocumentIngestionResult",
    preferred: list[DocumentCategory],
) -> List["ProcessedDocument"]:
    """Return docs ordered by *preferred* categories first, then the rest."""
    seen: set[str] = set()
    ordered: List[ProcessedDocument] = []
    for cat in preferred:
        for d in ingestion.by_category(cat):
            if d.doc_id not in seen and d.extracted_text:
                ordered.append(d)
                seen.add(d.doc_id)
    # Append remaining docs that have text
    for d in ingestion.documents:
        if d.doc_id not in seen and d.extracted_text:
            ordered.append(d)
            seen.add(d.doc_id)
    return ordered


def extract_planning_facts(
    ingestion: Optional["DocumentIngestionResult"],
) -> ExtractedPlanningFacts:
    """Parse key planning measurements from ingested document text.

    Searches the text layers of classified PDFs in priority order
    (proposed elevations → floor plans → site plan → DAS → …) and
    returns the first match found for each field.

    This is a best-effort heuristic — values should be verified by an
    officer.  Fields that cannot be parsed remain ``None``.
    """
    facts = ExtractedPlanningFacts()
    if not ingestion or ingestion.total_count == 0:
        return facts

    # ---- Build prioritised search lists per field ----
    height_cats = [
        DocumentCategory.ELEVATION,
        DocumentCategory.SECTION_DRAWING,
        DocumentCategory.DESIGN_ACCESS_STATEMENT,
    ]
    area_cats = [
        DocumentCategory.FLOOR_PLAN,
        DocumentCategory.DESIGN_ACCESS_STATEMENT,
        DocumentCategory.PLANNING_STATEMENT,
    ]
    site_cats = [
        DocumentCategory.SITE_PLAN,
        DocumentCategory.BLOCK_PLAN,
        DocumentCategory.DESIGN_ACCESS_STATEMENT,
    ]

    height_docs = _prioritised_docs(ingestion, height_cats)
    area_docs = _prioritised_docs(ingestion, area_cats)
    site_docs = _prioritised_docs(ingestion, site_cats)
    all_docs = _prioritised_docs(ingestion, _SEARCH_PRIORITY)

    # ---- Ridge height ----
    val, src = _search_docs_for_pattern(height_docs, [
        (r'ridge\s*(?:height)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?', 'ridge'),
        (r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:to\s*)?ridge', 'ridge'),
        (r'max(?:imum)?\s*height[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?', 'height'),
    ])
    if val:
        facts.ridge_height_m = val
        facts.ridge_height_source = src or ""

    # ---- Eaves height ----
    val, src = _search_docs_for_pattern(height_docs, [
        (r'eaves?\s*(?:height)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?', 'eaves'),
        (r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:to\s*)?eaves?', 'eaves'),
    ])
    if val:
        facts.eaves_height_m = val
        facts.eaves_height_source = src or ""

    # ---- Floor area ----
    val, src = _search_docs_for_pattern(area_docs, [
        (r'(?:total\s*)?(?:floor\s*)?area[:\s]*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)', 'area'),
        (r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)\s*(?:floor\s*)?area', 'area'),
        (r'gi(?:f)?a[:\s]*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)', 'gia'),
        (r'(\d+(?:\.\d+)?)\s*(?:square\s*)?met(?:re|er)s?\s*(?:floor\s*)?area', 'area'),
    ])
    if val:
        facts.floor_area_sqm = val
        facts.floor_area_source = src or ""

    # ---- Number of storeys ----
    val, src = _search_docs_for_pattern(all_docs, [
        (r'(\d+)\s*(?:storey|story|stories|storeys)', 'storeys'),
        (r'(\d+)[\s\-]*storey', 'storeys'),
        (r'(?:number\s*of\s*)?(?:floor|storey)s?\s*[:=]\s*(\d+)', 'storeys'),
        (r'over\s+(\d+)\s+floors?', 'floors'),
    ])
    if val:
        facts.storeys = val
        facts.storeys_source = src or ""

    # ---- Parking spaces ----
    val, src = _search_docs_for_pattern(site_docs, [
        (r'(\d+)\s*(?:car\s*)?(?:parking\s*)?(?:space|bay)s?', 'parking'),
        (r'parking[:\s]*(\d+)', 'parking'),
        (r'(\d+)\s*(?:off[\-\s]*street|on[\-\s]*site)\s*(?:parking\s*)?(?:space|bay)?s?', 'parking'),
    ])
    if val:
        facts.parking_spaces = val
        facts.parking_source = src or ""

    # ---- Access width ----
    val, src = _search_docs_for_pattern(site_docs, [
        (r'access\s*(?:width)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?', 'access'),
        (r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:wide\s*)?access', 'access'),
        (r'vehicular\s*access[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:wide)?', 'access'),
    ])
    if val:
        facts.access_width_m = val
        facts.access_width_source = src or ""

    return facts


@dataclass
class MaterialInfoItem:
    """A material information item with extraction status and confidence."""

    name: str  # e.g., "Ridge/eaves height"
    value: str  # e.g., "8.5m ridge, 5.2m eaves" or ""
    status: str  # "Found on <drawing>" / "Not found …" / "Missing …"
    required_reason: str  # Why the item matters


def _search_docs_for_pattern(
    docs: List[ProcessedDocument],
    patterns: list[tuple[str, str]],
) -> tuple[Optional[str], Optional[str]]:
    """Search extracted text of *docs* for the first regex match.

    *patterns* is a list of ``(regex, label)`` tuples.  Each regex must
    contain exactly one capture group for the numeric value.

    Returns ``(matched_value, source_document_title)`` or ``(None, None)``.
    """
    for doc in docs:
        if not doc.extracted_text:
            continue
        text_lower = doc.extracted_text.lower()
        for pattern, _label in patterns:
            m = re.search(pattern, text_lower)
            if m:
                return m.group(1), doc.title
    return None, None


def extract_material_info(
    ingestion: Optional[DocumentIngestionResult],
    documents_count: int = 0,
    documents_verified: bool = True,
    evidence_map: object = None,
    planning_facts: Optional[ExtractedPlanningFacts] = None,
) -> List[MaterialInfoItem]:
    """Extract material-information items from ingested documents.

    Scans extracted text from classified documents to find:
    - Ridge / eaves height (from elevations, D&A statement)
    - Floor area / GIA (from floor plans, D&A statement)
    - Number of storeys
    - Parking count (from site plan, D&A statement)
    - Access width (from site plan)

    When *planning_facts* is provided (pre-computed by
    ``extract_planning_facts``), the already-extracted values are used
    directly instead of re-scanning.

    When *evidence_map* is provided, [D#] tags from the evidence
    register are cited alongside document references so the officer
    can cross-reference the appendix.

    RULE: Only report "submitted plans missing" when
    ``documents_count == 0 AND documents_verified is True``.  When
    ``documents_count > 0`` but ingestion has no results, say
    "Not extracted from submitted documents yet" and cite [D#] docs.
    """
    items: List[MaterialInfoItem] = []
    facts = planning_facts or ExtractedPlanningFacts()

    # Resolve effective document count — never undercount
    effective_docs = max(
        documents_count,
        ingestion.total_count if ingestion else 0,
    )
    confirmed_no_docs = effective_docs == 0 and documents_verified

    # Helper: build [D#] citation list for docs of a category
    def _cite_category(docs: List[ProcessedDocument]) -> str:
        if not docs or evidence_map is None:
            return ""
        tags = []
        for d in docs[:3]:
            t = getattr(evidence_map, "tag_for_doc", lambda x: "")(d.doc_id)
            if t:
                tags.append(f"{t} {d.title}")
        if tags:
            return f" (see {', '.join(tags)})"
        return ""

    if ingestion is None or ingestion.total_count == 0:
        if confirmed_no_docs:
            _status = "Missing — no documents submitted"
        else:
            _status = (
                f"Not extracted from submitted documents yet — "
                f"{effective_docs} document(s) received, "
                f"plan content extraction pending"
            )
        for name, reason in [
            ("Ridge/eaves height",
             "Required for overbearing/daylight assessment (BRE Guidelines, 45-degree test)"),
            ("Floor area (GIA)",
             "Required to assess scale relative to plot and CIL liability"),
            ("Number of storeys",
             "Required to assess scale, massing, and overbearing impact"),
            ("Parking provision",
             "Required for highways assessment (NPPF para 111)"),
            ("Access width",
             "Required for highways safety assessment"),
        ]:
            items.append(MaterialInfoItem(
                name=name, value="", status=_status,
                required_reason=reason,
            ))
        return items

    # Collect documents by category
    elevation_docs = ingestion.by_category(DocumentCategory.ELEVATION)
    floor_plan_docs = ingestion.by_category(DocumentCategory.FLOOR_PLAN)
    site_plan_docs = ingestion.by_category(DocumentCategory.SITE_PLAN)
    section_docs = ingestion.by_category(DocumentCategory.SECTION_DRAWING)

    # ---- Ridge / Eaves Height ----
    ridge_val = facts.ridge_height_m
    eaves_val = facts.eaves_height_m
    ridge_src = facts.ridge_height_source
    eaves_src = facts.eaves_height_source

    if ridge_val or eaves_val:
        parts = []
        if ridge_val:
            parts.append(f"{ridge_val}m ridge")
        if eaves_val:
            parts.append(f"{eaves_val}m eaves")
        src = ridge_src or eaves_src
        items.append(MaterialInfoItem(
            name="Ridge/eaves height",
            value=", ".join(parts),
            status=f"Found on {src}",
            required_reason="Required for overbearing/daylight assessment",
        ))
    elif elevation_docs or section_docs:
        cite = _cite_category(elevation_docs or section_docs)
        items.append(MaterialInfoItem(
            name="Ridge/eaves height",
            value="",
            status=(
                f"Not extracted from submitted plans yet{cite}; "
                f"officer to verify from drawing"
            ),
            required_reason=(
                "Required for overbearing/daylight assessment "
                "(BRE Guidelines, 45-degree test)"
            ),
        ))
    else:
        items.append(MaterialInfoItem(
            name="Ridge/eaves height",
            value="",
            status=(
                "Missing — no elevation drawings submitted"
                if confirmed_no_docs
                else f"Not extracted from submitted documents yet — "
                     f"{effective_docs} document(s) received but "
                     f"elevation drawings not yet classified"
            ),
            required_reason=(
                "Required for overbearing/daylight assessment "
                "(BRE Guidelines, 45-degree test)"
            ),
        ))

    # ---- Floor Area / GIA ----
    area_val = facts.floor_area_sqm
    area_src = facts.floor_area_source

    if area_val:
        items.append(MaterialInfoItem(
            name="Floor area (GIA)",
            value=f"{area_val} sqm",
            status=f"Found on {area_src}",
            required_reason="Required to assess scale relative to plot and CIL liability",
        ))
    elif floor_plan_docs:
        cite = _cite_category(floor_plan_docs)
        items.append(MaterialInfoItem(
            name="Floor area (GIA)",
            value="",
            status=(
                f"Not extracted from submitted floor plans yet{cite}; "
                f"officer to measure from drawing"
            ),
            required_reason="Required to assess scale relative to plot and CIL liability",
        ))
    else:
        items.append(MaterialInfoItem(
            name="Floor area (GIA)",
            value="",
            status=(
                "Missing — no floor plans submitted"
                if confirmed_no_docs
                else f"Not extracted from submitted documents yet — "
                     f"{effective_docs} document(s) received but "
                     f"floor plans not yet classified"
            ),
            required_reason="Required to assess scale relative to plot and CIL liability",
        ))

    # ---- Number of Storeys ----
    storeys_val = facts.storeys
    storeys_src = facts.storeys_source

    if storeys_val:
        items.append(MaterialInfoItem(
            name="Number of storeys",
            value=f"{storeys_val} storeys",
            status=f"Found on {storeys_src}",
            required_reason="Required to assess scale, massing, and overbearing impact",
        ))
    elif elevation_docs or section_docs or floor_plan_docs:
        cite = _cite_category(elevation_docs or section_docs or floor_plan_docs)
        items.append(MaterialInfoItem(
            name="Number of storeys",
            value="",
            status=(
                f"Not extracted from submitted plans yet{cite}; "
                f"officer to verify from drawings"
            ),
            required_reason="Required to assess scale, massing, and overbearing impact",
        ))
    else:
        items.append(MaterialInfoItem(
            name="Number of storeys",
            value="",
            status=(
                "Missing — no elevation or section drawings submitted"
                if confirmed_no_docs
                else f"Not extracted from submitted documents yet — "
                     f"{effective_docs} document(s) received but "
                     f"elevation/section drawings not yet classified"
            ),
            required_reason="Required to assess scale, massing, and overbearing impact",
        ))

    # ---- Parking Provision ----
    parking_val = facts.parking_spaces
    parking_src = facts.parking_source

    if parking_val:
        items.append(MaterialInfoItem(
            name="Parking provision",
            value=f"{parking_val} spaces",
            status=f"Found on {parking_src}",
            required_reason="Required for highways assessment (NPPF para 111)",
        ))
    elif site_plan_docs:
        cite = _cite_category(site_plan_docs)
        items.append(MaterialInfoItem(
            name="Parking provision",
            value="",
            status=(
                f"Not extracted from submitted site plan yet{cite}; "
                f"officer to verify from drawing"
            ),
            required_reason="Required for highways assessment (NPPF para 111)",
        ))
    else:
        items.append(MaterialInfoItem(
            name="Parking provision",
            value="",
            status=(
                "Missing — no site plan submitted"
                if confirmed_no_docs
                else f"Not extracted from submitted documents yet — "
                     f"{effective_docs} document(s) received but "
                     f"site plan not yet classified"
            ),
            required_reason="Required for highways assessment (NPPF para 111)",
        ))

    # ---- Access Width ----
    access_val = facts.access_width_m
    access_src = facts.access_width_source

    if access_val:
        items.append(MaterialInfoItem(
            name="Access width",
            value=f"{access_val}m",
            status=f"Found on {access_src}",
            required_reason="Required for highways safety assessment",
        ))
    elif site_plan_docs:
        cite = _cite_category(site_plan_docs)
        items.append(MaterialInfoItem(
            name="Access width",
            value="",
            status=(
                f"Not extracted from submitted site plan yet{cite}; "
                f"officer to verify from drawing"
            ),
            required_reason="Required for highways safety assessment",
        ))
    else:
        items.append(MaterialInfoItem(
            name="Access width",
            value="",
            status=(
                "Missing — no site plan submitted"
                if confirmed_no_docs
                else f"Not extracted from submitted documents yet — "
                     f"{effective_docs} document(s) received but "
                     f"site plan not yet classified"
            ),
            required_reason="Required for highways safety assessment",
        ))

    return items


def _compute_evidence_quality(result: DocumentIngestionResult) -> str:
    """Compute overall evidence quality from processed documents.

    Rules:
    - HIGH: Key plans + statements extracted and could be cited.
    - MEDIUM: Some key docs exist (even without full extraction).
    - LOW: No docs at all, OR extraction failed on every document AND
      no plan-type documents were classified (even by filename).

    IMPORTANT: If ``total_count > 0`` the quality can only be LOW when
    extraction completely failed AND there are zero plan-type or
    statement-type classifications.  Having plans classified by
    filename alone (without extraction) is enough for MEDIUM because
    the documents *exist* and can be reviewed by the officer.
    """
    if result.total_count == 0:
        return "LOW"

    has_plans = result.plans_count > 0
    has_statements = len(result.statements()) > 0

    # Check how many key docs were successfully extracted
    key_extracted = sum(
        1 for d in result.key_documents()
        if d.extraction_status in (ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL)
    )

    # HIGH: key plans AND statements available, with some extraction
    if has_plans and has_statements and key_extracted >= 2:
        return "HIGH"

    # MEDIUM: some key docs present (even without extraction — their
    # existence is evidence that plans were submitted)
    if has_plans or has_statements:
        return "MEDIUM"

    # All extraction failed AND no plan/statement classification at all
    # — this is the ONLY case where docs > 0 can yield LOW
    if (result.extracted_count == 0
            and result.failed_count == result.total_count
            and not has_plans
            and not has_statements):
        return "LOW"

    # Documents exist but none are key categories — still MEDIUM
    # because the officer can review the uploaded files
    return "MEDIUM"
