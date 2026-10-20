package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class ForecastEngineResolutionRuleTest {
    @Test fun anyPositiveHistoricalReturnIsUpEvenBelowLegacyThreshold() {
        val candles = (0 until 106).map { i ->
            val close = 100.0 + i * 0.01
            Candle(
                openTime = i * 60_000L,
                open = close - 0.005,
                high = close + 0.01,
                low = close - 0.01,
                close = close,
                volume = 1.0,
                closed = true
            )
        }
        val now = candles.last().openTime + 60_000L
        val snapshot = ForecastEngine(
            horizonMinutes = 5,
            sidewaysThreshold = 0.5,
            minimumSamples = 100,
            maximumAgeMs = 120_000L
        ).forecast(candles, now)

        assertNotNull(snapshot)
        assertEquals(1.0, snapshot!!.probabilityUp, 1e-9)
        assertEquals(0.0, snapshot.probabilityDown, 1e-9)
        assertEquals(0.0, snapshot.probabilitySideways, 1e-9)
    }
}
