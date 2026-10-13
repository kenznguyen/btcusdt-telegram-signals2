package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class StrategyEngineTest {
    private val engine = StrategyEngine()

    @Test fun roeAndThresholdsRespectLeverage() {
        assertEquals(5.0, engine.roeFor("LONG", 100.0, 100.0 * (1.0 + 5.0 / 1300.0)), 1e-8)
        assertEquals(-20.0, engine.roeFor("SHORT", 100.0, 100.0 * (1.0 + 20.0 / 1300.0)), 1e-8)
        assertEquals(100.0 * (1.0 - 35.0 / 1300.0), engine.thresholdPrice("LONG", 100.0, 35.0), 1e-8)
        assertEquals(100.0 * (1.0 + 90.0 / 1300.0), engine.thresholdPrice("SHORT", 100.0, 90.0), 1e-8)
    }

    @Test fun stopFillsAccountForGapsAndSlippage() {
        assertTrue(engine.stopFillPrice("LONG", 97.0, 95.0) < 95.0)
        assertTrue(engine.stopFillPrice("SHORT", 103.0, 105.0) > 105.0)
        assertEquals(97.0 * (1.0 - 5.0 / 10000.0), engine.stopFillPrice("LONG", 97.0, 100.0), 1e-8)
    }

    @Test fun stateSurvivesSerialization() {
        val state = StrategyState(balance = 123.45,
            position = StrategyPosition("LONG", 0.1, 65000.0, 50.0, 50.0, 6500.0, 1234L, true),
            lastProcessedOpenTime = 4567L,
            recentEvents = listOf(StrategyEvent("DCA", "LONG", 63000.0, 4567L, -21.0, "test")))
        val restored = StrategyState.fromJson(state.toJson())
        assertEquals(state.balance, restored.balance, 1e-8)
        assertEquals(state.lastProcessedOpenTime, restored.lastProcessedOpenTime)
        assertNotNull(restored.position)
        assertEquals("LONG", restored.position?.side)
        assertEquals(100.0, restored.position?.reservedMargin ?: 0.0, 1e-8)
        assertEquals("DCA", restored.recentEvents.first().kind)
    }


    @Test fun entryRulesRequireCrossAndClosedH1TrendStrength() {
        assertTrue(engine.longEntrySignal(29.0, 31.0, 30.0, 20.0, 21.0))
        assertFalse(engine.longEntrySignal(31.0, 32.0, 30.0, 20.0, 21.0))
        assertFalse(engine.longEntrySignal(29.0, 31.0, 30.0, 20.0, 20.0))
        assertTrue(engine.shortEntrySignal(71.0, 69.0, 20.0, 30.0, 21.0))
        assertFalse(engine.shortEntrySignal(69.0, 68.0, 20.0, 30.0, 21.0))
    }

    @Test fun takeProfitRequiresBothRsiAndRoe() {
        assertTrue(engine.takeProfitSignal("LONG", 76.0, 5.0))
        assertFalse(engine.takeProfitSignal("LONG", 76.0, 4.99))
        assertTrue(engine.takeProfitSignal("SHORT", 24.0, 5.0))
        assertFalse(engine.takeProfitSignal("SHORT", 25.0, 8.0))
    }

    @Test fun dcaRequiresLossAdxAndCorrectRsiDirection() {
        assertTrue(engine.dcaSignal("LONG", -20.0, 46.0, 25.0, 24.0))
        assertFalse(engine.dcaSignal("LONG", -19.9, 46.0, 25.0, 24.0))
        assertFalse(engine.dcaSignal("LONG", -21.0, 45.0, 25.0, 24.0))
        assertTrue(engine.dcaSignal("SHORT", -22.0, 46.0, 79.0, 80.0))
        assertFalse(engine.dcaSignal("SHORT", -22.0, 46.0, 81.0, 80.0))
    }

    @Test fun stopRulesRespectPriorityConditionsAndTwoCandleConfirmation() {
        val emergency = engine.thresholdPrice("LONG", 100.0, 90.0)
        assertTrue(engine.emergencyStopTriggered("LONG", emergency, 100.0, 100.0))
        val soft = engine.thresholdPrice("LONG", 100.0, 35.0)
        assertTrue(engine.softStopTriggered("LONG", soft, 99.0, 99.0, 98.0, 101.0, 99.0, 10.0, 20.0, 36.0, 100.0))
        assertFalse(engine.softStopTriggered("LONG", soft, 99.0, 99.0, 98.0, 101.0, 102.0, 10.0, 20.0, 36.0, 100.0))
        val shortSoft = engine.thresholdPrice("SHORT", 100.0, 35.0)
        assertTrue(engine.softStopTriggered("SHORT", 101.0, shortSoft, 98.0, 99.0, 98.0, 99.0, 20.0, 10.0, 36.0, 100.0))
    }

    @Test fun invalidStateDefaultsSafely() {
        assertEquals(100.0, StrategyState.fromJson(null).balance, 1e-8)
        assertNull(StrategyState.fromJson("{not-json").position)
    }

    @Test fun indicatorsWarmUpAndStayInRange() {
        val candles = (0 until 120).map { i ->
            val close = 60000.0 + i * 12.0 + kotlin.math.sin(i / 3.0) * 35.0
            Candle(i * 900000L, close - 5.0, close + 20.0, close - 20.0, close, 1.0, true)
        }
        val points = engine.indicatorSeries(candles)
        assertEquals(candles.size, points.size)
        assertNotNull(points.last().rsi)
        assertNotNull(points.last().adx)
        assertFalse(points.last().rsi!!.isNaN())
        assertTrue(points.last().rsi!! in 0.0..100.0)
    }
}
