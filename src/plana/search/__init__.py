"""
Search and similarity systems.

Provides vector storage and semantic search for documents,
policies, and historic cases.
"""

from plana.search.vector_store import SearchResult, VectorStore
from plana.search.similarity import SimilaritySearcher

__all__ = [
    "SearchResult",
    "VectorStore",
    "SimilaritySearcher",
]
