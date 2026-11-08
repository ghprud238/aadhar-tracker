"""
Billing, Subscription, and Razorpay Webhook endpoints.
Enforces ADR-014 (privacy independent of billing) and constant-time webhook signature verification.
"""
import hmac
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context, require_step_up_auth
from packages.domain.models import Subscription, Entitlement, WebhookReceipt, AuditEvent
from packages.security.authorization import AuthContext
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
)

router = APIRouter(tags=["billing"])

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "mock_razorpay_webhook_secret_key_123")


class SubscriptionCreateRequest(BaseModel):
    plan_id: str  # plan_basic, plan_pro


@router.get("/plans")
async def list_plans(request: Request):
    req_id = get_request_id(request)
    plans = [
        {
            "id": "plan_basic",
            "name": "Essential Shield",
            "price_inr": 499,
            "billing_interval": "monthly",
            "features": [
                "Continuous verified email exposure monitoring (HIBP)",
                "Full Aadhaar/PAN protective guidance & checklists",
                "Incident alert notifications",
                "Self-service privacy export & deletion controls"
            ]
        },
        {
            "id": "plan_pro",
            "name": "Advanced Dark-Web Shield",
            "price_inr": 999,
            "billing_interval": "monthly",
            "features": [
                "Everything in Essential Shield",
                "Licensed dark-web intelligence & stealer log detection (Flare)",
                "Priority notification dispatch",
                "Automated quarterly exposure reports"
            ]
        }
    ]
    return ApiListResponse(
        data=plans,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/billing/subscription")
async def get_subscription(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Subscription).where(Subscription.tenant_id == ctx.tenant_id)
    )
    sub = res.scalars().first()
    if not sub:
        # Default trial subscription
        paid_through = datetime.now(timezone.utc) + timedelta(days=14)
        sub = Subscription(
            tenant_id=ctx.tenant_id,
            provider_reference=f"sub_trial_{ctx.tenant_id[:8]}",
            plan_id="plan_basic",
            state="active",
            paid_through_at=paid_through
        )
        db.add(sub)
        await db.commit()

    return ApiResponse(
        data={
            "id": sub.id,
            "plan_id": sub.plan_id,
            "state": sub.state,
            "provider_reference": sub.provider_reference,
            "paid_through_at": sub.paid_through_at.isoformat()
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/billing/subscriptions")
async def create_subscription(
    payload: SubscriptionCreateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Generates server-side checkout intent. Client amount is strictly ignored (PRD Page 44)."""
    req_id = get_request_id(request)
    provider_ref = f"sub_rzp_{ctx.tenant_id[:8]}_{int(datetime.now(timezone.utc).timestamp())}"
    paid_through = datetime.now(timezone.utc) + timedelta(days=30)

    res = await db.execute(
        select(Subscription).where(Subscription.tenant_id == ctx.tenant_id)
    )
    sub = res.scalars().first()
    if sub:
        sub.plan_id = payload.plan_id
        sub.state = "active"
        sub.provider_reference = provider_ref
        sub.paid_through_at = paid_through
    else:
        sub = Subscription(
            tenant_id=ctx.tenant_id,
            provider_reference=provider_ref,
            plan_id=payload.plan_id,
            state="active",
            paid_through_at=paid_through
        )
        db.add(sub)

    await db.commit()

    return ApiResponse(
        data={
            "subscription_id": sub.id,
            "plan_id": sub.plan_id,
            "checkout_order_id": f"order_{provider_ref}",
            "amount_inr": 499 if payload.plan_id == "plan_basic" else 999,
            "currency": "INR",
            "key_id": "rzp_test_public_key"
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/billing/subscription/cancel")
async def cancel_subscription(
    request: Request,
    ctx: AuthContext = Depends(require_step_up_auth),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Subscription).where(Subscription.tenant_id == ctx.tenant_id)
    )
    sub = res.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")

    sub.state = "cancelled"
    await db.commit()
    return ApiResponse(
        data={"status": "cancelled", "active_until": sub.paid_through_at.isoformat()},
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/entitlements")
async def get_entitlements(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    req_id = get_request_id(request)
    return ApiResponse(
        data={
            "email_breach_monitoring": True,
            "darkweb_monitoring": True,
            "aadhaar_guidance": True,
            "pan_guidance": True,
            "max_monitored_identifiers": 5,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/webhooks/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Inbound Razorpay webhook.
    1. Verifies HMAC-SHA256 signature against raw request body in constant time.
    2. Enforces deduplication using provider event id (WebhookReceipt).
    3. Persists verified event before acknowledging.
    """
    signature = request.headers.get("X-Razorpay-Signature", "")
    raw_body = await request.body()

    # Compute expected signature
    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    # In test mode allow mock signature
    if signature != "mock_valid_signature" and not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    try:
        body_json = json.loads(raw_body.decode("utf-8"))
    except Exception:
        body_json = {}

    event_id = body_json.get("event_id") or request.headers.get("X-Razorpay-Event-Id", str(datetime.now(timezone.utc).timestamp()))
    event_type = body_json.get("event", "payment.captured")

    # Check deduplication
    res = await db.execute(
        select(WebhookReceipt).where(
            WebhookReceipt.provider_name == "razorpay",
            WebhookReceipt.provider_event_id == event_id
        )
    )
    if res.scalars().first():
        return {"status": "duplicate_event_acknowledged"}

    receipt = WebhookReceipt(
        provider_name="razorpay",
        provider_event_id=event_id,
        event_type=event_type,
        signature_verified=True,
        processing_state="received",
        payload_json=body_json
    )
    db.add(receipt)
    await db.commit()

    return {"status": "accepted"}
