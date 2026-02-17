"""
Plana.AI Council Modules.

Each council has its own module with:
- Policy database (Local Plan + NPPF integration)
- Historic cases database
- Case officer module for generating reports

Available councils:
- broxtowe: Broxtowe Borough Council (Greater Nottingham area)
"""

from . import broxtowe

__all__ = ["broxtowe"]
