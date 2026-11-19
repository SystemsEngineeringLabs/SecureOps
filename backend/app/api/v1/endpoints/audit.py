from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.permissions import Action, Resource
from app.core.tenant_context import get_tenant
from app.db.tenant_session import get_tenant_db
from app.models.membership import Membership
from app.models.user import User
from app.schemas.audit import AuditEventResponse, AuditListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
async def query_audit_events(
    db: AsyncSession = Depends(get_tenant_db),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.AUDIT, Action.READ)),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    user_id: UUID | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AuditListResponse:
    tenant_id = get_tenant()
    service = AuditService(db)
    events, total = await service.query(
        tenant_id,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )

    return AuditListResponse(
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )
