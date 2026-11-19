from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    id: UUID
    action: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    user_id: UUID | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditQueryParams(BaseModel):
    action: str | None = None
    resource_type: str | None = None
    user_id: UUID | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class AuditListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
    limit: int
    offset: int
