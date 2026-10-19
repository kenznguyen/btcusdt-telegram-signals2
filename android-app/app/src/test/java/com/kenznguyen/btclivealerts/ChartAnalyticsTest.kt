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

    @Test fun volumeProfileAllocatesVolumeByPriceOverlapAndFindsPoc() {
        val candles = listOf(
            candle(1L, 5.0, 10.0, 0.0, 5.0, 100.0),
            candle(2L, 2.0, 5.0, 0.0, 2.0, 100.0)
        )
        val profile = ChartAnalytics.volumeProfile(candles, 0.0, 10.0, 2)!!
        assertEquals(2, profile.bins.size)
        assertEquals(150.0, profile.bins[0].volume, 1e-10)
        assertEquals(50.0, profile.bins[1].volume, 1e-10)
        assertEquals(2.5, profile.pointOfControl, 1e-10)
        assertEquals(200.0, profile.totalVolume, 1e-10)
    }

    @Test fun volumeProfileRejectsInvalidRangeAndHandlesFlatCandle() {
        assertNull(ChartAnalytics.volumeProfile(emptyList(), 0.0, 1.0))
        assertNull(ChartAnalytics.volumeProfile(listOf(candle(1L, 1.0, 1.0, 1.0, 1.0, 1.0)), 2.0, 1.0))
        val profile = ChartAnalytics.volumeProfile(
            listOf(candle(1L, 5.0, 5.0, 5.0, 5.0, 12.0)), 0.0, 10.0, 2
        )!!
        assertEquals(12.0, profile.totalVolume, 1e-10)
        assertEquals(7.5, profile.pointOfControl, 1e-10)
    }
}
