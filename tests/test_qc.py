"""
Unit tests for Plana.AI Quality Control module.

Tests scoring rules, confusion matrix, and report generation.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from plana.qc.scorer import (
    Decision,
    MatchType,
    CaseScore,
    score_case,
    compute_metrics,
    load_gold_file,
    load_results_file,
    run_qc,
)
from plana.qc.report import generate_qc_report
from plana.qc.benchmark import (
    generate_refs_file,
    generate_gold_template,
    DEFAULT_BENCHMARK_REFS,
)


class TestDecisionParsing:
    """Tests for Decision.from_string parsing."""

    def test_parse_approve(self):
        """Test parsing APPROVE variants."""
        assert Decision.from_string("APPROVE") == Decision.APPROVE
        assert Decision.from_string("approve") == Decision.APPROVE
        assert Decision.from_string("Approved") == Decision.APPROVE
        assert Decision.from_string("GRANT") == Decision.APPROVE
        assert Decision.from_string("granted") == Decision.APPROVE

    def test_parse_approve_with_conditions(self):
        """Test parsing APPROVE_WITH_CONDITIONS variants."""
        assert Decision.from_string("APPROVE_WITH_CONDITIONS") == Decision.APPROVE_WITH_CONDITIONS
        assert Decision.from_string("approve_with_conditions") == Decision.APPROVE_WITH_CONDITIONS
        assert Decision.from_string("APPROVED_WITH_CONDITIONS") == Decision.APPROVE_WITH_CONDITIONS
        assert Decision.from_string("conditional") == Decision.APPROVE_WITH_CONDITIONS

    def test_parse_refuse(self):
        """Test parsing REFUSE variants."""
        assert Decision.from_string("REFUSE") == Decision.REFUSE
        assert Decision.from_string("refuse") == Decision.REFUSE
        assert Decision.from_string("REFUSED") == Decision.REFUSE
        assert Decision.from_string("reject") == Decision.REFUSE
        assert Decision.from_string("REJECTED") == Decision.REFUSE

    def test_parse_unknown(self):
        """Test that invalid values return UNKNOWN."""
        assert Decision.from_string("") == Decision.UNKNOWN
        assert Decision.from_string("invalid") == Decision.UNKNOWN
        assert Decision.from_string("pending") == Decision.UNKNOWN

    def test_parse_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        assert Decision.from_string("  APPROVE  ") == Decision.APPROVE
        assert Decision.from_string("\tREFUSE\n") == Decision.REFUSE


class TestScoringRules:
    """Tests for scoring rules (exact, partial, miss)."""

    def test_exact_match_approve(self):
        """Test exact match for APPROVE."""
        score = score_case("REF001", Decision.APPROVE, Decision.APPROVE)
        assert score.match_type == MatchType.EXACT
        assert score.score == 1.0

    def test_exact_match_approve_with_conditions(self):
        """Test exact match for APPROVE_WITH_CONDITIONS."""
        score = score_case("REF001", Decision.APPROVE_WITH_CONDITIONS, Decision.APPROVE_WITH_CONDITIONS)
        assert score.match_type == MatchType.EXACT
        assert score.score == 1.0

    def test_exact_match_refuse(self):
        """Test exact match for REFUSE."""
        score = score_case("REF001", Decision.REFUSE, Decision.REFUSE)
        assert score.match_type == MatchType.EXACT
        assert score.score == 1.0

    def test_partial_match_approve_to_conditions(self):
        """Test partial match APPROVE <-> APPROVE_WITH_CONDITIONS."""
        score = score_case("REF001", Decision.APPROVE, Decision.APPROVE_WITH_CONDITIONS)
        assert score.match_type == MatchType.PARTIAL
        assert score.score == 0.5

    def test_partial_match_conditions_to_approve(self):
        """Test partial match APPROVE_WITH_CONDITIONS <-> APPROVE."""
        score = score_case("REF001", Decision.APPROVE_WITH_CONDITIONS, Decision.APPROVE)
        assert score.match_type == MatchType.PARTIAL
        assert score.score == 0.5

    def test_miss_approve_vs_refuse(self):
        """Test miss: APPROVE vs REFUSE."""
        score = score_case("REF001", Decision.APPROVE, Decision.REFUSE)
        assert score.match_type == MatchType.MISS
        assert score.score == 0.0
        assert "approved but officer refused" in score.notes.lower()

    def test_miss_refuse_vs_approve(self):
        """Test miss: REFUSE vs APPROVE."""
        score = score_case("REF001", Decision.REFUSE, Decision.APPROVE)
        assert score.match_type == MatchType.MISS
        assert score.score == 0.0
        assert "refused but officer approved" in score.notes.lower()

    def test_miss_approve_conditions_vs_refuse(self):
        """Test miss: APPROVE_WITH_CONDITIONS vs REFUSE."""
        score = score_case("REF001", Decision.APPROVE_WITH_CONDITIONS, Decision.REFUSE)
        assert score.match_type == MatchType.MISS
        assert score.score == 0.0

    def test_miss_refuse_vs_approve_conditions(self):
        """Test miss: REFUSE vs APPROVE_WITH_CONDITIONS."""
        score = score_case("REF001", Decision.REFUSE, Decision.APPROVE_WITH_CONDITIONS)
        assert score.match_type == MatchType.MISS
        assert score.score == 0.0

    def test_unknown_plana_decision(self):
        """Test that UNKNOWN Plana decision is a miss."""
        score = score_case("REF001", Decision.UNKNOWN, Decision.APPROVE)
        assert score.match_type == MatchType.MISS
        assert score.score == 0.0

    def test_unknown_actual_decision(self):
        """Test that UNKNOWN actual decision is a miss."""
        score = score_case("REF001", Decision.APPROVE, Decision.UNKNOWN)
        assert score.match_type == MatchType.MISS
        assert score.score == 0.0


class TestMetricsComputation:
    """Tests for QCMetrics computation."""

    def test_empty_cases(self):
        """Test metrics with no cases."""
        metrics = compute_metrics([])
        assert metrics.total_cases == 0
        assert metrics.qc_percentage == 0.0

    def test_all_exact_matches(self):
        """Test metrics with all exact matches."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            score_case("REF002", Decision.REFUSE, Decision.REFUSE),
            score_case("REF003", Decision.APPROVE_WITH_CONDITIONS, Decision.APPROVE_WITH_CONDITIONS),
        ]
        metrics = compute_metrics(cases)
        assert metrics.total_cases == 3
        assert metrics.exact_matches == 3
        assert metrics.partial_matches == 0
        assert metrics.misses == 0
        assert metrics.qc_percentage == 100.0

    def test_all_misses(self):
        """Test metrics with all misses."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.REFUSE),
            score_case("REF002", Decision.REFUSE, Decision.APPROVE),
        ]
        metrics = compute_metrics(cases)
        assert metrics.total_cases == 2
        assert metrics.exact_matches == 0
        assert metrics.misses == 2
        assert metrics.qc_percentage == 0.0

    def test_mixed_scores(self):
        """Test metrics with mixed scores."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),  # 1.0
            score_case("REF002", Decision.APPROVE, Decision.APPROVE_WITH_CONDITIONS),  # 0.5
            score_case("REF003", Decision.APPROVE, Decision.REFUSE),  # 0.0
            score_case("REF004", Decision.REFUSE, Decision.REFUSE),  # 1.0
        ]
        metrics = compute_metrics(cases)
        assert metrics.total_cases == 4
        assert metrics.exact_matches == 2
        assert metrics.partial_matches == 1
        assert metrics.misses == 1
        assert metrics.total_score == 2.5
        assert metrics.qc_percentage == 62.5  # 2.5/4 * 100

    def test_confusion_matrix(self):
        """Test that confusion matrix is correctly computed."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            score_case("REF002", Decision.APPROVE, Decision.REFUSE),
            score_case("REF003", Decision.REFUSE, Decision.APPROVE),
            score_case("REF004", Decision.REFUSE, Decision.REFUSE),
        ]
        metrics = compute_metrics(cases)

        # Check confusion matrix values
        assert metrics.confusion_matrix["APPROVE"]["APPROVE"] == 1
        assert metrics.confusion_matrix["REFUSE"]["APPROVE"] == 1
        assert metrics.confusion_matrix["APPROVE"]["REFUSE"] == 1
        assert metrics.confusion_matrix["REFUSE"]["REFUSE"] == 1


class TestFileLoading:
    """Tests for loading gold and results files."""

    def test_load_gold_file(self):
        """Test loading gold standard CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("reference,actual_decision\n")
            f.write("REF001,APPROVE\n")
            f.write("REF002,REFUSE\n")
            f.write("REF003,APPROVE_WITH_CONDITIONS\n")
            f.flush()

            gold = load_gold_file(Path(f.name))

            assert len(gold) == 3
            assert gold["REF001"] == Decision.APPROVE
            assert gold["REF002"] == Decision.REFUSE
            assert gold["REF003"] == Decision.APPROVE_WITH_CONDITIONS

    def test_load_results_file(self):
        """Test loading Plana results CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("reference,decision,status\n")
            f.write("REF001,APPROVE,success\n")
            f.write("REF002,REFUSE,success\n")
            f.write("REF003,UNKNOWN,error\n")
            f.flush()

            results = load_results_file(Path(f.name))

            assert len(results) == 3
            assert results["REF001"] == Decision.APPROVE
            assert results["REF002"] == Decision.REFUSE
            assert results["REF003"] == Decision.UNKNOWN


class TestRunQC:
    """Tests for full QC run."""

    def test_run_qc_full_pipeline(self):
        """Test running full QC comparison."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gold_path = Path(tmpdir) / "gold.csv"
            results_path = Path(tmpdir) / "results.csv"

            # Create gold file
            with open(gold_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["reference", "actual_decision"])
                writer.writerow(["REF001", "APPROVE"])
                writer.writerow(["REF002", "REFUSE"])
                writer.writerow(["REF003", "APPROVE_WITH_CONDITIONS"])

            # Create results file
            with open(results_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["reference", "decision", "status"])
                writer.writerow(["REF001", "APPROVE", "success"])
                writer.writerow(["REF002", "APPROVE", "success"])  # Miss
                writer.writerow(["REF003", "APPROVE", "success"])  # Partial

            metrics = run_qc(gold_path, results_path)

            assert metrics.total_cases == 3
            assert metrics.exact_matches == 1
            assert metrics.partial_matches == 1
            assert metrics.misses == 1
            assert metrics.qc_percentage == pytest.approx(50.0)


class TestReportGeneration:
    """Tests for QC report generation."""

    def test_report_contains_all_references(self):
        """Test that report contains all evaluated references."""
        cases = [
            score_case("2025/0001/01/DET", Decision.APPROVE, Decision.APPROVE),
            score_case("2025/0002/01/HOU", Decision.REFUSE, Decision.APPROVE),
            score_case("2025/0003/01/LBC", Decision.APPROVE_WITH_CONDITIONS, Decision.APPROVE_WITH_CONDITIONS),
        ]
        metrics = compute_metrics(cases)
        report = generate_qc_report(metrics)

        assert "2025/0001/01/DET" in report
        assert "2025/0002/01/HOU" in report
        assert "2025/0003/01/LBC" in report

    def test_report_contains_qc_percentage(self):
        """Test that report contains QC percentage."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            score_case("REF002", Decision.REFUSE, Decision.REFUSE),
        ]
        metrics = compute_metrics(cases)
        report = generate_qc_report(metrics)

        assert "100.0%" in report
        assert "PASS" in report

    def test_report_contains_confusion_matrix(self):
        """Test that report contains confusion matrix."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            score_case("REF002", Decision.REFUSE, Decision.APPROVE),
        ]
        metrics = compute_metrics(cases)
        report = generate_qc_report(metrics)

        assert "Confusion Matrix" in report
        assert "Approve" in report

    def test_report_contains_mismatch_analysis(self):
        """Test that report contains mismatch analysis for misses."""
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.REFUSE),
        ]
        metrics = compute_metrics(cases)
        report = generate_qc_report(metrics)

        assert "Mismatch Analysis" in report
        assert "REF001" in report

    def test_report_writes_to_file(self):
        """Test that report can be written to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "qc_report.md"

            cases = [
                score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            ]
            metrics = compute_metrics(cases)
            generate_qc_report(metrics, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "Quality Control Report" in content


class TestBenchmarkHelpers:
    """Tests for benchmark helper functions."""

    def test_generate_refs_file(self):
        """Test generating refs file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            refs_path = Path(tmpdir) / "refs.txt"
            generate_refs_file(refs_path)

            assert refs_path.exists()
            content = refs_path.read_text()

            # Check all default refs are present
            for ref in DEFAULT_BENCHMARK_REFS:
                assert ref in content

    def test_generate_gold_template(self):
        """Test generating gold template CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gold_path = Path(tmpdir) / "gold.csv"
            generate_gold_template(gold_path)

            assert gold_path.exists()

            # Read and verify
            with open(gold_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == len(DEFAULT_BENCHMARK_REFS)
            for row in rows:
                assert row["reference"] in DEFAULT_BENCHMARK_REFS
                assert row["actual_decision"] == ""

    def test_benchmark_continues_if_one_case_fails(self):
        """Test that benchmark continues processing if one case fails."""
        # This is implicitly tested by the evaluate command
        # which catches exceptions and records UNKNOWN status
        cases = [
            score_case("REF001", Decision.APPROVE, Decision.APPROVE),
            score_case("REF002", Decision.UNKNOWN, Decision.REFUSE),  # Simulates failure
            score_case("REF003", Decision.REFUSE, Decision.REFUSE),
        ]
        metrics = compute_metrics(cases)

        # Should process all 3 cases
        assert metrics.total_cases == 3
        assert metrics.exact_matches == 2
        assert metrics.misses == 1


class TestDefaultBenchmarkRefs:
    """Tests for default benchmark reference set."""

    def test_default_refs_count(self):
        """Test that we have 10 default refs."""
        assert len(DEFAULT_BENCHMARK_REFS) == 10

    def test_default_refs_format(self):
        """Test that default refs have valid format."""
        for ref in DEFAULT_BENCHMARK_REFS:
            parts = ref.split("/")
            assert len(parts) == 4, f"Invalid ref format: {ref}"
            assert parts[0].isdigit(), f"Year should be numeric: {ref}"
            assert parts[1].isdigit(), f"Number should be numeric: {ref}"
