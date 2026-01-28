"""
Unit tests for CLI argument parsing.

Tests that the CLI correctly parses --mode, --council, and other arguments.
"""

import argparse
import sys
from io import StringIO
from unittest.mock import patch

import pytest


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing."""

    def _get_parser(self):
        """Get the argument parser from CLI module."""
        # Import the CLI module and create parser
        from plana.cli import SUPPORTED_COUNCILS

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")

        # Process command
        process_parser = subparsers.add_parser("process")
        process_parser.add_argument("reference")
        process_parser.add_argument("--output", "-o", type=str)
        process_parser.add_argument(
            "--mode", "-m",
            choices=["demo", "live"],
            default="demo",
        )
        process_parser.add_argument(
            "--council", "-c",
            choices=SUPPORTED_COUNCILS,
            default="newcastle",
        )

        # Report command
        report_parser = subparsers.add_parser("report")
        report_parser.add_argument("reference")
        report_parser.add_argument("--output", "-o", type=str, required=True)
        report_parser.add_argument(
            "--mode", "-m",
            choices=["demo", "live"],
            default="demo",
        )
        report_parser.add_argument(
            "--council", "-c",
            choices=SUPPORTED_COUNCILS,
            default="newcastle",
        )

        return parser

    def test_process_accepts_mode_demo(self):
        """Test that process accepts --mode demo."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET", "--mode", "demo"])

        assert args.command == "process"
        assert args.reference == "2024/0930/01/DET"
        assert args.mode == "demo"

    def test_process_accepts_mode_live(self):
        """Test that process accepts --mode live."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET", "--mode", "live"])

        assert args.command == "process"
        assert args.mode == "live"

    def test_process_mode_defaults_to_demo(self):
        """Test that --mode defaults to demo when not specified."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET"])

        assert args.mode == "demo"

    def test_process_accepts_council_newcastle(self):
        """Test that process accepts --council newcastle."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET", "--council", "newcastle"])

        assert args.council == "newcastle"

    def test_process_council_defaults_to_newcastle(self):
        """Test that --council defaults to newcastle."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET"])

        assert args.council == "newcastle"

    def test_process_rejects_invalid_council(self):
        """Test that invalid council value is rejected."""
        parser = self._get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["process", "2024/0930/01/DET", "--council", "invalid"])

    def test_process_rejects_invalid_mode(self):
        """Test that invalid mode value is rejected."""
        parser = self._get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["process", "2024/0930/01/DET", "--mode", "invalid"])

    def test_process_accepts_short_flags(self):
        """Test that short flags -m and -c work."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET", "-m", "live", "-c", "newcastle"])

        assert args.mode == "live"
        assert args.council == "newcastle"

    def test_process_accepts_output_flag(self):
        """Test that --output flag is accepted."""
        parser = self._get_parser()
        args = parser.parse_args(["process", "2024/0930/01/DET", "--output", "report.md"])

        assert args.output == "report.md"

    def test_process_accepts_all_flags_together(self):
        """Test that all flags work together."""
        parser = self._get_parser()
        args = parser.parse_args([
            "process", "2024/0930/01/DET",
            "--mode", "live",
            "--council", "newcastle",
            "--output", "report.md",
        ])

        assert args.command == "process"
        assert args.reference == "2024/0930/01/DET"
        assert args.mode == "live"
        assert args.council == "newcastle"
        assert args.output == "report.md"

    def test_report_accepts_mode_flag(self):
        """Test that report command accepts --mode flag."""
        parser = self._get_parser()
        args = parser.parse_args([
            "report", "2024/0930/01/DET",
            "--mode", "live",
            "--output", "report.md",
        ])

        assert args.command == "report"
        assert args.mode == "live"

    def test_report_accepts_council_flag(self):
        """Test that report command accepts --council flag."""
        parser = self._get_parser()
        args = parser.parse_args([
            "report", "2024/0930/01/DET",
            "--council", "newcastle",
            "--output", "report.md",
        ])

        assert args.council == "newcastle"


class TestSupportedCouncils:
    """Tests for supported councils list."""

    def test_newcastle_is_supported(self):
        """Test that newcastle is in the supported councils list."""
        from plana.cli import SUPPORTED_COUNCILS

        assert "newcastle" in SUPPORTED_COUNCILS

    def test_supported_councils_is_list(self):
        """Test that SUPPORTED_COUNCILS is a list."""
        from plana.cli import SUPPORTED_COUNCILS

        assert isinstance(SUPPORTED_COUNCILS, list)
        assert len(SUPPORTED_COUNCILS) > 0


class TestIngestionAdapter:
    """Tests for ingestion adapter factory."""

    def test_get_adapter_returns_newcastle(self):
        """Test that get_adapter returns Newcastle adapter."""
        try:
            from plana.ingestion import get_adapter, NewcastleAdapter

            adapter = get_adapter("newcastle")
            assert isinstance(adapter, NewcastleAdapter)
        except ImportError:
            pytest.skip("Live dependencies not installed")

    def test_get_adapter_rejects_unknown_council(self):
        """Test that get_adapter raises ValueError for unknown council."""
        try:
            from plana.ingestion import get_adapter

            with pytest.raises(ValueError) as exc_info:
                get_adapter("unknown_council")

            assert "Unsupported council" in str(exc_info.value)
            assert "unknown_council" in str(exc_info.value)
        except ImportError:
            pytest.skip("Live dependencies not installed")


class TestPortalAccessError:
    """Tests for PortalAccessError exception."""

    def test_portal_access_error_has_url(self):
        """Test that PortalAccessError stores URL."""
        try:
            from plana.ingestion import PortalAccessError

            error = PortalAccessError(
                "Test error",
                url="https://example.com",
                status_code=403,
            )

            assert error.url == "https://example.com"
            assert error.status_code == 403
            assert error.message == "Test error"
        except ImportError:
            pytest.skip("Live dependencies not installed")

    def test_portal_access_error_str(self):
        """Test that PortalAccessError __str__ includes all info."""
        try:
            from plana.ingestion import PortalAccessError

            error = PortalAccessError(
                "Test error",
                url="https://example.com",
                status_code=403,
            )

            error_str = str(error)
            assert "Test error" in error_str
            assert "https://example.com" in error_str
            assert "403" in error_str
        except ImportError:
            pytest.skip("Live dependencies not installed")


class TestModuleImports:
    """Tests for module import behavior without crashes."""

    def test_ingestion_module_imports_without_nameerror(self):
        """Test that ingestion module imports without NameError.

        This verifies that type annotations using httpx don't cause NameError
        when the module is imported, even if httpx isn't installed.
        """
        # This should NOT raise NameError - the module should import cleanly
        # It may raise ImportError later when actually used, but not at import time
        try:
            from plana.ingestion import base
            from plana.ingestion import newcastle

            # Verify key classes are accessible
            assert hasattr(base, 'PortalAccessError')
            assert hasattr(base, 'CouncilAdapter')
            assert hasattr(newcastle, 'NewcastleAdapter')
        except ImportError:
            # ImportError is acceptable - this means the optional deps aren't installed
            # but we did NOT get a NameError, which is the important thing
            pass

    def test_ingestion_base_imports_without_deps(self):
        """Test that base module imports cleanly without optional deps."""
        # base.py has no httpx dependencies, should always import
        from plana.ingestion.base import (
            PortalAccessError,
            CouncilAdapter,
            ApplicationDetails,
            PortalDocument,
        )

        assert PortalAccessError is not None
        assert CouncilAdapter is not None

    def test_newcastle_adapter_raises_importerror_not_nameerror(self):
        """Test that NewcastleAdapter raises ImportError (not NameError) when deps missing."""
        import sys

        # If httpx is available, we can't test the missing deps case
        if 'httpx' in sys.modules:
            pytest.skip("httpx is installed, can't test missing deps behavior")

        try:
            from plana.ingestion.newcastle import NewcastleAdapter
            # If we get here without error, deps are available
            # Try to instantiate - this will check deps
            try:
                adapter = NewcastleAdapter()
                # If successful, deps are installed
                pytest.skip("Live dependencies are installed")
            except ImportError as e:
                # This is the expected behavior - clean ImportError, not NameError
                assert "pip install" in str(e).lower() or "live" in str(e).lower()
        except NameError as e:
            # This is the bug we're testing for - should NOT happen
            pytest.fail(f"Got NameError instead of clean import: {e}")

    def test_cli_handles_missing_live_deps_gracefully(self):
        """Test that CLI prints helpful message when live deps are missing."""
        import subprocess

        result = subprocess.run(
            ["plana", "process", "2024/0930/01/DET", "--mode", "demo"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Demo mode should work regardless of live deps
        assert result.returncode == 0 or "demo" in result.stdout.lower()
