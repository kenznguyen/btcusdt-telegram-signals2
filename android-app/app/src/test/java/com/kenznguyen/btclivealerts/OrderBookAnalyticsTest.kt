package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class OrderBookAnalyticsTest {
    @Test
    fun calculatesSpreadAndBidAskImbalance() {
        val result = OrderBookAnalytics.calculate(
            bids = listOf(OrderBookLevel(100.0, 8.0), OrderBookLevel(99.9, 2.0)),
            asks = listOf(OrderBookLevel(100.1, 5.0), OrderBookLevel(100.2, 5.0)),
            updateId = 123L,
            updatedAtMs = 1_800_000_000_000L,
            synchronized = true
        )!!

        assertEquals(100.0, result.bestBid, 0.000001)
        assertEquals(100.1, result.bestAsk, 0.000001)
        assertEquals(10.0, result.bidDepth, 0.000001)
        assertEquals(10.0, result.askDepth, 0.000001)
        assertEquals(0.0, result.imbalance, 0.000001)
        assertEquals(123L, result.updateId)
        assertTrue(result.spreadBps > 0.0)
    }

    @Test
    fun rejectsUnsynchronizedOrCrossedBooks() {
        assertNull(OrderBookAnalytics.calculate(
            listOf(OrderBookLevel(100.0, 1.0)),
            listOf(OrderBookLevel(101.0, 1.0)),
            1L, 1L, false
        ))
        assertNull(OrderBookAnalytics.calculate(
            listOf(OrderBookLevel(102.0, 1.0)),
            listOf(OrderBookLevel(101.0, 1.0)),
            1L, 1L, true
        ))
    }

    @Test
    fun ignoresNegativeQuantitiesAndLimitsDepth() {
        val result = OrderBookAnalytics.calculate(
            bids = listOf(
                OrderBookLevel(100.0, 3.0),
                OrderBookLevel(99.9, -4.0),
                OrderBookLevel(99.8, 9.0)
            ),
            asks = listOf(OrderBookLevel(100.1, 2.0), OrderBookLevel(100.2, 7.0)),
            updateId = 5L,
            updatedAtMs = 5L,
            synchronized = true,
            depthLevels = 1
        )!!

        assertEquals(3.0, result.bidDepth, 0.000001)
        assertEquals(2.0, result.askDepth, 0.000001)
    }
}

