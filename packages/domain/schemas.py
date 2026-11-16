"""
Pydantic schemas adhering strictly to the PRD envelope format and error contracts.
"""
from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str


class PaginationInfo(BaseModel):
    next_cursor: Optional[str] = None
    has_more: bool = False


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


class ApiListResponse(BaseModel, Generic[T]):
    data: List[T]
    page: PaginationInfo
    meta: ResponseMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False
    field_errors: List[Dict[str, str]] = Field(default_factory=list)


class ApiErrorResponse(BaseModel):
    error: ErrorDetail
    meta: ResponseMeta


# -----------------------------------------------------------------------------
# DTOs
# -----------------------------------------------------------------------------

class UserProfileDTO(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    account_state: str


class WorkspaceDTO(BaseModel):
    id: str
    name: str
    tenant_type: str
    region_policy: str
    account_state: str


class ProcessingNoticeDTO(BaseModel):
    id: str
    version: str
    purpose: str
    title: str
    content_html: str
    published_at: datetime


class ConsentGrantRequest(BaseModel):
    purpose: str = "identity_exposure_monitoring"
    notice_version: str = "1.0"
    provider_categories: List[str] = Field(default_factory=lambda: ["breach_intelligence"])
    subject_id: str


class ConsentGrantDTO(BaseModel):
    id: str
    subject_id: str
    purpose: str
    provider_categories: List[str]
    notice_version: str
    status: str
    created_at: datetime


class IdentifierCreateRequest(BaseModel):
    type: str = "email"
    value: str
    label: Optional[str] = "Personal email"


class IdentifierDTO(BaseModel):
    id: str
    type: str
    masked_value: str
    state: str
    monitoring_enabled: bool


class VerificationCompleteRequest(BaseModel):
    identifier_id: str
    challenge_token: str


class ScanSubmitRequest(BaseModel):
    identifier_ids: List[str]
    reason: str = "user_requested"


class ScanSourceStatus(BaseModel):
    provider: str
    state: str


class ScanSubmitDTO(BaseModel):
    id: str
    state: str
    sources: List[ScanSourceStatus]


class IncidentIdentifierInfo(BaseModel):
    id: str
    masked_value: str


class IncidentDTO(BaseModel):
    id: str
    title: str
    severity: str
    confidence: str
    state: str
    identifier: IncidentIdentifierInfo
    exposure_categories: List[str]
    credential_validity: str = "not_tested"
    event_occurred_at: Optional[datetime] = None
    first_detected_at: datetime
    priority_score: int
    rules_version: str = "1.0"
    recommended_actions: List[str] = Field(default_factory=list)


class RemediationActionDTO(BaseModel):
    id: str
    action_type: str
    title: str
    description: str
    state: str
    completed_at: Optional[datetime] = None
    completion_provenance: Optional[str] = None


class CoverageItemDTO(BaseModel):
    source: str
    capability: str
    last_successful_check: Optional[datetime]
    current_state: str
    known_limitation: str
    next_expected_check: Optional[datetime]


class AssistanceGuideDTO(BaseModel):
    id: str
    topic: str
    official_authority: str
    portal_url: str
    steps: List[str]
    protective_action: str


class AssistanceReportRequest(BaseModel):
    category: str
    description: str
    reported_action_taken: Optional[str] = None


class AssistanceReportDTO(BaseModel):
    id: str
    category: str
    description_redacted: str
    reported_action_taken: Optional[str]
    provenance: str = "user_reported"
    created_at: datetime


# -----------------------------------------------------------------------------
# High-Appeal Citizen Defense Schemas
# -----------------------------------------------------------------------------

class ScamAnalysisRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=10000, description="SMS text, WhatsApp forward, or transcript of suspicious call")
    sender_header: Optional[str] = Field(None, max_length=100, description="Sender ID (e.g. VM-BESCOM, VK-CHLLAN, +91...)")
    channel: Optional[str] = Field("sms", max_length=30, description="sms, whatsapp, video_call, or phone")
    suspect_claims: Optional[str] = Field(None, max_length=2000, description="Specific claims like digital arrest, parcel held, etc.")


class ScamAnalysisDTO(BaseModel):
    is_scam: bool
    threat_level: str  # critical, high, medium, safe
    scam_category: str  # digital_arrest_impersonation, malicious_apk_sideload, electricity_bill_urgency, traffic_challan_fraud, legitimate_notice
    matched_indicators: List[str]
    mha_official_advisory: str
    statutory_clauses: List[str]
    prefilled_fir_draft: str
    confidence_score: float


class EphemeralPassCreateRequest(BaseModel):
    document_type: str = Field("aadhaar", max_length=50)
    masked_identifier: str = Field("XXXX-XXXX-4819", max_length=50)
    recipient_entity: str = Field("Hotel Check-In", min_length=1, max_length=200)
    purpose: str = Field("hotel_checkin", min_length=1, max_length=100)
    ttl_seconds: int = Field(86400, ge=60, le=604800, description="TTL in seconds (1 min to 7 days)")
    single_burn: bool = True  # Self-destruct after first viewing
    encrypted_payload: str = Field(..., min_length=1, max_length=100000, description="Encrypted pass JSON ciphertext or armored string")


class EphemeralPassDTO(BaseModel):
    token: str
    share_url: str
    expires_at: datetime
    single_burn: bool
    views_remaining: int
    created_at: datetime


class EphemeralPassReadDTO(BaseModel):
    token: str
    document_type: str
    recipient_entity: str
    purpose: str
    encrypted_payload: str
    burned: bool
    expires_at: datetime


class WalletPassRequest(BaseModel):
    pass_id: str = Field(..., min_length=1, max_length=100)
    holder_name: str = Field("Aarav Sharma", min_length=1, max_length=200)
    document_type: str = Field("aadhaar", max_length=50)
    masked_identifier: str = Field("XXXX-XXXX-4819", max_length=50)
    recipient_entity: str = Field("Hotel Check-In", min_length=1, max_length=200)
    purpose: str = Field("hotel_checkin", min_length=1, max_length=100)
    valid_until: str = Field("2026-12-31", max_length=50)
    signer_public_key: str = Field(..., min_length=1, max_length=256)
    signature_hex: str = Field(..., min_length=1, max_length=512)
    platform: str = Field("both", max_length=20)  # apple, google, both


class WalletPassDTO(BaseModel):
    apple_pass_json: Dict[str, Any]
    google_wallet_jwt_payload: Dict[str, Any]
    barcode_payload: str
    mime_type: str = "application/json"


class PanicPackRequest(BaseModel):
    victim_name: str = Field("Aarav Sharma", min_length=1, max_length=200)
    lost_device_model: Optional[str] = Field("iPhone 15 Pro / Android Device", max_length=150)
    lost_imei_masked: Optional[str] = Field("3569********102", max_length=50)
    compromised_docs: List[str] = Field(default_factory=lambda: ["aadhaar", "pan", "driving_license"])
    incident_location: Optional[str] = Field("Mumbai, Maharashtra", max_length=250)
    incident_description: Optional[str] = Field("Lost wallet containing physical identity cards and companion phone.", max_length=2000)


class PanicPackExecutionDTO(BaseModel):
    pack_id: str
    biometric_lock_dispatched: bool
    ceir_block_instructions: Dict[str, str]
    credit_bureau_fraud_advisory: Dict[str, str]
    section63_ncr_affidavit: str
    emergency_helpline_numbers: Dict[str, str]
    executed_at: datetime


class PassVerificationRequest(BaseModel):
    raw_qr_payload: str = Field(..., min_length=1, max_length=50000)
    verifier_entity: Optional[str] = Field("Hotel Reception Desk", max_length=200)


class PassVerificationDTO(BaseModel):
    verified: bool
    pass_type: str
    holder_name: Optional[str] = None
    masked_identifier: Optional[str] = None
    recipient_entity: Optional[str] = None
    purpose: Optional[str] = None
    valid_until: Optional[str] = None
    security_audit: str
    algorithm_used: str
    verified_at: datetime
