"""
Text extraction from documents.

Handles PDF text extraction and basic image OCR preparation.
"""

import io
import re
from typing import NamedTuple

import structlog
from pypdf import PdfReader

logger = structlog.get_logger(__name__)


class ExtractionResult(NamedTuple):
    """Result of text extraction."""

    text: str
    page_count: int
    method: str  # "native", "ocr", "hybrid"
    confidence: float


class TextExtractor:
    """
    Extracts text from planning documents.

    Supports:
    - Native PDF text extraction
    - Fallback to OCR for scanned documents (when available)
    - Basic text cleanup and normalization
    """

    def __init__(self):
        """Initialize text extractor."""
        self._ocr_available = self._check_ocr_available()

    def _check_ocr_available(self) -> bool:
        """Check if OCR libraries are available."""
        try:
            import pytesseract
            from pdf2image import convert_from_bytes

            return True
        except ImportError:
            logger.warning("OCR libraries not available (pytesseract/pdf2image)")
            return False

    async def extract_from_pdf(self, content: bytes) -> ExtractionResult:
        """Extract text from PDF content.

        Args:
            content: PDF file bytes

        Returns:
            Extraction result with text and metadata
        """
        try:
            reader = PdfReader(io.BytesIO(content))
            page_count = len(reader.pages)
            texts = []
            pages_with_text = 0

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages_with_text += 1
                    texts.append(f"--- Page {page_num} ---\n{page_text}")
                except Exception as e:
                    logger.warning(
                        "Failed to extract page",
                        page=page_num,
                        error=str(e),
                    )
                    texts.append(f"--- Page {page_num} ---\n[Extraction failed]")

            full_text = "\n\n".join(texts)
            cleaned_text = self._clean_text(full_text)

            # Determine if OCR is needed
            text_coverage = pages_with_text / page_count if page_count > 0 else 0

            if text_coverage < 0.3 and self._ocr_available:
                logger.info("Low text coverage, attempting OCR", coverage=text_coverage)
                ocr_result = await self._extract_with_ocr(content, page_count)
                if ocr_result and len(ocr_result) > len(cleaned_text):
                    return ExtractionResult(
                        text=ocr_result,
                        page_count=page_count,
                        method="ocr",
                        confidence=0.7,
                    )

            confidence = min(1.0, text_coverage + 0.2)
            return ExtractionResult(
                text=cleaned_text,
                page_count=page_count,
                method="native",
                confidence=confidence,
            )

        except Exception as e:
            logger.error("PDF extraction failed", error=str(e))
            return ExtractionResult(
                text="",
                page_count=0,
                method="failed",
                confidence=0.0,
            )

    async def _extract_with_ocr(
        self, content: bytes, expected_pages: int
    ) -> str | None:
        """Extract text using OCR.

        Args:
            content: PDF file bytes
            expected_pages: Expected number of pages

        Returns:
            Extracted text or None if OCR fails
        """
        if not self._ocr_available:
            return None

        try:
            from pdf2image import convert_from_bytes
            import pytesseract

            images = convert_from_bytes(content, dpi=200)
            texts = []

            for page_num, image in enumerate(images, 1):
                try:
                    text = pytesseract.image_to_string(image, lang="eng")
                    texts.append(f"--- Page {page_num} (OCR) ---\n{text}")
                except Exception as e:
                    logger.warning("OCR failed for page", page=page_num, error=str(e))

            return self._clean_text("\n\n".join(texts))

        except Exception as e:
            logger.error("OCR extraction failed", error=str(e))
            return None

    def extract_from_text(self, content: bytes) -> ExtractionResult:
        """Extract text from plain text file.

        Args:
            content: Text file bytes

        Returns:
            Extraction result
        """
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except UnicodeDecodeError:
                text = content.decode("utf-8", errors="replace")

        cleaned = self._clean_text(text)
        return ExtractionResult(
            text=cleaned,
            page_count=1,
            method="native",
            confidence=1.0,
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Normalize whitespace
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\r", "\n", text)

        # Remove excessive blank lines
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        # Remove excessive spaces
        text = re.sub(r"[ \t]{3,}", "  ", text)

        # Fix common OCR artifacts
        text = re.sub(r"([a-z])- \n([a-z])", r"\1\2", text)  # Hyphenated words
        text = re.sub(r"\x00", "", text)  # Null bytes
        text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", text)  # Control chars

        # Normalize quotes
        text = text.replace(""", '"').replace(""", '"')
        text = text.replace("'", "'").replace("'", "'")

        return text.strip()

    def estimate_word_count(self, text: str) -> int:
        """Estimate word count in text."""
        return len(text.split())

    def extract_sections(self, text: str) -> list[dict[str, str]]:
        """Extract section headings and content from text.

        Args:
            text: Full document text

        Returns:
            List of dicts with 'heading' and 'content' keys
        """
        sections = []

        # Common section heading patterns
        heading_patterns = [
            r"^(\d+\.?\s+[A-Z][A-Za-z\s]+)$",  # 1. Introduction
            r"^([A-Z][A-Z\s]+)$",  # ALL CAPS HEADING
            r"^(#{1,3}\s+.+)$",  # Markdown headings
        ]

        lines = text.split("\n")
        current_section = {"heading": "Introduction", "content": []}

        for line in lines:
            is_heading = False
            for pattern in heading_patterns:
                if re.match(pattern, line.strip()):
                    if current_section["content"]:
                        current_section["content"] = "\n".join(current_section["content"])
                        sections.append(current_section)
                    current_section = {"heading": line.strip(), "content": []}
                    is_heading = True
                    break

            if not is_heading:
                current_section["content"].append(line)

        # Add final section
        if current_section["content"]:
            current_section["content"] = "\n".join(current_section["content"])
            sections.append(current_section)

        return sections
