"""
Incident, Finding, and Remediation endpoints.
Implements incident state machine, user remediation provenance, and false-match dispute handling.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import (
    Incident,
    Finding,
    IncidentFinding,
    RemediationAction,
    Identifier,
    AuditEvent,
)
from packages.domain.enums import IncidentState
from packages.security.authorization import AuthContext
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
    IncidentDTO,
    IncidentIdentifierInfo,
    RemediationActionDTO,
)

router = APIRouter(tags=["incidents"])


class IncidentStateUpdateRequest(BaseModel):
    state: str  # acknowledged, action_in_progress, resolved_by_user


class DisputeCreateRequest(BaseModel):
    reason: str  # this_is_not_mine, do_not_recognize, already_addressed
    notes: Optional[str] = None


@router.get("/incidents")
async def list_incidents(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Incident, Identifier).join(
            Identifier, Incident.identifier_id == Identifier.id
        ).where(
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id
        ).order_by(Incident.priority_score.desc(), Incident.first_detected_at.desc())
    )
    rows = res.all()
    dtos = []
    for inc, ident in rows:
        # Load recommended actions from remediation_actions table
        res_actions = await db.execute(
            select(RemediationAction).where(RemediationAction.incident_id == inc.id)
        )
        actions = res_actions.scalars().all()
        action_keys = [a.action_type for a in actions] or ["change_affected_password", "review_reuse", "enable_mfa"]

        dtos.append(
            IncidentDTO(
                id=inc.id,
                title=inc.title,
                severity=inc.severity,
                confidence=inc.confidence,
                state=inc.state,
                identifier=IncidentIdentifierInfo(id=ident.id, masked_value=ident.masked_value),
                exposure_categories=inc.exposure_categories,
                credential_validity="not_tested",
                event_occurred_at=inc.event_occurred_at,
                first_detected_at=inc.first_detected_at,
                priority_score=inc.priority_score,
                rules_version=inc.rules_version,
                recommended_actions=action_keys
            )
        )

    return ApiListResponse(
        data=dtos,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/incidents/{id}")
async def get_incident_detail(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Incident, Identifier).join(
            Identifier, Incident.identifier_id == Identifier.id
        ).where(
            Incident.id == id,
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id
        )
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Incident unavailable to this principal")
    inc, ident = row

    res_actions = await db.execute(
        select(RemediationAction).where(RemediationAction.incident_id == inc.id)
    )
    actions = res_actions.scalars().all()
    action_keys = [a.action_type for a in actions] or ["change_affected_password", "review_reuse", "enable_mfa"]

    dto = IncidentDTO(
        id=inc.id,
        title=inc.title,
        severity=inc.severity,
        confidence=inc.confidence,
        state=inc.state,
        identifier=IncidentIdentifierInfo(id=ident.id, masked_value=ident.masked_value),
        exposure_categories=inc.exposure_categories,
        credential_validity="not_tested",
        event_occurred_at=inc.event_occurred_at,
        first_detected_at=inc.first_detected_at,
        priority_score=inc.priority_score,
        rules_version=inc.rules_version,
        recommended_actions=action_keys
    )
    return ApiResponse(data=dto, meta=ResponseMeta(request_id=req_id))


@router.patch("/incidents/{id}")
async def update_incident_state(
    id: str,
    payload: IncidentStateUpdateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Incident).where(
            Incident.id == id,
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id
        )
    )
    inc = res.scalars().first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    allowed_transitions = [
        IncidentState.ACKNOWLEDGED.value,
        IncidentState.ACTION_IN_PROGRESS.value,
        IncidentState.RESOLVED_BY_USER.value
    ]
    if payload.state not in allowed_transitions:
        raise HTTPException(status_code=400, detail=f"Invalid state transition to {payload.state}")

    inc.state = payload.state
    await db.commit()
    return ApiResponse(
        data={"id": inc.id, "state": inc.state},
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/incidents/{id}/remediations")
async def get_incident_remediations(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(RemediationAction).where(
            RemediationAction.incident_id == id,
            RemediationAction.tenant_id == ctx.tenant_id
        )
    )
    actions = res.scalars().all()
    dtos = [
        RemediationActionDTO(
            id=a.id,
            action_type=a.action_type,
            title=a.title,
            description=a.description,
            state=a.state,
            completed_at=a.completed_at,
            completion_provenance=a.completion_provenance
        )
        for a in actions
    ]
    return ApiListResponse(
        data=dtos,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/remediations/{id}/complete")
async def complete_remediation_action(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Records that user completed action with clear provenance (FR-016).
    Semantic note: User reports protective action was completed; does not imply leaked record disappeared.
    """
    req_id = get_request_id(request)
    res = await db.execute(
        select(RemediationAction).where(
            RemediationAction.id == id,
            RemediationAction.tenant_id == ctx.tenant_id
        )
    )
    action = res.scalars().first()
    if not action:
        raise HTTPException(status_code=404, detail="Remediation action not found")

    action.state = "completed"
    action.completed_at = datetime.now(timezone.utc)
    action.completion_provenance = "user_reported"
    await db.commit()

    return ApiResponse(
        data=RemediationActionDTO(
            id=action.id,
            action_type=action.action_type,
            title=action.title,
            description=action.description,
            state=action.state,
            completed_at=action.completed_at,
            completion_provenance=action.completion_provenance
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/remediations/{id}/reopen")
async def reopen_remediation_action(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(RemediationAction).where(
            RemediationAction.id == id,
            RemediationAction.tenant_id == ctx.tenant_id
        )
    )
    action = res.scalars().first()
    if not action:
        raise HTTPException(status_code=404, detail="Remediation action not found")

    action.state = "pending"
    action.completed_at = None
    action.completion_provenance = None
    await db.commit()

    return ApiResponse(
        data=RemediationActionDTO(
            id=action.id,
            action_type=action.action_type,
            title=action.title,
            description=action.description,
            state=action.state,
            completed_at=None,
            completion_provenance=None
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/findings/{id}/disputes")
async def create_finding_dispute(
    id: str,
    payload: DisputeCreateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an auditable dispute (FR-026).
    Transitions associated incident to disputed and stops notification re-alerts.
    """
    req_id = get_request_id(request)
    res = await db.execute(
        select(Finding).where(
            Finding.id == id,
            Finding.tenant_id == ctx.tenant_id,
            Finding.subject_id == ctx.subject_id
        )
    )
    finding = res.scalars().first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.state = "disputed"

    # Find parent incident if any
    res_link = await db.execute(
        select(IncidentFinding).where(IncidentFinding.finding_id == finding.id)
    )
    link = res_link.scalars().first()
    if link:
        await db.execute(
            update(Incident)
            .where(Incident.id == link.incident_id)
            .values(state=IncidentState.DISPUTED.value)
        )

    # Record audit event
    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="finding.dispute_created",
        scoped_resource=f"finding:{finding.id}",
        result="success",
        details_json={"reason": payload.reason, "notes": payload.notes or ""}
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data={
            "dispute_id": f"disp_{finding.id[:8]}",
            "finding_id": finding.id,
            "status": "under_review",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        meta=ResponseMeta(request_id=req_id)
    )
