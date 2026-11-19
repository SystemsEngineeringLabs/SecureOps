import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_model import Base, TimestampMixin


class Framework(TimestampMixin, Base):
    __tablename__ = "frameworks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    versions: Mapped[list["FrameworkVersion"]] = relationship(
        back_populates="framework", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Framework {self.key}>"


class FrameworkVersion(TimestampMixin, Base):
    __tablename__ = "framework_versions"
    __table_args__ = (
        UniqueConstraint("framework_id", "version", name="uq_framework_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    framework: Mapped["Framework"] = relationship(back_populates="versions")
    controls: Mapped[list["Control"]] = relationship(  # noqa: F821
        back_populates="framework_version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FrameworkVersion {self.framework_id} v{self.version}>"
