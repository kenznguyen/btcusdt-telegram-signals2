package com.kenznguyen.btclivealerts

import org.junit.Assert.assertThrows
import org.junit.Test

class BacktestCandleValidationTest {
    private val step = 900_000L

    private fun candle(index: Long, closed: Boolean = true) = Candle(
        openTime = index * step,
        open = 100.0,
        high = 102.0,
        low = 99.0,
        close = 101.0,
        volume = 12.0,
        closed = closed
    )

    @Test fun acceptsCompleteClosedCandles() {
        validateBacktestCandles(listOf(candle(1), candle(2), candle(3)), step, "M15")
    }

    @Test fun rejectsTimestampGap() {
        assertThrows(IllegalArgumentException::class.java) {
            validateBacktestCandles(listOf(candle(1), candle(3)), step, "M15")
        }
    }

    @Test fun rejectsDuplicateTimestamp() {
        assertThrows(IllegalArgumentException::class.java) {
            validateBacktestCandles(listOf(candle(1), candle(1)), step, "M15")
        }
    }

    @Test fun rejectsUnclosedCandle() {
        assertThrows(IllegalArgumentException::class.java) {
            validateBacktestCandles(listOf(candle(1), candle(2, closed = false)), step, "M15")
        }
    }

    @Test fun rejectsInvalidOhlc() {
        assertThrows(IllegalArgumentException::class.java) {
            validateBacktestCandles(listOf(candle(1).copy(low = 103.0)), step, "M15")
        }
    }
}
