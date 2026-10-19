package com.kenznguyen.btclivealerts

import kotlin.math.sqrt

/** Rolling Bollinger Bands. Population standard deviation matches the common TradingView default. */
data class BollingerPoint(
    val middle: Double,
    val upper: Double,
    val lower: Double,
    val percentB: Double?
)

data class VolumeProfileBin(
    val lowerPrice: Double,
    val upperPrice: Double,
    val volume: Double
)

data class VolumeProfile(
    val bins: List<VolumeProfileBin>,
    val pointOfControl: Double,
    val totalVolume: Double
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

    /**
     * OHLCV-estimated volume profile. Public kline data has no trade-by-price histogram,
     * so each candle's volume is distributed uniformly across its high-low range.
     */
    fun volumeProfile(candles: List<Candle>, minPrice: Double, maxPrice: Double, binCount: Int = 24): VolumeProfile? {
        require(binCount in 1..200) { "binCount must be between 1 and 200" }
        if (candles.isEmpty() || !minPrice.isFinite() || !maxPrice.isFinite() || maxPrice <= minPrice) return null
        val width = (maxPrice - minPrice) / binCount
        val volumes = DoubleArray(binCount)
        for (candle in candles) {
            if (!candle.volume.isFinite() || candle.volume <= 0.0 ||
                !candle.low.isFinite() || !candle.high.isFinite() || candle.high < candle.low) continue
            val lo = candle.low.coerceIn(minPrice, maxPrice)
            val hi = candle.high.coerceIn(minPrice, maxPrice)
            if (candle.high == candle.low || hi <= lo) {
                if (candle.close in minPrice..maxPrice) {
                    val index = (((candle.close - minPrice) / width).toInt()).coerceIn(0, binCount - 1)
                    volumes[index] += candle.volume
                }
                continue
            }
            val candleRange = candle.high - candle.low
            val first = (((lo - minPrice) / width).toInt()).coerceIn(0, binCount - 1)
            val last = (((hi - minPrice) / width).toInt()).coerceIn(0, binCount - 1)
            for (index in first..last) {
                val binLow = minPrice + index * width
                val binHigh = binLow + width
                val overlap = (minOf(candle.high, binHigh) - maxOf(candle.low, binLow)).coerceAtLeast(0.0)
                if (overlap > 0.0) volumes[index] += candle.volume * overlap / candleRange
            }
        }
        val maxIndex = volumes.indices.maxByOrNull { volumes[it] } ?: return null
        val bins = volumes.indices.map { i ->
            VolumeProfileBin(minPrice + i * width, minPrice + (i + 1) * width, volumes[i])
        }
        return VolumeProfile(bins, minPrice + (maxIndex + 0.5) * width, volumes.sum())
    }
}
