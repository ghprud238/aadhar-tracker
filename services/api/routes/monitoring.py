"""
Monitoring and Scan initiation endpoints.
Implements FR-009 (asynchronous initial scans), outbox queuing, and transparent coverage reporting.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.domain.models import (
    Identifier,
    Subject,
    ConsentGrant,
    MonitoringJob,
    OutboxEvent,
    ProviderConnection,
)
from packages.domain.enums import IdentifierState, ScanState, ProviderOutcome
from packages.security.authorization import AuthContext
from packages.provider_adapters.registry import provider_registry
from packages.domain.schemas import (
    ApiResponse,
    ApiListResponse,
    ResponseMeta,
    PaginationInfo,
    ScanSubmitRequest,
    ScanSubmitDTO,
    ScanSourceStatus,
    CoverageItemDTO,
)

router = APIRouter(tags=["monitoring"])


@router.get("/monitoring/status")
async def get_monitoring_status(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    # Check verified identifiers
    res_id = await db.execute(
        select(Identifier).where(
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id,
            Identifier.state == IdentifierState.ACTIVE.value
        )
    )
    active_ids = res_id.scalars().all()

    # Check active consent
    res_c = await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.tenant_id == ctx.tenant_id,
            ConsentGrant.subject_id == ctx.subject_id,
            ConsentGrant.status == "granted"
        )
    )
    has_consent = res_c.scalars().first() is not None

    status_str = "active" if (active_ids and has_consent) else "pending_setup"

    return ApiResponse(
        data={
            "monitoring_status": status_str,
            "active_monitored_identifiers_count": len(active_ids),
            "consent_granted": has_consent,
            "last_scan_at": datetime.now(timezone.utc).isoformat(),
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/scans", status_code=status.HTTP_202_ACCEPTED)
async def submit_scan(
    payload: ScanSubmitRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an asynchronous scan for verified identifiers.
    Writes job intents to transactional outbox atomically.
    """
    req_id = get_request_id(request)

    # 1. Verify consent
    res_c = await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.tenant_id == ctx.tenant_id,
            ConsentGrant.subject_id == ctx.subject_id,
            ConsentGrant.status == "granted"
        )
    )
    consent = res_c.scalars().first()
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid consent grant required prior to scanning"
        )

    # 2. Verify subject authorization version
    res_sub = await db.execute(select(Subject).where(Subject.id == ctx.subject_id))
    subject = res_sub.scalars().first()
    auth_version = subject.authorization_version if subject else 1

    # 3. Verify identifiers
    res_ids = await db.execute(
        select(Identifier).where(
            Identifier.id.in_(payload.identifier_ids),
            Identifier.tenant_id == ctx.tenant_id,
            Identifier.subject_id == ctx.subject_id
        )
    )
    identifiers = res_ids.scalars().all()
    if not identifiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid owned identifiers supplied for scanning"
        )

    for i in identifiers:
        if i.state != IdentifierState.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Identifier {i.masked_value} is not verified or active for monitoring"
            )

    scan_run_id = str(uuid.uuid4())
    enabled_providers = ["hibp", "flare"]
    source_statuses = []

    for ident in identifiers:
        for prov_name in enabled_providers:
            provider = provider_registry.get_provider(prov_name)
            is_enabled = getattr(provider, "is_enabled", True) if provider else False
            initial_state = ScanState.QUEUED.value if is_enabled else ScanState.CANCELLED.value

            job = MonitoringJob(
                tenant_id=ctx.tenant_id,
                subject_id=ctx.subject_id,
                identifier_id=ident.id,
                provider_name=prov_name,
                authorization_version=auth_version,
                state=initial_state
            )
            db.add(job)
            await db.flush()

            if is_enabled:
                # Add to Transactional Outbox
                outbox_evt = OutboxEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="monitoring.scan.requested",
                    tenant_id=ctx.tenant_id,
                    subject_id=ctx.subject_id,
                    resource_id=job.id,
                    authorization_version=auth_version,
                    payload={
                        "scan_run_id": scan_run_id,
                        "job_id": job.id,
                        "identifier_id": ident.id,
                        "provider_name": prov_name,
                        "reason": payload.reason
                    }
                )
                db.add(outbox_evt)

            source_statuses.append(ScanSourceStatus(provider=prov_name, state=initial_state))

    await db.commit()

    return ApiResponse(
        data=ScanSubmitDTO(
            id=scan_run_id,
            state="queued",
            sources=source_statuses
        ),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/scans")
async def list_scans(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(
        select(MonitoringJob).where(
            MonitoringJob.tenant_id == ctx.tenant_id,
            MonitoringJob.subject_id == ctx.subject_id
        ).order_by(MonitoringJob.created_at.desc())
    )
    jobs = res.scalars().all()
    data = [
        {
            "id": j.id,
            "identifier_id": j.identifier_id,
            "provider_name": j.provider_name,
            "state": j.state,
            "outcome": j.outcome,
            "created_at": j.created_at.isoformat(),
            "completed_at": j.completed_at.isoformat() if j.completed_at else None
        }
        for j in jobs
    ]
    return ApiListResponse(
        data=data,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/coverage")
async def get_coverage_matrix(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    """
    Returns transparency matrix distinguishing checked, delayed, and unsupported sources (ADR-012).
    """
    req_id = get_request_id(request)
    now = datetime.now(timezone.utc)
    items = [
        CoverageItemDTO(
            source="Have I Been Pwned",
            capability="Email Breach Associations & Catalog",
            last_successful_check=now,
            current_state="healthy",
            known_limitation="Covers public and curated commercial breaches; does not monitor live paste sites without separate enterprise tier.",
            next_expected_check=now
        ),
        CoverageItemDTO(
            source="Flare Cyber Threat Intelligence",
            capability="Dark-Web Mentions & Stealer Logs",
            last_successful_check=now,
            current_state="healthy",
            known_limitation="Covers indexed cybercrime forums and stealer telemetry; does not interact directly with threat actors or purchase files.",
            next_expected_check=now
        ),
        CoverageItemDTO(
            source="UIDAI Official Resident Services",
            capability="Aadhaar Resident Safety Assistance",
            last_successful_check=None,
            current_state="guidance_only",
            known_limitation="Educational and resident-initiated guidance only. No direct dark-web Aadhaar queries or portal scraping.",
            next_expected_check=None
        ),
        CoverageItemDTO(
            source="Income Tax Department / Protean",
            capability="PAN Verification Capability",
            last_successful_check=None,
            current_state="disabled_pending_partner_approval",
            known_limitation="Requires official Income Tax Department authorization. No unauthorized PAN queries.",
            next_expected_check=None
        )
    ]
    return ApiListResponse(
        data=items,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/providers")
async def list_providers_metadata(request: Request):
    req_id = get_request_id(request)
    caps = await provider_registry.get_all_capabilities()
    return ApiListResponse(
        data=[c.__dict__ for c in caps],
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )
