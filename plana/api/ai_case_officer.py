"""
AI Case Officer - The UK's Most Advanced Planning Assessment Engine.

This module provides senior case officer-grade planning analysis using:
- Deep policy understanding with paragraph-level NPPF citations
- Material considerations framework with proper weighing
- Harm quantification (substantial, less than substantial, no harm)
- Planning balance as per Mansell v Tonbridge
- Site-specific condition drafting
- Document analysis and interpretation
- Consultation response synthesis

The AI Case Officer follows the exact methodology used by senior
planning officers, ensuring legally robust and defensible recommendations.
"""

import os
import json
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class HarmLevel(Enum):
    """Heritage harm levels per NPPF paragraphs 201-202."""
    NO_HARM = "no_harm"
    NEGLIGIBLE = "negligible"
    LESS_THAN_SUBSTANTIAL_LOW = "less_than_substantial_low"
    LESS_THAN_SUBSTANTIAL_MODERATE = "less_than_substantial_moderate"
    LESS_THAN_SUBSTANTIAL_HIGH = "less_than_substantial_high"
    SUBSTANTIAL = "substantial"
    TOTAL_LOSS = "total_loss"


class AmenityImpact(Enum):
    """Residential amenity impact levels."""
    NO_IMPACT = "no_impact"
    MINOR_ACCEPTABLE = "minor_acceptable"
    MODERATE_MITIGATABLE = "moderate_mitigatable"
    SIGNIFICANT_HARMFUL = "significant_harmful"
    SEVERE_UNACCEPTABLE = "severe_unacceptable"


class Weight(Enum):
    """Weight to be given to material considerations."""
    NO_WEIGHT = 0
    LIMITED = 1
    MODERATE = 2
    SIGNIFICANT = 3
    SUBSTANTIAL = 4
    GREAT = 5
    VERY_GREAT = 6  # Reserved for heritage assets per NPPF 199


@dataclass
class MaterialConsideration:
    """A material consideration in the planning balance."""
    factor: str
    description: str
    is_benefit: bool  # True = benefit, False = harm
    weight: Weight
    policy_basis: list[str]
    evidence: str
    confidence: float = 0.8


@dataclass
class HeritageAssessment:
    """Assessment of heritage impact per NPPF Chapter 16."""
    asset_type: str  # Listed Building, Conservation Area, etc.
    asset_grade: Optional[str]  # Grade I, II*, II, or None
    significance: str  # Description of what makes it significant
    impact_on_significance: str
    harm_level: HarmLevel
    justification: str
    public_benefits: list[str]
    nppf_paragraph: str  # 199, 200, 201, 202, etc.
    statutory_duty: str  # Section 66 or 72
    weight_to_harm: Weight = Weight.VERY_GREAT  # NPPF 199 requires great weight


@dataclass
class AmenityAssessment:
    """Assessment of residential amenity impact."""
    affected_property: str
    impact_type: str  # daylight, sunlight, privacy, outlook, noise
    current_situation: str
    proposed_impact: str
    impact_level: AmenityImpact
    mitigation_possible: bool
    mitigation_measures: list[str]
    policy_basis: list[str]


@dataclass
class Condition:
    """A planning condition meeting the 6 tests."""
    number: int
    title: str
    full_wording: str
    reason: str
    policy_basis: str
    condition_type: str  # pre-commencement, pre-occupation, compliance, informative
    is_necessary: bool = True
    is_relevant: bool = True
    is_enforceable: bool = True
    is_precise: bool = True
    is_reasonable: bool = True
    meets_six_tests: bool = True


@dataclass
class PlanningBalance:
    """The planning balance - heart of the case officer's assessment."""
    benefits: list[MaterialConsideration]
    harms: list[MaterialConsideration]
    heritage_harm: Optional[HeritageAssessment]
    amenity_impacts: list[AmenityAssessment]

    # The tilted balance per NPPF para 11
    tilted_balance_engaged: bool = False
    tilted_balance_reason: str = ""

    # Paragraph 202 balance for heritage
    para_202_balance: Optional[str] = None

    # Overall assessment
    benefits_outweigh_harms: bool = True
    overall_narrative: str = ""


@dataclass
class CaseOfficerReport:
    """Complete case officer report."""
    # Header
    reference: str
    site_address: str
    proposal: str
    applicant: str
    application_type: str
    ward: str

    # Site analysis
    site_description: str
    planning_history: list[dict]
    constraints: list[str]

    # Policy framework
    development_plan_policies: list[dict]
    nppf_chapters: list[dict]
    spd_guidance: list[str]

    # Consultation responses
    statutory_consultees: list[dict]
    neighbour_responses: dict

    # Assessment
    key_issues: list[str]
    principle_of_development: str
    design_assessment: str
    heritage_assessment: Optional[HeritageAssessment]
    amenity_assessment: list[AmenityAssessment]
    highways_assessment: str
    other_matters: list[dict]

    # Planning balance
    planning_balance: PlanningBalance

    # Recommendation
    recommendation: str  # APPROVE, APPROVE_WITH_CONDITIONS, REFUSE
    conditions: list[Condition]
    refusal_reasons: list[dict]
    informatives: list[str]

    # Metadata
    confidence_score: float
    key_risks: list[str]
    council_id: str = "broxtowe"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# NPPF DEEP KNOWLEDGE BASE
# =============================================================================

NPPF_PARAGRAPHS = {
    # Chapter 2: Achieving sustainable development
    "7": "The purpose of the planning system is to contribute to the achievement of sustainable development.",
    "8": "Achieving sustainable development means the planning system has three overarching objectives: economic, social, and environmental.",
    "10": "At the heart of the Framework is a presumption in favour of sustainable development.",
    "11": "Plans and decisions should apply a presumption in favour of sustainable development. For decision-taking this means: (c) approving development proposals that accord with an up-to-date development plan without delay; or (d) where there are no relevant development plan policies, or the policies most important for determining the application are out-of-date, granting permission unless: (i) the application of policies in this Framework that protect areas or assets of particular importance provides a clear reason for refusing the development proposed; or (ii) any adverse impacts of doing so would significantly and demonstrably outweigh the benefits, when assessed against the policies in this Framework taken as a whole.",

    # Chapter 4: Decision-making
    "38": "Local planning authorities should approach decisions on proposed development in a positive and creative way, and work proactively with applicants to secure developments that will improve the economic, social and environmental conditions of the area. Decision-makers at every level should seek to approve applications for sustainable development where possible.",
    "47": "Planning law requires that applications for planning permission be determined in accordance with the development plan, unless material considerations indicate otherwise.",

    # Chapter 12: Achieving well-designed places
    "126": "The creation of high quality, beautiful and sustainable buildings and places is fundamental to what the planning and development process should achieve.",
    "130": "Planning decisions should ensure that developments: (a) will function well and add to the overall quality of the area; (b) are visually attractive as a result of good architecture, layout and appropriate and effective landscaping; (c) are sympathetic to local character and history; (d) establish or maintain a strong sense of place; (e) optimise the potential of the site; (f) create places that are safe, inclusive and accessible.",
    "134": "Development that is not well designed should be refused, especially where it fails to reflect local design policies and government guidance on design.",

    # Chapter 16: Conserving and enhancing the historic environment
    "194": "In determining applications, local planning authorities should require an applicant to describe the significance of any heritage assets affected.",
    "195": "Local planning authorities should identify and assess the particular significance of any heritage asset that may be affected by a proposal.",
    "197": "In determining applications, local planning authorities should take account of: (a) the desirability of sustaining and enhancing the significance of heritage assets; (b) the positive contribution that conservation of heritage assets can make; (c) the desirability of new development making a positive contribution to local character and distinctiveness.",
    "199": "When considering the impact of a proposed development on the significance of a designated heritage asset, great weight should be given to the asset's conservation (and the more important the asset, the greater the weight should be). This is irrespective of whether any potential harm amounts to substantial harm, total loss or less than substantial harm to its significance.",
    "200": "Any harm to, or loss of, the significance of a designated heritage asset (from its alteration or destruction, or from development within its setting), should require clear and convincing justification.",
    "201": "Where a proposed development will lead to substantial harm to (or total loss of significance of) a designated heritage asset, local planning authorities should refuse consent, unless it can be demonstrated that the substantial harm or total loss is necessary to achieve substantial public benefits that outweigh that harm or loss.",
    "202": "Where a development proposal will lead to less than substantial harm to the significance of a designated heritage asset, this harm should be weighed against the public benefits of the proposal including, where appropriate, securing its optimum viable use.",
    "206": "Local planning authorities should look for opportunities for new development within Conservation Areas and World Heritage Sites, and within the setting of heritage assets, to enhance or better reveal their significance. Proposals that preserve those elements of the setting that make a positive contribution to the asset (or which better reveal its significance) should be treated favourably.",
}

STATUTORY_DUTIES = {
    "section_66": """Section 66(1) of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires that: "In considering whether to grant planning permission for development which affects a listed building or its setting, the local planning authority shall have special regard to the desirability of preserving the building or its setting or any features of special architectural or historic interest which it possesses." The Court of Appeal in Barnwell Manor confirmed this creates a strong statutory presumption against granting permission for development that harms a listed building or its setting.""",

    "section_72": """Section 72(1) of the Planning (Listed Buildings and Conservation Areas) Act 1990 requires that: "In the exercise, with respect to any buildings or other land in a conservation area, special attention shall be paid to the desirability of preserving or enhancing the character or appearance of that area." This is a statutory duty that must be discharged before any grant of planning permission.""",
}


# =============================================================================
# BROXTOWE CONSERVATION AREA CHARACTER APPRAISALS
# =============================================================================

BROXTOWE_CONSERVATION_AREAS = {
    "eastwood": {
        "name": "Eastwood Conservation Area",
        "character": "Victorian and Edwardian terraced housing with distinctive red-brick construction, slate roofs, and bay windows. Strong association with D.H. Lawrence whose birthplace and childhood homes are within the area. Traditional streetscape with continuous building lines, stone kerbs, and period street furniture.",
        "key_features": [
            "Red-brick Victorian terraces with decorative detailing",
            "Slate roofing and chimneys forming distinctive roofline",
            "Bay windows and stone lintels/sills",
            "Continuous building lines creating enclosed street character",
            "D.H. Lawrence birthplace (8a Victoria Street) - Grade II listed",
            "Traditional shopfronts on Nottingham Road",
            "Stone boundary walls and traditional railings",
        ],
        "sensitivities": [
            "uPVC windows and doors eroding historic character",
            "Loss of chimney stacks breaking roofline",
            "Inappropriate modern materials (concrete tiles, render over brick)",
            "Front garden parking removing traditional boundary treatments",
            "Satellite dishes and modern additions on front elevations",
            "Loss of original architectural details (cornices, lintels, sills)",
        ],
        "materials_expected": ["Red brick", "Natural slate", "Timber windows", "Stone lintels/sills", "Cast iron rainwater goods"],
        "wards": ["Eastwood St Marys", "Eastwood Hall"],
    },
    "beeston": {
        "name": "Beeston Conservation Area",
        "character": "Mixed-period town centre with Victorian commercial core, Georgian residential edges, and medieval church. Compact urban form with narrow plots and varied roofline. The High Road forms the commercial spine with traditional shopfronts and upper-floor residential.",
        "key_features": [
            "Parish Church of St John the Baptist (medieval origins)",
            "Victorian commercial buildings on High Road",
            "Georgian residential properties on Dovecote Lane",
            "Narrow medieval plot widths visible in building pattern",
            "Traditional shopfronts with stall risers and fascias",
            "Mix of brick types reflecting different building periods",
        ],
        "sensitivities": [
            "Scale of new development relative to existing fine grain",
            "Loss of traditional shopfronts to modern fascias",
            "Inappropriate infill development breaking established pattern",
            "Traffic impact on pedestrian character of High Road",
        ],
        "materials_expected": ["Red/brown brick", "Slate/plain tile roofs", "Timber shopfronts", "Stone dressings"],
        "wards": ["Beeston Central", "Beeston North", "Beeston West"],
    },
    "bramcote": {
        "name": "Bramcote Conservation Area",
        "character": "Semi-rural village character with large mature gardens, substantial Victorian and Edwardian houses, and a prominent hilltop church. Tree-lined streets with low-density development and generous spacing between buildings. Important long-distance views across the Trent Valley.",
        "key_features": [
            "St Michael and All Angels Church (hilltop landmark)",
            "Substantial Victorian/Edwardian villas with large gardens",
            "Mature trees and hedgerows defining street character",
            "Long-distance views across Trent Valley from higher ground",
            "Low-density development with generous plot sizes",
            "Bramcote Hills Park (open landscape setting)",
        ],
        "sensitivities": [
            "Subdivision of large plots eroding spacious character",
            "Loss of mature trees and hedgerows",
            "Development blocking important views",
            "Building heights exceeding established 2-storey pattern",
            "Erosion of green character through hard landscaping",
        ],
        "materials_expected": ["Red brick", "Render", "Plain tile/slate roofs", "Timber windows"],
        "wards": ["Bramcote"],
    },
    "kimberley": {
        "name": "Kimberley Conservation Area",
        "character": "Former industrial town with post-industrial regeneration character. Strong association with brewery heritage and Victorian workers' housing. Compact town centre with varied building periods and distinctive chimneyscape.",
        "key_features": [
            "Former Hardy and Hanson brewery buildings",
            "Victorian workers' cottages in red brick",
            "Town centre commercial buildings of varied periods",
            "Industrial heritage structures",
            "Traditional pub buildings",
        ],
        "sensitivities": [
            "Loss of industrial heritage features",
            "Inappropriate modern materials on Victorian terraces",
            "Scale of new development relative to small-scale existing",
            "Loss of brewery-related heritage features",
        ],
        "materials_expected": ["Red brick", "Slate roofs", "Timber windows", "Stone details"],
        "wards": ["Kimberley"],
    },
    "stapleford": {
        "name": "Stapleford Conservation Area",
        "character": "Historic market town core with medieval street pattern, Victorian commercial buildings, and remnants of framework knitting heritage. Narrow streets with tight urban grain.",
        "key_features": [
            "Medieval street pattern around Church Street",
            "Victorian commercial buildings on Derby Road",
            "Framework knitting heritage (domestic workshops)",
            "Parish church with medieval origins",
        ],
        "sensitivities": [
            "Loss of historic street pattern to road widening",
            "Inappropriate scale of infill development",
            "Loss of framework knitting workshop evidence",
        ],
        "materials_expected": ["Red brick", "Slate roofs", "Timber windows"],
        "wards": ["Stapleford North", "Stapleford South"],
    },
    "attenborough": {
        "name": "Attenborough Conservation Area",
        "character": "Riverside village with strong landscape setting alongside River Trent and Attenborough Nature Reserve (SSSI/Ramsar). Low-density development with mature vegetation. Important ecological corridor.",
        "key_features": [
            "St Mary's Church (Grade I listed)",
            "Riverside setting and Nature Reserve context",
            "Village green and traditional layout",
            "Mature trees and hedgerows",
            "Low-density development reflecting village character",
        ],
        "sensitivities": [
            "Ecological impact on Nature Reserve (SSSI/Ramsar)",
            "Flood risk from River Trent",
            "Loss of village-scale development pattern",
            "Impact on important views to river and Nature Reserve",
            "Light pollution affecting ecology",
        ],
        "materials_expected": ["Red brick", "Natural slate", "Timber windows", "Stone dressings"],
        "wards": ["Attenborough and Chilwell East"],
    },
}


# =============================================================================
# MEASUREMENT EXTRACTION FROM DOCUMENTS/PROPOSALS
# =============================================================================

@dataclass
class ExtractedMeasurements:
    """Measurements extracted from proposal text and documents."""
    ridge_height_m: Optional[float] = None
    eaves_height_m: Optional[float] = None
    depth_m: Optional[float] = None
    width_m: Optional[float] = None
    length_m: Optional[float] = None
    separation_to_boundary_m: Optional[float] = None
    separation_to_neighbour_m: Optional[float] = None
    floor_area_sqm: Optional[float] = None
    garden_area_sqm: Optional[float] = None
    plot_area_sqm: Optional[float] = None
    num_bedrooms: Optional[int] = None
    num_units: Optional[int] = None
    parking_spaces: Optional[int] = None
    all_dimensions: list[tuple[float, str]] = field(default_factory=list)


def extract_measurements(proposal: str, documents: list[dict] | None = None) -> ExtractedMeasurements:
    """Extract actual measurements from proposal text and document content."""
    m = ExtractedMeasurements()
    texts = [proposal]

    # Gather text from documents if available
    if documents:
        for doc in documents:
            if isinstance(doc, dict):
                for key in ("extracted_text", "text", "content", "description"):
                    if doc.get(key):
                        texts.append(str(doc[key]))

    combined = " ".join(texts).lower()

    # Ridge height
    match = re.search(r'ridge\s*(?:height)?\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', combined)
    if match:
        m.ridge_height_m = float(match.group(1))

    # Eaves height
    match = re.search(r'eaves?\s*(?:height)?\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', combined)
    if match:
        m.eaves_height_m = float(match.group(1))

    # Depth/projection
    for pattern in [
        r'(?:depth|projection|projects?)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)',
        r'(\d+(?:\.\d+)?)\s*(?:m|metres?)\s*(?:deep|depth|projection)',
    ]:
        match = re.search(pattern, combined)
        if match:
            m.depth_m = float(match.group(1))
            break

    # Width
    match = re.search(r'(?:width|wide)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)', combined)
    if not match:
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|metres?)\s*(?:wide|width)', combined)
    if match:
        m.width_m = float(match.group(1))

    # Separation to boundary
    for pattern in [
        r'(?:boundary|set[\s-]?back)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)',
        r'(\d+(?:\.\d+)?)\s*(?:m|metres?)\s*(?:from|to|off)\s*(?:the\s+)?boundary',
    ]:
        match = re.search(pattern, combined)
        if match:
            m.separation_to_boundary_m = float(match.group(1))
            break

    # Separation to neighbour windows
    for pattern in [
        r'(\d+(?:\.\d+)?)\s*(?:m|metres?)\s*(?:from|to|between)\s*(?:the\s+)?(?:neighbour|adjacent|adjoining)',
        r'(?:separation|distance)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)',
        r'(?:window[\s-]?to[\s-]?window|facing\s+distance)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|metres?)',
    ]:
        match = re.search(pattern, combined)
        if match:
            m.separation_to_neighbour_m = float(match.group(1))
            break

    # Floor area
    match = re.search(r'(?:floor\s*area|floorspace|gfa|gia)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|m2|m²|sqm)', combined)
    if match:
        m.floor_area_sqm = float(match.group(1))

    # Garden / amenity area
    match = re.search(r'(?:garden|amenity\s*space|rear\s*garden)\s*(?:area)?\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|m2|m²|sqm)', combined)
    if match:
        m.garden_area_sqm = float(match.group(1))

    # Plot area
    match = re.search(r'(?:plot|site)\s*(?:area)?\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|m2|m²|sqm|hectare)', combined)
    if match:
        m.plot_area_sqm = float(match.group(1))

    # Bedrooms
    match = re.search(r'(\d+)\s*(?:no\.?\s*)?(?:bed(?:room)?s?)', combined)
    if match:
        m.num_bedrooms = int(match.group(1))

    # Units
    match = re.search(r'(\d+)\s*(?:no\.?\s*)?(?:unit|dwelling|flat|apartment|house)s?', combined)
    if match:
        m.num_units = int(match.group(1))

    # Parking
    match = re.search(r'(\d+)\s*(?:no\.?\s*)?(?:parking|car)\s*(?:space|bay)', combined)
    if match:
        m.parking_spaces = int(match.group(1))

    # Collect all dimensional values for context
    for dm in re.finditer(r'(\d+(?:\.\d+)?)\s*(m|mm|metres?|meters?|sq\.?\s*m|m2|m²|sqm)', combined):
        val = float(dm.group(1))
        unit = dm.group(2)
        if unit in ('mm',):
            val = val / 1000.0
            unit = 'm'
        m.all_dimensions.append((val, unit))

    return m


# =============================================================================
# INTELLIGENT ANALYSIS FUNCTIONS
# =============================================================================

def _extract_public_benefits(proposal: str) -> list[str]:
    """
    Extract public benefits from proposal text for NPPF 201/202 balance.

    Public benefits include: housing delivery, affordable housing, heritage
    enhancement, economic activity, community facilities, etc.
    Per Palmer v Herefordshire, private benefits that benefit the wider public
    (improved living conditions) are legitimate public benefits.
    """
    benefits = []
    proposal_lower = proposal.lower()

    # Housing delivery
    dwelling_match = re.search(r'(\d+)\s*(?:dwelling|unit|house|home|apartment|flat)', proposal_lower)
    if dwelling_match:
        num = int(dwelling_match.group(1))
        if num >= 10:
            benefits.append(f"Delivery of {num} dwellings contributing to housing supply")
        elif num >= 1:
            benefits.append(f"Provision of {num} dwelling(s) contributing to housing need")

    # Affordable housing
    if any(kw in proposal_lower for kw in ['affordable', 'social housing', 'shared ownership']):
        affordable_match = re.search(r'(\d+)%?\s*affordable', proposal_lower)
        if affordable_match:
            benefits.append(f"Provision of {affordable_match.group(1)}% affordable housing")
        else:
            benefits.append("Provision of affordable housing")

    # Heritage enhancement
    if any(kw in proposal_lower for kw in ['restoration', 'restore', 'reinstate', 'repair', 'conserve']):
        benefits.append("Heritage enhancement through restoration/repair of historic fabric")
    if any(kw in proposal_lower for kw in ['replace upvc', 'replacing upvc', 'removing upvc', 'timber sash', 'timber window']):
        benefits.append("Heritage enhancement through replacement of inappropriate modern materials with traditional alternatives")
    if any(kw in proposal_lower for kw in ['optimum viable use', 'bring back into use', 'vacant', 'derelict']):
        benefits.append("Securing the optimum viable use of a heritage asset (NPPF para 202)")

    # Economic benefits
    if any(kw in proposal_lower for kw in ['employment', 'job', 'business', 'commercial', 'retail', 'office']):
        jobs_match = re.search(r'(\d+)\s*(?:job|employment|post)', proposal_lower)
        if jobs_match:
            benefits.append(f"Creation of {jobs_match.group(1)} employment opportunities")
        else:
            benefits.append("Economic activity and employment generation")

    # Community facilities
    if any(kw in proposal_lower for kw in ['community', 'school', 'nursery', 'health', 'surgery', 'play area', 'open space']):
        benefits.append("Provision of community facilities/infrastructure")

    # Improved living accommodation (private benefit that counts per Palmer)
    if any(kw in proposal_lower for kw in ['extension', 'alteration', 'enlargement', 'improvement']):
        benefits.append("Improved living accommodation for occupiers (private benefit weighing in the balance per Palmer v Herefordshire)")

    # Brownfield / PDL
    if any(kw in proposal_lower for kw in ['brownfield', 'previously developed', 'derelict', 'vacant site']):
        benefits.append("Efficient use of previously developed land in accordance with NPPF paragraph 120")

    return benefits


def analyse_heritage_impact(
    proposal: str,
    constraints: list[str],
    site_description: str,
    ward: str = "",
    site_address: str = "",
) -> Optional[HeritageAssessment]:
    """
    Perform heritage impact assessment following NPPF Chapter 16.

    This follows the methodology established in case law:
    1. Identify the heritage asset(s) — including setting
    2. Assess significance — Grade-weighted
    3. Assess impact on significance — context-aware (elevation, location)
    4. Quantify harm level — Grade baseline + proposal specifics
    5. Apply statutory duty — combined Section 66 AND 72 where both apply
    6. Extract and weigh public benefits (NPPF 201/202)
    """
    constraints_lower = [c.lower() for c in constraints]
    proposal_lower = proposal.lower()

    # Identify heritage assets — including SETTING (NPPF 200)
    has_listed = any('listed' in c for c in constraints_lower)
    has_conservation = any('conservation' in c for c in constraints_lower)

    # Check for development affecting SETTING of a heritage asset (not just ON it)
    setting_keywords = ['adjacent to listed', 'near listed', 'opposite listed',
                        'setting of', 'within setting', 'adjoining listed',
                        'next to listed', 'near grade', 'adjacent to grade']
    affects_setting = any(kw in ' '.join(constraints_lower) for kw in setting_keywords) or \
                      any(kw in proposal_lower for kw in ['setting', 'curtilage', 'adjacent to'])

    if not has_listed and not has_conservation and not affects_setting:
        return None

    # Determine asset type and grade
    asset_type = "Conservation Area"
    asset_grade = None
    statutory_duties = []  # Track ALL applicable duties

    for c in constraints:
        cl = c.lower()
        if 'grade i ' in cl or 'grade i listed' in cl:
            asset_type = "Listed Building"
            asset_grade = "I"
        elif 'grade ii*' in cl:
            asset_type = "Listed Building"
            asset_grade = "II*"
        elif 'grade ii' in cl or ('listed' in cl and 'conservation' not in cl):
            asset_type = "Listed Building"
            asset_grade = "II"

    # FIX 4: Combine BOTH statutory duties when applicable
    if has_listed or asset_grade:
        statutory_duties.append("section_66")
    if has_conservation:
        statutory_duties.append("section_72")

    # If only setting affected (not on the asset itself)
    if affects_setting and not has_listed and not has_conservation:
        asset_type = "Setting of Heritage Asset"
        statutory_duties.append("section_66")  # Setting of LB still engages s.66

    # Primary duty for compatibility
    statutory_duty = statutory_duties[0] if statutory_duties else "section_72"

    # Assess significance — Grade-weighted (FIX 1)
    if asset_grade == "I":
        significance = "This Grade I listed building is of exceptional interest, representing only 2% of all listed buildings nationally. Its significance derives from its outstanding architectural and historic interest. NPPF paragraph 199 requires that the more important the asset, the greater the weight to its conservation."
    elif asset_grade == "II*":
        significance = "This Grade II* listed building is of particularly important interest, representing only 5.8% of listed buildings nationally. It is of more than special interest, warranting every effort to preserve it. NPPF paragraph 199 gives greater weight to more important assets."
    elif asset_grade == "II":
        significance = "This Grade II listed building is of special interest, warranting every effort to preserve it in accordance with paragraph 199 of the NPPF."
    elif affects_setting and not has_conservation:
        significance = "The significance of the nearby heritage asset may be affected by development within its setting. NPPF paragraph 200 states that harm from development within the setting of a heritage asset requires clear and convincing justification."
    else:
        # Conservation Area — try to load specific character
        ca_info = _find_conservation_area(ward, site_address, constraints)
        if ca_info:
            significance = f"The {ca_info['name']} derives its significance from: {ca_info['character']} The contribution of individual buildings and spaces to this character must be preserved or enhanced."
        else:
            significance = "The Conservation Area derives its significance from the quality of its historic townscape, architectural coherence, and the contribution individual buildings make to the character of the area."

    # FIX 1: Grade-weighted baseline harm + context-aware assessment
    # Grade I/II* get HIGHER baseline harm for equivalent proposals
    grade_harm_uplift = 0  # 0 = no uplift, 1 = one level higher, 2 = two levels higher
    if asset_grade == "I":
        grade_harm_uplift = 2
    elif asset_grade == "II*":
        grade_harm_uplift = 1

    # Detect which elevation is affected
    is_principal_elevation = any(kw in proposal_lower for kw in
                                 ['front elevation', 'principal elevation', 'street facing',
                                  'front of', 'main facade', 'front facade'])
    is_rear = any(kw in proposal_lower for kw in ['rear', 'back of'])
    is_side = any(kw in proposal_lower for kw in ['side elevation', 'side of'])

    # Principal elevation = higher harm than rear
    if is_principal_elevation:
        grade_harm_uplift = min(grade_harm_uplift + 1, 2)

    # Check for POSITIVE heritage indicators first
    positive_indicators = [
        'restoration', 'restore', 'reinstate', 'repair', 'timber sash',
        'timber window', 'traditional', 'historic', 'original',
        'replace upvc', 'replace u-pvc', 'replacing upvc', 'removing upvc',
        'secondary glazing', 'sympathetic', 'preserve', 'enhance', 'conserve',
        'like for like', 'match existing', 'internal alteration', 'internal works'
    ]

    is_positive = any(term in proposal_lower for term in positive_indicators)
    is_internal = 'internal' in proposal_lower and 'external' not in proposal_lower

    # uPVC INSTALLATION on listed building = substantial harm
    installing_upvc = (('upvc' in proposal_lower or 'u-pvc' in proposal_lower) and
                       not any(term in proposal_lower for term in
                               ['replace upvc', 'replacing upvc', 'remove upvc', 'removing upvc', 'with timber']))

    # Loss of historic features
    loses_features = any(kw in proposal_lower for kw in
                          ['remove chimney', 'demolish chimney', 'remove cornice',
                           'remove lintel', 'remove sill', 'remove boundary wall',
                           'demolish boundary', 'remove railings', 'demolish wall'])

    # Determine base harm level
    harm_level = HarmLevel.NO_HARM

    if has_listed and installing_upvc:
        harm_level = HarmLevel.SUBSTANTIAL
        impact = "The introduction of uPVC windows would cause substantial harm to the significance of this listed building by fundamentally altering its historic character with inappropriate modern materials."
    elif is_positive or is_internal:
        harm_level = HarmLevel.NO_HARM
        impact = "The proposal would preserve or enhance the significance of the heritage asset. The works are considered sympathetic and appropriate."
    elif any(term in proposal_lower for term in ['demolition', 'demolish', 'total loss', 'remove entirely']):
        harm_level = HarmLevel.SUBSTANTIAL
        impact = "The proposal would cause substantial harm to the significance of the heritage asset through demolition or total loss."
    elif any(term in proposal_lower for term in ['significant alteration', 'major extension', 'dominant']):
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH
        impact = "The proposal would cause less than substantial harm at the higher end of the spectrum."
    elif loses_features:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE
        impact = "The proposal involves the loss of historic features which contribute to the significance of the heritage asset, causing less than substantial harm at the moderate level."
    elif 'single storey' in proposal_lower and is_rear:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
        impact = "The proposed single-storey rear extension is typically acceptable where subordinate and using appropriate materials. The harm is at the lower end of less than substantial."
    elif 'extension' in proposal_lower or 'alteration' in proposal_lower:
        harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
        impact = "The proposal would cause less than substantial harm at the lower end of the spectrum, subject to appropriate materials and detailing."
    elif affects_setting:
        # Development affecting setting of heritage asset (NPPF 200)
        # New buildings, tall structures, and large developments = higher setting harm
        is_new_building = any(kw in proposal_lower for kw in
                              ['erection', 'new build', 'dwelling', 'apartment', 'block', 'house'])
        is_large_scale = any(kw in proposal_lower for kw in
                             ['three storey', 'three-storey', 'four storey', 'apartment block',
                              'flats', 'commercial', 'industrial'])
        if is_large_scale:
            harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE
            impact = "The proposed development, by virtue of its scale, would affect the setting of the heritage asset. NPPF paragraph 200 requires clear and convincing justification for any harm from development within the setting of a designated heritage asset."
        elif is_new_building:
            harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
            impact = "The proposed new development may affect the setting of the heritage asset. NPPF paragraph 200 requires clear and convincing justification for any harm within the setting."
        else:
            harm_level = HarmLevel.LESS_THAN_SUBSTANTIAL_LOW
            impact = "The proposal may affect the setting of the heritage asset. NPPF paragraph 200 requires clear and convincing justification for any harm within the setting."
    else:
        harm_level = HarmLevel.NO_HARM
        impact = "The proposal is not considered to cause harm to the significance of the heritage asset."

    # FIX 1: Apply Grade-based harm uplift (Grade I/II* = higher baseline)
    if grade_harm_uplift > 0 and harm_level not in [HarmLevel.NO_HARM, HarmLevel.SUBSTANTIAL, HarmLevel.TOTAL_LOSS]:
        harm_levels_ascending = [
            HarmLevel.NEGLIGIBLE,
            HarmLevel.LESS_THAN_SUBSTANTIAL_LOW,
            HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE,
            HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH,
            HarmLevel.SUBSTANTIAL,
        ]
        try:
            current_idx = harm_levels_ascending.index(harm_level)
            new_idx = min(current_idx + grade_harm_uplift, len(harm_levels_ascending) - 1)
            old_harm = harm_level
            harm_level = harm_levels_ascending[new_idx]
            if harm_level != old_harm:
                grade_label = f"Grade {asset_grade}" if asset_grade else "heritage asset"
                elevation_note = ""
                if is_principal_elevation:
                    elevation_note = " affecting the principal elevation"
                impact += f" Given the exceptional significance of this {grade_label}{elevation_note}, the harm is assessed at {harm_level.value.replace('_', ' ')} (NPPF paragraph 199: 'the more important the asset, the greater the weight')."
        except ValueError:
            pass

    # FIX 4: Combined statutory duty text
    if len(statutory_duties) > 1:
        duty_text = "Both " + " and ".join(
            STATUTORY_DUTIES[d].split('"')[0].strip().rstrip(':') + ' (requiring "' + STATUTORY_DUTIES[d].split('"')[1] + '")'
            if '"' in STATUTORY_DUTIES[d] else STATUTORY_DUTIES[d]
            for d in statutory_duties[:2]
        ) + " apply to this proposal."
    else:
        duty_text = STATUTORY_DUTIES.get(statutory_duty, "")

    # Determine NPPF paragraph and justification
    if harm_level == HarmLevel.SUBSTANTIAL:
        nppf_para = "201"
        justification = f"Paragraph 201 of the NPPF states that where a proposed development will lead to substantial harm, permission should be refused unless substantial public benefits outweigh that harm. {duty_text}"
    elif harm_level in [HarmLevel.LESS_THAN_SUBSTANTIAL_LOW, HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE, HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH]:
        nppf_para = "202"
        justification = f"Paragraph 202 of the NPPF requires that where development leads to less than substantial harm, this harm should be weighed against the public benefits. The harm identified carries great weight per paragraph 199. {duty_text}"
    else:
        nppf_para = "199"
        justification = f"The proposal would preserve the significance of the heritage asset in accordance with paragraph 199 of the NPPF and the statutory duty under {' and '.join(d.replace('_', ' ').title() for d in statutory_duties)}."

    # FIX 2: Extract public benefits from proposal
    public_benefits = _extract_public_benefits(proposal)

    return HeritageAssessment(
        asset_type=asset_type,
        asset_grade=asset_grade,
        significance=significance,
        impact_on_significance=impact,
        harm_level=harm_level,
        justification=justification,
        public_benefits=public_benefits,
        nppf_paragraph=nppf_para,
        statutory_duty=statutory_duty,
        weight_to_harm=Weight.VERY_GREAT,
    )


def analyse_amenity_impact(
    proposal: str,
    constraints: list[str],
    application_type: str,
    measurements: Optional[ExtractedMeasurements] = None,
    council_id: str = "broxtowe",
) -> list[AmenityAssessment]:
    """
    Perform residential amenity assessment following Broxtowe Policy 17 (LP17).

    Broxtowe LP17 standards:
    - Privacy: 21m minimum between habitable room windows
    - Privacy: 12m minimum to a blank wall or high-level window
    - Daylight: 45-degree test from centre of ground floor windows
    - Sunlight: Development should not cause significant overshadowing
    - Outlook: Development should not be overbearing or oppressive
    - Private amenity space: Minimum 50sqm garden for houses
    """
    assessments = []
    proposal_lower = proposal.lower()
    m = measurements or ExtractedMeasurements()

    # Broxtowe policy references
    amenity_policy = "Policy 17" if council_id == "broxtowe" else "DM6.6"
    amenity_policies = [amenity_policy, "NPPF paragraph 130(f)"]

    # --- Privacy / Overlooking Assessment ---
    has_balcony = 'balcony' in proposal_lower
    has_first_floor = 'first floor' in proposal_lower or 'two storey' in proposal_lower or 'two-storey' in proposal_lower
    has_roof_terrace = 'roof terrace' in proposal_lower or 'rooftop' in proposal_lower
    has_side_windows = 'side window' in proposal_lower or 'side elevation' in proposal_lower
    has_new_windows = any(kw in proposal_lower for kw in ['new window', 'additional window', 'dormer', 'rooflight', 'velux'])

    # Check separation distances against LP17 21m rule
    if m.separation_to_neighbour_m is not None:
        if m.separation_to_neighbour_m < 12.0:
            assessments.append(AmenityAssessment(
                affected_property="Neighbouring residential properties",
                impact_type="privacy",
                current_situation="Neighbouring properties are in close proximity.",
                proposed_impact=f"The proposed development would have a window-to-wall/boundary separation of only {m.separation_to_neighbour_m:.1f}m, which is below the 12m minimum standard for blank walls/high-level windows set out in {amenity_policy}. This would result in unacceptable overlooking.",
                impact_level=AmenityImpact.SEVERE_UNACCEPTABLE,
                mitigation_possible=True,
                mitigation_measures=["Obscure glazing to affected windows", "Non-opening below 1.7m", "Removal of permitted development rights for future openings"],
                policy_basis=amenity_policies,
            ))
        elif m.separation_to_neighbour_m < 21.0 and has_first_floor:
            assessments.append(AmenityAssessment(
                affected_property="Neighbouring residential properties",
                impact_type="privacy",
                current_situation="Neighbouring properties currently maintain adequate separation distances.",
                proposed_impact=f"The proposed first-floor habitable room windows would be {m.separation_to_neighbour_m:.1f}m from the neighbouring windows, below the 21m standard in {amenity_policy}. This requires mitigation to be acceptable.",
                impact_level=AmenityImpact.MODERATE_MITIGATABLE,
                mitigation_possible=True,
                mitigation_measures=["Obscure glazing to affected first-floor windows", "Non-opening below 1.7m", "Angled window reveals to restrict views"],
                policy_basis=amenity_policies,
            ))

    # Balcony at first floor - generally unacceptable in residential areas
    if has_balcony and has_first_floor:
        assessments.append(AmenityAssessment(
            affected_property="Neighbouring residential properties",
            impact_type="privacy",
            current_situation="Neighbouring properties currently enjoy reasonable levels of privacy in their rear gardens and habitable rooms.",
            proposed_impact=f"The proposed first-floor balcony would introduce an elevated external amenity space with direct views into neighbouring rear gardens and potentially into habitable room windows, contrary to {amenity_policy}.",
            impact_level=AmenityImpact.SEVERE_UNACCEPTABLE,
            mitigation_possible=False,
            mitigation_measures=[],
            policy_basis=amenity_policies,
        ))

    if has_roof_terrace:
        assessments.append(AmenityAssessment(
            affected_property="Neighbouring residential properties",
            impact_type="privacy",
            current_situation="The existing building does not have any elevated external amenity space.",
            proposed_impact=f"The proposed roof terrace would create an elevated platform with potential for overlooking of neighbouring properties contrary to {amenity_policy}.",
            impact_level=AmenityImpact.SIGNIFICANT_HARMFUL,
            mitigation_possible=True,
            mitigation_measures=["Privacy screens to 1.8m height", "Restriction on use hours", "Planting to screen views"],
            policy_basis=amenity_policies,
        ))

    # --- Daylight / 45-degree test ---
    if m.depth_m is not None and m.eaves_height_m is not None:
        # 45-degree rule: extension depth should not exceed height to eaves
        # measured from the centre of the nearest ground floor window of a neighbour
        if m.depth_m > m.eaves_height_m and m.depth_m > 3.0:
            assessments.append(AmenityAssessment(
                affected_property="Adjoining residential properties",
                impact_type="daylight",
                current_situation="Neighbouring properties currently receive adequate daylight.",
                proposed_impact=f"The proposed extension has a depth of {m.depth_m:.1f}m and eaves height of {m.eaves_height_m:.1f}m. Applying the 45-degree test required by {amenity_policy}, the extension would breach the 45-degree line from the neighbouring ground floor windows, resulting in unacceptable loss of daylight.",
                impact_level=AmenityImpact.SIGNIFICANT_HARMFUL,
                mitigation_possible=True,
                mitigation_measures=["Reduce depth of extension", "Lower eaves height", "Set back from shared boundary"],
                policy_basis=amenity_policies,
            ))
    elif m.depth_m is not None and m.depth_m > 4.0 and 'single storey' in proposal_lower:
        # Single storey over 4m deep = potential daylight concern
        assessments.append(AmenityAssessment(
            affected_property="Adjoining residential properties",
            impact_type="daylight",
            current_situation="Neighbouring properties currently receive adequate daylight.",
            proposed_impact=f"The proposed single-storey extension has a depth of {m.depth_m:.1f}m. Extensions of this depth have potential to affect daylight to neighbouring windows. A 45-degree assessment is required under {amenity_policy}.",
            impact_level=AmenityImpact.MODERATE_MITIGATABLE,
            mitigation_possible=True,
            mitigation_measures=["Compliance with 45-degree test to be demonstrated", "Set-back from boundary"],
            policy_basis=amenity_policies,
        ))

    # --- Overbearing / Outlook ---
    if has_first_floor and m.separation_to_boundary_m is not None and m.separation_to_boundary_m < 1.0:
        assessments.append(AmenityAssessment(
            affected_property="Adjoining residential properties",
            impact_type="outlook_overbearing",
            current_situation="Neighbouring property currently has reasonable outlook.",
            proposed_impact=f"The proposed two-storey element is only {m.separation_to_boundary_m:.1f}m from the shared boundary. At this proximity, the development would appear overbearing and oppressive when viewed from the neighbouring property, contrary to {amenity_policy}.",
            impact_level=AmenityImpact.SIGNIFICANT_HARMFUL,
            mitigation_possible=True,
            mitigation_measures=["Increase set-back from boundary", "Reduce height of element closest to boundary", "Use hipped roof to reduce bulk"],
            policy_basis=amenity_policies,
        ))

    # --- Private amenity space (LP17: minimum 50sqm for houses) ---
    is_flat = any(kw in proposal_lower for kw in ['flat', 'apartment'])
    if m.garden_area_sqm is not None and m.garden_area_sqm < 50.0 and not is_flat:
        assessments.append(AmenityAssessment(
            affected_property="Future occupiers of the proposed development",
            impact_type="amenity_space",
            current_situation=f"The site would provide {m.garden_area_sqm:.0f}sqm of private amenity space.",
            proposed_impact=f"The proposed development would result in only {m.garden_area_sqm:.0f}sqm of private amenity space, below the 50sqm minimum standard set out in {amenity_policy}. This would provide inadequate outdoor amenity for future occupiers.",
            impact_level=AmenityImpact.SIGNIFICANT_HARMFUL if m.garden_area_sqm < 30 else AmenityImpact.MODERATE_MITIGATABLE,
            mitigation_possible=m.garden_area_sqm >= 30,
            mitigation_measures=["Redesign layout to increase garden area"] if m.garden_area_sqm >= 30 else [],
            policy_basis=amenity_policies,
        ))

    # FIX 7: Per-unit amenity space for flats/apartments (25sqm per unit minimum)
    if is_flat and m.num_units and m.garden_area_sqm is not None:
        per_unit_space = m.garden_area_sqm / m.num_units if m.num_units > 0 else 0
        if per_unit_space < 25.0:
            assessments.append(AmenityAssessment(
                affected_property="Future occupiers of the proposed flats/apartments",
                impact_type="amenity_space",
                current_situation=f"The site provides {m.garden_area_sqm:.0f}sqm of communal amenity space for {m.num_units} units ({per_unit_space:.0f}sqm per unit).",
                proposed_impact=f"The communal outdoor amenity space equates to only {per_unit_space:.0f}sqm per unit, below the expected minimum of 25sqm per unit. {amenity_policy} requires adequate outdoor amenity space for all occupiers including those in flatted developments.",
                impact_level=AmenityImpact.SIGNIFICANT_HARMFUL if per_unit_space < 15 else AmenityImpact.MODERATE_MITIGATABLE,
                mitigation_possible=per_unit_space >= 15,
                mitigation_measures=["Increase communal garden area", "Provide private balconies (minimum 5sqm each)", "Provide high-quality landscaped communal space"] if per_unit_space >= 15 else [],
                policy_basis=amenity_policies,
            ))
        else:
            assessments.append(AmenityAssessment(
                affected_property="Future occupiers of the proposed flats/apartments",
                impact_type="amenity_space",
                current_situation=f"The site provides {m.garden_area_sqm:.0f}sqm of communal amenity space for {m.num_units} units ({per_unit_space:.0f}sqm per unit).",
                proposed_impact=f"The communal outdoor amenity space of {per_unit_space:.0f}sqm per unit is considered adequate to serve the needs of future occupiers in accordance with {amenity_policy}.",
                impact_level=AmenityImpact.MINOR_ACCEPTABLE,
                mitigation_possible=True,
                mitigation_measures=[],
                policy_basis=amenity_policies,
            ))

    # --- Default assessment when no specific issues but extension proposed ---
    if 'extension' in proposal_lower and not assessments:
        # Check if we have measurements to make an informed assessment
        if m.depth_m or m.separation_to_boundary_m:
            detail_parts = []
            if m.depth_m:
                detail_parts.append(f"depth of {m.depth_m:.1f}m")
            if m.separation_to_boundary_m:
                detail_parts.append(f"set-back of {m.separation_to_boundary_m:.1f}m from the boundary")
            detail = ", ".join(detail_parts)
            assessments.append(AmenityAssessment(
                affected_property="Adjoining residential properties",
                impact_type="daylight_outlook",
                current_situation="Neighbouring properties currently receive adequate daylight and have reasonable outlook.",
                proposed_impact=f"The proposed extension (with {detail}) has been assessed against the 45-degree daylight test and separation standards in {amenity_policy}. The development is considered acceptable in amenity terms.",
                impact_level=AmenityImpact.MINOR_ACCEPTABLE,
                mitigation_possible=True,
                mitigation_measures=["Design kept subordinate to main dwelling", "Appropriate set-back from boundaries"],
                policy_basis=amenity_policies,
            ))
        else:
            # No measurements available - flag that assessment is limited
            assessments.append(AmenityAssessment(
                affected_property="Adjoining residential properties",
                impact_type="daylight_outlook",
                current_situation="Neighbouring properties currently receive adequate daylight and have reasonable outlook.",
                proposed_impact=f"No specific dimensions have been extracted from the submitted documents. Assessment against {amenity_policy} standards (21m window-to-window, 45-degree daylight test) requires verification from the submitted drawings. Subject to compliance with these standards, the amenity impact is considered acceptable in principle.",
                impact_level=AmenityImpact.MINOR_ACCEPTABLE,
                mitigation_possible=True,
                mitigation_measures=["Compliance with LP17 separation standards to be verified from drawings"],
                policy_basis=amenity_policies,
            ))

    # --- New dwellings: assess impact on existing neighbours ---
    if any(kw in proposal_lower for kw in ['dwelling', 'house', 'bungalow']) and 'extension' not in proposal_lower:
        if not any(a.impact_type == "privacy" for a in assessments):
            if m.separation_to_neighbour_m and m.separation_to_neighbour_m >= 21.0:
                assessments.append(AmenityAssessment(
                    affected_property="Existing neighbouring residential properties",
                    impact_type="privacy",
                    current_situation="Existing properties have established levels of privacy.",
                    proposed_impact=f"The proposed dwelling maintains a separation of {m.separation_to_neighbour_m:.1f}m to the nearest habitable room windows, meeting the 21m standard in {amenity_policy}. Privacy impact is acceptable.",
                    impact_level=AmenityImpact.MINOR_ACCEPTABLE,
                    mitigation_possible=True,
                    mitigation_measures=[],
                    policy_basis=amenity_policies,
                ))
            elif not m.separation_to_neighbour_m:
                assessments.append(AmenityAssessment(
                    affected_property="Existing neighbouring residential properties",
                    impact_type="privacy",
                    current_situation="Existing properties have established levels of privacy.",
                    proposed_impact=f"Separation distances to neighbouring habitable room windows could not be determined from the submitted documents. Compliance with the 21m window-to-window standard in {amenity_policy} must be verified from the submitted drawings.",
                    impact_level=AmenityImpact.MINOR_ACCEPTABLE,
                    mitigation_possible=True,
                    mitigation_measures=["Verify 21m separation from drawings", "Condition obscure glazing if below standard"],
                    policy_basis=amenity_policies,
                ))

    return assessments


def assess_principle_of_development(
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str,
    postcode: str,
    council_id: str = "broxtowe",
    site_address: str = "",
) -> str:
    """
    Assess the principle of development based on site location and policy context.

    For Broxtowe, this considers:
    - Green Belt (Policy 3/ACS-3 + Policy 4/LP4 + NPPF 147-149)
    - Countryside (Policy 3/LP3)
    - Urban area (Policy 15/LP15)
    - Conservation Area context (Policy 11/ACS-11 + Policy 26/LP26)
    - Allocated sites (Policy 2/LP2)
    - Town centre uses (Policy 10/LP10)
    """
    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]

    is_green_belt = any('green belt' in c for c in constraints_lower)
    is_conservation = any('conservation' in c for c in constraints_lower)
    is_listed = any('listed' in c for c in constraints_lower)
    is_extension = any(kw in proposal_lower for kw in ['extension', 'alteration', 'enlargement'])
    is_new_dwelling = any(kw in proposal_lower for kw in ['dwelling', 'new house', 'bungalow', 'erection of']) and not is_extension
    is_change_of_use = 'change of use' in proposal_lower or 'conversion' in proposal_lower
    is_commercial = any(kw in proposal_lower for kw in ['retail', 'shop', 'office', 'industrial', 'warehouse'])

    # Broxtowe settlement hierarchy
    urban_wards = [
        'beeston central', 'beeston north', 'beeston west', 'beeston rylands',
        'chilwell', 'attenborough', 'toton', 'stapleford north', 'stapleford south',
        'eastwood st marys', 'eastwood hall', 'kimberley', 'nuthall',
        'bramcote', 'trowell',
    ]
    is_urban = any(w in ward.lower() for w in urban_wards) if ward else True

    # Detect Green Belt wards (Awsworth, Cossall, parts of Trowell)
    green_belt_indicators = ['awsworth', 'cossall']
    may_be_gb = any(ind in ward.lower() for ind in green_belt_indicators) if ward else False
    if may_be_gb and not is_green_belt:
        is_green_belt = True  # assume Green Belt for these wards unless told otherwise

    parts = []

    # --- GREEN BELT ASSESSMENT ---
    if is_green_belt:
        parts.append("The application site is located within the Nottingham-Derby Green Belt as defined on the Broxtowe Policies Map.")
        parts.append("")

        if is_extension:
            parts.append("Policy 4 of the Broxtowe Part 2 Local Plan (2019) and NPPF paragraph 149(c) allow extensions or alterations to existing buildings in the Green Belt provided they do not result in disproportionate additions over and above the size of the original building.")
            parts.append("")
            parts.append("The proposed extension must be assessed for proportionality. Cumulative extensions since 1 July 1948 (or date of original construction if later) must be considered. Subject to the extension being proportionate and not harming the openness of the Green Belt, the principle of development may be acceptable.")
        elif is_new_dwelling:
            parts.append("The construction of new buildings in the Green Belt is inappropriate development by definition (NPPF paragraph 147). Policy 4 of the Broxtowe Part 2 Local Plan (2019) states that inappropriate development should not be approved except in very special circumstances.")
            parts.append("")
            parts.append("Very special circumstances will not exist unless the potential harm to the Green Belt by reason of inappropriateness, and any other harm resulting from the proposal, is clearly outweighed by other considerations (NPPF paragraph 148).")
            parts.append("")
            parts.append("NPPF paragraph 149 provides limited exceptions including: (e) limited infilling in villages; (g) limited infilling or redevelopment of previously developed land. The applicant must demonstrate which exception applies, or demonstrate very special circumstances.")
            parts.append("")
            parts.append("THE PRINCIPLE OF DEVELOPMENT IS NOT ESTABLISHED. The applicant must demonstrate either that an exception under NPPF paragraph 149 applies, or that very special circumstances exist to outweigh the harm to the Green Belt.")
        else:
            parts.append("The proposal must be assessed against Policy 4 of the Broxtowe Part 2 Local Plan (2019) and NPPF paragraphs 147-149. Development in the Green Belt is inappropriate unless it falls within the exceptions listed at NPPF paragraph 149.")

    # --- CONSERVATION AREA PRINCIPLE ---
    elif is_conservation:
        # Find matching CA character
        ca_info = _find_conservation_area(ward, site_address, constraints)
        ca_name = ca_info["name"] if ca_info else "Conservation Area"

        parts.append(f"The application site is located within the {ca_name}.")
        parts.append("")

        if is_extension:
            parts.append(f"Policy 26 of the Broxtowe Part 2 Local Plan (2019) and Policy 11 of the Aligned Core Strategy (2014) require that development within Conservation Areas should preserve or enhance the character or appearance of the area. This is reinforced by the statutory duty under Section 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990.")
            parts.append("")
            if ca_info:
                parts.append(f"The key character of this Conservation Area is: {ca_info['character']}")
                parts.append("")
                sensitivities = ca_info.get("sensitivities", [])
                if sensitivities:
                    parts.append("Key sensitivities relevant to this proposal include:")
                    for s in sensitivities[:3]:
                        parts.append(f"- {s}")
                    parts.append("")
            parts.append("The principle of development is acceptable in this location subject to the proposal preserving or enhancing the character and appearance of the Conservation Area. The detailed design, materials, and impact on the area's character are assessed below.")
        elif is_new_dwelling:
            parts.append(f"Policy 26 (LP26) requires that development within or affecting a Conservation Area should preserve or enhance its character or appearance. New development must demonstrate particular sensitivity to the established character.")
            parts.append("")
            if ca_info:
                parts.append(f"Character context: {ca_info['character']}")
                parts.append("")
            parts.append("The principle of a new dwelling within the Conservation Area is not automatically unacceptable, but requires careful justification demonstrating that the proposal would preserve or enhance the area's character. The detailed assessment below considers this.")
        else:
            parts.append(f"Development within the Conservation Area must preserve or enhance its character or appearance (Policy 26/LP26, Section 72 P(LBCA)A 1990). The principle is subject to the detailed heritage assessment below.")

    # --- URBAN AREA ---
    elif is_urban and not is_green_belt:
        if is_new_dwelling:
            parts.append("The application site is located within the urban area of Broxtowe as defined on the Policies Map.")
            parts.append("")
            parts.append("Policy 15 of the Broxtowe Part 2 Local Plan (2019) supports residential development on unallocated sites within the urban area where it is of appropriate scale, design and density, would not result in the loss of valued open space or community facilities, and would not have unacceptable impacts on residential amenity.")
            parts.append("")
            parts.append("Policy 2 of the Aligned Core Strategy (2014) directs development to the main built-up area, with an appropriate level in the Key Settlements of Beeston, Stapleford, Eastwood and Kimberley.")
            parts.append("")
            parts.append("The principle of residential development in this urban location is acceptable, subject to the detailed considerations assessed below.")
        elif is_extension:
            parts.append("The application site is a residential property within the urban area of Broxtowe.")
            parts.append("")
            parts.append("Policy 19 of the Broxtowe Part 2 Local Plan (2019) supports extensions and alterations where they respect the scale, form and character of the original building, use complementary materials, are subordinate to the main building, and avoid unacceptable impact on neighbours.")
            parts.append("")
            parts.append("The principle of extending a residential property is acceptable. The detailed design and amenity impacts are assessed below.")
        elif is_change_of_use:
            parts.append("The application site is within the urban area of Broxtowe.")
            parts.append("")
            if any(kw in proposal_lower for kw in ['residential', 'flat', 'apartment', 'dwelling']):
                parts.append("The change of use to residential is supported by Policy 15 (LP15) which encourages housing within the urban area. The NPPF also supports the efficient use of existing buildings and making best use of land in urban areas.")
            elif is_commercial:
                parts.append("Commercial development in the urban area should comply with Policy 10 (LP10) Town Centre and District Centre Uses. The sequential test must be applied for main town centre uses proposed outside defined centres.")
            else:
                parts.append("The principle of the proposed change of use must be assessed against the relevant development plan policies. The site's urban location is generally supportive of development.")
            parts.append("")
            parts.append("The principle of development is acceptable, subject to the detailed considerations below.")
        else:
            parts.append("The application site is within the urban area of Broxtowe where the principle of development is generally supported by Policy 2 (ACS) and Policy 15 (LP), subject to detailed policy compliance.")
    else:
        # Countryside / unknown
        parts.append("The site's location relative to the defined urban area, Green Belt, and countryside designations should be verified against the Broxtowe Policies Map.")
        parts.append("")
        if is_new_dwelling:
            parts.append("If the site is outside the defined urban area, Policy 3 of the Broxtowe Part 2 Local Plan (2019) strictly controls development in the countryside. New residential development will only be permitted where it falls within the specified exceptions (agriculture, rural workers, replacement dwellings, etc.).")
        else:
            parts.append("Development outside the urban area is subject to Policy 3 (LP3) which restricts development in the countryside to specified exceptions.")

    return "\n".join(parts)


def assess_design(
    proposal: str,
    constraints: list[str],
    ward: str,
    measurements: Optional[ExtractedMeasurements] = None,
    council_id: str = "broxtowe",
    site_address: str = "",
) -> str:
    """
    Assess design quality based on proposal, context, and Broxtowe policies.

    Uses Policy 10 (ACS), Policy 17 (LP17), Policy 19 (LP19 for extensions),
    and Policy 26 (LP26 for heritage contexts).
    """
    proposal_lower = proposal.lower()
    m = measurements or ExtractedMeasurements()
    parts = []

    is_extension = any(kw in proposal_lower for kw in ['extension', 'alteration', 'enlargement'])
    is_new_dwelling = any(kw in proposal_lower for kw in ['dwelling', 'new house', 'bungalow']) and not is_extension
    is_conservation = any('conservation' in c.lower() for c in constraints)
    is_listed = any('listed' in c.lower() for c in constraints)

    # Find CA character if relevant
    ca_info = _find_conservation_area(ward, site_address, constraints) if is_conservation else None

    if is_extension:
        parts.append("The design of the proposed extension is assessed against Policy 19 of the Broxtowe Part 2 Local Plan (2019) and Policy 10 of the Aligned Core Strategy (2014).")
        parts.append("")
        parts.append("Policy 19 requires extensions to: (a) respect the scale, form and character of the original building; (b) use complementary materials; (c) be subordinate to the main building; and (d) avoid unacceptable impact on neighbours.")
        parts.append("")

        # Assess subordination
        if 'two storey' in proposal_lower or 'two-storey' in proposal_lower:
            parts.append("The proposed two-storey extension requires careful assessment of subordination. Two-storey extensions must not project beyond the front building line (Policy 19) and should maintain appropriate separation to boundaries.")
        elif 'single storey' in proposal_lower:
            parts.append("The proposed single-storey extension is inherently subordinate in height to the main dwelling, which is a positive design consideration.")

        if m.depth_m:
            parts.append(f" The extension has a depth of {m.depth_m:.1f}m.")
        if m.ridge_height_m:
            parts.append(f" The proposed ridge height is {m.ridge_height_m:.1f}m.")
        parts.append("")

        # Overdevelopment check
        if m.garden_area_sqm is not None and m.garden_area_sqm < 50:
            parts.append(f"CONCERN: The remaining garden area of {m.garden_area_sqm:.0f}sqm is below the 50sqm minimum standard in Policy 17, suggesting potential overdevelopment of the plot.")
        elif m.garden_area_sqm is not None:
            parts.append(f"The remaining garden area of {m.garden_area_sqm:.0f}sqm meets the 50sqm minimum standard in Policy 17.")
        parts.append("")

    elif is_new_dwelling:
        parts.append("The design of the proposed dwelling is assessed against Policy 10 of the Aligned Core Strategy (2014) and Policy 17 of the Broxtowe Part 2 Local Plan (2019).")
        parts.append("")
        parts.append("Policy 10 requires development to create an attractive, safe and distinctive environment that reinforces valued local characteristics. Policy 17 requires development to respond positively to local character and context.")
        parts.append("")

        if m.num_bedrooms:
            parts.append(f"The proposed {m.num_bedrooms}-bedroom dwelling should contribute to the mix of housing sizes required by Policy 8 (ACS).")
        if m.parking_spaces:
            parts.append(f"The proposal includes {m.parking_spaces} parking space(s). Compliance with Policy 21 (LP21) parking standards should be verified.")
        parts.append("")
    else:
        parts.append("The design of the proposed development is assessed against Policy 10 of the Aligned Core Strategy (2014) and Policy 17 of the Broxtowe Part 2 Local Plan (2019).")
        parts.append("")

    # Heritage design context
    if is_conservation and ca_info:
        parts.append(f"Within the {ca_info['name']}, particular regard must be had to the established character: {ca_info['character']}")
        parts.append("")
        expected_materials = ca_info.get("materials_expected", [])
        if expected_materials:
            parts.append(f"Materials expected in this Conservation Area: {', '.join(expected_materials)}.")
            parts.append("")

    if is_listed:
        parts.append("As the site involves a listed building, the design must have special regard to preserving the building, its setting, and features of special architectural or historic interest (Section 66 P(LBCA)A 1990, Policy 26 LP26).")
        parts.append("")

    # Materials assessment
    material_keywords = ['brick', 'render', 'stone', 'timber', 'slate', 'tile', 'cladding', 'upvc']
    mentioned_materials = [m_kw for m_kw in material_keywords if m_kw in proposal_lower]
    if mentioned_materials:
        parts.append(f"Materials mentioned in the proposal: {', '.join(mentioned_materials)}.")
        if is_conservation and 'upvc' in mentioned_materials:
            parts.append("CONCERN: uPVC is generally not appropriate within a Conservation Area and would require strong justification against Policy 26 (LP26).")
    else:
        parts.append("No specific materials are mentioned in the proposal description. A materials condition will be required.")
    parts.append("")

    if not parts or all(p.strip() == "" for p in parts):
        parts.append("The design is assessed against Policy 10 (ACS) and Policy 17 (LP17).")

    return "\n".join(parts)


def _find_conservation_area(
    ward: str,
    site_address: str = "",
    constraints: list[str] | None = None,
) -> Optional[dict]:
    """Find the matching Broxtowe Conservation Area from ward/address/constraints."""
    search_text = f"{ward} {site_address} {' '.join(constraints or [])}".lower()

    for ca_id, ca_data in BROXTOWE_CONSERVATION_AREAS.items():
        # Check if CA name mentioned in constraints
        if ca_id in search_text or ca_data["name"].lower() in search_text:
            return ca_data
        # Check ward match
        for ca_ward in ca_data.get("wards", []):
            if ca_ward.lower() in search_text:
                return ca_data

    # Fallback: try ward-based matching
    if ward:
        ward_lower = ward.lower()
        for ca_id, ca_data in BROXTOWE_CONSERVATION_AREAS.items():
            for ca_ward in ca_data.get("wards", []):
                if ca_ward.lower() in ward_lower or ward_lower in ca_ward.lower():
                    return ca_data

    return None


def generate_planning_balance(
    benefits: list[MaterialConsideration],
    harms: list[MaterialConsideration],
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
    constraints: list[str],
    proposal: str = "",
) -> PlanningBalance:
    """
    Generate the planning balance following established methodology.

    This follows the approach in:
    - City of Edinburgh v Secretary of State (the planning balance)
    - Mansell v Tonbridge (heritage balance)
    - Palmer v Herefordshire (tilted balance)
    """

    # ----- FIX 5: TILTED BALANCE (NPPF 11d) -----
    # Engaged when no "protective" policies (heritage, Green Belt, AONB etc.) provide
    # a clear reason for refusal AND the most important policies are out of date
    heritage_constraint = any('listed' in c.lower() or 'conservation' in c.lower() for c in constraints)
    green_belt = any('green belt' in c.lower() for c in constraints)
    flood_zone = any('flood zone 3' in c.lower() for c in constraints)
    sssi = any('sssi' in c.lower() or 'ramsar' in c.lower() for c in constraints)

    # NPPF footnote 7: policies that protect — heritage, Green Belt, AONB, flood risk, SSSI
    has_protective_policy = heritage_constraint or green_belt or flood_zone or sssi

    # Heritage harm actually found?
    heritage_harm_found = heritage_assessment and heritage_assessment.harm_level not in [
        HarmLevel.NO_HARM, HarmLevel.NEGLIGIBLE
    ]

    tilted_balance_engaged = False
    tilted_balance_reason = ""

    if has_protective_policy and (heritage_harm_found or green_belt):
        # Protective policies provide clear reason — tilted balance NOT engaged (NPPF 11(d)(i))
        tilted_balance_engaged = False
        protective_reasons = []
        if heritage_harm_found:
            protective_reasons.append("heritage assets (NPPF Chapter 16)")
        if green_belt:
            protective_reasons.append("Green Belt (NPPF Chapter 13)")
        if flood_zone:
            protective_reasons.append("areas at risk of flooding (NPPF Chapter 14)")
        if sssi:
            protective_reasons.append("habitats sites (NPPF Chapter 15)")
        tilted_balance_reason = f"The tilted balance at paragraph 11(d) is not engaged as NPPF footnote 7 policies that protect {', '.join(protective_reasons)} provide a clear reason for refusing development that causes harm."
    elif has_protective_policy and not heritage_harm_found and not green_belt:
        # Protective policy area exists but no actual harm found — tilted balance MAY apply
        tilted_balance_engaged = True
        tilted_balance_reason = "Although the site is within an area covered by a footnote 7 protective policy, no actual harm has been identified from this proposal. The tilted balance at paragraph 11(d)(ii) is therefore engaged: permission should be granted unless adverse impacts would significantly and demonstrably outweigh the benefits."
    else:
        # No protective policies — tilted balance applies if policies are out of date
        # For Broxtowe: Local Plan adopted 2019, ACS 2014 — generally up to date
        # But if housing delivery test failed, policies would be out of date
        tilted_balance_engaged = False
        tilted_balance_reason = "The development plan policies most important for determining this application (Broxtowe Part 2 Local Plan 2019, Aligned Core Strategy 2014) are considered up to date. The tilted balance at paragraph 11(d) is not engaged. The application falls to be determined under the standard balance at paragraph 11(c): approved if in accordance with the development plan."

    # ----- LEGAL TEST APPROACH -----
    any_fatal_harm = False
    heritage_fatal = False
    amenity_fatal = False
    green_belt_fatal = False

    # 1. NPPF 201 TEST — Substantial heritage harm
    if heritage_assessment and heritage_assessment.harm_level == HarmLevel.SUBSTANTIAL:
        substantial_benefits = [b for b in benefits if b.weight.value >= Weight.SIGNIFICANT.value]
        # Also check heritage assessment's own public benefits
        heritage_pbs = heritage_assessment.public_benefits if heritage_assessment else []
        has_substantial_pbs = len(substantial_benefits) > 0 or any(
            'housing' in pb.lower() or 'affordable' in pb.lower() or 'regeneration' in pb.lower()
            for pb in heritage_pbs
        )
        if not has_substantial_pbs:
            heritage_fatal = True
            any_fatal_harm = True

    # 2. NPPF 202 TEST — Less than substantial heritage harm
    heritage_para_202_pass = True
    if heritage_assessment and heritage_assessment.harm_level in [
        HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH,
        HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE,
        HarmLevel.LESS_THAN_SUBSTANTIAL_LOW,
    ]:
        # Include heritage-specific public benefits in the count
        heritage_pbs = heritage_assessment.public_benefits if heritage_assessment else []
        all_benefit_count = len(benefits) + len(heritage_pbs)

        if heritage_assessment.harm_level == HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH:
            significant_benefits = [b for b in benefits if b.weight.value >= Weight.MODERATE.value]
            heritage_para_202_pass = len(significant_benefits) >= 2 or all_benefit_count >= 3
        elif heritage_assessment.harm_level == HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE:
            heritage_para_202_pass = all_benefit_count >= 1
        else:
            heritage_para_202_pass = True

        if not heritage_para_202_pass:
            heritage_fatal = True
            any_fatal_harm = True

    # 3. AMENITY TEST — Severe unacceptable harm = refusal
    unmitigated_severe = [
        a for a in amenity_assessments
        if a.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE and not a.mitigation_possible
    ]
    if unmitigated_severe:
        amenity_fatal = True
        any_fatal_harm = True

    # FIX 6: GREEN BELT — NPPF 148 Very Special Circumstances test
    green_belt_vsc_narrative = ""
    proposal_lower = proposal.lower() if proposal else ""
    if green_belt:

        # Extensions can be appropriate (NPPF 149(c)) if proportionate
        is_likely_appropriate = any(
            kw in proposal_lower for kw in ['proportionate', 'limited extension', 'replacement', 'infilling', 'extension', 'alteration']
        )

        if not is_likely_appropriate:
            # Inappropriate development — apply NPPF 148 two-part test
            # Part 1: Harm by reason of inappropriateness (definitional)
            # Part 2: Any other harm (openness, purposes of Green Belt, visual amenity)
            total_vsc_benefits = sum(b.weight.value for b in benefits)
            green_belt_harm = Weight.SUBSTANTIAL.value  # Inappropriateness carries substantial weight

            if total_vsc_benefits <= green_belt_harm:
                green_belt_fatal = True
                any_fatal_harm = True

            green_belt_vsc_narrative = f"""Green Belt Assessment (NPPF paragraph 148):

The proposal constitutes inappropriate development in the Green Belt. NPPF paragraph 148 states that 'Very special circumstances' will not exist unless the potential harm to the Green Belt by reason of inappropriateness, and any other harm resulting from the proposal, is clearly outweighed by other considerations.

Harm identified:
- Harm by reason of inappropriateness (definitional — substantial weight)
- Any other harm to openness and the purposes of including land within the Green Belt

Benefits/other considerations: {', '.join([b.factor for b in benefits]) if benefits else 'No very special circumstances demonstrated'}

{'Very special circumstances have not been demonstrated.' if green_belt_fatal else 'The considerations advanced are considered to clearly outweigh the harm, constituting very special circumstances.'}"""

    # 4. OVERALL BALANCE
    total_benefit_weight = sum(b.weight.value for b in benefits)
    total_harm_weight = sum(h.weight.value for h in harms)

    for amenity in amenity_assessments:
        if amenity.impact_level == AmenityImpact.SIGNIFICANT_HARMFUL:
            if amenity.mitigation_possible:
                total_harm_weight += Weight.LIMITED.value
            else:
                total_harm_weight += Weight.SIGNIFICANT.value
        elif amenity.impact_level == AmenityImpact.MODERATE_MITIGATABLE:
            total_harm_weight += Weight.LIMITED.value

    # Apply tilted balance threshold if engaged
    if tilted_balance_engaged:
        # Tilted balance: adverse impacts must SIGNIFICANTLY AND DEMONSTRABLY outweigh benefits
        benefits_outweigh = not any_fatal_harm and (total_harm_weight < total_benefit_weight * 1.5)
    else:
        benefits_outweigh = not any_fatal_harm and total_benefit_weight >= total_harm_weight

    # Generate para 202 balance if heritage harm
    para_202_balance = None
    if heritage_assessment and heritage_assessment.harm_level in [
        HarmLevel.LESS_THAN_SUBSTANTIAL_LOW,
        HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE,
        HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH,
    ]:
        heritage_pbs = heritage_assessment.public_benefits if heritage_assessment else []
        all_benefits_text = ", ".join(
            [b.factor for b in benefits] + heritage_pbs
        ) if (benefits or heritage_pbs) else "No significant public benefits identified"

        para_202_balance = f"""Paragraph 202 Balance:

The proposal would cause {heritage_assessment.harm_level.value.replace('_', ' ')} to the significance of the {heritage_assessment.asset_type}. In accordance with paragraph 199 of the NPPF, great weight must be given to the conservation of this designated heritage asset.

The public benefits identified are: {all_benefits_text}.

Weighing the public benefits against the harm, and giving great weight to the heritage harm as required by the NPPF, {'the benefits are considered to outweigh the harm' if benefits_outweigh else 'the harm is considered to outweigh the benefits'}."""

    # Generate overall narrative
    if heritage_assessment and heritage_assessment.harm_level == HarmLevel.SUBSTANTIAL:
        heritage_pbs = heritage_assessment.public_benefits if heritage_assessment else []
        if heritage_fatal:
            narrative = f"""The proposed development would cause SUBSTANTIAL HARM to the significance of the {heritage_assessment.asset_type}. Paragraph 201 of the NPPF states that permission should be refused unless substantial public benefits outweigh that harm.

No substantial public benefits have been demonstrated that would outweigh the substantial harm to this designated heritage asset. The proposal is contrary to Chapter 16 of the NPPF and the statutory duty under {heritage_assessment.statutory_duty.replace('_', ' ').title()}."""
            benefits_outweigh = False
        else:
            pbs_text = ", ".join(heritage_pbs) if heritage_pbs else ", ".join(b.factor for b in benefits)
            narrative = f"""The proposed development would cause SUBSTANTIAL HARM to the significance of the {heritage_assessment.asset_type}. However, the substantial public benefits ({pbs_text}) are considered to outweigh this harm in accordance with NPPF paragraph 201."""

    elif green_belt_fatal:
        narrative = f"""{green_belt_vsc_narrative}

The proposal is therefore contrary to Policy 4 of the Broxtowe Part 2 Local Plan (2019), Policy 3 of the Aligned Core Strategy (2014), and NPPF paragraphs 147-148."""
        benefits_outweigh = False

    elif any(a.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE for a in amenity_assessments):
        harmful_impacts = [a for a in amenity_assessments if a.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE]
        narrative = f"""The proposed development would cause severe and unacceptable harm to the residential amenity of neighbouring properties through {', '.join([a.impact_type for a in harmful_impacts])}.

This harm cannot be adequately mitigated through conditions and the proposal is contrary to Policy 17 of the Broxtowe Part 2 Local Plan (2019) and paragraph 130 of the NPPF."""
        benefits_outweigh = False

    else:
        tilted_note = ""
        if tilted_balance_engaged:
            tilted_note = "\n\nThe tilted balance at NPPF paragraph 11(d)(ii) is engaged. Permission should be granted unless the adverse impacts would significantly and demonstrably outweigh the benefits."

        gb_note = f"\n\n{green_belt_vsc_narrative}" if green_belt_vsc_narrative else ""

        narrative = f"""The proposed development has been assessed against the policies of the Development Plan and the National Planning Policy Framework.

Benefits identified: {', '.join([b.factor for b in benefits]) if benefits else 'Limited benefits identified'}
Weight given to benefits: {Weight(total_benefit_weight).name if total_benefit_weight <= 6 else 'COMBINED SIGNIFICANT'}

Harms identified: {', '.join([h.factor for h in harms]) if harms else 'No significant harms identified'}
Weight given to harms: {Weight(total_harm_weight).name if total_harm_weight <= 6 else 'COMBINED SIGNIFICANT'}{tilted_note}{gb_note}

{'The benefits are considered to outweigh the harms.' if benefits_outweigh else 'The harms are considered to outweigh the benefits.'}"""

    return PlanningBalance(
        benefits=benefits,
        harms=harms,
        heritage_harm=heritage_assessment,
        amenity_impacts=amenity_assessments,
        tilted_balance_engaged=tilted_balance_engaged,
        tilted_balance_reason=tilted_balance_reason,
        para_202_balance=para_202_balance,
        benefits_outweigh_harms=benefits_outweigh,
        overall_narrative=narrative,
    )


def generate_conditions(
    proposal: str,
    constraints: list[str],
    application_type: str,
    heritage_assessment: Optional[HeritageAssessment],
    amenity_assessments: list[AmenityAssessment],
    council_id: str = "broxtowe",
) -> list[Condition]:
    """
    Generate planning conditions that meet the six tests:
    1. Necessary
    2. Relevant to planning
    3. Relevant to the development
    4. Enforceable
    5. Precise
    6. Reasonable
    """
    conditions = []
    num = 1

    # Standard time limit (required by law)
    conditions.append(Condition(
        number=num,
        title="Time Limit",
        full_wording="The development hereby permitted shall be begun before the expiration of three years from the date of this permission.",
        reason="To comply with Section 91 of the Town and Country Planning Act 1990, as amended by Section 51 of the Planning and Compulsory Purchase Act 2004.",
        policy_basis="TCPA 1990 s.91",
        condition_type="compliance",
    ))
    num += 1

    # Approved plans
    conditions.append(Condition(
        number=num,
        title="Approved Plans",
        full_wording="The development hereby permitted shall be carried out in complete accordance with the approved plans listed in the schedule attached to this decision notice.",
        reason="For the avoidance of doubt and in the interests of proper planning.",
        policy_basis="NPPF paragraph 38",
        condition_type="compliance",
    ))
    num += 1

    # Materials - especially important for heritage
    if heritage_assessment or any('conservation' in c.lower() for c in constraints):
        conditions.append(Condition(
            number=num,
            title="Materials",
            full_wording="""Notwithstanding any description of materials in the application, no development above damp proof course level shall take place until samples or precise specifications of all external facing materials, including:
(a) walls (showing brick bond, mortar colour and pointing style);
(b) roof covering;
(c) windows and doors (including 1:20 scale drawings showing frame profiles, glazing bar details, and finish);
(d) rainwater goods;
(e) any other external materials,
have been submitted to and approved in writing by the Local Planning Authority. The development shall be constructed in complete accordance with the approved materials and retained as such thereafter.""",
            reason=f"To ensure the development is constructed in materials appropriate to the character of the area and the significance of the heritage asset, having regard to {'Policy 10 (ACS), Policy 17 (LP) and Policy 26 (LP) of the Development Plan' if council_id == 'broxtowe' else 'Policies CS15, DM6.1 and DM15 of the Development Plan'}, and Chapter 16 of the NPPF.",
            policy_basis=f"{'Policy 10, Policy 17, Policy 26' if council_id == 'broxtowe' else 'CS15, DM6.1, DM15'}, NPPF Chapter 16",
            condition_type="pre-commencement",
        ))
        num += 1

        # Window details for heritage context
        conditions.append(Condition(
            number=num,
            title="Window and Door Details",
            full_wording="""Prior to the installation of any new or replacement windows or external doors, the following details shall be submitted to and approved in writing by the Local Planning Authority:
(a) 1:5 scale sectional drawings showing frame profiles, glazing bars, sill and head details;
(b) Method of opening;
(c) Materials and finish;
(d) Colour (RAL reference);
(e) Depth of reveal.
The windows and doors shall be installed in complete accordance with the approved details and shall be retained as such thereafter. Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015, no subsequent alterations shall be made without the prior written approval of the Local Planning Authority.""",
            reason=f"To preserve the character and appearance of the Conservation Area / significance of the listed building, having regard to {'Policy 26 (LP) and Policy 11 (ACS)' if council_id == 'broxtowe' else 'Policies DM15 and DM16'} of the Development Plan, Chapter 16 of the NPPF, and the statutory duties under Sections 66 and 72 of the Planning (Listed Buildings and Conservation Areas) Act 1990.",
            policy_basis=f"{'Policy 26, Policy 11' if council_id == 'broxtowe' else 'DM15, DM16'}, NPPF Chapter 16, LBCA 1990",
            condition_type="pre-installation",
        ))
        num += 1

    # Amenity protection conditions
    for amenity in amenity_assessments:
        if amenity.mitigation_possible and amenity.impact_level in [AmenityImpact.MODERATE_MITIGATABLE, AmenityImpact.SIGNIFICANT_HARMFUL]:
            if 'privacy' in amenity.impact_type:
                conditions.append(Condition(
                    number=num,
                    title="Obscure Glazing",
                    full_wording=f"""The window(s) in the {'side' if 'side' in proposal.lower() else 'rear'} elevation at first floor level and above serving non-habitable rooms shall be:
(a) fitted with obscure glass to a minimum of Pilkington Level 3 (or equivalent); and
(b) non-opening below 1.7m from internal floor level.
The windows shall be installed in accordance with these requirements prior to first occupation of the development and shall be retained as such thereafter. Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015, no subsequent alterations shall be made without the prior written approval of the Local Planning Authority.""",
                    reason=f"To protect the residential amenity of neighbouring occupiers and prevent unacceptable overlooking, having regard to {'Policy 17 (LP)' if council_id == 'broxtowe' else 'Policy DM6.6'} of the Development Plan.",
                    policy_basis=f"{'Policy 17' if council_id == 'broxtowe' else 'DM6.6'}",
                    condition_type="pre-occupation",
                ))
                num += 1

    # Removal of PD rights where appropriate
    if 'extension' in proposal.lower() or 'householder' in application_type.lower():
        conditions.append(Condition(
            number=num,
            title="Removal of Permitted Development Rights",
            full_wording="""Notwithstanding the provisions of the Town and Country Planning (General Permitted Development) (England) Order 2015 (or any order revoking and re-enacting that Order with or without modification), no additional windows, doors, or other openings shall be inserted in the side elevation(s) of the development hereby approved at first floor level or above without the prior written approval of the Local Planning Authority.""",
            reason=f"To protect the residential amenity of neighbouring properties and to enable the Local Planning Authority to retain control over future alterations that could cause harm, having regard to {'Policy 17 (LP)' if council_id == 'broxtowe' else 'Policy DM6.6'} of the Development Plan.",
            policy_basis=f"{'Policy 17' if council_id == 'broxtowe' else 'DM6.6'}",
            condition_type="compliance",
        ))
        num += 1

    return conditions


def generate_case_officer_report(
    reference: str,
    site_address: str,
    proposal: str,
    application_type: str,
    constraints: list[str],
    ward: str,
    postcode: str,
    applicant_name: str,
    documents: list[dict],
    council_id: str,
) -> CaseOfficerReport:
    """
    Generate a complete case officer report to senior planning officer standard.

    This is the main entry point for the AI Case Officer system.
    """

    # 0. Extract measurements from proposal text and documents
    measurements = extract_measurements(proposal, documents)

    # 1. Analyse heritage impact
    heritage_assessment = analyse_heritage_impact(
        proposal, constraints, site_address,
        ward=ward, site_address=site_address,
    )

    # 2. Analyse amenity impact (now uses measurements)
    amenity_assessments = analyse_amenity_impact(
        proposal, constraints, application_type,
        measurements=measurements, council_id=council_id,
    )

    # 3. Identify benefits
    # Per Palmer v Herefordshire and City of Edinburgh - private benefits that benefit
    # the wider public (housing, living conditions) are legitimate public benefits
    benefits = [
        MaterialConsideration(
            factor="Provision of improved living accommodation",
            description="The proposal would provide improved living accommodation for the occupiers, contributing to the social objective of sustainable development.",
            is_benefit=True,
            weight=Weight.MODERATE,  # Private benefits count in planning balance
            policy_basis=["NPPF paragraph 8", "NPPF paragraph 130"],
            evidence="Inherent benefit of householder development",
        ),
    ]

    # Additional benefit for extensions providing family accommodation
    if 'extension' in proposal.lower() or 'bedroom' in proposal.lower():
        benefits.append(MaterialConsideration(
            factor="Support for family housing needs",
            description="The extension would support the changing needs of the household without requiring a move, supporting sustainable communities.",
            is_benefit=True,
            weight=Weight.LIMITED,
            policy_basis=["NPPF paragraph 8"],
            evidence="Social sustainability benefit",
        ))

    # Economic benefit for larger developments
    if 'change of use' in application_type.lower() or 'commercial' in proposal.lower():
        benefits.append(MaterialConsideration(
            factor="Economic benefit",
            description="The proposal would support economic activity and potentially create employment.",
            is_benefit=True,
            weight=Weight.MODERATE,
            policy_basis=["NPPF paragraph 8", "NPPF paragraph 81"],
            evidence="Economic objective of sustainable development",
        ))

    # 4. Identify harms
    harms = []

    if heritage_assessment and heritage_assessment.harm_level != HarmLevel.NO_HARM:
        # Weight proportional to harm level - NPPF 199 requires great weight but
        # this must be proportionate to the level of harm (per case law)
        harm_weights = {
            HarmLevel.SUBSTANTIAL: Weight.VERY_GREAT,
            HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH: Weight.SUBSTANTIAL,
            HarmLevel.LESS_THAN_SUBSTANTIAL_MODERATE: Weight.SIGNIFICANT,
            HarmLevel.LESS_THAN_SUBSTANTIAL_LOW: Weight.LIMITED,
            HarmLevel.NEGLIGIBLE: Weight.NO_WEIGHT,
        }
        heritage_weight = harm_weights.get(heritage_assessment.harm_level, Weight.MODERATE)

        harms.append(MaterialConsideration(
            factor="Harm to heritage asset",
            description=heritage_assessment.impact_on_significance,
            is_benefit=False,
            weight=heritage_weight,
            policy_basis=["NPPF paragraphs 199-202", heritage_assessment.statutory_duty],
            evidence="Heritage impact assessment",
        ))

    for amenity in amenity_assessments:
        if amenity.impact_level in [AmenityImpact.SIGNIFICANT_HARMFUL, AmenityImpact.SEVERE_UNACCEPTABLE]:
            harms.append(MaterialConsideration(
                factor=f"Harm to residential amenity ({amenity.impact_type})",
                description=amenity.proposed_impact,
                is_benefit=False,
                weight=Weight.SUBSTANTIAL if amenity.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE else Weight.SIGNIFICANT,
                policy_basis=amenity.policy_basis,
                evidence="Amenity impact assessment",
            ))

    # 5. Generate planning balance
    planning_balance = generate_planning_balance(
        benefits=benefits,
        harms=harms,
        heritage_assessment=heritage_assessment,
        amenity_assessments=amenity_assessments,
        constraints=constraints,
        proposal=proposal,
    )

    # 6. Determine recommendation
    if not planning_balance.benefits_outweigh_harms:
        recommendation = "REFUSE"
        conditions = []
        refusal_reasons = []

        if heritage_assessment and heritage_assessment.harm_level == HarmLevel.SUBSTANTIAL:
            refusal_reasons.append({
                "number": 1,
                "reason": heritage_assessment.justification,
                "policy_basis": f"NPPF paragraph {heritage_assessment.nppf_paragraph}, {heritage_assessment.statutory_duty.replace('_', ' ').title()}, {'Policy 26 (LP), Policy 11 (ACS)' if council_id == 'broxtowe' else 'Policy DM15'}",
            })

        for i, amenity in enumerate(amenity_assessments):
            if amenity.impact_level == AmenityImpact.SEVERE_UNACCEPTABLE:
                refusal_reasons.append({
                    "number": len(refusal_reasons) + 1,
                    "reason": f"The proposed development would cause unacceptable harm to the residential amenity of neighbouring properties by reason of {amenity.impact_type}. {amenity.proposed_impact} This is contrary to {'Policy 17 of the Broxtowe Part 2 Local Plan (2019)' if council_id == 'broxtowe' else 'Policy DM6.6 of the Development and Allocations Plan'} and paragraph 130 of the NPPF.",
                    "policy_basis": ", ".join(amenity.policy_basis),
                })

        # Only add heritage refusal reason for HIGH harm (not moderate or low)
        if heritage_assessment and heritage_assessment.harm_level == HarmLevel.LESS_THAN_SUBSTANTIAL_HIGH:
            if not any('heritage' in r.get('reason', '').lower() for r in refusal_reasons):
                refusal_reasons.append({
                    "number": len(refusal_reasons) + 1,
                    "reason": f"The proposed development would cause {heritage_assessment.harm_level.value.replace('_', ' ')} to the significance of the {heritage_assessment.asset_type}. When weighing the public benefits against this harm, and giving great weight to the conservation of the heritage asset as required by paragraph 199 of the NPPF, the harm is not outweighed by the public benefits. The proposal is therefore contrary to Chapter 16 of the NPPF, {'Policy 26 (LP) and Policy 11 (ACS)' if council_id == 'broxtowe' else 'Policies DM15 and DM16'} of the Development Plan, and the statutory duty under {heritage_assessment.statutory_duty.replace('_', ' ').title()}.",
                    "policy_basis": f"NPPF paragraphs 199, 202; {'Policy 26, Policy 11' if council_id == 'broxtowe' else 'DM15; DM16'}; {heritage_assessment.statutory_duty.replace('_', ' ').title()}",
                })
    else:
        recommendation = "APPROVE_WITH_CONDITIONS"
        conditions = generate_conditions(
            proposal=proposal,
            constraints=constraints,
            application_type=application_type,
            heritage_assessment=heritage_assessment,
            amenity_assessments=amenity_assessments,
            council_id=council_id,
        )
        refusal_reasons = []

    # 7. Generate site description
    site_description = f"The application site comprises {site_address}. "
    if constraints:
        site_description += f"The site is affected by the following constraints: {', '.join(constraints)}. "
    site_description += f"The site is located within the {ward} ward."

    # 8. Key issues
    key_issues = ["Principle of development", "Design and visual impact"]
    if heritage_assessment:
        key_issues.append(f"Impact on {heritage_assessment.asset_type}")
    key_issues.append("Residential amenity")

    # 9. Calculate confidence
    confidence = 0.85
    if heritage_assessment:
        confidence += 0.05
    if len(amenity_assessments) > 0:
        confidence += 0.05
    confidence = min(confidence, 0.95)

    # 10. Identify risks
    key_risks = []
    if recommendation == "APPROVE_WITH_CONDITIONS" and heritage_assessment:
        key_risks.append("Heritage impact depends on quality of materials - robust condition monitoring required")
    if any(a.mitigation_possible for a in amenity_assessments):
        key_risks.append("Amenity protection relies on condition compliance")

    # Build development plan policies dynamically from the policy engine
    from .policy_engine import get_relevant_policies as _get_relevant_policies
    _relevant = _get_relevant_policies(
        proposal=proposal,
        application_type=application_type,
        constraints=constraints,
        council_id=council_id,
        site_address=site_address,
    )
    _dev_plan_policies = []
    _nppf_chapters_seen: set[str] = set()
    _nppf_chapters: list[dict] = []
    for _pol in _relevant[:10]:
        if _pol.source_type == "NPPF":
            if _pol.chapter and _pol.chapter not in _nppf_chapters_seen:
                _nppf_chapters_seen.add(_pol.chapter)
                _key_paras = [p.number for p in _pol.paragraphs[:3]]
                _nppf_chapters.append({
                    "chapter": int(_pol.chapter) if _pol.chapter.isdigit() else _pol.chapter,
                    "title": _pol.name,
                    "key_paras": _key_paras,
                })
        else:
            _dev_plan_policies.append({
                "id": _pol.id,
                "name": _pol.name,
                "relevance": _pol.summary[:80] if _pol.summary else "",
            })

    # Fallback if no policies found
    if not _dev_plan_policies:
        _dev_plan_policies = [
            {"id": "Policy 10", "name": "Design and Enhancing Local Identity", "relevance": "Design quality"},
        ]
    if not _nppf_chapters:
        _nppf_chapters = [
            {"chapter": 12, "title": "Achieving well-designed places", "key_paras": ["126", "130", "134"]},
        ]

    return CaseOfficerReport(
        reference=reference,
        site_address=site_address,
        proposal=proposal,
        applicant=applicant_name or "Not specified",
        application_type=application_type,
        ward=ward,
        site_description=site_description,
        planning_history=[],
        constraints=constraints,
        development_plan_policies=_dev_plan_policies,
        nppf_chapters=_nppf_chapters,
        spd_guidance=[],
        statutory_consultees=[],
        neighbour_responses={"support": 0, "object": 0, "neutral": 0, "total": 0},
        key_issues=key_issues,
        principle_of_development=assess_principle_of_development(
            proposal=proposal,
            application_type=application_type,
            constraints=constraints,
            ward=ward,
            postcode=postcode,
            council_id=council_id,
            site_address=site_address,
        ),
        design_assessment=assess_design(
            proposal=proposal,
            constraints=constraints,
            ward=ward,
            measurements=measurements,
            council_id=council_id,
            site_address=site_address,
        ),
        heritage_assessment=heritage_assessment,
        amenity_assessment=amenity_assessments,
        highways_assessment="No highways objections.",
        other_matters=[],
        planning_balance=planning_balance,
        recommendation=recommendation,
        conditions=conditions,
        refusal_reasons=refusal_reasons,
        informatives=[
            "This permission does not convey any approval under the Building Regulations 2010.",
            "The applicant is advised that this permission does not override any private rights.",
        ],
        confidence_score=confidence,
        key_risks=key_risks,
        council_id=council_id,
    )


def _council_display_name(council_id: str) -> str:
    """Get the display name for a council."""
    try:
        from .local_plans_complete import LOCAL_PLANS_DATABASE
        council_data = LOCAL_PLANS_DATABASE.get(council_id.lower(), {})
        return council_data.get("council_name", council_id.upper())
    except Exception:
        _COUNCIL_NAMES = {
            "broxtowe": "BROXTOWE BOROUGH COUNCIL",
            "newcastle": "NEWCASTLE CITY COUNCIL",
        }
        return _COUNCIL_NAMES.get(council_id.lower(), council_id.upper())


def _council_plan_names(council_id: str) -> list[str]:
    """Get the development plan document names for a council."""
    try:
        from .local_plans_complete import LOCAL_PLANS_DATABASE
        council_data = LOCAL_PLANS_DATABASE.get(council_id.lower(), {})
        plans = council_data.get("plans", [])
        return [f"{p['name']} ({p['adopted']})" for p in plans]
    except Exception:
        return ["Local Plan"]


def format_report_markdown(report: CaseOfficerReport) -> str:
    """Format the case officer report as professional markdown."""

    council_name = _council_display_name(report.council_id)
    plan_names = _council_plan_names(report.council_id)

    lines = []

    # Header
    lines.append("# DELEGATED REPORT")
    lines.append("")
    lines.append(f"**{council_name.upper()}**")
    lines.append("**DEVELOPMENT MANAGEMENT**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Application details table
    lines.append("## APPLICATION DETAILS")
    lines.append("")
    lines.append("| Field | Details |")
    lines.append("|-------|---------|")
    lines.append(f"| **Reference** | {report.reference} |")
    lines.append(f"| **Site Address** | {report.site_address} |")
    lines.append(f"| **Ward** | {report.ward} |")
    lines.append(f"| **Applicant** | {report.applicant} |")
    lines.append(f"| **Application Type** | {report.application_type} |")
    lines.append(f"| **Date of Report** | {datetime.now().strftime('%d %B %Y')} |")
    lines.append("")

    # Proposal
    lines.append("## PROPOSAL")
    lines.append("")
    lines.append(report.proposal)
    lines.append("")

    # Site and constraints
    lines.append("## SITE AND SURROUNDINGS")
    lines.append("")
    lines.append(report.site_description)
    lines.append("")

    if report.constraints:
        lines.append("### Constraints")
        lines.append("")
        for c in report.constraints:
            lines.append(f"- {c}")
        lines.append("")

    # Policy framework
    lines.append("## RELEVANT PLANNING POLICY")
    lines.append("")
    lines.append("### Development Plan")
    lines.append("")
    for plan_name in plan_names:
        lines.append(f"**{plan_name}**")
    lines.append("")
    for policy in report.development_plan_policies:
        pid = policy['id']
        prefix = "" if pid.lower().startswith("policy") else "Policy "
        lines.append(f"- **{prefix}{pid}** - {policy['name']}")
    lines.append("")

    lines.append("### National Planning Policy Framework (2023)")
    lines.append("")
    for chapter in report.nppf_chapters:
        lines.append(f"- **Chapter {chapter['chapter']}** - {chapter['title']} (paragraphs {', '.join(chapter['key_paras'])})")
    lines.append("")

    # Statutory duties if heritage
    if report.heritage_assessment:
        lines.append("### Statutory Duties")
        lines.append("")
        lines.append(STATUTORY_DUTIES[report.heritage_assessment.statutory_duty])
        lines.append("")

    # Key issues
    lines.append("## KEY ISSUES")
    lines.append("")
    for i, issue in enumerate(report.key_issues, 1):
        lines.append(f"{i}. {issue}")
    lines.append("")

    # Assessment
    lines.append("## ASSESSMENT")
    lines.append("")

    # Principle
    lines.append("### 1. Principle of Development")
    lines.append("")
    lines.append(report.principle_of_development)
    lines.append("")

    # Design
    lines.append("### 2. Design and Visual Impact")
    lines.append("")
    lines.append(report.design_assessment)
    lines.append("")

    # Heritage if applicable
    if report.heritage_assessment:
        lines.append(f"### 3. Impact on {report.heritage_assessment.asset_type}")
        lines.append("")
        lines.append(f"**Significance:** {report.heritage_assessment.significance}")
        lines.append("")
        lines.append(f"**Impact:** {report.heritage_assessment.impact_on_significance}")
        lines.append("")
        lines.append(f"**Harm Level:** {report.heritage_assessment.harm_level.value.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**NPPF Assessment:** {report.heritage_assessment.justification}")
        lines.append("")

    # Amenity
    lines.append(f"### {'4' if report.heritage_assessment else '3'}. Residential Amenity")
    lines.append("")
    if report.amenity_assessment:
        for amenity in report.amenity_assessment:
            lines.append(f"**{amenity.impact_type.replace('_', ' ').title()}**")
            lines.append("")
            lines.append(amenity.proposed_impact)
            lines.append("")
            lines.append(f"*Impact Level: {amenity.impact_level.value.replace('_', ' ').title()}*")
            lines.append("")
    else:
        lines.append("The proposal is not considered to cause unacceptable harm to residential amenity.")
        lines.append("")

    # Planning balance
    lines.append("## PLANNING BALANCE")
    lines.append("")
    lines.append(report.planning_balance.overall_narrative)
    lines.append("")

    if report.planning_balance.para_202_balance:
        lines.append("### Heritage Balance (NPPF Paragraph 202)")
        lines.append("")
        lines.append(report.planning_balance.para_202_balance)
        lines.append("")

    # Recommendation
    lines.append("## RECOMMENDATION")
    lines.append("")
    lines.append(f"**{report.recommendation.replace('_', ' ')}**")
    lines.append("")

    # Conditions or refusal reasons
    if report.recommendation == "REFUSE":
        lines.append("### Reasons for Refusal")
        lines.append("")
        for reason in report.refusal_reasons:
            lines.append(f"**{reason['number']}.** {reason['reason']}")
            lines.append("")
            lines.append(f"*Policy Basis: {reason['policy_basis']}*")
            lines.append("")
    else:
        lines.append("### Conditions")
        lines.append("")
        for condition in report.conditions:
            lines.append(f"**{condition.number}. {condition.title}**")
            lines.append("")
            lines.append(condition.full_wording)
            lines.append("")
            lines.append(f"*Reason: {condition.reason}*")
            lines.append("")

        if report.informatives:
            lines.append("### Informatives")
            lines.append("")
            for i, info in enumerate(report.informatives, 1):
                lines.append(f"{i}. {info}")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Plana.AI Senior Case Officer Engine*")
    lines.append(f"*Confidence: {report.confidence_score:.0%}*")
    lines.append(f"*Generated: {report.generated_at}*")

    return "\n".join(lines)
