import SwiftUI

public struct MoreView: View {
    @Binding public var currentLanguageCode: String
    public let onOpenLanguage: () -> Void

    public init(currentLanguageCode: Binding<String>, onOpenLanguage: @escaping () -> Void) {
        self._currentLanguageCode = currentLanguageCode
        self.onOpenLanguage = onOpenLanguage
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                // Resident Profile Banner
                HStack(spacing: 14) {
                    Circle()
                        .fill(Color(red: 0.14, green: 0.38, blue: 0.92))
                        .frame(width: 50, height: 50)
                        .overlay(
                            Text("AS")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundStyle(.white)
                        )

                    VStack(alignment: .leading, spacing: 2) {
                        Text("Aarav Sharma")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundStyle(Color.primary)

                        HStack(spacing: 6) {
                            Text("🛡️ Resident Tier")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))

                            Text("•")
                                .foregroundStyle(Color.secondary)

                            Text("Fortress Guardian")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundStyle(Color.green)
                        }
                    }

                    Spacer()
                }
                .padding(16)
                .background(Color(red: 0.07, green: 0.1, blue: 0.16))
                .clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(
                    RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.1), lineWidth: 1)
                )

                // Settings Group 1: Preferences
                VStack(alignment: .leading, spacing: 10) {
                    Text("PREFERENCES & LOCALIZATION")
                        .font(.system(size: 11, weight: .black))
                        .foregroundStyle(Color.secondary)
                        .tracking(1.0)

                    Button(action: onOpenLanguage) {
                        HStack {
                            Text("🗣️ Regional Language")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundStyle(Color.primary)

                            Spacer()

                            Text(currentLanguageCode.uppercased())
                                .font(.system(size: 13, weight: .bold))
                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))

                            Image(systemName: "chevron.right")
                                .font(.system(size: 12))
                                .foregroundStyle(Color.secondary)
                        }
                        .padding(14)
                        .background(Color(red: 0.07, green: 0.1, blue: 0.16))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .buttonStyle(.plain)
                }

                // Settings Group 2: Compliance & Legal
                VStack(alignment: .leading, spacing: 10) {
                    Text("REGULATORY COMPLIANCE & PRIVACY")
                        .font(.system(size: 11, weight: .black))
                        .foregroundStyle(Color.secondary)
                        .tracking(1.0)

                    VStack(spacing: 1) {
                        HStack {
                            Text("DPDP Act 2023 Compliance")
                                .font(.system(size: 13))
                                .foregroundStyle(Color.primary)
                            Spacer()
                            Text("ACTIVE ✓")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(Color.green)
                        }
                        .padding(14)
                        .background(Color(red: 0.07, green: 0.1, blue: 0.16))

                        Divider().background(Color.white.opacity(0.08))

                        HStack {
                            Text("Zero-Plaintext Invariant")
                                .font(.system(size: 13))
                                .foregroundStyle(Color.primary)
                            Spacer()
                            Text("ENFORCED")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                        }
                        .padding(14)
                        .background(Color(red: 0.07, green: 0.1, blue: 0.16))

                        Divider().background(Color.white.opacity(0.08))

                        HStack {
                            Text("National Helpline 1930 / I4C")
                                .font(.system(size: 13))
                                .foregroundStyle(Color.primary)
                            Spacer()
                            Text("CONNECTED")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(Color.green)
                        }
                        .padding(14)
                        .background(Color(red: 0.07, green: 0.1, blue: 0.16))
                    }
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12).stroke(Color.white.opacity(0.1), lineWidth: 1)
                    )
                }

                // Build & Version Info
                VStack(alignment: .center, spacing: 4) {
                    Text("Suraksha Native iOS Client • v2.4.0 (Build 2026.11)")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(Color.secondary)
                    Text("Designed for Citizen Identity Resilience")
                        .font(.system(size: 10))
                        .foregroundStyle(Color.secondary.opacity(0.8))
                }
                .frame(maxWidth: .infinity)
                .padding(.top, 12)
            }
            .padding(16)
        }
        .background(Color(red: 0.04, green: 0.06, blue: 0.1).ignoresSafeArea())
    }
}
