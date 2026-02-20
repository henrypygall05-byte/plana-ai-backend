"""
SQLite database for Plana.AI storage.
"""

import json
import os
import socket
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional
from urllib.parse import unquote

from plana.core.logging import get_logger
from plana.storage.models import (
    StoredApplication,
    StoredDocument,
    StoredFeedback,
    StoredPolicyWeight,
    StoredReport,
    StoredRunLog,
)


class Database:
    """SQLite database for storing applications, documents, and feedback."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database.

        Args:
            db_path: Path to SQLite database file.
                    Reads DATABASE_SQLITE_PATH env var when db_path is None.
                    Falls back to ~/.plana/plana.db.
        """
        if db_path is None:
            env_path = os.environ.get("DATABASE_SQLITE_PATH")
            if env_path:
                db_path = Path(env_path)
            else:
                db_path = Path.home() / ".plana" / "plana.db"

        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        _db_logger = get_logger("plana.storage")
        _db_logger.info(
            "db_init",
            db_path=str(self.db_path),
            exists=self.db_path.exists(),
            size_bytes=self.db_path.stat().st_size if self.db_path.exists() else 0,
            pid=os.getpid(),
            cwd=os.getcwd(),
            hostname=socket.gethostname(),
            render_service=os.environ.get("RENDER_SERVICE_NAME"),
            render_instance=os.environ.get("RENDER_INSTANCE_ID"),
            git_sha=os.environ.get("RENDER_GIT_COMMIT"),
        )

        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with WAL mode and busy timeout."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # WAL mode allows concurrent readers + writer (critical for
        # the background worker thread running alongside web requests).
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference TEXT NOT NULL UNIQUE,
                    council_id TEXT NOT NULL,
                    address TEXT NOT NULL,
                    proposal TEXT NOT NULL,
                    application_type TEXT,
                    status TEXT,
                    date_received TEXT,
                    date_validated TEXT,
                    decision_date TEXT,
                    decision TEXT,
                    ward TEXT,
                    postcode TEXT,
                    constraints_json TEXT DEFAULT '[]',
                    applicant_name TEXT,
                    portal_url TEXT,
                    portal_key TEXT,
                    fetched_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER,
                    reference TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    doc_type TEXT,
                    url TEXT,
                    local_path TEXT,
                    content_hash TEXT,
                    size_bytes INTEGER,
                    content_type TEXT,
                    date_published TEXT,
                    downloaded_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id),
                    UNIQUE(reference, doc_id)
                )
            """)

            # Reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER,
                    reference TEXT NOT NULL,
                    report_path TEXT NOT NULL,
                    recommendation TEXT,
                    confidence REAL,
                    policies_cited INTEGER DEFAULT 0,
                    similar_cases_count INTEGER DEFAULT 0,
                    generation_mode TEXT DEFAULT 'demo',
                    prompt_version TEXT DEFAULT '1.0.0',
                    schema_version TEXT DEFAULT '1.0.0',
                    generated_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id)
                )
            """)

            # Migration: Add prompt_version and schema_version if not present
            cursor.execute("PRAGMA table_info(reports)")
            columns = [col[1] for col in cursor.fetchall()]
            if "prompt_version" not in columns:
                cursor.execute("ALTER TABLE reports ADD COLUMN prompt_version TEXT DEFAULT '1.0.0'")
            if "schema_version" not in columns:
                cursor.execute("ALTER TABLE reports ADD COLUMN schema_version TEXT DEFAULT '1.0.0'")

            # Migration: Add council_name column to applications
            cursor.execute("PRAGMA table_info(applications)")
            app_columns = [col[1] for col in cursor.fetchall()]
            if "council_name" not in app_columns:
                cursor.execute(
                    "ALTER TABLE applications ADD COLUMN council_name TEXT DEFAULT ''"
                )

            # Migration: Add applicant_name column to applications
            if "applicant_name" not in app_columns:
                cursor.execute(
                    "ALTER TABLE applications ADD COLUMN applicant_name TEXT"
                )

            # Migration: Add extraction_status column to documents
            cursor.execute("PRAGMA table_info(documents)")
            doc_columns = [col[1] for col in cursor.fetchall()]
            if "extraction_status" not in doc_columns:
                cursor.execute(
                    "ALTER TABLE documents ADD COLUMN extraction_status TEXT DEFAULT 'queued'"
                )

            # Migration: Add document processing pipeline columns
            # (re-read columns after possible ALTER above)
            cursor.execute("PRAGMA table_info(documents)")
            doc_columns = [col[1] for col in cursor.fetchall()]
            _new_doc_cols = {
                "mime_type": "TEXT DEFAULT ''",
                "uploaded_at": "TEXT",
                "processing_status": "TEXT DEFAULT 'queued'",
                "extract_method": "TEXT DEFAULT 'none'",
                "extracted_text_chars": "INTEGER DEFAULT 0",
                "extracted_text": "TEXT",
                "extracted_metadata_json": "TEXT",
                "is_plan_or_drawing": "INTEGER DEFAULT 0",
                "is_scanned": "INTEGER DEFAULT 0",
                "has_any_content_signal": "INTEGER DEFAULT 0",
                "failure_reason": "TEXT",
                "updated_at": "TEXT",
                "claimed_at": "TEXT",
                "claimed_by_pid": "INTEGER",
            }
            for col_name, col_type in _new_doc_cols.items():
                if col_name not in doc_columns:
                    cursor.execute(
                        f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}"
                    )

            # Index on processing_status for fast claim queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_doc_processing_status "
                "ON documents(processing_status)"
            )

            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER,
                    reference TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    notes TEXT,
                    conditions_json TEXT,
                    refusal_reasons_json TEXT,
                    actual_decision TEXT,
                    actual_decision_date TEXT,
                    submitted_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id)
                )
            """)

            # Run logs table (for continuous improvement)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS run_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL UNIQUE,
                    reference TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    council TEXT NOT NULL,
                    timestamp TEXT,
                    raw_decision TEXT,
                    calibrated_decision TEXT,
                    confidence REAL,
                    policy_ids_used TEXT,
                    docs_downloaded_count INTEGER DEFAULT 0,
                    similar_cases_count INTEGER DEFAULT 0,
                    total_duration_ms INTEGER DEFAULT 0,
                    steps_json TEXT,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    error_step TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Policy weights table (for deterministic re-ranking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS policy_weights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_id TEXT NOT NULL,
                    application_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    match_count INTEGER DEFAULT 0,
                    mismatch_count INTEGER DEFAULT 0,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(policy_id, application_type)
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_reference ON applications(reference)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_postcode ON applications(postcode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_ward ON applications(ward)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_reference ON documents(reference)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_hash ON documents(content_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reference ON feedback(reference)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_logs_reference ON run_logs(reference)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_logs_timestamp ON run_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_weights_type ON policy_weights(application_type)")

            conn.commit()

    # ========== Application CRUD ==========

    def save_application(self, app: StoredApplication) -> int:
        """Save or update an application.

        Args:
            app: Application to save

        Returns:
            Application ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO applications (
                    reference, council_id, council_name, address, proposal,
                    application_type, status, date_received, date_validated,
                    decision_date, decision, ward, postcode, constraints_json,
                    applicant_name, portal_url, portal_key, fetched_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reference) DO UPDATE SET
                    council_id = excluded.council_id,
                    council_name = excluded.council_name,
                    address = excluded.address,
                    proposal = excluded.proposal,
                    application_type = excluded.application_type,
                    status = excluded.status,
                    date_received = excluded.date_received,
                    date_validated = excluded.date_validated,
                    decision_date = excluded.decision_date,
                    decision = excluded.decision,
                    ward = excluded.ward,
                    postcode = excluded.postcode,
                    constraints_json = excluded.constraints_json,
                    applicant_name = excluded.applicant_name,
                    portal_url = excluded.portal_url,
                    portal_key = excluded.portal_key,
                    fetched_at = excluded.fetched_at,
                    updated_at = excluded.updated_at
            """, (
                app.reference, app.council_id, app.council_name,
                app.address, app.proposal,
                app.application_type, app.status, app.date_received,
                app.date_validated, app.decision_date, app.decision,
                app.ward, app.postcode, app.constraints_json,
                app.applicant_name, app.portal_url, app.portal_key,
                app.fetched_at, now, now
            ))

            conn.commit()

            # Get the ID
            cursor.execute("SELECT id FROM applications WHERE reference = ?", (app.reference,))
            row = cursor.fetchone()
            return row["id"] if row else -1

    def get_application(self, reference: str) -> Optional[StoredApplication]:
        """Get an application by reference.

        Args:
            reference: Application reference

        Returns:
            StoredApplication or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE reference = ?", (reference,))
            row = cursor.fetchone()

            if not row:
                return None

            return StoredApplication(**dict(row))

    def get_application_by_id(self, app_id: int) -> Optional[StoredApplication]:
        """Get an application by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            return StoredApplication(**dict(row)) if row else None

    def update_applicant_name(self, reference: str, applicant_name: str) -> None:
        """Update the applicant_name for an application (if not already set)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE applications SET applicant_name = ? "
                "WHERE reference = ? AND (applicant_name IS NULL OR applicant_name = '')",
                (applicant_name, reference),
            )
            conn.commit()

    def get_completed_applications(self, council_id: str = "", limit: int = 100) -> List[StoredApplication]:
        """Get applications that have a recorded decision, for use as precedent.

        Returns applications with a non-null decision, ordered by most recent
        decision date.  Optionally filtered by council_id.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if council_id:
                cursor.execute(
                    "SELECT * FROM applications WHERE decision IS NOT NULL "
                    "AND decision != '' AND council_id = ? "
                    "ORDER BY decision_date DESC LIMIT ?",
                    (council_id, limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM applications WHERE decision IS NOT NULL "
                    "AND decision != '' "
                    "ORDER BY decision_date DESC LIMIT ?",
                    (limit,),
                )
            return [StoredApplication(**dict(row)) for row in cursor.fetchall()]

    def search_applications(
        self,
        postcode: Optional[str] = None,
        ward: Optional[str] = None,
        status: Optional[str] = None,
        address_contains: Optional[str] = None,
        limit: int = 50,
    ) -> List[StoredApplication]:
        """Search for applications in the database.

        Args:
            postcode: Filter by postcode
            ward: Filter by ward
            status: Filter by status
            address_contains: Filter by address substring
            limit: Maximum results

        Returns:
            List of matching applications
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM applications WHERE 1=1"
            params = []

            if postcode:
                query += " AND postcode LIKE ?"
                params.append(f"%{postcode}%")
            if ward:
                query += " AND ward LIKE ?"
                params.append(f"%{ward}%")
            if status:
                query += " AND status = ?"
                params.append(status)
            if address_contains:
                query += " AND address LIKE ?"
                params.append(f"%{address_contains}%")

            query += f" ORDER BY created_at DESC LIMIT {limit}"

            cursor.execute(query, params)
            return [StoredApplication(**dict(row)) for row in cursor.fetchall()]

    # ========== Document CRUD ==========

    def save_document(self, doc: StoredDocument) -> int:
        """Save or update a document.

        Args:
            doc: Document to save

        Returns:
            Document ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO documents (
                    application_id, reference, doc_id, title, doc_type,
                    url, local_path, content_hash, size_bytes, content_type,
                    mime_type, date_published, downloaded_at, uploaded_at,
                    extraction_status, processing_status, extract_method,
                    extracted_text_chars, extracted_text, extracted_metadata_json,
                    is_plan_or_drawing, is_scanned, has_any_content_signal,
                    created_at
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?
                )
                ON CONFLICT(reference, doc_id) DO UPDATE SET
                    url = COALESCE(NULLIF(excluded.url, ''), documents.url),
                    local_path = COALESCE(excluded.local_path, documents.local_path),
                    content_hash = COALESCE(excluded.content_hash, documents.content_hash),
                    size_bytes = COALESCE(excluded.size_bytes, documents.size_bytes),
                    content_type = COALESCE(excluded.content_type, documents.content_type),
                    mime_type = COALESCE(NULLIF(excluded.mime_type, ''), documents.mime_type),
                    downloaded_at = COALESCE(excluded.downloaded_at, documents.downloaded_at),
                    uploaded_at = COALESCE(excluded.uploaded_at, documents.uploaded_at),
                    -- Never reset processing state for docs already processed/processing.
                    -- Only update if the existing doc is still in 'queued' or 'failed' state.
                    extraction_status = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.extraction_status
                        ELSE excluded.extraction_status
                    END,
                    processing_status = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.processing_status
                        ELSE excluded.processing_status
                    END,
                    extract_method = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.extract_method
                        ELSE excluded.extract_method
                    END,
                    extracted_text_chars = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.extracted_text_chars
                        ELSE excluded.extracted_text_chars
                    END,
                    extracted_text = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.extracted_text
                        ELSE excluded.extracted_text
                    END,
                    extracted_metadata_json = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.extracted_metadata_json
                        ELSE excluded.extracted_metadata_json
                    END,
                    is_plan_or_drawing = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.is_plan_or_drawing
                        ELSE excluded.is_plan_or_drawing
                    END,
                    is_scanned = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.is_scanned
                        ELSE excluded.is_scanned
                    END,
                    has_any_content_signal = CASE
                        WHEN documents.processing_status IN ('processed', 'processing')
                        THEN documents.has_any_content_signal
                        ELSE excluded.has_any_content_signal
                    END
            """, (
                doc.application_id, doc.reference, doc.doc_id, doc.title,
                doc.doc_type, doc.url, doc.local_path, doc.content_hash,
                doc.size_bytes, doc.content_type,
                doc.mime_type, doc.date_published, doc.downloaded_at,
                doc.uploaded_at,
                doc.extraction_status or "queued",
                doc.processing_status or "queued",
                doc.extract_method or "none",
                doc.extracted_text_chars,
                doc.extracted_text,
                doc.extracted_metadata_json,
                1 if doc.is_plan_or_drawing else 0,
                1 if doc.is_scanned else 0,
                1 if doc.has_any_content_signal else 0,
                now,
            ))

            conn.commit()
            _db_logger = get_logger("plana.storage")
            _db_logger.info(
                "doc_enqueued",
                reference=doc.reference,
                document_id=doc.doc_id,
                title=doc.title,
                processing_status=doc.processing_status or "queued",
            )
            return cursor.lastrowid or -1

    def resolve_reference(self, reference: str) -> Optional[str]:
        """Find the actual reference string stored in the DB.

        Tries the reference as-is, URL-decoded, stripped, uppercased,
        and case-insensitive LIKE to handle encoding/casing mismatches
        between the frontend and the stored data.

        Returns the stored reference on match, or None.
        """
        candidates = list(dict.fromkeys([
            reference,
            unquote(reference),
            reference.strip(),
            unquote(reference).strip(),
            reference.strip().upper(),
            unquote(reference).strip().upper(),
        ]))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for ref in candidates:
                cursor.execute(
                    "SELECT reference FROM documents WHERE reference = ? LIMIT 1",
                    (ref,),
                )
                row = cursor.fetchone()
                if row:
                    return row["reference"]
            # Last resort: case-insensitive LIKE
            base = unquote(reference).strip()
            cursor.execute(
                "SELECT reference FROM documents WHERE reference LIKE ? LIMIT 1",
                (base,),
            )
            row = cursor.fetchone()
            if row:
                return row["reference"]
        return None

    def get_documents(self, reference: str) -> List[StoredDocument]:
        """Get all documents for an application.

        Args:
            reference: Application reference

        Returns:
            List of documents
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE reference = ? ORDER BY created_at",
                (reference,)
            )
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                # SQLite stores bools as 0/1 — convert back
                for bool_col in ("is_plan_or_drawing", "is_scanned", "has_any_content_signal"):
                    if bool_col in data:
                        data[bool_col] = bool(data[bool_col])
                results.append(StoredDocument(**data))
            return results

    def get_extraction_counts(self, reference: str) -> dict:
        """Get document extraction status counts for an application.

        Args:
            reference: Application reference

        Returns:
            Dict with queued, extracted, failed counts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN extraction_status = 'queued' THEN 1 ELSE 0 END), 0) AS queued,
                    COALESCE(SUM(CASE WHEN extraction_status = 'extracted' THEN 1 ELSE 0 END), 0) AS extracted,
                    COALESCE(SUM(CASE WHEN extraction_status = 'failed' THEN 1 ELSE 0 END), 0) AS failed
                FROM documents
                WHERE reference = ?
            """, (reference,))
            row = cursor.fetchone()
            if row:
                return {
                    "queued": row["queued"],
                    "extracted": row["extracted"],
                    "failed": row["failed"],
                }
            return {"queued": 0, "extracted": 0, "failed": 0}

    def get_processing_counts(self, reference: str) -> dict:
        """Get document processing status counts for an application.

        Uses the new ``processing_status`` column which tracks the full
        lifecycle: queued → processing → processed → failed.

        Args:
            reference: Application reference

        Returns:
            Dict with total, queued, processing, processed, failed counts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN processing_status = 'queued' THEN 1 ELSE 0 END), 0) AS queued,
                    COALESCE(SUM(CASE WHEN processing_status = 'processing' THEN 1 ELSE 0 END), 0) AS processing,
                    COALESCE(SUM(CASE WHEN processing_status = 'processed' THEN 1 ELSE 0 END), 0) AS processed,
                    COALESCE(SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END), 0) AS failed,
                    COALESCE(SUM(extracted_text_chars), 0) AS total_text_chars,
                    COALESCE(SUM(CASE WHEN has_any_content_signal THEN 1 ELSE 0 END), 0) AS with_content_signal,
                    COALESCE(SUM(CASE WHEN is_plan_or_drawing THEN 1 ELSE 0 END), 0) AS plan_drawing_count
                FROM documents
                WHERE reference = ?
            """, (reference,))
            row = cursor.fetchone()
            if row:
                return {
                    "total": row["total"],
                    "queued": row["queued"],
                    "processing": row["processing"],
                    "processed": row["processed"],
                    "failed": row["failed"],
                    "total_text_chars": row["total_text_chars"],
                    "with_content_signal": row["with_content_signal"],
                    "plan_drawing_count": row["plan_drawing_count"],
                }
            return {
                "total": 0, "queued": 0, "processing": 0,
                "processed": 0, "failed": 0, "total_text_chars": 0,
                "with_content_signal": 0, "plan_drawing_count": 0,
            }

    def get_document_by_doc_id(self, doc_id: str) -> Optional[StoredDocument]:
        """Get a single document by its doc_id.

        Args:
            doc_id: The document identifier

        Returns:
            StoredDocument or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE doc_id = ?",
                (doc_id,)
            )
            row = cursor.fetchone()
            if row:
                data = dict(row)
                for bool_col in ("is_plan_or_drawing", "is_scanned", "has_any_content_signal"):
                    if bool_col in data:
                        data[bool_col] = bool(data[bool_col])
                return StoredDocument(**data)
            return None

    def get_extracted_texts(self, reference: str) -> List[dict]:
        """Get extracted text from processed documents for a reference.

        Returns a list of dicts with title, extracted_text, extracted_text_chars,
        and is_plan_or_drawing for each document that has text.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, extracted_text, extracted_text_chars,
                       is_plan_or_drawing, extract_method
                FROM documents
                WHERE reference = ?
                  AND processing_status = 'processed'
                  AND extracted_text IS NOT NULL
                  AND extracted_text_chars > 0
                ORDER BY extracted_text_chars DESC
            """, (reference,))
            return [
                {
                    "title": row["title"],
                    "extracted_text": row["extracted_text"],
                    "chars": row["extracted_text_chars"],
                    "is_plan": bool(row["is_plan_or_drawing"]),
                    "method": row["extract_method"],
                }
                for row in cursor.fetchall()
            ]

    def get_documents_debug(self, reference: str) -> dict:
        """Get detailed debug info for documents belonging to a reference.

        Returns counts, a sample of up to 10 documents, and the oldest
        queued/processing timestamps so operators can see exactly what is
        stuck and why.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Counts
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN processing_status='queued' THEN 1 ELSE 0 END),0) AS queued,
                    COALESCE(SUM(CASE WHEN processing_status='processing' THEN 1 ELSE 0 END),0) AS processing,
                    COALESCE(SUM(CASE WHEN processing_status='processed' THEN 1 ELSE 0 END),0) AS processed,
                    COALESCE(SUM(CASE WHEN processing_status='failed' THEN 1 ELSE 0 END),0) AS failed
                FROM documents WHERE reference = ?
            """, (reference,))
            counts_row = cursor.fetchone()
            counts = dict(counts_row) if counts_row else {
                "total": 0, "queued": 0, "processing": 0,
                "processed": 0, "failed": 0,
            }

            # Sample of up to 10 docs (most recently updated first)
            cursor.execute("""
                SELECT id, doc_id, title, processing_status,
                       updated_at, claimed_at, claimed_by_pid,
                       failure_reason, url, local_path,
                       extract_method, extracted_text_chars
                FROM documents
                WHERE reference = ?
                ORDER BY
                    CASE processing_status
                        WHEN 'processing' THEN 0
                        WHEN 'queued' THEN 1
                        WHEN 'failed' THEN 2
                        ELSE 3
                    END,
                    COALESCE(updated_at, created_at) DESC
                LIMIT 10
            """, (reference,))
            docs = []
            for row in cursor.fetchall():
                docs.append({
                    "id": row["id"],
                    "doc_id": row["doc_id"],
                    "filename": row["title"],
                    "status": row["processing_status"],
                    "updated_at": row["updated_at"],
                    "claimed_at": row["claimed_at"],
                    "claimed_by_pid": row["claimed_by_pid"],
                    "fail_reason": row["failure_reason"],
                    "url": row["url"],
                    "local_path": row["local_path"],
                    "extract_method": row["extract_method"],
                    "extracted_text_chars": row["extracted_text_chars"],
                })

            # Oldest queued
            cursor.execute("""
                SELECT MIN(COALESCE(updated_at, created_at)) AS oldest
                FROM documents
                WHERE reference = ? AND processing_status = 'queued'
            """, (reference,))
            oldest_queued_row = cursor.fetchone()
            oldest_queued = oldest_queued_row["oldest"] if oldest_queued_row else None

            # Oldest processing
            cursor.execute("""
                SELECT MIN(claimed_at) AS oldest
                FROM documents
                WHERE reference = ? AND processing_status = 'processing'
            """, (reference,))
            oldest_proc_row = cursor.fetchone()
            oldest_processing = oldest_proc_row["oldest"] if oldest_proc_row else None

            return {
                "reference": reference,
                "counts": counts,
                "documents": docs,
                "oldest_queued_at": oldest_queued,
                "oldest_processing_at": oldest_processing,
            }

    def get_document_by_hash(self, content_hash: str) -> Optional[StoredDocument]:
        """Get a document by its content hash (for deduplication).

        Args:
            content_hash: MD5 hash of document content

        Returns:
            StoredDocument or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            return StoredDocument(**dict(row)) if row else None

    def reset_documents_for_reference(self, reference: str) -> int:
        """Reset all documents for a reference back to queued state.

        Clears extracted fields (text chars, metadata, content signal,
        flags) and sets processing_status/extraction_status back to
        'queued' so they can be reprocessed.

        Args:
            reference: Application reference

        Returns:
            Number of documents reset
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'queued',
                    extraction_status = 'queued',
                    extract_method = 'none',
                    extracted_text_chars = 0,
                    extracted_text = NULL,
                    extracted_metadata_json = NULL,
                    has_any_content_signal = 0,
                    is_scanned = 0,
                    failure_reason = NULL
                WHERE reference = ?
            """, (reference,))
            conn.commit()
            _db_logger = get_logger("plana.storage")
            _db_logger.info(
                "docs_requeued",
                reference=reference,
                reset_count=cursor.rowcount,
            )
            return cursor.rowcount

    def reset_stalled_for_reference(self, reference: str) -> int:
        """Reset only queued and failed documents for a reference.

        Unlike ``reset_documents_for_reference`` which resets *all*
        documents (including already-processed ones), this only touches
        documents in ``queued`` or ``failed`` state — i.e. the ones that
        are stuck and need re-processing.

        Returns:
            Number of documents reset.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'queued',
                    extraction_status = 'queued',
                    extract_method = 'none',
                    extracted_text_chars = 0,
                    extracted_text = NULL,
                    extracted_metadata_json = NULL,
                    has_any_content_signal = 0,
                    is_scanned = 0,
                    failure_reason = NULL
                WHERE reference = ?
                  AND processing_status IN ('queued', 'failed')
            """, (reference,))
            conn.commit()
            _db_logger = get_logger("plana.storage")
            _db_logger.info(
                "docs_requeued_stalled",
                reference=reference,
                reset_count=cursor.rowcount,
            )
            return cursor.rowcount

    def force_process_urlless_documents(self, reference: str) -> int:
        """Mark all URL-less documents as 'processed' with method 'filename_only'.

        Documents without a download URL cannot be fetched by the background
        worker, so leaving them as 'queued' means they stay stuck forever.
        This method marks them as processed so report generation can proceed.

        Documents that DO have a URL are left in their current state
        (queued/processing) for the background worker to handle.

        Args:
            reference: Application reference

        Returns:
            Number of documents force-processed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'processed',
                    extraction_status = 'extracted',
                    extract_method = 'filename_only',
                    has_any_content_signal = CASE
                        WHEN title LIKE '%plan%' OR title LIKE '%elevation%'
                             OR title LIKE '%section%' OR title LIKE '%drawing%'
                             OR title LIKE '%layout%' OR title LIKE '%floor%'
                             OR title LIKE '%site%' OR title LIKE '%block%'
                             OR title LIKE '%location%' OR title LIKE '%street%'
                        THEN 1 ELSE 0 END,
                    is_plan_or_drawing = CASE
                        WHEN title LIKE '%plan%' OR title LIKE '%elevation%'
                             OR title LIKE '%section%' OR title LIKE '%drawing%'
                             OR title LIKE '%layout%' OR title LIKE '%floor%'
                             OR title LIKE '%site%' OR title LIKE '%block%'
                             OR title LIKE '%location%'
                        THEN 1 ELSE 0 END
                WHERE reference = ?
                  AND (url IS NULL OR url = '')
                  AND processing_status IN ('queued', 'failed')
            """, (reference,))
            conn.commit()
            _db_logger = get_logger("plana.storage")
            _db_logger.info(
                "docs_force_processed_urlless",
                reference=reference,
                count=cursor.rowcount,
            )
            return cursor.rowcount

    def force_process_all_documents(self, reference: str) -> int:
        """Mark ALL queued/failed documents as 'processed' for a reference.

        Unlike ``force_process_urlless_documents`` which only touches URL-less
        docs, this method force-processes **every** stuck document — including
        those with URLs that the background worker could not download.

        Use this as a last resort when the background worker has been unable
        to make progress (e.g. portal URLs are unreachable).

        Args:
            reference: Application reference

        Returns:
            Number of documents force-processed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'processed',
                    extraction_status = 'extracted',
                    extract_method = CASE
                        WHEN url IS NOT NULL AND url != '' THEN 'url_unreachable'
                        ELSE 'filename_only'
                    END,
                    has_any_content_signal = CASE
                        WHEN title LIKE '%plan%' OR title LIKE '%elevation%'
                             OR title LIKE '%section%' OR title LIKE '%drawing%'
                             OR title LIKE '%layout%' OR title LIKE '%floor%'
                             OR title LIKE '%site%' OR title LIKE '%block%'
                             OR title LIKE '%location%' OR title LIKE '%street%'
                        THEN 1 ELSE 0 END,
                    is_plan_or_drawing = CASE
                        WHEN title LIKE '%plan%' OR title LIKE '%elevation%'
                             OR title LIKE '%section%' OR title LIKE '%drawing%'
                             OR title LIKE '%layout%' OR title LIKE '%floor%'
                             OR title LIKE '%site%' OR title LIKE '%block%'
                             OR title LIKE '%location%'
                        THEN 1 ELSE 0 END
                WHERE reference = ?
                  AND processing_status IN ('queued', 'failed', 'processing')
            """, (reference,))
            conn.commit()
            _db_logger = get_logger("plana.storage")
            _db_logger.info(
                "docs_force_processed_all",
                reference=reference,
                count=cursor.rowcount,
            )
            return cursor.rowcount

    def reset_single_document(self, doc_id: str) -> bool:
        """Reset a single document back to queued state.

        Clears extracted fields and sets processing_status back to
        'queued' so it can be reprocessed.

        Args:
            doc_id: The document identifier

        Returns:
            True if a document was found and reset, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'queued',
                    extraction_status = 'queued',
                    extract_method = 'none',
                    extracted_text_chars = 0,
                    extracted_text = NULL,
                    extracted_metadata_json = NULL,
                    has_any_content_signal = 0,
                    is_scanned = 0,
                    failure_reason = NULL
                WHERE doc_id = ?
            """, (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

    def recover_stale_processing(self, max_age_seconds: int = 300) -> int:
        """Re-queue documents stuck in 'processing' for longer than *max_age_seconds*.

        This handles the case where the worker/process crashed or was
        redeployed while a document was mid-processing.  Since we have
        no ``claimed_at`` timestamp the heuristic is simple: if *any*
        documents are in ``processing`` state we re-queue them all,
        because the in-process worker only claims one at a time and
        finishes quickly.

        Returns:
            Number of documents recovered.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents
                SET processing_status = 'queued'
                WHERE processing_status = 'processing'
            """)
            conn.commit()
            count = cursor.rowcount
            if count:
                _db_logger = get_logger("plana.storage")
                _db_logger.info(
                    "docs_recovered_from_processing",
                    recovered_count=count,
                )
            return count

    def claim_queued_document(self) -> Optional[StoredDocument]:
        """Atomically claim one queued document for processing.

        Alias for claim_next_document() — kept for backwards compatibility.
        """
        return self.claim_next_document()

    def claim_next_document(self) -> Optional[StoredDocument]:
        """Atomically claim one queued document for processing.

        Uses a single transaction to:
        1. SELECT the target row id (oldest queued)
        2. UPDATE that specific row to 'processing'
        3. Re-SELECT the claimed row by its id

        This prevents the race where a second SELECT could return a
        different 'processing' row claimed by another worker.

        Returns None when no queued documents remain.
        """
        import os
        now = datetime.now().isoformat()
        pid = os.getpid()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Step 1: Find the target row (use `id` — the INTEGER PRIMARY KEY)
            cursor.execute("""
                SELECT id FROM documents
                WHERE processing_status = 'queued'
                ORDER BY id
                LIMIT 1
            """)
            target = cursor.fetchone()
            if target is None:
                return None

            target_id = target["id"]

            # Step 2: Claim it (atomic within this connection's implicit txn)
            cursor.execute("""
                UPDATE documents
                SET processing_status = 'processing',
                    claimed_at = ?,
                    claimed_by_pid = ?,
                    updated_at = ?
                WHERE id = ?
                  AND processing_status = 'queued'
            """, (now, pid, now, target_id))

            if cursor.rowcount == 0:
                # Another worker got it between SELECT and UPDATE —
                # commit (no-op) and return None; caller will retry.
                conn.commit()
                return None

            # Step 3: Fetch the exact row we claimed
            cursor.execute(
                "SELECT * FROM documents WHERE id = ?",
                (target_id,),
            )
            row = cursor.fetchone()
            conn.commit()

            if row:
                data = dict(row)
                for bool_col in ("is_plan_or_drawing", "is_scanned", "has_any_content_signal"):
                    if bool_col in data:
                        data[bool_col] = bool(data[bool_col])
                return StoredDocument(**data)
            return None

    def mark_document_processed(
        self,
        doc_id: str,
        *,
        extract_method: str,
        extracted_text_chars: int,
        extracted_text: Optional[str] = None,
        extracted_metadata_json: Optional[str] = None,
        is_plan_or_drawing: bool = False,
        is_scanned: bool = False,
        has_any_content_signal: bool = False,
    ) -> None:
        """Mark a document as successfully processed."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'processed',
                    extraction_status = 'extracted',
                    extract_method = ?,
                    extracted_text_chars = ?,
                    extracted_text = ?,
                    extracted_metadata_json = ?,
                    is_plan_or_drawing = ?,
                    is_scanned = ?,
                    has_any_content_signal = ?,
                    updated_at = ?
                WHERE doc_id = ?
            """, (
                extract_method,
                extracted_text_chars,
                extracted_text,
                extracted_metadata_json,
                1 if is_plan_or_drawing else 0,
                1 if is_scanned else 0,
                1 if has_any_content_signal else 0,
                now,
                doc_id,
            ))
            conn.commit()

    def mark_document_failed(self, doc_id: str, *, reason: str = "") -> None:
        """Mark a document as failed processing.

        Args:
            doc_id: Document identifier.
            reason: Human-readable failure reason (exception message, etc.).
        """
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET
                    processing_status = 'failed',
                    extraction_status = 'failed',
                    failure_reason = ?,
                    updated_at = ?
                WHERE doc_id = ?
            """, (reason or None, now, doc_id))
            conn.commit()

    def update_document_local_path(self, doc_id: str, local_path: str) -> None:
        """Update the local_path for a document after downloading."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents SET local_path = ? WHERE doc_id = ?
            """, (local_path, doc_id))
            conn.commit()

    # ========== Report CRUD ==========

    def save_report(self, report: StoredReport) -> int:
        """Save a generated report.

        Args:
            report: Report to save

        Returns:
            Report ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO reports (
                    application_id, reference, report_path, recommendation,
                    confidence, policies_cited, similar_cases_count,
                    generation_mode, generated_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.application_id, report.reference, report.report_path,
                report.recommendation, report.confidence, report.policies_cited,
                report.similar_cases_count, report.generation_mode,
                report.generated_at or now, now
            ))

            conn.commit()
            return cursor.lastrowid or -1

    def get_reports(self, reference: str) -> List[StoredReport]:
        """Get all reports for an application.

        Args:
            reference: Application reference

        Returns:
            List of reports
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM reports WHERE reference = ? ORDER BY created_at DESC",
                (reference,)
            )
            return [StoredReport(**dict(row)) for row in cursor.fetchall()]

    # ========== Feedback CRUD ==========

    def save_feedback(self, feedback: StoredFeedback) -> int:
        """Save user feedback.

        Args:
            feedback: Feedback to save

        Returns:
            Feedback ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO feedback (
                    application_id, reference, decision, notes,
                    conditions_json, refusal_reasons_json,
                    actual_decision, actual_decision_date,
                    submitted_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.application_id, feedback.reference, feedback.decision,
                feedback.notes, feedback.conditions_json, feedback.refusal_reasons_json,
                feedback.actual_decision, feedback.actual_decision_date,
                feedback.submitted_by, now
            ))

            conn.commit()
            return cursor.lastrowid or -1

    def get_feedback(self, reference: str) -> List[StoredFeedback]:
        """Get all feedback for an application.

        Args:
            reference: Application reference

        Returns:
            List of feedback entries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM feedback WHERE reference = ? ORDER BY created_at DESC",
                (reference,)
            )
            return [StoredFeedback(**dict(row)) for row in cursor.fetchall()]

    def get_all_feedback(self, limit: int = 100) -> List[StoredFeedback]:
        """Get all feedback entries.

        Args:
            limit: Maximum results

        Returns:
            List of feedback entries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM feedback ORDER BY created_at DESC LIMIT {limit}"
            )
            return [StoredFeedback(**dict(row)) for row in cursor.fetchall()]

    # ========== Run Logs CRUD ==========

    def save_run_log(self, run_log: StoredRunLog) -> int:
        """Save a pipeline run log.

        Args:
            run_log: Run log to save

        Returns:
            Run log ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO run_logs (
                    run_id, reference, mode, council, timestamp,
                    raw_decision, calibrated_decision, confidence,
                    policy_ids_used, docs_downloaded_count, similar_cases_count,
                    total_duration_ms, steps_json, success, error_message,
                    error_step, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    raw_decision = excluded.raw_decision,
                    calibrated_decision = excluded.calibrated_decision,
                    confidence = excluded.confidence,
                    policy_ids_used = excluded.policy_ids_used,
                    docs_downloaded_count = excluded.docs_downloaded_count,
                    similar_cases_count = excluded.similar_cases_count,
                    total_duration_ms = excluded.total_duration_ms,
                    steps_json = excluded.steps_json,
                    success = excluded.success,
                    error_message = excluded.error_message,
                    error_step = excluded.error_step
            """, (
                run_log.run_id, run_log.reference, run_log.mode, run_log.council,
                run_log.timestamp or now, run_log.raw_decision, run_log.calibrated_decision,
                run_log.confidence, run_log.policy_ids_used, run_log.docs_downloaded_count,
                run_log.similar_cases_count, run_log.total_duration_ms, run_log.steps_json,
                1 if run_log.success else 0, run_log.error_message, run_log.error_step, now
            ))

            conn.commit()
            return cursor.lastrowid or -1

    def get_run_log(self, run_id: str) -> Optional[StoredRunLog]:
        """Get a run log by ID.

        Args:
            run_id: Run ID

        Returns:
            StoredRunLog or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM run_logs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data['success'] = bool(data.get('success', 1))
            return StoredRunLog(**data)

    def get_run_logs_for_reference(self, reference: str, limit: int = 10) -> List[StoredRunLog]:
        """Get run logs for a reference.

        Args:
            reference: Application reference
            limit: Maximum results

        Returns:
            List of run logs
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM run_logs WHERE reference = ? ORDER BY timestamp DESC LIMIT ?",
                (reference, limit)
            )
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data['success'] = bool(data.get('success', 1))
                results.append(StoredRunLog(**data))
            return results

    def get_run_logs_by_type(
        self,
        application_type: str,
        success_only: bool = True,
        limit: int = 100,
    ) -> List[StoredRunLog]:
        """Get run logs for a specific application type.

        Args:
            application_type: Application type code (e.g., HOU, LBC)
            success_only: Only return successful runs
            limit: Maximum results

        Returns:
            List of run logs
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Extract type from reference (last part after /)
            pattern = f"%/{application_type}"
            query = "SELECT * FROM run_logs WHERE reference LIKE ?"
            if success_only:
                query += " AND success = 1"
            query += f" ORDER BY timestamp DESC LIMIT {limit}"

            cursor.execute(query, (pattern,))
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data['success'] = bool(data.get('success', 1))
                results.append(StoredRunLog(**data))
            return results

    # ========== Policy Weights CRUD ==========

    def save_policy_weight(self, weight: StoredPolicyWeight) -> int:
        """Save or update a policy weight.

        Args:
            weight: Policy weight to save

        Returns:
            Weight ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO policy_weights (
                    policy_id, application_type, weight, match_count,
                    mismatch_count, last_updated, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(policy_id, application_type) DO UPDATE SET
                    weight = excluded.weight,
                    match_count = excluded.match_count,
                    mismatch_count = excluded.mismatch_count,
                    last_updated = excluded.last_updated
            """, (
                weight.policy_id, weight.application_type, weight.weight,
                weight.match_count, weight.mismatch_count, now, now
            ))

            conn.commit()
            return cursor.lastrowid or -1

    def get_policy_weight(
        self,
        policy_id: str,
        application_type: str,
    ) -> Optional[StoredPolicyWeight]:
        """Get a policy weight.

        Args:
            policy_id: Policy ID
            application_type: Application type code

        Returns:
            StoredPolicyWeight or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM policy_weights WHERE policy_id = ? AND application_type = ?",
                (policy_id, application_type)
            )
            row = cursor.fetchone()
            return StoredPolicyWeight(**dict(row)) if row else None

    def get_policy_weights_for_type(
        self,
        application_type: str,
    ) -> List[StoredPolicyWeight]:
        """Get all policy weights for an application type.

        Args:
            application_type: Application type code

        Returns:
            List of policy weights
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM policy_weights WHERE application_type = ? ORDER BY weight DESC",
                (application_type,)
            )
            return [StoredPolicyWeight(**dict(row)) for row in cursor.fetchall()]

    def increment_policy_match(
        self,
        policy_id: str,
        application_type: str,
        is_match: bool,
    ) -> None:
        """Increment match or mismatch count for a policy.

        Args:
            policy_id: Policy ID
            application_type: Application type code
            is_match: Whether this was a correct match
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            if is_match:
                cursor.execute("""
                    INSERT INTO policy_weights (policy_id, application_type, match_count, last_updated, created_at)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(policy_id, application_type) DO UPDATE SET
                        match_count = match_count + 1,
                        weight = 1.0 + (CAST(match_count + 1 AS REAL) / (match_count + mismatch_count + 1)) * 0.5,
                        last_updated = excluded.last_updated
                """, (policy_id, application_type, now, now))
            else:
                cursor.execute("""
                    INSERT INTO policy_weights (policy_id, application_type, mismatch_count, last_updated, created_at)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(policy_id, application_type) DO UPDATE SET
                        mismatch_count = mismatch_count + 1,
                        weight = 1.0 + (CAST(match_count AS REAL) / (match_count + mismatch_count + 1)) * 0.5 - 0.1,
                        last_updated = excluded.last_updated
                """, (policy_id, application_type, now, now))

            conn.commit()

    # ========== Statistics ==========

    def get_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dictionary with counts and statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM applications")
            app_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reports")
            report_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM feedback")
            feedback_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM run_logs")
            run_log_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM run_logs WHERE success = 1")
            successful_runs = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(size_bytes) FROM documents")
            total_size = cursor.fetchone()[0] or 0

            return {
                "applications": app_count,
                "documents": doc_count,
                "reports": report_count,
                "feedback": feedback_count,
                "run_logs": run_log_count,
                "successful_runs": successful_runs,
                "total_document_size_mb": round(total_size / (1024 * 1024), 2),
            }


# Singleton instance
_database: Optional[Database] = None


def get_database(db_path: Optional[Path] = None) -> Database:
    """Get the database instance (singleton).

    Args:
        db_path: Optional path to database file

    Returns:
        Database instance
    """
    global _database
    if _database is None:
        _database = Database(db_path)
    return _database
