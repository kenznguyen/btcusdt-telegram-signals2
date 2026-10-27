package com.kenznguyen.btclivealerts

import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class ChartMarketSessionTest {
    @Test fun initialPeriodicAndReconnectLoadsKeepTheSelectedCoin() = runBlocking {
        val requests = mutableListOf<String>()
        val session = ChartMarketSession("ETHUSDT", "15m",
            { interval, _, symbol ->
                requests += "$symbol:$interval"
                listOf(candle(1, if (symbol == "ETHUSDT") 3000.0 else 90000.0))
            },
            { symbol -> requests += "$symbol:mark"; 3001.0 })

        val initial = session.snapshot(otherLimit = 1500)
        val periodic = session.snapshot()
        val reconnected = session.snapshot()

        assertEquals(List(3) { listOf("ETHUSDT:15m", "ETHUSDT:1h", "ETHUSDT:mark") }.flatten(), requests)
        listOf(initial, periodic, reconnected).forEach {
            assertEquals(3000.0, it.candles.single().close, 0.0)
            assertEquals(3000.0, it.otherCandles.single().close, 0.0)
            assertEquals(3001.0, it.markPrice, 0.0)
        }
    }

    @Test fun hourlyChartStillLoadsTheSameSymbolsM15Companion() = runBlocking {
        val requests = mutableListOf<Pair<String, String>>()
        val session = ChartMarketSession("SOLUSDT", "1h",
            { interval, _, symbol -> requests += symbol to interval; emptyList() }, { 150.0 })
        session.snapshot()
        assertEquals(listOf("SOLUSDT" to "1h", "SOLUSDT" to "15m"), requests)
    }

    @Test fun queuedOldSocketCallbackCannotChangeNewConnectionState() {
        val generation = ChartConnectionGeneration()
        val first = generation.next()
        var displayedPrice = 3000.0
        val lateOldCallback = { if (generation.accepts(first)) displayedPrice = 90000.0 }
        val replacement = generation.next()
        lateOldCallback()
        assertEquals(3000.0, displayedPrice, 0.0)
        assertTrue(generation.accepts(replacement))
        generation.close()
        assertFalse(generation.accepts(replacement))
    }

    @Test fun staleOpenUpdateDoesNotReopenConfirmedCandleAndCacheIsBounded() {
        val cache = ChartCandleCache(capacity = 2)
        cache.merge(candle(1, 10.0))
        cache.merge(candle(1, 99.0).copy(closed = false))
        assertEquals(10.0, cache.snapshot().single().close, 0.0)
        cache.mergeAll(listOf(candle(2, 20.0), candle(3, 30.0)))
        assertEquals(listOf(2L, 3L), cache.snapshot().map { it.openTime })
    }

    @Test fun simultaneousAlertsForDifferentCoinsAndTimeframesDoNotSuppressEachOther() {
        val btc = ChartAlertIdentity("BTCUSDT", "15m", "MFIB_HIGH", 1000)
        val eth = ChartAlertIdentity("ETHUSDT", "15m", "MFIB_HIGH", 1000)
        val hourly = ChartAlertIdentity("ETHUSDT", "1h", "MFIB_HIGH", 1000)
        assertEquals(3, setOf(btc.eventKey, eth.eventKey, hourly.eventKey).size)
        assertEquals(3, setOf(btc.preferenceKey, eth.preferenceKey, hourly.preferenceKey).size)
        assertEquals(3, setOf(btc.notificationKey, eth.notificationKey, hourly.notificationKey).size)
        assertEquals(eth.eventKey, eth.copy(symbol = "ethusdt").eventKey)
        assertNotEquals(eth.eventKey, eth.copy(candleOpenTime = 2000).eventKey)
        assertEquals(eth.preferenceKey, eth.copy(candleOpenTime = 2000).preferenceKey)
    }

    private fun candle(time: Long, close: Double) = Candle(time, close, close, close, close, 1.0, true)
}
