"""
Unit and Integration tests for Companion Glance API (/api/v1/companion/glance).
Tests lightweight summary endpoints powering Smartwatch Tiles, Watch Faces, and Mobile Widgets.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db, async_session_factory
from services.api.outbox_dispatcher import OutboxDispatcher


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_companion_glance_initial_state():
    """Verify companion glance returns secure status and zero active incidents initially."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=watch_user@example.com")
        token = res_auth.json()["data"]["session_id"]

        res = await client.get(
            "/api/v1/companion/glance",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["shield_status"] == "secure"
        assert data["active_incidents"] == 0
        assert data["highest_severity"] == "none"
        assert data["biometrics_locked"] is False
        assert data["urgent_alert"] is None
        assert "last_synced_at" in data


@pytest.mark.asyncio
async def test_companion_glance_with_active_incident():
    """Verify companion glance escalates shield status when incidents are present."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=watch_breached@example.com")
        token = res_auth.json()["data"]["session_id"]
        sub_id = res_auth.json()["data"]["subject_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Grant consent
        await client.post(
            "/api/v1/consents",
            headers=auth_headers,
            json={"purpose": "identity_exposure_monitoring", "notice_version": "1.0", "subject_id": sub_id}
        )

        # 2. Add email identifier
        res_id = await client.post(
            "/api/v1/identifiers",
            headers=auth_headers,
            json={"type": "email", "value": "watch_breached@example.com"}
        )
        ident_id = res_id.json()["data"]["id"]

        # 3. Challenge and verify
        res_chal = await client.post(
            f"/api/v1/identifiers/{ident_id}/verification-challenges",
            headers=auth_headers
        )
        code = res_chal.json()["data"]["demo_token"]
        await client.post(
            "/api/v1/identifiers/verification-challenges/complete",
            headers=auth_headers,
            json={"identifier_id": ident_id, "challenge_token": code}
        )

        # 4. Trigger scan
        await client.post(
            "/api/v1/scans",
            headers=auth_headers,
            json={"identifier_ids": [ident_id]}
        )

        # 5. Run outbox dispatcher
        async with async_session_factory() as db_session:
            dispatcher = OutboxDispatcher(db_session)
            await dispatcher.dispatch_pending(limit=10)

        # 6. Fetch companion glance
        res = await client.get(
            "/api/v1/companion/glance",
            headers=auth_headers
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["shield_status"] in ["warning", "critical"]
        assert data["active_incidents"] > 0
        assert data["urgent_alert"] is not None
        assert "incident_id" in data["urgent_alert"]
        assert "title" in data["urgent_alert"]
        assert "severity" in data["urgent_alert"]
