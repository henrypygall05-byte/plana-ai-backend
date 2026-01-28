"""
SQLite database for Plana.AI storage.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from plana.storage.models import (
    StoredApplication,
    StoredDocument,
    StoredFeedback,
    StoredReport,
)


class Database:
    """SQLite database for storing applications, documents, and feedback."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.plana/plana.db
        """
        if db_path is None:
            db_path = Path.home() / ".plana" / "plana.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
                    generated_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id)
                )
            """)

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

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_reference ON applications(reference)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_postcode ON applications(postcode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_ward ON applications(ward)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_reference ON documents(reference)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_hash ON documents(content_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reference ON feedback(reference)")

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
                    reference, council_id, address, proposal, application_type,
                    status, date_received, date_validated, decision_date, decision,
                    ward, postcode, constraints_json, portal_url, portal_key,
                    fetched_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reference) DO UPDATE SET
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
                    portal_url = excluded.portal_url,
                    portal_key = excluded.portal_key,
                    fetched_at = excluded.fetched_at,
                    updated_at = excluded.updated_at
            """, (
                app.reference, app.council_id, app.address, app.proposal,
                app.application_type, app.status, app.date_received,
                app.date_validated, app.decision_date, app.decision,
                app.ward, app.postcode, app.constraints_json,
                app.portal_url, app.portal_key, app.fetched_at,
                now, now
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
                    date_published, downloaded_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reference, doc_id) DO UPDATE SET
                    local_path = excluded.local_path,
                    content_hash = excluded.content_hash,
                    size_bytes = excluded.size_bytes,
                    content_type = excluded.content_type,
                    downloaded_at = excluded.downloaded_at
            """, (
                doc.application_id, doc.reference, doc.doc_id, doc.title,
                doc.doc_type, doc.url, doc.local_path, doc.content_hash,
                doc.size_bytes, doc.content_type, doc.date_published,
                doc.downloaded_at, now
            ))

            conn.commit()
            return cursor.lastrowid or -1

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
            return [StoredDocument(**dict(row)) for row in cursor.fetchall()]

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

            cursor.execute("SELECT SUM(size_bytes) FROM documents")
            total_size = cursor.fetchone()[0] or 0

            return {
                "applications": app_count,
                "documents": doc_count,
                "reports": report_count,
                "feedback": feedback_count,
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
