"""Report retrieval endpoints.

Supports two storage backends:
1. ``_demo_reports`` — in-memory dict populated by the import endpoint.
2. ``PipelineService.get_report()`` — database-backed report generation.

Both query-parameter and legacy path-parameter URL forms are accepted.
"""

import uuid
from datetime import datetime
from typing import Any, List, Optional, Union
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from plana.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# In-memory store populated by the import endpoint
# ---------------------------------------------------------------------------

_demo_reports: dict[str, "ReportResponse"] = {}

# Raw report dicts keyed by normalized reference.
# When the import endpoint generates a report inline, the raw dict
# (from generate_professional_report()) is what the frontend consumes.
# We cache it here so that GET /reports returns the **same format**.
_raw_reports: dict[str, dict] = {}


class ReportSectionResponse(BaseModel):
    """Report section response."""

    section_id: str
    title: str
    content: str
    order: int


class ReportResponse(BaseModel):
    """Report response model."""

    id: str
    application_reference: str
    version: int
    sections: list[ReportSectionResponse]
    recommendation: str | None = None
    generated_at: str
    generation_time_seconds: float | None = None
    mode: str = "live"
    demo_reference_used: str | None = None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _normalize_ref(ref: str) -> str:
    """Normalize a reference for lookup — decode URL-encoding and uppercase."""
    return unquote(ref).strip().upper()


def _lookup_demo_report(reference: str) -> Optional[ReportResponse]:
    """Check the in-memory demo store for a report."""
    normalized = _normalize_ref(reference)
    return _demo_reports.get(normalized)


def _auto_unblock_stuck_documents(reference: str, counts: dict) -> dict:
    """Try to auto-unblock documents that are stuck in 'queued'.

    Step 1: Force-process URL-less documents (they can never be downloaded).
    Step 2: If documents are STILL stuck, force-process ALL of them —
            the background worker has clearly been unable to make progress.

    Returns the updated processing counts.
    """
    try:
        from plana.storage.database import get_database

        db = get_database()

        # Step 1: Force-process URL-less docs (safe — worker can't help)
        urlless_count = db.force_process_urlless_documents(reference)
        if urlless_count > 0:
            logger.info(
                "auto_unblock_urlless",
                reference=reference,
                force_processed=urlless_count,
            )

        # Re-check counts after step 1
        counts = db.get_processing_counts(reference)
        if counts["queued"] == 0 and counts["processing"] == 0:
            return counts

        # Step 2: If still stuck (all remaining have URLs but worker
        # can't download them), force-process everything.
        all_count = db.force_process_all_documents(reference)
        if all_count > 0:
            logger.info(
                "auto_unblock_all",
                reference=reference,
                force_processed=all_count,
            )

        # Clear cached reports so regeneration uses fresh data
        normalized = _normalize_ref(reference)
        _raw_reports.pop(normalized, None)
        _raw_reports.pop(reference, None)
        _demo_reports.pop(normalized, None)
        _demo_reports.pop(reference, None)

        return db.get_processing_counts(reference)
    except Exception as exc:
        logger.warning(
            "auto_unblock_failed",
            reference=reference,
            error=str(exc),
        )
        return counts


def _check_document_processing_block(reference: str) -> Optional[JSONResponse]:
    """Return a 202 JSONResponse if documents for *reference* are still
    queued or processing.  Returns ``None`` when it is safe to generate /
    serve the report.

    This is the **hard block** — no report may be served while
    ``queued > 0`` or ``processing > 0``.

    Auto-unblock: if ALL queued documents cannot make progress (URL-less
    or background worker unable to download), they are automatically
    force-processed so the report can be generated.
    """
    try:
        from plana.storage.database import get_database

        db = get_database()
        # Try the reference as-is first, then normalized (uppercased)
        counts = db.get_processing_counts(reference)
        if counts["total"] == 0:
            normalized = _normalize_ref(reference)
            if normalized != reference:
                counts = db.get_processing_counts(normalized)
                if counts["total"] > 0:
                    reference = normalized

        if counts["total"] > 0 and (counts["queued"] > 0 or counts["processing"] > 0):
            # --- Auto-unblock: try to force-process stuck documents ---
            # This prevents the infinite 202 polling loop when the
            # background worker can't download documents (no URL, broken
            # URL, unsupported council portal, etc.).
            if counts["processing"] == 0:
                # Nothing actively processing — worker has given up or
                # hasn't started. Safe to force-process everything.
                counts = _auto_unblock_stuck_documents(reference, counts)
                if counts["queued"] == 0 and counts["processing"] == 0:
                    logger.info(
                        "report_block_auto_resolved",
                        reference=reference,
                        processed=counts["processed"],
                    )
                    return None  # Block cleared — proceed to generation

            logger.info(
                "report_blocked_documents_pending",
                reference=reference,
                queued=counts["queued"],
                processing=counts["processing"],
                processed=counts["processed"],
            )
            return JSONResponse(
                status_code=202,
                content={
                    "status": "processing_documents",
                    "reference": reference,
                    "documents": {
                        "total": counts["total"],
                        "queued": counts["queued"],
                        "processing": counts["processing"],
                        "processed": counts["processed"],
                        "failed": counts["failed"],
                    },
                },
            )
        logger.debug(
            "report_block_check_passed",
            reference=reference,
            total=counts["total"],
        )
    except Exception as exc:
        logger.error(
            "report_block_check_failed_trying_fallback",
            reference=reference,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        # Fallback: if the full query fails (e.g. missing columns from
        # an old schema), try a simple COUNT(*) so we never return a
        # false 404 when documents exist.
        try:
            from plana.storage.database import get_database
            db = get_database()
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM documents WHERE reference = ?",
                    (reference,),
                )
                row = cursor.fetchone()
                total = row["cnt"] if row else 0
                if total == 0:
                    normalized = _normalize_ref(reference)
                    if normalized != reference:
                        cursor.execute(
                            "SELECT COUNT(*) AS cnt FROM documents WHERE reference = ?",
                            (normalized,),
                        )
                        row = cursor.fetchone()
                        total = row["cnt"] if row else 0
                if total > 0:
                    logger.info(
                        "report_blocked_documents_exist_fallback",
                        reference=reference,
                        total=total,
                    )
                    return JSONResponse(
                        status_code=202,
                        content={
                            "status": "processing_documents",
                            "reference": reference,
                            "documents": {
                                "total": total,
                                "queued": total,
                                "processing": 0,
                                "processed": 0,
                                "failed": 0,
                            },
                        },
                    )
        except Exception as fallback_exc:
            logger.error(
                "report_block_fallback_also_failed",
                reference=reference,
                error=str(fallback_exc),
            )
    return None


def _any_documents_exist(reference: str) -> bool:
    """Return True if ANY documents exist in the DB for this reference.

    Uses the simplest possible query to avoid schema-related failures.
    """
    try:
        from plana.storage.database import get_database
        db = get_database()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            for ref in {reference, _normalize_ref(reference)}:
                cursor.execute(
                    "SELECT 1 FROM documents WHERE reference = ? LIMIT 1",
                    (ref,),
                )
                if cursor.fetchone():
                    return True
    except Exception as exc:
        logger.debug("any_documents_exist_check_failed", error=str(exc))
    return False


def _all_documents_processed(reference: str) -> bool:
    """Return True if documents exist AND all are in 'processed' or 'failed'
    state (none still queued or processing)."""
    try:
        from plana.storage.database import get_database
        db = get_database()
        counts = db.get_processing_counts(reference)
        if counts["total"] == 0:
            normalized = _normalize_ref(reference)
            if normalized != reference:
                counts = db.get_processing_counts(normalized)
        return counts["total"] > 0 and counts["queued"] == 0 and counts["processing"] == 0
    except Exception:
        return False


def _generate_minimal_report(reference: str) -> Optional[ReportResponse]:
    """Generate a minimal placeholder report when full generation fails.

    This prevents the frontend from polling 202 forever when all documents
    are processed but the full report generator is unavailable.
    """
    try:
        from plana.storage.database import get_database

        db = get_database()
        app = db.get_application(reference)
        if app is None:
            normalized = _normalize_ref(reference)
            if normalized != reference:
                app = db.get_application(normalized)
        if app is None:
            return None

        stored_docs = db.get_documents(app.reference)
        doc_count = len(stored_docs) if stored_docs else 0
        processed = sum(1 for d in (stored_docs or []) if d.processing_status == "processed")
        with_text = sum(1 for d in (stored_docs or []) if d.extracted_text_chars and d.extracted_text_chars > 0)

        markdown = f"""# Planning Assessment Report

## Application: {app.reference}

**Address:** {app.address or 'Not specified'}
**Proposal:** {app.proposal or 'Not specified'}
**Application Type:** {app.application_type or 'Not specified'}
**Council:** {app.council_name or app.council_id or 'Not specified'}

## Document Summary

- **Total documents:** {doc_count}
- **Processed:** {processed}
- **With extracted text:** {with_text}

## Status

Documents have been processed. {"Text was successfully extracted from " + str(with_text) + " document(s)." if with_text > 0 else "No extractable text was found in the submitted documents. A full assessment requires document content — please check that document URLs are included in the import request."}

*A full detailed assessment report will be available once the report generation service processes this application.*
"""
        report = ReportResponse(
            id=str(uuid.uuid4()),
            application_reference=app.reference,
            version=1,
            sections=[
                ReportSectionResponse(
                    section_id="full_report",
                    title="Planning Assessment Report",
                    content=markdown,
                    order=1,
                )
            ],
            recommendation=None,
            generated_at=datetime.now().isoformat(),
            generation_time_seconds=None,
            mode="minimal",
        )

        normalized = _normalize_ref(app.reference)
        _demo_reports[normalized] = report
        logger.info("minimal_report_generated", reference=normalized, doc_count=doc_count)
        return report

    except Exception as exc:
        logger.warning("minimal_report_failed", reference=reference, error=str(exc))
        return None


def _regenerate_report_from_db(reference: str) -> Optional[dict]:
    """Regenerate the report from stored application + document data.

    Uses the same ``generate_professional_report()`` function as the
    import endpoint so the frontend gets an **identical** response
    format — the raw dict with ``report_markdown``,
    ``recommendation.outcome``, ``assessment``, etc.

    Returns ``None`` if the application is not in the DB or documents
    are not yet processed.
    """
    try:
        import json as _json
        from plana.storage.database import get_database
        from plana.api.report_generator import generate_professional_report

        db = get_database()

        # Load stored application
        app = db.get_application(reference)
        if app is None:
            normalized = _normalize_ref(reference)
            if normalized != reference:
                app = db.get_application(normalized)
        if app is None:
            return None

        # Load documents with extracted text
        stored_docs = db.get_documents(app.reference)
        if not stored_docs:
            return None

        # Build documents list matching generate_professional_report input
        documents = []
        for doc in stored_docs:
            documents.append({
                "filename": doc.title,
                "document_type": doc.doc_type or "other",
                "content_text": doc.extracted_text or "",
            })

        constraints = _json.loads(app.constraints_json or "[]")
        council_id = (app.council_id or "").strip().lower()

        # Run GIS constraint checks using location enrichment
        gis_verified: dict = {}
        gis_checked_types: list = []
        try:
            from plana.location.postcodes import enrich_application_location
            location_data = enrich_application_location(
                postcode=app.postcode,
                address=app.address,
                existing_constraints=constraints,
            )
            gis_verified = location_data.get("gis_verified", {})
            gis_checked_types = location_data.get("gis_checked_types", [])
            # Merge any newly-detected constraints
            constraints = location_data.get("all_constraints", constraints)
        except Exception:
            pass  # Non-fatal — report will show "Not checked"

        report_dict = generate_professional_report(
            reference=app.reference,
            site_address=app.address,
            proposal_description=app.proposal,
            application_type=app.application_type or "",
            constraints=constraints,
            ward=app.ward,
            postcode=app.postcode,
            applicant_name=None,
            documents=documents,
            council_id=council_id,
            portal_documents_count=len(stored_docs),
            documents_verified=True,
            gis_verified=gis_verified,
            gis_checked_types=gis_checked_types,
        )

        # Cache the raw dict so subsequent polls return instantly.
        # This is the SAME format the import endpoint returns in
        # ImportApplicationResponse.report — the frontend expects it.
        normalized = _normalize_ref(app.reference)
        _raw_reports[normalized] = report_dict

        # Also cache as ReportResponse for the legacy code path
        markdown = report_dict.get("report_markdown", "")
        recommendation = report_dict.get("recommendation", {}).get("outcome", "")
        meta = report_dict.get("meta", {})

        report_response = ReportResponse(
            id=meta.get("run_id", str(uuid.uuid4())),
            application_reference=app.reference,
            version=1,
            sections=[
                ReportSectionResponse(
                    section_id="full_report",
                    title="Full Planning Assessment Report",
                    content=markdown,
                    order=1,
                )
            ],
            recommendation=recommendation,
            generated_at=meta.get("generated_at", datetime.now().isoformat()),
            generation_time_seconds=None,
            mode="live",
        )
        _demo_reports[normalized] = report_response

        logger.info("report_stored_after_regeneration", reference=normalized)

        return report_dict

    except Exception as exc:
        logger.warning(
            "report_regeneration_from_db_failed",
            reference=reference,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        return None


async def _get_report(
    reference: str,
    version: Optional[int] = None,
) -> Any:
    """Fetch the report from demo store first, then regenerate from DB,
    then fall back to PipelineService.

    Returns 202 if documents are still being processed.
    """
    # ---- Resolve reference to handle encoding / casing mismatches ----
    try:
        from plana.storage.database import get_database
        resolved = get_database().resolve_reference(reference)
        if resolved and resolved != reference:
            logger.debug(
                "report_reference_resolved",
                original=reference,
                resolved=resolved,
            )
            reference = resolved
    except Exception:
        pass  # non-fatal; proceed with original reference

    # ---- Hard block: never serve a report while docs are pending ----
    block_response = _check_document_processing_block(reference)
    if block_response is not None:
        return block_response

    # 1. Check raw report cache first — this is the SAME format the
    #    import endpoint returns (report_markdown, recommendation, etc.)
    #    so the frontend can parse it identically.
    normalized = _normalize_ref(reference)
    raw = _raw_reports.get(normalized)
    if raw is not None:
        return raw

    # 1b. Check legacy in-memory store (ReportResponse format)
    demo = _lookup_demo_report(reference)
    if demo is not None:
        return demo

    # 2. Try to regenerate from stored DB data (same path as import).
    #    Returns the raw dict matching the import endpoint format.
    regenerated = _regenerate_report_from_db(reference)
    if regenerated is not None:
        logger.info("report_regenerated_from_db", reference=reference)
        return regenerated

    # 2b. If all docs are processed but regeneration failed, serve a
    #     minimal report so the frontend doesn't poll 202 forever.
    if _all_documents_processed(reference):
        minimal = _generate_minimal_report(reference)
        if minimal is not None:
            logger.info("minimal_report_served", reference=reference)
            return minimal

    # 3. Fall through to PipelineService (database-backed)
    try:
        from plana.api.services import PipelineService
        from plana.api.models import DocumentProcessingResponse
    except ImportError:
        logger.warning("pipeline_service_unavailable", reference=reference)
        if _any_documents_exist(reference):
            # Try minimal report first to avoid perpetual 202
            if _all_documents_processed(reference):
                minimal = _generate_minimal_report(reference)
                if minimal:
                    return minimal
            return JSONResponse(
                status_code=202,
                content={
                    "status": "processing_documents",
                    "reference": reference,
                    "message": "Documents exist but report is not ready yet.",
                },
            )
        raise HTTPException(
            status_code=404,
            detail=f"Report not found: {reference}",
        )

    try:
        service = PipelineService()
        result = await service.get_report(reference=reference, version=version)
        if result is None:
            # Before returning 404, double-check that there really are
            # no documents being processed.  The initial block check may
            # have failed silently.
            retry_block = _check_document_processing_block(reference)
            if retry_block is not None:
                return retry_block

            # If all docs are processed, serve a minimal report
            if _all_documents_processed(reference):
                minimal = _generate_minimal_report(reference)
                if minimal:
                    return minimal

            # Last resort: if ANY documents exist for this reference,
            # return 202 rather than a false 404.
            if _any_documents_exist(reference):
                logger.warning(
                    "report_404_prevented_docs_exist",
                    reference=reference,
                )
                return JSONResponse(
                    status_code=202,
                    content={
                        "status": "processing_documents",
                        "reference": reference,
                        "message": "Documents exist but report is not ready yet.",
                    },
                )

            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {reference}",
            )
        return result
    except HTTPException as http_exc:
        # CRITICAL: Never let a 404 escape when documents exist.
        if http_exc.status_code == 404 and _any_documents_exist(reference):
            # If all docs are done, serve minimal report instead of 202
            if _all_documents_processed(reference):
                minimal = _generate_minimal_report(reference)
                if minimal:
                    return minimal
            logger.warning(
                "report_404_converted_to_202",
                reference=reference,
                original_detail=http_exc.detail,
            )
            return JSONResponse(
                status_code=202,
                content={
                    "status": "processing_documents",
                    "reference": reference,
                    "message": "Documents exist but report is not ready yet.",
                },
            )
        raise
    except Exception as e:
        # Catch-all: DocumentsProcessingError (possibly from a
        # different module path due to plana/ vs src/plana/ duality)
        # or any other exception.  Check for the duck-typed attributes
        # before falling back to a generic 202/500.
        if hasattr(e, "extraction_status") and hasattr(e, "processing_status"):
            # This is a DocumentsProcessingError (or quacks like one)
            try:
                return JSONResponse(
                    status_code=202,
                    content={
                        "status": "processing_documents",
                        "extraction_status": {
                            "queued": e.extraction_status.queued,
                            "extracted": e.extraction_status.extracted,
                            "failed": e.extraction_status.failed,
                        },
                        "documents": {
                            "total": e.processing_status.total,
                            "queued": e.processing_status.queued,
                            "processing": e.processing_status.processing,
                            "processed": e.processing_status.processed,
                            "failed": e.processing_status.failed,
                        },
                    },
                )
            except Exception:
                pass  # fall through to generic handler

        # If documents exist, return 202 instead of 500
        if _any_documents_exist(reference):
            logger.warning(
                "report_error_converted_to_202",
                reference=reference,
                error=str(e),
                error_type=type(e).__name__,
            )
            return JSONResponse(
                status_code=202,
                content={
                    "status": "processing_documents",
                    "reference": reference,
                    "message": "Documents exist but report is not ready yet.",
                },
            )

        logger.error("get_report_error", reference=reference, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Query-param endpoints (preferred)
# ---------------------------------------------------------------------------


@router.get("")
async def get_report_root(
    reference: str = Query(
        ..., description="Application reference (e.g. 24/00730/FUL)"
    ),
    version: Optional[int] = Query(None, description="Specific version number"),
):
    """Get a generated report for an application.

    Example: ``GET /api/v1/reports?reference=24/00730/FUL``
    """
    return await _get_report(reference=reference, version=version)


@router.get("/by-reference")
async def get_report_by_reference(
    reference: str = Query(
        ..., description="Application reference (e.g. 24/00730/FUL)"
    ),
    version: Optional[int] = Query(None, description="Specific version number"),
):
    """Get a generated report for an application.

    Pass the reference as a query parameter to avoid URL-encoding
    issues with slashes.

    Example: ``GET /api/v1/reports/by-reference?reference=24/00730/FUL``
    """
    return await _get_report(reference=reference, version=version)


@router.get("/by-reference/versions")
async def get_report_versions_by_reference(
    reference: str = Query(
        ..., description="Application reference (e.g. 24/00730/FUL)"
    ),
):
    """Get all versions of a report.

    Example: ``GET /api/v1/reports/by-reference/versions?reference=24/00730/FUL``
    """
    demo = _lookup_demo_report(reference)
    if demo is not None:
        return [
            {
                "version": demo.version,
                "generated_at": demo.generated_at,
                "recommendation": demo.recommendation,
            }
        ]

    try:
        from plana.api.services import PipelineService

        service = PipelineService()
        return await service.get_report_versions(reference=reference)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Legacy path-param routes — serve reports if found, 400 if not
# ---------------------------------------------------------------------------


@router.get("/{reference:path}/versions")
async def get_report_versions_legacy(reference: str):
    """Legacy path-param versions route."""
    decoded = unquote(reference)
    normalized = decoded.strip().upper()

    if normalized in _demo_reports:
        report = _demo_reports[normalized]
        return [
            {
                "version": report.version,
                "generated_at": report.generated_at,
                "recommendation": report.recommendation,
            }
        ]
    return []


@router.get("/{reference:path}")
async def get_report_legacy(reference: str):
    """Legacy path-param report retrieval.

    Checks in-memory store first, then falls through to PipelineService.
    """
    decoded = unquote(reference)
    return await _get_report(reference=decoded)
