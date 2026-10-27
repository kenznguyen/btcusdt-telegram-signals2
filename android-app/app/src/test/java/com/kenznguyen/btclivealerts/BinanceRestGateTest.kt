package com.kenznguyen.btclivealerts

import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BinanceRestGateTest {
    @Test fun http418OpensSharedCooldownAndCanBeResetInTest() {
        BinanceRestGate.resetForTests()
        val before = System.currentTimeMillis()
        val response = Response.Builder()
            .request(Request.Builder().url("https://fapi.binance.com/fapi/v1/klines").build())
            .protocol(Protocol.HTTP_1_1)
            .code(418)
            .message("I'm a teapot")
            .build()
        BinanceRestGate.observe(response)
        assertEquals("HTTP 418", BinanceRestGate.currentBlockReason())
        assertTrue(BinanceRestGate.blockedUntil() >= before + 14L * 60L * 1000L)
        BinanceRestGate.resetForTests()
        assertEquals(null, BinanceRestGate.currentBlockReason())
    }

    @Test fun http429HonorsRetryAfterHeader() {
        BinanceRestGate.resetForTests()
        val before = System.currentTimeMillis()
        val response = Response.Builder()
            .request(Request.Builder().url("https://fapi.binance.com/fapi/v1/depth").build())
            .protocol(Protocol.HTTP_1_1)
            .code(429)
            .message("Too Many Requests")
            .header("Retry-After", "120")
            .build()
        BinanceRestGate.observe(response)
        assertEquals("HTTP 429", BinanceRestGate.currentBlockReason())
        assertTrue(BinanceRestGate.blockedUntil() >= before + 119_000L)
        BinanceRestGate.resetForTests()
    }
}
