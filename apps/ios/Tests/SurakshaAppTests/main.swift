import Foundation
@testable import SurakshaApp

print("🧪 Starting Suraksha Native iOS Test Suite...")

// Test 1: Bootstrap JSON Decoding & Model Integrity
do {
    let sampleJSON = """
    {
        "glance": {
            "shield_status": "active",
            "active_monitored_count": 2,
            "active_incidents": 0,
            "urgent_alert": null,
            "biometrics_locked": true
        },
        "health_score": {
            "score": 920,
            "max_score": 1000,
            "tier": "FORTRESS GUARDIAN",
            "tier_color": "#10B981",
            "percentile_text": "Top 1% of protected citizens",
            "badges": [
                {
                    "id": "biometric_lock",
                    "title": "Biometrics Locked",
                    "description": "AePS fraud vector eliminated",
                    "icon": "🔒",
                    "unlocked": true
                }
            ],
            "pillars": [
                {
                    "id": "biometrics",
                    "title": "Biometric Shield",
                    "points": 350,
                    "max_points": 350,
                    "status": "optimal"
                }
            ],
            "top_recommendations": []
        },
        "unread_alerts_count": 0,
        "biometric_status": {
            "locked": true,
            "locked_confirmed_at": "2026-11-18T00:00:00Z",
            "auto_relock_active": false,
            "auto_relock_seconds_left": 0,
            "status_label": "AePS Locked"
        },
        "masked_pass": {
            "doc_type": "aadhaar",
            "holder_name": "Aarav Sharma",
            "masked_identifier": "XXXX-XXXX-4819",
            "recipient": "Hotel Checkin",
            "purpose": "kyc_verification",
            "verified": true,
            "compliance_standard": "UIDAI Circular 2022"
        },
        "quick_actions": [
            {
                "id": "scam_radar",
                "title": "Scam Radar",
                "subtitle": "Detect CBI Extortion",
                "icon": "🚨",
                "badge": "AI",
                "route": "scam_radar"
            }
        ],
        "sync_timestamp": "2026-11-18T04:00:00Z"
    }
    """

    let data = Data(sampleJSON.utf8)
    let payload = try JSONDecoder().decode(MobileBootstrapPayload.self, from: data)

    assert(payload.healthScore.score == 920, "Health score must be 920")
    assert(payload.biometricStatus.locked == true, "Biometrics must be locked")
    assert(payload.maskedPass.maskedIdentifier == "XXXX-XXXX-4819", "Masked identifier mismatch")
    assert(payload.quickActions.count == 1, "Quick actions count mismatch")
    assert(payload.glance.shieldStatus == "active", "Shield status mismatch")
    print("  ✅ Test 1 Passed: MobileBootstrapPayload decoding and field validation")
} catch {
    print("  ❌ Test 1 Failed: \(error)")
    exit(1)
}

// Test 2: ScamRadar Heuristic Analysis Model
do {
    let json = """
    {
        "is_scam": true,
        "threat_level": "critical",
        "scam_category": "digital_arrest",
        "confidence_score": 0.96,
        "matched_indicators": ["skype", "cbi", "arrest"],
        "mha_official_advisory": "Law enforcement never conducts arrests via video call.",
        "prefilled_fir_draft": "I am lodging an urgent complaint under Section 66D IT Act..."
    }
    """
    let res = try JSONDecoder().decode(ScamAnalysisData.self, from: Data(json.utf8))
    assert(res.isScam == true, "Must be flagged as scam")
    assert(res.threatLevel == "critical", "Threat level must be critical")
    assert(res.confidenceScore == 0.96, "Confidence score mismatch")
    assert(res.matchedIndicators.count == 3, "Indicators count mismatch")
    print("  ✅ Test 2 Passed: ScamAnalysisData heuristic response model")
} catch {
    print("  ❌ Test 2 Failed: \(error)")
    exit(1)
}

// Test 3: Offline QR Pass Cryptographic Verification Model
do {
    let json = """
    {
        "verified": true,
        "title": "Suraksha Certified Redacted Pass (Ed25519)",
        "security_audit": "Ed25519 signature cryptographically verified with zero-cloud leakage.",
        "extracted_details": {
            "holder": "Aarav Sharma",
            "doc_type": "aadhaar",
            "masked_id": "XXXX-XXXX-4819",
            "recipient": "Taj Lands End, Mumbai"
        }
    }
    """
    let res = try JSONDecoder().decode(PassVerificationData.self, from: Data(json.utf8))
    assert(res.verified == true, "Verification status must be true")
    assert(res.extractedDetails["masked_id"] == "XXXX-XXXX-4819", "Masked ID claim mismatch")
    assert(res.extractedDetails["doc_type"] == "aadhaar", "Doc type claim mismatch")
    print("  ✅ Test 3 Passed: PassVerificationData zero-cloud offline verification model")
} catch {
    print("  ❌ Test 3 Failed: \(error)")
    exit(1)
}

// Test 4: Activity Payload with Exposures & Radar Alerts
do {
    let json = """
    {
        "exposures": [
            {
                "id": "inc_001",
                "title": "Telecom Data Leak",
                "severity": "critical",
                "priority_score": 92,
                "state": "unresolved",
                "exposure_categories": ["Phone", "Aadhaar"],
                "source": "Dark Web Telegram",
                "created_at": "2026-11-18T02:00:00Z"
            }
        ],
        "radar_alerts": [
            {
                "id": "alert_001",
                "channel": "sms",
                "status": "delivered",
                "recipient": "+91 98*** 12345",
                "payload_preview": "BESCOM power disconnection scam alert",
                "created_at": "2026-11-18T03:00:00Z"
            }
        ],
        "active_exposures_count": 1,
        "unread_alerts_count": 1
    }
    """
    let activity = try JSONDecoder().decode(MobileActivityPayload.self, from: Data(json.utf8))
    assert(activity.activeExposuresCount == 1, "Active exposures count mismatch")
    assert(activity.exposures.first?.severity == "critical", "Exposure severity mismatch")
    assert(activity.radarAlerts.first?.channel == "sms", "Radar channel mismatch")
    print("  ✅ Test 4 Passed: MobileActivityPayload aggregated telemetry model")
} catch {
    print("  ❌ Test 4 Failed: \(error)")
    exit(1)
}

print("🎉 All 4 Suraksha Native iOS Test Suites Passed Successfully (0 failures)!")
