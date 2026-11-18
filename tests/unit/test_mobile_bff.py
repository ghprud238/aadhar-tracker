"""
Unit and Integration Tests for Mobile Backend for Frontend (BFF) Router (/api/v1/mobile).
Tests aggregated, battery-efficient, resilient endpoints powering Native Android and Native iOS applications.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_mobile_bootstrap_initial_state():
    """Verify mobile bootstrap delivers complete startup state in a single network round-trip."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=native_resident@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.get("/api/v1/mobile/bootstrap", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert "data" in body
        data = body["data"]

        # 1. Session verification
        assert data["session"]["email"] == "native_resident@example.com"
        assert data["session"]["role"] in ("consumer_owner", "resident")

        # 2. Glance & Shield status
        assert data["glance"]["shield_status"] in ("secure", "warning", "critical")
        assert data["glance"]["active_incidents"] == 0

        # 3. Health Score (0-1000)
        health = data["health_score"]
        assert 0 <= health["score"] <= 1000
        assert health["tier"] in ("FORTRESS GUARDIAN", "VIGILANT SENTINEL", "PROTECTED CITIZEN", "ACTION REQUIRED")
        assert len(health["badges"]) >= 3
        assert len(health["pillars"]) >= 3
        assert len(health["top_recommendations"]) >= 1

        # 4. Biometric status
        assert "locked" in data["biometric_status"]
        assert data["biometric_status"]["auto_relock_active"] is False

        # 5. Masked Pass Summary
        assert data["masked_pass"]["masked_identifier"] == "XXXX-XXXX-4819"
        assert data["masked_pass"]["verified"] is True

        # 6. Quick Actions
        assert len(data["quick_actions"]) == 4
        action_ids = [a["id"] for a in data["quick_actions"]]
        assert "scam_radar" in action_ids
        assert "verify_qr" in action_ids
        assert "auto_relock" in action_ids

        # 7. ETag caching header presence
        assert "etag" in res.headers


@pytest.mark.asyncio
async def test_mobile_bootstrap_etag_304_caching():
    """Verify that mobile clients sending If-None-Match receive 304 Not Modified to save battery and data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=caching_user@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # First request
        res1 = await client.get("/api/v1/mobile/bootstrap", headers=headers)
        assert res1.status_code == 200
        etag = res1.headers.get("etag")
        assert etag is not None

        # Second request with matching ETag
        headers["If-None-Match"] = etag
        res2 = await client.get("/api/v1/mobile/bootstrap", headers=headers)
        assert res2.status_code == 304


@pytest.mark.asyncio
async def test_mobile_activity_feed():
    """Verify unified activity feed returns both exposures and radar alerts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=activity_user@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.get("/api/v1/mobile/activity", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert "exposures" in data
        assert "radar_alerts" in data
        assert "active_exposures_count" in data


@pytest.mark.asyncio
async def test_mobile_scam_radar_detection():
    """Verify mobile scam radar detects digital arrest and APK sideload extortion attacks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=scam_test@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Digital arrest attack test
        attack_msg = "You are placed under Digital Arrest by CBI. Stay on Skype video call. 16 packets of MDMA found in parcel."
        res = await client.post(
            "/api/v1/mobile/scam-radar/analyze",
            headers=headers,
            json={"message_text": attack_msg, "channel": "video_call", "sender_header": "+91 98201 00192"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_scam"] is True
        assert data["threat_level"] in ("critical", "high")
        assert "digital_arrest" in data["scam_category"]
        assert len(data["matched_indicators"]) >= 2
        assert "MHA" in data["mha_official_advisory"] or "Cyber" in data["mha_official_advisory"]


@pytest.mark.asyncio
async def test_mobile_qr_offline_verifier():
    """Verify mobile zero-cloud QR verifier detects valid and tampered passes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=qr_test@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Valid Certified Pass
        valid_payload = '{"suraksha_certified": true, "pass_id": "P1", "claim": {"doc_type": "aadhaar", "masked_id": "XXXX-4819", "recipient": "Taj Lands End", "valid_until": "2030-01-01"}, "pubkey": "ed25519_pk_7fa83b9c02e5b7b1d3f9821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b", "sig": "ed25519_sig_c2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9"}'
        res_valid = await client.post(
            "/api/v1/mobile/qr/verify",
            headers=headers,
            json={"raw_qr_payload": valid_payload, "verifier_entity": "Taj Lands End"}
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["data"]["verified"] is True

        # 2. Tampered Pass
        tampered_payload = '{"suraksha_certified": true, "claim": {}, "pubkey": "short", "sig": "invalid"}'
        res_tampered = await client.post(
            "/api/v1/mobile/qr/verify",
            headers=headers,
            json={"raw_qr_payload": tampered_payload}
        )
        assert res_tampered.status_code == 200
        assert res_tampered.json()["data"]["verified"] is False


@pytest.mark.asyncio
async def test_mobile_auto_relock_window_lifecycle():
    """Verify starting and cancelling temporary 10-minute biometric window."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=relock_user@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Start 10-min window
        res_start = await client.post(
            "/api/v1/mobile/biometric/auto-relock",
            headers=headers,
            json={"action": "start_window", "duration_seconds": 600}
        )
        assert res_start.status_code == 200
        data_start = res_start.json()["data"]
        assert data_start["auto_relock_active"] is True
        assert data_start["seconds_left"] == 600

        # Verify bootstrap reflects active auto-relock
        res_boot = await client.get("/api/v1/mobile/bootstrap", headers=headers)
        assert res_boot.json()["data"]["biometric_status"]["auto_relock_active"] is True

        # 2. Manual immediate relock
        res_relock = await client.post(
            "/api/v1/mobile/biometric/auto-relock",
            headers=headers,
            json={"action": "relock_now"}
        )
        assert res_relock.status_code == 200
        assert res_relock.json()["data"]["auto_relock_active"] is False

        # Verify bootstrap reflects relocked
        res_boot2 = await client.get("/api/v1/mobile/bootstrap", headers=headers)
        assert res_boot2.json()["data"]["biometric_status"]["auto_relock_active"] is False


@pytest.mark.asyncio
async def test_mobile_crash_telemetry_report():
    """Verify client diagnostics and crash telemetry are ingested safely."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=crash_user@example.com")
        token = res_auth.json()["data"]["session_id"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.post(
            "/api/v1/mobile/telemetry/crash-report",
            headers=headers,
            json={
                "device_model": "Pixel 8 Pro / iPhone 15 Pro",
                "os_name": "android",
                "os_version": "14.0",
                "app_version": "2.0.0",
                "error_message": "Network timeout on weak 4G connection",
                "stack_trace": "java.net.SocketTimeoutException: timeout\n\tat okhttp3.internal..."
            }
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "received"
