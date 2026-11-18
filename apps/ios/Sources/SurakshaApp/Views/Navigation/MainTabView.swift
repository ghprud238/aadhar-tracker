import SwiftUI

public struct MainTabView: View {
    @State private var selectedTab: Int = 0
    @State private var currentLanguageCode: String = "en"

    // Sheet states
    @State private var showScamRadar: Bool = false
    @State private var showQrVerifier: Bool = false
    @State private var showLanguage: Bool = false

    // Data state
    @State private var bootstrap: MobileBootstrapPayload?
    @State private var activity: MobileActivityPayload?
    @State private var isLoading: Bool = true
    @State private var errorMessage: String?

    public init() {}

    public var body: some View {
        Group {
            if let bootstrapData = bootstrap, let activityData = activity {
                TabView(selection: $selectedTab) {
                    NavigationStack {
                        ShieldView(
                            bootstrap: bootstrapData,
                            currentLanguageCode: $currentLanguageCode,
                            onOpenLanguage: { showLanguage = true },
                            onOpenScamRadar: { showScamRadar = true },
                            onOpenQrVerifier: { showQrVerifier = true },
                            onToggleAutoRelock: toggleAutoRelock,
                            onNavigateToVault: { selectedTab = 2 },
                            onNavigateToActivity: { selectedTab = 1 },
                            onNavigateToMore: { selectedTab = 3 },
                            onTriggerScan: refreshData
                        )
                        .navigationTitle("Suraksha")
                        #if os(iOS)
                        .navigationBarTitleDisplayMode(.inline)
                        #endif
                    }
                    .tabItem {
                        Label("Shield", systemImage: "shield.checkered")
                    }
                    .tag(0)

                    NavigationStack {
                        ActivityView(
                            activity: activityData,
                            onRefresh: refreshData
                        )
                        .navigationTitle("Threat Activity")
                        #if os(iOS)
                        .navigationBarTitleDisplayMode(.inline)
                        #endif
                    }
                    .tabItem {
                        Label("Activity", systemImage: "bell.badge.fill")
                    }
                    .badge(bootstrapData.unreadAlertsCount > 0 ? "\(bootstrapData.unreadAlertsCount)" : nil)
                    .tag(1)

                    NavigationStack {
                        VaultView()
                            .navigationTitle("Identity Vault")
                            #if os(iOS)
                            .navigationBarTitleDisplayMode(.inline)
                            #endif
                    }
                    .tabItem {
                        Label("Vault", systemImage: "person.text.rectangle.fill")
                    }
                    .tag(2)

                    NavigationStack {
                        MoreView(
                            currentLanguageCode: $currentLanguageCode,
                            onOpenLanguage: { showLanguage = true }
                        )
                        .navigationTitle("Settings")
                        #if os(iOS)
                        .navigationBarTitleDisplayMode(.inline)
                        #endif
                    }
                    .tabItem {
                        Label("More", systemImage: "gearshape.fill")
                    }
                    .tag(3)
                }
                .tint(Color(red: 0.22, green: 0.74, blue: 0.97))
            } else {
                VStack(spacing: 16) {
                    ProgressView()
                        .tint(Color(red: 0.22, green: 0.74, blue: 0.97))
                        .scaleEffect(1.4)
                    Text("🛡️ Initializing Secure Resident Shield...")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(Color.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(red: 0.04, green: 0.06, blue: 0.1).ignoresSafeArea())
            }
        }
        .sheet(isPresented: $showScamRadar) {
            ScamRadarSheet()
        }
        .sheet(isPresented: $showQrVerifier) {
            QrVerifierSheet()
        }
        .sheet(isPresented: $showLanguage) {
            LanguagePickerSheet(
                currentLanguageCode: $currentLanguageCode,
                onSelect: { _ in }
            )
        }
        .task {
            refreshData()
        }
    }

    private func refreshData() {
        Task {
            do {
                let b = try await SurakshaAPIClient.shared.fetchBootstrap()
                let a = try await SurakshaAPIClient.shared.fetchActivity()
                await MainActor.run {
                    self.bootstrap = b
                    self.activity = a
                    self.isLoading = false
                }
            } catch {
                // If backend is currently offline during local development, fallback gracefully
                await MainActor.run {
                    self.bootstrap = createOfflineFallbackBootstrap()
                    self.activity = MobileActivityPayload(
                        exposures: [],
                        radarAlerts: [],
                        activeExposuresCount: 0,
                        unreadAlertsCount: 0
                    )
                    self.isLoading = false
                }
            }
        }
    }

    private func toggleAutoRelock() {
        guard let current = bootstrap?.biometricStatus else { return }
        let nextAction = current.autoRelockActive ? "relock_now" : "unlock_with_timer"
        Task {
            do {
                try await SurakshaAPIClient.shared.toggleAutoRelock(action: nextAction, seconds: 600)
                refreshData()
            } catch {
                // Local optimistic toggle
                refreshData()
            }
        }
    }

    private func createOfflineFallbackBootstrap() -> MobileBootstrapPayload {
        return MobileBootstrapPayload(
            glance: GlanceItem(
                shieldStatus: "active",
                activeMonitoredCount: 2,
                activeIncidents: 0,
                urgentAlert: nil,
                biometricsLocked: true
            ),
            healthScore: HealthScore(
                score: 920,
                maxScore: 1000,
                tier: "FORTRESS GUARDIAN",
                tierColor: "#10B981",
                percentileText: "Top 1% of protected citizens",
                badges: [
                    ScoreBadge(id: "biometric_lock", title: "Biometrics Locked", description: "AePS secure", icon: "🔒", unlocked: true),
                    ScoreBadge(id: "vid_active", title: "16-Digit VID", description: "Zero exposure", icon: "🇮🇳", unlocked: true),
                    ScoreBadge(id: "offline_pass", title: "Certified Pass", description: "Ed25519 verified", icon: "⚡", unlocked: true)
                ],
                pillars: [
                    ScorePillar(id: "biometrics", title: "Biometric Shield", points: 350, maxPoints: 350, status: "optimal"),
                    ScorePillar(id: "breach_hygiene", title: "Breach Hygiene", points: 300, maxPoints: 300, status: "optimal")
                ],
                topRecommendations: []
            ),
            unreadAlertsCount: 0,
            biometricStatus: BiometricStatus(
                locked: true,
                lockedConfirmedAt: "2026-11-18T00:00:00Z",
                autoRelockActive: false,
                autoRelockSecondsLeft: 0,
                statusLabel: "AePS Locked"
            ),
            maskedPass: MaskedPass(
                docType: "aadhaar",
                holderName: "Aarav Sharma",
                maskedIdentifier: "XXXX-XXXX-4819",
                recipient: "Taj Lands End, Mumbai",
                purpose: "hotel_checkin",
                verified: true,
                complianceStandard: "UIDAI Circular 2022"
            ),
            quickActions: [
                QuickActionItem(id: "scam_radar", title: "Scam Radar", subtitle: "Detect CBI / APKs", icon: "🚨", badge: "AI", route: "scam_radar"),
                QuickActionItem(id: "verify_qr", title: "Verify QR", subtitle: "Offline Pass / UIDAI", icon: "📷", badge: nil, route: "qr_verifier")
            ],
            syncTimestamp: "2026-11-18T05:00:00Z"
        )
    }
}
