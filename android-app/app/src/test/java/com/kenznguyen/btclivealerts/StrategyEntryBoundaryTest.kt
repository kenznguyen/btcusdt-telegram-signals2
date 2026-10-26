package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

/** Exact threshold boundary cases shared conceptually with Python predicate tests. */
class StrategyEntryBoundaryTest {
    private val engine = StrategyEngine()

    @Test fun longRequiresCrossAboveThirty() {
        assertTrue(engine.longEntrySignal(30.0, 30.0001, 25.0, 10.0, 21.0))
        assertFalse(engine.longEntrySignal(30.0, 30.0, 25.0, 10.0, 21.0))
        assertFalse(engine.longEntrySignal(31.0, 32.0, 25.0, 10.0, 21.0))
    }

    @Test fun shortRequiresCrossBelowSeventy() {
        assertTrue(engine.shortEntrySignal(70.0, 69.9999, 10.0, 25.0, 21.0))
        assertFalse(engine.shortEntrySignal(70.0, 70.0, 10.0, 25.0, 21.0))
        assertFalse(engine.shortEntrySignal(69.0, 68.0, 10.0, 25.0, 21.0))
    }

    @Test fun h1AdxThresholdIsStrict() {
        assertFalse(engine.longEntrySignal(30.0, 31.0, 25.0, 10.0, 20.0))
        assertTrue(engine.longEntrySignal(30.0, 31.0, 25.0, 10.0, 20.0001))
    }

    @Test fun directionalIndexMustNotBeTied() {
        assertFalse(engine.longEntrySignal(30.0, 31.0, 20.0, 20.0, 40.0))
        assertFalse(engine.shortEntrySignal(70.0, 69.0, 20.0, 20.0, 40.0))
    }
}
