"""
India-specific Identity Assistance module (Aadhaar & PAN).
Strictly complies with FR-025 and ADR-010: Guidance-only protective workflows,
no government scraping, no OTP capture, and no unsupported tracking claims.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import (
    UserAssistanceReport,
    AuditEvent,
    Incident,
    OutboxEvent,
    Identifier,
    RemediationAction,
)
from packages.security.authorization import AuthContext
from packages.security.crypto import vault
from packages.redaction.sanitizer import redact_sensitive_secrets
from packages.domain.verhoeff import CANARY_TEST_PRESETS, validate_aadhaar, validate_pan
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
    AssistanceGuideDTO,
    AssistanceReportRequest,
    AssistanceReportDTO,
)

router = APIRouter(prefix="/identity-assistance", tags=["identity-assistance"])


APPROVED_GUIDES = [
    AssistanceGuideDTO(
        id="guide_aadhaar_biometric_lock",
        topic="Aadhaar Biometric Locking",
        official_authority="Unique Identification Authority of India (UIDAI)",
        portal_url="https://myaadhaar.uidai.gov.in/",
        steps=[
            "Visit the official UIDAI myAadhaar resident portal (https://myaadhaar.uidai.gov.in).",
            "Log in using your Aadhaar number and OTP received on your UIDAI-registered mobile number.",
            "Navigate to the 'Lock/Unlock Biometrics' service.",
            "Enable Biometric Lock. Once locked, fingerprint and iris authentication cannot be performed by anyone until you temporarily unlock it.",
            "Record your action in this dashboard to track your protective status."
        ],
        protective_action="biometric_lock"
    ),
    AssistanceGuideDTO(
        id="guide_aadhaar_auth_history",
        topic="Audit Aadhaar Authentication History",
        official_authority="Unique Identification Authority of India (UIDAI)",
        portal_url="https://myaadhaar.uidai.gov.in/",
        steps=[
            "Log in to the official myAadhaar portal using your registered credentials.",
            "Select 'Aadhaar Authentication History'.",
            "Filter for the desired period (up to 6 months of historical transactions).",
            "Review transaction types (Biometric, Demographic, OTP) and Requesting Entity Names (AUAs).",
            "If any unauthorized or suspicious transaction is discovered, report it immediately to UIDAI (1947 or help@uidai.gov.in) and file a record in this tracker."
        ],
        protective_action="auth_history_audit"
    ),
    AssistanceGuideDTO(
        id="guide_aadhaar_vid",
        topic="Generate Virtual ID (VID)",
        official_authority="Unique Identification Authority of India (UIDAI)",
        portal_url="https://myaadhaar.uidai.gov.in/",
        steps=[
            "Log in to myAadhaar portal or mAadhaar app.",
            "Select 'Generate Virtual ID (VID)'.",
            "A temporary, revocable 16-digit VID will be generated.",
            "Use this 16-digit VID instead of your permanent 12-digit Aadhaar number for KYC verifications."
        ],
        protective_action="generate_vid"
    ),
    AssistanceGuideDTO(
        id="guide_pan_misuse_prevention",
        topic="PAN Safety & Fraud Reporting",
        official_authority="Income Tax Department / NSDL / Protean",
        portal_url="https://www.incometax.gov.in/",
        steps=[
            "Never share clear photocopies of your PAN card without self-attesting the specific purpose and date across the document.",
            "Check your Annual Information Statement (AIS) and Form 26AS regularly via the Income Tax e-Filing portal to detect unauthorized financial transactions mapped to your PAN.",
            "Check your credit report (CIBIL / Experian) for unauthorized loans or credit inquiries.",
            "If fraudulent activity is detected, file a grievance via the Income Tax e-Filing portal and report cybercrime at https://cybercrime.gov.in."
        ],
        protective_action="pan_monitoring_review"
    ),
]


@router.get("/capabilities")
async def get_assistance_capabilities(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    req_id = get_request_id(request)
    return ApiResponse(
        data={
            "aadhaar_guidance_available": True,
            "pan_guidance_available": True,
            "user_activity_reporting": True,
            "automated_scraping_enabled": False,  # Strictly false by policy
            "pan_partner_verification_status": "disabled_pending_partner_certification"
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/guides")
async def list_guides(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    req_id = get_request_id(request)
    return ApiListResponse(
        data=APPROVED_GUIDES,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_assistance_report(
    payload: AssistanceReportRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Files structured, user-reported suspicious activity (e.g. unsolicited OTPs, unauthorized history entries).
    Redacts any sensitive passwords or raw biometrics from text before persisting.
    """
    req_id = get_request_id(request)
    sanitized_desc = redact_sensitive_secrets(payload.description)

    report = UserAssistanceReport(
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        category=payload.category,
        description_redacted=sanitized_desc,
        reported_action_taken=payload.reported_action_taken,
        provenance="user_reported"
    )
    db.add(report)

    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="assistance.report_filed",
        scoped_resource=f"report:{report.id}",
        result="success",
        details_json={"category": payload.category}
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data=AssistanceReportDTO(
            id=report.id,
            category=report.category,
            description_redacted=report.description_redacted,
            reported_action_taken=report.reported_action_taken,
            provenance=report.provenance,
            created_at=report.created_at
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/reports")
async def list_reports(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(UserAssistanceReport).where(
            UserAssistanceReport.tenant_id == ctx.tenant_id,
            UserAssistanceReport.subject_id == ctx.subject_id
        ).order_by(UserAssistanceReport.created_at.desc())
    )
    reports = res.scalars().all()
    dtos = [
        AssistanceReportDTO(
            id=r.id,
            category=r.category,
            description_redacted=r.description_redacted,
            reported_action_taken=r.reported_action_taken,
            provenance=r.provenance,
            created_at=r.created_at
        )
        for r in reports
    ]
    return ApiListResponse(
        data=dtos,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/actions/{id}/confirm")
async def confirm_assistance_action(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Allows user to record that they successfully performed an official protective action."""
    req_id = get_request_id(request)
    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="assistance.action_confirmed_by_user",
        scoped_resource=f"guide:{id}",
        result="success",
        details_json={"action_id": id, "provenance": "user_reported"}
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data={"action_id": id, "status": "confirmed_by_user", "timestamp": datetime.now(timezone.utc).isoformat()},
        meta=ResponseMeta(request_id=req_id)
    )


class CanaryTestRequest(BaseModel):
    preset_id: Optional[str] = Field(None, description="Preset sandbox identity ID (e.g. aadhaar_sandbox_1)")
    custom_identifier: Optional[str] = Field(None, description="Custom 12-digit Aadhaar or 10-char PAN to test")
    leak_scenario: Optional[str] = Field(default="darkweb_market", description="Leak scenario: darkweb_market, infostealer_log, whatsapp_leak, or telecom_breach")


@router.get("/canary-presets", response_model=ApiResponse)
async def get_canary_presets(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    """
    Returns valid official test Aadhaar and PAN numbers configured for developer/auditor testing.
    All test Aadhaar numbers pass mathematical Verhoeff checksum validation.
    """
    req_id = get_request_id(request)
    return ApiResponse(
        data={"presets": CANARY_TEST_PRESETS},
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/canary-test", response_model=ApiResponse)
async def execute_canary_test(
    payload: CanaryTestRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes an end-to-end simulated tracking and exposure lifecycle for an Aadhaar or PAN number.
    Validates formatting & Verhoeff algorithm, performs AES-256-GCM envelope encryption,
    generates an HMAC-SHA256 blind index, synthesizes breach intelligence, publishes outbox events,
    and returns the created Incident and protective remediation checklist.
    """
    req_id = get_request_id(request)
    id_val = None
    id_type = None
    masked_val = None
    desc_extra = ""

    if payload.preset_id:
        preset = next((p for p in CANARY_TEST_PRESETS if p["id"] == payload.preset_id), None)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{payload.preset_id}' not found. Available presets: {[p['id'] for p in CANARY_TEST_PRESETS]}"
            )
        id_val = preset["identifier"]
        id_type = preset["type"]
        masked_val = preset["masked"]
        desc_extra = f"Preset: {preset['label']}. {preset['description']}."
    elif payload.custom_identifier:
        raw = payload.custom_identifier.strip()
        clean_digits = "".join(filter(str.isdigit, raw))
        if len(clean_digits) == 12:
            is_valid, err_msg, masked = validate_aadhaar(raw)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)
            id_val = clean_digits
            id_type = "aadhaar"
            masked_val = masked
        elif len(raw.replace(" ", "")) == 10:
            is_valid, err_msg, masked = validate_pan(raw)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)
            id_val = raw.upper()
            id_type = "pan"
            masked_val = masked
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Custom identifier must be a valid 12-digit Aadhaar number (with valid Verhoeff checksum) or a 10-char PAN."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'preset_id' or 'custom_identifier' must be provided."
        )

    # 1. Cryptographic Envelope Encryption & Blind Index
    encrypted_envelope = vault.encrypt(id_val, associated_data=ctx.tenant_id)
    blind_index = vault.compute_blind_index(id_val, scope=ctx.tenant_id)

    # 2. Scenario Mapping
    scenario_sources = {
        "darkweb_market": ("Dark Web Intelligence Feed (Flare / Tor)", "critical", 95, "Identity credentials and unmasked documents found on underground market."),
        "infostealer_log": ("Infostealer Malware Exfiltration (Lumma/Vidar)", "critical", 92, "Browser autofill and cached identity documents harvested by malware."),
        "whatsapp_leak": ("WhatsApp Insecure Chat Forward", "high", 88, "Unmasked identity document forwarded in unencrypted chat screenshot or dump."),
        "telecom_breach": ("Enterprise Telecom KYC Breach", "high", 85, "Bulk customer database exposed on dark web containing customer KYC records.")
    }
    src_name, severity, prio, scen_desc = scenario_sources.get(
        payload.leak_scenario or "darkweb_market",
        scenario_sources["darkweb_market"]
    )

    incident_id = f"inc_canary_{uuid.uuid4().hex[:10]}"
    grouping_key = f"canary:{id_type}:{blind_index[:16]}"
    now = datetime.now(timezone.utc)

    # 3. Ensure an identifier exists for this subject
    res = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id,
            Identifier.blind_index == blind_index
        )
    )
    ident = res.scalar_one_or_none()
    if not ident:
        ident = Identifier(
            id=f"ident_{uuid.uuid4().hex[:12]}",
            tenant_id=ctx.tenant_id,
            subject_id=ctx.subject_id,
            type=id_type,
            encrypted_value=encrypted_envelope,
            blind_index=blind_index,
            masked_value=masked_val,
            state="verified"
        )
        db.add(ident)
        await db.flush()

    # 4. Create Incident Record
    incident = Incident(
        id=incident_id,
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        incident_grouping_key=grouping_key,
        title=f"Exposed {id_type.upper()} Document Detected ({masked_val})",
        severity=severity,
        confidence="confirmed",
        state="new",
        identifier_id=ident.id,
        exposure_categories=["government_id", "identity_document", id_type],
        priority_score=prio,
        event_occurred_at=now,
        first_detected_at=now
    )
    db.add(incident)
    await db.flush()

    # 5. Add Remediation Actions
    actions = [
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="biometric_lock" if id_type == "aadhaar" else "check_ais_income_tax",
            title=f"Lock {id_type.upper()} Biometrics on myAadhaar" if id_type == "aadhaar" else "Check Annual Information Statement (AIS)",
            description="Visit https://myaadhaar.uidai.gov.in/ and enable biometric lock." if id_type == "aadhaar" else "Review AIS/Form 26AS on Income Tax e-filing portal.",
            state="pending"
        ),
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="generate_vid" if id_type == "aadhaar" else "check_cibil_loans",
            title="Generate 16-Digit Virtual ID (VID)" if id_type == "aadhaar" else "Check CIBIL Credit Report for Unauthorized Inquiries",
            description="Generate a temporary revocable 16-digit VID via mAadhaar app." if id_type == "aadhaar" else "Review credit bureau files for unrecognized loans.",
            state="pending"
        )
    ]
    for act in actions:
        db.add(act)

    # 6. Enqueue Transactional Outbox Event
    outbox_event = OutboxEvent(
        id=f"evt_canary_{uuid.uuid4().hex[:12]}",
        event_id=f"evt_{uuid.uuid4().hex[:16]}",
        event_type="incident.detected",
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        resource_id=incident.id,
        authorization_version=1,
        payload={
            "incident_id": incident.id,
            "type": id_type,
            "masked_identifier": masked_val,
            "scenario": payload.leak_scenario,
            "priority_score": prio,
            "source": src_name,
            "timestamp": now.isoformat()
        },
        retry_count=0
    )
    db.add(outbox_event)

    # 7. Immutable Audit Trail
    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="canary.test_executed",
        scoped_resource=f"incident:{incident.id}",
        result="success",
        details_json={
            "identifier_type": id_type,
            "masked": masked_val,
            "scenario": payload.leak_scenario
        }
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data={
            "test_status": "success",
            "pipeline_trace": [
                {"stage": "1. Format & Verhoeff Validation", "status": "PASSED", "details": f"Valid {id_type.upper()} format and mathematical checksum."},
                {"stage": "2. Zero-Plaintext Envelope Vault", "status": "ENCRYPTED", "details": f"AES-256-GCM Envelope: {encrypted_envelope[:28]}..."},
                {"stage": "3. Blind Index Generation", "status": "INDEXED", "details": f"HMAC-SHA256: {blind_index}"},
                {"stage": "4. Dark Web & CTI Synthesis", "status": "MATCHED", "details": f"Matched scenario '{payload.leak_scenario}' against {src_name}."},
                {"stage": "5. Transactional Outbox Enqueue", "status": "QUEUED", "details": f"Outbox Event {outbox_event.id} enqueued."},
                {"stage": "6. Incident Created in Dashboard", "status": "CREATED", "details": f"Incident {incident.id} generated with priority {prio}."}
            ],
            "masked_identifier": masked_val,
            "incident_id": incident.id,
            "severity": severity,
            "priority_score": prio,
            "remediation_checklist": [f"{act.title}: {act.description}" for act in actions]
        },
        meta=ResponseMeta(request_id=req_id)
    )
