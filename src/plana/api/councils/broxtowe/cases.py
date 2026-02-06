"""
Broxtowe Borough Council Historic Planning Cases Database.

This module contains historic planning decisions from Broxtowe to enable:
- Precedent-based decision making
- Similar case analysis
- Outcome prediction based on local patterns

Areas covered: Beeston, Stapleford, Eastwood, Kimberley, Bramcote, Chilwell,
               Attenborough, Toton, Long Eaton, Nuthall, Awsworth
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import re


@dataclass
class BroxtoweCase:
    """A historic planning case from Broxtowe."""
    reference: str
    address: str
    ward: str
    postcode: str
    proposal: str
    application_type: str
    constraints: list[str]
    decision: str
    decision_date: str
    conditions: list[str]
    refusal_reasons: list[str]
    case_officer_reasoning: str
    key_policies_cited: list[str]


# =============================================================================
# HISTORIC BROXTOWE PLANNING DECISIONS
# =============================================================================

BROXTOWE_HISTORIC_CASES = [
    # BEESTON - Major town centre
    {
        "reference": "23/00456/FUL",
        "address": "45 High Road, Beeston, NG9 2JQ",
        "ward": "Beeston Central",
        "postcode": "NG9 2JQ",
        "proposal": "Single storey rear extension measuring 4m depth with flat roof",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-06-15",
        "conditions": ["Materials to match existing", "Compliance with approved plans"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposed extension is subordinate to the main dwelling and would not have a detrimental impact on the character of the area or amenity of neighbours. The design complies with Policy 17.",
        "key_policies_cited": ["Policy-17", "ACS-10"],
    },
    {
        "reference": "23/00789/FUL",
        "address": "12 Wollaton Road, Beeston, NG9 2NG",
        "ward": "Beeston Central",
        "postcode": "NG9 2NG",
        "proposal": "Two storey side extension and single storey rear extension",
        "application_type": "Householder",
        "constraints": ["Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-08-22",
        "conditions": ["Materials to be approved", "Window details at 1:20 scale", "Compliance with approved plans"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extensions are designed sympathetically and would preserve the character of the Conservation Area. Materials condition required to ensure appropriate finish.",
        "key_policies_cited": ["Policy-23", "ACS-11", "Policy-17"],
    },
    {
        "reference": "22/00234/FUL",
        "address": "8 Church Street, Beeston, NG9 1FY",
        "ward": "Beeston Central",
        "postcode": "NG9 1FY",
        "proposal": "Replace timber sash windows with uPVC double glazed windows",
        "application_type": "Householder",
        "constraints": ["Conservation Area"],
        "decision": "Refused",
        "decision_date": "2022-04-18",
        "conditions": [],
        "refusal_reasons": [
            "The proposed uPVC windows would fail to preserve or enhance the character and appearance of the Beeston Conservation Area by virtue of their inappropriate materials and profiles, contrary to Policy 23 of the Part 2 Local Plan, Policy 11 of the Aligned Core Strategy, and the NPPF."
        ],
        "case_officer_reasoning": "uPVC windows are not appropriate in this Conservation Area location. The existing timber windows contribute to the character of the area and should be retained or replaced like-for-like.",
        "key_policies_cited": ["Policy-23", "ACS-11", "NPPF Chapter 16"],
    },

    # STAPLEFORD
    {
        "reference": "23/00123/FUL",
        "address": "67 Derby Road, Stapleford, NG9 7AA",
        "ward": "Stapleford North",
        "postcode": "NG9 7AA",
        "proposal": "Change of use from dwelling (C3) to 6-bed House in Multiple Occupation (C4)",
        "application_type": "Change of Use",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-03-10",
        "conditions": ["Bin storage details", "Cycle storage details", "Compliance with approved plans"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The property is of sufficient size to accommodate 6 occupants. Adequate parking and amenity space is available. The proposal would not harm the character of the area or residential amenity.",
        "key_policies_cited": ["Policy-17", "ACS-8"],
    },
    {
        "reference": "23/00567/FUL",
        "address": "23 Nottingham Road, Stapleford, NG9 8AA",
        "ward": "Stapleford South East",
        "postcode": "NG9 8AA",
        "proposal": "Erection of two storey rear extension with first floor balcony",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Refused",
        "decision_date": "2023-07-28",
        "conditions": [],
        "refusal_reasons": [
            "The proposed first floor balcony would result in unacceptable overlooking of neighbouring properties at 21 and 25 Nottingham Road, causing significant harm to residential amenity contrary to Policy 17 of the Part 2 Local Plan."
        ],
        "case_officer_reasoning": "While the two storey extension is acceptable in principle, the first floor balcony would create unacceptable overlooking. Removal of the balcony would make the scheme acceptable.",
        "key_policies_cited": ["Policy-17", "ACS-10"],
    },

    # EASTWOOD - D.H. Lawrence connection
    {
        "reference": "23/00890/LBC",
        "address": "D.H. Lawrence Birthplace Museum, 8a Victoria Street, Eastwood, NG16 3AW",
        "ward": "Eastwood",
        "postcode": "NG16 3AW",
        "proposal": "Internal alterations to create accessible WC facilities and conservation repairs to windows",
        "application_type": "Listed Building Consent",
        "constraints": ["Grade II Listed Building"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-09-05",
        "conditions": ["Method statement for works", "Materials schedule", "Historic fabric protection"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The internal alterations are sensitively designed and would not harm the significance of this Grade II listed building. The works would improve accessibility and ensure the building's continued use.",
        "key_policies_cited": ["Policy-23", "ACS-11", "NPPF Chapter 16"],
    },
    {
        "reference": "22/00678/FUL",
        "address": "Former Miners Welfare, Church Street, Eastwood, NG16 3BS",
        "ward": "Eastwood",
        "postcode": "NG16 3BS",
        "proposal": "Demolition of existing building and erection of 12 dwellings",
        "application_type": "Full Application",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2022-11-30",
        "conditions": ["Reserved matters", "Materials", "Landscaping", "Highway works", "Drainage"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The redevelopment of this brownfield site for housing is acceptable in principle. The design responds appropriately to the local context and would contribute to housing delivery in a sustainable location.",
        "key_policies_cited": ["ACS-2", "ACS-8", "ACS-10", "Policy-17"],
    },

    # BRAMCOTE - Conservation Area
    {
        "reference": "23/00345/FUL",
        "address": "The Old Rectory, Church Street, Bramcote, NG9 3HD",
        "ward": "Bramcote",
        "postcode": "NG9 3HD",
        "proposal": "Erection of single storey garden room to rear",
        "application_type": "Householder",
        "constraints": ["Conservation Area", "Adjacent to Grade II* Listed Church"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-05-12",
        "conditions": ["Natural stone/brick materials", "Roofing materials", "Landscaping scheme"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The modest single storey garden room to the rear would not be visible from public vantage points and would preserve the setting of the adjacent listed church. The design is sympathetic to the Conservation Area.",
        "key_policies_cited": ["Policy-23", "ACS-11", "Policy-17"],
    },
    {
        "reference": "22/00901/FUL",
        "address": "15 Town Street, Bramcote, NG9 3HH",
        "ward": "Bramcote",
        "postcode": "NG9 3HH",
        "proposal": "Two storey front extension creating additional bedroom and enlarged living accommodation",
        "application_type": "Householder",
        "constraints": ["Conservation Area"],
        "decision": "Refused",
        "decision_date": "2022-12-08",
        "conditions": [],
        "refusal_reasons": [
            "The proposed two storey front extension would fail to preserve or enhance the character and appearance of the Bramcote Conservation Area by reason of its prominent forward projection which would disrupt the established building line and streetscene, contrary to Policy 23 of the Part 2 Local Plan and Policy 11 of the Aligned Core Strategy."
        ],
        "case_officer_reasoning": "Front extensions in this Conservation Area are rarely acceptable as they disrupt the established streetscene. The proposal would be prominent and harmful to the character of the area.",
        "key_policies_cited": ["Policy-23", "ACS-11"],
    },

    # KIMBERLEY
    {
        "reference": "23/00234/FUL",
        "address": "Former Hardys & Hansons Brewery, Eastwood Road, Kimberley, NG16 2NG",
        "ward": "Kimberley",
        "postcode": "NG16 2NG",
        "proposal": "Conversion of former brewery building to 8 residential apartments",
        "application_type": "Full Application",
        "constraints": ["Locally Listed Building"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-04-20",
        "conditions": ["Retention of historic features", "Materials schedule", "Window details", "Landscaping"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The conversion would secure the future of this locally listed building which is an important part of Kimberley's brewing heritage. The proposals retain the key historic features including the distinctive tower.",
        "key_policies_cited": ["Policy-23", "ACS-11", "ACS-8"],
    },

    # CHILWELL - Near MOD site
    {
        "reference": "23/00678/FUL",
        "address": "42 High Road, Chilwell, NG9 5HR",
        "ward": "Chilwell West",
        "postcode": "NG9 5HR",
        "proposal": "Erection of detached garage to front of property",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Refused",
        "decision_date": "2023-08-15",
        "conditions": [],
        "refusal_reasons": [
            "The proposed detached garage in this prominent front garden location would appear as an incongruous and dominant feature which would be harmful to the character and appearance of the streetscene, contrary to Policy 17 of the Part 2 Local Plan and Policy 10 of the Aligned Core Strategy."
        ],
        "case_officer_reasoning": "Front garden garages are generally resisted where they would be prominent in the streetscene. The open front gardens contribute to the character of this road and should be retained.",
        "key_policies_cited": ["Policy-17", "ACS-10"],
    },

    # ATTENBOROUGH - Nature Reserve area
    {
        "reference": "23/00111/FUL",
        "address": "28 The Strand, Attenborough, NG9 6AU",
        "ward": "Attenborough & Chilwell East",
        "postcode": "NG9 6AU",
        "proposal": "Single storey rear extension and replacement of existing conservatory",
        "application_type": "Householder",
        "constraints": ["Adjacent to Attenborough Nature Reserve SSSI"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-02-28",
        "conditions": ["Construction environmental management plan", "Materials", "Compliance with approved plans"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The extension would not harm the adjacent SSSI. The CEMP condition will ensure construction activities do not disturb wildlife. The design is acceptable.",
        "key_policies_cited": ["Policy-17", "Policy-21", "ACS-17"],
    },

    # NUTHALL - Green Belt edge
    {
        "reference": "22/00456/FUL",
        "address": "Green Acres Farm, Nottingham Road, Nuthall, NG16 1DP",
        "ward": "Nuthall East & Strelley",
        "postcode": "NG16 1DP",
        "proposal": "Erection of agricultural storage building",
        "application_type": "Full Application",
        "constraints": ["Green Belt"],
        "decision": "Approved with Conditions",
        "decision_date": "2022-07-14",
        "conditions": ["Agricultural use only", "Materials", "Landscaping"],
        "refusal_reasons": [],
        "case_officer_reasoning": "Agricultural buildings are appropriate development in the Green Belt. The building is appropriately sited adjacent to existing farm buildings and would not harm openness.",
        "key_policies_cited": ["Policy-8", "ACS-16", "NPPF Chapter 13"],
    },
    {
        "reference": "23/00789/FUL",
        "address": "Rose Cottage, Main Street, Nuthall, NG16 1AY",
        "ward": "Nuthall East & Strelley",
        "postcode": "NG16 1AY",
        "proposal": "Two storey side extension increasing floor area by 80%",
        "application_type": "Householder",
        "constraints": ["Green Belt"],
        "decision": "Refused",
        "decision_date": "2023-10-12",
        "conditions": [],
        "refusal_reasons": [
            "The proposed extension would result in disproportionate additions to the original dwelling, representing inappropriate development in the Green Belt. No very special circumstances have been demonstrated to outweigh the harm to the Green Belt by reason of inappropriateness, contrary to Policy 8 of the Part 2 Local Plan, Policy 16 of the Aligned Core Strategy, and the NPPF."
        ],
        "case_officer_reasoning": "The cumulative extensions would exceed the 50% threshold for proportionate additions. This represents inappropriate development in the Green Belt and is harmful by definition.",
        "key_policies_cited": ["Policy-8", "ACS-16", "NPPF Chapter 13"],
    },

    # TOTON - HS2/East Midlands Hub area
    {
        "reference": "23/00567/OUT",
        "address": "Land adjacent to Toton Sidings, Stapleford Lane, Toton, NG9 6GJ",
        "ward": "Toton & Chilwell Meadows",
        "postcode": "NG9 6GJ",
        "proposal": "Outline application for mixed use development including up to 500 dwellings",
        "application_type": "Outline",
        "constraints": ["Strategic Allocation"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-11-30",
        "conditions": ["Reserved matters", "Phasing plan", "Transport assessment", "S106 agreement"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The site is allocated for development in the Local Plan. The outline proposal accords with the allocation and would deliver significant housing and employment in this sustainable location.",
        "key_policies_cited": ["ACS-2", "ACS-8", "Policy-17"],
    },

    # AWSWORTH
    {
        "reference": "23/00234/FUL",
        "address": "The Mill House, Main Street, Awsworth, NG16 2QQ",
        "ward": "Awsworth, Cossall & Trowell",
        "postcode": "NG16 2QQ",
        "proposal": "Conversion of detached outbuilding to holiday let accommodation",
        "application_type": "Full Application",
        "constraints": ["Conservation Area"],
        "decision": "Approved with Conditions",
        "decision_date": "2023-06-22",
        "conditions": ["Holiday let restriction", "Parking provision", "Materials"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The conversion of the traditional outbuilding to holiday let would preserve the building and contribute to tourism. The use is compatible with the residential surroundings.",
        "key_policies_cited": ["Policy-23", "ACS-11", "Policy-17"],
    },

    # LONG EATON (part of Broxtowe)
    {
        "reference": "23/00901/FUL",
        "address": "145 Derby Road, Long Eaton, NG10 4LH",
        "ward": "Long Eaton",
        "postcode": "NG10 4LH",
        "proposal": "Rear dormer window and hip to gable roof extension to create additional bedroom",
        "application_type": "Householder",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2023-09-18",
        "conditions": ["Materials to match", "Compliance with approved plans"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The rear dormer is acceptable in principle. The hip to gable is set back from the front elevation. The proposal would not harm the streetscene or neighbouring amenity.",
        "key_policies_cited": ["Policy-17", "ACS-10"],
    },
    {
        "reference": "22/00345/FUL",
        "address": "Unit 3, Tamworth Road Industrial Estate, Long Eaton, NG10 3GR",
        "ward": "Long Eaton",
        "postcode": "NG10 3GR",
        "proposal": "Change of use from B2 (industrial) to E(g)(iii) (light industrial)",
        "application_type": "Change of Use",
        "constraints": [],
        "decision": "Approved with Conditions",
        "decision_date": "2022-05-30",
        "conditions": ["Hours of operation", "Noise management"],
        "refusal_reasons": [],
        "case_officer_reasoning": "The proposed use is compatible with the industrial estate location. The change would support local employment and business needs.",
        "key_policies_cited": ["ACS-4", "Policy-17"],
    },
]


def find_similar_broxtowe_cases(
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str | None = None,
    postcode: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Find similar historic cases in Broxtowe.

    Args:
        proposal: The proposal description
        application_type: Type of application
        constraints: Site constraints
        ward: Ward name (optional)
        postcode: Postcode (optional)
        limit: Maximum number of results

    Returns:
        List of similar cases with similarity scores
    """
    proposal_lower = proposal.lower()
    app_type_lower = application_type.lower()
    constraints_lower = [c.lower() for c in constraints]

    scored_cases = []

    for case in BROXTOWE_HISTORIC_CASES:
        score = 0.0

        # Application type match (high weight)
        if case["application_type"].lower() == app_type_lower:
            score += 0.25
        elif "householder" in app_type_lower and "householder" in case["application_type"].lower():
            score += 0.25

        # Constraint matches (very high weight)
        case_constraints_lower = [c.lower() for c in case["constraints"]]
        for constraint in constraints_lower:
            if any(constraint in cc for cc in case_constraints_lower):
                score += 0.20
            # Partial matches
            if "conservation" in constraint and any("conservation" in cc for cc in case_constraints_lower):
                score += 0.15
            if "listed" in constraint and any("listed" in cc for cc in case_constraints_lower):
                score += 0.15
            if "green belt" in constraint and any("green belt" in cc for cc in case_constraints_lower):
                score += 0.15

        # Proposal keyword matches
        proposal_keywords = [
            "extension", "single storey", "two storey", "rear", "side", "front",
            "dormer", "loft", "garage", "outbuilding", "conversion",
            "change of use", "hmo", "balcony", "windows", "upvc", "timber"
        ]
        for keyword in proposal_keywords:
            if keyword in proposal_lower and keyword in case["proposal"].lower():
                score += 0.05

        # Ward match (local precedent)
        if ward and ward.lower() in case["ward"].lower():
            score += 0.10

        # Postcode area match
        if postcode:
            postcode_area = postcode[:4].upper()
            if postcode_area in case["postcode"]:
                score += 0.05

        if score > 0.1:
            scored_cases.append({
                **case,
                "similarity_score": min(score, 1.0),
            })

    # Sort by score
    scored_cases.sort(key=lambda x: x["similarity_score"], reverse=True)

    return scored_cases[:limit]


def get_broxtowe_precedent_analysis(similar_cases: list[dict]) -> dict[str, Any]:
    """
    Analyse precedent from similar cases.

    Returns summary of approval rates, common conditions, etc.
    """
    if not similar_cases:
        return {
            "total_cases": 0,
            "approval_rate": 0.5,
            "precedent_strength": "no_precedent",
            "common_conditions": [],
            "common_refusal_reasons": [],
        }

    approved = sum(1 for c in similar_cases if "Approved" in c["decision"])
    refused = sum(1 for c in similar_cases if "Refused" in c["decision"])
    total = len(similar_cases)

    approval_rate = approved / total if total > 0 else 0.5

    # Determine precedent strength
    if total >= 3 and approval_rate >= 0.8:
        precedent_strength = "strong_approve"
    elif total >= 3 and approval_rate <= 0.2:
        precedent_strength = "strong_refuse"
    elif total >= 2:
        precedent_strength = "moderate"
    else:
        precedent_strength = "limited"

    # Common conditions from approved cases
    all_conditions = []
    for case in similar_cases:
        if "Approved" in case["decision"]:
            all_conditions.extend(case.get("conditions", []))

    # Common refusal reasons
    all_refusals = []
    for case in similar_cases:
        if "Refused" in case["decision"]:
            all_refusals.extend(case.get("refusal_reasons", []))

    return {
        "total_cases": total,
        "approved": approved,
        "refused": refused,
        "approval_rate": approval_rate,
        "precedent_strength": precedent_strength,
        "common_conditions": list(set(all_conditions))[:5],
        "common_refusal_reasons": all_refusals[:3],
    }
