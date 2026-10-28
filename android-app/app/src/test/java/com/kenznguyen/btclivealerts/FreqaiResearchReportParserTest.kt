package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class FreqaiResearchReportParserTest {
    private fun sample(accuracy: Double = 0.52): String = """
        {
          "engine":"independent LightGBM walk-forward diagnostics; not FreqAI internal predictions",
          "target":"four M15 closed-candle forward return (60 minutes)",
          "not_profitability_evidence":true,
          "oos_rows":1400,
          "oos_mae":0.002,
          "zero_return_mae":0.0025,
          "oos_direction_accuracy":$accuracy,
          "windows":[{"start_utc":"2026-01-01T00:00:00Z","test_rows":1400}]
        }
    """.trimIndent()

    @Test fun importsIndependentResearchWithExplicitLimitations() {
        val report = FreqaiResearchReportParser.parse(sample())
        assertEquals(1400, report.samples)
        assertEquals(1, report.windows)
        assertTrue(report.improvesBaseline)
    }
    @Test fun rejectsInvalidDirectionAccuracy() {
        assertThrows(IllegalArgumentException::class.java) {
            FreqaiResearchReportParser.parse(sample(accuracy = 1.2))
        }
    }
    @Test fun rejectsUnlabeledProfitClaims() {
        assertThrows(IllegalArgumentException::class.java) {
            FreqaiResearchReportParser.parse(sample().replace(
                "\"not_profitability_evidence\":true", "\"not_profitability_evidence\":false"))
        }
    }
}
