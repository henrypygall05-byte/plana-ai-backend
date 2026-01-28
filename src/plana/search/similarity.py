"""
Historic case similarity search.

Finds similar planning applications based on location,
proposal type, and semantic similarity.
"""

import math
from typing import NamedTuple, TYPE_CHECKING

import structlog

from plana.core.models import Application, ApplicationStatus, HistoricCase

# Use stub by default, full vector store if available
from plana.search.stub_vector_store import StubVectorStore

if TYPE_CHECKING:
    from plana.search.vector_store import VectorStore

logger = structlog.get_logger(__name__)


class SimilarityFactors(NamedTuple):
    """Breakdown of similarity factors."""

    location: float  # Geographic proximity
    proposal_type: float  # Semantic similarity of proposals
    application_type: float  # Same application type
    outcome: float  # Decision outcome relevance
    overall: float  # Combined score


class SimilaritySearcher:
    """
    Finds similar historic planning cases.

    Uses a combination of:
    - Geographic proximity (using coordinates or postcode)
    - Proposal semantic similarity
    - Application type matching
    - Outcome relevance
    """

    def __init__(
        self,
        vector_store: "StubVectorStore | VectorStore | None" = None,
    ):
        """Initialize similarity searcher.

        Args:
            vector_store: Vector store for semantic search (defaults to stub)
        """
        self.vector_store = vector_store or StubVectorStore()
        self._historic_cases: dict[str, Application] = {}

    async def add_historic_case(self, application: Application) -> None:
        """Add an application to the historic cases index.

        Args:
            application: Application to add
        """
        # Only add decided applications
        if not application.is_decided:
            return

        self._historic_cases[application.reference] = application

        # Add to vector store for semantic search
        summary = self._create_application_summary(application)
        await self.vector_store.add(
            collection="historic_cases",
            id=application.reference,
            content=summary,
            metadata={
                "council_id": application.council_id,
                "application_type": application.application_type.value,
                "status": application.status.value,
                "postcode": application.address.postcode or "",
                "ward": application.address.ward or "",
            },
        )

        logger.debug("Added historic case", reference=application.reference)

    def _create_application_summary(self, application: Application) -> str:
        """Create a text summary for embedding."""
        parts = [
            f"Proposal: {application.proposal}",
            f"Address: {application.address.full_address}",
            f"Type: {application.application_type.value}",
            f"Decision: {application.status.value}",
        ]

        if application.constraints:
            constraints = ", ".join(c.constraint_type for c in application.constraints)
            parts.append(f"Constraints: {constraints}")

        return "\n".join(parts)

    async def find_similar_cases(
        self,
        application: Application,
        max_results: int = 10,
        min_score: float = 0.3,
    ) -> list[HistoricCase]:
        """Find similar historic cases for an application.

        Args:
            application: Application to find similar cases for
            max_results: Maximum number of results
            min_score: Minimum similarity score

        Returns:
            List of similar historic cases with scores
        """
        logger.info("Finding similar cases", reference=application.reference)

        # First, do semantic search on proposals
        query = self._create_application_summary(application)

        semantic_results = await self.vector_store.search(
            query=query,
            collection="historic_cases",
            top_k=max_results * 2,  # Get more for filtering
            filter_metadata={"council_id": application.council_id},
        )

        similar_cases = []

        for result in semantic_results:
            historic_app = self._historic_cases.get(result.id)
            if not historic_app:
                continue

            # Skip the same application
            if historic_app.reference == application.reference:
                continue

            # Calculate detailed similarity
            factors = self._calculate_similarity_factors(application, historic_app, result.score)

            if factors.overall >= min_score:
                similar_cases.append(
                    HistoricCase(
                        application=historic_app,
                        similarity_score=factors.overall,
                        similarity_factors={
                            "location": factors.location,
                            "proposal_type": factors.proposal_type,
                            "application_type": factors.application_type,
                            "outcome": factors.outcome,
                        },
                        relevance_notes=self._generate_relevance_notes(factors, historic_app),
                    )
                )

        # Sort by score and limit
        similar_cases.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar_cases[:max_results]

    def _calculate_similarity_factors(
        self,
        query_app: Application,
        historic_app: Application,
        semantic_score: float,
    ) -> SimilarityFactors:
        """Calculate detailed similarity factors between applications."""

        # Location similarity (based on postcode/coordinates)
        location_score = self._calculate_location_similarity(query_app, historic_app)

        # Proposal type similarity (from semantic search)
        proposal_score = semantic_score

        # Application type match
        type_score = 1.0 if query_app.application_type == historic_app.application_type else 0.3

        # Outcome relevance (higher for approved cases)
        if historic_app.is_approved:
            outcome_score = 0.8
        elif historic_app.status == ApplicationStatus.REFUSED:
            outcome_score = 0.7  # Refusals also useful for understanding
        else:
            outcome_score = 0.3

        # Calculate overall score with weights
        weights = {
            "location": 0.2,
            "proposal": 0.4,
            "type": 0.2,
            "outcome": 0.2,
        }

        overall = (
            weights["location"] * location_score
            + weights["proposal"] * proposal_score
            + weights["type"] * type_score
            + weights["outcome"] * outcome_score
        )

        return SimilarityFactors(
            location=location_score,
            proposal_type=proposal_score,
            application_type=type_score,
            outcome=outcome_score,
            overall=overall,
        )

    def _calculate_location_similarity(
        self,
        app1: Application,
        app2: Application,
    ) -> float:
        """Calculate geographic similarity between applications."""

        # If coordinates available, use haversine distance
        if (
            app1.address.location
            and app2.address.location
            and app1.address.location.latitude
            and app2.address.location.latitude
        ):
            distance = self._haversine_distance(
                app1.address.location.latitude,
                app1.address.location.longitude,
                app2.address.location.latitude,
                app2.address.location.longitude,
            )
            # Convert distance to similarity (1.0 at 0km, 0.0 at 10km+)
            return max(0, 1 - (distance / 10))

        # Fall back to postcode matching
        if app1.address.postcode and app2.address.postcode:
            pc1 = app1.address.postcode.upper().replace(" ", "")
            pc2 = app2.address.postcode.upper().replace(" ", "")

            # Same postcode = high similarity
            if pc1 == pc2:
                return 1.0

            # Same outward code (e.g., NE1)
            if pc1[:3] == pc2[:3]:
                return 0.7

            # Same postcode area (e.g., NE)
            if pc1[:2] == pc2[:2]:
                return 0.4

        # Same ward
        if app1.address.ward and app2.address.ward:
            if app1.address.ward.lower() == app2.address.ward.lower():
                return 0.5

        return 0.1

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points in kilometers."""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _generate_relevance_notes(
        self,
        factors: SimilarityFactors,
        historic_app: Application,
    ) -> str:
        """Generate human-readable notes on why case is relevant."""
        notes = []

        if factors.location > 0.7:
            notes.append("Located nearby")
        elif factors.location > 0.4:
            notes.append("Same area")

        if factors.proposal_type > 0.7:
            notes.append("Similar proposal type")

        if factors.application_type > 0.8:
            notes.append(f"Same application type ({historic_app.application_type.value})")

        if historic_app.is_approved:
            notes.append("Approved - provides precedent")
        elif historic_app.status == ApplicationStatus.REFUSED:
            notes.append("Refused - shows refusal reasons")

        return ". ".join(notes) if notes else "Generally similar case"

    async def get_precedent_cases(
        self,
        application: Application,
        approved_only: bool = True,
        max_results: int = 5,
    ) -> list[HistoricCase]:
        """Get precedent cases (typically approved) for an application.

        Args:
            application: Application to find precedents for
            approved_only: Only return approved cases
            max_results: Maximum results

        Returns:
            List of precedent cases
        """
        all_similar = await self.find_similar_cases(application, max_results=max_results * 2)

        if approved_only:
            all_similar = [c for c in all_similar if c.application.is_approved]

        return all_similar[:max_results]
