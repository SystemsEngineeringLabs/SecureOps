import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_model import Base, TenantScopedBase
from app.models.enums import (
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
    RiskStatus,
    RiskTreatment,
)

LIKELIHOOD_SCORES: dict[RiskLikelihood, int] = {
    RiskLikelihood.VERY_LOW: 1,
    RiskLikelihood.LOW: 2,
    RiskLikelihood.MEDIUM: 3,
    RiskLikelihood.HIGH: 4,
    RiskLikelihood.VERY_HIGH: 5,
}

IMPACT_SCORES: dict[RiskImpact, int] = {
    RiskImpact.VERY_LOW: 1,
    RiskImpact.LOW: 2,
    RiskImpact.MEDIUM: 3,
    RiskImpact.HIGH: 4,
    RiskImpact.VERY_HIGH: 5,
}


def compute_risk_score(
    likelihood: RiskLikelihood | None, impact: RiskImpact | None
) -> float | None:
    if likelihood is None or impact is None:
        return None
    return float(LIKELIHOOD_SCORES[likelihood] * IMPACT_SCORES[impact])


class Risk(TenantScopedBase, Base):
    __tablename__ = "risks"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[RiskCategory] = mapped_column(
        Enum(RiskCategory, name="risk_category", create_constraint=True),
        nullable=False,
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    likelihood: Mapped[RiskLikelihood] = mapped_column(
        Enum(RiskLikelihood, name="risk_likelihood", create_constraint=True),
        nullable=False,
    )
    impact: Mapped[RiskImpact] = mapped_column(
        Enum(RiskImpact, name="risk_impact", create_constraint=True),
        nullable=False,
    )
    inherent_score: Mapped[float] = mapped_column(Float, nullable=False)

    treatment: Mapped[RiskTreatment | None] = mapped_column(
        Enum(RiskTreatment, name="risk_treatment", create_constraint=True),
        nullable=True,
    )
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)

    residual_likelihood: Mapped[RiskLikelihood | None] = mapped_column(
        Enum(RiskLikelihood, name="risk_residual_likelihood", create_constraint=False),
        nullable=True,
    )
    residual_impact: Mapped[RiskImpact | None] = mapped_column(
        Enum(RiskImpact, name="risk_residual_impact", create_constraint=False),
        nullable=True,
    )
    residual_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[RiskStatus] = mapped_column(
        Enum(RiskStatus, name="risk_status", create_constraint=True),
        default=RiskStatus.OPEN,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    related_control_ids: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)

    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Risk {self.title[:40]} score={self.inherent_score}>"
