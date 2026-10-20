package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ForecastTargetCandleTest {
    @Test fun choosesOnlyTheClosedMinuteCandleEndingAtTargetTime() {
        val target = 600_000L
        val candles = listOf(
            Candle(480_000L, 1.0, 1.0, 1.0, 1.0, 1.0, true),
            Candle(540_000L, 2.0, 2.0, 2.0, 2.0, 1.0, true),
            Candle(600_000L, 3.0, 3.0, 3.0, 3.0, 1.0, false)
        )
        val result = closedCandleAtExactTarget(target, candles, target)
        assertEquals(540_000L, result?.openTime)
        assertEquals(2.0, result?.close ?: 0.0, 1e-9)
    }

    @Test fun refusesToSettleFromAnUnclosedOrMisalignedCandle() {
        val target = 600_000L
        val candles = listOf(
            Candle(540_000L, 2.0, 2.0, 2.0, 2.0, 1.0, false),
            Candle(480_000L, 1.0, 1.0, 1.0, 1.0, 1.0, true)
        )
        assertNull(closedCandleAtExactTarget(target, candles, target))
    }
}
