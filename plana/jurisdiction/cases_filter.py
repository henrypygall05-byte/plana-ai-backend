"""
LPA-Strict Similar Cases Search.

Provides strict Local Planning Authority filtering for comparable
application searches. All searches are filtered by:
    planning_authority == identified_LPA

Cross-authority case retrieval is not permitted.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from plana.core.models import Application
from plana.jurisdiction.service import JurisdictionService, LPAIdentificationResult

if TYPE_CHECKING:
    from plana.search.stub_vector_store import StubVectorStore

logger = structlog.get_logger(__name__)


@dataclass
class StrictCaseMatch:
    """A matched historic case with LPA jurisdiction context."""

    reference: str
    address: str
    ward: str
    postcode: str
    proposal: str
    application_type: str
    constraints: list[str]
    decision: str
    decision_date: str
    case_officer_reasoning: str
    key_policies_cited: list[str]
    similarity_score: float
    relevance_reason: str
    lpa_verified: bool  # True if case council matches identified LPA

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "reference": self.reference,
            "address": self.address,
            "ward": self.ward,
            "postcode": self.postcode,
            "proposal": self.proposal,
            "application_type": self.application_type,
            "constraints": self.constraints,
            "decision": self.decision,
            "decision_date": self.decision_date,
            "case_officer_reasoning": self.case_officer_reasoning,
            "key_policies_cited": self.key_policies_cited,
            "similarity_score": self.similarity_score,
            "relevance_reason": self.relevance_reason,
            "lpa_verified": self.lpa_verified,
        }


@dataclass
class StrictCaseSearchResult:
    """Result of strict LPA-filtered case search."""

    # LPA context
    lpa: LPAIdentificationResult

    # Matching cases
    cases: list[StrictCaseMatch] = field(default_factory=list)

    # Search metadata
    total_searched: int = 0
    total_matched: int = 0
    search_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "identified_lpa": self.lpa.to_dict(),
            "comparable_applications": [c.to_dict() for c in self.cases],
            "total_searched": self.total_searched,
            "total_matched": self.total_matched,
            "search_notes": self.search_notes,
            "jurisdiction_note": (
                f"All comparable applications are from {self.lpa.council_name} only. "
                "Cross-authority case retrieval is not permitted."
            ),
        }


class StrictCaseSearch:
    """
    LPA-strict similar cases search.

    Enforces hard data partitioning by Local Planning Authority:
    - All case searches filtered by planning_authority == identified_LPA
    - No cross-authority case retrieval permitted
    - Only returns cases determined by the same authority
    """

    def __init__(
        self,
        vector_store: "StubVectorStore | None" = None,
        jurisdiction_service: JurisdictionService | None = None,
    ):
        """Initialize strict case search.

        Args:
            vector_store: Vector store for semantic search
            jurisdiction_service: LPA jurisdiction enforcement service
        """
        self.vector_store = vector_store
        self.jurisdiction_service = jurisdiction_service or JurisdictionService()

        # Import historic cases database
        self._cases_db = self._load_cases_database()

    def _load_cases_database(self) -> dict[str, list[dict[str, Any]]]:
        """Load historic cases database by council."""
        try:
            from plana.api.similar_cases import ALL_HISTORIC_CASES

            return ALL_HISTORIC_CASES
        except ImportError:
            logger.warning("Could not load historic cases database")
            return {}

    async def search_similar_cases_strict(
        self,
        application: Application,
        lpa: LPAIdentificationResult | None = None,
        max_results: int = 10,
        min_score: float = 0.3,
    ) -> StrictCaseSearchResult:
        """
        Search for similar cases with strict LPA boundary enforcement.

        All cases filtered by planning_authority == identified_LPA.
        No cross-authority case retrieval is permitted.

        Args:
            application: The application to find similar cases for
            lpa: Pre-identified LPA (if None, will identify from application)
            max_results: Maximum number of cases to return
            min_score: Minimum similarity score threshold

        Returns:
            StrictCaseSearchResult with LPA-filtered cases
        """
        # Identify LPA if not provided
        if lpa is None:
            lpa = self.jurisdiction_service.identify_lpa(
                address=application.address.full_address,
                postcode=application.address.postcode,
            )

        result = StrictCaseSearchResult(lpa=lpa)
        result.search_notes.append(
            f"Search restricted to {lpa.council_name} applications only"
        )

        # Get cases for this council only
        council_cases = self._cases_db.get(lpa.council_id, [])
        result.total_searched = len(council_cases)

        if not council_cases:
            result.search_notes.append(
                f"No historic cases available for {lpa.council_name}"
            )
            return result

        # Score and filter cases
        scored_cases = []
        for case_data in council_cases:
            score, reason = self._calculate_similarity(application, case_data)
            if score >= min_score:
                scored_cases.append((score, reason, case_data))

        # Sort by score and limit results
        scored_cases.sort(key=lambda x: x[0], reverse=True)
        top_cases = scored_cases[:max_results]

        # Build result matches
        for score, reason, case_data in top_cases:
            match = StrictCaseMatch(
                reference=case_data["reference"],
                address=case_data["address"],
                ward=case_data["ward"],
                postcode=case_data["postcode"],
                proposal=case_data["proposal"],
                application_type=case_data["application_type"],
                constraints=case_data.get("constraints", []),
                decision=case_data["decision"],
                decision_date=case_data["decision_date"],
                case_officer_reasoning=case_data.get("case_officer_reasoning", ""),
                key_policies_cited=case_data.get("key_policies_cited", []),
                similarity_score=score,
                relevance_reason=reason,
                lpa_verified=True,  # Guaranteed by strict filter
            )
            result.cases.append(match)

        result.total_matched = len(result.cases)

        logger.info(
            "Strict case search complete",
            lpa=lpa.council_id,
            total_searched=result.total_searched,
            total_matched=result.total_matched,
        )

        return result

    async def search_with_vector_store_strict(
        self,
        application: Application,
        lpa: LPAIdentificationResult,
        max_results: int = 10,
    ) -> list[StrictCaseMatch]:
        """
        Search using vector store with strict LPA filter.

        Vector store metadata filter enforces council_id constraint.
        """
        if not self.vector_store:
            return []

        query = f"{application.proposal}. {application.application_type.value}."
        if application.constraints:
            constraint_text = ", ".join(c.constraint_type for c in application.constraints)
            query += f" Constraints: {constraint_text}."

        try:
            results = await self.vector_store.search(
                query=query,
                collection="historic_cases",
                top_k=max_results,
                filter_metadata={"council_id": lpa.council_id},  # STRICT FILTER
            )

            matches = []
            for result in results:
                # Verify council_id in metadata (double-check)
                if result.metadata.get("council_id") != lpa.council_id:
                    logger.warning(
                        "Case council_id mismatch - skipping",
                        expected=lpa.council_id,
                        actual=result.metadata.get("council_id"),
                    )
                    continue

                matches.append(
                    StrictCaseMatch(
                        reference=result.metadata.get("reference", ""),
                        address=result.metadata.get("address", ""),
                        ward=result.metadata.get("ward", ""),
                        postcode=result.metadata.get("postcode", ""),
                        proposal=result.metadata.get("proposal", ""),
                        application_type=result.metadata.get("application_type", ""),
                        constraints=result.metadata.get("constraints", []),
                        decision=result.metadata.get("decision", ""),
                        decision_date=result.metadata.get("decision_date", ""),
                        case_officer_reasoning=result.metadata.get(
                            "case_officer_reasoning", ""
                        ),
                        key_policies_cited=result.metadata.get("key_policies_cited", []),
                        similarity_score=result.score,
                        relevance_reason="Semantic similarity (LPA-filtered)",
                        lpa_verified=True,
                    )
                )

            return matches

        except Exception as e:
            logger.error("Vector store case search failed", error=str(e))
            return []

    def _calculate_similarity(
        self, application: Application, case_data: dict[str, Any]
    ) -> tuple[float, str]:
        """
        Calculate similarity score between application and historic case.

        Returns (score, reason) tuple.
        """
        score = 0.0
        reasons = []

        # Ward match (high weight)
        if (
            application.address.ward
            and application.address.ward.lower() == case_data.get("ward", "").lower()
        ):
            score += 0.25
            reasons.append("Same ward")

        # Postcode area match
        app_postcode = (application.address.postcode or "")[:4].upper()
        case_postcode = case_data.get("postcode", "")[:4].upper()
        if app_postcode and app_postcode == case_postcode:
            score += 0.15
            reasons.append("Same postcode area")

        # Application type match
        app_type = application.application_type.value.lower()
        case_type = case_data.get("application_type", "").lower()
        if app_type in case_type or case_type in app_type:
            score += 0.2
            reasons.append("Same application type")

        # Constraint overlap
        app_constraints = {c.constraint_type.lower() for c in application.constraints}
        case_constraints = {c.lower() for c in case_data.get("constraints", [])}
        constraint_overlap = app_constraints & case_constraints
        if constraint_overlap:
            overlap_bonus = min(0.3, len(constraint_overlap) * 0.1)
            score += overlap_bonus
            reasons.append(f"Shared constraints: {', '.join(constraint_overlap)}")

        # Proposal keyword similarity
        proposal_score = self._calculate_proposal_similarity(
            application.proposal, case_data.get("proposal", "")
        )
        score += proposal_score * 0.2
        if proposal_score > 0.5:
            reasons.append("Similar proposal type")

        # Decision relevance (boost approved/refused based on constraints)
        if app_constraints and case_constraints:
            score += 0.1  # Boost cases with matching constraints that have decisions
            reasons.append("Relevant precedent")

        reason = "; ".join(reasons) if reasons else "General similarity"
        return min(score, 1.0), reason

    def _calculate_proposal_similarity(self, proposal1: str, proposal2: str) -> float:
        """Calculate simple keyword-based proposal similarity."""
        keywords1 = set(proposal1.lower().split())
        keywords2 = set(proposal2.lower().split())

        # Remove common words
        stopwords = {
            "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "at",
            "with", "by", "from", "erection", "construction", "of", "and",
        }
        keywords1 -= stopwords
        keywords2 -= stopwords

        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        return len(intersection) / len(union) if union else 0.0
