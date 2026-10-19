package com.kenznguyen.btclivealerts

import kotlin.math.sqrt

/** Rolling Bollinger Bands. Population standard deviation matches the common TradingView default. */
data class BollingerPoint(
    val middle: Double,
    val upper: Double,
    val lower: Double,
    val percentB: Double?
)

object ChartAnalytics {
    fun bollinger(candles: List<Candle>, period: Int = 20, deviations: Double = 2.0): List<BollingerPoint?> {
        require(period >= 2) { "period must be >= 2" }
        require(deviations.isFinite() && deviations >= 0.0) { "deviations must be finite and non-negative" }
        val result = MutableList<BollingerPoint?>(candles.size) { null }
        if (candles.size < period) return result
        for (i in period - 1 until candles.size) {
            val window = candles.subList(i - period + 1, i + 1)
            if (window.any { !it.close.isFinite() }) continue
            val mean = window.sumOf { it.close } / period
            val variance = window.sumOf { (it.close - mean) * (it.close - mean) } / period
            val sd = sqrt(variance.coerceAtLeast(0.0))
            val upper = mean + deviations * sd
            val lower = mean - deviations * sd
            val width = upper - lower
            val percentB = if (width > 0.0) (candles[i].close - lower) / width else null
            result[i] = BollingerPoint(mean, upper, lower, percentB)
        }
        return result
    }
}
