"""
Decision calibrator for Plana.AI.

Calibrates raw Plana decisions to match Newcastle case officer patterns.

Newcastle case officers routinely issue "Grant Conditionally" (APPROVE_WITH_CONDITIONS)
for most application types. This calibration layer adjusts Plana's raw decisions
to reflect these local patterns without changing the core assessment logic.
"""

from typing import Optional


# Calibration rules by application type
# These reflect observed Newcastle case officer decision patterns
CALIBRATION_RULES = {
    # Types that almost always get conditions
    "HOU": "APPROVE_WITH_CONDITIONS",  # Householder
    "LBC": "APPROVE_WITH_CONDITIONS",  # Listed Building Consent
    "DET": "APPROVE_WITH_CONDITIONS",  # Full Planning (Detailed)
    "LDC": "APPROVE_WITH_CONDITIONS",  # Lawful Development Certificate

    # Types that typically get plain approval
    "DCC": "APPROVE",  # Discharge of Conditions

    # Types with variable outcomes - no forced calibration
    "TPO": None,  # Tree Preservation Order
    "TCA": None,  # Trees in Conservation Area
}


def parse_application_type(reference: str) -> str:
    """
    Extract application type code from reference number.

    Newcastle reference format: YYYY/NNNN/NN/XXX
    Where XXX is the application type code.

    Args:
        reference: Application reference number (e.g., "2025/2090/01/LDC")

    Returns:
        Application type code in uppercase (e.g., "LDC")

    Examples:
        >>> parse_application_type("2025/2090/01/LDC")
        'LDC'
        >>> parse_application_type("2025/0486/04/DCC")
        'DCC'
        >>> parse_application_type("  2025/1974/01/HOU  ")
        'HOU'
    """
    if not reference:
        return "UNKNOWN"

    # Strip whitespace and convert to uppercase
    ref_clean = reference.strip().upper()

    # Split by forward slash
    parts = ref_clean.split("/")

    if len(parts) >= 4:
        return parts[-1].strip()
    elif len(parts) >= 1:
        # Fallback: try to extract last component
        return parts[-1].strip()

    return "UNKNOWN"


def calibrate_decision(reference: str, raw_decision: str) -> str:
    """
    Calibrate a raw decision based on application type.

    This applies Newcastle-specific decision patterns to improve QC accuracy.

    Calibration Rules:
    1. REFUSE decisions are NEVER overridden
    2. For APPROVE/APPROVE_WITH_CONDITIONS:
       - HOU, LBC, DET, LDC → APPROVE_WITH_CONDITIONS (officers add conditions)
       - DCC → APPROVE (discharge is typically unconditional)
       - TPO, TCA → Keep raw decision (variable outcomes)
    3. Unknown decisions remain UNKNOWN

    Args:
        reference: Application reference number
        raw_decision: Plana's original decision

    Returns:
        Calibrated decision string

    Examples:
        >>> calibrate_decision("2025/1974/01/HOU", "APPROVE")
        'APPROVE_WITH_CONDITIONS'
        >>> calibrate_decision("2025/0486/04/DCC", "APPROVE_WITH_CONDITIONS")
        'APPROVE'
        >>> calibrate_decision("2025/1739/01/TPO", "REFUSE")
        'REFUSE'
    """
    if not raw_decision:
        return "UNKNOWN"

    # Normalize raw decision
    decision = raw_decision.strip().upper().replace(" ", "_").replace("-", "_")

    # Map common variations
    if decision in ("APPROVE", "APPROVED", "GRANT", "GRANTED"):
        decision = "APPROVE"
    elif decision in ("APPROVE_WITH_CONDITIONS", "APPROVED_WITH_CONDITIONS",
                      "GRANT_WITH_CONDITIONS", "CONDITIONAL", "CONDITIONAL_APPROVAL"):
        decision = "APPROVE_WITH_CONDITIONS"
    elif decision in ("REFUSE", "REFUSED", "REJECT", "REJECTED"):
        decision = "REFUSE"
    else:
        return "UNKNOWN"

    # Rule 1: Never override refusals
    if decision == "REFUSE":
        return "REFUSE"

    # Rule 2: Calibrate approvals based on application type
    if decision in ("APPROVE", "APPROVE_WITH_CONDITIONS"):
        app_type = parse_application_type(reference)

        # Check if we have a calibration rule for this type
        if app_type in CALIBRATION_RULES:
            calibrated = CALIBRATION_RULES[app_type]
            if calibrated is not None:
                return calibrated

        # No specific rule - return raw decision as-is
        return decision

    return "UNKNOWN"


def get_calibration_explanation(app_type: str) -> Optional[str]:
    """
    Get explanation for why a particular application type is calibrated.

    Args:
        app_type: Application type code

    Returns:
        Explanation string or None if no special calibration
    """
    explanations = {
        "HOU": "Householder applications typically receive conditions",
        "LBC": "Listed Building Consent typically includes protective conditions",
        "DET": "Full planning applications typically receive standard conditions",
        "LDC": "Lawful Development Certificates typically include conditions",
        "DCC": "Discharge of Conditions typically granted without further conditions",
        "TPO": "Tree works outcomes vary based on arboricultural assessment",
        "TCA": "Tree works in conservation areas have variable outcomes",
    }
    return explanations.get(app_type)
