import SwiftUI

public struct ActivityView: View {
    public let activity: MobileActivityPayload
    public let onRefresh: () -> Void
    @State private var selectedTab: Int = 0

    public init(activity: MobileActivityPayload, onRefresh: @escaping () -> Void) {
        self.activity = activity
        self.onRefresh = onRefresh
    }

    public var body: some View {
        VStack(spacing: 0) {
            // Segmented Tab Picker
            Picker("Activity View", selection: $selectedTab) {
                Text("⚠️ Exposures & Breaches (\(activity.exposures.count))").tag(0)
                Text("🔔 Live Alerts (\(activity.radarAlerts.count))").tag(1)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color(red: 0.05, green: 0.08, blue: 0.14))

            ScrollView {
                if selectedTab == 0 {
                    // Exposures Section
                    if activity.exposures.isEmpty {
                        VStack(spacing: 12) {
                            Spacer(minLength: 60)
                            Text("🛡️")
                                .font(.system(size: 48))
                            Text("Zero Active Exposures")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundStyle(Color.primary)
                            Text("No compromised credentials or data breaches found matching your Aadhaar or linked identifiers.")
                                .font(.system(size: 12))
                                .foregroundStyle(Color.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 32)
                            Spacer(minLength: 60)
                        }
                    } else {
                        LazyVStack(spacing: 12) {
                            ForEach(activity.exposures) { inc in
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack {
                                        Text(inc.severity.uppercased())
                                            .font(.system(size: 10, weight: .black))
                                            .foregroundStyle(inc.severity == "critical" ? Color.red : Color.orange)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 3)
                                            .background((inc.severity == "critical" ? Color.red : Color.orange).opacity(0.15))
                                            .clipShape(Capsule())

                                        Spacer()

                                        Text("Score: \(inc.priorityScore)")
                                            .font(.system(size: 11, weight: .semibold))
                                            .foregroundStyle(Color.secondary)
                                    }

                                    Text(inc.title)
                                        .font(.system(size: 14, weight: .bold))
                                        .foregroundStyle(Color.primary)

                                    HStack(spacing: 6) {
                                        Text("Source: \(inc.source)")
                                            .font(.system(size: 11))
                                            .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))

                                        Spacer()

                                        if let dt = inc.createdAt {
                                            Text(dt.prefix(10))
                                                .font(.system(size: 10))
                                                .foregroundStyle(Color.secondary)
                                        }
                                    }

                                    if !inc.exposureCategories.isEmpty {
                                        HStack(spacing: 6) {
                                            ForEach(inc.exposureCategories, id: \.self) { cat in
                                                Text(cat)
                                                    .font(.system(size: 9, weight: .bold))
                                                    .foregroundStyle(Color.secondary)
                                                    .padding(.horizontal, 6)
                                                    .padding(.vertical, 2)
                                                    .background(Color.white.opacity(0.06))
                                                    .clipShape(RoundedRectangle(cornerRadius: 4))
                                            }
                                        }
                                    }
                                }
                                .padding(14)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color(red: 0.07, green: 0.1, blue: 0.16))
                                .clipShape(RoundedRectangle(cornerRadius: 14))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(inc.severity == "critical" ? Color.red.opacity(0.4) : Color.white.opacity(0.1), lineWidth: 1)
                                )
                            }
                        }
                        .padding(16)
                    }
                } else {
                    // Radar Alerts Section
                    if activity.radarAlerts.isEmpty {
                        VStack(spacing: 12) {
                            Spacer(minLength: 60)
                            Text("🔔")
                                .font(.system(size: 48))
                            Text("No Recent Radar Alerts")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundStyle(Color.primary)
                            Text("Real-time notifications from SMS, WhatsApp, and email radar scanners will appear here.")
                                .font(.system(size: 12))
                                .foregroundStyle(Color.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 32)
                            Spacer(minLength: 60)
                        }
                    } else {
                        LazyVStack(spacing: 12) {
                            ForEach(activity.radarAlerts) { alert in
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack {
                                        Text(alert.channel.uppercased())
                                            .font(.system(size: 10, weight: .black))
                                            .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 3)
                                            .background(Color(red: 0.22, green: 0.74, blue: 0.97).opacity(0.15))
                                            .clipShape(Capsule())

                                        Spacer()

                                        Text(alert.status.uppercased())
                                            .font(.system(size: 10, weight: .bold))
                                            .foregroundStyle(alert.status == "delivered" ? Color.green : Color.secondary)
                                    }

                                    Text(alert.payloadPreview)
                                        .font(.system(size: 13))
                                        .foregroundStyle(Color.primary)

                                    HStack {
                                        Text("To: \(alert.recipient)")
                                            .font(.system(size: 11))
                                            .foregroundStyle(Color.secondary)

                                        Spacer()

                                        if let dt = alert.createdAt {
                                            Text(dt.prefix(10))
                                                .font(.system(size: 10))
                                                .foregroundStyle(Color.secondary)
                                        }
                                    }
                                }
                                .padding(14)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color(red: 0.07, green: 0.1, blue: 0.16))
                                .clipShape(RoundedRectangle(cornerRadius: 14))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(Color.white.opacity(0.1), lineWidth: 1)
                                )
                            }
                        }
                        .padding(16)
                    }
                }
            }
            .refreshable {
                onRefresh()
            }
        }
        .background(Color(red: 0.04, green: 0.06, blue: 0.1).ignoresSafeArea())
    }
}
