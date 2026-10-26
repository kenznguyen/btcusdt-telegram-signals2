package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

/** Boundary symmetry with Python test_soft_stop_boundary.py. */
class StrategySoftStopBoundaryTest {
    private val engine = StrategyEngine()

    @Test fun longSoftStopRequiresPriorClosedH1ReversalAndTwoBearishCandles() {
        val entry = 100.0 * 1.0005
        val threshold = engine.thresholdPrice("LONG", entry, 35.0)
        val low = threshold - 0.01
        assertTrue(engine.softStopTriggered(
            "LONG", low, entry, entry, low + 0.005,
            entry + 0.5, entry, 10.0, 30.0, 40.0, entry))
        assertFalse(engine.softStopTriggered(
            "LONG", low, entry, entry, low + 0.005,
            entry + 0.5, entry, 10.0, 30.0, 35.0, entry))
        assertFalse(engine.softStopTriggered(
            "LONG", low, entry, entry, low + 0.005,
            entry + 0.5, entry, 35.0, 30.0, 40.0, entry))
        assertFalse(engine.softStopTriggered(
            "LONG", low, entry, entry, low + 0.005,
            entry + 0.5, entry + 1.0, 10.0, 30.0, 40.0, entry))
        assertFalse(engine.softStopTriggered(
            "LONG", entry, entry, entry, low + 0.005,
            entry + 0.5, entry, 10.0, 30.0, 40.0, entry))
        assertTrue(engine.stopFillPrice("LONG", threshold, entry) < threshold)
    }
}
