package com.kenznguyen.btclivealerts

import org.json.JSONException
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class PaperOrderValidationTest {
    private val now = 1_800_000_000_000L
    // Actual PaperLedger.submit/cancel output from separate temporary SQLite databases.
    private fun fixtures() = JSONObject("""{
"filled":{"orderId":"paper:9e529df550da0f8c114d7022f14fc009368b14643c3f4c9b922a965821425a76","intentId":"intent:filled","status":"FILLED","side":"BUY","quantityBase":"0.2","filledBase":"0.2","remainingBase":"0","averagePrice":"100.1","feeQuote":"0.02002","createdAtMs":1800000000000,"updatedAtMs":1800000000000,"mode":"PAPER","reason":"VISIBLE_DEPTH_SIMULATION"},
"partial":{"orderId":"paper:ab2e744f3c894356ce57a3d59fb41f4d8b6e8d7b573d87e21d14510ee0b790d0","intentId":"intent:partial","status":"PARTIALLY_FILLED","side":"BUY","quantityBase":"0.2","filledBase":"0.05","remainingBase":"0.15","averagePrice":"100.1","feeQuote":"0.005005","createdAtMs":1800000000000,"updatedAtMs":1800000000000,"mode":"PAPER","reason":"VISIBLE_DEPTH_SIMULATION"},
"open":{"orderId":"paper:f61aff6487d118e9bf443a515c7eebb236c6075ddfd4c4b6ed8e404a07d00dc1","intentId":"intent:open","status":"OPEN","side":"BUY","quantityBase":"0.2","filledBase":"0","remainingBase":"0.2","averagePrice":null,"feeQuote":"0","createdAtMs":1800000000000,"updatedAtMs":1800000000000,"mode":"PAPER","reason":"VISIBLE_DEPTH_SIMULATION"},
"canceledPartial":{"orderId":"paper:60fc8c46b32e23f9bbf6474133c5fbddd7f0f3ebff3b2c6063e52f2ecb64bf2f","intentId":"intent:canceledPartial","status":"CANCELED","side":"BUY","quantityBase":"0.2","filledBase":"0.05","remainingBase":"0.15","averagePrice":"100.1","feeQuote":"0.005005","createdAtMs":1800000000000,"updatedAtMs":1800000000001,"mode":"PAPER","reason":"CANCELED_BY_USER"},
"canceledOpen":{"orderId":"paper:08a42c701989c8fd53799e40bc58a4202d345eae2889090513e4fe4cd40c180a","intentId":"intent:canceledOpen","status":"CANCELED","side":"BUY","quantityBase":"0.2","filledBase":"0","remainingBase":"0.2","averagePrice":null,"feeQuote":"0","createdAtMs":1800000000000,"updatedAtMs":1800000000001,"mode":"PAPER","reason":"CANCELED_BY_USER"},
"zeroFilled":{"orderId":"paper:8ea31013fa1bea8d7ac8e05ae55ab1fe8766bf261007204efbffe0e1d7b9438c","intentId":"intent:zeroFilled","status":"FILLED","side":"NONE","quantityBase":"0","filledBase":"0","remainingBase":"0","averagePrice":null,"feeQuote":"0","createdAtMs":1800000000000,"updatedAtMs":1800000000000,"mode":"PAPER","reason":"TARGET_ALREADY_REACHED"},
"zeroRejected":{"orderId":"paper:f3c34332854be5be592dbc7375698c6b5dc6ece6a8397057d14482f157ddd1cd","intentId":"intent:zeroRejected","status":"REJECTED","side":"NONE","quantityBase":"0","filledBase":"0","remainingBase":"0","averagePrice":null,"feeQuote":"0","createdAtMs":1800000000000,"updatedAtMs":1800000000000,"mode":"PAPER","reason":"PAUSED"},
"rejectedPositive":{"orderId":"paper:c4e6161a1ea42d80a801a822d74f95e463e83481e2c167968cce8d99190ff840","intentId":"intent:rejectedPositive","status":"REJECTED","side":"BUY","quantityBase":"0.2","filledBase":"0","remainingBase":"0.2","averagePrice":null,"feeQuote":"0","createdAtMs":1800000000000,"updatedAtMs":1800000000000,"mode":"PAPER","reason":"PAUSED"}
}""")
    private fun receipt(name: String) = fixtures().getJSONObject(name)
    private fun parse(json: JSONObject) = FiveLayerJson.order(json, now + 1)

    @Test fun acceptsActualFilledOpenPartialCanceledAndZeroQuantityReceipts() {
        val expected = mapOf("filled" to "FILLED", "partial" to "PARTIALLY_FILLED", "open" to "OPEN",
            "canceledPartial" to "CANCELED", "canceledOpen" to "CANCELED",
            "zeroFilled" to "FILLED", "zeroRejected" to "REJECTED", "rejectedPositive" to "REJECTED")
        expected.forEach { (name, status) ->
            val order = parse(receipt(name))
            assertEquals(status, order.status)
            assertEquals("intent:$name", order.intentId)
        }
        val noChange = parse(receipt("zeroFilled"))
        assertEquals("NONE", noChange.side)
        assertEquals("0", noChange.quantityBase)
        assertNull(noChange.averagePrice)
        assertEquals("TARGET_ALREADY_REACHED", noChange.reason)
        val paused = parse(receipt("zeroRejected"))
        assertEquals("NONE", paused.side)
        assertEquals("PAUSED", paused.reason)
        val canceledPartial = parse(receipt("canceledPartial"))
        assertEquals("0.05", canceledPartial.filledBase)
        assertEquals("0.15", canceledPartial.remainingBase)
        assertEquals("0.005005", canceledPartial.feeQuote)
        assertEquals("100.1", canceledPartial.averagePrice)
    }

    @Test fun rejectsContradictoryAmountsAndStatusClaims() {
        listOf(
            receipt("partial").put("remainingBase", "0.149999999999999999999999"),
            receipt("partial").put("quantityBase", "0.200000000000000000000001"),
            receipt("partial").put("status", "OPEN"),
            receipt("open").put("status", "PARTIALLY_FILLED"),
            receipt("partial").put("status", "FILLED"),
            receipt("partial").put("status", "REJECTED"),
            receipt("filled").put("status", "CANCELED"),
            receipt("zeroFilled").put("status", "OPEN"),
            receipt("zeroFilled").put("status", "PARTIALLY_FILLED"),
            receipt("zeroFilled").put("status", "CANCELED")
        ).forEach { assertThrows(IllegalArgumentException::class.java) { parse(it) } }
    }

    @Test fun requiresSideToMatchQuantityAndPriceFeeToMatchObservedFills() {
        listOf(
            receipt("partial").put("side", "NONE"),
            receipt("zeroFilled").put("side", "BUY"),
            receipt("zeroRejected").put("side", "SELL"),
            receipt("open").put("feeQuote", "0.000000000000000000000001"),
            receipt("open").put("averagePrice", "100.1"),
            receipt("zeroFilled").put("averagePrice", "0"),
            receipt("rejectedPositive").put("feeQuote", "0.001"),
            receipt("partial").put("averagePrice", JSONObject.NULL),
            receipt("filled").put("averagePrice", "0")
        ).forEach { assertThrows(IllegalArgumentException::class.java) { parse(it) } }
        // A zero-fee simulator configuration remains valid for an actual fill.
        assertEquals("0", parse(receipt("filled").put("feeQuote", "0")).feeQuote)
        assertEquals("SELL", parse(receipt("partial").put("side", "SELL")).side)
    }

    @Test fun requiresBoundedNonblankPrintableIntentIdentifier() {
        listOf(JSONObject.NULL, "", " ", "x".repeat(201), "intent:\nsecret", 123).forEach { value ->
            assertThrows(IllegalArgumentException::class.java) { parse(receipt("filled").put("intentId", value)) }
        }
        val missing = receipt("filled").also { it.remove("intentId") }
        assertThrows(JSONException::class.java) { parse(missing) }
        val longest = "x".repeat(200)
        assertEquals(longest, parse(receipt("filled").put("intentId", longest)).intentId)
    }

    @Test fun quantityConservationUsesDecimalArithmeticWithoutRounding() {
        val precise = receipt("partial").put("quantityBase", "0.12345678901234567890123456789")
            .put("filledBase", "0.1").put("remainingBase", "0.02345678901234567890123456789")
        assertEquals("0.12345678901234567890123456789", parse(precise).quantityBase)
        assertThrows(IllegalArgumentException::class.java) {
            parse(precise.put("remainingBase", "0.02345678901234567890123456788"))
        }
    }
}

