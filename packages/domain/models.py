"""
SQLAlchemy ORM models implementing the complete core entities specified in the PRD (Page 30-31).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Text, ForeignKey,
    UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------
# Core Tenant & Subject Hierarchy
# -----------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    idp_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_state: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    owner_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="Personal Workspace")
    tenant_type: Mapped[str] = mapped_column(String(50), default="personal")
    region_policy: Mapped[str] = mapped_column(String(50), default="IN")
    account_state: Mapped[str] = mapped_column(String(50), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(50), default="consumer_owner")
    state: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    owner_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    monitoring_state: Mapped[str] = mapped_column(String(50), default="active")
    authorization_version: Mapped[int] = mapped_column(Integer, default=1)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# -----------------------------------------------------------------------------
# Identifiers & Verification
# -----------------------------------------------------------------------------

class Identifier(Base):
    __tablename__ = "identifiers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    type: Mapped[str] = mapped_column(String(50), default="email")
    encrypted_value: Mapped[str] = mapped_column(Text)
    blind_index: Mapped[str] = mapped_column(String(64), index=True)
    masked_value: Mapped[str] = mapped_column(String(255))
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(50), default="pending_verification")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "subject_id", "blind_index", name="uq_identifier_tenant_subject_blind"),
    )


class IdentifierVerification(Base):
    __tablename__ = "identifier_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    identifier_id: Mapped[str] = mapped_column(String(36), ForeignKey("identifiers.id"), index=True)
    challenge_digest: Mapped[str] = mapped_column(String(64), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# -----------------------------------------------------------------------------
# Consent & Legal Processing Notices
# -----------------------------------------------------------------------------

class ProcessingNotice(Base):
    __tablename__ = "processing_notices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    version: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    content_html: Mapped[str] = mapped_column(Text)
    publication_state: Mapped[str] = mapped_column(String(50), default="published")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConsentGrant(Base):
    __tablename__ = "consent_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(100), default="identity_exposure_monitoring")
    provider_categories: Mapped[list] = mapped_column(JSON, default=list)
    notice_version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="granted")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentEvent(Base):
    __tablename__ = "consent_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # grant, withdraw
    purpose: Mapped[str] = mapped_column(String(100))
    notice_version: Mapped[str] = mapped_column(String(50))
    effective_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# -----------------------------------------------------------------------------
# Provider Connections, Registrations & Checkpoints
# -----------------------------------------------------------------------------

class ProviderConnection(Base):
    __tablename__ = "provider_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    provider_name: Mapped[str] = mapped_column(String(100), index=True)
    account_reference: Mapped[str] = mapped_column(String(255))
    capability_state: Mapped[str] = mapped_column(String(50), default="active")
    capabilities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    health_status: Mapped[str] = mapped_column(String(50), default="healthy")
    last_health_check_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProviderRegistration(Base):
    __tablename__ = "provider_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    provider_connection_id: Mapped[str] = mapped_column(String(36), ForeignKey("provider_connections.id"), index=True)
    identifier_id: Mapped[str] = mapped_column(String(36), ForeignKey("identifiers.id"), index=True)
    provider_resource_id: Mapped[str] = mapped_column(String(255))
    lifecycle_state: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("provider_connection_id", "identifier_id", name="uq_reg_connection_identifier"),
    )


class MonitoringJob(Base):
    __tablename__ = "monitoring_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    identifier_id: Mapped[str] = mapped_column(String(36), ForeignKey("identifiers.id"), index=True)
    provider_name: Mapped[str] = mapped_column(String(100))
    authorization_version: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(50), default="queued")
    outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    lease_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# -----------------------------------------------------------------------------
# Observations, Findings & Incidents
# -----------------------------------------------------------------------------

class SourceObservation(Base):
    __tablename__ = "source_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    provider_connection_id: Mapped[str] = mapped_column(String(36), ForeignKey("provider_connections.id"), index=True)
    provider_record_id: Mapped[str] = mapped_column(String(255), index=True)
    source_class: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(255))
    event_occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    platform_ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    exposure_categories: Mapped[list] = mapped_column(JSON, default=list)
    credential_material_present: Mapped[bool] = mapped_column(Boolean, default=False)
    redacted_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("provider_connection_id", "provider_record_id", name="uq_obs_conn_record"),
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    identifier_id: Mapped[str] = mapped_column(String(36), ForeignKey("identifiers.id"), index=True)
    exposure_category: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[str] = mapped_column(String(50), default="high")
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    state: Mapped[str] = mapped_column(String(50), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FindingObservation(Base):
    __tablename__ = "finding_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    finding_id: Mapped[str] = mapped_column(String(36), ForeignKey("findings.id"), index=True)
    observation_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_observations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("finding_id", "observation_id", name="uq_finding_observation"),
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    incident_grouping_key: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    confidence: Mapped[str] = mapped_column(String(50), default="high")
    state: Mapped[str] = mapped_column(String(50), default="new")
    identifier_id: Mapped[str] = mapped_column(String(36), ForeignKey("identifiers.id"), index=True)
    exposure_categories: Mapped[list] = mapped_column(JSON, default=list)
    priority_score: Mapped[int] = mapped_column(Integer, default=50)
    rules_version: Mapped[str] = mapped_column(String(50), default="1.0")
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    event_occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "subject_id", "incident_grouping_key", name="uq_incident_tenant_subject_key"),
    )


class IncidentFinding(Base):
    __tablename__ = "incident_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), index=True)
    finding_id: Mapped[str] = mapped_column(String(36), ForeignKey("findings.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("incident_id", "finding_id", name="uq_incident_finding"),
    )


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(100))  # change_affected_password, review_reuse, enable_mfa, biometric_lock
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(50), default="pending")  # pending, completed
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_provenance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # user_reported
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# -----------------------------------------------------------------------------
# Outbox & Idempotency
# -----------------------------------------------------------------------------

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    schema_version: Mapped[str] = mapped_column(String(50), default="1.0")
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), index=True)
    resource_id: Mapped[str] = mapped_column(String(36), index=True)
    authorization_version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    state: Mapped[str] = mapped_column(String(50), default="pending")  # pending, published, failed, dead_letter
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dead_lettered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    consumer_name: Mapped[str] = mapped_column(String(100), index=True)
    event_id: Mapped[str] = mapped_column(String(36), index=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("consumer_name", "event_id", name="uq_processed_consumer_event"),
    )


# -----------------------------------------------------------------------------
# Notifications & Preferences
# -----------------------------------------------------------------------------

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    destination: Mapped[str] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    immediate_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    immediate_high: Mapped[bool] = mapped_column(Boolean, default=True)
    digest_low: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    notification_intent_id: Mapped[str] = mapped_column(String(36), index=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    destination_reference: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    body_sanitized: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="sent")
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("notification_intent_id", "channel", "destination_reference", name="uq_notif_intent_dest"),
    )


# -----------------------------------------------------------------------------
# Billing & Entitlements (Razorpay)
# -----------------------------------------------------------------------------

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    provider_reference: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String(100), default="plan_basic")
    state: Mapped[str] = mapped_column(String(50), default="active")  # active, cancelled, expired
    paid_through_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Entitlement(Base):
    __tablename__ = "entitlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    feature: Mapped[str] = mapped_column(String(100))  # email_breach, darkweb_monitoring, pan_assistance
    quota_limit: Mapped[int] = mapped_column(Integer, default=5)
    effective_state: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WebhookReceipt(Base):
    __tablename__ = "webhook_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    provider_name: Mapped[str] = mapped_column(String(50), index=True)
    provider_event_id: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_state: Mapped[str] = mapped_column(String(50), default="received")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("provider_name", "provider_event_id", name="uq_webhook_provider_event"),
    )


# -----------------------------------------------------------------------------
# Privacy, Audit & Identity Assistance
# -----------------------------------------------------------------------------

class PrivacyRequest(Base):
    __tablename__ = "privacy_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    request_type: Mapped[str] = mapped_column(String(50))  # export, deletion, grievance
    state: Mapped[str] = mapped_column(String(50), default="requested")
    download_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    download_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    actor_id: Mapped[str] = mapped_column(String(255), index=True)
    actor_role: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100), index=True)
    scoped_resource: Mapped[str] = mapped_column(String(255))
    result: Mapped[str] = mapped_column(String(50), default="success")  # success, failure, denied
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserAssistanceReport(Base):
    __tablename__ = "user_assistance_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))  # aadhaar_biometric_misuse, pan_financial_fraud, etc.
    description_redacted: Mapped[str] = mapped_column(Text)
    reported_action_taken: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provenance: Mapped[str] = mapped_column(String(50), default="user_reported")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
