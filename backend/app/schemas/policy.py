import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PolicyStatus


class PolicyCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    category: str | None = None
    effective_date: date | None = None
    review_date: date | None = None
    owner_id: uuid.UUID | None = None
    tags: list[str] | None = None


class PolicyUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = Field(default=None, min_length=1)
    category: str | None = None
    status: PolicyStatus | None = None
    effective_date: date | None = None
    review_date: date | None = None
    owner_id: uuid.UUID | None = None
    tags: list[str] | None = None


class PolicyResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    category: str | None
    version: int
    status: PolicyStatus
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    effective_date: date | None
    review_date: date | None
    owner_id: uuid.UUID | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PolicyListResponse(BaseModel):
    items: list[PolicyResponse]
    total: int
    limit: int
    offset: int


class PolicyQueryParams(BaseModel):
    category: str | None = None
    status: PolicyStatus | None = None
    search: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
