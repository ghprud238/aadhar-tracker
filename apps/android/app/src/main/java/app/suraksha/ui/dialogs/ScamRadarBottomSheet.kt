package app.suraksha.ui.dialogs

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.suraksha.data.model.ScamAnalysisResult
import app.suraksha.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScamRadarBottomSheet(
    onDismiss: () -> Unit,
    onAnalyze: (message: String, channel: String, sender: String?) -> Unit,
    analysisResult: ScamAnalysisResult?
) {
    var messageText by remember { mutableStateOf("") }
    var senderInput by remember { mutableStateOf("") }
    var channel by remember { mutableStateOf("video_call") }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        scrimColor = Color.Black.copy(alpha = 0.7f)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            Text(
                text = "🚨 Scam & Digital Arrest Threat Radar",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )
            Text(
                text = "Zero-cloud heuristic scanner for fake police video calls, WhatsApp extortion, and malicious APK links.",
                fontSize = 12.sp,
                color = TextSecondary,
                modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
            )

            Text(
                text = "TEST ATTACK SCENARIOS:",
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = TextMuted
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = {
                        channel = "video_call"
                        senderInput = "+91 98201 92841"
                        messageText = "You are placed under Digital Arrest by CBI. Stay on Skype video call. 16 packets of MDMA found in FedEx parcel."
                        onAnalyze(messageText, channel, senderInput)
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("CBI Call", fontSize = 11.sp, color = CriticalRed)
                }

                OutlinedButton(
                    onClick = {
                        channel = "sms"
                        senderInput = "VM-BESCOM"
                        messageText = "Dear consumer, electricity will be disconnected tonight at 9:30 PM. Install BESCOM_update.apk from bit.ly/pay."
                        onAnalyze(messageText, channel, senderInput)
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Power APK", fontSize = 11.sp, color = WarningAmber)
                }

                OutlinedButton(
                    onClick = {
                        channel = "sms"
                        senderInput = "+91 88291 00291"
                        messageText = "Traffic police e-challan pending. Warrant issued. Install echallan_parivahan.apk to pay."
                        onAnalyze(messageText, channel, senderInput)
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Challan APK", fontSize = 11.sp, color = CyberBlue)
                }
            }

            OutlinedTextField(
                value = messageText,
                onValueChange = { messageText = it },
                label = { Text("Paste suspicious SMS or video call claims") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(90.dp),
                shape = RoundedCornerShape(8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = CyberBlue,
                    unfocusedBorderColor = DarkBorder,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                )
            )

            Spacer(modifier = Modifier.height(10.dp))

            Button(
                onClick = {
                    if (messageText.isNotBlank()) {
                        onAnalyze(messageText, channel, senderInput.ifBlank { null })
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFB91C1C)),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("🔍 Scan for Extortion & Phishing", fontWeight = FontWeight.Bold)
            }

            if (analysisResult != null) {
                Spacer(modifier = Modifier.height(14.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(if (analysisResult.isScam) CrimsonDark else DarkCard)
                        .border(
                            1.dp,
                            if (analysisResult.isScam) CriticalRed else ShieldEmerald,
                            RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp)
                ) {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = analysisResult.scamCategory.uppercase().replace('_', ' '),
                                fontWeight = FontWeight.Bold,
                                color = TextPrimary,
                                fontSize = 12.sp
                            )
                            Text(
                                text = analysisResult.threatLevel.uppercase(),
                                fontWeight = FontWeight.ExtraBold,
                                color = if (analysisResult.isScam) CriticalRed else ShieldEmerald,
                                fontSize = 11.sp
                            )
                        }

                        if (analysisResult.isScam) {
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = "🚨 EXTORTION WARNING (Confidence: ${(analysisResult.confidenceScore * 100).toInt()}%)",
                                color = Color(0xFFFCA5A5),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                            analysisResult.matchedIndicators.forEach { ind ->
                                Text("• $ind", fontSize = 10.sp, color = Color(0xFFFEE2E2))
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "OFFICIAL MHA ADVISORY: ${analysisResult.mhaAdvisory}",
                            fontSize = 10.sp,
                            color = CyberBlue,
                            lineHeight = 14.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
