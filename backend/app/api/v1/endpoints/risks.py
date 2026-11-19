import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.permissions import Action, Resource
from app.db.tenant_session import get_tenant_db
from app.models.enums import RiskCategory, RiskImpact, RiskLikelihood, RiskStatus
from app.models.membership import Membership
from app.models.user import User
from app.schemas.risk import (
    RiskCreateRequest,
    RiskHeatmapResponse,
    RiskListResponse,
    RiskQueryParams,
    RiskResponse,
    RiskSortField,
    RiskSummary,
    RiskUpdateRequest,
    SortOrder,
)
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risks", tags=["Risks"])


@router.post("", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
async def create_risk(
    data: RiskCreateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskResponse:
    user, membership = user_membership
    svc = RiskService(db)
    risk = await svc.create_risk(membership.tenant_id, data, user.id)
    return RiskResponse.model_validate(risk)


@router.get("", response_model=RiskListResponse)
async def list_risks(
    category: RiskCategory | None = Query(None),
    risk_status: RiskStatus | None = Query(None, alias="status"),
    likelihood: RiskLikelihood | None = Query(None),
    impact: RiskImpact | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    min_score: float | None = Query(None),
    search: str | None = Query(None),
    sort_by: RiskSortField = Query("inherent_score"),
    sort_order: SortOrder = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskListResponse:
    _, membership = user_membership
    params = RiskQueryParams(
        category=category,
        status=risk_status,
        likelihood=likelihood,
        impact=impact,
        owner_id=owner_id,
        min_score=min_score,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    svc = RiskService(db)
    items, total = await svc.list_risks(membership.tenant_id, params)
    return RiskListResponse(
        items=[RiskResponse.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=RiskSummary)
async def risk_summary(
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskSummary:
    _, membership = user_membership
    svc = RiskService(db)
    return await svc.get_risk_summary(membership.tenant_id)


@router.get("/heatmap", response_model=RiskHeatmapResponse)
async def risk_heatmap(
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskHeatmapResponse:
    _, membership = user_membership
    svc = RiskService(db)
    return await svc.get_risk_heatmap(membership.tenant_id)


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskResponse:
    _, membership = user_membership
    svc = RiskService(db)
    risk = await svc.get_risk(membership.tenant_id, risk_id)
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return RiskResponse.model_validate(risk)


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: uuid.UUID,
    data: RiskUpdateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskResponse:
    _, membership = user_membership
    svc = RiskService(db)
    risk = await svc.update_risk(membership.tenant_id, risk_id, data)
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return RiskResponse.model_validate(risk)


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(
    risk_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.DELETE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> None:
    _, membership = user_membership
    svc = RiskService(db)
    deleted = await svc.delete_risk(membership.tenant_id, risk_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")


@router.post("/{risk_id}/review", response_model=RiskResponse)
async def mark_risk_reviewed(
    risk_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.RISKS, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> RiskResponse:
    _, membership = user_membership
    svc = RiskService(db)
    risk = await svc.mark_reviewed(membership.tenant_id, risk_id)
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return RiskResponse.model_validate(risk)
