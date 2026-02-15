"""
Tests for upgraded plan_set_present detection.

Covers:
- Title-block phrase detection from extracted text / OCR
- Drawing scale pattern detection
- Sheet numbering and Proposed/Existing markers
- Weird filenames ("-1527192.pdf") with text-based detection
- Scanned drawings with no text layer
- 3-leg rule: (location OR block) AND (site) AND (detail)
- detected_labels feeding into check_plan_set_present
- DrawingMetadata new fields (detected_labels, scale_found)
"""

import json

import pytest

from plana.documents.ingestion import DocumentCategory
from plana.documents.processor import (
    DrawingMetadata,
    check_plan_set_present,
    extract_drawing_metadata,
    is_plan_or_drawing_heuristic,
)


# ---------------------------------------------------------------------------
# DrawingMetadata new fields
# ---------------------------------------------------------------------------


class TestDrawingMetadataNewFields:
    """Test new detected_labels and scale_found fields."""

    def test_defaults_empty(self):
        meta = DrawingMetadata()
        assert meta.detected_labels == []
        assert meta.scale_found == ""

    def test_to_json_includes_new_fields(self):
        meta = DrawingMetadata(
            detected_labels=["site plan", "elevations"],
            scale_found="1:500",
        )
        data = json.loads(meta.to_json())
        assert data["detected_labels"] == ["site plan", "elevations"]
        assert data["scale_found"] == "1:500"

    def test_from_json_with_new_fields(self):
        raw = json.dumps({
            "document_type_guess": "site plan",
            "key_labels_found": ["scale"],
            "any_dimensions_detected": False,
            "any_scale_detected": True,
            "detected_labels": ["site plan"],
            "scale_found": "1:200",
        })
        meta = DrawingMetadata.from_json(raw)
        assert meta.detected_labels == ["site plan"]
        assert meta.scale_found == "1:200"

    def test_from_json_backward_compat(self):
        """Old JSON without new fields should load cleanly."""
        raw = json.dumps({
            "document_type_guess": "floor plan",
            "key_labels_found": [],
            "any_dimensions_detected": False,
            "any_scale_detected": False,
        })
        meta = DrawingMetadata.from_json(raw)
        assert meta.detected_labels == []
        assert meta.scale_found == ""


# ---------------------------------------------------------------------------
# Title-block phrase detection from text
# ---------------------------------------------------------------------------


class TestTitleBlockDetection:
    """extract_drawing_metadata should detect title-block phrases from text."""

    def test_location_plan_in_text(self):
        meta = extract_drawing_metadata(
            "-1527192.pdf",
            DocumentCategory.OTHER,
            extracted_text="LOCATION PLAN  Scale 1:1250  Sheet 1 of 5",
        )
        assert "location plan" in meta.detected_labels
        assert meta.scale_found == "1:1250"
        assert meta.any_scale_detected is True

    def test_site_plan_in_text(self):
        meta = extract_drawing_metadata(
            "doc_003.pdf",
            DocumentCategory.OTHER,
            extracted_text="PROPOSED SITE PLAN  1:500",
        )
        assert "site plan" in meta.detected_labels
        assert meta.scale_found == "1:500"

    def test_elevation_in_text(self):
        meta = extract_drawing_metadata(
            "upload-99.pdf",
            DocumentCategory.OTHER,
            extracted_text="PROPOSED ELEVATIONS\nFront Elevation  Rear Elevation",
        )
        assert "elevations" in meta.detected_labels

    def test_floor_plan_in_text(self):
        meta = extract_drawing_metadata(
            "random_name.pdf",
            DocumentCategory.OTHER,
            extracted_text="Ground Floor Plan  First Floor Plan  Scale 1:50",
        )
        assert "floor plan" in meta.detected_labels
        assert meta.scale_found == "1:50"

    def test_sections_in_text(self):
        meta = extract_drawing_metadata(
            "dwg_4.pdf",
            DocumentCategory.OTHER,
            extracted_text="Section Drawing A-A  Cross-section B-B",
        )
        assert "sections" in meta.detected_labels

    def test_street_scene_in_text(self):
        meta = extract_drawing_metadata(
            "plan_x.pdf",
            DocumentCategory.OTHER,
            extracted_text="STREET SCENE  Proposed",
        )
        assert "street scene" in meta.detected_labels

    def test_block_plan_in_text(self):
        meta = extract_drawing_metadata(
            "foo.pdf",
            DocumentCategory.OTHER,
            extracted_text="Block Plan  Scale 1:500  North →",
        )
        assert "block plan" in meta.detected_labels

    def test_multiple_labels_detected(self):
        """A single drawing can contain multiple title-block phrases."""
        meta = extract_drawing_metadata(
            "combined_sheet.pdf",
            DocumentCategory.OTHER,
            extracted_text=(
                "LOCATION PLAN  1:1250\n"
                "SITE PLAN  1:500\n"
                "PROPOSED ELEVATIONS\n"
                "Sheet 1 of 3"
            ),
        )
        assert "location plan" in meta.detected_labels
        assert "site plan" in meta.detected_labels
        assert "elevations" in meta.detected_labels
        assert "sheet_numbered" in meta.detected_labels

    def test_no_labels_for_text_report(self):
        """Non-drawing text should not produce drawing-type labels."""
        meta = extract_drawing_metadata(
            "design_access_statement.pdf",
            DocumentCategory.DESIGN_ACCESS_STATEMENT,
            extracted_text=(
                "This design and access statement describes the proposal "
                "for a two-storey extension to the rear of the dwelling."
            ),
        )
        # Should not detect drawing types from statement text
        assert "site plan" not in meta.detected_labels
        assert "elevations" not in meta.detected_labels

    def test_document_type_guess_inferred_from_text(self):
        """When filename is opaque, document_type_guess should come from text."""
        meta = extract_drawing_metadata(
            "-1527192.pdf",
            DocumentCategory.OTHER,
            extracted_text="LOCATION PLAN  Scale 1:1250",
        )
        assert meta.document_type_guess == "location plan"


# ---------------------------------------------------------------------------
# Scale detection
# ---------------------------------------------------------------------------


class TestScaleDetection:
    """extract_drawing_metadata should capture the actual scale string."""

    def test_scale_1_500(self):
        meta = extract_drawing_metadata(
            "plan.pdf", extracted_text="Scale 1:500"
        )
        assert meta.scale_found == "1:500"
        assert meta.any_scale_detected is True

    def test_scale_1_1250(self):
        meta = extract_drawing_metadata(
            "plan.pdf", extracted_text="1 : 1250"
        )
        assert meta.scale_found == "1:1250"

    def test_scale_1_50(self):
        meta = extract_drawing_metadata(
            "plan.pdf", extracted_text="@1:50 on A3"
        )
        assert meta.scale_found == "1:50"

    def test_no_scale_in_statement(self):
        meta = extract_drawing_metadata(
            "das.pdf",
            extracted_text="The proposal is appropriate in scale and design",
        )
        assert meta.scale_found == ""


# ---------------------------------------------------------------------------
# Sheet numbering detection
# ---------------------------------------------------------------------------


class TestSheetNumbering:
    """extract_drawing_metadata should detect sheet numbering patterns."""

    def test_sheet_number(self):
        meta = extract_drawing_metadata(
            "plan.pdf",
            extracted_text="Sheet No. 3 of 5  Location Plan",
        )
        assert "sheet_numbered" in meta.detected_labels

    def test_drawing_number(self):
        meta = extract_drawing_metadata(
            "plan.pdf",
            extracted_text="Drawing Number 001  Site Plan  1:500",
        )
        assert "sheet_numbered" in meta.detected_labels

    def test_dwg_number(self):
        meta = extract_drawing_metadata(
            "plan.pdf",
            extracted_text="Dwg No 12  Proposed Elevations",
        )
        assert "sheet_numbered" in meta.detected_labels


# ---------------------------------------------------------------------------
# Weird filenames — text-based detection
# ---------------------------------------------------------------------------


class TestWeirdFilenames:
    """Documents with opaque filenames should still be detectable from text."""

    def test_numeric_only_filename_with_text(self):
        """Filename '-1527192.pdf' with OCR text 'Location Plan'."""
        meta = extract_drawing_metadata(
            "-1527192.pdf",
            DocumentCategory.OTHER,
            extracted_text="LOCATION PLAN  Scale 1:1250  Ordnance Survey",
        )
        assert "location plan" in meta.detected_labels
        assert meta.document_type_guess == "location plan"
        assert meta.scale_found == "1:1250"

    def test_guid_filename_with_text(self):
        """Filename 'a3b2c1d0-e4f5-6789.pdf' with text."""
        meta = extract_drawing_metadata(
            "a3b2c1d0-e4f5-6789.pdf",
            DocumentCategory.OTHER,
            extracted_text="PROPOSED SITE PLAN  1:500  Application Site Boundary",
        )
        assert "site plan" in meta.detected_labels
        assert meta.document_type_guess == "site plan"

    def test_underscore_number_filename_with_text(self):
        """Filename 'upload_00047.pdf' with floor plan content."""
        meta = extract_drawing_metadata(
            "upload_00047.pdf",
            DocumentCategory.OTHER,
            extracted_text="Ground Floor Plan  First Floor Plan  Scale 1:50",
        )
        assert "floor plan" in meta.detected_labels
        assert meta.document_type_guess == "floor plan"


# ---------------------------------------------------------------------------
# Scanned drawings with no text layer
# ---------------------------------------------------------------------------


class TestScannedNoText:
    """Scanned drawings with no text layer produce minimal metadata."""

    def test_no_text_no_labels(self):
        """Without text, no labels can be detected from content."""
        meta = extract_drawing_metadata(
            "-999999.pdf",
            DocumentCategory.OTHER,
            extracted_text="",
        )
        assert meta.detected_labels == []
        assert meta.scale_found == ""

    def test_no_text_with_known_category(self):
        """Category-based guess still works even without text."""
        meta = extract_drawing_metadata(
            "-999999.pdf",
            DocumentCategory.SITE_PLAN,
            extracted_text="",
        )
        assert meta.document_type_guess == "site plan"
        assert meta.detected_labels == []

    def test_no_text_with_filename_hint(self):
        """Filename hints still work for document_type_guess."""
        meta = extract_drawing_metadata(
            "proposed_elevations.pdf",
            DocumentCategory.ELEVATION,
            extracted_text="",
        )
        assert meta.document_type_guess == "elevation"


# ---------------------------------------------------------------------------
# 3-leg rule: (location OR block) AND (site) AND (detail)
# ---------------------------------------------------------------------------


class TestThreeLegRule:
    """check_plan_set_present with the 3-leg requirement."""

    # --- All three legs present ---

    def test_all_three_legs_from_categories(self):
        assert check_plan_set_present([
            DocumentCategory.LOCATION_PLAN,
            DocumentCategory.SITE_PLAN,
            DocumentCategory.ELEVATION,
        ]) is True

    def test_block_plan_satisfies_location_leg(self):
        assert check_plan_set_present([
            DocumentCategory.BLOCK_PLAN,
            DocumentCategory.SITE_PLAN,
            DocumentCategory.FLOOR_PLAN,
        ]) is True

    def test_section_drawing_satisfies_detail_leg(self):
        assert check_plan_set_present([
            DocumentCategory.LOCATION_PLAN,
            DocumentCategory.SITE_PLAN,
            DocumentCategory.SECTION_DRAWING,
        ]) is True

    # --- Missing one leg ---

    def test_missing_location_leg(self):
        """Site + detail but no location/block → incomplete."""
        assert check_plan_set_present([
            DocumentCategory.SITE_PLAN,
            DocumentCategory.ELEVATION,
        ]) is False

    def test_missing_site_leg(self):
        """Location + detail but no site → incomplete."""
        assert check_plan_set_present([
            DocumentCategory.LOCATION_PLAN,
            DocumentCategory.ELEVATION,
        ]) is False

    def test_missing_detail_leg(self):
        """Location + site but no detail → incomplete."""
        assert check_plan_set_present([
            DocumentCategory.LOCATION_PLAN,
            DocumentCategory.SITE_PLAN,
        ]) is False

    # --- Mixed signals across detection methods ---

    def test_category_plus_detected_labels(self):
        """Location from category, site from labels, detail from filename."""
        assert check_plan_set_present(
            categories=[DocumentCategory.LOCATION_PLAN],
            filenames=["proposed_elevations.pdf"],
            all_detected_labels=["site plan"],
        ) is True

    def test_all_from_detected_labels(self):
        """All three legs from text-content detected labels."""
        assert check_plan_set_present(
            categories=[],
            all_detected_labels=[
                "location plan",
                "site plan",
                "floor plan",
            ],
        ) is True

    def test_all_from_filenames(self):
        """All three legs from filenames."""
        assert check_plan_set_present(
            categories=[],
            filenames=[
                "Location_Plan.pdf",
                "Site_Plan.pdf",
                "Proposed_Elevations.pdf",
            ],
        ) is True

    def test_all_from_metadata_guesses(self):
        """All three legs from metadata_guesses."""
        assert check_plan_set_present(
            categories=[],
            metadata_guesses=["block plan", "site plan", "sections"],
        ) is True

    # --- Combined sheet with all labels ---

    def test_single_combined_sheet(self):
        """A single combined drawing sheet can satisfy all three legs."""
        assert check_plan_set_present(
            categories=[],
            all_detected_labels=[
                "location plan",
                "site plan",
                "elevations",
                "floor plan",
            ],
        ) is True

    # --- Only unrelated docs ---

    def test_no_plan_docs(self):
        assert check_plan_set_present([
            DocumentCategory.COVER_LETTER,
            DocumentCategory.PHOTOGRAPH,
        ]) is False
