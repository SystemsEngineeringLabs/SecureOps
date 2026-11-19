import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.dependencies import get_current_active_user
from app.core.permissions import Action, Resource
from app.db.tenant_session import get_tenant_db
from app.models.membership import Membership
from app.models.user import User
from app.schemas.framework import (
    ControlDetailResponse,
    ControlMappingResponse,
    ControlResponse,
    ControlStatusSummary,
    FrameworkDetailResponse,
    FrameworkResponse,
    FrameworkVersionResponse,
    GapAssessmentResponse,
    TenantControlStatusResponse,
    TenantControlStatusUpdateRequest,
)
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/frameworks", response_model=list[FrameworkResponse])
async def list_frameworks(
    active_only: bool = Query(True),
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[FrameworkResponse]:
    svc = ComplianceService(db)
    frameworks = await svc.list_frameworks(active_only=active_only)
    return [FrameworkResponse.model_validate(f) for f in frameworks]


@router.get("/frameworks/{framework_id}", response_model=FrameworkDetailResponse)
async def get_framework(
    framework_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> FrameworkDetailResponse:
    svc = ComplianceService(db)
    framework = await svc.get_framework(framework_id)
    if framework is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found")

    current_version = next((v for v in framework.versions if v.is_current), None)
    control_count = 0
    if current_version:
        control_count = await svc.get_control_count(current_version.id)

    return FrameworkDetailResponse(
        id=framework.id,
        key=framework.key,
        name=framework.name,
        description=framework.description,
        organization=framework.organization,
        is_active=framework.is_active,
        versions=[FrameworkVersionResponse.model_validate(v) for v in framework.versions],
        control_count=control_count,
    )


@router.get(
    "/frameworks/{framework_id}/versions/{version_id}/controls",
    response_model=list[ControlResponse],
)
async def list_controls(
    framework_id: uuid.UUID,
    version_id: uuid.UUID,
    category: str | None = Query(None),
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[ControlResponse]:
    svc = ComplianceService(db)
    version = await svc.get_framework_version(version_id)
    if version is None or version.framework_id != framework_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework version not found"
        )
    controls = await svc.list_controls(version_id, category=category)
    return [ControlResponse.model_validate(c) for c in controls]


@router.get(
    "/frameworks/{framework_id}/versions/{version_id}/categories",
    response_model=list[str],
)
async def list_control_categories(
    framework_id: uuid.UUID,
    version_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[str]:
    svc = ComplianceService(db)
    version = await svc.get_framework_version(version_id)
    if version is None or version.framework_id != framework_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework version not found"
        )
    return await svc.get_control_categories(version_id)


@router.get("/controls/{control_id}", response_model=ControlDetailResponse)
async def get_control(
    control_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> ControlDetailResponse:
    svc = ComplianceService(db)
    control = await svc.get_control(control_id)
    if control is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    mappings = await svc.get_control_mappings(control_id)
    return ControlDetailResponse(
        id=control.id,
        framework_version_id=control.framework_version_id,
        code=control.code,
        title=control.title,
        description=control.description,
        category=control.category,
        parent_id=control.parent_id,
        sort_order=control.sort_order,
        mappings=[ControlMappingResponse.model_validate(m) for m in mappings],
    )


@router.get("/controls/{control_id}/mappings", response_model=list[ControlMappingResponse])
async def get_control_mappings(
    control_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[ControlMappingResponse]:
    svc = ComplianceService(db)
    mappings = await svc.get_control_mappings(control_id)
    return [ControlMappingResponse.model_validate(m) for m in mappings]


@router.get("/status/{version_id}", response_model=list[TenantControlStatusResponse])
async def get_control_statuses(
    version_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.COMPLIANCE, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[TenantControlStatusResponse]:
    _, membership = user_membership
    svc = ComplianceService(db)
    statuses = await svc.get_tenant_control_statuses(membership.tenant_id, version_id)
    return [TenantControlStatusResponse.model_validate(s) for s in statuses]


@router.put("/status/{control_id}", response_model=TenantControlStatusResponse)
async def update_control_status(
    control_id: uuid.UUID,
    data: TenantControlStatusUpdateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.COMPLIANCE, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> TenantControlStatusResponse:
    _, membership = user_membership
    svc = ComplianceService(db)
    result = await svc.update_control_status(membership.tenant_id, control_id, data)
    return TenantControlStatusResponse.model_validate(result)


@router.get("/summary/{version_id}", response_model=ControlStatusSummary)
async def compliance_summary(
    version_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.COMPLIANCE, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> ControlStatusSummary:
    _, membership = user_membership
    svc = ComplianceService(db)
    return await svc.get_compliance_summary(membership.tenant_id, version_id)


@router.get("/gap-assessment/{version_id}", response_model=GapAssessmentResponse)
async def gap_assessment(
    version_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.COMPLIANCE, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> GapAssessmentResponse:
    _, membership = user_membership
    svc = ComplianceService(db)
    return await svc.get_gap_assessment(membership.tenant_id, version_id)
