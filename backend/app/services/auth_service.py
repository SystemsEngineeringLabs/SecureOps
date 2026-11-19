import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.enums import MembershipRole
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


async def register(
    db: AsyncSession,
    data: RegisterRequest,
) -> tuple[User, Tenant, Membership]:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("A user with this email already exists")

    slug = _slugify(data.tenant_name)
    existing_tenant = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if existing_tenant.scalar_one_or_none() is not None:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    tenant = Tenant(name=data.tenant_name.strip(), slug=slug)
    db.add(tenant)
    await db.flush()

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name.strip(),
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    membership = Membership(
        tenant_id=tenant.id,
        user_id=user.id,
        role=MembershipRole.ORG_ADMIN,
    )
    db.add(membership)
    await db.flush()

    return user, tenant, membership


async def authenticate(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
    return user


async def get_user_memberships(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Membership]:
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.tenant))
        .where(Membership.user_id == user_id, Membership.is_active.is_(True))
    )
    return list(result.scalars().all())


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_membership(
    db: AsyncSession,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Membership | None:
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.tenant))
        .where(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
            Membership.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


def generate_tokens(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: str,
) -> TokenResponse:
    token_data = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )
