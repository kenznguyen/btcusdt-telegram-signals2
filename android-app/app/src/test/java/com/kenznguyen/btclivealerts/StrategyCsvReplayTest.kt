package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class StrategyCsvReplayTest {
    private val header = "open_time,open,high,low,close,volume,closed\n"
    @Test fun csvFeedsExactEngineAndMatchesV2Hash() {
        val m15 = header + "0,1.0,2.0,0.5,1.5,5.0,1\n"
        val h1 = header + "0,1.0,2.0,0.5,1.5,5.0,1\n"
        val trace = StrategyCsvReplay.replay(m15.reader(), h1.reader())
        val parsed = StrategyCsvReplay.parse(m15.reader(), 900000L)
        assertEquals(1, parsed.size)
        assertEquals(StrategyTraceExporter.datasetHash(parsed, StrategyCsvReplay.parse(h1.reader(), 3600000L)),
            trace.json.getString("dataset_sha256"))
        assertEquals("kotlin", trace.json.getString("engine"))
    }
    @Test fun refusesGapsDuplicatesAndFormingCandles() {
        val first = "0,1,2,0.5,1.5,5,1\n"
        for (second in listOf("1800000,1,2,0.5,1.5,5,1\n",
                              "0,1,2,0.5,1.5,5,1\n",
                              "900000,1,2,0.5,1.5,5,0\n")) {
            try {
                StrategyCsvReplay.parse((header + first + second).reader(), 900000L)
                fail("Expected invalid input to be rejected")
            } catch (expected: IllegalArgumentException) { }
        }
    }
}
