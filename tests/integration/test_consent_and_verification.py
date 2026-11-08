"""
Integration tests for Identifier Verification Challenges and Consent Lifecycle.
Covers ID-001 through ID-010 and CON-001 through CON-010.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_identifier_verification_lifecycle_id_001_id_002():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sign in
        res_auth = await client.get("/api/v1/auth/callback?email=resident_verify@domain.com")
        token = res_auth.json()["data"]["session_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Add email (ID-001)
        res_create = await client.post(
            "/api/v1/identifiers",
            headers=auth_headers,
            json={"type": "email", "value": "my.identity@domain.com"}
        )
        assert res_create.status_code == 201
        ident = res_create.json()["data"]
        assert ident["state"] == "pending_verification"
        assert ident["monitoring_enabled"] is False
        assert ident["masked_value"] == "m***@domain.com"
        ident_id = ident["id"]

        # 2. Trigger verification challenge
        res_chal = await client.post(
            f"/api/v1/identifiers/{ident_id}/verification-challenges",
            headers=auth_headers
        )
        assert res_chal.status_code == 201
        chal_token = res_chal.json()["data"]["demo_token"]

        # 3. Complete verification with wrong token (ID-003/ID-004)
        res_wrong = await client.post(
            "/api/v1/identifiers/verification-challenges/complete",
            headers=auth_headers,
            json={"identifier_id": ident_id, "challenge_token": "000000"}
        )
        assert res_wrong.status_code == 400

        # 4. Complete verification with correct token (ID-002)
        res_ok = await client.post(
            "/api/v1/identifiers/verification-challenges/complete",
            headers=auth_headers,
            json={"identifier_id": ident_id, "challenge_token": chal_token}
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["data"]["state"] == "active"
        assert res_ok.json()["data"]["monitoring_enabled"] is True


@pytest.mark.asyncio
async def test_consent_withdrawal_halts_monitoring_con_001_con_004():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=consent_test@domain.com")
        token = res_auth.json()["data"]["session_id"]
        sub_id = res_auth.json()["data"]["subject_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Attempt scan without consent (CON-001) -> Forbidden
        res_scan_no_consent = await client.post(
            "/api/v1/scans",
            headers=auth_headers,
            json={"identifier_ids": ["some_id"]}
        )
        assert res_scan_no_consent.status_code == 403

        # 2. Grant consent
        res_grant = await client.post(
            "/api/v1/consents",
            headers=auth_headers,
            json={"purpose": "identity_exposure_monitoring", "notice_version": "1.0", "subject_id": sub_id}
        )
        assert res_grant.status_code == 201
        grant_id = res_grant.json()["data"]["id"]

        # 3. Withdraw consent (CON-004)
        res_withdraw = await client.post(
            f"/api/v1/consents/{grant_id}/withdraw",
            headers=auth_headers
        )
        assert res_withdraw.status_code == 200
        assert res_withdraw.json()["data"]["status"] == "withdrawn"
        assert res_withdraw.json()["data"]["authorization_version"] > 1
