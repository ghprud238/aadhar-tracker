"""
Comprehensive Unit Tests for Commercial Pivot Features:
1. Embedded Mobile Banking SDK (@suraksha/shield-sdk & SurakshaShieldBackendSDK)
2. B2B Digital Lending Fraud Verification API (NBFC API endpoints)
3. Corporate Executive & Family Office Protection Suite (CISO Portal & VIP Dispatch)
"""
import pytest
import os
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from packages.domain.shield_sdk import SurakshaShieldBackendSDK
from packages.domain.b2b_lending_fraud import LendingFraudVerifier
from dummy_data_to_test.generator import generate_synthetic_aadhaar


# -----------------------------------------------------------------------------
# 1. Tests for Embedded Mobile Banking SDK
# -----------------------------------------------------------------------------

def test_shield_backend_sdk_initialization_and_verhoeff():
    sdk = SurakshaShieldBackendSDK(
        api_key="sk_live_hdfc_bank_test",
        tenant_id="tenant_hdfc_123",
        bank_identifier="HDFC_BANK"
    )
    status = sdk.get_sdk_status()
    assert status["bank_identifier"] == "HDFC_BANK"
    assert status["status"] == "active"

    # Valid Aadhaar
    valid_aadhaar = generate_synthetic_aadhaar(formatted=False, seed=123)
    res_a = sdk.validate_kyc_document("aadhaar", valid_aadhaar)
    assert res_a["is_valid"] is True
    assert res_a["masked_identifier"].startswith("XXXX-XXXX-")

    # Invalid Aadhaar
    res_a_inv = sdk.validate_kyc_document("aadhaar", "123412341234")
    assert res_a_inv["is_valid"] is False
    assert res_a_inv["validation_error"] is not None

    # Valid PAN
    res_p = sdk.validate_kyc_document("pan", "ABCDE1234F")
    assert res_p["is_valid"] is True
    assert res_p["entity_type"] == "Other Entity"

    res_p_ind = sdk.validate_kyc_document("pan", "ABCPK9999Z")
    assert res_p_ind["is_valid"] is True
    assert res_p_ind["entity_type"] == "Individual Resident"


def test_shield_backend_sdk_scam_radar_and_telemetry():
    sdk = SurakshaShieldBackendSDK(
        api_key="sk_live_phonepe_test",
        tenant_id="tenant_phonepe_123",
        bank_identifier="PHONEPE"
    )

    # Scan Digital Arrest
    threat = sdk.evaluate_transaction_message(
        "CBI Mumbai cyber branch: An arrest warrant is issued in your name for money laundering. Join Skype video interrogation immediately.",
        "+919876543210"
    )
    assert threat.is_scam is True
    assert threat.threat_level == "critical"
    assert threat.scam_category == "digital_arrest_impersonation"
    assert len(threat.matched_indicators) > 0
    assert threat.prefilled_fir_draft is not None

    # Scan Clean Transaction
    clean_threat = sdk.evaluate_transaction_message(
        "Your electricity bill of Rs 1,450 for meter 10293 has been paid successfully via UPI.",
        "BESCOM"
    )
    assert clean_threat.is_scam is False
    assert clean_threat.threat_level == "safe"

    assert sdk.get_sdk_status()["calls_evaluated"] == 2


def test_typescript_shield_sdk_build_artifacts():
    """Verifies that the TypeScript @suraksha/shield-sdk compiled bundle exists and has declarations."""
    dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "packages", "shield_sdk", "dist")
    assert os.path.exists(os.path.join(dist_dir, "index.js")), "dist/index.js missing from @suraksha/shield-sdk"
    assert os.path.exists(os.path.join(dist_dir, "index.d.ts")), "dist/index.d.ts missing from @suraksha/shield-sdk"


# -----------------------------------------------------------------------------
# 2. Tests for B2B Digital Lending Fraud API (LendingFraudVerifier & API)
# -----------------------------------------------------------------------------

def test_lending_fraud_verifier_synthetic_identity_detection():
    verifier = LendingFraudVerifier()

    # Repetitive synthetic sequence
    res_synth = verifier.verify_identity(
        document_type="aadhaar",
        document_value="111122223333",
        borrower_entity_type="individual"
    )
    assert res_synth["synthetic_fraud_risk"] in ("critical", "high")
    assert res_synth["recommendation"] == "reject"
    assert any("repetitive" in f.lower() or "synthetic" in f.lower() for f in res_synth["risk_factors"])

    # Valid Aadhaar
    valid_aadhaar = generate_synthetic_aadhaar(formatted=False, seed=456)
    res_valid = verifier.verify_identity(
        document_type="aadhaar",
        document_value=valid_aadhaar,
        borrower_entity_type="individual"
    )
    assert res_valid["is_checksum_valid"] is True
    assert res_valid["synthetic_fraud_risk"] == "low"
    assert res_valid["recommendation"] == "approve"

    # PAN Entity Mismatch (Applicant claims Individual, but PAN is Company 'C')
    res_pan_mismatch = verifier.verify_identity(
        document_type="pan",
        document_value="ABCCT1234F",
        borrower_entity_type="individual"
    )
    assert res_pan_mismatch["is_valid_syntax"] is True
    assert any("does not match declared borrower entity" in f for f in res_pan_mismatch["risk_factors"])


def test_lending_fraud_verifier_document_tampering_and_reused_stamps():
    verifier = LendingFraudVerifier()

    # Forged document reusing hotel check-in stamp
    tampered_text = """
    GOVERNMENT OF INDIA - AADHAAR
    Name: Ramesh Kumar
    DOB: 12/05/1988
    RESTRICTED USE: FOR HOTEL REGISTRATION ONLY - SINGLE-BURN PASS
    UID: 9988 7766 5544
    """
    res_t = verifier.verify_document_tampering(
        document_type="aadhaar",
        ocr_extracted_text=tampered_text,
        declared_dob="12/05/1988"
    )
    assert res_t["tampering_detected"] is True
    assert res_t["reused_hotel_stamp_detected"] is True
    assert res_t["uidai_masking_violation"] is True
    assert res_t["verdict"] == "tampered"

    # Authentic masked document
    authentic_text = """
    GOVERNMENT OF INDIA - MASKED AADHAAR
    Name: Ananya Roy
    DOB: 24/09/1992
    Aadhaar: XXXX-XXXX-4589
    """
    res_auth = verifier.verify_document_tampering(
        document_type="aadhaar",
        ocr_extracted_text=authentic_text,
        declared_dob="24/09/1992"
    )
    assert res_auth["tampering_detected"] is False
    assert res_auth["reused_hotel_stamp_detected"] is False
    assert res_auth["verdict"] == "authentic"


@pytest.mark.asyncio
async def test_b2b_api_endpoints_and_usage_metering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Call B2B Identity Verification
        valid_aadhaar = generate_synthetic_aadhaar(formatted=False, seed=789)
        res_id = await client.post(
            "/api/v1/b2b/verify/identity",
            headers={"X-Suraksha-API-Key": "sk_live_kreditbee_test_key_123"},
            json={
                "document_type": "aadhaar",
                "document_value": valid_aadhaar,
                "declared_name": "Vikram Seth",
                "borrower_entity_type": "individual"
            }
        )
        assert res_id.status_code == 200
        data_id = res_id.json()["data"]
        assert data_id["is_checksum_valid"] is True
        assert data_id["recommendation"] == "approve"

        # 2. Call B2B Document Tamper Verification
        res_dt = await client.post(
            "/api/v1/b2b/verify/document-tamper",
            headers={"X-Suraksha-API-Key": "sk_live_kreditbee_test_key_123"},
            json={
                "document_type": "aadhaar",
                "ocr_extracted_text": "Sample Aadhaar copy with Purpose: Hotel check-in only stamp",
                "declared_dob": "01/01/1990"
            }
        )
        assert res_dt.status_code == 200
        data_dt = res_dt.json()["data"]
        assert data_dt["reused_hotel_stamp_detected"] is True

        # 3. Call B2B Telecom SIM Velocity Check
        res_tel = await client.post(
            "/api/v1/b2b/verify/telecom-sim-velocity",
            headers={"X-Suraksha-API-Key": "sk_live_kreditbee_test_key_123"},
            json={
                "mobile_number": "+919876543219",
                "aadhaar_masked": "XXXX-XXXX-9012"
            }
        )
        assert res_tel.status_code == 200
        data_tel = res_tel.json()["data"]
        assert "sim_velocity_risk" in data_tel
        assert data_tel["associated_sims_on_aadhaar"] >= 1

        # 4. Call B2B Breach Canary Check
        res_canary = await client.post(
            "/api/v1/b2b/verify/breach-canary",
            headers={"X-Suraksha-API-Key": "sk_live_kreditbee_test_key_123"},
            json={
                "email": "hacked_test_user@leak.corp",
                "phone": "+919876549999"
            }
        )
        assert res_canary.status_code == 200
        data_canary = res_canary.json()["data"]
        assert data_canary["credentials_leaked"] is True
        assert data_canary["disbursement_recommendation"] == "decline"

        # 5. Call B2B Usage Metering Dashboard
        res_usage = await client.get(
            "/api/v1/b2b/usage",
            headers={"X-Suraksha-API-Key": "sk_live_kreditbee_test_key_123"}
        )
        assert res_usage.status_code == 200
        data_usage = res_usage.json()["data"]
        assert data_usage["total_calls"] >= 4
        assert data_usage["total_cost_inr"] > 0
        assert "/api/v1/b2b/verify/identity" in data_usage["endpoint_breakdown"]


# -----------------------------------------------------------------------------
# 3. Tests for Corporate Executive & Family Office Protection Suite
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_executive_protection_workflow_and_vip_dispatch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Authenticate session as enterprise CISO
        auth_res = await client.get("/api/v1/auth/callback?email=ciso@tata.com&full_name=Tata+CISO")
        token = auth_res.json()["data"]["session_id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Get CISO Dashboard
        res_dash = await client.get("/api/v1/executive-protection/dashboard", headers=auth_headers)
        assert res_dash.status_code == 200
        data_dash = res_dash.json()["data"]
        assert data_dash["corporate_exposure_index"] >= 350
        assert data_dash["total_executives_protected"] >= 1

        # 2. Enroll a New Board Director
        res_enroll = await client.post(
            "/api/v1/executive-protection/executives",
            headers=auth_headers,
            json={
                "full_name": "Natarajan Chandrasekaran",
                "corporate_email": "n.chandra@tata.com",
                "designation": "Executive Chairman",
                "vip_tier": "c_suite",
                "personal_email": "chandra.personal@gmail.com",
                "personal_phone": "+919820011223",
                "masked_aadhaar": "XXXX-XXXX-8821",
                "pan": "ABCDE9988K"
            }
        )
        assert res_enroll.status_code == 200
        data_exec = res_enroll.json()["data"]
        assert data_exec["full_name"] == "Natarajan Chandrasekaran"
        assert data_exec["assets_count"] == 4
        exec_id = data_exec["id"]

        # 3. List Executives
        res_list = await client.get("/api/v1/executive-protection/executives", headers=auth_headers)
        assert res_list.status_code == 200
        execs = res_list.json()["data"]
        assert any(e["id"] == exec_id for e in execs)

        # 4. Ingest/Simulate Targeted Threat against Executive
        res_threat = await client.post(
            "/api/v1/executive-protection/threats/simulate",
            headers=auth_headers,
            json={
                "executive_id": exec_id,
                "threat_type": "digital_arrest",
                "title": "Extortion Dial Impersonating Enforcement Directorate Mumbai",
                "description": "Scammer syndicate contacted executive's personal phone claiming urgent money-laundering investigation over Skype video call.",
                "severity": "critical"
            }
        )
        assert res_threat.status_code == 200
        data_threat = res_threat.json()["data"]
        assert data_threat["threat_type"] == "digital_arrest"
        assert data_threat["state"] == "active"
        threat_id = data_threat["id"]

        # 5. Dispatch 1-Click VIP Evidence Pack
        res_pack = await client.post(
            f"/api/v1/executive-protection/incidents/{threat_id}/dispatch-pack",
            headers=auth_headers
        )
        assert res_pack.status_code == 200
        data_pack = res_pack.json()["data"]
        assert "SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM" in data_pack["section63_bsa_affidavit"]
        assert data_pack["biometric_lock_pushed"] is True
        assert data_pack["ceir_handset_block_dossier"]["portal"] == "https://ceir.sancharsaathi.gov.in"
        assert "1930" in data_pack["priority_1930_cybercrime_escalation"]["helpline"]
