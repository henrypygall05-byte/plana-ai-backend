"""
GIS constraint checking using free UK government APIs.

Queries real geographic datasets to verify planning constraints at a
given lat/lon point:

- **Flood zones** — Environment Agency Flood Map for Planning API
- **Listed buildings** — Historic England Listed Buildings API
- **SSSIs** — Natural England MAGIC/DEFRA API
- **Conservation areas** — Historic England Conservation Areas API

All APIs are free, no authentication required, and return GeoJSON.
Results are cached per postcode for the lifetime of the process.

Usage::

    from plana.location.gis import check_gis_constraints

    result = check_gis_constraints(lat=52.9877, lon=-1.2822)
    for c in result.constraints:
        print(f"{c.constraint_type}: {c.name} (source: {c.source})")
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from plana.core.logging import get_logger

logger = get_logger(__name__)

# Timeout for external API calls (seconds)
_API_TIMEOUT = 8.0

# Buffer distance for point-based searches (metres)
_SEARCH_RADIUS_M = 100


@dataclass
class GISConstraint:
    """A single constraint verified against GIS data."""

    constraint_type: str  # e.g. "Flood Zone", "Listed Building"
    name: str  # e.g. "Flood Zone 3", "Grade II: The Old Vicarage"
    verified: bool = True  # True = confirmed by GIS query
    source: str = ""  # e.g. "Environment Agency Flood Map for Planning"
    distance_m: Optional[float] = None  # distance from site (if relevant)
    details: str = ""  # extra detail string
    raw: dict = field(default_factory=dict)  # raw API response


@dataclass
class GISCheckResult:
    """Result of running all GIS constraint checks for a location."""

    latitude: float
    longitude: float
    constraints: list[GISConstraint] = field(default_factory=list)
    checked_types: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_flood_risk(self) -> bool:
        return any(c.constraint_type == "Flood Zone" for c in self.constraints)

    @property
    def has_listed_building(self) -> bool:
        return any(c.constraint_type == "Listed Building" for c in self.constraints)

    @property
    def has_conservation_area(self) -> bool:
        return any(c.constraint_type == "Conservation Area" for c in self.constraints)

    @property
    def has_sssi(self) -> bool:
        return any(c.constraint_type == "SSSI" for c in self.constraints)

    def constraint_strings(self) -> list[str]:
        """Return constraint strings suitable for the constraints list."""
        result = []
        for c in self.constraints:
            if c.name:
                result.append(f"{c.constraint_type}: {c.name}")
            else:
                result.append(c.constraint_type)
        return result


# =========================================================================
# Environment Agency — Flood Map for Planning
# =========================================================================

def _check_flood_zones(lat: float, lon: float) -> list[GISConstraint]:
    """Query the EA Flood Map for Planning (flood zones 2 and 3).

    Uses the EA's open GeoJSON endpoint. Free, no key required.
    Docs: https://environment.data.gov.uk/
    """
    constraints = []

    # EA Flood Zones endpoint — query by bounding box around the point
    # The API uses EPSG:4326 (WGS84) coordinates
    delta = 0.001  # ~100m buffer
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    for zone_id, zone_name in [("2", "Flood Zone 2"), ("3", "Flood Zone 3")]:
        url = (
            f"https://environment.data.gov.uk/arcgis/rest/services/"
            f"EA/FloodMapForPlanningRiversAndSeaFloodZone{zone_id}/"
            f"MapServer/0/query"
            f"?geometry={bbox}"
            f"&geometryType=esriGeometryEnvelope"
            f"&inSR=4326&outSR=4326"
            f"&spatialRel=esriSpatialRelIntersects"
            f"&returnCountOnly=true"
            f"&f=json"
        )
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            count = data.get("count", 0)
            if count > 0:
                constraints.append(GISConstraint(
                    constraint_type="Flood Zone",
                    name=zone_name,
                    source="Environment Agency Flood Map for Planning",
                    details=f"Site intersects {zone_name} (EA open data)",
                    raw=data,
                ))
        except Exception as exc:
            logger.warning("gis_flood_check_failed", zone=zone_name, error=str(exc))

    return constraints


# =========================================================================
# Historic England — Listed Buildings
# =========================================================================

def _check_listed_buildings(lat: float, lon: float) -> list[GISConstraint]:
    """Query Historic England for listed buildings near the site.

    Uses the HE open data API (ArcGIS REST). Free, no key required.
    """
    constraints = []

    delta = 0.002  # ~200m search radius
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    url = (
        "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/ArcGIS/rest/services/"
        "Listed_Buildings/FeatureServer/0/query"
        f"?geometry={bbox}"
        "&geometryType=esriGeometryEnvelope"
        "&inSR=4326&outSR=4326"
        "&spatialRel=esriSpatialRelIntersects"
        "&outFields=ListEntry,Name,Grade,ListDate"
        "&returnGeometry=false"
        "&resultRecordCount=10"
        "&f=json"
    )

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        features = data.get("features", [])
        for feat in features[:5]:
            attrs = feat.get("attributes", {})
            name = attrs.get("Name", "Unknown")
            grade = attrs.get("Grade", "")
            entry = attrs.get("ListEntry", "")
            grade_text = f"Grade {grade}" if grade else ""

            constraints.append(GISConstraint(
                constraint_type="Listed Building",
                name=f"{grade_text}: {name}".strip(": "),
                source="Historic England Listed Buildings Register",
                details=f"List Entry: {entry}" if entry else "",
                raw=attrs,
            ))
    except Exception as exc:
        logger.warning("gis_listed_buildings_check_failed", error=str(exc))

    return constraints


# =========================================================================
# Historic England — Conservation Areas
# =========================================================================

def _check_conservation_areas(lat: float, lon: float) -> list[GISConstraint]:
    """Query Historic England for conservation areas at the site.

    Uses the HE open data API. Free, no key required.
    """
    constraints = []

    delta = 0.001  # ~100m buffer
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    url = (
        "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/ArcGIS/rest/services/"
        "Conservation_Areas/FeatureServer/0/query"
        f"?geometry={bbox}"
        "&geometryType=esriGeometryEnvelope"
        "&inSR=4326&outSR=4326"
        "&spatialRel=esriSpatialRelIntersects"
        "&outFields=NAME,DESIG_DATE,REFERENCE"
        "&returnGeometry=false"
        "&resultRecordCount=5"
        "&f=json"
    )

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        features = data.get("features", [])
        for feat in features:
            attrs = feat.get("attributes", {})
            name = attrs.get("NAME", "Unnamed Conservation Area")
            constraints.append(GISConstraint(
                constraint_type="Conservation Area",
                name=name,
                source="Historic England Conservation Areas Dataset",
                raw=attrs,
            ))
    except Exception as exc:
        logger.warning("gis_conservation_area_check_failed", error=str(exc))

    return constraints


# =========================================================================
# Natural England — SSSIs
# =========================================================================

def _check_sssi(lat: float, lon: float) -> list[GISConstraint]:
    """Query Natural England for SSSIs near the site.

    Uses the DEFRA/NE open data API. Free, no key required.
    """
    constraints = []

    delta = 0.005  # ~500m search radius for SSSIs
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    url = (
        "https://services.arcgis.com/JJzESW51TqeY9uj9/arcgis/rest/services/"
        "SSSI_England/FeatureServer/0/query"
        f"?geometry={bbox}"
        "&geometryType=esriGeometryEnvelope"
        "&inSR=4326&outSR=4326"
        "&spatialRel=esriSpatialRelIntersects"
        "&outFields=SSSI_NAME,STATUS"
        "&returnGeometry=false"
        "&resultRecordCount=5"
        "&f=json"
    )

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        features = data.get("features", [])
        for feat in features:
            attrs = feat.get("attributes", {})
            name = attrs.get("SSSI_NAME", "Unnamed SSSI")
            constraints.append(GISConstraint(
                constraint_type="SSSI",
                name=name,
                source="Natural England SSSI Dataset",
                raw=attrs,
            ))
    except Exception as exc:
        logger.warning("gis_sssi_check_failed", error=str(exc))

    return constraints


# =========================================================================
# Green Belt — DLUHC
# =========================================================================

def _check_green_belt(lat: float, lon: float) -> list[GISConstraint]:
    """Query for Green Belt designation at the site.

    Uses the DLUHC Local Authority Green Belt dataset.
    """
    constraints = []

    delta = 0.001
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    url = (
        "https://services.arcgis.com/JJzESW51TqeY9uj9/arcgis/rest/services/"
        "Green_Belt_England/FeatureServer/0/query"
        f"?geometry={bbox}"
        "&geometryType=esriGeometryEnvelope"
        "&inSR=4326&outSR=4326"
        "&spatialRel=esriSpatialRelIntersects"
        "&outFields=LA_Name"
        "&returnCountOnly=true"
        "&f=json"
    )

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        count = data.get("count", 0)
        if count > 0:
            constraints.append(GISConstraint(
                constraint_type="Green Belt",
                name="Green Belt",
                source="DLUHC Green Belt Dataset",
                raw=data,
            ))
    except Exception as exc:
        logger.warning("gis_green_belt_check_failed", error=str(exc))

    return constraints


# =========================================================================
# Main entry point
# =========================================================================

@lru_cache(maxsize=256)
def _cached_check(lat_round: float, lon_round: float) -> tuple:
    """Internal cached implementation — rounds coords to ~11m precision."""
    constraints = []
    checked = []
    errors = []

    checks = [
        ("Flood Zone", _check_flood_zones),
        ("Listed Building", _check_listed_buildings),
        ("Conservation Area", _check_conservation_areas),
        ("SSSI", _check_sssi),
        ("Green Belt", _check_green_belt),
    ]

    for check_name, check_fn in checks:
        try:
            results = check_fn(lat_round, lon_round)
            constraints.extend(results)
            checked.append(check_name)
        except Exception as exc:
            errors.append(f"{check_name}: {exc}")
            logger.warning("gis_check_error", check=check_name, error=str(exc))

    return tuple(constraints), tuple(checked), tuple(errors)


def check_gis_constraints(
    lat: float, lon: float,
) -> GISCheckResult:
    """Run all GIS constraint checks for a location.

    Queries free UK government APIs to verify planning constraints.
    Results are cached per ~11m grid cell.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        GISCheckResult with verified constraints and check status.
    """
    # Round to 4 decimal places (~11m precision) for caching
    lat_r = round(lat, 4)
    lon_r = round(lon, 4)

    logger.info("gis_constraint_check_start", lat=lat_r, lon=lon_r)

    constraints, checked, errors = _cached_check(lat_r, lon_r)

    result = GISCheckResult(
        latitude=lat,
        longitude=lon,
        constraints=list(constraints),
        checked_types=list(checked),
        errors=list(errors),
    )

    logger.info(
        "gis_constraint_check_complete",
        lat=lat_r,
        lon=lon_r,
        constraints_found=len(result.constraints),
        types_checked=len(result.checked_types),
        errors=len(result.errors),
    )

    return result
