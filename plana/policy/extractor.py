"""
Policy PDF text extraction with caching.

Extracts text from planning policy PDFs and caches the results
to avoid re-extraction on subsequent runs.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

# PDF paths (configurable)
DEFAULT_PDF_PATHS = {
    "NPPF": "/mnt/data/NPPF.pdf",
    "CSUCP": "/mnt/data/planning_for_the_future_core_strategy_and_urban_core_plan_2010-2030.pdf",
    "DAP": "/mnt/data/DAP FINAL Adoption - Online Version.pdf",
}


class PolicyExtractor:
    """
    Extracts text from planning policy PDFs.

    Caches extracted text to .plana/cache/policies/ to avoid
    re-extraction on subsequent runs.
    """

    def __init__(self, cache_dir: Optional[Path] = None, pdf_paths: Optional[dict] = None):
        """Initialize the policy extractor.

        Args:
            cache_dir: Directory to cache extracted text. Defaults to ~/.plana/cache/policies
            pdf_paths: Dictionary mapping doc_id to PDF file path
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".plana" / "cache" / "policies"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_paths = pdf_paths or DEFAULT_PDF_PATHS
        self._extracted_cache: dict = {}

    def _get_cache_path(self, doc_id: str) -> Path:
        """Get the cache file path for a document."""
        return self.cache_dir / f"{doc_id.lower()}_extracted.json"

    def _compute_file_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of a file for cache validation."""
        if not filepath.exists():
            return "file_not_found"

        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _load_from_cache(self, doc_id: str, pdf_path: Path) -> Optional[dict]:
        """Try to load extracted text from cache."""
        cache_path = self._get_cache_path(doc_id)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)

            # Validate cache by checking file hash
            if cached.get("source_hash") == self._compute_file_hash(pdf_path):
                return cached

            # Hash mismatch - cache is stale
            return None
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_to_cache(self, doc_id: str, pdf_path: Path, data: dict) -> None:
        """Save extracted text to cache."""
        cache_path = self._get_cache_path(doc_id)

        data["source_hash"] = self._compute_file_hash(pdf_path)
        data["source_path"] = str(pdf_path)

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def extract_pdf(self, doc_id: str) -> dict:
        """Extract text from a policy PDF.

        Args:
            doc_id: Document identifier (NPPF, CSUCP, DAP)

        Returns:
            Dictionary with extracted pages and metadata
        """
        if doc_id in self._extracted_cache:
            return self._extracted_cache[doc_id]

        pdf_path = Path(self.pdf_paths.get(doc_id, ""))

        # Try cache first
        cached = self._load_from_cache(doc_id, pdf_path)
        if cached:
            self._extracted_cache[doc_id] = cached
            return cached

        # Try to extract from PDF
        if pdf_path.exists():
            try:
                extracted = self._extract_pdf_text(pdf_path, doc_id)
                self._save_to_cache(doc_id, pdf_path, extracted)
                self._extracted_cache[doc_id] = extracted
                return extracted
            except Exception as e:
                print(f"Warning: Could not extract PDF {pdf_path}: {e}")

        # Fall back to demo content
        from plana.policy.demo_policies import DEMO_POLICIES

        if doc_id in DEMO_POLICIES:
            demo_data = {
                "doc_id": doc_id,
                "title": DEMO_POLICIES[doc_id]["title"],
                "pages": self._demo_policies_to_pages(doc_id),
                "source": "demo",
            }
            self._extracted_cache[doc_id] = demo_data
            return demo_data

        return {"doc_id": doc_id, "pages": [], "source": "not_found"}

    def _extract_pdf_text(self, pdf_path: Path, doc_id: str) -> dict:
        """Extract text from a PDF file using pypdf."""
        try:
            from pypdf import PdfReader
        except ImportError:
            # If pypdf not available, return demo content
            return self._get_demo_fallback(doc_id)

        reader = PdfReader(pdf_path)
        pages = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "page_number": page_num,
                    "text": text,
                })

        from plana.policy.demo_policies import DEMO_POLICIES
        title = DEMO_POLICIES.get(doc_id, {}).get("title", doc_id)

        return {
            "doc_id": doc_id,
            "title": title,
            "pages": pages,
            "total_pages": len(reader.pages),
            "source": "pdf",
        }

    def _demo_policies_to_pages(self, doc_id: str) -> list:
        """Convert demo policies to page format."""
        from plana.policy.demo_policies import DEMO_POLICIES

        if doc_id not in DEMO_POLICIES:
            return []

        doc = DEMO_POLICIES[doc_id]
        pages = {}

        for policy in doc["policies"]:
            page_num = policy["page"]
            if page_num not in pages:
                pages[page_num] = {
                    "page_number": page_num,
                    "text": "",
                    "policies": [],
                }
            pages[page_num]["text"] += f"\n\n{policy['id']}: {policy['title']}\n{policy['text']}"
            pages[page_num]["policies"].append(policy["id"])

        return sorted(pages.values(), key=lambda p: p["page_number"])

    def _get_demo_fallback(self, doc_id: str) -> dict:
        """Get demo fallback data for a document."""
        from plana.policy.demo_policies import DEMO_POLICIES

        if doc_id in DEMO_POLICIES:
            return {
                "doc_id": doc_id,
                "title": DEMO_POLICIES[doc_id]["title"],
                "pages": self._demo_policies_to_pages(doc_id),
                "source": "demo",
            }
        return {"doc_id": doc_id, "pages": [], "source": "not_found"}

    def extract_all(self) -> dict:
        """Extract text from all configured policy PDFs.

        Returns:
            Dictionary mapping doc_id to extracted data
        """
        results = {}
        for doc_id in self.pdf_paths:
            results[doc_id] = self.extract_pdf(doc_id)
        return results

    def is_cache_valid(self, doc_id: str) -> bool:
        """Check if cache exists and is valid for a document."""
        pdf_path = Path(self.pdf_paths.get(doc_id, ""))
        cache_path = self._get_cache_path(doc_id)

        if not cache_path.exists():
            return False

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            return cached.get("source_hash") == self._compute_file_hash(pdf_path)
        except Exception:
            return False
