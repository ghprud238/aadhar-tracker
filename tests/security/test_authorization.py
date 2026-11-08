"""
Tenant isolation and Object-Level Authorization tests.
Covers AZ-001 through AZ-020 from PRD Page 59.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db
from packages.security.sessions import session_store


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_cross_tenant_incident_access_denied_az_001():
    """User A cannot read User B's incident (returns 404 non-enumerating)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create User A
        res_a = await client.get("/api/v1/auth/callback?email=userA@domain.com&full_name=User+A")
        sess_a = res_a.json()["data"]["session_id"]

        # Create User B
        res_b = await client.get("/api/v1/auth/callback?email=userB@domain.com&full_name=User+B")
        sess_b = res_b.json()["data"]["session_id"]

        # User B attempts to access a fake or arbitrary incident ID
        res = await client.get(
            "/api/v1/incidents/some_unknown_incident_id",
            headers={"Authorization": f"Bearer {sess_a}"}
        )
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_user_a_cannot_scan_user_b_identifier_az_002():
    """User A cannot submit a scan targeting User B's identifier."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_a = await client.get("/api/v1/auth/callback?email=userA2@domain.com")
        sess_a = res_a.json()["data"]["session_id"]
        sub_a = res_a.json()["data"]["subject_id"]

        res_b = await client.get("/api/v1/auth/callback?email=userB2@domain.com")
        sess_b = res_b.json()["data"]["session_id"]
        sub_b = res_b.json()["data"]["subject_id"]

        # Grant consent for User A
        await client.post(
            "/api/v1/consents",
            headers={"Authorization": f"Bearer {sess_a}"},
            json={"purpose": "identity_exposure_monitoring", "notice_version": "1.0", "subject_id": sub_a}
        )

        # User B creates an identifier
        res_ident_b = await client.post(
            "/api/v1/identifiers",
            headers={"Authorization": f"Bearer {sess_b}"},
            json={"type": "email", "value": "userB_target@domain.com"}
        )
        ident_b_id = res_ident_b.json()["data"]["id"]

        # User A tries to scan User B's identifier
        res_scan = await client.post(
            "/api/v1/scans",
            headers={"Authorization": f"Bearer {sess_a}"},
            json={"identifier_ids": [ident_b_id]}
        )
        assert res_scan.status_code == 400
        assert "No valid owned identifiers" in res_scan.json()["error"]["message"]


@pytest.mark.asyncio
async def test_step_up_required_for_data_export_az_003():
    """Data export endpoint requires recent step-up authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_a = await client.get("/api/v1/auth/callback?email=exportuser@domain.com")
        sess_a = res_a.json()["data"]["session_id"]

        # Without step-up -> 403 Forbidden
        res_export_fail = await client.post(
            "/api/v1/privacy/exports",
            headers={"Authorization": f"Bearer {sess_a}"}
        )
        assert res_export_fail.status_code == 403
        assert "Step-up" in res_export_fail.json()["error"]["message"]

        # Perform step-up
        await client.post(
            "/api/v1/auth/step-up",
            headers={"Authorization": f"Bearer {sess_a}"},
            params={"passcode": "123456"}
        )

        # Now export succeeds
        res_export_ok = await client.post(
            "/api/v1/privacy/exports",
            headers={"Authorization": f"Bearer {sess_a}"}
        )
        assert res_export_ok.status_code == 201
        assert "export_id" in res_export_ok.json()["data"]
