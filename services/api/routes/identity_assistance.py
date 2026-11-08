"""
India-specific Identity Assistance module (Aadhaar & PAN).
Strictly complies with FR-025 and ADR-010: Guidance-only protective workflows,
no government scraping, no OTP capture, and no unsupported tracking claims.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import UserAssistanceReport, AuditEvent
from packages.security.authorization import AuthContext
from packages.redaction.sanitizer import redact_sensitive_secrets
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
