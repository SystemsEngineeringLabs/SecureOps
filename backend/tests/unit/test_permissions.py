import pytest

from app.core.permissions import (
    _ALL_PERMISSIONS,
    ALL_ACTIONS,
    ALL_RESOURCES,
    ROLE_PERMISSIONS,
    Action,
    Resource,
)
from app.models.enums import MembershipRole

pytestmark = pytest.mark.unit


class TestRoleDefinitions:
    def test_all_five_roles_defined(self):
        for role in MembershipRole:
            assert role in ROLE_PERMISSIONS, f"{role} missing from ROLE_PERMISSIONS"

    def test_no_extra_roles(self):
        for role in ROLE_PERMISSIONS:
            assert role in MembershipRole, f"{role} not a valid MembershipRole"


class TestSuperAdmin:
    def test_super_admin_has_all_permissions(self):
        assert ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN] == _ALL_PERMISSIONS

    def test_super_admin_permission_count(self):
        expected = len(ALL_RESOURCES) * len(ALL_ACTIONS)
        assert len(ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN]) == expected


class TestOrgAdmin:
    def test_org_admin_has_admin_read(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ORG_ADMIN]
        assert (Resource.ADMIN, Action.READ) in perms

    def test_org_admin_has_admin_write(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ORG_ADMIN]
        assert (Resource.ADMIN, Action.WRITE) in perms

    def test_org_admin_has_admin_delete(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ORG_ADMIN]
        assert (Resource.ADMIN, Action.DELETE) in perms

    def test_org_admin_lacks_admin_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ORG_ADMIN]
        assert (Resource.ADMIN, Action.ADMIN) not in perms

    def test_org_admin_is_subset_of_super_admin(self):
        org_perms = ROLE_PERMISSIONS[MembershipRole.ORG_ADMIN]
        super_perms = ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN]
        assert org_perms.issubset(super_perms)


class TestSecurityManager:
    def test_can_read_and_write_compliance(self):
        perms = ROLE_PERMISSIONS[MembershipRole.SECURITY_MANAGER]
        assert (Resource.COMPLIANCE, Action.READ) in perms
        assert (Resource.COMPLIANCE, Action.WRITE) in perms

    def test_can_read_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.SECURITY_MANAGER]
        assert (Resource.ADMIN, Action.READ) in perms

    def test_cannot_write_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.SECURITY_MANAGER]
        assert (Resource.ADMIN, Action.WRITE) not in perms

    def test_can_read_audit(self):
        perms = ROLE_PERMISSIONS[MembershipRole.SECURITY_MANAGER]
        assert (Resource.AUDIT, Action.READ) in perms

    def test_is_subset_of_super_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.SECURITY_MANAGER]
        super_perms = ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN]
        assert perms.issubset(super_perms)


class TestEngineer:
    def test_can_read_compliance(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.COMPLIANCE, Action.READ) in perms

    def test_cannot_write_compliance(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.COMPLIANCE, Action.WRITE) not in perms

    def test_cannot_admin_compliance(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.COMPLIANCE, Action.ADMIN) not in perms

    def test_can_write_vulnerabilities(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.VULNERABILITIES, Action.WRITE) in perms

    def test_can_write_remediation(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.REMEDIATION, Action.WRITE) in perms

    def test_can_write_cloud_security(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        assert (Resource.CLOUD_SECURITY, Action.WRITE) in perms

    def test_cannot_delete_anything(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        delete_perms = {(r, a) for r, a in perms if a == Action.DELETE}
        assert len(delete_perms) == 0

    def test_is_subset_of_super_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.ENGINEER]
        super_perms = ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN]
        assert perms.issubset(super_perms)


class TestAuditor:
    def test_has_only_read_permissions(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        for resource, action in perms:
            assert action == Action.READ, f"Auditor has non-read: ({resource}, {action})"

    def test_cannot_write_anything(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        write_perms = {(r, a) for r, a in perms if a == Action.WRITE}
        assert len(write_perms) == 0

    def test_cannot_delete_anything(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        delete_perms = {(r, a) for r, a in perms if a == Action.DELETE}
        assert len(delete_perms) == 0

    def test_cannot_admin_anything(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        admin_perms = {(r, a) for r, a in perms if a == Action.ADMIN}
        assert len(admin_perms) == 0

    def test_can_read_compliance(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        assert (Resource.COMPLIANCE, Action.READ) in perms

    def test_can_read_evidence(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        assert (Resource.EVIDENCE, Action.READ) in perms

    def test_can_read_audit(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        assert (Resource.AUDIT, Action.READ) in perms

    def test_cannot_read_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        assert (Resource.ADMIN, Action.READ) not in perms

    def test_is_subset_of_super_admin(self):
        perms = ROLE_PERMISSIONS[MembershipRole.AUDITOR]
        super_perms = ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN]
        assert perms.issubset(super_perms)


class TestPermissionIntegrity:
    def test_all_permissions_use_defined_resources(self):
        for role, perms in ROLE_PERMISSIONS.items():
            for resource, _action in perms:
                assert resource in ALL_RESOURCES, f"{role}: unknown resource '{resource}'"

    def test_all_permissions_use_defined_actions(self):
        for role, perms in ROLE_PERMISSIONS.items():
            for _resource, action in perms:
                assert action in ALL_ACTIONS, f"{role}: unknown action '{action}'"

    def test_every_role_is_subset_of_super_admin(self):
        super_perms = ROLE_PERMISSIONS[MembershipRole.SUPER_ADMIN]
        for role, perms in ROLE_PERMISSIONS.items():
            assert perms.issubset(super_perms), f"{role} has permissions outside super_admin"
