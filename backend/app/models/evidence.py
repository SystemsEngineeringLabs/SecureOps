import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_model import Base, TenantScopedBase
from app.models.enums import CollectionRunStatus, EvidenceCollectionMethod, EvidenceStatus


class Evidence(TenantScopedBase, Base):
    __tablename__ = "evidence"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus, name="evidence_status", create_constraint=True),
        default=EvidenceStatus.PENDING,
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    collection_method: Mapped[EvidenceCollectionMethod] = mapped_column(
        Enum(
            EvidenceCollectionMethod,
            name="evidence_collection_method",
            create_constraint=True,
        ),
        default=EvidenceCollectionMethod.MANUAL,
        nullable=False,
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    previous_version: Mapped["Evidence | None"] = relationship(remote_side="Evidence.id")
    control_links: Mapped[list["ControlEvidence"]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Evidence {self.title[:40]} v{self.version}>"


class ControlEvidence(TenantScopedBase, Base):
    __tablename__ = "control_evidence"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "control_id",
            "evidence_id",
            name="uq_control_evidence",
        ),
    )

    control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence: Mapped["Evidence"] = relationship(back_populates="control_links")

    def __repr__(self) -> str:
        return f"<ControlEvidence control={self.control_id} evidence={self.evidence_id}>"


class EvidenceCollectionRun(TenantScopedBase, Base):
    __tablename__ = "evidence_collection_runs"

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[CollectionRunStatus] = mapped_column(
        Enum(
            CollectionRunStatus,
            name="collection_run_status",
            create_constraint=True,
        ),
        default=CollectionRunStatus.PENDING,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<EvidenceCollectionRun {self.source} status={self.status}>"
