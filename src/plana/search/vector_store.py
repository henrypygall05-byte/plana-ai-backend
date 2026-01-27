"""
Vector store abstraction for semantic search.

Provides a unified interface for vector databases with
support for ChromaDB (default) and other backends.
"""

from typing import Any, NamedTuple

import structlog
from sentence_transformers import SentenceTransformer

from plana.config import get_settings

logger = structlog.get_logger(__name__)


class SearchResult(NamedTuple):
    """A search result with score and metadata."""

    id: str
    score: float
    content: str
    metadata: dict[str, Any]


class VectorStore:
    """
    Vector database interface for semantic search.

    Supports storing and searching embeddings of:
    - Policy content
    - Document text
    - Application summaries
    """

    def __init__(self):
        """Initialize vector store."""
        self.settings = get_settings()
        self._client = None
        self._embedder = None
        self._collections: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the vector store and embedding model."""
        if self._client is not None:
            return

        logger.info("Initializing vector store")

        # Load embedding model
        model_name = self.settings.vector_store.embedding_model
        self._embedder = SentenceTransformer(model_name)

        # Initialize ChromaDB
        if self.settings.vector_store.backend == "chroma":
            import chromadb
            from chromadb.config import Settings

            persist_path = str(self.settings.vector_store.chroma_persist_path)
            self._client = chromadb.Client(
                Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_path,
                    anonymized_telemetry=False,
                )
            )

        logger.info("Vector store initialized", backend=self.settings.vector_store.backend)

    def _get_collection(self, name: str):
        """Get or create a collection."""
        full_name = f"{self.settings.vector_store.collection_prefix}_{name}"

        if full_name not in self._collections:
            self._collections[full_name] = self._client.get_or_create_collection(
                name=full_name,
                metadata={"hnsw:space": "cosine"},
            )

        return self._collections[full_name]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        return self._embedder.encode(texts, convert_to_numpy=True).tolist()

    async def add(
        self,
        collection: str,
        id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a document to the vector store.

        Args:
            collection: Collection name
            id: Unique document ID
            content: Text content to embed
            metadata: Optional metadata
        """
        await self.initialize()

        coll = self._get_collection(collection)
        embedding = self._embed([content])[0]

        coll.add(
            ids=[id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata or {}],
        )

        logger.debug("Added to vector store", collection=collection, id=id)

    async def add_batch(
        self,
        collection: str,
        items: list[tuple[str, str, dict[str, Any] | None]],
    ) -> None:
        """Add multiple documents to the vector store.

        Args:
            collection: Collection name
            items: List of (id, content, metadata) tuples
        """
        await self.initialize()

        if not items:
            return

        coll = self._get_collection(collection)

        ids = [item[0] for item in items]
        contents = [item[1] for item in items]
        metadatas = [item[2] or {} for item in items]

        embeddings = self._embed(contents)

        coll.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )

        logger.info("Added batch to vector store", collection=collection, count=len(items))

    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents.

        Args:
            query: Search query text
            collection: Collection to search
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of search results
        """
        await self.initialize()

        coll = self._get_collection(collection)
        query_embedding = self._embed([query])[0]

        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                # Convert distance to similarity score (cosine)
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - (distance / 2)  # Convert cosine distance to similarity

                search_results.append(
                    SearchResult(
                        id=id_,
                        score=score,
                        content=results["documents"][0][i] if results["documents"] else "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )

        return search_results

    async def delete(self, collection: str, id: str) -> bool:
        """Delete a document from the vector store.

        Args:
            collection: Collection name
            id: Document ID to delete

        Returns:
            True if deleted
        """
        await self.initialize()

        coll = self._get_collection(collection)
        coll.delete(ids=[id])
        return True

    async def clear_collection(self, collection: str) -> None:
        """Clear all documents from a collection."""
        await self.initialize()

        full_name = f"{self.settings.vector_store.collection_prefix}_{collection}"
        self._client.delete_collection(full_name)
        if full_name in self._collections:
            del self._collections[full_name]

        logger.info("Cleared collection", collection=collection)

    async def get_collection_count(self, collection: str) -> int:
        """Get the number of documents in a collection."""
        await self.initialize()

        coll = self._get_collection(collection)
        return coll.count()
