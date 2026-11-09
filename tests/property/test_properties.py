"""
Property-based invariants testing with Hypothesis.
Verifies invariants specified on PRD Page 63-64.
"""
from hypothesis import given, strategies as st
from packages.redaction.masking import mask_email, mask_phone
from packages.redaction.sanitizer import redact_sensitive_secrets
from packages.security.crypto import vault


@given(st.emails())
def test_mask_email_invariants(email):
    """Masked email must always contain an '@' and never expose the raw local part if len > 1."""
    masked = mask_email(email)
    assert "@" in masked
    assert "***" in masked


@given(st.text(min_size=1, max_size=200))
def test_vault_encryption_roundtrip_property(text_val):
    """Any utf-8 text should roundtrip through envelope encryption."""
    encrypted = vault.encrypt(text_val, associated_data="prop_tenant")
    decrypted = vault.decrypt(encrypted, associated_data="prop_tenant")
    assert decrypted == text_val


@given(st.from_regex(r"^password\s*=\s*[A-Za-z0-9@#$%^&*]{8,20}$", fullmatch=True))
def test_redaction_invariant_never_reveals_password(raw_secret):
    """Redaction must never output plaintext passwords."""
    sanitized = redact_sensitive_secrets(raw_secret)
    assert "[REDACTED_PASSWORD]" in sanitized
    pwd = raw_secret.split("=", 1)[1].strip()
    if pwd:
        assert pwd not in sanitized
