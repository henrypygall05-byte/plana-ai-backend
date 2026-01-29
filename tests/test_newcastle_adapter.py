"""Tests for Newcastle adapter and portal URL configuration.

These tests ensure that:
1. The Newcastle adapter uses the correct portal URL (portal.newcastle.gov.uk)
2. Uses SPA XHR endpoints, NOT old Idox .do endpoints
3. No references to old dead Idox endpoints (publicaccess.newcastle.gov.uk)
4. Proper handling of 406 (Idox IDX002) errors
"""

import pytest


class TestNewcastleAdapterURLs:
    """Tests for Newcastle adapter URL configuration."""

    def test_base_url_is_new_portal(self):
        """Verify BASE_URL uses portal.newcastle.gov.uk NOT publicaccess."""
        from plana.ingestion.newcastle import NewcastleAdapter

        assert "portal.newcastle.gov.uk" in NewcastleAdapter.BASE_URL
        assert "publicaccess" not in NewcastleAdapter.BASE_URL.lower()

    def test_base_url_does_not_contain_old_domain(self):
        """Ensure the old publicaccess domain is NOT used."""
        from plana.ingestion.newcastle import NewcastleAdapter

        # The old domain is DEAD and must never be used
        assert "publicaccess.newcastle.gov.uk" not in NewcastleAdapter.BASE_URL

    def test_search_endpoint_is_index_html_not_do(self):
        """Verify search endpoint uses index.html NOT .do pattern.

        Evidence from DevTools: POST to /planning/index.html with fa=search
        """
        from plana.ingestion.newcastle import NewcastleAdapter

        assert hasattr(NewcastleAdapter, "SEARCH_ENDPOINT")
        assert "index.html" in NewcastleAdapter.SEARCH_ENDPOINT
        assert ".do" not in NewcastleAdapter.SEARCH_ENDPOINT

    def test_legacy_do_endpoints_marked_do_not_use(self):
        """Verify legacy .do endpoints are marked as DO NOT USE."""
        from plana.ingestion.newcastle import NewcastleAdapter

        # The adapter should have legacy constants for documentation
        assert hasattr(NewcastleAdapter, "_LEGACY_SEARCH_DO")
        assert hasattr(NewcastleAdapter, "_LEGACY_DETAILS_DO")
        # They should contain the old .do pattern
        assert ".do" in NewcastleAdapter._LEGACY_SEARCH_DO
        assert ".do" in NewcastleAdapter._LEGACY_DETAILS_DO

    def test_legacy_url_is_marked_do_not_use(self):
        """Verify legacy URL constant is marked as DO NOT USE."""
        from plana.ingestion.newcastle import NewcastleAdapter

        # The adapter should have a reference to the legacy URL for documentation
        assert hasattr(NewcastleAdapter, "_LEGACY_BASE_URL")
        # But it should contain publicaccess (for reference only)
        assert "publicaccess" in NewcastleAdapter._LEGACY_BASE_URL

    def test_search_url_uses_xhr_endpoint(self):
        """Verify search URL uses the XHR endpoint, not .do."""
        pytest.importorskip("httpx")
        from plana.ingestion.newcastle import NewcastleAdapter

        adapter = NewcastleAdapter()
        search_url = adapter.get_search_url("2024/0001/01/DET")

        assert "portal.newcastle.gov.uk" in search_url
        assert "publicaccess" not in search_url.lower()
        # Should NOT use old .do endpoints
        assert "search.do" not in search_url
        assert "simpleSearchResults.do" not in search_url

    def test_portal_url_uses_new_domain(self):
        """Verify portal URL for display uses new domain."""
        pytest.importorskip("httpx")
        from plana.ingestion.newcastle import NewcastleAdapter

        adapter = NewcastleAdapter()
        portal_url = adapter.get_portal_url("2024/0001/01/DET")

        assert "portal.newcastle.gov.uk" in portal_url
        assert "publicaccess" not in portal_url.lower()


class TestIdoxWAFBlockDetection:
    """Tests for Idox WAF (IDX002) block detection."""

    def test_is_idox_waf_block_detects_idx002(self):
        """Test detection of Idox IDX002 error."""
        from plana.ingestion.newcastle import is_idox_waf_block

        # Typical IDX002 error page content
        response_text = """
        <html>
        <head><title>Error (IDX002)</title></head>
        <body>
        <img src="https://www.gs1uk.org/sites/default/files/partners/2021-01/Idox_Logo_RGB.gif" />
        <h1>We ran into an issue.</h1>
        <p>Error code: IDX002</p>
        <p>Please contact the Idox service desk.</p>
        </body>
        </html>
        """

        assert is_idox_waf_block(response_text, 406) is True

    def test_is_idox_waf_block_detects_idx002_on_any_status(self):
        """Test that IDX002 is detected regardless of status code.

        The Idox WAF can return any status code (200, 406, etc.) with
        the IDX002 error page, so we detect based on content.
        """
        from plana.ingestion.newcastle import is_idox_waf_block

        response_text = "IDX002 error"
        # IDX002 in text should trigger detection regardless of status
        assert is_idox_waf_block(response_text, 200) is True
        assert is_idox_waf_block(response_text, 404) is True
        assert is_idox_waf_block(response_text, 406) is True
        assert is_idox_waf_block(response_text, 500) is True

    def test_is_idox_waf_block_detects_idox_branding(self):
        """Test detection of Idox branding in error page."""
        from plana.ingestion.newcastle import is_idox_waf_block

        response_text = """
        <html>
        <body>
        <img src="idoxgroup.com/logo.png" />
        Contact support at idox.
        </body>
        </html>
        """

        assert is_idox_waf_block(response_text, 406) is True

    def test_is_idox_waf_block_returns_false_for_normal_406(self):
        """Test that generic 406 errors are not flagged as Idox blocks."""
        from plana.ingestion.newcastle import is_idox_waf_block

        response_text = "Not Acceptable: The requested resource is not available."
        assert is_idox_waf_block(response_text, 406) is False


class TestProgressLoggerIDX002Handling:
    """Tests for progress logger handling of IDX002 errors."""

    def test_suggestion_includes_idx002_info_for_idox_error(self):
        """Test that error suggestions mention IDX002 for Idox errors."""
        from plana.progress import print_live_error_suggestion

        # Create an error that mentions IDX002
        error = Exception("Portal blocked automated access (Idox IDX002)")

        suggestion = print_live_error_suggestion(406, error=error)

        assert "IDX002" in suggestion
        assert "Idox" in suggestion
        assert "browser" in suggestion.lower()

    def test_suggestion_for_generic_406(self):
        """Test suggestion for generic 406 errors."""
        from plana.progress import print_live_error_suggestion

        suggestion = print_live_error_suggestion(406)

        assert "406" in suggestion
        assert "demo mode" in suggestion.lower()

    def test_suggestion_for_403(self):
        """Test suggestion for 403 errors."""
        from plana.progress import print_live_error_suggestion

        suggestion = print_live_error_suggestion(403)

        assert "403" in suggestion
        assert "blocking" in suggestion.lower()


class TestNoOldEndpointsInCodebase:
    """Integration tests to ensure old endpoints are not used anywhere."""

    def test_newcastle_module_no_active_do_endpoints(self):
        """Ensure .do endpoints are not used in active code (only in constants)."""
        import inspect
        from plana.ingestion import newcastle

        source = inspect.getsource(newcastle)

        # Find lines with .do that are NOT comments or _LEGACY_ constants
        do_patterns = ["search.do", "applicationDetails.do", "advancedSearchResults.do", "simpleSearchResults.do"]
        active_code_lines = []

        for line in source.split("\n"):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#"):
                continue
            # Skip _LEGACY_ constant definitions
            if "_LEGACY_" in line:
                continue
            # Check for .do patterns
            for pattern in do_patterns:
                if pattern in line:
                    active_code_lines.append(line)

        # There should be no active code using .do endpoints
        assert len(active_code_lines) == 0, (
            f"Found active code using old .do endpoints: {active_code_lines}"
        )

    def test_newcastle_module_uses_search_post(self):
        """Ensure the adapter uses form POST for search."""
        import inspect
        from plana.ingestion import newcastle

        source = inspect.getsource(newcastle)

        # Should have _search_post method
        assert "_search_post" in source, "Adapter should have _search_post method for form submission"
        # Should have SEARCH_ENDPOINT constant
        assert "SEARCH_ENDPOINT" in source, "Adapter should define SEARCH_ENDPOINT constant"
        # Should have fa=search in the form data
        assert 'fa": "search"' in source or '"fa": "search"' in source or "'fa': 'search'" in source, \
            "Adapter should use fa=search action parameter"

    def test_cli_no_hardcoded_old_portal_url(self):
        """Ensure CLI doesn't have hardcoded old portal URLs."""
        import inspect
        from plana import cli

        source = inspect.getsource(cli)

        # Check for old domain
        assert "publicaccess.newcastle.gov.uk" not in source, (
            "CLI contains reference to old dead domain publicaccess.newcastle.gov.uk"
        )

        # Check for old .do endpoints in active code (not comments)
        do_patterns = ["search.do", "simpleSearchResults.do"]
        for line in source.split("\n"):
            if line.strip().startswith("#"):
                continue
            for pattern in do_patterns:
                assert pattern not in line, (
                    f"CLI contains reference to old .do endpoint: {pattern}"
                )


class TestAdapterInitialization:
    """Tests for adapter initialization."""

    def test_adapter_requires_live_deps(self):
        """Test that adapter checks for live dependencies."""
        # This test verifies the adapter import works when deps are available
        try:
            from plana.ingestion.newcastle import NewcastleAdapter
            adapter = NewcastleAdapter()
            assert adapter.council_id == "newcastle"
        except ImportError:
            # Expected if httpx/bs4 not installed
            pytest.skip("Live dependencies not installed")

    def test_adapter_council_properties(self):
        """Test adapter council identification."""
        pytest.importorskip("httpx")
        from plana.ingestion.newcastle import NewcastleAdapter

        adapter = NewcastleAdapter()
        assert adapter.council_id == "newcastle"
        assert adapter.council_name == "Newcastle City Council"
