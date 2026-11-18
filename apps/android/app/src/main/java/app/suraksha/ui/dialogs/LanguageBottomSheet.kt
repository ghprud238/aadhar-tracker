package app.suraksha.ui.dialogs

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
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

data class SupportedLang(val code: String, val name: String, val nativeName: String, val flag: String)

val REGIONAL_LANGUAGES = listOf(
    SupportedLang("en", "English", "English", "🇬🇧"),
    SupportedLang("hi", "Hindi", "हिंदी", "🇮🇳"),
    SupportedLang("ta", "Tamil", "தமிழ்", "🇮🇳"),
    SupportedLang("te", "Telugu", "తెలుగు", "🇮🇳"),
    SupportedLang("bn", "Bengali", "বাংলা", "🇮🇳")
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LanguageBottomSheet(
    currentLanguageCode: String,
    onSelectLanguage: (String) -> Unit,
    onDismiss: () -> Unit
) {
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
                text = "🗣️ Select Regional Language",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )
            Text(
                text = "Powered by Project Bhashini Vernacular AI Engine",
                fontSize = 12.sp,
                color = TextSecondary,
                modifier = Modifier.padding(top = 4.dp, bottom = 14.dp)
            )

            REGIONAL_LANGUAGES.forEach { lang ->
                val isSelected = lang.code == currentLanguageCode
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(if (isSelected) Color(0xFF1E3A8A) else DarkCard)
                        .border(
                            1.dp,
                            if (isSelected) CyberBlue else DarkBorder,
                            RoundedCornerShape(10.dp)
                        )
                        .clickable {
                            onSelectLanguage(lang.code)
                            onDismiss()
                        }
                        .padding(14.dp)
                ) {
                    Text(text = lang.flag, fontSize = 20.sp)
                    Spacer(modifier = Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = lang.nativeName,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isSelected) CyberBlue else TextPrimary
                        )
                        Text(
                            text = lang.name,
                            fontSize = 11.sp,
                            color = TextSecondary
                        )
                    }
                    if (isSelected) {
                        Text(
                            text = "✓",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = CyberBlue
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}
