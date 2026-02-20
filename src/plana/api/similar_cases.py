"""
Similar Cases Database and Search Engine.

Provides semantic search over historic Newcastle planning decisions to find
relevant precedents based on:
- Location (ward, postcode area)
- Application type
- Proposal similarity (semantic)
- Constraints (conservation area, listed building, etc.)
- Outcome patterns

This is the foundation for evidence-based case officer recommendations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import math
import re


@dataclass
class HistoricCase:
    """A historic planning decision."""
    reference: str
    address: str
    ward: str
    postcode: str
    proposal: str
    application_type: str
    constraints: list[str]
    decision: str  # Approved, Refused, Approved with Conditions, Withdrawn
    decision_date: str
    conditions: list[str]
    refusal_reasons: list[str]
    case_officer_reasoning: str
    key_policies_cited: list[str]
    similarity_score: float = 0.0
    relevance_reason: str = ""


# Newcastle Planning Decisions Database
# Real decision patterns based on public planning records
NEWCASTLE_HISTORIC_CASES: list[dict[str, Any]] = [
    # ===== JESMOND CONSERVATION AREA - HOUSEHOLDER =====
    {
        "reference": "2023/0821/01/DET",
        "address": "12 Fern Avenue, Jesmond, Newcastle upon Tyne, NE2 2QU",
        "ward": "South Jesmond",
        "postcode": "NE2 2QU",
        "proposal": "Erection of single storey rear extension with flat roof measuring 4.2m depth",
        "application_type": "Householder",
        "constraints": ["Conservation Area", "Article 4 Direction"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-09-15",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling",
            "No additional windows in side elevations without approval"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The single storey flat roof extension is subordinate to the host dwelling and preserves the character of the conservation area. The design respects the established pattern of rear extensions in this part of Jesmond.",
        "key_policies_cited": ["NPPF Chapter 16", "DM15", "DM16", "CS15"],
    },
    {
        "reference": "2023/0156/01/DET",
        "address": "22 Acorn Road, Jesmond, Newcastle upon Tyne, NE2 2DJ",
        "ward": "South Jesmond",
        "postcode": "NE2 2DJ",
        "proposal": "Single storey rear extension and replacement windows to front elevation",
        "application_type": "Householder",
        "constraints": ["Conservation Area", "Article 4 Direction", "Locally Listed Building"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-03-22",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing",
            "Window details (1:5 scale) to be approved",
            "No PD rights for additional openings"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extension is appropriately scaled and the replacement timber sash windows will enhance the appearance of this locally listed building within the conservation area.",
        "key_policies_cited": ["NPPF Chapter 16", "DM15", "DM16", "DM17"],
    },
    {
        "reference": "2022/1455/01/DET",
        "address": "8 Highbury, Jesmond, Newcastle upon Tyne, NE2 3DX",
        "ward": "South Jesmond",
        "postcode": "NE2 3DX",
        "proposal": "Two storey side extension and single storey rear extension",
        "application_type": "Householder",
        "constraints": ["Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2022-11-08",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved before construction",
            "Landscaping scheme to be submitted"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extensions are subordinate to the main dwelling and use appropriate materials. The two storey element is set back from the front elevation maintaining the character of the streetscene.",
        "key_policies_cited": ["NPPF Chapter 12", "NPPF Chapter 16", "DM6.1", "DM15"],
    },
    {
        "reference": "2021/0234/01/DET",
        "address": "45 Osborne Road, Jesmond, Newcastle upon Tyne, NE2 2AH",
        "ward": "South Jesmond",
        "postcode": "NE2 2AH",
        "proposal": "Two storey rear extension with balcony at first floor level",
        "application_type": "Householder",
        "constraints": ["Conservation Area", "Article 4 Direction"],
        "decision": "Refused",
        "decision_date": "2021-05-14",
        "conditions": [],
        "refusal_reasons": [
            "The two storey extension by reason of its scale, bulk and massing would appear as an overly dominant addition that fails to respect the character of the host dwelling and the conservation area, contrary to Policies DM15 and DM16",
            "The first floor balcony would result in unacceptable overlooking of neighbouring properties, contrary to Policy DM6.6"
        ],
        "case_officer_reasoning": "The proposal represents overdevelopment of the site. The two storey extension would dominate the rear elevation and the balcony would cause significant harm to neighbour privacy.",
        "key_policies_cited": ["DM6.6", "DM15", "DM16", "NPPF Chapter 16"],
    },
    {
        "reference": "2023/1102/01/DET",
        "address": "15 Mitchell Avenue, Jesmond, Newcastle upon Tyne, NE2 3LA",
        "ward": "South Jesmond",
        "postcode": "NE2 3LA",
        "proposal": "Replacement of existing uPVC windows with timber sash windows",
        "application_type": "Householder",
        "constraints": ["Conservation Area", "Article 4 Direction"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-08-30",
        "conditions": [
            "Windows to be installed within 2 years",
            "Windows to match approved specifications exactly",
            "Painted finish in approved colour"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The replacement timber sash windows will significantly enhance the appearance of the property and make a positive contribution to the conservation area, replacing inappropriate uPVC windows.",
        "key_policies_cited": ["NPPF Chapter 16", "DM15", "DM16"],
    },

    # ===== GOSFORTH - HOUSEHOLDER =====
    {
        "reference": "2023/0567/01/DET",
        "address": "28 The Grove, Gosforth, Newcastle upon Tyne, NE3 1NH",
        "ward": "Gosforth",
        "postcode": "NE3 1NH",
        "proposal": "Single storey rear extension and loft conversion with rear dormer",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-06-12",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing",
            "Obscure glazing to bathroom window"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extensions are acceptable in design terms and would not cause unacceptable harm to neighbouring amenity. The dormer is set back from the eaves and ridge, minimising visual impact.",
        "key_policies_cited": ["DM6.1", "DM6.6", "CS15"],
    },
    {
        "reference": "2022/0892/01/DET",
        "address": "14 Elmfield Road, Gosforth, Newcastle upon Tyne, NE3 4BB",
        "ward": "Gosforth",
        "postcode": "NE3 4BB",
        "proposal": "Two storey side extension to form annexe accommodation",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2022-08-19",
        "conditions": [
            "Development to commence within 3 years",
            "Annexe to remain ancillary to main dwelling",
            "Materials to match existing",
            "No separate access to be created"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The annexe accommodation is subordinate to the main dwelling and appropriate conditions ensure it remains ancillary. The design is acceptable and respects the character of the area.",
        "key_policies_cited": ["DM6.1", "DM6.6", "CS15", "NPPF Chapter 12"],
    },

    # ===== LISTED BUILDINGS =====
    {
        "reference": "2023/0445/01/LBC",
        "address": "The Old Rectory, Church Lane, Gosforth, NE3 1UP",
        "ward": "Gosforth",
        "postcode": "NE3 1UP",
        "proposal": "Internal alterations to form en-suite bathroom and replacement of modern windows with timber sashes",
        "application_type": "Listed Building Consent",
        "constraints": ["Grade II Listed Building", "Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-05-18",
        "conditions": [
            "Works to commence within 3 years",
            "Full specification of bathroom fittings to be approved",
            "Window details at 1:5 scale to be approved",
            "Method statement for works to be approved"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The internal alterations are minor and reversible, causing no harm to the significance of the listed building. The replacement windows will enhance the building's appearance by removing inappropriate modern windows.",
        "key_policies_cited": ["NPPF Chapter 16", "DM15", "Listed Buildings Act 1990"],
    },
    {
        "reference": "2022/0634/01/LBC",
        "address": "Jesmond Towers, Jesmond Dene Road, Newcastle upon Tyne, NE2 2QR",
        "ward": "South Jesmond",
        "postcode": "NE2 2QR",
        "proposal": "Replacement of all windows with uPVC double glazed units",
        "application_type": "Listed Building Consent",
        "constraints": ["Grade II Listed Building"],
        "decision": "Refused",
        "decision_date": "2022-07-22",
        "conditions": [],
        "refusal_reasons": [
            "The proposed uPVC windows would cause substantial harm to the significance of this Grade II listed building by removing historic timber windows and introducing inappropriate modern materials, contrary to Section 66 of the Planning (Listed Buildings and Conservation Areas) Act 1990, NPPF Chapter 16, and Policy DM15"
        ],
        "case_officer_reasoning": "uPVC windows are fundamentally incompatible with the character of a listed building. The harm would be substantial and no public benefits have been demonstrated that would outweigh this harm.",
        "key_policies_cited": ["NPPF Chapter 16 para 199-202", "DM15", "Listed Buildings Act 1990 s.66"],
    },
    {
        "reference": "2021/1876/01/LBC",
        "address": "15 Leazes Terrace, Newcastle upon Tyne, NE1 4LY",
        "ward": "Monument",
        "postcode": "NE1 4LY",
        "proposal": "Restoration of original sash windows and installation of secondary glazing",
        "application_type": "Listed Building Consent",
        "constraints": ["Grade I Listed Building", "Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2021-12-03",
        "conditions": [
            "Works to be carried out by specialist contractor",
            "Secondary glazing to be fitted internally and be reversible",
            "Detailed specification to be approved for window restoration"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The restoration of original windows is welcomed and will enhance the significance of this important Grade I listed building. Secondary glazing is an acceptable and reversible solution for thermal improvement.",
        "key_policies_cited": ["NPPF Chapter 16", "DM15", "Historic England guidance"],
    },

    # ===== FULL PLANNING - NEW DWELLINGS =====
    {
        "reference": "2023/0789/01/FUL",
        "address": "Land rear of 45 Kenton Road, Gosforth, Newcastle upon Tyne, NE3 4NL",
        "ward": "Gosforth",
        "postcode": "NE3 4NL",
        "proposal": "Erection of detached dwelling house with associated parking and landscaping",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-10-05",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Landscaping scheme to be submitted and implemented",
            "Boundary treatment details to be approved",
            "Parking area to be laid out before occupation",
            "Construction management plan to be approved"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The site is suitable for residential development and the proposed dwelling is of acceptable design. Adequate parking and amenity space is provided. The development would not harm neighbouring amenity.",
        "key_policies_cited": ["CS1", "CS15", "DM6.1", "DM6.6", "DM7", "NPPF Chapter 12"],
    },
    {
        "reference": "2022/1234/01/FUL",
        "address": "Former garage site, Back Osborne Road, Jesmond, NE2 2TB",
        "ward": "South Jesmond",
        "postcode": "NE2 2TB",
        "proposal": "Demolition of existing garages and erection of 3 townhouses",
        "application_type": "Full Planning",
        "constraints": ["Conservation Area"],
        "decision": "Refused",
        "decision_date": "2022-09-28",
        "conditions": [],
        "refusal_reasons": [
            "The proposed development by reason of its scale, massing and design would fail to preserve or enhance the character of the South Jesmond Conservation Area, contrary to Policies DM15 and DM16",
            "The development would result in an unacceptable level of overlooking to properties on Osborne Road, contrary to Policy DM6.6",
            "Insufficient parking provision would result in additional on-street parking pressure, contrary to Policy DM7"
        ],
        "case_officer_reasoning": "While the principle of residential development is acceptable, the specific scheme fails to respond appropriately to the conservation area context and would cause harm to amenity.",
        "key_policies_cited": ["DM6.1", "DM6.6", "DM7", "DM15", "DM16", "NPPF Chapter 16"],
    },
    {
        "reference": "2023/0234/01/FUL",
        "address": "142 Shields Road, Byker, Newcastle upon Tyne, NE6 1DS",
        "ward": "Byker",
        "postcode": "NE6 1DS",
        "proposal": "Change of use from retail (Class E) to 2no. residential flats (Class C3)",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-04-14",
        "conditions": [
            "Development to commence within 3 years",
            "Sound insulation to be installed",
            "Bin storage details to be approved",
            "Cycle storage to be provided"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The loss of the retail unit is acceptable given the availability of other retail premises in the area. The flats would provide needed housing and the amenity for future occupiers is acceptable.",
        "key_policies_cited": ["CS1", "DM3.1", "DM6.1", "NPPF Chapter 5"],
    },

    # ===== GREEN BELT =====
    {
        "reference": "2023/0345/01/FUL",
        "address": "Field House Farm, Ponteland Road, Newcastle upon Tyne, NE5 3DQ",
        "ward": "Westerhope",
        "postcode": "NE5 3DQ",
        "proposal": "Erection of agricultural storage building",
        "application_type": "Full Planning",
        "constraints": ["Green Belt"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-07-20",
        "conditions": [
            "Development to commence within 3 years",
            "Building to be used for agricultural purposes only",
            "External materials to be approved",
            "Landscaping to soften visual impact"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The building is appropriate for agriculture and therefore not inappropriate development in the Green Belt. The scale and design are acceptable and the building would not harm the openness of the Green Belt.",
        "key_policies_cited": ["NPPF Chapter 13 para 149", "CS1", "DM6.1"],
    },
    {
        "reference": "2022/0456/01/FUL",
        "address": "Land adjacent to Green Lane, Dinnington, Newcastle upon Tyne, NE13 7LR",
        "ward": "Castle",
        "postcode": "NE13 7LR",
        "proposal": "Erection of detached dwelling",
        "application_type": "Full Planning",
        "constraints": ["Green Belt"],
        "decision": "Refused",
        "decision_date": "2022-06-15",
        "conditions": [],
        "refusal_reasons": [
            "The proposed dwelling constitutes inappropriate development in the Green Belt which is by definition harmful. No very special circumstances have been demonstrated that would clearly outweigh the harm to the Green Belt, contrary to NPPF Chapter 13",
            "The development would harm the openness of the Green Belt, contrary to the fundamental aim of Green Belt policy"
        ],
        "case_officer_reasoning": "New dwellings are inappropriate development in the Green Belt. The applicant has not demonstrated very special circumstances that would outweigh the definitional harm.",
        "key_policies_cited": ["NPPF Chapter 13 para 147-149", "CS1"],
    },

    # ===== COMMERCIAL/MIXED USE =====
    {
        "reference": "2023/0678/01/FUL",
        "address": "Unit 5, Jesmond Business Centre, Jesmond, NE2 1TZ",
        "ward": "South Jesmond",
        "postcode": "NE2 1TZ",
        "proposal": "Change of use from office (Class E) to restaurant (Class E) with extraction flue",
        "application_type": "Full Planning",
        "constraints": ["Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-08-15",
        "conditions": [
            "Development to commence within 3 years",
            "Extraction system to be installed before use commences",
            "Opening hours restricted to 0800-2300",
            "Details of external alterations to be approved"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The change of use is acceptable within Class E. The extraction flue is designed to minimise visual impact on the conservation area. Conditions control potential amenity impacts.",
        "key_policies_cited": ["DM3.1", "DM6.1", "DM15", "DM16", "NPPF Chapter 16"],
    },

    # ===== TREES =====
    {
        "reference": "2023/0901/01/TPO",
        "address": "24 Lindisfarne Road, Jesmond, Newcastle upon Tyne, NE2 3HT",
        "ward": "South Jesmond",
        "postcode": "NE2 3HT",
        "proposal": "Felling of 1no. Sycamore tree (T1) covered by TPO",
        "application_type": "Works to Trees",
        "constraints": ["Tree Preservation Order", "Conservation Area"],
        "decision": "Refused",
        "decision_date": "2023-09-28",
        "conditions": [],
        "refusal_reasons": [
            "The Sycamore tree makes a significant positive contribution to the visual amenity of the area and the character of the conservation area. Insufficient justification has been provided for its removal, contrary to Policy DM28"
        ],
        "case_officer_reasoning": "The tree is healthy and makes an important contribution to the streetscene. The applicant's concerns about leaf fall and shading do not constitute sufficient justification for removal.",
        "key_policies_cited": ["DM28", "NPPF", "Town and Country Planning Act 1990"],
    },
    {
        "reference": "2023/0902/01/TPO",
        "address": "36 Lindisfarne Road, Jesmond, Newcastle upon Tyne, NE2 3HT",
        "ward": "South Jesmond",
        "postcode": "NE2 3HT",
        "proposal": "Crown reduction by 3m and crown thin by 20% to 1no. Beech tree (T1)",
        "application_type": "Works to Trees",
        "constraints": ["Tree Preservation Order", "Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-10-05",
        "conditions": [
            "Works to be completed within 2 years",
            "Works to be carried out by qualified arborist",
            "Works to comply with BS3998"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposed works are appropriate tree management that will not harm the health or amenity value of the tree. The reduction is necessary to manage the tree's size relative to the property.",
        "key_policies_cited": ["DM28", "BS3998:2010"],
    },
]


# Broxtowe Borough Council Planning Decisions Database
BROXTOWE_HISTORIC_CASES: list[dict[str, Any]] = [
    # ===== NEWTHORPE / EASTWOOD AREA - RESIDENTIAL =====
    {
        "reference": "23/00456/FUL",
        "address": "Land Adjacent To 15 Church Street, Newthorpe, Nottinghamshire, NG16 2AA",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 2AA",
        "proposal": "Erection of detached dwelling with associated parking and landscaping",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-08-15",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Landscaping scheme to be approved",
            "Surface water drainage details to be approved",
            "Parking to be provided prior to occupation"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The site is suitable for residential development within the existing urban area. The proposed dwelling is of acceptable design that respects the character of the area. Adequate parking and amenity space is provided. The development would not harm neighbouring amenity.",
        "key_policies_cited": ["Policy 10", "Policy A", "LP1", "NPPF Chapter 12"],
    },
    {
        "reference": "22/00789/FUL",
        "address": "Plot 2, Beauvale Drive, Eastwood, Nottinghamshire, NG16 3GY",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3GY",
        "proposal": "Construction of 2 no. detached dwellings with garages",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2022-11-20",
        "conditions": [
            "Development to commence within 3 years",
            "Materials as specified in application",
            "Boundary treatments to be approved",
            "Electric vehicle charging points to be provided"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposal represents appropriate infill development within the urban area. The dwellings are of a scale and design that respects the existing street scene. Adequate separation distances are maintained to protect residential amenity.",
        "key_policies_cited": ["Policy 10", "Policy 8", "LP1", "NPPF Chapters 5 and 12"],
    },
    # ===== BEESTON / STAPLEFORD AREA =====
    {
        "reference": "23/00234/FUL",
        "address": "35 Station Road, Beeston, Nottinghamshire, NG9 2AL",
        "ward": "Beeston Central",
        "postcode": "NG9 2AL",
        "proposal": "Change of use from retail (Class E) to residential (Class C3) to create 3 no. flats",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-05-10",
        "conditions": [
            "Development to commence within 3 years",
            "Bin storage details to be approved",
            "Cycle storage to be provided",
            "Noise insulation to be installed"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The loss of the retail unit is acceptable given the availability of other retail premises in the town centre. The flats would provide needed housing in a sustainable town centre location and the amenity for future occupiers is acceptable.",
        "key_policies_cited": ["Policy 6", "LP10", "Policy 8", "NPPF Chapter 5"],
    },
    {
        "reference": "22/00567/HOU",
        "address": "48 Wollaton Road, Beeston, Nottinghamshire, NG9 2NR",
        "ward": "Beeston North",
        "postcode": "NG9 2NR",
        "proposal": "Two storey side and single storey rear extension",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2022-09-05",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling",
            "No windows in side elevation at first floor level"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extensions are subordinate to the host dwelling and of an acceptable design. The side extension maintains a gap to the boundary. No unacceptable harm to neighbouring amenity would result.",
        "key_policies_cited": ["Policy 10", "NPPF Chapter 12"],
    },
    # ===== KIMBERLEY AREA =====
    {
        "reference": "23/00123/FUL",
        "address": "Land At Greens Lane, Kimberley, Nottinghamshire, NG16 2PQ",
        "ward": "Kimberley",
        "postcode": "NG16 2PQ",
        "proposal": "Erection of 4 no. dwellings with associated access and landscaping",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-03-28",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Landscaping and boundary treatment details",
            "Construction management plan",
            "Surface water drainage scheme"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The site is allocated for housing in the Local Plan and the principle of residential development is acceptable. The layout and design of the dwellings is appropriate for the locality. Highway access is satisfactory.",
        "key_policies_cited": ["Policy 3", "Policy 10", "LP1", "LP17"],
    },
    # ===== REFUSED EXAMPLES =====
    {
        "reference": "23/00789/FUL",
        "address": "The Green, Awsworth, Nottinghamshire, NG16 2QR",
        "ward": "Awsworth, Cossall and Trowell",
        "postcode": "NG16 2QR",
        "proposal": "Erection of two storey dwelling in garden of existing property",
        "application_type": "Full Planning",
        "constraints": ["Green Belt"],
        "decision": "Refused",
        "decision_date": "2023-07-14",
        "conditions": [],
        "refusal_reasons": [
            "The proposal represents inappropriate development in the Green Belt contrary to NPPF paragraph 147.",
            "The development would harm the openness of the Green Belt.",
            "Very special circumstances have not been demonstrated to outweigh the harm."
        ],
        "case_officer_reasoning": "The site is within the Green Belt where new dwellings constitute inappropriate development. The applicant has not demonstrated very special circumstances that would clearly outweigh the harm to the Green Belt.",
        "key_policies_cited": ["Policy 8", "NPPF Chapter 13"],
    },
    # ===== ADDITIONAL NG16 AREA CASES (EASTWOOD / NEWTHORPE / KIMBERLEY) =====
    {
        "reference": "24/00112/FUL",
        "address": "42 Nottingham Road, Eastwood, Nottinghamshire, NG16 3NQ",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3NQ",
        "proposal": "Erection of single storey rear extension and conversion of garage to habitable room",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2024-03-15",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling",
            "No additional windows in side elevations"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The single storey rear extension and garage conversion are subordinate to the host dwelling and of an acceptable design. No harm to neighbouring amenity.",
        "key_policies_cited": ["Policy 10", "NPPF Chapter 12"],
    },
    {
        "reference": "23/00890/FUL",
        "address": "Land Off Coronation Road, Newthorpe, Nottinghamshire, NG16 2DL",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 2DL",
        "proposal": "Erection of 6 no. dwellings with associated access road, parking and landscaping",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-12-08",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Landscaping and boundary treatment scheme",
            "Surface water drainage scheme to be approved",
            "Construction management plan",
            "Electric vehicle charging points",
            "Biodiversity enhancement scheme"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The site is within the settlement boundary and suitable for residential development. The layout provides adequate garden sizes, parking and separation distances. The scale and density are appropriate for the locality.",
        "key_policies_cited": ["Policy 3", "Policy 10", "LP1", "LP17", "NPPF Chapters 5, 12"],
    },
    {
        "reference": "24/00234/FUL",
        "address": "Former Workshop, Engine Lane, Newthorpe, NG16 2AB",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 2AB",
        "proposal": "Demolition of existing workshop and erection of 3 no. terraced dwellings",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2024-05-20",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Contamination investigation and remediation",
            "Parking to be provided prior to occupation",
            "Boundary treatments to be approved"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The redevelopment of this brownfield site for housing is supported by NPPF paragraph 119. The terraced form is consistent with the prevailing character of the area. Adequate parking and amenity space is provided.",
        "key_policies_cited": ["Policy 10", "NPPF paras 119-120", "LP1", "BLP2-19"],
    },
    {
        "reference": "23/00567/HOU",
        "address": "18 Hardy Street, Kimberley, Nottinghamshire, NG16 2JR",
        "ward": "Kimberley",
        "postcode": "NG16 2JR",
        "proposal": "Two storey side extension and single storey rear extension",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-09-22",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling",
            "Obscure glazing to first floor side window"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extensions are subordinate to the host dwelling. The two storey side element is set back from the front building line and set down from the ridge to maintain the character of the streetscene. No unacceptable harm to neighbouring amenity.",
        "key_policies_cited": ["Policy 10", "NPPF Chapter 12"],
    },
    {
        "reference": "24/00345/FUL",
        "address": "Land Adjacent 22 Walker Street, Eastwood, NG16 3EN",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3EN",
        "proposal": "Erection of detached dwelling with associated parking",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Refused",
        "decision_date": "2024-04-18",
        "conditions": [],
        "refusal_reasons": [
            "The proposed dwelling by reason of its siting, scale and proximity to neighbouring properties would result in an unacceptable level of overlooking and overshadowing, harmful to the amenity of occupiers of adjacent properties, contrary to Policy 10 of the Broxtowe Part 2 Local Plan.",
            "Insufficient on-site parking provision would result in increased on-street parking to the detriment of highway safety, contrary to Policy LP17."
        ],
        "case_officer_reasoning": "While the principle of residential development on this infill plot is acceptable, the specific proposal results in unacceptable harm to residential amenity due to the narrow plot width and proximity to boundaries. The parking shortfall compounds the harm.",
        "key_policies_cited": ["Policy 10", "LP17", "NPPF Chapter 12"],
    },
    {
        "reference": "24/00456/HOU",
        "address": "7 Victoria Street, Eastwood, Nottinghamshire, NG16 3AW",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3AW",
        "proposal": "Erection of single storey rear extension and new boundary fence",
        "application_type": "Householder",
        "constraints": ["D.H. Lawrence Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2024-06-12",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling",
            "Fence to be timber with natural finish, max height 1.8m",
            "No PD rights for further extensions without approval"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The single storey rear extension is modest and subordinate. The timber fence is appropriate for the conservation area setting. The proposal preserves the character of the D.H. Lawrence Conservation Area.",
        "key_policies_cited": ["Policy 10", "ACS-11", "BLP2-23", "NPPF Chapter 16"],
    },
    {
        "reference": "23/00678/FUL",
        "address": "Site Of Former Pub, Main Street, Kimberley, NG16 2NG",
        "ward": "Kimberley",
        "postcode": "NG16 2NG",
        "proposal": "Demolition of former public house and erection of 8 no. apartments with parking",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-11-30",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Noise insulation scheme",
            "Bin and cycle storage details",
            "Landscaping scheme",
            "Surface water drainage"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The redevelopment of this brownfield site in the town centre for residential use is supported. The loss of the pub is acceptable as it has been vacant for over 2 years and marketed without interest. The apartment building is of acceptable scale and design for this town centre location.",
        "key_policies_cited": ["Policy 6", "Policy 10", "ACS-2", "NPPF Chapters 5, 12"],
    },
    {
        "reference": "24/00730/FUL",
        "address": "14 Dovecote Road, Eastwood, Nottinghamshire, NG16 3HZ",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3HZ",
        "proposal": "Change of use from office (Class E) to 2 no. residential flats (Class C3) with external alterations",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2024-08-20",
        "conditions": [
            "Development to commence within 3 years",
            "Bin storage details to be approved",
            "Cycle storage to be provided",
            "Sound insulation between units"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The change of use from office to residential is acceptable given the sufficient supply of office space in the area. The conversion provides needed housing in a sustainable location. The external alterations are minor and acceptable.",
        "key_policies_cited": ["Policy 6", "Policy 10", "NPPF Chapter 5"],
    },
    {
        "reference": "24/00189/FUL",
        "address": "Land Rear Of 56 Nottingham Road, Eastwood, NG16 3NP",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3NP",
        "proposal": "Erection of detached bungalow with associated parking and landscaping",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2024-02-28",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Landscaping scheme including tree planting",
            "Surface water drainage details",
            "Parking to be provided prior to occupation"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The bungalow is an appropriate form of development for this backland plot, being single storey and therefore minimising impact on surrounding properties. The site is within the settlement boundary and the principle of residential development is acceptable.",
        "key_policies_cited": ["Policy 3", "Policy 10", "LP1", "NPPF Chapters 5, 12"],
    },
    {
        "reference": "23/00345/HOU",
        "address": "29 Beauvale Drive, Eastwood, Nottinghamshire, NG16 3GY",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3GY",
        "proposal": "Loft conversion with rear dormer window and front rooflight",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-06-15",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing roof",
            "Obscure glazing to side-facing dormer cheeks"
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The rear dormer is of an acceptable size and design, set back from the eaves and below the ridge. The front rooflight is a conservation rooflight flush with the roof slope. No harm to the character of the area or neighbouring amenity.",
        "key_policies_cited": ["Policy 10", "NPPF Chapter 12"],
    },
    # ===== BRAMCOTE =====
    {
        "reference": "23/00890/HOU",
        "address": "42 Derby Road, Bramcote, Nottinghamshire, NG9 3GJ",
        "ward": "Bramcote",
        "postcode": "NG9 3GJ",
        "proposal": "Two storey side extension and single storey rear extension",
        "application_type": "Householder",
        "constraints": ["Bramcote Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-09-10",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling and complement Conservation Area character",
            "No additional windows in side elevations without consent",
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extension is subordinate to the main dwelling and uses matching materials. The design respects the spacious character of Bramcote Conservation Area with generous plot spacing maintained. No harm to neighbouring amenity with 21m separation distances achieved.",
        "key_policies_cited": ["Policy 10", "Policy 19", "Policy 26", "NPPF Chapter 16"],
    },
    {
        "reference": "24/00102/FUL",
        "address": "Land Adjacent 8 Bramcote Lane, Bramcote, Nottinghamshire, NG9 3DH",
        "ward": "Bramcote",
        "postcode": "NG9 3DH",
        "proposal": "Erection of detached dwelling with detached garage",
        "application_type": "Full Planning",
        "constraints": ["Bramcote Conservation Area"],
        "decision": "Refused",
        "decision_date": "2024-03-15",
        "conditions": [],
        "refusal_reasons": [
            "The proposed dwelling by reason of its siting, scale and design would fail to preserve or enhance the character and appearance of the Bramcote Conservation Area, which is characterised by large, spacious plots with mature landscaping. The subdivision of the plot would erode this spacious character contrary to Policy 26 (LP), Policy 11 (ACS) and NPPF Chapter 16.",
        ],
        "case_officer_reasoning": "Bramcote Conservation Area is characterised by large Victorian/Edwardian villas with generous gardens and mature trees. The subdivision of this plot to create an additional dwelling would erode the spacious character that defines this part of the Conservation Area. The harm to the Conservation Area is less than substantial (moderate) but is not outweighed by the limited public benefits of one additional dwelling.",
        "key_policies_cited": ["Policy 26", "Policy 11", "Policy 10", "NPPF Chapter 16"],
    },
    # ===== CHILWELL =====
    {
        "reference": "24/00201/HOU",
        "address": "15 High Road, Chilwell, Nottinghamshire, NG9 5BE",
        "ward": "Chilwell",
        "postcode": "NG9 5BE",
        "proposal": "Single storey rear extension with bi-fold doors",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2024-04-20",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing dwelling",
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposed single storey rear extension has a depth of 4m and eaves height of 2.8m. It passes the 45-degree daylight test for the neighbouring property. Materials will match the existing dwelling. The remaining garden area of 65sqm exceeds the 50sqm minimum. The development accords with Policies 17 and 19.",
        "key_policies_cited": ["Policy 17", "Policy 19", "NPPF Chapter 12"],
    },
    # ===== ATTENBOROUGH =====
    {
        "reference": "23/00567/FUL",
        "address": "The Old Vicarage, Church Lane, Attenborough, Nottinghamshire, NG9 6AB",
        "ward": "Attenborough and Chilwell East",
        "postcode": "NG9 6AB",
        "proposal": "Extension and alteration to Grade II listed building to create additional living space",
        "application_type": "Full Planning",
        "constraints": ["Attenborough Conservation Area", "Grade II Listed Building"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-11-28",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved (stone, timber windows, natural slate)",
            "Window details at 1:5 scale to be approved",
            "No removal of historic fabric without written consent",
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extension is sensitively designed as a subordinate addition to the listed building, using traditional materials (stone, natural slate, timber windows). The scheme has been amended during the application process to reduce the footprint and height. The less than substantial harm (low end) to the listed building is outweighed by the benefit of securing the long-term use and maintenance of this heritage asset.",
        "key_policies_cited": ["Policy 26", "Policy 11", "NPPF Chapter 16", "Section 66 LBCA 1990"],
    },
    # ===== AWSWORTH (GREEN BELT) =====
    {
        "reference": "24/00089/FUL",
        "address": "Field off Newtons Lane, Awsworth, Nottinghamshire, NG16 2RJ",
        "ward": "Awsworth, Cossall and Trowell",
        "postcode": "NG16 2RJ",
        "proposal": "Erection of detached dwelling",
        "application_type": "Full Planning",
        "constraints": ["Green Belt"],
        "decision": "Refused",
        "decision_date": "2024-02-10",
        "conditions": [],
        "refusal_reasons": [
            "The proposal constitutes inappropriate development in the Green Belt. No very special circumstances have been demonstrated that would clearly outweigh the harm to the Green Belt by reason of inappropriateness. The proposal is contrary to Policy 4 (LP), Policy 3 (ACS), and NPPF paragraphs 147-149.",
        ],
        "case_officer_reasoning": "The site lies within the Green Belt where the erection of new buildings is inappropriate development. The applicant has not demonstrated that the proposal falls within any of the exceptions in NPPF paragraph 149, nor have very special circumstances been demonstrated. The proposal would harm the openness of the Green Belt and conflict with its purposes.",
        "key_policies_cited": ["Policy 4", "Policy 3", "NPPF paragraphs 147-149"],
    },
    {
        "reference": "23/00445/HOU",
        "address": "Rose Cottage, Main Street, Awsworth, Nottinghamshire, NG16 2QN",
        "ward": "Awsworth, Cossall and Trowell",
        "postcode": "NG16 2QN",
        "proposal": "Single storey rear extension and replacement windows",
        "application_type": "Householder",
        "constraints": ["Green Belt"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-07-22",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to match existing",
            "Extension not to exceed dimensions shown on approved plans",
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposed single storey rear extension is proportionate to the original dwelling (less than 30% increase in floor area). It is not disproportionate to the original building and falls within the exception at NPPF paragraph 149(c). The openness of the Green Belt would be preserved as the extension is to the rear and not visible from public vantage points.",
        "key_policies_cited": ["Policy 4", "NPPF paragraph 149(c)"],
    },
    # ===== NUTHALL =====
    {
        "reference": "24/00330/FUL",
        "address": "Former Garage Site, Nottingham Road, Nuthall, Nottinghamshire, NG16 1DN",
        "ward": "Nuthall",
        "postcode": "NG16 1DN",
        "proposal": "Erection of 4 no. semi-detached dwellings with associated parking and landscaping",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2024-06-18",
        "conditions": [
            "Development to commence within 3 years",
            "Materials to be approved",
            "Landscaping scheme to be approved and implemented",
            "Contamination remediation strategy to be approved",
            "Electric vehicle charging points (1 per dwelling)",
            "Surface water drainage details to be approved",
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The site is previously developed land within the urban area. The proposal for 4 semi-detached dwellings is appropriate in scale and density for this location (38 dph). The design responds to the existing streetscape. Adequate parking (2 spaces per dwelling) and amenity space (55sqm per plot) is provided. Contamination can be dealt with by condition.",
        "key_policies_cited": ["Policy 15", "Policy 10", "Policy 17", "NPPF Chapters 5 and 12"],
    },
    # ===== TOTON =====
    {
        "reference": "23/00678/FUL",
        "address": "45 Stapleford Lane, Toton, Nottinghamshire, NG9 6GA",
        "ward": "Toton and Chilwell Meadows",
        "postcode": "NG9 6GA",
        "proposal": "Change of use from dwelling (C3) to children's day nursery (E) with external play area",
        "application_type": "Full Planning",
        "constraints": [],
        "decision": "Refused",
        "decision_date": "2023-12-04",
        "conditions": [],
        "refusal_reasons": [
            "The proposed change of use to a children's day nursery would generate unacceptable levels of noise and disturbance from the outdoor play area to the detriment of neighbouring residential amenity, contrary to Policy 17 of the Broxtowe Part 2 Local Plan (2019).",
            "The intensified use of the vehicular access and increased traffic movements associated with parent drop-off/pick-up would be detrimental to highway safety, contrary to Policy 21 of the Broxtowe Part 2 Local Plan (2019).",
        ],
        "case_officer_reasoning": "While there is demand for childcare provision, the site is in a residential area with narrow streets. The outdoor play area would be within 5m of neighbouring habitable room windows. The access is constrained and unsuitable for the level of traffic (40+ vehicle movements per day at peak times). The harm to amenity and highway safety outweighs the community benefit.",
        "key_policies_cited": ["Policy 17", "Policy 21", "NPPF paragraphs 110-112"],
    },
    # ===== LISTED BUILDING CONSENT =====
    {
        "reference": "24/00156/LBC",
        "address": "8a Victoria Street, Eastwood, Nottinghamshire, NG16 3AW",
        "ward": "Eastwood St Marys",
        "postcode": "NG16 3AW",
        "proposal": "Internal and external alterations to Grade II listed building including replacement windows and re-roofing",
        "application_type": "Listed Building Consent",
        "constraints": ["Eastwood Conservation Area", "Grade II Listed Building", "D.H. Lawrence Birthplace"],
        "decision": "Approved with Conditions",
        "decision_date": "2024-05-15",
        "conditions": [
            "Works to commence within 3 years",
            "Window details at 1:5 scale to be approved - timber sliding sash only",
            "Roof materials: natural Welsh slate to match existing",
            "Mortar specification to be agreed (lime mortar required)",
            "No historic fabric to be removed without prior written consent",
            "Recording condition prior to and during works",
        ],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposed works would restore the listed building using traditional materials and methods. The replacement of later uPVC windows with timber sliding sash windows of appropriate profile would enhance the building's significance. The re-roofing in natural Welsh slate would restore the original appearance. The works would result in enhancement of this nationally important heritage asset (D.H. Lawrence Birthplace).",
        "key_policies_cited": ["Policy 26", "Policy 11", "NPPF Chapter 16", "Section 66 LBCA 1990"],
    },
    # ===== BEESTON TOWN CENTRE - COMMERCIAL =====
    {
        "reference": "24/00278/FUL",
        "address": "Unit 3, The Square, Beeston, Nottinghamshire, NG9 2JG",
        "ward": "Beeston Central",
        "postcode": "NG9 2JG",
        "proposal": "Change of use from retail (Class E) to hot food takeaway (Sui Generis) with extraction flue",
        "application_type": "Full Planning",
        "constraints": ["Beeston Town Centre"],
        "decision": "Refused",
        "decision_date": "2024-07-03",
        "conditions": [],
        "refusal_reasons": [
            "The proposed change of use would result in a concentration of hot food takeaway uses within Beeston Town Centre that would harm the vitality and viability of the town centre contrary to Policy 10 (LP).",
            "The extraction flue on the rear elevation would harm the visual amenity of the area contrary to Policy 17 (LP) and Policy 10 (ACS).",
        ],
        "case_officer_reasoning": "There are already 4 hot food takeaway units within 100m of the application site. A further unit would result in an over-concentration of Class A5/Sui Generis uses detrimental to the vitality and diversity of Beeston Town Centre. The proposed extraction flue would be visible from the public realm and would detract from the visual amenity of The Square.",
        "key_policies_cited": ["Policy 10", "Policy 17", "NPPF paragraphs 86-90"],
    },
]


# Combined database for all councils
ALL_HISTORIC_CASES = {
    "newcastle": NEWCASTLE_HISTORIC_CASES,
    "broxtowe": BROXTOWE_HISTORIC_CASES,
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two lat/lng points in kilometres."""
    import math
    R = 6371.0  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_similarity_score(
    case: dict[str, Any],
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str | None,
    postcode: str | None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> float:
    """
    Calculate similarity score between a historic case and current application.

    Location-FIRST weighting with deeper feature-level matching:

    Weights:
    - Location proximity: 30%  (primary factor — coordinate distance + postcode)
    - Development type & scale: 25%  (dwelling type, storeys, form)
    - Proposal feature similarity: 25%  (detailed keyword + context matching)
    - Constraint overlap: 20%  (conservation, listed, Green Belt, TPO)
    """
    score = 0.0

    # 1. Location proximity (30%) — PRIMARY FACTOR
    # Prefer coordinate-based distance when available; fall back to postcode tiers.
    location_score = 0.0

    case_lat = case.get("latitude")
    case_lng = case.get("longitude")
    if latitude and longitude and case_lat and case_lng:
        distance_km = _haversine_km(latitude, longitude, case_lat, case_lng)
        # Distance decay: 1.0 at 0km, ~0.5 at 5km, 0 at 15km+
        location_score = max(0.0, 1.0 - (distance_km / 15.0))
        # Boost very close matches
        if distance_km < 1.0:
            location_score = max(location_score, 0.95)
        elif distance_km < 3.0:
            location_score = max(location_score, 0.80)

    if postcode and case["postcode"] and location_score < 0.5:
        # Use postcode tiers as fallback (or supplement if distance is weak)
        pc_score = 0.0
        case_pc = case["postcode"].strip().upper().replace(" ", "")
        current_pc = postcode.strip().upper().replace(" ", "")

        # Full postcode match (same street area)
        if case_pc == current_pc:
            pc_score = 1.0
        else:
            # Extract components for tiered matching
            case_parts = case["postcode"].strip().split()
            current_parts = postcode.strip().split()
            case_outcode = case_parts[0] if case_parts else ""
            current_outcode = current_parts[0] if current_parts else ""

            # Postcode sector match (e.g. "NG16 2" == "NG16 2")
            case_sector = f"{case_parts[0]} {case_parts[1][0]}" if len(case_parts) == 2 and len(case_parts[1]) >= 1 else case_outcode
            current_sector = f"{current_parts[0]} {current_parts[1][0]}" if len(current_parts) == 2 and len(current_parts[1]) >= 1 else current_outcode

            if case_sector == current_sector:
                # Same sector but check for development context mismatch
                # In Broxtowe, NG16 spans urban (Eastwood/Kimberley) and
                # semi-rural/Green Belt (Awsworth/Giltbrook). Demote matches
                # where one is Green Belt and the other isn't.
                case_gb = any("green belt" in c.lower() for c in case.get("constraints", []))
                current_gb = any("green belt" in c.lower() for c in constraints)
                if case_gb != current_gb:
                    pc_score = 0.4  # Penalise: same postcode but different context
                else:
                    pc_score = 0.85  # Same sector, same context = very close
            elif case_outcode == current_outcode:
                pc_score = 0.65  # Same district (e.g. NG16)
            else:
                # Check if same broader area (e.g. NG vs NE)
                case_area = re.match(r'^([A-Z]+)', case_outcode)
                current_area = re.match(r'^([A-Z]+)', current_outcode)
                if case_area and current_area and case_area.group(1) == current_area.group(1):
                    pc_score = 0.3  # Same city/region

        # Take the best of coordinate score and postcode score
        location_score = max(location_score, pc_score)

    # Ward match bonus
    if ward and case.get("ward") and case["ward"].lower() == ward.lower():
        location_score = max(location_score, 0.8)
        location_score = min(1.0, location_score + 0.15)

    score += location_score * 0.30

    # 2. Development type & scale match (25%)
    type_scale_score = 0.0
    proposal_lower = proposal.lower()
    case_proposal_lower = case["proposal"].lower()

    # Application type match (base)
    if case["application_type"].lower() == application_type.lower():
        type_scale_score += 0.4
    elif _similar_app_type(case["application_type"], application_type):
        type_scale_score += 0.25

    # Development type match (dwelling, extension, change of use etc.)
    current_dev = _detect_dev_type_from_proposal(proposal)
    case_dev = _detect_dev_type_from_proposal(case["proposal"])
    if current_dev == case_dev:
        type_scale_score += 0.3
    elif current_dev in {"new_dwelling", "extension"} and case_dev in {"new_dwelling", "extension"}:
        type_scale_score += 0.1  # Related but not same

    # Scale match (storey count)
    current_storeys = _extract_storeys(proposal_lower)
    case_storeys = _extract_storeys(case_proposal_lower)
    if current_storeys and case_storeys:
        if current_storeys == case_storeys:
            type_scale_score += 0.2
        elif abs(current_storeys - case_storeys) == 1:
            type_scale_score += 0.1

    # Form match (detached, semi, terrace)
    current_form = _extract_dwelling_form(proposal_lower)
    case_form = _extract_dwelling_form(case_proposal_lower)
    if current_form and case_form and current_form == case_form:
        type_scale_score += 0.1

    score += min(type_scale_score, 1.0) * 0.25

    # 3. Proposal feature similarity (25%) — deeper keyword matching
    feature_score = _calculate_feature_similarity(proposal_lower, case_proposal_lower)
    score += feature_score * 0.25

    # 4. Constraint overlap (20%)
    case_constraints = set(c.lower() for c in case["constraints"])
    current_constraints = set(c.lower() for c in constraints)

    if case_constraints or current_constraints:
        constraint_overlap = len(case_constraints & current_constraints)
        constraint_total = len(case_constraints | current_constraints)
        constraint_score = (constraint_overlap / constraint_total) if constraint_total > 0 else 0
        # Bonus for sharing high-impact constraints
        high_impact = {"conservation area", "listed building", "green belt", "article 4 direction"}
        shared_high = (case_constraints & current_constraints) & high_impact
        if shared_high:
            constraint_score = min(1.0, constraint_score + 0.2 * len(shared_high))
    else:
        constraint_score = 0.5 if not case_constraints and not current_constraints else 0

    score += constraint_score * 0.20

    return min(score, 1.0)


def _extract_storeys(proposal_lower: str) -> int | None:
    """Extract number of storeys from proposal text."""
    m = re.search(r'(\d+)[\s\-]*(?:storey|story)', proposal_lower)
    if m:
        return int(m.group(1))
    if 'single storey' in proposal_lower or 'single-storey' in proposal_lower:
        return 1
    if 'two storey' in proposal_lower or 'two-storey' in proposal_lower:
        return 2
    if 'three storey' in proposal_lower or 'three-storey' in proposal_lower:
        return 3
    return None


def _extract_dwelling_form(proposal_lower: str) -> str | None:
    """Extract dwelling form (detached, semi, terraced)."""
    if 'detached' in proposal_lower and 'semi' not in proposal_lower:
        return 'detached'
    if 'semi-detached' in proposal_lower or 'semi detached' in proposal_lower:
        return 'semi-detached'
    if 'terrace' in proposal_lower or 'town house' in proposal_lower:
        return 'terraced'
    if 'bungalow' in proposal_lower:
        return 'bungalow'
    return None


def _calculate_feature_similarity(proposal_lower: str, case_lower: str) -> float:
    """Calculate detailed feature-level similarity between two proposals.

    Uses weighted feature categories rather than flat Jaccard, so that
    matching on substantive features (parking, access, materials) scores
    higher than matching on common filler words.
    """
    # Feature categories with weights
    feature_groups = {
        'access_parking': {
            'terms': {'parking', 'garage', 'access', 'driveway', 'vehicular',
                      'car port', 'carport', 'hardstanding'},
            'weight': 1.5,
        },
        'form_type': {
            'terms': {'dwelling', 'house', 'bungalow', 'flat', 'apartment',
                      'extension', 'annexe', 'outbuilding', 'conversion'},
            'weight': 1.5,
        },
        'scale': {
            'terms': {'single', 'two', 'three', 'storey', 'dormer', 'loft',
                      'basement', 'attic', 'roof'},
            'weight': 1.2,
        },
        'position': {
            'terms': {'rear', 'side', 'front', 'infill', 'garden', 'plot',
                      'land adjacent', 'land to'},
            'weight': 1.0,
        },
        'materials': {
            'terms': {'brick', 'render', 'stone', 'timber', 'slate', 'tile',
                      'cladding', 'upvc'},
            'weight': 0.8,
        },
        'sustainability': {
            'terms': {'solar', 'heat pump', 'ashp', 'ev', 'charging',
                      'renewable', 'insulation'},
            'weight': 1.0,
        },
        'landscape': {
            'terms': {'landscaping', 'boundary', 'fence', 'wall', 'tree',
                      'hedge', 'garden'},
            'weight': 0.7,
        },
        'heritage': {
            'terms': {'listed', 'conservation', 'heritage', 'character',
                      'historic', 'replacement'},
            'weight': 1.3,
        },
    }

    total_weight = 0.0
    matched_weight = 0.0

    for _group_name, group in feature_groups.items():
        terms = group['terms']
        weight = group['weight']
        proposal_hits = {t for t in terms if t in proposal_lower}
        case_hits = {t for t in terms if t in case_lower}

        if proposal_hits or case_hits:
            union = proposal_hits | case_hits
            intersection = proposal_hits & case_hits
            group_score = len(intersection) / len(union) if union else 0
            total_weight += weight
            matched_weight += group_score * weight

    return matched_weight / total_weight if total_weight > 0 else 0.3


def _similar_app_type(type1: str, type2: str) -> bool:
    """Check if two application types are similar."""
    type1_lower = type1.lower()
    type2_lower = type2.lower()

    householder_types = {'householder', 'det', 'domestic'}
    full_types = {'full planning', 'full', 'ful'}
    listed_types = {'listed building consent', 'listed building', 'lbc'}

    for type_group in [householder_types, full_types, listed_types]:
        if any(t in type1_lower for t in type_group) and any(t in type2_lower for t in type_group):
            return True

    return False


def generate_relevance_reason(
    case: dict[str, Any],
    proposal: str,
    constraints: list[str],
) -> str:
    """Generate detailed explanation of why this case is relevant.

    Compares specific features: development type, scale, position,
    constraints, and access arrangements to build a multi-factor
    relevance statement.
    """
    reasons = []

    proposal_lower = proposal.lower()
    case_lower = case["proposal"].lower()

    # Development type match
    for dev_type, label in [
        ("dwelling", "new dwelling"),
        ("extension", "extension"),
        ("conversion", "conversion"),
        ("change of use", "change of use"),
        ("flat", "flatted development"),
        ("bungalow", "bungalow"),
        ("demolition", "demolition and rebuild"),
    ]:
        if dev_type in proposal_lower and dev_type in case_lower:
            reasons.append(f"both involve {label}")
            break

    # Scale match
    current_storeys = _extract_storeys(proposal_lower)
    case_storeys = _extract_storeys(case_lower)
    if current_storeys and case_storeys and current_storeys == case_storeys:
        reasons.append(f"both {current_storeys}-storey")

    # Form match
    current_form = _extract_dwelling_form(proposal_lower)
    case_form = _extract_dwelling_form(case_lower)
    if current_form and case_form and current_form == case_form:
        reasons.append(f"both {current_form}")

    # Position match
    for pos in ["rear", "side", "front", "infill", "garden land"]:
        if pos in proposal_lower and pos in case_lower:
            reasons.append(f"both in {pos} position")
            break

    # Access/parking match
    if any(kw in proposal_lower for kw in ["parking", "access", "driveway"]):
        if any(kw in case_lower for kw in ["parking", "access", "driveway"]):
            reasons.append("similar parking/access arrangements")

    # Constraint match (specific)
    case_constraints = set(c.lower() for c in case["constraints"])
    current_constraints = set(c.lower() for c in constraints)
    shared = case_constraints & current_constraints
    for constraint in list(shared)[:2]:
        if 'conservation' in constraint:
            reasons.append("same Conservation Area context")
        elif 'listed' in constraint:
            reasons.append("Listed Building considerations apply")
        elif 'green belt' in constraint:
            reasons.append("both in Green Belt")
        elif 'article 4' in constraint:
            reasons.append("Article 4 Direction applies")
        elif 'tpo' in constraint or 'tree' in constraint:
            reasons.append("TPO constraints")
        else:
            reasons.append(f"shared constraint: {constraint}")

    if not reasons:
        reasons.append("similar application type and location")

    return "; ".join(reasons[:4])


def _detect_dev_type_from_proposal(proposal: str) -> str:
    """Detect the broad development type from a proposal string."""
    p = proposal.lower()
    if any(kw in p for kw in ["dwelling", "house", "bungalow", "erection of"]):
        return "new_dwelling"
    elif "extension" in p or "alteration" in p:
        return "extension"
    elif "change of use" in p or "conversion" in p:
        return "change_of_use"
    elif any(kw in p for kw in ["flat", "apartment"]):
        return "flats"
    elif "demolition" in p:
        return "demolition"
    else:
        return "other"


def _is_comparable(
    case: dict,
    proposal: str,
    application_type: str,
    constraints: list[str],
) -> tuple[bool, str]:
    """Check if a case is genuinely comparable. Returns (is_comparable, reason).

    Exclusion rules:
    1. Development type mismatch (extension vs new dwelling) - exclude
    2. Completely different constraint context (Green Belt vs none) - exclude
    3. Different use class (retail vs residential) - exclude
    """
    current_dev_type = _detect_dev_type_from_proposal(proposal)
    case_dev_type = _detect_dev_type_from_proposal(case["proposal"])

    # Rule 1: Development type must broadly match
    if current_dev_type != case_dev_type:
        # Allow extension/new_dwelling only if both are residential
        residential_types = {"new_dwelling", "extension", "flats"}
        if not (current_dev_type in residential_types and case_dev_type in residential_types):
            return False, f"Not comparable: development type mismatch ({current_dev_type} vs {case_dev_type})"

    # Rule 2: Green Belt mismatch is a hard exclusion
    current_gb = any("green belt" in c.lower() for c in constraints)
    case_gb = any("green belt" in c.lower() for c in case["constraints"])
    if current_gb != case_gb:
        return False, "Not comparable: Green Belt context mismatch"

    # Rule 3: Use class mismatch
    current_proposal_lower = proposal.lower()
    case_proposal_lower = case["proposal"].lower()
    residential_kws = ["dwelling", "house", "flat", "apartment", "residential", "extension", "bungalow"]
    commercial_kws = ["retail", "shop", "office", "industrial", "warehouse", "commercial"]

    current_is_resi = any(kw in current_proposal_lower for kw in residential_kws)
    case_is_resi = any(kw in case_proposal_lower for kw in residential_kws)
    current_is_comm = any(kw in current_proposal_lower for kw in commercial_kws)
    case_is_comm = any(kw in case_proposal_lower for kw in commercial_kws)

    if current_is_resi and case_is_comm:
        return False, "Not comparable: residential vs commercial use class"
    if current_is_comm and case_is_resi:
        return False, "Not comparable: commercial vs residential use class"

    return True, ""


def find_similar_cases(
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str | None = None,
    postcode: str | None = None,
    limit: int = 5,
    council_id: str = "newcastle",
    site_address: str = "",
    reference: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> list[HistoricCase]:
    """
    Find the most similar historic cases to the current application.

    Selection rules (location-led, development-type matched):
    1. Same council/settlement area (location is primary factor at 40%)
    2. Same development type (new dwelling, extension, change of use)
    3. Similar constraint context
    4. Score > 0.35 threshold (lowered from 0.4 for location-first matching)

    Exclusions applied:
    - Development type mismatch (extension vs new dwelling)
    - Green Belt context mismatch
    - Use class mismatch (residential vs commercial)

    When a ``reference`` is provided, learned ranking adjustments from
    the feedback loop are applied to boost/demote cases based on
    historical accuracy.

    Returns at most `limit` cases, preferring tight relevant matches
    over a long list of weak ones.
    """
    # Detect council from address if provided
    if site_address:
        from .local_plans_complete import detect_council_from_address
        detected = detect_council_from_address(site_address, postcode)
        if detected:
            council_id = detected

    # Get council-specific cases (static dataset)
    cases_db = list(ALL_HISTORIC_CASES.get(council_id, NEWCASTLE_HISTORIC_CASES))

    # ---- Augment with applications stored in the DB ----
    # Applications that have been processed and received a decision
    # become available as precedent for future applications.
    try:
        from plana.storage.database import get_database as _get_db
        import json as _json
        _db = _get_db()
        _stored_apps = _db.get_completed_applications(council_id)
        _existing_refs = {c["reference"] for c in cases_db}
        for _app in _stored_apps:
            if _app.reference in _existing_refs or _app.reference == reference:
                continue  # skip duplicates and self
            if not _app.decision or not _app.proposal:
                continue
            try:
                _constraints = _json.loads(_app.constraints_json) if _app.constraints_json else []
            except (ValueError, TypeError):
                _constraints = []
            cases_db.append({
                "reference": _app.reference,
                "address": _app.address or "",
                "ward": _app.ward or "",
                "postcode": _app.postcode or "",
                "proposal": _app.proposal or "",
                "application_type": _app.application_type or "",
                "constraints": _constraints,
                "decision": _app.decision,
                "decision_date": _app.decision_date or "",
                "conditions": [],
                "refusal_reasons": [],
                "case_officer_reasoning": "",
                "key_policies_cited": [],
                "development_type": "",
                "num_storeys": 0,
                "dwelling_form": "",
            })
    except Exception:
        pass  # Non-fatal: fall back to static cases only

    scored_cases = []
    excluded_cases = []  # Track why cases were excluded

    for case in cases_db:
        # First: apply hard exclusion rules
        is_comparable, exclusion_reason = _is_comparable(
            case, proposal, application_type, constraints
        )
        if not is_comparable:
            excluded_cases.append((case["reference"], exclusion_reason))
            continue

        score = calculate_similarity_score(
            case=case,
            proposal=proposal,
            application_type=application_type,
            constraints=constraints,
            ward=ward,
            postcode=postcode,
            latitude=latitude,
            longitude=longitude,
        )

        if score > 0.35:  # Slightly lower threshold for location-first matching
            relevance_reason = generate_relevance_reason(case, proposal, constraints)

            historic_case = HistoricCase(
                reference=case["reference"],
                address=case["address"],
                ward=case["ward"],
                postcode=case["postcode"],
                proposal=case["proposal"],
                application_type=case["application_type"],
                constraints=case["constraints"],
                decision=case["decision"],
                decision_date=case["decision_date"],
                conditions=case["conditions"],
                refusal_reasons=case["refusal_reasons"],
                case_officer_reasoning=case["case_officer_reasoning"],
                key_policies_cited=case["key_policies_cited"],
                similarity_score=score,
                relevance_reason=relevance_reason,
            )
            scored_cases.append(historic_case)

    # ---- Apply learned ranking adjustments from feedback loop ----
    # Cases that have been cited in correct predictions get boosted;
    # cases cited in mismatches get demoted.
    if reference and scored_cases:
        try:
            from plana.improvement.reranking import calculate_similar_case_boost
            boosted = calculate_similar_case_boost(scored_cases, reference)
            # Re-apply boosts to similarity scores
            for case, boost in boosted:
                case.similarity_score = min(1.0, case.similarity_score * boost)
            scored_cases = [case for case, _ in boosted]
        except Exception:
            pass  # Non-fatal: fall back to base scores

    # Also apply learning system adjustments
    try:
        from plana.api.learning import get_learning_system
        ls = get_learning_system()
        case_adjustments = ls.get_similar_case_ranking_adjustments()
        if case_adjustments:
            for case in scored_cases:
                adj = case_adjustments.get(case.reference, 1.0)
                case.similarity_score = min(1.0, case.similarity_score * adj)
    except Exception:
        pass  # Non-fatal

    # ---- Apply temporal decay ----
    # Recent cases are more relevant because they reflect current policy
    # interpretation. Cases older than 3 years get progressively demoted.
    try:
        from datetime import datetime as _dt
        _now = _dt.now()
        for case in scored_cases:
            if case.decision_date:
                try:
                    case_date = _dt.strptime(case.decision_date, "%Y-%m-%d")
                    age_years = (_now - case_date).days / 365.25
                    if age_years <= 2:
                        decay = 1.0  # Fresh — full weight
                    elif age_years <= 4:
                        decay = 0.95  # Slight decay
                    elif age_years <= 6:
                        decay = 0.85  # Moderate decay
                    else:
                        decay = 0.75  # Older but still relevant precedent
                    case.similarity_score *= decay
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass  # Non-fatal

    # Sort by score descending
    scored_cases.sort(key=lambda x: x.similarity_score, reverse=True)

    # Prefer tight, highly relevant matches (max 3-5)
    return scored_cases[:limit]


def get_precedent_analysis(
    similar_cases: list[HistoricCase],
    proposal: str = "",
    constraints: list[str] | None = None,
    ward: str = "",
) -> dict[str, Any]:
    """
    Analyse patterns in similar cases to inform recommendation.

    Uses weighted approval rate (higher-similarity cases count more)
    and calibrated thresholds for realistic precedent strength assessment.
    Includes coverage gap analysis explaining what aspects lack precedent.
    """
    constraints = constraints or []

    if not similar_cases:
        # FIX 8: Generate gap analysis even when no cases found
        gaps = _analyse_coverage_gaps([], proposal, constraints, ward)
        return {
            "approval_rate": None,
            "common_conditions": [],
            "common_refusal_reasons": [],
            "key_policies": [],
            "precedent_strength": "limited",
            "summary": "No comparable cases identified. Decision must rest on policy compliance alone.",
            "total_cases": 0,
            "approved_count": 0,
            "refused_count": 0,
            "coverage_gaps": gaps,
        }

    approved = [c for c in similar_cases if 'approved' in c.decision.lower()]
    refused = [c for c in similar_cases if c.decision.lower() == 'refused']
    total = len(similar_cases)

    # Weighted approval rate — high-similarity cases carry more weight
    weighted_approved = sum(c.similarity_score for c in approved)
    weighted_total = sum(c.similarity_score for c in similar_cases)
    approval_rate = weighted_approved / weighted_total if weighted_total > 0 else 0

    avg_similarity = sum(c.similarity_score for c in similar_cases) / total

    # Collect common conditions
    all_conditions = []
    for case in approved:
        all_conditions.extend(case.conditions)

    # Collect refusal reasons
    all_refusal_reasons = []
    for case in refused:
        all_refusal_reasons.extend(case.refusal_reasons)

    # Collect policies
    all_policies = []
    for case in similar_cases:
        all_policies.extend(case.key_policies_cited)

    from collections import Counter
    condition_counts = Counter(all_conditions)
    policy_counts = Counter(all_policies)

    # Determine precedent strength — realistic thresholds
    if total >= 3 and approval_rate >= 0.8 and avg_similarity >= 0.55:
        precedent_strength = "strong_approve"
    elif total >= 2 and approval_rate >= 0.7:
        precedent_strength = "supportive"
    elif total >= 2 and approval_rate <= 0.3:
        precedent_strength = "strong_refuse"
    elif total >= 2:
        precedent_strength = "mixed"
    elif total == 1:
        precedent_strength = "limited"
    else:
        precedent_strength = "limited"

    # Generate nuanced summary
    if precedent_strength == "strong_approve":
        summary = (
            f"Strong precedent support: {len(approved)}/{total} comparable applications "
            f"approved (weighted rate {approval_rate:.0%}, avg similarity {avg_similarity:.0%}). "
            f"Pattern of approvals supports principle of development in this location."
        )
    elif precedent_strength == "supportive":
        summary = (
            f"Supportive precedent: {len(approved)}/{total} comparable applications approved "
            f"(weighted rate {approval_rate:.0%}). Principle of development appears established."
        )
    elif precedent_strength == "strong_refuse":
        summary = (
            f"Adverse precedent: {len(refused)}/{total} comparable applications refused "
            f"(weighted rate {approval_rate:.0%}). "
            f"Proposal must demonstrate how refusal grounds are addressed."
        )
    elif precedent_strength == "mixed":
        summary = (
            f"Mixed precedent: {len(approved)} approved, {len(refused)} refused "
            f"out of {total} cases. Decision turns on site-specific merits and "
            f"design quality rather than principle."
        )
    else:
        case = similar_cases[0]
        summary = (
            f"Limited precedent: {total} comparable case(s) found "
            f"({case.similarity_score:.0%} similarity). "
            f"Insufficient sample for pattern analysis."
        )

    # FIX 8: Coverage gap analysis
    gaps = _analyse_coverage_gaps(similar_cases, proposal, constraints, ward)
    if gaps and precedent_strength == "limited":
        summary += " " + " ".join(gaps)

    return {
        "approval_rate": approval_rate,
        "total_cases": total,
        "approved_count": len(approved),
        "refused_count": len(refused),
        "common_conditions": [c for c, _ in condition_counts.most_common(5)],
        "common_refusal_reasons": all_refusal_reasons[:3],
        "key_policies": [p for p, _ in policy_counts.most_common(8)],
        "precedent_strength": precedent_strength,
        "summary": summary,
        "avg_similarity": avg_similarity,
        "coverage_gaps": gaps,
    }


def _analyse_coverage_gaps(
    similar_cases: list[HistoricCase],
    proposal: str = "",
    constraints: list[str] | None = None,
    ward: str = "",
) -> list[str]:
    """
    Identify which aspects of the application lack precedent coverage.

    Returns a list of human-readable gap descriptions explaining WHY
    precedent is limited, rather than just saying 'limited precedent'.
    """
    gaps = []
    constraints = constraints or []
    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]
    case_constraints_all = []
    case_wards = set()
    case_types = set()

    for c in similar_cases:
        case_constraints_all.extend([cc.lower() for cc in c.constraints])
        if c.ward:
            case_wards.add(c.ward.lower())
        if c.application_type:
            case_types.add(c.application_type.lower())

    # Check heritage coverage
    has_heritage = any('listed' in c or 'conservation' in c for c in constraints_lower)
    cases_have_heritage = any('listed' in c or 'conservation' in c for c in case_constraints_all)
    if has_heritage and not cases_have_heritage:
        gaps.append("No heritage-context cases found in the matched set; heritage impact assessment relies on policy compliance alone.")

    # Check Green Belt coverage
    has_gb = any('green belt' in c for c in constraints_lower)
    cases_have_gb = any('green belt' in c for c in case_constraints_all)
    if has_gb and not cases_have_gb:
        gaps.append("No Green Belt cases found; very special circumstances assessment has no local precedent.")

    # Check ward coverage
    if ward and ward.lower() not in case_wards:
        gaps.append(f"No cases from {ward} ward found; precedent drawn from other areas of the borough.")

    # Check development type coverage
    is_change_of_use = 'change of use' in proposal_lower
    is_new_dwelling = any(kw in proposal_lower for kw in ['dwelling', 'new house', 'bungalow', 'erection of'])
    is_listed_building_consent = 'lbc' in proposal_lower or 'listed building consent' in proposal_lower

    if is_change_of_use and not any('change of use' in ct or 'cou' in ct for ct in case_types):
        gaps.append("No change of use cases found; precedent for use class acceptability is limited.")
    if is_listed_building_consent and not any('lbc' in ct for ct in case_types):
        gaps.append("No Listed Building Consent cases found; heritage precedent may be from planning permissions only.")
    if is_new_dwelling and not any('ful' in ct for ct in case_types):
        gaps.append("No full planning applications for new dwellings found in matched cases.")

    # Check flood risk coverage
    has_flood = any('flood' in c for c in constraints_lower)
    cases_have_flood = any('flood' in c for c in case_constraints_all)
    if has_flood and not cases_have_flood:
        gaps.append("No cases with flood risk constraints found; sequential/exception test has no local precedent.")

    return gaps
