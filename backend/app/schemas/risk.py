import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
    RiskStatus,
    RiskTreatment,
)


class RiskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    category: RiskCategory
    likelihood: RiskLikelihood
    impact: RiskImpact
    treatment: RiskTreatment | None = None
    treatment_plan: str | None = None
    owner_id: uuid.UUID | None = None
    due_date: date | None = None
    related_control_ids: list[uuid.UUID] | None = None


class RiskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    category: RiskCategory | None = None
    likelihood: RiskLikelihood | None = None
    impact: RiskImpact | None = None
    treatment: RiskTreatment | None = None
    treatment_plan: str | None = None
    residual_likelihood: RiskLikelihood | None = None
    residual_impact: RiskImpact | None = None
    status: RiskStatus | None = None
    owner_id: uuid.UUID | None = None
    due_date: date | None = None
    related_control_ids: list[uuid.UUID] | None = None


class RiskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    category: RiskCategory
    source: str | None
    likelihood: RiskLikelihood
    impact: RiskImpact
    inherent_score: float
    treatment: RiskTreatment | None
    treatment_plan: str | None
    residual_likelihood: RiskLikelihood | None
    residual_impact: RiskImpact | None
    residual_score: float | None
    status: RiskStatus
    owner_id: uuid.UUID | None
    due_date: date | None
    related_control_ids: list[uuid.UUID] | None
    last_reviewed_at: datetime | None
    next_review_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskListResponse(BaseModel):
    items: list[RiskResponse]
    total: int
    limit: int
    offset: int


class RiskSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_risk_level: dict[str, int]
    average_inherent_score: float
    average_residual_score: float | None


class RiskHeatmapCell(BaseModel):
    likelihood: str
    impact: str
    count: int
    risk_ids: list[uuid.UUID]


class RiskHeatmapResponse(BaseModel):
    cells: list[RiskHeatmapCell]


RiskSortField = Literal[
    "inherent_score",
    "residual_score",
    "title",
    "category",
    "status",
    "likelihood",
    "impact",
    "due_date",
    "next_review_at",
    "created_at",
    "updated_at",
]
SortOrder = Literal["asc", "desc"]


class RiskQueryParams(BaseModel):
    category: RiskCategory | None = None
    status: RiskStatus | None = None
    likelihood: RiskLikelihood | None = None
    impact: RiskImpact | None = None
    owner_id: uuid.UUID | None = None
    min_score: float | None = None
    search: str | None = None
    sort_by: RiskSortField = "inherent_score"
    sort_order: SortOrder = "desc"
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
