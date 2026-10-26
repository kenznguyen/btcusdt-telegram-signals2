package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import com.kenznguyen.btclivealerts.StrategyPosition
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SharedEmergencyExitFixtureTest {
    @Test fun seededPositionEmergencyExitMatchesSharedFixture() {
        val name = "freqtrade-backtest/fixtures/android_python_emergency_exit_v1.json"
        val working = java.io.File(System.getProperty("user.dir")).canonicalFile
        val file = generateSequence(working) { it.parentFile }
            .map { java.io.File(it, name) }.firstOrNull { it.isFile }
            ?: error("Missing shared fixture: $name")
        val fixture = JSONObject(file.readText())
        val p = fixture.getJSONObject("initial_position")
        val initial = StrategyState(
            balance = fixture.getDouble("initial_balance"),
            position = StrategyPosition(
                p.getString("side"), p.getDouble("qty"), p.getDouble("avg_entry"),
                p.getDouble("initial_margin"), p.getDouble("dca_margin"),
                p.getDouble("entry_notional"), p.getLong("entry_time"),
                p.getBoolean("dca_used")
            )
        )
        fun readCandles(rows: JSONArray): List<Candle> =
            (0 until rows.length()).map { i ->
                val c = rows.getJSONObject(i)
                Candle(
                    openTime = c.getLong("timestamp_ms"),
                    open = c.getDouble("open"), high = c.getDouble("high"),
                    low = c.getDouble("low"), close = c.getDouble("close"),
                    volume = c.getDouble("volume"), closed = c.getBoolean("closed")
                )
            }
        val result = StrategyTraceReplay.run(
            StrategyEngine(), readCandles(fixture.getJSONArray("candles_m15")),
            readCandles(fixture.getJSONArray("candles_h1")), fixture.getString("symbol"), initial
        )
        val expected = fixture.getJSONObject("expected")
        assertEquals(expected.getInt("event_count"), result.transitions.size)
        assertEquals("EMERGENCY SL", result.transitions.single().event.kind)
        assertEquals(expected.getString("side"), result.transitions.single().event.side)
        assertNull(result.finalState.position)
        val event = JSONArray(result.json).getJSONObject(0)
        assertEquals(expected.getString("kind"), event.getString("kind"))
        assertEquals(p.getDouble("qty"), event.getDouble("quantity"), 1e-9)
        assertEquals(p.getDouble("avg_entry"), event.getDouble("avg_entry"), 1e-9)
        assertEquals(50.0, event.getDouble("margin"), 1e-9)
        assertEquals(initial.balance + event.getDouble("net_pnl"), result.finalState.balance, 1e-8)
        assertTrue(event.getDouble("fees") > 0.0)
    }
}
