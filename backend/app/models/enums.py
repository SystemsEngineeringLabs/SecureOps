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


# --- GRC enums ---


class ControlStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


class ControlEffectiveness(str, enum.Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class ControlMappingType(str, enum.Enum):
    EQUIVALENT = "equivalent"
    PARTIAL = "partial"
    RELATED = "related"


class RiskCategory(str, enum.Enum):
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"


class RiskLikelihood(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskImpact(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskTreatment(str, enum.Enum):
    ACCEPT = "accept"
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    AVOID = "avoid"


class RiskStatus(str, enum.Enum):
    OPEN = "open"
    MITIGATING = "mitigating"
    CLOSED = "closed"
    ACCEPTED = "accepted"


class EvidenceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EvidenceCollectionMethod(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"


class CollectionRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class VendorRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VendorStatus(str, enum.Enum):
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
