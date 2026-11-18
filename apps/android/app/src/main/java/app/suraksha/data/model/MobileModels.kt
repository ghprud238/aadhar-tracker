package app.suraksha.data.model

data class ScoreBadge(
    val id: String,
    val title: String,
    val description: String,
    val icon: String,
    val unlocked: Boolean
)

data class ScorePillar(
    val id: String,
    val title: String,
    val points: Int,
    val maxPoints: Int,
    val status: String
)

data class HealthScore(
    val score: Int,
    val maxScore: Int,
    val tier: String,
    val tierColor: String,
    val percentileText: String,
    val badges: List<ScoreBadge>,
    val pillars: List<ScorePillar>,
    val topRecommendations: List<String>
)

data class BiometricStatus(
    val locked: Boolean,
    val lockedConfirmedAt: String?,
    val autoRelockActive: Boolean,
    val autoRelockSecondsLeft: Int,
    val statusLabel: String
)

data class MaskedPass(
    val docType: String,
    val holderName: String,
    val maskedIdentifier: String,
    val recipient: String,
    val purpose: String,
    val verified: Boolean,
    val complianceStandard: String
)

data class QuickAction(
    val id: String,
    val title: String,
    val subtitle: String,
    val icon: String,
    val badge: String?,
    val route: String
)

data class UrgentAlert(
    val incidentId: String,
    val title: String,
    val severity: String,
    val priorityScore: Int
)

data class GlanceData(
    val shieldStatus: String,
    val activeMonitoredCount: Int,
    val activeIncidents: Int,
    val urgentAlert: UrgentAlert?,
    val biometricsLocked: Boolean
)

data class MobileBootstrap(
    val sessionEmail: String,
    val sessionRole: String,
    val glance: GlanceData,
    val healthScore: HealthScore,
    val unreadAlertsCount: Int,
    val biometricStatus: BiometricStatus,
    val maskedPass: MaskedPass,
    val quickActions: List<QuickAction>,
    val syncTimestamp: String
)

data class ExposureIncident(
    val id: String,
    val title: String,
    val severity: String,
    val priorityScore: Int,
    val state: String,
    val exposureCategories: List<String>,
    val source: String,
    val createdAt: String?
)

data class RadarAlert(
    val id: String,
    val channel: String,
    val status: String,
    val recipient: String,
    val payloadPreview: String,
    val createdAt: String?
)

data class MobileActivity(
    val exposures: List<ExposureIncident>,
    val radarAlerts: List<RadarAlert>,
    val activeExposuresCount: Int,
    val unreadAlertsCount: Int
)

data class ScamAnalysisResult(
    val isScam: Boolean,
    val threatLevel: String,
    val scamCategory: String,
    val confidenceScore: Double,
    val matchedIndicators: List<String>,
    val mhaAdvisory: String,
    val prefilledFir: String
)

data class PassVerificationResult(
    val verified: Boolean,
    val title: String,
    val securityAudit: String,
    val extractedDetails: Map<String, String>
)
