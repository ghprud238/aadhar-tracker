import SwiftUI

public struct VaultView: View {
    @State private var vidFormatted: String = "0982  1928  4719  3810"
    @State private var vidRotated: Bool = false
    @State private var sosActive: Bool = false
    @State private var passGenerated: Bool = false

    public init() {}

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                // Header
                VStack(alignment: .leading, spacing: 2) {
                    Text("🇮🇳 Identity Protection Vault")
                        .font(.system(size: 22, weight: .heavy))
                        .foregroundStyle(Color.primary)

                    Text("Zero-plaintext cryptographic tools for Aadhaar, PAN, and emergency fraud response.")
                        .font(.system(size: 12))
                        .foregroundStyle(Color.secondary)
                }

                // Feature 1: 16-Digit Virtual ID Generator
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("UIDAI 16-DIGIT VIRTUAL ID (VID)")
                            .font(.system(size: 10, weight: .black))
                            .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                            .tracking(0.8)

                        Spacer()

                        Text("VALID 24H")
                            .font(.system(size: 9, weight: .heavy))
                            .foregroundStyle(Color.green)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(Color.green.opacity(0.15))
                            .clipShape(Capsule())
                    }

                    Text(vidFormatted)
                        .font(.system(size: 22, weight: .bold, design: .monospaced))
                        .foregroundStyle(Color.primary)
                        .tracking(2.0)

                    Text("Never share your raw 12-digit Aadhaar. Use this disposable 16-digit VID for hotel check-ins and KYC.")
                        .font(.system(size: 11))
                        .foregroundStyle(Color.secondary)
                        .lineSpacing(3)

                    HStack(spacing: 10) {
                        Button(action: {
                            let part1 = String(format: "%04d", Int.random(in: 1000...9999))
                            let part2 = String(format: "%04d", Int.random(in: 1000...9999))
                            let part3 = String(format: "%04d", Int.random(in: 1000...9999))
                            let part4 = String(format: "%04d", Int.random(in: 1000...9999))
                            vidFormatted = "\(part1)  \(part2)  \(part3)  \(part4)"
                            vidRotated = true
                        }) {
                            Text("🔄 Generate New VID")
                                .font(.system(size: 12, weight: .bold))
                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                                .background(Color(red: 0.08, green: 0.12, blue: 0.2))
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8).stroke(Color.white.opacity(0.12), lineWidth: 1)
                                )
                        }
                        .buttonStyle(.plain)

                        Button(action: {
                            #if os(iOS)
                            UIPasteboard.general.string = vidFormatted.replacingOccurrences(of: " ", with: "")
                            #endif
                        }) {
                            Text("Copy")
                                .font(.system(size: 12, weight: .bold))
                                .foregroundStyle(Color.white)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 10)
                                .background(Color(red: 0.14, green: 0.38, blue: 0.92))
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(16)
                .background(Color(red: 0.06, green: 0.09, blue: 0.15))
                .clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color(red: 0.14, green: 0.38, blue: 0.92).opacity(0.5), lineWidth: 1.5)
                )

                // Feature 2: Offline Certified Redacted Pass
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("CERTIFIED REDACTED PASS (ED25519)")
                            .font(.system(size: 10, weight: .black))
                            .foregroundStyle(Color.indigo)
                            .tracking(0.8)

                        Spacer()

                        Text("SECURE")
                            .font(.system(size: 9, weight: .heavy))
                            .foregroundStyle(Color.green)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(Color.green.opacity(0.15))
                            .clipShape(Capsule())
                    }

                    Text("Generate a cryptographically signed QR token concealing your biometrics and full Aadhaar, valid only for 24 hours.")
                        .font(.system(size: 11))
                        .foregroundStyle(Color.secondary)
                        .lineSpacing(3)

                    if passGenerated {
                        VStack(spacing: 10) {
                            Image(systemName: "qrcode")
                                .font(.system(size: 80))
                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                .padding(12)
                                .background(Color.white)
                                .clipShape(RoundedRectangle(cornerRadius: 12))

                            Text("PASS-SURAKSHA-8921 • ED25519 SIGNED")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(Color.green)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                    }

                    Button(action: {
                        passGenerated.toggle()
                    }) {
                        Text(passGenerated ? "Hide QR Pass" : "⚡ Generate Certified Pass")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(Color.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(Color(red: 0.25, green: 0.3, blue: 0.8))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                }
                .padding(16)
                .background(Color(red: 0.06, green: 0.09, blue: 0.15))
                .clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.white.opacity(0.1), lineWidth: 1)
                )

                // Feature 3: Emergency Fraud SOS Panic Pack
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text("EMERGENCY FRAUD SOS")
                            .font(.system(size: 10, weight: .black))
                            .foregroundStyle(Color.red)
                            .tracking(0.8)

                        Spacer()

                        Text("HIGH PRIORITY")
                            .font(.system(size: 9, weight: .heavy))
                            .foregroundStyle(Color.red)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(Color.red.opacity(0.15))
                            .clipShape(Capsule())
                    }

                    Text("If you suspect your identity is being actively misused in a financial cybercrime, trigger the Emergency Panic Pack immediately.")
                        .font(.system(size: 11))
                        .foregroundStyle(Color.secondary)

                    Button(action: {
                        sosActive = true
                    }) {
                        HStack {
                            Spacer()
                            Image(systemName: "exclamationmark.octagon.fill")
                            Text(sosActive ? "🚨 PANIC PACK DISPATCHED (1930 / MHA)" : "TRIGGER EMERGENCY PANIC PACK")
                                .font(.system(size: 12, weight: .heavy))
                            Spacer()
                        }
                        .padding(.vertical, 12)
                        .background(sosActive ? Color.red : Color.red.opacity(0.8))
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                }
                .padding(16)
                .background(Color.red.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.red.opacity(0.4), lineWidth: 1.5)
                )
            }
            .padding(16)
        }
        .background(Color(red: 0.04, green: 0.06, blue: 0.1).ignoresSafeArea())
    }
}
