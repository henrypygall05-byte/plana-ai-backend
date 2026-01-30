"""
Council abstraction layer for multi-council support.

This module provides a plugin-based architecture for supporting different UK council
planning portals. Each council implements the CouncilPortal interface.

Set PLANA_USE_FIXTURES=true to use offline fixture data instead of live portal.
"""

import os

from plana.councils.base import CouncilPortal, CouncilRegistry
from plana.councils.newcastle import NewcastlePortal
from plana.councils.fixtures import FixturePortal

# Register available councils
CouncilRegistry.register("newcastle", NewcastlePortal)


def get_portal(council_id: str = "newcastle") -> CouncilPortal:
    """
    Get the appropriate portal based on configuration.

    Returns FixturePortal if PLANA_USE_FIXTURES=true, otherwise live portal.

    Args:
        council_id: Council identifier

    Returns:
        CouncilPortal instance
    """
    use_fixtures = os.environ.get("PLANA_USE_FIXTURES", "").lower() in ("true", "1", "yes")

    if use_fixtures:
        return FixturePortal(council_id)

    return CouncilRegistry.get(council_id)


__all__ = [
    "CouncilPortal",
    "CouncilRegistry",
    "NewcastlePortal",
    "FixturePortal",
    "get_portal",
]
