package com.kenznguyen.btclivealerts.analytics

import org.json.JSONObject

/**
 * Read-only parser for offline Freqtrade reports.
 * No dependency on StrategyEngine, networking, trading or Android permissions.
 */
data class BacktestAnalyticsReport(
    val symbol: String,
    val periodDays: Int,
    val strategyCommit: String,
    val verified: Boolean,
    val netProfitUsdt: Double?,
    val winRatePct: Double?,
    val profitFactor: Double?,
    val maxDrawdownPct: Double?,
    val totalFeesUsdt: Double?
) {
    companion object {
        fun fromJson(raw: String): BacktestAnalyticsReport {
            val root = JSONObject(raw)
            require(root.getString("schema_version") == "1.0") { "Unsupported schema" }
            require(root.getString("engine") == "freqtrade") { "Unsupported engine" }
            require(root.getString("timeframe") == "15m") { "Unsupported timeframe" }
            val days = root.getInt("period_days")
            require(days in setOf(90, 180, 360)) { "Unsupported period" }
            val symbol = root.getString("symbol")
            require(symbol.isNotBlank()) { "Missing symbol" }
            val commit = root.getString("strategy_commit")
            require(commit.isNotBlank()) { "Missing provenance" }
            require(root.get("verified") is Boolean) { "Invalid verification flag" }
            require(root.getJSONArray("trades") != null) { "Missing trades" }
            val metrics = root.getJSONObject("metrics")
            fun metric(key: String): Double? {
                require(metrics.has(key)) { "Missing metric: $key" }
                if (metrics.isNull(key)) return null
                val value = metrics.get(key)
                require(value is Number) { "Non-numeric metric: $key" }
                return value.toDouble().also { require(it.isFinite()) { "Non-finite metric: $key" } }
            }
            return BacktestAnalyticsReport(
                symbol = symbol,
                periodDays = days,
                strategyCommit = commit,
                // Certification requires separate parity review; never trust a self-declared true.
                verified = false,
                netProfitUsdt = metric("net_profit_usdt"),
                winRatePct = metric("win_rate_pct"),
                profitFactor = metric("profit_factor"),
                maxDrawdownPct = metric("max_drawdown_pct"),
                totalFeesUsdt = metric("total_fees_usdt")
            )
        }
    }
}
