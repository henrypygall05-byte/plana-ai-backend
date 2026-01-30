"""
Similarity search module for historic planning applications.

Finds similar cases based on proposal type, constraints,
location, and decision outcomes.
"""

from plana.similarity.search import SimilaritySearch, SimilarCase

__all__ = ["SimilaritySearch", "SimilarCase"]
