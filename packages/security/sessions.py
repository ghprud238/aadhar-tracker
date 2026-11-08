"""
Server-side session management and step-up authentication verification.
Ensures bearer tokens are never exposed to browser localStorage.
"""
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any


SESSION_LIFETIME = timedelta(hours=8)
STEP_UP_WINDOW = timedelta(minutes=5)


class SessionData:
    def __init__(self, user_id: str, tenant_id: str, subject_id: str, role: str, email: str):
        self.session_id = secrets.token_urlsafe(32)
        self.csrf_token = secrets.token_urlsafe(32)
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.subject_id = subject_id
        self.role = role
        self.email = email
        self.created_at = datetime.now(timezone.utc)
        self.last_seen_at = datetime.now(timezone.utc)
        self.last_step_up_at: datetime | None = None
        self.revoked = False

    @property
    def is_expired(self) -> bool:
        if self.revoked:
            return True
        return datetime.now(timezone.utc) - self.last_seen_at > SESSION_LIFETIME

    def record_step_up(self):
        self.last_step_up_at = datetime.now(timezone.utc)

    @property
    def has_valid_step_up(self) -> bool:
        if not self.last_step_up_at:
            return False
        return datetime.now(timezone.utc) - self.last_step_up_at <= STEP_UP_WINDOW


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}

    def create_session(self, user_id: str, tenant_id: str, subject_id: str, role: str, email: str) -> SessionData:
        session = SessionData(user_id=user_id, tenant_id=tenant_id, subject_id=subject_id, role=role, email=email)
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str | None) -> SessionData | None:
        if not session_id or session_id not in self._sessions:
            return None
        session = self._sessions[session_id]
        if session.is_expired:
            self.revoke_session(session_id)
            return None
        session.last_seen_at = datetime.now(timezone.utc)
        return session

    def rotate_session(self, old_session_id: str) -> SessionData | None:
        old_session = self.get_session(old_session_id)
        if not old_session:
            return None
        old_session.revoked = True
        new_session = self.create_session(
            user_id=old_session.user_id,
            tenant_id=old_session.tenant_id,
            subject_id=old_session.subject_id,
            role=old_session.role,
            email=old_session.email,
        )
        new_session.last_step_up_at = old_session.last_step_up_at
        return new_session

    def revoke_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].revoked = True

    def revoke_all_user_sessions(self, user_id: str):
        for s in self._sessions.values():
            if s.user_id == user_id:
                s.revoked = True

    def list_active_user_sessions(self, user_id: str) -> list[SessionData]:
        return [
            s for s in self._sessions.values()
            if s.user_id == user_id and not s.is_expired
        ]


session_store = SessionStore()
