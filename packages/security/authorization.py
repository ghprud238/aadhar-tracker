"""
Authorization context, permission evaluation, and database RLS enforcement.
Enforces multi-layer tenant and subject ownership.
"""
from contextvars import ContextVar
from typing import Optional
from fastapi import HTTPException, status
from packages.domain.enums import UserRole
from packages.security.sessions import SessionData


# Request-scoped context variables
current_tenant_var: ContextVar[Optional[str]] = ContextVar("current_tenant_var", default=None)
current_subject_var: ContextVar[Optional[str]] = ContextVar("current_subject_var", default=None)
current_user_var: ContextVar[Optional[str]] = ContextVar("current_user_var", default=None)
current_role_var: ContextVar[Optional[str]] = ContextVar("current_role_var", default=None)


class AuthContext:
    def __init__(self, session: SessionData):
        self.user_id = session.user_id
        self.tenant_id = session.tenant_id
        self.subject_id = session.subject_id
        self.role = session.role
        self.session = session

    def require_ownership(self, resource_tenant_id: str, resource_subject_id: str | None = None):
        """Enforce tenant and subject isolation; fail closed without disclosing other tenants."""
        if resource_tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource unavailable to this principal"
            )
        if resource_subject_id and resource_subject_id != self.subject_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource unavailable to this principal"
            )

    def require_step_up(self):
        """Enforce recent step-up authentication within 5-minute window for sensitive actions."""
        if not self.session.has_valid_step_up:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Step-up authentication required for this operation"
            )

    def require_role(self, *allowed_roles: UserRole):
        if self.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation forbidden for current role"
            )


def set_request_auth_context(ctx: AuthContext):
    current_tenant_var.set(ctx.tenant_id)
    current_subject_var.set(ctx.subject_id)
    current_user_var.set(ctx.user_id)
    current_role_var.set(ctx.role)


def clear_request_auth_context():
    current_tenant_var.set(None)
    current_subject_var.set(None)
    current_user_var.set(None)
    current_role_var.set(None)
