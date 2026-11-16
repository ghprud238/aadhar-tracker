"""
Ephemeral Self-Destructing Pass Store.
Provides time-bombed, encrypted document pass sharing with atomic single-view burning.
Never stores raw Aadhaar or unmasked PII.
"""
import uuid
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
from packages.domain.schemas import (
    EphemeralPassCreateRequest,
    EphemeralPassDTO,
    EphemeralPassReadDTO,
)


MAX_STORE_CAPACITY = 10_000


class EphemeralPassEntry:
    def __init__(
        self,
        token: str,
        document_type: str,
        masked_identifier: str,
        recipient_entity: str,
        purpose: str,
        encrypted_payload: str,
        ttl_seconds: int,
        single_burn: bool,
        tenant_id: str,
    ):
        self.token = token
        self.document_type = document_type
        self.masked_identifier = masked_identifier
        self.recipient_entity = recipient_entity
        self.purpose = purpose
        self.encrypted_payload = encrypted_payload
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.single_burn = single_burn
        self.views_remaining = 1 if single_burn else 10
        self.tenant_id = tenant_id
        self.burned = False

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at or self.views_remaining <= 0


class EphemeralPassStore:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._store: Dict[str, EphemeralPassEntry] = {}

    @classmethod
    def get_instance(cls) -> "EphemeralPassStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def create_pass(self, req: EphemeralPassCreateRequest, tenant_id: str) -> EphemeralPassDTO:
        with self._lock:
            # Purge expired
            self._cleanup_expired()

            # Evict oldest if reaching capacity bound
            if len(self._store) >= MAX_STORE_CAPACITY:
                oldest_tokens = sorted(self._store.keys(), key=lambda k: self._store[k].created_at)[:100]
                for tok in oldest_tokens:
                    self._store.pop(tok, None)

            token = f"suraksha_ephem_{uuid.uuid4().hex[:16]}"
            entry = EphemeralPassEntry(
                token=token,
                document_type=req.document_type,
                masked_identifier=req.masked_identifier,
                recipient_entity=req.recipient_entity,
                purpose=req.purpose,
                encrypted_payload=req.encrypted_payload,
                ttl_seconds=req.ttl_seconds,
                single_burn=req.single_burn,
                tenant_id=tenant_id,
            )
            self._store[token] = entry

            return EphemeralPassDTO(
                token=token,
                share_url=f"/p/{token}",
                expires_at=entry.expires_at,
                single_burn=entry.single_burn,
                views_remaining=entry.views_remaining,
                created_at=entry.created_at,
            )

    def read_and_burn_pass(self, token: str) -> Optional[EphemeralPassReadDTO]:
        with self._lock:
            entry = self._store.get(token)
            if not entry:
                return None

            if entry.is_expired():
                del self._store[token]
                return None

            # Decrement view count
            entry.views_remaining -= 1
            if entry.single_burn or entry.views_remaining <= 0:
                entry.burned = True
                del self._store[token]

            return EphemeralPassReadDTO(
                token=entry.token,
                document_type=entry.document_type,
                recipient_entity=entry.recipient_entity,
                purpose=entry.purpose,
                encrypted_payload=entry.encrypted_payload,
                burned=entry.burned,
                expires_at=entry.expires_at,
            )

    def _cleanup_expired(self):
        now = datetime.now(timezone.utc)
        expired_tokens = [k for k, v in self._store.items() if now >= v.expires_at or v.views_remaining <= 0]
        for t in expired_tokens:
            del self._store[t]
