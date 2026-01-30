"""
Unit tests for Plana.AI planning assessment engine.
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestPolicyModule:
    """Tests for policy extraction and search."""

    def test_policy_search_returns_results(self):
        """Test that policy search returns results for demo application."""
        from plana.policy import PolicySearch

        search = PolicySearch()
        results = search.retrieve_relevant_policies(
            proposal="Extension and conversion to residential",
            constraints=["Conservation Area", "Listed Building"],
            application_type="Full Planning",
            address="Grainger Street, Newcastle",
        )

        assert len(results) > 0
        assert all(hasattr(r, "doc_id") for r in results)
        assert all(hasattr(r, "page") for r in results)

    def test_policy_search_returns_citations_from_all_documents(self):
        """Test that policy search returns citations from NPPF, CSUCP, and DAP."""
        from plana.policy import PolicySearch

        search = PolicySearch()
        results = search.retrieve_relevant_policies(
            proposal="Extension and conversion to residential",
            constraints=["Conservation Area"],
            application_type="Full Planning",
            address="Grainger Street",
        )

        doc_ids = set(r.doc_id for r in results)
        assert "NPPF" in doc_ids, "Should include NPPF policies"
        assert "CSUCP" in doc_ids or "DAP" in doc_ids, "Should include local policies"

    def test_policy_excerpt_has_page_number(self):
        """Test that policy excerpts include page numbers."""
        from plana.policy import PolicySearch

        search = PolicySearch()
        results = search.retrieve_relevant_policies(
            proposal="Heritage impact",
            constraints=["Conservation Area"],
            application_type="Listed Building Consent",
            address="Newcastle",
        )

        assert len(results) > 0
        for result in results:
            assert isinstance(result.page, int)
            assert result.page > 0

    def test_policy_extractor_caching(self):
        """Test that policy extractor creates cache directory."""
        from plana.policy import PolicyExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            extractor = PolicyExtractor(cache_dir=cache_dir)

            # Cache directory should be created
            assert cache_dir.exists()

            # Extract should return data (demo mode)
            data = extractor.extract_pdf("NPPF")
            assert data["doc_id"] == "NPPF"


class TestSimilarityModule:
    """Tests for similarity search."""

    def test_similarity_search_returns_cases(self):
        """Test that similarity search returns similar cases."""
        from plana.similarity import SimilaritySearch

        search = SimilaritySearch()
        results = search.find_similar_cases(
            proposal="Extension and conversion to residential with external alterations",
            constraints=["Grainger Town Conservation Area", "Adjacent to listed buildings"],
            address="Grainger Street, Newcastle",
            application_type="Full Planning",
        )

        assert len(results) > 0
        assert all(hasattr(r, "reference") for r in results)
        assert all(hasattr(r, "similarity_score") for r in results)

    def test_similar_cases_have_decision(self):
        """Test that similar cases include decision information."""
        from plana.similarity import SimilaritySearch

        search = SimilaritySearch()
        results = search.find_similar_cases(
            proposal="Shop front alterations",
            constraints=["Conservation Area"],
            address="Newcastle",
            application_type="Full Planning",
        )

        assert len(results) > 0
        for case in results:
            assert case.decision in ["APPROVED", "REFUSED"]
            assert case.decision_date is not None


class TestDocumentsModule:
    """Tests for documents management."""

    def test_document_manager_lists_documents(self):
        """Test that document manager returns documents for demo application."""
        from plana.documents import DocumentManager

        manager = DocumentManager()
        documents = manager.list_documents("2024/0930/01/DET")

        assert len(documents) > 0
        assert all(hasattr(d, "title") for d in documents)
        assert all(hasattr(d, "format") for d in documents)

    def test_document_summary(self):
        """Test that document summary returns correct counts."""
        from plana.documents import DocumentManager

        manager = DocumentManager()
        summary = manager.get_document_summary("2024/0930/01/DET")

        assert summary["total_documents"] > 0
        assert "document_types" in summary
        assert "total_size_kb" in summary


class TestReportGenerator:
    """Tests for report generation."""

    def test_report_generator_produces_output(self):
        """Test that report generator creates a report."""
        from plana.report.generator import ReportGenerator, ApplicationData

        generator = ReportGenerator()
        application = ApplicationData(
            reference="2024/0930/01/DET",
            address="T J Hughes, Grainger Street, Newcastle",
            proposal="Extension and conversion",
            application_type="Full Planning",
            constraints=["Conservation Area"],
        )

        report = generator.generate_report(application)

        assert len(report) > 0
        assert "Planning Assessment Report" in report

    def test_report_contains_required_sections(self):
        """Test that report contains all required sections."""
        from plana.report.generator import ReportGenerator, ApplicationData

        generator = ReportGenerator()
        application = ApplicationData(
            reference="2024/0930/01/DET",
            address="Test Address",
            proposal="Test Proposal",
            application_type="Full Planning",
            constraints=["Conservation Area"],
        )

        report = generator.generate_report(application)

        # Check for required sections
        assert "## 1. Executive Summary" in report
        assert "## 5. Policy Context" in report
        assert "## 7. Similar Cases" in report
        assert "## 9. Recommendation" in report
        assert "## Appendix: Evidence Citations" in report

    def test_report_writes_to_file(self):
        """Test that report can be written to a file."""
        from plana.report.generator import ReportGenerator, ApplicationData

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"

            generator = ReportGenerator()
            application = ApplicationData(
                reference="2024/0930/01/DET",
                address="Test Address",
                proposal="Test Proposal",
                application_type="Full Planning",
                constraints=["Conservation Area"],
            )

            generator.generate_report(application, output_path=output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert len(content) > 0
            assert "Planning Assessment Report" in content


class TestCLI:
    """Tests for CLI commands."""

    def test_process_with_output_creates_file(self):
        """Test that plana process --output creates a report file."""
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"

            result = subprocess.run(
                ["plana", "process", "2024/0930/01/DET", "--output", str(output_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert output_path.exists()

            content = output_path.read_text()
            assert "Policy Context" in content
            assert "Similar Cases" in content
            assert "Recommendation" in content

    def test_report_has_minimum_policy_citations(self):
        """Test that generated report has at least 5 policy citations."""
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"

            subprocess.run(
                ["plana", "process", "2024/0930/01/DET", "--output", str(output_path)],
                capture_output=True,
                text=True,
            )

            content = output_path.read_text()

            # Count page citations (p.XX format)
            import re
            citations = re.findall(r"p\.\d+", content)

            assert len(citations) >= 5, f"Expected at least 5 citations, found {len(citations)}"


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_for_demo_reference(self):
        """Test the full pipeline for the demo reference."""
        from plana.report.generator import ReportGenerator, ApplicationData
        from plana.policy import PolicySearch
        from plana.similarity import SimilaritySearch
        from plana.documents import DocumentManager

        # Get policies
        policy_search = PolicySearch()
        policies = policy_search.retrieve_relevant_policies(
            proposal="Extension and conversion to residential",
            constraints=["Grainger Town Conservation Area", "Adjacent to Grade II listed buildings"],
            application_type="Full Planning",
            address="T J Hughes, Grainger Street",
        )

        # Get similar cases
        similarity_search = SimilaritySearch()
        similar_cases = similarity_search.find_similar_cases(
            proposal="Extension and conversion to residential",
            constraints=["Grainger Town Conservation Area"],
        )

        # Get documents
        doc_manager = DocumentManager()
        documents = doc_manager.list_documents("2024/0930/01/DET")

        # Generate report
        generator = ReportGenerator()
        application = ApplicationData(
            reference="2024/0930/01/DET",
            address="T J Hughes, 86-92 Grainger Street, Newcastle Upon Tyne, NE1 5JQ",
            proposal="Erection of two storey rear/roof extension and conversion of upper floors to residential",
            application_type="Full Planning",
            constraints=["Grainger Town Conservation Area", "Adjacent to Grade II listed buildings"],
        )
        report = generator.generate_report(application)

        # Verify all components worked
        assert len(policies) >= 5, "Should have at least 5 relevant policies"
        assert len(similar_cases) >= 1, "Should have at least 1 similar case"
        assert len(documents) >= 1, "Should have at least 1 document"
        assert len(report) > 1000, "Report should be substantial"

        # Verify citations from all documents
        doc_ids = set(p.doc_id for p in policies)
        assert "NPPF" in doc_ids
        assert "DAP" in doc_ids or "CSUCP" in doc_ids
