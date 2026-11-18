import SwiftUI

public struct ShieldView: View {
    public let bootstrap: MobileBootstrapPayload
    @Binding public var currentLanguageCode: String
    public let onOpenLanguage: () -> Void
    public let onOpenScamRadar: () -> Void
    public let onOpenQrVerifier: () -> Void
    public let onToggleAutoRelock: () -> Void
    public let onNavigateToVault: () -> Void
    public let onNavigateToActivity: () -> Void
    public let onNavigateToMore: () -> Void
    public let onTriggerScan: () -> Void

    public init(
        bootstrap: MobileBootstrapPayload,
        currentLanguageCode: Binding<String>,
        onOpenLanguage: @escaping () -> Void,
        onOpenScamRadar: @escaping () -> Void,
        onOpenQrVerifier: @escaping () -> Void,
        onToggleAutoRelock: @escaping () -> Void,
        onNavigateToVault: @escaping () -> Void,
        onNavigateToActivity: @escaping () -> Void,
        onNavigateToMore: @escaping () -> Void,
        onTriggerScan: @escaping () -> Void
    ) {
        self.bootstrap = bootstrap
        self._currentLanguageCode = currentLanguageCode
        self.onOpenLanguage = onOpenLanguage
        self.onOpenScamRadar = onOpenScamRadar
        self.onOpenQrVerifier = onOpenQrVerifier
        self.onToggleAutoRelock = onToggleAutoRelock
        self.onNavigateToVault = onNavigateToVault
        self.onNavigateToActivity = onNavigateToActivity
        self.onNavigateToMore = onNavigateToMore
        self.onTriggerScan = onTriggerScan
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                // Top Resident Header
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("🇮🇳 CITIZEN IDENTITY SHIELD")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                            .tracking(1.0)

                        Text("Aarav Sharma")
                            .font(.system(size: 24, weight: .heavy))
                            .foregroundStyle(Color.primary)
                    }

                    Spacer()

                    HStack(spacing: 8) {
                        Button(action: onOpenLanguage) {
                            Text("🌐 \(currentLanguageCode.uppercased())")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(Color(red: 0.08, green: 0.12, blue: 0.2))
                                .clipShape(Capsule())
                                .overlay(
                                    Capsule().stroke(Color.white.opacity(0.12), lineWidth: 1)
                                )
                        }
                        .buttonStyle(.plain)

                        Button(action: onTriggerScan) {
                            HStack(spacing: 4) {
                                Image(systemName: "bolt.fill")
                                Text("Scan")
                            }
                            .font(.system(size: 11, weight: .bold))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color(red: 0.14, green: 0.38, blue: 0.92))
                            .clipShape(Capsule())
                        }
                        .buttonStyle(.plain)
                    }
                }

                // Health Dial Gauge
                HealthDialGauge(
                    healthScore: bootstrap.healthScore,
                    shieldStatus: bootstrap.glance.shieldStatus
                )

                // Quick Actions 2x2 Grid
                VStack(alignment: .leading, spacing: 10) {
                    Text("QUICK ACTIONS")
                        .font(.system(size: 11, weight: .black))
                        .foregroundStyle(Color.secondary)
                        .tracking(1.0)

                    HStack(spacing: 12) {
                        QuickActionTile(
                            title: "Scam Radar",
                            subtitle: "Detect CBI / APKs",
                            icon: "🚨",
                            borderColor: Color.red.opacity(0.4),
                            action: onOpenScamRadar
                        )

                        QuickActionTile(
                            title: "Verify QR",
                            subtitle: "Offline Pass / UIDAI",
                            icon: "📷",
                            borderColor: Color(red: 0.22, green: 0.74, blue: 0.97).opacity(0.4),
                            action: onOpenQrVerifier
                        )
                    }

                    HStack(spacing: 12) {
                        let autoRelock = bootstrap.biometricStatus
                        QuickActionTile(
                            title: autoRelock.autoRelockActive ? "Relock Now" : "Auto-Relock",
                            subtitle: autoRelock.autoRelockActive ? "\(autoRelock.autoRelockSecondsLeft / 60)m Left" : "10-Min KYC Window",
                            icon: autoRelock.autoRelockActive ? "🔓" : "⏱️",
                            badge: autoRelock.autoRelockActive ? "ACTIVE" : nil,
                            borderColor: autoRelock.autoRelockActive ? Color.orange.opacity(0.6) : Color.green.opacity(0.4),
                            action: onToggleAutoRelock
                        )

                        QuickActionTile(
                            title: "Masked Pass",
                            subtitle: "UIDAI Compliant",
                            icon: "🇮🇳",
                            borderColor: Color.indigo.opacity(0.4),
                            action: onNavigateToVault
                        )
                    }
                }

                // Urgent Alert (if present)
                if let urgent = bootstrap.glance.urgentAlert {
                    Button(action: onNavigateToActivity) {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text("🚨 URGENT ACTION REQUIRED")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(Color.red)
                                Spacer()
                                Text("Score: \(urgent.priorityScore)")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundStyle(Color.red.opacity(0.8))
                            }
                            Text(urgent.title)
                                .font(.system(size: 14, weight: .bold))
                                .foregroundStyle(Color.primary)
                            Text("Tap to review compromised records →")
                                .font(.system(size: 11))
                                .foregroundStyle(Color.red.opacity(0.9))
                        }
                        .padding(14)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.red.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                        .overlay(
                            RoundedRectangle(cornerRadius: 14)
                                .stroke(Color.red.opacity(0.5), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }

                // Security Telemetry 2x2 Grid
                VStack(alignment: .leading, spacing: 10) {
                    Text("SECURITY TELEMETRY")
                        .font(.system(size: 11, weight: .black))
                        .foregroundStyle(Color.secondary)
                        .tracking(1.0)

                    HStack(spacing: 12) {
                        SecurityMetricTile(
                            value: "\(bootstrap.glance.activeMonitoredCount)",
                            label: "Monitored IDs",
                            footer: "Manage →",
                            action: onNavigateToMore
                        )

                        SecurityMetricTile(
                            value: "\(bootstrap.glance.activeIncidents)",
                            label: "Threats Detected",
                            footer: bootstrap.glance.activeIncidents == 0 ? "Zero Breaches ✓" : "Review Incidents →",
                            valueColor: bootstrap.glance.activeIncidents == 0 ? Color.green : Color.red,
                            footerColor: bootstrap.glance.activeIncidents == 0 ? Color.green : Color.red,
                            action: onNavigateToActivity
                        )
                    }

                    HStack(spacing: 12) {
                        SecurityMetricTile(
                            value: bootstrap.biometricStatus.locked ? "LOCKED" : "OPEN",
                            label: "Biometric Shield",
                            footer: "AePS Protection →",
                            valueColor: bootstrap.biometricStatus.locked ? Color.green : Color.orange,
                            footerColor: Color.green,
                            action: onNavigateToVault
                        )

                        SecurityMetricTile(
                            value: "1",
                            label: "Family Protected",
                            footer: "Family Hub →",
                            valueColor: Color(red: 0.22, green: 0.74, blue: 0.97),
                            footerColor: Color(red: 0.22, green: 0.74, blue: 0.97),
                            action: onNavigateToMore
                        )
                    }
                }

                // Masked Pass Card
                MaskedPassCard(
                    maskedNumber: bootstrap.maskedPass.maskedIdentifier,
                    complianceText: "Offline Redacted Pass ready for hotels and rental verification under UIDAI Circular 2022.",
                    onOpenVault: onNavigateToVault
                )
            }
            .padding(16)
        }
        .background(Color(red: 0.04, green: 0.06, blue: 0.1).ignoresSafeArea())
    }
}
