"""
Broxtowe Borough Council Policy Engine.

Development Plan for Broxtowe:
1. Greater Nottingham Aligned Core Strategy (2014) - Part 1
2. Broxtowe Part 2 Local Plan (2019) - Part 2

Together with the NPPF, these form the policy basis for planning decisions.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class BroxtowePolicy:
    """A policy from the Broxtowe Development Plan."""
    id: str
    name: str
    source: str  # "ACS" (Aligned Core Strategy) or "Part2" (Part 2 Local Plan)
    source_full: str
    text: str
    key_requirements: list[str]
    triggers: list[str]  # Keywords that indicate this policy applies


# =============================================================================
# GREATER NOTTINGHAM ALIGNED CORE STRATEGY (2014) - PART 1
# =============================================================================

ALIGNED_CORE_STRATEGY_POLICIES = [
    BroxtowePolicy(
        id="ACS-1",
        name="Climate Change",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="Development will be designed to reduce the causes and impacts of climate change through high quality sustainable design and construction.",
        key_requirements=[
            "Sustainable design and construction",
            "Energy efficiency measures",
            "Renewable energy where appropriate",
            "Climate adaptation measures",
        ],
        triggers=["climate", "sustainable", "energy", "carbon", "renewable"],
    ),
    BroxtowePolicy(
        id="ACS-2",
        name="The Spatial Strategy",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="The priority for development in Broxtowe is in or adjoining the main built up area of Nottingham. The settlement hierarchy identifies: Sub-Regional Centre (Nottingham City Centre), Town Centres, District Centres, Local Centres, and other urban areas.",
        key_requirements=[
            "Development prioritised in sustainable locations",
            "Respect settlement hierarchy",
            "Focus on main built up areas",
            "Protect Green Belt",
        ],
        triggers=["location", "settlement", "sustainable", "urban", "green belt"],
    ),
    BroxtowePolicy(
        id="ACS-8",
        name="Housing Size, Mix and Choice",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="Residential development should maintain, provide and contribute to a mix of housing tenures, types and sizes in order to create mixed and balanced communities. The appropriate mix will be assessed on a site by site basis.",
        key_requirements=[
            "Mix of housing types and sizes",
            "Meet local housing needs",
            "Affordable housing provision where required",
            "Accessible and adaptable homes",
        ],
        triggers=["housing", "residential", "dwelling", "affordable", "mix"],
    ),
    BroxtowePolicy(
        id="ACS-10",
        name="Design and Enhancing Local Identity",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="""Development will be assessed in terms of its treatment of:
a) Structure, texture and grain including street patterns, plot sizes and orientation of buildings
b) Density and mix
c) Massing, scale and proportion
d) Materials, architectural style and detailing
e) Impact on the amenity of nearby residents or occupiers
f) The need to reduce opportunities for crime
g) Landscape treatment
h) Legacy arrangements including the consideration of future management and maintenance
i) Views and vistas.""",
        key_requirements=[
            "High quality design that responds to context",
            "Appropriate scale, massing and materials",
            "Protection of amenity",
            "Consideration of landscape and views",
            "Designing out crime",
        ],
        triggers=["design", "appearance", "scale", "massing", "materials", "character", "amenity", "views"],
    ),
    BroxtowePolicy(
        id="ACS-11",
        name="The Historic Environment",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="""Proposals and initiatives will be supported where the historic environment and heritage assets and their settings are conserved and/or enhanced in line with their interest and significance. Planning decisions will have regard to:
a) Protecting the significance of heritage assets (including where relevant their setting)
b) Maximising opportunities to sustain and enhance the significance of heritage assets and to better reveal the contribution that they make
c) Conservation Area Appraisals and Management Plans
d) Development that would result in harm to heritage assets will require clear and convincing justification.""",
        key_requirements=[
            "Conserve and enhance heritage assets",
            "Protect significance and setting",
            "Clear justification for any harm",
            "Respect Conservation Area character",
            "Have regard to listed building significance",
        ],
        triggers=["heritage", "listed", "conservation", "historic", "character", "significance", "setting"],
    ),
    BroxtowePolicy(
        id="ACS-12",
        name="Local Services and Healthy Lifestyles",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="The provision and enhancement of local services and facilities, including community facilities, education, health facilities, cultural and leisure facilities will be supported where they meet identified needs.",
        key_requirements=[
            "Support for local services and facilities",
            "Meet identified community needs",
            "Promote healthy lifestyles",
        ],
        triggers=["community", "health", "education", "leisure", "facilities", "services"],
    ),
    BroxtowePolicy(
        id="ACS-14",
        name="Managing Travel Demand",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="The need to travel will be reduced by securing new development in sustainable locations with good access to key services and facilities, and by requiring that new development provides access to sustainable transport.",
        key_requirements=[
            "Sustainable locations",
            "Good access to services",
            "Promote sustainable transport",
            "Appropriate parking provision",
        ],
        triggers=["transport", "parking", "highway", "access", "travel", "sustainable"],
    ),
    BroxtowePolicy(
        id="ACS-16",
        name="Green Infrastructure, Parks and Open Space",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="A strategic approach to the delivery, protection and enhancement of Green Infrastructure will be taken. Development proposals that would compromise the Green Belt will be refused except where a robust case can be demonstrated for very special circumstances.",
        key_requirements=[
            "Protect Green Belt openness",
            "Enhance green infrastructure",
            "Protect open space",
            "Maintain ecological networks",
        ],
        triggers=["green belt", "open space", "green infrastructure", "park", "recreation", "ecology"],
    ),
    BroxtowePolicy(
        id="ACS-17",
        name="Biodiversity",
        source="ACS",
        source_full="Greater Nottingham Aligned Core Strategy (2014)",
        text="The biodiversity of the area will be increased by: protecting, enhancing, restoring and expanding sites of biological and geological importance; requiring development to provide for appropriate species and habitat protection, and where required mitigation, with a net gain in biodiversity being secured.",
        key_requirements=[
            "Protect biodiversity",
            "Net gain in biodiversity",
            "Protect and enhance habitats",
            "Species protection and mitigation",
        ],
        triggers=["biodiversity", "ecology", "wildlife", "habitat", "species", "trees", "protected"],
    ),
]


# =============================================================================
# BROXTOWE PART 2 LOCAL PLAN (2019)
# =============================================================================

PART2_LOCAL_PLAN_POLICIES = [
    BroxtowePolicy(
        id="Policy-1",
        name="Flood Risk",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Planning permission will not be granted for development in areas at risk of flooding, or development that may increase the risk of flooding elsewhere, unless appropriate flood mitigation measures are incorporated.",
        key_requirements=[
            "Sequential test applied",
            "Exception test where required",
            "Flood mitigation measures",
            "No increased flood risk elsewhere",
        ],
        triggers=["flood", "drainage", "watercourse", "water"],
    ),
    BroxtowePolicy(
        id="Policy-8",
        name="Development in the Green Belt",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="""Planning permission will not be granted for inappropriate development in the Green Belt except in very special circumstances. Extensions and alterations to dwellings will be permitted provided that they:
a) Do not result in disproportionate additions over and above the size of the original building
b) Do not have a materially greater impact on the openness of the Green Belt.""",
        key_requirements=[
            "No inappropriate development",
            "Extensions not disproportionate",
            "Maintain Green Belt openness",
            "Very special circumstances if inappropriate",
        ],
        triggers=["green belt", "openness", "extension", "countryside"],
    ),
    BroxtowePolicy(
        id="Policy-15",
        name="Housing Size, Mix and Choice",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Residential development should provide an appropriate mix of housing types and sizes to meet local needs. All new residential development should meet minimum space standards and accessibility requirements.",
        key_requirements=[
            "Appropriate housing mix",
            "Meet minimum space standards",
            "Accessibility requirements",
            "Meet local needs",
        ],
        triggers=["housing", "residential", "bedroom", "dwelling", "flat", "apartment"],
    ),
    BroxtowePolicy(
        id="Policy-17",
        name="Place-making, Design and Amenity",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="""Permission will be granted for development which:
a) Creates or contributes to a place which has a clear and legible character
b) Protects the amenity of the area including residential amenity in terms of noise, odour, air quality, light intrusion, overlooking, shadowing or other adverse impacts
c) Provides adequate amenity for future occupiers
d) Uses high quality materials appropriate to the character of the area
e) Provides attractive, safe and convenient access for all users
f) Includes landscaping and boundary treatments which create an attractive setting.""",
        key_requirements=[
            "High quality design",
            "Protect residential amenity",
            "No unacceptable overlooking",
            "No unacceptable shadowing",
            "Appropriate materials",
            "Adequate amenity for occupiers",
        ],
        triggers=["design", "amenity", "privacy", "overlooking", "daylight", "materials", "boundary", "landscaping"],
    ),
    BroxtowePolicy(
        id="Policy-19",
        name="Pollution, Hazardous Substances and Ground Conditions",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development will be permitted where the potential for land contamination has been addressed. Development that would expose occupiers to unacceptable levels of pollution will not be permitted.",
        key_requirements=[
            "Land contamination addressed",
            "No unacceptable pollution",
            "Appropriate mitigation measures",
        ],
        triggers=["contamination", "pollution", "noise", "air quality", "ground conditions"],
    ),
    BroxtowePolicy(
        id="Policy-20",
        name="Air Quality",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development will be required to take account of air quality. Development that would result in significant harm to air quality will not be permitted.",
        key_requirements=[
            "Consider air quality impacts",
            "No significant harm to air quality",
            "Appropriate mitigation",
        ],
        triggers=["air quality", "pollution", "emissions"],
    ),
    BroxtowePolicy(
        id="Policy-21",
        name="Biodiversity",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development proposals should seek to protect and enhance biodiversity, including securing a net gain in biodiversity. Development should avoid harm to biodiversity; where harm cannot be avoided, it should be mitigated or, as a last resort, compensated for.",
        key_requirements=[
            "Protect and enhance biodiversity",
            "Net gain in biodiversity",
            "Avoid harm to habitats",
            "Mitigation hierarchy applied",
        ],
        triggers=["biodiversity", "ecology", "trees", "wildlife", "habitat", "protected species"],
    ),
    BroxtowePolicy(
        id="Policy-22",
        name="Minerals",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development will be required to safeguard mineral resources from unnecessary sterilisation.",
        key_requirements=[
            "Safeguard mineral resources",
        ],
        triggers=["minerals", "extraction"],
    ),
    BroxtowePolicy(
        id="Policy-23",
        name="Proposals Affecting Designated and Non-Designated Heritage Assets",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="""Planning permission will be granted for development affecting heritage assets, including alterations and extensions to Listed Buildings and development within Conservation Areas, provided that:
a) The significance of the heritage asset is sustained and enhanced
b) The proposals would not cause harm to the significance of the heritage asset or its setting
c) Where some harm is caused, this is clearly outweighed by public benefits
d) Features which contribute to the character of the Conservation Area are preserved or enhanced
e) Development would not adversely affect the character or setting of the Conservation Area
f) Development of Listed Buildings is compatible with their character and significance.""",
        key_requirements=[
            "Sustain and enhance heritage significance",
            "Protect significance and setting",
            "Public benefits weighed against harm",
            "Preserve Conservation Area character",
            "Compatible with Listed Building character",
        ],
        triggers=["heritage", "listed", "conservation", "historic", "significance", "character", "setting", "grade"],
    ),
    BroxtowePolicy(
        id="Policy-24",
        name="The Health and Wellbeing of Residents",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development should promote the health and wellbeing of future occupiers and should not have an unacceptable impact on the health of existing residents.",
        key_requirements=[
            "Promote health and wellbeing",
            "No unacceptable health impacts",
        ],
        triggers=["health", "wellbeing", "amenity"],
    ),
    BroxtowePolicy(
        id="Policy-26",
        name="Travel Plans",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development proposals that generate significant amounts of movement should be accompanied by a Travel Plan to encourage sustainable travel.",
        key_requirements=[
            "Travel Plan for major development",
            "Promote sustainable travel",
        ],
        triggers=["travel", "transport", "trip generation"],
    ),
    BroxtowePolicy(
        id="Policy-27",
        name="Local Green Space",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development affecting Local Green Spaces will only be permitted in very special circumstances.",
        key_requirements=[
            "Protect Local Green Space",
            "Very special circumstances required",
        ],
        triggers=["local green space", "open space"],
    ),
    BroxtowePolicy(
        id="Policy-30",
        name="Landscape",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Development should have regard to landscape character and should protect and enhance important landscape features. Development should not have an unacceptable impact on landscape character.",
        key_requirements=[
            "Protect landscape character",
            "Enhance important features",
            "No unacceptable landscape impact",
        ],
        triggers=["landscape", "trees", "hedgerows", "views", "countryside"],
    ),
    BroxtowePolicy(
        id="Policy-31",
        name="Shopfronts, Signage and Security",
        source="Part2",
        source_full="Broxtowe Part 2 Local Plan (2019)",
        text="Shopfronts, signage and security measures should be of good quality design that respects the character of the building and area.",
        key_requirements=[
            "Good quality design",
            "Respect building character",
            "Appropriate signage",
        ],
        triggers=["shopfront", "signage", "advertisement", "shop", "retail"],
    ),
]


# Combine all policies
BROXTOWE_POLICIES = ALIGNED_CORE_STRATEGY_POLICIES + PART2_LOCAL_PLAN_POLICIES


def get_broxtowe_policies(
    proposal: str,
    application_type: str,
    constraints: list[str],
) -> list[BroxtowePolicy]:
    """
    Get relevant Broxtowe policies for a proposal.

    Args:
        proposal: The proposal description
        application_type: Type of application
        constraints: Site constraints

    Returns:
        List of relevant policies ordered by relevance
    """
    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]
    app_type_lower = application_type.lower()

    relevant = []
    scored = []

    for policy in BROXTOWE_POLICIES:
        score = 0

        # Check triggers against proposal
        for trigger in policy.triggers:
            if trigger in proposal_lower:
                score += 2

        # Check triggers against constraints
        for trigger in policy.triggers:
            for constraint in constraints_lower:
                if trigger in constraint:
                    score += 3  # Higher weight for constraint matches

        # Check triggers against application type
        for trigger in policy.triggers:
            if trigger in app_type_lower:
                score += 1

        # Always include core design and amenity policies
        if policy.id in ["ACS-10", "ACS-11", "Policy-17", "Policy-23"]:
            score += 1  # Ensure these are always considered

        # Heritage policies for heritage constraints
        if any("conservation" in c or "listed" in c for c in constraints_lower):
            if policy.id in ["ACS-11", "Policy-23"]:
                score += 5

        # Green Belt policies
        if any("green belt" in c for c in constraints_lower):
            if policy.id in ["ACS-16", "Policy-8"]:
                score += 5

        if score > 0:
            scored.append((policy, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return top policies
    return [p for p, s in scored[:12]]


def get_policy_citation(policy_id: str) -> str:
    """Get a citation string for a policy."""
    for policy in BROXTOWE_POLICIES:
        if policy.id == policy_id:
            return f"{policy.source_full} {policy.id} ({policy.name})"
    return policy_id
