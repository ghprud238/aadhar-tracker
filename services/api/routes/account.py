"""
Account, Session, and Workspace routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from services.api.database import get_db
from services.api.dependencies import (
    get_request_id,
    get_current_session,
    get_auth_context,
    require_step_up_auth,
)
from packages.domain.models import User, Tenant, Subject
from packages.security.authorization import AuthContext
from packages.security.sessions import session_store, SessionData
from packages.domain.schemas import ApiResponse, ApiListResponse, ResponseMeta, PaginationInfo

router = APIRouter(tags=["account"])


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None


@router.get("/session")
async def get_session_info(
    request: Request,
    session: SessionData = Depends(get_current_session)
):
    req_id = get_request_id(request)
    return ApiResponse(
        data={
            "user_id": session.user_id,
            "tenant_id": session.tenant_id,
            "subject_id": session.subject_id,
            "role": session.role,
            "email": session.email,
            "created_at": session.created_at.isoformat(),
            "has_valid_step_up": session.has_valid_step_up,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/sessions")
async def list_sessions(
    request: Request,
    session: SessionData = Depends(get_current_session)
):
    req_id = get_request_id(request)
    active = session_store.list_active_user_sessions(session.user_id)
    items = [
        {
            "session_id": s.session_id[:8] + "...",
            "current": s.session_id == session.session_id,
            "created_at": s.created_at.isoformat(),
            "last_seen_at": s.last_seen_at.isoformat(),
        }
        for s in active
    ]
    return ApiListResponse(
        data=items,
        page=PaginationInfo(has_more=False),
        meta=ResponseMeta(request_id=req_id)
    )


@router.delete("/sessions/{id}")
async def revoke_session_by_id(
    id: str,
    request: Request,
    ctx: AuthContext = Depends(require_step_up_auth)
):
    req_id = get_request_id(request)
    # Revoke session matching prefix or exact
    for s in session_store.list_active_user_sessions(ctx.user_id):
        if s.session_id.startswith(id) or s.session_id == id:
            session_store.revoke_session(s.session_id)
            break
    return ApiResponse(
        data={"revoked": True},
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/me")
async def get_profile(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(select(User).where(User.id == ctx.user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return ApiResponse(
        data={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "account_state": user.account_state,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.patch("/me")
async def update_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(select(User).where(User.id == ctx.user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    await db.commit()
    return ApiResponse(
        data={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "account_state": user.account_state,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/me/security")
async def get_security_settings(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context)
):
    req_id = get_request_id(request)
    return ApiResponse(
        data={
            "mfa_enabled": True,
            "step_up_authenticated": ctx.session.has_valid_step_up,
            "recovery_email_configured": True,
            "active_sessions_count": len(session_store.list_active_user_sessions(ctx.user_id)),
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/workspace")
async def get_workspace(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(select(Tenant).where(Tenant.id == ctx.tenant_id))
    tenant = res.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ApiResponse(
        data={
            "id": tenant.id,
            "name": tenant.name,
            "tenant_type": tenant.tenant_type,
            "region_policy": tenant.region_policy,
            "account_state": tenant.account_state,
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/workspace")
async def create_workspace_idempotent(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    req_id = get_request_id(request)
    res = await db.execute(select(Tenant).where(Tenant.owner_user_id == ctx.user_id))
    tenant = res.scalars().first()
    if not tenant:
        tenant = Tenant(
            owner_user_id=ctx.user_id,
            name="Personal Workspace",
            tenant_type="personal",
            region_policy="IN"
        )
        db.add(tenant)
        await db.commit()
    return ApiResponse(
        data={
            "id": tenant.id,
            "name": tenant.name,
            "tenant_type": tenant.tenant_type,
            "region_policy": tenant.region_policy,
            "account_state": tenant.account_state,
        },
        meta=ResponseMeta(request_id=req_id)
    )
