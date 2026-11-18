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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.suraksha.data.model.PassVerificationResult
import app.suraksha.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QrVerifierBottomSheet(
    onDismiss: () -> Unit,
    onVerify: (qrPayload: String) -> Unit,
    verificationResult: PassVerificationResult?
) {
    var qrInput by remember { mutableStateOf("") }

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
                text = "📷 Universal Offline Identity QR Scanner",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )
            Text(
                text = "Zero-cloud verifier for Suraksha Certified Passes (Ed25519) and UIDAI 2048-bit Secure QR codes.",
                fontSize = 12.sp,
                color = TextSecondary,
                modifier = Modifier.padding(top = 4.dp, bottom = 12.dp)
            )

            Text(
                text = "SELECT TEST PAYLOAD:",
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
                        qrInput = "{\"suraksha_certified\": true, \"pass_id\": \"PASS_SAMPLE_8921\", \"claim\": {\"doc_type\": \"aadhaar\", \"holder\": \"Aarav Sharma\", \"masked_id\": \"XXXX-XXXX-4819\", \"recipient\": \"Taj Lands End, Mumbai\", \"purpose\": \"hotel_checkin\", \"valid_until\": \"2028-12-31\"}, \"pubkey\": \"ed25519_pk_7fa83b9c02e5b7b1d3f9821a4f5c9e2b\", \"sig\": \"ed25519_sig_c2b1d3f821a4f5c9e2b1d3f821a4f5c9\"}"
                        onVerify(qrInput)
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Valid Pass", fontSize = 11.sp, color = ShieldEmerald)
                }

                OutlinedButton(
                    onClick = {
                        qrInput = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><PrintLetterBarcodeData uid=\"XXXXXXXX4819\" name=\"Aarav Sharma\" dob=\"1990-05-14\" gender=\"M\" signature=\"MIIEvgY...\" />"
                        onVerify(qrInput)
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("UIDAI XML", fontSize = 11.sp, color = CyberBlue)
                }

                OutlinedButton(
                    onClick = {
                        qrInput = "{\"suraksha_certified\": true, \"claim\": {}, \"pubkey\": \"short\", \"sig\": \"tampered\"}"
                        onVerify(qrInput)
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Tampered", fontSize = 11.sp, color = CriticalRed)
                }
            }

            OutlinedTextField(
                value = qrInput,
                onValueChange = { qrInput = it },
                label = { Text("Scan or paste raw QR payload string") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(85.dp),
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
                onClick = { if (qrInput.isNotBlank()) onVerify(qrInput) },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = ElectricBlue),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("🔍 Verify Signature Offline", fontWeight = FontWeight.Bold)
            }

            if (verificationResult != null) {
                Spacer(modifier = Modifier.height(14.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(DarkCard)
                        .border(
                            1.dp,
                            if (verificationResult.verified) ShieldEmerald else CriticalRed,
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
                                text = verificationResult.title,
                                fontWeight = FontWeight.Bold,
                                color = TextPrimary,
                                fontSize = 13.sp
                            )
                            Text(
                                text = if (verificationResult.verified) "✓ AUTHENTIC" else "❌ TAMPERED",
                                fontWeight = FontWeight.ExtraBold,
                                color = if (verificationResult.verified) ShieldEmerald else CriticalRed,
                                fontSize = 11.sp
                            )
                        }

                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = verificationResult.securityAudit,
                            fontSize = 11.sp,
                            color = TextSecondary,
                            lineHeight = 15.sp
                        )

                        if (verificationResult.extractedDetails.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(8.dp))
                            verificationResult.extractedDetails.forEach { (k, v) ->
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(text = "$k:", fontSize = 10.sp, color = TextMuted)
                                    Text(text = v, fontSize = 10.sp, color = TextPrimary, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
