"""
Complete Local Plans Database.

Comprehensive policy database for multiple Local Planning Authorities including:
- Newcastle City Council (Core Strategy 2015, DAP 2022)
- Broxtowe Borough Council (Aligned Core Strategy 2014, Part 2 Local Plan 2019)

Each policy includes full text, relevance triggers, and proper citation information.
"""

from typing import Any

# =============================================================================
# NEWCASTLE CITY COUNCIL LOCAL PLAN
# =============================================================================

NEWCASTLE_LOCAL_PLAN = {
    "council_id": "newcastle",
    "council_name": "Newcastle City Council",
    "plans": [
        {
            "name": "Core Strategy and Urban Core Plan",
            "adopted": "2015",
            "status": "Adopted",
        },
        {
            "name": "Development and Allocations Plan",
            "adopted": "2022",
            "status": "Adopted",
        },
    ],
    "policies": {
        # =====================================================================
        # CORE STRATEGY POLICIES
        # =====================================================================
        "CS1": {
            "id": "CS1",
            "name": "Spatial Strategy for Sustainable Growth",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Strategic Policies",
            "page": "45-48",
            "text": "The majority of new development will be located within the urban area of Newcastle and Gateshead. Development will be directed to the most sustainable and accessible locations, primarily within the Urban Core, and at locations well served by public transport.",
            "relevance_triggers": ["strategic", "location", "sustainable"],
        },
        "CS5": {
            "id": "CS5",
            "name": "Employment",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Employment",
            "page": "62-65",
            "text": "Sufficient land will be made available to meet the employment needs of the area. A range of employment sites will be protected and allocated to meet the needs of different sectors.",
            "relevance_triggers": ["employment", "office", "industrial", "commercial"],
        },
        "CS11": {
            "id": "CS11",
            "name": "Providing a Range and Choice of Housing",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Housing",
            "page": "78-82",
            "text": "The plan will ensure the delivery of a range of housing types, sizes and tenures to meet the needs of existing and future households. Residential development should provide an appropriate mix of dwelling types and sizes to meet identified needs.",
            "relevance_triggers": ["housing", "residential", "dwelling", "mix"],
        },
        "CS12": {
            "id": "CS12",
            "name": "Affordable Housing",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Housing",
            "page": "83-86",
            "text": "Affordable housing will be sought on residential developments of 10 or more units or sites of 0.5 hectares or more. The target is 15% affordable housing on qualifying sites in Newcastle. The tenure split should be 70% social/affordable rent and 30% intermediate housing unless evidence demonstrates otherwise.",
            "relevance_triggers": ["affordable housing", "housing", "major"],
        },
        "CS13": {
            "id": "CS13",
            "name": "Student Housing",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Housing",
            "page": "87-89",
            "text": "Purpose built student accommodation will be directed to the most sustainable and accessible locations, primarily within the Urban Core. Development should not result in an over-concentration of student housing that would harm the character or amenity of an area.",
            "relevance_triggers": ["student", "student accommodation", "university"],
        },
        "CS14": {
            "id": "CS14",
            "name": "Wellbeing and Health",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Community",
            "page": "90-93",
            "text": "New development should contribute to creating an age-friendly city that promotes health and wellbeing. Development should provide or contribute to healthcare, education and community facilities where there is identified need.",
            "relevance_triggers": ["health", "community", "education", "infrastructure"],
        },
        "CS15": {
            "id": "CS15",
            "name": "Place-making",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Design",
            "page": "94-98",
            "text": "Development will be required to contribute to good place-making through the delivery of high quality and sustainable design, and by responding positively to local distinctiveness and character. Development should create attractive and safe environments, with clear and legible layouts, and should protect and enhance existing positive characteristics.",
            "relevance_triggers": ["design", "place-making", "character", "all"],
        },
        "CS16": {
            "id": "CS16",
            "name": "Climate Change",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Environment",
            "page": "99-103",
            "text": "Development will be required to mitigate and adapt to climate change. Development should minimise carbon emissions through energy efficient design, incorporate sustainable drainage systems, and be designed to be resilient to the effects of climate change.",
            "relevance_triggers": ["climate", "sustainability", "energy", "flood", "drainage"],
        },
        "CS17": {
            "id": "CS17",
            "name": "Flood Risk and Water Management",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Environment",
            "page": "104-108",
            "text": "Development will be required to minimise flood risk and manage surface water sustainably. A sequential approach to development in areas at risk of flooding will be applied. All major developments should incorporate sustainable drainage systems (SuDS).",
            "relevance_triggers": ["flood", "drainage", "suds", "water"],
        },
        "CS18": {
            "id": "CS18",
            "name": "Green Infrastructure and the Natural Environment",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Environment",
            "page": "109-114",
            "text": "Development will be required to maintain, protect and enhance green infrastructure and biodiversity. The integrity of wildlife corridors and the Strategic Green Infrastructure Network will be maintained. Development should deliver net gains for biodiversity.",
            "relevance_triggers": ["green infrastructure", "biodiversity", "ecology", "wildlife", "trees"],
        },
        "CS19": {
            "id": "CS19",
            "name": "Heritage and Conservation",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Heritage",
            "page": "115-120",
            "text": "Newcastle's heritage assets will be protected, preserved and enhanced. Development affecting heritage assets should sustain and enhance their significance. Opportunities to better reveal the significance of heritage assets will be supported.",
            "relevance_triggers": ["heritage", "conservation area", "listed building", "historic"],
        },

        # =====================================================================
        # DEVELOPMENT AND ALLOCATIONS PLAN (DAP) POLICIES
        # =====================================================================
        "DM1": {
            "id": "DM1",
            "name": "Sustainable Development",
            "source": "Development and Allocations Plan (2022)",
            "section": "Strategic",
            "page": "24-26",
            "text": "When considering development proposals, the Council will take a positive approach that reflects the presumption in favour of sustainable development contained in the National Planning Policy Framework. Development proposals that accord with the policies of the Development Plan will be approved without delay.",
            "relevance_triggers": ["all", "sustainable"],
        },
        "DM5": {
            "id": "DM5",
            "name": "Pollution and Land Stability",
            "source": "Development and Allocations Plan (2022)",
            "section": "Environment",
            "page": "42-46",
            "text": "Development will not be permitted where it would cause unacceptable levels of pollution or where it would be adversely affected by existing sources of pollution. Development on or near land that is potentially contaminated will require appropriate investigation and, where necessary, remediation. Development should not result in unacceptable levels of noise, vibration, light, air or water pollution.",
            "relevance_triggers": ["pollution", "contamination", "noise", "air quality"],
        },
        "DM6.1": {
            "id": "DM6.1",
            "name": "Design of New Development",
            "source": "Development and Allocations Plan (2022)",
            "section": "Design",
            "page": "48-54",
            "text": "Proposals will be required to demonstrate a positive response to the following urban design principles: response to context, positive contribution to place, creation of a coherent urban form, appropriate scale and massing, and active frontages. Development should respond to the local vernacular, including building forms, materials, and detailing.",
            "relevance_triggers": ["design", "all"],
        },
        "DM6.2": {
            "id": "DM6.2",
            "name": "Public Realm",
            "source": "Development and Allocations Plan (2022)",
            "section": "Design",
            "page": "55-58",
            "text": "Development should create high quality public realm that is accessible, safe and inclusive. The design of streets and spaces should promote pedestrian and cyclist priority, minimise vehicle dominance, and create attractive environments.",
            "relevance_triggers": ["public realm", "street", "design"],
        },
        "DM6.3": {
            "id": "DM6.3",
            "name": "Masterplanning and Design Statements",
            "source": "Development and Allocations Plan (2022)",
            "section": "Design",
            "page": "59-61",
            "text": "Major development proposals should be accompanied by a Design and Access Statement that demonstrates how the proposal responds to its context and achieves high quality design. Large-scale developments should be the subject of a masterplan.",
            "relevance_triggers": ["masterplan", "design", "major"],
        },
        "DM6.4": {
            "id": "DM6.4",
            "name": "Accessible and Adaptable Buildings",
            "source": "Development and Allocations Plan (2022)",
            "section": "Design",
            "page": "62-64",
            "text": "New housing developments should be designed to be accessible and adaptable in accordance with Building Regulations M4(2). A proportion of dwellings should be wheelchair accessible M4(3) on larger sites.",
            "relevance_triggers": ["accessible", "adaptable", "housing"],
        },
        "DM6.5": {
            "id": "DM6.5",
            "name": "National Space Standards",
            "source": "Development and Allocations Plan (2022)",
            "section": "Design",
            "page": "65-67",
            "text": "New residential development should meet the Nationally Described Space Standard. The minimum gross internal floor areas and storage requirements set out in the Standard will apply to all new dwellings.",
            "relevance_triggers": ["space standards", "housing", "residential"],
        },
        "DM6.6": {
            "id": "DM6.6",
            "name": "Protection of Residential Amenity",
            "source": "Development and Allocations Plan (2022)",
            "section": "Amenity",
            "page": "68-74",
            "text": """Development proposals will be required to ensure that existing and future occupiers of land and buildings are provided with a good standard of amenity in terms of daylight, sunlight, outlook, privacy, noise, and disturbance.

QUANTITATIVE STANDARDS:
- Privacy: A minimum separation distance of 21 metres between facing habitable room windows
- Privacy (side): A minimum of 12 metres to a blank wall or non-habitable room window
- Daylight: The 45-degree test should be applied to assess impact on daylight to existing windows
- Sunlight: Development should not result in significant overshadowing of neighbouring gardens
- Private amenity space: Houses should have a private garden of at least 50sqm

QUALITATIVE FACTORS:
- Outlook: Development should not result in an unacceptably oppressive or overbearing impact
- Noise: Development should not result in unacceptable noise and disturbance
- Light pollution: External lighting should be designed to minimise light spill""",
            "relevance_triggers": ["amenity", "residential", "privacy", "daylight", "extension"],
        },
        "DM7": {
            "id": "DM7",
            "name": "Transport and Highways",
            "source": "Development and Allocations Plan (2022)",
            "section": "Transport",
            "page": "76-84",
            "text": """Development will be required to provide safe and suitable access for all users. Proposals should not have an unacceptable impact on highway safety or result in severe residual cumulative impacts on the road network.

PARKING STANDARDS:
- Zone 1 (City Centre): Car-free or minimal parking encouraged
- Zone 2 (Inner Areas): Maximum 1 space per dwelling
- Zone 3 (Outer Areas): Maximum 1.5 spaces per dwelling
- Cycle parking: 1 secure covered space per bedroom

TRANSPORT ASSESSMENTS:
- Transport Statement required for developments generating 30-80 vehicle trips per day
- Transport Assessment required for developments generating 80+ vehicle trips per day
- Travel Plan required for major developments""",
            "relevance_triggers": ["transport", "highway", "parking", "access"],
        },
        "DM15": {
            "id": "DM15",
            "name": "Conservation of Heritage Assets",
            "source": "Development and Allocations Plan (2022)",
            "section": "Heritage",
            "page": "112-118",
            "text": """Proposals affecting a heritage asset will be permitted where they sustain, conserve and, where appropriate, enhance the significance, appearance, character and setting of heritage assets and their contribution to local distinctiveness, character and sense of place.

DESIGNATED HERITAGE ASSETS:
- Great weight will be given to the conservation of designated heritage assets
- Any harm to significance requires clear and convincing justification
- Substantial harm should be exceptional/wholly exceptional (Grade I/II*)
- Less than substantial harm must be weighed against public benefits

SETTING:
- Development within the setting of a heritage asset should preserve or enhance its significance
- Key views and the contribution of setting to significance must be considered""",
            "relevance_triggers": ["heritage", "conservation area", "listed building"],
        },
        "DM16": {
            "id": "DM16",
            "name": "Conservation Areas",
            "source": "Development and Allocations Plan (2022)",
            "section": "Heritage",
            "page": "119-124",
            "text": """Development within or affecting the setting of a conservation area will be permitted where it preserves or enhances the character or appearance of the conservation area.

STATUTORY DUTY (Section 72 P(LBCA)A 1990):
Special attention shall be paid to the desirability of preserving or enhancing the character or appearance of conservation areas.

ASSESSMENT CRITERIA:
- Scale, form, massing and height in relation to neighbouring buildings
- Materials and architectural details
- Impact on important views and vistas
- Contribution to the special character and appearance
- Impact on trees and landscape features

DEMOLITION:
- Demolition of buildings that make a positive contribution will only be permitted in exceptional circumstances
- A robust justification for demolition must be provided
- Replacement buildings must preserve or enhance character and appearance""",
            "relevance_triggers": ["conservation area"],
        },
        "DM17": {
            "id": "DM17",
            "name": "Locally Listed Buildings and Non-Designated Heritage Assets",
            "source": "Development and Allocations Plan (2022)",
            "section": "Heritage",
            "page": "125-128",
            "text": """Development affecting a non-designated heritage asset will require a balanced judgement having regard to the scale of any harm or loss and the significance of the heritage asset (NPPF Para 203).

LOCAL LIST CRITERIA:
- Architectural interest
- Historic interest
- Close historical association with notable persons or events
- Group value
- Townscape value
- Social and communal value

ASSESSMENT:
- The significance of the asset should be described proportionate to its importance
- Direct and indirect impacts should be assessed
- Harm should be weighed against public benefits""",
            "relevance_triggers": ["locally listed", "non-designated heritage", "heritage"],
        },
        "DM27": {
            "id": "DM27",
            "name": "Open Space",
            "source": "Development and Allocations Plan (2022)",
            "section": "Green Infrastructure",
            "page": "156-162",
            "text": "Development should protect, enhance and provide open space. New residential development of 10 or more dwellings should provide open space on site or contribute to off-site provision. The standard is 4.16 hectares per 1,000 population.",
            "relevance_triggers": ["open space", "green space", "recreation"],
        },
        "DM28": {
            "id": "DM28",
            "name": "Trees, Woodlands and Hedgerows",
            "source": "Development and Allocations Plan (2022)",
            "section": "Green Infrastructure",
            "page": "163-170",
            "text": """Development will be required to protect existing trees, woodlands and hedgerows that contribute to the quality and character of an area.

TREE PROTECTION:
- Trees covered by TPO must be retained unless removal is justified
- Development should be designed to retain trees of amenity value
- Root protection areas must be safeguarded during construction
- Arboricultural Impact Assessment required where trees are affected

REPLACEMENT PLANTING:
- Where tree loss is unavoidable, replacement planting will be required
- Replacement ratio should be at least 2:1 for native species
- New trees should be of appropriate species and size

HEDGEROWS:
- Important hedgerows (under the Hedgerows Regulations 1997) should be retained
- Where removal is unavoidable, compensatory planting is required""",
            "relevance_triggers": ["tree", "tpo", "woodland", "hedgerow", "landscaping"],
        },
        "DM29": {
            "id": "DM29",
            "name": "Biodiversity and Geodiversity",
            "source": "Development and Allocations Plan (2022)",
            "section": "Green Infrastructure",
            "page": "171-178",
            "text": """Development should protect and enhance biodiversity. A net gain in biodiversity will be sought from all development.

HIERARCHY OF SITES:
1. International (SAC, SPA, Ramsar) - Highest protection
2. National (SSSI) - Development should not normally be permitted if adverse impact
3. Local (LWS, LNR) - Development should avoid, mitigate or compensate for impacts

BIODIVERSITY NET GAIN:
- Minimum 10% net gain required (mandatory from 2024)
- Calculated using Defra Biodiversity Metric
- On-site delivery preferred; off-site or credits as last resort
- 30-year management and monitoring required

PROTECTED SPECIES:
- Surveys required where protected species may be present
- Mitigation hierarchy: avoid, mitigate, compensate
- Licences may be required from Natural England""",
            "relevance_triggers": ["biodiversity", "ecology", "wildlife", "protected species"],
        },
    },
}


# =============================================================================
# BROXTOWE BOROUGH COUNCIL LOCAL PLAN (NOTTINGHAMSHIRE)
# =============================================================================

BROXTOWE_LOCAL_PLAN = {
    "council_id": "broxtowe",
    "council_name": "Broxtowe Borough Council",
    "plans": [
        {
            "name": "Part 1: Greater Nottingham Aligned Core Strategy",
            "adopted": "2014",
            "status": "Adopted",
        },
        {
            "name": "Part 2: Local Plan",
            "adopted": "2019",
            "status": "Adopted",
        },
    ],
    "policies": {
        # =====================================================================
        # ALIGNED CORE STRATEGY (PART 1) POLICIES
        # =====================================================================
        "ACS-A": {
            "id": "Policy A",
            "name": "Presumption in Favour of Sustainable Development",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "18",
            "text": "When considering development proposals the Council will take a positive approach that reflects the presumption in favour of sustainable development contained in the National Planning Policy Framework. The Council will work proactively with applicants jointly to find solutions which mean that proposals can be approved wherever possible, and to secure development that improves the economic, social and environmental conditions in the area.",
            "relevance_triggers": ["all", "sustainable"],
        },
        "ACS-1": {
            "id": "Policy 1",
            "name": "Climate Change",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "20-24",
            "text": """Development will be required to mitigate against and adapt to climate change.

MITIGATION:
a) Giving priority to development on previously developed land, particularly in urban regeneration areas
b) Locating development in accessible locations to reduce the need to travel
c) Promoting sustainable transport choices
d) Requiring new development to achieve the highest viable standards of energy efficiency
e) Generating renewable or low carbon energy where appropriate

ADAPTATION:
f) Incorporating sustainable drainage systems (SuDS)
g) Including green infrastructure to reduce urban heat island effects
h) Designing buildings to be resilient to climate change impacts""",
            "relevance_triggers": ["climate", "sustainability", "energy", "flood"],
        },
        "ACS-2": {
            "id": "Policy 2",
            "name": "The Spatial Strategy",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "26-32",
            "text": "The principal focus will be for urban concentration with development in and adjoining the main built up area of Nottingham, with an appropriate level of new development in the Key Settlements of Beeston, Stapleford, Eastwood and Kimberley. Development in other locations will be limited to meeting local needs.",
            "relevance_triggers": ["strategic", "location"],
        },
        "ACS-3": {
            "id": "Policy 3",
            "name": "The Green Belt",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "34-38",
            "text": """The principle of the Nottingham-Derby Green Belt will be retained. The detailed boundaries of the Green Belt will only be altered where exceptional circumstances can be demonstrated.

GREEN BELT PURPOSES:
a) To check the unrestricted sprawl of the Nottingham built up area
b) To prevent the merging of settlements in the plan area
c) To assist in safeguarding the countryside from encroachment
d) To preserve the setting and special character of the settlements within the Green Belt
e) To assist in urban regeneration, by encouraging the recycling of derelict and other urban land

SAFEGUARDED LAND:
Land between the urban area and the Green Belt may be identified as Safeguarded Land for future development needs.""",
            "relevance_triggers": ["green belt"],
        },
        "ACS-8": {
            "id": "Policy 8",
            "name": "Housing Size, Mix and Choice",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Housing",
            "page": "56-60",
            "text": """Residential development should maintain, provide and contribute to a mix of housing types, sizes and tenures.

HOUSING MIX:
- A mix of house types and sizes should be provided on larger sites
- The mix should respond to the Strategic Housing Market Assessment
- Adaptable and accessible homes should be provided

AFFORDABLE HOUSING:
- Affordable housing will be sought on sites of 10 or more dwellings
- Target of 30% affordable housing (subject to viability)
- Tenure split to meet identified needs (typically 70/30 social rent/intermediate)

SELF-BUILD AND CUSTOM HOUSEBUILDING:
- Opportunities for self-build and custom housebuilding should be considered""",
            "relevance_triggers": ["housing", "residential", "affordable housing"],
        },
        "ACS-10": {
            "id": "Policy 10",
            "name": "Design and Enhancing Local Identity",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Design",
            "page": "68-74",
            "text": """All new development should be designed to:

DESIGN PRINCIPLES:
a) Create an attractive, safe and distinctive environment
b) Reinforce valued local characteristics
c) Be adaptable to meet changing needs
d) Create well-defined and legible streets and spaces
e) Provide appropriate landscaping
f) Minimise opportunities for crime
g) Provide sufficient, well-integrated parking
h) Be accessible to all users

CONSERVATION AND HERITAGE:
i) Conserve and enhance the significance of heritage assets and their settings
j) Protect and enhance locally important heritage assets
k) Preserve or enhance the character or appearance of Conservation Areas""",
            "relevance_triggers": ["design", "character", "all"],
        },
        "ACS-11": {
            "id": "Policy 11",
            "name": "The Historic Environment",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Heritage",
            "page": "76-80",
            "text": """The historic environment will be conserved and enhanced.

DESIGNATED HERITAGE ASSETS:
- Great weight will be given to the conservation of designated heritage assets
- Development should sustain and enhance the significance of heritage assets
- Proposals affecting a heritage asset must describe its significance

CONSERVATION AREAS:
- Development within or affecting a Conservation Area should preserve or enhance its character or appearance
- Important views, open spaces and landscape features should be protected

LISTED BUILDINGS:
- Development affecting a Listed Building should have special regard to preserving the building, its setting, and features of special interest
- Enabling development may be considered where it secures the future conservation of a heritage asset

NON-DESIGNATED HERITAGE ASSETS:
- The effect on non-designated heritage assets will be taken into account
- A balanced judgement will be required having regard to the scale of harm and the significance""",
            "relevance_triggers": ["heritage", "conservation area", "listed building", "historic"],
        },
        "ACS-16": {
            "id": "Policy 16",
            "name": "Green Infrastructure, Parks and Open Space",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Environment",
            "page": "96-102",
            "text": """A network of multi-functional green infrastructure will be protected and enhanced.

GREEN INFRASTRUCTURE FUNCTIONS:
- Biodiversity and geodiversity conservation
- Climate change adaptation (cooling, flood attenuation)
- Health and wellbeing (recreation, access to nature)
- Landscape and heritage conservation
- Food production
- Water management

OPEN SPACE:
- Development should provide open space in accordance with local standards
- Existing open space should be protected
- Loss of open space requires replacement provision""",
            "relevance_triggers": ["green infrastructure", "open space", "recreation", "biodiversity"],
        },
        "ACS-17": {
            "id": "Policy 17",
            "name": "Biodiversity",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Environment",
            "page": "104-110",
            "text": """The biodiversity of the area will be increased over the plan period.

HIERARCHY OF PROTECTION:
1. Sites of international importance (SAC, SPA, Ramsar)
2. Sites of national importance (SSSI, NNR)
3. Local sites (Local Wildlife Sites, Local Nature Reserves)
4. Priority habitats and species

DEVELOPMENT PRINCIPLES:
- The mitigation hierarchy should be followed: avoid, mitigate, compensate
- Biodiversity Net Gain should be delivered
- Ecological networks and wildlife corridors should be maintained and enhanced
- Development affecting protected species requires appropriate surveys and mitigation

PROTECTED SITES:
- Development likely to have significant effects on internationally important sites will be subject to Habitats Regulations Assessment
- Development should not adversely affect SSSIs unless the benefits outweigh the impacts""",
            "relevance_triggers": ["biodiversity", "ecology", "wildlife", "sssi"],
        },

        # =====================================================================
        # PART 2: LOCAL PLAN POLICIES
        # =====================================================================
        "LP1": {
            "id": "Policy 1",
            "name": "Flood Risk",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "28-34",
            "text": """Development should avoid areas at risk of flooding and should not increase flood risk elsewhere.

SEQUENTIAL TEST:
- Development should be directed to areas at lowest risk of flooding
- The Sequential Test is required for development in Flood Zones 2 and 3
- Exception Test required where Sequential Test cannot be satisfied

FLOOD RISK ASSESSMENT:
- Site-specific FRA required for:
  - All development in Flood Zones 2 and 3
  - Development over 1 hectare in Flood Zone 1
  - Development in areas with known surface water flood risk

SUSTAINABLE DRAINAGE:
- SuDS should be incorporated into all major developments
- Peak runoff rate should not exceed greenfield rate
- SuDS hierarchy should be followed (infiltration preferred)
- 30% climate change allowance for all drainage design""",
            "relevance_triggers": ["flood", "drainage", "suds"],
        },
        "LP3": {
            "id": "Policy 3",
            "name": "Development in the Countryside",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Strategic",
            "page": "42-48",
            "text": """Development in the countryside will be strictly controlled.

ACCEPTABLE DEVELOPMENT:
a) Agriculture and forestry
b) Rural diversification where it meets Policy 5
c) Rural employment uses where they meet local needs
d) Re-use of rural buildings
e) Replacement of existing dwellings
f) Extensions proportionate to the existing dwelling
g) Development essential for outdoor sport and recreation
h) Essential infrastructure

DESIGN IN THE COUNTRYSIDE:
- Development should respect the character of the countryside
- Materials and design should reflect local vernacular
- Landscaping should integrate development into its surroundings""",
            "relevance_triggers": ["countryside", "rural", "agricultural"],
        },
        "LP4": {
            "id": "Policy 4",
            "name": "Development in the Green Belt",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Strategic",
            "page": "50-58",
            "text": """Development in the Green Belt will be strictly controlled in accordance with national policy.

INAPPROPRIATE DEVELOPMENT:
- Inappropriate development is by definition harmful and should not be approved except in very special circumstances
- Very special circumstances will not exist unless the harm to the Green Belt and any other harm is clearly outweighed by other considerations

EXCEPTIONS (NPPF Para 149):
a) Buildings for agriculture and forestry
b) Facilities for outdoor sport and recreation
c) Extensions or alterations not resulting in disproportionate additions
d) Replacement buildings in the same use and not materially larger
e) Limited infilling in villages
f) Limited affordable housing for local community needs
g) Limited infilling or redevelopment of previously developed land

OPENNESS:
- Development should preserve the openness of the Green Belt
- The five purposes of the Green Belt must not be harmed

EXTENSIONS IN THE GREEN BELT:
- Extensions should not be disproportionate to the original building
- Cumulative extensions will be considered
- Original building means as it existed on 1 July 1948 or as first built if later""",
            "relevance_triggers": ["green belt"],
        },
        "LP10": {
            "id": "Policy 10",
            "name": "Town Centre and District Centre Uses",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Economy",
            "page": "84-92",
            "text": """Town centre uses should be directed to the most sustainable locations.

SEQUENTIAL TEST:
- Main town centre uses should be located in town centres
- If no suitable sites, edge of centre locations may be considered
- Out of centre locations only if no sequentially preferable sites available

IMPACT ASSESSMENT:
- Retail impact assessment required for retail development over 500sqm outside town centres
- Assessment should consider impact on town centre vitality and viability

TOWN CENTRE HIERARCHY:
1. Beeston Town Centre (principal town centre)
2. Eastwood Town Centre
3. Stapleford Town Centre
4. Kimberley Town Centre
5. District and local centres""",
            "relevance_triggers": ["retail", "town centre", "sequential test"],
        },
        "LP11": {
            "id": "Policy 11",
            "name": "Housing Allocations",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "94-108",
            "text": "Land is allocated for residential development to meet the housing requirement of 6,150 dwellings between 2011 and 2028. Allocated sites should be developed in accordance with the site-specific requirements set out in the policy.",
            "relevance_triggers": ["housing", "allocation"],
        },
        "LP14": {
            "id": "Policy 14",
            "name": "Housing Density",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "118-122",
            "text": """Housing development should make efficient use of land while respecting local character.

DENSITY STANDARDS:
- Highly accessible locations (town centres, transport hubs): Minimum 50 dwellings per hectare
- Accessible locations: Minimum 35 dwellings per hectare
- Other locations: Minimum 30 dwellings per hectare

FLEXIBILITY:
- Lower densities may be acceptable where:
  - Site constraints limit capacity
  - Character considerations require it
  - Heritage significance would be harmed
  - Affordable housing viability would be affected

HIGHER DENSITIES:
- Higher densities will be encouraged in sustainable locations
- Design quality must not be compromised by density""",
            "relevance_triggers": ["housing", "density"],
        },
        "LP17": {
            "id": "Policy 17",
            "name": "Place-making, Design and Amenity",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Design",
            "page": "132-142",
            "text": """All development should be designed to create high quality places.

DESIGN PRINCIPLES:
a) Respond positively to local character and context
b) Create attractive and functional spaces
c) Incorporate green infrastructure and landscaping
d) Provide safe and accessible environments
e) Minimise opportunities for crime
f) Respond to topography and landscape features

RESIDENTIAL AMENITY (DM6.6 EQUIVALENT):
- Privacy: 21m minimum between habitable room windows
- Privacy: 12m minimum to a blank wall or high level window
- Daylight: 45-degree test from centre of ground floor windows
- Sunlight: Development should not cause significant overshadowing
- Outlook: Development should not be overbearing or oppressive
- Private amenity space: Minimum garden standards apply

BUILDING HEIGHTS:
- New buildings should respect the height of surrounding development
- Taller buildings may be appropriate in town centres and at transport nodes
- Impact on skyline and important views should be considered""",
            "relevance_triggers": ["design", "amenity", "privacy", "daylight", "all"],
        },
        "LP18": {
            "id": "Policy 18",
            "name": "Shopfronts and Signage",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Design",
            "page": "144-148",
            "text": "Shopfronts and signage should be well designed and respect the character of the building and surrounding area. Traditional shopfronts should be retained and restored where possible. Illuminated signage should be appropriate to the location.",
            "relevance_triggers": ["shopfront", "signage", "advertisement"],
        },
        "LP19": {
            "id": "Policy 19",
            "name": "Extensions and Conversions",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "150-156",
            "text": """Extensions and alterations to existing buildings should be well designed and respect the character of the original building.

DESIGN PRINCIPLES:
a) Respect the scale, form and character of the original building
b) Use materials that complement the existing building
c) Be subordinate to the main building
d) Avoid unacceptable impact on neighbours

RESIDENTIAL EXTENSIONS:
- Should not result in overdevelopment of the plot
- Should retain adequate parking provision
- Should retain adequate private amenity space (minimum 50sqm for houses)
- Should comply with residential amenity standards (Policy 17)

TWO-STOREY EXTENSIONS:
- More careful consideration of design and impact required
- Should not project beyond the building line at the front
- Should maintain separation to boundaries""",
            "relevance_triggers": ["extension", "alteration", "householder", "conversion"],
        },
        "LP20": {
            "id": "Policy 20",
            "name": "Air Quality",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "158-162",
            "text": """Development should not result in unacceptable impacts on air quality.

AIR QUALITY MANAGEMENT AREAS:
- Broxtowe has declared AQMAs for nitrogen dioxide (NO2)
- Development in or near AQMAs requires Air Quality Assessment
- Development should contribute to improving air quality in AQMAs

MITIGATION:
- Electric vehicle charging points required
- Low emission boilers (<40mg/kWh NOx)
- Measures to reduce vehicle trips
- Construction dust management

SENSITIVE RECEPTORS:
- Schools, hospitals and residential uses are sensitive to air quality
- Development introducing sensitive receptors near pollution sources requires assessment""",
            "relevance_triggers": ["air quality", "pollution", "aqma"],
        },
        "LP21": {
            "id": "Policy 21",
            "name": "Transport Infrastructure",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Transport",
            "page": "164-172",
            "text": """Development should provide safe and suitable access and promote sustainable transport.

ACCESS:
- Safe access for all users must be demonstrated
- Access should be provided from adopted highway where possible
- Visibility splays must meet highway authority requirements

PARKING:
- Parking should be provided in accordance with adopted standards
- Cycle parking: 1 space per bedroom for residential
- Electric vehicle charging: 1 per dwelling (new build), 10% for non-residential
- Motorcycle parking should be considered for larger developments

TRANSPORT ASSESSMENT:
- Transport Statement: 30-80 vehicle trips per day
- Transport Assessment: 80+ vehicle trips per day
- Travel Plan: Major developments

SUSTAINABLE TRANSPORT:
- Priority should be given to walking, cycling and public transport
- Contributions may be sought for off-site highway improvements
- Connection to existing footpath and cycle networks should be provided""",
            "relevance_triggers": ["transport", "highway", "parking", "access"],
        },
        "LP24": {
            "id": "Policy 24",
            "name": "Protected and Priority Species and Habitats",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "182-190",
            "text": """Development should protect and enhance biodiversity.

PROTECTED SPECIES:
- Ecological surveys required where protected species may be present
- Surveys should be undertaken at appropriate times of year
- Mitigation must follow the hierarchy: avoid, mitigate, compensate
- Licences from Natural England may be required

PRIORITY HABITATS:
- Development affecting priority habitats should be avoided
- Where loss is unavoidable, compensation must be provided
- Compensatory habitat should be of equal or greater biodiversity value

BIODIVERSITY NET GAIN:
- Minimum 10% net gain required
- Calculated using Defra Biodiversity Metric 4.0
- On-site delivery preferred
- Off-site delivery or credits may be acceptable
- 30-year management and monitoring required
- Gain must be secured through planning condition or legal agreement""",
            "relevance_triggers": ["biodiversity", "ecology", "protected species", "wildlife"],
        },
        "LP25": {
            "id": "Policy 25",
            "name": "Trees, Hedgerows and Other Landscape Features",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "192-198",
            "text": """Development should protect and enhance trees, hedgerows and other landscape features.

TREE PROTECTION:
- Trees protected by TPO must be retained unless exceptional circumstances
- Trees of amenity value should be retained and protected during construction
- Arboricultural Impact Assessment required where trees affected
- Root Protection Areas must be calculated in accordance with BS 5837:2012

REPLACEMENT PLANTING:
- Where tree loss unavoidable, replacement planting required
- Replacement ratio: minimum 2:1 for native trees
- Species appropriate to the location should be selected
- Adequate space for trees to mature must be provided

HEDGEROWS:
- Important hedgerows should be retained
- Hedgerows contributing to ecological networks should be protected
- Compensatory planting required where loss unavoidable

LANDSCAPING:
- Soft landscaping should use native species where appropriate
- Planting schemes should support biodiversity
- Maintenance and management arrangements required""",
            "relevance_triggers": ["tree", "tpo", "hedgerow", "landscaping"],
        },
        "LP26": {
            "id": "Policy 26",
            "name": "Heritage Assets",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Heritage",
            "page": "200-210",
            "text": """Heritage assets and their settings will be conserved and enhanced.

DESIGNATED HERITAGE ASSETS:
- Great weight should be given to the conservation of designated heritage assets
- Substantial harm or total loss should be exceptional/wholly exceptional
- Less than substantial harm should be weighed against public benefits

STATUTORY DUTIES:
- Section 66 P(LBCA)A 1990: Special regard to preserving listed buildings and their settings
- Section 72 P(LBCA)A 1990: Special attention to preserving or enhancing conservation areas

HERITAGE STATEMENTS:
- Applicants must describe the significance of heritage assets affected
- The level of detail should be proportionate to the asset's importance
- Impact on significance, including setting, must be assessed

CONSERVATION AREAS IN BROXTOWE:
- Beeston (multiple character areas)
- Bramcote
- Eastwood (D.H. Lawrence connections)
- Kimberley
- Stapleford
- Attenborough

LISTED BUILDINGS:
- Broxtowe contains approximately 150 listed buildings
- The majority are Grade II
- Notable Grade I include St Mary's Church, Attenborough

ARCHAEOLOGY:
- Archaeological assessment may be required
- Where significant remains are discovered, preservation in situ is preferred
- Recording may be required as a condition of permission""",
            "relevance_triggers": ["heritage", "conservation area", "listed building", "archaeology"],
        },
        "LP27": {
            "id": "Policy 27",
            "name": "Local Green Space",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "212-216",
            "text": "Areas of Local Green Space are designated and shown on the Policies Map. Development on Local Green Space will not be permitted except in very special circumstances. Proposals will be assessed against Green Belt policy in accordance with NPPF paragraph 101.",
            "relevance_triggers": ["local green space", "green space"],
        },
        "LP28": {
            "id": "Policy 28",
            "name": "Green Infrastructure Assets",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "218-224",
            "text": """Green infrastructure assets will be protected and enhanced.

STRATEGIC GREEN INFRASTRUCTURE:
- River Trent corridor
- Nottingham Canal
- Erewash Valley Trail
- Beeston Canal
- Attenborough Nature Reserve

FUNCTIONS:
- Biodiversity corridors
- Flood risk management
- Recreation and health
- Climate change adaptation
- Landscape and visual amenity

DEVELOPMENT REQUIREMENTS:
- Development should contribute to green infrastructure networks
- Links to existing networks should be provided where possible
- On-site green infrastructure should be multi-functional
- Management and maintenance arrangements required""",
            "relevance_triggers": ["green infrastructure", "open space"],
        },
        "LP29": {
            "id": "Policy 29",
            "name": "Development Contributions",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Infrastructure",
            "page": "226-232",
            "text": """Development will be required to contribute to the provision of infrastructure.

COMMUNITY INFRASTRUCTURE LEVY (CIL):
- Broxtowe has an adopted CIL Charging Schedule
- Residential: £45/sqm (Zone A), £15/sqm (Zone B)
- Retail: £60/sqm (out of town)
- Strategic sites: £0/sqm

SECTION 106 OBLIGATIONS:
S106 may be used for site-specific requirements including:
- Affordable housing (on sites of 10+ units)
- Education contributions (primary and secondary)
- Healthcare contributions (on larger sites)
- Open space provision or contributions
- Biodiversity net gain (where not secured by condition)
- Highway improvements
- Travel plan implementation

REGULATION 122 TESTS:
All S106 obligations must be:
a) Necessary to make the development acceptable
b) Directly related to the development
c) Fairly and reasonably related in scale and kind""",
            "relevance_triggers": ["cil", "s106", "contributions", "infrastructure"],
        },
    },
}


# =============================================================================
# COMBINED LOCAL PLANS DATABASE
# =============================================================================

LOCAL_PLANS_DATABASE = {
    "newcastle": NEWCASTLE_LOCAL_PLAN,
    "broxtowe": BROXTOWE_LOCAL_PLAN,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_council_policies(council_id: str) -> dict | None:
    """Get all policies for a specific council."""
    council_data = LOCAL_PLANS_DATABASE.get(council_id.lower())
    if council_data:
        return council_data.get("policies", {})
    return None


def get_policy(council_id: str, policy_id: str) -> dict | None:
    """Get a specific policy by council and policy ID."""
    policies = get_council_policies(council_id)
    if policies:
        return policies.get(policy_id)
    return None


def search_local_plan_policies(
    council_id: str,
    keywords: list[str],
) -> list[dict]:
    """Search local plan policies by keywords."""
    policies = get_council_policies(council_id)
    if not policies:
        return []

    results = []
    keywords_lower = [kw.lower() for kw in keywords]

    for policy_id, policy in policies.items():
        triggers = policy.get("relevance_triggers", [])
        text_lower = policy.get("text", "").lower()
        name_lower = policy.get("name", "").lower()

        # Check triggers
        for trigger in triggers:
            if any(kw in trigger for kw in keywords_lower):
                results.append({"policy_id": policy_id, **policy})
                break
        else:
            # Check text content
            if any(kw in text_lower or kw in name_lower for kw in keywords_lower):
                results.append({"policy_id": policy_id, **policy})

    return results


def get_relevant_local_plan_policies(
    council_id: str,
    constraints: list[str],
    application_type: str,
    proposal: str,
) -> list[dict]:
    """
    Get relevant local plan policies based on application characteristics.

    Returns policies with full citation information.
    """
    policies = get_council_policies(council_id)
    if not policies:
        return []

    selected = []
    proposal_lower = proposal.lower()
    constraints_lower = [c.lower() for c in constraints]
    app_type_lower = application_type.lower()

    for policy_id, policy in policies.items():
        triggers = policy.get("relevance_triggers", [])
        relevant = False

        for trigger in triggers:
            if trigger == "all":
                relevant = True
                break
            if trigger in proposal_lower:
                relevant = True
                break
            if any(trigger in c for c in constraints_lower):
                relevant = True
                break
            if trigger in app_type_lower:
                relevant = True
                break

        if relevant:
            selected.append({
                "policy_id": policy_id,
                "policy_name": policy.get("name", ""),
                "source": policy.get("source", ""),
                "section": policy.get("section", ""),
                "page": policy.get("page", ""),
                "relevance": f"Applicable to {application_type}",
                "text": policy.get("text", ""),
            })

    return selected


def format_local_plan_citation(council_id: str, policy_id: str) -> str:
    """Format a proper local plan policy citation string."""
    policy = get_policy(council_id, policy_id)
    if policy:
        source = policy.get("source", "")
        name = policy.get("name", "")
        page = policy.get("page", "")
        citation = f"{source}, Policy {policy_id}: {name}"
        if page:
            citation += f" (page {page})"
        return citation
    return f"Policy {policy_id}"


def get_available_councils() -> list[dict]:
    """Get list of available councils in the database."""
    return [
        {
            "council_id": council_id,
            "council_name": data.get("council_name", ""),
            "plans": data.get("plans", []),
            "policy_count": len(data.get("policies", {})),
        }
        for council_id, data in LOCAL_PLANS_DATABASE.items()
    ]
