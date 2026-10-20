package com.kenznguyen.btc5mforecast

import org.junit.Assert.*
import org.junit.Test

class ForecastCoreTest {
    @Test fun exactPriceEqualityIsTie() {
        val f = Forecast(0, 300, 100.0, .4, .4, .2, 98.0, 100.0, 102.0, 100)
        assertEquals(Direction.TIE, ForecastCore.settle(f, 100.0, 300)?.actual)
    }

    @Test fun anyPositivePriceMoveIsUp() {
        val f = Forecast(0, 300, 100.0, .4, .4, .2, 98.0, 100.0, 102.0, 100)
        assertEquals(Direction.UP, ForecastCore.settle(f, 100.00001, 300)?.actual)
    }

    @Test fun anyNegativePriceMoveIsDown() {
        val f = Forecast(0, 300, 100.0, .4, .4, .2, 98.0, 100.0, 102.0, 100)
        assertEquals(Direction.DOWN, ForecastCore.settle(f, 99.99999, 300)?.actual)
    }

    @Test fun doesNotSettleBeforeTarget() {
        val f = Forecast(0, 300, 100.0, .4, .4, .2, 98.0, 100.0, 102.0, 100)
        assertNull(ForecastCore.settle(f, 101.0, 299))
    }

    @Test fun rejectsGapAndUnclosedCandles() {
        val candles = (0 until 110).map { i ->
            val close = 100.0 + i * 0.01
            Candle(i * 60_000L, close, close + 1, close - 1, close, 1.0, i * 60_000L + 59_999L)
        }.filterIndexed { i, _ -> i != 50 }
        assertNull(ForecastCore.forecast(candles, 7_000_000L))
    }
}
