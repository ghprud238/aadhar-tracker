"""
Consent and Processing Notices endpoints.
Strictly implements granular consent tracking, version validation, and immediate revocation.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import (
    ProcessingNotice,
    ConsentGrant,
    ConsentEvent,
    Subject,
    OutboxEvent,
    MonitoringJob,
)
from packages.security.authorization import AuthContext
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
    ConsentGrantRequest,
    ConsentGrantDTO,
    ProcessingNoticeDTO,
)

router = APIRouter(tags=["consents"])


class PrivacySettingsUpdate(BaseModel):
    allow_telemetry: Optional[bool] = None
    data_minimization_mode: Optional[bool] = None


@router.get("/processing-notices")
async def list_processing_notices(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(ProcessingNotice).where(ProcessingNotice.publication_state == "published")
    )
    notices = res.scalars().all()
    dtos = [
        ProcessingNoticeDTO(
            id=n.id,
            version=n.version,
            purpose=n.purpose,
            title=n.title,
            content_html=n.content_html,
            published_at=n.published_at
        )
        for n in notices
    ]
    return ApiListResponse(
        data=dtos,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/processing-notices/{version}")
async def get_processing_notice_by_version(
    version: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(ProcessingNotice).where(ProcessingNotice.version == version)
    )
    notice = res.scalars().first()
    if not notice:
        raise HTTPException(status_code=404, detail="Processing notice version not found")
    return ApiResponse(
        data=ProcessingNoticeDTO(
            id=notice.id,
            version=notice.version,
            purpose=notice.purpose,
            title=notice.title,
            content_html=notice.content_html,
            published_at=notice.published_at
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/consents")
async def list_consents(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.tenant_id == ctx.tenant_id,
            ConsentGrant.subject_id == ctx.subject_id,
            ConsentGrant.status == "granted"
        )
    )
    grants = res.scalars().all()
    dtos = [
        ConsentGrantDTO(
            id=g.id,
            subject_id=g.subject_id,
            purpose=g.purpose,
            provider_categories=g.provider_categories,
            notice_version=g.notice_version,
            status=g.status,
            created_at=g.created_at
        )
        for g in grants
    ]
    return ApiListResponse(
        data=dtos,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/consents", status_code=status.HTTP_201_CREATED)
async def grant_consent(
    payload: ConsentGrantRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)

    # Validate that notice exists
    res_notice = await db.execute(
        select(ProcessingNotice).where(ProcessingNotice.version == payload.notice_version)
    )
    notice = res_notice.scalars().first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unapproved processing notice version"
        )

    # Check for existing active grant
    res_grant = await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.tenant_id == ctx.tenant_id,
            ConsentGrant.subject_id == ctx.subject_id,
            ConsentGrant.purpose == payload.purpose,
            ConsentGrant.status == "granted"
        )
    )
    existing = res_grant.scalars().first()
    if existing:
        return ApiResponse(
            data=ConsentGrantDTO(
                id=existing.id,
                subject_id=existing.subject_id,
                purpose=existing.purpose,
                provider_categories=existing.provider_categories,
                notice_version=existing.notice_version,
                status=existing.status,
                created_at=existing.created_at
            ),
            meta=ResponseMeta(request_id=req_id)
        )

    grant = ConsentGrant(
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        purpose=payload.purpose,
        provider_categories=payload.provider_categories,
        notice_version=payload.notice_version,
        status="granted"
    )
    db.add(grant)

    # Record immutable audit event
    c_event = ConsentEvent(
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        event_type="grant",
        purpose=payload.purpose,
        notice_version=payload.notice_version,
    )
    db.add(c_event)
    await db.commit()

    return ApiResponse(
        data=ConsentGrantDTO(
            id=grant.id,
            subject_id=grant.subject_id,
            purpose=grant.purpose,
            provider_categories=grant.provider_categories,
            notice_version=grant.notice_version,
            status=grant.status,
            created_at=grant.created_at
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/consents/{id}/withdraw")
async def withdraw_consent(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    On withdrawal:
    1. Mark authorization inactive immediately.
    2. Increment authorization version.
    3. Cancel queued jobs.
    4. Emit outbox event.
    """
    req_id = get_request_id(request)
    res = await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.id == id,
            ConsentGrant.tenant_id == ctx.tenant_id,
            ConsentGrant.subject_id == ctx.subject_id
        )
    )
    grant = res.scalars().first()
    if not grant:
        raise HTTPException(status_code=404, detail="Consent grant not found")

    grant.status = "withdrawn"
    grant.withdrawn_at = datetime.now(timezone.utc)

    # Increment subject authorization version
    res_sub = await db.execute(select(Subject).where(Subject.id == ctx.subject_id))
    subject = res_sub.scalars().first()
    if subject:
        subject.authorization_version += 1
        new_auth_version = subject.authorization_version
    else:
        new_auth_version = 1

    # Cancel any queued monitoring jobs
    await db.execute(
        update(MonitoringJob)
        .where(
            MonitoringJob.tenant_id == ctx.tenant_id,
            MonitoringJob.subject_id == ctx.subject_id,
            MonitoringJob.state.in_(["queued", "running"])
        )
        .values(state="authorization_revoked")
    )

    # Consent event history
    event = ConsentEvent(
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        event_type="withdraw",
        purpose=grant.purpose,
        notice_version=grant.notice_version,
    )
    db.add(event)

    # Transactional outbox event
    outbox = OutboxEvent(
        event_id=req_id,
        event_type="privacy.consent.withdrawn",
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        resource_id=grant.id,
        authorization_version=new_auth_version,
        payload={"purpose": grant.purpose}
    )
    db.add(outbox)
    await db.commit()

    return ApiResponse(
        data={"status": "withdrawn", "authorization_version": new_auth_version},
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/consent-events")
async def list_consent_events(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(ConsentEvent).where(
            ConsentEvent.tenant_id == ctx.tenant_id,
            ConsentEvent.subject_id == ctx.subject_id
        ).order_by(ConsentEvent.effective_time.desc())
    )
    events = res.scalars().all()
    data = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "purpose": e.purpose,
            "notice_version": e.notice_version,
            "effective_time": e.effective_time.isoformat()
        }
        for e in events
    ]
    return ApiListResponse(
        data=data,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/privacy/settings")
async def get_privacy_settings(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    req_id = get_request_id(request)
    return ApiResponse(
        data={
            "allow_telemetry": False,
            "data_minimization_mode": True,
            "retention_policy_days": 30
        },
        meta=ResponseMeta(request_id=req_id)
    )
