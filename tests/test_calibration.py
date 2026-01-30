"""
Unit tests for decision calibration module.

Tests parsing, calibration rules, and integration with QC pipeline.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from plana.decision_calibration import (
    parse_application_type,
    calibrate_decision,
    CALIBRATION_RULES,
)


class TestParseApplicationType:
    """Tests for parse_application_type function."""

    def test_standard_format(self):
        """Test standard Newcastle reference format."""
        assert parse_application_type("2025/2090/01/LDC") == "LDC"
        assert parse_application_type("2025/0486/04/DCC") == "DCC"
        assert parse_application_type("2025/1974/01/HOU") == "HOU"
        assert parse_application_type("2025/1710/01/DET") == "DET"
        assert parse_application_type("2025/1617/01/LBC") == "LBC"

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        assert parse_application_type("  2025/2090/01/LDC  ") == "LDC"
        assert parse_application_type("\t2025/1974/01/HOU\n") == "HOU"

    def test_case_insensitivity(self):
        """Test that type codes are normalized to uppercase."""
        assert parse_application_type("2025/2090/01/ldc") == "LDC"
        assert parse_application_type("2025/1974/01/hou") == "HOU"

    def test_empty_reference(self):
        """Test handling of empty reference."""
        assert parse_application_type("") == "UNKNOWN"
        assert parse_application_type(None) == "UNKNOWN"

    def test_malformed_reference(self):
        """Test handling of malformed references."""
        # Should extract last component
        assert parse_application_type("DET") == "DET"
        assert parse_application_type("2025/DET") == "DET"


class TestCalibrateDecision:
    """Tests for calibrate_decision function."""

    def test_refuse_never_overridden(self):
        """Test that REFUSE decisions are never overridden."""
        assert calibrate_decision("2025/1974/01/HOU", "REFUSE") == "REFUSE"
        assert calibrate_decision("2025/0486/04/DCC", "REFUSE") == "REFUSE"
        assert calibrate_decision("2025/1739/01/TPO", "REFUSE") == "REFUSE"
        assert calibrate_decision("2025/2090/01/LDC", "REFUSE") == "REFUSE"

    def test_hou_calibration(self):
        """Test HOU (Householder) calibration to APPROVE_WITH_CONDITIONS."""
        assert calibrate_decision("2025/1974/01/HOU", "APPROVE") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1974/01/HOU", "APPROVE_WITH_CONDITIONS") == "APPROVE_WITH_CONDITIONS"

    def test_lbc_calibration(self):
        """Test LBC (Listed Building Consent) calibration to APPROVE_WITH_CONDITIONS."""
        assert calibrate_decision("2025/1617/01/LBC", "APPROVE") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1617/01/LBC", "APPROVE_WITH_CONDITIONS") == "APPROVE_WITH_CONDITIONS"

    def test_det_calibration(self):
        """Test DET (Full Planning) calibration to APPROVE_WITH_CONDITIONS."""
        assert calibrate_decision("2025/1710/01/DET", "APPROVE") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1710/01/DET", "APPROVE_WITH_CONDITIONS") == "APPROVE_WITH_CONDITIONS"

    def test_ldc_calibration(self):
        """Test LDC (Lawful Development Certificate) calibration to APPROVE_WITH_CONDITIONS."""
        assert calibrate_decision("2025/2090/01/LDC", "APPROVE") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/2090/01/LDC", "APPROVE_WITH_CONDITIONS") == "APPROVE_WITH_CONDITIONS"

    def test_dcc_calibration(self):
        """Test DCC (Discharge Conditions) calibration to APPROVE."""
        assert calibrate_decision("2025/0486/04/DCC", "APPROVE") == "APPROVE"
        assert calibrate_decision("2025/0486/04/DCC", "APPROVE_WITH_CONDITIONS") == "APPROVE"

    def test_tpo_no_forced_calibration(self):
        """Test TPO (Tree Preservation Order) keeps raw decision."""
        assert calibrate_decision("2025/1739/01/TPO", "APPROVE") == "APPROVE"
        assert calibrate_decision("2025/1739/01/TPO", "APPROVE_WITH_CONDITIONS") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1739/01/TPO", "REFUSE") == "REFUSE"

    def test_tca_no_forced_calibration(self):
        """Test TCA (Trees in Conservation Area) keeps raw decision."""
        assert calibrate_decision("2025/1985/01/TCA", "APPROVE") == "APPROVE"
        assert calibrate_decision("2025/1985/01/TCA", "APPROVE_WITH_CONDITIONS") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1985/01/TCA", "REFUSE") == "REFUSE"

    def test_unknown_decision(self):
        """Test handling of unknown/invalid decisions."""
        assert calibrate_decision("2025/1974/01/HOU", "") == "UNKNOWN"
        assert calibrate_decision("2025/1974/01/HOU", "INVALID") == "UNKNOWN"
        assert calibrate_decision("2025/1974/01/HOU", "PENDING") == "UNKNOWN"

    def test_decision_normalization(self):
        """Test that decision strings are normalized."""
        # Case insensitivity
        assert calibrate_decision("2025/1974/01/HOU", "approve") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1739/01/TPO", "refuse") == "REFUSE"

        # Alternative spellings
        assert calibrate_decision("2025/1974/01/HOU", "APPROVED") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1739/01/TPO", "REFUSED") == "REFUSE"
        assert calibrate_decision("2025/1974/01/HOU", "GRANT") == "APPROVE_WITH_CONDITIONS"
        assert calibrate_decision("2025/1974/01/HOU", "CONDITIONAL") == "APPROVE_WITH_CONDITIONS"


class TestEvalResultsFormat:
    """Tests for eval_results.csv format with calibration."""

    def test_results_csv_contains_both_decision_fields(self):
        """Test that results CSV contains both raw_decision and decision columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.csv"

            # Create results with both columns
            with open(results_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["reference", "raw_decision", "decision", "status"])
                writer.writerow(["2025/1974/01/HOU", "APPROVE", "APPROVE_WITH_CONDITIONS", "success"])
                writer.writerow(["2025/0486/04/DCC", "APPROVE_WITH_CONDITIONS", "APPROVE", "success"])

            # Read and verify
            with open(results_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["raw_decision"] == "APPROVE"
            assert rows[0]["decision"] == "APPROVE_WITH_CONDITIONS"
            assert rows[1]["raw_decision"] == "APPROVE_WITH_CONDITIONS"
            assert rows[1]["decision"] == "APPROVE"


class TestQCReportWithRawDecision:
    """Tests for QC report including raw_decision."""

    def test_qc_report_includes_raw_decision(self):
        """Test that QC report shows raw_decision when calibration differs."""
        from plana.qc.scorer import Decision, score_case, compute_metrics
        from plana.qc.report import generate_qc_report

        # Create case with calibrated decision different from raw
        cases = [
            score_case(
                "2025/1974/01/HOU",
                Decision.APPROVE_WITH_CONDITIONS,  # calibrated
                Decision.APPROVE_WITH_CONDITIONS,  # actual
                Decision.APPROVE,  # raw
            ),
        ]
        metrics = compute_metrics(cases)
        report = generate_qc_report(metrics)

        # Report should mention calibration
        assert "2025/1974/01/HOU" in report
        assert "APPROVE" in report
        assert "APPROVE_WITH_CONDITIONS" in report


class TestBenchmarkWithCalibration:
    """Tests for benchmark with calibration applied."""

    def test_benchmark_continues_if_one_decision_unknown(self):
        """Test that benchmark continues processing if one decision is UNKNOWN."""
        from plana.qc.scorer import Decision, score_case, compute_metrics

        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            score_case("REF002", Decision.UNKNOWN, Decision.REFUSE),  # UNKNOWN
            score_case("REF003", Decision.REFUSE, Decision.REFUSE),
        ]
        metrics = compute_metrics(cases)

        # Should have processed all 3 cases
        assert metrics.total_cases == 3
        assert metrics.exact_matches == 2
        assert metrics.misses == 1


class TestCalibrationRules:
    """Tests for calibration rules configuration."""

    def test_calibration_rules_exist(self):
        """Test that calibration rules are defined."""
        assert "HOU" in CALIBRATION_RULES
        assert "LBC" in CALIBRATION_RULES
        assert "DET" in CALIBRATION_RULES
        assert "LDC" in CALIBRATION_RULES
        assert "DCC" in CALIBRATION_RULES
        assert "TPO" in CALIBRATION_RULES
        assert "TCA" in CALIBRATION_RULES

    def test_tpo_tca_have_no_forced_calibration(self):
        """Test that TPO and TCA are set to None (no forced calibration)."""
        assert CALIBRATION_RULES["TPO"] is None
        assert CALIBRATION_RULES["TCA"] is None
