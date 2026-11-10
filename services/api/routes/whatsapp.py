"""
WhatsApp Integration & Data Loss Prevention (DLP) Route.
Handles incoming WhatsApp Business Webhooks (Meta Cloud API / Twilio) and
simulates/detects unmasked Aadhaar or PAN sharing in messaging platforms.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import Incident, OutboxEvent, AuditEvent, Identifier, RemediationAction, NotificationDelivery
from packages.security.authorization import AuthContext
from packages.security.crypto import vault
from packages.domain.verhoeff import detect_identifiers_in_text, validate_aadhaar, validate_pan
from packages.domain.schemas import ApiResponse, ResponseMeta

router = APIRouter(prefix="/integrations/whatsapp", tags=["whatsapp-dlp"])


class WhatsAppSimulateShareRequest(BaseModel):
    message_text: str = Field(..., description="Message content to scan for unmasked Aadhaar or PAN")
    sender_phone: Optional[str] = Field(default="+919876543210", description="Sender WhatsApp phone number")
    recipient_phone: Optional[str] = Field(default="+919876500000", description="Recipient phone or group name")
    channel: Optional[str] = Field(default="whatsapp_direct", description="Sharing channel: whatsapp_direct, whatsapp_group, or forward")


class WhatsAppSimulateShareResponse(BaseModel):
    detected: bool
    summary: str
    findings: Dict[str, List[Dict[str, str]]]
    automated_whatsapp_alert: Optional[str] = None
    incident_created: bool = False
    incident_id: Optional[str] = None
    remediation_checklist: List[str] = []


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    redaction_label: str


class WhatsAppMediaShareRequest(BaseModel):
    media_type: str = Field(default="image/jpeg", description="MIME type: image/jpeg, image/png, application/pdf")
    file_name: str = Field(default="aadhaar_card_photo.jpg", description="Name of shared image or document")
    ocr_text_sample: Optional[str] = Field(
        default="GOVERNMENT OF INDIA\nUnique Identification Authority of India\nEnrollment No: 1234/56789/12345\n9999 4105 7058\nMERA AADHAAR, MERI PEHCHAAN",
        description="Text extracted from image via on-device ML Kit / Vision OCR"
    )
    sender_phone: Optional[str] = Field(default="+919876543210")
    channel: Optional[str] = Field(default="whatsapp_media_photo")


class WhatsAppMediaShareResponse(BaseModel):
    detected: bool
    document_type: str
    extracted_identifiers: List[str]
    redaction_coordinates: List[BoundingBox]
    masked_aadhaar_recommendation: str
    automated_whatsapp_alert: str
    incident_id: str
    remediation_checklist: List[str]


@router.get("/webhook")
async def verify_whatsapp_webhook(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Standard Meta WhatsApp Cloud API webhook challenge handshake.
    """
    expected_token = "suraksha_secure_whatsapp_token_2026"
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=hub_challenge or "OK", media_type="text/plain")
    if hub_challenge:
        return Response(content=hub_challenge, media_type="text/plain")
    return {"status": "ready", "webhook": "whatsapp_meta_cloud_api"}


@router.post("/simulate-share", response_model=ApiResponse)
async def simulate_whatsapp_share(
    payload: WhatsAppSimulateShareRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulates or inspects sharing of text across WhatsApp.
    Detects unmasked Aadhaar (via Verhoeff algorithm) and PAN numbers.
    Dispatches automated WhatsApp security alerts and creates an in-app Incident.
    """
    req_id = get_request_id(request)
    findings = detect_identifiers_in_text(payload.message_text)
    has_aadhaar = len(findings.get("aadhaar", [])) > 0
    has_pan = len(findings.get("pan", [])) > 0

    if not has_aadhaar and not has_pan:
        data = WhatsAppSimulateShareResponse(
            detected=False,
            summary="No sensitive government identifiers detected in message text.",
            findings=findings,
            incident_created=False,
            remediation_checklist=[]
        )
        return ApiResponse(data=data.model_dump(), meta=ResponseMeta(request_id=req_id))

    # Format findings and compose automated WhatsApp alert message
    detected_items = []
    masked_summaries = []
    for a in findings.get("aadhaar", []):
        detected_items.append(f"• Aadhaar Number: {a['masked']}")
        masked_summaries.append(a['masked'])
    for p in findings.get("pan", []):
        detected_items.append(f"• PAN: {p['masked']}")
        masked_summaries.append(p['masked'])

    items_str = "\n".join(detected_items)
    automated_alert = (
        f"⚠️ *SURAKSHA SECURITY ALERT: SENSITIVE ID DETECTED ON WHATSAPP*\n\n"
        f"An unmasked government identifier was detected in your WhatsApp transmission:\n"
        f"{items_str}\n\n"
        f"🔒 *Immediate Protective Actions*:\n"
        f"1. Delete this message ('Delete for Everyone') immediately to prevent unauthorized caching.\n"
        f"2. Never share full 12-digit Aadhaar. Use official UIDAI Masked Aadhaar or a 16-digit Virtual ID (VID).\n"
        f"3. Lock your biometrics on UIDAI: https://myaadhaar.uidai.gov.in/\n"
        f"4. View your incident details in Suraksha Dashboard: http://localhost:8000/app#incidents"
    )

    # Ensure an identifier exists for this subject
    res = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        ).limit(1)
    )
    ident = res.scalar_one_or_none()
    if not ident:
        ident_phone = payload.sender_phone or "+919876543210"
        ident = Identifier(
            id=f"ident_{uuid.uuid4().hex[:12]}",
            tenant_id=ctx.tenant_id,
            subject_id=ctx.subject_id,
            type="aadhaar" if has_aadhaar else "pan",
            encrypted_value=vault.encrypt(ident_phone, associated_data=ctx.tenant_id),
            blind_index=vault.compute_blind_index(ident_phone, scope=ctx.tenant_id),
            masked_value=masked_summaries[0],
            state="verified"
        )
        db.add(ident)
        await db.flush()

    incident_id = f"inc_wa_{uuid.uuid4().hex[:10]}"
    grouping_key = f"whatsapp:{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    # Create tracked incident in database
    incident = Incident(
        id=incident_id,
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        incident_grouping_key=grouping_key,
        title=f"Insecure WhatsApp Transmission ({', '.join(masked_summaries)})",
        severity="high" if has_aadhaar else "medium",
        confidence="confirmed",
        state="new",
        identifier_id=ident.id,
        exposure_categories=["messaging_leak", "whatsapp_dlp", "government_id"],
        priority_score=88 if has_aadhaar else 75,
        event_occurred_at=now,
        first_detected_at=now
    )
    db.add(incident)
    await db.flush()

    # Add actionable remediation items
    actions = [
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="delete_message",
            title="Delete WhatsApp Message for Everyone",
            description="Delete the WhatsApp message containing the unmasked identity number to prevent further caching.",
            state="pending"
        ),
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="biometric_lock",
            title="Lock Aadhaar Biometrics on myAadhaar",
            description="Enable UIDAI Biometric Lock at https://myaadhaar.uidai.gov.in/ to prevent physical fingerprint spoofing.",
            state="pending"
        )
    ]
    for act in actions:
        db.add(act)

    # Enqueue Outbox event to notify user via notification worker
    outbox_event = OutboxEvent(
        id=f"evt_wa_{uuid.uuid4().hex[:12]}",
        event_id=f"evt_{uuid.uuid4().hex[:16]}",
        event_type="incident.detected",
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        resource_id=incident.id,
        authorization_version=1,
        payload={
            "incident_id": incident.id,
            "channel": "whatsapp_dlp",
            "sender_phone": payload.sender_phone,
            "detected_identifiers": masked_summaries,
            "severity": incident.severity,
            "priority_score": incident.priority_score,
            "timestamp": now.isoformat()
        },
        retry_count=0
    )
    db.add(outbox_event)

    # Record immediate citizen notifications for mobile app and WhatsApp channel
    delivery_wa = NotificationDelivery(
        tenant_id=ctx.tenant_id,
        notification_intent_id=outbox_event.event_id,
        channel="whatsapp_dlp",
        destination_reference=payload.sender_phone or "+919876543210",
        title=f"⚠️ WhatsApp Alert: Unmasked {', '.join(masked_summaries)} Detected",
        body_sanitized=f"Unmasked government identifier detected in WhatsApp transmission ({', '.join(masked_summaries)}). Delete for everyone and lock biometrics immediately.",
        status="sent"
    )
    delivery_push = NotificationDelivery(
        tenant_id=ctx.tenant_id,
        notification_intent_id=f"push_{outbox_event.event_id}",
        channel="push_mobile_wearable",
        destination_reference=f"device_token_subject_{ctx.subject_id}",
        title=f"🛡️ [HIGH] WhatsApp Sharing Alert ({', '.join(masked_summaries)})",
        body_sanitized=f"Unmasked government identifier shared via WhatsApp message. Review recommended remediation in dashboard.",
        status="sent"
    )
    db.add(delivery_wa)
    db.add(delivery_push)

    # Log immutable audit event
    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="whatsapp.dlp_violation_detected",
        scoped_resource=f"incident:{incident.id}",
        result="warning",
        details_json={
            "channel": payload.channel,
            "identifiers_masked": masked_summaries
        }
    )
    db.add(audit)
    await db.commit()

    remediation = [
        "Delete the WhatsApp message for all recipients immediately.",
        "Enable UIDAI Biometric Lock at https://myaadhaar.uidai.gov.in.",
        "Generate a 16-digit Virtual ID (VID) via the mAadhaar app.",
        "Review your recent Aadhaar authentication history."
    ]

    response_data = WhatsAppSimulateShareResponse(
        detected=True,
        summary=f"Detected {len(masked_summaries)} unmasked identifier(s) shared on WhatsApp.",
        findings=findings,
        automated_whatsapp_alert=automated_alert,
        incident_created=True,
        incident_id=incident.id,
        remediation_checklist=remediation
    )

    return ApiResponse(data=response_data.model_dump(), meta=ResponseMeta(request_id=req_id))


@router.post("/simulate-media-share", response_model=ApiResponse)
async def simulate_whatsapp_media_share(
    payload: WhatsAppMediaShareRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulates detection and automated masking of Aadhaar/PAN cards shared as images or PDFs.
    Models on-device OCR (Google ML Kit / Apple Vision) scanning, Verhoeff checksum validation,
    bounding box redaction coordinates for creating a compliant Masked Aadhaar image,
    and automated WhatsApp security advisories.
    """
    req_id = get_request_id(request)
    ocr_text = payload.ocr_text_sample or ""
    findings = detect_identifiers_in_text(ocr_text)
    has_aadhaar = len(findings.get("aadhaar", [])) > 0
    has_pan = len(findings.get("pan", [])) > 0

    if not has_aadhaar and not has_pan:
        data = {
            "detected": False,
            "document_type": "unknown",
            "extracted_identifiers": [],
            "redaction_coordinates": [],
            "masked_aadhaar_recommendation": "No government identifiers detected in media file.",
            "automated_whatsapp_alert": "No sensitive document detected in media attachment.",
            "incident_id": "",
            "remediation_checklist": []
        }
        return ApiResponse(data=data, meta=ResponseMeta(request_id=req_id))

    masked_summaries = []
    for a in findings.get("aadhaar", []):
        masked_summaries.append(a['masked'])
    for p in findings.get("pan", []):
        masked_summaries.append(p['masked'])

    doc_type = "aadhaar_card" if has_aadhaar else "pan_card"
    
    # Calculate bounding box redaction coordinates for the image
    # In a real mobile app, this overlays a solid black rectangle over the first 8 digits
    redaction_coords = []
    if has_aadhaar:
        redaction_coords.append(
            BoundingBox(
                x=140,
                y=380,
                width=240,
                height=45,
                redaction_label="Mask First 8 Digits (XXXX XXXX)"
            )
        )
        redaction_coords.append(
            BoundingBox(
                x=420,
                y=180,
                width=160,
                height=160,
                redaction_label="Mask 2048-bit Biometric QR Code"
            )
        )

    incident_id = f"inc_img_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc)

    # Ensure an identifier exists for this subject
    res = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        ).limit(1)
    )
    ident = res.scalar_one_or_none()
    if not ident:
        ident_phone = payload.sender_phone or "+919876543210"
        ident = Identifier(
            id=f"ident_{uuid.uuid4().hex[:12]}",
            tenant_id=ctx.tenant_id,
            subject_id=ctx.subject_id,
            type="aadhaar" if has_aadhaar else "pan",
            encrypted_value=vault.encrypt(ident_phone, associated_data=ctx.tenant_id),
            blind_index=vault.compute_blind_index(ident_phone, scope=ctx.tenant_id),
            masked_value=masked_summaries[0],
            state="verified"
        )
        db.add(ident)
        await db.flush()

    # Create incident in database with CRITICAL severity (photo card exposes biometric face, DOB, address)
    incident = Incident(
        id=incident_id,
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        incident_grouping_key=f"image_dlp:{uuid.uuid4().hex[:12]}",
        title=f"Unmasked {doc_type.replace('_', ' ').title()} Image Shared on WhatsApp ({', '.join(masked_summaries)})",
        severity="critical" if has_aadhaar else "high",
        confidence="confirmed",
        state="new",
        identifier_id=ident.id,
        exposure_categories=["image_leak", "photo_id", "whatsapp_dlp", doc_type],
        priority_score=95 if has_aadhaar else 88,
        event_occurred_at=now,
        first_detected_at=now
    )
    db.add(incident)
    await db.flush()

    # Remediation actions
    actions = [
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="delete_whatsapp_media",
            title="Delete Image in WhatsApp ('Delete for Everyone')",
            description="Use WhatsApp 'Delete for Everyone' before the image is downloaded to recipient device galleries.",
            state="pending"
        ),
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="use_masked_aadhaar",
            title="Replace with UIDAI Official Masked Aadhaar",
            description="Download an official Masked Aadhaar from https://myaadhaar.uidai.gov.in displaying only XXXX-XXXX-1234.",
            state="pending"
        ),
        RemediationAction(
            tenant_id=ctx.tenant_id,
            incident_id=incident.id,
            action_type="biometric_lock",
            title="Lock Biometrics on myAadhaar Portal",
            description="Prevent fingerprint/face authentication abuse by enabling biometric lock at https://myaadhaar.uidai.gov.in.",
            state="pending"
        )
    ]
    for act in actions:
        db.add(act)

    # Enqueue Outbox Event
    outbox_event = OutboxEvent(
        id=f"evt_img_{uuid.uuid4().hex[:12]}",
        event_id=f"evt_{uuid.uuid4().hex[:16]}",
        event_type="incident.detected",
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        resource_id=incident.id,
        authorization_version=1,
        payload={
            "incident_id": incident.id,
            "media_type": payload.media_type,
            "file_name": payload.file_name,
            "detected_identifiers": masked_summaries,
            "severity": incident.severity,
            "priority_score": incident.priority_score,
            "timestamp": now.isoformat()
        },
        retry_count=0
    )
    db.add(outbox_event)

    # Multi-Surface Notifications
    delivery_wa = NotificationDelivery(
        tenant_id=ctx.tenant_id,
        notification_intent_id=outbox_event.event_id,
        channel="whatsapp_dlp",
        destination_reference=payload.sender_phone or "+919876543210",
        title=f"⚠️ Critical Alert: Unmasked {doc_type.upper()} Photo Shared",
        body_sanitized=f"Unmasked physical identity card photo detected ({', '.join(masked_summaries)}). Full facial photo, DOB, and 12-digit number are exposed. Delete immediately.",
        status="sent"
    )
    delivery_push = NotificationDelivery(
        tenant_id=ctx.tenant_id,
        notification_intent_id=f"push_{outbox_event.event_id}",
        channel="push_mobile_wearable",
        destination_reference=f"device_token_subject_{ctx.subject_id}",
        title=f"🚨 [CRITICAL] Identity Card Photo Shared on WhatsApp",
        body_sanitized=f"Raw image leak of {doc_type.replace('_', ' ').title()} ({', '.join(masked_summaries)}). Auto-masking recommended.",
        status="sent"
    )
    db.add(delivery_wa)
    db.add(delivery_push)

    # Immutable Audit Log
    audit = AuditEvent(
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        actor_role=ctx.role,
        action="whatsapp.media_dlp_violation_detected",
        scoped_resource=f"incident:{incident.id}",
        result="warning",
        details_json={
            "file_name": payload.file_name,
            "media_type": payload.media_type,
            "identifiers_masked": masked_summaries
        }
    )
    db.add(audit)
    await db.commit()

    automated_alert = (
        f"⚠️ *SURAKSHA SECURITY ALERT: SENSITIVE ID CARD DETECTED IN IMAGE*\n\n"
        f"An unmasked photo/scan of a physical {doc_type.replace('_', ' ').title()} was shared ({payload.file_name}):\n"
        f"• Number: {', '.join(masked_summaries)}\n"
        f"• Risk: Full raw biometric photo, date of birth, home address, and 12-digit number are exposed in image form.\n\n"
        f"🔒 *UIDAI-Compliant Protective Actions*:\n"
        f"1. Delete this image ('Delete for Everyone') in WhatsApp immediately.\n"
        f"2. Use Suraksha Auto-Mask or download official Masked Aadhaar from UIDAI.\n"
        f"3. Lock your biometrics on UIDAI: https://myaadhaar.uidai.gov.in/\n"
        f"4. View details in Suraksha Dashboard: http://localhost:8000/app#incidents"
    )

    checklist = [
        "Delete the image for all recipients ('Delete for Everyone') immediately in WhatsApp.",
        "Ensure the image is not backed up in unencrypted Google Drive or iCloud WhatsApp chats.",
        "Use official Masked Aadhaar (XXXX-XXXX-1234) for hotel check-ins and travel.",
        "Lock your biometrics at https://myaadhaar.uidai.gov.in."
    ]

    response_data = WhatsAppMediaShareResponse(
        detected=True,
        document_type=doc_type,
        extracted_identifiers=masked_summaries,
        redaction_coordinates=redaction_coords,
        masked_aadhaar_recommendation="UIDAI circular 2022 advises citizens to share only Masked Aadhaar displaying the last 4 digits.",
        automated_whatsapp_alert=automated_alert,
        incident_id=incident.id,
        remediation_checklist=checklist
    )

    return ApiResponse(data=response_data.model_dump(), meta=ResponseMeta(request_id=req_id))
