package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class StrategyTraceExporterTest {
    @Test fun exportsRealEngineReplayWithoutChangingState() {
        val candles = (0 until 100).map { i ->
            Candle(i * 900000L, 100000.0, 100100.0, 99900.0, 100000.0, 1.0, true)
        }
        val hours = (0 until 60).map { i ->
            Candle(i * 3600000L, 100000.0, 100100.0, 99900.0, 100000.0, 1.0, true)
        }
        val engine = StrategyEngine()
        val baseline = engine.processClosedCandles(candles, hours, StrategyState())
        val report = StrategyTraceExporter.replay(engine, candles, hours, StrategyState())
        assertEquals(baseline.first.toJson(), report.state.toJson())
        assertEquals(baseline.second, report.events)
        assertTrue(report.json.getString("dataset_sha256").startsWith("sha256:"))
        assertEquals("kotlin", report.json.getString("engine"))
        assertEquals(report.events.size, report.json.getJSONArray("events").length())
    }

    @Test fun binaryHashMatchesSharedPythonGoldenVector() {
        val bar = Candle(0L, 1.0, 2.0, 0.5, 1.5, 5.0, true)
        assertEquals("sha256:8e39ddb3256cd38e90e160a40767c4d99e93570bca1d402d1972772ee2722a93", StrategyTraceExporter.datasetHash(listOf(bar), emptyList()))
    }

    @Test fun datasetHashDependsOnClosedOhlcvAndNotOpenCandle() {
        val a = Candle(0L, 1.0, 2.0, 0.5, 1.5, 5.0, true)
        val unclosed = a.copy(openTime = 900000L, closed = false)
        val original = StrategyTraceExporter.datasetHash(listOf(a, unclosed), emptyList())
        assertEquals(original, StrategyTraceExporter.datasetHash(listOf(a), emptyList()))
        assertNotEquals(original, StrategyTraceExporter.datasetHash(listOf(a.copy(close = 1.6)), emptyList()))
    }
}
