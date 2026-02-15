"""
Document manager for planning application documents.

Provides interfaces for listing, downloading, and
managing planning application documents.
"""

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional


@dataclass
class ApplicationDocument:
    """A document submitted with a planning application."""

    id: str  # Unique document ID
    title: str  # Document title
    doc_type: str  # Document type (e.g., "Design Statement")
    format: str  # File format (PDF, DOCX, etc.)
    size_kb: int  # File size in KB
    date_received: str  # Date received
    url: Optional[str] = None  # Download URL (if available)
    local_path: Optional[str] = None  # Local file path (if downloaded)
    content_hash: Optional[str] = None  # MD5 hash for deduplication

    @property
    def filename(self) -> str:
        """Generate a filename for the document."""
        safe_title = "".join(c if c.isalnum() or c in "- " else "_" for c in self.title)
        return f"{safe_title}.{self.format.lower()}"


# Demo documents for offline mode
DEMO_DOCUMENTS = {
    "2024/0930/01/DET": [
        {
            "id": "doc_001",
            "title": "Application Form",
            "doc_type": "Application Form",
            "format": "PDF",
            "size_kb": 245,
            "date_received": "2024-09-15",
        },
        {
            "id": "doc_002",
            "title": "Design and Access Statement",
            "doc_type": "Design Statement",
            "format": "PDF",
            "size_kb": 4520,
            "date_received": "2024-09-15",
        },
        {
            "id": "doc_003",
            "title": "Heritage Statement",
            "doc_type": "Heritage Assessment",
            "format": "PDF",
            "size_kb": 3200,
            "date_received": "2024-09-15",
        },
        {
            "id": "doc_004",
            "title": "Proposed Floor Plans",
            "doc_type": "Plans",
            "format": "PDF",
            "size_kb": 1850,
            "date_received": "2024-09-15",
        },
        {
            "id": "doc_005",
            "title": "Proposed Elevations",
            "doc_type": "Plans",
            "format": "PDF",
            "size_kb": 2100,
            "date_received": "2024-09-15",
        },
        {
            "id": "doc_006",
            "title": "Existing and Proposed Site Plan",
            "doc_type": "Site Plan",
            "format": "PDF",
            "size_kb": 950,
            "date_received": "2024-09-15",
        },
        {
            "id": "doc_007",
            "title": "Structural Survey Report",
            "doc_type": "Technical Report",
            "format": "PDF",
            "size_kb": 5600,
            "date_received": "2024-09-18",
        },
    ],
    "2024/0943/01/LBC": [
        {
            "id": "doc_101",
            "title": "Listed Building Application Form",
            "doc_type": "Application Form",
            "format": "PDF",
            "size_kb": 280,
            "date_received": "2024-09-20",
        },
        {
            "id": "doc_102",
            "title": "Heritage Impact Assessment",
            "doc_type": "Heritage Assessment",
            "format": "PDF",
            "size_kb": 6800,
            "date_received": "2024-09-20",
        },
        {
            "id": "doc_103",
            "title": "Schedule of Works",
            "doc_type": "Schedule",
            "format": "PDF",
            "size_kb": 1200,
            "date_received": "2024-09-20",
        },
    ],
    "2024/0300/01/LBC": [
        {
            "id": "doc_201",
            "title": "Application Form",
            "doc_type": "Application Form",
            "format": "PDF",
            "size_kb": 210,
            "date_received": "2024-03-05",
        },
        {
            "id": "doc_202",
            "title": "Shop Front Design Details",
            "doc_type": "Design Statement",
            "format": "PDF",
            "size_kb": 2400,
            "date_received": "2024-03-05",
        },
    ],
    "2025/0015/01/DET": [
        {
            "id": "doc_301",
            "title": "Application Form",
            "doc_type": "Application Form",
            "format": "PDF",
            "size_kb": 195,
            "date_received": "2025-01-03",
        },
        {
            "id": "doc_302",
            "title": "Flood Risk Assessment",
            "doc_type": "Technical Report",
            "format": "PDF",
            "size_kb": 8500,
            "date_received": "2025-01-03",
        },
        {
            "id": "doc_303",
            "title": "Drainage Strategy",
            "doc_type": "Technical Report",
            "format": "PDF",
            "size_kb": 4200,
            "date_received": "2025-01-03",
        },
    ],
    "2023/1500/01/HOU": [
        {
            "id": "doc_401",
            "title": "Householder Application Form",
            "doc_type": "Application Form",
            "format": "PDF",
            "size_kb": 180,
            "date_received": "2023-10-12",
        },
        {
            "id": "doc_402",
            "title": "Proposed Plans and Elevations",
            "doc_type": "Plans",
            "format": "PDF",
            "size_kb": 1600,
            "date_received": "2023-10-12",
        },
    ],
    "24/00730/FUL": [
        {"id": "doc_501", "title": "Application Form", "doc_type": "Application Form", "format": "PDF", "size_kb": 320, "date_received": "2024-07-18"},
        {"id": "doc_502", "title": "Design and Access Statement", "doc_type": "Design Statement", "format": "PDF", "size_kb": 5200, "date_received": "2024-07-18"},
        {"id": "doc_503", "title": "Proposed Site Plan", "doc_type": "Site Plan", "format": "PDF", "size_kb": 1200, "date_received": "2024-07-18"},
        {"id": "doc_504", "title": "Proposed Block Plan 1:500", "doc_type": "Plans", "format": "PDF", "size_kb": 850, "date_received": "2024-07-18"},
        {"id": "doc_505", "title": "Proposed Ground Floor Plan", "doc_type": "Plans", "format": "PDF", "size_kb": 1800, "date_received": "2024-07-18"},
        {"id": "doc_506", "title": "Proposed First Floor Plan", "doc_type": "Plans", "format": "PDF", "size_kb": 1750, "date_received": "2024-07-18"},
        {"id": "doc_507", "title": "Proposed Second Floor Plan", "doc_type": "Plans", "format": "PDF", "size_kb": 1680, "date_received": "2024-07-18"},
        {"id": "doc_508", "title": "Proposed Roof Plan", "doc_type": "Plans", "format": "PDF", "size_kb": 920, "date_received": "2024-07-18"},
        {"id": "doc_509", "title": "Proposed Elevations (Front and Rear)", "doc_type": "Plans", "format": "PDF", "size_kb": 2400, "date_received": "2024-07-18"},
        {"id": "doc_510", "title": "Proposed Elevations (Side)", "doc_type": "Plans", "format": "PDF", "size_kb": 2100, "date_received": "2024-07-18"},
        {"id": "doc_511", "title": "Existing Ground Floor Plan", "doc_type": "Plans", "format": "PDF", "size_kb": 1450, "date_received": "2024-07-18"},
        {"id": "doc_512", "title": "Existing First Floor Plan", "doc_type": "Plans", "format": "PDF", "size_kb": 1420, "date_received": "2024-07-18"},
        {"id": "doc_513", "title": "Existing Elevations", "doc_type": "Plans", "format": "PDF", "size_kb": 1900, "date_received": "2024-07-18"},
        {"id": "doc_514", "title": "Existing and Proposed Section AA", "doc_type": "Plans", "format": "PDF", "size_kb": 1100, "date_received": "2024-07-18"},
        {"id": "doc_515", "title": "Existing and Proposed Section BB", "doc_type": "Plans", "format": "PDF", "size_kb": 1050, "date_received": "2024-07-18"},
        {"id": "doc_516", "title": "Location Plan 1:1250", "doc_type": "Plans", "format": "PDF", "size_kb": 680, "date_received": "2024-07-18"},
        {"id": "doc_517", "title": "Heritage Impact Assessment", "doc_type": "Heritage Assessment", "format": "PDF", "size_kb": 4600, "date_received": "2024-07-18"},
        {"id": "doc_518", "title": "Planning Statement", "doc_type": "Planning Statement", "format": "PDF", "size_kb": 3200, "date_received": "2024-07-18"},
        {"id": "doc_519", "title": "Biodiversity Net Gain Assessment", "doc_type": "Technical Report", "format": "PDF", "size_kb": 3800, "date_received": "2024-07-20"},
        {"id": "doc_520", "title": "Flood Risk Assessment", "doc_type": "Technical Report", "format": "PDF", "size_kb": 2900, "date_received": "2024-07-18"},
        {"id": "doc_521", "title": "Drainage Strategy Report", "doc_type": "Technical Report", "format": "PDF", "size_kb": 2100, "date_received": "2024-07-18"},
        {"id": "doc_522", "title": "Noise Impact Assessment", "doc_type": "Technical Report", "format": "PDF", "size_kb": 1800, "date_received": "2024-07-19"},
        {"id": "doc_523", "title": "Contamination Phase 1 Report", "doc_type": "Technical Report", "format": "PDF", "size_kb": 2600, "date_received": "2024-07-18"},
        {"id": "doc_524", "title": "Transport Statement", "doc_type": "Technical Report", "format": "PDF", "size_kb": 1500, "date_received": "2024-07-18"},
        {"id": "doc_525", "title": "Covering Letter from Agent", "doc_type": "Correspondence", "format": "PDF", "size_kb": 280, "date_received": "2024-07-18"},
        {"id": "doc_526", "title": "Site Photographs (12 images)", "doc_type": "Photographs", "format": "PDF", "size_kb": 8400, "date_received": "2024-07-18"},
    ],
}


class DocumentManager:
    """
    Manages planning application documents.

    Provides interfaces for listing documents, downloading them,
    and checking for duplicates using content hashing.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize the document manager.

        Args:
            storage_dir: Directory to store downloaded documents.
                        Defaults to ~/.plana/documents
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".plana" / "documents"
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._document_index: dict = {}  # reference -> [documents]
        self._hash_index: dict = {}  # hash -> document_id (for dedup)

    def list_documents(self, reference: str) -> List[ApplicationDocument]:
        """List all documents for an application.

        Args:
            reference: Application reference number

        Returns:
            List of ApplicationDocument objects
        """
        # Check if we have real documents indexed
        if reference in self._document_index:
            return self._document_index[reference]

        # Fall back to demo documents
        if reference in DEMO_DOCUMENTS:
            docs = []
            for doc_data in DEMO_DOCUMENTS[reference]:
                docs.append(ApplicationDocument(**doc_data))
            return docs

        return []

    def download_document(
        self, reference: str, document_id: str
    ) -> Optional[ApplicationDocument]:
        """Download a specific document.

        In demo mode, this just returns the document metadata.
        In live mode, this would fetch from the council portal.

        Args:
            reference: Application reference
            document_id: Document ID to download

        Returns:
            ApplicationDocument with local_path set, or None if not found
        """
        documents = self.list_documents(reference)
        for doc in documents:
            if doc.id == document_id:
                # In demo mode, we don't actually download
                # Just return the document with a simulated local path
                app_dir = self.storage_dir / reference.replace("/", "_")
                app_dir.mkdir(parents=True, exist_ok=True)
                doc.local_path = str(app_dir / doc.filename)
                return doc

        return None

    def download_all(self, reference: str) -> List[ApplicationDocument]:
        """Download all documents for an application.

        Args:
            reference: Application reference

        Returns:
            List of downloaded ApplicationDocument objects
        """
        documents = self.list_documents(reference)
        downloaded = []

        for doc in documents:
            result = self.download_document(reference, doc.id)
            if result:
                downloaded.append(result)

        return downloaded

    def compute_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of a file.

        Args:
            filepath: Path to the file

        Returns:
            MD5 hash string
        """
        if not filepath.exists():
            return ""

        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def is_duplicate(self, filepath: Path) -> Optional[str]:
        """Check if a file is a duplicate of an existing document.

        Args:
            filepath: Path to the file to check

        Returns:
            Document ID of the duplicate, or None if unique
        """
        file_hash = self.compute_hash(filepath)
        return self._hash_index.get(file_hash)

    def get_document_summary(self, reference: str) -> dict:
        """Get a summary of documents for an application.

        Args:
            reference: Application reference

        Returns:
            Dictionary with document count and types
        """
        documents = self.list_documents(reference)

        types: dict = {}
        total_size = 0

        for doc in documents:
            types[doc.doc_type] = types.get(doc.doc_type, 0) + 1
            total_size += doc.size_kb

        return {
            "total_documents": len(documents),
            "document_types": types,
            "total_size_kb": total_size,
            "total_size_mb": round(total_size / 1024, 2),
        }
