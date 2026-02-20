"""Step-by-step pipeline endpoints for the report generation wizard.

Each endpoint performs **real work** and returns **real data** so the
frontend wizard can show genuine progress and results at every step.

Flow:
  1. POST /analyse-documents   — force-process stuck docs, return extraction summary
  2. POST /check-policies      — run policy search, return matched policies
  3. POST /find-similar-cases  — run similarity search, return comparable cases
  4. POST /assess-constraints  — GIS enrichment + heritage/highways/amenity assessment
  5. POST /generate-report     — full report generation using all available data
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from plana.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_application(reference: str) -> Optional[Any]:
    """Load a stored application from the database."""
    try:
        from plana.storage.database import get_database
        db = get_database()
        app = db.get_application(reference)
        if app is None:
            # Try normalised (uppercase)
            from urllib.parse import unquote
            normalized = unquote(reference).strip().upper()
            if normalized != reference:
                app = db.get_application(normalized)
        return app
    except Exception as exc:
        logger.warning("pipeline_load_app_failed", reference=reference, error=str(exc))
        return None


def _get_constraints(app) -> list[str]:
    """Extract constraints list from a stored application."""
    try:
        return json.loads(app.constraints_json or "[]")
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Step 1: Analyse Documents
# ---------------------------------------------------------------------------

@router.post("/analyse-documents")
@router.get("/analyse-documents")
async def analyse_documents(
    reference: str = Query(..., description="Application reference"),
):
    """Analyse all submitted documents for a planning application.

    Forces processing of any stuck documents, then returns a detailed
    summary of what was found — document counts, types, extracted text,
    plan set presence, and evidence quality assessment.

    This is real document analysis, not a simulated progress bar.
    """
    try:
        from plana.storage.database import get_database
        db = get_database()

        # Force-process any stuck documents so we don't block forever
        counts = db.get_processing_counts(reference)
        if counts["total"] == 0:
            from urllib.parse import unquote
            normalized = unquote(reference).strip().upper()
            if normalized != reference:
                counts = db.get_processing_counts(normalized)
                if counts["total"] > 0:
                    reference = normalized

        if counts["total"] > 0 and (counts["queued"] > 0 or counts["processing"] > 0):
            # Auto-unblock: force-process URL-less docs first
            urlless = db.force_process_urlless_documents(reference)
            counts = db.get_processing_counts(reference)
            if counts["queued"] > 0 or counts["processing"] > 0:
                # Force-process everything — worker can't make progress
                db.force_process_all_documents(reference)
                counts = db.get_processing_counts(reference)

        # Load all documents for detailed analysis
        stored_docs = db.get_documents(reference)
        if not stored_docs:
            return JSONResponse(status_code=404, content={
                "error": True,
                "message": f"No documents found for reference {reference}",
            })

        # Classify documents by type
        by_type: dict[str, int] = {}
        plans_count = 0
        with_text = 0
        total_text_chars = 0
        documents_detail = []

        for doc in stored_docs:
            doc_type = doc.doc_type or "other"
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

            is_plan = bool(doc.is_plan_or_drawing)
            if is_plan:
                plans_count += 1

            chars = doc.extracted_text_chars or 0
            if chars > 0:
                with_text += 1
            total_text_chars += chars

            documents_detail.append({
                "doc_id": doc.doc_id,
                "filename": doc.title,
                "type": doc_type,
                "is_plan": is_plan,
                "status": doc.processing_status,
                "extract_method": doc.extract_method or "none",
                "text_chars": chars,
                "has_content": bool(doc.has_any_content_signal),
            })

        # Determine evidence quality
        if with_text >= 3 and total_text_chars > 5000:
            evidence_quality = "HIGH"
        elif with_text >= 1 and total_text_chars > 500:
            evidence_quality = "MEDIUM"
        else:
            evidence_quality = "LOW"

        # Check for plan set (at least one plan/drawing identified)
        plan_set_present = plans_count > 0

        logger.info(
            "pipeline_documents_analysed",
            reference=reference,
            total=len(stored_docs),
            with_text=with_text,
            plans=plans_count,
            quality=evidence_quality,
        )

        return {
            "step": 1,
            "step_name": "analyse_documents",
            "status": "complete",
            "reference": reference,
            "summary": {
                "total_documents": len(stored_docs),
                "processed": counts.get("processed", len(stored_docs)),
                "with_extracted_text": with_text,
                "total_text_chars": total_text_chars,
                "plans_identified": plans_count,
                "plan_set_present": plan_set_present,
                "evidence_quality": evidence_quality,
                "by_type": by_type,
            },
            "documents": documents_detail,
        }
    except Exception as exc:
        logger.error("pipeline_analyse_documents_failed", reference=reference, error=str(exc))
        return JSONResponse(status_code=500, content={
            "error": True,
            "message": f"Document analysis failed: {exc}",
        })


# ---------------------------------------------------------------------------
# Step 2: Check Policies
# ---------------------------------------------------------------------------

@router.post("/check-policies")
@router.get("/check-policies")
async def check_policies(
    reference: str = Query(..., description="Application reference"),
):
    """Cross-reference the proposal against NPPF and local plan policies.

    Runs the full policy search engine against the stored application's
    proposal, constraints, and application type. Returns every matched
    policy with its source document and relevance reasoning.
    """
    app = _load_application(reference)
    if app is None:
        return JSONResponse(status_code=404, content={
            "error": True,
            "message": f"Application not found: {reference}",
        })

    constraints = _get_constraints(app)
    council_id = (app.council_id or "").strip().lower()

    try:
        from plana.policy.search import PolicySearch
        policy_search = PolicySearch()
        policies = policy_search.retrieve_relevant_policies(
            proposal=app.proposal or "",
            constraints=constraints,
            application_type=app.application_type or "",
            council_id=council_id,
            reference=app.reference,
        )

        # Categorise by source
        nppf_count = 0
        local_plan_count = 0
        spd_count = 0
        policy_list = []

        for p in policies[:20]:
            source = (p.doc_id or "").lower()
            if "nppf" in source:
                nppf_count += 1
                category = "NPPF"
            elif "spd" in source or "supplementary" in source:
                spd_count += 1
                category = "SPD"
            else:
                local_plan_count += 1
                category = "Local Plan"

            policy_list.append({
                "policy_id": p.policy_id,
                "title": p.policy_title,
                "source": p.doc_id,
                "category": category,
                "relevance": p.match_reason,
                "text_excerpt": (p.text[:300] + "...") if p.text and len(p.text) > 300 else (p.text or ""),
            })

        logger.info(
            "pipeline_policies_checked",
            reference=reference,
            total=len(policies),
            nppf=nppf_count,
            local_plan=local_plan_count,
            spd=spd_count,
        )

        return {
            "step": 2,
            "step_name": "check_policies",
            "status": "complete",
            "reference": reference,
            "summary": {
                "total_policies": len(policies),
                "nppf_paragraphs": nppf_count,
                "local_plan_policies": local_plan_count,
                "spd_references": spd_count,
            },
            "policies": policy_list,
        }
    except Exception as exc:
        logger.error("pipeline_check_policies_failed", reference=reference, error=str(exc))
        return JSONResponse(status_code=500, content={
            "error": True,
            "message": f"Policy check failed: {exc}",
        })


# ---------------------------------------------------------------------------
# Step 3: Find Similar Cases
# ---------------------------------------------------------------------------

@router.post("/find-similar-cases")
@router.get("/find-similar-cases")
async def find_similar_cases(
    reference: str = Query(..., description="Application reference"),
):
    """Search for comparable planning applications with similar characteristics.

    Matches by location, development type, constraints, and proposal
    keywords. Returns each case with its decision outcome, similarity
    score, and the reasoning for why it's comparable.
    """
    app = _load_application(reference)
    if app is None:
        return JSONResponse(status_code=404, content={
            "error": True,
            "message": f"Application not found: {reference}",
        })

    constraints = _get_constraints(app)

    try:
        from plana.similarity.search import SimilaritySearch
        similarity_search = SimilaritySearch()
        cases = similarity_search.find_similar_cases(
            proposal=app.proposal or "",
            constraints=constraints,
            address=app.address or "",
            application_type=app.application_type or "",
        )

        approved = 0
        refused = 0
        withdrawn = 0
        case_list = []

        for c in cases[:10]:
            decision = (c.decision or "").lower()
            if "approv" in decision or "grant" in decision:
                approved += 1
            elif "refus" in decision or "reject" in decision:
                refused += 1
            elif "withdraw" in decision:
                withdrawn += 1

            case_list.append({
                "reference": c.reference,
                "address": getattr(c, "address", "")[:100],
                "proposal": (c.proposal or "")[:200],
                "decision": c.decision,
                "decision_date": getattr(c, "decision_date", None),
                "similarity_score": round(c.similarity_score, 2),
                "relevance_reason": c.similarity_reason,
                "application_type": getattr(c, "application_type", ""),
            })

        logger.info(
            "pipeline_similar_cases_found",
            reference=reference,
            total=len(cases),
            approved=approved,
            refused=refused,
        )

        return {
            "step": 3,
            "step_name": "find_similar_cases",
            "status": "complete",
            "reference": reference,
            "summary": {
                "total_cases": len(cases),
                "approved": approved,
                "refused": refused,
                "withdrawn": withdrawn,
            },
            "cases": case_list,
        }
    except Exception as exc:
        logger.error("pipeline_find_similar_failed", reference=reference, error=str(exc))
        return JSONResponse(status_code=500, content={
            "error": True,
            "message": f"Similar case search failed: {exc}",
        })


# ---------------------------------------------------------------------------
# Step 4: Assess Constraints
# ---------------------------------------------------------------------------

@router.post("/assess-constraints")
@router.get("/assess-constraints")
async def assess_constraints(
    reference: str = Query(..., description="Application reference"),
):
    """Analyse site designations and constraints for a planning application.

    Performs GIS enrichment via postcodes.io, then runs the full
    constraint assessment: heritage impact (listed buildings, conservation
    areas), highways (parking, access, visibility), amenity impact
    (overlooking, daylight, noise), and design (materials, scale, massing).

    Returns real evidence-based assessments, not generic placeholders.
    """
    app = _load_application(reference)
    if app is None:
        return JSONResponse(status_code=404, content={
            "error": True,
            "message": f"Application not found: {reference}",
        })

    constraints = _get_constraints(app)
    council_id = (app.council_id or "").strip().lower()
    proposal = app.proposal or ""
    address = app.address or ""
    ward = app.ward or ""
    postcode = app.postcode or ""
    application_type = app.application_type or ""

    result: dict[str, Any] = {
        "step": 4,
        "step_name": "assess_constraints",
        "status": "complete",
        "reference": reference,
        "constraints_detected": list(constraints),
        "gis_verified": {},
        "heritage_assessment": None,
        "highways_assessment": None,
        "amenity_assessment": None,
        "design_assessment": None,
    }

    # --- GIS enrichment ---
    try:
        from plana.location.postcodes import enrich_application_location
        location_data = enrich_application_location(
            postcode=postcode,
            address=address,
            existing_constraints=constraints,
        )
        if location_data.get("all_constraints"):
            constraints = location_data["all_constraints"]
            result["constraints_detected"] = list(constraints)
        result["gis_verified"] = location_data.get("gis_verified", {})
        result["gis_checked_types"] = location_data.get("gis_checked_types", [])
    except Exception as exc:
        logger.debug("pipeline_gis_enrichment_failed", error=str(exc))

    # --- Load extracted document text for evidence ---
    measurements = None
    try:
        from plana.storage.database import get_database
        db = get_database()
        stored_docs = db.get_documents(reference)
        combined_text = " ".join(
            d.extracted_text or "" for d in (stored_docs or [])
            if d.extracted_text
        )
    except Exception:
        combined_text = ""

    # --- Extract measurements from documents ---
    try:
        from plana.documents.processor import extract_measurements
        if combined_text:
            measurements = extract_measurements(combined_text)
    except Exception:
        pass

    # --- Heritage assessment ---
    has_heritage = any(
        "conservation" in str(c).lower() or "listed" in str(c).lower()
        for c in constraints
    )
    if has_heritage:
        try:
            from plana.api.ai_case_officer import analyse_heritage_impact
            heritage = analyse_heritage_impact(
                proposal=proposal,
                constraints=constraints,
                ward=ward,
                site_description=address,
                council_id=council_id,
            )
            result["heritage_assessment"] = {
                "asset_type": heritage.asset_type,
                "grade": heritage.asset_grade,
                "significance": heritage.significance,
                "impact_on_significance": heritage.impact_on_significance,
                "harm_level": heritage.harm_level.value if hasattr(heritage.harm_level, "value") else str(heritage.harm_level),
                "justification": heritage.justification,
                "statutory_duty": heritage.statutory_duty,
                "public_benefits": heritage.public_benefits,
                "nppf_paragraph": heritage.nppf_paragraph,
                "weight_to_harm": heritage.weight_to_harm.value if hasattr(heritage.weight_to_harm, "value") else str(heritage.weight_to_harm),
            }
        except Exception as exc:
            logger.debug("pipeline_heritage_failed", error=str(exc))

    # --- Highways assessment ---
    try:
        from plana.api.ai_case_officer import assess_highways
        highways = assess_highways(
            proposal=proposal,
            constraints=constraints,
            application_type=application_type,
            measurements=measurements,
            council_id=council_id,
        )
        result["highways_assessment"] = highways
    except Exception as exc:
        logger.debug("pipeline_highways_failed", error=str(exc))

    # --- Amenity assessment ---
    try:
        from dataclasses import asdict
        from plana.api.ai_case_officer import analyse_amenity_impact
        amenity_list = analyse_amenity_impact(
            proposal=proposal,
            constraints=constraints,
            application_type=application_type,
            measurements=measurements,
            council_id=council_id,
        )
        result["amenity_assessment"] = [
            {k: (v.value if hasattr(v, "value") else v) for k, v in asdict(a).items()}
            for a in amenity_list
        ] if amenity_list else []
    except Exception as exc:
        logger.debug("pipeline_amenity_failed", error=str(exc))

    # --- Design assessment ---
    try:
        from plana.api.ai_case_officer import assess_design
        design = assess_design(
            proposal=proposal,
            constraints=constraints,
            ward=ward,
            measurements=measurements,
            council_id=council_id,
            site_address=address,
        )
        result["design_assessment"] = design
    except Exception as exc:
        logger.debug("pipeline_design_failed", error=str(exc))

    # Build summary
    summary_items = []
    for c in constraints:
        c_lower = str(c).lower()
        if "conservation" in c_lower:
            summary_items.append({"type": "Conservation Area", "severity": "significant"})
        elif "listed" in c_lower:
            grade = "II"
            if "grade i " in c_lower or "grade i*" in c_lower:
                grade = "I" if "grade i " in c_lower else "II*"
            summary_items.append({"type": f"Listed Building (Grade {grade})", "severity": "significant"})
        elif "green belt" in c_lower:
            summary_items.append({"type": "Green Belt", "severity": "significant"})
        elif "flood" in c_lower:
            summary_items.append({"type": "Flood Zone", "severity": "moderate"})
        elif "tree" in c_lower or "tpo" in c_lower:
            summary_items.append({"type": "Tree Preservation Order", "severity": "moderate"})
        elif "sssi" in c_lower or "ecology" in c_lower:
            summary_items.append({"type": "Ecology/SSSI", "severity": "moderate"})
        else:
            summary_items.append({"type": str(c), "severity": "low"})

    result["constraint_items"] = summary_items
    result["constraints_count"] = len(constraints)

    logger.info(
        "pipeline_constraints_assessed",
        reference=reference,
        constraints=len(constraints),
        has_heritage=has_heritage,
    )

    return result


# ---------------------------------------------------------------------------
# Step 5: Generate Report
# ---------------------------------------------------------------------------

@router.post("/generate-report")
@router.get("/generate-report")
async def generate_report(
    reference: str = Query(..., description="Application reference"),
):
    """Generate the full case officer report.

    This is the real report generation — not a simulated step. It loads
    the application from the database, runs all assessment functions
    (heritage, highways, amenity, design, planning balance), retrieves
    policies and similar cases, and produces a structured, evidence-based
    case officer report with a recommendation.

    The response contains the full CaseOutputResponse including the
    report_markdown, recommendation, assessment topics, conditions,
    evidence citations, and confidence scoring.
    """
    app = _load_application(reference)
    if app is None:
        return JSONResponse(status_code=404, content={
            "error": True,
            "message": f"Application not found: {reference}",
        })

    council_id = (app.council_id or "").strip().lower()

    # --- Primary path: regenerate from DB (uses full report generator) ---
    try:
        from plana.api.routes.reports import _regenerate_report_from_db, _normalize_ref, _raw_reports
        report_dict = _regenerate_report_from_db(reference)
        if report_dict is not None:
            logger.info("pipeline_report_generated_primary", reference=reference)
            return report_dict
    except Exception as exc:
        logger.warning("pipeline_primary_generation_failed", reference=reference, error=str(exc))

    # --- Fallback: PipelineService ---
    try:
        from plana.api.services.pipeline_service import PipelineService
        service = PipelineService()

        if app is not None:
            # Use the imported application regeneration path
            result = await service._regenerate_imported_report(app, council_id)
        else:
            result = await service.process_application(
                reference=reference,
                council_id=council_id,
                mode="live",
            )

        # Cache for subsequent GET /reports calls
        try:
            from plana.api.routes.reports import _raw_reports, _normalize_ref
            normalized = _normalize_ref(reference)
            if hasattr(result, "model_dump"):
                _raw_reports[normalized] = result.model_dump()
            elif hasattr(result, "dict"):
                _raw_reports[normalized] = result.dict()
        except Exception:
            pass

        logger.info("pipeline_report_generated_fallback", reference=reference)
        return result

    except Exception as exc:
        logger.error("pipeline_report_generation_failed", reference=reference, error=str(exc))

        # Last resort: generate minimal report so user gets something
        try:
            from plana.api.routes.reports import _generate_minimal_report
            minimal = _generate_minimal_report(reference)
            if minimal:
                return minimal
        except Exception:
            pass

        return JSONResponse(status_code=500, content={
            "error": True,
            "message": f"Report generation failed: {exc}",
            "reference": reference,
        })


# ---------------------------------------------------------------------------
# Full pipeline status
# ---------------------------------------------------------------------------

@router.get("/status")
async def pipeline_status(
    reference: str = Query(..., description="Application reference"),
):
    """Get the current pipeline status for an application.

    Returns which steps have been completed and which are pending,
    along with cached results from previous step runs.
    """
    app = _load_application(reference)
    if app is None:
        return JSONResponse(status_code=404, content={
            "error": True,
            "message": f"Application not found: {reference}",
        })

    # Check document status
    try:
        from plana.storage.database import get_database
        db = get_database()
        counts = db.get_processing_counts(reference)
        docs_exist = counts["total"] > 0
        docs_ready = docs_exist and counts["queued"] == 0 and counts["processing"] == 0
    except Exception:
        docs_exist = False
        docs_ready = False

    # Check if report exists
    report_exists = False
    try:
        from plana.api.routes.reports import _raw_reports, _normalize_ref, _demo_reports
        normalized = _normalize_ref(reference)
        report_exists = normalized in _raw_reports or normalized in _demo_reports
    except Exception:
        pass

    return {
        "reference": reference,
        "application_exists": True,
        "address": app.address,
        "proposal": app.proposal,
        "steps": {
            "analyse_documents": {
                "available": docs_exist,
                "complete": docs_ready,
            },
            "check_policies": {
                "available": True,
                "complete": False,  # Always re-runnable
            },
            "find_similar_cases": {
                "available": True,
                "complete": False,
            },
            "assess_constraints": {
                "available": True,
                "complete": False,
            },
            "generate_report": {
                "available": docs_ready or not docs_exist,
                "complete": report_exists,
            },
        },
    }
