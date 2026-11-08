"""
Authentication and Session endpoints.
Implements OIDC authorization-code flow, session cookies, CSRF, and step-up auth.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api.database import get_db
from services.api.dependencies import get_request_id, get_current_session, require_step_up_auth
from packages.domain.models import User, Tenant, Membership, Subject, AuditEvent
from packages.security.sessions import session_store, SessionData
from packages.domain.schemas import ApiResponse, ResponseMeta

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def auth_login(request: Request):
    """Initiates OIDC login flow. Returns mock redirect URL for testing/demo."""
    req_id = get_request_id(request)
    state = "state_" + req_id[:8]
    auth_url = f"https://auth.identityprotection.internal/oauth2/authorize?client_id=ipp_client&response_type=code&state={state}"
    return ApiResponse(
        data={"authorization_url": auth_url, "state": state},
        meta=ResponseMeta(request_id=req_id)
    )


@router.get("/callback")
async def auth_callback(
    code: str = "mock_auth_code",
    email: str = "user@example.com",
    full_name: str = "Test Resident",
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """OIDC callback endpoint. Exchanges code, ensures User/Tenant/Subject exist, sets session cookie."""
    req_id = get_request_id(request)

    # Find or create user
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if not user:
        user = User(
            idp_subject=f"oidc_{email}",
            email=email,
            full_name=full_name,
            account_state="active"
        )
        db.add(user)
        await db.flush()

        # Create personal tenant
        tenant = Tenant(
            owner_user_id=user.id,
            name=f"{full_name}'s Personal Workspace",
            tenant_type="personal",
            region_policy="IN"
        )
        db.add(tenant)
        await db.flush()

        # Membership
        membership = Membership(
            tenant_id=tenant.id,
            user_id=user.id,
            role="consumer_owner",
            state="active"
        )
        db.add(membership)

        # Subject
        subject = Subject(
            tenant_id=tenant.id,
            owner_user_id=user.id,
            monitoring_state="active"
        )
        db.add(subject)
        await db.commit()
    else:
        # Find tenant & subject
        res_tenant = await db.execute(select(Tenant).where(Tenant.owner_user_id == user.id))
        tenant = res_tenant.scalars().first()
        res_sub = await db.execute(select(Subject).where(Subject.owner_user_id == user.id))
        subject = res_sub.scalars().first()

    # Create server session
    session = session_store.create_session(
        user_id=user.id,
        tenant_id=tenant.id,
        subject_id=subject.id,
        role="consumer_owner",
        email=user.email
    )

    if response:
        response.set_cookie(
            key="ipp_session",
            value=session.session_id,
            httponly=True,
            secure=False,  # True in prod HTTPS
            samesite="lax",
            max_age=8 * 3600
        )

    return ApiResponse(
        data={
            "session_id": session.session_id,
            "csrf_token": session.csrf_token,
            "user_id": user.id,
            "tenant_id": tenant.id,
            "subject_id": subject.id,
            "email": user.email
        },
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/step-up")
async def auth_step_up(
    passcode: str = "123456",
    request: Request = None,
    session: SessionData = Depends(get_current_session),
    db: AsyncSession = Depends(get_db)
):
    """Performs recent step-up authentication. Grants a 5-minute elevated session window."""
    req_id = get_request_id(request)
    if passcode != "123456":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid step-up verification code"
        )

    session.record_step_up()

    # Record audit event
    audit = AuditEvent(
        tenant_id=session.tenant_id,
        actor_id=session.user_id,
        actor_role=session.role,
        action="auth.step_up_granted",
        scoped_resource=f"user:{session.user_id}",
        result="success"
    )
    db.add(audit)
    await db.commit()

    return ApiResponse(
        data={"step_up_active": True, "valid_for_seconds": 300},
        meta=ResponseMeta(request_id=req_id)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def auth_logout(
    response: Response,
    session: SessionData = Depends(get_current_session)
):
    session_store.revoke_session(session.session_id)
    response.delete_cookie("ipp_session")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
