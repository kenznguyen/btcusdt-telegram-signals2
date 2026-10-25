package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.StrategyEvent
import com.kenznguyen.btclivealerts.StrategyState
import org.json.JSONArray
import org.json.JSONObject

/**
 * Read-only export for deterministic offline parity checks.
 * The caller must collect full event/state snapshots via StrategyEngine's
 * onCandle callback; recentEvents is limited to 30 and is not sufficient.
 */
object StrategyTraceExporter {
    private val kinds = mapOf(
        "ENTRY" to "ENTRY",
        "LONG ENTRY" to "ENTRY",
        "SHORT ENTRY" to "ENTRY",
        "DCA" to "DCA",
        "TAKE PROFIT" to "TP",
        "SOFT SL" to "SOFT_SL",
        "EMERGENCY SL" to "EMERGENCY_SL"
    )

    /**
     * Canonical complete trace: for an exit, quantity/margin/average entry
     * come from the pre-event position, never the already-flat post state.
     * Capture snapshots using the existing per-candle StrategyEngine callback.
     */
    data class Transition(val event: StrategyEvent, val before: StrategyState, val after: StrategyState)

    fun exportTransitions(transitions: List<Transition>, symbol: String): String {
        require(symbol.isNotBlank()) { "Missing symbol" }
        val result = JSONArray()
        var lastTimestamp = -1L
        for (transition in transitions) {
            val event = transition.event
            val kind = kinds[event.kind] ?: error("Unknown event kind: ${event.kind}")
            val side = event.side ?: error("Missing event side")
            require(side == "LONG" || side == "SHORT")
            require(event.candleTime >= lastTimestamp) { "Unordered events" }
            lastTimestamp = event.candleTime
            val isExit = kind == "TP" || kind == "SOFT_SL" || kind == "EMERGENCY_SL"
            val position = if (isExit) transition.before.position else transition.after.position
            require(position != null && position.side == side) { "Missing position snapshot for $kind" }
            val values = listOf(event.price, position.qty, position.avgEntry,
                position.reservedMargin, transition.after.balance)
            require(values.all { it.isFinite() }) { "Non-finite trace value" }
            require(event.price > 0 && position.qty > 0 && position.avgEntry > 0 &&
                position.reservedMargin > 0) { "Invalid position accounting" }
            val item = JSONObject()
                .put("timestamp_ms", event.candleTime)
                .put("symbol", symbol)
                .put("kind", kind)
                .put("side", side)
                .put("price", event.price)
                .put("quantity", position.qty)
                .put("avg_entry", position.avgEntry)
                .put("margin", position.reservedMargin)
                .put("roe_pct", event.roePct ?: JSONObject.NULL)
                .put("balance", transition.after.balance)
                .put("net_pnl", event.netPnl ?: JSONObject.NULL)
                .put("fees", event.fees ?: JSONObject.NULL)
            result.put(item)
        }
        return result.toString()
    }

    fun export(snapshots: List<Pair<StrategyEvent, StrategyState>>, symbol: String): String {
        require(symbol.isNotBlank()) { "Missing symbol" }
        val result = JSONArray()
        var lastTimestamp = -1L
        for ((event, state) in snapshots) {
            val kind = kinds[event.kind] ?: error("Unknown event kind: ${event.kind}")
            val side = event.side ?: error("Missing event side")
            require(side == "LONG" || side == "SHORT")
            require(event.candleTime >= lastTimestamp) { "Unordered events" }
            lastTimestamp = event.candleTime
            val position = state.position
            // Exit snapshots need the pre-exit position. The single-state
            // exporter deliberately leaves those values null rather than guessing.
            val item = JSONObject()
                .put("timestamp_ms", event.candleTime)
                .put("symbol", symbol)
                .put("kind", kind)
                .put("side", side)
                .put("price", event.price)
                .put("quantity", position?.qty ?: JSONObject.NULL)
                .put("avg_entry", position?.avgEntry ?: JSONObject.NULL)
                .put("margin", position?.reservedMargin ?: JSONObject.NULL)
                .put("roe_pct", event.roePct ?: JSONObject.NULL)
                .put("balance", state.balance)
                .put("net_pnl", event.netPnl ?: JSONObject.NULL)
                .put("fees", event.fees ?: JSONObject.NULL)
            result.put(item)
        }
        return result.toString()
    }
}
