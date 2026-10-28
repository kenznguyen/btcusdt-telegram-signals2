package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

/**
 * Loads the identical JSON OHLC dataset as Python exporter.
 * All indicators are computed by the real Android StrategyEngine.
 */
class GenuineOhlcEntryTest {
    @Test fun realRsiCrossWithPriorClosedH1ProducesLongEntry() {
        val fixtureName = "freqtrade-backtest/fixtures/android_python_entry_ohlc_v1.json"
        val working = java.io.File(System.getProperty("user.dir")).canonicalFile
        val fixtureFile = generateSequence(working) { it.parentFile }
            .map { java.io.File(it, fixtureName) }.firstOrNull { it.isFile }
            ?: error("Missing shared fixture: $fixtureName")
        val fixture = org.json.JSONObject(fixtureFile.readText())
        fun readCandles(rows: JSONArray): List<Candle> =
            (0 until rows.length()).map { i ->
                val c = rows.getJSONObject(i)
                Candle(
                    openTime = c.getLong("timestamp_ms"),
                    open = c.getDouble("open"),
                    high = c.getDouble("high"),
                    low = c.getDouble("low"),
                    close = c.getDouble("close"),
                    volume = c.getDouble("volume"),
                    closed = c.getBoolean("closed")
                )
            }
        val m15 = readCandles(fixture.getJSONArray("candles_m15"))
        val h1 = readCandles(fixture.getJSONArray("candles_h1"))
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
