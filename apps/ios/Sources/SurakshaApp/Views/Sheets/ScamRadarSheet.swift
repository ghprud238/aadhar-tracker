import SwiftUI

public struct ScamRadarSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var messageText: String = ""
    @State private var senderInput: String = ""
    @State private var channel: String = "video_call"
    @State private var isAnalyzing: Bool = false
    @State private var result: ScamAnalysisData?
    @State private var copiedFIR: Bool = false

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Header Description
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Zero-cloud heuristic scanner for fake police video calls, WhatsApp extortion, and malicious APK links.")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.secondary)
                    }

                    // Predefined Test Scenarios
                    VStack(alignment: .leading, spacing: 8) {
                        Text("TEST ATTACK SCENARIOS:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(Color.secondary)

                        HStack(spacing: 8) {
                            Button(action: {
                                channel = "video_call"
                                senderInput = "+91 98201 92841"
                                messageText = "You are placed under Digital Arrest by CBI. Stay on Skype video call. 16 packets of MDMA found in FedEx parcel."
                                triggerAnalysis()
                            }) {
                                Text("CBI Call")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(Color.red)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(Color.red.opacity(0.12))
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(Color.red.opacity(0.4), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)

                            Button(action: {
                                channel = "sms"
                                senderInput = "VM-BESCOM"
                                messageText = "Dear consumer, electricity will be disconnected tonight at 9:30 PM. Install BESCOM_update.apk from bit.ly/pay."
                                triggerAnalysis()
                            }) {
                                Text("Power APK")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(Color.orange)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(Color.orange.opacity(0.12))
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(Color.orange.opacity(0.4), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)

                            Button(action: {
                                channel = "sms"
                                senderInput = "+91 88291 00291"
                                messageText = "Traffic police e-challan pending. Warrant issued. Install echallan_parivahan.apk to pay."
                                triggerAnalysis()
                            }) {
                                Text("Traffic Warrant")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(Color.orange)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(Color.orange.opacity(0.12))
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(Color.orange.opacity(0.4), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    // Input Form
                    VStack(alignment: .leading, spacing: 10) {
                        TextField("Sender Header (e.g. +91 98201... or VM-BESCOM)", text: $senderInput)
                            .font(.system(size: 13))
                            .padding(10)
                            .background(Color(red: 0.08, green: 0.12, blue: 0.18))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.white.opacity(0.1), lineWidth: 1))

                        TextEditor(text: $messageText)
                            .font(.system(size: 13))
                            .frame(height: 90)
                            .padding(4)
                            .background(Color(red: 0.08, green: 0.12, blue: 0.18))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.white.opacity(0.1), lineWidth: 1))

                        Button(action: triggerAnalysis) {
                            HStack {
                                Spacer()
                                if isAnalyzing {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Image(systemName: "shield.righthalf.filled")
                                    Text("Analyze Threat Vector")
                                        .font(.system(size: 13, weight: .bold))
                                }
                                Spacer()
                            }
                            .padding(.vertical, 12)
                            .background(Color(red: 0.14, green: 0.38, blue: 0.92))
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }
                        .disabled(messageText.isEmpty || isAnalyzing)
                        .buttonStyle(.plain)
                    }

                    // Results View
                    if let res = result {
                        VStack(alignment: .leading, spacing: 14) {
                            HStack {
                                Text(res.threatLevel.uppercased())
                                    .font(.system(size: 11, weight: .black))
                                    .foregroundStyle(res.isScam ? Color.red : Color.green)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background((res.isScam ? Color.red : Color.green).opacity(0.15))
                                    .clipShape(Capsule())

                                Spacer()

                                Text("\(Int(res.confidenceScore * 100))% CONFIDENCE")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundStyle(Color.secondary)
                            }

                            Text(res.scamCategory.replacingOccurrences(of: "_", with: " ").capitalized)
                                .font(.system(size: 16, weight: .bold))
                                .foregroundStyle(Color.primary)

                            // Matched Indicators
                            VStack(alignment: .leading, spacing: 6) {
                                Text("MATCHED INDICATORS:")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundStyle(Color.secondary)

                                ForEach(res.matchedIndicators, id: \.self) { ind in
                                    HStack(spacing: 6) {
                                        Image(systemName: "exclamationmark.triangle.fill")
                                            .font(.system(size: 11))
                                            .foregroundStyle(Color.orange)
                                        Text(ind)
                                            .font(.system(size: 12))
                                            .foregroundStyle(Color.primary)
                                    }
                                }
                            }

                            // Advisory Card
                            VStack(alignment: .leading, spacing: 6) {
                                Text("MHA / I4C OFFICIAL ADVISORY")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))

                                Text(res.mhaAdvisory)
                                    .font(.system(size: 12))
                                    .foregroundStyle(Color.secondary)
                            }
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color(red: 0.08, green: 0.12, blue: 0.2))
                            .clipShape(RoundedRectangle(cornerRadius: 10))

                            // FIR Draft
                            if !res.prefilledFir.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack {
                                        Text("PREFILLED 1930 FIR DRAFT")
                                            .font(.system(size: 10, weight: .bold))
                                            .foregroundStyle(Color.secondary)

                                        Spacer()

                                        Button(action: {
                                            #if os(iOS)
                                            UIPasteboard.general.string = res.prefilledFir
                                            #endif
                                            copiedFIR = true
                                        }) {
                                            Text(copiedFIR ? "✓ Copied" : "Copy FIR")
                                                .font(.system(size: 10, weight: .bold))
                                                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                        }
                                    }

                                    Text(res.prefilledFir)
                                        .font(.system(size: 11, design: .monospaced))
                                        .foregroundStyle(Color.primary)
                                        .padding(10)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .background(Color(red: 0.04, green: 0.06, blue: 0.1))
                                        .clipShape(RoundedRectangle(cornerRadius: 8))
                                }
                            }
                        }
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 14)
                                .fill(Color(red: 0.06, green: 0.09, blue: 0.15))
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 14)
                                .stroke(res.isScam ? Color.red.opacity(0.4) : Color.green.opacity(0.4), lineWidth: 1.5)
                        )
                    }
                }
                .padding(20)
            }
            .navigationTitle("🚨 Scam Radar")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }

    private func triggerAnalysis() {
        guard !messageText.isEmpty else { return }
        isAnalyzing = true
        Task {
            do {
                let res = try await SurakshaAPIClient.shared.analyzeScam(
                    message: messageText,
                    channel: channel,
                    sender: senderInput.isEmpty ? nil : senderInput
                )
                await MainActor.run {
                    self.result = res
                    self.isAnalyzing = false
                    self.copiedFIR = false
                }
            } catch {
                await MainActor.run {
                    self.isAnalyzing = false
                }
            }
        }
    }
}
