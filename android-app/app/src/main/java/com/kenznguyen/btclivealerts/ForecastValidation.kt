package com.kenznguyen.btclivealerts

import kotlin.math.abs

data class ForecastValidationReport(
    val forecastsEvaluated: Int,
    val multiclassBrierScore: Double?,
    val directionAccuracy: Double?,
    val medianPriceMae: Double?,
    val centralIntervalCoverage: Double?,
    val baselineVersion: String = "historical-frequency-baseline-v1",
    val note: String = "Historical walk-forward diagnostic; not a guarantee of future performance."
)

/**
 * Chronological, expanding-window validation. Each forecast only sees candles that were
 * closed at its forecast time; the target candle is read only after forecast creation.
 *
 * This is a diagnostic utility, not proof of predictive edge. Results can be dependent
 * because adjacent forecast horizons overlap. Prefer a step of at least the horizon.
 */
class ForecastWalkForwardValidator(
    private val engine: ForecastEngine = ForecastEngine(),
    private val horizonMinutes: Int = 5,
    private val minimumTrainingSamples: Int = 100,
    private val evaluationStepMinutes: Int = 5
) {
    init {
        require(horizonMinutes > 0)
        require(minimumTrainingSamples >= 1)
        require(evaluationStepMinutes > 0)
    }

    fun evaluate(candles: List<Candle>): ForecastValidationReport {
        val data = candles.filter { it.closed }.distinctBy { it.openTime }.sortedBy { it.openTime }
        if (data.size < minimumTrainingSamples + 2 * horizonMinutes + 1) {
            return ForecastValidationReport(0, null, null, null, null)
        }
        // Reject gaps globally rather than silently producing misleading validation.
        for (i in 1 until data.size) {
            if (data[i].openTime - data[i - 1].openTime != 60_000L) {
                return ForecastValidationReport(0, null, null, null, null)
            }
        }

        var count = 0
        var brierSum = 0.0
        var correct = 0
        var absoluteErrorSum = 0.0
        var covered = 0
        val firstForecastIndex = minimumTrainingSamples + horizonMinutes
        val lastForecastIndex = data.lastIndex - horizonMinutes
        for (i in firstForecastIndex..lastForecastIndex step evaluationStepMinutes) {
            val prefix = data.subList(0, i + 1)
            val forecastTime = data[i].openTime + 60_000L
            val forecast = engine.forecast(prefix, forecastTime) ?: continue
            val targetIndex = i + horizonMinutes
            val actualPrice = data[targetIndex].close
            val actualReturn = actualPrice / forecast.referencePrice - 1.0
            val actualClass = when {
                actualReturn > 0.0003 -> 0 // up
                actualReturn < -0.0003 -> 1 // down
                else -> 2 // sideways
            }
            val probabilities = doubleArrayOf(
                forecast.probabilityUp,
                forecast.probabilityDown,
                forecast.probabilitySideways
            )
            for (classIndex in probabilities.indices) {
                val observed = if (classIndex == actualClass) 1.0 else 0.0
                val difference = probabilities[classIndex] - observed
                brierSum += difference * difference
            }
            val predictedClass = probabilities.indices.maxByOrNull { probabilities[it] } ?: 2
            if (predictedClass == actualClass) correct++
            absoluteErrorSum += abs(forecast.medianPrice - actualPrice)
            if (actualPrice >= forecast.lowerPrice && actualPrice <= forecast.upperPrice) covered++
            count++
        }

        if (count == 0) return ForecastValidationReport(0, null, null, null, null)
        return ForecastValidationReport(
            forecastsEvaluated = count,
            multiclassBrierScore = brierSum / count,
            directionAccuracy = correct.toDouble() / count,
            medianPriceMae = absoluteErrorSum / count,
            centralIntervalCoverage = covered.toDouble() / count
        )
    }
}
