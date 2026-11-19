import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_model import Base, TenantScopedBase
from app.models.enums import PolicyStatus


class Policy(TenantScopedBase, Base):
    __tablename__ = "policies"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, name="policy_status", create_constraint=True),
        default=PolicyStatus.DRAFT,
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Policy {self.title[:40]} v{self.version}>"
