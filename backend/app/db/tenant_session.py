from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy import Select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_context import get_tenant
from app.db.base import async_session_factory


async def get_tenant_db() -> AsyncGenerator[AsyncSession]:
    tenant_id = get_tenant()

    async with async_session_factory() as session:
        try:
            await session.execute(
                text("SET LOCAL app.current_tenant_id = :tid"),
                {"tid": str(tenant_id)},
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def apply_tenant_filter[T](query: Select[T], model: type, tenant_id: UUID | None = None) -> Select[T]:
    tid = tenant_id if tenant_id is not None else get_tenant()
    return query.where(model.tenant_id == tid)  # type: ignore[attr-defined]
