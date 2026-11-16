"""
Comprehensive unit tests for Suraksha high-appeal citizen defense features:
1. Digital Arrest & Malicious APK Scam Radar (ScamRadarEngine + /scam-radar API)
2. Time-Bombed Ephemeral Document Passes (EphemeralPassStore + /ephemeral-passes API)
3. Apple & Google Wallet Digital Pass Generator (WalletPassGenerator + /wallet-pass API)
4. Emergency SOS Panic Pack (PanicPackService + /panic-pack API)
5. Zero-Install Offline Pass Verifier (PassVerifierService + /verify-pass API)
"""
import json
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from packages.domain.schemas import (
    ScamAnalysisRequest,
    EphemeralPassCreateRequest,
    WalletPassRequest,
    PanicPackRequest,
    PassVerificationRequest,
)
from packages.domain.scam_radar import ScamRadarEngine
from packages.domain.ephemeral_passes import EphemeralPassStore
from packages.domain.wallet_passes import WalletPassGenerator
from packages.domain.panic_pack import PanicPackService
from packages.domain.pass_verifier import PassVerifierService


# -----------------------------------------------------------------------------
# 1. Digital Arrest & Malicious APK Scam Radar Tests
# -----------------------------------------------------------------------------

def test_scam_radar_digital_arrest_detection():
    """Verify ScamRadarEngine accurately detects Digital Arrest extortion tactics."""
    scam_text = (
        "Dear citizen, you are placed under DIGITAL ARREST by CBI and Cyber Cell Mumbai. "
        "Your Aadhaar was found in money laundering package at customs. Connect on Skype "
        "video call immediately within 2 hours or police team will arrest you."
    )
    result = ScamRadarEngine.analyze_message(
        message_text=scam_text,
        sender_header="POLICE_HQ",
        channel="video_call"
    )

    assert result.is_scam is True
    assert result.scam_category == "digital_arrest_impersonation"
    assert result.threat_level in ("high", "critical")
    assert result.confidence_score >= 0.8
    assert "MHA" in result.mha_official_advisory
    assert "1930" in result.mha_official_advisory
    assert result.prefilled_fir_draft is not None
    assert "1930" in result.prefilled_fir_draft
    assert "Section 66D" in str(result.statutory_clauses)


def test_scam_radar_malicious_apk_sideload_detection():
    """Verify ScamRadarEngine detects malicious .apk download lures."""
    apk_text = (
        "Dear BESCOM Consumer, your power supply will be disconnected tonight at 9:30 PM "
        "due to unpaid bill. Immediately update your electricity app by downloading: "
        "http://electricity-bills-karnataka.in/update.apk or contact officer."
    )
    result = ScamRadarEngine.analyze_message(
        message_text=apk_text,
        sender_header="+919876543210",
        channel="sms"
    )

    assert result.is_scam is True
    assert result.scam_category == "malicious_apk_sideload"
    assert result.threat_level in ("high", "critical")
    assert any("apk" in flag.lower() for flag in result.matched_indicators)


def test_scam_radar_clean_message():
    """Verify legitimate transactional messages receive low risk scores and no scam alerts."""
    clean_text = "Your one-time password (OTP) for SBI NetBanking transaction of Rs 1,500 is 492019. Valid for 5 mins."
    result = ScamRadarEngine.analyze_message(
        message_text=clean_text,
        sender_header="SBIINB",
        channel="sms"
    )

    assert result.is_scam is False
    assert result.confidence_score < 0.20
    assert result.threat_level == "safe"
    assert result.scam_category == "legitimate_notice"


# -----------------------------------------------------------------------------
# 2. Ephemeral Document Sharing Link Tests
# -----------------------------------------------------------------------------

def test_ephemeral_pass_store_lifecycle_and_single_burn():
    """Verify EphemeralPassStore enforces TTL and atomic single-view burning."""
    store = EphemeralPassStore.get_instance()
    req = EphemeralPassCreateRequest(
        document_type="aadhaar",
        masked_identifier="XXXX-XXXX-9012",
        recipient_entity="Grand Hotel Front Desk",
        purpose="hotel_checkin",
        ttl_seconds=3600,
        single_burn=True,
        encrypted_payload="AES256_TEST_PAYLOAD_CIPHERTEXT"
    )
    pass_dto = store.create_pass(req, tenant_id="tenant_alpha")
    token = pass_dto.token
    assert pass_dto.single_burn is True
    assert pass_dto.views_remaining == 1

    # First read: Successfully retrieves pass and burns single-use pass
    read1 = store.read_and_burn_pass(token)
    assert read1 is not None
    assert read1.token == token
    assert read1.encrypted_payload == "AES256_TEST_PAYLOAD_CIPHERTEXT"
    assert read1.burned is True

    # Second read: Must return None because single-use pass was burned
    read2 = store.read_and_burn_pass(token)
    assert read2 is None


def test_ephemeral_pass_store_multi_view():
    """Verify EphemeralPassStore allows multi-view when single_burn=False."""
    store = EphemeralPassStore.get_instance()
    req = EphemeralPassCreateRequest(
        document_type="pan",
        masked_identifier="ABCXXXX12D",
        recipient_entity="Rental Agency",
        purpose="vehicle_rental",
        ttl_seconds=3600,
        single_burn=False,
        encrypted_payload="PAYLOAD_MULTI_VIEW"
    )
    pass_dto = store.create_pass(req, tenant_id="tenant_alpha")
    token = pass_dto.token

    # Read twice without burn
    read1 = store.read_and_burn_pass(token)
    assert read1 is not None
    assert read1.burned is False

    read2 = store.read_and_burn_pass(token)
    assert read2 is not None
    assert read2.burned is False


# -----------------------------------------------------------------------------
# 3. Apple & Google Wallet Pass Generator Tests
# -----------------------------------------------------------------------------

def test_wallet_pass_generation():
    """Verify WalletPassGenerator produces Apple .pkpass manifest and Google Wallet object."""
    req = WalletPassRequest(
        pass_id="PASS_WAL_123",
        holder_name="Aarav Sharma",
        document_type="Aadhaar",
        masked_identifier="XXXX-XXXX-9012",
        recipient_entity="Lemon Tree Hotel",
        purpose="hotel_checkin",
        valid_until="2026-12-31",
        signer_public_key="ed25519_pk_test_sample",
        signature_hex="ed25519_sig_test_sample"
    )
    wallet = WalletPassGenerator.generate_wallet_pass(req)

    # Apple Wallet validation
    assert wallet.apple_pass_json is not None
    apple = wallet.apple_pass_json
    assert apple["formatVersion"] == 1
    assert "barcodes" in apple
    assert apple["barcodes"][0]["format"] == "PKBarcodeFormatQR"
    assert "generic" in apple
    assert any(f["value"] == "Aarav Sharma" for f in apple["generic"]["secondaryFields"])

    # Google Wallet validation
    assert wallet.google_wallet_jwt_payload is not None
    google = wallet.google_wallet_jwt_payload
    assert "payload" in google
    assert "genericObjects" in google["payload"]
    obj0 = google["payload"]["genericObjects"][0]
    assert obj0["barcode"]["type"] == "QR_CODE"
    assert obj0["header"]["defaultValue"]["value"] == "XXXX-XXXX-9012"


# -----------------------------------------------------------------------------
# 4. Emergency SOS Panic Pack Tests
# -----------------------------------------------------------------------------

def test_panic_pack_service_execution():
    """Verify PanicPackService produces CEIR lock instructions, credit advisory, and Section 63 NCR affidavit."""
    req = PanicPackRequest(
        victim_name="Aarav Sharma",
        lost_device_model="iPhone 15 Pro",
        lost_imei_masked="354892XXXXXX123",
        compromised_docs=["Aadhaar", "PAN"],
        incident_location="Indiranagar 100ft Road, Bengaluru",
        incident_description="Lost wallet and phone during evening commute."
    )
    res = PanicPackService.execute_panic_pack(req)

    assert res.pack_id.startswith("PANIC_")
    assert res.biometric_lock_dispatched is True
    assert "ceir.gov.in" in res.ceir_block_instructions["portal"]
    assert "cibil.com" in res.credit_bureau_fraud_advisory["cibil_link"]
    
    # Section 63 BSA Police Affidavit validation
    affidavit = res.section63_ncr_affidavit
    assert "SECTION 63 BHARATIYA SAKSHYA ADHINIYAM, 2023" in affidavit
    assert "Aarav Sharma" in affidavit
    assert "Indiranagar 100ft Road, Bengaluru" in affidavit
    assert "iPhone 15 Pro" in affidavit
    assert "1930" in res.emergency_helpline_numbers["National Cybercrime Helpline"]


# -----------------------------------------------------------------------------
# 5. Zero-Install Offline Pass Verifier Tests
# -----------------------------------------------------------------------------

def test_pass_verifier_suraksha_certified():
    """Verify PassVerifierService handles Suraksha Certified Passes correctly."""
    valid_payload = json.dumps({
        "suraksha_certified": True,
        "claim": {
            "holder": "Aarav Sharma",
            "masked_id": "XXXX-XXXX-9012",
            "recipient": "Lemon Tree Hotel",
            "purpose": "hotel_checkin",
            "valid_until": "2030-12-31"
        },
        "sig": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pubkey": "abcdef0123456789abcdef0123456789"
    })

    req = PassVerificationRequest(
        raw_qr_payload=valid_payload,
        verifier_entity="Lemon Tree Hotel Reception"
    )
    res = PassVerifierService.verify_pass(req)

    assert res.verified is True
    assert res.pass_type == "suraksha_certified_pass"
    assert res.holder_name == "Aarav Sharma"
    assert res.masked_identifier == "XXXX-XXXX-9012"
    assert res.recipient_entity == "Lemon Tree Hotel"


def test_pass_verifier_uidai_secure_qr():
    """Verify PassVerifierService identifies official UIDAI 2048-bit Secure QR codes."""
    xml_payload = '<PrintLetterBarcodeData name="Aarav Sharma" uid="999912344819" dob="1990-01-01"/>'
    req = PassVerificationRequest(
        raw_qr_payload=xml_payload,
        verifier_entity="Airport Security Kiosk"
    )
    res = PassVerifierService.verify_pass(req)

    assert res.verified is True
    assert res.pass_type == "uidai_secure_qr"
    assert res.holder_name == "Aarav Sharma"
    assert res.masked_identifier == "XXXX-XXXX-4819"


def test_pass_verifier_unknown_payload():
    """Verify PassVerifierService rejects uncertified payloads."""
    req = PassVerificationRequest(
        raw_qr_payload="RANDOM_PLAIN_TEXT_NOT_A_PASS",
        verifier_entity="Visitor Gate"
    )
    res = PassVerifierService.verify_pass(req)

    assert res.verified is False
    assert res.pass_type == "unrecognized_text"


# -----------------------------------------------------------------------------
# 6. FastAPI End-to-End API Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_scam_radar_endpoint():
    """E2E test for POST /api/v1/identity-assistance/scam-radar."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_res = await client.get("/api/v1/auth/callback?email=scam.tester@suraksha.in&full_name=Scam+Tester")
        token = auth_res.json()["data"]["session_id"]

        payload = {
            "message_text": "URGENT: Arrest warrant issued by ED Delhi. Connect on Skype for verification.",
            "sender_header": "CYBER_CELL",
            "channel": "video_call"
        }
        res = await client.post(
            "/api/v1/identity-assistance/scam-radar",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_scam"] is True
        assert data["scam_category"] == "digital_arrest_impersonation"


@pytest.mark.asyncio
async def test_api_ephemeral_pass_lifecycle_endpoints():
    """E2E test for POST & GET /api/v1/identity-assistance/ephemeral-passes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_res = await client.get("/api/v1/auth/callback?email=pass.tester@suraksha.in&full_name=Pass+Tester")
        token = auth_res.json()["data"]["session_id"]

        # Create pass
        create_payload = {
            "document_type": "aadhaar",
            "masked_identifier": "XXXX-XXXX-4819",
            "recipient_entity": "Taj Palace Hotel",
            "purpose": "hotel_checkin",
            "ttl_seconds": 1800,
            "single_burn": True,
            "encrypted_payload": "E2E_ENCRYPTED_BLOB_XYZ"
        }
        create_res = await client.post(
            "/api/v1/identity-assistance/ephemeral-passes",
            json=create_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_res.status_code == 201
        created_data = create_res.json()["data"]
        pass_token = created_data["token"]

        # Read pass (first time - success)
        read_res = await client.get(f"/api/v1/identity-assistance/ephemeral-passes/{pass_token}")
        assert read_res.status_code == 200
        assert read_res.json()["data"]["encrypted_payload"] == "E2E_ENCRYPTED_BLOB_XYZ"

        # Read pass second time - 404 burned
        read_res2 = await client.get(f"/api/v1/identity-assistance/ephemeral-passes/{pass_token}")
        assert read_res2.status_code == 404


@pytest.mark.asyncio
async def test_api_wallet_pass_endpoint():
    """E2E test for POST /api/v1/identity-assistance/wallet-pass."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_res = await client.get("/api/v1/auth/callback?email=wallet.tester@suraksha.in&full_name=Wallet+Tester")
        token = auth_res.json()["data"]["session_id"]

        payload = {
            "pass_id": "PASS_WAL_API",
            "holder_name": "Rohan Deshmukh",
            "document_type": "PAN",
            "masked_identifier": "ABCXXXX12D",
            "recipient_entity": "HDFC Bank Account Opening",
            "purpose": "bank_kyc",
            "valid_until": "2026-12-31",
            "signer_public_key": "ed25519_pk",
            "signature_hex": "ed25519_sig"
        }
        res = await client.post(
            "/api/v1/identity-assistance/wallet-pass",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "apple_pass_json" in data
        assert "google_wallet_jwt_payload" in data
        assert "barcode_payload" in data


@pytest.mark.asyncio
async def test_api_panic_pack_endpoint():
    """E2E test for POST /api/v1/identity-assistance/panic-pack."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_res = await client.get("/api/v1/auth/callback?email=panic.tester@suraksha.in&full_name=Panic+Tester")
        token = auth_res.json()["data"]["session_id"]

        payload = {
            "victim_name": "Kavita Rao",
            "lost_device_model": "Samsung Galaxy S24",
            "lost_imei_masked": "864219XXXXXX999",
            "compromised_docs": ["Aadhaar", "Driving License"],
            "incident_location": "MG Road Metro Station, Bengaluru"
        }
        res = await client.post(
            "/api/v1/identity-assistance/panic-pack",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["biometric_lock_dispatched"] is True
        assert "MG Road Metro Station" in data["section63_ncr_affidavit"]


@pytest.mark.asyncio
async def test_api_verify_pass_endpoint():
    """E2E test for POST /api/v1/identity-assistance/verify-pass."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        valid_json = json.dumps({
            "suraksha_certified": True,
            "claim": {
                "holder": "Kavita Rao",
                "masked_id": "XXXX-XXXX-4321",
                "recipient": "Hotel Royal",
                "purpose": "hotel_checkin",
                "valid_until": "2030-12-31"
            },
            "sig": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
            "pubkey": "abcdef0123456789abcdef0123456789"
        })
        payload = {
            "raw_qr_payload": valid_json,
            "verifier_entity": "Hotel Royal Front Desk"
        }
        res = await client.post(
            "/api/v1/identity-assistance/verify-pass",
            json=payload
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["verified"] is True
        assert data["holder_name"] == "Kavita Rao"
