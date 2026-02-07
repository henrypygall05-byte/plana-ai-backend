"""
Comprehensive Planning Policy Engine.

Contains the complete NPPF (National Planning Policy Framework) and
Newcastle Local Plan policies with paragraph-level detail for
evidence-based planning assessments.

This enables:
- Precise policy citations with paragraph numbers
- Policy matching based on application characteristics
- Conflict identification between policies
- Weight assessment (statutory vs material consideration)
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PolicyParagraph:
    """A specific paragraph within a policy."""
    number: str  # e.g., "130", "199"
    text: str
    key_tests: list[str] = field(default_factory=list)  # Key tests/criteria in this paragraph


@dataclass
class Policy:
    """A planning policy with full detail."""
    id: str
    name: str
    source: str
    source_type: str  # NPPF, Core Strategy, DAP, SPD
    chapter: str | None = None
    section: str | None = None
    weight: str = "full"  # full, significant, moderate, limited
    paragraphs: list[PolicyParagraph] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)  # Keywords that trigger this policy
    conflicts_with: list[str] = field(default_factory=list)  # Policies that may conflict
    summary: str = ""


# =============================================================================
# NATIONAL PLANNING POLICY FRAMEWORK (NPPF) - December 2023
# =============================================================================

NPPF_POLICIES: dict[str, Policy] = {
    # Chapter 2: Achieving sustainable development
    "NPPF-2": Policy(
        id="NPPF-2",
        name="Achieving sustainable development",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="2",
        weight="full",
        summary="The presumption in favour of sustainable development is at the heart of the Framework.",
        triggers=["all", "principle", "sustainable"],
        paragraphs=[
            PolicyParagraph(
                number="7",
                text="The purpose of the planning system is to contribute to the achievement of sustainable development. At a very high level, the objective of sustainable development can be summarised as meeting the needs of the present without compromising the ability of future generations to meet their own needs.",
                key_tests=["meeting present needs", "not compromising future generations"],
            ),
            PolicyParagraph(
                number="8",
                text="Achieving sustainable development means that the planning system has three overarching objectives: an economic objective, a social objective, and an environmental objective.",
                key_tests=["economic objective", "social objective", "environmental objective"],
            ),
            PolicyParagraph(
                number="10",
                text="So that sustainable development is pursued in a positive way, at the heart of the Framework is a presumption in favour of sustainable development.",
                key_tests=["presumption in favour"],
            ),
            PolicyParagraph(
                number="11",
                text="Plans and decisions should apply a presumption in favour of sustainable development. For decision-taking this means: approving development proposals that accord with an up-to-date development plan without delay; or where there are no relevant development plan policies, or the policies most important for determining the application are out-of-date, granting permission unless the application of policies in the Framework that protect areas or assets of particular importance provides a clear reason for refusing the development proposed, or any adverse impacts of doing so would significantly and demonstrably outweigh the benefits.",
                key_tests=["accord with development plan", "approve without delay", "tilted balance"],
            ),
        ],
    ),

    # Chapter 4: Decision-making
    "NPPF-4": Policy(
        id="NPPF-4",
        name="Decision-making",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="4",
        weight="full",
        summary="Local planning authorities should approach decisions on proposed development in a positive and creative way.",
        triggers=["decision", "determination", "all"],
        paragraphs=[
            PolicyParagraph(
                number="38",
                text="Local planning authorities should approach decisions on proposed development in a positive and creative way. They should use the full range of planning tools available and work proactively with applicants to secure developments that will improve the economic, social and environmental conditions of the area. Decision-makers at every level should seek to approve applications for sustainable development where possible.",
                key_tests=["positive approach", "proactive working", "approve where possible"],
            ),
            PolicyParagraph(
                number="47",
                text="Planning law requires that applications for planning permission be determined in accordance with the development plan, unless material considerations indicate otherwise.",
                key_tests=["accordance with development plan", "material considerations"],
            ),
        ],
    ),

    # Chapter 5: Delivering a sufficient supply of homes
    "NPPF-5": Policy(
        id="NPPF-5",
        name="Delivering a sufficient supply of homes",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="5",
        weight="full",
        summary="To support the Government's objective of significantly boosting the supply of homes.",
        triggers=["housing", "dwelling", "residential", "flat", "apartment", "new home"],
        paragraphs=[
            PolicyParagraph(
                number="60",
                text="To support the Government's objective of significantly boosting the supply of homes, it is important that a sufficient amount and variety of land can come forward where it is needed.",
                key_tests=["boosting supply", "sufficient land"],
            ),
            PolicyParagraph(
                number="69",
                text="Small and medium sized sites can make an important contribution to meeting the housing requirement of an area, and are often built-out relatively quickly.",
                key_tests=["small sites contribution"],
            ),
        ],
    ),

    # Chapter 9: Promoting sustainable transport
    "NPPF-9": Policy(
        id="NPPF-9",
        name="Promoting sustainable transport",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="9",
        weight="full",
        summary="Transport issues should be considered from the earliest stages of plan-making and development proposals.",
        triggers=["transport", "parking", "highway", "access", "traffic"],
        paragraphs=[
            PolicyParagraph(
                number="104",
                text="Transport issues should be considered from the earliest stages of plan-making and development proposals, so that the potential impacts of development on transport networks can be addressed.",
                key_tests=["early consideration", "network impacts"],
            ),
            PolicyParagraph(
                number="110",
                text="In assessing sites that may be allocated for development in plans, or specific applications for development, it should be ensured that: appropriate opportunities to promote sustainable transport modes can be taken up; safe and suitable access to the site can be achieved for all users; and the design of streets, parking areas, other transport elements and the content of associated standards reflects current national guidance.",
                key_tests=["sustainable transport", "safe access", "design standards"],
            ),
            PolicyParagraph(
                number="111",
                text="Development should only be prevented or refused on highways grounds if there would be an unacceptable impact on highway safety, or the residual cumulative impacts on the road network would be severe.",
                key_tests=["unacceptable highway safety impact", "severe cumulative impact"],
            ),
        ],
    ),

    # Chapter 11: Making effective use of land
    "NPPF-11": Policy(
        id="NPPF-11",
        name="Making effective use of land",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="11",
        weight="full",
        summary="Planning policies and decisions should promote an effective use of land in meeting the need for homes and other uses.",
        triggers=["land use", "density", "previously developed", "brownfield"],
        paragraphs=[
            PolicyParagraph(
                number="119",
                text="Planning policies and decisions should promote an effective use of land in meeting the need for homes and other uses, while safeguarding and improving the environment and ensuring safe and healthy living conditions.",
                key_tests=["effective use", "safeguard environment", "healthy living"],
            ),
            PolicyParagraph(
                number="120",
                text="Planning policies and decisions should give substantial weight to the value of using suitable brownfield land within settlements for homes and other identified needs, and support appropriate opportunities to remediate despoiled, degraded, derelict, contaminated or unstable land.",
                key_tests=["substantial weight to brownfield", "remediation support"],
            ),
        ],
    ),

    # Chapter 12: Achieving well-designed places
    "NPPF-12": Policy(
        id="NPPF-12",
        name="Achieving well-designed places",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="12",
        weight="full",
        summary="The creation of high quality, beautiful and sustainable buildings and places is fundamental to what the planning and development process should achieve.",
        triggers=["design", "appearance", "character", "extension", "alteration", "visual", "all"],
        paragraphs=[
            PolicyParagraph(
                number="126",
                text="The creation of high quality, beautiful and sustainable buildings and places is fundamental to what the planning and development process should achieve. Good design is a key aspect of sustainable development, creates better places in which to live and work and helps make development acceptable to communities.",
                key_tests=["high quality design", "sustainable buildings", "acceptable to communities"],
            ),
            PolicyParagraph(
                number="130",
                text="Planning policies and decisions should ensure that developments: will function well and add to the overall quality of the area; are visually attractive as a result of good architecture, layout and appropriate and effective landscaping; are sympathetic to local character and history, including the surrounding built environment and landscape setting; establish or maintain a strong sense of place; optimise the potential of the site to accommodate and sustain an appropriate amount and mix of development; and create places that are safe, inclusive and accessible.",
                key_tests=["function well", "visually attractive", "sympathetic to character", "sense of place", "safe and inclusive"],
            ),
            PolicyParagraph(
                number="131",
                text="Trees make an important contribution to the character and quality of urban environments, and can also help mitigate and adapt to climate change. Planning policies and decisions should ensure that new streets are tree-lined, and that opportunities are taken to incorporate trees elsewhere in developments.",
                key_tests=["trees contribution", "tree-lined streets"],
            ),
            PolicyParagraph(
                number="134",
                text="Development that is not well designed should be refused, especially where it fails to reflect local design policies and government guidance on design. Conversely, significant weight should be given to development which reflects local design policies and government guidance on design, and outstanding or innovative designs which promote high levels of sustainability.",
                key_tests=["refuse poor design", "weight to good design", "innovative design"],
            ),
        ],
    ),

    # Chapter 13: Protecting Green Belt land
    "NPPF-13": Policy(
        id="NPPF-13",
        name="Protecting Green Belt land",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="13",
        weight="full",
        summary="The Government attaches great importance to Green Belts. The fundamental aim is to prevent urban sprawl by keeping land permanently open.",
        triggers=["green belt", "openness", "sprawl"],
        paragraphs=[
            PolicyParagraph(
                number="137",
                text="The Government attaches great importance to Green Belts. The fundamental aim of Green Belt policy is to prevent urban sprawl by keeping land permanently open; the essential characteristics of Green Belts are their openness and their permanence.",
                key_tests=["prevent sprawl", "openness", "permanence"],
            ),
            PolicyParagraph(
                number="138",
                text="Green Belt serves five purposes: to check the unrestricted sprawl of large built-up areas; to prevent neighbouring towns merging; to assist in safeguarding the countryside from encroachment; to preserve the setting and special character of historic towns; and to assist in urban regeneration.",
                key_tests=["five purposes", "check sprawl", "prevent merging", "safeguard countryside"],
            ),
            PolicyParagraph(
                number="147",
                text="Inappropriate development is, by definition, harmful to the Green Belt and should not be approved except in very special circumstances.",
                key_tests=["inappropriate harmful by definition", "very special circumstances"],
            ),
            PolicyParagraph(
                number="148",
                text="When considering any planning application, local planning authorities should ensure that substantial weight is given to any harm to the Green Belt. 'Very special circumstances' will not exist unless the potential harm to the Green Belt by reason of inappropriateness, and any other harm resulting from the proposal, is clearly outweighed by other considerations.",
                key_tests=["substantial weight to harm", "clearly outweighed"],
            ),
            PolicyParagraph(
                number="149",
                text="A local planning authority should regard the construction of new buildings as inappropriate in the Green Belt. Exceptions to this are: buildings for agriculture and forestry; the provision of appropriate facilities for outdoor sport and recreation; the extension or alteration of a building provided that it does not result in disproportionate additions over and above the size of the original building; the replacement of a building, provided the new building is in the same use and not materially larger; limited infilling in villages; limited affordable housing for local community needs; and limited infilling or the partial or complete redevelopment of previously developed land.",
                key_tests=["new buildings inappropriate", "exceptions listed", "proportionate extensions"],
            ),
            PolicyParagraph(
                number="150",
                text="Certain other forms of development are also not inappropriate in the Green Belt provided they preserve its openness and do not conflict with the purposes of including land within it. These are: mineral extraction; engineering operations; local transport infrastructure; the re-use of buildings; material changes in the use of land; and development brought forward under a Community Right to Build Order or Neighbourhood Development Order.",
                key_tests=["other acceptable development", "preserve openness", "not conflict with purposes"],
            ),
        ],
    ),

    # Chapter 14: Meeting the challenge of climate change
    "NPPF-14": Policy(
        id="NPPF-14",
        name="Meeting the challenge of climate change, flooding and coastal change",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="14",
        weight="full",
        summary="The planning system should support the transition to a low carbon future in a changing climate.",
        triggers=["flood", "climate", "renewable", "energy", "coastal"],
        paragraphs=[
            PolicyParagraph(
                number="152",
                text="The planning system should support the transition to a low carbon future in a changing climate, taking full account of flood risk and coastal change.",
                key_tests=["low carbon transition", "flood risk consideration"],
            ),
            PolicyParagraph(
                number="159",
                text="Inappropriate development in areas at risk of flooding should be avoided by directing development away from areas at highest risk. Where development is necessary in such areas, the development should be made safe for its lifetime without increasing flood risk elsewhere.",
                key_tests=["avoid flood risk areas", "safe for lifetime", "no increased risk"],
            ),
        ],
    ),

    # Chapter 15: Conserving and enhancing the natural environment
    "NPPF-15": Policy(
        id="NPPF-15",
        name="Conserving and enhancing the natural environment",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="15",
        weight="full",
        summary="Planning policies and decisions should contribute to and enhance the natural and local environment.",
        triggers=["biodiversity", "ecology", "landscape", "natural", "wildlife", "tree", "habitat"],
        paragraphs=[
            PolicyParagraph(
                number="174",
                text="Planning policies and decisions should contribute to and enhance the natural and local environment by: protecting and enhancing valued landscapes, sites of biodiversity or geological value and soils; recognising the intrinsic character and beauty of the countryside; and minimising impacts on and providing net gains for biodiversity.",
                key_tests=["protect valued landscapes", "biodiversity net gain", "countryside character"],
            ),
            PolicyParagraph(
                number="180",
                text="When determining planning applications, local planning authorities should apply the following principles: if significant harm to biodiversity resulting from a development cannot be avoided, adequately mitigated, or, as a last resort, compensated for, then planning permission should be refused; development on land within or outside a Site of Special Scientific Interest should not normally be permitted; and development resulting in the loss or deterioration of irreplaceable habitats should be refused.",
                key_tests=["avoid significant harm", "mitigation hierarchy", "refuse if irreplaceable"],
            ),
        ],
    ),

    # Chapter 16: Conserving and enhancing the historic environment
    "NPPF-16": Policy(
        id="NPPF-16",
        name="Conserving and enhancing the historic environment",
        source="National Planning Policy Framework",
        source_type="NPPF",
        chapter="16",
        weight="full",
        summary="Heritage assets are an irreplaceable resource, and should be conserved in a manner appropriate to their significance.",
        triggers=["heritage", "conservation area", "listed building", "historic", "archaeology", "setting"],
        paragraphs=[
            PolicyParagraph(
                number="189",
                text="Heritage assets range from sites and buildings of local historic value to those of the highest significance, such as World Heritage Sites. These assets are an irreplaceable resource, and should be conserved in a manner appropriate to their significance, so that they can be enjoyed for their contribution to the quality of life of existing and future generations.",
                key_tests=["irreplaceable resource", "conserve appropriately", "future generations"],
            ),
            PolicyParagraph(
                number="194",
                text="In determining applications, local planning authorities should require an applicant to describe the significance of any heritage assets affected, including any contribution made by their setting. The level of detail should be proportionate to the assets' importance.",
                key_tests=["describe significance", "setting contribution", "proportionate detail"],
            ),
            PolicyParagraph(
                number="195",
                text="Local planning authorities should identify and assess the particular significance of any heritage asset that may be affected by a proposal, including by development affecting the setting of a heritage asset. They should take this into account when considering the impact of a proposal.",
                key_tests=["assess significance", "setting impacts"],
            ),
            PolicyParagraph(
                number="199",
                text="When considering the impact of a proposed development on the significance of a designated heritage asset, great weight should be given to the asset's conservation (and the more important the asset, the greater the weight should be). This is irrespective of whether any potential harm amounts to substantial harm, total loss or less than substantial harm to its significance.",
                key_tests=["great weight to conservation", "more important = greater weight"],
            ),
            PolicyParagraph(
                number="200",
                text="Any harm to, or loss of, the significance of a designated heritage asset (from its alteration or destruction, or from development within its setting), should require clear and convincing justification.",
                key_tests=["clear and convincing justification for harm"],
            ),
            PolicyParagraph(
                number="201",
                text="Where a proposed development will lead to substantial harm to (or total loss of significance of) a designated heritage asset, local planning authorities should refuse consent, unless it can be demonstrated that the substantial harm or total loss is necessary to achieve substantial public benefits that outweigh that harm or loss.",
                key_tests=["refuse substantial harm", "unless substantial public benefits"],
            ),
            PolicyParagraph(
                number="202",
                text="Where a development proposal will lead to less than substantial harm to the significance of a designated heritage asset, this harm should be weighed against the public benefits of the proposal including, where appropriate, securing its optimum viable use.",
                key_tests=["weigh less than substantial harm", "against public benefits"],
            ),
            PolicyParagraph(
                number="203",
                text="The effect of an application on the significance of a non-designated heritage asset should be taken into account in determining the application. In weighing applications that directly or indirectly affect non-designated heritage assets, a balanced judgement will be required having regard to the scale of any harm or loss and the significance of the heritage asset.",
                key_tests=["balanced judgement", "scale of harm vs significance"],
            ),
            PolicyParagraph(
                number="206",
                text="Local planning authorities should look for opportunities for new development within Conservation Areas and World Heritage Sites, and within the setting of heritage assets, to enhance or better reveal their significance. Proposals that preserve those elements of the setting that make a positive contribution to the asset should be treated favourably.",
                key_tests=["enhance significance", "preserve positive setting", "treat favourably"],
            ),
        ],
    ),
}


# =============================================================================
# NEWCASTLE CORE STRATEGY AND URBAN CORE PLAN (2015)
# =============================================================================

NEWCASTLE_CORE_STRATEGY: dict[str, Policy] = {
    "CS1": Policy(
        id="CS1",
        name="Spatial Strategy for Sustainable Growth",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="Development will be concentrated in the most sustainable locations.",
        triggers=["location", "sustainable", "urban", "growth"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="The Local Planning Authorities will deliver sustainable growth by directing development to the most sustainable locations within the urban area, making the best use of previously developed land, supporting sustainable transport, and protecting and enhancing environmental assets.",
                key_tests=["sustainable locations", "previously developed land", "sustainable transport"],
            ),
        ],
    ),
    "CS14": Policy(
        id="CS14",
        name="Wellbeing and Health",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="The health and wellbeing of communities will be maintained and improved.",
        triggers=["health", "wellbeing", "amenity"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="The health and wellbeing of communities will be maintained and improved by requiring development to contribute to creating an age-friendly, healthy and equitable living environment.",
                key_tests=["healthy environment", "age-friendly", "equitable"],
            ),
        ],
    ),
    "CS15": Policy(
        id="CS15",
        name="Place-making",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="Development will be required to contribute to good place-making through high quality and sustainable design.",
        triggers=["design", "place", "character", "quality", "all"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development will be required to contribute to good place-making through the delivery of high quality and sustainable design, and by responding positively to local distinctiveness and character.",
                key_tests=["high quality design", "sustainable design", "local character"],
            ),
            PolicyParagraph(
                number="2",
                text="Development should create places that are safe and inclusive, and designed to promote health and wellbeing, with particular consideration given to good standards of amenity.",
                key_tests=["safe and inclusive", "health and wellbeing", "amenity standards"],
            ),
        ],
    ),
    "CS16": Policy(
        id="CS16",
        name="Climate Change",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="Development will be directed towards locations with the lowest risk of flooding.",
        triggers=["flood", "climate", "sustainable drainage", "SUDS"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development will be directed towards locations that have the lowest risk of flooding, taking account of the impacts of climate change.",
                key_tests=["lowest flood risk", "climate change impacts"],
            ),
        ],
    ),
    "CS17": Policy(
        id="CS17",
        name="Promoting Good Design",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="New development should achieve a high standard of sustainable design and construction.",
        triggers=["design", "sustainable", "construction", "BREEAM"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="New development should achieve a high standard of sustainable design and construction, including measures that reduce energy consumption, carbon emissions and water use.",
                key_tests=["high standard design", "reduce energy", "reduce carbon", "reduce water"],
            ),
        ],
    ),
    "CS18": Policy(
        id="CS18",
        name="Green Infrastructure and the Natural Environment",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="Development proposals should maintain and improve the integrity and connectivity of the green infrastructure network.",
        triggers=["green", "natural", "biodiversity", "ecology", "tree", "landscape"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development proposals should maintain and improve the integrity and connectivity of the green infrastructure network, including biodiversity and geodiversity assets.",
                key_tests=["maintain green infrastructure", "improve connectivity", "biodiversity"],
            ),
        ],
    ),
    "CS19": Policy(
        id="CS19",
        name="Heritage",
        source="Newcastle Core Strategy and Urban Core Plan",
        source_type="Core Strategy",
        section="Strategic Policies",
        weight="full",
        summary="Development should conserve and enhance the historic environment.",
        triggers=["heritage", "conservation area", "listed building", "historic"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development should conserve and enhance the historic environment, including designated and non-designated heritage assets and their settings.",
                key_tests=["conserve heritage", "enhance heritage", "settings"],
            ),
        ],
    ),
}


# =============================================================================
# NEWCASTLE DEVELOPMENT AND ALLOCATIONS PLAN (2022)
# =============================================================================

NEWCASTLE_DAP: dict[str, Policy] = {
    # Design Policies
    "DM6.1": Policy(
        id="DM6.1",
        name="Design of New Development",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Design",
        weight="full",
        summary="Proposals will be required to demonstrate a positive response to urban design principles.",
        triggers=["design", "extension", "new build", "alteration", "all"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Proposals will be required to demonstrate a positive response to the following urban design principles: response to context and local character; positive contribution to sense of place; creation of a coherent development; appropriate scale and massing that respects the prevailing townscape character; active frontages; and designing out crime.",
                key_tests=["context response", "sense of place", "coherent development", "appropriate scale"],
            ),
            PolicyParagraph(
                number="2",
                text="Development should demonstrate high standards of design quality that respond positively to local character and distinctiveness, taking account of any design guidance such as Supplementary Planning Documents, Conservation Area Character Appraisals, or other design frameworks.",
                key_tests=["high design standards", "local character", "design guidance"],
            ),
        ],
    ),
    "DM6.6": Policy(
        id="DM6.6",
        name="Protection of Residential Amenity",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Design",
        weight="full",
        summary="Development should ensure that both existing and future occupiers of land and buildings are provided with a good standard of amenity.",
        triggers=["amenity", "residential", "neighbour", "overlooking", "daylight", "sunlight", "privacy", "extension", "householder"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development should ensure that both existing and future occupiers of land and buildings are provided with a good standard of amenity, particularly in terms of: outlook, privacy, daylight, sunlight, and disturbance from noise, odour, vibration, dust, and light pollution.",
                key_tests=["outlook", "privacy", "daylight", "sunlight", "disturbance"],
            ),
            PolicyParagraph(
                number="2",
                text="To achieve adequate levels of privacy, a minimum of 21 metres will normally be required between habitable room windows of dwellings that face each other, unless the site characteristics, existing levels of privacy, or design solutions can achieve adequate privacy at closer distances.",
                key_tests=["21m separation", "habitable rooms", "facing windows", "design solutions"],
            ),
            PolicyParagraph(
                number="3",
                text="Development should not result in unacceptable levels of overshadowing, overbearing, or a loss of outlook to neighbouring properties. A 45-degree daylight test will be applied to assess impacts on daylight where relevant.",
                key_tests=["no unacceptable overshadowing", "no overbearing", "45-degree test"],
            ),
        ],
    ),

    # Heritage Policies
    "DM15": Policy(
        id="DM15",
        name="Conservation of Heritage Assets",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Heritage",
        weight="full",
        summary="Proposals affecting heritage assets will be permitted where they sustain, conserve and enhance their significance.",
        triggers=["heritage", "conservation area", "listed building", "archaeology", "historic"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Proposals affecting a heritage asset will be permitted where they sustain, conserve and, where appropriate, enhance the significance, appearance, character and setting of heritage assets and their contribution to local distinctiveness, character and sense of place.",
                key_tests=["sustain significance", "conserve", "enhance", "setting"],
            ),
            PolicyParagraph(
                number="2",
                text="Where a development proposal will lead to less than substantial harm to the significance of a designated heritage asset, the harm will be weighed against the public benefits of the proposal.",
                key_tests=["less than substantial harm", "weigh against public benefits"],
            ),
            PolicyParagraph(
                number="3",
                text="Proposals that will lead to substantial harm to, or total loss of, a designated heritage asset will be refused unless it can be demonstrated that the proposal meets the tests in paragraph 201 of the NPPF.",
                key_tests=["refuse substantial harm", "NPPF paragraph 201 tests"],
            ),
        ],
    ),
    "DM16": Policy(
        id="DM16",
        name="Conservation Areas",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Heritage",
        weight="full",
        summary="Development within or affecting a conservation area will be permitted where it preserves or enhances its character or appearance.",
        triggers=["conservation area"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development within or affecting the setting of a conservation area will be permitted where it preserves or enhances the character or appearance of the conservation area, including views into and out of the area.",
                key_tests=["preserve character", "enhance character", "views"],
            ),
            PolicyParagraph(
                number="2",
                text="Development in conservation areas should: use materials sympathetic to the character of the area; retain features of architectural or historic interest; be of appropriate scale, form and detailing; and have regard to relevant Conservation Area Character Appraisals and Management Plans.",
                key_tests=["sympathetic materials", "retain features", "appropriate scale", "character appraisals"],
            ),
            PolicyParagraph(
                number="3",
                text="The demolition of buildings or structures within a conservation area that make a positive contribution to the area will not normally be permitted unless there are exceptional circumstances.",
                key_tests=["no demolition unless exceptional"],
            ),
        ],
    ),
    "DM17": Policy(
        id="DM17",
        name="Locally Listed Buildings and Non-Designated Heritage Assets",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Heritage",
        weight="full",
        summary="Development affecting non-designated heritage assets will require a balanced judgement.",
        triggers=["locally listed", "non-designated heritage", "local list"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development affecting a non-designated heritage asset will require a balanced judgement having regard to the scale of any harm or loss and the significance of the heritage asset.",
                key_tests=["balanced judgement", "scale of harm", "significance"],
            ),
            PolicyParagraph(
                number="2",
                text="Proposals should seek to retain, and where possible enhance, the significance of non-designated heritage assets, including locally listed buildings.",
                key_tests=["retain significance", "enhance where possible"],
            ),
        ],
    ),

    # Natural Environment Policies
    "DM27": Policy(
        id="DM27",
        name="Protecting and Enhancing Green Infrastructure",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Natural Environment",
        weight="full",
        summary="Development should protect and enhance green infrastructure assets.",
        triggers=["green infrastructure", "biodiversity", "ecology", "open space"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development should protect, enhance and manage existing green infrastructure assets, and where appropriate create new green infrastructure.",
                key_tests=["protect", "enhance", "manage", "create new"],
            ),
        ],
    ),
    "DM28": Policy(
        id="DM28",
        name="Trees, Woodlands and Hedgerows",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Natural Environment",
        weight="full",
        summary="Development will be required to protect trees, woodlands and hedgerows of value.",
        triggers=["tree", "TPO", "woodland", "hedgerow", "arboricultural"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development will be required to protect trees, woodlands and hedgerows of value, particularly those covered by Tree Preservation Orders, ancient woodland, and veteran trees.",
                key_tests=["protect TPO trees", "ancient woodland", "veteran trees"],
            ),
            PolicyParagraph(
                number="2",
                text="Where the loss of trees is unavoidable, appropriate replacement planting will be required, preferably on site or within the local area.",
                key_tests=["replacement planting", "on site preferred"],
            ),
            PolicyParagraph(
                number="3",
                text="Development should retain trees of value and incorporate them into the design of the scheme, ensuring adequate root protection areas are maintained.",
                key_tests=["retain valuable trees", "incorporate in design", "root protection"],
            ),
        ],
    ),

    # Transport Policies
    "DM7": Policy(
        id="DM7",
        name="Transport and Highways",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Transport",
        weight="full",
        summary="Development should be accessible by sustainable transport modes and provide appropriate parking.",
        triggers=["parking", "highway", "access", "transport", "traffic"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Development should be accessible by a range of sustainable transport modes, including walking, cycling and public transport.",
                key_tests=["sustainable transport access", "walking", "cycling", "public transport"],
            ),
            PolicyParagraph(
                number="2",
                text="Development should provide safe and suitable access for all users, including pedestrians, cyclists, and vehicles, and should not result in unacceptable impacts on highway safety or the operation of the road network.",
                key_tests=["safe access", "no unacceptable highway impact"],
            ),
            PolicyParagraph(
                number="3",
                text="Parking provision should accord with the Council's adopted parking standards, unless evidence demonstrates that a variation is justified.",
                key_tests=["parking standards", "justified variation"],
            ),
        ],
    ),

    # Other Key Policies
    "DM3.1": Policy(
        id="DM3.1",
        name="Employment Land",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Economy",
        weight="full",
        summary="Employment land will be protected from non-employment uses.",
        triggers=["employment", "office", "industrial", "commercial"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Proposals for non-employment uses on allocated or safeguarded employment land will not normally be permitted unless the land is no longer viable for employment use.",
                key_tests=["protect employment land", "viability evidence"],
            ),
        ],
    ),
    "DM4.1": Policy(
        id="DM4.1",
        name="Retail Centres",
        source="Development and Allocations Plan",
        source_type="DAP",
        section="Retail",
        weight="full",
        summary="Retail development should be directed to designated centres.",
        triggers=["retail", "shop", "town centre"],
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Retail development should be directed to designated centres. Proposals for retail development outside centres will be subject to the sequential test.",
                key_tests=["directed to centres", "sequential test"],
            ),
        ],
    ),
}


def _extract_key_requirements(policy_text: str) -> list[str]:
    """
    Extract key requirements from policy text.

    Looks for common patterns like lettered lists (a), b), etc.) and bullet points.
    """
    import re

    requirements = []

    # Look for lettered requirements (a), b), c) or a., b., c.)
    letter_pattern = r"[a-z][\)\.]?\s*([A-Z][^;\n\.]+)"
    letter_matches = re.findall(letter_pattern, policy_text)
    for match in letter_matches[:6]:  # Limit to first 6
        cleaned = match.strip()
        if len(cleaned) > 10 and len(cleaned) < 150:
            requirements.append(cleaned)

    # Look for dash/bullet points
    bullet_pattern = r"[-•]\s*([A-Z][^;\n\.]+)"
    bullet_matches = re.findall(bullet_pattern, policy_text)
    for match in bullet_matches[:4]:  # Add up to 4 more
        cleaned = match.strip()
        if len(cleaned) > 10 and len(cleaned) < 150 and cleaned not in requirements:
            requirements.append(cleaned)

    # Look for KEY sections like "KEY REQUIREMENTS:" or "DESIGN PRINCIPLES:"
    section_pattern = r"(?:KEY REQUIREMENTS|DESIGN PRINCIPLES|ASSESSMENT CRITERIA):\s*\n?((?:[-•a-z\d\)\.].*\n?)+)"
    section_matches = re.findall(section_pattern, policy_text, re.IGNORECASE)
    for section in section_matches:
        items = re.findall(r"[-•a-z\d\)\.]?\s*([A-Z][^\n]+)", section)
        for item in items[:4]:
            cleaned = item.strip()
            if len(cleaned) > 10 and len(cleaned) < 150 and cleaned not in requirements:
                requirements.append(cleaned)

    # If no structured requirements found, extract key phrases from first paragraph
    if not requirements:
        first_para = policy_text.split("\n\n")[0] if "\n\n" in policy_text else policy_text[:300]
        # Look for "should", "must", "will be" phrases
        should_pattern = r"(?:should|must|will be|shall)\s+([^\.;]+)"
        should_matches = re.findall(should_pattern, first_para, re.IGNORECASE)
        for match in should_matches[:4]:
            cleaned = match.strip()
            if len(cleaned) > 10 and len(cleaned) < 100:
                requirements.append(cleaned.capitalize())

    return requirements[:8]  # Return max 8 requirements


def get_all_policies(council_id: str = "newcastle") -> dict[str, Policy]:
    """
    Get all policies from NPPF and the specified council's local plan.

    Args:
        council_id: The council ID (e.g., "newcastle", "broxtowe", "nottingham")

    Returns:
        Combined dictionary of NPPF policies and local plan policies
    """
    # Import complete databases
    from .local_plans_complete import LOCAL_PLANS_DATABASE
    from .nppf_complete import NPPF_PARAGRAPHS

    all_policies = {}

    # Add NPPF policies (these apply to all councils)
    all_policies.update(NPPF_POLICIES)

    # Get council-specific local plan policies
    council_data = LOCAL_PLANS_DATABASE.get(council_id.lower())
    if council_data and "policies" in council_data:
        # Convert local plan policies to Policy dataclass format
        for policy_id, policy_data in council_data["policies"].items():
            policy_text = policy_data.get("text", "")

            # Extract key requirements from policy text
            key_requirements = _extract_key_requirements(policy_text)

            # Create a PolicyParagraph with the full text and key requirements
            paragraphs = []
            if policy_text:
                paragraphs.append(PolicyParagraph(
                    number="1",
                    text=policy_text[:800] if len(policy_text) > 800 else policy_text,
                    key_tests=key_requirements,
                ))

            # Use more of the policy text in the summary (up to 500 chars)
            summary_text = policy_text[:500].strip()
            if len(policy_text) > 500:
                # Try to end at a sentence boundary
                last_period = summary_text.rfind(".")
                if last_period > 300:
                    summary_text = summary_text[:last_period + 1]
                else:
                    summary_text += "..."

            all_policies[policy_id] = Policy(
                id=policy_data.get("id", policy_id),
                name=policy_data.get("name", ""),
                source=policy_data.get("source", ""),
                source_type="Local Plan",
                section=policy_data.get("section", ""),
                weight="full",
                summary=summary_text,
                triggers=policy_data.get("relevance_triggers", []),
                paragraphs=paragraphs,
            )
    else:
        # Fallback to Newcastle policies if council not found
        all_policies.update(NEWCASTLE_CORE_STRATEGY)
        all_policies.update(NEWCASTLE_DAP)

    return all_policies


def get_relevant_policies(
    proposal: str,
    application_type: str,
    constraints: list[str],
    include_general: bool = True,
    council_id: str = "newcastle",
    site_address: str = "",
) -> list[Policy]:
    """
    Get policies relevant to an application based on its characteristics.

    Args:
        proposal: Description of the proposed development
        application_type: Type of planning application
        constraints: List of site constraints
        include_general: Include policies that apply to all applications
        council_id: The council ID (will be auto-detected from site_address if provided)
        site_address: Site address for auto-detecting the council

    Returns:
        List of relevant policies sorted by relevance
    """
    # ALWAYS detect council from address if address is provided
    # This ensures correct council is used regardless of what's passed in
    if site_address:
        from .local_plans_complete import detect_council_from_address
        detected_council = detect_council_from_address(site_address)
        if detected_council:
            council_id = detected_council
        from .local_plans_complete import detect_council_from_address
        council_id = detect_council_from_address(site_address)

    all_policies = get_all_policies(council_id)
    relevant = []

    proposal_lower = proposal.lower()
    app_type_lower = application_type.lower()
    constraints_lower = [c.lower() for c in constraints]

    for policy_id, policy in all_policies.items():
        relevance_score = 0

        for trigger in policy.triggers:
            if trigger == "all" and include_general:
                relevance_score += 1
                break
            if trigger in proposal_lower:
                relevance_score += 2
            if trigger in app_type_lower:
                relevance_score += 2
            for constraint in constraints_lower:
                if trigger in constraint:
                    relevance_score += 3  # Constraints are high priority

        if relevance_score > 0:
            relevant.append((policy, relevance_score))

    # Sort by relevance score descending
    relevant.sort(key=lambda x: x[1], reverse=True)

    return [policy for policy, score in relevant]


def get_policy_citation(policy_id: str, paragraph: str | None = None) -> str:
    """
    Get a formatted policy citation.

    Args:
        policy_id: The policy ID (e.g., "NPPF-16", "DM15")
        paragraph: Optional specific paragraph number

    Returns:
        Formatted citation string
    """
    all_policies = get_all_policies()

    if policy_id not in all_policies:
        return f"Policy {policy_id}"

    policy = all_policies[policy_id]

    if paragraph:
        for para in policy.paragraphs:
            if para.number == paragraph:
                return f"{policy.source} {policy.name} (paragraph {paragraph})"

    if policy.source_type == "NPPF":
        return f"NPPF Chapter {policy.chapter}: {policy.name}"
    else:
        # Avoid "Policy Policy X" duplication if id already starts with "Policy"
        policy_id = policy.id
        if policy_id.lower().startswith("policy"):
            return f"{policy.source} {policy_id}: {policy.name}"
        else:
            return f"{policy.source} Policy {policy_id}: {policy.name}"


def get_policy_test(policy_id: str, test_keyword: str) -> str | None:
    """
    Get the specific test/criterion from a policy paragraph.

    Args:
        policy_id: The policy ID
        test_keyword: Keyword to search for in key_tests

    Returns:
        The test text if found, None otherwise
    """
    all_policies = get_all_policies()

    if policy_id not in all_policies:
        return None

    policy = all_policies[policy_id]

    for para in policy.paragraphs:
        for test in para.key_tests:
            if test_keyword.lower() in test.lower():
                return f"Paragraph {para.number}: {test}"

    return None
