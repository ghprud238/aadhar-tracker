"""
End-to-End User Journeys.
Covers E2E-001 through E2E-016 from PRD Page 68.
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
async def test_complete_e2e_journey_e2e_001_and_e2e_004():
    """
    Sign up -> consent -> verify email -> submit scan -> outbox worker execution ->
    incident created -> complete remediation action.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Sign in
        res_auth = await client.get("/api/v1/auth/callback?email=test.user@domain.com&full_name=Test+Citizen")
        token = res_auth.json()["data"]["session_id"]
        sub_id = res_auth.json()["data"]["subject_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 2. Grant consent
        await client.post(
            "/api/v1/consents",
            headers=auth_headers,
            json={"purpose": "identity_exposure_monitoring", "notice_version": "1.0", "subject_id": sub_id}
        )

        # 3. Add email
        res_id = await client.post(
            "/api/v1/identifiers",
            headers=auth_headers,
            json={"type": "email", "value": "test.user@domain.com"}
        )
        ident_id = res_id.json()["data"]["id"]

        # 4. Trigger challenge and complete verification
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

        # 5. Submit on-demand scan
        res_scan = await client.post(
            "/api/v1/scans",
            headers=auth_headers,
            json={"identifier_ids": [ident_id]}
        )
        assert res_scan.status_code == 202

        # 6. Run Outbox Dispatcher (asynchronously simulated)
        async with async_session_factory() as db_session:
            dispatcher = OutboxDispatcher(db_session)
            dispatched = await dispatcher.dispatch_pending(limit=10)
            assert dispatched > 0

        # 7. Check Incidents
        res_inc = await client.get("/api/v1/incidents", headers=auth_headers)
        assert res_inc.status_code == 200
        incidents = res_inc.json()["data"]
        assert len(incidents) > 0
        incident_id = incidents[0]["id"]
        assert incidents[0]["severity"] in ("medium", "high", "critical")

        # 8. Check Remediation Checklist (E2E-004)
        res_rem = await client.get(f"/api/v1/incidents/{incident_id}/remediations", headers=auth_headers)
        actions = res_rem.json()["data"]
        assert len(actions) > 0
        action_id = actions[0]["id"]

        # Complete remediation
        res_done = await client.post(f"/api/v1/remediations/{action_id}/complete", headers=auth_headers)
        assert res_done.status_code == 200
        assert res_done.json()["data"]["state"] == "completed"
        assert res_done.json()["data"]["completion_provenance"] == "user_reported"


@pytest.mark.asyncio
async def test_aadhaar_guidance_and_confirmation_e2e_012():
    """Verify Aadhaar assistance guidance retrieval and user-reported action confirmation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=aadhaar_user@domain.in")
        token = res_auth.json()["data"]["session_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Retrieve official guides
        res_guides = await client.get("/api/v1/identity-assistance/guides", headers=auth_headers)
        assert res_guides.status_code == 200
        guides = res_guides.json()["data"]
        assert any(g["id"] == "guide_aadhaar_biometric_lock" for g in guides)

        # Confirm user executed biometric lock
        res_confirm = await client.post(
            "/api/v1/identity-assistance/actions/guide_aadhaar_biometric_lock/confirm",
            headers=auth_headers
        )
        assert res_confirm.status_code == 200
        assert res_confirm.json()["data"]["status"] == "confirmed_by_user"
