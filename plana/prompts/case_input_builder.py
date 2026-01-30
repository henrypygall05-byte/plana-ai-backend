"""
CASE_INPUT builder for Plana Case Officer prompt.

Constructs the structured input object from pipeline artifacts.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from plana.prompts.loader import DEFAULT_PROMPT_VERSION, DEFAULT_SCHEMA_VERSION


@dataclass
class CaseInputApplication:
    """Application metadata for CASE_INPUT."""

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
    applicant_name: Optional[str] = None
    agent_name: Optional[str] = None


@dataclass
class CaseInputConstraint:
    """Constraint for CASE_INPUT."""

    constraint_type: str
    name: str
    distance_m: Optional[float] = None
    source: str = "metadata"


@dataclass
class CaseInputDocument:
    """Document for CASE_INPUT."""

    doc_id: str
    document_title: str
    document_type: str = "other"
    published_date: Optional[str] = None
    file_type: str = "pdf"
    source_url: Optional[str] = None
    provenance: str = "manual intake"
    storage_key: str = ""
    hash: str = ""
    size_bytes: Optional[int] = None
    extracted_text: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.extracted_text is None:
            self.extracted_text = []


@dataclass
class CaseInputPolicy:
    """Policy chunk for CASE_INPUT."""

    policy_id: str
    policy_name: str
    policy_source: str
    chunk_id: str = ""
    text: str = ""
    page: Optional[int] = None
    score: float = 0.0


@dataclass
class CaseInputSimilarCase:
    """Similar case for CASE_INPUT."""

    case_id: str
    council_id: str
    reference: str
    address: str = ""
    proposal: str = ""
    outcome: Optional[str] = None
    decision_date: Optional[str] = None
    distance_km: Optional[float] = None
    similarity_score: float = 0.0
    reason_features: List[str] = None
    evidence_snippets: List[str] = None

    def __post_init__(self):
        if self.reason_features is None:
            self.reason_features = []
        if self.evidence_snippets is None:
            self.evidence_snippets = []


@dataclass
class CaseInputHistory:
    """Planning history entry for CASE_INPUT."""

    reference: str
    proposal: str
    decision: str
    decision_date: str


class CaseInputBuilder:
    """
    Builder for constructing CASE_INPUT objects.

    Usage:
        builder = CaseInputBuilder(run_id, council_id, reference, mode)
        builder.set_application(address=..., proposal=...)
        builder.add_constraint(constraint_type=..., name=...)
        builder.add_document(doc_id=..., title=...)
        builder.add_policy(policy_id=..., name=...)
        builder.add_similar_case(case_id=..., reference=...)
        case_input = builder.build()
    """

    def __init__(
        self,
        run_id: str,
        council_id: str,
        reference: str,
        mode: str = "demo",
    ):
        """Initialize the builder.

        Args:
            run_id: Unique run identifier
            council_id: Council ID (e.g., 'newcastle')
            reference: Application reference
            mode: Processing mode ('demo' or 'live')
        """
        self.run_id = run_id
        self.council_id = council_id
        self.reference = reference
        self.mode = mode

        self.feature_flags: Dict[str, str] = {
            "NEWCASTLE_PORTAL_FETCH": "manual",
        }
        self.application = CaseInputApplication()
        self.constraints: List[CaseInputConstraint] = []
        self.documents: List[CaseInputDocument] = []
        self.policies: List[CaseInputPolicy] = []
        self.similar_cases: List[CaseInputSimilarCase] = []
        self.history: List[CaseInputHistory] = []
        self.previous_runs: List[Dict[str, Any]] = []
        self.feedback: List[Dict[str, Any]] = []

    def set_feature_flag(self, key: str, value: str) -> "CaseInputBuilder":
        """Set a feature flag."""
        self.feature_flags[key] = value
        return self

    def set_application(
        self,
        address: str = "",
        proposal: str = "",
        application_type: str = "",
        status: str = "",
        date_received: Optional[str] = None,
        date_validated: Optional[str] = None,
        decision_date: Optional[str] = None,
        decision: Optional[str] = None,
        ward: Optional[str] = None,
        postcode: Optional[str] = None,
        applicant_name: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> "CaseInputBuilder":
        """Set application metadata."""
        self.application = CaseInputApplication(
            address=address,
            proposal=proposal,
            application_type=application_type,
            status=status,
            date_received=date_received,
            date_validated=date_validated,
            decision_date=decision_date,
            decision=decision,
            ward=ward,
            postcode=postcode,
            applicant_name=applicant_name,
            agent_name=agent_name,
        )
        return self

    def add_constraint(
        self,
        constraint_type: str,
        name: str,
        distance_m: Optional[float] = None,
        source: str = "metadata",
    ) -> "CaseInputBuilder":
        """Add a site constraint."""
        self.constraints.append(
            CaseInputConstraint(
                constraint_type=constraint_type,
                name=name,
                distance_m=distance_m,
                source=source,
            )
        )
        return self

    def add_document(
        self,
        doc_id: str,
        document_title: str,
        document_type: str = "other",
        published_date: Optional[str] = None,
        file_type: str = "pdf",
        source_url: Optional[str] = None,
        provenance: str = "manual intake",
        storage_key: str = "",
        hash: str = "",
        size_bytes: Optional[int] = None,
        extracted_text: Optional[List[Dict[str, Any]]] = None,
    ) -> "CaseInputBuilder":
        """Add a document."""
        self.documents.append(
            CaseInputDocument(
                doc_id=doc_id,
                document_title=document_title,
                document_type=document_type,
                published_date=published_date,
                file_type=file_type,
                source_url=source_url,
                provenance=provenance,
                storage_key=storage_key,
                hash=hash,
                size_bytes=size_bytes,
                extracted_text=extracted_text or [],
            )
        )
        return self

    def add_policy(
        self,
        policy_id: str,
        policy_name: str,
        policy_source: str,
        chunk_id: str = "",
        text: str = "",
        page: Optional[int] = None,
        score: float = 0.0,
    ) -> "CaseInputBuilder":
        """Add a policy chunk."""
        self.policies.append(
            CaseInputPolicy(
                policy_id=policy_id,
                policy_name=policy_name,
                policy_source=policy_source,
                chunk_id=chunk_id,
                text=text,
                page=page,
                score=score,
            )
        )
        return self

    def add_similar_case(
        self,
        case_id: str,
        council_id: str,
        reference: str,
        address: str = "",
        proposal: str = "",
        outcome: Optional[str] = None,
        decision_date: Optional[str] = None,
        distance_km: Optional[float] = None,
        similarity_score: float = 0.0,
        reason_features: Optional[List[str]] = None,
        evidence_snippets: Optional[List[str]] = None,
    ) -> "CaseInputBuilder":
        """Add a similar case."""
        self.similar_cases.append(
            CaseInputSimilarCase(
                case_id=case_id,
                council_id=council_id,
                reference=reference,
                address=address,
                proposal=proposal,
                outcome=outcome,
                decision_date=decision_date,
                distance_km=distance_km,
                similarity_score=similarity_score,
                reason_features=reason_features or [],
                evidence_snippets=evidence_snippets or [],
            )
        )
        return self

    def add_history(
        self,
        reference: str,
        proposal: str,
        decision: str,
        decision_date: str,
    ) -> "CaseInputBuilder":
        """Add a planning history entry."""
        self.history.append(
            CaseInputHistory(
                reference=reference,
                proposal=proposal,
                decision=decision,
                decision_date=decision_date,
            )
        )
        return self

    def add_previous_run(
        self,
        run_id: str,
        generated_at: str,
        recommendation: str,
        confidence: float,
    ) -> "CaseInputBuilder":
        """Add a previous run for comparison."""
        self.previous_runs.append({
            "run_id": run_id,
            "generated_at": generated_at,
            "recommendation": recommendation,
            "confidence": confidence,
        })
        return self

    def add_feedback(
        self,
        feedback_id: str,
        field: str,
        original_value: str,
        corrected_value: str,
        reason: str,
        submitted_by: str,
        submitted_at: str,
    ) -> "CaseInputBuilder":
        """Add user feedback from previous runs."""
        self.feedback.append({
            "feedback_id": feedback_id,
            "field": field,
            "original_value": original_value,
            "corrected_value": corrected_value,
            "reason": reason,
            "submitted_by": submitted_by,
            "submitted_at": submitted_at,
        })
        return self

    def build(self) -> Dict[str, Any]:
        """Build the CASE_INPUT object.

        Returns:
            Complete CASE_INPUT dictionary
        """
        return {
            "run_id": self.run_id,
            "council_id": self.council_id,
            "reference": self.reference,
            "mode": self.mode,
            "feature_flags": self.feature_flags,
            "application": asdict(self.application),
            "constraints": [asdict(c) for c in self.constraints],
            "documents": [asdict(d) for d in self.documents],
            "policies": [asdict(p) for p in self.policies],
            "similar_cases": [asdict(s) for s in self.similar_cases],
            "history": [asdict(h) for h in self.history],
            "previous_runs": self.previous_runs,
            "feedback": self.feedback,
        }

    def to_json(self, indent: int = 2) -> str:
        """Build and return as JSON string.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """
        return json.dumps(self.build(), indent=indent, default=str)
