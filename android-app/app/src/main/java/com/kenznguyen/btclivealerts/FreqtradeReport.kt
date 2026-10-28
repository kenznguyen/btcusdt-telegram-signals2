package com.kenznguyen.btclivealerts

import org.json.JSONObject

/** Actual Freqtrade runtime export, never a locally simulated Android report. */
data class FreqtradeTradeRow(
    val side: String, val opened: String, val closed: String,
    val reason: String, val profitUsdt: Double, val entryCount: Int
)

data class FreqtradeReport(
    val strategy: String, val source: String, val period: String,
    val days: Int, val startBalance: Double, val endBalance: Double,
    val netProfit: Double, val winRate: Double, val profitFactor: Double?,
    val maxDrawdownPct: Double?, val leverage: Double?,
    val trades: List<FreqtradeTradeRow>,
    val fundingVerified: Boolean, val androidParityVerified: Boolean
) {
    val dcaTrades: Int get() = trades.count { it.entryCount > 1 }
    val liquidationTrades: Int get() = trades.count { it.reason == "liquidation" }
}

object FreqtradeReportParser {
    /** Refuses unverifiable/incorrect engine or non-futures backtest exports. */
    fun parse(rawJson: String): FreqtradeReport {
        val root = JSONObject(rawJson)
        val strategies = root.getJSONObject("strategy")
        require(strategies.length() == 1) { "Cần đúng một strategy Freqtrade" }
        val strategy = strategies.keys().next()
        val data = strategies.getJSONObject(strategy)
        require(data.optString("trading_mode") == "futures") { "Chỉ nhận Futures backtest" }
        val expected = data.optInt("total_trades", -1)
        val tradeArray = data.getJSONArray("trades")
        require(expected >= 0 && tradeArray.length() == expected) { "Thiếu hoặc lệch danh sách giao dịch" }
        val start = data.getDouble("starting_balance")
        val end = data.getDouble("final_balance")
        val net = data.getDouble("profit_total_abs")
        require(start > 0 && start.isFinite() && end.isFinite() && net.isFinite()) { "Số dư không hợp lệ" }
        require(kotlin.math.abs((end - start) - net) < maxOf(0.03, kotlin.math.abs(net) * 1e-5)) {
            "Số dư không khớp lợi nhuận Freqtrade"
        }
        val trades = (0 until tradeArray.length()).map { idx ->
            val row = tradeArray.getJSONObject(idx)
            val orders = row.optJSONArray("orders")
            val entries = if (orders == null) 1 else (0 until orders.length()).count {
                orders.getJSONObject(it).optBoolean("ft_is_entry", false)
            }
            FreqtradeTradeRow(
                side = if (row.getBoolean("is_short")) "SHORT" else "LONG",
                opened = row.optString("open_date"), closed = row.optString("close_date"),
                reason = row.optString("exit_reason", "unknown"),
                profitUsdt = row.getDouble("profit_abs"), entryCount = entries
            )
        }
        val wins = trades.count { it.profitUsdt > 0 }
        fun optionalNumber(name: String): Double? =
            if (data.has(name) && !data.isNull(name)) data.optDouble(name).takeIf { it.isFinite() } else null
        return FreqtradeReport(
            strategy = strategy, source = "Freqtrade runtime · OKX Futures",
            period = data.optString("backtest_start") + " → " + data.optString("backtest_end"),
            days = data.optInt("backtest_days"), startBalance = start, endBalance = end,
            netProfit = net, winRate = if (trades.isEmpty()) 0.0 else wins * 100.0 / trades.size,
            profitFactor = optionalNumber("profit_factor"),
            maxDrawdownPct = optionalNumber("max_drawdown_account")?.times(100.0),
            leverage = trades.firstOrNull()?.let { tradeArray.getJSONObject(0).optDouble("leverage").takeIf(Double::isFinite) },
            trades = trades,
            fundingVerified = false, androidParityVerified = false
        )
    }
}
