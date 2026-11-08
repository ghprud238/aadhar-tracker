"""
Unit tests for cryptographic envelope vault, blind indexing, masking, and HTML sanitization.
"""
import pytest
from packages.security.crypto import EnvelopeVault, vault
from packages.redaction.masking import mask_email, mask_phone, mask_aadhaar, mask_pan
from packages.redaction.sanitizer import (
    sanitize_provider_html,
    sanitize_to_plain_text,
    redact_sensitive_secrets,
)


def test_envelope_encryption_roundtrip():
    secret_email = "citizen@example.in"
    tenant_id = "ten_12345"
    encrypted = vault.encrypt(secret_email, associated_data=tenant_id)

    assert encrypted.startswith("v1:")
    assert secret_email not in encrypted

    decrypted = vault.decrypt(encrypted, associated_data=tenant_id)
    assert decrypted == secret_email


def test_envelope_tamper_detection():
    secret = "secret_data"
    encrypted = vault.encrypt(secret, associated_data="tenant_a")
    with pytest.raises(Exception):
        # Mismatched associated data fails authentication
        vault.decrypt(encrypted, associated_data="tenant_b")


def test_blind_indexing_deterministic_within_scope():
    val = "user.name@domain.com"
    idx1 = vault.compute_blind_index(val, scope="tenant_1")
    idx2 = vault.compute_blind_index(" USER.NAME@DOMAIN.COM ", scope="tenant_1")
    idx_other = vault.compute_blind_index(val, scope="tenant_2")

    assert idx1 == idx2
    assert idx1 != idx_other
    assert len(idx1) == 64


def test_masking_rules():
    assert mask_email("aarav@domain.com") == "a***@domain.com"
    assert mask_email("x@domain.com") == "x***@domain.com"
    assert mask_phone("9876543210") == "******3210"
    assert mask_aadhaar("123456789012") == "XXXX-XXXX-9012"
    assert mask_pan("ABCDE1234F") == "XXXXX1234F"


def test_html_sanitization_removes_scripts_and_iframes():
    malicious = "<p>Breach notice <script>alert('xss')</script><iframe src='evil.com'></iframe></p>"
    cleaned = sanitize_provider_html(malicious)
    assert "<script>" not in cleaned
    assert "<iframe>" not in cleaned
    assert "Breach notice" in cleaned


def test_redact_sensitive_secrets_filters_passwords_and_tokens():
    raw_text = "Leaked record: password=SecretP@ssw0rd! and session_id=abc123xyz on host."
    sanitized = redact_sensitive_secrets(raw_text)
    assert "SecretP@ssw0rd!" not in sanitized
    assert "[REDACTED_PASSWORD]" in sanitized
    assert "abc123xyz" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized


def test_redact_sensitive_secrets_filters_aadhaar_numbers():
    text_with_id = "Customer Aadhaar: 9876 5432 1098 submitted for eKYC."
    sanitized = redact_sensitive_secrets(text_with_id)
    assert "9876 5432 1098" not in sanitized
    assert "XXXX-XXXX-1098" in sanitized
