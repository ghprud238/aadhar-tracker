"""
Pytest global configuration and database fixtures.
Ensures clean database isolation between test executions.
"""
import pytest
import os
from services.api.database import init_db, engine
from packages.domain.models import Base


@pytest.fixture(autouse=True)
async def clean_database():
    """Drops and recreates all tables before each test function to guarantee isolation."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await init_db()
    yield
