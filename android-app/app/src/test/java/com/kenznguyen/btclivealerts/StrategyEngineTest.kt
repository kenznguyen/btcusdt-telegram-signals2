package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class StrategyEngineTest {
    @Test fun strategyDefaultsMatchRequestedM15H1DcaProfile() {
        val cfg = StrategyConfig()
        assertEquals(13.0, cfg.leverage, 0.0)
        assertEquals(14, cfg.rsiLength)
        assertEquals(14, cfg.dmiLength)
        assertEquals(14, cfg.adxSmoothing)
        assertEquals(20.0, cfg.h1AdxEntry, 0.0)
        assertEquals(30.0, cfg.longRsiEntry, 0.0)
        assertEquals(70.0, cfg.shortRsiEntry, 0.0)
        assertEquals(76.0, cfg.longRsiTp, 0.0)
        assertEquals(24.0, cfg.shortRsiTp, 0.0)
        assertEquals(5.0, cfg.tpRoe, 0.0)
        assertEquals(-20.0, cfg.dcaRoe, 0.0)
        assertEquals(-35.0, cfg.softSlRoe, 0.0)
        assertEquals(-90.0, cfg.emergencySlRoe, 0.0)
        assertEquals(35.0, cfg.softSlAdx, 0.0)
        assertEquals(45.0, cfg.dcaAdx, 0.0)
        assertEquals(80.0, cfg.shortDcaRsi, 0.0)
        assertEquals(20.0, cfg.longDcaRsi, 0.0)
        assertEquals(0.50, cfg.entryMarginPct, 0.0)
        assertEquals(1.0, cfg.dcaMarginRatio, 0.0)
        assertEquals(100.0, StrategyState().balance, 0.0)
    }


    private val engine = StrategyEngine()

    @Test fun roeAndThresholdsRespectLeverage() {
        assertEquals(5.0, engine.roeFor("LONG", 100.0, 100.0 * (1.0 + 5.0 / 1300.0)), 1e-8)
        assertEquals(-20.0, engine.roeFor("SHORT", 100.0, 100.0 * (1.0 + 20.0 / 1300.0)), 1e-8)
        assertEquals(100.0 * (1.0 - 25.0 / 1300.0), engine.thresholdPrice("LONG", 100.0, 25.0), 1e-8)
        assertEquals(100.0 * (1.0 + 90.0 / 1300.0), engine.thresholdPrice("SHORT", 100.0, 90.0), 1e-8)
    }

    @Test fun stopFillsAccountForGapsAndSlippage() {
        assertTrue(engine.stopFillPrice("LONG", 97.0, 95.0) < 95.0)
        assertTrue(engine.stopFillPrice("SHORT", 103.0, 105.0) > 105.0)
        assertEquals(97.0 * (1.0 - 5.0 / 10000.0), engine.stopFillPrice("LONG", 97.0, 100.0), 1e-8)
    }

    @Test fun entrySlippageIsAdverseForBothSides() {
        assertTrue(engine.executionFillPrice(100.0, "BUY") > 100.0)
        assertTrue(engine.executionFillPrice(100.0, "SELL") < 100.0)
        val noSlippage = StrategyEngine(StrategyConfig(slippageBps = 0.0))
        assertEquals(100.0, noSlippage.executionFillPrice(100.0, "BUY"), 0.0)
        assertEquals(100.0, noSlippage.executionFillPrice(100.0, "SELL"), 0.0)
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
        // DCA threshold is -20% ROE; ADX must be strictly greater than 45.
        assertTrue(engine.dcaSignal("LONG", -20.0, 46.0, 25.0, 24.0))
        assertFalse(engine.dcaSignal("LONG", -19.9, 46.0, 25.0, 24.0))
        assertFalse(engine.dcaSignal("LONG", -20.0, 45.0, 25.0, 24.0))
        assertTrue(engine.dcaSignal("SHORT", -20.0, 46.0, 79.0, 80.0))
        assertFalse(engine.dcaSignal("SHORT", -20.0, 46.0, 81.0, 80.0))
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

    @Test fun indicatorSeriesHandlesRisingFallingAndFlatMarkets() {
        fun candlesFor(step: Double): List<Candle> = (0 until 100).map { i ->
            val close = 1000.0 + step * i
            Candle(
                openTime = i * 900000L,
                open = close - step / 2.0,
                high = close + 2.0,
                low = close - 2.0,
                close = close,
                volume = 1.0,
                closed = true
            )
        }

        val rising = engine.indicatorSeries(candlesFor(2.0)).last()
        assertEquals(100.0, rising.rsi!!, 1e-8)
        assertTrue(rising.plusDi!! > 0.0)
        assertEquals(0.0, rising.minusDi!!, 1e-8)
        assertTrue(rising.adx!! in 0.0..100.0)

        val falling = engine.indicatorSeries(candlesFor(-2.0)).last()
        assertEquals(0.0, falling.rsi!!, 1e-8)
        assertEquals(0.0, falling.plusDi!!, 1e-8)
        assertTrue(falling.minusDi!! > 0.0)
        assertTrue(falling.adx!! in 0.0..100.0)

        val flat = engine.indicatorSeries(candlesFor(0.0)).last()
        assertEquals(50.0, flat.rsi!!, 1e-8)
        assertEquals(0.0, flat.plusDi!!, 1e-8)
        assertEquals(0.0, flat.minusDi!!, 1e-8)
        // With no directional movement, DX/ADX is undefined rather than a fabricated trend.
        assertNull(flat.adx)
    }

    @Test fun invalidStateDefaultsSafely() {
        assertEquals(100.0, StrategyState.fromJson(null).balance, 1e-8)
        assertNull(StrategyState.fromJson("{not-json").position)
    }

    @Test fun corruptPersistedStrategyStateFailsClosedInsteadOfResetting() {
        try {
            StrategyState.fromJson("{broken")
            fail("Corrupt persisted state must not silently reset an open position")
        } catch (expected: IllegalStateException) {
            assertTrue(expected.message!!.contains("refusing to reset"))
        }
    }

    @Test fun persistedPositionRoundTripsAcrossRestart() {
        val state = StrategyState(
            balance = 123.0,
            position = StrategyPosition("LONG", 0.02, 65000.0, 50.0, 50.0, 1300.0, 123456L, true),
            lastProcessedOpenTime = 987654L
        )
        val restored = StrategyState.fromJson(state.toJson())
        assertEquals(state.balance, restored.balance, 0.000001)
        assertEquals(state.position, restored.position)
        assertEquals(state.lastProcessedOpenTime, restored.lastProcessedOpenTime)
    }

    @Test fun h1FilterUsesOnlyCandlesClosedByM15Close() {
        val h1AtMidnight = 0L
        val h1AtOneAm = 60L * 60L * 1000L
        val m15At0045 = 45L * 60L * 1000L
        val m15At0030 = 30L * 60L * 1000L

        // M15 00:45 closes at 01:00, so H1 00:00 is closed and available.
        assertTrue(h1CandleClosedByM15Close(h1AtMidnight, m15At0045))
        // M15 00:30 closes at 00:45; H1 00:00 is still forming.
        assertFalse(h1CandleClosedByM15Close(h1AtMidnight, m15At0030))
        // H1 01:00 cannot be used by the M15 candle closing at 01:00.
        assertFalse(h1CandleClosedByM15Close(h1AtOneAm, m15At0045))
    }

    @Test fun missingHourlyIndicatorsDoNotSuppressEmergencyExit() {
        val m15 = (0 until 100).map { i ->
            val close = if (i == 99) 90.0 else 100.0
            Candle(i * 900000L, 100.0, 101.0, if (i == 99) 80.0 else 99.0, close, 1.0, true)
        }
        // No H1 candles are available; protective emergency exits must still run.
        val h1 = emptyList<Candle>()
        val position = StrategyPosition("LONG", 1.0, 100.0, 50.0, 0.0, 100.0, 0L, false)
        val initial = StrategyState(balance = 100.0, position = position, lastProcessedOpenTime = 98 * 900000L)
        val result = engine.processClosedCandles(m15, h1, initial)
        assertNull(result.first.position)
        assertTrue(result.second.any { it.kind == "EMERGENCY SL" })
    }

    @Test fun emergencyStopStillRunsBeforeRsiWarmupCompletes() {
        val m15 = (0 until 25).map { i ->
            val breached = i == 1
            Candle(
                openTime = i * 900000L,
                open = 100.0,
                high = 101.0,
                low = if (breached) 80.0 else 99.0,
                close = if (breached) 90.0 else 100.0,
                volume = 1.0,
                closed = true
            )
        }
        val position = StrategyPosition("LONG", 1.0, 100.0, 50.0, 0.0, 100.0, 0L, false)
        val initial = StrategyState(balance = 100.0, position = position, lastProcessedOpenTime = 0L)
        val result = engine.processClosedCandles(m15, emptyList(), initial)
        assertNull(result.first.position)
        assertTrue(result.second.any { it.kind == "EMERGENCY SL" && it.candleTime == 900000L })
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
        // Reference values calculated by bot.py/add_indicators on the identical synthetic candles.
        assertEquals(100.0, points.last().rsi!!, 1e-8)
        assertEquals(100.0, points.last().adx!!, 1e-8)
        assertEquals(34.54663034626543, points.last().plusDi!!, 1e-6)
    }
}
