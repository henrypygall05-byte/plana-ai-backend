"""
Plana.AI REST API for Loveable integration.

Exposes endpoints for:
- Processing applications
- Retrieving reports
- Submitting feedback
- Health checks
"""

from plana.api.app import create_app

__all__ = ["create_app"]
