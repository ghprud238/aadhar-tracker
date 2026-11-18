import SwiftUI

public struct MaskedPassCard: View {
    public let maskedNumber: String
    public let complianceText: String
    public let onOpenVault: () -> Void

    public init(
        maskedNumber: String,
        complianceText: String,
        onOpenVault: @escaping () -> Void
    ) {
        self.maskedNumber = maskedNumber
        self.complianceText = complianceText
        self.onOpenVault = onOpenVault
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("GOVERNMENT OF INDIA • MASKED AADHAAR")
                    .font(.system(size: 9, weight: .black))
                    .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                    .tracking(0.8)

                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: 9))
                    Text("VERIFIED")
                        .font(.system(size: 9, weight: .heavy))
                }
                .foregroundStyle(Color(red: 0.06, green: 0.73, blue: 0.51))
                .padding(.horizontal, 6)
                .padding(.vertical, 3)
                .background(
                    Capsule()
                        .fill(Color(red: 0.06, green: 0.73, blue: 0.51).opacity(0.15))
                )
            }

            Text(maskedNumber)
                .font(.system(size: 22, weight: .bold, design: .monospaced))
                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                .tracking(2.0)

            Text(complianceText)
                .font(.system(size: 11))
                .foregroundStyle(Color.secondary)
                .lineSpacing(3)

            Button(action: onOpenVault) {
                HStack {
                    Spacer()
                    Text("Open Identity Vault & Generate Pass →")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                    Spacer()
                }
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color(red: 0.07, green: 0.1, blue: 0.16))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.white.opacity(0.1), lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 18)
                .fill(Color(red: 0.05, green: 0.08, blue: 0.14))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color(red: 0.12, green: 0.23, blue: 0.54), lineWidth: 1.5)
        )
    }
}
