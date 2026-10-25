package com.kenznguyen.btclivealerts.analytics

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Offline, read-only Analytics panel. Call from navigation only after
 * the Android integration branch passes tests and the existing tabs are audited.
 */
@Composable
fun BacktestAnalyticsScreen(report: BacktestAnalyticsReport?, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    var importedReport by remember { mutableStateOf<BacktestAnalyticsReport?>(null) }
    var importError by remember { mutableStateOf<String?>(null) }
    val chooseReport = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            importedReport = null
            importError = null
            runCatching {
                val bytes = context.contentResolver.openInputStream(uri)?.use { stream ->
                    val output = java.io.ByteArrayOutputStream()
                    val buffer = ByteArray(8192)
                    while (true) {
                        val count = stream.read(buffer)
                        if (count < 0) break
                        require(output.size() + count <= 1_048_576) { "Tệp JSON vượt quá 1 MB" }
                        output.write(buffer, 0, count)
                    }
                    output.toByteArray()
                } ?: error("Không mở được tệp")
                BacktestAnalyticsReport.fromJson(bytes.toString(Charsets.UTF_8))
            }.onSuccess { importedReport = it }
                .onFailure { importError = "Không thể đọc báo cáo: " + (it.message ?: "JSON không hợp lệ") }
        }
    }
    val currentReport = importedReport ?: report
    Column(
        modifier = modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Backtest Analytics", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Chỉ phân tích dữ liệu offline · Không đặt lệnh thật",
            style = MaterialTheme.typography.bodySmall
        )
        Button(onClick = { chooseReport.launch(arrayOf("application/json", "text/plain", "application/octet-stream")) }) {
            Text("Nhập báo cáo JSON")
        }
        if (importError != null) Text(importError!!, color = MaterialTheme.colorScheme.error)
        if (currentReport == null) {
            Text("Chưa có báo cáo. Chọn tệp JSON backtest từ bộ nhớ Android.")
            return@Column
        }
        val summary = AnalyticsSummaryFormatter.format(currentReport)
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
