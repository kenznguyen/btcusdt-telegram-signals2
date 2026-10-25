package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.StrategyEvent
import com.kenznguyen.btclivealerts.StrategyPosition
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

class StrategyTraceExporterTest {
    @Test fun entrySnapshotExportsPositionAndAccountState() {
        val position = StrategyPosition("LONG", 0.013, 50000.0, 50.0, 0.0, 650.0, 900000L, false)
        val event = StrategyEvent("ENTRY", "LONG", 50000.0, 900000L, 0.0)
        val json = JSONArray(StrategyTraceExporter.export(listOf(event to StrategyState(position = position)), "BTCUSDT"))
        val item = json.getJSONObject(0)
        assertEquals("ENTRY", item.getString("kind"))
        assertEquals(0.013, item.getDouble("quantity"), 1e-9)
        assertEquals(50.0, item.getDouble("margin"), 1e-9)
        assertEquals(100.0, item.getDouble("balance"), 1e-9)
    }

    @Test fun closedPositionDoesNotFabricateExitQuantity() {
        val event = StrategyEvent("TAKE PROFIT", "LONG", 51000.0, 1800000L, 5.0, netPnl = 2.0, fees = 0.5)
        val item = JSONArray(StrategyTraceExporter.export(listOf(event to StrategyState(balance = 102.0)), "BTCUSDT")).getJSONObject(0)
        assertEquals("TP", item.getString("kind"))
        assertTrue(item.isNull("quantity"))
        assertEquals(2.0, item.getDouble("net_pnl"), 1e-9)
    }

    @Test fun exitTransitionUsesPreExitPositionAndPostExitBalance() {
        val position = StrategyPosition("LONG", 0.013, 50000.0, 50.0, 50.0, 650.0, 900000L, true)
        val before = StrategyState(balance = 100.0, position = position)
        val after = StrategyState(balance = 103.0, position = null)
        val event = StrategyEvent("TAKE PROFIT", "LONG", 51000.0, 1800000L, 5.0,
            netPnl = 3.0, fees = 0.25)
        val transition = StrategyTraceExporter.Transition(event, before, after)
        val item = JSONArray(StrategyTraceExporter.exportTransitions(listOf(transition), "BTCUSDT"))
            .getJSONObject(0)
        assertEquals("TP", item.getString("kind"))
        assertEquals(0.013, item.getDouble("quantity"), 1e-9)
        assertEquals(100.0, item.getDouble("margin"), 1e-9)
        assertEquals(103.0, item.getDouble("balance"), 1e-9)
        assertEquals(0.25, item.getDouble("fees"), 1e-9)
    }

    @Test(expected = IllegalArgumentException::class)
    fun exitTransitionRejectsMissingPreExitPosition() {
        val event = StrategyEvent("SOFT SL", "SHORT", 100.0, 900000L, -35.0)
        StrategyTraceExporter.exportTransitions(
            listOf(StrategyTraceExporter.Transition(event, StrategyState(), StrategyState())),
            "BTCUSDT"
        )
    }

    @Test(expected = IllegalStateException::class)
    fun rejectsUnknownEventKinds() {
        StrategyTraceExporter.export(listOf(StrategyEvent("UNKNOWN", "LONG", 100.0, 1L) to StrategyState()), "BTCUSDT")
    }
}
