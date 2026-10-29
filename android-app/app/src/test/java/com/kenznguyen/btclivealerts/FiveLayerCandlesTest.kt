package com.kenznguyen.btclivealerts

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException
import java.net.SocketTimeoutException

class FiveLayerCandlesTest {
    private val now = 1_800_000_000_000L
    private val step = 900_000L
    private val start = now - 20 * step
    // Captured from market_data.store.read_window using a real temporary SQLite store.
    private fun fixture() = JSONObject("""{
  "exchange": "binance",
  "marketType": "USDT_PERPETUAL",
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "startMs": 1799982000000,
  "endMs": 1800000000000,
  "asOfMs": null,
  "candles": [
    {
      "exchange": "binance",
      "marketType": "USDT_PERPETUAL",
      "symbol": "BTCUSDT",
      "timeframe": "15m",
      "openTimeMs": 1799982000000,
      "closeTimeMs": 1799982900000,
      "open": "100000.1234567890123456789012345",
      "high": "100001.1234567890123456789012345",
      "low": "99999.1234567890123456789012345",
      "close": "100000.2234567890123456789012345",
      "volume": "2.5000000000000000000000001",
      "isClosed": true,
      "availableAtMs": 1799982900007,
      "availabilityKind": "FIRST_OBSERVED",
      "quality": "VALIDATED",
      "source": "ccxt.binanceusdm"
    },
    {
      "exchange": "binance",
      "marketType": "USDT_PERPETUAL",
      "symbol": "BTCUSDT",
      "timeframe": "15m",
      "openTimeMs": 1799983800000,
      "closeTimeMs": 1799984700000,
      "open": "100001",
      "high": "100002",
      "low": "100000",
      "close": "100001.5",
      "volume": "0",
      "isClosed": true,
      "availableAtMs": 1799984700011,
      "availabilityKind": "FIRST_OBSERVED",
      "quality": "VALIDATED",
      "source": "ccxt.binanceusdm"
    }
  ],
  "datasetVersion": "sha256:a2ba6b4d89c9994f3444b6484a47ba008fc999505d5c7acc8d197a662fabcfee",
  "coverage": {
    "expected": 20,
    "returned": 2,
    "complete": false,
    "gaps": [
      {
        "startMs": 1799982900000,
        "endMs": 1799983800000
      },
      {
        "startMs": 1799984700000,
        "endMs": 1800000000000
      }
    ]
  },
  "generatedAtMs": 1800000000000
}""")
    private fun parse(json: JSONObject) = FiveLayerJson.candles(json, start, now, now)
    private fun first(json: JSONObject) = json.getJSONArray("candles").getJSONObject(0)

    @Test fun queryRequestsExactlyTwentyClosedSlotsWithoutAsOfDrift() {
        val endpoint = fiveLayerCandleEndpoint("https://example.com/api/", now + step - 1)
        assertEquals("/api/v1/candles", endpoint.encodedPath)
        assertEquals(setOf("symbol", "timeframe", "startMs", "endMs"), endpoint.queryParameterNames)
        assertEquals("BTCUSDT", endpoint.queryParameter("symbol"))
        assertEquals("15m", endpoint.queryParameter("timeframe"))
        assertEquals(start.toString(), endpoint.queryParameter("startMs"))
        assertEquals(now.toString(), endpoint.queryParameter("endMs"))
        assertEquals((now + step).toString(),
            fiveLayerCandleEndpoint("https://example.com", now + step).queryParameter("endMs"))
    }

    @Test fun canonicalFixturePreservesPrecisionAndShowsMissingSlots() {
        val window = parse(fixture())
        assertEquals(20, window.expected)
        assertEquals(2, window.returned)
        assertFalse(window.complete)
        assertEquals("100000.1234567890123456789012345", window.candles.first().open)
        assertEquals("2.5000000000000000000000001", window.candles.first().volume)
        assertEquals("0", window.candles.last().volume)
        assertEquals(listOf(CandleGap(start + step, start + 2 * step),
            CandleGap(start + 3 * step, now)), window.gaps)
        assertEquals(java.lang.Long.valueOf(now), window.generatedAtMs)
        val legacy = fixture().also { it.remove("generatedAtMs") }
        assertNull(parse(legacy).generatedAtMs)
        assertEquals(2, parse(legacy).candles.size)
    }

    @Test fun wrongRangeMarketSourceAndMutableAsOfAreRejected() {
        val variants = listOf(
            fixture().put("startMs", start + step), fixture().put("endMs", now + step),
            fixture().put("symbol", "ETHUSDT"), fixture().put("timeframe", "1h"),
            fixture().put("marketType", "SPOT"), fixture().put("asOfMs", now),
            fixture().put("datasetVersion", "sha256:abc"),
            fixture().also { first(it).put("source", "demo") },
            fixture().also { first(it).put("availabilityKind", "BACKDATED") },
            fixture().also { first(it).put("symbol", "ETHUSDT") }
        )
        variants.forEach { assertThrows(IllegalArgumentException::class.java) { parse(it) } }
    }

    @Test fun coverageCannotHideGapsDuplicateReorderOrExcessCandles() {
        val variants = listOf(
            fixture().also { it.getJSONObject("coverage").put("complete", true) },
            fixture().also { it.getJSONObject("coverage").put("returned", 20) },
            fixture().also { it.getJSONObject("coverage").put("expected", 19) },
            fixture().also { it.getJSONObject("coverage").put("gaps", JSONArray()) },
            fixture().also { it.getJSONObject("coverage").getJSONArray("gaps").getJSONObject(0).put("endMs", now) },
            fixture().also { it.getJSONArray("candles").put(1, first(it)) },
            fixture().also {
                val rows = it.getJSONArray("candles")
                val second = rows.getJSONObject(1)
                rows.put(1, rows.getJSONObject(0)); rows.put(0, second)
            },
            fixture().also { json ->
                json.put("candles", JSONArray((0..20).map { first(json) }))
            }
        )
        variants.forEach { assertThrows(IllegalArgumentException::class.java) { parse(it) } }
        val empty = fixture().put("candles", JSONArray()).put("coverage", JSONObject()
            .put("expected", 20).put("returned", 0).put("complete", false)
            .put("gaps", JSONArray().put(JSONObject().put("startMs", start).put("endMs", now))))
        assertEquals(0, parse(empty).returned)
        assertEquals(listOf(CandleGap(start, now)), parse(empty).gaps)
    }

    @Test fun openFutureInvalidOhlcAndNonDecimalValuesAreRejected() {
        val variants = listOf(
            fixture().also { first(it).put("isClosed", false) },
            fixture().also { first(it).put("openTimeMs", start + 1) },
            fixture().also { first(it).put("closeTimeMs", start + step + 1) },
            fixture().also { first(it).put("availableAtMs", now + 1) },
            fixture().also { first(it).put("availableAtMs", start + step - 1) },
            fixture().put("generatedAtMs", now + 1),
            fixture().put("generatedAtMs", now.toDouble()),
            fixture().also { first(it).put("high", "1") },
            fixture().also { first(it).put("low", "0") },
            fixture().also { first(it).put("open", 100000) },
            fixture().also { first(it).put("close", "NaN") },
            fixture().also { first(it).put("volume", "-1") },
            fixture().also { first(it).put("volume", "1e-31") },
            fixture().also { first(it).put("close", "1e9999999") }
        )
        variants.forEach { assertThrows(IllegalArgumentException::class.java) { parse(it) } }
    }

    @Test fun candleFreshnessDetectsOldLatestCloseEvenWhenApiWasJustFetched() {
        val window = parse(fixture())
        assertEquals(17_100_000L, canonicalCandleLagMs(window, now))
        assertTrue(canonicalCandlesStale(window, now))
        assertFalse(canonicalCandlesStale(window, window.candles.last().closeTimeMs + 1_800_000L))
        assertTrue(canonicalCandlesStale(window, window.candles.last().closeTimeMs + 1_800_001L))
        assertNull(canonicalCandleLagMs(window.copy(candles = emptyList()), now))
        assertTrue(canonicalCandlesStale(window.copy(candles = emptyList()), now))
    }

    @Test fun errorsExposeOnlyStructuredCodesAndFixedMessages() {
        val expected = mapOf(401 to FiveLayerFailure.AUTH, 403 to FiveLayerFailure.AUTH,
            404 to FiveLayerFailure.ENDPOINT, 429 to FiveLayerFailure.RATE_LIMIT,
            503 to FiveLayerFailure.UNAVAILABLE, 500 to FiveLayerFailure.HTTP, 302 to FiveLayerFailure.HTTP)
        expected.forEach { (status, code) ->
            val failure = fiveLayerHttpFailure(status)
            assertEquals(code, failure.code)
            assertEquals(status, failure.httpStatus)
            assertEquals(code.messageVi, failure.message)
            assertNull(failure.cause)
        }
        val secretText = "https://secret.example?token=secret-response"
        val network = fiveLayerNetworkFailure(IOException(secretText))
        val timeout = fiveLayerNetworkFailure(SocketTimeoutException(secretText))
        assertEquals(FiveLayerFailure.NETWORK, network.code)
        assertEquals(FiveLayerFailure.TIMEOUT, timeout.code)
        listOf(network, timeout, FiveLayerApiException(FiveLayerFailure.INVALID_RESPONSE)).forEach {
            assertFalse(it.toString().contains(secretText))
            assertNull(it.cause)
            assertNull(it.httpStatus)
        }
    }
}

