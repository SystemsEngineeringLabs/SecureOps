import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.control import Control, ControlMapping, TenantControlStatus
from app.models.enums import ControlStatus
from app.models.framework import Framework, FrameworkVersion
from app.schemas.framework import (
    ControlDetailResponse,
    ControlStatusSummary,
    GapAssessmentResponse,
    TenantControlStatusResponse,
    TenantControlStatusUpdateRequest,
)


class ComplianceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_frameworks(self, active_only: bool = True) -> list[Framework]:
        stmt = select(Framework).options(selectinload(Framework.versions))
        if active_only:
            stmt = stmt.where(Framework.is_active.is_(True))
        stmt = stmt.order_by(Framework.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_framework(self, framework_id: uuid.UUID) -> Framework | None:
        stmt = (
            select(Framework)
            .options(selectinload(Framework.versions))
            .where(Framework.id == framework_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_framework_version(self, version_id: uuid.UUID) -> FrameworkVersion | None:
        stmt = select(FrameworkVersion).where(FrameworkVersion.id == version_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_framework_versions(self, framework_id: uuid.UUID) -> list[FrameworkVersion]:
        stmt = (
            select(FrameworkVersion)
            .where(FrameworkVersion.framework_id == framework_id)
            .order_by(FrameworkVersion.version.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_controls(
        self,
        framework_version_id: uuid.UUID,
        category: str | None = None,
    ) -> list[Control]:
        stmt = (
            select(Control)
            .where(Control.framework_version_id == framework_version_id)
            .order_by(Control.sort_order, Control.code)
        )
        if category:
            stmt = stmt.where(Control.category == category)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_control(self, control_id: uuid.UUID) -> Control | None:
        stmt = (
            select(Control)
            .options(
                selectinload(Control.source_mappings),
                selectinload(Control.target_mappings),
            )
            .where(Control.id == control_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_control_mappings(self, control_id: uuid.UUID) -> list[ControlMapping]:
        stmt = select(ControlMapping).where(
            (ControlMapping.source_control_id == control_id)
            | (ControlMapping.target_control_id == control_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_control_categories(self, framework_version_id: uuid.UUID) -> list[str]:
        stmt = (
            select(Control.category)
            .where(
                Control.framework_version_id == framework_version_id,
                Control.category.isnot(None),
            )
            .distinct()
            .order_by(Control.category)
        )
        result = await self.db.execute(stmt)
        return [c for c in result.scalars().all() if c is not None]

    async def get_control_count(self, framework_version_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Control)
            .where(Control.framework_version_id == framework_version_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_tenant_control_statuses(
        self,
        tenant_id: uuid.UUID,
        framework_version_id: uuid.UUID,
    ) -> list[TenantControlStatus]:
        stmt = (
            select(TenantControlStatus)
            .join(Control, TenantControlStatus.control_id == Control.id)
            .where(
                TenantControlStatus.tenant_id == tenant_id,
                Control.framework_version_id == framework_version_id,
            )
            .options(selectinload(TenantControlStatus.control))
            .order_by(Control.sort_order, Control.code)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_tenant_control_status(
        self,
        tenant_id: uuid.UUID,
        control_id: uuid.UUID,
    ) -> TenantControlStatus | None:
        stmt = select(TenantControlStatus).where(
            TenantControlStatus.tenant_id == tenant_id,
            TenantControlStatus.control_id == control_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_control_status(
        self,
        tenant_id: uuid.UUID,
        control_id: uuid.UUID,
        data: TenantControlStatusUpdateRequest,
    ) -> TenantControlStatus:
        existing = await self.get_tenant_control_status(tenant_id, control_id)

        if existing:
            existing.status = data.status
            if data.effectiveness is not None:
                existing.effectiveness = data.effectiveness
            if data.owner_id is not None:
                existing.owner_id = data.owner_id
            if data.notes is not None:
                existing.notes = data.notes
            existing.last_assessed_at = datetime.now(UTC)
            await self.db.flush()
            return existing

        new_status = TenantControlStatus(
            tenant_id=tenant_id,
            control_id=control_id,
            status=data.status,
            effectiveness=data.effectiveness,
            owner_id=data.owner_id,
            notes=data.notes,
            last_assessed_at=datetime.now(UTC),
        )
        self.db.add(new_status)
        await self.db.flush()
        await self.db.refresh(new_status)
        return new_status

    async def get_compliance_summary(
        self,
        tenant_id: uuid.UUID,
        framework_version_id: uuid.UUID,
    ) -> ControlStatusSummary:
        total_controls = await self.get_control_count(framework_version_id)
        statuses = await self.get_tenant_control_statuses(tenant_id, framework_version_id)

        counts: dict[ControlStatus, int] = {}
        for s in statuses:
            counts[s.status] = counts.get(s.status, 0) + 1

        implemented = counts.get(ControlStatus.IMPLEMENTED, 0)
        not_applicable = counts.get(ControlStatus.NOT_APPLICABLE, 0)
        assessable = total_controls - not_applicable
        pct = (implemented / assessable * 100) if assessable > 0 else 0.0

        return ControlStatusSummary(
            total=total_controls,
            not_started=total_controls - len(statuses) + counts.get(ControlStatus.NOT_STARTED, 0),
            in_progress=counts.get(ControlStatus.IN_PROGRESS, 0),
            implemented=implemented,
            not_applicable=not_applicable,
            failed=counts.get(ControlStatus.FAILED, 0),
            compliance_percentage=round(pct, 1),
        )

    async def get_gap_assessment(
        self,
        tenant_id: uuid.UUID,
        framework_version_id: uuid.UUID,
    ) -> GapAssessmentResponse:
        summary = await self.get_compliance_summary(tenant_id, framework_version_id)

        all_controls = await self.list_controls(framework_version_id)
        statuses = await self.get_tenant_control_statuses(tenant_id, framework_version_id)
        status_map = {s.control_id: s for s in statuses}

        gaps: list[ControlDetailResponse] = []
        for control in all_controls:
            cs = status_map.get(control.id)
            if cs is None or cs.status not in (
                ControlStatus.IMPLEMENTED,
                ControlStatus.NOT_APPLICABLE,
            ):
                gaps.append(
                    ControlDetailResponse(
                        id=control.id,
                        framework_version_id=control.framework_version_id,
                        code=control.code,
                        title=control.title,
                        description=control.description,
                        category=control.category,
                        parent_id=control.parent_id,
                        sort_order=control.sort_order,
                        tenant_status=TenantControlStatusResponse.model_validate(cs)
                        if cs
                        else None,
                        mappings=[],
                    )
                )

        return GapAssessmentResponse(
            framework_version_id=framework_version_id,
            summary=summary,
            gaps=gaps,
        )

    async def bulk_update_control_statuses(
        self,
        tenant_id: uuid.UUID,
        updates: list[dict[str, Any]],
    ) -> int:
        count = 0
        for update in updates:
            control_id = update["control_id"]
            data = TenantControlStatusUpdateRequest(**update)
            await self.update_control_status(tenant_id, control_id, data)
            count += 1
        return count
