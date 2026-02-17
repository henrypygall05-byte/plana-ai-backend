"""
Document Analysis System for Planning Applications.

Extracts structured data from planning documents including:
- Floor plans: bedroom count, floor area, room layouts
- Site plans: plot dimensions, parking spaces, separation distances
- Elevations: building height, materials, storey count
- Design & Access Statements: design rationale, policy compliance claims

This module provides evidence-based data extraction to replace placeholder text
with actual verified measurements and specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import re


class DocumentConfidence(str, Enum):
    """Confidence level in extracted data."""
    VERIFIED = "verified"           # Explicitly stated in document
    MEASURED = "measured"           # Measured from scaled drawing
    INFERRED = "inferred"           # Deduced from context
    ESTIMATED = "estimated"         # Best guess from limited info
    NOT_FOUND = "not_found"         # Could not extract


class DataSource(str, Enum):
    """Source of extracted data."""
    FLOOR_PLAN = "floor_plan"
    SITE_PLAN = "site_plan"
    ELEVATION = "elevation"
    SECTION_DRAWING = "section"
    DESIGN_ACCESS_STATEMENT = "das"
    APPLICATION_FORM = "application_form"
    PLANNING_STATEMENT = "planning_statement"
    COVER_LETTER = "cover_letter"
    MANUAL_ENTRY = "manual_entry"


@dataclass
class ExtractedMeasurement:
    """A measurement extracted from a document with provenance."""
    value: float
    unit: str
    confidence: DocumentConfidence
    source: DataSource
    source_document: str = ""           # Document filename
    source_page: int | None = None      # Page number if applicable
    extraction_method: str = ""         # How it was extracted
    raw_text: str = ""                  # Original text if from OCR
    verified_by: str | None = None      # Case officer verification


@dataclass
class ExtractedRoom:
    """Room information extracted from floor plans."""
    name: str                           # e.g., "Bedroom 1", "Kitchen"
    room_type: str                      # bedroom, bathroom, living, kitchen, etc.
    floor_level: int = 0                # 0=ground, 1=first, -1=basement
    area_sqm: float | None = None
    dimensions: tuple[float, float] | None = None  # (width, length) in metres
    has_window: bool = True
    window_orientation: str | None = None  # N, S, E, W, NE, etc.
    is_ensuite: bool = False
    confidence: DocumentConfidence = DocumentConfidence.INFERRED


@dataclass
class ExtractedParkingSpace:
    """Parking space information from site plans."""
    space_type: str                     # "driveway", "garage", "carport", "on-street"
    dimensions: tuple[float, float] | None = None  # (width, length) metres
    is_covered: bool = False
    ev_charging: bool = False
    disabled_access: bool = False
    confidence: DocumentConfidence = DocumentConfidence.INFERRED


@dataclass
class ExtractedBoundary:
    """Boundary relationship extracted from site plans."""
    direction: str                      # "north", "south", "east", "west"
    boundary_type: str                  # "fence", "wall", "hedge", "open"
    height_metres: float | None = None
    neighbour_address: str | None = None
    separation_distance_metres: float | None = None
    window_to_window_distance: float | None = None
    confidence: DocumentConfidence = DocumentConfidence.INFERRED


@dataclass
class ExtractedMaterial:
    """Building material extracted from documents."""
    element: str                        # "walls", "roof", "windows", "doors"
    material: str                       # "brick", "render", "slate", etc.
    colour: str | None = None
    manufacturer: str | None = None
    matches_neighbours: bool | None = None
    confidence: DocumentConfidence = DocumentConfidence.INFERRED
    source: DataSource = DataSource.ELEVATION


@dataclass
class ExtractedDocumentData:
    """Complete extracted data from all application documents."""

    # Basic proposal details
    development_type: str = ""
    development_description: str = ""

    # Unit counts (with confidence)
    num_units: int = 0
    num_units_confidence: DocumentConfidence = DocumentConfidence.NOT_FOUND
    num_units_source: str = ""

    num_bedrooms: int = 0
    num_bedrooms_confidence: DocumentConfidence = DocumentConfidence.NOT_FOUND
    num_bedrooms_source: str = ""

    num_bathrooms: int = 0
    num_storeys: int = 0

    # Dimensions
    total_floor_area_sqm: float = 0.0
    floor_area_confidence: DocumentConfidence = DocumentConfidence.NOT_FOUND
    floor_area_source: str = ""

    plot_area_sqm: float = 0.0
    plot_coverage_percent: float = 0.0
    garden_area_sqm: float = 0.0

    ridge_height_metres: float = 0.0
    ridge_height_confidence: DocumentConfidence = DocumentConfidence.NOT_FOUND

    eaves_height_metres: float = 0.0
    building_width_metres: float = 0.0
    building_depth_metres: float = 0.0

    # Detailed room breakdown
    rooms: list[ExtractedRoom] = field(default_factory=list)

    # Parking
    parking_spaces: list[ExtractedParkingSpace] = field(default_factory=list)
    total_parking_spaces: int = 0
    cycle_spaces: int = 0
    ev_charging_provision: bool = False

    # Boundaries and neighbours
    boundaries: list[ExtractedBoundary] = field(default_factory=list)

    # Materials
    materials: list[ExtractedMaterial] = field(default_factory=list)

    # Access
    access_type: str = ""               # "new", "existing", "improved"
    access_width_metres: float = 0.0
    visibility_splay_left: float = 0.0  # metres
    visibility_splay_right: float = 0.0

    # Distances to neighbours (key for amenity assessment)
    distance_to_nearest_neighbour: float = 0.0
    distance_to_rear_boundary: float = 0.0
    distance_to_front_boundary: float = 0.0

    # Window relationships (for privacy/overlooking)
    proposed_windows: list[dict] = field(default_factory=list)
    facing_neighbours_windows: bool = False
    overlooking_risk: str = ""          # "none", "low", "moderate", "high"

    # Extraction metadata
    documents_analysed: list[str] = field(default_factory=list)
    extraction_timestamp: str = ""
    extraction_warnings: list[str] = field(default_factory=list)
    data_gaps: list[str] = field(default_factory=list)
    verification_required: list[str] = field(default_factory=list)


def extract_from_text(text: str, document_type: str, filename: str = "") -> ExtractedDocumentData:
    """
    Extract structured data from document text.

    Args:
        text: The extracted text content from the document
        document_type: Type of document (floor_plan, elevation, das, etc.)
        filename: Original filename for provenance tracking

    Returns:
        ExtractedDocumentData with all found information
    """
    data = ExtractedDocumentData()
    data.documents_analysed.append(filename)
    data.extraction_timestamp = datetime.now().isoformat()
    text_lower = text.lower()

    # Extract bedrooms
    bedroom_patterns = [
        r'(\d+)\s*(?:no\.?\s*)?bed(?:room)?s?(?:\s*dwelling)?',
        r'(\d+)\s*(?:bed|br|bedroom)\s*(?:house|property|dwelling|home)',
        r'bed(?:room)?s?\s*[:\-]?\s*(\d+)',
        r'(\d+)\s*(?:single|double|master|guest)\s*bed(?:room)?s?',
        r'number of bedrooms[:\s]*(\d+)',
    ]

    for pattern in bedroom_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.num_bedrooms = int(match.group(1))
            data.num_bedrooms_confidence = DocumentConfidence.VERIFIED
            data.num_bedrooms_source = filename
            break

    # Extract from room labels in floor plans
    bedroom_labels = re.findall(r'(?:bed(?:room)?\s*\d+|master\s*bed(?:room)?|guest\s*bed(?:room)?|single\s*bed(?:room)?|double\s*bed(?:room)?)', text_lower)
    if bedroom_labels and data.num_bedrooms == 0:
        data.num_bedrooms = len(set(bedroom_labels))
        data.num_bedrooms_confidence = DocumentConfidence.MEASURED
        data.num_bedrooms_source = filename

        # Create room entries
        for i, label in enumerate(set(bedroom_labels), 1):
            data.rooms.append(ExtractedRoom(
                name=f"Bedroom {i}",
                room_type="bedroom",
                floor_level=1 if 'first' in text_lower else 0,
                confidence=DocumentConfidence.MEASURED
            ))

    # Extract number of units
    unit_patterns = [
        r'(\d+)\s*(?:no\.?\s*)?(?:dwelling|unit|house|flat|apartment|home)s?',
        r'(?:erection|construction|development)\s*of\s*(\d+)',
        r'(\d+)\s*(?:new\s*)?(?:residential\s*)?(?:dwelling|unit)s?',
    ]

    for pattern in unit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.num_units = int(match.group(1))
            data.num_units_confidence = DocumentConfidence.VERIFIED
            data.num_units_source = filename
            break

    # Default to 1 for single dwelling proposals
    if data.num_units == 0 and any(word in text_lower for word in ['dwelling', 'house', 'bungalow']):
        data.num_units = 1
        data.num_units_confidence = DocumentConfidence.INFERRED

    # Extract floor area
    area_patterns = [
        r'(?:total\s*)?(?:floor\s*)?area[:\s]*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)',
        r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)\s*(?:floor\s*)?area',
        r'gifa[:\s]*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)',
        r'(\d+(?:\.\d+)?)\s*(?:square\s*)?met(?:re|er)s?\s*(?:floor\s*)?area',
    ]

    for pattern in area_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.total_floor_area_sqm = float(match.group(1))
            data.floor_area_confidence = DocumentConfidence.VERIFIED
            data.floor_area_source = filename
            break

    # Extract ridge height
    height_patterns = [
        r'ridge\s*(?:height)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?',
        r'(?:overall\s*)?height[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?',
        r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:to\s*)?ridge',
        r'max(?:imum)?\s*height[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?',
    ]

    for pattern in height_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.ridge_height_metres = float(match.group(1))
            data.ridge_height_confidence = DocumentConfidence.VERIFIED
            break

    # Extract eaves height
    eaves_patterns = [
        r'eaves?\s*(?:height)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?',
        r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:to\s*)?eaves?',
    ]

    for pattern in eaves_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.eaves_height_metres = float(match.group(1))
            break

    # Extract storeys
    storey_patterns = [
        r'(\d+)[\s\-]*(?:storey|story|floor)(?:ed)?',
        r'(?:single|one)[\s\-]*(?:storey|story)',
        r'(?:two|2)[\s\-]*(?:storey|story)',
        r'(?:three|3)[\s\-]*(?:storey|story)',
    ]

    if 'single' in text_lower or 'one storey' in text_lower or '1 storey' in text_lower:
        data.num_storeys = 1
    elif 'two storey' in text_lower or '2 storey' in text_lower or 'two-storey' in text_lower:
        data.num_storeys = 2
    elif 'three storey' in text_lower or '3 storey' in text_lower:
        data.num_storeys = 3
    else:
        for pattern in storey_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if match.group(1):
                    data.num_storeys = int(match.group(1))
                break

    # Extract parking spaces
    parking_patterns = [
        r'(\d+)\s*(?:car\s*)?(?:parking\s*)?(?:space|bay)s?',
        r'parking[:\s]*(\d+)',
        r'(\d+)\s*(?:off[\-\s]*street|on[\-\s]*site)\s*(?:parking\s*)?(?:space|bay)?s?',
    ]

    for pattern in parking_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.total_parking_spaces = int(match.group(1))
            # Create parking space entries
            for i in range(data.total_parking_spaces):
                space_type = "garage" if "garage" in text_lower else "driveway"
                data.parking_spaces.append(ExtractedParkingSpace(
                    space_type=space_type,
                    is_covered="garage" in text_lower or "carport" in text_lower,
                    ev_charging="ev" in text_lower or "electric" in text_lower,
                    confidence=DocumentConfidence.VERIFIED
                ))
            break

    # Extract materials
    material_mappings = {
        'walls': ['brick', 'render', 'stone', 'timber', 'cladding', 'weatherboard'],
        'roof': ['slate', 'tile', 'tiles', 'metal', 'thatch', 'sedum', 'green roof'],
        'windows': ['upvc', 'aluminium', 'aluminum', 'timber', 'wood'],
        'doors': ['composite', 'timber', 'upvc', 'aluminium'],
    }

    for element, keywords in material_mappings.items():
        for material in keywords:
            if material in text_lower:
                data.materials.append(ExtractedMaterial(
                    element=element,
                    material=material,
                    confidence=DocumentConfidence.VERIFIED,
                    source=DataSource.ELEVATION if document_type == "elevation" else DataSource.DESIGN_ACCESS_STATEMENT
                ))

    # Extract separation distances
    separation_patterns = [
        r'separation\s*(?:distance)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?',
        r'(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*(?:from|to)\s*(?:boundary|neighbour)',
        r'distance\s*to\s*(?:boundary|neighbour)[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?',
    ]

    for pattern in separation_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.distance_to_nearest_neighbour = float(match.group(1))
            break

    # Extract visibility splays
    visibility_patterns = [
        r'visibility\s*(?:splay)?[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*[xX×]\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:m|metre|meter)s?\s*visibility',
    ]

    for pattern in visibility_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Typically expressed as 2.4m x 43m (setback x splay distance)
            data.visibility_splay_left = float(match.group(2))
            data.visibility_splay_right = float(match.group(2))
            break

    # Extract plot/site area
    plot_patterns = [
        r'(?:plot|site)\s*area[:\s]*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)',
        r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|m2|m²)\s*(?:plot|site)',
    ]

    for pattern in plot_patterns:
        match = re.search(pattern, text_lower)
        if match:
            data.plot_area_sqm = float(match.group(1))
            break

    # Calculate plot coverage if we have both values
    if data.plot_area_sqm > 0 and data.total_floor_area_sqm > 0:
        data.plot_coverage_percent = (data.total_floor_area_sqm / data.plot_area_sqm) * 100

    # Identify data gaps
    if data.num_bedrooms == 0:
        data.data_gaps.append("Number of bedrooms not specified")
    if data.total_floor_area_sqm == 0:
        data.data_gaps.append("Floor area not specified")
    if data.ridge_height_metres == 0:
        data.data_gaps.append("Building height not specified")
    if data.total_parking_spaces == 0:
        data.data_gaps.append("Parking provision not specified")
    if data.num_storeys == 0:
        data.data_gaps.append("Number of storeys not specified")
    if not data.materials:
        data.data_gaps.append("External materials not specified")
    if data.distance_to_nearest_neighbour == 0:
        data.verification_required.append("Separation distances to be measured from plans")

    return data


def merge_document_extractions(extractions: list[ExtractedDocumentData]) -> ExtractedDocumentData:
    """
    Merge multiple document extractions, preferring higher confidence data.

    Args:
        extractions: List of extractions from different documents

    Returns:
        Single merged ExtractedDocumentData with best available data
    """
    if not extractions:
        return ExtractedDocumentData()

    if len(extractions) == 1:
        return extractions[0]

    merged = ExtractedDocumentData()

    # Priority order for confidence levels
    confidence_priority = {
        DocumentConfidence.VERIFIED: 4,
        DocumentConfidence.MEASURED: 3,
        DocumentConfidence.INFERRED: 2,
        DocumentConfidence.ESTIMATED: 1,
        DocumentConfidence.NOT_FOUND: 0,
    }

    for extraction in extractions:
        merged.documents_analysed.extend(extraction.documents_analysed)

        # Bedrooms - take highest confidence
        if confidence_priority.get(extraction.num_bedrooms_confidence, 0) > \
           confidence_priority.get(merged.num_bedrooms_confidence, 0):
            merged.num_bedrooms = extraction.num_bedrooms
            merged.num_bedrooms_confidence = extraction.num_bedrooms_confidence
            merged.num_bedrooms_source = extraction.num_bedrooms_source

        # Units - take highest confidence
        if confidence_priority.get(extraction.num_units_confidence, 0) > \
           confidence_priority.get(merged.num_units_confidence, 0):
            merged.num_units = extraction.num_units
            merged.num_units_confidence = extraction.num_units_confidence
            merged.num_units_source = extraction.num_units_source

        # Floor area - take highest confidence
        if confidence_priority.get(extraction.floor_area_confidence, 0) > \
           confidence_priority.get(merged.floor_area_confidence, 0):
            merged.total_floor_area_sqm = extraction.total_floor_area_sqm
            merged.floor_area_confidence = extraction.floor_area_confidence
            merged.floor_area_source = extraction.floor_area_source

        # Ridge height - take highest confidence
        if confidence_priority.get(extraction.ridge_height_confidence, 0) > \
           confidence_priority.get(merged.ridge_height_confidence, 0):
            merged.ridge_height_metres = extraction.ridge_height_metres
            merged.ridge_height_confidence = extraction.ridge_height_confidence

        # Take non-zero values for simple fields
        if extraction.num_bathrooms > merged.num_bathrooms:
            merged.num_bathrooms = extraction.num_bathrooms
        if extraction.num_storeys > merged.num_storeys:
            merged.num_storeys = extraction.num_storeys
        if extraction.eaves_height_metres > merged.eaves_height_metres:
            merged.eaves_height_metres = extraction.eaves_height_metres
        if extraction.total_parking_spaces > merged.total_parking_spaces:
            merged.total_parking_spaces = extraction.total_parking_spaces
        if extraction.plot_area_sqm > merged.plot_area_sqm:
            merged.plot_area_sqm = extraction.plot_area_sqm
        if extraction.distance_to_nearest_neighbour > merged.distance_to_nearest_neighbour:
            merged.distance_to_nearest_neighbour = extraction.distance_to_nearest_neighbour

        # Merge lists
        merged.rooms.extend(extraction.rooms)
        merged.parking_spaces.extend(extraction.parking_spaces)
        merged.boundaries.extend(extraction.boundaries)
        merged.materials.extend(extraction.materials)
        merged.data_gaps.extend(extraction.data_gaps)
        merged.verification_required.extend(extraction.verification_required)
        merged.extraction_warnings.extend(extraction.extraction_warnings)

    # Deduplicate lists
    merged.data_gaps = list(set(merged.data_gaps))
    merged.verification_required = list(set(merged.verification_required))
    merged.extraction_warnings = list(set(merged.extraction_warnings))

    # Remove data gaps that have been filled
    if merged.num_bedrooms > 0:
        merged.data_gaps = [g for g in merged.data_gaps if "bedrooms" not in g.lower()]
    if merged.total_floor_area_sqm > 0:
        merged.data_gaps = [g for g in merged.data_gaps if "floor area" not in g.lower()]
    if merged.ridge_height_metres > 0:
        merged.data_gaps = [g for g in merged.data_gaps if "height" not in g.lower()]
    if merged.total_parking_spaces > 0:
        merged.data_gaps = [g for g in merged.data_gaps if "parking" not in g.lower()]

    # Calculate plot coverage if possible
    if merged.plot_area_sqm > 0 and merged.total_floor_area_sqm > 0:
        merged.plot_coverage_percent = (merged.total_floor_area_sqm / merged.plot_area_sqm) * 100

    merged.extraction_timestamp = datetime.now().isoformat()

    return merged


def generate_data_quality_summary(data: ExtractedDocumentData) -> dict:
    """
    Generate a summary of data quality and completeness.

    Returns dict with:
    - overall_confidence: "high", "medium", "low"
    - verified_fields: list of fields with verified data
    - missing_fields: list of fields without data
    - verification_needed: list of fields needing officer verification
    """
    verified = []
    missing = []
    needs_verification = []

    # Check key fields
    if data.num_bedrooms > 0:
        if data.num_bedrooms_confidence == DocumentConfidence.VERIFIED:
            verified.append(f"Bedrooms: {data.num_bedrooms}")
        else:
            needs_verification.append(f"Bedrooms: {data.num_bedrooms} (from {data.num_bedrooms_confidence.value})")
    else:
        missing.append("Number of bedrooms")

    if data.num_units > 0:
        if data.num_units_confidence == DocumentConfidence.VERIFIED:
            verified.append(f"Units: {data.num_units}")
        else:
            needs_verification.append(f"Units: {data.num_units} (from {data.num_units_confidence.value})")
    else:
        missing.append("Number of units")

    if data.total_floor_area_sqm > 0:
        if data.floor_area_confidence == DocumentConfidence.VERIFIED:
            verified.append(f"Floor area: {data.total_floor_area_sqm}sqm")
        else:
            needs_verification.append(f"Floor area: {data.total_floor_area_sqm}sqm (from {data.floor_area_confidence.value})")
    else:
        missing.append("Floor area")

    if data.ridge_height_metres > 0:
        if data.ridge_height_confidence == DocumentConfidence.VERIFIED:
            verified.append(f"Ridge height: {data.ridge_height_metres}m")
        else:
            needs_verification.append(f"Ridge height: {data.ridge_height_metres}m (from {data.ridge_height_confidence.value})")
    else:
        missing.append("Building height")

    if data.total_parking_spaces > 0:
        verified.append(f"Parking: {data.total_parking_spaces} spaces")
    else:
        missing.append("Parking provision")

    if data.num_storeys > 0:
        verified.append(f"Storeys: {data.num_storeys}")
    else:
        missing.append("Number of storeys")

    if data.materials:
        verified.append(f"Materials: {', '.join(m.material for m in data.materials[:3])}")
    else:
        missing.append("External materials")

    # Calculate overall confidence
    total_fields = len(verified) + len(missing) + len(needs_verification)
    verified_ratio = len(verified) / total_fields if total_fields > 0 else 0

    if verified_ratio >= 0.7:
        overall = "high"
    elif verified_ratio >= 0.4:
        overall = "medium"
    else:
        overall = "low"

    return {
        "overall_confidence": overall,
        "verified_fields": verified,
        "missing_fields": missing,
        "verification_needed": needs_verification,
        "documents_analysed": data.documents_analysed,
        "completeness_percent": int(verified_ratio * 100),
    }


def format_extracted_data_for_report(data: ExtractedDocumentData) -> dict:
    """
    Format extracted data for inclusion in the report.

    Returns a dictionary suitable for populating report templates.
    """
    def format_with_source(value: Any, confidence: DocumentConfidence, source: str = "") -> str:
        """Format a value with its source and confidence indicator."""
        if value in (0, 0.0, None, "", []):
            return "Not specified in documents"

        if confidence == DocumentConfidence.VERIFIED:
            return str(value)
        elif confidence == DocumentConfidence.MEASURED:
            return f"{value} (measured from plans)"
        elif confidence == DocumentConfidence.INFERRED:
            return f"{value} (inferred)"
        else:
            return f"{value} (to be verified)"

    # Build materials string
    materials_by_element = {}
    for mat in data.materials:
        if mat.element not in materials_by_element:
            materials_by_element[mat.element] = []
        materials_by_element[mat.element].append(mat.material)

    materials_str = "; ".join(
        f"{element}: {', '.join(mats)}"
        for element, mats in materials_by_element.items()
    ) if materials_by_element else "To be confirmed by condition"

    # Format parking details
    parking_details = []
    if data.parking_spaces:
        garage_count = sum(1 for p in data.parking_spaces if p.space_type == "garage")
        driveway_count = sum(1 for p in data.parking_spaces if p.space_type == "driveway")
        if garage_count:
            parking_details.append(f"{garage_count} garage")
        if driveway_count:
            parking_details.append(f"{driveway_count} driveway")
        if data.ev_charging_provision:
            parking_details.append("EV charging")
    parking_str = ", ".join(parking_details) if parking_details else (
        f"{data.total_parking_spaces} spaces" if data.total_parking_spaces > 0 else "Not specified"
    )

    return {
        "num_units": format_with_source(
            data.num_units, data.num_units_confidence, data.num_units_source
        ),
        "num_bedrooms": format_with_source(
            data.num_bedrooms, data.num_bedrooms_confidence, data.num_bedrooms_source
        ),
        "num_storeys": str(data.num_storeys) if data.num_storeys > 0 else "Not specified",
        "floor_area": format_with_source(
            f"{data.total_floor_area_sqm}sqm" if data.total_floor_area_sqm > 0 else "",
            data.floor_area_confidence,
            data.floor_area_source
        ),
        "ridge_height": format_with_source(
            f"{data.ridge_height_metres}m" if data.ridge_height_metres > 0 else "",
            data.ridge_height_confidence
        ),
        "eaves_height": f"{data.eaves_height_metres}m" if data.eaves_height_metres > 0 else "Not specified",
        "materials": materials_str,
        "parking": parking_str,
        "total_parking_spaces": data.total_parking_spaces,
        "plot_area": f"{data.plot_area_sqm}sqm" if data.plot_area_sqm > 0 else "Not specified",
        "plot_coverage": f"{data.plot_coverage_percent:.1f}%" if data.plot_coverage_percent > 0 else "Not calculated",
        "separation_distance": f"{data.distance_to_nearest_neighbour}m" if data.distance_to_nearest_neighbour > 0 else "To be measured",
        "visibility_splays": f"2.4m x {data.visibility_splay_left}m" if data.visibility_splay_left > 0 else "To be verified",
        "data_gaps": data.data_gaps,
        "verification_required": data.verification_required,
        "documents_analysed": data.documents_analysed,
    }
