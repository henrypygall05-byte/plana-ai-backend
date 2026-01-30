"""Tests for prompt loading and versioning."""

import json
import pytest
from pathlib import Path


class TestPromptLoader:
    """Tests for prompt loading functionality."""

    def test_case_officer_prompt_exists(self):
        """Test that case officer prompt can be loaded."""
        from plana.prompts import get_case_officer_prompt

        prompt = get_case_officer_prompt()

        assert prompt is not None
        assert prompt.name == "case_officer"
        assert prompt.version == "1.0.0"
        assert len(prompt.content) > 1000  # Should be substantial
        assert "Plana Case Officer" in prompt.content

    def test_evaluator_prompt_exists(self):
        """Test that evaluator prompt can be loaded."""
        from plana.prompts import get_evaluator_prompt

        prompt = get_evaluator_prompt()

        assert prompt is not None
        assert prompt.name == "evaluator"
        assert prompt.version == "1.0.0"
        assert "Evaluator" in prompt.content

    def test_case_input_schema_valid(self):
        """Test that CASE_INPUT schema is valid JSON Schema."""
        from plana.prompts.loader import get_case_input_schema

        schema = get_case_input_schema()

        assert "$schema" in schema
        assert schema["title"] == "CASE_INPUT"
        assert "properties" in schema
        assert "run_id" in schema["properties"]
        assert "council_id" in schema["properties"]
        assert "reference" in schema["properties"]

    def test_case_output_schema_valid(self):
        """Test that CASE_OUTPUT schema is valid JSON Schema."""
        from plana.prompts.loader import get_case_output_schema

        schema = get_case_output_schema()

        assert "$schema" in schema
        assert schema["title"] == "CASE_OUTPUT"
        assert "properties" in schema
        assert "meta" in schema["properties"]
        assert "pipeline_audit" in schema["properties"]
        assert "report_markdown" in schema["properties"]

    def test_prompt_version_constants(self):
        """Test that version constants are defined."""
        from plana.prompts.loader import DEFAULT_PROMPT_VERSION, DEFAULT_SCHEMA_VERSION

        assert DEFAULT_PROMPT_VERSION == "1.0.0"
        assert DEFAULT_SCHEMA_VERSION == "1.0.0"


class TestCaseInputBuilder:
    """Tests for CASE_INPUT builder."""

    def test_builder_basic(self):
        """Test basic builder functionality."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder(
            run_id="test_123",
            council_id="newcastle",
            reference="2024/0001/01/DET",
            mode="demo",
        )

        case_input = builder.build()

        assert case_input["run_id"] == "test_123"
        assert case_input["council_id"] == "newcastle"
        assert case_input["reference"] == "2024/0001/01/DET"
        assert case_input["mode"] == "demo"

    def test_builder_application(self):
        """Test setting application metadata."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
        builder.set_application(
            address="123 Test Street",
            proposal="Build extension",
            application_type="Full Planning",
        )

        case_input = builder.build()

        assert case_input["application"]["address"] == "123 Test Street"
        assert case_input["application"]["proposal"] == "Build extension"
        assert case_input["application"]["application_type"] == "Full Planning"

    def test_builder_constraints(self):
        """Test adding constraints."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
        builder.add_constraint(
            constraint_type="conservation_area",
            name="Grainger Town Conservation Area",
            source="council GIS",
        )
        builder.add_constraint(
            constraint_type="listed_building",
            name="Grade II Listed",
        )

        case_input = builder.build()

        assert len(case_input["constraints"]) == 2
        assert case_input["constraints"][0]["constraint_type"] == "conservation_area"
        assert case_input["constraints"][1]["name"] == "Grade II Listed"

    def test_builder_documents(self):
        """Test adding documents."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
        builder.add_document(
            doc_id="doc_001",
            document_title="Application Form",
            document_type="application_form",
            hash="abc123",
            extracted_text=[
                {"chunk_id": "c1", "page": 1, "text": "Sample text"}
            ],
        )

        case_input = builder.build()

        assert len(case_input["documents"]) == 1
        assert case_input["documents"][0]["doc_id"] == "doc_001"
        assert len(case_input["documents"][0]["extracted_text"]) == 1

    def test_builder_policies(self):
        """Test adding policies."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
        builder.add_policy(
            policy_id="NPPF-199",
            policy_name="Heritage Conservation",
            policy_source="NPPF",
            text="Great weight should be given...",
            score=0.85,
        )

        case_input = builder.build()

        assert len(case_input["policies"]) == 1
        assert case_input["policies"][0]["policy_id"] == "NPPF-199"
        assert case_input["policies"][0]["score"] == 0.85

    def test_builder_similar_cases(self):
        """Test adding similar cases."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
        builder.add_similar_case(
            case_id="case_001",
            council_id="newcastle",
            reference="2023/0500/01/DET",
            address="456 Other Street",
            proposal="Similar extension",
            outcome="APPROVE_WITH_CONDITIONS",
            similarity_score=0.78,
            reason_features=["same_ward", "similar_type"],
        )

        case_input = builder.build()

        assert len(case_input["similar_cases"]) == 1
        assert case_input["similar_cases"][0]["similarity_score"] == 0.78
        assert "same_ward" in case_input["similar_cases"][0]["reason_features"]

    def test_builder_to_json(self):
        """Test JSON serialization."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        builder = CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
        builder.set_application(address="Test")

        json_str = builder.to_json()
        parsed = json.loads(json_str)

        assert parsed["run_id"] == "run1"
        assert parsed["application"]["address"] == "Test"

    def test_builder_fluent_api(self):
        """Test fluent/chained API."""
        from plana.prompts.case_input_builder import CaseInputBuilder

        case_input = (
            CaseInputBuilder("run1", "newcastle", "2024/0001", "demo")
            .set_application(address="Test", proposal="Build")
            .add_constraint("conservation_area", "Test Area")
            .add_document("doc1", "Form", hash="abc")
            .add_policy("NPPF-1", "Test Policy", "NPPF")
            .add_similar_case("case1", "newcastle", "2023/0001")
            .build()
        )

        assert case_input["application"]["address"] == "Test"
        assert len(case_input["constraints"]) == 1
        assert len(case_input["documents"]) == 1
        assert len(case_input["policies"]) == 1
        assert len(case_input["similar_cases"]) == 1


class TestPromptContent:
    """Tests for prompt content requirements."""

    def test_case_officer_has_required_sections(self):
        """Test that case officer prompt has all required sections."""
        from plana.prompts import get_case_officer_prompt

        prompt = get_case_officer_prompt()
        content = prompt.content

        # Hard rules
        assert "Evidence-first" in content or "Evidence-First" in content
        assert "No hallucinations" in content or "No Hallucinations" in content
        assert "Traceability" in content

        # Tasks
        assert "Task A" in content or "Pipeline" in content
        assert "Task B" in content or "Report" in content
        assert "Task C" in content or "Similarity" in content
        assert "Task D" in content or "Continuous improvement" in content

        # Output schema
        assert "meta" in content
        assert "pipeline_audit" in content
        assert "report_markdown" in content
        assert "learning_signals" in content

    def test_evaluator_has_scoring_criteria(self):
        """Test that evaluator prompt has scoring criteria."""
        from plana.prompts import get_evaluator_prompt

        prompt = get_evaluator_prompt()
        content = prompt.content

        # Scoring dimensions
        assert "Policy Coverage" in content
        assert "Similarity Relevance" in content
        assert "Evidence Traceability" in content
        assert "Structural Completeness" in content

        # Grading
        assert "Grade" in content or "grade" in content
        assert "PASS" in content or "pass" in content


class TestDatabaseVersioning:
    """Tests for database prompt version tracking."""

    def test_stored_report_has_version_fields(self):
        """Test that StoredReport model has version fields."""
        from plana.storage.models import StoredReport

        report = StoredReport(
            reference="2024/0001",
            report_path="/tmp/test.md",
            prompt_version="1.0.0",
            schema_version="1.0.0",
        )

        assert report.prompt_version == "1.0.0"
        assert report.schema_version == "1.0.0"
