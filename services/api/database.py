"""
Database configuration, session management, and RLS context attachment.
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from packages.domain.models import Base, ProcessingNotice
from packages.security.authorization import current_tenant_var, current_subject_var

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_identity_platform.db")

# For sqlite, foreign keys must be enabled on connect
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    future=True
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db():
    """Create tables and ensure initial required seed data is present."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # In PostgreSQL, enable RLS policies on tenant/subject tables:
        if "postgresql" in DATABASE_URL:
            await conn.execute(text("""
                ALTER TABLE identifiers ENABLE ROW LEVEL SECURITY;
                ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
                ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
            """))

    # Seed initial processing notice if not present
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id FROM processing_notices WHERE version = '1.0'")
        )
        if not result.first():
            notice = ProcessingNotice(
                version="1.0",
                purpose="identity_exposure_monitoring",
                title="Identity Exposure Monitoring and Protective Assistance Notice",
                content_html="<p>This notice explains how verified identifiers are monitored across approved breach catalogs and licensed feeds.</p>",
                publication_state="published"
            )
            session.add(notice)
            await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a session and sets transaction-local RLS variables if PostgreSQL."""
    async with async_session_factory() as session:
        tenant_id = current_tenant_var.get()
        subject_id = current_subject_var.get()

        if "postgresql" in DATABASE_URL and tenant_id:
            await session.execute(
                text("SET LOCAL app.current_tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            if subject_id:
                await session.execute(
                    text("SET LOCAL app.current_subject_id = :subject_id"),
                    {"subject_id": subject_id}
                )

        try:
            yield session
        finally:
            await session.close()
