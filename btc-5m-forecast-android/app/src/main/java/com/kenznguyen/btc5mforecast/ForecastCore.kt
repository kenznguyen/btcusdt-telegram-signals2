package com.kenznguyen.btc5mforecast

import kotlin.math.abs
import kotlin.math.floor

data class Candle(
    val openTime: Long,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double,
    val closeTime: Long
)

enum class Direction { UP, DOWN, TIE }

data class Forecast(
    val createdAt: Long,
    val targetAt: Long,
    val referencePrice: Double,
    val pUp: Double,
    val pDown: Double,
    val pTie: Double,
    val lower: Double,
    val median: Double,
    val upper: Double,
    val sampleCount: Int,
    val model: String = "historical-frequency-baseline-v1"
) {
    val predicted: Direction
        get() = when (maxOf(pUp, pDown, pTie)) {
            pUp -> Direction.UP
            pDown -> Direction.DOWN
            else -> Direction.TIE
        }
}

data class SettledForecast(
    val forecast: Forecast,
    val actualPrice: Double,
    val actual: Direction,
    val settledAt: Long,
    val brier: Double
)

object ForecastCore {
    const val FIVE_MINUTES = 300_000L
    const val ONE_MINUTE = 60_000L

    /** Predict at a 5m boundary from the last fully closed 1m candle only. */
    fun forecast(candles: List<Candle>, now: Long, minimumSamples: Int = 100): Forecast? {
        val closed = candles.filter { it.closeTime < now && it.close > 0.0 }
            .distinctBy { it.openTime }.sortedBy { it.openTime }
        if (closed.size < minimumSamples + 6) return null
        val latest = closed.last()
        if (now - (latest.closeTime + 1) > 90_000L) return null
        for (i in 1 until closed.size) if (closed[i].openTime - closed[i - 1].openTime != ONE_MINUTE) return null

        // Exclude any return whose outcome is the latest/reference candle; only completed
        // historical five-minute outcomes strictly before the reference may train the baseline.
        val returns = (0 until closed.size - 6).mapNotNull { i ->
            val start = closed[i].close
            val end = closed[i + 5].close
            if (start > 0.0 && end > 0.0) end / start - 1.0 else null
        }
        if (returns.size < minimumSamples) return null
        val up = returns.count { it > 0.0 }
        val down = returns.count { it < 0.0 }
        val tie = returns.count { it == 0.0 }
        val sorted = returns.sorted()
        val ref = latest.close
        val created = latest.closeTime + 1
        return Forecast(
            createdAt = created,
            targetAt = created + FIVE_MINUTES,
            referencePrice = ref,
            pUp = up.toDouble() / returns.size,
            pDown = down.toDouble() / returns.size,
            pTie = tie.toDouble() / returns.size,
            lower = ref * (1.0 + quantile(sorted, 0.10)),
            median = ref * (1.0 + quantile(sorted, 0.50)),
            upper = ref * (1.0 + quantile(sorted, 0.90)),
            sampleCount = returns.size
        )
    }

    /** Market rule: positive -> UP, negative -> DOWN, exactly equal -> TIE. */
    fun settle(forecast: Forecast, actualPrice: Double, settledAt: Long): SettledForecast? {
        if (settledAt < forecast.targetAt || !actualPrice.isFinite() || actualPrice <= 0.0) return null
        val actual = when {
            actualPrice > forecast.referencePrice -> Direction.UP
            actualPrice < forecast.referencePrice -> Direction.DOWN
            else -> Direction.TIE
        }
        val probs = listOf(forecast.pUp, forecast.pDown, forecast.pTie)
        val classes = listOf(Direction.UP, Direction.DOWN, Direction.TIE)
        val brier = probs.indices.sumOf { i ->
            val error = probs[i] - if (classes[i] == actual) 1.0 else 0.0
            error * error
        }
        return SettledForecast(forecast, actualPrice, actual, settledAt, brier)
    }

    private fun quantile(values: List<Double>, q: Double): Double {
        if (values.size == 1) return values.first()
        val pos = q * (values.size - 1)
        val lo = floor(pos).toInt()
        val hi = (lo + 1).coerceAtMost(values.lastIndex)
        return values[lo] + (values[hi] - values[lo]) * (pos - lo)
    }
}
