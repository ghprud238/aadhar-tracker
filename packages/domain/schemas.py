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
