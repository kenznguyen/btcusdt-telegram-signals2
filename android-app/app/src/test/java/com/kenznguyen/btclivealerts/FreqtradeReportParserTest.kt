package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class FreqtradeReportParserTest {
    private fun sample(balance: Double = 102.0, net: Double = 2.0, mode: String = "futures"): String = """
        {"strategy":{"BtcM15H1FuturesRuntime":{
          "trading_mode":"$mode","total_trades":1,"starting_balance":100,
          "final_balance":$balance,"profit_total_abs":$net,
          "backtest_start":"2026-01-01 00:00:00","backtest_end":"2026-02-01 00:00:00",
          "backtest_days":31,"profit_factor":2.5,"max_drawdown_account":0.17,
          "trades":[{"is_short":true,"open_date":"2026-01-10","close_date":"2026-01-11",
              "exit_reason":"soft_sl","profit_abs":2.0,"leverage":13,
              "orders":[{"ft_is_entry":true},{"ft_is_entry":true},{"ft_is_entry":false}]}]
        }}}
    """.trimIndent()

    @Test fun importsRealFuturesTradesAndDca() {
        val report = FreqtradeReportParser.parse(sample())
        assertEquals(1, report.trades.size)
        assertEquals(1, report.dcaTrades)
        assertEquals("SHORT", report.trades.first().side)
        assertEquals(17.0, report.maxDrawdownPct!!, 0.001)
        assertFalse(report.androidParityVerified)
        assertFalse(report.fundingVerified)
    }

    @Test fun rejectsSpotAndCorruptedBalance() {
        assertThrows(IllegalArgumentException::class.java) { FreqtradeReportParser.parse(sample(mode="spot")) }
        assertThrows(IllegalArgumentException::class.java) { FreqtradeReportParser.parse(sample(balance=120.0)) }
    }

    @Test fun rejectsMismatchedTradeCount() {
        assertThrows(IllegalArgumentException::class.java) {
            FreqtradeReportParser.parse(sample().replace("\"total_trades\":1", "\"total_trades\":2"))
        }
    }
}
