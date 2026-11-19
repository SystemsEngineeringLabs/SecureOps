import asyncio
import uuid

import pytest

from app.core.tenant_context import (
    TenantNotSetError,
    clear_tenant,
    get_tenant,
    get_tenant_or_none,
    set_tenant,
)

pytestmark = pytest.mark.unit


class TestSetAndGetTenant:
    def test_set_and_get_tenant(self):
        tid = uuid.uuid4()
        set_tenant(tid)
        assert get_tenant() == tid
        clear_tenant()

    def test_get_tenant_returns_exact_uuid(self):
        tid = uuid.uuid4()
        set_tenant(tid)
        result = get_tenant()
        assert result is tid
        clear_tenant()

    def test_overwrite_tenant(self):
        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        set_tenant(t1)
        set_tenant(t2)
        assert get_tenant() == t2
        clear_tenant()


class TestGetTenantRaises:
    def test_get_tenant_raises_when_not_set(self):
        clear_tenant()
        with pytest.raises(TenantNotSetError):
            get_tenant()

    def test_get_tenant_or_none_returns_none(self):
        clear_tenant()
        assert get_tenant_or_none() is None


class TestClearTenant:
    def test_clear_tenant_removes_context(self):
        tid = uuid.uuid4()
        set_tenant(tid)
        clear_tenant()
        with pytest.raises(TenantNotSetError):
            get_tenant()

    def test_clear_tenant_idempotent(self):
        clear_tenant()
        clear_tenant()
        assert get_tenant_or_none() is None


class TestContextIsolation:
    def test_contextvars_isolated_across_tasks(self):
        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        results = {}

        async def task_a():
            set_tenant(t1)
            await asyncio.sleep(0.01)
            results["a"] = get_tenant()
            clear_tenant()

        async def task_b():
            set_tenant(t2)
            await asyncio.sleep(0.01)
            results["b"] = get_tenant()
            clear_tenant()

        async def run():
            await asyncio.gather(task_a(), task_b())

        asyncio.run(run())
        assert results["a"] == t1
        assert results["b"] == t2
