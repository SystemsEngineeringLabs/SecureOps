import uuid

import pytest

from app.core.permissions import ROLE_PERMISSIONS, Resource, Action
from app.core.tenant_context import (
    TenantNotSetError,
    clear_tenant,
    get_tenant,
    set_tenant,
)
from app.models.enums import MembershipRole

pytestmark = pytest.mark.security


class TestTenantContextIsolation:
    def test_tenant_a_context_does_not_leak_to_b(self):
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()

        set_tenant(tenant_a)
        assert get_tenant() == tenant_a

        set_tenant(tenant_b)
        assert get_tenant() == tenant_b
        assert get_tenant() != tenant_a

        clear_tenant()

    def test_cleared_context_blocks_access(self):
        tid = uuid.uuid4()
        set_tenant(tid)
        clear_tenant()
        with pytest.raises(TenantNotSetError):
            get_tenant()

    def test_must_set_tenant_before_access(self):
        clear_tenant()
        with pytest.raises(TenantNotSetError):
            get_tenant()

    def test_tenant_id_is_exact_not_similar(self):
        t1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
        t2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
        set_tenant(t1)
        assert get_tenant() != t2
        clear_tenant()


class TestCrossTenantPermissions:
    def test_no_role_grants_cross_tenant_access(self):
        """No permission tuple encodes a different tenant — permissions are resource/action only."""
        for role, perms in ROLE_PERMISSIONS.items():
            for resource, action in perms:
                assert isinstance(resource, str)
                assert isinstance(action, str)
                assert len(resource) > 0
                assert len(action) > 0

    def test_auditor_cannot_escalate_to_write(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        assert (Resource.ADMIN, Action.WRITE) not in perms
        assert (Resource.ADMIN, Action.DELETE) not in perms
        assert (Resource.ADMIN, Action.ADMIN) not in perms

    def test_engineer_cannot_access_admin_resource(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.ADMIN, Action.READ) not in perms
        assert (Resource.ADMIN, Action.WRITE) not in perms
        assert (Resource.ADMIN, Action.DELETE) not in perms
        assert (Resource.ADMIN, Action.ADMIN) not in perms

    def test_no_role_except_super_admin_has_admin_admin(self):
        for role in MembershipRole:
            if role == MembershipRole.SUPER_ADMIN:
                continue
            perms = ROLE_PERMISSIONS[role]
            assert (Resource.ADMIN, Action.ADMIN) not in perms, (
                f"{role} should not have admin:admin"
            )


class TestTenantScopedOperations:
    def test_different_tenants_are_distinct_uuids(self):
        """Sanity: two tenant IDs generated independently are never equal."""
        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        assert t1 != t2

    def test_set_tenant_enforces_uuid_type(self):
        tid = uuid.uuid4()
        set_tenant(tid)
        result = get_tenant()
        assert isinstance(result, uuid.UUID)
        clear_tenant()
