"""
Tests for deferral and evidence quality logic.

Verifies that:
- Drawings-only (processed, plan_set_present) scenarios are NOT deferred
- Evidence quality is MEDIUM when plan_set_present even with zero extracted text
- Missing numeric details use "Officer to verify" wording when plans present
- Deferral only happens when plan_set_present==False AND no documents at all
"""

import sys
import os
import types
import importlib.util

# Import legacy modules BEFORE _setup_modules() creates stubs that
# would shadow the real plana package.
from plana.documents.ingestion import (
    DocumentCategory,
    DocumentIngestionResult,
    ExtractionStatus,
    ProcessedDocument,
    _compute_evidence_quality,
)
from plana.report.generator import ApplicationData as LegacyApplicationData
from plana.report.generator import ReportGenerator as LegacyReportGenerator


def _setup_modules():
    """Load src/plana/api modules with isolated imports to avoid heavy deps."""
    src = os.path.join(os.path.dirname(__file__), "..", "src")
    sys.path.insert(0, os.path.abspath(src))

    # Create module stubs — use setdefault so we don't clobber real plana
    # modules that were already imported above.
    plana_pkg = types.ModuleType("plana")
    plana_pkg.__path__ = [os.path.join(src, "plana")]
    plana_api_pkg = types.ModuleType("plana.api")
    plana_api_pkg.__path__ = [os.path.join(src, "plana", "api")]
    sys.modules.setdefault("plana", plana_pkg)
    sys.modules.setdefault("plana.api", plana_api_pkg)

    def _load(name, filepath):
        spec = importlib.util.spec_from_file_location(name, filepath)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    _load("plana.api.evidence_tracker", os.path.join(src, "plana/api/evidence_tracker.py"))
    _load("plana.api.similar_cases", os.path.join(src, "plana/api/similar_cases.py"))
    _load("plana.api.policy_engine", os.path.join(src, "plana/api/policy_engine.py"))
    # Load modules lazily imported by reasoning_engine
    for extra in ("nppf_complete", "local_plans_complete"):
        p = os.path.join(src, "plana", "api", f"{extra}.py")
        if os.path.exists(p):
            _load(f"plana.api.{extra}", p)
    reasoning = _load("plana.api.reasoning_engine", os.path.join(src, "plana/api/reasoning_engine.py"))
    learning = types.ModuleType("plana.api.learning")
    learning.get_learning_system = lambda: None
    sys.modules["plana.api.learning"] = learning
    report = _load("plana.api.report_generator", os.path.join(src, "plana/api/report_generator.py"))

    return reasoning, report


reasoning_mod, report_mod = _setup_modules()

_should_defer = report_mod._should_defer
_build_material_info_missing = report_mod._build_material_info_missing
ProposalDetails = reasoning_mod.ProposalDetails


# ---------------------------------------------------------------------------
# Helper: build a ProposalDetails with no numeric measurements
# ---------------------------------------------------------------------------

def _empty_proposal_details():
    """ProposalDetails with no measurements (simulates drawings-only)."""
    return ProposalDetails(
        development_type="dwelling",
        num_storeys=0,
        num_units=1,
        num_bedrooms=0,
        height_metres=0,
        floor_area_sqm=0,
        parking_spaces=0,
        materials=[],
    )


def _full_proposal_details():
    """ProposalDetails with all measurements populated."""
    return ProposalDetails(
        development_type="dwelling",
        num_storeys=2,
        num_units=1,
        num_bedrooms=3,
        height_metres=8.5,
        floor_area_sqm=120.0,
        parking_spaces=2,
        materials=["brick", "slate"],
    )


# ===========================================================================
# Test _should_defer
# ===========================================================================


class TestShouldDefer:
    """Test the _should_defer function with plan_set_present."""

    def test_defer_when_no_docs_no_plan_set(self):
        """DEFER when documents_count==0, verified, no plan set."""
        assert _should_defer(
            documents_count=0, missing_items=["some missing"],
            documents_verified=True, plan_set_present=False,
        ) is True

    def test_no_defer_when_plan_set_present(self):
        """NEVER defer when plan_set_present==True, even if documents_count==0."""
        assert _should_defer(
            documents_count=0, missing_items=["some missing"],
            documents_verified=True, plan_set_present=True,
        ) is False

    def test_no_defer_when_docs_present(self):
        """NEVER defer when documents_count > 0."""
        assert _should_defer(
            documents_count=5, missing_items=["some missing"],
            documents_verified=True, plan_set_present=False,
        ) is False

    def test_no_defer_when_docs_present_and_plan_set(self):
        """NEVER defer when documents exist AND plan set present."""
        assert _should_defer(
            documents_count=3, missing_items=["some missing"],
            documents_verified=True, plan_set_present=True,
        ) is False

    def test_no_defer_when_unverified(self):
        """NEVER defer when documents status is unverified."""
        assert _should_defer(
            documents_count=0, missing_items=["some missing"],
            documents_verified=False, plan_set_present=False,
        ) is False

    def test_drawings_only_processed_plan_set_not_deferred(self):
        """Core scenario: drawings only, all processed, plan set present => NOT deferred.

        This is the key test: documents.total > 0, queued==0, processing==0,
        plan_set_present==True => must NOT defer.
        """
        assert _should_defer(
            documents_count=3,  # total > 0
            missing_items=[
                "**Ridge/eaves height** — Not extracted",
                "**Floor area** — Not extracted",
                "**Parking layout** — Not extracted",
                "**External materials schedule** — Not specified",
            ],
            documents_verified=True,
            plan_set_present=True,
        ) is False


# ===========================================================================
# Test _build_material_info_missing
# ===========================================================================


class TestBuildMaterialInfoMissing:
    """Test material info wording with plan_set_present."""

    def test_officer_verify_wording_when_plan_set_present(self):
        """When plan_set_present, missing items should say 'Officer to verify'."""
        details = _empty_proposal_details()
        section, items = _build_material_info_missing(
            documents_count=3,
            proposal_details=details,
            constraints=[],
            assessments=[],
            documents_verified=True,
            plan_set_present=True,
        )
        # Check wording for each numeric gap
        ridge_items = [i for i in items if "Ridge/eaves" in i]
        assert len(ridge_items) == 1
        assert "Officer to verify from plans" in ridge_items[0]

        floor_items = [i for i in items if "Floor area" in i]
        assert len(floor_items) == 1
        assert "Officer to verify from plans" in floor_items[0]

        parking_items = [i for i in items if "Parking" in i]
        assert len(parking_items) == 1
        assert "Officer to verify from plans" in parking_items[0]

        materials_items = [i for i in items if "materials" in i.lower()]
        assert len(materials_items) == 1
        assert "Officer to verify from plans" in materials_items[0]

    def test_no_submitted_plans_missing_when_plan_set_present(self):
        """When plan_set_present, should NOT list 'Submitted plans' as missing."""
        details = _empty_proposal_details()
        section, items = _build_material_info_missing(
            documents_count=0,  # count is 0 but plan_set is detected
            proposal_details=details,
            constraints=[],
            assessments=[],
            documents_verified=True,
            plan_set_present=True,
        )
        submitted_plans_items = [i for i in items if "Submitted plans" in i]
        assert len(submitted_plans_items) == 0, \
            "Should NOT list 'Submitted plans' as missing when plan_set_present"

    def test_submitted_plans_missing_when_no_plan_set(self):
        """When NOT plan_set_present and no docs, SHOULD list 'Submitted plans'."""
        details = _empty_proposal_details()
        section, items = _build_material_info_missing(
            documents_count=0,
            proposal_details=details,
            constraints=[],
            assessments=[],
            documents_verified=True,
            plan_set_present=False,
        )
        submitted_plans_items = [i for i in items if "Submitted plans" in i]
        assert len(submitted_plans_items) == 1, \
            "SHOULD list 'Submitted plans' as missing when no plan set"

    def test_no_lawfully_determine_when_plan_set_present(self):
        """When plan_set_present, section should NOT mention 'lawfully determine'."""
        details = _empty_proposal_details()
        section, items = _build_material_info_missing(
            documents_count=3,
            proposal_details=details,
            constraints=[],
            assessments=[],
            documents_verified=True,
            plan_set_present=True,
        )
        assert "lawfully" not in section.lower()

    def test_no_missing_items_when_all_details_present(self):
        """No measurement gaps when all details are populated."""
        details = _full_proposal_details()
        section, items = _build_material_info_missing(
            documents_count=3,
            proposal_details=details,
            constraints=["Residential Area"],
            assessments=[],
            documents_verified=True,
            plan_set_present=True,
        )
        # Should still have consultee/site visit gaps but NOT measurement gaps
        measurement_items = [
            i for i in items
            if any(kw in i for kw in ["Ridge", "Floor area", "Parking layout", "materials schedule"])
        ]
        assert len(measurement_items) == 0, \
            f"Should have no measurement gaps when all details present, got: {measurement_items}"


# ===========================================================================
# Test full report generation: drawings only, plan set present => not deferred
# ===========================================================================


class TestFullReportDrawingsOnly:
    """End-to-end: generate_full_markdown_report with drawings-only scenario."""

    def _generate_report(self, documents_count, plan_set_present, proposal_details=None):
        """Helper to generate a report with given document/plan-set settings."""
        from plana.api.policy_engine import Policy, PolicyParagraph
        from plana.api.similar_cases import HistoricCase

        if proposal_details is None:
            proposal_details = _empty_proposal_details()

        policies = [
            Policy(
                id="12", name="Achieving well-designed places", source="NPPF",
                source_type="NPPF", chapter=12,
                summary="Well-designed developments.",
                paragraphs=[PolicyParagraph(
                    number=130, text="Developments must be sympathetic.",
                    key_tests=["local character"],
                )],
            ),
        ]

        similar_cases = [
            HistoricCase(
                reference="22/00471/FUL",
                address="9 Maple Drive", ward="Test", postcode="NG9 4EU",
                proposal="Single storey dwelling",
                decision="Approved with Conditions", decision_date="2022-11-18",
                similarity_score=0.82, relevance_reason="Similar",
                constraints=[], conditions=[], refusal_reasons=[],
                case_officer_reasoning="Appropriate scale.",
                key_policies_cited=["NPPF Chapter 12"],
                application_type="Full Planning",
            ),
        ]

        precedent_analysis = {"total_cases": 1, "approved_count": 1, "approval_rate": 1.0}

        assessments = []
        for topic in ["Principle of Development", "Design and Visual Impact"]:
            a = reasoning_mod.generate_topic_assessment(
                topic=topic, proposal="Single storey dwelling",
                constraints=[], policies=policies,
                similar_cases=similar_cases, application_type="Full Planning",
                council_id="broxtowe", site_address="1 Test Street",
                proposal_details=proposal_details,
            )
            assessments.append(a)

        reasoning = reasoning_mod.generate_recommendation(
            assessments=assessments, constraints=[],
            precedent_analysis=precedent_analysis,
            proposal="Single storey dwelling",
            application_type="Full Planning",
            site_address="1 Test Street",
        )

        md = report_mod.generate_full_markdown_report(
            reference="25/00001/FUL",
            address="1 Test Street",
            proposal="Single storey dwelling",
            application_type="Full Planning",
            constraints=[],
            ward="TestWard",
            postcode="TE1 1ST",
            applicant_name="Test Applicant",
            policies=policies,
            similar_cases=similar_cases,
            precedent_analysis=precedent_analysis,
            assessments=assessments,
            reasoning=reasoning,
            documents_count=documents_count,
            documents_verified=True,
            council_name="Test Council",
            council_id="broxtowe",
            proposal_details=proposal_details,
            plan_set_present=plan_set_present,
        )
        return md

    def test_drawings_only_plan_set_not_deferred(self):
        """Drawings only, processed, plan set present => NOT deferred."""
        md = self._generate_report(
            documents_count=3, plan_set_present=True,
        )
        assert "DEFER" not in md, \
            "Report with plan_set_present=True must NOT recommend deferral"

    def test_drawings_only_evidence_not_low(self):
        """Drawings only with plan_set_present => evidence quality NOT LOW."""
        md = self._generate_report(
            documents_count=3, plan_set_present=True,
        )
        # Evidence quality should be MEDIUM (not LOW)
        assert "**Evidence Quality** | **LOW**" not in md, \
            "Evidence quality must NOT be LOW when plan_set_present=True"

    def test_drawings_only_evidence_is_medium(self):
        """Drawings only with plan_set_present => evidence quality MEDIUM."""
        md = self._generate_report(
            documents_count=3, plan_set_present=True,
        )
        assert "**MEDIUM**" in md, \
            "Evidence quality should be MEDIUM when plan_set_present=True"

    def test_drawings_only_officer_verify_wording(self):
        """Missing measurements should say 'Officer to verify from plans'."""
        md = self._generate_report(
            documents_count=3, plan_set_present=True,
        )
        assert "Officer to verify from plans" in md, \
            "Missing measurements should use 'Officer to verify' wording"

    def test_no_docs_no_plan_set_does_defer(self):
        """No docs, no plan set => DOES defer."""
        md = self._generate_report(
            documents_count=0, plan_set_present=False,
        )
        assert "DEFER" in md, \
            "Report with no docs and no plan set SHOULD recommend deferral"

    def test_no_docs_no_plan_set_is_deferral_report(self):
        """No docs, no plan set => deferral report generated."""
        md = self._generate_report(
            documents_count=0, plan_set_present=False,
        )
        # Deferral report has a specific format — check it's a deferral
        assert "DEFERRAL" in md or "DEFER" in md, \
            "Report with no docs and no plan set should be a deferral report"

    def test_docs_present_plan_set_present_normal_recommendation(self):
        """Docs present + plan set => normal recommendation (APPROVE/etc)."""
        md = self._generate_report(
            documents_count=3, plan_set_present=True,
            proposal_details=_full_proposal_details(),
        )
        assert "DEFER" not in md
        # Should have a normal recommendation
        assert "Recommendation" in md


# ===========================================================================
# Test legacy report generator deferral with plan_set_present
# ===========================================================================


class TestLegacyGeneratorDeferral:
    """Test the legacy ReportGenerator._generate_recommendation with plan set."""

    def test_legacy_no_defer_when_plan_set_present(self):
        """Legacy generator should NOT defer when plan_set_present in ingestion."""
        # Drawings-only: plan set present (all 3 legs), zero extracted text
        docs = [
            ProcessedDocument(
                doc_id="d0", title="Location Plan",
                filename="location_plan.pdf",
                category=DocumentCategory.LOCATION_PLAN,
                classification_confidence=0.9,
                extraction_status=ExtractionStatus.FAILED,
                extracted_text="",
            ),
            ProcessedDocument(
                doc_id="d1", title="Site Plan",
                filename="site_plan.pdf",
                category=DocumentCategory.SITE_PLAN,
                classification_confidence=0.9,
                extraction_status=ExtractionStatus.FAILED,
                extracted_text="",
            ),
            ProcessedDocument(
                doc_id="d2", title="Proposed Elevations",
                filename="elevations.pdf",
                category=DocumentCategory.ELEVATION,
                classification_confidence=0.9,
                extraction_status=ExtractionStatus.FAILED,
                extracted_text="",
            ),
            ProcessedDocument(
                doc_id="d3", title="Floor Plans",
                filename="floor_plans.pdf",
                category=DocumentCategory.FLOOR_PLAN,
                classification_confidence=0.9,
                extraction_status=ExtractionStatus.FAILED,
                extracted_text="",
            ),
        ]
        ingestion = DocumentIngestionResult(
            documents=docs,
            total_count=4,
            plans_count=4,
            key_docs_count=4,
            extracted_count=0,
            failed_count=4,
        )
        ingestion.evidence_quality = _compute_evidence_quality(ingestion)

        app = LegacyApplicationData(
            reference="TEST/DEFER",
            address="1 Test Street",
            proposal="Single storey dwelling",
            application_type="Full Planning",
            constraints=[],
            documents_count=4,
            documents_verified=True,
            document_ingestion=ingestion,
        )

        gen = LegacyReportGenerator.__new__(LegacyReportGenerator)
        section = gen._generate_recommendation(app, policies=[])

        assert "DEFER" not in section, \
            "Legacy generator should NOT defer when plan set is present in ingestion"

    def test_legacy_defers_when_no_plan_set(self):
        """Legacy generator SHOULD defer when no docs and no plan set."""
        app = LegacyApplicationData(
            reference="TEST/DEFER2",
            address="1 Test Street",
            proposal="Single storey dwelling",
            application_type="Full Planning",
            constraints=[],
            documents_count=0,
            documents_verified=True,
            document_ingestion=None,
        )

        gen = LegacyReportGenerator.__new__(LegacyReportGenerator)
        section = gen._generate_recommendation(app, policies=[])

        assert "DEFER" in section, \
            "Legacy generator SHOULD defer when no docs and no plan set"


# ===========================================================================
# End-to-end regression: DB docs processed → plan_set_present → NOT deferred
# ===========================================================================


class TestE2EDbDocsPlanSetPresent:
    """End-to-end regression test: documents stored in the DB with
    extracted_metadata_json containing detected_labels should feed
    into check_plan_set_present and produce plan_set_present=True.

    This tests the exact fix to generate_professional_report where
    plan_set_present was always False because it only checked inline
    request documents (categories=[]), not the DB.
    """

    def test_db_docs_with_metadata_produce_plan_set_true(self):
        """DB documents with detected_labels → plan_set_present=True."""
        import json
        import tempfile
        from pathlib import Path
        from plana.storage.database import Database
        from plana.storage.models import StoredDocument
        from plana.documents.processor import (
            DrawingMetadata,
            check_plan_set_present,
        )
        from plana.documents.ingestion import classify_document

        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(Path(tmpdir) / "test.db")

            # Simulate processed documents with opaque filenames but
            # detected_labels from OCR / text analysis.
            docs_spec = [
                ("d1", "-1527192.pdf", "PDF",
                 DrawingMetadata(
                     document_type_guess="location plan",
                     detected_labels=["location plan"],
                     scale_found="1:1250",
                     any_scale_detected=True,
                 )),
                ("d2", "-1527193.pdf", "PDF",
                 DrawingMetadata(
                     document_type_guess="site plan",
                     detected_labels=["site plan"],
                     scale_found="1:500",
                     any_scale_detected=True,
                 )),
                ("d3", "-1527194.pdf", "PDF",
                 DrawingMetadata(
                     document_type_guess="elevations",
                     detected_labels=["elevations"],
                     scale_found="1:100",
                     any_scale_detected=True,
                 )),
            ]

            for doc_id, title, doc_type, meta in docs_spec:
                db.save_document(StoredDocument(
                    reference="24/00730/FUL",
                    doc_id=doc_id,
                    title=title,
                    doc_type=doc_type,
                    processing_status="processed",
                    extract_method="drawing_only",
                    extracted_text_chars=0,
                    extracted_metadata_json=meta.to_json(),
                    is_plan_or_drawing=True,
                    has_any_content_signal=True,
                ))

            # --- Replicate what generate_professional_report now does ---
            stored_docs = db.get_documents("24/00730/FUL")

            categories = []
            filenames = []
            metadata_guesses = []
            all_detected_labels = []

            for sd in stored_docs:
                cat, _ = classify_document(sd.title, sd.doc_type, sd.title)
                categories.append(cat)
                filenames.append(sd.title)
                if sd.extracted_metadata_json:
                    meta_dict = json.loads(sd.extracted_metadata_json)
                    guess = meta_dict.get("document_type_guess", "")
                    if guess:
                        metadata_guesses.append(guess)
                    labels = meta_dict.get("detected_labels", [])
                    all_detected_labels.extend(labels)

            plan_set = check_plan_set_present(
                categories=categories,
                filenames=filenames,
                metadata_guesses=metadata_guesses or None,
                all_detected_labels=all_detected_labels or None,
            )

            # With opaque filenames, categories are all OTHER → no match.
            # But detected_labels have all 3 legs → plan_set_present=True.
            assert plan_set is True, (
                f"plan_set_present should be True from detected_labels. "
                f"categories={categories}, metadata_guesses={metadata_guesses}, "
                f"detected_labels={all_detected_labels}"
            )

    def test_db_docs_plan_set_feeds_into_report_not_deferred(self):
        """Full flow: DB plan_set=True → generate_full_markdown_report → NOT deferred."""
        md = TestFullReportDrawingsOnly()._generate_report(
            documents_count=26,
            plan_set_present=True,
        )
        # Must NOT defer
        assert "DEFER" not in md, \
            "Report must NOT defer when plan_set_present=True and documents processed"
        # Evidence quality must NOT be LOW
        assert "**Evidence Quality** | **LOW**" not in md, \
            "Evidence quality must NOT be LOW when plan_set_present=True"
        # Evidence quality should be MEDIUM (drawings present, no extracted text)
        assert "**MEDIUM**" in md, \
            "Evidence quality should be MEDIUM when plan_set_present=True"

    def test_db_docs_plan_set_with_26_docs_not_deferred(self):
        """Simulate the real scenario: 26 docs in DB, queued=0, processed=26,
        plan_set_present=True → NOT deferred, NOT LOW evidence."""
        md = TestFullReportDrawingsOnly()._generate_report(
            documents_count=26,
            plan_set_present=True,
            proposal_details=_empty_proposal_details(),
        )
        # Core assertions matching the user's exact scenario
        assert "DEFER" not in md
        assert "**LOW**" not in md or "**Evidence Quality** | **LOW**" not in md
        assert "Officer to verify from plans" in md
        assert "Recommendation" in md
