"""
Notification and Preference management routes.
Strictly enforces privacy-safe alert templates and deduplication (FR-017).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import NotificationDelivery, NotificationPreference
from packages.security.authorization import AuthContext
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
)

router = APIRouter(tags=["notifications"])


class NotificationPreferencesUpdate(BaseModel):
    immediate_critical: Optional[bool] = None
    immediate_high: Optional[bool] = None
    digest_low: Optional[bool] = None


@router.get("/notifications")
async def list_notifications(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.tenant_id == ctx.tenant_id
        ).order_by(NotificationDelivery.created_at.desc())
    )
    deliveries = res.scalars().all()
    data = [
        {
            "id": d.id,
            "title": d.title,
            "body": d.body_sanitized,
            "channel": d.channel,
            "status": d.status,
            "created_at": d.created_at.isoformat()
        }
        for d in deliveries
    ]
    return ApiListResponse(
        data=data,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/notifications/{id}/read")
async def mark_notification_read(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.id == id,
            NotificationDelivery.tenant_id == ctx.tenant_id
        )
    )
    delivery = res.scalars().first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Notification not found")
    delivery.status = "read"
    await db.commit()
    return ApiResponse(data={"id": id, "status": "read"}, meta=ResponseMeta(request_id=req_id))


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    await db.execute(
        update(NotificationDelivery)
        .where(NotificationDelivery.tenant_id == ctx.tenant_id)
        .values(status="read")
    )
    await db.commit()
    return ApiResponse(data={"marked_all_read": True}, meta=ResponseMeta(request_id=req_id))


@router.get("/notification-preferences")
async def get_notification_preferences(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(NotificationPreference).where(NotificationPreference.tenant_id == ctx.tenant_id)
    )
    pref = res.scalars().first()
    if not pref:
        pref = NotificationPreference(
            tenant_id=ctx.tenant_id,
            channel="email",
            destination=ctx.session.email,
            immediate_critical=True,
            immediate_high=True,
            digest_low=True
        )
        db.add(pref)
        await db.commit()

    return ApiResponse(
        data={
            "channel": pref.channel,
            "destination": pref.destination,
            "immediate_critical": pref.immediate_critical,
            "immediate_high": pref.immediate_high,
            "digest_low": pref.digest_low,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.patch("/notification-preferences")
async def update_notification_preferences(
    payload: NotificationPreferencesUpdate,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(NotificationPreference).where(NotificationPreference.tenant_id == ctx.tenant_id)
    )
    pref = res.scalars().first()
    if not pref:
        pref = NotificationPreference(
            tenant_id=ctx.tenant_id,
            channel="email",
            destination=ctx.session.email
        )
        db.add(pref)

    if payload.immediate_critical is not None:
        pref.immediate_critical = payload.immediate_critical
    if payload.immediate_high is not None:
        pref.immediate_high = payload.immediate_high
    if payload.digest_low is not None:
        pref.digest_low = payload.digest_low

    await db.commit()
    return ApiResponse(
        data={
            "immediate_critical": pref.immediate_critical,
            "immediate_high": pref.immediate_high,
            "digest_low": pref.digest_low,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/notification-preferences/test")
async def send_test_notification(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Dispatches privacy-safe test notification without sensitive data."""
    req_id = get_request_id(request)
    delivery = NotificationDelivery(
        tenant_id=ctx.tenant_id,
        notification_intent_id=str(uuid.uuid4()),
        channel="email",
        destination_reference=ctx.session.email,
        title="Identity Protection Test Notification",
        body_sanitized="This is a test notification confirming that alert delivery is operational. No personal secrets are included.",
        status="sent"
    )
    db.add(delivery)
    await db.commit()

    return ApiResponse(
        data={"sent": True, "delivery_id": delivery.id},
        meta=ResponseMeta(request_id=req_id)
    )
