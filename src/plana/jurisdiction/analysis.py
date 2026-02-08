"""
LPA-Strict Planning Policy Analysis.

Provides comprehensive planning policy analysis with strict Local Planning
Authority boundary enforcement. This is the main interface for LPA-partitioned
analysis.

Output includes:
- Identified Local Planning Authority
- Adopted Local Plan version and date
- Relevant policy references (LPA-filtered)
- Relevant NPPF paragraphs
- Comparable applications from the same authority only
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

from plana.core.models import Application
from plana.jurisdiction.cases_filter import StrictCaseMatch, StrictCaseSearch
from plana.jurisdiction.policy_filter import (
    StrictPolicyMatch,
    StrictPolicyRetriever,
)
from plana.jurisdiction.service import (
    JurisdictionService,
    LPAIdentificationResult,
    MultipleJurisdictionsError,
    UnknownJurisdictionError,
)
from plana.policies.manager import PolicyManager

if TYPE_CHECKING:
    from plana.search.stub_vector_store import StubVectorStore

logger = structlog.get_logger(__name__)


@dataclass
class LPAAnalysisResult:
    """
    Complete LPA-strict planning policy analysis result.

    Contains all required output fields:
    - Identified Local Planning Authority
    - Adopted Local Plan version and date
    - Relevant policy references
    - Relevant NPPF paragraphs
    - Comparable applications from the same authority only
    """

    # Core identification
    identified_lpa: LPAIdentificationResult

    # Policy analysis
    local_plan_policies: list[StrictPolicyMatch] = field(default_factory=list)
    spd_policies: list[StrictPolicyMatch] = field(default_factory=list)
    nppf_policies: list[StrictPolicyMatch] = field(default_factory=list)

    # Comparable applications
    comparable_applications: list[StrictCaseMatch] = field(default_factory=list)

    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analysis_notes: list[str] = field(default_factory=list)

    # Jurisdiction enforcement
    jurisdiction_enforced: bool = True
    cross_authority_retrieval_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            # Required output: Identified Local Planning Authority
            "identified_local_planning_authority": {
                "council_id": self.identified_lpa.council_id,
                "council_name": self.identified_lpa.council_name,
                "is_confirmed": self.identified_lpa.is_confirmed,
                "confidence_score": self.identified_lpa.confidence_score,
                "boundary_warning": self.identified_lpa.boundary_warning,
            },
            # Required output: Adopted Local Plan version and date
            "adopted_local_plan": {
                "plan_name": (
                    self.identified_lpa.adopted_local_plan.plan_name
                    if self.identified_lpa.adopted_local_plan
                    else None
                ),
                "adoption_date": (
                    self.identified_lpa.adopted_local_plan.adoption_date.isoformat()
                    if self.identified_lpa.adopted_local_plan
                    and self.identified_lpa.adopted_local_plan.adoption_date
                    else None
                ),
                "plan_period": (
                    self.identified_lpa.adopted_local_plan.plan_period
                    if self.identified_lpa.adopted_local_plan
                    else None
                ),
                "status": (
                    self.identified_lpa.adopted_local_plan.status
                    if self.identified_lpa.adopted_local_plan
                    else None
                ),
                "source_url": (
                    self.identified_lpa.adopted_local_plan.source_url
                    if self.identified_lpa.adopted_local_plan
                    else None
                ),
            },
            # Supplementary Planning Documents
            "supplementary_planning_documents": self.identified_lpa.supplementary_documents,
            # Required output: Relevant policy references (LPA-filtered)
            "relevant_local_plan_policies": [
                {
                    "reference": p.policy.reference,
                    "title": p.policy.title,
                    "chapter": p.policy.chapter,
                    "score": p.score,
                    "match_reason": p.match_reason,
                    "content_summary": (
                        p.policy.summary or p.policy.content[:200] + "..."
                        if len(p.policy.content) > 200
                        else p.policy.content
                    ),
                }
                for p in self.local_plan_policies
            ],
            "relevant_spd_policies": [
                {
                    "reference": p.policy.reference,
                    "title": p.policy.title,
                    "score": p.score,
                    "match_reason": p.match_reason,
                }
                for p in self.spd_policies
            ],
            # Required output: Relevant NPPF paragraphs
            "relevant_nppf_paragraphs": [
                {
                    "reference": p.policy.reference,
                    "title": p.policy.title,
                    "chapter": p.policy.chapter,
                    "score": p.score,
                    "match_reason": p.match_reason,
                    "content_summary": (
                        p.policy.summary or p.policy.content[:200] + "..."
                        if len(p.policy.content) > 200
                        else p.policy.content
                    ),
                }
                for p in self.nppf_policies
            ],
            # Required output: Comparable applications from same authority only
            "comparable_applications": [
                {
                    "reference": c.reference,
                    "address": c.address,
                    "ward": c.ward,
                    "proposal": c.proposal,
                    "application_type": c.application_type,
                    "constraints": c.constraints,
                    "decision": c.decision,
                    "decision_date": c.decision_date,
                    "case_officer_reasoning": c.case_officer_reasoning,
                    "key_policies_cited": c.key_policies_cited,
                    "similarity_score": c.similarity_score,
                    "relevance_reason": c.relevance_reason,
                }
                for c in self.comparable_applications
            ],
            # Jurisdiction enforcement confirmation
            "jurisdiction_enforcement": {
                "strict_lpa_filtering": True,
                "cross_authority_retrieval_blocked": True,
                "nppf_national_scope": True,
                "local_policy_authority_specific": True,
                "enforcement_note": (
                    f"All local policy and comparable application data is restricted to "
                    f"{self.identified_lpa.council_name}. Cross-authority contamination "
                    "is not permitted. NPPF applies nationally."
                ),
            },
            # Metadata
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "analysis_notes": self.analysis_notes,
        }


class LPAStrictAnalyzer:
    """
    Comprehensive LPA-strict planning policy analyzer.

    Enforces strict Local Planning Authority boundary enforcement:
    - All policy retrieval filtered by planning_authority == identified_LPA
    - All comparable application searches filtered by planning_authority == identified_LPA
    - No cross-authority semantic retrieval
    - NPPF may be used nationally
    - All local policy must be authority-specific
    - Multiple LPA detection halts and requests clarification
    """

    def __init__(
        self,
        policy_manager: PolicyManager | None = None,
        vector_store: "StubVectorStore | None" = None,
    ):
        """Initialize the LPA-strict analyzer.

        Args:
            policy_manager: Policy storage manager
            vector_store: Vector store for semantic search
        """
        self.jurisdiction_service = JurisdictionService()
        self.policy_retriever = StrictPolicyRetriever(
            policy_manager=policy_manager,
            vector_store=vector_store,
            jurisdiction_service=self.jurisdiction_service,
        )
        self.case_search = StrictCaseSearch(
            vector_store=vector_store,
            jurisdiction_service=self.jurisdiction_service,
        )

    async def analyze(
        self,
        application: Application,
        council_id: str | None = None,
        max_policies: int = 20,
        max_cases: int = 10,
        allow_boundary_ambiguity: bool = False,
    ) -> LPAAnalysisResult:
        """
        Perform comprehensive LPA-strict planning policy analysis.

        Args:
            application: The planning application to analyze
            council_id: Optional explicit council_id (overrides detection)
            max_policies: Maximum policies to retrieve
            max_cases: Maximum comparable cases to retrieve
            allow_boundary_ambiguity: If False (default), raises error on ambiguity

        Returns:
            LPAAnalysisResult with complete analysis

        Raises:
            UnknownJurisdictionError: If LPA cannot be identified
            MultipleJurisdictionsError: If multiple LPAs detected and ambiguity not allowed
        """
        analysis_notes = []

        # Step 1: Identify LPA
        if council_id:
            # Explicit council_id provided - validate and use
            if not self.jurisdiction_service.validate_council_id(council_id):
                raise UnknownJurisdictionError(
                    address=application.address.full_address,
                    postcode=application.address.postcode,
                )
            lpa = LPAIdentificationResult(
                council_id=council_id,
                council_name=self.jurisdiction_service._get_council_name(council_id),
                is_confirmed=True,
                adopted_local_plan=self.jurisdiction_service.get_local_plan_info(
                    council_id
                ),
                supplementary_documents=self.jurisdiction_service.get_spd_list(
                    council_id
                ),
                input_address=application.address.full_address,
                input_postcode=application.address.postcode,
                confidence_score=1.0,
                notes=["Council ID explicitly provided"],
            )
            analysis_notes.append(f"LPA explicitly set to {lpa.council_name}")
        else:
            # Detect LPA from address
            lpa = self.jurisdiction_service.identify_lpa(
                address=application.address.full_address,
                postcode=application.address.postcode,
                allow_boundary_ambiguity=allow_boundary_ambiguity,
            )
            analysis_notes.append(f"LPA detected: {lpa.council_name}")
            if lpa.boundary_warning:
                analysis_notes.append(f"Warning: {lpa.boundary_warning}")

        # Step 2: Retrieve policies with strict LPA filter
        logger.info(
            "Performing strict policy retrieval",
            council_id=lpa.council_id,
            application_ref=application.reference,
        )

        policy_result = await self.policy_retriever.retrieve_policies_strict(
            application=application,
            lpa=lpa,
            max_policies=max_policies,
        )
        analysis_notes.extend(policy_result.retrieval_notes)

        # Step 3: Search comparable cases with strict LPA filter
        logger.info(
            "Performing strict case search",
            council_id=lpa.council_id,
            application_ref=application.reference,
        )

        case_result = await self.case_search.search_similar_cases_strict(
            application=application,
            lpa=lpa,
            max_results=max_cases,
        )
        analysis_notes.extend(case_result.search_notes)

        # Step 4: Build result
        result = LPAAnalysisResult(
            identified_lpa=lpa,
            local_plan_policies=policy_result.local_plan_policies,
            spd_policies=policy_result.spd_policies,
            nppf_policies=policy_result.nppf_policies,
            comparable_applications=case_result.cases,
            analysis_notes=analysis_notes,
            jurisdiction_enforced=True,
            cross_authority_retrieval_blocked=True,
        )

        logger.info(
            "LPA-strict analysis complete",
            council_id=lpa.council_id,
            local_policies=len(result.local_plan_policies),
            nppf_policies=len(result.nppf_policies),
            comparable_cases=len(result.comparable_applications),
        )

        return result

    async def analyze_from_address(
        self,
        address: str,
        postcode: str | None = None,
        proposal: str = "",
        application_type: str = "full",
        constraints: list[str] | None = None,
        max_policies: int = 20,
        max_cases: int = 10,
    ) -> LPAAnalysisResult:
        """
        Analyze planning policy from address without full Application object.

        Convenience method for quick analysis.

        Args:
            address: Full site address
            postcode: Optional postcode
            proposal: Proposal description
            application_type: Type of application
            constraints: List of constraint types
            max_policies: Maximum policies to retrieve
            max_cases: Maximum comparable cases to retrieve

        Returns:
            LPAAnalysisResult with complete analysis
        """
        from plana.core.models import (
            Address,
            Application,
            ApplicationType,
            Constraint,
        )

        # Build minimal Application object
        app_address = Address(
            full_address=address,
            postcode=postcode,
        )

        app_constraints = [
            Constraint(constraint_type=c, name=c) for c in (constraints or [])
        ]

        # Map application type string to enum
        type_map = {
            "full": ApplicationType.FULL,
            "householder": ApplicationType.HOUSEHOLDER,
            "listed_building": ApplicationType.LISTED_BUILDING,
            "conservation_area": ApplicationType.CONSERVATION_AREA,
            "change_of_use": ApplicationType.CHANGE_OF_USE,
            "outline": ApplicationType.OUTLINE,
        }
        app_type = type_map.get(application_type.lower(), ApplicationType.FULL)

        application = Application(
            reference="ANALYSIS",
            council_id="",  # Will be detected
            address=app_address,
            proposal=proposal or "Planning application",
            application_type=app_type,
            constraints=app_constraints,
        )

        return await self.analyze(
            application=application,
            max_policies=max_policies,
            max_cases=max_cases,
        )
