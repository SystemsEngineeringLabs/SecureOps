import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EvidenceCollectionMethod, EvidenceStatus


class EvidenceUploadRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    control_ids: list[uuid.UUID] | None = None
    tags: list[str] | None = None


class EvidenceUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    tags: list[str] | None = None


class EvidenceApproveRequest(BaseModel):
    approved: bool
    notes: str | None = None


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    file_name: str
    file_size: int
    content_type: str
    sha256_hash: str
    version: int
    status: EvidenceStatus
    uploaded_by: uuid.UUID
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    expires_at: datetime | None
    collection_method: EvidenceCollectionMethod
    source: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    limit: int
    offset: int


class EvidenceSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    pending_approval: int
    expiring_soon: int
    total_size_bytes: int


class ControlEvidenceResponse(BaseModel):
    control_id: uuid.UUID
    control_code: str
    control_title: str
    evidence_count: int


class EvidenceQueryParams(BaseModel):
    status: EvidenceStatus | None = None
    search: str | None = None
    control_id: uuid.UUID | None = None
    uploaded_by: uuid.UUID | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
