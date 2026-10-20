package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class ForecastSettlementCandleTest {
    private fun candle(openTime: Long, close: Double = 100.0, closed: Boolean = true) = Candle(
        openTime = openTime,
        open = close,
        high = close,
        low = close,
        close = close,
        volume = 1.0,
        closed = closed
    )

    @Test fun picksClosedCandleAtExactTarget() {
        val candles = listOf(
            candle(0L),
            candle(60_000L),
            candle(120_000L),
            candle(180_000L)
        )
        val selected = closedCandleAtExactTarget(
            targetAtMs = 180_000L,
            candles = candles,
            nowMs = 240_000L
        )
        assertNotNull(selected)
        assertEquals(120_000L, selected!!.openTime)
    }

    @Test fun missingExactTargetCandleIsNotReplacedWithALaterPrice() {
        val candles = listOf(candle(60_000L), candle(180_000L))
        assertNull(closedCandleAtExactTarget(180_000L, candles, 240_000L))
    }

    @Test fun doesNotUseFormingOrFutureCandle() {
        val candles = listOf(
            candle(60_000L, closed = false),
            candle(120_000L)
        )
        assertNull(closedCandleAtExactTarget(50_000L, candles, 100_000L))
    }
}
