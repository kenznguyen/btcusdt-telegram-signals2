package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.sin

class ForecastEngineTest {
    private fun candles(count: Int, closeAt: (Int) -> Double = { 60_000.0 + it * 2.0 }): List<Candle> =
        (0 until count).map { i ->
            val close = closeAt(i)
            Candle(i * 60_000L, close - 1.0, close + 2.0, close - 2.0, close, 10.0, true)
        }

    @Test fun probabilitiesSumToOneAndRangeIsOrdered() {
        val input = candles(180) { 60_000.0 + it * 5.0 + sin(it.toDouble()) * 20.0 }
        val result = ForecastEngine().forecast(input, nowMs = 180 * 60_000L)
        assertNotNull(result)
        result!!
        assertEquals(1.0, result.probabilityUp + result.probabilityDown + result.probabilitySideways, 1e-9)
        assertTrue(result.lowerPrice <= result.medianPrice)
        assertTrue(result.medianPrice <= result.upperPrice)
        assertEquals("NOT_VALIDATED", result.validationStatus)
    }

    @Test fun insufficientHistoryReturnsNull() {
        assertNull(ForecastEngine().forecast(candles(30), nowMs = 30 * 60_000L))
    }

    @Test fun staleDataReturnsNull() {
        val input = candles(180)
        assertNull(ForecastEngine().forecast(input, nowMs = 180 * 60_000L + 300_000L))
    }

    @Test fun gapsReturnNullRatherThanFabricatingConsecutiveMinutes() {
        val input = candles(180).filterIndexed { index, _ -> index != 70 }
        assertNull(ForecastEngine().forecast(input, nowMs = 180 * 60_000L))
    }

    @Test fun unclosedCandlesAreIgnored() {
        val all = candles(180)
        val input = all.dropLast(1) + all.last().copy(closed = false)
        val result = ForecastEngine().forecast(input, nowMs = 180 * 60_000L)
        assertNotNull(result)
        // The unclosed candle at index 179 must not become the reference price.
        assertEquals(all[178].close, result!!.referencePrice, 0.0)
    }
}
