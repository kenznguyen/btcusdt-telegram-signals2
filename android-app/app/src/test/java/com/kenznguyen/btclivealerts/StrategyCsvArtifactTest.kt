package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test
import java.io.File

/** CI runner: exports an actual Kotlin StrategyEngine replay from input CSV files. */
class StrategyCsvArtifactTest {
    @Test fun replayProvidedDatasetAndWriteTrace() {
        val m15Path = System.getenv("PARITY_M15_CSV") ?: return
        val h1Path = System.getenv("PARITY_H1_CSV")
            ?: throw IllegalArgumentException("PARITY_H1_CSV required")
        val output = System.getenv("PARITY_KOTLIN_TRACE_OUTPUT")
            ?: throw IllegalArgumentException("PARITY_KOTLIN_TRACE_OUTPUT required")
        val result = File(m15Path).reader().use { m15 ->
            File(h1Path).reader().use { h1 -> StrategyCsvReplay.replay(m15, h1) }
        }
        val target = File(output)
        target.parentFile?.mkdirs()
        target.writeText(result.json.toString(2), Charsets.UTF_8)
        assertEquals("kotlin", result.json.getString("engine"))
        assertFalse(result.json.getBoolean("parity_verified"))
        assertTrue(target.length() > 0)
    }
}
