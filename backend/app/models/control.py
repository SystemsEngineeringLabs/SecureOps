import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_model import Base, TenantScopedBase, TimestampMixin
from app.models.enums import ControlEffectiveness, ControlMappingType, ControlStatus

if TYPE_CHECKING:
    from app.models.framework import FrameworkVersion


class Control(TimestampMixin, Base):
    __tablename__ = "controls"
    __table_args__ = (
        UniqueConstraint("framework_version_id", "code", name="uq_control_framework_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    framework_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("controls.id", ondelete="SET NULL"),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    framework_version: Mapped["FrameworkVersion"] = relationship(  # noqa: F821
        back_populates="controls"
    )
    parent: Mapped["Control | None"] = relationship(remote_side="Control.id", backref="children")
    source_mappings: Mapped[list["ControlMapping"]] = relationship(
        foreign_keys="ControlMapping.source_control_id",
        back_populates="source_control",
        cascade="all, delete-orphan",
    )
    target_mappings: Mapped[list["ControlMapping"]] = relationship(
        foreign_keys="ControlMapping.target_control_id",
        back_populates="target_control",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Control {self.code}>"


class ControlMapping(Base):
    __tablename__ = "control_mappings"
    __table_args__ = (
        UniqueConstraint(
            "source_control_id",
            "target_control_id",
            name="uq_control_mapping_src_tgt",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mapping_type: Mapped[ControlMappingType] = mapped_column(
        Enum(ControlMappingType, name="control_mapping_type", create_constraint=True),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source_control: Mapped["Control"] = relationship(
        foreign_keys=[source_control_id], back_populates="source_mappings"
    )
    target_control: Mapped["Control"] = relationship(
        foreign_keys=[target_control_id], back_populates="target_mappings"
    )

    def __repr__(self) -> str:
        return f"<ControlMapping {self.source_control_id} -> {self.target_control_id}>"


class TenantControlStatus(TenantScopedBase, Base):
    __tablename__ = "tenant_control_statuses"
    __table_args__ = (UniqueConstraint("tenant_id", "control_id", name="uq_tenant_control_status"),)

    control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ControlStatus] = mapped_column(
        Enum(ControlStatus, name="control_status", create_constraint=True),
        default=ControlStatus.NOT_STARTED,
        nullable=False,
    )
    effectiveness: Mapped[ControlEffectiveness | None] = mapped_column(
        Enum(ControlEffectiveness, name="control_effectiveness", create_constraint=True),
        nullable=True,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    control: Mapped["Control"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<TenantControlStatus tenant={self.tenant_id} "
            f"control={self.control_id} status={self.status}>"
        )
