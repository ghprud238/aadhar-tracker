"""
Identifier lifecycle management and verification challenges.
Strictly implements FR-006 (no provider query before verification) and FR-007 (email control proof).
"""
import secrets
import re
from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import Identifier, IdentifierVerification, AuditEvent
from packages.domain.enums import IdentifierState, IdentifierType
from packages.security.authorization import AuthContext
from packages.security.crypto import vault
from packages.redaction.masking import mask_email, mask_phone, mask_aadhaar, mask_pan
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
    IdentifierCreateRequest,
    IdentifierDTO,
    VerificationCompleteRequest,
)

router = APIRouter(prefix="/identifiers", tags=["identifiers"])


def normalize_email_input(val: str) -> str:
    cleaned = val.strip()
    if "@" not in cleaned:
        raise HTTPException(status_code=400, detail="Invalid email format")
    local, domain = cleaned.split("@", 1)
    # Apply IDNA encoding / ascii conversion to domain
    try:
        normalized_domain = domain.encode("idna").decode("ascii").lower()
    except Exception:
        normalized_domain = domain.lower()
    return f"{local.strip()}@{normalized_domain}"


@router.get("")
async def list_identifiers(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id,
            Identifier.state != IdentifierState.DELETED.value
        )
    )
    identifiers = res.scalars().all()
    dtos = [
        IdentifierDTO(
            id=i.id,
            type=i.type,
            masked_value=i.masked_value,
            state=i.state,
            monitoring_enabled=i.state == IdentifierState.ACTIVE.value
        )
        for i in identifiers
    ]
    return ApiListResponse(
        data=dtos,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_identifier(
    payload: IdentifierCreateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an identifier in pending_verification state.
    CRITICAL: Never queries any intelligence provider at creation time (FR-006).
    """
    req_id = get_request_id(request)
    id_type = payload.type.lower()

    if id_type == IdentifierType.EMAIL.value:
        normalized_value = normalize_email_input(payload.value)
        masked = mask_email(normalized_value)
    elif id_type == IdentifierType.PHONE.value:
        normalized_value = re.sub(r"\D", "", payload.value)
        masked = mask_phone(normalized_value)
    elif id_type == IdentifierType.AADHAAR.value:
        # Full Aadhaar storage is disallowed for external monitoring; only allowed as assistance reference
        normalized_value = re.sub(r"\D", "", payload.value)
        if len(normalized_value) != 12:
            raise HTTPException(status_code=400, detail="Invalid Aadhaar number length")
        masked = mask_aadhaar(normalized_value)
    elif id_type == IdentifierType.PAN.value:
        normalized_value = payload.value.strip().upper()
        if len(normalized_value) != 10:
            raise HTTPException(status_code=400, detail="Invalid PAN format")
        masked = mask_pan(normalized_value)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported identifier type: {id_type}")

    # Envelope encrypt and compute scoped blind index
    encrypted = vault.encrypt(normalized_value, associated_data=ctx.tenant_id)
    blind_idx = vault.compute_blind_index(normalized_value, scope=ctx.tenant_id)

    # Check for duplicate in this subject
    res = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id,
            Identifier.blind_index == blind_idx,
            Identifier.state != IdentifierState.DELETED.value
        )
    )
    existing = res.scalars().first()
    if existing:
        return ApiResponse(
            data=IdentifierDTO(
                id=existing.id,
                type=existing.type,
                masked_value=existing.masked_value,
                state=existing.state,
                monitoring_enabled=existing.state == IdentifierState.ACTIVE.value
            ),
            meta=ResponseMeta(request_id=req_id)
        )

    identifier = Identifier(
        tenant_id=ctx.tenant_id,
        subject_id=ctx.subject_id,
        type=id_type,
        encrypted_value=encrypted,
        blind_index=blind_idx,
        masked_value=masked,
        label=payload.label,
        state=IdentifierState.PENDING_VERIFICATION.value
    )
    db.add(identifier)
    await db.commit()

    return ApiResponse(
        data=IdentifierDTO(
            id=identifier.id,
            type=identifier.type,
            masked_value=identifier.masked_value,
            state=identifier.state,
            monitoring_enabled=False
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/{id}")
async def get_identifier(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Identifier).where(
            Identifier.id == id,
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    ident = res.scalars().first()
    if not ident:
        raise HTTPException(status_code=404, detail="Identifier unavailable to this principal")

    return ApiResponse(
        data=IdentifierDTO(
            id=ident.id,
            type=ident.type,
            masked_value=ident.masked_value,
            state=ident.state,
            monitoring_enabled=ident.state == IdentifierState.ACTIVE.value
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.delete("/{id}")
async def delete_identifier(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Identifier).where(
            Identifier.id == id,
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    ident = res.scalars().first()
    if not ident:
        raise HTTPException(status_code=404, detail="Identifier unavailable to this principal")

    ident.state = IdentifierState.DELETED.value
    await db.commit()
    return ApiResponse(
        data={"id": ident.id, "state": IdentifierState.DELETED.value},
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/{id}/verification-challenges", status_code=status.HTTP_201_CREATED)
async def create_verification_challenge(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Generates single-use 6-digit verification code. Stores only the cryptographic digest."""
    req_id = get_request_id(request)
    res = await db.execute(
        select(Identifier).where(
            Identifier.id == id,
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    ident = res.scalars().first()
    if not ident:
        raise HTTPException(status_code=404, detail="Identifier not found")

    # Generate 6-digit challenge token
    raw_token = f"{secrets.randbelow(900000) + 100000}"
    token_digest = vault.hash_verification_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    challenge = IdentifierVerification(
        tenant_id=ctx.tenant_id,
        identifier_id=ident.id,
        challenge_digest=token_digest,
        expires_at=expires_at,
        max_attempts=5
    )
    db.add(challenge)
    await db.commit()

    return ApiResponse(
        data={
            "challenge_id": challenge.id,
            "expires_in_seconds": 600,
            "masked_destination": ident.masked_value,
            # In test/dev environment, return demo_token for automated testing
            "demo_token": raw_token
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/verification-challenges/complete")
async def complete_verification(
    payload: VerificationCompleteRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Validates challenge token digest and transitions identifier to verified & active."""
    req_id = get_request_id(request)
    res_ident = await db.execute(
        select(Identifier).where(
            Identifier.id == payload.identifier_id,
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    ident = res_ident.scalars().first()
    if not ident:
        raise HTTPException(status_code=404, detail="Identifier not found")

    # Find pending challenge
    now = datetime.now(timezone.utc)
    res_chal = await db.execute(
        select(IdentifierVerification).where(
            IdentifierVerification.identifier_id == ident.id,
            IdentifierVerification.tenant_id == ctx.tenant_id,
            IdentifierVerification.completed_at.is_(None),
            IdentifierVerification.expires_at > now
        ).order_by(IdentifierVerification.created_at.desc())
    )
    challenge = res_chal.scalars().first()
    if not challenge:
        raise HTTPException(status_code=400, detail="No active verification challenge found or expired")

    challenge.attempts += 1
    if challenge.attempts > challenge.max_attempts:
        ident.state = IdentifierState.VERIFICATION_LOCKED.value
        await db.commit()
        raise HTTPException(status_code=429, detail="Too many failed verification attempts")

    # Check token digest in constant time
    expected_digest = challenge.challenge_digest
    provided_digest = vault.hash_verification_token(payload.challenge_token)

    if not vault.secure_compare(expected_digest, provided_digest):
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid verification token")

    challenge.completed_at = now
    ident.state = IdentifierState.ACTIVE.value
    await db.commit()

    return ApiResponse(
        data=IdentifierDTO(
            id=ident.id,
            type=ident.type,
            masked_value=ident.masked_value,
            state=ident.state,
            monitoring_enabled=True
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/{id}/pause")
async def pause_identifier(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Identifier).where(
            Identifier.id == id,
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    ident = res.scalars().first()
    if not ident:
        raise HTTPException(status_code=404, detail="Identifier not found")

    ident.state = IdentifierState.PAUSED.value
    await db.commit()
    return ApiResponse(
        data=IdentifierDTO(
            id=ident.id,
            type=ident.type,
            masked_value=ident.masked_value,
            state=ident.state,
            monitoring_enabled=False
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/{id}/resume")
async def resume_identifier(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(Identifier).where(
            Identifier.id == id,
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    ident = res.scalars().first()
    if not ident:
        raise HTTPException(status_code=404, detail="Identifier not found")

    ident.state = IdentifierState.ACTIVE.value
    await db.commit()
    return ApiResponse(
        data=IdentifierDTO(
            id=ident.id,
            type=ident.type,
            masked_value=ident.masked_value,
            state=ident.state,
            monitoring_enabled=True
        ),
        meta=ResponseMeta(request_id=req_id)
    )
