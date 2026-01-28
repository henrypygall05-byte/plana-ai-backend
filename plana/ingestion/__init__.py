"""
Council portal ingestion adapters.

Provides interfaces and implementations for fetching planning
application data from UK council planning portals.
"""

from plana.ingestion.base import (
    CouncilAdapter,
    ApplicationDetails,
    PortalDocument,
    PortalAccessError,
)
from plana.ingestion.newcastle import NewcastleAdapter

__all__ = [
    "CouncilAdapter",
    "ApplicationDetails",
    "PortalDocument",
    "PortalAccessError",
    "NewcastleAdapter",
    "get_adapter",
]


def get_adapter(council_id: str) -> CouncilAdapter:
    """Get the appropriate adapter for a council.

    Args:
        council_id: Council identifier (e.g., 'newcastle')

    Returns:
        CouncilAdapter instance

    Raises:
        ValueError: If council is not supported
    """
    adapters = {
        "newcastle": NewcastleAdapter,
    }

    adapter_class = adapters.get(council_id.lower())
    if not adapter_class:
        supported = ", ".join(adapters.keys())
        raise ValueError(f"Unsupported council: {council_id}. Supported: {supported}")

    return adapter_class()
