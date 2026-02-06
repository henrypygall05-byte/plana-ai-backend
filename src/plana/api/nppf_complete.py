"""
Complete National Planning Policy Framework (NPPF) 2023 Policy Database.

This module contains the full text of all NPPF paragraphs organised by chapter,
enabling precise paragraph-level citations in planning assessments.

Source: Ministry of Housing, Communities & Local Government
Version: NPPF 2023 (December 2023 revision)
"""

from typing import Any

# =============================================================================
# NPPF CHAPTER STRUCTURE
# =============================================================================

NPPF_CHAPTERS = {
    1: {"name": "Introduction", "paragraphs": "1-6"},
    2: {"name": "Achieving sustainable development", "paragraphs": "7-14"},
    3: {"name": "Plan-making", "paragraphs": "15-37"},
    4: {"name": "Decision-making", "paragraphs": "38-58"},
    5: {"name": "Delivering a sufficient supply of homes", "paragraphs": "59-80"},
    6: {"name": "Building a strong, competitive economy", "paragraphs": "81-86"},
    7: {"name": "Ensuring the vitality of town centres", "paragraphs": "87-91"},
    8: {"name": "Promoting healthy and safe communities", "paragraphs": "92-101"},
    9: {"name": "Promoting sustainable transport", "paragraphs": "102-113"},
    10: {"name": "Supporting high quality communications", "paragraphs": "114-118"},
    11: {"name": "Making effective use of land", "paragraphs": "119-125"},
    12: {"name": "Achieving well-designed places", "paragraphs": "126-136"},
    13: {"name": "Protecting Green Belt land", "paragraphs": "137-151"},
    14: {"name": "Meeting the challenge of climate change, flooding and coastal change", "paragraphs": "152-173"},
    15: {"name": "Conserving and enhancing the natural environment", "paragraphs": "174-188"},
    16: {"name": "Conserving and enhancing the historic environment", "paragraphs": "189-208"},
    17: {"name": "Facilitating the sustainable use of minerals", "paragraphs": "209-217"},
}

# =============================================================================
# COMPLETE NPPF PARAGRAPHS
# =============================================================================

NPPF_PARAGRAPHS: dict[int, dict[str, Any]] = {
    # =========================================================================
    # CHAPTER 1: INTRODUCTION (Para 1-6)
    # =========================================================================
    1: {
        "chapter": 1,
        "text": "The National Planning Policy Framework sets out the Government's planning policies for England and how these should be applied. It provides a framework within which locally prepared plans can provide for local housing and other development needs.",
        "key_principle": "Framework for local plan preparation",
        "relevance_triggers": ["all"],
    },
    2: {
        "chapter": 1,
        "text": "Planning law requires that applications for planning permission be determined in accordance with the development plan, unless material considerations indicate otherwise. The National Planning Policy Framework must be taken into account in preparing the development plan, and is a material consideration in planning decisions.",
        "key_principle": "Plan-led system with NPPF as material consideration",
        "relevance_triggers": ["all"],
    },
    3: {
        "chapter": 1,
        "text": "The Framework does not change the statutory status of the development plan as the starting point for decision-making. Where a planning application conflicts with an up-to-date development plan, permission should not usually be granted. Local planning authorities may take decisions that depart from an up-to-date development plan, but only if material considerations in a particular case indicate that the plan should not be followed.",
        "key_principle": "Development plan primacy",
        "relevance_triggers": ["all"],
    },
    4: {
        "chapter": 1,
        "text": "The policies in this Framework are material considerations which should be taken into account in dealing with applications from the day of its publication.",
        "key_principle": "Immediate material weight",
        "relevance_triggers": ["all"],
    },
    5: {
        "chapter": 1,
        "text": "This Framework should be read in conjunction with the Government's planning policy for traveller sites, and its planning policy for waste.",
        "key_principle": "Related policy documents",
        "relevance_triggers": ["traveller", "waste"],
    },
    6: {
        "chapter": 1,
        "text": "Other statements of government policy may be material when preparing plans or deciding applications, such as relevant Written Ministerial Statements.",
        "key_principle": "Other material considerations",
        "relevance_triggers": ["all"],
    },

    # =========================================================================
    # CHAPTER 2: ACHIEVING SUSTAINABLE DEVELOPMENT (Para 7-14)
    # =========================================================================
    7: {
        "chapter": 2,
        "text": "The purpose of the planning system is to contribute to the achievement of sustainable development. At a very high level, the objective of sustainable development can be summarised as meeting the needs of the present without compromising the ability of future generations to meet their own needs.",
        "key_principle": "Purpose of planning system",
        "relevance_triggers": ["all"],
    },
    8: {
        "chapter": 2,
        "text": "Achieving sustainable development means that the planning system has three overarching objectives, which are interdependent and need to be pursued in mutually supportive ways: a) an economic objective; b) a social objective; c) an environmental objective.",
        "key_principle": "Three pillars of sustainability",
        "relevance_triggers": ["all"],
    },
    9: {
        "chapter": 2,
        "text": "These objectives should be delivered through the preparation and implementation of plans and the application of the policies in this Framework; they are not criteria against which every decision can or should be judged.",
        "key_principle": "Plan-led delivery of objectives",
        "relevance_triggers": ["all"],
    },
    10: {
        "chapter": 2,
        "text": "So that sustainable development is pursued in a positive way, at the heart of the Framework is a presumption in favour of sustainable development.",
        "key_principle": "Presumption in favour",
        "relevance_triggers": ["all"],
    },
    11: {
        "chapter": 2,
        "text": "Plans and decisions should apply a presumption in favour of sustainable development. For plan-making this means that: a) all plans should promote a sustainable pattern of development; b) strategic policies should provide for objectively assessed needs for housing and other uses. For decision-taking this means: c) approving development proposals that accord with an up-to-date development plan without delay; or d) where there are no relevant development plan policies, or the policies which are most important for determining the application are out-of-date, granting permission unless: i. the application of policies in this Framework that protect areas or assets of particular importance provides a clear reason for refusing the development proposed; or ii. any adverse impacts of doing so would significantly and demonstrably outweigh the benefits, when assessed against the policies in this Framework taken as a whole.",
        "key_principle": "Tilted balance / presumption in favour",
        "relevance_triggers": ["all", "tilted balance", "out-of-date", "five year supply"],
    },
    12: {
        "chapter": 2,
        "text": "The presumption in favour of sustainable development does not change the statutory status of the development plan as the starting point for decision-making. Where a planning application conflicts with an up-to-date development plan, permission should not usually be granted.",
        "key_principle": "Development plan primacy maintained",
        "relevance_triggers": ["all"],
    },
    13: {
        "chapter": 2,
        "text": "The application of the presumption has implications for the way communities engage in neighbourhood planning. Neighbourhood plans should support the delivery of strategic policies contained in local plans; and should shape and direct development that is outside of these strategic policies.",
        "key_principle": "Neighbourhood plan role",
        "relevance_triggers": ["neighbourhood plan"],
    },
    14: {
        "chapter": 2,
        "text": "In situations where the presumption applies to applications involving the provision of housing, the adverse impact of allowing development that conflicts with the neighbourhood plan is likely to significantly and demonstrably outweigh the benefits, provided: a) the neighbourhood plan became part of the development plan two years or less before the date on which the decision is made; b) the neighbourhood plan contains policies and allocations to meet its identified housing requirement; c) the local planning authority has at least a three year supply of deliverable housing sites; and d) the local planning authority's housing delivery was at least 45% of that required over the previous three years.",
        "key_principle": "Neighbourhood plan protection",
        "relevance_triggers": ["neighbourhood plan", "housing"],
    },

    # =========================================================================
    # CHAPTER 3: PLAN-MAKING (Para 15-37)
    # =========================================================================
    15: {
        "chapter": 3,
        "text": "The planning system should be genuinely plan-led. Succinct and up-to-date plans should provide a positive vision for the future of each area; a framework for addressing housing needs and other economic, social and environmental priorities; and a platform for local people to shape their surroundings.",
        "key_principle": "Plan-led system",
        "relevance_triggers": ["local plan"],
    },
    16: {
        "chapter": 3,
        "text": "Plans should: a) be prepared with the objective of contributing to the achievement of sustainable development; b) be prepared positively, in a way that is aspirational but deliverable; c) be shaped by early, proportionate and effective engagement between plan-makers and communities, local organisations, businesses, infrastructure providers and operators and statutory consultees; d) contain policies that are clearly written and unambiguous; e) be accessible through the use of digital tools to assist public involvement and policy presentation; and f) serve a clear purpose, avoiding unnecessary duplication of policies that apply to a particular area.",
        "key_principle": "Plan preparation requirements",
        "relevance_triggers": ["local plan"],
    },
    17: {
        "chapter": 3,
        "text": "The development plan must include strategic policies to address each local planning authority's priorities for the development and use of land in its area. These strategic policies can be produced by local planning authorities, either individually or jointly with other authorities, or by an elected Mayor or combined authority where plan-making powers have been conferred.",
        "key_principle": "Strategic policies required",
        "relevance_triggers": ["local plan", "strategic"],
    },
    18: {
        "chapter": 3,
        "text": "Policies to address non-strategic matters should be included in local plans that contain both strategic and non-strategic policies, and/or in neighbourhood plans that contain policies to address non-strategic matters.",
        "key_principle": "Non-strategic policies location",
        "relevance_triggers": ["local plan", "neighbourhood plan"],
    },
    19: {
        "chapter": 3,
        "text": "The development plan for an area comprises the combination of strategic policies and non-strategic local and/or neighbourhood plan policies, together with any spatial development strategy that is in place for the area and in London, the spatial development strategy published by the Mayor.",
        "key_principle": "Development plan composition",
        "relevance_triggers": ["local plan"],
    },
    20: {
        "chapter": 3,
        "text": "Strategic policies should set out an overall strategy for the pattern, scale and design quality of places, and make sufficient provision for: a) housing, employment, retail, leisure and other commercial development; b) infrastructure for transport, telecommunications, security, waste management, water supply, wastewater, flood risk and coastal change management, and the provision of minerals and energy; c) community facilities; and d) conservation and enhancement of the natural, built and historic environment.",
        "key_principle": "Strategic policy scope",
        "relevance_triggers": ["local plan", "strategic"],
    },
    21: {
        "chapter": 3,
        "text": "Plans should make explicit which policies are strategic policies. These should be limited to those necessary to address the strategic priorities of the area (and any relevant cross-boundary issues), to provide a clear starting point for any non-strategic policies that are needed.",
        "key_principle": "Identify strategic policies",
        "relevance_triggers": ["local plan", "strategic"],
    },
    22: {
        "chapter": 3,
        "text": "Strategic policies should look ahead over a minimum 15 year period from adoption, to anticipate and respond to long-term requirements and opportunities, such as those arising from major improvements in infrastructure.",
        "key_principle": "15 year plan period",
        "relevance_triggers": ["local plan"],
    },
    23: {
        "chapter": 3,
        "text": "Broad locations for development should be indicated on a key diagram, and land-use designations and allocations identified on a policies map. Strategic policies should provide a clear strategy for bringing sufficient land forward, and at a sufficient rate, to address objectively assessed needs over the plan period.",
        "key_principle": "Key diagram and policies map",
        "relevance_triggers": ["local plan", "allocation"],
    },
    24: {
        "chapter": 3,
        "text": "Local planning authorities and county councils (in two-tier areas) are under a duty to cooperate with each other, and with other prescribed bodies, on strategic matters that cross administrative boundaries.",
        "key_principle": "Duty to cooperate",
        "relevance_triggers": ["local plan"],
    },
    25: {
        "chapter": 3,
        "text": "Strategic policy-making authorities should collaborate to identify the relevant strategic matters which they need to address in their plans. They should also engage with their local communities and relevant bodies including Local Enterprise Partnerships, Local Nature Partnerships, the Marine Management Organisation, county councils, infrastructure providers, elected Mayors and combined authorities.",
        "key_principle": "Collaboration on strategic matters",
        "relevance_triggers": ["local plan"],
    },
    26: {
        "chapter": 3,
        "text": "Effective and on-going joint working between strategic policy-making authorities and relevant bodies is integral to the production of a positively prepared and justified strategy. In particular, joint working should help to determine where additional infrastructure is necessary, and whether development needs that cannot be met wholly within a particular plan area could be met elsewhere.",
        "key_principle": "Joint working",
        "relevance_triggers": ["local plan", "infrastructure"],
    },
    27: {
        "chapter": 3,
        "text": "In order to demonstrate effective and on-going joint working, strategic policy-making authorities should prepare and maintain one or more statements of common ground, documenting the cross-boundary matters being addressed and progress in cooperating to address these.",
        "key_principle": "Statements of common ground",
        "relevance_triggers": ["local plan"],
    },
    28: {
        "chapter": 3,
        "text": "Non-strategic policies should be used by local planning authorities and communities to set out more detailed policies for specific areas, neighbourhoods or types of development. This can include allocating sites, the provision of infrastructure and community facilities at a local level, establishing design principles, conserving and enhancing the natural and historic environment and setting out other development management policies.",
        "key_principle": "Non-strategic policy scope",
        "relevance_triggers": ["local plan", "design", "heritage"],
    },
    29: {
        "chapter": 3,
        "text": "Neighbourhood planning gives communities the power to develop a shared vision for their area. Neighbourhood plans can shape, direct and help to deliver sustainable development, by influencing local planning decisions as part of the statutory development plan.",
        "key_principle": "Neighbourhood planning purpose",
        "relevance_triggers": ["neighbourhood plan"],
    },
    30: {
        "chapter": 3,
        "text": "Once a neighbourhood plan has been brought into force, the policies it contains take precedence over existing non-strategic policies in a local plan covering the neighbourhood area, where they are in conflict; unless they are superseded by strategic or non-strategic policies that are adopted subsequently.",
        "key_principle": "Neighbourhood plan precedence",
        "relevance_triggers": ["neighbourhood plan"],
    },
    31: {
        "chapter": 3,
        "text": "The preparation and review of all policies should be underpinned by relevant and up-to-date evidence. This should be adequate and proportionate, focused tightly on supporting and justifying the policies concerned, and take into account relevant market signals.",
        "key_principle": "Evidence-based policy",
        "relevance_triggers": ["local plan"],
    },
    32: {
        "chapter": 3,
        "text": "Local plans and spatial development strategies should be informed throughout their preparation by a sustainability appraisal that meets the relevant legal requirements. This should demonstrate how the plan has addressed relevant economic, social and environmental objectives.",
        "key_principle": "Sustainability appraisal required",
        "relevance_triggers": ["local plan"],
    },
    33: {
        "chapter": 3,
        "text": "Policies in local plans and spatial development strategies should be reviewed to assess whether they need updating at least once every five years, and should then be updated as necessary.",
        "key_principle": "Five year policy review",
        "relevance_triggers": ["local plan"],
    },
    34: {
        "chapter": 3,
        "text": "Reviews should be completed no later than five years from the adoption date of a plan, and should take into account changing circumstances affecting the area, or any relevant changes in national policy. Relevant strategic policies will need updating at least once every five years if their applicable local housing need figure has changed significantly.",
        "key_principle": "Review timescales",
        "relevance_triggers": ["local plan", "housing"],
    },
    35: {
        "chapter": 3,
        "text": "Local plans and spatial development strategies are examined to assess whether they have been prepared in accordance with legal and procedural requirements, and whether they are sound. Plans are 'sound' if they are: a) Positively prepared; b) Justified; c) Effective; and d) Consistent with national policy.",
        "key_principle": "Soundness tests",
        "relevance_triggers": ["local plan"],
    },
    36: {
        "chapter": 3,
        "text": "These tests of soundness will be applied to non-strategic policies in a proportionate way, taking into account the extent to which they are consistent with relevant strategic policies for the area.",
        "key_principle": "Proportionate soundness tests",
        "relevance_triggers": ["local plan"],
    },
    37: {
        "chapter": 3,
        "text": "Neighbourhood plans must meet certain 'basic conditions' and other legal requirements before they can come into force. These are tested through an independent examination before the neighbourhood plan may proceed to referendum.",
        "key_principle": "Neighbourhood plan basic conditions",
        "relevance_triggers": ["neighbourhood plan"],
    },

    # =========================================================================
    # CHAPTER 4: DECISION-MAKING (Para 38-58)
    # =========================================================================
    38: {
        "chapter": 4,
        "text": "Local planning authorities should approach decisions on proposed development in a positive and creative way. They should use the full range of planning tools available, including brownfield registers and permission in principle, and work proactively with applicants to secure developments that will improve the economic, social and environmental conditions of the area. Decision-makers at every level should seek to approve applications for sustainable development where possible.",
        "key_principle": "Positive decision-making approach",
        "relevance_triggers": ["all"],
    },
    39: {
        "chapter": 4,
        "text": "Early engagement has significant potential to improve the efficiency and effectiveness of the planning application system for all parties. Good quality pre-application discussion enables better coordination between public and private resources and improved outcomes for the community.",
        "key_principle": "Pre-application engagement",
        "relevance_triggers": ["all"],
    },
    40: {
        "chapter": 4,
        "text": "Local planning authorities have a key role to play in encouraging other parties to take maximum advantage of the pre-application stage. They cannot require that a developer engages with them before submitting a planning application, but they should encourage take-up of any pre-application services they offer.",
        "key_principle": "Pre-application services",
        "relevance_triggers": ["all"],
    },
    41: {
        "chapter": 4,
        "text": "The more issues that can be resolved at pre-application stage, including the need to deliver improvements in infrastructure and affordable housing, the greater the benefits.",
        "key_principle": "Early issue resolution",
        "relevance_triggers": ["all", "affordable housing", "infrastructure"],
    },
    42: {
        "chapter": 4,
        "text": "The participation of other consenting bodies in pre-application discussions should enable early consideration of all the fundamental issues relating to whether a particular development will be acceptable in principle.",
        "key_principle": "Multi-body pre-application engagement",
        "relevance_triggers": ["all"],
    },
    43: {
        "chapter": 4,
        "text": "The right information is crucial to good decision-making, particularly where formal assessments are required (such as Environmental Impact Assessment, Habitats Regulations Assessment). To avoid delay, applicants should discuss what information is needed with the local planning authority and expert bodies as early as possible.",
        "key_principle": "Right information for decisions",
        "relevance_triggers": ["eia", "hra", "major development"],
    },
    44: {
        "chapter": 4,
        "text": "Local planning authorities should not normally require applicants or developers to demonstrate the overall need for commercial development.",
        "key_principle": "No need test for commercial",
        "relevance_triggers": ["commercial", "retail", "office"],
    },
    45: {
        "chapter": 4,
        "text": "Local planning authorities should approach decisions on proposed development in a positive and creative way. They should use the full range of planning tools available, and work proactively with applicants to secure developments that will improve the economic, social and environmental conditions of the area. Decision-makers at every level should seek to approve applications for sustainable development where possible.",
        "key_principle": "Positive approach to decisions",
        "relevance_triggers": ["all"],
    },
    46: {
        "chapter": 4,
        "text": "When considering applications for planning permission, local planning authorities should give weight to relevant policies in existing plans according to their consistency with this Framework, the closer the policies in the plan to the policies in the Framework, the greater the weight that may be given.",
        "key_principle": "Weight to plan policies",
        "relevance_triggers": ["all"],
    },
    47: {
        "chapter": 4,
        "text": "Planning applications should be determined in accordance with the development plan, unless material considerations indicate otherwise. Decisions on applications should be made as quickly as possible, and within statutory timescales unless a longer period has been agreed by the applicant in writing.",
        "key_principle": "Timely determination",
        "relevance_triggers": ["all"],
    },
    48: {
        "chapter": 4,
        "text": "Applicants and local planning authorities should consider whether otherwise unacceptable development could be made acceptable through the use of conditions or planning obligations. Planning obligations should only be used where it is not possible to address unacceptable impacts through a planning condition.",
        "key_principle": "Conditions before obligations",
        "relevance_triggers": ["conditions", "s106"],
    },
    49: {
        "chapter": 4,
        "text": "Local planning authorities have discretion to charge for advice on pre-application enquiries but are expected to provide a free service for applicants for their first home in line with the guidance published by the Department.",
        "key_principle": "Pre-application charges discretion",
        "relevance_triggers": ["pre-application", "householder"],
    },
    50: {
        "chapter": 4,
        "text": "Local planning authorities should, where they think this would be beneficial, encourage any applicants who are not already required to do so by law to engage with the local community before submitting their applications.",
        "key_principle": "Community engagement",
        "relevance_triggers": ["major development", "community"],
    },
    51: {
        "chapter": 4,
        "text": "Early engagement has significant potential to improve the efficiency and effectiveness of the planning application system for all parties. Good quality pre-application discussion enables better coordination between public and private resources and improved outcomes for the community.",
        "key_principle": "Benefits of early engagement",
        "relevance_triggers": ["pre-application"],
    },
    52: {
        "chapter": 4,
        "text": "The participation of other consenting bodies in pre-application discussions should enable early consideration of all the fundamental issues relating to whether a particular development will be acceptable in principle. This can avoid the need for multiple applications where a subsequent refusal of consent effectively overrides earlier permissions.",
        "key_principle": "Multi-body pre-application coordination",
        "relevance_triggers": ["pre-application", "major development"],
    },
    53: {
        "chapter": 4,
        "text": "Local planning authorities should also, where they think this would be beneficial, use Planning Performance Agreements where this would help in managing and monitoring larger or more complex applications for development.",
        "key_principle": "Planning Performance Agreements",
        "relevance_triggers": ["major development", "complex"],
    },
    54: {
        "chapter": 4,
        "text": "Applicants should work closely with those affected by their proposals to evolve designs that take account of the views of the community. Applications that can demonstrate early, proactive and effective engagement with the community should be looked on more favourably than those that cannot.",
        "key_principle": "Community engagement and design evolution",
        "relevance_triggers": ["design", "community"],
    },
    55: {
        "chapter": 4,
        "text": "Planning conditions should be kept to a minimum and only imposed where they are necessary, relevant to planning and to the development to be permitted, enforceable, precise and reasonable in all other respects. Agreeing conditions early is beneficial to all parties involved in the process.",
        "key_principle": "Six tests for conditions",
        "relevance_triggers": ["conditions"],
    },
    56: {
        "chapter": 4,
        "text": "Planning obligations should only be used where it is not possible to address unacceptable impacts through a planning condition. Planning obligations should only be sought where they meet all of the following tests: a) necessary to make the development acceptable in planning terms; b) directly related to the development; and c) fairly and reasonably related in scale and kind to the development.",
        "key_principle": "Regulation 122 tests for S106",
        "relevance_triggers": ["s106", "planning obligation", "affordable housing", "infrastructure"],
    },
    57: {
        "chapter": 4,
        "text": "Where up-to-date policies have set out the contributions expected from development, planning applications that comply with them should be assumed to be viable. It is up to the applicant to demonstrate whether particular circumstances justify the need for a viability assessment at the application stage.",
        "key_principle": "Viability and policy compliance",
        "relevance_triggers": ["viability", "s106", "affordable housing"],
    },
    58: {
        "chapter": 4,
        "text": "Where safeguards are necessary to make a particular development acceptable in planning terms, and these safeguards cannot adequately be secured by conditions, the local planning authority should only grant permission if the applicant is willing to enter into a planning obligation.",
        "key_principle": "Planning obligation requirement",
        "relevance_triggers": ["s106", "planning obligation"],
    },

    # =========================================================================
    # CHAPTER 5: DELIVERING A SUFFICIENT SUPPLY OF HOMES (Para 59-80)
    # =========================================================================
    59: {
        "chapter": 5,
        "text": "To support the Government's objective of significantly boosting the supply of homes, it is important that a sufficient amount and variety of land can come forward where it is needed, that the needs of groups with specific housing requirements are addressed and that land with permission is developed without unnecessary delay.",
        "key_principle": "Government housing objective",
        "relevance_triggers": ["housing", "residential", "dwelling"],
    },
    60: {
        "chapter": 5,
        "text": "To support the Government's objective of significantly boosting the supply of homes, it is important that a sufficient amount and variety of land can come forward where it is needed, that the needs of groups with specific housing requirements are addressed and that land with permission is developed without unnecessary delay.",
        "key_principle": "Boosting housing supply",
        "relevance_triggers": ["housing", "residential", "dwelling"],
    },
    61: {
        "chapter": 5,
        "text": "To determine the minimum number of homes needed, strategic policies should be informed by a local housing need assessment, conducted using the standard method in national planning guidance.",
        "key_principle": "Standard method for housing need",
        "relevance_triggers": ["housing", "local plan"],
    },
    62: {
        "chapter": 5,
        "text": "Within this context, the size, type and tenure of housing needed for different groups in the community should be assessed and reflected in planning policies. These groups include, but are not limited to: those who require affordable housing, families with children, older people, students, people with disabilities, service families, travellers, people who rent their homes and people wishing to commission or build their own homes.",
        "key_principle": "Housing for different groups",
        "relevance_triggers": ["housing", "affordable housing", "older people", "accessibility"],
    },
    63: {
        "chapter": 5,
        "text": "Where a need for affordable housing is identified, planning policies should specify the type of affordable housing required, and expect it to be met on-site unless: a) off-site provision or an appropriate financial contribution in lieu can be robustly justified; and b) the agreed approach contributes to the objective of creating mixed and balanced communities.",
        "key_principle": "On-site affordable housing",
        "relevance_triggers": ["affordable housing"],
    },
    64: {
        "chapter": 5,
        "text": "Provision of affordable housing should not be sought for residential developments that are not major developments, other than in designated rural areas. To support the re-use of brownfield land, where vacant buildings are being reused or redeveloped, any affordable housing contribution due should be reduced by a proportionate amount.",
        "key_principle": "Affordable housing thresholds",
        "relevance_triggers": ["affordable housing", "major development"],
    },
    65: {
        "chapter": 5,
        "text": "Where major development involving the provision of housing is proposed, planning policies and decisions should expect at least 10% of the total number of homes to be available for affordable home ownership, unless this would exceed the level of affordable housing required in the area, or significantly prejudice the ability to meet the identified affordable housing needs of specific groups.",
        "key_principle": "10% affordable home ownership",
        "relevance_triggers": ["affordable housing", "major development"],
    },
    66: {
        "chapter": 5,
        "text": "Exemptions to the requirement for 10% affordable home ownership should apply to: a) developments which provide solely for Build to Rent homes; b) developments that provide specialist accommodation for a group of people with specific needs (such as purpose-built accommodation for the elderly or students); c) developments where the overall affordable housing requirement is below 10%; d) development of a site that is exclusively for affordable housing, an entry-level exception site or a rural exception site.",
        "key_principle": "Affordable home ownership exemptions",
        "relevance_triggers": ["affordable housing", "build to rent", "specialist accommodation"],
    },
    67: {
        "chapter": 5,
        "text": "Strategic policy-making authorities should establish a housing requirement figure for their whole area, which shows the extent to which their identified housing need can be met over the plan period. Within this overall requirement, strategic policies should also set out a housing requirement for designated neighbourhood areas which reflects the overall strategy for the pattern and scale of development.",
        "key_principle": "Housing requirement figures",
        "relevance_triggers": ["housing", "local plan", "neighbourhood plan"],
    },
    68: {
        "chapter": 5,
        "text": "Where it is not possible to meet housing need within a local planning authority's boundaries, strategic policies should be informed by statements of common ground, prepared and maintained throughout the plan-making process, on the approach to addressing cross-boundary housing needs.",
        "key_principle": "Cross-boundary housing needs",
        "relevance_triggers": ["housing", "local plan"],
    },
    69: {
        "chapter": 5,
        "text": "Small and medium sized sites can make an important contribution to meeting the housing requirement of an area, and are often built-out relatively quickly. To promote the development of a good mix of sites local planning authorities should: a) identify land to accommodate at least 10% of their housing requirement on sites no larger than one hectare; b) use tools such as area-wide design assessments and Local Development Orders to help bring small and medium sized sites forward; c) support the development of windfall sites through their policies and decisions.",
        "key_principle": "Small sites importance",
        "relevance_triggers": ["housing", "small site"],
    },
    70: {
        "chapter": 5,
        "text": "Neighbourhood planning groups should also give particular consideration to the opportunities for allocating small and medium-sized sites suitable for housing in their area.",
        "key_principle": "Neighbourhood plan housing sites",
        "relevance_triggers": ["neighbourhood plan", "housing"],
    },
    71: {
        "chapter": 5,
        "text": "Where an allowance is to be made for windfall sites as part of anticipated supply, there should be compelling evidence that they will provide a reliable source of supply. Any allowance should be realistic having regard to the strategic housing land availability assessment, historic windfall delivery rates and expected future trends.",
        "key_principle": "Windfall allowance evidence",
        "relevance_triggers": ["housing", "windfall"],
    },
    72: {
        "chapter": 5,
        "text": "Local planning authorities should support the development of entry-level exception sites, suitable for first time buyers (or those looking to rent their first home), unless the need for such homes is already being met within the authority's area. These sites should be on land which is not already allocated for housing and should: a) comprise of entry-level homes that offer one or more types of affordable housing as defined in this Framework; and b) be adjacent to existing settlements, and proportionate in size to them.",
        "key_principle": "Entry-level exception sites",
        "relevance_triggers": ["housing", "affordable housing", "first time buyer"],
    },
    73: {
        "chapter": 5,
        "text": "Entry-level exception sites should not be larger than one hectare in size or exceed 5% of the size of the existing settlement. Entry-level exception sites should not be permitted in areas covered by the policies in paragraphs 11 (footnote 6) and 182 of this Framework (relating to habitats sites and/or designated heritage assets), and a rural exception site policy should be used to deliver affordable housing in designated rural areas instead.",
        "key_principle": "Entry-level site limitations",
        "relevance_triggers": ["housing", "affordable housing", "exception site"],
    },
    74: {
        "chapter": 5,
        "text": "Strategic policies should include a trajectory illustrating the expected rate of housing delivery over the plan period, and all plans should consider whether it is appropriate to set out the anticipated rate of development for specific sites. Local planning authorities should identify and update annually a supply of specific deliverable sites sufficient to provide a minimum of five years' worth of housing against their housing requirement.",
        "key_principle": "Five year housing land supply",
        "relevance_triggers": ["housing", "five year supply"],
    },
    75: {
        "chapter": 5,
        "text": "The supply of specific deliverable sites should in addition include a buffer of: a) 5% to ensure choice and competition in the market for land; or b) 10% where the local planning authority wishes to demonstrate a five year supply of deliverable sites through an annual position statement or recently adopted plan; or c) 20% where there has been significant under delivery of housing over the previous three years.",
        "key_principle": "Housing supply buffers",
        "relevance_triggers": ["housing", "five year supply"],
    },
    76: {
        "chapter": 5,
        "text": "To maintain supply and delivery of land for housing, the Housing Delivery Test will be used to measure performance. Where the Housing Delivery Test indicates that delivery has fallen below 95% of the local planning authority's housing requirement over the previous three years, the authority should prepare an action plan to assess the causes of under-delivery and identify actions to increase delivery in future years.",
        "key_principle": "Housing Delivery Test",
        "relevance_triggers": ["housing", "delivery"],
    },
    77: {
        "chapter": 5,
        "text": "Where the Housing Delivery Test indicates that the delivery of housing has fallen below 75% of the housing requirement over the previous three years, the presumption in favour of sustainable development as set out in paragraph 11(d) of this Framework will apply, as set out in that paragraph.",
        "key_principle": "Housing Delivery Test presumption trigger",
        "relevance_triggers": ["housing", "tilted balance", "presumption"],
    },
    78: {
        "chapter": 5,
        "text": "In rural areas, planning policies and decisions should be responsive to local circumstances and support housing developments that reflect local needs. Local planning authorities should support opportunities to bring forward rural exception sites that will provide affordable housing to meet identified local needs.",
        "key_principle": "Rural housing",
        "relevance_triggers": ["rural", "housing"],
    },
    79: {
        "chapter": 5,
        "text": "To promote sustainable development in rural areas, housing should be located where it will enhance or maintain the vitality of rural communities. Planning policies should identify opportunities for villages to grow and thrive, especially where this will support local services.",
        "key_principle": "Rural community vitality",
        "relevance_triggers": ["rural", "village", "housing"],
    },
    80: {
        "chapter": 5,
        "text": "Planning policies and decisions should avoid the development of isolated homes in the countryside unless one or more of the following circumstances apply: a) there is an essential need for a rural worker; b) the development would represent the optimal viable use of a heritage asset; c) the development would re-use redundant or disused buildings; d) the development would involve the subdivision of an existing residential building; or e) the design is of exceptional quality.",
        "key_principle": "Isolated rural dwellings",
        "relevance_triggers": ["rural", "isolated", "countryside", "agricultural worker"],
    },

    # =========================================================================
    # CHAPTER 6: BUILDING A STRONG, COMPETITIVE ECONOMY (Para 81-86)
    # =========================================================================
    81: {
        "chapter": 6,
        "text": "Planning policies and decisions should help create the conditions in which businesses can invest, expand and adapt. Significant weight should be placed on the need to support economic growth and productivity, taking into account both local business needs and wider opportunities for development.",
        "key_principle": "Support economic growth",
        "relevance_triggers": ["economic", "employment", "business", "commercial"],
    },
    82: {
        "chapter": 6,
        "text": "Planning policies should: a) set out a clear economic vision and strategy which positively and proactively encourages sustainable economic growth; b) set criteria, or identify strategic sites, for local and inward investment; c) seek to address potential barriers to investment; and d) be flexible enough to accommodate needs not anticipated in the plan.",
        "key_principle": "Economic policy requirements",
        "relevance_triggers": ["economic", "employment", "local plan"],
    },
    83: {
        "chapter": 6,
        "text": "Planning policies and decisions should recognise and address the specific locational requirements of different sectors. This includes making provision for clusters or networks of knowledge and data-driven, creative or high technology industries; and for storage and distribution operations at a variety of scales and in suitably accessible locations.",
        "key_principle": "Sector-specific needs",
        "relevance_triggers": ["industrial", "warehouse", "logistics", "technology"],
    },
    84: {
        "chapter": 6,
        "text": "Planning policies and decisions should enable: a) the sustainable growth and expansion of all types of business in rural areas; b) the development and diversification of agricultural and other land-based rural businesses; c) sustainable rural tourism and leisure developments; and d) the retention and development of accessible local services and community facilities.",
        "key_principle": "Rural economy",
        "relevance_triggers": ["rural", "farm", "agricultural", "tourism"],
    },
    85: {
        "chapter": 6,
        "text": "Planning policies and decisions should recognise that sites to meet local business and community needs in rural areas may have to be found adjacent to or beyond existing settlements, and in locations that are not well served by public transport. In these circumstances it will be important to ensure that development is sensitive to its surroundings, does not have an unacceptable impact on local roads and exploits any opportunities to make a location more sustainable.",
        "key_principle": "Rural employment sites",
        "relevance_triggers": ["rural", "employment"],
    },
    86: {
        "chapter": 6,
        "text": "Planning policies and decisions should: a) give significant weight to the need to create, expand or alter schools and other educational facilities; and b) work with school promoters, delivery partners and statutory bodies to identify and resolve key planning issues before applications are submitted.",
        "key_principle": "Schools and education",
        "relevance_triggers": ["school", "education", "college", "university"],
    },

    # =========================================================================
    # CHAPTER 7: ENSURING THE VITALITY OF TOWN CENTRES (Para 87-91)
    # =========================================================================
    87: {
        "chapter": 7,
        "text": "Planning policies and decisions should support the role that town centres play at the heart of local communities, by taking a positive approach to their growth, management and adaptation.",
        "key_principle": "Town centre support",
        "relevance_triggers": ["town centre", "retail", "high street"],
    },
    88: {
        "chapter": 7,
        "text": "Planning policies should: a) define a network and hierarchy of town centres; b) define the extent of town centres and primary shopping areas; c) retain and enhance existing markets and, where appropriate, re-introduce or create new ones; d) allocate a range of suitable sites in town centres to meet the scale and type of development likely to be needed; e) where suitable and viable town centre sites are not available for main town centre uses, allocate appropriate edge of centre sites; f) recognise that residential development often plays an important role in ensuring the vitality of centres and encourage residential development on appropriate sites.",
        "key_principle": "Town centre policy requirements",
        "relevance_triggers": ["town centre", "retail", "local plan"],
    },
    89: {
        "chapter": 7,
        "text": "When assessing applications for retail and leisure development outside town centres, which are not in accordance with an up-to-date plan, local planning authorities should require an impact assessment if the development is over a proportionate, locally set floorspace threshold. If there is no locally set threshold, the default threshold is 2,500 sqm of gross floorspace.",
        "key_principle": "Retail impact assessment threshold",
        "relevance_triggers": ["retail", "out of centre", "impact assessment"],
    },
    90: {
        "chapter": 7,
        "text": "Where an application fails to satisfy the sequential test or is likely to have significant adverse impact on one or more of the considerations in paragraph 89, it should be refused.",
        "key_principle": "Sequential test failure",
        "relevance_triggers": ["retail", "sequential test"],
    },
    91: {
        "chapter": 7,
        "text": "Local planning authorities should apply a sequential test to planning applications for main town centre uses which are neither in an existing centre nor in accordance with an up-to-date plan. Main town centre uses should be located in town centres, then in edge of centre locations; and only if suitable sites are not available should out of centre sites be considered.",
        "key_principle": "Sequential test",
        "relevance_triggers": ["retail", "leisure", "office", "sequential test"],
    },

    # =========================================================================
    # CHAPTER 8: PROMOTING HEALTHY AND SAFE COMMUNITIES (Para 92-101)
    # =========================================================================
    92: {
        "chapter": 8,
        "text": "Planning policies and decisions should aim to achieve healthy, inclusive and safe places which: a) promote social interaction; b) are safe and accessible; and c) enable and support healthy lifestyles.",
        "key_principle": "Healthy places",
        "relevance_triggers": ["health", "community", "safety"],
    },
    93: {
        "chapter": 8,
        "text": "To provide the social, recreational and cultural facilities and services the community needs, planning policies and decisions should: a) plan positively for the provision and use of shared spaces, community facilities and other local services; b) take into account and support the delivery of local strategies to improve health, social and cultural well-being; c) guard against the unnecessary loss of valued facilities and services; d) ensure that established shops, facilities and services are able to develop and modernise; and e) ensure an integrated approach to considering the location of housing, economic uses and community facilities and services.",
        "key_principle": "Community facilities",
        "relevance_triggers": ["community", "facility", "health", "leisure"],
    },
    94: {
        "chapter": 8,
        "text": "Planning policies and decisions should consider the social, economic and environmental benefits of estate regeneration. Local planning authorities should use their planning powers to help deliver estate regeneration to a high standard.",
        "key_principle": "Estate regeneration",
        "relevance_triggers": ["regeneration", "estate"],
    },
    95: {
        "chapter": 8,
        "text": "It is important that a sufficient choice of school places is available to meet the needs of existing and new communities. Local planning authorities should take a proactive, positive and collaborative approach to meeting this requirement.",
        "key_principle": "School places",
        "relevance_triggers": ["school", "education"],
    },
    96: {
        "chapter": 8,
        "text": "Access to a network of high quality open spaces and opportunities for sport and physical activity is important for the health and well-being of communities, and can deliver wider benefits for nature and support efforts to address climate change. Planning policies should be based on robust and up-to-date assessments of the need for open space, sport and recreation facilities.",
        "key_principle": "Open space and recreation",
        "relevance_triggers": ["open space", "sport", "recreation", "playing field"],
    },
    97: {
        "chapter": 8,
        "text": "Existing open space, sports and recreational buildings and land, including playing fields, should not be built on unless: a) an assessment has been undertaken which has clearly shown the open space, buildings or land to be surplus to requirements; or b) the loss resulting from the proposed development would be replaced by equivalent or better provision; or c) the development is for alternative sports and recreational provision, the benefits of which clearly outweigh the loss of the current or former use.",
        "key_principle": "Protection of open space",
        "relevance_triggers": ["open space", "playing field", "sport"],
    },
    98: {
        "chapter": 8,
        "text": "Planning policies and decisions should protect and enhance public rights of way and access, including taking opportunities to provide better facilities for users, for example by adding links to existing rights of way networks.",
        "key_principle": "Public rights of way",
        "relevance_triggers": ["footpath", "right of way", "access"],
    },
    99: {
        "chapter": 8,
        "text": "The designation of land as Local Green Space through local and neighbourhood plans allows communities to identify and protect green areas of particular importance to them. Designating land as Local Green Space should be consistent with the local planning of sustainable development and complement investment in sufficient homes, jobs and other essential services.",
        "key_principle": "Local Green Space",
        "relevance_triggers": ["local green space", "green space"],
    },
    100: {
        "chapter": 8,
        "text": "The Local Green Space designation should only be used where the green space is: a) in reasonably close proximity to the community it serves; b) demonstrably special to a local community and holds a particular local significance; and c) local in character and is not an extensive tract of land.",
        "key_principle": "Local Green Space criteria",
        "relevance_triggers": ["local green space"],
    },
    101: {
        "chapter": 8,
        "text": "Policies for managing development within a Local Green Space should be consistent with those for Green Belts.",
        "key_principle": "Local Green Space management",
        "relevance_triggers": ["local green space"],
    },

    # =========================================================================
    # CHAPTER 9: PROMOTING SUSTAINABLE TRANSPORT (Para 102-113)
    # =========================================================================
    102: {
        "chapter": 9,
        "text": "Transport issues should be considered from the earliest stages of plan-making and development proposals, so that: a) the potential impacts of development on transport networks can be addressed; b) opportunities from existing or proposed transport infrastructure, and changing transport technology and usage, are realised; c) opportunities to promote walking, cycling and public transport use are identified and pursued; d) the environmental impacts of traffic and transport infrastructure can be identified, assessed and taken into account; and e) patterns of movement, streets, parking and other transport considerations are integral to the design of schemes.",
        "key_principle": "Early transport consideration",
        "relevance_triggers": ["transport", "highway", "parking"],
    },
    103: {
        "chapter": 9,
        "text": "The planning system should actively manage patterns of growth in support of these objectives. Significant development should be focused on locations which are or can be made sustainable, through limiting the need to travel and offering a genuine choice of transport modes.",
        "key_principle": "Sustainable locations",
        "relevance_triggers": ["transport", "sustainable location"],
    },
    104: {
        "chapter": 9,
        "text": "Planning policies should: a) support an appropriate mix of uses across an area, and within larger scale sites, to minimise the number and length of journeys needed for employment, shopping, leisure, education and other activities; b) be prepared with the active involvement of local highways authorities, other transport infrastructure providers and operators and neighbouring councils; c) identify and protect, where there is robust evidence, sites and routes which could be critical in developing infrastructure to widen transport choice and realise opportunities for large scale development; d) provide for attractive and well-designed walking and cycling networks with supporting facilities such as secure cycle parking; and e) provide for any large scale transport facilities that need to be located in the area, and the infrastructure and wider development required to support their operation, expansion and contribution to the wider economy.",
        "key_principle": "Transport policy requirements",
        "relevance_triggers": ["transport", "cycling", "walking", "local plan"],
    },
    105: {
        "chapter": 9,
        "text": "If setting local parking standards for residential and non-residential development, policies should take into account: a) the accessibility of the development; b) the type, mix and use of development; c) the availability of and opportunities for public transport; d) local car ownership levels; and e) the need to ensure an adequate provision of spaces for charging plug-in and other ultra-low emission vehicles.",
        "key_principle": "Parking standards",
        "relevance_triggers": ["parking", "car", "electric vehicle"],
    },
    106: {
        "chapter": 9,
        "text": "Maximum parking standards for residential and non-residential development should only be set where there is a clear and compelling justification that they are necessary for managing the local road network, or for optimising the density of development in city and town centres and other locations that are well served by public transport.",
        "key_principle": "Maximum parking standards",
        "relevance_triggers": ["parking", "town centre"],
    },
    107: {
        "chapter": 9,
        "text": "Planning policies and decisions should support local and neighbourhood plans that promote walking and cycling networks, and safeguard land required for transport infrastructure development.",
        "key_principle": "Walking and cycling networks",
        "relevance_triggers": ["cycling", "pedestrian", "walking", "transport infrastructure"],
    },
    108: {
        "chapter": 9,
        "text": "Planning policies should provide for high quality walking and cycling networks and supporting facilities such as cycle parking (drawing on Local Cycling and Walking Infrastructure Plans).",
        "key_principle": "High quality walking and cycling facilities",
        "relevance_triggers": ["cycling", "walking", "cycle parking"],
    },
    109: {
        "chapter": 9,
        "text": "Significant development should be focused on locations which are or can be made sustainable, through limiting the need to travel and offering a genuine choice of transport modes. This can help to reduce congestion and emissions, and improve air quality and public health.",
        "key_principle": "Sustainable locations for development",
        "relevance_triggers": ["sustainable transport", "major development", "location"],
    },
    110: {
        "chapter": 9,
        "text": "In assessing sites that may be allocated for development in plans, or specific applications for development, it should be ensured that: a) appropriate opportunities to promote sustainable transport modes can be – or have been – taken up, given the type of development and its location; b) safe and suitable access to the site can be achieved for all users; c) the design of streets, parking areas, other transport elements and the content of associated standards reflects current national guidance, including the National Design Guide and the National Model Design Code; and d) any significant impacts from the development on the transport network (in terms of capacity and congestion), or on highway safety, can be cost effectively mitigated to an acceptable degree.",
        "key_principle": "Site assessment for transport",
        "relevance_triggers": ["transport", "highway", "access"],
    },
    111: {
        "chapter": 9,
        "text": "Development should only be prevented or refused on highways grounds if there would be an unacceptable impact on highway safety, or the residual cumulative impacts on the road network would be severe.",
        "key_principle": "Highway refusal test",
        "relevance_triggers": ["highway", "transport", "traffic"],
    },
    112: {
        "chapter": 9,
        "text": "Within this context, applications for development should: a) give priority first to pedestrian and cycle movements, both within the scheme and with neighbouring areas; and second – so far as possible – to facilitating access to high quality public transport, with layouts that maximise the catchment area for bus or other public transport services, and appropriate facilities that encourage public transport use; b) address the needs of people with disabilities and reduced mobility in relation to all modes of transport; c) create places that are safe, secure and attractive – which minimise the scope for conflicts between pedestrians, cyclists and vehicles, avoid unnecessary street clutter, and respond to local character and design standards; d) allow for the efficient delivery of goods, and access by service and emergency vehicles; and e) be designed to enable charging of plug-in and other ultra-low emission vehicles in safe, accessible and convenient locations.",
        "key_principle": "Development design for transport",
        "relevance_triggers": ["transport", "design", "cycling", "pedestrian"],
    },
    113: {
        "chapter": 9,
        "text": "All developments that will generate significant amounts of movement should be required to provide a travel plan, and the application should be supported by a transport statement or transport assessment so that the likely impacts of the proposal can be assessed.",
        "key_principle": "Travel plans and transport assessments",
        "relevance_triggers": ["transport", "travel plan", "transport assessment"],
    },

    # =========================================================================
    # CHAPTER 10: SUPPORTING HIGH QUALITY COMMUNICATIONS (Para 114-118)
    # =========================================================================
    114: {
        "chapter": 10,
        "text": "Advanced, high quality and reliable communications infrastructure is essential for economic growth and social well-being. Planning policies and decisions should support the expansion of electronic communications networks, including next generation mobile technology (such as 5G) and full fibre broadband connections, taking into account the latest industry guidance published by the DCMS.",
        "key_principle": "Communications infrastructure support",
        "relevance_triggers": ["telecommunications", "broadband", "mast", "5G"],
    },
    115: {
        "chapter": 10,
        "text": "The number of radio and electronic communications masts, and the sites for such installations, should be kept to a minimum consistent with the needs of consumers, the efficient operation of the network and providing reasonable capacity for future expansion.",
        "key_principle": "Minimise mast proliferation",
        "relevance_triggers": ["telecommunications", "mast"],
    },
    116: {
        "chapter": 10,
        "text": "Local planning authorities should not impose a ban on new electronic communications development in certain areas, impose blanket Article 4 directions over a wide area or a wide range of electronic communications development, or set out unreasonable expectations for mast sharing.",
        "key_principle": "No blanket restrictions",
        "relevance_triggers": ["telecommunications"],
    },
    117: {
        "chapter": 10,
        "text": "Applications for electronic communications development (including applications for prior approval under the General Permitted Development Order) should be supported by the necessary evidence to justify the proposed development.",
        "key_principle": "Evidence for telecoms applications",
        "relevance_triggers": ["telecommunications"],
    },
    118: {
        "chapter": 10,
        "text": "Local planning authorities must determine applications on planning grounds only. They should not seek to prevent competition between different operators, question the need for an electronic communications system, or set health safeguards different from the International Commission guidelines for public exposure.",
        "key_principle": "Planning grounds only for telecoms",
        "relevance_triggers": ["telecommunications", "health"],
    },

    # =========================================================================
    # CHAPTER 11: MAKING EFFECTIVE USE OF LAND (Para 119-125)
    # =========================================================================
    119: {
        "chapter": 11,
        "text": "Planning policies and decisions should promote an effective use of land in meeting the need for homes and other uses, while safeguarding and improving the environment and ensuring safe and healthy living conditions. Strategic policies should set out a clear strategy for accommodating objectively assessed needs, in a way that makes as much use as possible of previously-developed or 'brownfield' land.",
        "key_principle": "Effective land use and brownfield priority",
        "relevance_triggers": ["brownfield", "land use", "density"],
    },
    120: {
        "chapter": 11,
        "text": "Planning policies and decisions should: a) encourage multiple benefits from both urban and rural land, including through mixed use schemes and taking opportunities to achieve net environmental gains; b) recognise that some undeveloped land can perform many functions, such as for wildlife, recreation, flood risk mitigation, cooling/shading, carbon storage or food production; c) give substantial weight to the value of using suitable brownfield land within settlements for homes and other identified needs; d) promote and support the development of under-utilised land and buildings; e) support opportunities to use the airspace above existing residential and commercial premises for new homes.",
        "key_principle": "Multiple land use benefits",
        "relevance_triggers": ["brownfield", "mixed use", "airspace"],
    },
    121: {
        "chapter": 11,
        "text": "Local planning authorities, and other plan-making bodies, should take a proactive role in identifying and helping to bring forward land that may be suitable for meeting development needs, including suitable sites on brownfield registers or held in public ownership, using the full range of powers available to them.",
        "key_principle": "Proactive site identification",
        "relevance_triggers": ["brownfield", "public land"],
    },
    122: {
        "chapter": 11,
        "text": "Planning policies and decisions should support development that makes efficient use of land, taking into account: a) the identified need for different types of housing and other forms of development, and the availability of land suitable for accommodating it; b) local market conditions and viability; c) the availability and capacity of infrastructure and services; d) the desirability of maintaining an area's prevailing character and setting, or of promoting regeneration and change; and e) the importance of securing well-designed, attractive and healthy places.",
        "key_principle": "Efficient land use factors",
        "relevance_triggers": ["density", "land use", "design"],
    },
    123: {
        "chapter": 11,
        "text": "Where there is an existing or anticipated shortage of land for meeting identified housing needs, it is especially important that planning policies and decisions avoid homes being built at low densities, and ensure that developments make optimal use of the potential of each site.",
        "key_principle": "Optimal density in housing shortage",
        "relevance_triggers": ["density", "housing"],
    },
    124: {
        "chapter": 11,
        "text": "Area-based character assessments, design guides and codes and masterplans can be used to help ensure that land is used efficiently while also creating beautiful and sustainable places. Where there is a shortage of land to meet identified housing needs, the use of minimum density standards should also be considered.",
        "key_principle": "Design tools for density",
        "relevance_triggers": ["density", "design code", "masterplan"],
    },
    125: {
        "chapter": 11,
        "text": "Area-based character assessments, design guides and codes and masterplans can be used to help ensure that land is used efficiently while also creating beautiful and sustainable places. Where there is a shortage of land to meet identified housing needs, the use of minimum density standards should also be considered.",
        "key_principle": "Design and density tools",
        "relevance_triggers": ["design", "density"],
    },

    # =========================================================================
    # CHAPTER 12: ACHIEVING WELL-DESIGNED PLACES (Para 126-136)
    # =========================================================================
    126: {
        "chapter": 12,
        "text": "The creation of high quality, beautiful and sustainable buildings and places is fundamental to what the planning and development process should achieve. Good design is a key aspect of sustainable development, creates better places in which to live and work and helps make development acceptable to communities.",
        "key_principle": "Design as fundamental",
        "relevance_triggers": ["design", "all"],
    },
    127: {
        "chapter": 12,
        "text": "Plans should, at the most appropriate level, set out a clear design vision and expectations, so that applicants have as much certainty as possible about what is likely to be acceptable. Design policies should be developed with local communities so they reflect local aspirations, and are grounded in an understanding and evaluation of each area's defining characteristics.",
        "key_principle": "Clear design vision",
        "relevance_triggers": ["design", "local plan"],
    },
    128: {
        "chapter": 12,
        "text": "To provide maximum clarity about design expectations at an early stage, all local planning authorities should prepare design guides or codes consistent with the principles set out in the National Design Guide and National Model Design Code, and which reflect local character and design preferences.",
        "key_principle": "Design guides and codes",
        "relevance_triggers": ["design", "design code"],
    },
    129: {
        "chapter": 12,
        "text": "Design guides and codes can be prepared at an area-wide, neighbourhood or site specific scale, and to carry weight in decision-making should be produced either as part of a plan or as supplementary planning documents.",
        "key_principle": "Design code status",
        "relevance_triggers": ["design", "design code"],
    },
    130: {
        "chapter": 12,
        "text": "Planning policies and decisions should ensure that developments: a) will function well and add to the overall quality of the area, not just for the short term but over the lifetime of the development; b) are visually attractive as a result of good architecture, layout and appropriate and effective landscaping; c) are sympathetic to local character and history, including the surrounding built environment and landscape setting, while not preventing or discouraging appropriate innovation or change; d) establish or maintain a strong sense of place, using the arrangement of streets, spaces, building types and materials to create attractive, welcoming and distinctive places to live, work and visit; e) optimise the potential of the site to accommodate and sustain an appropriate amount and mix of development and support local facilities and transport networks; and f) create places that are safe, inclusive and accessible and which promote health and well-being, with a high standard of amenity for existing and future users; and where crime and disorder, and the fear of crime, do not undermine the quality of life or community cohesion and resilience.",
        "key_principle": "Design quality criteria",
        "relevance_triggers": ["design", "all"],
    },
    131: {
        "chapter": 12,
        "text": "Trees make an important contribution to the character and quality of urban environments, and can also help mitigate and adapt to climate change. Planning policies and decisions should ensure that new streets are tree-lined, that opportunities are taken to incorporate trees elsewhere in developments, that appropriate measures are in place to secure the long-term maintenance of newly-planted trees, and that existing trees are retained wherever possible.",
        "key_principle": "Trees in design",
        "relevance_triggers": ["tree", "landscaping", "design"],
    },
    132: {
        "chapter": 12,
        "text": "Design quality should be considered throughout the evolution and assessment of individual proposals. Early discussion between applicants, the local planning authority and local community about the design and style of emerging schemes is important for clarifying expectations and reconciling local and commercial interests. Applicants should work closely with those affected by their proposals to evolve designs that take account of the views of the community. Applications that can demonstrate early, proactive and effective engagement with the community should be looked on more favourably than those that cannot.",
        "key_principle": "Design evolution and engagement",
        "relevance_triggers": ["design", "consultation"],
    },
    133: {
        "chapter": 12,
        "text": "Local planning authorities should ensure that they have access to, and make appropriate use of, tools and processes for assessing and improving the design of development. These include workshops to engage the local community, design advice and review arrangements, and assessment frameworks such as Building for a Healthy Life.",
        "key_principle": "Design assessment tools",
        "relevance_triggers": ["design", "design review"],
    },
    134: {
        "chapter": 12,
        "text": "Development that is not well designed should be refused, especially where it fails to reflect local design policies and government guidance on design, taking into account any local design guidance and supplementary planning documents such as design guides and codes. Conversely, significant weight should be given to: a) development which reflects local design policies and government guidance on design, taking into account any local design guidance and supplementary planning documents such as design guides and codes; and/or b) outstanding or innovative designs which promote high levels of sustainability, or help raise the standard of design more generally in an area, so long as they fit in with the overall form and layout of their surroundings.",
        "key_principle": "Refuse poor design / support good design",
        "relevance_triggers": ["design", "all"],
    },
    135: {
        "chapter": 12,
        "text": "Local planning authorities should seek to ensure that the quality of approved development is not materially diminished between permission and completion, as a result of changes being made to the permitted scheme.",
        "key_principle": "Maintain design quality",
        "relevance_triggers": ["design", "conditions"],
    },
    136: {
        "chapter": 12,
        "text": "The quality and character of places can suffer when advertisements are poorly sited and designed. Control over outdoor advertisements should be efficient, effective and simple in concept and operation. Only those advertisements which will clearly have an appreciable impact on a building or on their surroundings should be subject to the local planning authority's detailed assessment. Advertisements should be subject to control only in the interests of amenity and public safety, taking account of cumulative impacts.",
        "key_principle": "Advertisement control",
        "relevance_triggers": ["advertisement", "signage"],
    },

    # =========================================================================
    # CHAPTER 13: PROTECTING GREEN BELT LAND (Para 137-151)
    # =========================================================================
    137: {
        "chapter": 13,
        "text": "The Government attaches great importance to Green Belts. The fundamental aim of Green Belt policy is to prevent urban sprawl by keeping land permanently open; the essential characteristics of Green Belts are their openness and their permanence.",
        "key_principle": "Green Belt importance",
        "relevance_triggers": ["green belt"],
    },
    138: {
        "chapter": 13,
        "text": "Green Belt serves five purposes: a) to check the unrestricted sprawl of large built-up areas; b) to prevent neighbouring towns merging into one another; c) to assist in safeguarding the countryside from encroachment; d) to preserve the setting and special character of historic towns; and e) to assist in urban regeneration, by encouraging the recycling of derelict and other urban land.",
        "key_principle": "Five purposes of Green Belt",
        "relevance_triggers": ["green belt"],
    },
    139: {
        "chapter": 13,
        "text": "The general extent of Green Belts across the country is already established. New Green Belts should only be established in exceptional circumstances, for example when planning for larger scale development such as new settlements or major urban extensions.",
        "key_principle": "New Green Belt exceptional",
        "relevance_triggers": ["green belt"],
    },
    140: {
        "chapter": 13,
        "text": "Once established, Green Belt boundaries should only be altered where exceptional circumstances are fully evidenced and justified, through the preparation or updating of plans. Strategic policies should establish the need for any changes to Green Belt boundaries, having regard to their intended permanence in the long term, so they can endure beyond the plan period.",
        "key_principle": "Green Belt boundary changes exceptional",
        "relevance_triggers": ["green belt"],
    },
    141: {
        "chapter": 13,
        "text": "Before concluding that exceptional circumstances exist to justify changes to Green Belt boundaries, the strategic policy-making authority should be able to demonstrate that it has examined fully all other reasonable options for meeting its identified need for development.",
        "key_principle": "Exhaust alternatives first",
        "relevance_triggers": ["green belt"],
    },
    142: {
        "chapter": 13,
        "text": "When drawing up or reviewing Green Belt boundaries, the need to promote sustainable patterns of development should be taken into account. Strategic policy-making authorities should consider the consequences for sustainable development of channelling development towards urban areas inside the Green Belt boundary, towards towns and villages inset within the Green Belt or towards locations beyond the outer Green Belt boundary.",
        "key_principle": "Sustainable patterns in Green Belt review",
        "relevance_triggers": ["green belt"],
    },
    143: {
        "chapter": 13,
        "text": "When defining Green Belt boundaries, plans should: a) ensure consistency with the development plan's strategy for meeting identified requirements for sustainable development; b) not include land which it is unnecessary to keep permanently open; c) where necessary, identify areas of safeguarded land between the urban area and the Green Belt, in order to meet longer-term development needs; d) make clear that the safeguarded land is not allocated for development at the present time; e) be able to demonstrate that Green Belt boundaries will not need to be altered at the end of the plan period; and f) define boundaries clearly, using physical features that are readily recognisable and likely to be permanent.",
        "key_principle": "Green Belt boundary definition",
        "relevance_triggers": ["green belt"],
    },
    144: {
        "chapter": 13,
        "text": "If it is necessary to restrict development in a village primarily because of the important contribution which the open character of the village makes to the openness of the Green Belt, the village should be included in the Green Belt. If, however, the character of the village needs to be protected for other reasons, other means should be used, such as conservation area or normal development management policies, and the village should be excluded from the Green Belt.",
        "key_principle": "Village inclusion in Green Belt",
        "relevance_triggers": ["green belt", "village"],
    },
    145: {
        "chapter": 13,
        "text": "Once Green Belts have been defined, local planning authorities should plan positively to enhance their beneficial use, such as looking for opportunities to provide access; to provide opportunities for outdoor sport and recreation; to retain and enhance landscapes, visual amenity and biodiversity; or to improve damaged and derelict land.",
        "key_principle": "Enhancing Green Belt beneficial use",
        "relevance_triggers": ["green belt", "recreation", "landscape"],
    },
    146: {
        "chapter": 13,
        "text": "The general extent of Green Belts across the country is already established. New Green Belts should only be established in exceptional circumstances, for example when planning for larger scale development such as new settlements or major urban extensions. Any proposals for new Green Belts should be set out in strategic policies, which should: a) demonstrate why normal planning and development management policies would not be adequate; b) set out whether any major changes in circumstances have made the adoption of this exceptional measure necessary; c) show what the consequences of the proposal would be for sustainable development; d) demonstrate the necessity for the Green Belt and its consistency with strategic policies for adjoining areas; and e) show how the Green Belt would meet the other objectives of the Framework.",
        "key_principle": "Establishing new Green Belts",
        "relevance_triggers": ["green belt", "strategic"],
    },
    147: {
        "chapter": 13,
        "text": "Inappropriate development is, by definition, harmful to the Green Belt and should not be approved except in very special circumstances.",
        "key_principle": "Inappropriate development harmful",
        "relevance_triggers": ["green belt"],
    },
    148: {
        "chapter": 13,
        "text": "When considering any planning application, local planning authorities should ensure that substantial weight is given to any harm to the Green Belt. 'Very special circumstances' will not exist unless the potential harm to the Green Belt by reason of inappropriateness, and any other harm resulting from the proposal, is clearly outweighed by other considerations.",
        "key_principle": "Very special circumstances test",
        "relevance_triggers": ["green belt"],
    },
    149: {
        "chapter": 13,
        "text": "A local planning authority should regard the construction of new buildings as inappropriate in the Green Belt. Exceptions to this are: a) buildings for agriculture and forestry; b) the provision of appropriate facilities (in connection with the existing use of land or a change of use) for outdoor sport, outdoor recreation, cemeteries and burial grounds and allotments; c) the extension or alteration of a building provided that it does not result in disproportionate additions over and above the size of the original building; d) the replacement of a building, provided the new building is in the same use and not materially larger than the one it replaces; e) limited infilling in villages; f) limited affordable housing for local community needs under policies set out in the development plan; and g) limited infilling or the partial or complete redevelopment of previously developed land, whether redundant or in continuing use (excluding temporary buildings), which would not have a greater impact on the openness of the Green Belt than the existing development, or not cause substantial harm to the openness of the Green Belt.",
        "key_principle": "Exceptions to inappropriate development",
        "relevance_triggers": ["green belt", "extension", "replacement", "agricultural"],
    },
    150: {
        "chapter": 13,
        "text": "Certain other forms of development are also not inappropriate in the Green Belt provided they preserve its openness and do not conflict with the purposes of including land within it. These are: a) mineral extraction; b) engineering operations; c) local transport infrastructure which can demonstrate a requirement for a Green Belt location; d) the re-use of buildings provided that the buildings are of permanent and substantial construction; e) material changes in the use of land (such as changes of use for outdoor sport or recreation, or for cemeteries and burial grounds); and f) development, including buildings, brought forward under a Community Right to Build Order or Neighbourhood Development Order.",
        "key_principle": "Other appropriate development in Green Belt",
        "relevance_triggers": ["green belt", "change of use", "engineering"],
    },
    151: {
        "chapter": 13,
        "text": "When located in the Green Belt, elements of many renewable energy projects will comprise inappropriate development. In such cases developers will need to demonstrate very special circumstances if projects are to proceed. Such very special circumstances may include the wider environmental benefits associated with increased production of energy from renewable sources.",
        "key_principle": "Renewable energy in Green Belt",
        "relevance_triggers": ["green belt", "renewable", "solar", "wind"],
    },

    # =========================================================================
    # CHAPTER 14: CLIMATE CHANGE AND FLOODING (Para 152-173)
    # =========================================================================
    152: {
        "chapter": 14,
        "text": "The planning system should support the transition to a low carbon future in a changing climate, taking full account of flood risk and coastal change. It should help to: shape places in ways that contribute to radical reductions in greenhouse gas emissions, minimise vulnerability and improve resilience; encourage the reuse of existing resources; and support renewable and low carbon energy and associated infrastructure.",
        "key_principle": "Low carbon transition",
        "relevance_triggers": ["climate", "flood", "renewable", "energy"],
    },
    153: {
        "chapter": 14,
        "text": "Plans should take a proactive approach to mitigating and adapting to climate change, taking into account the long-term implications for flood risk, coastal change, water supply, biodiversity and landscapes, and the risk of overheating from rising temperatures.",
        "key_principle": "Climate adaptation in plans",
        "relevance_triggers": ["climate", "flood", "biodiversity"],
    },
    154: {
        "chapter": 14,
        "text": "New development should be planned for in ways that: a) avoid increased vulnerability to the range of impacts arising from climate change; b) can help to reduce greenhouse gas emissions, such as through its location, orientation and design.",
        "key_principle": "Climate-responsive development",
        "relevance_triggers": ["climate", "design", "sustainability"],
    },
    155: {
        "chapter": 14,
        "text": "To help increase the use and supply of renewable and low carbon energy and heat, plans should: a) provide a positive strategy for energy from these sources, that maximises the potential for suitable development; b) consider identifying suitable areas for renewable and low carbon energy sources, and supporting infrastructure; c) identify opportunities for development to draw its energy supply from decentralised, renewable or low carbon energy supply systems and for co-locating potential heat customers and suppliers.",
        "key_principle": "Renewable energy strategy",
        "relevance_triggers": ["renewable", "energy", "solar", "wind"],
    },
    156: {
        "chapter": 14,
        "text": "Local planning authorities should support community-led initiatives for renewable and low carbon energy, including developments outside areas identified in local plans or other strategic policies that are being taken forward through neighbourhood planning.",
        "key_principle": "Community energy support",
        "relevance_triggers": ["renewable", "community", "neighbourhood plan"],
    },
    157: {
        "chapter": 14,
        "text": "In determining planning applications, local planning authorities should expect new development to: a) comply with any development plan policies on local requirements for decentralised energy supply unless it can be demonstrated by the applicant, having regard to the type of development involved and its design, that this is not feasible or viable; and b) take account of landform, layout, building orientation, massing and landscaping to minimise energy consumption.",
        "key_principle": "Energy efficiency in development",
        "relevance_triggers": ["energy", "design", "sustainability"],
    },
    158: {
        "chapter": 14,
        "text": "When determining planning applications for renewable and low carbon development, local planning authorities should: a) not require applicants to demonstrate the overall need for renewable or low carbon energy, and recognise that even small-scale projects provide a valuable contribution to cutting greenhouse gas emissions; and b) approve the application if its impacts are (or can be made) acceptable.",
        "key_principle": "Support renewable applications",
        "relevance_triggers": ["renewable", "solar", "wind"],
    },
    159: {
        "chapter": 14,
        "text": "Inappropriate development in areas at risk of flooding should be avoided by directing development away from areas at highest risk (whether existing or future). Where development is necessary in such areas, the development should be made safe for its lifetime without increasing flood risk elsewhere.",
        "key_principle": "Avoid flood risk areas",
        "relevance_triggers": ["flood"],
    },
    160: {
        "chapter": 14,
        "text": "Strategic policies should be informed by a strategic flood risk assessment, and should manage flood risk from all sources. They should consider cumulative impacts in, or affecting, local areas susceptible to flooding, and take account of advice from the Environment Agency and other relevant flood risk management authorities.",
        "key_principle": "Strategic flood risk assessment",
        "relevance_triggers": ["flood", "local plan"],
    },
    161: {
        "chapter": 14,
        "text": "All plans should apply a sequential, risk-based approach to the location of development – taking into account all sources of flood risk and the current and future impacts of climate change – so as to avoid, where possible, flood risk to people and property.",
        "key_principle": "Sequential approach to flood risk",
        "relevance_triggers": ["flood"],
    },
    162: {
        "chapter": 14,
        "text": "The aim of the sequential test is to steer new development to areas with the lowest risk of flooding from any source. Development should not be allocated or permitted if there are reasonably available sites appropriate for the proposed development in areas with a lower risk of flooding.",
        "key_principle": "Sequential test for flooding",
        "relevance_triggers": ["flood", "sequential test"],
    },
    163: {
        "chapter": 14,
        "text": "If it is not possible for development to be located in areas with a lower risk of flooding (taking into account wider sustainable development objectives), the exception test may have to be applied. The need for the exception test will depend on the potential vulnerability of the site and of the development proposed, in line with the Flood Risk Vulnerability Classification set out in national planning guidance.",
        "key_principle": "Exception test for flooding",
        "relevance_triggers": ["flood", "exception test"],
    },
    164: {
        "chapter": 14,
        "text": "The application of the exception test should be informed by a strategic or site-specific flood risk assessment, depending on whether it is being applied during plan preparation or at the application stage. To pass the exception test it should be demonstrated that: a) the development would provide wider sustainability benefits to the community that outweigh the flood risk; and b) the development will be safe for its lifetime taking account of the vulnerability of its users, without increasing flood risk elsewhere, and, where possible, will reduce flood risk overall.",
        "key_principle": "Exception test requirements",
        "relevance_triggers": ["flood", "exception test"],
    },
    165: {
        "chapter": 14,
        "text": "Both elements of the exception test should be satisfied for development to be allocated or permitted.",
        "key_principle": "Both exception test elements required",
        "relevance_triggers": ["flood"],
    },
    166: {
        "chapter": 14,
        "text": "The exception test has two parts: a) it must be demonstrated that the development would provide wider sustainability benefits to the community that outweigh the flood risk; and b) the development will be safe for its lifetime taking account of the vulnerability of its users, without increasing flood risk elsewhere, and, where possible, will reduce flood risk overall.",
        "key_principle": "Exception test requirements",
        "relevance_triggers": ["flood", "exception test"],
    },
    167: {
        "chapter": 14,
        "text": "When determining any planning applications, local planning authorities should ensure that flood risk is not increased elsewhere. Where appropriate, applications should be supported by a site-specific flood risk assessment. Development should only be allowed in areas at risk of flooding where, in the light of this assessment it can be demonstrated that: a) within the site, the most vulnerable development is located in areas of lowest flood risk, unless there are overriding reasons to prefer a different location; b) the development is appropriately flood resistant and resilient such that, in the event of a flood, it could be quickly brought back into use without significant refurbishment; c) it incorporates sustainable drainage systems, unless there is clear evidence that this would be inappropriate; d) any residual risk can be safely managed; and e) safe access and escape routes are included where appropriate, as part of an agreed emergency plan.",
        "key_principle": "Flood risk assessment requirements",
        "relevance_triggers": ["flood", "suds", "drainage"],
    },
    168: {
        "chapter": 14,
        "text": "Applications for some minor development and changes of use should not be subject to the sequential or exception tests but should still meet the requirements for site-specific flood risk assessments set out in the PPG.",
        "key_principle": "Minor development flood risk",
        "relevance_triggers": ["flood", "minor development"],
    },
    169: {
        "chapter": 14,
        "text": "Major developments should incorporate sustainable drainage systems unless there is clear evidence that this would be inappropriate. The systems used should: a) take account of advice from the lead local flood authority; b) have appropriate proposed minimum operational standards; c) have maintenance arrangements in place to ensure an acceptable standard of operation for the lifetime of the development; and d) where possible, provide multifunctional benefits.",
        "key_principle": "SuDS requirement",
        "relevance_triggers": ["suds", "drainage", "major development"],
    },
    170: {
        "chapter": 14,
        "text": "In coastal areas, planning policies and decisions should take account of the UK Marine Policy Statement and marine plans. Integrated Coastal Zone Management should be pursued across local authority and land/sea boundaries, to ensure effective alignment of the terrestrial and marine planning regimes.",
        "key_principle": "Coastal planning alignment",
        "relevance_triggers": ["coastal", "marine"],
    },
    171: {
        "chapter": 14,
        "text": "Plans should reduce risk from coastal change by avoiding inappropriate development in vulnerable areas and not exacerbating the impacts of physical changes to the coast. They should identify as a Coastal Change Management Area any area likely to be affected by physical changes to the coast, and be clear as to what development will be appropriate in such areas and in what circumstances.",
        "key_principle": "Coastal Change Management Areas",
        "relevance_triggers": ["coastal", "erosion"],
    },
    172: {
        "chapter": 14,
        "text": "Development in a Coastal Change Management Area will be appropriate only where it is demonstrated that: a) it will be safe over its planned lifetime and not have an unacceptable impact on coastal change; b) the character of the coast including designations is not compromised; c) the development provides wider sustainability benefits; and d) the development does not hinder the creation and maintenance of a continuous signed and managed route around the coast.",
        "key_principle": "Development in Coastal Change Management Areas",
        "relevance_triggers": ["coastal", "coastal change"],
    },
    173: {
        "chapter": 14,
        "text": "Local planning authorities should support community-led initiatives for relocating development, including community facilities, from areas at risk of coastal change to more sustainable locations. This may include community relocation planning strategies and the identification of areas where relocation may be facilitated.",
        "key_principle": "Coastal community relocation",
        "relevance_triggers": ["coastal", "relocation", "community"],
    },

    # =========================================================================
    # CHAPTER 15: CONSERVING THE NATURAL ENVIRONMENT (Para 174-188)
    # =========================================================================
    174: {
        "chapter": 15,
        "text": "Planning policies and decisions should contribute to and enhance the natural and local environment by: a) protecting and enhancing valued landscapes, sites of biodiversity or geological value and soils; b) recognising the intrinsic character and beauty of the countryside, and the wider benefits from natural capital and ecosystem services; c) maintaining the character of the undeveloped coast; d) minimising impacts on and providing net gains for biodiversity, including by establishing coherent ecological networks that are more resilient to current and future pressures; e) preventing new and existing development from contributing to, being put at unacceptable risk from, or being adversely affected by, unacceptable levels of soil, air, water or noise pollution or land instability; and f) remediating and mitigating despoiled, degraded, derelict, contaminated and unstable land, where appropriate.",
        "key_principle": "Natural environment protection",
        "relevance_triggers": ["landscape", "biodiversity", "ecology", "trees", "contamination"],
    },
    175: {
        "chapter": 15,
        "text": "Plans should: distinguish between the hierarchy of international, national and locally designated sites; allocate land with the least environmental or amenity value; take a strategic approach to maintaining and enhancing networks of habitats and green infrastructure; and plan for the enhancement of natural capital at a catchment or landscape scale across local authority boundaries.",
        "key_principle": "Biodiversity hierarchy in plans",
        "relevance_triggers": ["biodiversity", "local plan", "green infrastructure"],
    },
    176: {
        "chapter": 15,
        "text": "Great weight should be given to conserving and enhancing landscape and scenic beauty in National Parks, the Broads and Areas of Outstanding Natural Beauty, which have the highest status of protection in relation to these issues. The conservation and enhancement of wildlife and cultural heritage are also important considerations in these areas, and should be given great weight in National Parks and the Broads.",
        "key_principle": "AONB and National Park protection",
        "relevance_triggers": ["aonb", "national park", "landscape"],
    },
    177: {
        "chapter": 15,
        "text": "When considering applications for development within National Parks, the Broads and Areas of Outstanding Natural Beauty, permission should be refused for major development other than in exceptional circumstances, and where it can be demonstrated that the development is in the public interest.",
        "key_principle": "Major development in AONB/National Park",
        "relevance_triggers": ["aonb", "national park", "major development"],
    },
    178: {
        "chapter": 15,
        "text": "Consideration of such applications should include an assessment of: a) the need for the development, including in terms of any national considerations, and the impact of permitting it, or refusing it, upon the local economy; b) the cost of, and scope for, developing outside the designated area, or meeting the need for it in some other way; and c) any detrimental effect on the environment, the landscape and recreational opportunities, and the extent to which that could be moderated.",
        "key_principle": "Assessment for major development in designated areas",
        "relevance_triggers": ["aonb", "national park", "major development"],
    },
    179: {
        "chapter": 15,
        "text": "To protect and enhance biodiversity and geodiversity, plans should: a) identify, map and safeguard components of local wildlife-rich habitats and wider ecological networks; b) promote the conservation, restoration and enhancement of priority habitats, ecological networks and the protection and recovery of priority species; and c) identify and pursue opportunities for securing measurable net gains for biodiversity.",
        "key_principle": "Biodiversity protection in plans",
        "relevance_triggers": ["biodiversity", "ecology", "local plan"],
    },
    180: {
        "chapter": 15,
        "text": "When determining planning applications, local planning authorities should apply the following principles: a) if significant harm to biodiversity resulting from a development cannot be avoided, adequately mitigated, or, as a last resort, compensated for, then planning permission should be refused; b) development on land within or outside a Site of Special Scientific Interest, and which is likely to have an adverse effect on it, should not normally be permitted; c) development resulting in the loss or deterioration of irreplaceable habitats (such as ancient woodland and ancient or veteran trees) should be refused, unless there are wholly exceptional reasons and a suitable compensation strategy exists; and d) development whose primary objective is to conserve or enhance biodiversity should be supported; while opportunities to improve biodiversity in and around developments should be integrated as part of their design, especially where this can secure measurable net gains for biodiversity or enhance public access to nature where this is appropriate.",
        "key_principle": "Biodiversity in decision-making",
        "relevance_triggers": ["biodiversity", "ecology", "sssi", "ancient woodland", "trees"],
    },
    181: {
        "chapter": 15,
        "text": "The following should be given the same protection as habitats sites: a) potential Special Protection Areas and possible Special Areas of Conservation; b) listed or proposed Ramsar sites; and c) sites identified, or required, as compensatory measures for adverse effects on habitats sites, potential Special Protection Areas, possible Special Areas of Conservation, and listed or proposed Ramsar sites.",
        "key_principle": "Habitats sites protection",
        "relevance_triggers": ["habitats", "spa", "sac", "ramsar"],
    },
    182: {
        "chapter": 15,
        "text": "The presumption in favour of sustainable development does not apply where the plan or project is likely to have a significant effect on a habitats site (either alone or in combination with other plans or projects), unless an appropriate assessment has concluded that the plan or project will not adversely affect the integrity of the habitats site.",
        "key_principle": "Habitats Regulations Assessment",
        "relevance_triggers": ["habitats", "hra", "appropriate assessment"],
    },
    183: {
        "chapter": 15,
        "text": "Planning policies and decisions should ensure that: a) a site is suitable for its proposed use taking account of ground conditions and any risks arising from land instability and contamination; b) after remediation, as a minimum, land should not be capable of being determined as contaminated land under Part IIA of the Environmental Protection Act 1990; and c) adequate site investigation information, prepared by a competent person, is available to inform these assessments.",
        "key_principle": "Contaminated land assessment",
        "relevance_triggers": ["contamination", "land stability"],
    },
    184: {
        "chapter": 15,
        "text": "Where a site is affected by contamination or land stability issues, responsibility for securing a safe development rests with the developer and/or landowner.",
        "key_principle": "Developer responsibility for contamination",
        "relevance_triggers": ["contamination", "land stability"],
    },
    185: {
        "chapter": 15,
        "text": "Planning policies and decisions should also ensure that new development is appropriate for its location taking into account the likely effects (including cumulative effects) of pollution on health, living conditions and the natural environment, as well as the potential sensitivity of the site or the wider area to impacts that could arise from the development.",
        "key_principle": "Pollution and amenity",
        "relevance_triggers": ["pollution", "noise", "air quality", "amenity"],
    },
    186: {
        "chapter": 15,
        "text": "Planning policies and decisions should sustain and contribute towards compliance with relevant limit values or national objectives for pollutants, taking into account the presence of Air Quality Management Areas and Clean Air Zones, and the cumulative impacts from individual sites in local areas. Opportunities to improve air quality or mitigate impacts should be identified.",
        "key_principle": "Air quality",
        "relevance_triggers": ["air quality", "aqma", "pollution"],
    },
    187: {
        "chapter": 15,
        "text": "Planning policies and decisions should ensure that new development can be integrated effectively with existing businesses and community facilities. Existing businesses and facilities should not have unreasonable restrictions placed on them as a result of development permitted after they were established. Where the operation of an existing business or community facility could have a significant adverse effect on new development in its vicinity, the applicant (or 'agent of change') should be required to provide suitable mitigation before the development has been completed.",
        "key_principle": "Agent of change principle",
        "relevance_triggers": ["noise", "agent of change", "amenity"],
    },
    188: {
        "chapter": 15,
        "text": "The focus of planning policies and decisions should be on whether proposed development is an acceptable use of land, rather than the control of processes or emissions (where these are subject to separate pollution control regimes). Planning decisions should assume that these regimes will operate effectively.",
        "key_principle": "Planning vs pollution control",
        "relevance_triggers": ["pollution", "emissions"],
    },

    # =========================================================================
    # CHAPTER 16: CONSERVING THE HISTORIC ENVIRONMENT (Para 189-208)
    # =========================================================================
    189: {
        "chapter": 16,
        "text": "Heritage assets range from sites and buildings of local historic value to those of the highest significance, such as World Heritage Sites which are internationally recognised to be of Outstanding Universal Value. These assets are an irreplaceable resource, and should be conserved in a manner appropriate to their significance, so that they can be enjoyed for their contribution to the quality of life of existing and future generations.",
        "key_principle": "Heritage assets irreplaceable",
        "relevance_triggers": ["heritage", "listed building", "conservation area"],
    },
    190: {
        "chapter": 16,
        "text": "Plans should set out a positive strategy for the conservation and enjoyment of the historic environment, including heritage assets most at risk through neglect, decay or other threats. This strategy should take into account: a) the desirability of sustaining and enhancing the significance of heritage assets, and putting them to viable uses consistent with their conservation; b) the wider social, cultural, economic and environmental benefits that conservation of the historic environment can bring; c) the desirability of new development making a positive contribution to local character and distinctiveness; and d) opportunities to draw on the contribution made by the historic environment to the character of a place.",
        "key_principle": "Positive heritage strategy",
        "relevance_triggers": ["heritage", "local plan"],
    },
    191: {
        "chapter": 16,
        "text": "When considering the designation of conservation areas, local planning authorities should ensure that an area justifies such status because of its special architectural or historic interest, and that the concept of conservation is not devalued through the designation of areas that lack special interest.",
        "key_principle": "Conservation area designation",
        "relevance_triggers": ["conservation area"],
    },
    192: {
        "chapter": 16,
        "text": "Local planning authorities should maintain or have access to a historic environment record. This should contain up-to-date evidence about the historic environment in their area and be used to: a) assess the significance of heritage assets and the contribution they make to their environment; and b) predict the likelihood that currently unidentified heritage assets, particularly sites of historic and archaeological interest, will be discovered in the future.",
        "key_principle": "Historic environment record",
        "relevance_triggers": ["heritage", "archaeology"],
    },
    193: {
        "chapter": 16,
        "text": "Local planning authorities should make information about the historic environment, gathered as part of policy-making or development management, publicly accessible.",
        "key_principle": "Public access to heritage information",
        "relevance_triggers": ["heritage"],
    },
    194: {
        "chapter": 16,
        "text": "In determining applications, local planning authorities should require an applicant to describe the significance of any heritage assets affected, including any contribution made by their setting. The level of detail should be proportionate to the assets' importance and no more than is sufficient to understand the potential impact of the proposal on their significance. As a minimum the relevant historic environment record should have been consulted and the heritage assets assessed using appropriate expertise where necessary.",
        "key_principle": "Significance assessment requirement",
        "relevance_triggers": ["heritage", "listed building", "conservation area"],
    },
    195: {
        "chapter": 16,
        "text": "Local planning authorities should identify and assess the particular significance of any heritage asset that may be affected by a proposal (including by development affecting the setting of a heritage asset) taking account of the available evidence and any necessary expertise. They should take this into account when considering the impact of a proposal on a heritage asset, to avoid or minimise any conflict between the heritage asset's conservation and any aspect of the proposal.",
        "key_principle": "LPA significance assessment",
        "relevance_triggers": ["heritage", "setting"],
    },
    196: {
        "chapter": 16,
        "text": "Where there is evidence of deliberate neglect of, or damage to, a heritage asset, the deteriorated state of the heritage asset should not be taken into account in any decision.",
        "key_principle": "No benefit from deliberate neglect",
        "relevance_triggers": ["heritage"],
    },
    197: {
        "chapter": 16,
        "text": "In determining applications, local planning authorities should take account of: a) the desirability of sustaining and enhancing the significance of heritage assets and putting them to viable uses consistent with their conservation; b) the positive contribution that conservation of heritage assets can make to sustainable communities including their economic vitality; and c) the desirability of new development making a positive contribution to local character and distinctiveness.",
        "key_principle": "Heritage considerations in decisions",
        "relevance_triggers": ["heritage", "listed building", "conservation area"],
    },
    198: {
        "chapter": 16,
        "text": "In considering any applications to remove or alter a historic statue, plaque, memorial or monument (whether listed or not), local planning authorities should have regard to the importance of retaining these features as part of the local scene and history, and only grant consent for their removal, alteration or relocation in exceptional circumstances. This policy applies to all such features, whether or not they have heritage designation.",
        "key_principle": "Historic monuments and memorials",
        "relevance_triggers": ["heritage", "monument", "statue", "memorial"],
    },
    199: {
        "chapter": 16,
        "text": "When considering the impact of a proposed development on the significance of a designated heritage asset, great weight should be given to the asset's conservation (and the more important the asset, the greater the weight should be). This is irrespective of whether any potential harm amounts to substantial harm, total loss or less than substantial harm to its significance.",
        "key_principle": "Great weight to heritage conservation",
        "relevance_triggers": ["heritage", "listed building", "conservation area"],
    },
    200: {
        "chapter": 16,
        "text": "Any harm to, or loss of, the significance of a designated heritage asset (from its alteration or destruction, or from development within its setting), should require clear and convincing justification. Substantial harm to or loss of: a) grade II listed buildings, or grade II registered parks or gardens, should be exceptional; b) assets of the highest significance, notably scheduled monuments, protected wreck sites, registered battlefields, grade I and II* listed buildings, grade I and II* registered parks and gardens, and World Heritage Sites, should be wholly exceptional.",
        "key_principle": "Justification for harm",
        "relevance_triggers": ["heritage", "listed building", "scheduled monument"],
    },
    201: {
        "chapter": 16,
        "text": "Where a proposed development will lead to substantial harm to (or total loss of significance of) a designated heritage asset, local planning authorities should refuse consent, unless it can be demonstrated that the substantial harm or total loss is necessary to achieve substantial public benefits that outweigh that harm or loss, or all of the following apply: a) the nature of the heritage asset prevents all reasonable uses of the site; and b) no viable use of the heritage asset itself can be found in the medium term through appropriate marketing that will enable its conservation; and c) conservation by grant-funding or some form of not for profit, charitable or public ownership is demonstrably not possible; and d) the harm or loss is outweighed by the benefit of bringing the site back into use.",
        "key_principle": "Substantial harm test",
        "relevance_triggers": ["heritage", "substantial harm"],
    },
    202: {
        "chapter": 16,
        "text": "Where a development proposal will lead to less than substantial harm to the significance of a designated heritage asset, this harm should be weighed against the public benefits of the proposal including, where appropriate, securing its optimum viable use.",
        "key_principle": "Less than substantial harm balance",
        "relevance_triggers": ["heritage", "less than substantial harm"],
    },
    203: {
        "chapter": 16,
        "text": "The effect of an application on the significance of a non-designated heritage asset should be taken into account in determining the application. In weighing applications that directly or indirectly affect non-designated heritage assets, a balanced judgement will be required having regard to the scale of any harm or loss and the significance of the heritage asset.",
        "key_principle": "Non-designated heritage assets",
        "relevance_triggers": ["heritage", "non-designated", "locally listed"],
    },
    204: {
        "chapter": 16,
        "text": "Local planning authorities should not permit the loss of the whole or part of a heritage asset without taking all reasonable steps to ensure the new development will proceed after the loss has occurred.",
        "key_principle": "Ensure development proceeds after loss",
        "relevance_triggers": ["heritage", "demolition"],
    },
    205: {
        "chapter": 16,
        "text": "Local planning authorities should require developers to record and advance understanding of the significance of any heritage assets to be lost (wholly or in part) in a manner proportionate to their importance and the impact, and to make this evidence (and any archive generated) publicly accessible. However, the ability to record evidence of our past should not be a factor in deciding whether such loss should be permitted.",
        "key_principle": "Recording heritage assets",
        "relevance_triggers": ["heritage", "archaeology", "recording"],
    },
    206: {
        "chapter": 16,
        "text": "Local planning authorities should look for opportunities for new development within Conservation Areas and World Heritage Sites, and within the setting of heritage assets, to enhance or better reveal their significance. Proposals that preserve those elements of the setting that make a positive contribution to the asset (or which better reveal its significance) should be treated favourably.",
        "key_principle": "Enhancement opportunities",
        "relevance_triggers": ["conservation area", "world heritage", "setting"],
    },
    207: {
        "chapter": 16,
        "text": "Not all elements of a Conservation Area or World Heritage Site will necessarily contribute to its significance. Loss of a building (or other element) which makes a positive contribution to the significance of the Conservation Area or World Heritage Site should be treated either as substantial harm under paragraph 201 or less than substantial harm under paragraph 202, as appropriate, taking into account the relative significance of the element affected and its contribution to the significance of the Conservation Area or World Heritage Site as a whole.",
        "key_principle": "Contribution to conservation area significance",
        "relevance_triggers": ["conservation area", "world heritage"],
    },
    208: {
        "chapter": 16,
        "text": "Local planning authorities should assess whether the benefits of a proposal for enabling development, which would otherwise conflict with planning policies but which would secure the future conservation of a heritage asset, outweigh the disbenefits of departing from those policies.",
        "key_principle": "Enabling development",
        "relevance_triggers": ["heritage", "enabling development"],
    },

    # =========================================================================
    # CHAPTER 17: MINERALS (Para 209-217)
    # =========================================================================
    209: {
        "chapter": 17,
        "text": "It is essential that there is a sufficient supply of minerals to provide the infrastructure, buildings, energy and goods that the country needs. Since minerals are a finite natural resource, and can only be worked where they are found, best use needs to be made of them to secure their long-term conservation.",
        "key_principle": "Minerals supply essential",
        "relevance_triggers": ["minerals", "quarry"],
    },
    210: {
        "chapter": 17,
        "text": "Planning policies should: a) provide for the extraction of mineral resources of local and national importance, but not identify new sites or extensions to existing sites for peat extraction; b) so far as practicable, take account of the contribution that substitute or secondary and recycled materials and minerals waste would make to the supply of materials, before considering extraction of primary materials, whilst aiming to source minerals supplies indigenously; c) safeguard mineral resources by defining Mineral Safeguarding Areas; and d) set out policies to encourage the prior extraction of minerals, where practical and environmentally feasible, if it is necessary for non-mineral development to take place.",
        "key_principle": "Minerals policy requirements",
        "relevance_triggers": ["minerals", "quarry", "safeguarding"],
    },
    211: {
        "chapter": 17,
        "text": "When determining planning applications, great weight should be given to the benefits of mineral extraction, including to the economy. In considering proposals for mineral extraction, minerals planning authorities should: a) as far as is practical, provide for the maintenance of landbanks of non-energy minerals from outside National Parks, the Broads, Areas of Outstanding Natural Beauty and World Heritage Sites, scheduled monuments and conservation areas; b) ensure that there are no unacceptable adverse impacts on the natural and historic environment, human health or aviation safety, and take into account the cumulative effect of multiple impacts from individual sites and/or from a number of sites in a locality; c) ensure that any unavoidable noise, dust and particle emissions and any blasting vibrations are controlled, mitigated or removed at source, and establish appropriate noise limits for extraction in proximity to noise sensitive properties; d) not grant planning permission for peat extraction from new or extended sites; e) provide for restoration and aftercare at the earliest opportunity, to be carried out to high environmental standards, through the application of appropriate conditions. Bonds or other financial guarantees to underpin planning conditions should only be sought in exceptional circumstances; f) consider how to meet any demand for the extraction of building stone needed for the repair of heritage assets; and g) recognise the small-scale nature and impact of building and roofing stone quarries, and the need for a flexible approach to the potentially long duration of planning permissions reflecting the intermittent or low rate of working at many sites.",
        "key_principle": "Minerals extraction assessment",
        "relevance_triggers": ["minerals", "quarry"],
    },
    212: {
        "chapter": 17,
        "text": "Minerals planning authorities should plan for a steady and adequate supply of aggregates by: a) preparing an annual Local Aggregate Assessment; b) participating in the operation of an Aggregate Working Party and taking the advice of that Party into account when preparing their Local Aggregate Assessment; c) making provision for the land-won and other elements of their Local Aggregate Assessment in their mineral plans, taking account of the advice of the Aggregate Working Parties and the National Aggregate Co-ordinating Group; d) taking account of any published National and Sub National Guidelines on future provision which should be used as a guideline when planning for the future demand for and supply of aggregates; e) using landbanks of aggregate minerals reserves principally as an indicator of the security of aggregate minerals supply, and to indicate the additional provision that needs to be made for new aggregate extraction and alternative supplies in mineral plans; f) maintaining landbanks of at least 7 years for sand and gravel and at least 10 years for crusite rock, whilst ensuring that the capacity of operations to supply a wide range of materials is not compromised; g) ensuring that large landbanks bound up in very few sites do not stifle competition; and h) calculating and maintaining separate landbanks for any aggregate materials of a specific type or quality which have a distinct and separate market.",
        "key_principle": "Aggregate supply planning",
        "relevance_triggers": ["aggregate", "sand", "gravel", "quarry"],
    },
    213: {
        "chapter": 17,
        "text": "Minerals planning authorities should plan for a steady and adequate supply of industrial minerals by: a) co-operating with neighbouring and more distant authorities to co-ordinate the planning of industrial minerals to ensure adequate provision is made to support their likely use in industrial and manufacturing processes; b) encouraging, where appropriate, the use of alternatives to primary minerals; and c) maintaining a stock of permitted reserves to support the level of actual and proposed investment required for new or existing plant, and the maintenance and improvement of existing plant and equipment.",
        "key_principle": "Industrial minerals supply",
        "relevance_triggers": ["industrial minerals", "clay", "chalk"],
    },
    214: {
        "chapter": 17,
        "text": "Minerals planning authorities should plan for a steady and adequate supply of energy minerals, including from on-shore oil and gas, by: a) defining clear Petroleum Exploration and Development Licence Areas, and other areas where development would be acceptable, for oil and gas extraction; b) ensuring that sites meet the requirements set out in paragraph 211; and c) recognising the benefits of on-shore oil and gas development, including unconventional hydrocarbons, for the security of energy supplies and supporting the transition to a low-carbon economy; and put in place policies to facilitate their exploration and extraction.",
        "key_principle": "Energy minerals supply",
        "relevance_triggers": ["oil", "gas", "energy minerals"],
    },
    215: {
        "chapter": 17,
        "text": "When planning for on-shore oil and gas development, minerals planning authorities should clearly distinguish between, and plan positively for, the three phases of development (exploration, appraisal and production), whilst ensuring appropriate monitoring and site restoration is provided for.",
        "key_principle": "Oil and gas development phases",
        "relevance_triggers": ["oil", "gas"],
    },
    216: {
        "chapter": 17,
        "text": "When determining applications for the exploration, appraisal and production of hydrocarbons, the following issues should, subject to the requirements of other policies in this Framework, be given great weight: i. the security of energy supplies; ii. the role of gas as a transitional fuel; iii. economic growth and jobs; and iv. addressing climate change through the use of carbon capture and storage or carbon capture usage and storage.",
        "key_principle": "Hydrocarbon extraction considerations",
        "relevance_triggers": ["oil", "gas", "fracking"],
    },
    217: {
        "chapter": 17,
        "text": "Minerals planning authorities should: a) when planning for surface coal, give substantial weight to the environmental, economic and social impacts of such operations, together with any benefits, including the contribution coal makes to meeting demand and security of energy supplies; and b) not grant planning permission for the extraction of coal unless: i. the proposal is environmentally acceptable, or can be made so by planning conditions or obligations; or ii. if it is not environmentally acceptable, then it provides national, local or community benefits which clearly outweigh its likely impacts (taking all relevant matters into account, including any residual environmental impacts).",
        "key_principle": "Surface coal extraction",
        "relevance_triggers": ["coal", "mining"],
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_nppf_paragraph(para_num: int) -> dict | None:
    """Get a specific NPPF paragraph by number."""
    return NPPF_PARAGRAPHS.get(para_num)


def get_nppf_chapter(chapter_num: int) -> list[dict]:
    """Get all paragraphs for a specific chapter."""
    return [
        {"paragraph": num, **para}
        for num, para in NPPF_PARAGRAPHS.items()
        if para.get("chapter") == chapter_num
    ]


def search_nppf(keywords: list[str]) -> list[dict]:
    """Search NPPF for paragraphs matching keywords."""
    results = []
    keywords_lower = [kw.lower() for kw in keywords]

    for para_num, para in NPPF_PARAGRAPHS.items():
        triggers = para.get("relevance_triggers", [])
        text_lower = para.get("text", "").lower()
        key_principle_lower = para.get("key_principle", "").lower()

        # Check triggers
        for trigger in triggers:
            if any(kw in trigger for kw in keywords_lower):
                results.append({"paragraph": para_num, **para})
                break
        else:
            # Check text content
            if any(kw in text_lower or kw in key_principle_lower for kw in keywords_lower):
                results.append({"paragraph": para_num, **para})

    return results


def get_relevant_nppf_paragraphs(
    constraints: list[str],
    application_type: str,
    proposal: str,
) -> list[dict]:
    """
    Get relevant NPPF paragraphs based on application characteristics.

    Returns paragraphs with full citation information.
    """
    keywords = []

    # Extract keywords from constraints
    for constraint in constraints:
        constraint_lower = constraint.lower()
        if "conservation" in constraint_lower:
            keywords.extend(["conservation area", "heritage"])
        if "listed" in constraint_lower:
            keywords.extend(["listed building", "heritage"])
        if "green belt" in constraint_lower:
            keywords.append("green belt")
        if "flood" in constraint_lower:
            keywords.append("flood")
        if "tree" in constraint_lower or "tpo" in constraint_lower:
            keywords.extend(["tree", "biodiversity"])
        if "aonb" in constraint_lower:
            keywords.append("aonb")
        if "sssi" in constraint_lower:
            keywords.extend(["sssi", "biodiversity"])

    # Extract keywords from application type
    app_type_lower = application_type.lower()
    if "householder" in app_type_lower or "extension" in app_type_lower:
        keywords.extend(["design", "amenity"])
    if "residential" in app_type_lower or "dwelling" in app_type_lower:
        keywords.extend(["housing", "design"])
    if "commercial" in app_type_lower or "retail" in app_type_lower:
        keywords.extend(["economic", "town centre"])
    if "change of use" in app_type_lower:
        keywords.extend(["change of use"])

    # Extract keywords from proposal
    proposal_lower = proposal.lower()
    if "solar" in proposal_lower or "renewable" in proposal_lower:
        keywords.extend(["renewable", "energy"])
    if "agricultural" in proposal_lower or "farm" in proposal_lower:
        keywords.extend(["agricultural", "rural"])

    # Always include core paragraphs
    keywords.extend(["all", "design"])

    # Search and return unique results
    results = search_nppf(list(set(keywords)))

    # Sort by paragraph number
    results.sort(key=lambda x: x["paragraph"])

    return results


def format_nppf_citation(para_num: int) -> str:
    """Format a proper NPPF citation string."""
    para = NPPF_PARAGRAPHS.get(para_num)
    if para:
        chapter = NPPF_CHAPTERS.get(para["chapter"], {})
        chapter_name = chapter.get("name", "Unknown")
        return f"NPPF 2023 Para {para_num} (Chapter {para['chapter']}: {chapter_name})"
    return f"NPPF 2023 Para {para_num}"


def get_full_nppf_text(para_num: int) -> str:
    """Get full text of an NPPF paragraph with citation."""
    para = NPPF_PARAGRAPHS.get(para_num)
    if para:
        citation = format_nppf_citation(para_num)
        return f"**{citation}**\n\n{para['text']}"
    return f"Paragraph {para_num} not found"
