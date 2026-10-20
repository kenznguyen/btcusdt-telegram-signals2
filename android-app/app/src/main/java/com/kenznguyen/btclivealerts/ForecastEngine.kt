package com.kenznguyen.btclivealerts

import kotlin.math.floor

/**
 * Transparent historical baseline for a five-minute BTCUSDT forecast.
 *
 * IMPORTANT: probabilities are historical class frequencies, not calibrated estimates
 * of the next five-minute outcome. Keep the UI marked EXPERIMENTAL until walk-forward
 * evaluation demonstrates calibration and improvement over a simple baseline.
 */
data class ForecastSnapshot(
    val generatedAtMs: Long,
    val targetAtMs: Long,
    val referencePrice: Double,
    val probabilityUp: Double,
    val probabilityDown: Double,
    val probabilitySideways: Double,
    val lowerPrice: Double,
    val medianPrice: Double,
    val upperPrice: Double,
    val historicalSamples: Int,
    val modelVersion: String = "historical-frequency-baseline-v1",
    val validationStatus: String = "NOT_VALIDATED"
)

class ForecastEngine(
    private val horizonMinutes: Int = 5,
    private val sidewaysThreshold: Double = 0.0003,
    private val minimumSamples: Int = 100,
    private val maximumAgeMs: Long = 120_000L
) {
    init {
        require(horizonMinutes > 0)
        require(sidewaysThreshold >= 0.0)
        require(minimumSamples >= 1)
        require(maximumAgeMs > 0)
    }

    /**
     * candles must be one-minute candles in ascending openTime order.
     * Only closed candles are used. Returns null when data is stale or insufficient.
     */
    fun forecast(candles: List<Candle>, nowMs: Long): ForecastSnapshot? {
        val closed = candles.asSequence()
            .filter { it.closed }
            .distinctBy { it.openTime }
            .sortedBy { it.openTime }
            .toList()
        if (closed.size < minimumSamples + horizonMinutes + 1) return null

        val latest = closed.last()
        if (latest.close <= 0.0 || nowMs < latest.openTime ||
            nowMs - (latest.openTime + 60_000L) > maximumAgeMs) return null

        // Reject gaps: silently treating missing minutes as consecutive would corrupt labels.
        for (i in 1 until closed.size) {
            if (closed[i].openTime - closed[i - 1].openTime != 60_000L) return null
        }

        val returns = ArrayList<Double>()
        for (i in 0 until closed.size - horizonMinutes) {
            val start = closed[i].close
            val end = closed[i + horizonMinutes].close
            if (start > 0.0 && end > 0.0) returns += (end / start) - 1.0
        }
        if (returns.size < minimumSamples) return null

        // Match the requested market resolution rule: every positive return is UP,
        // every negative return is DOWN, and only an exactly unchanged close is a tie.
        // Keep sidewaysThreshold in the constructor for backward compatibility only.
        val up = returns.count { it > 0.0 }
        val down = returns.count { it < 0.0 }
        val sideways = returns.count { it == 0.0 }
        val total = returns.size.toDouble()
        val sorted = returns.sorted()
        val ref = latest.close

        return ForecastSnapshot(
            generatedAtMs = nowMs,
            targetAtMs = latest.openTime + 60_000L + horizonMinutes * 60_000L,
            referencePrice = ref,
            probabilityUp = up / total,
            probabilityDown = down / total,
            probabilitySideways = sideways / total,
            lowerPrice = ref * (1.0 + quantile(sorted, 0.10)),
            medianPrice = ref * (1.0 + quantile(sorted, 0.50)),
            upperPrice = ref * (1.0 + quantile(sorted, 0.90)),
            historicalSamples = returns.size
        )
    }

    private fun quantile(sorted: List<Double>, q: Double): Double {
        if (sorted.size == 1) return sorted[0]
        val position = q.coerceIn(0.0, 1.0) * (sorted.size - 1)
        val low = floor(position).toInt()
        val high = (low + 1).coerceAtMost(sorted.lastIndex)
        val fraction = position - low
        return sorted[low] + (sorted[high] - sorted[low]) * fraction
    }
}
