"""
Search and similarity systems.

Provides vector storage and semantic search for documents,
policies, and historic cases.

By default, uses a stub implementation that works without ML dependencies.
Set VECTOR_BACKEND=chroma to use ChromaDB with sentence-transformers.
"""

import os

from plana.search.stub_vector_store import SearchResult, StubVectorStore

# Export SearchResult from stub (same interface)
__all__ = [
    "SearchResult",
    "VectorStore",
    "SimilaritySearcher",
    "get_vector_store",
]


def get_vector_store():
    """
    Get appropriate vector store based on configuration.

    Returns StubVectorStore by default (no ML dependencies).
    Returns full VectorStore if VECTOR_BACKEND=chroma and dependencies installed.
    """
    from plana.config import get_settings

    settings = get_settings()

    # Check if user explicitly wants the full vector store
    if settings.vector_store.backend == "chroma":
        try:
            from plana.search.vector_store import VectorStore as FullVectorStore
            return FullVectorStore()
        except ImportError as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning(
                "ChromaDB/sentence-transformers not installed, using stub",
                error=str(e),
            )
            return StubVectorStore()

    # Default to stub
    return StubVectorStore()


# Default VectorStore - use stub for zero-dependency startup
# This allows `from plana.search import VectorStore` to work
class VectorStore(StubVectorStore):
    """
    Default vector store (stub implementation).

    For full semantic search with embeddings, use get_vector_store()
    with VECTOR_BACKEND=chroma configured.
    """
    pass


def get_similarity_searcher():
    """Get similarity searcher with appropriate vector store."""
    from plana.search.similarity import SimilaritySearcher
    return SimilaritySearcher(vector_store=get_vector_store())


# Lazy import for SimilaritySearcher
def __getattr__(name):
    if name == "SimilaritySearcher":
        from plana.search.similarity import SimilaritySearcher
        return SimilaritySearcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
