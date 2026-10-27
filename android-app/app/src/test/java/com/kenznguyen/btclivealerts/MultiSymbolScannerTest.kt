package com.kenznguyen.btclivealerts

import java.io.Closeable
import java.io.IOException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class MultiSymbolScannerTest {
    @Test fun reconnectBackfillsBeforePublishingAndIgnoresRetiredCallbacks() = runTest {
        val h = harness()
        h.scanner.start()
        runCurrent()
        advanceTimeBy(500); runCurrent()
        assertEquals(1_800_000L, h.updates.last().single().m15CloseTime)
        val oldConnection = h.feed.connections.single()
        val oldBookCallback = h.bookCallbacks.single()
        oldConnection.disconnect("network unavailable")
        runCurrent()
        assertTrue(h.updates.last().isEmpty())
        assertTrue(oldConnection.closed)
        advanceTimeBy(1_999); runCurrent()
        assertEquals(1, h.feed.connections.size)

        val backfill = CompletableDeferred<Unit>()
        h.feed.backfillBarrier = backfill
        h.feed.latestOpen = 1_800_000L
        advanceTimeBy(1); runCurrent()
        assertEquals(2, h.feed.connections.size)
        h.feed.connections.last().candle(candle(2_700_000L))
        oldConnection.candle(candle(99_000_000L))
        oldConnection.disconnect("late failure from retired connection")
        assertTrue(h.updates.last().isEmpty())

        backfill.complete(Unit)
        runCurrent()
        advanceTimeBy(500); runCurrent()
        assertEquals(3_600_000L, h.updates.last().single().m15CloseTime)
        assertEquals(listOf("15m", "1h", "15m", "1h"), h.feed.requestedIntervals)
        val updateCount = h.updates.size
        oldBookCallback(book())
        assertEquals(updateCount, h.updates.size)
        h.scanner.close()
    }

    @Test fun disconnectCancelsBlockedBackfillAndRestartsBeforePublishing() = runTest {
        val h = harness()
        val backfill = CompletableDeferred<Unit>()
        h.feed.backfillBarrier = backfill
        h.scanner.start(); runCurrent()
        val first = h.feed.connections.single()
        assertEquals(listOf("15m"), h.feed.requestedIntervals)

        first.disconnect("lost network during backfill")
        runCurrent()
        assertTrue(first.closed)
        assertTrue(h.updates.all { it.isEmpty() })
        advanceTimeBy(2_000); runCurrent()
        assertEquals(2, h.feed.connections.size)

        backfill.complete(Unit)
        runCurrent(); advanceTimeBy(500); runCurrent()
        // The retired bootstrap must not resume and request H1 after its M15 wait.
        assertEquals(listOf("15m", "15m", "1h"), h.feed.requestedIntervals)
        assertFalse(h.updates.last().isEmpty())
        h.scanner.close()
    }

    @Test fun delayedFormingUpdateCannotDowngradeClosedBufferedCandle() = runTest {
        val h = harness()
        h.feed.latestOpen = 1_800_000L
        h.feed.snapshotClosed = false
        val backfill = CompletableDeferred<Unit>()
        h.feed.backfillBarrier = backfill
        h.scanner.start(); runCurrent()
        val live = h.feed.connections.single()
        live.candle(candle(1_800_000L))
        live.candle(candle(1_800_000L, closed = false))
        backfill.complete(Unit)
        runCurrent(); advanceTimeBy(500); runCurrent()
        assertEquals(2_700_000L, h.updates.last().single().m15CloseTime)
        live.candle(candle(1_800_000L, closed = false))
        h.bookCallbacks.single().invoke(book())
        assertEquals(2_700_000L, h.updates.last().single().m15CloseTime)
        h.scanner.close()
    }

    @Test fun bootstrapFailureRetriesInsteadOfLeavingScannerInert() = runTest {
        val h = harness()
        h.feed.symbolFailures = 2
        h.scanner.start(); runCurrent()
        assertEquals(1, h.feed.symbolCalls)
        advanceTimeBy(2_000); runCurrent()
        assertEquals(2, h.feed.symbolCalls)
        advanceTimeBy(3_999); runCurrent()
        assertEquals(2, h.feed.symbolCalls)
        advanceTimeBy(1); runCurrent()
        advanceTimeBy(500); runCurrent()
        assertEquals(3, h.feed.symbolCalls)
        assertFalse(h.updates.last().isEmpty())
        h.scanner.close()
    }

    @Test fun failedBackfillRetiresSocketAndRetriesWithoutPublishingPartialData() = runTest {
        val h = harness()
        h.feed.candleFailures = 1
        h.scanner.start(); runCurrent()
        assertTrue(h.feed.connections.single().closed)
        assertTrue(h.updates.all { it.isEmpty() })
        advanceTimeBy(2_000); runCurrent()
        advanceTimeBy(500); runCurrent()
        assertEquals(2, h.feed.connections.size)
        assertFalse(h.updates.last().isEmpty())
        h.scanner.close()
    }

    @Test fun connectionTimeoutRetriesAndCloseCancelsPendingBackfill() = runTest {
        val h = harness()
        h.feed.autoConnect = false
        h.scanner.start(); runCurrent()
        advanceTimeBy(30_000); runCurrent()
        assertTrue(h.feed.connections.single().closed)
        h.feed.autoConnect = true
        h.feed.backfillBarrier = CompletableDeferred()
        advanceTimeBy(2_000); runCurrent()
        assertEquals(2, h.feed.connections.size)
        h.scanner.close(); runCurrent()
        val updatesAfterClose = h.updates.size
        h.feed.backfillBarrier!!.complete(Unit)
        h.feed.connections.last().candle(candle(4_500_000L))
        h.feed.connections.last().disconnect("late close")
        advanceTimeBy(120_000); runCurrent()
        assertEquals(2, h.feed.connections.size)
        assertTrue(h.bookCallbacks.isEmpty())
        assertEquals(updatesAfterClose, h.updates.size)
    }

    private fun TestScope.harness(): Harness {
        val feed = FakeFeed()
        val updates = mutableListOf<List<MultiSymbolScanner.SymbolScanResult>>()
        val callbacks = mutableListOf<(OrderBookMetrics) -> Unit>()
        val scanner = MultiSymbolScanner(feed, { updates += it }, {},
            CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler)),
            { _, metrics, _ -> callbacks += metrics; Closeable { } },
            nowMs = { 10_000_000L + testScheduler.currentTime })
        return Harness(scanner, feed, updates, callbacks)
    }

    private data class Harness(
        val scanner: MultiSymbolScanner,
        val feed: FakeFeed,
        val updates: MutableList<List<MultiSymbolScanner.SymbolScanResult>>,
        val bookCallbacks: MutableList<(OrderBookMetrics) -> Unit>
    )

    private class FakeFeed : ScannerMarketFeed {
        var symbolFailures = 0
        var candleFailures = 0
        var snapshotClosed = true
        var symbolCalls = 0
        var autoConnect = true
        var latestOpen = 900_000L
        var backfillBarrier: CompletableDeferred<Unit>? = null
        val requestedIntervals = mutableListOf<String>()
        val connections = mutableListOf<Connection>()

        override suspend fun symbols(): List<String> {
            symbolCalls++
            if (symbolFailures-- > 0) throw IOException("temporary REST failure")
            return listOf("BTCUSDT")
        }
        override suspend fun candles(symbol: String, interval: String): List<Candle> {
            requestedIntervals += interval
            if (candleFailures-- > 0) throw IOException("temporary kline failure")
            backfillBarrier?.await()
            return listOf(candle(latestOpen, snapshotClosed))
        }
        override fun connect(
            symbols: List<String>, onConnected: () -> Unit, onDisconnected: (String) -> Unit,
            onCandle: (String, String, Candle) -> Unit, onMarkPrice: (String, Double) -> Unit,
            onStatus: (String) -> Unit
        ): Closeable {
            val connection = Connection(onDisconnected, onCandle)
            connections += connection
            if (autoConnect) onConnected()
            return connection
        }
    }

    private class Connection(
        val disconnect: (String) -> Unit,
        private val onCandle: (String, String, Candle) -> Unit
    ) : Closeable {
        var closed = false
        fun candle(value: Candle) = onCandle("BTCUSDT", "15m", value)
        override fun close() { closed = true }
    }

    companion object {
        private fun candle(time: Long, closed: Boolean = true) =
            Candle(time, 100.0, 101.0, 99.0, 100.0, 10.0, closed)
        private fun book() = OrderBookMetrics(100.0, 101.0, 100.0, 10.0, 10.0,
            0.0, 0.0, 1L, 10_000_000L, true)
    }
}
