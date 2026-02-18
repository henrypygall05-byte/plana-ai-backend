"""
Postcodes.io integration for location intelligence.

Provides free, no-API-key-required lookup of UK postcodes to enrich
planning applications with:
- Latitude / longitude
- Administrative district (council)
- Ward name
- Parish
- LSOA (Lower Layer Super Output Area)
- Country
- Region

Also derives location-based constraints by cross-referencing the
postcode data with known constraint zones (flood risk areas,
conservation areas, Green Belt, etc.).
"""

import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PostcodeResult:
    """Result of a postcodes.io lookup."""

    postcode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    admin_district: str = ""  # e.g. "Broxtowe", "Newcastle upon Tyne"
    admin_county: str = ""  # e.g. "Nottinghamshire"
    ward: str = ""  # e.g. "Eastwood St Marys"
    parish: str = ""  # e.g. "Eastwood"
    lsoa: str = ""  # e.g. "Broxtowe 007A"
    region: str = ""  # e.g. "East Midlands"
    country: str = ""  # e.g. "England"
    parliamentary_constituency: str = ""
    outcode: str = ""  # e.g. "NG16"
    incode: str = ""  # e.g. "2AA"
    # Derived enrichments
    distance_to_town_centre_km: Optional[float] = None
    flood_risk_zone: Optional[str] = None
    detected_constraints: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)

    @property
    def full_postcode(self) -> str:
        return self.postcode

    @property
    def postcode_sector(self) -> str:
        """e.g. 'NG16 2' from 'NG16 2AA'."""
        parts = self.postcode.strip().split()
        if len(parts) == 2 and len(parts[1]) >= 1:
            return f"{parts[0]} {parts[1][0]}"
        return self.outcode

    @property
    def postcode_district(self) -> str:
        """e.g. 'NG16' from 'NG16 2AA'."""
        return self.outcode


def lookup_postcode(postcode: str, timeout: float = 5.0) -> Optional[PostcodeResult]:
    """Look up a UK postcode via the postcodes.io API.

    This is a free API with no authentication required.
    Rate limit: ~unlimited for normal usage.

    Args:
        postcode: UK postcode (e.g. "NG16 2AA" or "NE2 2QU")
        timeout: Request timeout in seconds

    Returns:
        PostcodeResult with location data, or None if lookup failed.
    """
    # Normalize postcode for URL
    clean = postcode.strip().replace(" ", "")
    if not clean:
        return None

    url = f"https://api.postcodes.io/postcodes/{clean}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return None

    if data.get("status") != 200 or not data.get("result"):
        return None

    r = data["result"]

    return PostcodeResult(
        postcode=r.get("postcode", postcode),
        latitude=r.get("latitude"),
        longitude=r.get("longitude"),
        admin_district=r.get("admin_district") or "",
        admin_county=r.get("admin_county") or "",
        ward=r.get("admin_ward") or "",
        parish=r.get("parish") or "",
        lsoa=r.get("lsoa") or "",
        region=r.get("region") or "",
        country=r.get("country") or "",
        parliamentary_constituency=r.get("parliamentary_constituency") or "",
        outcode=r.get("outcode") or "",
        incode=r.get("incode") or "",
        raw_data=r,
    )


def bulk_lookup_postcodes(
    postcodes: list[str], timeout: float = 10.0
) -> dict[str, Optional[PostcodeResult]]:
    """Look up multiple postcodes in a single API call (max 100).

    Args:
        postcodes: List of UK postcodes
        timeout: Request timeout in seconds

    Returns:
        Dict mapping postcode -> PostcodeResult (or None if failed)
    """
    if not postcodes:
        return {}

    # API supports max 100 per request
    batch = [p.strip().replace(" ", "") for p in postcodes[:100]]
    url = "https://api.postcodes.io/postcodes"
    body = json.dumps({"postcodes": batch}).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return {p: None for p in postcodes}

    results = {}
    for item in data.get("result", []):
        query = item.get("query", "")
        r = item.get("result")
        if r:
            results[query] = PostcodeResult(
                postcode=r.get("postcode", query),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
                admin_district=r.get("admin_district") or "",
                admin_county=r.get("admin_county") or "",
                ward=r.get("admin_ward") or "",
                parish=r.get("parish") or "",
                lsoa=r.get("lsoa") or "",
                region=r.get("region") or "",
                country=r.get("country") or "",
                parliamentary_constituency=r.get("parliamentary_constituency") or "",
                outcode=r.get("outcode") or "",
                incode=r.get("incode") or "",
                raw_data=r,
            )
        else:
            results[query] = None

    return results


# =========================================================================
# Constraint detection from location data
# =========================================================================

# Known flood risk areas by LSOA prefix (simplified mapping)
# In production, this would use Environment Agency flood map API
FLOOD_RISK_LSOA: dict[str, str] = {
    # Broxtowe known flood risk areas
    "Broxtowe 001": "Flood Zone 2",  # Attenborough area near River Trent
    "Broxtowe 002": "Flood Zone 3",  # Beeston Rylands near River Trent
    "Broxtowe 003": "Flood Zone 2",  # Beeston near canal
    # Newcastle known flood risk areas
    "Newcastle upon Tyne 018": "Flood Zone 2",  # Ouseburn valley
    "Newcastle upon Tyne 024": "Flood Zone 2",  # Walker riverside
}

# Known conservation areas by ward (simplified mapping)
# In production, this would use GIS polygon data
CONSERVATION_AREA_WARDS: dict[str, list[str]] = {
    # Newcastle
    "South Jesmond": ["Jesmond Conservation Area"],
    "Monument": ["Grainger Town Conservation Area", "Central Conservation Area"],
    "Ouseburn": ["Ouseburn Conservation Area"],
    "Gosforth": ["Gosforth High Street Conservation Area"],
    # Broxtowe
    "Eastwood St Marys": ["D.H. Lawrence Conservation Area"],
    "Beeston Central": ["Beeston Town Centre Conservation Area"],
}

# Green Belt areas by ward (simplified mapping)
GREEN_BELT_WARDS: dict[str, str] = {
    # Newcastle
    "Westerhope": "Tyne and Wear Green Belt",
    "Castle": "Tyne and Wear Green Belt",
    # Broxtowe
    "Awsworth, Cossall and Trowell": "Nottinghamshire Green Belt",
    "Brinsley": "Nottinghamshire Green Belt",
}

# Listed buildings hotspots by ward (simplified)
LISTED_BUILDING_WARDS: dict[str, str] = {
    "South Jesmond": "Multiple Grade II listed buildings",
    "Monument": "Multiple Grade I and II listed buildings",
    "Gosforth": "Scattered Grade II listed buildings",
    "Eastwood St Marys": "D.H. Lawrence birthplace (Grade II)",
}

# Tree Preservation Order hotspots
TPO_WARDS: set[str] = {
    "South Jesmond", "Gosforth", "Beeston Central",
    "Bramcote", "Attenborough",
}


def get_location_constraints(
    postcode_result: PostcodeResult,
) -> list[str]:
    """Derive planning constraints from postcode location data.

    Cross-references the ward, LSOA, and area data against known
    constraint zones.  This is a best-effort enrichment — the
    definitive source is always the council's own constraint map.

    Args:
        postcode_result: Result from ``lookup_postcode()``

    Returns:
        List of detected constraint strings (may be empty)
    """
    constraints: list[str] = []
    ward = postcode_result.ward
    lsoa = postcode_result.lsoa

    # Flood risk check
    for lsoa_prefix, zone in FLOOD_RISK_LSOA.items():
        if lsoa and lsoa.startswith(lsoa_prefix):
            constraints.append(f"{zone} (based on LSOA {lsoa})")
            break

    # Conservation area check
    if ward in CONSERVATION_AREA_WARDS:
        for ca in CONSERVATION_AREA_WARDS[ward]:
            constraints.append(f"Potential: {ca}")

    # Green Belt check
    if ward in GREEN_BELT_WARDS:
        constraints.append(f"Green Belt ({GREEN_BELT_WARDS[ward]})")

    # Listed building proximity
    if ward in LISTED_BUILDING_WARDS:
        constraints.append(f"Listed buildings in area: {LISTED_BUILDING_WARDS[ward]}")

    # TPO check
    if ward in TPO_WARDS:
        constraints.append("Tree Preservation Orders present in ward")

    postcode_result.detected_constraints = constraints
    return constraints


def enrich_application_location(
    postcode: Optional[str],
    address: str = "",
    existing_constraints: Optional[list[str]] = None,
) -> dict:
    """Enrich an application with location intelligence.

    Performs a postcodes.io lookup and derives constraints.
    Returns a dict with all enrichment data that can be merged
    into the application context.

    Args:
        postcode: UK postcode
        address: Site address (for context)
        existing_constraints: Already-known constraints (won't duplicate)

    Returns:
        Dict with location enrichment data::

            {
                "postcode_data": PostcodeResult or None,
                "ward": str,
                "parish": str,
                "admin_district": str,
                "region": str,
                "latitude": float or None,
                "longitude": float or None,
                "detected_constraints": [...],
                "all_constraints": [...],  # existing + detected, deduplicated
            }
    """
    existing = set(c.lower() for c in (existing_constraints or []))

    if not postcode:
        return {
            "postcode_data": None,
            "ward": "",
            "parish": "",
            "admin_district": "",
            "region": "",
            "latitude": None,
            "longitude": None,
            "detected_constraints": [],
            "all_constraints": list(existing_constraints or []),
        }

    result = lookup_postcode(postcode)
    if not result:
        return {
            "postcode_data": None,
            "ward": "",
            "parish": "",
            "admin_district": "",
            "region": "",
            "latitude": None,
            "longitude": None,
            "detected_constraints": [],
            "all_constraints": list(existing_constraints or []),
        }

    detected = get_location_constraints(result)

    # Merge constraints without duplicating
    all_constraints = list(existing_constraints or [])
    for c in detected:
        if c.lower() not in existing:
            all_constraints.append(c)
            existing.add(c.lower())

    return {
        "postcode_data": result,
        "ward": result.ward,
        "parish": result.parish,
        "admin_district": result.admin_district,
        "region": result.region,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "detected_constraints": detected,
        "all_constraints": all_constraints,
    }
