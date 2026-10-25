package com.kenznguyen.btclivealerts.analytics

import org.junit.Assert.*
import org.junit.Test

class BacktestAnalyticsReportTest {
    private fun json(verified: Boolean = false) = """
        {
          "schema_version": "1.0",
          "engine": "freqtrade",
          "symbol": "BTC/USDT:USDT",
          "timeframe": "15m",
          "period_days": 90,
          "strategy_commit": "abcdef123456",
          "verified": $verified,
          "metrics": {
            "net_profit_usdt": 12.5,
            "win_rate_pct": 55.0,
            "profit_factor": 1.2,
            "max_drawdown_pct": 8.0,
            "total_fees_usdt": null
          },
          "trades": []
        }
    """.trimIndent()

    @Test fun parsesKpisAndPreservesUnknownFees() {
        val report = BacktestAnalyticsReport.fromJson(json())
        assertEquals(12.5, report.netProfitUsdt!!, 1e-9)
        assertEquals(55.0, report.winRatePct!!, 1e-9)
        assertNull(report.totalFeesUsdt)
        assertFalse(report.verified)
    }

    @Test fun neverTrustsSelfDeclaredVerification() {
        assertFalse(BacktestAnalyticsReport.fromJson(json(verified = true)).verified)
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsUnsupportedSchema() {
        BacktestAnalyticsReport.fromJson(json().replace("\"1.0\"", "\"2.0\""))
    }

    @Test fun formatsUnavailableFees() {
        val formatted = AnalyticsSummaryFormatter.format(BacktestAnalyticsReport.fromJson(json()))
        assertEquals("N/A", formatted.fees)
        assertTrue(formatted.verificationLabel.contains("Chưa xác minh"))
    }
}
