import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RiskImpact, RiskLikelihood, RiskStatus
from app.models.risk import IMPACT_SCORES, LIKELIHOOD_SCORES, Risk, compute_risk_score
from app.schemas.risk import (
    RiskCreateRequest,
    RiskHeatmapCell,
    RiskHeatmapResponse,
    RiskQueryParams,
    RiskSummary,
    RiskUpdateRequest,
)

REVIEW_INTERVAL_DAYS = 90


class RiskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_risk(
        self,
        tenant_id: uuid.UUID,
        data: RiskCreateRequest,
        created_by: uuid.UUID,  # noqa: ARG002 - TODO: persist risk creator
    ) -> Risk:
        inherent = compute_risk_score(data.likelihood, data.impact)
        risk = Risk(
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            category=data.category,
            source="manual",
            likelihood=data.likelihood,
            impact=data.impact,
            inherent_score=inherent or 0.0,
            treatment=data.treatment,
            treatment_plan=data.treatment_plan,
            status=RiskStatus.OPEN,
            owner_id=data.owner_id,
            due_date=data.due_date,
            related_control_ids=[str(c) for c in data.related_control_ids]
            if data.related_control_ids
            else None,
        )
        self.db.add(risk)
        await self.db.flush()
        return risk

    async def get_risk(self, tenant_id: uuid.UUID, risk_id: uuid.UUID) -> Risk | None:
        stmt = select(Risk).where(Risk.tenant_id == tenant_id, Risk.id == risk_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_risk(
        self, tenant_id: uuid.UUID, risk_id: uuid.UUID, data: RiskUpdateRequest
    ) -> Risk | None:
        risk = await self.get_risk(tenant_id, risk_id)
        if risk is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        recompute_inherent = False
        recompute_residual = False

        for field, value in update_data.items():
            if field == "related_control_ids" and value is not None:
                value = [str(c) for c in value]
            if field in ("likelihood", "impact"):
                recompute_inherent = True
            if field in ("residual_likelihood", "residual_impact"):
                recompute_residual = True
            setattr(risk, field, value)

        if recompute_inherent:
            risk.inherent_score = compute_risk_score(risk.likelihood, risk.impact) or 0.0

        if recompute_residual:
            risk.residual_score = compute_risk_score(risk.residual_likelihood, risk.residual_impact)

        await self.db.flush()
        return risk

    async def delete_risk(self, tenant_id: uuid.UUID, risk_id: uuid.UUID) -> bool:
        risk = await self.get_risk(tenant_id, risk_id)
        if risk is None:
            return False
        risk.status = RiskStatus.CLOSED
        await self.db.flush()
        return True

    async def list_risks(
        self, tenant_id: uuid.UUID, params: RiskQueryParams
    ) -> tuple[list[Risk], int]:
        base = select(Risk).where(Risk.tenant_id == tenant_id)

        if params.category is not None:
            base = base.where(Risk.category == params.category)
        if params.status is not None:
            base = base.where(Risk.status == params.status)
        if params.likelihood is not None:
            base = base.where(Risk.likelihood == params.likelihood)
        if params.impact is not None:
            base = base.where(Risk.impact == params.impact)
        if params.owner_id is not None:
            base = base.where(Risk.owner_id == params.owner_id)
        if params.min_score is not None:
            base = base.where(Risk.inherent_score >= params.min_score)
        if params.search:
            pattern = f"%{params.search}%"
            base = base.where(Risk.title.ilike(pattern) | Risk.description.ilike(pattern))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        sort_col = getattr(Risk, params.sort_by, Risk.inherent_score)
        if params.sort_order == "asc":
            base = base.order_by(sort_col.asc())
        else:
            base = base.order_by(sort_col.desc())

        base = base.offset(params.offset).limit(params.limit)
        result = await self.db.execute(base)
        return list(result.scalars().all()), total

    async def get_risk_summary(self, tenant_id: uuid.UUID) -> RiskSummary:
        stmt = select(Risk).where(Risk.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        risks = list(result.scalars().all())

        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        by_risk_level: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_inherent = 0.0
        total_residual = 0.0
        residual_count = 0

        for r in risks:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
            by_category[r.category.value] = by_category.get(r.category.value, 0) + 1
            level = self.score_to_level(r.inherent_score)
            by_risk_level[level] = by_risk_level.get(level, 0) + 1
            total_inherent += r.inherent_score
            if r.residual_score is not None:
                total_residual += r.residual_score
                residual_count += 1

        total = len(risks)
        return RiskSummary(
            total=total,
            by_status=by_status,
            by_category=by_category,
            by_risk_level=by_risk_level,
            average_inherent_score=round(total_inherent / total, 2) if total else 0.0,
            average_residual_score=round(total_residual / residual_count, 2)
            if residual_count
            else None,
        )

    async def get_risk_heatmap(self, tenant_id: uuid.UUID) -> RiskHeatmapResponse:
        stmt = select(Risk).where(Risk.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        risks = list(result.scalars().all())

        grid: dict[tuple[str, str], list[uuid.UUID]] = {}
        for lk in RiskLikelihood:
            for imp in RiskImpact:
                grid[(lk.value, imp.value)] = []

        for r in risks:
            grid[(r.likelihood.value, r.impact.value)].append(r.id)

        cells = [
            RiskHeatmapCell(
                likelihood=lk,
                impact=imp,
                count=len(ids),
                risk_ids=ids,
            )
            for (lk, imp), ids in grid.items()
        ]
        return RiskHeatmapResponse(cells=cells)

    async def mark_reviewed(self, tenant_id: uuid.UUID, risk_id: uuid.UUID) -> Risk | None:
        risk = await self.get_risk(tenant_id, risk_id)
        if risk is None:
            return None
        now = datetime.now(UTC)
        risk.last_reviewed_at = now
        risk.next_review_at = now + timedelta(days=REVIEW_INTERVAL_DAYS)
        await self.db.flush()
        return risk

    @staticmethod
    def compute_score(likelihood: RiskLikelihood, impact: RiskImpact) -> float:
        return float(LIKELIHOOD_SCORES[likelihood] * IMPACT_SCORES[impact])

    @staticmethod
    def score_to_level(score: float) -> str:
        if score >= 15:
            return "critical"
        if score >= 10:
            return "high"
        if score >= 5:
            return "medium"
        return "low"
