"""
LPA Jurisdiction Enforcement Service.

Implements strict Local Planning Authority boundary enforcement.
All policy retrieval and comparable application searches must be
filtered by the identified LPA. Cross-authority contamination is
not permitted.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class JurisdictionError(Exception):
    """Base exception for jurisdiction-related errors."""

    pass


class UnknownJurisdictionError(JurisdictionError):
    """Raised when the LPA cannot be identified from the provided location."""

    def __init__(self, address: str, postcode: str | None = None):
        self.address = address
        self.postcode = postcode
        message = (
            f"Unable to identify Local Planning Authority for location: {address}"
            + (f" (postcode: {postcode})" if postcode else "")
            + ". Please provide a valid UK address within a supported council area, "
            + "or explicitly specify the council_id parameter."
        )
        super().__init__(message)


class MultipleJurisdictionsError(JurisdictionError):
    """Raised when multiple LPAs are detected for the provided location."""

    def __init__(
        self,
        address: str,
        detected_authorities: list[str],
        postcode: str | None = None,
    ):
        self.address = address
        self.postcode = postcode
        self.detected_authorities = detected_authorities
        authority_names = ", ".join(detected_authorities)
        message = (
            f"Multiple Local Planning Authorities detected for location: {address}. "
            f"Possible authorities: {authority_names}. "
            "Please clarify which authority has statutory planning control, "
            "or provide a more specific address/postcode to resolve jurisdiction."
        )
        super().__init__(message)


@dataclass
class LocalPlanInfo:
    """Information about an adopted Local Plan."""

    plan_name: str
    adoption_date: date | None
    plan_period: str | None
    status: str  # "adopted", "emerging", "under_review"
    source_url: str | None = None


@dataclass
class LPAIdentificationResult:
    """Result of LPA identification with full context."""

    # Core identification
    council_id: str
    council_name: str
    is_confirmed: bool  # True if high confidence, False if needs verification

    # Local Plan details
    adopted_local_plan: LocalPlanInfo | None = None
    supplementary_documents: list[str] = field(default_factory=list)

    # Location details
    input_address: str = ""
    input_postcode: str | None = None
    detected_ward: str | None = None

    # Confidence and warnings
    confidence_score: float = 1.0
    boundary_warning: str | None = None  # Set if near authority boundary
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "council_id": self.council_id,
            "council_name": self.council_name,
            "is_confirmed": self.is_confirmed,
            "adopted_local_plan": {
                "plan_name": self.adopted_local_plan.plan_name,
                "adoption_date": (
                    self.adopted_local_plan.adoption_date.isoformat()
                    if self.adopted_local_plan and self.adopted_local_plan.adoption_date
                    else None
                ),
                "plan_period": self.adopted_local_plan.plan_period,
                "status": self.adopted_local_plan.status,
                "source_url": self.adopted_local_plan.source_url,
            }
            if self.adopted_local_plan
            else None,
            "supplementary_documents": self.supplementary_documents,
            "input_address": self.input_address,
            "input_postcode": self.input_postcode,
            "detected_ward": self.detected_ward,
            "confidence_score": self.confidence_score,
            "boundary_warning": self.boundary_warning,
            "notes": self.notes,
        }


# =============================================================================
# POSTCODE TO COUNCIL MAPPING - STRICT BOUNDARIES
# =============================================================================

# Postcode areas with CONFIRMED council jurisdiction
# Note: Some postcodes cross boundaries - these are marked as BOUNDARY_POSTCODES
STRICT_POSTCODE_MAP: dict[str, str] = {
    # Newcastle City Council - CONFIRMED areas
    "NE1": "newcastle",  # City Centre
    "NE2": "newcastle",  # Jesmond, Sandyford
    "NE3": "newcastle",  # Gosforth, Kenton
    "NE4": "newcastle",  # Fenham, Arthur's Hill
    "NE5": "newcastle",  # Westerhope, Newbiggin Hall
    "NE6": "newcastle",  # Byker, Walker, Heaton
    "NE7": "newcastle",  # High Heaton, Benton
    "NE12": "newcastle",  # Longbenton (part - see boundary)
    "NE13": "newcastle",  # Brunswick Village, Hazlerigg
    "NE15": "newcastle",  # Lemington, Throckley
    # Broxtowe Borough Council - CONFIRMED areas
    "NG9": "broxtowe",  # Beeston, Chilwell, Stapleford
    "NG10": "broxtowe",  # Long Eaton (Erewash), Sandiacre (part)
    "NG16": "broxtowe",  # Eastwood, Kimberley, Newthorpe, Awsworth
}

# Postcodes that cross authority boundaries - REQUIRE CLARIFICATION
# Format: outward_code -> list of possible councils
BOUNDARY_POSTCODES: dict[str, list[str]] = {
    # NE8 - primarily Gateshead but some Newcastle areas
    "NE8": ["gateshead", "newcastle"],
    # NE12 - split between Newcastle and North Tyneside
    "NE12": ["newcastle", "north_tyneside"],
    # NE27, NE28 - North Tyneside but some boundary areas
    "NE27": ["north_tyneside", "newcastle"],
    "NE28": ["north_tyneside", "newcastle"],
    # NG6 - split between Nottingham City and Broxtowe (Bulwell area)
    "NG6": ["nottingham", "broxtowe"],
    # NG10 - split between Broxtowe and Erewash
    "NG10": ["broxtowe", "erewash"],
}

# Place names with CONFIRMED council jurisdiction
STRICT_PLACE_MAP: dict[str, str] = {
    # Newcastle City Council - CONFIRMED areas
    "newcastle upon tyne": "newcastle",
    "newcastle": "newcastle",
    "gosforth": "newcastle",
    "jesmond": "newcastle",
    "heaton": "newcastle",
    "byker": "newcastle",
    "walker": "newcastle",
    "benwell": "newcastle",
    "fenham": "newcastle",
    "kenton": "newcastle",
    "blakelaw": "newcastle",
    "denton": "newcastle",
    "westerhope": "newcastle",
    "elswick": "newcastle",
    "arthurs hill": "newcastle",
    "sandyford": "newcastle",
    "ouseburn": "newcastle",
    "city centre newcastle": "newcastle",
    # Broxtowe Borough Council - CONFIRMED areas
    "broxtowe": "broxtowe",
    "beeston": "broxtowe",
    "stapleford": "broxtowe",
    "chilwell": "broxtowe",
    "eastwood": "broxtowe",
    "kimberley": "broxtowe",
    "newthorpe": "broxtowe",
    "awsworth": "broxtowe",
    "nuthall": "broxtowe",
    "giltbrook": "broxtowe",
    "brinsley": "broxtowe",
    "cossall": "broxtowe",
    "trowell": "broxtowe",
    "bramcote": "broxtowe",
    "attenborough": "broxtowe",
    "toton": "broxtowe",
}

# Place names near boundaries - MAY REQUIRE CLARIFICATION
BOUNDARY_PLACES: dict[str, list[str]] = {
    "longbenton": ["newcastle", "north_tyneside"],
    "benton": ["newcastle", "north_tyneside"],
    "bulwell": ["nottingham", "broxtowe"],
    "long eaton": ["broxtowe", "erewash"],
    "sandiacre": ["broxtowe", "erewash"],
}

# Local Plan information by council
LOCAL_PLAN_INFO: dict[str, LocalPlanInfo] = {
    "newcastle": LocalPlanInfo(
        plan_name="Newcastle Local Plan (Core Strategy and Urban Core Plan)",
        adoption_date=date(2015, 3, 26),
        plan_period="2010-2030",
        status="adopted",
        source_url="https://www.newcastle.gov.uk/planning-and-buildings/planning-policy/local-plan",
    ),
    "broxtowe": LocalPlanInfo(
        plan_name="Broxtowe Part 2 Local Plan",
        adoption_date=date(2019, 10, 16),
        plan_period="2018-2028",
        status="adopted",
        source_url="https://www.broxtowe.gov.uk/for-you/planning/planning-policy/local-plan/",
    ),
}

# Supplementary Planning Documents by council
SPD_LIST: dict[str, list[str]] = {
    "newcastle": [
        "Design Quality SPD",
        "Developer Contributions SPD",
        "Biodiversity SPD",
        "Conservation Areas Character Appraisals",
    ],
    "broxtowe": [
        "Design Guide SPD",
        "Developer Contributions SPD",
        "Green Infrastructure Strategy",
    ],
}


class JurisdictionService:
    """
    Service for strict LPA jurisdiction enforcement.

    All policy retrieval and comparable application searches
    must be filtered by the identified LPA. No cross-authority
    semantic retrieval is permitted.
    """

    def __init__(self):
        """Initialize the jurisdiction service."""
        self._postcode_map = STRICT_POSTCODE_MAP.copy()
        self._boundary_postcodes = BOUNDARY_POSTCODES.copy()
        self._place_map = STRICT_PLACE_MAP.copy()
        self._boundary_places = BOUNDARY_PLACES.copy()

    def identify_lpa(
        self,
        address: str,
        postcode: str | None = None,
        allow_boundary_ambiguity: bool = False,
    ) -> LPAIdentificationResult:
        """
        Identify the Local Planning Authority for a given location.

        Args:
            address: Full site address
            postcode: Optional explicit postcode
            allow_boundary_ambiguity: If True, returns first match for boundary
                                      cases instead of raising error

        Returns:
            LPAIdentificationResult with full context

        Raises:
            UnknownJurisdictionError: If LPA cannot be identified
            MultipleJurisdictionsError: If multiple LPAs are detected
        """
        address_lower = address.lower()
        detected_councils: set[str] = set()
        boundary_warning: str | None = None
        notes: list[str] = []

        # Extract postcode from address if not provided
        if not postcode:
            postcode = self._extract_postcode(address)

        # Step 1: Check postcode (most reliable)
        if postcode:
            postcode_clean = postcode.replace(" ", "").upper()
            outward_code = self._extract_outward_code(postcode_clean)

            if outward_code:
                # Check for boundary postcodes first
                if outward_code in self._boundary_postcodes:
                    possible_councils = self._boundary_postcodes[outward_code]
                    if not allow_boundary_ambiguity:
                        raise MultipleJurisdictionsError(
                            address=address,
                            detected_authorities=[
                                self._get_council_name(c) for c in possible_councils
                            ],
                            postcode=postcode,
                        )
                    else:
                        # Use first match but add warning
                        detected_councils.add(possible_councils[0])
                        boundary_warning = (
                            f"Postcode {outward_code} crosses authority boundaries. "
                            f"Possible authorities: {', '.join(self._get_council_name(c) for c in possible_councils)}. "
                            "Please verify the correct jurisdiction."
                        )
                        notes.append(f"Boundary postcode detected: {outward_code}")

                # Check strict postcode map
                elif outward_code in self._postcode_map:
                    detected_councils.add(self._postcode_map[outward_code])
                    notes.append(f"LPA identified from postcode: {outward_code}")

        # Step 2: Check place names in address
        for place, council_id in self._place_map.items():
            if place in address_lower:
                detected_councils.add(council_id)
                notes.append(f"LPA identified from place name: {place}")

        # Step 3: Check for boundary place names
        for place, possible_councils in self._boundary_places.items():
            if place in address_lower:
                if not allow_boundary_ambiguity and len(possible_councils) > 1:
                    # Add to detected but will raise error below
                    for c in possible_councils:
                        detected_councils.add(c)
                    boundary_warning = (
                        f"Place '{place}' is near authority boundary. "
                        f"Possible authorities: {', '.join(self._get_council_name(c) for c in possible_councils)}."
                    )

        # Step 4: Check for regional indicators
        if "tyne and wear" in address_lower or "upon tyne" in address_lower:
            detected_councils.add("newcastle")
            notes.append("LPA inferred from 'Tyne and Wear' region indicator")

        if "nottinghamshire" in address_lower:
            # Could be multiple councils - check more specifically
            for place in ["eastwood", "kimberley", "beeston", "stapleford"]:
                if place in address_lower:
                    detected_councils.add("broxtowe")
                    notes.append(f"LPA identified from Nottinghamshire + {place}")
                    break

        # Evaluate results
        if len(detected_councils) == 0:
            logger.warning(
                "Unknown jurisdiction",
                address=address,
                postcode=postcode,
            )
            raise UnknownJurisdictionError(address=address, postcode=postcode)

        if len(detected_councils) > 1 and not allow_boundary_ambiguity:
            logger.warning(
                "Multiple jurisdictions detected",
                address=address,
                postcode=postcode,
                councils=list(detected_councils),
            )
            raise MultipleJurisdictionsError(
                address=address,
                detected_authorities=[
                    self._get_council_name(c) for c in detected_councils
                ],
                postcode=postcode,
            )

        # Single council identified (or first match if ambiguity allowed)
        council_id = list(detected_councils)[0]
        council_name = self._get_council_name(council_id)
        local_plan = LOCAL_PLAN_INFO.get(council_id)
        spds = SPD_LIST.get(council_id, [])

        logger.info(
            "LPA identified",
            council_id=council_id,
            council_name=council_name,
            address=address,
            postcode=postcode,
            confidence="high" if len(detected_councils) == 1 else "medium",
        )

        return LPAIdentificationResult(
            council_id=council_id,
            council_name=council_name,
            is_confirmed=len(detected_councils) == 1 and boundary_warning is None,
            adopted_local_plan=local_plan,
            supplementary_documents=spds,
            input_address=address,
            input_postcode=postcode,
            confidence_score=1.0 if len(detected_councils) == 1 else 0.7,
            boundary_warning=boundary_warning,
            notes=notes,
        )

    def validate_council_id(self, council_id: str) -> bool:
        """
        Validate that a council_id is supported.

        Args:
            council_id: The council identifier to validate

        Returns:
            True if supported, False otherwise
        """
        return council_id.lower() in LOCAL_PLAN_INFO

    def get_supported_councils(self) -> list[str]:
        """Get list of supported council IDs."""
        return list(LOCAL_PLAN_INFO.keys())

    def get_local_plan_info(self, council_id: str) -> LocalPlanInfo | None:
        """Get Local Plan information for a council."""
        return LOCAL_PLAN_INFO.get(council_id.lower())

    def get_spd_list(self, council_id: str) -> list[str]:
        """Get list of Supplementary Planning Documents for a council."""
        return SPD_LIST.get(council_id.lower(), [])

    def _extract_postcode(self, address: str) -> str | None:
        """Extract UK postcode from address string."""
        pattern = r"\b([A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2})\b"
        match = re.search(pattern, address.upper())
        return match.group(1).replace(" ", "") if match else None

    def _extract_outward_code(self, postcode: str) -> str | None:
        """Extract outward code (first part) from postcode."""
        match = re.match(r"^([A-Z]{1,2}[0-9]{1,2})", postcode.upper())
        return match.group(1) if match else None

    def _get_council_name(self, council_id: str) -> str:
        """Get full council name from ID."""
        names = {
            "newcastle": "Newcastle City Council",
            "broxtowe": "Broxtowe Borough Council",
            "gateshead": "Gateshead Council",
            "north_tyneside": "North Tyneside Council",
            "nottingham": "Nottingham City Council",
            "erewash": "Erewash Borough Council",
        }
        return names.get(council_id.lower(), council_id.title())
