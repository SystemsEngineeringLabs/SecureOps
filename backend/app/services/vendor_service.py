from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant_session import apply_tenant_filter
from app.models.enums import VendorRiskLevel, VendorStatus
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreateRequest, VendorQueryParams, VendorSummary, VendorUpdateRequest


class VendorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_vendor(
        self, tenant_id: UUID, data: VendorCreateRequest
    ) -> Vendor:
        vendor = Vendor(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            category=data.category,
            contact_name=data.contact_name,
            contact_email=data.contact_email,
            website=data.website,
            risk_level=data.risk_level,
            status=data.status,
            contract_start=data.contract_start,
            contract_end=data.contract_end,
            owner_id=data.owner_id,
            notes=data.notes,
        )
        self.db.add(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor

    async def get_vendor(self, tenant_id: UUID, vendor_id: UUID) -> Vendor | None:
        query = select(Vendor).where(Vendor.id == vendor_id)
        query = apply_tenant_filter(query, Vendor, tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_vendor(
        self, tenant_id: UUID, vendor_id: UUID, data: VendorUpdateRequest
    ) -> Vendor | None:
        vendor = await self.get_vendor(tenant_id, vendor_id)
        if vendor is None:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(vendor, field, value)

        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor

    async def delete_vendor(self, tenant_id: UUID, vendor_id: UUID) -> bool:
        vendor = await self.get_vendor(tenant_id, vendor_id)
        if vendor is None:
            return False
        await self.db.delete(vendor)
        await self.db.flush()
        return True

    async def list_vendors(
        self, tenant_id: UUID, params: VendorQueryParams
    ) -> tuple[list[Vendor], int]:
        base = select(Vendor)
        base = apply_tenant_filter(base, Vendor, tenant_id)

        if params.category is not None:
            base = base.where(Vendor.category == params.category)
        if params.status is not None:
            base = base.where(Vendor.status == params.status)
        if params.risk_level is not None:
            base = base.where(Vendor.risk_level == params.risk_level)
        if params.search:
            pattern = f"%{params.search}%"
            base = base.where(Vendor.name.ilike(pattern))

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        query = base.order_by(Vendor.name.asc()).offset(params.offset).limit(params.limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_vendor_summary(self, tenant_id: UUID) -> VendorSummary:
        base = select(Vendor)
        base = apply_tenant_filter(base, Vendor, tenant_id)

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        # Status breakdown
        status_query = (
            select(Vendor.status, func.count())
            .where(Vendor.tenant_id == tenant_id)
            .group_by(Vendor.status)
        )
        status_result = await self.db.execute(status_query)
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # Risk level breakdown
        risk_query = (
            select(Vendor.risk_level, func.count())
            .where(Vendor.tenant_id == tenant_id)
            .where(Vendor.risk_level.isnot(None))
            .group_by(Vendor.risk_level)
        )
        risk_result = await self.db.execute(risk_query)
        by_risk_level = {row[0].value: row[1] for row in risk_result.all()}

        # Contracts expiring within 90 days
        threshold = date.today() + timedelta(days=90)
        expiring_query = (
            select(func.count())
            .select_from(Vendor)
            .where(Vendor.tenant_id == tenant_id)
            .where(Vendor.contract_end.isnot(None))
            .where(Vendor.contract_end <= threshold)
            .where(Vendor.contract_end >= date.today())
            .where(Vendor.status == VendorStatus.ACTIVE)
        )
        expiring_result = await self.db.execute(expiring_query)
        contracts_expiring_soon = expiring_result.scalar_one()

        return VendorSummary(
            total=total,
            by_status=by_status,
            by_risk_level=by_risk_level,
            contracts_expiring_soon=contracts_expiring_soon,
        )

    async def record_assessment(
        self, tenant_id: UUID, vendor_id: UUID
    ) -> Vendor | None:
        vendor = await self.get_vendor(tenant_id, vendor_id)
        if vendor is None:
            return None

        now = datetime.now(timezone.utc)
        vendor.last_assessment_at = now
        vendor.next_assessment_at = now + timedelta(days=365)
        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor
