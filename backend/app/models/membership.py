import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_model import Base, TenantScopedBase
from app.models.enums import MembershipRole

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class Membership(TenantScopedBase, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, name="membership_role", create_constraint=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="memberships")  # noqa: F821
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="memberships", foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} tenant={self.tenant_id} role={self.role}>"
