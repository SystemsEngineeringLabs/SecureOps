from contextvars import ContextVar
from uuid import UUID

_current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)


class TenantNotSetError(Exception):
    pass


def set_tenant(tenant_id: UUID) -> None:
    _current_tenant_id.set(tenant_id)


def get_tenant() -> UUID:
    tenant_id = _current_tenant_id.get()
    if tenant_id is None:
        raise TenantNotSetError("Tenant context has not been set for this request")
    return tenant_id


def get_tenant_or_none() -> UUID | None:
    return _current_tenant_id.get()


def clear_tenant() -> None:
    _current_tenant_id.set(None)
