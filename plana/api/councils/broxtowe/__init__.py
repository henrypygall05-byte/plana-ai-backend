"""
Broxtowe Borough Council Planning Module.

This module provides planning assessment capabilities for Broxtowe Borough Council,
covering the Greater Nottingham area with the Aligned Core Strategy (2014) and
Broxtowe Part 2 Local Plan (2019).

Key areas covered:
- Beeston, Stapleford, Eastwood, Kimberley, Bramcote, Chilwell, Attenborough
"""

from .policies import BROXTOWE_POLICIES, get_broxtowe_policies
from .cases import BROXTOWE_HISTORIC_CASES, find_similar_broxtowe_cases
from .case_officer import generate_broxtowe_report

__all__ = [
    "BROXTOWE_POLICIES",
    "get_broxtowe_policies",
    "BROXTOWE_HISTORIC_CASES",
    "find_similar_broxtowe_cases",
    "generate_broxtowe_report",
]
