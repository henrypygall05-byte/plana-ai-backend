"""
LPA Jurisdiction Enforcement API Endpoints.

Provides strict Local Planning Authority boundary enforcement for
planning policy analysis. All requests are validated against LPA
boundaries and policy/case retrieval is strictly filtered.

Key requirements enforced:
- All policy retrieval filtered by planning_authority == identified_LPA
- All comparable application searches filtered by planning_authority == identified_LPA
- No cross-authority semantic retrieval
- NPPF may be used nationally, but all local policy must be authority-specific
- Multiple LPA detection halts and requests clarification
"""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from plana.core.models import Address, Application, ApplicationType, Constraint
from plana.jurisdiction import (
    JurisdictionService,
    LPAStrictAnalyzer,
    MultipleJurisdictionsError,
    UnknownJurisdictionError,
)

router = APIRouter(redirect_slashes=True)
logger = structlog.get_logger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class LPAIdentifyRequest(BaseModel):
    """Request to identify Local Planning Authority from location."""

    address: str = Field(..., description="Full site address")
    postcode: str | None = Field(None, description="Postcode (optional, extracted if not provided)")
    allow_boundary_ambiguity: bool = Field(
        False,
        description="If True, returns first match for boundary cases instead of error",
    )


class LPAIdentifyResponse(BaseModel):
    """Response with identified Local Planning Authority."""

    council_id: str
    council_name: str
    is_confirmed: bool
    confidence_score: float
    adopted_local_plan: dict[str, Any] | None
    supplementary_documents: list[str]
    boundary_warning: str | None
    notes: list[str]


class LPAAnalyzeRequest(BaseModel):
    """Request for LPA-strict policy analysis."""

    address: str = Field(..., description="Full site address")
    postcode: str | None = Field(None, description="Postcode")
    proposal: str = Field(..., description="Proposal description")
    application_type: str = Field("full", description="Application type")
    constraints: list[str] = Field(default_factory=list, description="Site constraints")
    council_id: str | None = Field(
        None,
        description="Explicit council_id (overrides auto-detection)",
    )
    max_policies: int = Field(20, ge=1, le=50, description="Maximum policies to return")
    max_cases: int = Field(10, ge=1, le=30, description="Maximum comparable cases")
    allow_boundary_ambiguity: bool = Field(
        False,
        description="If True, allows boundary ambiguity (returns warning instead of error)",
    )


class LPAAnalyzeResponse(BaseModel):
    """Response with complete LPA-strict analysis."""

    identified_local_planning_authority: dict[str, Any]
    adopted_local_plan: dict[str, Any]
    supplementary_planning_documents: list[str]
    relevant_local_plan_policies: list[dict[str, Any]]
    relevant_spd_policies: list[dict[str, Any]]
    relevant_nppf_paragraphs: list[dict[str, Any]]
    comparable_applications: list[dict[str, Any]]
    jurisdiction_enforcement: dict[str, Any]
    analysis_timestamp: str
    analysis_notes: list[str]


class JurisdictionErrorResponse(BaseModel):
    """Error response for jurisdiction issues."""

    error_type: str
    message: str
    address: str
    postcode: str | None
    detected_authorities: list[str] | None = None
    suggestion: str


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.post("/identify", response_model=LPAIdentifyResponse)
async def identify_lpa(request: LPAIdentifyRequest) -> LPAIdentifyResponse:
    """
    Identify the Local Planning Authority for a given location.

    This endpoint identifies which LPA has statutory planning control
    over the provided address. If the location is near authority boundaries,
    an error is returned unless allow_boundary_ambiguity is True.

    Args:
        request: Location details for LPA identification

    Returns:
        LPAIdentifyResponse with identified authority details

    Raises:
        HTTPException 400: If LPA cannot be identified or multiple detected
    """
    try:
        service = JurisdictionService()
        result = service.identify_lpa(
            address=request.address,
            postcode=request.postcode,
            allow_boundary_ambiguity=request.allow_boundary_ambiguity,
        )

        return LPAIdentifyResponse(
            council_id=result.council_id,
            council_name=result.council_name,
            is_confirmed=result.is_confirmed,
            confidence_score=result.confidence_score,
            adopted_local_plan=(
                {
                    "plan_name": result.adopted_local_plan.plan_name,
                    "adoption_date": (
                        result.adopted_local_plan.adoption_date.isoformat()
                        if result.adopted_local_plan.adoption_date
                        else None
                    ),
                    "plan_period": result.adopted_local_plan.plan_period,
                    "status": result.adopted_local_plan.status,
                }
                if result.adopted_local_plan
                else None
            ),
            supplementary_documents=result.supplementary_documents,
            boundary_warning=result.boundary_warning,
            notes=result.notes,
        )

    except MultipleJurisdictionsError as e:
        logger.warning(
            "Multiple jurisdictions detected",
            address=request.address,
            authorities=e.detected_authorities,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "multiple_jurisdictions",
                "message": str(e),
                "address": e.address,
                "postcode": e.postcode,
                "detected_authorities": e.detected_authorities,
                "suggestion": (
                    "Please provide a more specific address or postcode to resolve "
                    "the jurisdiction, or explicitly specify the council_id parameter."
                ),
            },
        )

    except UnknownJurisdictionError as e:
        logger.warning(
            "Unknown jurisdiction",
            address=request.address,
            postcode=request.postcode,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "unknown_jurisdiction",
                "message": str(e),
                "address": e.address,
                "postcode": e.postcode,
                "detected_authorities": None,
                "suggestion": (
                    "Please provide a valid UK address within a supported council area, "
                    "or use the /jurisdiction/councils endpoint to see supported councils."
                ),
            },
        )


@router.post("/analyze", response_model=LPAAnalyzeResponse)
async def analyze_with_strict_lpa_enforcement(
    request: LPAAnalyzeRequest,
) -> LPAAnalyzeResponse:
    """
    Perform comprehensive planning policy analysis with strict LPA enforcement.

    This endpoint provides:
    - Identified Local Planning Authority
    - Adopted Local Plan version and date
    - Relevant policy references (LPA-filtered)
    - Relevant NPPF paragraphs
    - Comparable applications from the same authority only

    All policy and case retrieval is strictly filtered to the identified LPA.
    Cross-authority contamination is not permitted.

    Args:
        request: Analysis request with location and proposal details

    Returns:
        LPAAnalyzeResponse with complete LPA-strict analysis

    Raises:
        HTTPException 400: If jurisdiction cannot be resolved
    """
    try:
        analyzer = LPAStrictAnalyzer()

        # Build Application object
        app_address = Address(
            full_address=request.address,
            postcode=request.postcode,
        )

        app_constraints = [
            Constraint(constraint_type=c, name=c) for c in request.constraints
        ]

        # Map application type
        type_map = {
            "full": ApplicationType.FULL,
            "householder": ApplicationType.HOUSEHOLDER,
            "listed_building": ApplicationType.LISTED_BUILDING,
            "conservation_area": ApplicationType.CONSERVATION_AREA,
            "change_of_use": ApplicationType.CHANGE_OF_USE,
            "outline": ApplicationType.OUTLINE,
        }
        app_type = type_map.get(request.application_type.lower(), ApplicationType.FULL)

        application = Application(
            reference="ANALYSIS",
            council_id=request.council_id or "",
            address=app_address,
            proposal=request.proposal,
            application_type=app_type,
            constraints=app_constraints,
        )

        # Perform analysis with strict LPA enforcement
        result = await analyzer.analyze(
            application=application,
            council_id=request.council_id,
            max_policies=request.max_policies,
            max_cases=request.max_cases,
            allow_boundary_ambiguity=request.allow_boundary_ambiguity,
        )

        # Convert to response
        result_dict = result.to_dict()
        return LPAAnalyzeResponse(**result_dict)

    except MultipleJurisdictionsError as e:
        logger.warning(
            "Multiple jurisdictions detected during analysis",
            address=request.address,
            authorities=e.detected_authorities,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "multiple_jurisdictions",
                "message": str(e),
                "address": e.address,
                "postcode": e.postcode,
                "detected_authorities": e.detected_authorities,
                "suggestion": (
                    "Jurisdictional contamination is not permitted. "
                    "Please provide a more specific address or explicitly specify council_id."
                ),
            },
        )

    except UnknownJurisdictionError as e:
        logger.warning(
            "Unknown jurisdiction during analysis",
            address=request.address,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "unknown_jurisdiction",
                "message": str(e),
                "address": e.address,
                "postcode": e.postcode,
                "detected_authorities": None,
                "suggestion": (
                    "Unable to identify Local Planning Authority. "
                    "Please provide a valid UK address or specify council_id."
                ),
            },
        )


@router.get("/councils")
async def list_supported_councils() -> list[dict[str, Any]]:
    """
    List all supported Local Planning Authorities.

    Returns councils that have Local Plan data and can be used
    for strict policy analysis.
    """
    service = JurisdictionService()

    councils = []
    for council_id in service.get_supported_councils():
        local_plan = service.get_local_plan_info(council_id)
        spds = service.get_spd_list(council_id)

        councils.append({
            "council_id": council_id,
            "council_name": service._get_council_name(council_id),
            "local_plan": {
                "plan_name": local_plan.plan_name if local_plan else None,
                "adoption_date": (
                    local_plan.adoption_date.isoformat()
                    if local_plan and local_plan.adoption_date
                    else None
                ),
                "plan_period": local_plan.plan_period if local_plan else None,
                "status": local_plan.status if local_plan else None,
            },
            "supplementary_documents_count": len(spds),
        })

    return councils


@router.get("/validate/{council_id}")
async def validate_council_id(council_id: str) -> dict[str, Any]:
    """
    Validate if a council_id is supported for strict analysis.

    Args:
        council_id: The council identifier to validate

    Returns:
        Validation result with council details if valid
    """
    service = JurisdictionService()

    if service.validate_council_id(council_id):
        local_plan = service.get_local_plan_info(council_id)
        return {
            "valid": True,
            "council_id": council_id.lower(),
            "council_name": service._get_council_name(council_id),
            "local_plan_available": local_plan is not None,
        }
    else:
        supported = service.get_supported_councils()
        return {
            "valid": False,
            "council_id": council_id,
            "message": f"Council '{council_id}' is not supported for strict LPA analysis",
            "supported_councils": supported,
        }
