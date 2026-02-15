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


def _extract_text_from_file(
    processed: ProcessedDocument, path: Path,
) -> ProcessedDocument:
    """Extract text from a local file (PDF or text)."""
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


def _compute_evidence_quality(result: DocumentIngestionResult) -> str:
    """Compute overall evidence quality from processed documents.

    Rules:
    - HIGH: Key plans + statements extracted and could be cited.
    - MEDIUM: Some key docs extracted.
    - LOW: No docs, or docs exist but extraction failed completely.
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
    key_total = result.key_docs_count

    # All extraction failed despite having docs
    if result.extracted_count == 0 and result.failed_count == result.total_count:
        return "LOW"

    # HIGH: key plans AND statements available, with some extraction
    if has_plans and has_statements and key_extracted >= 2:
        return "HIGH"

    # MEDIUM: some key docs present (even without extraction — their existence
    # is evidence that plans were submitted)
    if has_plans or has_statements:
        return "MEDIUM"

    # Documents exist but none are key categories
    if result.total_count > 0:
        return "MEDIUM"

    return "LOW"
