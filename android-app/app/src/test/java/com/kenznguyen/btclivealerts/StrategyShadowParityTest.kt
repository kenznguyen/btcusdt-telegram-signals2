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
        val buy = StrategyShadow.observe(state, events, "SELL", "OBSERVED", 900000L)
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

    @Test fun closedCandleEngineResultsRemainIdenticalWithShadowObserver() {
        val raw = engine.processClosedCandles(emptyList(), emptyList(), initial)
        val observed = StrategyShadow.observe(raw.first, raw.second, "BUY", "OBSERVED", 0L)
        assertEquals(raw.first.toJson(), observed.state.toJson())
        assertEquals(raw.second, observed.events)
        assertEquals(StrategyConfig(), engine.config)
    }
}
