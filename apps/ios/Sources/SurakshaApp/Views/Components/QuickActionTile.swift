import SwiftUI

public struct QuickActionTile: View {
    public let title: String
    public let subtitle: String
    public let icon: String
    public let badge: String?
    public let borderColor: Color
    public let action: () -> Void

    public init(
        title: String,
        subtitle: String,
        icon: String,
        badge: String? = nil,
        borderColor: Color = Color.white.opacity(0.12),
        action: @escaping () -> Void
    ) {
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self.badge = badge
        self.borderColor = borderColor
        self.action = action
    }

    public var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(icon)
                        .font(.system(size: 24))

                    Spacer()

                    if let badge = badge {
                        Text(badge)
                            .font(.system(size: 8, weight: .bold))
                            .foregroundStyle(Color(red: 0.96, green: 0.62, blue: 0.04))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(
                                Capsule()
                                    .fill(Color(red: 0.96, green: 0.62, blue: 0.04).opacity(0.2))
                            )
                            .overlay(
                                Capsule()
                                    .stroke(Color(red: 0.96, green: 0.62, blue: 0.04), lineWidth: 1)
                            )
                    }
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 14, weight: .bold))
                        .foregroundStyle(Color.primary)

                    Text(subtitle)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(Color.secondary)
                        .lineLimit(1)
                }
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(red: 0.07, green: 0.1, blue: 0.16))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(borderColor, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}
