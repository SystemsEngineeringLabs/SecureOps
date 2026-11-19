import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.permissions import Action, Resource
from app.db.tenant_session import get_tenant_db
from app.models.membership import Membership
from app.models.user import User
from app.schemas.vendor import (
    VendorCreateRequest,
    VendorListResponse,
    VendorQueryParams,
    VendorResponse,
    VendorSummary,
    VendorUpdateRequest,
)
from app.services.vendor_service import VendorService

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> VendorResponse:
    _, membership = user_membership
    svc = VendorService(db)
    vendor = await svc.create_vendor(membership.tenant_id, data)
    return VendorResponse.model_validate(vendor)


@router.get("", response_model=VendorListResponse)
async def list_vendors(
    category: str | None = Query(None),
    vendor_status: str | None = Query(None, alias="status"),
    risk_level: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> VendorListResponse:
    _, membership = user_membership
    params = VendorQueryParams(
        category=category,
        status=vendor_status,
        risk_level=risk_level,
        search=search,
        limit=limit,
        offset=offset,
    )
    svc = VendorService(db)
    items, total = await svc.list_vendors(membership.tenant_id, params)
    return VendorListResponse(
        items=[VendorResponse.model_validate(v) for v in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=VendorSummary)
async def vendor_summary(
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> VendorSummary:
    _, membership = user_membership
    svc = VendorService(db)
    return await svc.get_vendor_summary(membership.tenant_id)


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.READ)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> VendorResponse:
    _, membership = user_membership
    svc = VendorService(db)
    vendor = await svc.get_vendor(membership.tenant_id, vendor_id)
    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found"
        )
    return VendorResponse.model_validate(vendor)


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    data: VendorUpdateRequest,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> VendorResponse:
    _, membership = user_membership
    svc = VendorService(db)
    vendor = await svc.update_vendor(membership.tenant_id, vendor_id, data)
    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found"
        )
    return VendorResponse.model_validate(vendor)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.DELETE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> None:
    _, membership = user_membership
    svc = VendorService(db)
    deleted = await svc.delete_vendor(membership.tenant_id, vendor_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found"
        )


@router.post("/{vendor_id}/assess", response_model=VendorResponse)
async def record_vendor_assessment(
    vendor_id: uuid.UUID,
    user_membership: tuple[User, Membership] = Depends(
        require_permission(Resource.VENDORS, Action.WRITE)
    ),
    db: AsyncSession = Depends(get_tenant_db),
) -> VendorResponse:
    _, membership = user_membership
    svc = VendorService(db)
    vendor = await svc.record_assessment(membership.tenant_id, vendor_id)
    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found"
        )
    return VendorResponse.model_validate(vendor)
