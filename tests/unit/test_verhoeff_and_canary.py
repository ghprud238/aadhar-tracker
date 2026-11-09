"""
Unit and integration tests for Verhoeff validation, Aadhaar/PAN canary testing,
and WhatsApp Data Loss Prevention (DLP) integration.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from services.api.database import init_db
from packages.domain.verhoeff import (
    validate_verhoeff,
    generate_verhoeff_checksum,
    validate_aadhaar,
    validate_pan,
    detect_identifiers_in_text,
    CANARY_TEST_PRESETS,
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


def test_verhoeff_checksum_algorithm():
    # Known valid Aadhaar numbers with Verhoeff checksum
    assert validate_verhoeff("999941057058") is True
    assert validate_verhoeff("999900000016") is True
    assert validate_verhoeff("234567890124") is True
    assert validate_verhoeff("999999999999") is True

    # Single digit corruption / transposition catches
    assert validate_verhoeff("999941057059") is False
    assert validate_verhoeff("999941057085") is False  # Transposition error
    assert validate_verhoeff("123456789012") is False


def test_aadhaar_validation_rules():
    # Valid Aadhaar with spaces
    valid, err, masked = validate_aadhaar("9999 4105 7058")
    assert valid is True
    assert masked == "XXXX-XXXX-7058"
    assert err == ""

    # Starting with 0 or 1 is invalid in Aadhaar
    valid, err, masked = validate_aadhaar("0123 4567 8901")
    assert valid is False
    assert "cannot start with 0 or 1" in err

    # Wrong length
    valid, err, masked = validate_aadhaar("9999 4105 70")
    assert valid is False
    assert "exactly 12 digits" in err


def test_pan_validation_rules():
    # Valid PAN
    valid, err, masked = validate_pan("ABCDE1234F")
    assert valid is True
    assert masked == "AB***12*F"

    # Invalid format (wrong structure)
    valid, err, masked = validate_pan("ABCD12345F")
    assert valid is False
    assert "Invalid PAN format" in err


def test_detect_identifiers_in_whatsapp_text():
    sample_text = (
        "Hello Ramesh, please find my Aadhaar 9999 4105 7058 and PAN ABCDE1234F for hotel check-in. "
        "Also my friend's Aadhaar is 2345 6789 0124."
    )
    findings = detect_identifiers_in_text(sample_text)
    assert len(findings["aadhaar"]) == 2
    assert findings["aadhaar"][0]["masked"] == "XXXX-XXXX-7058"
    assert findings["aadhaar"][1]["masked"] == "XXXX-XXXX-0124"
    assert len(findings["pan"]) == 1
    assert findings["pan"][0]["masked"] == "AB***12*F"


@pytest.mark.asyncio
async def test_whatsapp_webhook_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Challenge verification
        res = await client.get("/api/v1/integrations/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=suraksha_secure_whatsapp_token_2026&hub.challenge=CHALLENGE_CODE_123")
        assert res.status_code == 200
        assert res.text == "CHALLENGE_CODE_123"


@pytest.mark.asyncio
async def test_whatsapp_simulate_share_detects_unmasked_aadhaar():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sign in to obtain session token
        res_auth = await client.get("/api/v1/auth/callback?email=citizen@suraksha.in&full_name=Aarav+Sharma")
        token = res_auth.json()["data"]["session_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Clean message - no detection
        clean_res = await client.post(
            "/api/v1/integrations/whatsapp/simulate-share",
            headers=auth_headers,
            json={"message_text": "Good morning team, meeting is at 10 AM."}
        )
        assert clean_res.status_code == 200
        assert clean_res.json()["data"]["detected"] is False

        # 2. Insecure message containing unmasked Aadhaar
        leak_res = await client.post(
            "/api/v1/integrations/whatsapp/simulate-share",
            headers=auth_headers,
            json={
                "message_text": "Sharing my Aadhaar 9999 4105 7058 for flight ticket booking.",
                "sender_phone": "+919876543210",
                "channel": "whatsapp_group"
            }
        )
        assert leak_res.status_code == 200
        data = leak_res.json()["data"]
        assert data["detected"] is True
        assert data["incident_created"] is True
        assert "SURAKSHA SECURITY ALERT" in data["automated_whatsapp_alert"]
        assert "XXXX-XXXX-7058" in data["automated_whatsapp_alert"]


@pytest.mark.asyncio
async def test_canary_test_presets_and_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sign in to obtain session token
        res_auth = await client.get("/api/v1/auth/callback?email=citizen@suraksha.in&full_name=Aarav+Sharma")
        token = res_auth.json()["data"]["session_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Fetch presets
        presets_res = await client.get("/api/v1/identity-assistance/canary-presets", headers=auth_headers)
        assert presets_res.status_code == 200
        presets = presets_res.json()["data"]["presets"]
        assert len(presets) >= 4

        # 2. Execute Canary Test with Preset
        exec_res = await client.post(
            "/api/v1/identity-assistance/canary-test",
            headers=auth_headers,
            json={
                "preset_id": "aadhaar_sandbox_1",
                "leak_scenario": "darkweb_market"
            }
        )
        assert exec_res.status_code == 200
        data = exec_res.json()["data"]
        assert data["test_status"] == "success"
        assert data["masked_identifier"] == "XXXX-XXXX-7058"
        assert data["priority_score"] == 95
        assert len(data["pipeline_trace"]) == 6

        # 3. Reject invalid custom Aadhaar checksum
        invalid_res = await client.post(
            "/api/v1/identity-assistance/canary-test",
            headers=auth_headers,
            json={"custom_identifier": "9999 4105 7059"}
        )
        assert invalid_res.status_code == 422
        assert "Verhoeff checksum" in invalid_res.json()["error"]["message"]
