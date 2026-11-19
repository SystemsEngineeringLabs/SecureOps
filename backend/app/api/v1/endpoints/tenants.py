from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.permissions import Action, Resource
from app.core.tenant_context import get_tenant
from app.db.tenant_session import get_tenant_db
from app.models.membership import Membership
from app.models.user import User
from app.schemas.tenant import (
    MemberInviteRequest,
    TenantMemberResponse,
    TenantResponse,
    TenantUpdateRequest,
)
from app.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    db: AsyncSession = Depends(get_tenant_db),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.ADMIN, Action.READ)),
) -> TenantResponse:
    tenant_id = get_tenant()
    tenant = await tenant_service.get_tenant(db, tenant_id)
    return TenantResponse.model_validate(tenant)


@router.put("/current", response_model=TenantResponse)
async def update_current_tenant(
    data: TenantUpdateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.ADMIN, Action.WRITE)),
) -> TenantResponse:
    tenant_id = get_tenant()
    tenant = await tenant_service.update_tenant(db, tenant_id, data)
    return TenantResponse.model_validate(tenant)


@router.get("/current/members", response_model=list[TenantMemberResponse])
async def list_tenant_members(
    db: AsyncSession = Depends(get_tenant_db),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.ADMIN, Action.READ)),
) -> list[TenantMemberResponse]:
    tenant_id = get_tenant()
    members = await tenant_service.list_members(db, tenant_id)
    return [TenantMemberResponse.model_validate(m) for m in members]


@router.post("/current/members/invite", response_model=TenantMemberResponse, status_code=201)
async def invite_tenant_member(
    data: MemberInviteRequest,
    db: AsyncSession = Depends(get_tenant_db),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.ADMIN, Action.ADMIN)),
) -> TenantMemberResponse:
    _user, membership = auth
    tenant_id = get_tenant()
    new_membership = await tenant_service.invite_member(
        db, tenant_id, data.email, data.role, invited_by=membership.user_id
    )

    user_result = await db.execute(
        select(User).where(User.id == new_membership.user_id)
    )
    user = user_result.scalar_one()

    return TenantMemberResponse(
        id=new_membership.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=new_membership.role,
        is_active=new_membership.is_active,
        joined_at=new_membership.joined_at,
    )
