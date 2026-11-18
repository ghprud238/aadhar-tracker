import SwiftUI

public struct HealthDialGauge: View {
    public let healthScore: HealthScore
    public let shieldStatus: String

    public init(healthScore: HealthScore, shieldStatus: String) {
        self.healthScore = healthScore
        self.shieldStatus = shieldStatus
    }

    private var tierColor: Color {
        switch healthScore.tier {
        case "FORTRESS GUARDIAN": return Color(red: 0.06, green: 0.73, blue: 0.51)
        case "VIGILANT SENTINEL": return Color(red: 0.22, green: 0.74, blue: 0.97)
        case "PROTECTED CITIZEN": return Color(red: 0.96, green: 0.62, blue: 0.04)
        default: return Color(red: 0.94, green: 0.27, blue: 0.27)
        }
    }

    private var progress: Double {
        Double(healthScore.score) / Double(healthScore.maxScore)
    }

    public var body: some View {
        VStack(spacing: 16) {
            // Header: Status Pill & Tier Badge
            HStack {
                HStack(spacing: 6) {
                    Circle()
                        .fill(shieldStatus == "critical" ? Color.red : Color.green)
                        .frame(width: 8, height: 8)
                    Text(shieldStatus == "critical" ? "CRITICAL THREAT" : "SHIELD ACTIVE & SECURE")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundStyle(shieldStatus == "critical" ? Color.red : Color.green)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(
                    Capsule()
                        .fill(shieldStatus == "critical" ? Color.red.opacity(0.15) : Color.green.opacity(0.15))
                )
                .overlay(
                    Capsule()
                        .stroke(shieldStatus == "critical" ? Color.red.opacity(0.4) : Color.green.opacity(0.4), lineWidth: 1)
                )

                Spacer()

                Text(healthScore.tier)
                    .font(.system(size: 10, weight: .heavy))
                    .foregroundStyle(tierColor)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(tierColor.opacity(0.15))
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(tierColor.opacity(0.4), lineWidth: 1)
                    )
            }

            // Circular Arc Gauge
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.08), lineWidth: 12)
                    .frame(width: 140, height: 140)

                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(
                        AngularGradient(
                            colors: [tierColor.opacity(0.4), tierColor],
                            center: .center,
                            startAngle: .degrees(-90),
                            endAngle: .degrees(270)
                        ),
                        style: StrokeStyle(lineWidth: 12, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))
                    .frame(width: 140, height: 140)
                    .animation(.spring(duration: 1.0), value: progress)

                VStack(spacing: -2) {
                    Text("\(healthScore.score)")
                        .font(.system(size: 40, weight: .black, design: .rounded))
                        .foregroundStyle(tierColor)
                    Text("/ \(healthScore.maxScore)")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Color.secondary)
                }
            }

            Text(healthScore.percentileText)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))

            // Badges Row
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(healthScore.badges) { badge in
                        HStack(spacing: 6) {
                            Text(badge.icon)
                                .font(.system(size: 13))
                            Text(badge.title)
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(badge.unlocked ? Color.primary : Color.secondary)
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(
                            Capsule()
                                .fill(badge.unlocked ? Color(red: 0.07, green: 0.1, blue: 0.15) : Color(red: 0.05, green: 0.07, blue: 0.1))
                        )
                        .overlay(
                            Capsule()
                                .stroke(badge.unlocked ? Color.blue.opacity(0.4) : Color.white.opacity(0.1), lineWidth: 1)
                        )
                    }
                }
                .padding(.vertical, 4)
            }
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 22)
                .fill(Color(red: 0.05, green: 0.1, blue: 0.18))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22)
                .stroke(tierColor.opacity(0.35), lineWidth: 1.5)
        )
    }
}
