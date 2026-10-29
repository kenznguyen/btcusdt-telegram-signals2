package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class StrategyShadowParityTest {
    private val engine = StrategyEngine()
    private val initial = StrategyState()

    @Test fun shadowCannotChangeBaseStateOrEventsWhenExternalInputsDisagree() {
        val events = listOf(StrategyEvent("LONG ENTRY", "LONG", 100000.0, 900000L))
        val state = initial.copy(lastProcessedOpenTime = 900000L)
        val original = state.toJson()
        val buy = StrategyShadow.observe(state, events, "SELL", "OBSERVED", 900000L, modelCandleTimeMs = 900000L)
        assertEquals(original, state.toJson())
        assertEquals(original, buy.state.toJson())
        assertEquals(events, buy.events)
        assertEquals("DISAGREE", buy.observation.alignment)
        assertEquals("SELL", buy.observation.freqaiAction)
        assertEquals("OBSERVED", buy.observation.intelligenceStatus)
        assertEquals("LONG ENTRY", buy.observation.baseAction)
    }

    @Test fun missingOrExpiredInputsNeverBecomeTradeInstructions() {
        val base = listOf(StrategyEvent("DCA", "LONG", 99000.0, 1800000L))
        val missing = StrategyShadow.observe(initial, base, null, null, 1800000L)
        assertEquals("UNAVAILABLE", missing.observation.alignment)
        assertEquals("DCA", missing.events.single().kind)
        val expired = StrategyShadow.observe(initial, emptyList(), "BUY", "OBSERVED", 900000L,
            validUntilMs = 899999L)
        assertEquals("EXPIRED", expired.observation.alignment)
        assertEquals("NONE", expired.observation.baseAction)
        assertTrue(expired.events.isEmpty())
    }

    @Test fun unmatchedModelCandleNeverClaimsParity() {
        val events = listOf(StrategyEvent("SHORT ENTRY", "SHORT", 100000.0, 900000L))
        val unverified = StrategyShadow.observe(initial, events, "SELL", "OBSERVED", 900000L)
        assertEquals("UNVERIFIED_TIME", unverified.observation.alignment)
        val mismatch = StrategyShadow.observe(initial, events, "SELL", "OBSERVED",
            900000L, modelCandleTimeMs = 1800000L)
        assertEquals("UNVERIFIED_TIME", mismatch.observation.alignment)
        val matched = StrategyShadow.observe(initial, events, "SELL", "OBSERVED",
            900000L, modelCandleTimeMs = 900000L)
        assertEquals("AGREE", matched.observation.alignment)
    }

    @Test fun replayClosedCandlesHasExactBaselineParityWithObserver() {
        val m15 = (0 until 130).map { i ->
            val price = 100000.0 + (i % 31 - 15) * 35.0
            Candle(i * 900000L, price, price + 90, price - 90, price + 12, 3.0, true)
        }
        val h1 = (0 until 70).map { i ->
            val price = 100000.0 + (i % 17 - 8) * 125.0
            Candle(i * 3600000L, price, price + 150, price - 150, price + 20, 15.0, true)
        }
        val baseline = engine.processClosedCandles(m15, h1, initial)
        listOf("BUY", "SELL", "WAIT", null).forEach { model ->
            val observed = StrategyShadow.observe(baseline.first, baseline.second, model,
                "OBSERVED", m15.last().openTime)
            assertEquals(baseline.first.toJson(), observed.state.toJson())
            assertEquals(baseline.second, observed.events)
            assertEquals(baseline.first.lastProcessedOpenTime, observed.state.lastProcessedOpenTime)
        }
    }

    @Test fun closedCandleEngineResultsRemainIdenticalWithShadowObserver() {
        val raw = engine.processClosedCandles(emptyList(), emptyList(), initial)
        val observed = StrategyShadow.observe(raw.first, raw.second, "BUY", "OBSERVED", 0L)
        assertEquals(raw.first.toJson(), observed.state.toJson())
        assertEquals(raw.second, observed.events)
        assertEquals(StrategyConfig(), engine.config)
    }
}
