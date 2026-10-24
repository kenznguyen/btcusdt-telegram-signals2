package com.kenznguyen.btclivealerts.analytics

import java.util.Locale

/**
 * Read-only display model for an offline report.
 * A report cannot assert its own certification.
 */
data class AnalyticsSummary(
    val title: String,
    val verificationLabel: String,
    val netProfit: String,
    val winRate: String,
    val profitFactor: String,
    val maxDrawdown: String,
    val fees: String
)

object AnalyticsSummaryFormatter {
    fun format(report: BacktestAnalyticsReport): AnalyticsSummary {
        fun number(value: Double?, suffix: String = ""): String =
            value?.let { String.format(Locale.US, "%.2f%s", it, suffix) } ?: "N/A"

        return AnalyticsSummary(
            title = "${report.symbol} · ${report.periodDays} ngày · M15",
            verificationLabel = "Chưa xác minh tương đương StrategyEngine",
            netProfit = number(report.netProfitUsdt, " USDT"),
            winRate = number(report.winRatePct, "%"),
            profitFactor = number(report.profitFactor),
            maxDrawdown = number(report.maxDrawdownPct, "%"),
            fees = number(report.totalFeesUsdt, " USDT")
        )
    }
}
