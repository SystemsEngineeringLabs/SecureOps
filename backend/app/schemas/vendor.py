import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import VendorRiskLevel, VendorStatus


class VendorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    description: str | None = None
    category: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    website: str | None = None
    risk_level: VendorRiskLevel | None = None
    status: VendorStatus = VendorStatus.ACTIVE
    contract_start: date | None = None
    contract_end: date | None = None
    owner_id: uuid.UUID | None = None
    notes: str | None = None


class VendorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    category: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    website: str | None = None
    risk_level: VendorRiskLevel | None = None
    status: VendorStatus | None = None
    contract_start: date | None = None
    contract_end: date | None = None
    owner_id: uuid.UUID | None = None
    notes: str | None = None


class VendorResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: str | None
    contact_name: str | None
    contact_email: str | None
    website: str | None
    risk_level: VendorRiskLevel | None
    status: VendorStatus
    contract_start: date | None
    contract_end: date | None
    last_assessment_at: datetime | None
    next_assessment_at: datetime | None
    owner_id: uuid.UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class VendorListResponse(BaseModel):
    items: list[VendorResponse]
    total: int
    limit: int
    offset: int


class VendorSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    by_risk_level: dict[str, int]
    contracts_expiring_soon: int


class VendorQueryParams(BaseModel):
    category: str | None = None
    status: VendorStatus | None = None
    risk_level: VendorRiskLevel | None = None
    search: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
