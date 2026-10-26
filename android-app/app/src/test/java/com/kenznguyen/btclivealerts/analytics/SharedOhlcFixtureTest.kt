package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Shared OHLC fixture is stored in freqtrade-backtest and loaded from the
 * checkout in CI. This test fails if the shared fixture is unavailable.
 */
class SharedOhlcFixtureTest {
    private fun candles(array: org.json.JSONArray): List<Candle> =
        (0 until array.length()).map { index ->
            val row = array.getJSONObject(index)
            Candle(
                openTime = row.getLong("timestamp_ms"),
                open = row.getDouble("open"),
                high = row.getDouble("high"),
                low = row.getDouble("low"),
                close = row.getDouble("close"),
                volume = row.getDouble("volume"),
                closed = row.getBoolean("closed")
            )
        }

    @Test fun sharedFixtureReplaysWithoutInventingSignals() {
        val fixtureFile = java.io.File("../freqtrade-backtest/fixtures/android_python_ohlc_v1.json")
        assertTrue("Shared fixture must be present in checkout", fixtureFile.isFile)
        val fixture = JSONObject(fixtureFile.readText())
        assertEquals(1, fixture.getInt("schema_version"))
        val result = StrategyTraceReplay.run(
            StrategyEngine(),
            candles(fixture.getJSONArray("candles_m15")),
            candles(fixture.getJSONArray("candles_h1")),
            fixture.getString("symbol")
        )
        assertEquals(fixture.getJSONObject("expected").getInt("event_count"), result.transitions.size)
        assertEquals(fixture.getJSONObject("expected").getDouble("final_balance"), result.finalState.balance, 1e-9)
        assertEquals(0, org.json.JSONArray(result.json).length())
    }
}
