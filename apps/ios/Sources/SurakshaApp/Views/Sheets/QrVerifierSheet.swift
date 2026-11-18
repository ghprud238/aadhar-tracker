import SwiftUI

public struct QrVerifierSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var qrInput: String = ""
    @State private var isVerifying: Bool = false
    @State private var result: PassVerificationData?

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Zero-cloud offline verifier for Suraksha Certified Passes (Ed25519) and UIDAI 2048-bit Secure QR codes.")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.secondary)
                    }

                    // Test payload buttons
                    VStack(alignment: .leading, spacing: 8) {
                        Text("SELECT TEST PAYLOAD:")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(Color.secondary)

                        HStack(spacing: 8) {
                            Button(action: {
                                qrInput = "{\"suraksha_certified\": true, \"pass_id\": \"PASS_SAMPLE_8921\", \"claim\": {\"doc_type\": \"aadhaar\", \"holder\": \"Aarav Sharma\", \"masked_id\": \"XXXX-XXXX-4819\", \"recipient\": \"Taj Lands End, Mumbai\", \"purpose\": \"hotel_checkin\", \"valid_until\": \"2028-12-31\"}, \"pubkey\": \"ed25519_pk_7fa83b9c02e5b7b1d3f9821a4f5c9e2b\", \"sig\": \"ed25519_sig_c2b1d3f821a4f5c9e2b1d3f821a4f5c9\"}"
                                triggerVerification()
                            }) {
                                Text("Valid Pass")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(Color.green)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(Color.green.opacity(0.12))
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(Color.green.opacity(0.4), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)

                            Button(action: {
                                qrInput = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><PrintLetterBarcodeData uid=\"XXXXXXXX4819\" name=\"Aarav Sharma\" dob=\"1990-05-14\" gender=\"M\" signature=\"MIIEvgY...\" />"
                                triggerVerification()
                            }) {
                                Text("UIDAI QR")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(Color(red: 0.22, green: 0.74, blue: 0.97).opacity(0.12))
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(Color(red: 0.22, green: 0.74, blue: 0.97).opacity(0.4), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)

                            Button(action: {
                                qrInput = "{\"tampered\": true, \"sig\": \"invalid\"}"
                                triggerVerification()
                            }) {
                                Text("Tampered")
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
                        }
                    }

                    // Raw Payload input
                    VStack(alignment: .leading, spacing: 10) {
                        TextEditor(text: $qrInput)
                            .font(.system(size: 12, design: .monospaced))
                            .frame(height: 100)
                            .padding(4)
                            .background(Color(red: 0.08, green: 0.12, blue: 0.18))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.white.opacity(0.1), lineWidth: 1))

                        Button(action: triggerVerification) {
                            HStack {
                                Spacer()
                                if isVerifying {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Image(systemName: "qrcode.viewfinder")
                                    Text("Cryptographically Verify QR")
                                        .font(.system(size: 13, weight: .bold))
                                }
                                Spacer()
                            }
                            .padding(.vertical, 12)
                            .background(Color(red: 0.14, green: 0.38, blue: 0.92))
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }
                        .disabled(qrInput.isEmpty || isVerifying)
                        .buttonStyle(.plain)
                    }

                    // Result View
                    if let res = result {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                HStack(spacing: 6) {
                                    Image(systemName: res.verified ? "checkmark.shield.fill" : "xmark.shield.fill")
                                    Text(res.verified ? "CRYPTOGRAPHICALLY AUTHENTIC" : "INVALID / TAMPERED")
                                        .font(.system(size: 11, weight: .black))
                                }
                                .foregroundStyle(res.verified ? Color.green : Color.red)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background((res.verified ? Color.green : Color.red).opacity(0.15))
                                .clipShape(Capsule())

                                Spacer()
                            }

                            Text(res.title)
                                .font(.system(size: 16, weight: .bold))
                                .foregroundStyle(Color.primary)

                            Text(res.securityAudit)
                                .font(.system(size: 11))
                                .foregroundStyle(Color.secondary)

                            Divider()
                                .background(Color.white.opacity(0.1))

                            VStack(alignment: .leading, spacing: 8) {
                                Text("EXTRACTED CLAIMS:")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))

                                ForEach(res.extractedDetails.sorted(by: { $0.key < $1.key }), id: \.key) { key, val in
                                    HStack {
                                        Text(key.replacingOccurrences(of: "_", with: " ").capitalized)
                                            .font(.system(size: 12))
                                            .foregroundStyle(Color.secondary)
                                        Spacer()
                                        Text(val)
                                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                            .foregroundStyle(Color.primary)
                                    }
                                    .padding(.vertical, 2)
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
                                .stroke(res.verified ? Color.green.opacity(0.4) : Color.red.opacity(0.4), lineWidth: 1.5)
                        )
                    }
                }
                .padding(20)
            }
            .navigationTitle("📷 Verify QR")
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

    private func triggerVerification() {
        guard !qrInput.isEmpty else { return }
        isVerifying = true
        Task {
            do {
                let res = try await SurakshaAPIClient.shared.verifyQR(rawQR: qrInput)
                await MainActor.run {
                    self.result = res
                    self.isVerifying = false
                }
            } catch {
                await MainActor.run {
                    self.isVerifying = false
                }
            }
        }
    }
}
