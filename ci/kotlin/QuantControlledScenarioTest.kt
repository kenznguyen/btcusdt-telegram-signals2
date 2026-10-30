package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test
import java.io.File

/** Real Kotlin StrategyEngine branch replay. Never submits any order. */
class QuantControlledScenarioTest {
    @Test fun exportIndependentControlledTrace() {
        val folder = File(requireNotNull(System.getenv("QUANT_SCENARIO_DIR")))
        val output = File(requireNotNull(System.getenv("QUANT_KOTLIN_TRACE_OUTPUT")))
        val m15 = File(folder, "m15.csv").reader().use { StrategyCsvReplay.parse(it, 900_000L) }
        val h1 = File(folder, "h1.csv").reader().use { StrategyCsvReplay.parse(it, 3_600_000L) }
        val state = StrategyState.fromJson(File(folder, "initial-state.json").readText())
        val replay = StrategyTraceExporter.replay(StrategyEngine(), m15, h1, state)
        output.parentFile?.mkdirs()
        output.writeText(replay.json.toString(2))
        assertFalse(replay.json.getBoolean("parity_verified"))
        assertTrue(output.length() > 0)
    }
}
