"""
Privacy, DPDP/GDPR Data Export, Account Deletion, and Audit Event endpoints.
Implements the 8-stage account deletion workflow and short-lived data export downloads.
"""
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context, require_step_up_auth
from packages.domain.models import (
    PrivacyRequest,
    AuditEvent,
    Subject,
    Identifier,
    Incident,
    ConsentGrant,
    OutboxEvent,
)
from packages.domain.enums import DeletionWorkflowState, IdentifierState
from packages.security.authorization import AuthContext
from packages.security.sessions import session_store
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
)

router = APIRouter(tags=["privacy"])


class GrievanceCreateRequest(BaseModel):
    category: str
    description: str


class SupportTicketCreateRequest(BaseModel):
    subject: str
    message: str


@router.post("/privacy/exports", status_code=status.HTTP_201_CREATED)
async def request_data_export(
    request: Request,
    ctx: AuthContext = Depends(require_step_up_auth),
    db: AsyncSession = Depends(get_db)
):
    """Initiates DPDP/GDPR data export. Requires recent step-up authentication."""
    req_id = get_request_id(request)
    download_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    req = PrivacyRequest(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        request_type="export",
        state="completed",
        download_token=download_token,
        download_expires_at=expires_at,
        details="User requested full personal data archive."
    )
    db.add(req)

    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="privacy.export_requested",
        scoped_resource=f"user:{ctx.user_id}",
        result="success"
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data={
            "export_id": req.id,
            "status": req.state,
            "download_token": download_token,
            "expires_at": expires_at.isoformat()
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/privacy/exports/{id}/download")
async def download_data_export(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(require_step_up_auth),
    db: AsyncSession = Depends(get_db)
):
    """Assembles and returns export archive. Validates tenant and subject ownership."""
    req_id = get_request_id(request)
    res_req = await db.execute(
        select(PrivacyRequest).where(
            PrivacyRequest.id == id,
            PrivacyRequest.tenant_id == ctx.tenant_id,
            PrivacyRequest.user_id == ctx.user_id
        )
    )
    pr = res_req.scalars().first()
    if not pr or pr.state != "completed":
        raise HTTPException(status_code=404, detail="Export not found or not ready")

    # Fetch user identifiers
    res_id = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    identifiers = [
        {"type": i.type, "masked_value": i.masked_value, "state": i.state, "created_at": i.created_at.isoformat()}
        for i in res_id.scalars().all()
    ]

    # Fetch incidents
    res_inc = await db.execute(
        select(Incident).where(
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id
        )
    )
    incidents = [
        {
            "id": inc.id,
            "title": inc.title,
            "severity": inc.severity,
            "confidence": inc.confidence,
            "categories": inc.exposure_categories,
            "detected_at": inc.first_detected_at.isoformat()
        }
        for inc in res_inc.scalars().all()
    ]

    export_payload = {
        "export_metadata": {
            "user_id": ctx.user_id,
            "tenant_id": ctx.tenant_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "notice": "Export generated under DPDP personal data rights."
        },
        "monitored_identifiers": identifiers,
        "exposure_incidents": incidents
    }

    return ApiResponse(data=export_payload, meta=ResponseMeta(request_id=req_id))


@router.post("/privacy/deletion-requests", status_code=status.HTTP_202_ACCEPTED)
async def request_account_deletion(
    request: Request,
    ctx: AuthContext = Depends(require_step_up_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiates 8-step deletion workflow:
    1. processing_disabled
    2. billing_addressed
    3. sessions_revoked
    4. provider_cleanup_pending
    5. active_store_cleanup
    6. completed_with_backup_expiry_notice
    """
    req_id = get_request_id(request)

    # 1. Disable processing on subject
    await db.execute(
        update(Subject)
        .where(Subject.id == ctx.subject_id)
        .values(monitoring_state="deletion_pending", authorization_version=Subject.authorization_version + 1)
    )

    # 2. Mark identifiers as deletion pending
    await db.execute(
        update(Identifier)
        .where(Identifier.tenant_id == ctx.tenant_id)
        .values(state=IdentifierState.DELETION_PENDING.value)
    )

    # 3. Create deletion request record
    del_req = PrivacyRequest(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        request_type="deletion",
        state=DeletionWorkflowState.PROCESSING_DISABLED.value,
        details="User initiated full account erasure."
    )
    db.add(del_req)

    # 4. Outbox event for privacy worker
    outbox = OutboxEvent(
        event_id=str(uuid.uuid4()),
        event_type="privacy.account.deletion_requested",
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        resource_id=del_req.id,
        authorization_version=999,
        payload={"user_id": ctx.user_id, "deletion_request_id": del_req.id}
    )
    db.add(outbox)

    # 5. Revoke all user sessions except current response completion
    session_store.revoke_all_user_sessions(ctx.user_id)

    await db.commit()

    return ApiResponse(
        data={
            "deletion_request_id": del_req.id,
            "status": "processing_disabled",
            "message": "Account processing disabled. Background erasure initiated with backup rolling expiry."
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/privacy/deletion-requests/{id}")
async def get_deletion_status(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(PrivacyRequest).where(
            PrivacyRequest.id == id,
            PrivacyRequest.tenant_id == ctx.tenant_id
        )
    )
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Deletion request not found")
    return ApiResponse(
        data={"id": req.id, "state": req.state, "created_at": req.created_at.isoformat()},
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/privacy/grievances", status_code=status.HTTP_201_CREATED)
async def submit_privacy_grievance(
    payload: GrievanceCreateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Submits privacy grievance under Section 13 of the Digital Personal Data Protection Act."""
    req_id = get_request_id(request)
    req = PrivacyRequest(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        request_type="grievance",
        state="submitted",
        details=f"Category: {payload.category}\nDetails: {payload.description}"
    )
    db.add(req)
    await db.commit()
    return ApiResponse(
        data={"grievance_id": req.id, "state": "submitted", "sla_days": 7},
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/audit-events")
async def list_audit_events(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(AuditEvent).where(
            AuditEvent.tenant_id == ctx.tenant_id
        ).order_by(AuditEvent.created_at.desc())
    )
    events = res.scalars().all()
    data = [
        {
            "id": e.id,
            "action": e.action,
            "scoped_resource": e.scoped_resource,
            "result": e.result,
            "created_at": e.created_at.isoformat()
        }
        for e in events
    ]
    return ApiListResponse(
        data=data,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )
