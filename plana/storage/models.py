"""
Storage models for SQLite persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class StoredApplication:
    """An application stored in the database."""

    id: Optional[int] = None
    reference: str = ""
    council_id: str = ""
    address: str = ""
    proposal: str = ""
    application_type: str = ""
    status: str = ""
    date_received: Optional[str] = None
    date_validated: Optional[str] = None
    decision_date: Optional[str] = None
    decision: Optional[str] = None
    ward: Optional[str] = None
    postcode: Optional[str] = None
    constraints_json: str = "[]"
    portal_url: Optional[str] = None
    portal_key: Optional[str] = None
    fetched_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class StoredDocument:
    """A document stored in the database."""

    id: Optional[int] = None
    application_id: Optional[int] = None
    reference: str = ""
    doc_id: str = ""
    title: str = ""
    doc_type: str = ""
    url: str = ""
    local_path: Optional[str] = None
    content_hash: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    date_published: Optional[str] = None
    downloaded_at: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class StoredReport:
    """A generated report stored in the database."""

    id: Optional[int] = None
    application_id: Optional[int] = None
    reference: str = ""
    report_path: str = ""
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    policies_cited: int = 0
    similar_cases_count: int = 0
    generation_mode: str = "demo"  # demo or live
    generated_at: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class StoredFeedback:
    """User feedback stored in the database."""

    id: Optional[int] = None
    application_id: Optional[int] = None
    reference: str = ""
    decision: str = ""  # APPROVE, APPROVE_WITH_CONDITIONS, REFUSE
    notes: Optional[str] = None
    conditions_json: Optional[str] = None  # JSON array of conditions
    refusal_reasons_json: Optional[str] = None  # JSON array of reasons
    actual_decision: Optional[str] = None  # Actual decision if known
    actual_decision_date: Optional[str] = None
    submitted_by: Optional[str] = None
    created_at: Optional[str] = None
