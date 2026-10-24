package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MultiStreamSignalEngineTest {
    private val engine = MultiStreamSignalEngine()
    private val now = 1_800_000_000_000L

    @Test
    fun staleTechnicalDataProducesWaitSignal() {
        val signal = engine.evaluate(
            TechnicalSignalInput(0.9, 0.9, now - 30 * 60_000L, "M15+H1"),
            freshBook(now),
            now
        )
        assertEquals("WAIT", signal.signal)
        assertFalse(signal.dataComplete)
        assertTrue(signal.reason.contains("cũ"))
    }

    @Test
    fun missingOrderBookReturnsWaitAndMarksIncomplete() {
        val signal = engine.evaluate(
            TechnicalSignalInput(0.8, 0.9, now - 60_000L, "M15+H1"),
            null,
            now
        )
        assertEquals("WAIT", signal.signal)
        assertFalse(signal.dataComplete)
        assertEquals(null, signal.orderBookScore)
        assertEquals(0.585, signal.confidence, 0.000001)
    }

    @Test
    fun freshBookIsCombinedWithTechnicalScore() {
        val signal = engine.evaluate(
            TechnicalSignalInput(0.8, 0.9, now - 60_000L, "M15+H1"),
            freshBook(now).copy(imbalance = 0.6, weightedImbalance = 0.4),
            now
        )
        assertEquals("BUY", signal.signal)
        assertTrue(signal.dataComplete)
        assertEquals(0.48, signal.orderBookScore!!, 0.000001)
        assertEquals(0.704, signal.score, 0.000001)
    }

    @Test
    fun staleOrderBookIsNotUsedAsCurrentEvidence() {
        val signal = engine.evaluate(
            TechnicalSignalInput(-0.8, 0.8, now - 60_000L, "M15+H1"),
            freshBook(now).copy(updatedAtMs = now - 5_000L),
            now
        )
        assertEquals("WAIT", signal.signal)
        assertFalse(signal.dataComplete)
        assertEquals(null, signal.orderBookScore)
    }

    private fun freshBook(now: Long) = OrderBookMetrics(
        bestBid = 100.0,
        bestAsk = 100.1,
        spreadBps = 10.0,
        bidDepth = 10.0,
        askDepth = 8.0,
        imbalance = 0.1,
        weightedImbalance = 0.1,
        updateId = 10L,
        updatedAtMs = now,
        synchronized = true
    )
}
