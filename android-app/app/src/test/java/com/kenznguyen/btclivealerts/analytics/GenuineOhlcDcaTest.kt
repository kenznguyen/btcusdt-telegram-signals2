package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import com.kenznguyen.btclivealerts.StrategyPosition
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

/** DCA with actual Wilder RSI/ADX, not mocked indicators. */
class GenuineOhlcDcaTest {
    @Test fun seededLongDcaBeforeEmergencyStopUsesWeightedAverage() {
        val engine = StrategyEngine()
        val prices = mutableListOf(100.0)
        for (i in 1 until 130) {
            prices.add(prices.last() + if (i % 6 == 5) 0.65 else -0.45)
        }
        val candles = prices.mapIndexed { i, price ->
            Candle(i * 900_000L, price, price + 0.1, price - 0.1, price, 10.0, true)
        }
        val indicators = engine.indicatorSeries(candles)
        val target = (1 until candles.size).firstOrNull { i ->
            val p = indicators[i]
            val prev = indicators[i - 1]
            p.rsi != null && prev.rsi != null && p.adx != null &&
                p.adx > 45.0 && p.rsi > 20.0 && p.rsi > prev.rsi
        } ?: error("OHLC must warm up a qualifying RSI/ADX rebound")
        val entryReference = candles[target].close / 0.98
        val fill = entryReference * 1.0005
        val qty = 650.0 / fill
        val initialPosition = StrategyPosition("LONG", qty, fill, 50.0, 0.0, 650.0, 0L, false)
        val initial = StrategyState(balance = 100.0, position = initialPosition)
        val result = StrategyTraceReplay.run(engine, candles.take(target + 1), emptyList(), "BTCUSDT", initial)
        assertEquals(1, result.transitions.size)
        assertEquals("DCA", result.transitions.single().event.kind)
        val position = result.finalState.position ?: error("DCA must keep position open")
        assertTrue(position.dcaUsed)
        assertEquals(50.0, position.dcaMargin, 1e-9)
        assertEquals(100.0, position.reservedMargin, 1e-9)
        assertEquals(1300.0, position.entryNotional, 1e-8)
        assertEquals(100.0, result.finalState.balance, 1e-9)
        val dcaFill = candles[target].close * 1.0005
        val addedQty = 650.0 / dcaFill
        val expectedQty = qty + addedQty
        val expectedAvg = (qty * fill + addedQty * dcaFill) / expectedQty
        assertEquals(expectedQty, position.qty, 1e-9)
        assertEquals(expectedAvg, position.avgEntry, 1e-9)
        val event = JSONArray(result.json).getJSONObject(0)
        assertEquals("DCA", event.getString("kind"))
        assertEquals(expectedQty, event.getDouble("quantity"), 1e-9)
        assertEquals(expectedAvg, event.getDouble("avg_entry"), 1e-9)
        assertEquals(100.0, event.getDouble("margin"), 1e-9)
    }
}
