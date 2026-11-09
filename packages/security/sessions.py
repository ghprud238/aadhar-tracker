"""
Server-side session management and step-up authentication verification.
Ensures bearer tokens are never exposed to browser localStorage.
Provides SQLite-backed persistence for multi-worker container deployments.
"""
import os
import sqlite3
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional


SESSION_LIFETIME = timedelta(hours=8)
STEP_UP_WINDOW = timedelta(minutes=5)


class SessionData:
    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        subject_id: str,
        role: str,
        email: str,
        session_id: Optional[str] = None,
        csrf_token: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_seen_at: Optional[datetime] = None,
        last_step_up_at: Optional[datetime] = None,
        revoked: bool = False,
    ):
        self.session_id = session_id or secrets.token_urlsafe(32)
        self.csrf_token = csrf_token or secrets.token_urlsafe(32)
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.subject_id = subject_id
        self.role = role
        self.email = email
        self.created_at = created_at or datetime.now(timezone.utc)
        self.last_seen_at = last_seen_at or datetime.now(timezone.utc)
        self.last_step_up_at: Optional[datetime] = last_step_up_at
        self.revoked = revoked

    @property
    def is_expired(self) -> bool:
        if self.revoked:
            return True
        return datetime.now(timezone.utc) - self.last_seen_at > SESSION_LIFETIME

    def record_step_up(self):
        self.last_step_up_at = datetime.now(timezone.utc)
        session_store.update_step_up(self.session_id, self.last_step_up_at)

    @property
    def has_valid_step_up(self) -> bool:
        if not self.last_step_up_at:
            return False
        return datetime.now(timezone.utc) - self.last_step_up_at <= STEP_UP_WINDOW


class SessionStore:
    def __init__(self, db_path: Optional[str] = None):
        self._memory_sessions: Dict[str, SessionData] = {}
        self.db_path = db_path or os.getenv("SESSION_DB_PATH")
        if not self.db_path:
            if os.path.exists("/app/data"):
                self.db_path = "/app/data/sessions.db"
            else:
                self.db_path = os.getenv("DATABASE_URL", "").replace("sqlite+aiosqlite:///", "")
                if not self.db_path or "sqlite" not in self.db_path:
                    self.db_path = "sessions.db"
        self._init_sqlite()

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def _init_sqlite(self):
        if self.db_path and not self.db_path.startswith(":memory:"):
            dir_name = os.path.dirname(self.db_path)
            if dir_name:
                try:
                    os.makedirs(dir_name, exist_ok=True)
                except Exception:
                    pass

        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        csrf_token TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        subject_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        email TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_seen_at TEXT NOT NULL,
                        last_step_up_at TEXT,
                        revoked INTEGER NOT NULL DEFAULT 0
                    )
                """)
        except Exception:
            pass
        finally:
            conn.close()

    def create_session(self, user_id: str, tenant_id: str, subject_id: str, role: str, email: str) -> SessionData:
        session = SessionData(user_id=user_id, tenant_id=tenant_id, subject_id=subject_id, role=role, email=email)
        self._memory_sessions[session.session_id] = session

        conn = self._get_conn()
        if conn:
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO user_sessions (
                            session_id, csrf_token, user_id, tenant_id, subject_id,
                            role, email, created_at, last_seen_at, last_step_up_at, revoked
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        session.session_id,
                        session.csrf_token,
                        session.user_id,
                        session.tenant_id,
                        session.subject_id,
                        session.role,
                        session.email,
                        session.created_at.isoformat(),
                        session.last_seen_at.isoformat(),
                        session.last_step_up_at.isoformat() if session.last_step_up_at else None,
                    ))
            except Exception:
                pass
            finally:
                conn.close()

        return session

    def _load_from_db(self, session_id: str) -> Optional[SessionData]:
        conn = self._get_conn()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM user_sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            if not row:
                return None

            created_at = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            last_seen_at = datetime.fromisoformat(row["last_seen_at"]) if row["last_seen_at"] else datetime.now(timezone.utc)
            last_step_up = datetime.fromisoformat(row["last_step_up_at"]) if row["last_step_up_at"] else None

            existing_mem = self._memory_sessions.get(row["session_id"])
            if existing_mem and existing_mem.last_step_up_at:
                if not last_step_up or existing_mem.last_step_up_at > last_step_up:
                    last_step_up = existing_mem.last_step_up_at

            session = SessionData(
                session_id=row["session_id"],
                csrf_token=row["csrf_token"],
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                subject_id=row["subject_id"],
                role=row["role"],
                email=row["email"],
                created_at=created_at,
                last_seen_at=last_seen_at,
                last_step_up_at=last_step_up,
                revoked=bool(row["revoked"]),
            )
            self._memory_sessions[session.session_id] = session
            return session
        except Exception:
            return None
        finally:
            conn.close()

    def get_session(self, session_id: str | None) -> Optional[SessionData]:
        if not session_id:
            return None

        # Always check database if available to get authoritative state across workers
        session = self._load_from_db(session_id)
        if not session:
            session = self._memory_sessions.get(session_id)

        if not session or session.is_expired:
            if session:
                self.revoke_session(session_id)
            return None

        session.last_seen_at = datetime.now(timezone.utc)
        conn = self._get_conn()
        if conn:
            try:
                with conn:
                    conn.execute("UPDATE user_sessions SET last_seen_at = ? WHERE session_id = ?", (
                        session.last_seen_at.isoformat(),
                        session_id,
                    ))
            except Exception:
                pass
            finally:
                conn.close()

        return session

    def rotate_session(self, old_session_id: str) -> Optional[SessionData]:
        old_session = self.get_session(old_session_id)
        if not old_session:
            return None
        old_session.revoked = True
        self.revoke_session(old_session_id)

        new_session = self.create_session(
            user_id=old_session.user_id,
            tenant_id=old_session.tenant_id,
            subject_id=old_session.subject_id,
            role=old_session.role,
            email=old_session.email,
        )
        new_session.last_step_up_at = old_session.last_step_up_at
        if new_session.last_step_up_at:
            self.update_step_up(new_session.session_id, new_session.last_step_up_at)
        return new_session

    def update_step_up(self, session_id: str, step_up_at: datetime):
        if session_id in self._memory_sessions:
            self._memory_sessions[session_id].last_step_up_at = step_up_at

        conn = self._get_conn()
        if conn:
            try:
                with conn:
                    conn.execute("UPDATE user_sessions SET last_step_up_at = ? WHERE session_id = ?", (
                        step_up_at.isoformat(),
                        session_id,
                    ))
            except Exception:
                pass
            finally:
                conn.close()

    def revoke_session(self, session_id: str):
        if session_id in self._memory_sessions:
            self._memory_sessions[session_id].revoked = True

        conn = self._get_conn()
        if conn:
            try:
                with conn:
                    conn.execute("UPDATE user_sessions SET revoked = 1 WHERE session_id = ?", (session_id,))
            except Exception:
                pass
            finally:
                conn.close()

    def revoke_all_user_sessions(self, user_id: str):
        for s in self._memory_sessions.values():
            if s.user_id == user_id:
                s.revoked = True

        conn = self._get_conn()
        if conn:
            try:
                with conn:
                    conn.execute("UPDATE user_sessions SET revoked = 1 WHERE user_id = ?", (user_id,))
            except Exception:
                pass
            finally:
                conn.close()

    def list_active_user_sessions(self, user_id: str) -> list[SessionData]:
        # Fetch active from DB to ensure cross-process completeness
        conn = self._get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT session_id FROM user_sessions WHERE user_id = ? AND revoked = 0", (user_id,))
                active = []
                for row in cur.fetchall():
                    s = self.get_session(row["session_id"])
                    if s and not s.is_expired:
                        active.append(s)
                return active
            except Exception:
                pass
            finally:
                conn.close()

        return [
            s for s in self._memory_sessions.values()
            if s.user_id == user_id and not s.is_expired
        ]


session_store = SessionStore()
