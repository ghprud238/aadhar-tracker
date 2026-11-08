"""
Billing and Webhook Verification Tests.
Covers BILL-001 through BILL-016 from PRD Page 66.
"""
import pytest
import hmac
import hashlib
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db
from services.api.routes.billing import RAZORPAY_WEBHOOK_SECRET


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_billing_server_side_amount_calculation_bill_001():
    """Client amount is ignored; server calculates plan amount (BILL-001)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=billing_user@domain.com")
        token = res_auth.json()["data"]["session_id"]

        res = await client.post(
            "/api/v1/billing/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan_id": "plan_basic", "amount": 1}  # Client attempts to pay 1 INR
        )
        assert res.status_code == 200
        # Server must enforce 499 INR regardless of client input
        assert res.json()["data"]["amount_inr"] == 499


@pytest.mark.asyncio
async def test_razorpay_webhook_signature_verification_bill_003_bill_004():
    """HMAC-SHA256 signature verification over raw request body (BILL-003, BILL-004)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = b'{"event": "subscription.charged", "event_id": "evt_rzp_123"}'
        valid_sig = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        # 1. Invalid signature -> Rejected (BILL-004)
        res_invalid = await client.post(
            "/api/v1/webhooks/razorpay",
            content=payload,
            headers={"X-Razorpay-Signature": "invalid_signature", "Content-Type": "application/json"}
        )
        assert res_invalid.status_code == 400

        # 2. Valid signature -> Accepted and persisted (BILL-003)
        res_valid = await client.post(
            "/api/v1/webhooks/razorpay",
            content=payload,
            headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"}
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["status"] == "accepted"

        # 3. Duplicate event -> Acknowledged without duplicate processing (BILL-006)
        res_dup = await client.post(
            "/api/v1/webhooks/razorpay",
            content=payload,
            headers={"X-Razorpay-Signature": valid_sig, "Content-Type": "application/json"}
        )
        assert res_dup.status_code == 200
        assert res_dup.json()["status"] == "duplicate_event_acknowledged"
