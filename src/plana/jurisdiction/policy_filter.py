"""
LPA-Strict Policy Filtering.

Provides strict Local Planning Authority filtering for policy retrieval.
All local policy retrieval is filtered by planning_authority == identified_LPA.
NPPF may be used nationally, but all local policy must be authority-specific.
Cross-authority semantic retrieval is not permitted.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple

import structlog

from plana.core.models import Application, Policy, PolicyType
from plana.jurisdiction.service import JurisdictionService, LPAIdentificationResult
from plana.policies.manager import PolicyManager

if TYPE_CHECKING:
    from plana.search.stub_vector_store import StubVectorStore

logger = structlog.get_logger(__name__)


class StrictPolicyMatch(NamedTuple):
    """A matched policy with LPA jurisdiction context."""

    policy: Policy
    score: float
    match_reason: str
    is_national: bool  # True for NPPF, False for local
    lpa_verified: bool  # True if policy council_id matches identified LPA


@dataclass
class StrictPolicyRetrievalResult:
    """Result of strict LPA-filtered policy retrieval."""

    # LPA context
    lpa: LPAIdentificationResult

    # Policies by type
    local_plan_policies: list[StrictPolicyMatch] = field(default_factory=list)
    spd_policies: list[StrictPolicyMatch] = field(default_factory=list)
    nppf_policies: list[StrictPolicyMatch] = field(default_factory=list)

    # Metadata
    total_policies: int = 0
    retrieval_notes: list[str] = field(default_factory=list)

    def all_policies(self) -> list[StrictPolicyMatch]:
        """Get all policies as a flat list, sorted by score."""
        all_matches = (
            self.local_plan_policies + self.spd_policies + self.nppf_policies
        )
        return sorted(all_matches, key=lambda m: m.score, reverse=True)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "identified_lpa": self.lpa.to_dict(),
            "local_plan_policies": [
                {
                    "reference": m.policy.reference,
                    "title": m.policy.title,
                    "policy_type": m.policy.policy_type.value,
                    "score": m.score,
                    "match_reason": m.match_reason,
                    "council_id": m.policy.council_id,
                }
                for m in self.local_plan_policies
            ],
            "spd_policies": [
                {
                    "reference": m.policy.reference,
                    "title": m.policy.title,
                    "policy_type": m.policy.policy_type.value,
                    "score": m.score,
                    "match_reason": m.match_reason,
                    "council_id": m.policy.council_id,
                }
                for m in self.spd_policies
            ],
            "nppf_policies": [
                {
                    "reference": m.policy.reference,
                    "title": m.policy.title,
                    "policy_type": m.policy.policy_type.value,
                    "score": m.score,
                    "match_reason": m.match_reason,
                    "chapter": m.policy.chapter,
                }
                for m in self.nppf_policies
            ],
            "total_policies": self.total_policies,
            "retrieval_notes": self.retrieval_notes,
        }


class StrictPolicyRetriever:
    """
    LPA-strict policy retriever.

    Enforces hard data partitioning by Local Planning Authority:
    - All local policy retrieval filtered by planning_authority == identified_LPA
    - No cross-authority semantic retrieval permitted
    - NPPF may be used nationally
    - All local policy must be authority-specific
    """

    def __init__(
        self,
        policy_manager: PolicyManager | None = None,
        vector_store: "StubVectorStore | None" = None,
        jurisdiction_service: JurisdictionService | None = None,
    ):
        """Initialize strict policy retriever.

        Args:
            policy_manager: Policy storage manager
            vector_store: Vector store for semantic search (optional)
            jurisdiction_service: LPA jurisdiction enforcement service
        """
        self.policy_manager = policy_manager or PolicyManager()
        self.vector_store = vector_store
        self.jurisdiction_service = jurisdiction_service or JurisdictionService()

    async def retrieve_policies_strict(
        self,
        application: Application,
        lpa: LPAIdentificationResult | None = None,
        max_policies: int = 20,
        include_nppf: bool = True,
    ) -> StrictPolicyRetrievalResult:
        """
        Retrieve policies with strict LPA boundary enforcement.

        All local policies are filtered by council_id == lpa.council_id.
        No cross-authority contamination is permitted.

        Args:
            application: The application to find policies for
            lpa: Pre-identified LPA (if None, will identify from application)
            max_policies: Maximum number of policies to return
            include_nppf: Whether to include NPPF policies

        Returns:
            StrictPolicyRetrievalResult with LPA-filtered policies
        """
        # Identify LPA if not provided
        if lpa is None:
            lpa = self.jurisdiction_service.identify_lpa(
                address=application.address.full_address,
                postcode=application.address.postcode,
            )

        # Verify application council_id matches identified LPA
        if application.council_id.lower() != lpa.council_id.lower():
            logger.warning(
                "Application council_id mismatch with identified LPA",
                application_council_id=application.council_id,
                identified_lpa=lpa.council_id,
            )

        result = StrictPolicyRetrievalResult(lpa=lpa)

        # 1. Get LOCAL PLAN policies - STRICT LPA FILTER
        local_matches = await self._get_local_plan_policies_strict(
            application, lpa.council_id
        )
        result.local_plan_policies = local_matches
        result.retrieval_notes.append(
            f"Local Plan policies filtered to {lpa.council_name} only"
        )

        # 2. Get SPD policies - STRICT LPA FILTER
        spd_matches = await self._get_spd_policies_strict(application, lpa.council_id)
        result.spd_policies = spd_matches
        result.retrieval_notes.append(
            f"SPD policies filtered to {lpa.council_name} only"
        )

        # 3. Get NPPF policies - NATIONAL (no LPA filter)
        if include_nppf:
            nppf_matches = await self._get_nppf_policies(application)
            result.nppf_policies = nppf_matches
            result.retrieval_notes.append("NPPF policies included (national scope)")

        # 4. Semantic search with STRICT LPA FILTER
        if self.vector_store:
            semantic_matches = await self._semantic_search_strict(
                application, lpa.council_id
            )
            # Merge semantic matches with existing matches
            for match in semantic_matches:
                if match.is_national:
                    if not any(
                        m.policy.id == match.policy.id for m in result.nppf_policies
                    ):
                        result.nppf_policies.append(match)
                else:
                    if not any(
                        m.policy.id == match.policy.id
                        for m in result.local_plan_policies
                    ):
                        result.local_plan_policies.append(match)

        # Calculate total
        result.total_policies = (
            len(result.local_plan_policies)
            + len(result.spd_policies)
            + len(result.nppf_policies)
        )

        logger.info(
            "Strict policy retrieval complete",
            lpa=lpa.council_id,
            local_plan_count=len(result.local_plan_policies),
            spd_count=len(result.spd_policies),
            nppf_count=len(result.nppf_policies),
            total=result.total_policies,
        )

        return result

    async def _get_local_plan_policies_strict(
        self, application: Application, council_id: str
    ) -> list[StrictPolicyMatch]:
        """
        Get Local Plan policies with STRICT LPA filter.

        Only returns policies where policy.council_id == council_id.
        No fallback to other councils permitted.
        """
        matches = []

        # Get all local plan policies for this specific council
        local_policies = self.policy_manager.list_policies(
            policy_type=PolicyType.LOCAL_PLAN,
            council_id=council_id,
            current_only=True,
        )

        # Constraint-triggered policies
        constraint_policy_map = {
            "conservation_area": ["DM21", "DM15", "DM16"],
            "listed_building": ["DM21", "DM17"],
            "flood_zone": [],  # Handled by NPPF
            "green_belt": [],  # Handled by NPPF
            "tree_preservation_order": ["DM26"],
            "article_4": ["DM15", "DM16"],
        }

        triggered_refs = set()
        for constraint in application.constraints:
            constraint_type = constraint.constraint_type.lower().replace(" ", "_")
            refs = constraint_policy_map.get(constraint_type, [])
            for ref in refs:
                triggered_refs.add(ref.upper())

        # Match policies
        for policy in local_policies:
            # Check if constraint-triggered
            if policy.reference.upper() in triggered_refs:
                matches.append(
                    StrictPolicyMatch(
                        policy=policy,
                        score=0.9,
                        match_reason=f"Triggered by site constraint",
                        is_national=False,
                        lpa_verified=True,
                    )
                )
                continue

            # Core policies always included
            if policy.reference.upper() in ["CS1", "DM20"]:
                matches.append(
                    StrictPolicyMatch(
                        policy=policy,
                        score=0.7,
                        match_reason="Core Local Plan policy",
                        is_national=False,
                        lpa_verified=True,
                    )
                )
                continue

            # Application type specific policies
            type_refs = self._get_type_specific_policy_refs(application)
            if policy.reference.upper() in type_refs:
                matches.append(
                    StrictPolicyMatch(
                        policy=policy,
                        score=0.75,
                        match_reason=f"Relevant to {application.application_type.value}",
                        is_national=False,
                        lpa_verified=True,
                    )
                )

        return matches

    async def _get_spd_policies_strict(
        self, application: Application, council_id: str
    ) -> list[StrictPolicyMatch]:
        """
        Get SPD policies with STRICT LPA filter.

        Only returns SPDs for the identified council.
        """
        matches = []

        spd_policies = self.policy_manager.list_policies(
            policy_type=PolicyType.SUPPLEMENTARY_PLANNING_DOCUMENT,
            council_id=council_id,
            current_only=True,
        )

        for policy in spd_policies:
            matches.append(
                StrictPolicyMatch(
                    policy=policy,
                    score=0.6,
                    match_reason="Supplementary Planning Document",
                    is_national=False,
                    lpa_verified=True,
                )
            )

        return matches

    async def _get_nppf_policies(
        self, application: Application
    ) -> list[StrictPolicyMatch]:
        """
        Get NPPF policies (national - no LPA filter).

        NPPF applies nationally and is not filtered by LPA.
        """
        matches = []

        # Always include sustainable development
        sustainable_dev = self.policy_manager.get_policy_by_reference("NPPF-2")
        if sustainable_dev:
            matches.append(
                StrictPolicyMatch(
                    policy=sustainable_dev,
                    score=0.5,
                    match_reason="Core NPPF sustainable development policy",
                    is_national=True,
                    lpa_verified=True,
                )
            )

        # Design chapter
        design = self.policy_manager.get_policy_by_reference("NPPF-12")
        if design:
            matches.append(
                StrictPolicyMatch(
                    policy=design,
                    score=0.6,
                    match_reason="NPPF design policy",
                    is_national=True,
                    lpa_verified=True,
                )
            )

        # Constraint-specific NPPF chapters
        constraint_nppf_map = {
            "conservation_area": "NPPF-16",
            "listed_building": "NPPF-16",
            "flood_zone": "NPPF-14",
            "green_belt": "NPPF-13",
            "sssi": "NPPF-15",
            "ancient_woodland": "NPPF-15",
        }

        for constraint in application.constraints:
            constraint_type = constraint.constraint_type.lower().replace(" ", "_")
            nppf_ref = constraint_nppf_map.get(constraint_type)
            if nppf_ref:
                policy = self.policy_manager.get_policy_by_reference(nppf_ref)
                if policy and not any(m.policy.id == policy.id for m in matches):
                    matches.append(
                        StrictPolicyMatch(
                            policy=policy,
                            score=0.85,
                            match_reason=f"NPPF guidance for {constraint.constraint_type}",
                            is_national=True,
                            lpa_verified=True,
                        )
                    )

        return matches

    async def _semantic_search_strict(
        self, application: Application, council_id: str
    ) -> list[StrictPolicyMatch]:
        """
        Semantic search with STRICT LPA filter.

        Local policies filtered by council_id in vector store metadata.
        NPPF policies not filtered.
        """
        if not self.vector_store:
            return []

        query = f"{application.proposal}. {application.application_type.value}."
        if application.constraints:
            constraint_text = ", ".join(c.constraint_type for c in application.constraints)
            query += f" Site constraints: {constraint_text}."

        try:
            # Search with council_id filter for local policies
            local_results = await self.vector_store.search(
                query=query,
                collection="policies",
                top_k=10,
                filter_metadata={"council_id": council_id},  # STRICT FILTER
            )

            # Search for NPPF (no filter)
            nppf_results = await self.vector_store.search(
                query=query,
                collection="policies",
                top_k=5,
                filter_metadata={"policy_type": "nppf"},
            )

            matches = []

            for result in local_results:
                policy = self.policy_manager.get_policy(result.id)
                if policy and policy.council_id == council_id:  # Double-check
                    matches.append(
                        StrictPolicyMatch(
                            policy=policy,
                            score=result.score,
                            match_reason="Semantic similarity (LPA-filtered)",
                            is_national=False,
                            lpa_verified=True,
                        )
                    )

            for result in nppf_results:
                policy = self.policy_manager.get_policy(result.id)
                if policy and policy.policy_type == PolicyType.NPPF:
                    matches.append(
                        StrictPolicyMatch(
                            policy=policy,
                            score=result.score,
                            match_reason="Semantic similarity (NPPF)",
                            is_national=True,
                            lpa_verified=True,
                        )
                    )

            return matches

        except Exception as e:
            logger.error("Strict semantic search failed", error=str(e))
            return []

    def _get_type_specific_policy_refs(self, application: Application) -> set[str]:
        """Get policy references specific to application type."""
        type_map = {
            "householder": {"DM20", "DM6"},
            "listed_building": {"DM21", "DM17"},
            "conservation_area": {"DM21", "DM15", "DM16"},
            "full": {"CS1", "DM20"},
            "change_of_use": {"DM20"},
        }
        app_type = application.application_type.value.lower()
        return type_map.get(app_type, {"DM20"})
