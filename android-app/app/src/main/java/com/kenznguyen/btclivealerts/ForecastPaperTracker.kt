package com.kenznguyen.btclivealerts

import kotlin.math.abs

enum class ForecastClass { UP, DOWN, SIDEWAYS }

data class ForecastPaperResult(
    val generatedAtMs: Long,
    val targetAtMs: Long,
    val settledAtMs: Long,
    val referencePrice: Double,
    val actualPrice: Double,
    val actualClass: ForecastClass,
    val predictedClass: ForecastClass,
    val absolutePriceError: Double,
    val intervalCovered: Boolean,
    val multiclassBrierScore: Double
)

/**
 * Settles a forecast only after its target time. This is paper evaluation only:
 * it does not represent a trade, PnL, or evidence of a tradable edge.
 */
object ForecastPaperTracker {
    fun settle(
        forecast: ForecastSnapshot,
        actualPrice: Double,
        settledAtMs: Long,
        sidewaysThreshold: Double = 0.0003
    ): ForecastPaperResult? {
        if (!actualPrice.isFinite() || actualPrice <= 0.0) return null
        if (!sidewaysThreshold.isFinite() || sidewaysThreshold < 0.0) return null
        if (settledAtMs < forecast.targetAtMs) return null
        val forecastPrices = listOf(
            forecast.referencePrice, forecast.lowerPrice, forecast.medianPrice, forecast.upperPrice
        )
        if (forecastPrices.any { !it.isFinite() || it <= 0.0 }) return null
        if (forecast.lowerPrice > forecast.medianPrice || forecast.medianPrice > forecast.upperPrice) return null

        val probabilities = listOf(
            forecast.probabilityUp,
            forecast.probabilityDown,
            forecast.probabilitySideways
        )
        if (probabilities.any { !it.isFinite() || it !in 0.0..1.0 } ||
            abs(probabilities.sum() - 1.0) > 1e-6) return null

        val actualReturn = actualPrice / forecast.referencePrice - 1.0
        val actualClass = when {
            actualReturn > sidewaysThreshold -> ForecastClass.UP
            actualReturn < -sidewaysThreshold -> ForecastClass.DOWN
            else -> ForecastClass.SIDEWAYS
        }
        val classes = listOf(ForecastClass.UP, ForecastClass.DOWN, ForecastClass.SIDEWAYS)
        val predictedClass = classes[probabilities.indices.maxByOrNull { probabilities[it] } ?: 2]
        val brier = probabilities.indices.sumOf { index ->
            val observed = if (classes[index] == actualClass) 1.0 else 0.0
            val error = probabilities[index] - observed
            error * error
        }

        return ForecastPaperResult(
            generatedAtMs = forecast.generatedAtMs,
            targetAtMs = forecast.targetAtMs,
            settledAtMs = settledAtMs,
            referencePrice = forecast.referencePrice,
            actualPrice = actualPrice,
            actualClass = actualClass,
            predictedClass = predictedClass,
            absolutePriceError = abs(forecast.medianPrice - actualPrice),
            intervalCovered = actualPrice >= forecast.lowerPrice && actualPrice <= forecast.upperPrice,
            multiclassBrierScore = brier
        )
    }
}
