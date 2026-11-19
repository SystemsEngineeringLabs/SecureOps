from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant_session import apply_tenant_filter
from app.models.enums import PolicyStatus
from app.models.policy import Policy
from app.schemas.policy import PolicyCreateRequest, PolicyQueryParams, PolicyUpdateRequest


class PolicyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_policy(
        self, tenant_id: UUID, data: PolicyCreateRequest
    ) -> Policy:
        policy = Policy(
            tenant_id=tenant_id,
            title=data.title,
            content=data.content,
            category=data.category,
            version=1,
            status=PolicyStatus.DRAFT,
            effective_date=data.effective_date,
            review_date=data.review_date,
            owner_id=data.owner_id,
            tags=data.tags,
        )
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def get_policy(self, tenant_id: UUID, policy_id: UUID) -> Policy | None:
        query = select(Policy).where(Policy.id == policy_id)
        query = apply_tenant_filter(query, Policy, tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_policy(
        self, tenant_id: UUID, policy_id: UUID, data: PolicyUpdateRequest
    ) -> Policy | None:
        policy = await self.get_policy(tenant_id, policy_id)
        if policy is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        content_changed = "content" in update_data and update_data["content"] != policy.content

        for field, value in update_data.items():
            setattr(policy, field, value)

        if content_changed:
            policy.version += 1

        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def publish_policy(
        self, tenant_id: UUID, policy_id: UUID, approved_by: UUID
    ) -> Policy | None:
        policy = await self.get_policy(tenant_id, policy_id)
        if policy is None:
            return None

        policy.status = PolicyStatus.PUBLISHED
        policy.approved_by = approved_by
        policy.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def archive_policy(
        self, tenant_id: UUID, policy_id: UUID
    ) -> Policy | None:
        policy = await self.get_policy(tenant_id, policy_id)
        if policy is None:
            return None

        policy.status = PolicyStatus.ARCHIVED
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def list_policies(
        self, tenant_id: UUID, params: PolicyQueryParams
    ) -> tuple[list[Policy], int]:
        base = select(Policy)
        base = apply_tenant_filter(base, Policy, tenant_id)

        if params.category is not None:
            base = base.where(Policy.category == params.category)
        if params.status is not None:
            base = base.where(Policy.status == params.status)
        if params.search:
            pattern = f"%{params.search}%"
            base = base.where(Policy.title.ilike(pattern))

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        query = base.order_by(Policy.created_at.desc()).offset(params.offset).limit(params.limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def delete_policy(self, tenant_id: UUID, policy_id: UUID) -> bool:
        policy = await self.get_policy(tenant_id, policy_id)
        if policy is None:
            return False
        await self.db.delete(policy)
        await self.db.flush()
        return True
