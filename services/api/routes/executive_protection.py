"""
Corporate Executive & Family Office Protection API Routes
CISO Management Portal, Executive Threat Dashboard, and 1-Click VIP Evidence Dispatch.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_auth_context
from packages.security.authorization import AuthContext
from packages.domain.models import ExecutiveProfile
from packages.domain.schemas import (
    ApiResponse,
    ResponseMeta,
    ExecutiveDashboardDTO,
    ExecutiveEnrollRequest,
    ExecutiveProfileDTO,
    ExecutiveThreatSimulateRequest,
    ExecutiveThreatIncidentDTO,
    ExecutiveDispatchPackDTO
)
from packages.domain.executive_protection import ExecutiveProtectionService

router = APIRouter(prefix="/executive-protection", tags=["Corporate Executive Protection Suite"])


@router.get("/dashboard", response_model=ApiResponse[ExecutiveDashboardDTO])
async def get_executive_dashboard(
    req_id: str = Depends(get_request_id),
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    service = ExecutiveProtectionService(db, tenant_id=ctx.tenant_id)
    data = await service.get_ciso_dashboard()
    return ApiResponse(
        data=ExecutiveDashboardDTO(**data),
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/executives", response_model=ApiResponse[ExecutiveProfileDTO])
async def enroll_executive_endpoint(
    req: ExecutiveEnrollRequest,
    req_id: str = Depends(get_request_id),
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    service = ExecutiveProtectionService(db, tenant_id=ctx.tenant_id)
    exec_profile = await service.enroll_executive(
        full_name=req.full_name,
        corporate_email=req.corporate_email,
        designation=req.designation,
        vip_tier=req.vip_tier,
        personal_email=req.personal_email,
        personal_phone=req.personal_phone,
        masked_aadhaar=req.masked_aadhaar,
        pan=req.pan
    )
    dto = ExecutiveProfileDTO(
        id=exec_profile.id,
        full_name=exec_profile.full_name,
        corporate_email=exec_profile.corporate_email,
        designation=exec_profile.designation,
        vip_tier=exec_profile.vip_tier,
        risk_score=exec_profile.risk_score,
        monitoring_status=exec_profile.monitoring_status,
        assets_count=exec_profile.assets_count,
        active_incidents_count=exec_profile.active_incidents_count,
        created_at=exec_profile.created_at
    )
    return ApiResponse(
        data=dto,
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/executives", response_model=ApiResponse[List[ExecutiveProfileDTO]])
async def list_executives_endpoint(
    req_id: str = Depends(get_request_id),
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    service = ExecutiveProtectionService(db, tenant_id=ctx.tenant_id)
    # Ensure at least demo executive exists
    await service.get_ciso_dashboard()

    res = await db.execute(
        select(ExecutiveProfile).where(ExecutiveProfile.tenant_id == ctx.tenant_id)
    )
    executives = res.scalars().all()

    dtos = [
        ExecutiveProfileDTO(
            id=e.id,
            full_name=e.full_name,
            corporate_email=e.corporate_email,
            designation=e.designation,
            vip_tier=e.vip_tier,
            risk_score=e.risk_score,
            monitoring_status=e.monitoring_status,
            assets_count=e.assets_count,
            active_incidents_count=e.active_incidents_count,
            created_at=e.created_at
        )
        for e in executives
    ]
    return ApiResponse(
        data=dtos,
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/threats/simulate", response_model=ApiResponse[ExecutiveThreatIncidentDTO])
async def simulate_threat_endpoint(
    req: ExecutiveThreatSimulateRequest,
    req_id: str = Depends(get_request_id),
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    service = ExecutiveProtectionService(db, tenant_id=ctx.tenant_id)
    try:
        incident = await service.simulate_or_ingest_threat(
            executive_id=req.executive_id,
            threat_type=req.threat_type,
            title=req.title,
            description=req.description,
            severity=req.severity
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    res_e = await db.execute(select(ExecutiveProfile).where(ExecutiveProfile.id == req.executive_id))
    exec_obj = res_e.scalar_one_or_none()
    exec_name = exec_obj.full_name if exec_obj else "Enterprise Executive"

    dto = ExecutiveThreatIncidentDTO(
        id=incident.id,
        executive_id=incident.executive_id,
        executive_name=exec_name,
        threat_type=incident.threat_type,
        severity=incident.severity,
        title=incident.title,
        description=incident.description,
        indicators=incident.indicators or {},
        state=incident.state,
        detected_at=incident.detected_at
    )
    return ApiResponse(
        data=dto,
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/incidents/{incident_id}/dispatch-pack", response_model=ApiResponse[ExecutiveDispatchPackDTO])
async def dispatch_vip_pack_endpoint(
    incident_id: str,
    req_id: str = Depends(get_request_id),
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    service = ExecutiveProtectionService(db, tenant_id=ctx.tenant_id)
    try:
        pack = await service.dispatch_vip_incident_pack(incident_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ApiResponse(
        data=ExecutiveDispatchPackDTO(**pack),
        meta=ResponseMeta(request_id=req_id)
    )
