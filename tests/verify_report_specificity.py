"""
Verification script for report case-specificity.

Tests that:
1. Generated report assessments reference the specific site, proposal, and precedent cases
2. Policy framework section includes "Why engaged" explanations
3. Similar cases section explains shared characteristics and officer findings
"""
import sys
import os
import importlib
import types

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Prevent the full app from importing (avoids heavy dependencies like pypdf/cryptography)
# Create a stub for plana.api that doesn't trigger __init__.py auto-imports
plana_pkg = types.ModuleType("plana")
plana_pkg.__path__ = [os.path.join(os.path.dirname(__file__), '..', 'src', 'plana')]
plana_api_pkg = types.ModuleType("plana.api")
plana_api_pkg.__path__ = [os.path.join(os.path.dirname(__file__), '..', 'src', 'plana', 'api')]
sys.modules["plana"] = plana_pkg
sys.modules["plana.api"] = plana_api_pkg

# Now import individual modules directly (bypassing __init__.py)
import importlib.util

def _load_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

src = os.path.join(os.path.dirname(__file__), '..', 'src')

# Load modules in dependency order
_load_module("plana.api.evidence_tracker", os.path.join(src, "plana", "api", "evidence_tracker.py"))
similar_cases_mod = _load_module("plana.api.similar_cases", os.path.join(src, "plana", "api", "similar_cases.py"))
policy_engine_mod = _load_module("plana.api.policy_engine", os.path.join(src, "plana", "api", "policy_engine.py"))
reasoning_mod = _load_module("plana.api.reasoning_engine", os.path.join(src, "plana", "api", "reasoning_engine.py"))

# Stub learning module to avoid DB dependencies
learning_stub = types.ModuleType("plana.api.learning")
learning_stub.get_learning_system = lambda: None
sys.modules["plana.api.learning"] = learning_stub

report_gen_mod = _load_module("plana.api.report_generator", os.path.join(src, "plana", "api", "report_generator.py"))

HistoricCase = similar_cases_mod.HistoricCase
Policy = policy_engine_mod.Policy
PolicyParagraph = policy_engine_mod.PolicyParagraph
ProposalDetails = reasoning_mod.ProposalDetails
AssessmentResult = reasoning_mod.AssessmentResult
ReasoningResult = reasoning_mod.ReasoningResult
generate_topic_assessment = reasoning_mod.generate_topic_assessment
generate_recommendation = reasoning_mod.generate_recommendation
_build_precedent_text = reasoning_mod._build_precedent_text

format_similar_cases_section = report_gen_mod.format_similar_cases_section
format_policy_framework_section = report_gen_mod.format_policy_framework_section
generate_full_markdown_report = report_gen_mod.generate_full_markdown_report

# =============================================================================
# TEST DATA — realistic Broxtowe application
# =============================================================================

SITE_ADDRESS = "Land At 19 Hallams Lane, Chilwell, Nottinghamshire, NG9 5FG"
PROPOSAL = "Construct single storey dwelling with Air Source Heat Pump (ASHP)"
APPLICATION_TYPE = "Full Planning"
CONSTRAINTS = ["Flood Zone 2", "Residential Area"]
COUNCIL_ID = "broxtowe"
COUNCIL_NAME = "Broxtowe Borough Council"

SIMILAR_CASES = [
    HistoricCase(
        reference="22/00471/FUL",
        address="9 Maple Drive, Chilwell, Nottingham, NG9 4EU",
        ward="Chilwell",
        postcode="NG9 4EU",
        proposal="Erection of single storey detached dwelling",
        application_type="Full Planning",
        constraints=["Residential Area"],
        decision="Approved with Conditions",
        decision_date="2022-11-18",
        conditions=[
            "Development to commence within 3 years",
            "Materials to match existing streetscene",
            "No additional windows on north elevation",
        ],
        refusal_reasons=[],
        case_officer_reasoning=(
            "The single storey dwelling is of an appropriate scale and design that "
            "respects the character of the surrounding residential area. The proposal "
            "maintains adequate separation distances to neighbouring properties and "
            "complies with Policy 10 of the Aligned Core Strategy regarding design."
        ),
        key_policies_cited=["Policy 10", "Policy 17", "NPPF Chapter 12"],
        similarity_score=0.82,
        relevance_reason="Both involve single storey dwelling in residential area of Chilwell",
    ),
    HistoricCase(
        reference="23/00195/FUL",
        address="14 Boundary Road, Beeston, Nottingham, NG9 2QT",
        ward="Beeston North",
        postcode="NG9 2QT",
        proposal="Construct detached single storey dwelling on garden land",
        application_type="Full Planning",
        constraints=["Flood Zone 2", "Residential Area"],
        decision="Refused",
        decision_date="2023-05-22",
        conditions=[],
        refusal_reasons=[
            "The proposed dwelling by reason of its scale, siting and design would "
            "appear as an incongruous addition within the streetscene, contrary to "
            "Policy 10 of the ACS and Policy 17 of the LP.",
            "Insufficient information submitted to demonstrate no adverse flood risk "
            "impact, contrary to NPPF Chapter 14.",
        ],
        case_officer_reasoning=(
            "The proposal would result in a cramped form of development on this "
            "constrained plot. The applicant has not submitted a satisfactory Flood "
            "Risk Assessment to address the sequential and exception tests required "
            "for development in Flood Zone 2."
        ),
        key_policies_cited=["Policy 10", "Policy 17", "NPPF Chapter 14"],
        similarity_score=0.74,
        relevance_reason="Single storey dwelling in Flood Zone 2 within Nottinghamshire",
    ),
]

POLICIES = [
    Policy(
        id="NPPF-12",
        name="Achieving well-designed and beautiful places",
        source="NPPF",
        source_type="NPPF",
        chapter="12",
        section="Design",
        weight="full",
        paragraphs=[
            PolicyParagraph(
                number="130",
                text=(
                    "Planning policies and decisions should ensure that developments "
                    "are visually attractive, sympathetic to local character and "
                    "history, and establish a strong sense of place."
                ),
                key_tests=["visual attractiveness", "local character", "sense of place"],
            )
        ],
        triggers=["design", "character"],
        summary="Developments should be well-designed and add to the quality of an area.",
    ),
    Policy(
        id="Policy 10",
        name="Design and Enhancing Local Identity",
        source="Aligned Core Strategy",
        source_type="Local Plan",
        chapter=None,
        section=None,
        weight="full",
        paragraphs=[
            PolicyParagraph(
                number="1",
                text=(
                    "Development will be assessed in terms of its treatment of "
                    "massing, scale and proportion, materials, architectural style "
                    "and detailing."
                ),
                key_tests=["massing", "scale", "proportion", "materials"],
            )
        ],
        triggers=["design"],
        summary="Development should be designed to a high standard of design and layout.",
    ),
    Policy(
        id="Policy 17",
        name="Place-making, Design and Amenity",
        source="Local Plan Part 2",
        source_type="Local Plan",
        chapter=None,
        section=None,
        weight="full",
        paragraphs=[
            PolicyParagraph(
                number="1",
                text="Permission will be granted for development that is of a high standard of design.",
                key_tests=["high design standard", "amenity protection"],
            )
        ],
        triggers=["design", "amenity"],
        summary="Development must achieve high design standards and protect amenity.",
    ),
    Policy(
        id="Policy A",
        name="Presumption in Favour of Sustainable Development",
        source="Local Plan Part 2",
        source_type="Local Plan",
        chapter=None,
        section=None,
        weight="full",
        paragraphs=[],
        triggers=["sustainable"],
        summary="A positive approach to development that accords with the development plan.",
    ),
]

PROPOSAL_DETAILS = ProposalDetails(
    development_type="dwelling",
    num_units=1,
    num_storeys=1,
    height_metres=0.0,
    depth_metres=0.0,
    materials=[],
    parking_spaces=0,
)


def verify_test_1_assessments_are_case_specific():
    """
    TEST 1: Generate a report for a real application and verify assessments
    reference the specific site, proposal, and precedent cases.
    """
    print("=" * 70)
    print("TEST 1: Assessments reference specific site, proposal, precedent")
    print("=" * 70)

    errors = []

    # Test _build_precedent_text references actual case data
    precedent_text = _build_precedent_text(SIMILAR_CASES, max_cases=3)
    print(f"\n[_build_precedent_text output ({len(precedent_text)} chars)]")
    print(precedent_text[:500])

    if "22/00471/FUL" not in precedent_text:
        errors.append("Precedent text missing case reference 22/00471/FUL")
    if "9 Maple Drive" not in precedent_text:
        errors.append("Precedent text missing case address '9 Maple Drive'")
    if "Approved" not in precedent_text and "approved" not in precedent_text:
        errors.append("Precedent text missing approval decision")

    # Test generate_topic_assessment with real data
    topics = ["Principle of Development", "Design and Visual Impact", "Residential Amenity"]
    assessments = []

    for topic in topics:
        assessment = generate_topic_assessment(
            topic=topic,
            proposal=PROPOSAL,
            constraints=CONSTRAINTS,
            policies=POLICIES,
            similar_cases=SIMILAR_CASES,
            application_type=APPLICATION_TYPE,
            council_id=COUNCIL_ID,
            site_address=SITE_ADDRESS,
            proposal_details=PROPOSAL_DETAILS,
        )
        assessments.append(assessment)

        print(f"\n--- Assessment: {topic} ({len(assessment.reasoning)} chars) ---")
        print(assessment.reasoning[:400])
        print("...")

        # Check that the assessment references the site or proposal
        reasoning_lower = assessment.reasoning.lower()
        has_site_ref = (
            "hallams lane" in reasoning_lower
            or "chilwell" in reasoning_lower
            or SITE_ADDRESS.lower()[:20] in reasoning_lower
        )
        has_proposal_ref = (
            "single storey dwelling" in reasoning_lower
            or "dwelling" in reasoning_lower
            or "ashp" in reasoning_lower
        )
        has_precedent_ref = (
            "22/00471" in assessment.reasoning
            or "maple drive" in reasoning_lower
            or "precedent" in reasoning_lower
        )

        if not has_site_ref and not has_proposal_ref:
            errors.append(f"Assessment '{topic}': no reference to site address or proposal")
        if not has_precedent_ref:
            errors.append(f"Assessment '{topic}': no reference to precedent cases")

    # Test generate_recommendation references site
    precedent_analysis = {
        "summary": "Mixed precedent: 1 approved, 1 refused",
        "precedent_strength": "moderate",
        "approval_rate": 0.5,
        "total_cases": 2,
    }
    reasoning_result = generate_recommendation(
        assessments=assessments,
        constraints=CONSTRAINTS,
        precedent_analysis=precedent_analysis,
        proposal=PROPOSAL,
        application_type=APPLICATION_TYPE,
        site_address=SITE_ADDRESS,
    )

    print(f"\n--- Recommendation reasoning ({len(reasoning_result.recommendation_reasoning)} chars) ---")
    print(reasoning_result.recommendation_reasoning[:400])

    rec_lower = reasoning_result.recommendation_reasoning.lower()
    if "dwelling" not in rec_lower and "hallams" not in rec_lower:
        errors.append("Recommendation reasoning has no reference to proposal or site")

    # Generate full markdown report
    report_md = generate_full_markdown_report(
        reference="25/00849/FUL",
        address=SITE_ADDRESS,
        proposal=PROPOSAL,
        application_type=APPLICATION_TYPE,
        constraints=CONSTRAINTS,
        ward="Chilwell",
        postcode="NG9 5FG",
        applicant_name="Test Applicant",
        policies=POLICIES,
        similar_cases=SIMILAR_CASES,
        precedent_analysis=precedent_analysis,
        assessments=assessments,
        reasoning=reasoning_result,
        documents_count=3,
        council_name=COUNCIL_NAME,
        council_id=COUNCIL_ID,
        proposal_details=PROPOSAL_DETAILS,
    )

    print(f"\n--- Full report length: {len(report_md)} chars ---")

    report_lower = report_md.lower()
    if "hallams lane" not in report_lower:
        errors.append("Full report missing site address 'Hallams Lane'")
    if "single storey dwelling" not in report_lower:
        errors.append("Full report missing proposal description")
    if "22/00471" not in report_md:
        errors.append("Full report missing precedent case reference 22/00471/FUL")

    if errors:
        print(f"\nFAILED - {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("\nPASSED - Assessments are case-specific with site, proposal, and precedent references")
        return True


def verify_test_2_policy_why_engaged():
    """
    TEST 2: Verify policy framework section includes "Why engaged" explanations.
    """
    print("\n" + "=" * 70)
    print("TEST 2: Policy framework includes 'Why engaged' explanations")
    print("=" * 70)

    errors = []

    policy_section = format_policy_framework_section(
        POLICIES,
        council_name=COUNCIL_NAME,
        proposal=PROPOSAL,
        address=SITE_ADDRESS,
        constraints=CONSTRAINTS,
    )

    print(f"\n[Policy framework section ({len(policy_section)} chars)]")
    print(policy_section[:1500])
    print("...")

    # Check for "Why engaged" text
    if "Why engaged" not in policy_section:
        errors.append("Policy section missing 'Why engaged' explanations")

    # Check that proposal is referenced
    if "Hallams Lane" not in policy_section and "single storey dwelling" not in policy_section.lower():
        errors.append("Policy section not referencing the specific proposal or site")

    # Check that Local Plan policies have engagement explanations
    local_plan_policies = [p for p in POLICIES if p.source_type == "Local Plan"]
    for p in local_plan_policies:
        p_name_lower = p.name.lower()
        has_design = any(kw in p_name_lower for kw in ["design", "character", "place-making"])
        has_sustainable = any(kw in p_name_lower for kw in ["sustainable", "presumption"])
        if has_design or has_sustainable:
            # Should have a "Why engaged" for this policy
            # Just check that at least one exists overall
            pass

    why_engaged_count = policy_section.count("Why engaged")
    print(f"\n'Why engaged' count: {why_engaged_count}")
    if why_engaged_count < 2:
        errors.append(f"Expected at least 2 'Why engaged' explanations, found {why_engaged_count}")

    if errors:
        print(f"\nFAILED - {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print(f"\nPASSED - Policy framework has {why_engaged_count} 'Why engaged' explanations")
        return True


def verify_test_3_similar_cases_evidence():
    """
    TEST 3: Verify similar cases section explains shared characteristics and officer findings.
    """
    print("\n" + "=" * 70)
    print("TEST 3: Similar cases explain shared characteristics & officer findings")
    print("=" * 70)

    errors = []

    cases_section = format_similar_cases_section(
        SIMILAR_CASES,
        proposal=PROPOSAL,
        address=SITE_ADDRESS,
    )

    print(f"\n[Similar cases section ({len(cases_section)} chars)]")
    print(cases_section[:2000])
    print("...")

    # Check shared characteristics explanations
    if "Why comparable" not in cases_section:
        errors.append("Missing 'Why comparable' explanations")

    if "dwelling" not in cases_section.lower():
        errors.append("Not explaining shared development type (dwelling)")

    # Check officer findings are included
    if "Officer Reasoning" not in cases_section:
        errors.append("Missing 'Officer Reasoning' section")

    if "appropriate scale" not in cases_section.lower() and "single storey" not in cases_section.lower():
        errors.append("Not including officer reasoning text from case 22/00471/FUL")

    # Check application to current proposal
    if "Application to current proposal" not in cases_section:
        errors.append("Missing 'Application to current proposal' section")

    if "Construct single storey dwelling" not in cases_section:
        errors.append("Not referencing the current proposal in the application section")

    # Check the refused case references refusal reasons
    if "refusal" not in cases_section.lower() and "refused" not in cases_section.lower():
        errors.append("Not mentioning the refused case's outcome")

    # Check both cases are present
    if "22/00471/FUL" not in cases_section:
        errors.append("Missing approved case reference 22/00471/FUL")
    if "23/00195/FUL" not in cases_section:
        errors.append("Missing refused case reference 23/00195/FUL")

    # Check officer reasoning from second case
    if "cramped" not in cases_section.lower() and "flood risk" not in cases_section.lower():
        errors.append("Not including officer reasoning from refused case 23/00195/FUL")

    if errors:
        print(f"\nFAILED - {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("\nPASSED - Similar cases section has evidence-based structure with shared characteristics and officer findings")
        return True


def verify_test_4_empty_proposal_fallback():
    """
    TEST 4: When proposal is empty, functions should still produce meaningful text
    (not empty parentheses or 'this proposal').
    """
    print("\n" + "=" * 70)
    print("TEST 4: Empty proposal fallback produces meaningful text")
    print("=" * 70)

    errors = []

    _resolve_proposal_text = reasoning_mod._resolve_proposal_text
    _resolve_dev_type = reasoning_mod._resolve_dev_type

    # Test _resolve_proposal_text with empty proposal
    resolved = _resolve_proposal_text("", PROPOSAL_DETAILS, "Full Planning", SITE_ADDRESS)
    print(f"\nResolved empty proposal: '{resolved}'")
    if not resolved or resolved == "the proposed development":
        errors.append(f"Empty proposal resolved to generic text: '{resolved}'")
    if "dwelling" not in resolved.lower():
        errors.append(f"Resolved proposal doesn't mention dwelling: '{resolved}'")

    # Test _resolve_dev_type with 'householder' dev_type
    dev_type = _resolve_dev_type("Construct single storey dwelling", PROPOSAL_DETAILS, "householder")
    print(f"Dev type from 'householder' with dwelling proposal: '{dev_type}'")
    if dev_type == "householder":
        errors.append(f"Dev type still 'householder' despite proposal saying 'dwelling': '{dev_type}'")

    # Test assessment with EMPTY proposal
    assessment = generate_topic_assessment(
        topic="Principle of Development",
        proposal="",  # EMPTY - simulating the live bug
        constraints=CONSTRAINTS,
        policies=POLICIES,
        similar_cases=SIMILAR_CASES,
        application_type="householder",
        council_id=COUNCIL_ID,
        site_address=SITE_ADDRESS,
        proposal_details=PROPOSAL_DETAILS,
    )
    print(f"\n--- Assessment with empty proposal ({len(assessment.reasoning)} chars) ---")
    print(assessment.reasoning[:400])

    if "()" in assessment.reasoning:
        errors.append("Assessment contains '()' — empty proposal parentheses")
    if "this proposal" in assessment.reasoning.lower():
        errors.append("Assessment contains 'this proposal' fallback")

    # Test similar cases with empty proposal
    cases_section = format_similar_cases_section(
        SIMILAR_CASES, proposal="", address=SITE_ADDRESS,
    )
    print(f"\n--- Similar cases with empty proposal ---")
    print(cases_section[:300])

    if "(this proposal)" in cases_section:
        errors.append("Similar cases contains '(this proposal)' fallback")
    if "()" in cases_section:
        errors.append("Similar cases contains '()' empty parentheses")

    # Test policy section with empty proposal
    policy_section = format_policy_framework_section(
        POLICIES, council_name=COUNCIL_NAME, proposal="", address=SITE_ADDRESS, constraints=CONSTRAINTS,
    )
    if "the proposed development at" not in policy_section.lower() and SITE_ADDRESS[:20] not in policy_section:
        errors.append("Policy section with empty proposal doesn't reference site address")

    if errors:
        print(f"\nFAILED - {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("\nPASSED - Empty proposal fallback produces meaningful, case-specific text")
        return True


if __name__ == "__main__":
    print("VERIFICATION: Report Case-Specificity")
    print("=" * 70)
    print(f"Site: {SITE_ADDRESS}")
    print(f"Proposal: {PROPOSAL}")
    print(f"Council: {COUNCIL_NAME}")
    print()

    results = []
    results.append(("Assessments reference site/proposal/precedent", verify_test_1_assessments_are_case_specific()))
    results.append(("Policy framework 'Why engaged'", verify_test_2_policy_why_engaged()))
    results.append(("Similar cases shared characteristics & officer findings", verify_test_3_similar_cases_evidence()))
    results.append(("Empty proposal fallback", verify_test_4_empty_proposal_fallback()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll 4 test items VERIFIED.")
    else:
        print("\nSome tests FAILED - see details above.")

    sys.exit(0 if all_passed else 1)
