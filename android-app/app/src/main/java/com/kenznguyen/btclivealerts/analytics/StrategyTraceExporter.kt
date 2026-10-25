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
