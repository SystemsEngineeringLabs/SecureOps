from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        action: str,
        *,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def query(
        self,
        tenant_id: UUID,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        user_id: UUID | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        base = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)

        if action is not None:
            base = base.where(AuditEvent.action == action)
        if resource_type is not None:
            base = base.where(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            base = base.where(AuditEvent.resource_id == resource_id)
        if user_id is not None:
            base = base.where(AuditEvent.user_id == user_id)
        if since is not None:
            base = base.where(AuditEvent.created_at >= since)
        if until is not None:
            base = base.where(AuditEvent.created_at <= until)

        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()

        rows_result = await self.db.execute(
            base.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
        )
        events = list(rows_result.scalars().all())

        return events, total
