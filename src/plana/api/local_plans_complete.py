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
        "CS2": {
            "id": "CS2",
            "name": "Delivery and Viability",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Strategic Policies",
            "page": "49-52",
            "text": "Development will be expected to contribute to infrastructure provision and community benefits where these are necessary to make the development acceptable in planning terms. Viability will be taken into account in determining the level of planning obligations required. The Council will work with developers and infrastructure providers to ensure timely delivery of necessary infrastructure.",
            "relevance_triggers": ["viability", "infrastructure", "s106", "cil"],
        },
        "CS3": {
            "id": "CS3",
            "name": "Sustainable Development",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Strategic Policies",
            "page": "53-55",
            "text": "When considering development proposals, the Council will take a positive approach that reflects the presumption in favour of sustainable development. Development should contribute to achieving sustainable development through: minimising greenhouse gas emissions; adapting to climate change; making efficient use of natural resources; minimising waste; and protecting and enhancing biodiversity.",
            "relevance_triggers": ["sustainable", "climate", "environment"],
        },
        "CS4": {
            "id": "CS4",
            "name": "Climate Change",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Environment",
            "page": "56-58",
            "text": "Development should minimise its impact on climate change by: reducing energy demand through sustainable design and construction; incorporating renewable and low carbon energy generation where feasible; and ensuring flood risk is not increased. Major developments should achieve BREEAM 'Very Good' or equivalent standard.",
            "relevance_triggers": ["climate", "energy", "renewable", "carbon"],
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
        "CS6": {
            "id": "CS6",
            "name": "Employment Land",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Employment",
            "page": "66-68",
            "text": "Key Employment Areas will be protected for employment uses (Use Classes E(g), B2, B8). The loss of employment land outside Key Employment Areas will be resisted unless it can be demonstrated that the site is no longer suitable or viable for employment use, or the proposed use would deliver significant regeneration benefits.",
            "relevance_triggers": ["employment", "industrial", "commercial", "loss of employment"],
        },
        "CS7": {
            "id": "CS7",
            "name": "Retail and Centres",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Retail",
            "page": "69-72",
            "text": "The vitality and viability of existing centres will be maintained and enhanced. A sequential approach will be applied to main town centre uses. Major retail development will be directed to the Primary Shopping Area within Newcastle City Centre. District and local centres will be protected and enhanced to serve local communities.",
            "relevance_triggers": ["retail", "town centre", "shopping", "sequential test"],
        },
        "CS8": {
            "id": "CS8",
            "name": "Leisure, Culture and Tourism",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Culture",
            "page": "73-74",
            "text": "Newcastle and Gateshead will be promoted as a major destination for leisure, culture and tourism. Development that supports the growth of the visitor economy will be encouraged. Leisure and cultural facilities should be accessible and located in sustainable locations.",
            "relevance_triggers": ["leisure", "tourism", "culture", "hotel"],
        },
        "CS9": {
            "id": "CS9",
            "name": "Existing Communities",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Community",
            "page": "75-76",
            "text": "Development should support existing communities by: protecting and enhancing local services and facilities; improving accessibility to services; and supporting the vitality of local centres. The loss of community facilities will be resisted unless adequate alternative provision is made or the facility is no longer needed.",
            "relevance_triggers": ["community", "local services", "facilities"],
        },
        "CS10": {
            "id": "CS10",
            "name": "Gypsies, Travellers and Travelling Showpeople",
            "source": "Newcastle Core Strategy and Urban Core Plan (2015)",
            "section": "Housing",
            "page": "77",
            "text": "The accommodation needs of Gypsies, Travellers and Travelling Showpeople will be met through site allocations and windfall sites. Sites should be in sustainable locations with access to local services and facilities. Proposals should not have unacceptable impacts on the character and appearance of the area.",
            "relevance_triggers": ["traveller", "gypsy", "showpeople"],
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
        "DM2": {
            "id": "DM2",
            "name": "Flood Risk and Water Management",
            "source": "Development and Allocations Plan (2022)",
            "section": "Environment",
            "page": "27-32",
            "text": "Development in areas at risk of flooding will only be permitted where it can be demonstrated that: the sequential test has been applied and passed; appropriate flood risk mitigation measures are incorporated; safe access and egress can be achieved; and the development would not increase flood risk elsewhere. All major development must incorporate sustainable drainage systems (SuDS) unless demonstrated to be inappropriate.",
            "relevance_triggers": ["flood", "drainage", "suds", "water"],
        },
        "DM3": {
            "id": "DM3",
            "name": "Green Infrastructure",
            "source": "Development and Allocations Plan (2022)",
            "section": "Environment",
            "page": "33-36",
            "text": "Development should protect, enhance and contribute to the City's green infrastructure network. Proposals should demonstrate how they will: maintain and enhance existing green infrastructure; create new green infrastructure where appropriate; and ensure connectivity between green spaces. A net gain in biodiversity should be achieved.",
            "relevance_triggers": ["green infrastructure", "open space", "biodiversity"],
        },
        "DM4": {
            "id": "DM4",
            "name": "Biodiversity and Nature Conservation",
            "source": "Development and Allocations Plan (2022)",
            "section": "Environment",
            "page": "37-41",
            "text": "Development should protect and enhance biodiversity and geodiversity. A minimum 10% biodiversity net gain is required as measured using the DEFRA Metric. Proposals that would have an adverse impact on nationally or internationally designated sites will not be permitted unless there are exceptional circumstances and appropriate mitigation or compensation.",
            "relevance_triggers": ["biodiversity", "ecology", "wildlife", "habitat"],
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
        "DM8": {
            "id": "DM8",
            "name": "Developer Contributions",
            "source": "Development and Allocations Plan (2022)",
            "section": "Infrastructure",
            "page": "85-90",
            "text": "Development will be required to make appropriate contributions towards infrastructure and services where these are necessary to make the development acceptable in planning terms. Contributions will be secured through Section 106 agreements or Community Infrastructure Levy (CIL). Contributions must meet the tests in Regulation 122: necessary, directly related, and fairly and reasonably related in scale.",
            "relevance_triggers": ["s106", "cil", "infrastructure", "contributions"],
        },
        "DM9": {
            "id": "DM9",
            "name": "Housing Mix and Type",
            "source": "Development and Allocations Plan (2022)",
            "section": "Housing",
            "page": "91-94",
            "text": "Residential development should provide a mix of dwelling types and sizes to meet local housing need. The mix should reflect the most up-to-date Strategic Housing Market Assessment and local circumstances. Proposals should include a range of house types including family housing with 3+ bedrooms, accessible and adaptable dwellings, and homes suitable for older people.",
            "relevance_triggers": ["housing", "residential", "dwelling", "mix"],
        },
        "DM10": {
            "id": "DM10",
            "name": "Affordable Housing",
            "source": "Development and Allocations Plan (2022)",
            "section": "Housing",
            "page": "95-100",
            "text": """Affordable housing will be required on developments of 10 or more dwellings or sites of 0.5 hectares or more:
- 25% affordable housing on greenfield sites
- 15% affordable housing on brownfield sites
- Tenure split: 75% social/affordable rent, 25% intermediate/shared ownership
- Affordable units should be distributed throughout the development and indistinguishable from market housing
- Viability assessments required to justify reduced contributions""",
            "relevance_triggers": ["affordable housing", "housing", "major development"],
        },
        "DM11": {
            "id": "DM11",
            "name": "Houses in Multiple Occupation",
            "source": "Development and Allocations Plan (2022)",
            "section": "Housing",
            "page": "101-104",
            "text": "Change of use to a House in Multiple Occupation (HMO) will be permitted where: it would not result in the proportion of HMOs exceeding 10% of dwellings within 100m; adequate refuse storage, cycle parking and amenity space is provided; the property can meet relevant space and amenity standards; and there would be no unacceptable impact on residential amenity or character.",
            "relevance_triggers": ["hmo", "house in multiple occupation", "change of use"],
        },
        "DM12": {
            "id": "DM12",
            "name": "Student Housing",
            "source": "Development and Allocations Plan (2022)",
            "section": "Housing",
            "page": "105-108",
            "text": "Purpose-built student accommodation will be supported in appropriate locations close to universities and public transport hubs. Proposals should provide high quality accommodation that meets relevant standards, makes adequate provision for cycle storage and waste management, and does not have an unacceptable impact on the amenity of nearby residents.",
            "relevance_triggers": ["student", "purpose built student accommodation", "pbsa"],
        },
        "DM13": {
            "id": "DM13",
            "name": "Residential Institutions and Care Homes",
            "source": "Development and Allocations Plan (2022)",
            "section": "Housing",
            "page": "109-111",
            "text": "Proposals for residential care and nursing homes, supported living and extra care housing will be supported where they are accessible by public transport, are within reasonable distance of community facilities and services, provide adequate private and communal amenity space, and meet relevant design and space standards.",
            "relevance_triggers": ["care home", "nursing home", "supported living", "extra care"],
        },
        "DM14": {
            "id": "DM14",
            "name": "Trees and Landscaping",
            "source": "Development and Allocations Plan (2022)",
            "section": "Environment",
            "page": "112-115",
            "text": "Development proposals should retain, protect and integrate existing trees, hedgerows and landscape features. Where tree removal is unavoidable, replacement planting should be provided at a ratio of at least 2:1. Tree surveys to BS 5837:2012 are required for sites with existing trees. New developments should incorporate substantial landscaping that provides biodiversity benefits, green infrastructure and amenity value.",
            "relevance_triggers": ["trees", "landscaping", "tpo", "hedgerow"],
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
        "DM18": {
            "id": "DM18",
            "name": "Archaeology",
            "source": "Development and Allocations Plan (2022)",
            "section": "Heritage",
            "page": "129-132",
            "text": "Development affecting sites of known or potential archaeological interest will require an appropriate level of investigation and recording. Desk-based assessment, field evaluation and, where necessary, excavation may be required. Significant archaeological remains should be preserved in situ where possible. Where preservation in situ is not justified, remains should be appropriately recorded and findings made publicly accessible.",
            "relevance_triggers": ["archaeology", "archaeological", "heritage"],
        },
        "DM19": {
            "id": "DM19",
            "name": "Town Centre Uses",
            "source": "Development and Allocations Plan (2022)",
            "section": "Retail",
            "page": "133-138",
            "text": "Main town centre uses should be located in town centres. Proposals for such uses outside town centres must demonstrate compliance with the sequential test and, for retail developments over 2,500 sqm, the impact test. The vitality and viability of existing centres must be protected and enhanced. Primary shopping frontages should maintain a predominance of A1 retail uses.",
            "relevance_triggers": ["retail", "town centre", "shopping", "commercial"],
        },
        "DM20": {
            "id": "DM20",
            "name": "Hot Food Takeaways",
            "source": "Development and Allocations Plan (2022)",
            "section": "Retail",
            "page": "139-141",
            "text": "Hot food takeaway (A5) uses will not be permitted within 400 metres of the boundary of a primary or secondary school. Proposals will be assessed against the cumulative impact on the vitality and viability of the town centre, residential amenity, highway safety, and public health objectives. Opening hours may be restricted by condition.",
            "relevance_triggers": ["hot food takeaway", "a5", "fast food"],
        },
        "DM21": {
            "id": "DM21",
            "name": "Employment Land",
            "source": "Development and Allocations Plan (2022)",
            "section": "Employment",
            "page": "142-146",
            "text": "The loss of employment land (Use Classes E(g), B2, B8) will be resisted unless: the site has been marketed unsuccessfully for at least 12 months at a realistic price; the proposal would not result in a significant loss of employment land; or the proposed use would generate equivalent employment opportunities. Key Employment Areas are protected for employment uses.",
            "relevance_triggers": ["employment", "industrial", "commercial", "office"],
        },
        "DM22": {
            "id": "DM22",
            "name": "Renewable Energy",
            "source": "Development and Allocations Plan (2022)",
            "section": "Climate",
            "page": "147-150",
            "text": "Renewable and low carbon energy development will be supported where the impacts are or can be made acceptable. Major developments should achieve a minimum 10% reduction in CO2 emissions through on-site renewable or low carbon energy generation. Developments should incorporate sustainable design and construction principles.",
            "relevance_triggers": ["renewable energy", "solar", "wind", "carbon"],
        },
        "DM23": {
            "id": "DM23",
            "name": "Telecommunications",
            "source": "Development and Allocations Plan (2022)",
            "section": "Infrastructure",
            "page": "151-153",
            "text": "Telecommunications development will be supported where it is sited and designed to minimise visual impact. Operators should demonstrate that they have explored the possibility of using existing sites, masts or structures. Health impacts are considered at the national level; the local planning authority should not set additional local standards.",
            "relevance_triggers": ["telecommunications", "mast", "5g", "broadband"],
        },
        "DM24": {
            "id": "DM24",
            "name": "Hot Food Takeaways and Health",
            "source": "Development and Allocations Plan (2022)",
            "section": "Health",
            "page": "154-155",
            "text": "Development should support healthy lifestyles and address health inequalities. Proposals for hot food takeaways will be assessed against potential impacts on public health. Health Impact Assessments may be required for major developments to demonstrate how health and wellbeing have been considered in the design process.",
            "relevance_triggers": ["health", "wellbeing", "takeaway"],
        },
        "DM25": {
            "id": "DM25",
            "name": "Community Facilities",
            "source": "Development and Allocations Plan (2022)",
            "section": "Community",
            "page": "156-158",
            "text": "The loss of community facilities will be resisted unless: an assessment demonstrates the facility is no longer needed; adequate alternative provision exists within reasonable distance; or the facility is no longer viable and has been marketed for at least 12 months. New community facilities should be accessible by sustainable transport modes.",
            "relevance_triggers": ["community", "health centre", "school", "library"],
        },
        "DM26": {
            "id": "DM26",
            "name": "Sports and Recreation",
            "source": "Development and Allocations Plan (2022)",
            "section": "Recreation",
            "page": "159-161",
            "text": "Existing sports and recreation facilities should be protected. Development resulting in the loss of such facilities will not be permitted unless replacement facilities of equivalent or better quality are provided, or the development is for alternative sports provision that outweighs the loss, or an assessment demonstrates the facility is surplus to requirements.",
            "relevance_triggers": ["sports", "recreation", "leisure", "playing fields"],
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
        "LP2": {
            "id": "Policy 2",
            "name": "Site Allocations",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Strategic",
            "page": "35-41",
            "text": """Sites are allocated to meet the development needs of the Borough as set out in the Aligned Core Strategy.

HOUSING ALLOCATIONS:
- Sites are allocated to deliver approximately 3,100 new dwellings
- Allocations are concentrated in accessible sustainable locations
- Key sites include strategic allocations at Toton and Field Farm

EMPLOYMENT ALLOCATIONS:
- Sites totalling approximately 18 hectares are allocated for employment
- Focus on accessible locations close to the strategic road network

SITE REQUIREMENTS:
- Development should accord with site-specific requirements set out for each allocation
- Infrastructure contributions will be required in accordance with policies""",
            "relevance_triggers": ["allocation", "housing", "employment"],
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
        "LP5": {
            "id": "Policy 5",
            "name": "Rural Diversification",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Economy",
            "page": "60-64",
            "text": """Farm diversification and rural business development will be supported where:
- The proposal supports farm viability or provides local employment
- The scale and nature is appropriate to the rural location
- It does not harm the character of the countryside
- It can be accommodated without significant new buildings
- The proposal is accessible and does not generate unacceptable traffic
- It does not harm residential amenity""",
            "relevance_triggers": ["rural", "farm diversification", "agricultural"],
        },
        "LP6": {
            "id": "Policy 6",
            "name": "Conversion of Buildings in the Countryside",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Economy",
            "page": "65-68",
            "text": """The conversion of existing buildings in the countryside to residential, employment, tourism or community uses will be permitted where:
- The building is of permanent and substantial construction
- The proposal does not require substantial reconstruction or extension
- The building is capable of conversion without significant alterations
- The proposal respects the character of the building and its surroundings
- Appropriate access can be provided without harm to the character of the area""",
            "relevance_triggers": ["conversion", "rural", "barn"],
        },
        "LP7": {
            "id": "Policy 7",
            "name": "Rural Workers Dwellings",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "69-72",
            "text": """New dwellings for rural workers will only be permitted where:
- There is a demonstrated essential need for a full-time worker to be present at the site
- The need relates to a well-established agricultural or forestry activity
- Financial and functional tests demonstrate the need cannot be met by existing dwellings
- The dwelling is sited to minimise visual impact and relate to existing buildings
- A legal agreement will tie the occupancy to the agricultural enterprise""",
            "relevance_triggers": ["agricultural worker", "rural worker", "farm dwelling"],
        },
        "LP8": {
            "id": "Policy 8",
            "name": "Housing Size, Mix and Choice",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "73-76",
            "text": """Residential development should provide a mix of house types and sizes to meet local needs:
- Mix should reflect the latest Strategic Housing Market Assessment
- Family housing (3+ bedrooms) should form a significant proportion
- Accessible and adaptable dwellings (Building Regulations M4(2)) required
- 5% of dwellings on major sites to be wheelchair accessible (M4(3))
- Proposals for 100% flatted development will be resisted unless justified""",
            "relevance_triggers": ["housing", "mix", "accessible"],
        },
        "LP9": {
            "id": "Policy 9",
            "name": "Self-Build and Custom Housebuilding",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "78-82",
            "text": """The Council will support the provision of self-build and custom build housing:
- Major residential developments should make provision for self-build plots
- Plots should be made available for at least 12 months
- If not taken up, plots may revert to general market housing
- Individual self-build proposals will be supported where they comply with other policies""",
            "relevance_triggers": ["self-build", "custom build", "housing"],
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
        "LP12": {
            "id": "Policy 12",
            "name": "Regeneration Allocations",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "109-112",
            "text": """Sites identified for regeneration and redevelopment are allocated to bring forward underused and derelict land for housing and mixed-use development.

SITE REQUIREMENTS:
- Development should contribute to area regeneration
- Proposals should address contamination and remediation
- High quality design responding to local context
- Contribution to affordable housing where viable""",
            "relevance_triggers": ["regeneration", "brownfield", "housing"],
        },
        "LP13": {
            "id": "Policy 13",
            "name": "Affordable Housing",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "113-117",
            "text": """Affordable housing provision is required on qualifying sites:

THRESHOLDS AND REQUIREMENTS:
- Sites of 10+ dwellings or 0.5+ hectares: 30% affordable housing
- Tenure split: 60% affordable/social rent, 40% intermediate
- First Homes: 25% of affordable provision

ON-SITE PROVISION:
- Affordable housing should be provided on-site unless exceptional circumstances justify off-site or commuted sum
- Affordable units should be indistinguishable from market units
- Units should be distributed throughout the development

VIABILITY:
- Reduced provision may be acceptable where independently verified viability evidence demonstrates 30% is not achievable""",
            "relevance_triggers": ["affordable housing", "housing"],
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
        "LP15": {
            "id": "Policy 15",
            "name": "Housing within Urban Areas",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "123-126",
            "text": """Residential development on unallocated sites within urban areas will be supported where:
- The site is within the urban area as defined on the Policies Map
- Development is of appropriate scale, design and density
- It would not result in the loss of valued open space or community facilities
- It would not have unacceptable impacts on residential amenity
- Appropriate infrastructure can be provided""",
            "relevance_triggers": ["housing", "infill", "urban"],
        },
        "LP16": {
            "id": "Policy 16",
            "name": "Gypsies, Travellers and Travelling Showpeople",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Housing",
            "page": "127-131",
            "text": """Provision will be made to meet the accommodation needs of Gypsies, Travellers and Travelling Showpeople:
- Existing sites will be protected
- New sites should be appropriately located with access to facilities
- Sites should be safe and provide adequate residential amenity
- Proposals should not cause significant harm to the character of the area
- Planning obligations may be required for site management and maintenance""",
            "relevance_triggers": ["traveller", "gypsy", "showpeople"],
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
        "LP22": {
            "id": "Policy 22",
            "name": "Recreational Facilities",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Community",
            "page": "173-177",
            "text": """Indoor and outdoor recreational facilities should be protected and enhanced.

PROTECTION:
- Existing facilities should be retained unless:
  - Replacement facilities of equal or better quality are provided
  - The facility is surplus to requirements (evidence required)
  - Alternative provision would outweigh the loss

NEW PROVISION:
- Major residential developments should contribute to recreation
- Contributions may be on-site provision or off-site financial contribution
- Standards: Sport England/Fields in Trust guidance will be used

PLAYING PITCHES:
- Playing pitch strategy identifies priority areas
- Developments should not prejudice pitch provision
- Contributions may be required for pitch improvements""",
            "relevance_triggers": ["recreation", "sports", "leisure", "playing pitch"],
        },
        "LP23": {
            "id": "Policy 23",
            "name": "Open Space and Green Infrastructure",
            "source": "Broxtowe Part 2 Local Plan (2019)",
            "section": "Environment",
            "page": "178-181",
            "text": """Open space and green infrastructure should be protected, enhanced and provided.

PROTECTION:
- Existing open space should be retained
- Development on open space will only be permitted where:
  - Assessment shows it is surplus to requirements, or
  - Replacement of equivalent or better quality is provided

NEW PROVISION:
- Major residential developments must provide open space
- Standard: 3.6 hectares per 1,000 population
- Mix of typologies should be provided

GREEN INFRASTRUCTURE:
- Development should contribute to the green infrastructure network
- Multifunctional green spaces are encouraged
- Green corridors and connectivity should be maintained and enhanced""",
            "relevance_triggers": ["open space", "green infrastructure", "park"],
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
# NOTTINGHAM CITY COUNCIL LOCAL PLAN
# =============================================================================

NOTTINGHAM_LOCAL_PLAN = {
    "council_id": "nottingham",
    "council_name": "Nottingham City Council",
    "plan_name": "Nottingham Local Plan Part 2: Land and Planning Policies",
    "adoption_date": "2020-01-13",
    "plan_period": "2011-2028",
    "policies": {
        # =====================================================================
        # STRATEGIC POLICIES (From Aligned Core Strategy)
        # =====================================================================
        "Policy A": {
            "id": "Policy A",
            "name": "Presumption in Favour of Sustainable Development",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "29",
            "text": "When considering development proposals, the Council will take a positive approach that reflects the presumption in favour of sustainable development contained in the National Planning Policy Framework. The Council will work proactively with applicants to find solutions that enable proposals to be approved wherever possible.",
            "relevance_triggers": ["all", "sustainable"],
        },
        "Policy 1": {
            "id": "Policy 1",
            "name": "Climate Change",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Environment",
            "page": "33-38",
            "text": "Development will be expected to mitigate against and adapt to climate change. New development should be designed to reduce energy demand and incorporate renewable energy where feasible. Development should not increase flood risk and should incorporate sustainable drainage systems.",
            "relevance_triggers": ["climate", "energy", "flood", "suds"],
        },
        "Policy 2": {
            "id": "Policy 2",
            "name": "The Spatial Strategy",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "42-48",
            "text": "Sustainable development will be achieved by focusing the majority of new development in and around the built up area of Nottingham. Development will be directed to sustainable, accessible locations within the urban area, with new allocations on the edge of the urban area where necessary to meet housing requirements.",
            "relevance_triggers": ["strategic", "location", "urban"],
        },
        "Policy 3": {
            "id": "Policy 3",
            "name": "The Green Belt",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Green Belt",
            "page": "52-56",
            "text": "The principle of the Nottingham-Derby Green Belt will be maintained. Inappropriate development will not be approved except in very special circumstances. Green Belt boundaries will be reviewed through the Local Plan process where necessary to meet development needs.",
            "relevance_triggers": ["green belt"],
        },
        "Policy 4": {
            "id": "Policy 4",
            "name": "Employment Provision and Economic Development",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Employment",
            "page": "60-66",
            "text": "Sufficient land will be identified to meet the employment needs of the area. Key employment sites will be protected for employment uses. The loss of employment land will be resisted unless it can be demonstrated that the site is no longer suitable or viable for employment use.",
            "relevance_triggers": ["employment", "commercial", "industrial", "office"],
        },
        "Policy 5": {
            "id": "Policy 5",
            "name": "Nottingham City Centre",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Retail",
            "page": "70-76",
            "text": "Nottingham City Centre will be the focus for major retail, leisure, cultural and office development. The vitality and viability of the City Centre will be maintained and enhanced. Development should strengthen the City Centre's role as a regional centre.",
            "relevance_triggers": ["city centre", "retail", "office", "leisure"],
        },
        "Policy 6": {
            "id": "Policy 6",
            "name": "Role of Town and Local Centres",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Retail",
            "page": "78-82",
            "text": "Town centres and local centres will be the focus for retail, leisure and community facilities serving local needs. A sequential approach will be applied to town centre uses. The vitality and viability of existing centres will be protected and enhanced.",
            "relevance_triggers": ["town centre", "local centre", "retail", "sequential test"],
        },
        "Policy 7": {
            "id": "Policy 7",
            "name": "Regeneration",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Strategic",
            "page": "84-88",
            "text": "Regeneration of the urban area will be supported through: prioritising previously developed land; supporting mixed-use development in sustainable locations; improving the quality of the built environment; and addressing areas of deprivation.",
            "relevance_triggers": ["regeneration", "brownfield", "urban"],
        },
        "Policy 8": {
            "id": "Policy 8",
            "name": "Housing Size, Mix and Choice",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Housing",
            "page": "92-96",
            "text": "Residential development should provide a mix of housing types, sizes and tenures to meet identified local needs. The mix should be informed by the Strategic Housing Market Assessment and local circumstances. Family housing and housing suitable for older people will be particularly encouraged.",
            "relevance_triggers": ["housing", "mix", "residential", "dwelling"],
        },
        "Policy 9": {
            "id": "Policy 9",
            "name": "Gypsies, Travellers and Travelling Showpeople",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Housing",
            "page": "98-100",
            "text": "Provision will be made to meet the accommodation needs of Gypsies, Travellers and Travelling Showpeople. Sites should be in sustainable locations with access to local services and facilities. Development should not have unacceptable impacts on the character of the area.",
            "relevance_triggers": ["traveller", "gypsy", "showpeople"],
        },
        "Policy 10": {
            "id": "Policy 10",
            "name": "Design and Enhancing Local Identity",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Design",
            "page": "102-108",
            "text": "All new development should be designed to a high standard. Development should respond positively to local character and context, create well-defined streets and spaces, and provide a safe and accessible environment. Building for Life 12 principles should be applied to major residential development.",
            "relevance_triggers": ["design", "character", "quality"],
        },
        "Policy 11": {
            "id": "Policy 11",
            "name": "The Historic Environment",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Heritage",
            "page": "110-114",
            "text": "The historic environment will be conserved and enhanced. Development affecting heritage assets should sustain and where appropriate enhance their significance. Great weight will be given to the conservation of designated heritage assets. Development within conservation areas should preserve or enhance their character and appearance.",
            "relevance_triggers": ["heritage", "conservation area", "listed building", "historic"],
        },
        "Policy 12": {
            "id": "Policy 12",
            "name": "Local Services and Healthy Lifestyles",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Community",
            "page": "116-120",
            "text": "Development should support healthy lifestyles and access to local services. The loss of community facilities will be resisted unless adequate alternative provision exists. New development should contribute to addressing health inequalities and promoting active travel.",
            "relevance_triggers": ["community", "health", "facilities"],
        },
        "Policy 13": {
            "id": "Policy 13",
            "name": "Culture, Tourism and Sport",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Culture",
            "page": "122-124",
            "text": "Development that supports cultural, tourism and sporting activities will be encouraged. Facilities should be accessible and located in sustainable locations. The loss of sports and recreation facilities will be resisted unless replacement facilities of equivalent or better quality are provided.",
            "relevance_triggers": ["culture", "tourism", "sport", "leisure"],
        },
        "Policy 14": {
            "id": "Policy 14",
            "name": "Managing Travel Demand",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Transport",
            "page": "126-132",
            "text": "Development should be located where it can maximise the use of sustainable transport modes. Development generating significant travel demand should be accompanied by a Transport Assessment and Travel Plan. Parking provision should accord with adopted standards.",
            "relevance_triggers": ["transport", "highway", "parking", "travel plan"],
        },
        "Policy 15": {
            "id": "Policy 15",
            "name": "Transport Infrastructure Priorities",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Transport",
            "page": "134-138",
            "text": "Development should support the delivery of strategic transport infrastructure. Developer contributions will be sought towards transport improvements where necessary to make development acceptable. Public transport, walking and cycling infrastructure will be prioritised.",
            "relevance_triggers": ["transport", "infrastructure", "contributions"],
        },
        "Policy 16": {
            "id": "Policy 16",
            "name": "Green Infrastructure, Parks and Open Space",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Environment",
            "page": "140-146",
            "text": "Development should protect and enhance green infrastructure networks. New development should provide open space in accordance with adopted standards. The loss of open space will be resisted unless replacement provision of equivalent or better quality is made.",
            "relevance_triggers": ["green infrastructure", "open space", "parks"],
        },
        "Policy 17": {
            "id": "Policy 17",
            "name": "Biodiversity",
            "source": "Greater Nottingham Aligned Core Strategy (2014)",
            "section": "Environment",
            "page": "148-152",
            "text": "Development should protect and enhance biodiversity. Sites of national and international importance will be afforded the highest level of protection. A minimum 10% biodiversity net gain is required. Ecological networks and corridors should be maintained and enhanced.",
            "relevance_triggers": ["biodiversity", "ecology", "wildlife", "habitat"],
        },
        # =====================================================================
        # LOCAL PLAN PART 2 POLICIES
        # =====================================================================
        "CC1": {
            "id": "CC1",
            "name": "Sustainable Design and Construction",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Climate",
            "page": "22-28",
            "text": """Development should incorporate sustainable design and construction principles:
- Minimise energy demand through orientation, layout and fabric
- Incorporate renewable and low carbon energy where feasible
- Use sustainable materials and construction methods
- Provide water efficiency measures
- Address overheating risk
- BREEAM 'Very Good' for major non-residential development""",
            "relevance_triggers": ["sustainable", "energy", "design", "construction"],
        },
        "CC2": {
            "id": "CC2",
            "name": "Decentralised Energy and Heat Networks",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Climate",
            "page": "29-32",
            "text": "Major development in priority areas should connect to existing or planned heat networks where feasible. Where connection is not feasible, development should be designed to facilitate future connection. Development should not prejudice the delivery of heat networks.",
            "relevance_triggers": ["energy", "heat network", "renewable"],
        },
        "CC3": {
            "id": "CC3",
            "name": "Water",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "33-36",
            "text": "Development should achieve water efficiency standards of 110 litres per person per day for residential development. Non-residential development should incorporate water efficiency measures. Development should protect water quality and should not adversely affect water resources.",
            "relevance_triggers": ["water", "efficiency", "pollution"],
        },
        "DE1": {
            "id": "DE1",
            "name": "Building Design and Use",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Design",
            "page": "40-48",
            "text": """Development should be of high quality design that:
a) Makes a positive contribution to the public realm
b) Creates attractive, safe and accessible places
c) Responds positively to local context and character
d) Uses appropriate materials and detailing
e) Achieves high standards of amenity for occupiers
f) Incorporates measures to reduce crime and fear of crime

RESIDENTIAL STANDARDS:
- Dwellings should meet Nationally Described Space Standards
- Adequate private amenity space should be provided
- Appropriate levels of daylight and sunlight""",
            "relevance_triggers": ["design", "all"],
        },
        "DE2": {
            "id": "DE2",
            "name": "Context and Place Making",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Design",
            "page": "49-54",
            "text": "Development should respond positively to its context and contribute to place making. Proposals should: respect and enhance local character; create or reinforce a sense of place; and integrate with the surrounding area. Major development should be informed by character analysis.",
            "relevance_triggers": ["design", "character", "context"],
        },
        "DE3": {
            "id": "DE3",
            "name": "Design Principles for Development within the City Centre Primary Shopping Area",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Design",
            "page": "55-58",
            "text": "Development within the Primary Shopping Area should: maintain active frontages at ground floor level; provide high quality public realm; and contribute to the vitality of the City Centre. Upper floors should be designed for flexible use.",
            "relevance_triggers": ["city centre", "retail", "design"],
        },
        "HO1": {
            "id": "HO1",
            "name": "Housing Development on Unallocated Sites",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Housing",
            "page": "62-66",
            "text": """Residential development on unallocated sites within the urban area will be supported where:
a) The site is within the urban area as defined on the Policies Map
b) Development is of appropriate scale, design and density
c) It would not result in the loss of valued open space
d) It would not have unacceptable impacts on residential amenity
e) Appropriate infrastructure can be provided""",
            "relevance_triggers": ["housing", "residential", "infill"],
        },
        "HO2": {
            "id": "HO2",
            "name": "Residential Density",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Housing",
            "page": "67-70",
            "text": """Housing development should make efficient use of land:
- City Centre: 200+ dwellings per hectare (minimum)
- Edge of City Centre: 75+ dwellings per hectare
- Other highly accessible locations: 50+ dwellings per hectare
- Elsewhere: 40+ dwellings per hectare

Lower densities may be acceptable where justified by site constraints or character considerations.""",
            "relevance_triggers": ["housing", "density"],
        },
        "HO3": {
            "id": "HO3",
            "name": "Affordable Housing",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Housing",
            "page": "71-76",
            "text": """Affordable housing provision is required on qualifying sites:

THRESHOLDS:
- 10+ dwellings or sites of 0.5+ hectares: 20% affordable housing

TENURE:
- 50% social/affordable rent
- 50% intermediate (including First Homes)

VIABILITY:
- Reduced provision may be acceptable with viability evidence
- Off-site provision or commuted sum only in exceptional circumstances""",
            "relevance_triggers": ["affordable housing", "housing"],
        },
        "HO4": {
            "id": "HO4",
            "name": "Specialist and Adaptable Housing",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Housing",
            "page": "77-80",
            "text": "New housing development should meet the needs of an ageing population and people with disabilities. All new dwellings should meet Building Regulations M4(2) (accessible and adaptable). 5% of dwellings on major sites should meet M4(3) (wheelchair accessible).",
            "relevance_triggers": ["accessible", "adaptable", "housing"],
        },
        "HO5": {
            "id": "HO5",
            "name": "Locations for Purpose Built Student Accommodation",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Housing",
            "page": "81-86",
            "text": "Purpose-built student accommodation should be located in the City Centre, within 400m of university campuses, or within 400m of high-frequency public transport routes to universities. Development should not result in an over-concentration of student housing.",
            "relevance_triggers": ["student", "pbsa", "university"],
        },
        "HO6": {
            "id": "HO6",
            "name": "Houses in Multiple Occupation and Sui Generis Uses",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Housing",
            "page": "87-92",
            "text": "Change of use to HMO will be permitted where: it would not result in HMOs exceeding 10% of properties within 100m; adequate refuse storage and cycle parking is provided; and there would be no unacceptable impact on residential amenity.",
            "relevance_triggers": ["hmo", "house in multiple occupation", "change of use"],
        },
        "HE1": {
            "id": "HE1",
            "name": "Proposals Affecting Heritage Assets",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Heritage",
            "page": "96-104",
            "text": """Development affecting heritage assets should:
a) Conserve and enhance significance, character and setting
b) Be of high quality design that respects context
c) Demonstrate understanding of significance through Heritage Statement

DESIGNATED ASSETS:
- Great weight given to conservation
- Substantial harm should be exceptional/wholly exceptional
- Less than substantial harm weighed against public benefits

NON-DESIGNATED ASSETS:
- Balanced judgement based on scale of harm and significance""",
            "relevance_triggers": ["heritage", "listed building", "conservation area"],
        },
        "HE2": {
            "id": "HE2",
            "name": "Conservation Areas",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Heritage",
            "page": "105-110",
            "text": "Development within or affecting the setting of conservation areas should preserve or enhance the character and appearance of the area. Proposals for demolition will only be permitted where justified and replacement development is secured. Key views and landmarks should be protected.",
            "relevance_triggers": ["conservation area", "heritage"],
        },
        "HE3": {
            "id": "HE3",
            "name": "Archaeology",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Heritage",
            "page": "111-114",
            "text": "Development affecting sites of archaeological interest should be accompanied by appropriate assessment and evaluation. Significant remains should be preserved in situ where possible. Where preservation is not justified, remains should be appropriately recorded.",
            "relevance_triggers": ["archaeology", "archaeological"],
        },
        "EN1": {
            "id": "EN1",
            "name": "Development of Open Space",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "118-122",
            "text": "Development on open space will only be permitted where: an assessment shows the space is surplus to requirements; replacement of equivalent or better quality is provided; or the development is for ancillary facilities that would enhance the use of the space.",
            "relevance_triggers": ["open space", "recreation", "green space"],
        },
        "EN2": {
            "id": "EN2",
            "name": "Open Space in New Development",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "123-128",
            "text": """New residential development should provide open space:

STANDARDS:
- Parks and gardens: 1.0 ha per 1,000 population
- Outdoor sports: 1.6 ha per 1,000 population
- Amenity greenspace: 0.7 ha per 1,000 population
- Children's play: 0.25 ha per 1,000 population

Contributions may be made to off-site provision where on-site provision is not feasible.""",
            "relevance_triggers": ["open space", "housing", "recreation"],
        },
        "EN3": {
            "id": "EN3",
            "name": "Playing Fields and Outdoor Sports Facilities",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "129-132",
            "text": "Development resulting in the loss of playing fields or outdoor sports facilities will not be permitted unless: replacement facilities of equivalent or better quality are provided; the development is for alternative sports provision; or assessment demonstrates the facility is surplus.",
            "relevance_triggers": ["sports", "playing fields", "recreation"],
        },
        "EN4": {
            "id": "EN4",
            "name": "Green Infrastructure",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "133-138",
            "text": "Development should protect and enhance green infrastructure networks. New development should incorporate green infrastructure elements including trees, landscaping, green roofs and walls where appropriate. Connectivity between green spaces should be maintained and enhanced.",
            "relevance_triggers": ["green infrastructure", "trees", "landscaping"],
        },
        "EN5": {
            "id": "EN5",
            "name": "Trees",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "139-144",
            "text": """Development should retain and protect existing trees:
- Tree Survey (BS 5837:2012) required where trees present
- Category A and B trees should be retained
- Replacement planting at 2:1 ratio where removal unavoidable
- Root Protection Areas must be protected during construction
- TPO consent required for works to protected trees""",
            "relevance_triggers": ["trees", "tpo", "landscaping"],
        },
        "EN6": {
            "id": "EN6",
            "name": "Biodiversity",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "145-152",
            "text": """Development should protect and enhance biodiversity:

PROTECTED SITES:
- International/national sites: Highest protection
- Local Wildlife Sites: Protection proportionate to significance

PROTECTED SPECIES:
- Ecological surveys required where protected species may be present
- Mitigation hierarchy: avoid, mitigate, compensate

BIODIVERSITY NET GAIN:
- Minimum 10% net gain required (measured using DEFRA Metric)
- Habitat creation and enhancement on-site preferred""",
            "relevance_triggers": ["biodiversity", "ecology", "wildlife", "habitat"],
        },
        "EN7": {
            "id": "EN7",
            "name": "Contaminated Land",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "153-156",
            "text": "Development on or near potentially contaminated land should be accompanied by appropriate investigation and, where necessary, remediation. The applicant must demonstrate that the site can be made safe for the proposed use. Remediation should be completed before occupation.",
            "relevance_triggers": ["contamination", "pollution", "remediation"],
        },
        "EN8": {
            "id": "EN8",
            "name": "Air Quality",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "157-162",
            "text": "Development should not result in unacceptable impacts on air quality. Development within or adjacent to Air Quality Management Areas should demonstrate how impacts will be mitigated. Major development should include measures to minimise emissions during construction and operation.",
            "relevance_triggers": ["air quality", "aqma", "pollution"],
        },
        "EN9": {
            "id": "EN9",
            "name": "Managing Flood Risk",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Environment",
            "page": "163-172",
            "text": """Development should avoid areas at risk of flooding and not increase flood risk:

SEQUENTIAL TEST:
- Development should be directed to areas at lowest flood risk
- Sequential Test required for development in Flood Zones 2 and 3

FLOOD RISK ASSESSMENT:
- Required for development in Flood Zones 2 and 3
- Required for sites over 1 hectare in Flood Zone 1
- Required in areas of surface water flood risk

SUSTAINABLE DRAINAGE:
- SuDS required for all major development
- Discharge rates should not exceed greenfield rates
- 40% climate change allowance for drainage design""",
            "relevance_triggers": ["flood", "drainage", "suds"],
        },
        "TR1": {
            "id": "TR1",
            "name": "Parking and Travel Planning",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Transport",
            "page": "176-184",
            "text": """Development should provide parking in accordance with adopted standards:

PARKING ZONES:
- Zone 1 (City Centre): Car-free or minimal parking
- Zone 2 (Edge of Centre): Reduced parking standards
- Zone 3 (Outer Areas): Standard parking provision

CYCLE PARKING:
- Residential: 1 space per bedroom (long stay), 1 per 20 dwellings (short stay)
- Non-residential: As per adopted standards

TRAVEL PLANS:
- Required for major development
- Should set targets for modal shift""",
            "relevance_triggers": ["parking", "transport", "travel plan"],
        },
        "TR2": {
            "id": "TR2",
            "name": "Transport Assessment",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Transport",
            "page": "185-190",
            "text": """Development generating significant travel demand should be accompanied by:

TRANSPORT STATEMENT:
- 30-80 vehicle trips per day (typical threshold)

TRANSPORT ASSESSMENT:
- 80+ vehicle trips per day
- Major development generating significant travel

REQUIREMENTS:
- Safe access for all users
- No unacceptable impact on highway safety
- No severe residual cumulative impact on road network""",
            "relevance_triggers": ["transport", "highway", "access"],
        },
        "SH1": {
            "id": "SH1",
            "name": "Retail Hierarchy",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Retail",
            "page": "194-198",
            "text": "Town centre uses should be directed to locations in accordance with the retail hierarchy: City Centre (primary); District Centres; Local Centres. Sequential test applies to proposals outside defined centres. The vitality and viability of centres will be protected and enhanced.",
            "relevance_triggers": ["retail", "town centre", "sequential test"],
        },
        "SH2": {
            "id": "SH2",
            "name": "Development in the City Centre Primary Shopping Area",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Retail",
            "page": "199-204",
            "text": "Within the Primary Shopping Area, retail uses (Class E) will be supported at ground floor level. Active frontages should be maintained. Upper floors are encouraged for complementary uses including residential, office and leisure.",
            "relevance_triggers": ["city centre", "retail", "commercial"],
        },
        "SH3": {
            "id": "SH3",
            "name": "District Centres",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Retail",
            "page": "205-210",
            "text": "District centres will be maintained as the focus for convenience retail and local services. Proposals that would undermine the vitality and viability of district centres will be resisted. Changes of use from retail should not result in an unacceptable concentration of non-retail uses.",
            "relevance_triggers": ["district centre", "retail", "local services"],
        },
        "SH4": {
            "id": "SH4",
            "name": "Local Centres and Neighbourhood Parades",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Retail",
            "page": "211-214",
            "text": "Local centres and neighbourhood parades serve an important role in providing for day-to-day convenience needs. The loss of local retail provision will be resisted unless it can be demonstrated that the use is no longer viable and adequate alternative provision exists.",
            "relevance_triggers": ["local centre", "retail", "neighbourhood"],
        },
        "SH5": {
            "id": "SH5",
            "name": "Hot Food Takeaways",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Retail",
            "page": "215-218",
            "text": "Hot food takeaway uses will not be permitted within 400m of the boundary of a primary or secondary school. Proposals will be assessed against cumulative impact on the vitality of centres, residential amenity, highway safety and public health.",
            "relevance_triggers": ["hot food takeaway", "a5", "health"],
        },
        "EE1": {
            "id": "EE1",
            "name": "Protecting Existing Employment Land",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Employment",
            "page": "222-228",
            "text": "Employment land (Use Classes E(g), B2, B8) will be protected. Loss will be resisted unless: the site has been marketed unsuccessfully for 12+ months; the proposed use generates equivalent employment; or there are significant regeneration benefits. Key Employment Areas receive the highest protection.",
            "relevance_triggers": ["employment", "industrial", "commercial", "office"],
        },
        "EE2": {
            "id": "EE2",
            "name": "Employment Uses within Mixed Use Development",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Employment",
            "page": "229-232",
            "text": "Mixed use development incorporating employment uses will be supported in appropriate locations. Employment floorspace should be designed to be flexible and meet modern occupier requirements. Residential and employment uses should be compatible.",
            "relevance_triggers": ["mixed use", "employment", "commercial"],
        },
        "EE3": {
            "id": "EE3",
            "name": "New Employment Development",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Employment",
            "page": "233-236",
            "text": "New employment development will be supported in sustainable locations. Proposals should demonstrate how they will contribute to economic growth and job creation. Development should be accessible by sustainable transport modes.",
            "relevance_triggers": ["employment", "commercial", "industrial"],
        },
        "RE1": {
            "id": "RE1",
            "name": "Telecommunications",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Infrastructure",
            "page": "240-244",
            "text": "Telecommunications development will be supported where sited and designed to minimise visual impact. Operators should demonstrate consideration of existing sites, masts and structures. Development should not harm the character of conservation areas or the setting of listed buildings.",
            "relevance_triggers": ["telecommunications", "mast", "5g"],
        },
        "RE2": {
            "id": "RE2",
            "name": "Renewable Energy and Low Carbon Energy Generation",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Climate",
            "page": "245-250",
            "text": "Renewable and low carbon energy development will be supported where impacts are or can be made acceptable. Wind turbines must demonstrate that identified impacts are acceptable. Solar installations should avoid the best and most versatile agricultural land.",
            "relevance_triggers": ["renewable", "solar", "wind", "energy"],
        },
        "IN1": {
            "id": "IN1",
            "name": "Developer Contributions",
            "source": "Nottingham Local Plan Part 2 (2020)",
            "section": "Infrastructure",
            "page": "254-262",
            "text": """Development will be required to contribute to infrastructure provision:

COMMUNITY INFRASTRUCTURE LEVY:
- CIL applies to most residential and retail development
- Rates set in Charging Schedule

SECTION 106:
- Site-specific obligations for matters CIL cannot address
- Must meet Regulation 122 tests

REGULATION 122 TESTS:
- Necessary to make development acceptable
- Directly related to development
- Fairly and reasonably related in scale and kind""",
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
    "nottingham": NOTTINGHAM_LOCAL_PLAN,
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
