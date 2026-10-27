package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.sqrt

class ChartAnalyticsTest {
    private fun candle(time: Long, open: Double, high: Double, low: Double, close: Double, volume: Double) =
        Candle(time, open, high, low, close, volume, true)

    @Test fun bollingerUsesTwentyCloseRollingPopulationDeviation() {
        val candles = (1..20).map { candle(it.toLong(), it.toDouble(), it.toDouble(), it.toDouble(), it.toDouble(), 1.0) }
        val bands = ChartAnalytics.bollinger(candles)
        assertEquals(19, bands.count { it == null })
        val last = bands.last()!!
        val mean = 10.5
        val sd = sqrt(33.25)
        assertEquals(mean, last.middle, 1e-10)
        assertEquals(mean + 2.0 * sd, last.upper, 1e-10)
        assertEquals(mean - 2.0 * sd, last.lower, 1e-10)
        assertEquals((20.0 - last.lower) / (last.upper - last.lower), last.percentB!!, 1e-10)
    }

    @Test fun bollingerFlatPricesHaveNullPercentBNotNan() {
        val candles = (0 until 25).map { candle(it.toLong(), 100.0, 100.0, 100.0, 100.0, 1.0) }
        val last = ChartAnalytics.bollinger(candles).last()!!
        assertEquals(100.0, last.middle, 0.0)
        assertEquals(100.0, last.upper, 0.0)
        assertEquals(100.0, last.lower, 0.0)
        assertNull(last.percentB)
    }
}

