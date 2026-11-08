"""
Domain enums representing states and classifications defined in the PRD.
"""
from enum import Enum


class IdentifierType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    PAN = "pan"
    AADHAAR = "aadhaar"
    DOMAIN = "domain"


class IdentifierState(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    MONITORING_PENDING = "monitoring_pending"
    ACTIVE = "active"
    PAUSED = "paused"
    REVOKED = "revoked"
    DELETION_PENDING = "deletion_pending"
    DELETED = "deleted"
    VERIFICATION_EXPIRED = "verification_expired"
    VERIFICATION_LOCKED = "verification_locked"
    UNSUPPORTED = "unsupported"
    PROVIDER_INELIGIBLE = "provider_ineligible"


class IncidentState(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    ACTION_IN_PROGRESS = "action_in_progress"
    RESOLVED_BY_USER = "resolved_by_user"
    DISPUTED = "disputed"
    CONFIRMED = "confirmed"
    FALSE_MATCH = "false_match"
    REOPENED = "reopened"


class SeverityLevel(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCONFIRMED = "unconfirmed"


class ScanState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AUTHORIZATION_REVOKED = "authorization_revoked"


class ProviderOutcome(str, Enum):
    MATCHED = "matched"
    NO_MATCH = "no_match"
    NOT_CHECKED = "not_checked"
    UNSUPPORTED = "unsupported"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    AUTHORIZATION_REQUIRED = "authorization_required"
    CONTRACT_DISABLED = "contract_disabled"


class EntitlementState(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    RESTRICTED = "restricted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DeletionWorkflowState(str, Enum):
    REQUESTED = "requested"
    PROCESSING_DISABLED = "processing_disabled"
    BILLING_ADDRESSED = "billing_addressed"
    SESSIONS_REVOKED = "sessions_revoked"
    PROVIDER_CLEANUP_PENDING = "provider_cleanup_pending"
    ACTIVE_STORE_CLEANUP = "active_store_cleanup"
    EVIDENCE_CLEANUP = "evidence_cleanup"
    EXPORT_CLEANUP = "export_cleanup"
    COMPLETED_WITH_BACKUP_EXPIRY_NOTICE = "completed_with_backup_expiry_notice"


class UserRole(str, Enum):
    CONSUMER_OWNER = "consumer_owner"
    SUPPORT_SPECIALIST = "support_specialist"
    SECURITY_REVIEWER = "security_reviewer"
    OPERATIONS_ENGINEER = "operations_engineer"
    PRIVACY_OPERATOR = "privacy_operator"
    BILLING_OPERATOR = "billing_operator"
    SERVICE_PRINCIPAL = "service_principal"
