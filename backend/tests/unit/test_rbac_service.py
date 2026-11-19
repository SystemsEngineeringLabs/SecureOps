import pytest

from app.core.permissions import Action, Resource, ROLE_PERMISSIONS
from app.models.enums import MembershipRole
from app.services.rbac_service import check_permission, get_role_permissions

pytestmark = pytest.mark.unit


class TestCheckPermission:
    def test_super_admin_can_do_anything(self):
        assert check_permission(MembershipRole.SUPER_ADMIN, Resource.ADMIN, Action.ADMIN) is True
        assert check_permission(MembershipRole.SUPER_ADMIN, Resource.COMPLIANCE, Action.DELETE) is True

    def test_org_admin_can_read_compliance(self):
        assert check_permission(MembershipRole.ORG_ADMIN, Resource.COMPLIANCE, Action.READ) is True

    def test_org_admin_cannot_admin_admin(self):
        assert check_permission(MembershipRole.ORG_ADMIN, Resource.ADMIN, Action.ADMIN) is False

    def test_engineer_can_write_vulnerabilities(self):
        assert check_permission(MembershipRole.ENGINEER, Resource.VULNERABILITIES, Action.WRITE) is True

    def test_engineer_cannot_write_compliance(self):
        assert check_permission(MembershipRole.ENGINEER, Resource.COMPLIANCE, Action.WRITE) is False

    def test_engineer_cannot_delete_vulnerabilities(self):
        assert check_permission(MembershipRole.ENGINEER, Resource.VULNERABILITIES, Action.DELETE) is False

    def test_auditor_can_read_compliance(self):
        assert check_permission(MembershipRole.AUDITOR, Resource.COMPLIANCE, Action.READ) is True

    def test_auditor_cannot_write_compliance(self):
        assert check_permission(MembershipRole.AUDITOR, Resource.COMPLIANCE, Action.WRITE) is False

    def test_auditor_cannot_delete_evidence(self):
        assert check_permission(MembershipRole.AUDITOR, Resource.EVIDENCE, Action.DELETE) is False

    def test_auditor_cannot_admin_anything(self):
        for resource in [Resource.COMPLIANCE, Resource.RISKS, Resource.EVIDENCE, Resource.ADMIN]:
            assert check_permission(MembershipRole.AUDITOR, resource, Action.ADMIN) is False

    def test_security_manager_can_write_risks(self):
        assert check_permission(MembershipRole.SECURITY_MANAGER, Resource.RISKS, Action.WRITE) is True

    def test_security_manager_can_read_audit(self):
        assert check_permission(MembershipRole.SECURITY_MANAGER, Resource.AUDIT, Action.READ) is True

    def test_invalid_resource_returns_false(self):
        assert check_permission(MembershipRole.SUPER_ADMIN, "nonexistent", Action.READ) is False

    def test_invalid_action_returns_false(self):
        assert check_permission(MembershipRole.SUPER_ADMIN, Resource.COMPLIANCE, "nonexistent") is False


class TestGetRolePermissions:
    def test_returns_sorted_list(self):
        perms = get_role_permissions(MembershipRole.AUDITOR)
        assert isinstance(perms, list)
        assert perms == sorted(perms)

    def test_super_admin_has_most_permissions(self):
        super_count = len(get_role_permissions(MembershipRole.SUPER_ADMIN))
        for role in MembershipRole:
            assert len(get_role_permissions(role)) <= super_count

    def test_each_role_returns_correct_count(self):
        for role in MembershipRole:
            perms = get_role_permissions(role)
            assert len(perms) == len(ROLE_PERMISSIONS[role])

    def test_auditor_permissions_all_read(self):
        perms = get_role_permissions(MembershipRole.AUDITOR)
        for resource, action in perms:
            assert action == Action.READ
