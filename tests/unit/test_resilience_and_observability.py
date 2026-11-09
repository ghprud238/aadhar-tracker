"""
Unit & Integration Tests for Enterprise Robustness Features.
Covers:
1. Circuit Breaker failure thresholds, cooldowns, and half-open canaries.
2. Outbox Dead Letter Queue (DLQ) max-retries and operator re-drive.
3. API Idempotency Key header replay and concurrent request protection.
4. Sliding window rate limiting on sensitive verification challenge endpoints.
5. Prometheus /metrics scrape output and /readyz /livez probes.
6. Cryptographic Key Rotation Manager for KEK re-wrapping.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db, async_session_factory
from packages.provider_adapters.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenException,
)
from packages.domain.models import OutboxEvent, Identifier
from services.api.outbox_dispatcher import OutboxDispatcher
from packages.security.crypto import EnvelopeVault
from packages.security.key_rotation import KeyRotationManager


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


# -----------------------------------------------------------------------------
# 1. Circuit Breaker Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_trips_to_open_after_threshold():
    """Verify circuit breaker trips from CLOSED to OPEN after 3 failures."""
    cb = CircuitBreaker("test_provider", failure_threshold=3, recovery_timeout_seconds=0.5)
    assert cb.state == CircuitState.CLOSED

    async def failing_call():
        raise RuntimeError("Remote provider 503")

    # Failures 1 and 2: Still CLOSED
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(failing_call)
        assert cb.state == CircuitState.CLOSED

    # Failure 3: Trips to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN
    assert cb.total_trips == 1

    # Immediate call is blocked without executing function
    with pytest.raises(CircuitBreakerOpenException):
        await cb.call(failing_call)

    # Wait for recovery timeout to transition to HALF_OPEN
    await asyncio.sleep(0.6)

    async def successful_call():
        return {"status": "ok"}

    res = await cb.call(successful_call)
    assert res == {"status": "ok"}
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


# -----------------------------------------------------------------------------
# 2. Dead Letter Queue (DLQ) & Operator Re-drive Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_outbox_moves_to_dead_letter_queue_after_max_retries():
    """Verify exhausted outbox tasks move to dead_letter state with last_error."""
    async with async_session_factory() as db:
        # Create a failing outbox event with non-existent job ID
        event = OutboxEvent(
            event_id="evt_fail_101",
            event_type="monitoring.scan.requested",
            tenant_id="ten_1",
            subject_id="sub_1",
            resource_id="res_1",
            authorization_version=1,
            payload={"job_id": "non_existent_job_uuid"},
            state="pending",
            retry_count=0
        )
        db.add(event)
        await db.commit()

        dispatcher = OutboxDispatcher(db, max_retries=3)

        # Dispatch 3 times -> exhausts retries
        for i in range(3):
            await dispatcher.dispatch_pending(limit=10)

        # Event should now be in dead_letter
        dead_letters = await dispatcher.get_dead_letter_events()
        dlq_event = next((e for e in dead_letters if e.event_id == "evt_fail_101"), None)
        assert dlq_event is not None
        assert dlq_event.state == "dead_letter"
        assert dlq_event.retry_count >= 3
        assert dlq_event.last_error is not None
        assert dlq_event.dead_lettered_at is not None

        # Operator re-drive
        success = await dispatcher.re_drive_dead_letter("evt_fail_101")
        assert success is True

        # Check reset
        await db.refresh(dlq_event)
        assert dlq_event.state == "pending"
        assert dlq_event.retry_count == 0
        assert dlq_event.last_error is None


# -----------------------------------------------------------------------------
# 3. Idempotency Key Middleware Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_idempotency_key_replays_cached_response():
    """Verify sending identical Idempotency-Key replays exact cached response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=idempotent_user@domain.com")
        token = res_auth.json()["data"]["session_id"]
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "key_unique_abc_123"
        }

        # First request: adds identifier
        res1 = await client.post(
            "/api/v1/identifiers",
            headers=auth_headers,
            json={"type": "email", "value": "idem.check@domain.com"}
        )
        assert res1.status_code == 201
        data1 = res1.json()

        # Second request with identical key: returns cached response
        res2 = await client.post(
            "/api/v1/identifiers",
            headers=auth_headers,
            json={"type": "email", "value": "idem.check@domain.com"}
        )
        assert res2.status_code == 201
        assert res2.headers.get("x-idempotent-replay") == "true"
        data2 = res2.json()
        assert data1["data"]["id"] == data2["data"]["id"]


# -----------------------------------------------------------------------------
# 4. Rate Limiting Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limiter_throttles_excessive_otp_attempts():
    """Verify rate limiter blocks more than 5 rapid challenge attempts with HTTP 429."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=rate_limit_user@domain.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Perform 5 rapid requests (allowed by limit)
        for _ in range(5):
            await client.post(
                "/api/v1/identifiers/verification-challenges/complete",
                headers=headers,
                json={"identifier_id": "dummy_id", "challenge_token": "000000"}
            )

        # 6th request: throttled with 429
        res_throttled = await client.post(
            "/api/v1/identifiers/verification-challenges/complete",
            headers=headers,
            json={"identifier_id": "dummy_id", "challenge_token": "000000"}
        )
        assert res_throttled.status_code == 429
        assert "Retry-After" in res_throttled.headers
        assert res_throttled.json()["error"]["code"] == "RATE_LIMITED"


# -----------------------------------------------------------------------------
# 5. Prometheus Metrics & Kubernetes Health Probes
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prometheus_metrics_and_health_probes():
    """Verify /metrics returns Prometheus exposition format and /readyz confirms dependencies."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # /livez
        res_live = await client.get("/livez")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "alive"

        # /readyz
        res_ready = await client.get("/readyz")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"
        assert res_ready.json()["checks"]["database"] is True

        # /metrics
        res_metrics = await client.get("/metrics")
        assert res_metrics.status_code == 200
        content = res_metrics.text
        assert "suraksha_http_requests_total" in content or "suraksha" in content


# -----------------------------------------------------------------------------
# 6. Cryptographic Key Rotation Manager Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cryptographic_key_rotation_re_wraps_envelopes():
    """Verify KeyRotationManager re-encrypts envelopes under new master key cleanly."""
    vault1 = EnvelopeVault(master_key=b"k" * 32)
    vault2 = EnvelopeVault(master_key=b"r" * 32)
    manager = KeyRotationManager(current_vault=vault1, target_vault=vault2)

    ad = "ten_test:sub_test"
    original_secret = "citizen.secret.pan@domain.com"
    envelope_v1 = vault1.encrypt(original_secret, associated_data=ad)

    # Re-wrap
    envelope_v2 = manager.re_encrypt_value(envelope_v1, associated_data=ad)
    assert envelope_v2 != envelope_v1

    # New vault decrypts successfully
    decrypted_v2 = vault2.decrypt(envelope_v2, associated_data=ad)
    assert decrypted_v2 == original_secret

    # Old vault cannot decrypt v2 envelope
    with pytest.raises(Exception):
        vault1.decrypt(envelope_v2, associated_data=ad)
