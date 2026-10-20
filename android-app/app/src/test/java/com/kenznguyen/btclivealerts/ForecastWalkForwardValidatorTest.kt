package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.sin

class ForecastWalkForwardValidatorTest {
    private fun candles(count: Int): List<Candle> = (0 until count).map { i ->
        val close = 60_000.0 + i * 2.0 + sin(i / 4.0) * 30.0
        Candle(i * 60_000L, close - 1.0, close + 2.0, close - 2.0, close, 10.0, true)
    }

    @Test fun walkForwardUsesChronologicalPredictionsAndReturnsBoundedMetrics() {
        val report = ForecastWalkForwardValidator().evaluate(candles(260))
        assertTrue(report.forecastsEvaluated > 0)
        assertNotNull(report.multiclassBrierScore)
        assertTrue(report.multiclassBrierScore!! in 0.0..2.0)
        assertTrue(report.directionAccuracy!! in 0.0..1.0)
        assertTrue(report.medianPriceMae!! >= 0.0)
        assertTrue(report.centralIntervalCoverage!! in 0.0..1.0)
    }

    @Test fun tooLittleDataProducesNoMetrics() {
        val report = ForecastWalkForwardValidator().evaluate(candles(40))
        assertEquals(0, report.forecastsEvaluated)
        assertNull(report.multiclassBrierScore)
    }

    @Test fun dataGapInvalidatesValidationInsteadOfBeingIgnored() {
        val report = ForecastWalkForwardValidator().evaluate(candles(260).filterIndexed { i, _ -> i != 70 })
        assertEquals(0, report.forecastsEvaluated)
        assertNull(report.directionAccuracy)
    }
}
