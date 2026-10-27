package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class AlertPolicyTest {
    @Test fun masterSwitchBlocksEveryAlertSourceAndDirection() {
        listOf(null, "LONG", "SHORT", "BUY", "SELL", "EARLY BUY", "EARLY SELL").forEach { direction ->
            assertFalse(AlertPolicy.allows(false, true, direction, true, true))
        }
    }

    @Test fun earlyAndScannerSignalsUseTheSameDirectionFiltersAsStrategyEvents() {
        listOf("LONG", "BUY", "EARLY BUY").forEach {
            assertFalse(AlertPolicy.allows(true, true, it, false, true))
            assertTrue(AlertPolicy.allows(true, true, it, true, false))
        }
        listOf("SHORT", "SELL", "EARLY SELL").forEach {
            assertFalse(AlertPolicy.allows(true, true, it, true, false))
            assertTrue(AlertPolicy.allows(true, true, it, false, true))
        }
        assertFalse(AlertPolicy.allows(true, false, "LONG", true, true))
    }

    @Test fun overnightQuietHoursIncludeStartButExcludeEnd() {
        assertFalse(AlertPolicy.isQuietHour(true, 22, 23, 7))
        assertTrue(AlertPolicy.isQuietHour(true, 23, 23, 7))
        assertTrue(AlertPolicy.isQuietHour(true, 0, 23, 7))
        assertTrue(AlertPolicy.isQuietHour(true, 6, 23, 7))
        assertFalse(AlertPolicy.isQuietHour(true, 7, 23, 7))
        assertFalse(AlertPolicy.isQuietHour(false, 0, 23, 7))
    }

    @Test fun daytimeAndAllDayQuietHoursAreHandled() {
        assertFalse(AlertPolicy.isQuietHour(true, 8, 9, 17))
        assertTrue(AlertPolicy.isQuietHour(true, 9, 9, 17))
        assertFalse(AlertPolicy.isQuietHour(true, 17, 9, 17))
        assertTrue(AlertPolicy.isQuietHour(true, 12, 7, 7))
    }

    @Test fun queuedAlertKeepsPolicyAndHistoryMetadataForCatchUp() {
        val alert = QueuedAlert("early:BUY:123", "title | separator", "body | more", "Cảnh báo sớm",
            "EARLY BUY", "early_warning_enabled", historyRecorded = true)
        val restored = QueuedAlert.decode(alert.encode())!!
        assertEquals(alert, restored)
        // A direction/type disabled after queueing must suppress catch-up delivery.
        assertFalse(AlertPolicy.allows(true, true, restored.direction, false, true))
        assertFalse(AlertPolicy.allows(true, false, restored.direction, true, true))
        assertFalse(AlertPolicy.allows(false, true, restored.direction, true, true))
        assertTrue(restored.historyRecorded)
    }

    @Test fun legacyQueueRemainsReadableWithoutLosingBodySeparators() {
        val restored = QueuedAlert.decode("event:123|BTCUSDT.P · LONG ENTRY|LONG · note | detail")!!
        assertEquals("LONG · note | detail", restored.body)
        assertEquals("LONG", restored.direction)
        assertEquals("alert_entry", restored.enabledPreference)
        assertFalse(restored.historyRecorded)
        assertNull(QueuedAlert.decode("invalid"))
    }
}
