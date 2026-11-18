import Foundation

public struct ScoreBadge: Codable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let description: String
    public let icon: String
    public let unlocked: Bool
}

public struct ScorePillar: Codable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let points: Int
    public let maxPoints: Int
    public let status: String

    enum CodingKeys: String, CodingKey {
        case id, title, points, status
        case maxPoints = "max_points"
    }
}

public struct HealthScore: Codable, Sendable {
    public let score: Int
    public let maxScore: Int
    public let tier: String
    public let tierColor: String
    public let percentileText: String
    public let badges: [ScoreBadge]
    public let pillars: [ScorePillar]
    public let topRecommendations: [String]

    enum CodingKeys: String, CodingKey {
        case score, tier, badges, pillars
        case maxScore = "max_score"
        case tierColor = "tier_color"
        case percentileText = "percentile_text"
        case topRecommendations = "top_recommendations"
    }
}

public struct BiometricStatus: Codable, Sendable {
    public let locked: Bool
    public let lockedConfirmedAt: String?
    public let autoRelockActive: Bool
    public let autoRelockSecondsLeft: Int
    public let statusLabel: String

    enum CodingKeys: String, CodingKey {
        case locked
        case lockedConfirmedAt = "locked_confirmed_at"
        case autoRelockActive = "auto_relock_active"
        case autoRelockSecondsLeft = "auto_relock_seconds_left"
        case statusLabel = "status_label"
    }
}

public struct MaskedPass: Codable, Sendable {
    public let docType: String
    public let holderName: String
    public let maskedIdentifier: String
    public let recipient: String
    public let purpose: String
    public let verified: Bool
    public let complianceStandard: String

    enum CodingKeys: String, CodingKey {
        case recipient, purpose, verified
        case docType = "doc_type"
        case holderName = "holder_name"
        case maskedIdentifier = "masked_identifier"
        case complianceStandard = "compliance_standard"
    }
}

public struct QuickActionItem: Codable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let subtitle: String
    public let icon: String
    public let badge: String?
    public let route: String
}

public struct UrgentAlertItem: Codable, Identifiable, Sendable {
    public var id: String { incidentId }
    public let incidentId: String
    public let title: String
    public let severity: String
    public let priorityScore: Int

    enum CodingKeys: String, CodingKey {
        case title, severity
        case incidentId = "incident_id"
        case priorityScore = "priority_score"
    }
}

public struct GlanceItem: Codable, Sendable {
    public let shieldStatus: String
    public let activeMonitoredCount: Int
    public let activeIncidents: Int
    public let urgentAlert: UrgentAlertItem?
    public let biometricsLocked: Bool?

    enum CodingKeys: String, CodingKey {
        case shieldStatus = "shield_status"
        case activeMonitoredCount = "active_monitored_count"
        case activeIncidents = "active_incidents"
        case urgentAlert = "urgent_alert"
        case biometricsLocked = "biometrics_locked"
    }
}

public struct MobileBootstrapPayload: Codable, Sendable {
    public let glance: GlanceItem
    public let healthScore: HealthScore
    public let unreadAlertsCount: Int
    public let biometricStatus: BiometricStatus
    public let maskedPass: MaskedPass
    public let quickActions: [QuickActionItem]
    public let syncTimestamp: String

    enum CodingKeys: String, CodingKey {
        case glance
        case healthScore = "health_score"
        case unreadAlertsCount = "unread_alerts_count"
        case biometricStatus = "biometric_status"
        case maskedPass = "masked_pass"
        case quickActions = "quick_actions"
        case syncTimestamp = "sync_timestamp"
    }
}

public struct ExposureItem: Codable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let severity: String
    public let priorityScore: Int
    public let state: String
    public let exposureCategories: [String]
    public let source: String
    public let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, title, severity, state, source
        case priorityScore = "priority_score"
        case exposureCategories = "exposure_categories"
        case createdAt = "created_at"
    }
}

public struct RadarAlertItem: Codable, Identifiable, Sendable {
    public let id: String
    public let channel: String
    public let status: String
    public let recipient: String
    public let payloadPreview: String
    public let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, channel, status, recipient
        case payloadPreview = "payload_preview"
        case createdAt = "created_at"
    }
}

public struct MobileActivityPayload: Codable, Sendable {
    public let exposures: [ExposureItem]
    public let radarAlerts: [RadarAlertItem]
    public let activeExposuresCount: Int
    public let unreadAlertsCount: Int

    enum CodingKeys: String, CodingKey {
        case exposures
        case radarAlerts = "radar_alerts"
        case activeExposuresCount = "active_exposures_count"
        case unreadAlertsCount = "unread_alerts_count"
    }
}

public struct ScamAnalysisData: Codable, Sendable {
    public let isScam: Bool
    public let threatLevel: String
    public let scamCategory: String
    public let confidenceScore: Double
    public let matchedIndicators: [String]
    public let mhaAdvisory: String
    public let prefilledFir: String

    enum CodingKeys: String, CodingKey {
        case isScam = "is_scam"
        case threatLevel = "threat_level"
        case scamCategory = "scam_category"
        case confidenceScore = "confidence_score"
        case matchedIndicators = "matched_indicators"
        case mhaAdvisory = "mha_official_advisory"
        case prefilledFir = "prefilled_fir_draft"
    }
}

public struct PassVerificationData: Codable, Sendable {
    public let verified: Bool
    public let title: String
    public let securityAudit: String
    public let extractedDetails: [String: String]

    enum CodingKeys: String, CodingKey {
        case verified, title
        case securityAudit = "security_audit"
        case extractedDetails = "extracted_details"
    }
}
