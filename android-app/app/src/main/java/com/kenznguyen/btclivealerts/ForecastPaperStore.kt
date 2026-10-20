package com.kenznguyen.btclivealerts

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * Device-local persistence for experimental forecasts and settled paper results.
 * Keeps a bounded history and never records orders or trading PnL.
 */

internal fun firstClosedCandleAtOrAfter(targetAtMs: Long, candles: List<Candle>, nowMs: Long): Candle? =
    candles.asSequence()
        .filter { it.closed }
        .sortedBy { it.openTime }
        .firstOrNull { it.openTime + 60_000L == targetAtMs && it.openTime + 60_000L <= nowMs }

class ForecastPaperStore(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences(
        "btc_m5_forecast_paper", Context.MODE_PRIVATE
    )

    @Synchronized
    fun savePending(snapshot: ForecastSnapshot): Boolean {
        val current = pending()
        if (current.any { it.generatedAtMs == snapshot.generatedAtMs }) return false
        val updated = (current + snapshot).takeLast(MAX_PENDING)
        preferences.edit()
            .putString(KEY_PENDING, JSONArray().apply {
                updated.forEach { put(it.toJson()) }
            }.toString())
            .putString(KEY_LATEST, snapshot.toJson().toString())
            .apply()
        return true
    }

    @Synchronized
    fun latestForecast(): ForecastSnapshot? = preferences.getString(KEY_LATEST, null)
        ?.let { raw -> runCatching { JSONObject(raw).asForecastSnapshot() }.getOrNull() }

    @Synchronized
    fun pending(): List<ForecastSnapshot> = readArray(KEY_PENDING).mapNotNull { value ->
        runCatching { value.asForecastSnapshot() }.getOrNull()
    }

    @Synchronized
    fun settleDue(actualClosedCandles: List<Candle>, nowMs: Long): List<ForecastPaperResult> {
        val closed = actualClosedCandles.filter { it.closed }.sortedBy { it.openTime }
        if (closed.isEmpty()) return emptyList()
        val remaining = mutableListOf<ForecastSnapshot>()
        val settled = mutableListOf<ForecastPaperResult>()
        for (forecast in pending()) {
            val targetCandle = firstClosedCandleAtOrAfter(forecast.targetAtMs, closed, nowMs)
            if (nowMs < forecast.targetAtMs || targetCandle == null) {
                remaining += forecast
                continue
            }
            val result = ForecastPaperTracker.settle(
                forecast = forecast,
                actualPrice = targetCandle.close,
                settledAtMs = targetCandle.openTime + ONE_MINUTE_MS
            )
            if (result == null) remaining += forecast else settled += result
        }
        preferences.edit().putString(KEY_PENDING, JSONArray().apply {
            remaining.forEach { put(it.toJson()) }
        }.toString()).apply()
        if (settled.isNotEmpty()) {
            val all = (history() + settled).takeLast(MAX_HISTORY)
            preferences.edit().putString(KEY_HISTORY, JSONArray().apply {
                all.forEach { put(it.toJson()) }
            }.toString()).apply()
        }
        return settled
    }

    @Synchronized
    fun history(): List<ForecastPaperResult> = readArray(KEY_HISTORY).mapNotNull { value ->
        runCatching { value.asPaperResult() }.getOrNull()
    }

    @Synchronized
    fun saveStatus(value: String) {
        preferences.edit().putString(KEY_STATUS, value.take(240)).apply()
    }

    @Synchronized
    fun status(): String = preferences.getString(KEY_STATUS, "Đang chuẩn bị dữ liệu M1…")
        ?: "Đang chuẩn bị dữ liệu M1…"

    @Synchronized
    fun saveValidationReport(report: ForecastValidationReport) {
        val json = JSONObject()
            .put("forecastsEvaluated", report.forecastsEvaluated)
            .put("baselineVersion", report.baselineVersion)
            .put("note", report.note)
        report.multiclassBrierScore?.let { json.put("multiclassBrierScore", it) }
        report.directionAccuracy?.let { json.put("directionAccuracy", it) }
        report.medianPriceMae?.let { json.put("medianPriceMae", it) }
        report.centralIntervalCoverage?.let { json.put("centralIntervalCoverage", it) }
        report.alwaysSidewaysBrierScore?.let { json.put("alwaysSidewaysBrierScore", it) }
        report.alwaysSidewaysAccuracy?.let { json.put("alwaysSidewaysAccuracy", it) }
        report.brierSkillVsAlwaysSideways?.let { json.put("brierSkillVsAlwaysSideways", it) }
        preferences.edit().putString(KEY_VALIDATION, json.toString()).apply()
    }

    @Synchronized
    fun validationReport(): ForecastValidationReport? {
        val raw = preferences.getString(KEY_VALIDATION, null) ?: return null
        return runCatching {
            val json = JSONObject(raw)
            fun optionalNumber(key: String): Double? =
                json.optDouble(key, Double.NaN).takeIf { it.isFinite() }
            ForecastValidationReport(
                forecastsEvaluated = json.getInt("forecastsEvaluated"),
                multiclassBrierScore = optionalNumber("multiclassBrierScore"),
                directionAccuracy = optionalNumber("directionAccuracy"),
                medianPriceMae = optionalNumber("medianPriceMae"),
                centralIntervalCoverage = optionalNumber("centralIntervalCoverage"),
                alwaysSidewaysBrierScore = optionalNumber("alwaysSidewaysBrierScore"),
                alwaysSidewaysAccuracy = optionalNumber("alwaysSidewaysAccuracy"),
                brierSkillVsAlwaysSideways = optionalNumber("brierSkillVsAlwaysSideways"),
                baselineVersion = json.optString("baselineVersion", "always-sideways-v1"),
                note = json.optString("note", "Historical walk-forward diagnostic.")
            )
        }.getOrNull()
    }

    private fun readArray(key: String): List<JSONObject> {
        val raw = preferences.getString(key, "[]") ?: "[]"
        return runCatching {
            val array = JSONArray(raw)
            (0 until array.length()).mapNotNull { array.optJSONObject(it) }
        }.getOrDefault(emptyList())
    }

    private fun ForecastSnapshot.toJson() = JSONObject().apply {
        put("generatedAtMs", generatedAtMs)
        put("targetAtMs", targetAtMs)
        put("referencePrice", referencePrice)
        put("probabilityUp", probabilityUp)
        put("probabilityDown", probabilityDown)
        put("probabilitySideways", probabilitySideways)
        put("lowerPrice", lowerPrice)
        put("medianPrice", medianPrice)
        put("upperPrice", upperPrice)
        put("historicalSamples", historicalSamples)
        put("modelVersion", modelVersion)
        put("validationStatus", validationStatus)
    }

    private fun JSONObject.asForecastSnapshot() = ForecastSnapshot(
        generatedAtMs = getLong("generatedAtMs"),
        targetAtMs = getLong("targetAtMs"),
        referencePrice = getDouble("referencePrice"),
        probabilityUp = getDouble("probabilityUp"),
        probabilityDown = getDouble("probabilityDown"),
        probabilitySideways = getDouble("probabilitySideways"),
        lowerPrice = getDouble("lowerPrice"),
        medianPrice = getDouble("medianPrice"),
        upperPrice = getDouble("upperPrice"),
        historicalSamples = getInt("historicalSamples"),
        modelVersion = optString("modelVersion", "historical-frequency-baseline-v1"),
        validationStatus = optString("validationStatus", "NOT_VALIDATED")
    )

    private fun ForecastPaperResult.toJson() = JSONObject().apply {
        put("generatedAtMs", generatedAtMs)
        put("targetAtMs", targetAtMs)
        put("settledAtMs", settledAtMs)
        put("referencePrice", referencePrice)
        put("actualPrice", actualPrice)
        put("actualClass", actualClass.name)
        put("predictedClass", predictedClass.name)
        put("absolutePriceError", absolutePriceError)
        put("intervalCovered", intervalCovered)
        put("multiclassBrierScore", multiclassBrierScore)
    }

    private fun JSONObject.asPaperResult() = ForecastPaperResult(
        generatedAtMs = getLong("generatedAtMs"),
        targetAtMs = getLong("targetAtMs"),
        settledAtMs = getLong("settledAtMs"),
        referencePrice = getDouble("referencePrice"),
        actualPrice = getDouble("actualPrice"),
        actualClass = ForecastClass.valueOf(getString("actualClass")),
        predictedClass = ForecastClass.valueOf(getString("predictedClass")),
        absolutePriceError = getDouble("absolutePriceError"),
        intervalCovered = getBoolean("intervalCovered"),
        multiclassBrierScore = getDouble("multiclassBrierScore")
    )

    private companion object {
        const val KEY_PENDING = "pending_forecasts_json"
        const val KEY_HISTORY = "settled_history_json"
        const val KEY_LATEST = "latest_forecast_json"
        const val KEY_STATUS = "forecast_status"
        const val KEY_VALIDATION = "forecast_validation_report"
        const val MAX_PENDING = 100
        const val MAX_HISTORY = 500
        const val ONE_MINUTE_MS = 60_000L
    }
}
