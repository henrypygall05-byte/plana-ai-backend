"""Policy management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from plana.core.models import PolicyType
from plana.policies import PolicyManager

router = APIRouter()


class PolicyResponse(BaseModel):
    """Policy response model."""

    id: str
    reference: str
    title: str
    policy_type: str
    summary: str | None
    council_id: str | None
    is_current: bool


class PolicyDetailResponse(BaseModel):
    """Detailed policy response."""

    id: str
    reference: str
    title: str
    policy_type: str
    content: str
    summary: str | None
    chapter: str | None
    council_id: str | None
    source_url: str | None
    is_current: bool


@router.get("/")
async def list_policies(
    policy_type: str | None = Query(None, description="Filter by policy type"),
    council_id: str | None = Query(None, description="Filter by council"),
    current_only: bool = Query(True, description="Only current policies"),
) -> list[PolicyResponse]:
    """List planning policies.

    Args:
        policy_type: Filter by type (nppf, local_plan, etc.)
        council_id: Filter by council
        current_only: Only return current policies
    """
    manager = PolicyManager()
    await manager.load_policies()

    type_filter = None
    if policy_type:
        try:
            type_filter = PolicyType(policy_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid policy type: {policy_type}",
            )

    policies = manager.list_policies(
        policy_type=type_filter,
        council_id=council_id,
        current_only=current_only,
    )

    return [
        PolicyResponse(
            id=p.id,
            reference=p.reference,
            title=p.title,
            policy_type=p.policy_type.value,
            summary=p.summary,
            council_id=p.council_id,
            is_current=p.is_current,
        )
        for p in policies
    ]


@router.get("/{policy_id}")
async def get_policy(policy_id: str) -> PolicyDetailResponse:
    """Get a policy by ID.

    Args:
        policy_id: Policy ID
    """
    manager = PolicyManager()
    await manager.load_policies()

    policy = manager.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return PolicyDetailResponse(
        id=policy.id,
        reference=policy.reference,
        title=policy.title,
        policy_type=policy.policy_type.value,
        content=policy.content,
        summary=policy.summary,
        chapter=policy.chapter,
        council_id=policy.council_id,
        source_url=policy.source_url,
        is_current=policy.is_current,
    )


@router.get("/reference/{reference}")
async def get_policy_by_reference(
    reference: str,
    council_id: str | None = Query(None),
) -> PolicyDetailResponse:
    """Get a policy by reference code.

    Args:
        reference: Policy reference (e.g., 'DM20', 'NPPF-12')
        council_id: Council ID for local policies
    """
    manager = PolicyManager()
    await manager.load_policies()

    policy = manager.get_policy_by_reference(reference, council_id=council_id)
    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"Policy {reference} not found",
        )

    return PolicyDetailResponse(
        id=policy.id,
        reference=policy.reference,
        title=policy.title,
        policy_type=policy.policy_type.value,
        content=policy.content,
        summary=policy.summary,
        chapter=policy.chapter,
        council_id=policy.council_id,
        source_url=policy.source_url,
        is_current=policy.is_current,
    )


@router.get("/types")
async def list_policy_types() -> list[dict[str, str]]:
    """List available policy types."""
    return [
        {"value": pt.value, "name": pt.name}
        for pt in PolicyType
    ]
