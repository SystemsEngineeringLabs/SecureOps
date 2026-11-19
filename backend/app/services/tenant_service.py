import re
import unicodedata
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MembershipRole
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantUpdateRequest


async def get_tenant(db: AsyncSession, tenant_id: UUID) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


async def update_tenant(
    db: AsyncSession, tenant_id: UUID, data: TenantUpdateRequest
) -> Tenant:
    tenant = await get_tenant(db, tenant_id)
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = await db.execute(
            select(Tenant).where(Tenant.name == update_data["name"], Tenant.id != tenant_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A tenant with this name already exists",
            )
        tenant.name = update_data["name"]
        tenant.slug = await generate_tenant_slug(db, update_data["name"], exclude_id=tenant_id)

    await db.flush()
    await db.refresh(tenant)
    return tenant


async def list_members(db: AsyncSession, tenant_id: UUID) -> list[dict]:
    result = await db.execute(
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.tenant_id == tenant_id)
        .order_by(Membership.joined_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": membership.id,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": membership.role,
            "is_active": membership.is_active,
            "joined_at": membership.joined_at,
        }
        for membership, user in rows
    ]


async def invite_member(
    db: AsyncSession,
    tenant_id: UUID,
    email: str,
    role: MembershipRole,
    invited_by: UUID,
) -> Membership:
    result = await db.execute(
        select(Membership)
        .join(User, Membership.user_id == User.id)
        .where(Membership.tenant_id == tenant_id, User.email == email)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this tenant",
        )

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()

    if user is None:
        user = User(email=email, hashed_password="PENDING_REGISTRATION", full_name="", is_active=False)
        db.add(user)
        await db.flush()

    membership = Membership(
        tenant_id=tenant_id,
        user_id=user.id,
        role=role,
        invited_by=invited_by,
        is_active=user.is_active,
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)
    return membership


async def create_tenant(db: AsyncSession, name: str) -> Tenant:
    slug = await generate_tenant_slug(db, name)
    tenant = Tenant(name=name, slug=slug)
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


async def generate_tenant_slug(
    db: AsyncSession, name: str, exclude_id: UUID | None = None
) -> str:
    slug = unicodedata.normalize("NFKD", name.lower())
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")

    if not slug:
        slug = "tenant"

    candidate = slug
    counter = 1
    while True:
        query = select(Tenant).where(Tenant.slug == candidate)
        if exclude_id is not None:
            query = query.where(Tenant.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{slug}-{counter}"
        counter += 1
