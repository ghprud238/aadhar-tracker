package app.suraksha.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.suraksha.data.model.MobileBootstrap
import app.suraksha.ui.components.*
import app.suraksha.ui.theme.*

@Composable
fun ShieldScreen(
    bootstrap: MobileBootstrap,
    currentLanguageCode: String,
    onOpenLanguageSheet: () -> Unit,
    onOpenScamRadar: () -> Unit,
    onOpenQrVerifier: () -> Unit,
    onToggleAutoRelock: () -> Unit,
    onNavigateToVault: () -> Unit,
    onNavigateToActivity: () -> Unit,
    onNavigateToMore: () -> Unit,
    onTriggerScan: () -> Unit
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        // Top Resident App Bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "🇮🇳 CITIZEN IDENTITY SHIELD",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = CyberBlue,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "Aarav Sharma",
                    fontSize = 22.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = TextPrimary
                )
            }

            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                // Language Pill
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(DarkSurface)
                        .border(1.dp, DarkBorder, RoundedCornerShape(12.dp))
                        .clickable(onClick = onOpenLanguageSheet)
                        .padding(horizontal = 8.dp, vertical = 5.dp)
                ) {
                    Text(
                        text = "🌐 ${currentLanguageCode.uppercase()}",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = CyberBlue
                    )
                }

                // Scan Button
                Button(
                    onClick = onTriggerScan,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = ElectricBlue),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    Text("⚡ Scan", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Hero Health & Shield Dial
        HealthDialView(
            healthScore = bootstrap.healthScore,
            shieldStatus = bootstrap.glance.shieldStatus
        )

        Spacer(modifier = Modifier.height(20.dp))

        // Quick Actions 2x2 Grid
        Text(
            text = "QUICK ACTIONS",
            fontSize = 11.sp,
            fontWeight = FontWeight.ExtraBold,
            color = TextMuted,
            letterSpacing = 1.sp
        )

        Spacer(modifier = Modifier.height(8.dp))

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuickActionCard(
                title = "Scam Radar",
                subtitle = "Detect CBI / APKs",
                icon = "🚨",
                borderColor = CriticalRed,
                onClick = onOpenScamRadar,
                modifier = Modifier.weight(1f)
            )
            QuickActionCard(
                title = "Verify QR",
                subtitle = "Offline Pass / UIDAI",
                icon = "📷",
                borderColor = CyberBlue,
                onClick = onOpenQrVerifier,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            val autoRelock = bootstrap.biometricStatus
            QuickActionCard(
                title = if (autoRelock.autoRelockActive) "Relock Now" else "Auto-Relock",
                subtitle = if (autoRelock.autoRelockActive) "${autoRelock.autoRelockSecondsLeft / 60}m Left" else "10-Min KYC Window",
                icon = if (autoRelock.autoRelockActive) "🔓" else "⏱️",
                badge = if (autoRelock.autoRelockActive) "ACTIVE" else null,
                borderColor = if (autoRelock.autoRelockActive) WarningAmber else ShieldEmerald,
                onClick = onToggleAutoRelock,
                modifier = Modifier.weight(1f)
            )
            QuickActionCard(
                title = "Masked Pass",
                subtitle = "UIDAI Compliant",
                icon = "🇮🇳",
                borderColor = Color(0xFF818CF8),
                onClick = onNavigateToVault,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Urgent Alert if present
        if (bootstrap.glance.urgentAlert != null) {
            val urgent = bootstrap.glance.urgentAlert
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(CrimsonDark)
                    .border(1.dp, CriticalRed, RoundedCornerShape(12.dp))
                    .clickable(onClick = onNavigateToActivity)
                    .padding(14.dp)
            ) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "🚨 URGENT ACTION REQUIRED",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = CriticalRed
                        )
                        Text(
                            text = "Score: ${urgent.priorityScore}",
                            fontSize = 11.sp,
                            color = Color(0xFFFCA5A5)
                        )
                    }
                    Text(
                        text = urgent.title,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                    Text(
                        text = "Tap to review compromised records →",
                        fontSize = 11.sp,
                        color = Color(0xFFFEE2E2),
                        modifier = Modifier.padding(top = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(20.dp))
        }

        // Security Telemetry 2x2 Grid
        Text(
            text = "SECURITY TELEMETRY",
            fontSize = 11.sp,
            fontWeight = FontWeight.ExtraBold,
            color = TextMuted,
            letterSpacing = 1.sp
        )

        Spacer(modifier = Modifier.height(8.dp))

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard(
                value = bootstrap.glance.activeMonitoredCount.toString(),
                label = "Monitored IDs",
                footer = "Manage →",
                onClick = onNavigateToMore,
                modifier = Modifier.weight(1f)
            )
            MetricCard(
                value = bootstrap.glance.activeIncidents.toString(),
                label = "Threats Detected",
                footer = if (bootstrap.glance.activeIncidents == 0) "Zero Breaches ✓" else "Review Incidents →",
                valueColor = if (bootstrap.glance.activeIncidents == 0) ShieldEmerald else CriticalRed,
                footerColor = if (bootstrap.glance.activeIncidents == 0) ShieldEmerald else CriticalRed,
                onClick = onNavigateToActivity,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard(
                value = if (bootstrap.biometricStatus.locked) "LOCKED" else "OPEN",
                label = "Biometric Shield",
                footer = "AePS Protection →",
                valueColor = if (bootstrap.biometricStatus.locked) ShieldEmerald else WarningAmber,
                footerColor = ShieldEmerald,
                onClick = onNavigateToVault,
                modifier = Modifier.weight(1f)
            )
            MetricCard(
                value = "1",
                label = "Family Protected",
                footer = "Family Hub →",
                valueColor = CyberBlue,
                footerColor = CyberBlue,
                onClick = onNavigateToMore,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Masked ID Pass Card
        MaskedIdCard(
            maskedNumber = bootstrap.maskedPass.maskedIdentifier,
            complianceText = "Offline Redacted Pass ready for hotels and rental verification under UIDAI Circular 2022.",
            onOpenVault = onNavigateToVault
        )

        Spacer(modifier = Modifier.height(24.dp))
    }
}
