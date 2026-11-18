import SwiftUI

public struct SecurityMetricTile: View {
    public let value: String
    public let label: String
    public let footer: String
    public let valueColor: Color
    public let footerColor: Color
    public let action: () -> Void

    public init(
        value: String,
        label: String,
        footer: String,
        valueColor: Color = Color.primary,
        footerColor: Color = Color(red: 0.22, green: 0.74, blue: 0.97),
        action: @escaping () -> Void
    ) {
        self.value = value
        self.label = label
        self.footer = footer
        self.valueColor = valueColor
        self.footerColor = footerColor
        self.action = action
    }

    public var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 4) {
                Text(value)
                    .font(.system(size: 24, weight: .black, design: .rounded))
                    .foregroundStyle(valueColor)

                Text(label)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(Color.secondary)

                Spacer(minLength: 4)

                Text(footer)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(footerColor)
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(red: 0.07, green: 0.1, blue: 0.16))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.white.opacity(0.1), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}
