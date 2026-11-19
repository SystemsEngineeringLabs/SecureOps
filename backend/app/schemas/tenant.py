from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MembershipRole


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)


class MemberInviteRequest(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.ENGINEER


class TenantMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: MembershipRole
    is_active: bool
    joined_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
