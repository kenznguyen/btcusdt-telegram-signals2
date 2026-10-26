package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import com.kenznguyen.btclivealerts.StrategyPosition
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SharedDcaWarmupGuardTest {
    @Test fun noDcaWhenRsiAndAdxNotWarmedUp() {
        val name = "freqtrade-backtest/fixtures/android_python_dca_warmup_guard_v1.json"
        val working = java.io.File(System.getProperty("user.dir")).canonicalFile
        val file = generateSequence(working) { it.parentFile }
            .map { java.io.File(it, name) }.firstOrNull { it.isFile }
            ?: error("Missing shared fixture: $name")
        val fixture = JSONObject(file.readText())
        val p = fixture.getJSONObject("initial_position")
        val position = StrategyPosition(
            p.getString("side"), p.getDouble("qty"), p.getDouble("avg_entry"),
            p.getDouble("initial_margin"), p.getDouble("dca_margin"),
            p.getDouble("entry_notional"), p.getLong("entry_time"), p.getBoolean("dca_used")
        )
        val rows = fixture.getJSONArray("candles_m15")
        val candles = (0 until rows.length()).map { i ->
            val c = rows.getJSONObject(i)
            Candle(
                openTime = c.getLong("timestamp_ms"), open = c.getDouble("open"),
                high = c.getDouble("high"), low = c.getDouble("low"),
                close = c.getDouble("close"), volume = c.getDouble("volume"),
                closed = c.getBoolean("closed")
            )
        }
        val result = StrategyTraceReplay.run(
            StrategyEngine(), candles, emptyList(), fixture.getString("symbol"),
            StrategyState(balance = fixture.getDouble("initial_balance"), position = position)
        )
        assertTrue(result.transitions.isEmpty())
        assertNotNull(result.finalState.position)
        assertFalse(result.finalState.position!!.dcaUsed)
        assertEquals(position.qty, result.finalState.position!!.qty, 1e-9)
        assertEquals(position.avgEntry, result.finalState.position!!.avgEntry, 1e-9)
        assertEquals(fixture.getDouble("initial_balance"), result.finalState.balance, 1e-9)
    }
}
