import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.permissions import Action, Resource
from app.db.tenant_session import get_tenant_db
from app.models.membership import Membership
from app.models.user import User
from app.schemas.policy import (
    PolicyCreateRequest,
    PolicyListResponse,
    PolicyQueryParams,
    PolicyResponse,
    PolicyUpdateRequest,
)
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: PolicyCreateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> PolicyResponse:
    _, membership = user_membership
    svc = PolicyService(db)
    policy = await svc.create_policy(membership.tenant_id, data)
    return PolicyResponse.model_validate(policy)


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    category: str | None = Query(None),
    policy_status: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> PolicyListResponse:
    _, membership = user_membership
    params = PolicyQueryParams(
        category=category,
        status=policy_status,
        search=search,
        limit=limit,
        offset=offset,
    )
    svc = PolicyService(db)
    items, total = await svc.list_policies(membership.tenant_id, params)
    return PolicyListResponse(
        items=[PolicyResponse.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> PolicyResponse:
    _, membership = user_membership
    svc = PolicyService(db)
    policy = await svc.get_policy(membership.tenant_id, policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return PolicyResponse.model_validate(policy)


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    data: PolicyUpdateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> PolicyResponse:
    _, membership = user_membership
    svc = PolicyService(db)
    policy = await svc.update_policy(membership.tenant_id, policy_id, data)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return PolicyResponse.model_validate(policy)


@router.post("/{policy_id}/publish", response_model=PolicyResponse)
async def publish_policy(
    policy_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.ADMIN)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> PolicyResponse:
    user, membership = user_membership
    svc = PolicyService(db)
    policy = await svc.publish_policy(membership.tenant_id, policy_id, user.id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return PolicyResponse.model_validate(policy)


@router.post("/{policy_id}/archive", response_model=PolicyResponse)
async def archive_policy(
    policy_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.ADMIN)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> PolicyResponse:
    _, membership = user_membership
    svc = PolicyService(db)
    policy = await svc.archive_policy(membership.tenant_id, policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.POLICIES, Action.DELETE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> None:
    _, membership = user_membership
    svc = PolicyService(db)
    deleted = await svc.delete_policy(membership.tenant_id, policy_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
