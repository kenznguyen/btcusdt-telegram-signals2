package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import com.kenznguyen.btclivealerts.StrategyPosition
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

class StrategyTraceReplayTest {
    @Test fun capturesEmergencyExitWithPreExitQuantityAndPostExitBalance() {
        val candles = (0 until 25).map { i ->
            val breach = i == 1
            Candle(i * 900000L, 100.0, 101.0,
                if (breach) 80.0 else 99.0,
                if (breach) 90.0 else 100.0, 1.0, true)
        }
        val position = StrategyPosition("LONG", 1.0, 100.0, 50.0, 0.0, 100.0, 0L, false)
        val initial = StrategyState(balance = 100.0, position = position)
        val result = StrategyTraceReplay.run(StrategyEngine(), candles, emptyList(), "BTCUSDT", initial)
        assertNull(result.finalState.position)
        assertEquals(1, result.transitions.size)
        val item = JSONArray(result.json).getJSONObject(0)
        assertEquals("EMERGENCY_SL", item.getString("kind"))
        assertEquals(1.0, item.getDouble("quantity"), 1e-9)
        assertEquals(50.0, item.getDouble("margin"), 1e-9)
        assertEquals(result.finalState.balance, item.getDouble("balance"), 1e-9)
        assertTrue(item.getDouble("fees") > 0)
    }

    @Test fun ignoresUnclosedCandlesAndEmitsEmptyTraceWithoutPosition() {
        val candles = (0 until 5).map { i ->
            Candle(i * 900000L, 100.0, 101.0, 99.0, 100.0, 1.0, i != 4)
        }
        val result = StrategyTraceReplay.run(StrategyEngine(), candles, emptyList(), "BTCUSDT")
        assertEquals(0, result.transitions.size)
        assertEquals(0, JSONArray(result.json).length())
    }
}
