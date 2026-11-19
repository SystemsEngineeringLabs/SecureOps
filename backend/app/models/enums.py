import enum


class MembershipRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    SECURITY_MANAGER = "security_manager"
    ENGINEER = "engineer"
    AUDITOR = "auditor"


class AuditAction(str, enum.Enum):
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    MEMBERSHIP_CREATE = "membership.create"
    MEMBERSHIP_UPDATE = "membership.update"
    PERMISSION_CHANGE = "permission.change"
    EVIDENCE_UPLOAD = "evidence.upload"
    EVIDENCE_ACCESS = "evidence.access"
    CONTROL_UPDATE = "control.update"
    RISK_UPDATE = "risk.update"
    INTEGRATION_CREATE = "integration.create"
    INTEGRATION_DELETE = "integration.delete"
    ADMIN_ACTION = "admin.action"
