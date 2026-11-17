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


# -----------------------------------------------------------------------------
# B2B Digital Lending Fraud Verification Schemas
# -----------------------------------------------------------------------------

class B2BIdentityVerifyRequest(BaseModel):
    document_type: str = Field(..., description="aadhaar, pan, driving_license, voter_id, passport")
    document_value: str = Field(..., min_length=5, max_length=100)
    declared_name: Optional[str] = Field(None, max_length=200)
    borrower_entity_type: Optional[str] = Field("individual", description="individual, company, trust, firm")
    loan_application_id: Optional[str] = Field(None, max_length=100)


class B2BIdentityVerifyDTO(BaseModel):
    document_type: str
    is_valid_syntax: bool
    is_checksum_valid: bool
    masked_identifier: str
    synthetic_fraud_risk: str  # low, medium, high, critical
    risk_score: int  # 0 to 100 (0=safe, 100=extreme risk)
    risk_factors: List[str]
    statutory_masking_compliant: bool
    recommendation: str  # approve, step_up_kyc, reject
    verified_at: datetime


class B2BDocTamperVerifyRequest(BaseModel):
    document_type: str = Field("aadhaar", description="aadhaar, pan, driving_license, salary_slip")
    ocr_extracted_text: str = Field(..., min_length=10, max_length=20000)
    declared_dob: Optional[str] = Field(None, max_length=20)
    has_photo: bool = Field(True)
    detected_watermark: Optional[str] = Field(None, max_length=200)


class B2BDocTamperVerifyDTO(BaseModel):
    tampering_detected: bool
    tamper_confidence: float
    detected_anomalies: List[str]
    uidai_masking_violation: bool
    reused_hotel_stamp_detected: bool
    verdict: str  # authentic, suspicious, tampered
    details: str
    verified_at: datetime


class B2BTelecomRiskRequest(BaseModel):
    mobile_number: str = Field(..., min_length=10, max_length=15)
    aadhaar_masked: Optional[str] = Field(None, max_length=30)
    borrower_city: Optional[str] = Field(None, max_length=100)


class B2BTelecomRiskDTO(BaseModel):
    mobile_number_masked: str
    sim_velocity_risk: str  # normal, high, critical
    sim_activation_age_days: int
    ghost_sim_cluster_detected: bool
    associated_sims_on_aadhaar: int
    unauthorized_sims_flagged: int
    risk_score: int  # 0 to 100
    telecom_fraud_warning: Optional[str] = None
    recommendation: str  # proceed, manual_verification_required, block_loan
    verified_at: datetime


class B2BBreachCanaryRequest(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    pan_masked: Optional[str] = Field(None, max_length=20)


class B2BBreachCanaryDTO(BaseModel):
    risk_level: str  # safe, moderate, severe, critical
    credentials_leaked: bool
    cleartext_password_dumped: bool
    session_tokens_compromised: bool
    known_breaches_matched: List[str]
    borrower_account_takeover_risk: str  # low, medium, high
    disbursement_recommendation: str  # safe_to_disburse, hold_for_step_up, decline
    checked_at: datetime


class B2BUsageDTO(BaseModel):
    api_key_prefix: str
    client_name: str
    tier: str
    rate_limit_rpm: int
    total_calls: int
    total_cost_inr: float
    endpoint_breakdown: Dict[str, int]
    billing_cycle: str


# -----------------------------------------------------------------------------
# Corporate Executive & Family Office Protection Schemas
# -----------------------------------------------------------------------------

class ExecutiveEnrollRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    corporate_email: str = Field(..., min_length=5, max_length=255)
    designation: str = Field("Chief Executive Officer", max_length=100)
    vip_tier: str = Field("c_suite", description="c_suite, board_member, promoter, family_member")
    personal_email: Optional[str] = Field(None, max_length=255)
    personal_phone: Optional[str] = Field(None, max_length=20)
    masked_aadhaar: Optional[str] = Field(None, max_length=30)
    pan: Optional[str] = Field(None, max_length=20)


class ExecutiveProfileDTO(BaseModel):
    id: str
    full_name: str
    corporate_email: str
    designation: str
    vip_tier: str
    risk_score: int
    monitoring_status: str
    assets_count: int
    active_incidents_count: int
    created_at: datetime


class ExecutiveThreatSimulateRequest(BaseModel):
    executive_id: str = Field(..., min_length=1)
    threat_type: str = Field("digital_arrest", description="spear_phishing, digital_arrest, sim_swap_attempt, darkweb_leak, unmasked_document_exposure")
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=3000)
    severity: str = Field("critical", description="critical, high, medium")


class ExecutiveThreatIncidentDTO(BaseModel):
    id: str
    executive_id: str
    executive_name: str
    threat_type: str
    severity: str
    title: str
    description: str
    indicators: Dict[str, Any]
    state: str
    detected_at: datetime


class ExecutiveDashboardDTO(BaseModel):
    company_name: str
    corporate_exposure_index: int  # 0 to 1000
    security_posture_tier: str  # fortress, strong, monitored, vulnerable
    total_executives_protected: int
    active_critical_threats: int
    assets_under_monitoring: int
    threat_category_breakdown: Dict[str, int]
    recent_threats: List[ExecutiveThreatIncidentDTO]
    audit_summary: str


class ExecutiveDispatchPackDTO(BaseModel):
    incident_id: str
    executive_name: str
    threat_type: str
    section63_bsa_affidavit: str
    ceir_handset_block_dossier: Dict[str, str]
    priority_1930_cybercrime_escalation: Dict[str, str]
    biometric_lock_pushed: bool
    corporate_legal_counsel_brief: str
    dispatched_at: datetime


# -----------------------------------------------------------------------------
# Market Research & Consumer Validation Schemas
# -----------------------------------------------------------------------------

class MarketValidationSurveyRequest(BaseModel):
    biometrics_locked_status: str = Field(..., description="'locked', 'unlocked', 'unaware'")
    shared_unmasked_photocopies: bool = Field(..., description="Whether user shared unmasked Aadhaar at hotels/rentals")
    received_scam_contacts: List[str] = Field(default_factory=list, description="List of scam categories encountered")
    tafcop_sim_awareness: str = Field(..., description="'checked_ok', 'never_checked', 'found_unknown'")
    most_valued_feature: str = Field(..., description="Top feature user desires")
    willingness_to_pay_model: str = Field(..., description="'free_via_bank', 'paid_monthly_49', 'paid_annual_199', 'free_only'")
    user_city: Optional[str] = Field(default="Metro", description="City tier or name")


class MarketValidationSummaryDTO(BaseModel):
    total_responses: int
    unlocked_biometrics_pct: float
    unmasked_photocopy_sharing_pct: float
    top_scam_categories: Dict[str, int]
    tafcop_unaware_pct: float
    feature_demand_distribution: Dict[str, int]
    willingness_to_pay_distribution: Dict[str, int]
    market_readiness_score: int  # 0 to 100
    investor_validation_summary: str


