package com.kenznguyen.btclivealerts.analytics

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Offline, read-only Analytics panel. Call from navigation only after
 * the Android integration branch passes tests and the existing tabs are audited.
 */
@Composable
fun BacktestAnalyticsScreen(report: BacktestAnalyticsReport?, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Backtest Analytics", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Chỉ phân tích dữ liệu offline · Không đặt lệnh thật",
            style = MaterialTheme.typography.bodySmall
        )
        if (report == null) {
            Text("Chưa có báo cáo. Cần nhập JSON backtest đã kiểm tra.")
            return@Column
        }
        val summary = AnalyticsSummaryFormatter.format(report)
        Text(summary.title, style = MaterialTheme.typography.titleMedium)
        Text(summary.verificationLabel, color = MaterialTheme.colorScheme.error)
        KpiRow("Net Profit", summary.netProfit, "Win Rate", summary.winRate)
        KpiRow("Profit Factor", summary.profitFactor, "Max Drawdown", summary.maxDrawdown)
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text("Total Fees", style = MaterialTheme.typography.labelMedium)
                Text(summary.fees, style = MaterialTheme.typography.titleMedium)
            }
        }
        Text(
            "Equity, Drawdown và lịch sử giao dịch chưa có dữ liệu được xác minh.",
            style = MaterialTheme.typography.bodySmall
        )
    }
}

@Composable
private fun KpiRow(labelA: String, valueA: String, labelB: String, valueB: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Card(Modifier.weight(1f)) {
            Column(Modifier.padding(12.dp)) {
                Text(labelA, style = MaterialTheme.typography.labelMedium)
                Text(valueA, style = MaterialTheme.typography.titleMedium)
            }
        }
        Card(Modifier.weight(1f)) {
            Column(Modifier.padding(12.dp)) {
                Text(labelB, style = MaterialTheme.typography.labelMedium)
                Text(valueB, style = MaterialTheme.typography.titleMedium)
            }
        }
    }
}
