"""
Integration test: proves that proposal data flows end-to-end into the report.

Tests the core report generation functions directly (bypasses FastAPI app
which has dependency issues in test environment).
"""

import sys
import os
import types
import importlib.util


def _setup_modules():
    """Load src/plana/api modules with isolated imports to avoid heavy deps."""
    src = os.path.join(os.path.dirname(__file__), "..", "src")
    sys.path.insert(0, os.path.abspath(src))

    # Create module stubs
    plana_pkg = types.ModuleType("plana")
    plana_pkg.__path__ = [os.path.join(src, "plana")]
    plana_api_pkg = types.ModuleType("plana.api")
    plana_api_pkg.__path__ = [os.path.join(src, "plana", "api")]
    sys.modules["plana"] = plana_pkg
    sys.modules["plana.api"] = plana_api_pkg

    def _load(name, filepath):
        spec = importlib.util.spec_from_file_location(name, filepath)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    _load("plana.api.evidence_tracker", os.path.join(src, "plana/api/evidence_tracker.py"))
    similar = _load("plana.api.similar_cases", os.path.join(src, "plana/api/similar_cases.py"))
    policy = _load("plana.api.policy_engine", os.path.join(src, "plana/api/policy_engine.py"))
    reasoning = _load("plana.api.reasoning_engine", os.path.join(src, "plana/api/reasoning_engine.py"))
    learning = types.ModuleType("plana.api.learning")
    learning.get_learning_system = lambda: None
    sys.modules["plana.api.learning"] = learning
    report = _load("plana.api.report_generator", os.path.join(src, "plana/api/report_generator.py"))

    return similar, policy, reasoning, report


similar_mod, policy_mod, reasoning_mod, report_mod = _setup_modules()

HistoricCase = similar_mod.HistoricCase
Policy = policy_mod.Policy
PolicyParagraph = policy_mod.PolicyParagraph
ProposalDetails = reasoning_mod.ProposalDetails


# ---------------------------------------------------------------------------
# Shared test data — mirrors what the frontend SHOULD send
# ---------------------------------------------------------------------------

PROPOSAL = "Construct single storey dwelling with Air Source Heat Pump (ASHP)"
SITE_ADDRESS = "Land At 19 Hallams Lane, Chilwell, Nottinghamshire, NG9 5FG"
APP_TYPE = "Full Planning"

POLICIES = [
    Policy(
        id="2", name="Achieving sustainable development", source="NPPF",
        source_type="NPPF", chapter=2,
        summary="Sustainable development through economic, social, environmental objectives.",
        paragraphs=[PolicyParagraph(number=11, text="Presumption in favour of sustainable development.", key_tests=["presumption"])],
    ),
    Policy(
        id="12", name="Achieving well-designed and beautiful places", source="NPPF",
        source_type="NPPF", chapter=12,
        summary="Developments should be well-designed.",
        paragraphs=[PolicyParagraph(number=130, text="Developments must be sympathetic to local character.", key_tests=["local character"])],
    ),
    Policy(
        id="14", name="Meeting the challenge of climate change", source="NPPF",
        source_type="NPPF", chapter=14,
        summary="Support transition to low carbon future.",
        paragraphs=[PolicyParagraph(number=152, text="Support renewable and low carbon energy.", key_tests=["renewable energy", "low carbon"])],
    ),
    Policy(
        id="10", name="Design and Enhancing Local Identity", source="Aligned Core Strategy",
        source_type="Local Plan",
        summary="High standard of design.",
        paragraphs=[PolicyParagraph(number=1, text="All new development designed to highest standard.", key_tests=["scale", "materials"])],
    ),
]

SIMILAR_CASES = [
    HistoricCase(
        reference="22/00471/FUL",
        address="9 Maple Drive, Chilwell, NG9 4EU", ward="Chilwell", postcode="NG9 4EU",
        proposal="Erection of single storey detached dwelling with ASHP",
        decision="Approved with Conditions", decision_date="2022-11-18",
        similarity_score=0.82, relevance_reason="Similar single-storey dwelling",
        constraints=["Residential Area"], conditions=[], refusal_reasons=[],
        case_officer_reasoning="The single storey dwelling is of appropriate scale and design.",
        key_policies_cited=["Policy 10", "NPPF Chapter 12"],
        application_type="Full Planning",
    ),
]


# ---------------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------------


class TestAnalyseProposal:
    """Verify that analyse_proposal extracts the right data from proposal text."""

    def test_detects_dwelling_type(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        assert details.development_type == "dwelling", \
            f"Expected 'dwelling', got '{details.development_type}'"

    def test_detects_single_storey(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        assert details.num_storeys == 1, \
            f"Expected num_storeys=1, got {details.num_storeys}"

    def test_detects_one_unit(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        assert details.num_units == 1, \
            f"Expected num_units=1, got {details.num_units}"

    def test_empty_proposal_with_householder_type(self):
        """When proposal is empty and type is householder, dev_type falls back."""
        details = reasoning_mod.analyse_proposal("", "householder")
        assert details.development_type == "householder"
        assert details.num_units == 0


class TestFeatureExtraction:
    """Verify that _extract_proposal_features finds ASHP, scale, etc."""

    def test_finds_ashp(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        features = reasoning_mod._extract_proposal_features(PROPOSAL, details)
        assert len(features["sustainability"]) > 0, "ASHP not found in sustainability features"
        assert any("ASHP" in f or "heat pump" in f.lower() for f in features["sustainability"])

    def test_finds_single_storey_scale(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        features = reasoning_mod._extract_proposal_features(PROPOSAL, details)
        assert len(features["scale"]) > 0, "Single storey scale not found"
        assert any("single-storey" in f for f in features["scale"])

    def test_finds_housing(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        features = reasoning_mod._extract_proposal_features(PROPOSAL, details)
        assert len(features["housing"]) > 0, "Housing contribution not found"

    def test_empty_proposal_returns_empty_features(self):
        details = reasoning_mod.analyse_proposal("", "householder")
        features = reasoning_mod._extract_proposal_features("", details)
        all_empty = all(len(v) == 0 for v in features.values())
        assert all_empty, f"Empty proposal should produce empty features, got: {features}"


class TestPolicyFrameworkSection:
    """Verify the policy framework section uses evidence from proposal."""

    def test_nppf_section_mentions_ashp(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        section = report_mod.format_policy_framework_section(
            POLICIES, "Broxtowe Borough Council",
            proposal=PROPOSAL, address=SITE_ADDRESS,
            constraints=["Flood Zone 2"],
            proposal_details=details,
        )
        assert "ASHP" in section or "Air Source Heat Pump" in section, \
            "NPPF section should mention ASHP as evidence for sustainability"

    def test_nppf_section_mentions_single_storey(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        section = report_mod.format_policy_framework_section(
            POLICIES, "Broxtowe Borough Council",
            proposal=PROPOSAL, address=SITE_ADDRESS,
            constraints=[], proposal_details=details,
        )
        assert "single-storey" in section.lower() or "single storey" in section.lower(), \
            "NPPF section should mention single-storey scale"


class TestSimilarCasesSection:
    """Verify similar cases section explains shared features."""

    def test_shared_ashp_detected(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        section = report_mod.format_similar_cases_section(
            SIMILAR_CASES, proposal=PROPOSAL, address=SITE_ADDRESS,
            proposal_details=details,
        )
        # Both proposals mention ASHP — should be detected as shared feature
        assert "ashp" in section.lower() or "heat pump" in section.lower(), \
            "Similar cases should note shared ASHP feature"

    def test_shared_single_storey_detected(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        section = report_mod.format_similar_cases_section(
            SIMILAR_CASES, proposal=PROPOSAL, address=SITE_ADDRESS,
            proposal_details=details,
        )
        assert "single-storey" in section.lower() or "single storey" in section.lower(), \
            "Similar cases should note shared single-storey feature"


class TestDesignAssessment:
    """Verify design assessment uses extracted features."""

    def test_design_mentions_scale(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        assessment = reasoning_mod.generate_topic_assessment(
            topic="Design and Visual Impact", proposal=PROPOSAL,
            constraints=["Flood Zone 2"], policies=POLICIES,
            similar_cases=SIMILAR_CASES, application_type=APP_TYPE,
            council_id="broxtowe", site_address=SITE_ADDRESS,
            proposal_details=details,
        )
        assert "single-storey" in assessment.reasoning.lower() or "1" in assessment.reasoning, \
            "Design assessment should reference single-storey scale"

    def test_design_mentions_ashp(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        assessment = reasoning_mod.generate_topic_assessment(
            topic="Design and Visual Impact", proposal=PROPOSAL,
            constraints=[], policies=POLICIES,
            similar_cases=SIMILAR_CASES, application_type=APP_TYPE,
            council_id="broxtowe", site_address=SITE_ADDRESS,
            proposal_details=details,
        )
        assert "ASHP" in assessment.reasoning or "heat pump" in assessment.reasoning.lower(), \
            "Design assessment should mention ASHP as sustainable design feature"


class TestAmenityAssessment:
    """Verify amenity assessment flags ASHP noise."""

    def test_amenity_flags_ashp_noise(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        assessment = reasoning_mod.generate_topic_assessment(
            topic="Residential Amenity", proposal=PROPOSAL,
            constraints=[], policies=POLICIES,
            similar_cases=SIMILAR_CASES, application_type=APP_TYPE,
            council_id="broxtowe", site_address=SITE_ADDRESS,
            proposal_details=details,
        )
        assert "noise" in assessment.reasoning.lower() or "ASHP" in assessment.reasoning, \
            "Amenity assessment should flag ASHP noise consideration"


class TestFullReportEndToEnd:
    """Full end-to-end: generate_full_markdown_report with all real data."""

    def _generate_full_report(self):
        details = reasoning_mod.analyse_proposal(PROPOSAL, APP_TYPE)
        precedent_analysis = {"total_cases": 1, "approved_count": 1, "approval_rate": 1.0}

        topics = ["Principle of Development", "Design and Visual Impact", "Residential Amenity"]
        assessments = []
        for topic in topics:
            a = reasoning_mod.generate_topic_assessment(
                topic=topic, proposal=PROPOSAL, constraints=["Flood Zone 2"],
                policies=POLICIES, similar_cases=SIMILAR_CASES,
                application_type=APP_TYPE, council_id="broxtowe",
                site_address=SITE_ADDRESS, proposal_details=details,
            )
            assessments.append(a)

        reasoning = reasoning_mod.generate_recommendation(
            assessments=assessments, constraints=["Flood Zone 2"],
            precedent_analysis=precedent_analysis, proposal=PROPOSAL,
            application_type=APP_TYPE, site_address=SITE_ADDRESS,
        )

        md = report_mod.generate_full_markdown_report(
            reference="25/00849/FUL", address=SITE_ADDRESS, proposal=PROPOSAL,
            application_type=APP_TYPE, constraints=["Flood Zone 2"],
            ward="Chilwell", postcode="NG9 5FG", applicant_name="Mr Smith",
            policies=POLICIES, similar_cases=SIMILAR_CASES,
            precedent_analysis=precedent_analysis,
            assessments=assessments, reasoning=reasoning, documents_count=0,
            council_name="Broxtowe Borough Council", council_id="broxtowe",
            proposal_details=details,
        )
        return md

    def test_report_not_generic(self):
        """The full report must not contain generic placeholder text."""
        md = self._generate_full_report()
        # These are signs of generic/empty-proposal output
        assert "the proposed development)" not in md, "Generic fallback text found in report"
        assert "Development Type | Householder" not in md, "Should be 'Dwelling' not 'Householder'"
        assert "N/A" not in md.split("Proposal Specifications")[1].split("---")[0] or \
               "Storeys | 1" in md, "Specs should not be all N/A"

    def test_report_contains_ashp(self):
        md = self._generate_full_report()
        ashp_count = md.lower().count("ashp") + md.lower().count("air source heat pump")
        assert ashp_count >= 3, \
            f"ASHP should appear at least 3 times in report (policy, design, amenity). Found {ashp_count}"

    def test_report_contains_dwelling(self):
        md = self._generate_full_report()
        assert "Dwelling" in md or "dwelling" in md

    def test_report_contains_single_storey(self):
        md = self._generate_full_report()
        assert "single storey" in md.lower() or "single-storey" in md.lower()

    def test_report_contains_flood_zone(self):
        md = self._generate_full_report()
        assert "Flood Zone 2" in md

    def test_report_contains_ward(self):
        md = self._generate_full_report()
        assert "Chilwell" in md

    def test_report_contains_site_address(self):
        md = self._generate_full_report()
        assert "Hallams Lane" in md
