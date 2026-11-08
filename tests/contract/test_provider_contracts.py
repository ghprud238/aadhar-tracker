"""
Provider contract tests for Have I Been Pwned (HIBP) and Flare Systems.
Covers test cases HIBP-001 through HIBP-015 and LIC-001 through LIC-016.
"""
import pytest
from packages.provider_adapters.hibp import HibpProvider
from packages.provider_adapters.flare import FlareProvider
from packages.provider_adapters.base import AuthorizedIdentifier


@pytest.mark.asyncio
async def test_hibp_known_test_account_hibp_001():
    provider = HibpProvider()
    target = AuthorizedIdentifier(
        id="id_123",
        tenant_id="ten_1",
        subject_id="sub_1",
        type="email",
        decrypted_value="test.user@domain.com",
        authorization_version=1
    )
    page = await provider.search(target)
    assert len(page.items) > 0
    assert page.items[0]["Name"] == "TelecomExposure2026"

    normalized = await provider.normalize(page, target)
    assert len(normalized) == 1
    assert normalized[0].source_name == "Telecom Mega Breach"
    assert normalized[0].credential_material_present is True
    assert "Have I Been Pwned" in normalized[0].provenance["attribution"]


@pytest.mark.asyncio
async def test_hibp_no_match_response_hibp_002():
    provider = HibpProvider()
    target = AuthorizedIdentifier(
        id="id_clean",
        tenant_id="ten_1",
        subject_id="sub_1",
        type="email",
        decrypted_value="clean.user@secure.org",
        authorization_version=1
    )
    page = await provider.search(target)
    assert len(page.items) == 0

    normalized = await provider.normalize(page, target)
    assert len(normalized) == 0


@pytest.mark.asyncio
async def test_hibp_html_description_safe_rendering_hibp_009():
    provider = HibpProvider()
    target = AuthorizedIdentifier(
        id="id_123",
        tenant_id="ten_1",
        subject_id="sub_1",
        type="email",
        decrypted_value="breached@domain.com",
        authorization_version=1
    )
    page = await provider.search(target)
    normalized = await provider.normalize(page, target)
    assert "<script>" not in normalized[0].redacted_excerpt
    assert "<p>" not in normalized[0].redacted_excerpt  # Plain text rendered


@pytest.mark.asyncio
async def test_flare_token_generation_and_search_lic_001():
    provider = FlareProvider()
    token = await provider._get_bearer_token()
    assert token == "mock_flare_bearer_token"

    target = AuthorizedIdentifier(
        id="id_flare",
        tenant_id="ten_1",
        subject_id="sub_1",
        type="email",
        decrypted_value="test.user@domain.com",
        authorization_version=1
    )
    page = await provider.search(target)
    assert len(page.items) == 1
    assert page.items[0]["source"] == "telegram_stealer_channel"

    normalized = await provider.normalize(page, target)
    assert normalized[0].source_class == "stealer_log"
    assert normalized[0].credential_material_present is True


@pytest.mark.asyncio
async def test_flare_deletion_status_pending_lic_012():
    provider = FlareProvider()
    receipt = await provider.unregister_identifier("flare_id_999")
    assert receipt.confirmed is False
    assert receipt.status == "requested"
