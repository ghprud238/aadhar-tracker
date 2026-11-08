"""
Deterministic, explainable severity, confidence, and prioritization scoring.
Rules version: 1.0 (Attributable and auditable).
"""
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any
from packages.domain.enums import SeverityLevel, ConfidenceLevel


RULES_VERSION = "1.0"


def calculate_severity_and_confidence(
    exposure_categories: List[str],
    credential_material_present: bool = False,
    is_stealer_log: bool = False,
    is_spam_list: bool = False,
    is_unverified: bool = False,
    is_fabricated: bool = False,
    exact_match: bool = True
) -> Tuple[SeverityLevel, ConfidenceLevel, Dict[str, Any]]:
    """
    Computes deterministic severity and confidence without opaque ML models.
    Returns (severity, confidence, explanation_dict).
    """
    explanation = {
        "rules_version": RULES_VERSION,
        "factors": []
    }

    if not exact_match:
        return SeverityLevel.INFORMATIONAL, ConfidenceLevel.UNCONFIRMED, {
            "rules_version": RULES_VERSION,
            "factors": ["Non-exact match: user-facing alert suppressed"]
        }

    # Determine confidence
    if is_fabricated:
        confidence = ConfidenceLevel.LOW
        explanation["factors"].append("Provider marked content as fabricated")
    elif is_unverified:
        confidence = ConfidenceLevel.MEDIUM
        explanation["factors"].append("Unverified breach claim")
    else:
        confidence = ConfidenceLevel.HIGH
        explanation["factors"].append("Exact verified identifier match with reputable provider provenance")

    # Determine severity
    has_session_tokens = any(c in ["session_token", "session_cookie", "api_key"] for c in exposure_categories)
    has_password = credential_material_present or any("password" in c.lower() for c in exposure_categories)

    if has_session_tokens:
        severity = SeverityLevel.CRITICAL
        explanation["factors"].append("Sensitive active credential or session token detected")
    elif is_stealer_log or has_password:
        severity = SeverityLevel.HIGH
        explanation["factors"].append("Password material or stealer log association confirmed")
    elif is_spam_list:
        severity = SeverityLevel.LOW
        explanation["factors"].append("Email address listed in marketing/spam aggregation")
    else:
        severity = SeverityLevel.MEDIUM
        explanation["factors"].append("Confirmed exposure of email address in historical breach")

    return severity, confidence, explanation


def calculate_priority_score(
    severity: SeverityLevel,
    event_occurred_at: datetime | None,
    corroborating_sources_count: int = 1
) -> Tuple[int, Dict[str, int]]:
    """
    Computes bounded 0-100 ordinal priority score:
    priority_score = min(100, impact_points + recency_points + sensitive_material_points + bounded_corroboration_points)
    """
    # 1. Impact points
    impact_map = {
        SeverityLevel.INFORMATIONAL: 10,
        SeverityLevel.LOW: 25,
        SeverityLevel.MEDIUM: 50,
        SeverityLevel.HIGH: 75,
        SeverityLevel.CRITICAL: 90
    }
    impact_points = impact_map.get(severity, 30)

    # 2. Recency points (strictly based on actual breach event date, never platform ingestion date)
    recency_points = 0
    if event_occurred_at:
        days_old = (datetime.now(timezone.utc) - event_occurred_at).days
        if days_old <= 30:
            recency_points = 20
        elif days_old <= 180:
            recency_points = 10
        elif days_old <= 365:
            recency_points = 5

    # 3. Bounded corroboration points (max 10 points)
    corroboration_points = min(10, max(0, (corroborating_sources_count - 1) * 5))

    total = min(100, impact_points + recency_points + corroboration_points)
    breakdown = {
        "impact_points": impact_points,
        "recency_points": recency_points,
        "corroboration_points": corroboration_points,
        "total_score": total
    }
    return total, breakdown
