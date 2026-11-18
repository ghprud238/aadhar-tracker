package app.suraksha.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.suraksha.data.model.HealthScore
import app.suraksha.ui.theme.*

@Composable
fun HealthDialView(
    healthScore: HealthScore,
    shieldStatus: String,
    modifier: Modifier = Modifier
) {
    val tierColor = when (healthScore.tier) {
        "FORTRESS GUARDIAN" -> ShieldEmerald
        "VIGILANT SENTINEL" -> CyberBlue
        "PROTECTED CITIZEN" -> WarningAmber
        else -> CriticalRed
    }

    val animatedProgress by animateFloatAsState(
        targetValue = healthScore.score / 1000f,
        animationSpec = tween(durationMillis = 1000),
        label = "score_arc_anim"
    )

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(DarkCard)
            .border(1.5.dp, tierColor.copy(alpha = 0.5f), RoundedCornerShape(20.dp))
            .padding(18.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.fillMaxWidth()
        ) {
            // Top Row: Status pill & Tier badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Shield Status Pill
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .clip(RoundedCornerShape(16.dp))
                        .background(
                            if (shieldStatus == "critical") CriticalRed.copy(alpha = 0.15f)
                            else ShieldEmerald.copy(alpha = 0.15f)
                        )
                        .border(
                            1.dp,
                            if (shieldStatus == "critical") CriticalRed.copy(alpha = 0.5f)
                            else ShieldEmerald.copy(alpha = 0.5f),
                            RoundedCornerShape(16.dp)
                        )
                        .padding(horizontal = 10.dp, vertical = 5.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(7.dp)
                            .clip(CircleShape)
                            .background(if (shieldStatus == "critical") CriticalRed else ShieldEmerald)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (shieldStatus == "critical") "CRITICAL THREAT" else "SHIELD ACTIVE & SECURE",
                        color = if (shieldStatus == "critical") CriticalRed else ShieldEmerald,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                }

                // Tier Pill
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(tierColor.copy(alpha = 0.15f))
                        .border(1.dp, tierColor.copy(alpha = 0.5f), RoundedCornerShape(8.dp))
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = healthScore.tier,
                        color = tierColor,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 0.5.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Canvas Score Arc
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.size(140.dp)
            ) {
                Canvas(modifier = Modifier.size(130.dp)) {
                    val strokeWidth = 10.dp.toPx()
                    // Background track
                    drawCircle(
                        color = Color(0xFF1E293B),
                        style = Stroke(width = strokeWidth)
                    )
                    // Animated gradient arc
                    drawArc(
                        brush = Brush.sweepGradient(
                            listOf(tierColor.copy(alpha = 0.4f), tierColor)
                        ),
                        startAngle = -90f,
                        sweepAngle = 360f * animatedProgress,
                        useCenter = false,
                        style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                    )
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = healthScore.score.toString(),
                        fontSize = 38.sp,
                        fontWeight = FontWeight.Black,
                        color = tierColor,
                        letterSpacing = (-1).sp
                    )
                    Text(
                        text = "/ 1000",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = TextMuted
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = healthScore.percentileText,
                color = CyberBlue,
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Badges Row
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(vertical = 4.dp)
            ) {
                items(healthScore.badges) { badge ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .clip(RoundedCornerShape(20.dp))
                            .background(if (badge.unlocked) DarkSurface else Color(0xFF0F172A))
                            .border(
                                1.dp,
                                if (badge.unlocked) CyberBlue.copy(alpha = 0.6f) else Color(0xFF334155),
                                RoundedCornerShape(20.dp)
                            )
                            .padding(horizontal = 10.dp, vertical = 5.dp)
                    ) {
                        Text(text = badge.icon, fontSize = 13.sp)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = badge.title,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (badge.unlocked) TextPrimary else TextMuted
                        )
                    }
                }
            }
        }
    }
}
