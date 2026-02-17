"""Report retrieval endpoints.

Supports two storage backends:
1. ``_demo_reports`` — in-memory dict populated by the import endpoint
   (``applications.py:_store_report_for_retrieval``).
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


def _check_document_processing_block(reference: str):
    """Return a 202 JSONResponse if documents for *reference* are still
    queued or processing.  Returns ``None`` when it is safe to generate /
    serve the report.

    This is the **hard block** — no report may be served while
    ``queued > 0`` or ``processing > 0``.
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
        if counts["total"] > 0 and (counts["queued"] > 0 or counts["processing"] > 0):
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


def _regenerate_report_from_db(reference: str) -> Optional[ReportResponse]:
    """Regenerate the report from stored application + document data.

    Uses the same ``generate_professional_report()`` function as the
    import endpoint so the frontend gets an identical report format.
    Returns ``None`` if the application is not in the DB or documents
    are not yet processed.
    """
    try:
        import json as _json
        from plana.storage.database import get_database
        from plana.api.report_generator import generate_professional_report
        from plana.core.constants import resolve_council_name

        db = get_database()

        # Load stored application
        app = db.get_application(reference)
        if app is None:
            # Try normalized reference
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

        report = generate_professional_report(
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
        )

        # Store in cache for fast subsequent polls
        from plana.api.routes.applications import _store_report_for_retrieval
        _store_report_for_retrieval(app.reference, report)

        # Return from the cache
        return _lookup_demo_report(reference)

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
    # ---- Hard block: never serve a report while docs are pending ----
    block_response = _check_document_processing_block(reference)
    if block_response is not None:
        return block_response

    # 1. Check in-memory store (populated by import endpoint)
    demo = _lookup_demo_report(reference)
    if demo is not None:
        return demo

    # 2. Try to regenerate from stored DB data (same path as import).
    #    This handles the reprocess case: documents are all processed,
    #    no cached report exists, but application + extracted text are
    #    in the database.
    regenerated = _regenerate_report_from_db(reference)
    if regenerated is not None:
        logger.info("report_regenerated_from_db", reference=reference)
        return regenerated

    # 3. Fall through to PipelineService (database-backed)
    try:
        from plana.api.services import PipelineService
        from plana.api.services.pipeline_service import DocumentsProcessingError
        from plana.api.models import DocumentProcessingResponse
    except ImportError:
        logger.warning("pipeline_service_unavailable", reference=reference)
        if _any_documents_exist(reference):
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

            # Last resort: if ANY documents exist for this reference,
            # return 202 rather than a false 404.  This catches edge
            # cases where _check_document_processing_block fails twice.
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
    except HTTPException:
        raise
    except DocumentsProcessingError as e:
        return JSONResponse(
            status_code=202,
            content=DocumentProcessingResponse(
                status="processing_documents",
                extraction_status=e.extraction_status,
                documents=e.processing_status,
            ).model_dump(),
        )
    except Exception as e:
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
    # Check demo store
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
