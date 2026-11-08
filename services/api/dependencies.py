"""
FastAPI dependencies for request ID tracing, OIDC/BFF session resolution, and ownership enforcement.
"""
import uuid
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from packages.security.sessions import session_store, SessionData
from packages.security.authorization import (
    AuthContext,
    set_request_auth_context,
    clear_request_auth_context,
)


def get_request_id(request: Request) -> str:
    """Extract or generate request correlation ID."""
    req_id = request.headers.get("X-Request-ID")
    if not req_id:
        req_id = str(uuid.uuid4())
    return req_id


async def get_current_session(request: Request) -> SessionData:
    """Retrieve and validate the active server-side session from auth header or HttpOnly cookie."""
    session_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.split(" ")[1]

    if not session_id:
        session_id = request.cookies.get("ipp_session")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return session


async def get_auth_context(
    request: Request,
    session: SessionData = Depends(get_current_session)
) -> AuthContext:
    """Construct AuthContext and bind transaction-scoped context variables."""
    ctx = AuthContext(session=session)
    set_request_auth_context(ctx)
    return ctx


async def require_step_up_auth(
    ctx: AuthContext = Depends(get_auth_context)
) -> AuthContext:
    """Enforce recent step-up authentication within the 5-minute window."""
    ctx.require_step_up()
    return ctx
