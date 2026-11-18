package app.suraksha.data.api

import app.suraksha.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class SurakshaApiService(
    private val baseUrl: String = "http://10.0.2.2:8000/api/v1"
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    private var authToken: String? = null
    private var cachedEtag: String? = null
    private var cachedBootstrap: MobileBootstrap? = null

    suspend fun authenticate(email: String = "resident@example.com"): String = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$baseUrl/auth/callback?email=$email")
            .get()
            .build()

        client.newCall(request).execute().use { response ->
            val json = JSONObject(response.body?.string() ?: "{}")
            val token = json.getJSONObject("data").getString("session_id")
            authToken = token
            token
        }
    }

    suspend fun getBootstrap(): MobileBootstrap = withContext(Dispatchers.IO) {
        if (authToken == null) authenticate()

        val reqBuilder = Request.Builder()
            .url("$baseUrl/mobile/bootstrap")
            .header("Authorization", "Bearer $authToken")

        cachedEtag?.let { reqBuilder.header("If-None-Match", it) }

        client.newCall(reqBuilder.build()).execute().use { response ->
            if (response.code == 304 && cachedBootstrap != null) {
                return@withContext cachedBootstrap!!
            }

            response.header("ETag")?.let { cachedEtag = it }
            val raw = response.body?.string() ?: "{}"
            val root = JSONObject(raw).getJSONObject("data")

            val session = root.getJSONObject("session")
            val glanceObj = root.getJSONObject("glance")
            val healthObj = root.getJSONObject("health_score")
            val bioObj = root.getJSONObject("biometric_status")
            val passObj = root.getJSONObject("masked_pass")
            val actionsArray = root.getJSONArray("quick_actions")

            // Parse Badges
            val badgesList = mutableListOf<ScoreBadge>()
            val badgesArr = healthObj.getJSONArray("badges")
            for (i in 0 until badgesArr.length()) {
                val b = badgesArr.getJSONObject(i)
                badgesList.add(
                    ScoreBadge(
                        id = b.getString("id"),
                        title = b.getString("title"),
                        description = b.getString("description"),
                        icon = b.getString("icon"),
                        unlocked = b.getBoolean("unlocked")
                    )
                )
            }

            // Parse Pillars
            val pillarsList = mutableListOf<ScorePillar>()
            val pillarsArr = healthObj.getJSONArray("pillars")
            for (i in 0 until pillarsArr.length()) {
                val p = pillarsArr.getJSONObject(i)
                pillarsList.add(
                    ScorePillar(
                        id = p.getString("id"),
                        title = p.getString("title"),
                        points = p.getInt("points"),
                        maxPoints = p.getInt("max_points"),
                        status = p.getString("status")
                    )
                )
            }

            // Parse Recommendations
            val recList = mutableListOf<String>()
            val recArr = healthObj.getJSONArray("top_recommendations")
            for (i in 0 until recArr.length()) {
                recList.add(recArr.getString(i))
            }

            // Parse Quick Actions
            val actionsList = mutableListOf<QuickAction>()
            for (i in 0 until actionsArray.length()) {
                val a = actionsArray.getJSONObject(i)
                actionsList.add(
                    QuickAction(
                        id = a.getString("id"),
                        title = a.getString("title"),
                        subtitle = a.getString("subtitle"),
                        icon = a.getString("icon"),
                        badge = if (a.has("badge") && !a.isNull("badge")) a.getString("badge") else null,
                        route = a.getString("route")
                    )
                )
            }

            val urgentAlert = if (glanceObj.has("urgent_alert") && !glanceObj.isNull("urgent_alert")) {
                val u = glanceObj.getJSONObject("urgent_alert")
                UrgentAlert(
                    incidentId = u.getString("incident_id"),
                    title = u.getString("title"),
                    severity = u.getString("severity"),
                    priorityScore = u.getInt("priority_score")
                )
            } else null

            val result = MobileBootstrap(
                sessionEmail = session.getString("email"),
                sessionRole = session.getString("role"),
                glance = GlanceData(
                    shieldStatus = glanceObj.getString("shield_status"),
                    activeMonitoredCount = glanceObj.getInt("active_monitored_count"),
                    activeIncidents = glanceObj.getInt("active_incidents"),
                    urgentAlert = urgentAlert,
                    biometricsLocked = glanceObj.getBoolean("biometrics_locked")
                ),
                healthScore = HealthScore(
                    score = healthObj.getInt("score"),
                    maxScore = healthObj.getInt("max_score"),
                    tier = healthObj.getString("tier"),
                    tierColor = healthObj.getString("tier_color"),
                    percentileText = healthObj.getString("percentile_text"),
                    badges = badgesList,
                    pillars = pillarsList,
                    topRecommendations = recList
                ),
                unreadAlertsCount = root.getInt("unread_alerts_count"),
                biometricStatus = BiometricStatus(
                    locked = bioObj.getBoolean("locked"),
                    lockedConfirmedAt = if (bioObj.has("locked_confirmed_at") && !bioObj.isNull("locked_confirmed_at")) bioObj.getString("locked_confirmed_at") else null,
                    autoRelockActive = bioObj.getBoolean("auto_relock_active"),
                    autoRelockSecondsLeft = bioObj.getInt("auto_relock_seconds_left"),
                    statusLabel = bioObj.getString("status_label")
                ),
                maskedPass = MaskedPass(
                    docType = passObj.getString("doc_type"),
                    holderName = passObj.getString("holder_name"),
                    maskedIdentifier = passObj.getString("masked_identifier"),
                    recipient = passObj.getString("recipient"),
                    purpose = passObj.getString("purpose"),
                    verified = passObj.getBoolean("verified"),
                    complianceStandard = passObj.getString("compliance_standard")
                ),
                quickActions = actionsList,
                syncTimestamp = root.getString("sync_timestamp")
            )
            cachedBootstrap = result
            result
        }
    }

    suspend fun getActivity(): MobileActivity = withContext(Dispatchers.IO) {
        if (authToken == null) authenticate()

        val request = Request.Builder()
            .url("$baseUrl/mobile/activity")
            .header("Authorization", "Bearer $authToken")
            .get()
            .build()

        client.newCall(request).execute().use { response ->
            val root = JSONObject(response.body?.string() ?: "{}").getJSONObject("data")

            val exposuresList = mutableListOf<ExposureIncident>()
            val expArr = root.getJSONArray("exposures")
            for (i in 0 until expArr.length()) {
                val e = expArr.getJSONObject(i)
                val cats = mutableListOf<String>()
                val catArr = e.getJSONArray("exposure_categories")
                for (c in 0 until catArr.length()) cats.add(catArr.getString(c))

                exposuresList.add(
                    ExposureIncident(
                        id = e.getString("id"),
                        title = e.getString("title"),
                        severity = e.getString("severity"),
                        priorityScore = e.getInt("priority_score"),
                        state = e.getString("state"),
                        exposureCategories = cats,
                        source = e.getString("source"),
                        createdAt = if (e.has("created_at") && !e.isNull("created_at")) e.getString("created_at") else null
                    )
                )
            }

            val alertsList = mutableListOf<RadarAlert>()
            val alertArr = root.getJSONArray("radar_alerts")
            for (i in 0 until alertArr.length()) {
                val a = alertArr.getJSONObject(i)
                alertsList.add(
                    RadarAlert(
                        id = a.getString("id"),
                        channel = a.getString("channel"),
                        status = a.getString("status"),
                        recipient = a.getString("recipient"),
                        payloadPreview = a.getString("payload_preview"),
                        createdAt = if (a.has("created_at") && !a.isNull("created_at")) a.getString("created_at") else null
                    )
                )
            }

            MobileActivity(
                exposures = exposuresList,
                radarAlerts = alertsList,
                activeExposuresCount = root.getInt("active_exposures_count"),
                unreadAlertsCount = root.getInt("unread_alerts_count")
            )
        }
    }

    suspend fun analyzeScam(message: String, channel: String = "video_call", sender: String? = null): ScamAnalysisResult = withContext(Dispatchers.IO) {
        if (authToken == null) authenticate()

        val bodyJson = JSONObject().apply {
            put("message_text", message)
            put("channel", channel)
            if (sender != null) put("sender_header", sender)
        }

        val request = Request.Builder()
            .url("$baseUrl/mobile/scam-radar/analyze")
            .header("Authorization", "Bearer $authToken")
            .post(bodyJson.toString().toRequestBody("application/json".toMediaType()))
            .build()

        client.newCall(request).execute().use { response ->
            val data = JSONObject(response.body?.string() ?: "{}").getJSONObject("data")
            val indicators = mutableListOf<String>()
            val indArr = data.getJSONArray("matched_indicators")
            for (i in 0 until indArr.length()) indicators.add(indArr.getString(i))

            ScamAnalysisResult(
                isScam = data.getBoolean("is_scam"),
                threatLevel = data.getString("threat_level"),
                scamCategory = data.getString("scam_category"),
                confidenceScore = data.getDouble("confidence_score"),
                matchedIndicators = indicators,
                mhaAdvisory = data.getString("mha_official_advisory"),
                prefilledFir = data.getString("prefilled_fir_draft")
            )
        }
    }

    suspend fun verifyQr(rawQr: String): PassVerificationResult = withContext(Dispatchers.IO) {
        if (authToken == null) authenticate()

        val bodyJson = JSONObject().apply {
            put("raw_qr_payload", rawQr)
            put("verifier_entity", "Suraksha Android Native Client")
        }

        val request = Request.Builder()
            .url("$baseUrl/mobile/qr/verify")
            .header("Authorization", "Bearer $authToken")
            .post(bodyJson.toString().toRequestBody("application/json".toMediaType()))
            .build()

        client.newCall(request).execute().use { response ->
            val data = JSONObject(response.body?.string() ?: "{}").getJSONObject("data")
            val detailsMap = mutableMapOf<String, String>()
            if (data.has("extracted_details")) {
                val d = data.getJSONObject("extracted_details")
                d.keys().forEach { k -> detailsMap[k] = d.getString(k) }
            }

            PassVerificationResult(
                verified = data.getBoolean("verified"),
                title = data.getString("title"),
                securityAudit = data.getString("security_audit"),
                extractedDetails = detailsMap
            )
        }
    }

    suspend fun toggleAutoRelock(action: String, seconds: Int = 600): Pair<Boolean, Int> = withContext(Dispatchers.IO) {
        if (authToken == null) authenticate()

        val bodyJson = JSONObject().apply {
            put("action", action)
            put("duration_seconds", seconds)
        }

        val request = Request.Builder()
            .url("$baseUrl/mobile/biometric/auto-relock")
            .header("Authorization", "Bearer $authToken")
            .post(bodyJson.toString().toRequestBody("application/json".toMediaType()))
            .build()

        client.newCall(request).execute().use { response ->
            val data = JSONObject(response.body?.string() ?: "{}").getJSONObject("data")
            Pair(data.getBoolean("auto_relock_active"), data.getInt("seconds_left"))
        }
    }
}
