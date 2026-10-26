package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

/**
 * Same deterministic OHLC construction as Python test_genuine_ohlc_entry.py.
 * All indicators are computed by the real Android StrategyEngine.
 */
class GenuineOhlcEntryTest {
    private fun bar(time: Long, price: Double) = Candle(
        openTime = time, open = price, high = price + 1.0,
        low = price - 1.0, close = price, volume = 10.0, closed = true
    )

    @Test fun realRsiCrossWithPriorClosedH1ProducesLongEntry() {
        val hour = 3_600_000L
        val quarter = 900_000L
        val h1 = (0 until 65).map { i -> bar(i * hour, 100.0 + 2.0 * i) }
        val prices = (0 until 45).map { 250.0 - it } +
            (0 until 35).map { 205.0 + it }
        val m15 = prices.mapIndexed { i, price ->
            bar(60 * hour + i * quarter, price)
        }
        val result = StrategyTraceReplay.run(StrategyEngine(), m15, h1, "BTCUSDT")
        val tracePath = System.getProperty("android.parity.entry.trace.output")
        if (!tracePath.isNullOrBlank()) {
            val output = java.io.File(tracePath)
            output.parentFile?.mkdirs()
            output.writeText(result.json)
        }
        val events = JSONArray(result.json)
        val entries = (0 until events.length()).map { events.getJSONObject(it) }
            .filter { it.getString("kind") == "ENTRY" && it.getString("side") == "LONG" }
        assertTrue("OHLC candles must create LONG entry", entries.isNotEmpty())
        assertTrue(entries.first().getDouble("quantity") > 0.0)
        assertTrue(entries.first().getDouble("margin") > 0.0)
    }
}
