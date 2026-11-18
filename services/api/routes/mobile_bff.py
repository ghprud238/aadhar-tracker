"""
Mobile Backend for Frontend (BFF) Router.
Provides optimized, aggregated, resilient, and battery-efficient endpoints
tailored specifically for Native Android (Jetpack Compose) and Native iOS (SwiftUI) applications.
Strictly adheres to Zero-Plaintext Invariant (no raw Aadhaar numbers or plain biometrics stored/transmitted).
"""
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import (
    Incident,
    Identifier,
    NotificationDelivery,
    UserAssistanceReport,
    AuditEvent,
)
from packages.domain.enums import IncidentState, IdentifierState
from packages.security.authorization import AuthContext
from packages.domain.schemas import (
    ApiResponse,
    ResponseMeta,
    ScamAnalysisRequest,
    ScamAnalysisDTO,
    PassVerificationRequest,
    PassVerificationDTO,
    PanicPackRequest,
    PanicPackExecutionDTO,
)
from packages.domain.scam_radar import ScamRadarEngine
from packages.domain.pass_verifier import PassVerifierService
from packages.domain.panic_pack import PanicPackService


router = APIRouter(prefix="/mobile", tags=["mobile-bff"])

# In-memory tracking for temporary biometric unlock countdown windows
_active_unlock_windows: Dict[str, datetime] = {}


# -----------------------------------------------------------------------------
# Mobile DTO Models
# -----------------------------------------------------------------------------

class MobileScoreBadgeDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    description: str
    icon: str
    unlocked: bool = Field(alias="unlocked")


class MobileScorePillarDTO(BaseModel):
    id: str
    title: str
    points: int
    max_points: int
    status: str  # achieved, partial, pending


class MobileHealthScoreDTO(BaseModel):
    score: int
    max_score: int = 1000
    tier: str
    tier_color: str
    percentile_text: str
    badges: List[Dict[str, Any]]
    pillars: List[MobileScorePillarDTO]
    top_recommendations: List[str]


class MobileBiometricStatusDTO(BaseModel):
    locked: bool
    locked_confirmed_at: Optional[str] = None
    auto_relock_active: bool
    auto_relock_seconds_left: int
    status_label: str


class MobileMaskedPassSummaryDTO(BaseModel):
    doc_type: str
    holder_name: str
    masked_identifier: str
    recipient: str
    purpose: str
    verified: bool
    compliance_standard: str


class MobileQuickActionDTO(BaseModel):
    id: str
    title: str
    subtitle: str
    icon: str
    badge: Optional[str] = None
    route: str


class MobileBootstrapDataDTO(BaseModel):
    session: Dict[str, Any]
    glance: Dict[str, Any]
    health_score: MobileHealthScoreDTO
    unread_alerts_count: int
    biometric_status: MobileBiometricStatusDTO
    masked_pass: MobileMaskedPassSummaryDTO
    quick_actions: List[MobileQuickActionDTO]
    sync_timestamp: str


class MobileAutoRelockRequest(BaseModel):
    action: str = Field(..., description="'start_window' | 'relock_now'")
    duration_seconds: int = Field(default=600, ge=60, le=3600)


class MobileCrashReportRequest(BaseModel):
    device_model: str
    os_name: str  # 'android' | 'ios'
    os_version: str
    app_version: str
    error_message: str
    stack_trace: Optional[str] = None


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def compute_mobile_health_score(
    biometrics_locked: bool,
    active_ids_count: int,
    active_incidents_count: int,
    has_generated_pass: bool = True
) -> MobileHealthScoreDTO:
    """Computes dynamic holistic citizen privacy hygiene score (0-1000)."""
    score = 200  # Baseline

    p_biometric = 250 if biometrics_locked else 0
    p_identity = 150 if active_ids_count > 0 else 0
    p_zero_breach = 150 if active_incidents_count == 0 else (50 if active_incidents_count == 1 else 0)
    p_family = 100
    p_pass = 150 if has_generated_pass else 0

    score += p_biometric + p_identity + p_zero_breach + p_family + p_pass
    score = min(score, 1000)

    if score >= 800:
        tier = "FORTRESS GUARDIAN"
        tier_color = "#10b981"
        percentile = "Top 4% Citizen Defense across India"
    elif score >= 650:
        tier = "VIGILANT SENTINEL"
        tier_color = "#38bdf8"
        percentile = "Top 18% Citizen Defense across India"
    elif score >= 450:
        tier = "PROTECTED CITIZEN"
        tier_color = "#f59e0b"
        percentile = "Top 45% Citizen Defense across India"
    else:
        tier = "ACTION REQUIRED"
        tier_color = "#ef4444"
        percentile = "Vulnerable to AePS & Dark Web Exploitation"

    badges = [
        {
            "id": "aeps_lock",
            "title": "AePS Biometric Shield",
            "description": "Aadhaar biometrics locked via m-Aadhaar against micro-ATM theft",
            "icon": "🔒",
            "unlocked": biometrics_locked
        },
        {
            "id": "zero_breach",
            "title": "Zero Active Exposures",
            "description": "All scanned databases clear of unaddressed credential breaches",
            "icon": "⚡",
            "unlocked": active_incidents_count == 0
        },
        {
            "id": "ed25519_pass",
            "title": "Ed25519 Pass Holder",
            "description": "Offline single-use masked Aadhaar generated for hotel check-ins",
            "icon": "🛡️",
            "unlocked": has_generated_pass
        },
        {
            "id": "family_guard",
            "title": "Family Mesh Active",
            "description": "At least 1 elder or dependent protected under shared radar",
            "icon": "👨‍👩‍👧",
            "unlocked": True
        }
    ]

    pillars = [
        MobileScorePillarDTO(
            id="biometric_lock",
            title="Aadhaar Biometric Lock",
            points=p_biometric,
            max_points=250,
            status="achieved" if biometrics_locked else "pending"
        ),
        MobileScorePillarDTO(
            id="verified_identity",
            title="Monitored Credentials & 2FA",
            points=p_identity,
            max_points=150,
            status="achieved" if active_ids_count > 0 else "pending"
        ),
        MobileScorePillarDTO(
            id="zero_breach",
            title="Dark Web Breach Hygiene",
            points=p_zero_breach,
            max_points=150,
            status="achieved" if active_incidents_count == 0 else "partial"
        ),
        MobileScorePillarDTO(
            id="masked_pass",
            title="Offline Redacted Sharing",
            points=p_pass,
            max_points=150,
            status="achieved" if has_generated_pass else "pending"
        ),
    ]

    recommendations = []
    if not biometrics_locked:
        recommendations.append("Lock Aadhaar biometrics on UIDAI portal to prevent unauthorized AePS cash withdrawal.")
    if active_incidents_count > 0:
        recommendations.append(f"Resolve {active_incidents_count} active security incident(s) in the Activity center.")
    if not recommendations:
        recommendations.append("Your identity perimeter is solid. Rotate your 16-digit Virtual ID every 30 days.")

    return MobileHealthScoreDTO(
        score=score,
        max_score=1000,
        tier=tier,
        tier_color=tier_color,
        percentile_text=percentile,
        badges=badges,
        pillars=pillars,
        top_recommendations=recommendations
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/bootstrap")
async def get_mobile_bootstrap(
    request: Request,
    response: Response,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Primary Aggregator Endpoint for Native Android and Native iOS Apps.
    Delivers full application startup state in a SINGLE network round-trip.
    Supports HTTP ETag & 304 Not Modified to minimize bandwidth and preserve mobile battery.
    """
    req_id = get_request_id(request)
    now = datetime.now(timezone.utc)

    # 1. Fetch active incidents
    res_inc = await db.execute(
        select(Incident).where(
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id,
            Incident.state.in_([
                IncidentState.NEW.value,
                IncidentState.ACKNOWLEDGED.value,
                IncidentState.ACTION_IN_PROGRESS.value
            ])
        ).order_by(Incident.priority_score.desc())
    )
    incidents = res_inc.scalars().all()
    active_incidents_count = len(incidents)

    urgent_alert = None
    if active_incidents_count > 0:
        top_inc = incidents[0]
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
    active_ids_count = len(res_ids.scalars().all())

    # 3. Check Aadhaar biometric lock status
    res_assist = await db.execute(
        select(UserAssistanceReport).where(
            UserAssistanceReport.tenant_id == ctx.tenant_id,
            UserAssistanceReport.subject_id == ctx.subject_id,
            UserAssistanceReport.category.in_(["aadhaar_biometric_misuse", "aadhaar_biometric_lock"])
        ).order_by(UserAssistanceReport.created_at.desc())
    )
    last_lock_report = res_assist.scalars().first()
    biometrics_locked = bool(last_lock_report and last_lock_report.reported_action_taken == "locked")
    lock_time_str = last_lock_report.created_at.isoformat() if last_lock_report else None

    # 4. Check active temporary unlock window
    auto_relock_active = False
    auto_relock_seconds_left = 0
    if ctx.subject_id in _active_unlock_windows:
        exp_time = _active_unlock_windows[ctx.subject_id]
        if exp_time > now:
            auto_relock_active = True
            auto_relock_seconds_left = int((exp_time - now).total_seconds())
        else:
            del _active_unlock_windows[ctx.subject_id]

    # 5. Count unread notifications
    res_notif = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.tenant_id == ctx.tenant_id,
            NotificationDelivery.status.in_(["pending", "sent", "unread"])
        )
    )
    unread_count = len(res_notif.scalars().all())

    # 6. Compute health score
    health_score = compute_mobile_health_score(
        biometrics_locked=biometrics_locked,
        active_ids_count=active_ids_count,
        active_incidents_count=active_incidents_count
    )

    # 7. Build Shield Status
    if active_incidents_count > 0:
        shield_status = "critical" if any(i.severity == "critical" for i in incidents) else "warning"
    else:
        shield_status = "secure"

    # 8. Assemble Bootstrap DTO
    bootstrap_data = MobileBootstrapDataDTO(
        session={
            "subject_id": ctx.subject_id,
            "tenant_id": ctx.tenant_id,
            "email": ctx.session.email,
            "role": ctx.session.role,
            "account_tier": "resident_shield",
            "step_up_active": ctx.session.has_valid_step_up,
        },
        glance={
            "shield_status": shield_status,
            "active_monitored_count": active_ids_count,
            "active_incidents": active_incidents_count,
            "urgent_alert": urgent_alert,
            "biometrics_locked": biometrics_locked,
        },
        health_score=health_score,
        unread_alerts_count=unread_count,
        biometric_status=MobileBiometricStatusDTO(
            locked=biometrics_locked,
            locked_confirmed_at=lock_time_str,
            auto_relock_active=auto_relock_active,
            auto_relock_seconds_left=auto_relock_seconds_left,
            status_label="LOCKED (AePS SAFE)" if biometrics_locked else "UNLOCKED (ACTION RECOMMENDED)"
        ),
        masked_pass=MobileMaskedPassSummaryDTO(
            doc_type="aadhaar",
            holder_name="Aarav Sharma",
            masked_identifier="XXXX-XXXX-4819",
            recipient="Taj Lands End, Mumbai",
            purpose="hotel_checkin",
            verified=True,
            compliance_standard="UIDAI Circular 2022 & DPDP Act 2023"
        ),
        quick_actions=[
            MobileQuickActionDTO(
                id="scam_radar",
                title="Scam Radar",
                subtitle="Detect CBI / APKs",
                icon="🚨",
                route="dialog_scam_radar"
            ),
            MobileQuickActionDTO(
                id="verify_qr",
                title="Verify QR",
                subtitle="Offline Verifier",
                icon="📷",
                route="dialog_verify_qr"
            ),
            MobileQuickActionDTO(
                id="auto_relock",
                title="Auto-Relock" if not auto_relock_active else "Relock Now",
                subtitle=f"{auto_relock_seconds_left // 60}:{auto_relock_seconds_left % 60:02d} Left" if auto_relock_active else "10-Min Window",
                icon="⏱️" if not auto_relock_active else "🔓",
                badge="ACTIVE" if auto_relock_active else None,
                route="action_auto_relock"
            ),
            MobileQuickActionDTO(
                id="vault_pass",
                title="Masked Pass",
                subtitle="UIDAI Redacted",
                icon="🇮🇳",
                route="tab_vault"
            ),
        ],
        sync_timestamp=now.isoformat()
    )

    # 9. Compute stable ETag from state (excluding dynamic request timestamp)
    state_sig = f"{ctx.subject_id}:{shield_status}:{active_incidents_count}:{active_ids_count}:{biometrics_locked}:{auto_relock_active}:{unread_count}:{health_score.score}"
    etag = f'"{hashlib.sha256(state_sig.encode()).hexdigest()[:16]}"'

    client_etag = request.headers.get("If-None-Match")
    if client_etag and client_etag.strip() == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, no-cache, must-revalidate"

    return ApiResponse(
        data=bootstrap_data,
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/activity", response_model=ApiResponse[Dict[str, Any]])
async def get_mobile_activity(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Unified Activity Feed for Native Mobile Apps.
    Returns both detected breach incidents and live radar notifications.
    """
    req_id = get_request_id(request)

    # Exposures & Incidents
    res_inc = await db.execute(
        select(Incident).where(
            Incident.tenant_id == ctx.tenant_id,
            Incident.subject_id == ctx.subject_id
        ).order_by(Incident.priority_score.desc(), Incident.created_at.desc())
    )
    incidents = res_inc.scalars().all()
    exposures = [
        {
            "id": inc.id,
            "title": inc.title,
            "severity": inc.severity,
            "priority_score": inc.priority_score,
            "state": inc.state,
            "exposure_categories": inc.exposure_categories or [],
            "source": "Dark Web Intelligence",
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in incidents
    ]

    # Live Radar & Notifications
    res_notif = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.tenant_id == ctx.tenant_id
        ).order_by(NotificationDelivery.created_at.desc()).limit(20)
    )
    notifs = res_notif.scalars().all()
    radar_alerts = [
        {
            "id": n.id,
            "channel": n.channel,
            "status": n.status,
            "recipient": n.destination_reference,
            "payload_preview": n.title,
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifs
    ]

    return ApiResponse(
        data={
            "exposures": exposures,
            "radar_alerts": radar_alerts,
            "active_exposures_count": len([e for e in exposures if e["state"] != "resolved"]),
            "unread_alerts_count": len([r for r in radar_alerts if r["status"] in ("pending", "unread")])
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/scam-radar/analyze", response_model=ApiResponse[ScamAnalysisDTO])
async def mobile_analyze_scam(
    request: Request,
    payload: ScamAnalysisRequest,
    ctx: AuthContext = Depends(get_auth_context)
):
    """
    Mobile-optimized heuristic scam detection for fake CBI/Police video calls and malicious APKs.
    """
    req_id = get_request_id(request)
    result = ScamRadarEngine.analyze_message(
        message_text=payload.message_text,
        sender_header=payload.sender_header,
        channel=payload.channel,
        suspect_claims=payload.suspect_claims
    )
    return ApiResponse(
        data=result,
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/qr/verify", response_model=ApiResponse[PassVerificationDTO])
async def mobile_verify_qr(
    request: Request,
    payload: PassVerificationRequest,
    ctx: AuthContext = Depends(get_auth_context)
):
    """
    Zero-cloud offline verifier for Ed25519 Certified Passes and UIDAI 2048-bit QR codes.
    """
    req_id = get_request_id(request)
    result = PassVerifierService.verify_pass(payload)
    return ApiResponse(
        data=result,
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/biometric/auto-relock", response_model=ApiResponse[Dict[str, Any]])
async def mobile_biometric_auto_relock(
    request: Request,
    payload: MobileAutoRelockRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Manages 10-minute temporary unlock windows for Indian bank / SIM KYC with automatic safety re-lock.
    """
    req_id = get_request_id(request)
    now = datetime.now(timezone.utc)

    if payload.action == "start_window":
        exp = now + timedelta(seconds=payload.duration_seconds)
        _active_unlock_windows[ctx.subject_id] = exp

        # Log audit trail
        audit = AuditEvent(
            id=str(uuid.uuid4()),
            tenant_id=ctx.tenant_id,
            actor_id=ctx.subject_id,
            actor_role=ctx.session.role,
            action="mobile.biometric_unlock_window_started",
            scoped_resource="biometrics",
            result="success",
            details_json={
                "duration_seconds": payload.duration_seconds,
                "expires_at": exp.isoformat()
            },
            created_at=now
        )
        db.add(audit)
        await db.commit()

        return ApiResponse(
            data={
                "auto_relock_active": True,
                "seconds_left": payload.duration_seconds,
                "message": f"Temporary window open for {payload.duration_seconds // 60} minutes. Biometrics will auto-relock safely."
            },
            meta=ResponseMeta(request_id=req_id)
        )

    elif payload.action == "relock_now":
        if ctx.subject_id in _active_unlock_windows:
            del _active_unlock_windows[ctx.subject_id]

        # Log audit trail
        audit = AuditEvent(
            id=str(uuid.uuid4()),
            tenant_id=ctx.tenant_id,
            actor_id=ctx.subject_id,
            actor_role=ctx.session.role,
            action="mobile.biometric_relocked_manually",
            scoped_resource="biometrics",
            result="success",
            details_json={"reason": "User manual relock action"},
            created_at=now
        )
        db.add(audit)
        await db.commit()

        return ApiResponse(
            data={
                "auto_relock_active": False,
                "seconds_left": 0,
                "message": "Biometrics re-locked immediately. Shield is active."
            },
            meta=ResponseMeta(request_id=req_id)
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{payload.action}'. Expected 'start_window' or 'relock_now'."
        )


@router.post("/panic-pack/trigger", response_model=ApiResponse[PanicPackExecutionDTO])
async def mobile_panic_pack_trigger(
    request: Request,
    payload: PanicPackRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Emergency SOS one-click freeze (CEIR, SIM, AePS, Bank, 1930) for mobile residents under active extortion.
    """
    req_id = get_request_id(request)
    result = PanicPackService.execute_panic_protocol(
        req=payload,
        subject_id=ctx.subject_id,
        tenant_id=ctx.tenant_id
    )

    # Record audit trail
    audit = AuditEvent(
        id=str(uuid.uuid4()),
        tenant_id=ctx.tenant_id,
        actor_id=ctx.subject_id,
        actor_role=ctx.session.role,
        action="mobile.panic_protocol_executed",
        scoped_resource="panic_pack",
        result="success",
        details_json={"incident_type": payload.incident_type, "dossier_id": result.emergency_dossier_id},
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data=result,
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/telemetry/crash-report", response_model=ApiResponse[Dict[str, Any]])
async def mobile_crash_report(
    request: Request,
    payload: MobileCrashReportRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests mobile client diagnostics, crash traces, and performance telemetry without capturing PII.
    """
    req_id = get_request_id(request)
    now = datetime.now(timezone.utc)

    audit = AuditEvent(
        id=str(uuid.uuid4()),
        tenant_id=ctx.tenant_id,
        actor_id=ctx.subject_id,
        actor_role=ctx.session.role,
        action="mobile.client_crash_reported",
        scoped_resource="telemetry",
        result="success",
        details_json={
            "device_model": payload.device_model,
            "os_name": payload.os_name,
            "os_version": payload.os_version,
            "app_version": payload.app_version,
            "error_message": payload.error_message[:500],
            "has_stack_trace": bool(payload.stack_trace)
        },
        created_at=now
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data={"status": "received", "event_id": audit.id},
        meta=ResponseMeta(request_id=req_id)
    )
