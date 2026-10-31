package com.kenznguyen.btclivealerts

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class FiveLayerApiTest {
    private val now = 1_800_000_000_000L
    private fun ledger() = JSONObject("""{
        "mode":"PAPER","liveTradingSupported":false,"paused":false,
        "positionBase":"0.001000000000000000000001","averageEntryPrice":"100000.1234567890123456789",
        "realizedPnlQuote":"-0.000000000000000000000001","feesQuote":"0.000000000000000000000002",
        "netRealizedPnlQuote":"-0.000000000000000000000003",
        "simulationModel":"VISIBLE_DEPTH_LIMIT_SNAPSHOT","orders":[]
    }""")
    private fun order() = JSONObject("""{
        "mode":"PAPER","orderId":"paper:123","intentId":"intent:123",
        "status":"PARTIALLY_FILLED","side":"BUY","quantityBase":"0.002",
        "filledBase":"0.001","remainingBase":"0.001","averagePrice":"100000",
        "feeQuote":"0.05","createdAtMs":$now,"updatedAtMs":$now,"reason":"VISIBLE_DEPTH_SIMULATION"
    }""")
    private fun decision() = JSONObject("""{
        "action":"BUY","reason":"MODEL_LONG","intent":{
        "mode":"PAPER","symbol":"BTCUSDT","exchange":"binance","marketType":"USDT_PERPETUAL",
        "targetPositionBase":"0.001","limitPrice":"100000.1234567890123456789",
        "modelVersion":"model-1","strategyVersion":"strategy-1","datasetVersion":"sha256:123",
        "decisionAtMs":$now,"validUntilMs":${now + 30_000}}}
    """)
    private fun intelligence(): JSONObject {
        val result = JSONObject("""{
            "schemaVersion":1,"symbol":"BTCUSDT","exchange":"binance","marketType":"USDT_PERPETUAL",
            "quality":"OBSERVED_ONLY","source":"binance-futures-collector@bc4f0ef633fbeee4a49defd72827f17162693805",
            "windowStartMs":${now - 60_000},"windowEndMs":$now,"availableAtMs":$now,
            "fundingRate":null,"fundingAtMs":null,"openInterestBase":null,"openInterestChangeBase":null,
            "takerBuyQuote":"1234567890.1234567890123456789","takerSellQuote":"0",
            "netTakerQuote":"1234567890.1234567890123456789","largeTradeQuote":"0",
            "observedLiquidationBuyQuote":null,"observedLiquidationSellQuote":null
        }""")
        val coverage = JSONObject()
        listOf("trades", "funding", "openInterest", "liquidations").forEach { name ->
            coverage.put(name, JSONObject().put("status", if (name == "trades") "OBSERVED" else "MISSING")
                .put("rows", if (name == "trades") 1 else 0).put("complete", false)
                .put("lastEventAtMs", if (name == "trades") now - 1 else JSONObject.NULL)
                .put("tradeIdGaps", 0))
        }
        return result.put("coverage", coverage)
    }

    @Test fun endpointsAreFixedHttpsAndNeverCarryCredentials() {
        assertEquals("https://example.com/api/v1/paper/evaluate",
            fiveLayerEndpoint("https://example.com/api/", "paper/evaluate").toString())
        listOf("http://example.com", "https://user:pass@example.com", "https://example.com?token=x",
            "https://example.com#fragment").forEach { url ->
            assertThrows(IllegalArgumentException::class.java) { fiveLayerEndpoint(url, "paper") }
        }
        assertThrows(IllegalArgumentException::class.java) { fiveLayerEndpoint("https://example.com", "../live/order") }
    }

    @Test fun systemRequiresFiveDistinctLayersAndPaperOnly() {
        fun system() = JSONObject().put("mode", "PAPER").put("liveTradingSupported", false)
            .put("layers", JSONArray((0..4).map { JSONObject().put("level", it).put("name", "Layer $it")
                .put("status", "WAIT").put("detail", "Waiting") }))
        assertEquals(5, FiveLayerJson.system(system()).layers.size)
        listOf(system().put("mode", "LIVE"), system().put("liveTradingSupported", true),
            system().put("liveTradingSupported", "false"),
            system().also { it.getJSONArray("layers").getJSONObject(4).put("level", 0) }).forEach {
            assertThrows(IllegalArgumentException::class.java) { FiveLayerJson.system(it) }
        }
    }

    @Test fun preservesDecimalPrecisionAndMissingFeedState() {
        val parsed = FiveLayerJson.intelligence(intelligence(), now)
        assertTrue(parsed.available)
        assertEquals("1234567890.1234567890123456789", parsed.netTakerQuote)
        assertNull(parsed.fundingRate)
        assertNull(parsed.observedLiquidationBuyQuote)
        assertEquals("MISSING", parsed.coverage.first { it.name == "funding" }.status)
        val missing = FiveLayerJson.intelligence(JSONObject("""{"available":false,"reason":"INTELLIGENCE_UNAVAILABLE"}"""), now)
        assertFalse(missing.available)
        assertNull(missing.netTakerQuote)
        assertEquals("0.001000000000000000000001", FiveLayerJson.ledger(ledger(), now).positionBase)
    }

    @Test fun rejectsWrongMarketFutureTimeAndContradictoryMissingMetrics() {
        listOf(intelligence().put("symbol", "ETHUSDT"), intelligence().put("source", "demo"),
            intelligence().put("availableAtMs", now + 5_001), intelligence().put("fundingRate", "0"),
            intelligence().put("netTakerQuote", 123.0), intelligence().put("netTakerQuote", "NaN")).forEach {
            assertThrows(IllegalArgumentException::class.java) { FiveLayerJson.intelligence(it, now) }
        }
    }

    @Test fun parsesDecisionAndRejectsLiveWrongMarketAndUnboundedLifetime() {
        assertEquals("100000.1234567890123456789", FiveLayerJson.decision(decision(), now).intent?.limitPrice)
        assertNull(FiveLayerJson.decision(JSONObject("""{"action":"WAIT","reason":"MODEL_MISSING","intent":null}"""), now).intent)
        listOf(decision().also { it.getJSONObject("intent").put("mode", "LIVE") },
            decision().also { it.getJSONObject("intent").put("symbol", "ETHUSDT") },
            decision().also { it.getJSONObject("intent").put("validUntilMs", now + 30_001) },
            decision().put("action", "WAIT"), decision().put("intent", JSONObject.NULL)).forEach {
            assertThrows(IllegalArgumentException::class.java) { FiveLayerJson.decision(it, now) }
        }
    }

    @Test fun paperBoundaryRejectsUnknownStateFutureOrdersAndInvalidAmounts() {
        val partial = FiveLayerJson.order(order(), now)
        assertEquals("PARTIALLY_FILLED", partial.status)
        assertEquals("0.001", partial.remainingBase)
        listOf(order().put("mode", "LIVE"), order().put("status", "PENDING_REMOTE"),
            order().put("updatedAtMs", now + 5_001), order().put("feeQuote", "-1"),
            order().put("filledBase", "0.003"), order().put("quantityBase", "1e9999999")).forEach {
            assertThrows(IllegalArgumentException::class.java) { FiveLayerJson.order(it, now) }
        }
        listOf(ledger().put("liveTradingSupported", true), ledger().put("positionBase", "Infinity"),
            ledger().put("averageEntryPrice", "0"), ledger().put("feesQuote", 0)).forEach {
            assertThrows(IllegalArgumentException::class.java) { FiveLayerJson.ledger(it, now) }
        }
    }

    @Test fun evaluateDistinguishesWaitFromSubmittedPaperOrder() {
        val wait = JSONObject("""{"decision":{"action":"WAIT","reason":"STALE_INPUT","intent":null},"order":null}""")
        assertNull(FiveLayerJson.evaluation(wait, now).order)
        val submitted = FiveLayerJson.evaluation(JSONObject().put("decision", decision()).put("order", order()), now)
        assertEquals("BUY", submitted.decision.action)
        assertEquals("paper:123", submitted.order?.orderId)
    }

    @Test fun equityParserPreservesPersistentRiskMetricsAndRejectsInvalidHistory() {
        val point = JSONObject().put("id",1).put("observedAtMs",now).put("equity","101.25")
        val latest = JSONObject().put("observedAtMs",now).put("equity","101.25").put("realizedPnl","2")
            .put("unrealizedPnl","-0.25").put("fees","0.5")
        val limits = JSONObject().put("configured",true).put("maxDrawdownPct","20")
            .put("maxDailyLossUsdt","10").put("maxExposureUsdt","1000")
        val payload = JSONObject().put("available",true).put("points",JSONArray().put(point))
            .put("latest",latest).put("initialCapital","100").put("maxDrawdownUsdt","5")
            .put("maxDrawdownPct","4.71").put("dailyLossUsdt","0.25")
            .put("dailyBaselineAtMs",now-60_000).put("exposureUsdt","101.25")
            .put("riskLimits",limits)
        val parsed = FiveLayerJson.equity(payload,now)
        assertEquals("100",parsed.initialCapital)
        assertEquals("101.25",parsed.equity)
        assertEquals("5",parsed.maxDrawdownUsdt)
        assertEquals("0.25",parsed.dailyLossUsdt)
        assertEquals(1,parsed.points.size)
        assertTrue(parsed.riskLimitsConfigured)
        assertEquals("1000",parsed.maxExposureUsdt)
        val invalid = JSONObject(payload.toString()).put("points",
            JSONArray().put(JSONObject(point.toString()).put("equity","NaN")))
        assertThrows(IllegalArgumentException::class.java) { FiveLayerJson.equity(invalid,now) }
    }

    @Test fun equityEndpointIsReadOnlyAndFixed() {
        assertEquals("https://example.com/v1/equity",fiveLayerEndpoint("https://example.com","equity").toString())
        assertThrows(IllegalArgumentException::class.java) { fiveLayerEndpoint("https://example.com","live/order") }
    }

}
