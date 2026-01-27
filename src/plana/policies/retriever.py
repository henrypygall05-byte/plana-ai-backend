"""
Policy retrieval and semantic search.

Retrieves relevant policies for planning applications using
keyword and semantic search.
"""

from typing import NamedTuple

import structlog

from plana.core.models import Application, Policy, PolicyType
from plana.policies.manager import PolicyManager
from plana.search.vector_store import VectorStore

logger = structlog.get_logger(__name__)


class PolicyMatch(NamedTuple):
    """A matched policy with relevance score."""

    policy: Policy
    score: float
    match_reason: str


class PolicyRetriever:
    """
    Retrieves relevant policies for planning applications.

    Uses a combination of:
    - Rule-based retrieval (constraint-triggered policies)
    - Keyword matching
    - Semantic similarity search
    """

    def __init__(
        self,
        policy_manager: PolicyManager | None = None,
        vector_store: VectorStore | None = None,
    ):
        """Initialize policy retriever.

        Args:
            policy_manager: Policy storage manager
            vector_store: Vector store for semantic search
        """
        self.policy_manager = policy_manager or PolicyManager()
        self.vector_store = vector_store

    async def retrieve_relevant_policies(
        self,
        application: Application,
        max_policies: int = 20,
        include_nppf: bool = True,
    ) -> list[PolicyMatch]:
        """Retrieve policies relevant to an application.

        Args:
            application: The application to find policies for
            max_policies: Maximum number of policies to return
            include_nppf: Whether to include NPPF policies

        Returns:
            List of matched policies with scores
        """
        matches: list[PolicyMatch] = []

        # 1. Get constraint-triggered policies
        constraint_matches = await self._get_constraint_policies(application)
        matches.extend(constraint_matches)

        # 2. Get policies by application type
        type_matches = await self._get_application_type_policies(application)
        matches.extend(type_matches)

        # 3. Get local plan policies for the council
        local_matches = await self._get_local_plan_policies(application.council_id)
        matches.extend(local_matches)

        # 4. Include NPPF policies
        if include_nppf:
            nppf_matches = await self._get_nppf_policies(application)
            matches.extend(nppf_matches)

        # 5. Semantic search if vector store available
        if self.vector_store:
            semantic_matches = await self._semantic_search(application)
            matches.extend(semantic_matches)

        # Deduplicate and sort by score
        seen = set()
        unique_matches = []
        for match in sorted(matches, key=lambda m: m.score, reverse=True):
            if match.policy.id not in seen:
                seen.add(match.policy.id)
                unique_matches.append(match)

        return unique_matches[:max_policies]

    async def _get_constraint_policies(
        self, application: Application
    ) -> list[PolicyMatch]:
        """Get policies triggered by site constraints."""
        matches = []

        constraint_policy_map = {
            "conservation_area": ["DM21", "NPPF-16"],
            "listed_building": ["DM21", "NPPF-16"],
            "flood_zone": ["NPPF-14"],
            "green_belt": ["NPPF-13"],
            "tree_preservation_order": ["DM26"],
            "sssi": ["NPPF-15"],
            "ancient_woodland": ["NPPF-15"],
        }

        for constraint in application.constraints:
            constraint_type = constraint.constraint_type.lower().replace(" ", "_")
            policy_refs = constraint_policy_map.get(constraint_type, [])

            for ref in policy_refs:
                policy = self.policy_manager.get_policy_by_reference(
                    ref, council_id=application.council_id
                )
                if not policy:
                    policy = self.policy_manager.get_policy_by_reference(ref)
                if policy:
                    matches.append(
                        PolicyMatch(
                            policy=policy,
                            score=0.9,  # High score for constraint-triggered
                            match_reason=f"Site has {constraint.constraint_type} constraint",
                        )
                    )

        return matches

    async def _get_application_type_policies(
        self, application: Application
    ) -> list[PolicyMatch]:
        """Get policies based on application type."""
        matches = []

        type_policy_map = {
            "householder": ["DM20"],
            "listed_building": ["DM21", "NPPF-16"],
            "conservation_area": ["DM21", "NPPF-16"],
            "full": ["CS1", "DM20"],
            "change_of_use": ["DM20"],
        }

        app_type = application.application_type.value.lower()
        policy_refs = type_policy_map.get(app_type, ["DM20"])

        for ref in policy_refs:
            policy = self.policy_manager.get_policy_by_reference(
                ref, council_id=application.council_id
            )
            if not policy:
                policy = self.policy_manager.get_policy_by_reference(ref)
            if policy:
                matches.append(
                    PolicyMatch(
                        policy=policy,
                        score=0.7,
                        match_reason=f"Relevant to {application.application_type.value} applications",
                    )
                )

        return matches

    async def _get_local_plan_policies(self, council_id: str) -> list[PolicyMatch]:
        """Get core local plan policies for a council."""
        matches = []

        # Always include core strategic policies
        core_refs = ["CS1", "DM20"]

        for ref in core_refs:
            policy = self.policy_manager.get_policy_by_reference(ref, council_id=council_id)
            if policy:
                matches.append(
                    PolicyMatch(
                        policy=policy,
                        score=0.6,
                        match_reason="Core local plan policy",
                    )
                )

        return matches

    async def _get_nppf_policies(self, application: Application) -> list[PolicyMatch]:
        """Get relevant NPPF policies."""
        matches = []

        # Always include sustainable development chapter
        sustainable_dev = self.policy_manager.get_policy_by_reference("NPPF-2")
        if sustainable_dev:
            matches.append(
                PolicyMatch(
                    policy=sustainable_dev,
                    score=0.5,
                    match_reason="Core NPPF sustainable development policy",
                )
            )

        # Design chapter for most applications
        design = self.policy_manager.get_policy_by_reference("NPPF-12")
        if design:
            matches.append(
                PolicyMatch(
                    policy=design,
                    score=0.6,
                    match_reason="NPPF design policy",
                )
            )

        return matches

    async def _semantic_search(
        self, application: Application
    ) -> list[PolicyMatch]:
        """Search for policies using semantic similarity."""
        if not self.vector_store:
            return []

        # Build query from application details
        query = f"{application.proposal}. {application.application_type.value}."

        if application.constraints:
            constraint_text = ", ".join(c.constraint_type for c in application.constraints)
            query += f" Site constraints: {constraint_text}."

        try:
            results = await self.vector_store.search(
                query=query,
                collection="policies",
                top_k=10,
            )

            matches = []
            for result in results:
                policy = self.policy_manager.get_policy(result.id)
                if policy:
                    matches.append(
                        PolicyMatch(
                            policy=policy,
                            score=result.score,
                            match_reason="Semantic similarity to proposal",
                        )
                    )

            return matches

        except Exception as e:
            logger.error("Semantic policy search failed", error=str(e))
            return []

    async def get_policies_for_document(
        self,
        document_text: str,
        council_id: str,
        max_policies: int = 10,
    ) -> list[PolicyMatch]:
        """Find policies relevant to a document's content.

        Args:
            document_text: Text content of the document
            council_id: Council for local policies
            max_policies: Maximum policies to return

        Returns:
            List of matched policies
        """
        if not self.vector_store:
            # Fall back to keyword matching
            return await self._keyword_match_policies(document_text, council_id)

        try:
            # Use first 1000 chars for query
            query = document_text[:1000]

            results = await self.vector_store.search(
                query=query,
                collection="policies",
                top_k=max_policies,
            )

            matches = []
            for result in results:
                policy = self.policy_manager.get_policy(result.id)
                if policy:
                    matches.append(
                        PolicyMatch(
                            policy=policy,
                            score=result.score,
                            match_reason="Semantic match to document content",
                        )
                    )

            return matches

        except Exception as e:
            logger.error("Policy search failed", error=str(e))
            return []

    async def _keyword_match_policies(
        self, text: str, council_id: str
    ) -> list[PolicyMatch]:
        """Simple keyword-based policy matching."""
        matches = []
        text_lower = text.lower()

        keywords = {
            "heritage": ["DM21", "NPPF-16"],
            "listed building": ["DM21", "NPPF-16"],
            "conservation area": ["DM21", "NPPF-16"],
            "design": ["DM20", "NPPF-12"],
            "flood": ["NPPF-14"],
            "ecology": ["NPPF-15"],
            "biodiversity": ["NPPF-15"],
            "sustainable": ["NPPF-2", "CS1"],
            "transport": ["DM24"],
            "parking": ["DM24"],
        }

        for keyword, policy_refs in keywords.items():
            if keyword in text_lower:
                for ref in policy_refs:
                    policy = self.policy_manager.get_policy_by_reference(ref, council_id)
                    if not policy:
                        policy = self.policy_manager.get_policy_by_reference(ref)
                    if policy:
                        matches.append(
                            PolicyMatch(
                                policy=policy,
                                score=0.5,
                                match_reason=f"Keyword match: '{keyword}'",
                            )
                        )

        # Deduplicate
        seen = set()
        unique = []
        for match in matches:
            if match.policy.id not in seen:
                seen.add(match.policy.id)
                unique.append(match)

        return unique
