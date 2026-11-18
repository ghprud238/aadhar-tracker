package app.suraksha.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.suraksha.ui.theme.*

@Composable
fun MoreScreen(
    currentLanguageCode: String,
    onOpenLanguageSheet: () -> Unit,
    onOpenScamRadar: () -> Unit,
    onOpenQrVerifier: () -> Unit,
    onSignOut: () -> Unit
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        Text(
            text = "⚙️ Settings & Identity Perimeter",
            fontSize = 22.sp,
            fontWeight = FontWeight.ExtraBold,
            color = TextPrimary
        )
        Text(
            text = "Monitored credentials, step-up security, and privacy compliance.",
            fontSize = 12.sp,
            color = TextSecondary,
            modifier = Modifier.padding(top = 2.dp, bottom = 16.dp)
        )

        // Monitored Identifiers Section
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(DarkSurface)
                .border(1.dp, DarkBorder, RoundedCornerShape(14.dp))
                .padding(16.dp)
        ) {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🔑 Monitored Identifiers",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(EmeraldDark)
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text("1 ACTIVE", color = ShieldEmerald, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(DarkCard)
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("resident@example.com", fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary)
                        Text("Verified Email • Zero Breaches", fontSize = 10.sp, color = ShieldEmerald)
                    }
                    Text("✓ Monitored", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = CyberBlue)
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Language & Bhashini Setting
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(DarkSurface)
                .border(1.dp, DarkBorder, RoundedCornerShape(14.dp))
                .clickable(onClick = onOpenLanguageSheet)
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("🗣️ Regional Language", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = TextPrimary)
                    Text("Powered by Project Bhashini AI Engine", fontSize = 10.sp, color = TextSecondary)
                }
                Text("🌐 ${currentLanguageCode.uppercase()} →", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = CyberBlue)
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Step-Up Security
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(DarkSurface)
                .border(1.dp, DarkBorder, RoundedCornerShape(14.dp))
                .padding(16.dp)
        ) {
            Column {
                Text("🛡️ Step-Up Authentication", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = TextPrimary)
                Text(
                    text = "Requires biometric or TOTP confirmation before viewing exposed breach records or rotating keys.",
                    fontSize = 11.sp,
                    color = TextSecondary,
                    modifier = Modifier.padding(top = 4.dp, bottom = 10.dp)
                )
                Button(
                    onClick = {},
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = DarkCard)
                ) {
                    Text("🔐 Elevate Session (Active for 5 min)", fontSize = 12.sp, color = CyberBlue)
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Sign Out Button
        OutlinedButton(
            onClick = onSignOut,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = CriticalRed)
        ) {
            Text("Sign Out", fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}
