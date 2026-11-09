"""
Companion endpoints for Mobile widgets and Wearable (smartwatch) glances.
Optimized for ultra-low latency, minimal payload size, and battery efficiency.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import Incident, Identifier, AuditEvent
from packages.domain.enums import IncidentState, IdentifierState
from packages.security.authorization import AuthContext
from packages.domain.schemas import ApiResponse, ResponseMeta

router = APIRouter(prefix="/companion", tags=["companion"])


@router.get("/glance")
async def get_companion_glance(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns lightweight summary payload designed specifically for smartwatch tiles,
    watch face complications, and mobile home screen widgets.
    """
    req_id = get_request_id(request)

    # 1. Fetch active incidents count & highest severity
    res_inc = await db.execute(
        select(Incident).where(
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id,
            Incident.state.in_([IncidentState.NEW.value, IncidentState.ACKNOWLEDGED.value, IncidentState.ACTION_IN_PROGRESS.value])
        ).order_by(Incident.priority_score.desc())
    )
    incidents = res_inc.scalars().all()
    active_count = len(incidents)

    highest_severity = "none"
    urgent_alert = None
    if active_count > 0:
        top_inc = incidents[0]
        highest_severity = top_inc.severity
        urgent_alert = {
            "incident_id": top_inc.id,
            "title": top_inc.title,
            "severity": top_inc.severity,
            "priority_score": top_inc.priority_score
        }

    # 2. Count active monitored identifiers
    res_ids = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id,
            Identifier.state == IdentifierState.ACTIVE.value
        )
    )
    active_identifiers = len(res_ids.scalars().all())

    # 3. Check biometric lock user confirmation in audit events
    res_audit = await db.execute(
        select(AuditEvent).where(
            AuditEvent.tenant_id == ctx.tenant_id,
            AuditEvent.action == "assistance.action_confirmed_by_user"
        )
    )
    biometrics_locked = res_audit.scalars().first() is not None

    shield_status = "critical" if highest_severity == "critical" else (
        "warning" if active_count > 0 else "secure"
    )

    return ApiResponse(
        data={
            "shield_status": shield_status,  # secure, warning, critical
            "active_incidents": active_count,
            "highest_severity": highest_severity,
            "active_monitored_count": active_identifiers,
            "biometrics_locked": biometrics_locked,
            "urgent_alert": urgent_alert,
            "last_synced_at": datetime.now(timezone.utc).isoformat()
        },
        meta=ResponseMeta(request_id=req_id)
    )
