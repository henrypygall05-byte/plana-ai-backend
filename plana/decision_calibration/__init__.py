"""
Decision calibration module for Plana.AI.

Normalizes Plana's raw decisions to match Newcastle case officer patterns.
This improves QC accuracy without changing core assessment logic.
"""

from plana.decision_calibration.calibrator import (
    parse_application_type,
    calibrate_decision,
    CALIBRATION_RULES,
)

__all__ = [
    "parse_application_type",
    "calibrate_decision",
    "CALIBRATION_RULES",
]
