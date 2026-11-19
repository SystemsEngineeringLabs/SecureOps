import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ControlEffectiveness, ControlMappingType, ControlStatus


class FrameworkResponse(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    organization: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class FrameworkVersionResponse(BaseModel):
    id: uuid.UUID
    framework_id: uuid.UUID
    version: str
    effective_date: date | None = None
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


class FrameworkDetailResponse(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    organization: str | None = None
    is_active: bool
    versions: list[FrameworkVersionResponse]
    control_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ControlResponse(BaseModel):
    id: uuid.UUID
    framework_version_id: uuid.UUID
    code: str
    title: str
    description: str | None = None
    category: str | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ControlMappingResponse(BaseModel):
    id: uuid.UUID
    source_control_id: uuid.UUID
    target_control_id: uuid.UUID
    mapping_type: ControlMappingType
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TenantControlStatusResponse(BaseModel):
    id: uuid.UUID
    control_id: uuid.UUID
    status: ControlStatus
    effectiveness: ControlEffectiveness | None = None
    owner_id: uuid.UUID | None = None
    notes: str | None = None
    last_assessed_at: datetime | None = None
    next_review_at: datetime | None = None
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TenantControlStatusUpdateRequest(BaseModel):
    status: ControlStatus
    effectiveness: ControlEffectiveness | None = None
    owner_id: uuid.UUID | None = None
    notes: str | None = None


class ControlDetailResponse(BaseModel):
    id: uuid.UUID
    framework_version_id: uuid.UUID
    code: str
    title: str
    description: str | None = None
    category: str | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int
    tenant_status: TenantControlStatusResponse | None = None
    mappings: list[ControlMappingResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ControlStatusSummary(BaseModel):
    total: int = 0
    not_started: int = 0
    in_progress: int = 0
    implemented: int = 0
    not_applicable: int = 0
    failed: int = 0
    compliance_percentage: float = 0.0


class GapAssessmentResponse(BaseModel):
    framework_version_id: uuid.UUID
    summary: ControlStatusSummary
    gaps: list[ControlDetailResponse]
