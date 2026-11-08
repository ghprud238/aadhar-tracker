"""
Unit tests for deterministic severity and confidence scoring (FR-015, ADR-011).
"""
from datetime import datetime, timezone, timedelta
from packages.domain.scoring import calculate_severity_and_confidence, calculate_priority_score
from packages.domain.enums import SeverityLevel, ConfidenceLevel


def test_scoring_password_material_yields_high_severity():
    sev, conf, exp = calculate_severity_and_confidence(
        exposure_categories=["email_address", "passwords"],
        credential_material_present=True,
        exact_match=True
    )
    assert sev == SeverityLevel.HIGH
    assert conf == ConfidenceLevel.HIGH
    assert exp["rules_version"] == "1.0"


def test_scoring_session_tokens_yields_critical_severity():
    sev, conf, exp = calculate_severity_and_confidence(
        exposure_categories=["email_address", "session_token"],
        credential_material_present=True,
        exact_match=True
    )
    assert sev == SeverityLevel.CRITICAL


def test_scoring_spam_list_yields_low_severity():
    sev, conf, exp = calculate_severity_and_confidence(
        exposure_categories=["email_address"],
        credential_material_present=False,
        is_spam_list=True,
        exact_match=True
    )
    assert sev == SeverityLevel.LOW


def test_scoring_unverified_source_reduces_confidence():
    sev, conf, exp = calculate_severity_and_confidence(
        exposure_categories=["email_address"],
        credential_material_present=False,
        is_unverified=True,
        exact_match=True
    )
    assert conf == ConfidenceLevel.MEDIUM


def test_priority_score_recency_and_bounds():
    now = datetime.now(timezone.utc)
    recent_date = now - timedelta(days=10)
    score_recent, _ = calculate_priority_score(SeverityLevel.HIGH, recent_date)

    old_date = now - timedelta(days=400)
    score_old, _ = calculate_priority_score(SeverityLevel.HIGH, old_date)

    assert score_recent > score_old
    assert score_recent <= 100
    assert score_old >= 0
