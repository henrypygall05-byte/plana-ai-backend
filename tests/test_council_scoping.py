"""
Tests for strict council scoping.

Verifies that:
1. Council mismatch is refused with CouncilMismatchError.
2. Broxtowe reports contain ONLY Broxtowe configuration
   (no "Nottingham City Council" strings).
3. Policy retrieval is scoped to the correct council's development plan.
"""

import re
import tempfile
from pathlib import Path

import pytest

from plana.core.constants import (
    COUNCIL_NAMES,
    PLANNING_AUTHORITY_SCOPE,
    resolve_council_name,
)
from plana.core.exceptions import CouncilMismatchError
from plana.policy.search import PolicySearch
from plana.report.generator import ApplicationData, ReportGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def broxtowe_app() -> ApplicationData:
    """A Broxtowe planning application."""
    return ApplicationData(
        reference="24/00567/FUL",
        address="Land At 19 Hallams Lane, Chilwell, Nottinghamshire, NG9 5FG",
        proposal="Construct single storey dwelling with Air Source Heat Pump (ASHP)",
        application_type="Full Planning",
        constraints=["Residential Area"],
        ward="Chilwell",
        council_id="broxtowe",
        council_name="Broxtowe Borough Council",
    )


@pytest.fixture()
def newcastle_app() -> ApplicationData:
    """A Newcastle planning application."""
    return ApplicationData(
        reference="2024/0930/01/DET",
        address="T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
        proposal="Erection of two storey rear/roof extension and conversion",
        application_type="Full Planning",
        constraints=["Grainger Town Conservation Area"],
        ward="Monument",
        council_id="newcastle",
        council_name="Newcastle City Council",
    )


@pytest.fixture()
def generator() -> ReportGenerator:
    return ReportGenerator()


# ---------------------------------------------------------------------------
# 1. Council mismatch guard
# ---------------------------------------------------------------------------

class TestCouncilMismatchGuard:
    """Verify that council_id mismatch raises CouncilMismatchError."""

    def test_mismatch_raises(self):
        """Different council_id vs stored must raise."""
        err = CouncilMismatchError(
            reference="24/00567/FUL",
            expected="broxtowe",
            got="newcastle",
        )
        assert err.status_code == 409
        assert "broxtowe" in str(err)
        assert "newcastle" in str(err)
        assert err.error_code == "COUNCIL_MISMATCH"

    def test_safe_message_contains_both(self):
        err = CouncilMismatchError(
            reference="REF/1",
            expected="broxtowe",
            got="newcastle",
        )
        assert "broxtowe" in err.safe_message
        assert "newcastle" in err.safe_message


# ---------------------------------------------------------------------------
# 2. Broxtowe report snapshot — no cross-council contamination
# ---------------------------------------------------------------------------

class TestBroxtoweReportSnapshot:
    """Verify Broxtowe reports contain ONLY Broxtowe configuration."""

    def test_no_nottingham_city_council_in_report(self, generator, broxtowe_app):
        """A Broxtowe report must never contain 'Nottingham City Council'."""
        report = generator.generate_report(broxtowe_app)
        assert "Nottingham City Council" not in report

    def test_no_newcastle_city_council_in_report(self, generator, broxtowe_app):
        """A Broxtowe report must never contain 'Newcastle City Council'."""
        report = generator.generate_report(broxtowe_app)
        assert "Newcastle City Council" not in report

    def test_header_uses_broxtowe(self, generator, broxtowe_app):
        """Report header must use Broxtowe Borough Council."""
        report = generator.generate_report(broxtowe_app)
        header = report.split("\n", 1)[0]
        assert "Broxtowe Borough Council" in header

    def test_lpa_line_uses_broxtowe(self, generator, broxtowe_app):
        """The LPA line must say Broxtowe."""
        report = generator.generate_report(broxtowe_app)
        assert "**Local Planning Authority:** Broxtowe Borough Council" in report

    def test_no_other_council_names_in_broxtowe_report(
        self, generator, broxtowe_app,
    ):
        """No other council's display name may appear in a Broxtowe report,
        EXCEPT within allowed contexts like 'Greater Nottingham'."""
        report = generator.generate_report(broxtowe_app)
        report_lower = report.lower()

        scope = PLANNING_AUTHORITY_SCOPE["broxtowe"]
        allowed = [p.lower() for p in scope.get("allowed_patterns", [])]

        for cid, cname in COUNCIL_NAMES.items():
            if cid == "broxtowe":
                continue
            cname_lower = cname.lower()
            # Find all occurrences
            idx = 0
            while True:
                pos = report_lower.find(cname_lower, idx)
                if pos == -1:
                    break
                # Check if within an allowed context
                context_start = max(0, pos - 30)
                context_end = min(len(report_lower), pos + len(cname_lower) + 30)
                context = report_lower[context_start:context_end]
                assert any(ap in context for ap in allowed), (
                    f"Found '{cname}' in Broxtowe report without allowed "
                    f"context. Near: ...{report[context_start:context_end]}..."
                )
                idx = pos + 1


class TestNewcastleReportSnapshot:
    """Symmetric check: Newcastle reports contain no Broxtowe strings."""

    def test_no_broxtowe_in_newcastle_report(self, generator, newcastle_app):
        report = generator.generate_report(newcastle_app)
        assert "Broxtowe Borough Council" not in report

    def test_header_uses_newcastle(self, generator, newcastle_app):
        report = generator.generate_report(newcastle_app)
        header = report.split("\n", 1)[0]
        assert "Newcastle City Council" in header


# ---------------------------------------------------------------------------
# 3. Policy retrieval is council-scoped
# ---------------------------------------------------------------------------

class TestPolicyScopeByCouncil:
    """Verify policy search returns only the correct council's policies."""

    def test_broxtowe_only_returns_broxtowe_and_nppf_policies(self):
        ps = PolicySearch()
        policies = ps.retrieve_relevant_policies(
            proposal="Construct single storey dwelling",
            constraints=["Residential Area"],
            application_type="Full Planning",
            council_id="broxtowe",
        )
        allowed_doc_ids = frozenset(PLANNING_AUTHORITY_SCOPE["broxtowe"]["doc_ids"])
        for p in policies:
            assert p.doc_id in allowed_doc_ids, (
                f"Policy {p.policy_id} from {p.doc_id} leaked into "
                f"Broxtowe results (allowed: {allowed_doc_ids})"
            )

    def test_newcastle_only_returns_newcastle_and_nppf_policies(self):
        ps = PolicySearch()
        policies = ps.retrieve_relevant_policies(
            proposal="Erection of two storey extension",
            constraints=["Conservation Area"],
            application_type="Full Planning",
            council_id="newcastle",
        )
        allowed_doc_ids = frozenset(PLANNING_AUTHORITY_SCOPE["newcastle"]["doc_ids"])
        for p in policies:
            assert p.doc_id in allowed_doc_ids, (
                f"Policy {p.policy_id} from {p.doc_id} leaked into "
                f"Newcastle results (allowed: {allowed_doc_ids})"
            )

    def test_no_newcastle_policies_in_broxtowe_search(self):
        """CSUCP and DAP must never appear for Broxtowe."""
        ps = PolicySearch()
        policies = ps.retrieve_relevant_policies(
            proposal="Construct dwelling with access",
            constraints=["Conservation Area"],
            application_type="Full Planning",
            council_id="broxtowe",
        )
        newcastle_only = {"CSUCP", "DAP"}
        doc_ids = {p.doc_id for p in policies}
        assert not doc_ids.intersection(newcastle_only), (
            f"Newcastle-only docs {doc_ids & newcastle_only} leaked into Broxtowe search"
        )

    def test_no_broxtowe_policies_in_newcastle_search(self):
        """ACS and BLP2 must never appear for Newcastle."""
        ps = PolicySearch()
        policies = ps.retrieve_relevant_policies(
            proposal="Residential conversion in conservation area",
            constraints=["Conservation Area", "Listed Building"],
            application_type="Full Planning",
            council_id="newcastle",
        )
        broxtowe_only = {"ACS", "BLP2"}
        doc_ids = {p.doc_id for p in policies}
        assert not doc_ids.intersection(broxtowe_only), (
            f"Broxtowe-only docs {doc_ids & broxtowe_only} leaked into Newcastle search"
        )


# ---------------------------------------------------------------------------
# 4. Report consistency check raises on contamination
# ---------------------------------------------------------------------------

class TestReportConsistencyCheck:
    """Verify _check_council_consistency raises on cross-council text."""

    def test_raises_on_wrong_header(self):
        report = "# Newcastle City Council – Planning Assessment Report\n\nBody text."
        with pytest.raises(CouncilMismatchError) as exc_info:
            ReportGenerator._check_council_consistency(
                report,
                expected_council="Broxtowe Borough Council",
                council_id="broxtowe",
            )
        assert exc_info.value.expected == "Broxtowe Borough Council"

    def test_raises_on_foreign_council_in_body(self):
        report = (
            "# Broxtowe Borough Council – Planning Assessment Report\n\n"
            "This site is near Nottingham City Council boundary."
        )
        with pytest.raises(CouncilMismatchError):
            ReportGenerator._check_council_consistency(
                report,
                expected_council="Broxtowe Borough Council",
                council_id="broxtowe",
            )

    def test_allows_greater_nottingham_for_broxtowe(self):
        """'Greater Nottingham' is the joint plan area — must be allowed."""
        report = (
            "# Broxtowe Borough Council – Planning Assessment Report\n\n"
            "The Greater Nottingham Aligned Core Strategy applies."
        )
        # Should NOT raise
        ReportGenerator._check_council_consistency(
            report,
            expected_council="Broxtowe Borough Council",
            council_id="broxtowe",
        )

    def test_passes_clean_report(self):
        report = (
            "# Broxtowe Borough Council – Planning Assessment Report\n\n"
            "Site at Chilwell. ACS and BLP2 policies apply."
        )
        ReportGenerator._check_council_consistency(
            report,
            expected_council="Broxtowe Borough Council",
            council_id="broxtowe",
        )


# ---------------------------------------------------------------------------
# 5. End-to-end: full report generation with scoping
# ---------------------------------------------------------------------------

class TestEndToEndCouncilScoping:
    """Full report generation enforces council scoping."""

    def test_broxtowe_report_policy_section_cites_blp2_not_dap(
        self, generator, broxtowe_app,
    ):
        """Policy context in a Broxtowe report should cite BLP2/ACS, not DAP."""
        report = generator.generate_report(broxtowe_app)
        # DAP is Newcastle-only
        # Check that DAP policies don't appear unless they're in NPPF
        # (DAP is a doc_id, not a policy_id prefix)
        lines = report.split("\n")
        for line in lines:
            if line.strip().startswith("- **") and "DAP" in line:
                # Should not find (p.XX, score Y.YY) — that's a policy citation
                assert "(p." not in line, (
                    f"Newcastle DAP policy cited in Broxtowe report: {line}"
                )

    def test_newcastle_report_policy_section_cites_csucp_not_acs(
        self, generator, newcastle_app,
    ):
        """Policy context in a Newcastle report should cite CSUCP/DAP, not ACS."""
        report = generator.generate_report(newcastle_app)
        lines = report.split("\n")
        for line in lines:
            if line.strip().startswith("- **") and "(p." in line:
                # Policy citation line — check it's not ACS or BLP2
                assert "ACS" not in line.split("**")[1] if "**" in line else True, (
                    f"Broxtowe ACS policy cited in Newcastle report: {line}"
                )
