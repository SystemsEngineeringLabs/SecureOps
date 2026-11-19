from app.models.enums import MembershipRole


class Resource:
    COMPLIANCE = "compliance"
    RISKS = "risks"
    EVIDENCE = "evidence"
    CLOUD_SECURITY = "cloud_security"
    VULNERABILITIES = "vulnerabilities"
    REMEDIATION = "remediation"
    POLICIES = "policies"
    VENDORS = "vendors"
    INTEGRATIONS = "integrations"
    REPORTS = "reports"
    ADMIN = "admin"
    AUDIT = "audit"


class Action:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


ALL_RESOURCES = [
    Resource.COMPLIANCE,
    Resource.RISKS,
    Resource.EVIDENCE,
    Resource.CLOUD_SECURITY,
    Resource.VULNERABILITIES,
    Resource.REMEDIATION,
    Resource.POLICIES,
    Resource.VENDORS,
    Resource.INTEGRATIONS,
    Resource.REPORTS,
    Resource.ADMIN,
    Resource.AUDIT,
]

ALL_ACTIONS = [Action.READ, Action.WRITE, Action.DELETE, Action.ADMIN]

_ALL_PERMISSIONS: set[tuple[str, str]] = {
    (r, a) for r in ALL_RESOURCES for a in ALL_ACTIONS
}

_SECURITY_DOMAINS = {
    Resource.COMPLIANCE,
    Resource.RISKS,
    Resource.EVIDENCE,
    Resource.CLOUD_SECURITY,
    Resource.VULNERABILITIES,
    Resource.REMEDIATION,
    Resource.POLICIES,
    Resource.VENDORS,
}

_ENGINEER_WRITE_DOMAINS = {
    Resource.CLOUD_SECURITY,
    Resource.VULNERABILITIES,
    Resource.REMEDIATION,
}

_AUDITOR_READ_DOMAINS = {
    Resource.COMPLIANCE,
    Resource.RISKS,
    Resource.EVIDENCE,
    Resource.CLOUD_SECURITY,
    Resource.VULNERABILITIES,
    Resource.REMEDIATION,
    Resource.POLICIES,
    Resource.VENDORS,
    Resource.REPORTS,
    Resource.AUDIT,
}

ROLE_PERMISSIONS: dict[MembershipRole, set[tuple[str, str]]] = {
    MembershipRole.SUPER_ADMIN: _ALL_PERMISSIONS,
    MembershipRole.ORG_ADMIN: {
        (r, a)
        for r in ALL_RESOURCES
        for a in ALL_ACTIONS
        if not (r == Resource.ADMIN and a == Action.ADMIN)
    }
    | {(Resource.ADMIN, Action.READ), (Resource.ADMIN, Action.WRITE), (Resource.ADMIN, Action.DELETE)},
    MembershipRole.SECURITY_MANAGER: (
        {(r, a) for r in _SECURITY_DOMAINS for a in [Action.READ, Action.WRITE, Action.DELETE]}
        | {(Resource.INTEGRATIONS, Action.READ), (Resource.INTEGRATIONS, Action.WRITE)}
        | {(Resource.REPORTS, Action.READ), (Resource.REPORTS, Action.WRITE)}
        | {(Resource.ADMIN, Action.READ)}
        | {(Resource.AUDIT, Action.READ)}
    ),
    MembershipRole.ENGINEER: (
        {(r, Action.READ) for r in [Resource.COMPLIANCE, Resource.RISKS, Resource.EVIDENCE, Resource.POLICIES, Resource.REPORTS]}
        | {(r, a) for r in _ENGINEER_WRITE_DOMAINS for a in [Action.READ, Action.WRITE]}
        | {(Resource.INTEGRATIONS, Action.READ)}
    ),
    MembershipRole.AUDITOR: {(r, Action.READ) for r in _AUDITOR_READ_DOMAINS},
}

ROLE_DISPLAY_NAMES: dict[MembershipRole, str] = {
    MembershipRole.SUPER_ADMIN: "Super Administrator",
    MembershipRole.ORG_ADMIN: "Organization Administrator",
    MembershipRole.SECURITY_MANAGER: "Security Manager",
    MembershipRole.ENGINEER: "Engineer",
    MembershipRole.AUDITOR: "Auditor",
}
