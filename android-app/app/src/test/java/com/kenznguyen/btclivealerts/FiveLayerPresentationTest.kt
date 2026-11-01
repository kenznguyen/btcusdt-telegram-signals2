package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class FiveLayerPresentationTest {
    @Test fun missingLayersHaveDifferentActionableExplanations() {
        val reasons = listOf("CANONICAL_DATA_UNAVAILABLE", "INTELLIGENCE_UNAVAILABLE",
            "PREDICTION_UNAVAILABLE", "ORDER_BOOK_UNAVAILABLE")
        val explanations = reasons.map(::fiveLayerReasonVi)
        assertEquals(4, explanations.toSet().size)
        explanations.forEachIndexed { level, text -> assertTrue(text.contains("tầng $level")) }
        assertEquals(fiveLayerReasonVi("CANONICAL_DATA_UNAVAILABLE"), fiveLayerReasonVi("CANDLES_UNAVAILABLE"))
    }

    @Test fun incompleteAndStaleObservationsRemainDistinctFromModelThresholds() {
        assertTrue(fiveLayerReasonVi("TRADE_DATA_INCOMPLETE").contains("khoảng trống ID"))
        assertTrue(fiveLayerReasonVi("STALE_TRADE_EVENTS").contains("bản ghi mới"))
        assertTrue(fiveLayerReasonVi("PREDICTION_BELOW_THRESHOLD").contains("ngưỡng chiến lược"))
        assertTrue(fiveLayerReasonVi("FLOW_DIRECTION_MISMATCH").contains("chưa cùng hướng"))
        assertEquals(fiveLayerReasonVi("INTENT_EXPIRED"), fiveLayerReasonVi("EXPIRED_INTENT"))
    }

    @Test fun observedConfiguredAndMissingStatesDoNotImplyVerifiedConnection() {
        assertEquals("Đã cấu hình", fiveLayerStatusVi("CONFIGURED"))
        assertEquals("Đã có tệp dự báo", fiveLayerStatusVi("ARTIFACT_AVAILABLE"))
        assertNotEquals(fiveLayerStatusVi("MISSING"), fiveLayerStatusVi("NO_ROWS"))
        assertNotEquals(fiveLayerStatusVi("PARTIALLY_FILLED"), fiveLayerStatusVi("FILLED"))
        assertEquals("Thanh lý quan sát", fiveLayerFeedVi("liquidations"))
    }

    @Test fun unknownServerTextIsNeverEchoed() {
        listOf("", "new_reason", "https://private.example/?token=secret", "secret\n/path/db.sqlite").forEach {
            assertEquals("Máy chủ chưa cung cấp giải thích được hỗ trợ.", fiveLayerReasonVi(it))
            assertEquals("Chưa xác định", fiveLayerStatusVi(it))
            assertEquals("Nguồn dữ liệu khác", fiveLayerFeedVi(it))
        }
    }
}
