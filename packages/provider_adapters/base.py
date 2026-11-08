"""
Base interface and dataclasses for intelligence provider adapters.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProviderCapabilities:
    provider: str
    environment: str
    contract_status: str
    email_breach_lookup: bool
    email_darkweb_mentions: bool
    phone_lookup: bool = False
    domain_monitoring: bool = False
    pan_lookup: bool = False
    aadhaar_lookup: bool = False
    persistent_identifier_registration: bool = False
    provider_deletion: bool = False
    allow_raw_secrets: bool = False
    allow_full_documents: bool = False
    allow_redacted_excerpt: bool = True


@dataclass
class ProviderHealth:
    provider: str
    is_healthy: bool
    status_message: str
    latency_ms: float
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_seconds: Optional[int] = None


@dataclass
class AuthorizedIdentifier:
    id: str
    tenant_id: str
    subject_id: str
    type: str
    decrypted_value: str
    authorization_version: int


@dataclass
class ProviderRegistrationResult:
    provider: str
    provider_resource_id: str
    status: str


@dataclass
class ProviderPage:
    provider: str
    items: List[Dict[str, Any]]
    next_cursor: Optional[str] = None
    high_watermark: Optional[str] = None


@dataclass
class NormalizedObservation:
    schema_version: str = "1.0"
    observation_id: str = ""
    provider: str = ""
    provider_record_id: str = ""
    provider_connection_id: str = ""
    source_class: str = ""  # breach, stealer_log, paste, darkweb_mention
    source_name: str = ""
    identifier_reference: str = ""
    match_type: str = "exact_email"
    event_occurred_at: Optional[datetime] = None
    source_published_at: Optional[datetime] = None
    provider_first_seen_at: Optional[datetime] = None
    platform_ingested_at: Optional[datetime] = None
    exposure_categories: List[str] = field(default_factory=list)
    credential_material_present: bool = False
    credential_validity: str = "not_tested"
    redacted_excerpt: Optional[str] = None
    is_spam_list: bool = False
    is_unverified: bool = False
    is_fabricated: bool = False
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderDeletionReceipt:
    provider: str
    provider_resource_id: str
    confirmed: bool
    status: str


class IntelligenceProvider(ABC):
    @abstractmethod
    async def capabilities(self) -> ProviderCapabilities:
        pass

    @abstractmethod
    async def healthcheck(self) -> ProviderHealth:
        pass

    @abstractmethod
    async def register_identifier(self, identifier: AuthorizedIdentifier) -> ProviderRegistrationResult:
        pass

    @abstractmethod
    async def search(
        self,
        target: AuthorizedIdentifier,
        checkpoint: Optional[str] = None
    ) -> ProviderPage:
        pass

    @abstractmethod
    async def normalize(
        self,
        page: ProviderPage,
        identifier: AuthorizedIdentifier
    ) -> List[NormalizedObservation]:
        pass

    @abstractmethod
    async def unregister_identifier(
        self,
        registration_resource_id: str
    ) -> ProviderDeletionReceipt:
        pass
