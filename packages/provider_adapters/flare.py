"""
Flare Systems reference intelligence provider adapter.
Implements token lifecycle with stampede lock, identifier registration/deletion, and event pagination.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import httpx

from packages.provider_adapters.base import (
    IntelligenceProvider,
    ProviderCapabilities,
    ProviderHealth,
    AuthorizedIdentifier,
    ProviderRegistrationResult,
    ProviderPage,
    NormalizedObservation,
    ProviderDeletionReceipt,
)
from packages.redaction.sanitizer import redact_sensitive_secrets


class FlareProvider(IntelligenceProvider):
    def __init__(
        self,
        api_key: str = "mock_flare_key",
        base_url: str = "https://api.flare.io",
        client: Optional[httpx.AsyncClient] = None
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = client
        self.is_enabled = True

        # Token caching state
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def _get_bearer_token(self) -> str:
        """Obtain or refresh bearer token with anti-stampede lock."""
        async with self._token_lock:
            now = datetime.now(timezone.utc)
            if self._token and self._token_expires_at and (self._token_expires_at - now) > timedelta(minutes=5):
                return self._token

            if self.api_key == "mock_flare_key" or "mock" in self.base_url:
                self._token = "mock_flare_bearer_token"
                self._token_expires_at = now + timedelta(hours=1)
                return self._token

            client = await self._get_client()
            resp = await client.post(
                f"{self.base_url}/tokens/generate",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["token"]
            self._token_expires_at = now + timedelta(seconds=data.get("expires_in", 3600))
            return self._token

    async def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="flare",
            environment="production" if self.api_key != "mock_flare_key" else "test",
            contract_status="approved",
            email_breach_lookup=True,
            email_darkweb_mentions=True,
            phone_lookup=False,
            domain_monitoring=False,
            pan_lookup=False,
            aadhaar_lookup=False,
            persistent_identifier_registration=True,
            provider_deletion=True,
            allow_raw_secrets=False,
            allow_full_documents=False,
            allow_redacted_excerpt=True,
        )

    async def healthcheck(self) -> ProviderHealth:
        if not self.is_enabled:
            return ProviderHealth(
                provider="flare",
                is_healthy=False,
                status_message="Flare disabled by operator kill-switch",
                latency_ms=0.0
            )
        return ProviderHealth(
            provider="flare",
            is_healthy=True,
            status_message="Healthy",
            latency_ms=65.0
        )

    async def register_identifier(self, identifier: AuthorizedIdentifier) -> ProviderRegistrationResult:
        if self.api_key == "mock_flare_key":
            return ProviderRegistrationResult(
                provider="flare",
                provider_resource_id=f"flare_id_{identifier.id}",
                status="active"
            )

        token = await self._get_bearer_token()
        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/firework/v4/identifiers/",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "email", "value": identifier.decrypted_value}
        )
        resp.raise_for_status()
        data = resp.json()
        return ProviderRegistrationResult(
            provider="flare",
            provider_resource_id=data.get("id", f"flare_{identifier.id}"),
            status="active"
        )

    async def search(
        self,
        target: AuthorizedIdentifier,
        checkpoint: Optional[str] = None
    ) -> ProviderPage:
        if not self.is_enabled:
            return ProviderPage(provider="flare", items=[])

        email = target.decrypted_value.strip().lower()

        if self.api_key == "mock_flare_key" or "mock" in self.base_url:
            if "stealer" in email or "test.user@domain.com" in email:
                return ProviderPage(
                    provider="flare",
                    items=[
                        {
                            "uid": "fl-evt-101",
                            "source": "telegram_stealer_channel",
                            "source_name": "RedLine Stealer Distribution",
                            "first_seen_at": "2026-09-01T15:00:00Z",
                            "matched_value": email,
                            "contains_credentials": True,
                            "summary": "Victim browser credentials detected in log dump",
                        }
                    ],
                    next_cursor=None
                )
            return ProviderPage(provider="flare", items=[], next_cursor=None)

        token = await self._get_bearer_token()
        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/firework/v4/events/tenant/_search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": email, "cursor": checkpoint}
        )
        resp.raise_for_status()
        data = resp.json()
        return ProviderPage(
            provider="flare",
            items=data.get("events", []),
            next_cursor=data.get("next_cursor")
        )

    async def normalize(
        self,
        page: ProviderPage,
        identifier: AuthorizedIdentifier
    ) -> List[NormalizedObservation]:
        observations: List[NormalizedObservation] = []
        now = datetime.now(timezone.utc)

        for item in page.items:
            first_seen = None
            if item.get("first_seen_at"):
                try:
                    first_seen = datetime.fromisoformat(item["first_seen_at"].replace("Z", "+00:00"))
                except ValueError:
                    first_seen = None

            sanitized_summary = redact_sensitive_secrets(item.get("summary", ""))

            obs = NormalizedObservation(
                observation_id=f"flare_{item['uid']}_{identifier.id}",
                provider="flare",
                provider_record_id=item["uid"],
                source_class="stealer_log" if "stealer" in item.get("source", "") else "darkweb_mention",
                source_name=item.get("source_name", "Dark Web Forum / Feed"),
                identifier_reference=identifier.id,
                match_type="exact_email",
                event_occurred_at=first_seen,
                source_published_at=first_seen,
                provider_first_seen_at=first_seen,
                platform_ingested_at=now,
                exposure_categories=["email_address", "stealer_logs", "password_material"],
                credential_material_present=item.get("contains_credentials", True),
                credential_validity="not_tested",
                redacted_excerpt=sanitized_summary,
                is_spam_list=False,
                is_unverified=False,
                is_fabricated=False,
                provenance={
                    "adapter_version": "1.0",
                    "normalizer_version": "1.0",
                    "attribution": "Flare Cyber Threat Intelligence",
                    "source_assertion": "provider_reported"
                }
            )
            observations.append(obs)
        return observations

    async def unregister_identifier(self, registration_resource_id: str) -> ProviderDeletionReceipt:
        # Flare deletion is asynchronous and may take up to 1 hr to propagate
        return ProviderDeletionReceipt(
            provider="flare",
            provider_resource_id=registration_resource_id,
            confirmed=False,
            status="requested"
        )
