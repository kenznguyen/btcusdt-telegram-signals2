package com.kenznguyen.btclivealerts

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class HummingbotOrderBookTest {
    private val now = 1_800_000_000_000L
    private fun snapshot() = JSONObject("""{
        "symbol":"ETHUSDT","source":"hummingbot","connector":"binance_perpetual",
        "observedAtMs":$now,
        "bids":[{"price":100,"quantity":8},{"price":99,"quantity":2}],
        "asks":[{"price":101,"quantity":5},{"price":102,"quantity":5}]
    }""")

    @Test fun normalizesSnapshotAndReusesExistingDepthCalculation() {
        val book = HummingbotSnapshot.parse(snapshot(), "ETHUSDT", now)
        assertEquals(100.0, book.metrics.bestBid, 0.0)
        assertEquals(101.0, book.metrics.bestAsk, 0.0)
        assertEquals(10.0, book.metrics.bidDepth, 0.0)
        assertEquals(0.0, book.metrics.imbalance, 0.0)
        assertEquals(now, book.observedAtMs)
        assertFalse(book.metrics.synchronized)
    }

    @Test fun rejectsWrongMarketSourceAndStaleOrFutureSnapshots() {
        listOf(
            snapshot().put("symbol", "BTCUSDT"),
            snapshot().put("connector", "binance"),
            snapshot().put("source", "binance"),
            snapshot().put("observedAtMs", now - 30_001),
            snapshot().put("observedAtMs", now + 5_001)
        ).forEach { data ->
            assertThrows(IllegalArgumentException::class.java) {
                HummingbotSnapshot.parse(data, "ETHUSDT", now)
            }
        }
    }

    @Test fun rejectsEmptyCrossedDuplicateAndInvalidLevels() {
        listOf("[]", "[{\"price\":101,\"quantity\":1}]",
            "[{\"price\":100,\"quantity\":-1}]",
            "[{\"price\":100,\"quantity\":1},{\"price\":100,\"quantity\":2}]")
            .forEach { levels ->
                val data = snapshot().put("bids", org.json.JSONArray(levels))
                assertThrows(IllegalArgumentException::class.java) {
                    HummingbotSnapshot.parse(data, "ETHUSDT", now)
                }
            }
    }

    @Test fun endpointRequiresHttpsAndKeepsTokenOutOfUrl() {
        assertEquals("https://example.com/analysis/v1/order-book?symbol=ETHUSDT",
            hummingbotEndpoint("https://example.com/analysis", "ETHUSDT").toString())
        listOf("http://example.com", "https://user:pass@example.com", "https://example.com?token=x")
            .forEach { url -> assertThrows(IllegalArgumentException::class.java) {
                hummingbotEndpoint(url, "ETHUSDT")
            } }
    }
}
