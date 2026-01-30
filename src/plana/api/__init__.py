"""
REST API for Plana.AI.

Exposes planning intelligence functionality via HTTP endpoints.
"""

from plana.api.app import create_app

__all__ = ["create_app"]
