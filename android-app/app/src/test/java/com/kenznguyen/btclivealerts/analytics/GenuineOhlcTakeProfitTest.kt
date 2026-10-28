package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import com.kenznguyen.btclivealerts.StrategyPosition
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

/** Matching Python test_genuine_ohlc_take_profit.py. */
class GenuineOhlcTakeProfitTest {
    @Test fun seededLongClosesAtRsiTakeProfit() {
        val candles = (0 until 85).map { i ->
            val price = 100.0 + 0.25 * i
            Candle(i * 900_000L, price, price + 0.1, price - 0.1, price, 10.0, true)
        }
        val entryFill = 100.0 * 1.0005
        val initial = StrategyState(
            balance = 100.0,
            position = StrategyPosition("LONG", 650.0 / entryFill, entryFill,
                50.0, 0.0, 650.0, 0L, false)
        )
        val result = StrategyTraceReplay.run(StrategyEngine(), candles, emptyList(), "BTCUSDT", initial)
        assertEquals(1, result.transitions.size)
        assertEquals("TAKE PROFIT", result.transitions.single().event.kind)
        assertNull(result.finalState.position)
        val event = JSONArray(result.json).getJSONObject(0)
        assertEquals("TP", event.getString("kind"))
        assertEquals("LONG", event.getString("side"))
        assertTrue(event.getDouble("net_pnl") > 0.0)
        assertTrue(event.getDouble("fees") > 0.0)
        assertEquals(100.0 + event.getDouble("net_pnl"), result.finalState.balance, 1e-8)
        System.getProperty("android.parity.tp.trace.output")?.takeIf { it.isNotBlank() }?.let { path ->
            val output = java.io.File(path)
            output.parentFile?.mkdirs()
            output.writeText(result.json)
        }
    }
}
