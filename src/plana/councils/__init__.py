"""
Council abstraction layer for multi-council support.

This module provides a plugin-based architecture for supporting different UK council
planning portals. Each council implements the CouncilPortal interface.
"""

from plana.councils.base import CouncilPortal, CouncilRegistry
from plana.councils.newcastle import NewcastlePortal

# Register available councils
CouncilRegistry.register("newcastle", NewcastlePortal)

__all__ = [
    "CouncilPortal",
    "CouncilRegistry",
    "NewcastlePortal",
]
