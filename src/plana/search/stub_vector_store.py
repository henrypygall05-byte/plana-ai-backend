"""
Stub vector store for local development without ML dependencies.

Provides a simple in-memory implementation that doesn't require
sentence-transformers or ChromaDB.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, NamedTuple

import structlog

from plana.config import get_settings

logger = structlog.get_logger(__name__)


class SearchResult(NamedTuple):
    """A search result with score and metadata."""

    id: str
    score: float
    content: str
    metadata: dict[str, Any]


class StubVectorStore:
    """
    Simple file-based vector store stub for local development.

    Uses keyword matching instead of embeddings. Stores data in JSON files.
    Suitable for testing and demos without ML dependencies.
    """

    def __init__(self):
        """Initialize stub vector store."""
        self.settings = get_settings()
        self._collections: dict[str, dict[str, dict]] = {}
        self._persist_path = self.settings.data_dir / "vector_store"
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the stub store."""
        if self._initialized:
            return

        self._persist_path.mkdir(parents=True, exist_ok=True)

        # Load existing collections from disk
        for collection_file in self._persist_path.glob("*.json"):
            collection_name = collection_file.stem
            try:
                with open(collection_file) as f:
                    self._collections[collection_name] = json.load(f)
            except Exception as e:
                logger.warning(
                    "Failed to load collection",
                    collection=collection_name,
                    error=str(e),
                )

        self._initialized = True
        logger.info("Stub vector store initialized (keyword-based, no ML)")

    def _get_collection(self, name: str) -> dict[str, dict]:
        """Get or create a collection."""
        prefix = self.settings.vector_store.collection_prefix
        full_name = f"{prefix}_{name}"

        if full_name not in self._collections:
            self._collections[full_name] = {}

        return self._collections[full_name]

    def _save_collection(self, name: str) -> None:
        """Persist collection to disk."""
        prefix = self.settings.vector_store.collection_prefix
        full_name = f"{prefix}_{name}"

        if full_name in self._collections:
            file_path = self._persist_path / f"{full_name}.json"
            with open(file_path, "w") as f:
                json.dump(self._collections[full_name], f, indent=2)

    def _compute_keyword_score(self, query: str, content: str) -> float:
        """Compute simple keyword-based similarity score."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.0

        # Jaccard-like similarity
        intersection = query_words & content_words
        union = query_words | content_words

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def add(
        self,
        collection: str,
        id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a document to the store."""
        await self.initialize()

        coll = self._get_collection(collection)
        coll[id] = {
            "content": content,
            "metadata": metadata or {},
        }

        self._save_collection(collection)
        logger.debug("Added to stub store", collection=collection, id=id)

    async def add_batch(
        self,
        collection: str,
        items: list[tuple[str, str, dict[str, Any] | None]],
    ) -> None:
        """Add multiple documents."""
        await self.initialize()

        coll = self._get_collection(collection)
        for id_, content, metadata in items:
            coll[id_] = {
                "content": content,
                "metadata": metadata or {},
            }

        self._save_collection(collection)
        logger.info("Added batch to stub store", collection=collection, count=len(items))

    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search using keyword matching."""
        await self.initialize()

        coll = self._get_collection(collection)
        results = []

        for id_, data in coll.items():
            # Apply metadata filter
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if data["metadata"].get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            score = self._compute_keyword_score(query, data["content"])
            results.append(
                SearchResult(
                    id=id_,
                    score=score,
                    content=data["content"],
                    metadata=data["metadata"],
                )
            )

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    async def delete(self, collection: str, id: str) -> bool:
        """Delete a document."""
        await self.initialize()

        coll = self._get_collection(collection)
        if id in coll:
            del coll[id]
            self._save_collection(collection)
            return True
        return False

    async def clear_collection(self, collection: str) -> None:
        """Clear all documents from a collection."""
        prefix = self.settings.vector_store.collection_prefix
        full_name = f"{prefix}_{collection}"

        if full_name in self._collections:
            del self._collections[full_name]

        file_path = self._persist_path / f"{full_name}.json"
        if file_path.exists():
            file_path.unlink()

        logger.info("Cleared collection", collection=collection)

    async def get_collection_count(self, collection: str) -> int:
        """Get number of documents in collection."""
        await self.initialize()

        coll = self._get_collection(collection)
        return len(coll)
