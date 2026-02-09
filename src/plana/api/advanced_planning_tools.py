"""
Advanced Planning Assessment Tools.

Tools for:
1. CIL/S106 Calculator — Infrastructure contribution calculations
2. Consultee Response Templates — SIMULATED statutory consultee responses
3. Document Intelligence — Extract data from submitted documents
4. Visual Impact Assessment — Generate impact diagrams and measurements

IMPORTANT: Consultee response templates (Section 2) generate SIMULATED responses
based on typical professional practice. These are NOT real consultation responses.
In production, all consultation responses must be marked [AWAITING RESPONSE] until
the actual consultee has responded. Simulated responses should only be used for
training, demonstration, or pre-application advice contexts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import re
import math


# =============================================================================
# 1. CIL / S106 CALCULATOR
# =============================================================================

@dataclass
class CILCalculation:
    """Community Infrastructure Levy calculation result."""
    liable: bool
    gross_internal_area: float  # sqm
    existing_lawful_use: float  # sqm (deductible)
    net_increase: float  # sqm
    cil_rate: float  # per sqm
    cil_amount: float  # total
    exemptions_applied: list[str]
    indexation_factor: float
    final_liability: float
    payment_schedule: list[dict]
    notes: list[str]


@dataclass
class S106Obligation:
    """Section 106 planning obligation."""
    category: str  # affordable_housing, highways, education, open_space, etc.
    trigger: str  # What triggers this obligation
    requirement: str  # What is required
    amount: float | None  # Financial contribution if applicable
    in_kind: str | None  # In-kind provision if applicable
    policy_basis: str
    timing: str  # When payable/deliverable
    monitoring_fee: float


@dataclass
class InfrastructureContributions:
    """Complete infrastructure contributions assessment."""
    cil: CILCalculation
    s106_obligations: list[S106Obligation]
    total_financial_contributions: float
    viability_concerns: bool
    viability_notes: str
    summary_table: str


# Newcastle CIL Rates (example - would need to be council-specific)
NEWCASTLE_CIL_RATES = {
    "residential_zone_1": 60.00,  # City centre
    "residential_zone_2": 30.00,  # Inner suburbs
    "residential_zone_3": 15.00,  # Outer areas
    "retail_supermarket": 100.00,
    "retail_other": 0.00,
    "office": 0.00,
    "industrial": 0.00,
    "student_accommodation": 50.00,
    "default": 0.00,
}

# S106 Thresholds
S106_THRESHOLDS = {
    "affordable_housing": {
        "unit_threshold": 10,  # 10+ units triggers
        "site_area_threshold": 0.5,  # or 0.5 hectares
        "percentage": 15,  # 15% affordable
        "tenure_split": "70% social rent, 30% intermediate",
    },
    "education": {
        "unit_threshold": 10,
        "primary_per_unit": 3195.00,
        "secondary_per_unit": 4025.00,
    },
    "open_space": {
        "unit_threshold": 1,
        "per_unit": 1500.00,
    },
    "highways": {
        "trip_threshold": 30,  # 30+ peak hour trips
        "per_trip": 500.00,
    },
    "healthcare": {
        "unit_threshold": 50,
        "per_unit": 360.00,
    },
}


def calculate_cil(
    proposal: str,
    application_type: str,
    gross_internal_area: float,
    existing_lawful_area: float = 0.0,
    use_class: str = "C3",
    zone: str = "zone_2",
    self_build: bool = False,
    affordable_housing: bool = False,
    charity_use: bool = False,
) -> CILCalculation:
    """
    Calculate Community Infrastructure Levy liability.

    Based on CIL Regulations 2010 (as amended).

    Formula: CIL = (Net Increase in GIA) x CIL Rate x Indexation Factor
    """
    exemptions = []
    notes = []

    # Determine CIL rate based on use class and zone
    if use_class in ["C3", "C4"]:  # Residential
        rate_key = f"residential_{zone}"
        cil_rate = NEWCASTLE_CIL_RATES.get(rate_key, NEWCASTLE_CIL_RATES["default"])
    elif use_class == "E" and "retail" in proposal.lower():
        if "supermarket" in proposal.lower() or gross_internal_area > 280:
            cil_rate = NEWCASTLE_CIL_RATES["retail_supermarket"]
        else:
            cil_rate = NEWCASTLE_CIL_RATES["retail_other"]
    elif use_class == "Sui Generis" and "student" in proposal.lower():
        cil_rate = NEWCASTLE_CIL_RATES["student_accommodation"]
    else:
        cil_rate = NEWCASTLE_CIL_RATES["default"]

    # Calculate net increase
    net_increase = max(0, gross_internal_area - existing_lawful_area)

    # Check for exemptions
    if self_build:
        exemptions.append("Self-build exemption (CIL Reg 54A)")
        notes.append("Self-build exemption claimed - owner must occupy for 3 years")

    if affordable_housing:
        exemptions.append("Social housing relief (CIL Reg 49)")
        notes.append("100% relief for affordable housing that meets criteria")

    if charity_use:
        exemptions.append("Charitable relief (CIL Reg 43)")
        notes.append("Discretionary relief for charitable purposes")

    # CIL only applies if net increase > 100sqm or creates new dwelling
    liable = net_increase >= 100 or "dwelling" in proposal.lower()

    if not liable:
        notes.append("Development below 100sqm threshold and does not create new dwelling")

    # Indexation (BCIS All-In Tender Price Index)
    # Using example factor - would be updated annually
    indexation_factor = 1.42  # Example: 2024 factor

    # Calculate base CIL
    if liable and not exemptions:
        cil_amount = net_increase * cil_rate
        final_liability = cil_amount * indexation_factor
    else:
        cil_amount = 0.0
        final_liability = 0.0

    # Payment schedule (for liabilities over 10,000)
    payment_schedule = []
    if final_liability > 0:
        if final_liability <= 10000:
            payment_schedule.append({
                "instalment": 1,
                "amount": final_liability,
                "due": "Within 60 days of commencement",
            })
        elif final_liability <= 50000:
            payment_schedule.append({
                "instalment": 1,
                "amount": final_liability * 0.5,
                "due": "Within 60 days of commencement",
            })
            payment_schedule.append({
                "instalment": 2,
                "amount": final_liability * 0.5,
                "due": "Within 240 days of commencement",
            })
        else:
            payment_schedule.append({
                "instalment": 1,
                "amount": final_liability * 0.25,
                "due": "Within 60 days of commencement",
            })
            payment_schedule.append({
                "instalment": 2,
                "amount": final_liability * 0.25,
                "due": "Within 240 days of commencement",
            })
            payment_schedule.append({
                "instalment": 3,
                "amount": final_liability * 0.5,
                "due": "Within 540 days of commencement",
            })

    return CILCalculation(
        liable=liable,
        gross_internal_area=gross_internal_area,
        existing_lawful_use=existing_lawful_area,
        net_increase=net_increase,
        cil_rate=cil_rate,
        cil_amount=cil_amount,
        exemptions_applied=exemptions,
        indexation_factor=indexation_factor,
        final_liability=final_liability,
        payment_schedule=payment_schedule,
        notes=notes,
    )


def calculate_s106_obligations(
    proposal: str,
    application_type: str,
    num_dwellings: int,
    site_area_ha: float,
    gross_internal_area: float,
    constraints: list[str],
    peak_hour_trips: int = 0,
) -> list[S106Obligation]:
    """
    Calculate Section 106 planning obligations.

    Based on CIL Regulations 2010 Regulation 122 tests:
    - Necessary to make the development acceptable in planning terms
    - Directly related to the development
    - Fairly and reasonably related in scale and kind
    """
    obligations = []

    # Affordable Housing
    if num_dwellings >= S106_THRESHOLDS["affordable_housing"]["unit_threshold"] or \
       site_area_ha >= S106_THRESHOLDS["affordable_housing"]["site_area_threshold"]:

        affordable_units = math.ceil(num_dwellings * S106_THRESHOLDS["affordable_housing"]["percentage"] / 100)

        obligations.append(S106Obligation(
            category="Affordable Housing",
            trigger=f"Development of {num_dwellings} units (threshold: 10 units or 0.5ha)",
            requirement=f"{affordable_units} affordable units ({S106_THRESHOLDS['affordable_housing']['percentage']}%)",
            amount=None,
            in_kind=f"{affordable_units} units on-site, tenure: {S106_THRESHOLDS['affordable_housing']['tenure_split']}",
            policy_basis="NPPF Para 65, Policy CS12",
            timing="Prior to occupation of 50% of market units",
            monitoring_fee=500.00,
        ))

    # Education Contributions
    if num_dwellings >= S106_THRESHOLDS["education"]["unit_threshold"]:
        primary_contribution = num_dwellings * S106_THRESHOLDS["education"]["primary_per_unit"]
        secondary_contribution = num_dwellings * S106_THRESHOLDS["education"]["secondary_per_unit"]
        total_education = primary_contribution + secondary_contribution

        obligations.append(S106Obligation(
            category="Education",
            trigger=f"Development of {num_dwellings} family dwellings",
            requirement="Contribution towards primary and secondary education capacity",
            amount=total_education,
            in_kind=None,
            policy_basis="Policy CS14, Education SPD",
            timing="Prior to commencement / 50% on commencement, 50% on occupation",
            monitoring_fee=250.00,
        ))

    # Open Space
    if num_dwellings >= 1:
        open_space_contribution = num_dwellings * S106_THRESHOLDS["open_space"]["per_unit"]

        obligations.append(S106Obligation(
            category="Open Space and Green Infrastructure",
            trigger=f"Residential development of {num_dwellings} units",
            requirement="Contribution towards open space provision and maintenance",
            amount=open_space_contribution,
            in_kind=None,
            policy_basis="Policy DM27, Open Space SPD",
            timing="Prior to occupation",
            monitoring_fee=150.00,
        ))

    # Highways
    if peak_hour_trips >= S106_THRESHOLDS["highways"]["trip_threshold"]:
        highways_contribution = peak_hour_trips * S106_THRESHOLDS["highways"]["per_trip"]

        obligations.append(S106Obligation(
            category="Highways and Transport",
            trigger=f"Development generating {peak_hour_trips} peak hour vehicle trips",
            requirement="Contribution towards local highway improvements and sustainable transport",
            amount=highways_contribution,
            in_kind="Travel Plan implementation, cycle parking, EV charging points",
            policy_basis="NPPF Para 110, Policy DM7",
            timing="Prior to occupation",
            monitoring_fee=350.00,
        ))

    # Healthcare
    if num_dwellings >= S106_THRESHOLDS["healthcare"]["unit_threshold"]:
        healthcare_contribution = num_dwellings * S106_THRESHOLDS["healthcare"]["per_unit"]

        obligations.append(S106Obligation(
            category="Healthcare",
            trigger=f"Development of {num_dwellings} units creating demand for healthcare",
            requirement="Contribution towards primary healthcare capacity",
            amount=healthcare_contribution,
            in_kind=None,
            policy_basis="Policy CS14, NHS consultation response",
            timing="Prior to occupation of 50% of units",
            monitoring_fee=150.00,
        ))

    # Heritage (if in conservation area)
    if any("conservation" in c.lower() for c in constraints):
        obligations.append(S106Obligation(
            category="Heritage",
            trigger="Development within Conservation Area",
            requirement="Heritage interpretation panel / contribution to conservation area enhancement",
            amount=2500.00,
            in_kind="On-site interpretation panel explaining local heritage",
            policy_basis="Policy DM15, DM16, Conservation Area Management Plan",
            timing="Prior to occupation",
            monitoring_fee=100.00,
        ))

    return obligations


def generate_infrastructure_assessment(
    proposal: str,
    application_type: str,
    gross_internal_area: float = 0.0,
    existing_area: float = 0.0,
    num_dwellings: int = 0,
    site_area_ha: float = 0.0,
    constraints: list[str] = None,
    use_class: str = "C3",
    zone: str = "zone_2",
) -> InfrastructureContributions:
    """Generate complete infrastructure contributions assessment."""

    if constraints is None:
        constraints = []

    # Calculate CIL
    cil = calculate_cil(
        proposal=proposal,
        application_type=application_type,
        gross_internal_area=gross_internal_area,
        existing_lawful_area=existing_area,
        use_class=use_class,
        zone=zone,
    )

    # Estimate peak hour trips (simplified - would use TRICS in practice)
    peak_hour_trips = num_dwellings * 0.5 if num_dwellings > 0 else 0

    # Calculate S106 obligations
    s106 = calculate_s106_obligations(
        proposal=proposal,
        application_type=application_type,
        num_dwellings=num_dwellings,
        site_area_ha=site_area_ha,
        gross_internal_area=gross_internal_area,
        constraints=constraints,
        peak_hour_trips=int(peak_hour_trips),
    )

    # Total financial contributions
    total_financial = cil.final_liability
    for obligation in s106:
        if obligation.amount:
            total_financial += obligation.amount
        total_financial += obligation.monitoring_fee

    # Viability assessment
    viability_concerns = total_financial > (num_dwellings * 15000 if num_dwellings > 0 else gross_internal_area * 100)
    viability_notes = ""
    if viability_concerns:
        viability_notes = "Total contributions may impact scheme viability. Viability assessment may be required per NPPF Para 58."

    # Generate summary table
    summary_lines = ["## INFRASTRUCTURE CONTRIBUTIONS SUMMARY", ""]
    summary_lines.append("### Community Infrastructure Levy (CIL)")
    summary_lines.append("")
    summary_lines.append("| Item | Value |")
    summary_lines.append("|------|-------|")
    summary_lines.append(f"| Gross Internal Area | {cil.gross_internal_area:.1f} sqm |")
    summary_lines.append(f"| Existing Lawful Use | {cil.existing_lawful_use:.1f} sqm |")
    summary_lines.append(f"| Net Increase | {cil.net_increase:.1f} sqm |")
    summary_lines.append(f"| CIL Rate | {cil.cil_rate:.2f}/sqm |")
    summary_lines.append(f"| Indexation Factor | {cil.indexation_factor:.2f} |")
    summary_lines.append(f"| **CIL Liability** | **{cil.final_liability:,.2f}** |")
    summary_lines.append("")

    if cil.exemptions_applied:
        summary_lines.append("**Exemptions Applied:**")
        for exemption in cil.exemptions_applied:
            summary_lines.append(f"- {exemption}")
        summary_lines.append("")

    if cil.payment_schedule:
        summary_lines.append("**Payment Schedule:**")
        summary_lines.append("")
        summary_lines.append("| Instalment | Amount | Due |")
        summary_lines.append("|------------|--------|-----|")
        for payment in cil.payment_schedule:
            summary_lines.append(f"| {payment['instalment']} | {payment['amount']:,.2f} | {payment['due']} |")
        summary_lines.append("")

    if s106:
        summary_lines.append("### Section 106 Obligations")
        summary_lines.append("")
        summary_lines.append("| Category | Requirement | Amount | Timing |")
        summary_lines.append("|----------|-------------|--------|--------|")
        for obligation in s106:
            amount_str = f"{obligation.amount:,.2f}" if obligation.amount else "In-kind"
            summary_lines.append(f"| {obligation.category} | {obligation.requirement[:50]}... | {amount_str} | {obligation.timing} |")
        summary_lines.append("")

    summary_lines.append(f"### **TOTAL FINANCIAL CONTRIBUTIONS: {total_financial:,.2f}**")

    if viability_concerns:
        summary_lines.append("")
        summary_lines.append(f"**VIABILITY NOTE:** {viability_notes}")

    return InfrastructureContributions(
        cil=cil,
        s106_obligations=s106,
        total_financial_contributions=total_financial,
        viability_concerns=viability_concerns,
        viability_notes=viability_notes,
        summary_table="\n".join(summary_lines),
    )


# =============================================================================
# 2. CONSULTEE RESPONSE TEMPLATES (SIMULATED)
# =============================================================================
# WARNING: These generate SIMULATED consultee responses based on typical
# professional practice. They are NOT real responses from actual consultees.
# In production reports, use [AWAITING RESPONSE] until actual responses are received.

@dataclass
class ConsulteeResponse:
    """A statutory consultee response (may be simulated).

    IMPORTANT: Check is_simulated — if True, this is a template response
    and must NOT be presented as a real consultation response in reports.
    """

    consultee: str
    response_type: str  # no_objection, objection, conditional, no_response
    summary: str
    detailed_comments: str
    recommended_conditions: list[dict]
    informatives: list[str]
    response_date: str
    officer: str
    is_simulated: bool = True  # Always True for template-generated responses


def generate_highways_response(
    proposal: str,
    application_type: str,
    num_dwellings: int = 0,
    parking_spaces: int = 0,
    site_access: str = "existing",
    constraints: list[str] = None,
) -> ConsulteeResponse:
    """Generate realistic Highways Development Control response."""

    conditions = []
    informatives = []

    proposal_lower = proposal.lower()

    # Parking assessment
    if num_dwellings > 0:
        # Newcastle parking standards (example)
        required_spaces = num_dwellings * 1.5  # Varies by zone

        if parking_spaces >= required_spaces:
            parking_comment = f"Parking provision of {parking_spaces} spaces meets the Council's adopted parking standards for {num_dwellings} dwelling(s)."
        else:
            parking_comment = f"Parking provision of {parking_spaces} spaces is below the standard of {required_spaces:.0f} spaces. However, given the sustainable location with good access to public transport, this is considered acceptable."
    else:
        parking_comment = "The proposal does not significantly alter parking demand."

    # Access assessment
    if site_access == "new":
        access_comment = "A new vehicular access is proposed. This should be constructed to adoptable standards with adequate visibility splays."
        conditions.append({
            "condition": "Prior to first occupation, the vehicular access shall be constructed with a minimum width of 4.8m for the first 10m from the highway boundary, with visibility splays of 2.4m x 43m in both directions.",
            "reason": "In the interests of highway safety, having regard to NPPF Para 110 and Policy DM7.",
        })
    else:
        access_comment = "The existing vehicular access is considered adequate for the proposed development."

    # Cycle parking
    if "dwelling" in proposal_lower or "residential" in proposal_lower:
        conditions.append({
            "condition": "Prior to occupation, secure covered cycle parking shall be provided in accordance with details to be submitted to and approved by the LPA. The cycle parking shall be retained thereafter.",
            "reason": "To promote sustainable transport, having regard to NPPF Para 104 and Policy DM7.",
        })

    # Construction management
    if num_dwellings > 5 or "major" in application_type.lower():
        conditions.append({
            "condition": "No development shall take place until a Construction Traffic Management Plan has been submitted to and approved by the LPA. This shall include details of routing, parking, wheel washing, and delivery times.",
            "reason": "In the interests of highway safety during construction, having regard to Policy DM7.",
        })

    # Informatives
    informatives.append("Any works within the highway require a Section 184 license from the Highway Authority.")
    informatives.append("The applicant is advised to contact Streetworks regarding any temporary road closures or traffic management.")

    detailed_comments = f"""**HIGHWAYS DEVELOPMENT CONTROL RESPONSE**

**Application Assessment**

The Highway Authority has assessed this application in accordance with NPPF Chapter 9 (Promoting Sustainable Transport) and Policy DM7 of the Development and Allocations Plan.

**NPPF Paragraph 111 Test:**
Development should only be refused on highways grounds if there would be:
- An unacceptable impact on highway safety; OR
- The residual cumulative impacts would be severe

**Parking Assessment:**
{parking_comment}

Newcastle Parking Standards Applied:
- Residential (Zone 2): 1.5 spaces per dwelling (max)
- Cycle parking: 1 space per bedroom

**Access Assessment:**
{access_comment}

**Visibility Splays:**
{'Visibility splays of 2.4m x 43m required for 30mph road.' if site_access == 'new' else 'Existing access visibility considered acceptable.'}

**Trip Generation:**
{'Estimated additional peak hour trips: ' + str(int(num_dwellings * 0.5)) + ' vehicles. This is within acceptable parameters for the local highway network.' if num_dwellings > 0 else 'No significant increase in trip generation.'}

**Sustainable Transport:**
The site is located within {'a sustainable location with good access to public transport.' if any('city centre' in str(c).lower() for c in (constraints or [])) else 'reasonable distance of public transport links.'}

**Recommendation:**
No objection, subject to conditions."""

    return ConsulteeResponse(
        consultee="Highways Development Control",
        response_type="conditional",
        summary="No objection subject to conditions regarding access, parking, and cycle storage.",
        detailed_comments=detailed_comments,
        recommended_conditions=conditions,
        informatives=informatives,
        response_date=datetime.now().strftime("%d %B %Y"),
        officer="Highway Development Control Officer",
    )


def generate_drainage_response(
    proposal: str,
    application_type: str,
    site_area_sqm: float = 0.0,
    constraints: list[str] = None,
    flood_zone: int = 1,
) -> ConsulteeResponse:
    """Generate Lead Local Flood Authority (LLFA) / Drainage response."""

    conditions = []
    informatives = []

    # SuDS requirements
    if site_area_sqm > 100:
        conditions.append({
            "condition": "No development shall commence until a surface water drainage scheme, based on sustainable drainage principles (SuDS), has been submitted to and approved by the LPA. The scheme shall include: (a) calculations demonstrating no increase in surface water runoff for the 1 in 100 year + climate change event; (b) details of SuDS features; (c) maintenance and management plan.",
            "reason": "To ensure adequate surface water drainage and reduce flood risk, having regard to NPPF Para 167 and Policy CS16.",
        })

    # Flood zone specific
    if flood_zone >= 2:
        conditions.append({
            "condition": "The development shall be carried out in accordance with the submitted Flood Risk Assessment and the mitigation measures identified therein. Finished floor levels shall be set no lower than [X]m AOD.",
            "reason": "To reduce flood risk to the development and its occupants, having regard to NPPF Para 167.",
        })

    # Foul drainage
    conditions.append({
        "condition": "Foul and surface water shall be drained on separate systems.",
        "reason": "To ensure satisfactory drainage and prevent pollution, having regard to Policy CS16.",
    })

    informatives.append("The applicant is advised to contact Northumbrian Water regarding connection to the public sewer system.")
    informatives.append("All SuDS features should be designed in accordance with CIRIA C753 (The SuDS Manual).")

    detailed_comments = f"""**LEAD LOCAL FLOOD AUTHORITY / DRAINAGE RESPONSE**

**Flood Risk Assessment**

The site is located in Flood Zone {flood_zone} as defined by the Environment Agency Flood Map for Planning.

| Flood Zone | Description | Sequential Test |
|------------|-------------|-----------------|
| Zone 1 | Low probability (<0.1% annual) | {'PASS' if flood_zone == 1 else 'N/A'} |
| Zone 2 | Medium probability (0.1-1% annual) | {'Required' if flood_zone == 2 else 'N/A'} |
| Zone 3a | High probability (>1% annual) | {'Required + Exception Test' if flood_zone >= 3 else 'N/A'} |

**Surface Water Drainage Requirements**

NPPF Paragraph 169 and Policy CS16 require surface water to be managed sustainably.

**SuDS Hierarchy (in order of preference):**
1. Infiltration (soakaways, permeable paving) - subject to ground conditions
2. Attenuation and discharge to watercourse
3. Attenuation and discharge to surface water sewer
4. Attenuation and discharge to combined sewer (last resort)

**Greenfield Runoff Rate:**
All developments should aim to achieve greenfield runoff rates. For this site, the estimated greenfield runoff rate is {site_area_sqm * 0.005:.1f} l/s (based on 5 l/s/ha).

**Climate Change Allowance:**
Surface water drainage design must include a {40 if flood_zone >= 2 else 30}% allowance for climate change (peak rainfall intensity).

**Recommended SuDS Features:**
- Permeable paving for driveways and parking areas
- Rain gardens / bioretention areas
- Green roofs (where appropriate)
- Rainwater harvesting
- Attenuation tanks (below ground) if above-ground features not feasible

**Foul Drainage:**
Connection to the public foul sewer is available. Northumbrian Water should be consulted regarding capacity.

**Recommendation:**
No objection, subject to conditions securing a comprehensive SuDS scheme."""

    return ConsulteeResponse(
        consultee="Lead Local Flood Authority / Drainage",
        response_type="conditional",
        summary="No objection subject to SuDS condition and separate foul/surface water drainage.",
        detailed_comments=detailed_comments,
        recommended_conditions=conditions,
        informatives=informatives,
        response_date=datetime.now().strftime("%d %B %Y"),
        officer="Flood Risk and Drainage Officer",
    )


def generate_ecology_response(
    proposal: str,
    application_type: str,
    site_area_sqm: float = 0.0,
    constraints: list[str] = None,
    trees_affected: bool = False,
) -> ConsulteeResponse:
    """Generate Ecology / Natural Environment response."""

    conditions = []
    informatives = []
    constraints = constraints or []

    # Protected species
    informatives.append("All wild birds, their nests and eggs are protected under the Wildlife and Countryside Act 1981. Vegetation clearance should be undertaken outside the bird nesting season (March-August inclusive) unless checked by a qualified ecologist.")

    # Biodiversity Net Gain (mandatory from 2024)
    if site_area_sqm > 25:  # Above de minimis threshold
        conditions.append({
            "condition": "Prior to commencement, a Biodiversity Gain Plan demonstrating a minimum 10% net gain in biodiversity units shall be submitted to and approved by the LPA. The Plan shall include: (a) baseline habitat assessment; (b) proposed habitat creation/enhancement; (c) 30-year management and monitoring plan.",
            "reason": "To secure measurable biodiversity net gain in accordance with the Environment Act 2021 and NPPF Para 180.",
        })

    # Trees and hedgerows
    if trees_affected:
        conditions.append({
            "condition": "No development shall take place until an Arboricultural Method Statement and Tree Protection Plan, in accordance with BS 5837:2012, have been submitted to and approved by the LPA. Tree protection fencing shall be erected prior to commencement and retained throughout construction.",
            "reason": "To protect trees and hedgerows of amenity value, having regard to Policy DM28.",
        })

    # Wildlife-friendly features
    conditions.append({
        "condition": "Prior to occupation, details of biodiversity enhancement measures shall be submitted to and approved by the LPA. These shall include at least: (a) 2 integrated bat boxes or bricks; (b) 2 integrated swift/bird boxes; (c) native species planting. The measures shall be implemented and retained thereafter.",
        "reason": "To enhance biodiversity, having regard to NPPF Para 180 and Policy CS18.",
    })

    # Lighting
    conditions.append({
        "condition": "Any external lighting shall be designed to minimise light spill and avoid illumination of potential bat foraging corridors and roost sites. Details shall be submitted to and approved by the LPA prior to installation.",
        "reason": "To protect nocturnal wildlife, particularly bats, having regard to Policy CS18.",
    })

    detailed_comments = f"""**ECOLOGY / NATURAL ENVIRONMENT RESPONSE**

**Statutory Framework**

The assessment has been undertaken with regard to:
- NPPF Chapter 15: Conserving and Enhancing the Natural Environment
- Environment Act 2021 (Biodiversity Net Gain)
- Wildlife and Countryside Act 1981 (as amended)
- Conservation of Habitats and Species Regulations 2017
- Natural Environment and Rural Communities Act 2006 (S.41 species)

**Biodiversity Net Gain (BNG) Requirement**

From February 2024, developments must deliver a minimum **10% biodiversity net gain**.

| Item | Requirement |
|------|-------------|
| Baseline assessment | Defra Metric 4.0 calculation |
| Net gain target | Minimum 10% (uplift from baseline) |
| Habitat delivery | On-site preferred, off-site permitted, credits as last resort |
| Management period | 30 years minimum |
| Small sites metric | Available for sites <0.5ha or <10 dwellings |

**Protected Species Assessment**

A desk-based assessment has been undertaken using:
- MAGIC database (statutory designations)
- Local Biological Records Centre data
- Aerial imagery and habitat assessment

**Potential ecological constraints:**
{'- Site within/adjacent to designated wildlife site' if any('sssi' in c.lower() or 'wildlife' in c.lower() for c in constraints) else '- No statutory designated sites within 500m'}
{'- Trees/hedgerows with potential for nesting birds and roosting bats' if trees_affected else '- Limited ecological features on site'}
- All sites have potential for nesting birds

**Mitigation Hierarchy (NPPF Para 180):**
1. Avoid - Design to avoid impacts on ecological features
2. Mitigate - Reduce unavoidable impacts during construction
3. Compensate - Provide compensation for residual impacts
4. Net Gain - Achieve measurable improvement

**Wildlife-Friendly Design:**
Integrated wildlife features are now expected on all developments:
- Bat boxes/bricks (south/southeast facing, 3m+ height)
- Swift bricks (under eaves, 5m+ height)
- Hedgehog highways (13cm gaps in fences)
- Native species planting for pollinators

**Recommendation:**
No objection, subject to conditions securing biodiversity net gain, wildlife features, and (where relevant) tree protection."""

    return ConsulteeResponse(
        consultee="Ecology / Natural Environment",
        response_type="conditional",
        summary="No objection subject to Biodiversity Net Gain, wildlife features, and tree protection conditions.",
        detailed_comments=detailed_comments,
        recommended_conditions=conditions,
        informatives=informatives,
        response_date=datetime.now().strftime("%d %B %Y"),
        officer="Ecology Officer",
    )


def generate_environmental_health_response(
    proposal: str,
    application_type: str,
    constraints: list[str] = None,
    near_noise_source: bool = False,
    potentially_contaminated: bool = False,
) -> ConsulteeResponse:
    """Generate Environmental Health response."""

    conditions = []
    informatives = []
    constraints = constraints or []

    # Contaminated land
    if potentially_contaminated or any("contaminated" in c.lower() for c in constraints):
        conditions.append({
            "condition": """Prior to commencement, a Phase 2 Site Investigation Report shall be submitted to and approved by the LPA. If contamination is found, a Remediation Strategy shall be submitted and approved. The approved remediation shall be implemented prior to occupation, and a Verification Report submitted to demonstrate completion.""",
            "reason": "To ensure the site is safe for the proposed use, having regard to NPPF Para 183 and Policy DM5.",
        })

    # Noise - near roads, railways, commercial
    if near_noise_source:
        conditions.append({
            "condition": "Prior to commencement, a Noise Assessment shall be submitted demonstrating that internal noise levels will meet BS 8233:2014 standards (35dB LAeq,16hr for living rooms, 30dB LAeq,8hr for bedrooms). Where necessary, a scheme of noise mitigation shall be implemented and retained.",
            "reason": "To protect residential amenity from noise, having regard to NPPF Para 185 and Policy DM6.6.",
        })

    # Air quality
    conditions.append({
        "condition": "No dwelling shall be occupied until electric vehicle charging points have been installed at a ratio of 1 charging point per dwelling with dedicated parking, plus 1 per 10 unallocated spaces.",
        "reason": "To promote sustainable transport and improve air quality, having regard to Policy CS16 and the Air Quality Action Plan.",
    })

    # Construction hours
    informatives.append("""Construction work audible at the site boundary should be limited to:
- Monday to Friday: 08:00 - 18:00
- Saturday: 08:00 - 13:00
- Sundays and Bank Holidays: No working""")

    informatives.append("Burning of materials on site is not permitted and may result in enforcement action.")

    detailed_comments = f"""**ENVIRONMENTAL HEALTH RESPONSE**

**Assessment Framework**

This response addresses:
- NPPF Para 183-188: Ground conditions and pollution
- NPPF Para 185: Noise
- Policy DM5: Pollution and Land Stability
- Policy DM6.6: Protection of Residential Amenity

**1. CONTAMINATED LAND ASSESSMENT**

{'**Potentially contaminated land identified.** A Phase 1 Desk Study has identified potential contamination sources. A Phase 2 intrusive investigation is required prior to commencement.' if potentially_contaminated else 'No significant contamination risk identified from desk-based assessment. Standard unexpected contamination condition recommended.'}

**Contaminated Land Framework:**
| Stage | Requirement |
|-------|-------------|
| Phase 1 | Desk Study and Conceptual Site Model |
| Phase 2 | Intrusive Site Investigation |
| Remediation | Strategy to break pollutant linkages |
| Verification | Report confirming remediation complete |

**2. NOISE ASSESSMENT**

{'**Noise-sensitive location identified.** Site is within 50m of significant noise source. Noise assessment required demonstrating compliance with BS 8233:2014.' if near_noise_source else 'No significant noise sources identified that would affect residential amenity.'}

**BS 8233:2014 Internal Noise Standards:**
| Room Type | Day (07:00-23:00) | Night (23:00-07:00) |
|-----------|-------------------|---------------------|
| Living rooms | 35 dB LAeq,16hr | - |
| Bedrooms | 35 dB LAeq,16hr | 30 dB LAeq,8hr |
| Maximum (bedrooms) | - | 45 dB LAmax |

**WHO Night Noise Guidelines:**
- 40 dB Lnight,outside: Lowest observed adverse effect level
- 55 dB Lnight,outside: Adverse health effects

**3. AIR QUALITY**

Newcastle has declared Air Quality Management Areas (AQMAs) for nitrogen dioxide (NO2). Developments should:
- Minimise emissions from heating (gas boilers <40mg/kWh NOx)
- Provide EV charging infrastructure
- Support sustainable transport

**4. ODOUR AND DUST**

{'Commercial kitchen extraction may be required to meet odour control standards.' if 'restaurant' in proposal.lower() or 'food' in proposal.lower() else 'No significant odour sources identified.'}

Construction dust should be controlled in accordance with IAQM guidance.

**Recommendation:**
{'No objection, subject to contaminated land investigation, noise assessment, and EV charging conditions.' if potentially_contaminated or near_noise_source else 'No objection, subject to EV charging condition. Standard informatives regarding construction hours apply.'}"""

    return ConsulteeResponse(
        consultee="Environmental Health",
        response_type="conditional",
        summary="No objection subject to conditions regarding contamination, noise (where applicable), and EV charging.",
        detailed_comments=detailed_comments,
        recommended_conditions=conditions,
        informatives=informatives,
        response_date=datetime.now().strftime("%d %B %Y"),
        officer="Environmental Health Officer",
    )


def generate_all_consultee_responses(
    proposal: str,
    application_type: str,
    num_dwellings: int = 0,
    site_area_sqm: float = 0.0,
    constraints: list[str] = None,
) -> dict[str, ConsulteeResponse]:
    """Generate all standard consultee responses."""

    constraints = constraints or []

    return {
        "highways": generate_highways_response(
            proposal=proposal,
            application_type=application_type,
            num_dwellings=num_dwellings,
            parking_spaces=int(num_dwellings * 1.5),
            site_access="existing" if "existing" in proposal.lower() else "new",
            constraints=constraints,
        ),
        "drainage": generate_drainage_response(
            proposal=proposal,
            application_type=application_type,
            site_area_sqm=site_area_sqm,
            constraints=constraints,
            flood_zone=1,
        ),
        "ecology": generate_ecology_response(
            proposal=proposal,
            application_type=application_type,
            site_area_sqm=site_area_sqm,
            constraints=constraints,
            trees_affected="tree" in proposal.lower(),
        ),
        "environmental_health": generate_environmental_health_response(
            proposal=proposal,
            application_type=application_type,
            constraints=constraints,
            near_noise_source=any("road" in c.lower() or "railway" in c.lower() for c in constraints),
            potentially_contaminated=any("contaminated" in c.lower() for c in constraints),
        ),
    }


# =============================================================================
# 3. DOCUMENT INTELLIGENCE
# =============================================================================

@dataclass
class ExtractedDimensions:
    """Dimensions extracted from submitted plans."""
    width: float | None
    depth: float | None
    height: float | None
    eaves_height: float | None
    ridge_height: float | None
    floor_area: float | None
    volume: float | None
    distance_to_boundary: float | None
    distance_to_neighbour: float | None
    source_document: str
    confidence: str  # high, medium, low
    notes: list[str]


@dataclass
class DocumentAnalysis:
    """Analysis of a submitted document."""
    document_type: str
    document_name: str
    key_information: dict[str, Any]
    policy_compliance_notes: list[str]
    missing_information: list[str]
    quality_assessment: str  # good, adequate, poor
    recommendations: list[str]


def extract_dimensions_from_text(text: str) -> ExtractedDimensions:
    """
    Extract dimensions from plan descriptions or OCR text.

    Looks for patterns like:
    - "5.0m wide"
    - "height: 2.5m"
    - "3.5m x 4.2m"
    - "distance to boundary: 1.0m"
    """
    notes = []

    # Regex patterns for dimension extraction
    patterns = {
        "width": [
            r"width[:\s]+(\d+\.?\d*)\s*m",
            r"(\d+\.?\d*)\s*m\s*wide",
            r"(\d+\.?\d*)\s*x\s*\d+\.?\d*\s*m",
        ],
        "depth": [
            r"depth[:\s]+(\d+\.?\d*)\s*m",
            r"(\d+\.?\d*)\s*m\s*deep",
            r"\d+\.?\d*\s*x\s*(\d+\.?\d*)\s*m",
        ],
        "height": [
            r"(?:overall\s+)?height[:\s]+(\d+\.?\d*)\s*m",
            r"(\d+\.?\d*)\s*m\s*(?:high|tall)",
            r"ridge\s+height[:\s]+(\d+\.?\d*)\s*m",
        ],
        "eaves_height": [
            r"eaves[:\s]+(\d+\.?\d*)\s*m",
            r"eaves\s+height[:\s]+(\d+\.?\d*)\s*m",
        ],
        "distance_to_boundary": [
            r"(?:distance\s+to\s+)?boundary[:\s]+(\d+\.?\d*)\s*m",
            r"(\d+\.?\d*)\s*m\s+from\s+boundary",
            r"set\s+back\s+(\d+\.?\d*)\s*m",
        ],
    }

    extracted = {}
    text_lower = text.lower()

    for dimension, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_lower)
            if match:
                extracted[dimension] = float(match.group(1))
                notes.append(f"Extracted {dimension}: {match.group(1)}m")
                break

    # Calculate derived values
    floor_area = None
    volume = None

    if extracted.get("width") and extracted.get("depth"):
        floor_area = extracted["width"] * extracted["depth"]
        notes.append(f"Calculated floor area: {floor_area:.1f}sqm")

        if extracted.get("height"):
            # Simplified volume calculation
            volume = floor_area * extracted["height"] * 0.75  # Account for roof
            notes.append(f"Estimated volume: {volume:.1f}m3")

    # Confidence assessment
    if len(extracted) >= 3:
        confidence = "high"
    elif len(extracted) >= 1:
        confidence = "medium"
    else:
        confidence = "low"
        notes.append("Limited dimension information found")

    return ExtractedDimensions(
        width=extracted.get("width"),
        depth=extracted.get("depth"),
        height=extracted.get("height"),
        eaves_height=extracted.get("eaves_height"),
        ridge_height=extracted.get("height"),  # Often same as height
        floor_area=floor_area,
        volume=volume,
        distance_to_boundary=extracted.get("distance_to_boundary"),
        distance_to_neighbour=None,  # Usually from site plan
        source_document="Extracted from text",
        confidence=confidence,
        notes=notes,
    )


def analyse_design_access_statement(text: str) -> DocumentAnalysis:
    """Analyse a Design and Access Statement."""

    key_info = {}
    compliance_notes = []
    missing_info = []
    recommendations = []

    text_lower = text.lower()

    # Check for required content
    required_sections = {
        "context": ["context", "site", "surrounding", "character"],
        "design": ["design", "appearance", "materials", "scale"],
        "access": ["access", "transport", "parking", "pedestrian"],
        "amount": ["amount", "floor area", "units", "density"],
        "layout": ["layout", "siting", "orientation"],
        "scale": ["scale", "height", "massing", "bulk"],
        "landscaping": ["landscape", "planting", "trees", "green"],
    }

    for section, keywords in required_sections.items():
        if any(kw in text_lower for kw in keywords):
            key_info[section] = "Addressed"
        else:
            missing_info.append(f"Section not clearly addressed: {section.title()}")

    # Check for policy references
    if "nppf" in text_lower or "national planning policy" in text_lower:
        key_info["nppf_referenced"] = True
        compliance_notes.append("NPPF referenced in statement")
    else:
        missing_info.append("No reference to NPPF")

    if any(p in text_lower for p in ["dm6", "cs15", "local plan", "development plan"]):
        key_info["local_plan_referenced"] = True
        compliance_notes.append("Local Plan policies referenced")
    else:
        missing_info.append("Local Plan policies not clearly referenced")

    # Quality assessment
    addressed_count = sum(1 for v in key_info.values() if v == "Addressed" or v is True)

    if addressed_count >= 6:
        quality = "good"
    elif addressed_count >= 4:
        quality = "adequate"
    else:
        quality = "poor"
        recommendations.append("Design and Access Statement should be expanded to address all required sections")

    return DocumentAnalysis(
        document_type="Design and Access Statement",
        document_name="Design and Access Statement",
        key_information=key_info,
        policy_compliance_notes=compliance_notes,
        missing_information=missing_info,
        quality_assessment=quality,
        recommendations=recommendations,
    )


def analyse_heritage_statement(text: str, constraints: list[str]) -> DocumentAnalysis:
    """Analyse a Heritage Impact Assessment / Heritage Statement."""

    key_info = {}
    compliance_notes = []
    missing_info = []
    recommendations = []

    text_lower = text.lower()

    has_conservation = any("conservation" in c.lower() for c in constraints)
    has_listed = any("listed" in c.lower() for c in constraints)

    # Check for significance assessment (NPPF Para 194)
    significance_keywords = ["significance", "special interest", "heritage value", "architectural", "historic"]
    if any(kw in text_lower for kw in significance_keywords):
        key_info["significance_assessed"] = True
        compliance_notes.append("NPPF Para 194: Significance of heritage asset described")
    else:
        missing_info.append("Significance of heritage asset not clearly described (NPPF Para 194)")

    # Check for setting assessment
    if "setting" in text_lower:
        key_info["setting_assessed"] = True
        compliance_notes.append("Setting of heritage asset considered")
    else:
        missing_info.append("Setting of heritage asset not addressed")

    # Check for harm assessment
    harm_keywords = ["harm", "impact", "effect", "substantial", "less than substantial"]
    if any(kw in text_lower for kw in harm_keywords):
        key_info["harm_assessed"] = True
        compliance_notes.append("Impact/harm to heritage asset assessed")
    else:
        missing_info.append("Level of harm not clearly assessed (NPPF Para 199-202)")

    # Check for justification (NPPF Para 200)
    justification_keywords = ["justification", "public benefit", "necessary", "outweigh"]
    if any(kw in text_lower for kw in justification_keywords):
        key_info["justification_provided"] = True
        compliance_notes.append("NPPF Para 200: Justification for any harm provided")

    # Check statutory references
    if "section 66" in text_lower or "section 72" in text_lower:
        key_info["statutory_duties_referenced"] = True
        compliance_notes.append("Statutory duties (S.66/S.72) referenced")
    else:
        missing_info.append("Statutory duties under Planning (Listed Buildings and Conservation Areas) Act 1990 not referenced")

    # Quality assessment
    addressed_count = sum(1 for v in key_info.values() if v is True)

    if addressed_count >= 4:
        quality = "good"
    elif addressed_count >= 2:
        quality = "adequate"
    else:
        quality = "poor"
        recommendations.append("Heritage Statement should provide detailed significance assessment in accordance with NPPF Para 194")
        recommendations.append("Statement should clearly assess level of harm and provide justification per NPPF Para 200-202")

    return DocumentAnalysis(
        document_type="Heritage Statement",
        document_name="Heritage Impact Assessment",
        key_information=key_info,
        policy_compliance_notes=compliance_notes,
        missing_information=missing_info,
        quality_assessment=quality,
        recommendations=recommendations,
    )


def analyse_documents(
    documents: list[dict],
    constraints: list[str] = None,
) -> dict[str, DocumentAnalysis]:
    """Analyse all submitted documents."""

    constraints = constraints or []
    analyses = {}

    for doc in documents:
        doc_type = doc.get("document_type", "").lower()
        doc_name = doc.get("name", "Unknown")
        content = doc.get("content_text", "")

        if not content:
            continue

        if "design" in doc_type or "access" in doc_type:
            analyses["design_access"] = analyse_design_access_statement(content)

        elif "heritage" in doc_type:
            analyses["heritage"] = analyse_heritage_statement(content, constraints)

        elif "plan" in doc_type or "drawing" in doc_type:
            dimensions = extract_dimensions_from_text(content)
            analyses["dimensions"] = DocumentAnalysis(
                document_type="Plans/Drawings",
                document_name=doc_name,
                key_information={
                    "width": dimensions.width,
                    "depth": dimensions.depth,
                    "height": dimensions.height,
                    "floor_area": dimensions.floor_area,
                    "boundary_distance": dimensions.distance_to_boundary,
                },
                policy_compliance_notes=dimensions.notes,
                missing_information=[],
                quality_assessment=dimensions.confidence,
                recommendations=[],
            )

    return analyses


# =============================================================================
# 4. VISUAL IMPACT ASSESSMENT
# =============================================================================

@dataclass
class DaylightAssessment:
    """45-degree daylight test assessment."""
    neighbour_address: str
    window_position: str  # ground, first, second
    window_height_from_ground: float  # metres
    distance_to_development: float  # metres
    development_height: float  # metres
    angle_subtended: float  # degrees
    passes_test: bool
    notes: str


@dataclass
class PrivacyAssessment:
    """Privacy distance assessment."""
    relationship: str  # front-to-front, rear-to-rear, side-to-side
    actual_distance: float  # metres
    required_distance: float  # metres
    compliant: bool
    mitigation: str | None
    notes: str


@dataclass
class VisualImpactResult:
    """Complete visual impact assessment result."""
    daylight_assessments: list[DaylightAssessment]
    privacy_assessments: list[PrivacyAssessment]
    overshadowing_summary: str
    overbearing_summary: str
    overall_impact: str  # acceptable, marginal, unacceptable
    diagram_ascii: str
    recommendations: list[str]


def calculate_45_degree_test(
    neighbour_window_height: float,  # Height of centre of window from ground
    distance_to_development: float,  # Horizontal distance to proposed development
    development_height: float,  # Height of proposed development
) -> DaylightAssessment:
    """
    Calculate the 45-degree daylight test.

    The test: Draw a line at 45 degrees from the centre of the lowest
    affected window (at 2m above ground level). If the development lies
    entirely below this line, daylight impact is acceptable.
    """

    # Height at which 45-degree line reaches the development
    height_at_45_deg = neighbour_window_height + distance_to_development

    # Actual angle subtended by development
    height_above_window = development_height - neighbour_window_height
    if distance_to_development > 0:
        angle = math.degrees(math.atan(height_above_window / distance_to_development))
    else:
        angle = 90.0

    passes = development_height <= height_at_45_deg

    notes = f"Window at {neighbour_window_height}m, development {distance_to_development}m away, "
    notes += f"45° line reaches {height_at_45_deg:.1f}m at development location. "
    notes += f"Development height {development_height}m. "
    notes += f"Angle subtended: {angle:.1f}°. "
    notes += "PASSES 45° test." if passes else "FAILS 45° test - further assessment required."

    return DaylightAssessment(
        neighbour_address="Adjacent property",
        window_position="ground" if neighbour_window_height < 3 else "first" if neighbour_window_height < 6 else "second",
        window_height_from_ground=neighbour_window_height,
        distance_to_development=distance_to_development,
        development_height=development_height,
        angle_subtended=angle,
        passes_test=passes,
        notes=notes,
    )


def assess_privacy_distance(
    actual_distance: float,
    relationship: str = "rear-to-rear",
    has_obscure_glazing: bool = False,
    has_high_level_window: bool = False,
) -> PrivacyAssessment:
    """
    Assess privacy distances against Policy DM6.6 standards.

    Standard distances:
    - Front-to-front: 21m (across street usually achieved)
    - Rear-to-rear: 21m between facing habitable room windows
    - Side-to-side: 12m to blank wall, 21m if both have windows
    """

    required_distances = {
        "front-to-front": 21.0,
        "rear-to-rear": 21.0,
        "side-to-side": 12.0,
        "side-to-rear": 21.0,
    }

    required = required_distances.get(relationship, 21.0)

    # Reduced standards may apply with mitigation
    mitigation = None
    if actual_distance < required:
        if has_obscure_glazing:
            mitigation = "Obscure glazing to non-habitable room windows"
            # Obscure glazing can reduce requirement for non-habitable rooms
        if has_high_level_window:
            mitigation = "High-level windows (1.7m+ above floor level)"
            # High level windows prevent direct overlooking

    compliant = actual_distance >= required or mitigation is not None

    notes = f"{relationship.replace('-', ' to ').title()}: {actual_distance}m actual vs {required}m required. "
    if compliant and actual_distance < required:
        notes += f"Acceptable with mitigation: {mitigation}."
    elif compliant:
        notes += "Complies with DM6.6 standards."
    else:
        notes += "Does not comply - unacceptable overlooking."

    return PrivacyAssessment(
        relationship=relationship,
        actual_distance=actual_distance,
        required_distance=required,
        compliant=compliant,
        mitigation=mitigation,
        notes=notes,
    )


def generate_visual_impact_assessment(
    development_width: float,
    development_depth: float,
    development_height: float,
    distance_to_north_boundary: float,
    distance_to_south_boundary: float,
    distance_to_east_boundary: float,
    distance_to_west_boundary: float,
    neighbour_window_heights: list[float] = None,
    orientation: str = "rear faces south",
) -> VisualImpactResult:
    """Generate comprehensive visual impact assessment with ASCII diagram."""

    if neighbour_window_heights is None:
        neighbour_window_heights = [2.0, 4.5]  # Ground and first floor windows

    daylight_tests = []
    privacy_tests = []
    recommendations = []

    # Daylight tests for each boundary direction
    for boundary_name, distance in [
        ("north", distance_to_north_boundary),
        ("south", distance_to_south_boundary),
        ("east", distance_to_east_boundary),
        ("west", distance_to_west_boundary),
    ]:
        for window_height in neighbour_window_heights:
            test = calculate_45_degree_test(
                neighbour_window_height=window_height,
                distance_to_development=distance,
                development_height=development_height,
            )
            test.neighbour_address = f"Neighbour to {boundary_name}"
            daylight_tests.append(test)

    # Privacy assessments
    privacy_tests.append(assess_privacy_distance(
        actual_distance=distance_to_south_boundary + 10,  # Assume 10m to neighbour's house
        relationship="rear-to-rear",
    ))
    privacy_tests.append(assess_privacy_distance(
        actual_distance=distance_to_east_boundary,
        relationship="side-to-side",
    ))
    privacy_tests.append(assess_privacy_distance(
        actual_distance=distance_to_west_boundary,
        relationship="side-to-side",
    ))

    # Overshadowing summary
    overshadowing = """**Overshadowing Assessment**

Based on BRE Guidelines, overshadowing impact is assessed for:
- Gardens: At least 50% should receive 2 hours sunlight on 21 March
- Windows: South-facing windows should retain reasonable sunlight access

"""
    if "south" in orientation.lower():
        overshadowing += "Development extends to rear (south). Main overshadowing impact will be on garden area to immediate north. "
    else:
        overshadowing += "Development orientation means limited overshadowing impact on neighbouring properties. "

    # Overbearing summary
    min_boundary = min(distance_to_north_boundary, distance_to_south_boundary,
                       distance_to_east_boundary, distance_to_west_boundary)

    if development_height > 2 * min_boundary:
        overbearing = "**Overbearing Impact: POTENTIAL CONCERN**\n\nDevelopment height exceeds 2x the distance to nearest boundary, which may result in overbearing impact."
        recommendations.append("Consider reducing height or increasing setback from boundary")
    else:
        overbearing = "**Overbearing Impact: ACCEPTABLE**\n\nDevelopment height is proportionate to boundary distances. No unacceptable overbearing impact."

    # Overall assessment
    daylight_passes = sum(1 for t in daylight_tests if t.passes_test)
    privacy_passes = sum(1 for t in privacy_tests if t.compliant)

    if daylight_passes == len(daylight_tests) and privacy_passes == len(privacy_tests):
        overall = "acceptable"
    elif daylight_passes >= len(daylight_tests) * 0.75 and privacy_passes >= len(privacy_tests) * 0.75:
        overall = "marginal"
        recommendations.append("Some aspects require careful consideration but overall acceptable")
    else:
        overall = "unacceptable"
        recommendations.append("Design amendments required to address amenity impacts")

    # Generate ASCII diagram
    diagram = generate_ascii_site_diagram(
        development_width=development_width,
        development_depth=development_depth,
        distance_to_north=distance_to_north_boundary,
        distance_to_south=distance_to_south_boundary,
        distance_to_east=distance_to_east_boundary,
        distance_to_west=distance_to_west_boundary,
    )

    return VisualImpactResult(
        daylight_assessments=daylight_tests,
        privacy_assessments=privacy_tests,
        overshadowing_summary=overshadowing,
        overbearing_summary=overbearing,
        overall_impact=overall,
        diagram_ascii=diagram,
        recommendations=recommendations,
    )


def generate_ascii_site_diagram(
    development_width: float,
    development_depth: float,
    distance_to_north: float,
    distance_to_south: float,
    distance_to_east: float,
    distance_to_west: float,
) -> str:
    """Generate ASCII site plan showing development and boundary distances."""

    diagram = """
```
SITE PLAN - BOUNDARY DISTANCES (Not to scale)

                    NORTH
                      |
         +---------------------------+
         |                           |
         |     {north}m to boundary       |
         |                           |
    W    |    +---------------+      |    E
    E    |    |               |      |    A
    S    |{west}m |  PROPOSED   | {east}m|    S
    T    |    |  DEVELOPMENT  |      |    T
         |    |   {w}m x {d}m    |      |
         |    +---------------+      |
         |                           |
         |     {south}m to boundary       |
         |                           |
         +---------------------------+
                      |
                    SOUTH


DIMENSIONS:
- Proposed development: {w}m (width) x {d}m (depth)
- Distance to north boundary: {north}m
- Distance to south boundary: {south}m
- Distance to east boundary: {east}m
- Distance to west boundary: {west}m

45-DEGREE TEST DIAGRAM:

    Neighbour's          Proposed
    window               development
    (2m high)            ({height}m high)
        |                    |
        |     45°           /
        |      \\          /
        |       \\        /
        |        \\      /
        |         \\    /
        |          \\  /
        |___________\\/_______________
              {dist}m

```
""".format(
        w=development_width,
        d=development_depth,
        north=distance_to_north,
        south=distance_to_south,
        east=distance_to_east,
        west=distance_to_west,
        height=max(3.0, development_depth * 0.5),  # Estimate
        dist=min(distance_to_north, distance_to_south, distance_to_east, distance_to_west),
    )

    return diagram


def format_visual_impact_section(assessment: VisualImpactResult) -> str:
    """Format the visual impact assessment for the report."""

    lines = []
    lines.append("## VISUAL IMPACT ASSESSMENT")
    lines.append("")
    lines.append("> **BRE Guidelines and Policy DM6.6 Assessment**")
    lines.append("")

    # Diagram
    lines.append("### Site Plan and Measurements")
    lines.append(assessment.diagram_ascii)
    lines.append("")

    # Daylight assessment
    lines.append("### Daylight Assessment (45-Degree Test)")
    lines.append("")
    lines.append("| Neighbour | Window | Distance | Dev Height | Angle | Result |")
    lines.append("|-----------|--------|----------|------------|-------|--------|")

    for test in assessment.daylight_assessments[:8]:  # Limit to 8 tests
        result = "PASS" if test.passes_test else "FAIL"
        lines.append(f"| {test.neighbour_address} | {test.window_position} | {test.distance_to_development}m | {test.development_height}m | {test.angle_subtended:.0f}° | {result} |")

    lines.append("")

    # Privacy assessment
    lines.append("### Privacy Assessment (Policy DM6.6)")
    lines.append("")
    lines.append("| Relationship | Actual | Required | Compliant | Mitigation |")
    lines.append("|--------------|--------|----------|-----------|------------|")

    for test in assessment.privacy_assessments:
        compliant = "Yes" if test.compliant else "NO"
        mitigation = test.mitigation or "-"
        lines.append(f"| {test.relationship} | {test.actual_distance}m | {test.required_distance}m | {compliant} | {mitigation[:30]} |")

    lines.append("")

    # Overshadowing
    lines.append(assessment.overshadowing_summary)
    lines.append("")

    # Overbearing
    lines.append(assessment.overbearing_summary)
    lines.append("")

    # Overall
    lines.append(f"### Overall Visual Impact: **{assessment.overall_impact.upper()}**")
    lines.append("")

    if assessment.recommendations:
        lines.append("**Recommendations:**")
        for rec in assessment.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    return "\n".join(lines)
