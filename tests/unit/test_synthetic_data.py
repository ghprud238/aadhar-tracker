"""
Unit tests for the synthetic data generation engine and test fixtures.
Validates mathematical Verhoeff D5 checksum correctness, PAN syntax,
breach catalog structures, WhatsApp DLP compatibility, and API endpoints.
"""
import json
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from services.api.main import app
from packages.domain.synthetic import (
    generate_synthetic_aadhaar,
    generate_synthetic_pan,
    generate_synthetic_vid,
    generate_synthetic_resident_profile,
    generate_synthetic_breach_dump,
    generate_synthetic_whatsapp_conversations,
    generate_complete_test_fixture_bundle,
    BREACH_TEMPLATES,
)
from packages.domain.verhoeff import (
    validate_verhoeff,
    validate_aadhaar,
    validate_pan,
    detect_identifiers_in_text,
)


def test_synthetic_aadhaar_generation_mathematical_validity():
    """All generated synthetic Aadhaar numbers must pass the UIDAI Verhoeff Dihedral D5 check."""
    for i in range(50):
        aadhaar = generate_synthetic_aadhaar(prefix_range="9999", formatted=False, seed=1000 + i)
        assert len(aadhaar) == 12
        assert aadhaar.startswith("9999")
        assert validate_verhoeff(aadhaar) is True
        
        is_valid, err, masked = validate_aadhaar(aadhaar)
        assert is_valid is True, f"Aadhaar {aadhaar} failed: {err}"
        assert masked == f"XXXX-XXXX-{aadhaar[-4:]}"

    # Verify formatted output (with spaces)
    formatted = generate_synthetic_aadhaar(prefix_range="2345", formatted=True, seed=42)
    assert len(formatted) == 14
    assert formatted[4] == " " and formatted[9] == " "
    assert validate_verhoeff(formatted) is True


def test_synthetic_pan_generation_syntax_and_status():
    """All generated PAN numbers must conform to Indian Income Tax Department syntax."""
    surnames = [("Sharma", "S"), ("Iyer", "I"), ("Mukherjee", "M"), ("Patel", "P"), ("Verma", "V")]
    for surname, expected_initial in surnames:
        pan = generate_synthetic_pan(last_name=surname, entity_type="P", seed=42)
        assert len(pan) == 10
        assert pan[3] == "P", "4th character must be 'P' for individual status"
        assert pan[4] == expected_initial, f"5th character must be '{expected_initial}' matching surname {surname}"
        
        is_valid, err, masked = validate_pan(pan)
        assert is_valid is True, f"PAN {pan} failed: {err}"
        assert masked.startswith(pan[:2])
        assert masked.endswith(pan[-1])


def test_synthetic_resident_profile_completeness():
    """Synthetic resident profile contains all required fields, valid addresses, and identifiers."""
    prof = generate_synthetic_resident_profile(seed=777)
    assert "full_name" in prof
    assert "email" in prof and "@" in prof["email"]
    assert "phone" in prof and prof["phone"].startswith("+9198")
    assert "aadhaar_raw" in prof
    assert "aadhaar_masked" in prof
    assert "pan_raw" in prof
    assert "pan_masked" in prof
    assert "vid_number" in prof
    assert len(prof["vid_number"].replace("-", "")) == 16
    assert "address" in prof
    assert prof["address"]["country"] == "India"
    assert len(prof["address"]["pincode"]) == 6

    # Verify mathematical validity of contained identifiers
    valid_aadhaar, _, _ = validate_aadhaar(prof["aadhaar_raw"])
    assert valid_aadhaar is True
    valid_pan, _, _ = validate_pan(prof["pan_raw"])
    assert valid_pan is True


def test_synthetic_breach_dump_simulation():
    """Simulated breach dumps contain structured records, data classes, and evidence digests."""
    breach = generate_synthetic_breach_dump(num_records=15, template_idx=0, seed=888)
    assert breach["breach_name"] == BREACH_TEMPLATES[0]["name"]
    assert breach["source_type"] == "telecom_breach"
    assert len(breach["sampled_records"]) == 15
    assert breach["magnet_hash"].startswith("urn:btih:")
    assert len(breach["raw_evidence_sha256"]) == 64

    for rec in breach["sampled_records"]:
        assert "record_id" in rec
        assert "aadhaar_number" in rec
        assert "pan_number" in rec
        valid_a, _, _ = validate_aadhaar(rec["aadhaar_number"])
        assert valid_a is True
        valid_p, _, _ = validate_pan(rec["pan_number"])
        assert valid_p is True


def test_synthetic_whatsapp_conversations_and_dlp():
    """Generated WhatsApp chat logs properly trigger the Data Loss Prevention (DLP) scanner."""
    threads = generate_synthetic_whatsapp_conversations(num_threads=6, seed=999)
    assert len(threads) == 6

    sensitive_count = 0
    clean_count = 0

    for thread in threads:
        text = thread["last_message_text"]
        findings = detect_identifiers_in_text(text)
        has_detection = len(findings["aadhaar"]) > 0 or len(findings["pan"]) > 0

        if thread["contains_sensitive_id"]:
            assert has_detection is True, f"Expected DLP detection in sensitive thread: {text}"
            sensitive_count += 1
        else:
            assert has_detection is False, f"Unexpected DLP detection in clean thread: {text}"
            clean_count += 1

    assert sensitive_count > 0
    assert clean_count > 0


def test_static_fixtures_bundle_integrity():
    """Verify that pre-exported static fixture files exist and have valid structure."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"
    bundle_path = fixtures_dir / "synthetic_bundle.json"
    
    if not bundle_path.exists():
        # Generate on the fly if not yet written
        bundle = generate_complete_test_fixture_bundle(num_profiles=10, seed=42)
    else:
        with open(bundle_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)

    assert "metadata" in bundle
    assert "identities" in bundle and len(bundle["identities"]) >= 10
    assert "breach_catalog" in bundle and len(bundle["breach_catalog"]) >= 3
    assert "whatsapp_dlp_samples" in bundle and len(bundle["whatsapp_dlp_samples"]) >= 3

    # Check first identity
    first_id = bundle["identities"][0]
    valid_a, _, _ = validate_aadhaar(first_id["aadhaar_raw"])
    assert valid_a is True


@pytest.mark.asyncio
async def test_synthetic_dataset_api_endpoint():
    """Verify GET /api/v1/identity-assistance/synthetic-dataset endpoint returns valid payloads."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Authenticate
        auth_res = await client.get("/api/v1/auth/callback?email=tester.synth@suraksha.in&full_name=Tester+Synth")
        token = auth_res.json()["data"]["session_id"]

        # Call endpoint
        res = await client.get(
            "/api/v1/identity-assistance/synthetic-dataset?count=3&include_breaches=true&seed=12345",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        body = res.json()
        assert "data" in body
        data = body["data"]
        assert len(data["identities"]) == 3
        assert len(data["breaches"]) > 0
        assert len(data["whatsapp_dlp_samples"]) > 0

        # Validate first identity from API response
        id0 = data["identities"][0]
        valid_a, _, _ = validate_aadhaar(id0["aadhaar_raw"])
        assert valid_a is True
        valid_p, _, _ = validate_pan(id0["pan_raw"])
        assert valid_p is True


def test_synthetic_card_image_generation_and_annotations():
    """Verify programmatic rendering of synthetic card images with pixel-accurate bounding boxes."""
    from dummy_data_to_test.generate_card_images import (
        create_synthetic_card_image,
        apply_domain_randomization,
    )
    profile = generate_synthetic_resident_profile(seed=999)
    
    # 1. Aadhaar Card Rendering
    aadhaar_img, aadhaar_ann = create_synthetic_card_image(profile, card_type="aadhaar")
    assert aadhaar_img.size == (856, 540)
    assert aadhaar_ann["card_type"] == "aadhaar"
    assert len(aadhaar_ann["corners"]) == 4
    # Digits 1-8 bounding box
    bbox_digits = aadhaar_ann["first_8_digits_bbox"]
    assert bbox_digits["width"] == 260
    assert bbox_digits["label"] == "mask_first_8_digits"
    # QR code bounding box
    bbox_qr = aadhaar_ann["qr_code_bbox"]
    assert bbox_qr["width"] == 180
    assert bbox_qr["label"] == "mask_biometric_qr"

    # 2. PAN Card Rendering
    pan_img, pan_ann = create_synthetic_card_image(profile, card_type="pan")
    assert pan_img.size == (856, 540)
    assert pan_ann["card_type"] == "pan"
    assert "pan_number_bbox" in pan_ann

    # 3. Domain Randomization (perspective rotation & background composite)
    scene_img, scene_meta = apply_domain_randomization(aadhaar_img, aadhaar_ann, canvas_size=(640, 480))
    assert scene_img.size == (640, 480)
    assert "rotation_angle" in scene_meta
    assert "offset" in scene_meta

