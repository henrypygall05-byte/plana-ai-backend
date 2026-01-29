"""
Unit tests for the progress logger module.

Tests step-by-step progress output with timing and error handling.
"""

import io
import pytest
from unittest.mock import patch

from plana.progress import ProgressLogger, StepResult, StepStatus
from plana.progress.logger import (
    LIVE_PIPELINE_STEPS,
    DEMO_PIPELINE_STEPS,
    is_dns_failure,
    print_dns_failure_message,
    print_live_error_suggestion,
)


class TestProgressLogger:
    """Tests for ProgressLogger class."""

    def test_logger_initializes_with_live_steps(self):
        """Test that live mode uses correct step count."""
        logger = ProgressLogger(mode="live", verbose=False)
        assert logger.mode == "live"
        assert logger.steps == LIVE_PIPELINE_STEPS
        assert logger.total_steps == len(LIVE_PIPELINE_STEPS)

    def test_logger_initializes_with_demo_steps(self):
        """Test that demo mode uses correct step count."""
        logger = ProgressLogger(mode="demo", verbose=False)
        assert logger.mode == "demo"
        assert logger.steps == DEMO_PIPELINE_STEPS
        assert logger.total_steps == len(DEMO_PIPELINE_STEPS)

    def test_start_pipeline_sets_metadata(self):
        """Test that start_pipeline sets reference, council, run_id."""
        output = io.StringIO()
        logger = ProgressLogger(mode="demo", verbose=True, output_stream=output)

        logger.start_pipeline("2024/0930/01/DET", "newcastle", "test_run_001")

        assert logger.reference == "2024/0930/01/DET"
        assert logger.council == "newcastle"
        assert logger.run_id == "test_run_001"

    def test_start_pipeline_prints_header(self):
        """Test that start_pipeline prints header with mode, council, reference."""
        output = io.StringIO()
        logger = ProgressLogger(mode="live", verbose=True, output_stream=output)

        logger.start_pipeline("2024/0930/01/DET", "newcastle")

        result = output.getvalue()
        assert "Plana.AI" in result
        assert "LIVE" in result
        assert "Newcastle" in result
        assert "2024/0930/01/DET" in result

    def test_start_step_prints_step_number(self):
        """Test that start_step prints step number in [N/M] format."""
        output = io.StringIO()
        logger = ProgressLogger(mode="demo", verbose=True, output_stream=output)
        logger.start_pipeline("REF001", "newcastle")

        # Clear buffer after header
        output.truncate(0)
        output.seek(0)

        logger.start_step("init", "Initialize runtime")

        result = output.getvalue()
        assert "[0/" in result
        assert "Initialize runtime" in result

    def test_start_step_prints_url(self):
        """Test that start_step prints URL when provided."""
        output = io.StringIO()
        logger = ProgressLogger(mode="live", verbose=True, output_stream=output)
        logger.start_pipeline("REF001", "newcastle")

        output.truncate(0)
        output.seek(0)

        logger.start_step("fetch_metadata", "Fetch metadata", url="https://example.com/api")

        result = output.getvalue()
        assert "https://example.com/api" in result
        assert "URL:" in result

    def test_complete_step_returns_result(self):
        """Test that complete_step returns StepResult with timing."""
        logger = ProgressLogger(mode="demo", verbose=False)
        logger.start_pipeline("REF001", "newcastle")
        logger.start_step("init")

        result = logger.complete_step("Done", {"key": "value"})

        assert isinstance(result, StepResult)
        assert result.status == StepStatus.SUCCESS
        assert result.message == "Done"
        assert result.duration_ms >= 0
        assert result.details == {"key": "value"}

    def test_fail_step_returns_error_result(self):
        """Test that fail_step returns StepResult with error info."""
        logger = ProgressLogger(mode="live", verbose=False)
        logger.start_pipeline("REF001", "newcastle")
        logger.start_step("fetch_metadata")

        result = logger.fail_step(
            error_message="Connection failed",
            url="https://example.com",
            status_code=403,
            suggestion="Try again later",
        )

        assert result.status == StepStatus.FAILED
        assert result.message == "Connection failed"
        assert result.error_url == "https://example.com"
        assert result.error_status_code == 403
        assert result.error_suggestion == "Try again later"

    def test_fail_step_prints_error_details(self):
        """Test that fail_step prints URL and status code without traceback."""
        output = io.StringIO()
        logger = ProgressLogger(mode="live", verbose=True, output_stream=output)
        logger.start_pipeline("REF001", "newcastle")
        logger.start_step("fetch_metadata")

        logger.fail_step(
            error_message="403 Forbidden",
            url="https://portal.example.com/api",
            status_code=403,
        )

        result = output.getvalue()
        assert "FAILED" in result
        assert "403" in result
        assert "https://portal.example.com/api" in result
        assert "PIPELINE ERROR" in result
        # Should NOT contain traceback
        assert "Traceback" not in result

    def test_skip_step_returns_skipped_result(self):
        """Test that skip_step returns StepResult with skipped status."""
        logger = ProgressLogger(mode="demo", verbose=False)
        logger.start_pipeline("REF001", "newcastle")
        logger.start_step("find_similar")

        result = logger.skip_step("No similar cases available")

        assert result.status == StepStatus.SKIPPED
        assert "No similar cases" in result.message

    def test_complete_pipeline_returns_summary(self):
        """Test that complete_pipeline returns summary dict."""
        logger = ProgressLogger(mode="demo", verbose=False)
        logger.start_pipeline("REF001", "newcastle", run_id="test_001")

        result = logger.complete_pipeline(success=True, summary={"decision": "APPROVE"})

        assert result["run_id"] == "test_001"
        assert result["reference"] == "REF001"
        assert result["success"] is True
        assert result["decision"] == "APPROVE"
        assert "total_duration_ms" in result

    def test_step_results_accumulated(self):
        """Test that step results are accumulated in step_results list."""
        logger = ProgressLogger(mode="demo", verbose=False)
        logger.start_pipeline("REF001", "newcastle")

        logger.start_step("init")
        logger.complete_step("Done")

        logger.start_step("load_fixture")
        logger.complete_step("Loaded")

        assert len(logger.step_results) == 2
        assert logger.step_results[0].step_name == "init"
        assert logger.step_results[1].step_name == "load_fixture"


class TestLiveErrorSuggestions:
    """Tests for error suggestion generation."""

    def test_403_suggestion_mentions_portal_blocking(self):
        """Test that 403 suggestion mentions portal blocking."""
        suggestion = print_live_error_suggestion(403)
        assert "403" in suggestion
        assert "blocking" in suggestion.lower()
        assert "demo mode" in suggestion.lower()

    def test_404_suggestion_mentions_not_found(self):
        """Test that 404 suggestion mentions not found."""
        suggestion = print_live_error_suggestion(404)
        assert "404" in suggestion
        assert "not found" in suggestion.lower()
        assert "reference" in suggestion.lower()

    def test_429_suggestion_mentions_rate_limit(self):
        """Test that 429 suggestion mentions rate limiting."""
        suggestion = print_live_error_suggestion(429)
        assert "429" in suggestion
        assert "rate" in suggestion.lower()

    def test_500_suggestion_mentions_server_error(self):
        """Test that 500+ suggestions mention server error."""
        suggestion = print_live_error_suggestion(500)
        assert "server" in suggestion.lower()

        suggestion = print_live_error_suggestion(503)
        assert "server" in suggestion.lower()

    def test_none_suggestion_mentions_connection(self):
        """Test that no status code suggests connection issue."""
        suggestion = print_live_error_suggestion(None)
        assert "connection" in suggestion.lower()


class TestProgressOutputFormat:
    """Tests for progress output format requirements."""

    def test_live_mode_has_8_steps(self):
        """Test that live mode has exactly 8+1 steps (0-8)."""
        # Steps 0-8 = 9 steps total
        assert len(LIVE_PIPELINE_STEPS) == 9

    def test_demo_mode_has_7_steps(self):
        """Test that demo mode has correct step count."""
        assert len(DEMO_PIPELINE_STEPS) == 7

    def test_live_steps_include_required_operations(self):
        """Test that live steps include all required operations."""
        step_names = [step[0] for step in LIVE_PIPELINE_STEPS]

        assert "init" in step_names
        assert "fetch_metadata" in step_names
        assert "fetch_documents" in step_names
        assert "download_documents" in step_names
        assert "persist_data" in step_names
        assert "retrieve_policies" in step_names
        assert "find_similar" in step_names
        assert "generate_report" in step_names
        assert "save_outputs" in step_names

    def test_step_descriptions_are_meaningful(self):
        """Test that step descriptions are non-empty and descriptive."""
        for name, desc in LIVE_PIPELINE_STEPS:
            assert len(desc) > 5, f"Step {name} description too short"
            assert name in desc.lower() or len(desc) > 10

    def test_progress_logger_prints_timing(self):
        """Test that step completion includes timing in milliseconds."""
        output = io.StringIO()
        logger = ProgressLogger(mode="demo", verbose=True, output_stream=output)
        logger.start_pipeline("REF001", "newcastle")

        logger.start_step("init")
        logger.complete_step("Done")

        result = output.getvalue()
        assert "ms)" in result  # Timing format: "Done (Xms)"


class TestDocumentProgressOutput:
    """Tests for document download progress output."""

    def test_print_document_progress_shows_counts(self):
        """Test that document progress shows succeeded/skipped/failed counts."""
        output = io.StringIO()
        logger = ProgressLogger(mode="live", verbose=True, output_stream=output)
        logger.start_pipeline("REF001", "newcastle")

        logger.print_document_progress(
            succeeded=10,
            skipped=2,
            failed=1,
            retries=3,
            deduped=2,
        )

        result = output.getvalue()
        assert "10 succeeded" in result
        assert "2 skipped" in result
        assert "1 failed" in result

    def test_print_document_progress_omits_zero_counts(self):
        """Test that zero counts are omitted from output."""
        output = io.StringIO()
        logger = ProgressLogger(mode="live", verbose=True, output_stream=output)
        logger.start_pipeline("REF001", "newcastle")

        logger.print_document_progress(
            succeeded=10,
            skipped=0,
            failed=0,
            retries=0,
            deduped=0,
        )

        result = output.getvalue()
        assert "10 succeeded" in result
        assert "skipped" not in result
        assert "failed" not in result


class TestDNSFailureDetection:
    """Tests for DNS failure detection and handling."""

    def test_is_dns_failure_detects_could_not_resolve(self):
        """Test that 'could not resolve host' is detected as DNS failure."""
        error = Exception("Could not resolve host: publicaccess.newcastle.gov.uk")
        assert is_dns_failure(error) is True

    def test_is_dns_failure_detects_name_not_known(self):
        """Test that 'Name or service not known' is detected as DNS failure."""
        error = Exception("Name or service not known")
        assert is_dns_failure(error) is True

    def test_is_dns_failure_detects_nxdomain(self):
        """Test that NXDOMAIN errors are detected."""
        error = Exception("NXDOMAIN: publicaccess.newcastle.gov.uk")
        assert is_dns_failure(error) is True

    def test_is_dns_failure_detects_errno_8(self):
        """Test that [Errno 8] is detected as DNS failure."""
        error = Exception("[Errno 8] nodename nor servname provided")
        assert is_dns_failure(error) is True

    def test_is_dns_failure_detects_getaddrinfo(self):
        """Test that getaddrinfo failures are detected."""
        error = Exception("getaddrinfo failed")
        assert is_dns_failure(error) is True

    def test_is_dns_failure_detects_gaierror_in_message(self):
        """Test that gaierror in message is detected."""
        error = Exception("socket.gaierror: [Errno -2]")
        assert is_dns_failure(error) is True

    def test_is_dns_failure_returns_false_for_403(self):
        """Test that HTTP 403 is not a DNS failure."""
        error = Exception("403 Forbidden")
        assert is_dns_failure(error) is False

    def test_is_dns_failure_returns_false_for_404(self):
        """Test that HTTP 404 is not a DNS failure."""
        error = Exception("404 Not Found")
        assert is_dns_failure(error) is False

    def test_is_dns_failure_returns_false_for_timeout(self):
        """Test that timeout is not a DNS failure."""
        error = Exception("Connection timed out")
        assert is_dns_failure(error) is False

    def test_is_dns_failure_checks_nested_cause(self):
        """Test that nested __cause__ is checked for DNS failure."""
        inner = Exception("Name or service not known")
        outer = Exception("Connection failed")
        outer.__cause__ = inner
        assert is_dns_failure(outer) is True

    def test_is_dns_failure_checks_nested_context(self):
        """Test that nested __context__ is checked for DNS failure."""
        inner = Exception("Could not resolve host")
        outer = Exception("Request failed")
        outer.__context__ = inner
        assert is_dns_failure(outer) is True


class TestDNSFailureMessage:
    """Tests for DNS failure message formatting."""

    def test_dns_message_mentions_dns_failure(self):
        """Test that DNS message mentions DNS failure."""
        message = print_dns_failure_message("https://example.com")
        assert "DNS" in message

    def test_dns_message_says_not_plana_bug(self):
        """Test that DNS message says it's not a Plana bug."""
        message = print_dns_failure_message("https://example.com")
        assert "not a Plana bug" in message

    def test_dns_message_suggests_browser_check(self):
        """Test that DNS message suggests trying browser."""
        message = print_dns_failure_message("https://example.com")
        assert "browser" in message.lower()

    def test_dns_message_suggests_different_network(self):
        """Test that DNS message suggests different network."""
        message = print_dns_failure_message("https://example.com")
        assert "network" in message.lower()

    def test_dns_message_suggests_dns_change(self):
        """Test that DNS message suggests changing DNS servers."""
        message = print_dns_failure_message("https://example.com")
        assert "1.1.1.1" in message or "8.8.8.8" in message

    def test_dns_message_confirms_plana_working(self):
        """Test that DNS message confirms LIVE mode is working."""
        message = print_dns_failure_message("https://example.com")
        assert "LIVE mode is working correctly" in message

    def test_dns_message_no_traceback(self):
        """Test that DNS message doesn't include traceback keywords."""
        message = print_dns_failure_message("https://example.com")
        assert "Traceback" not in message
        assert "File \"" not in message
        assert "line " not in message


class TestDNSFailureSuggestion:
    """Tests for DNS failure integration with error suggestion."""

    def test_suggestion_detects_dns_error(self):
        """Test that print_live_error_suggestion detects DNS errors."""
        error = Exception("Could not resolve host: example.com")
        suggestion = print_live_error_suggestion(None, error=error)
        assert "DNS" in suggestion
        assert "not a Plana bug" in suggestion

    def test_suggestion_prioritizes_dns_over_status_code(self):
        """Test that DNS detection takes priority over status code."""
        error = Exception("Could not resolve host")
        suggestion = print_live_error_suggestion(403, error=error)
        # Should show DNS message, not 403 message
        assert "not a Plana bug" in suggestion
        assert "LIVE mode is working correctly" in suggestion
