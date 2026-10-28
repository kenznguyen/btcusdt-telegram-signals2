package com.kenznguyen.btclivealerts

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.util.zip.ZipInputStream

private const val MAX_RESULT_JSON_BYTES = 32 * 1024 * 1024
private val FreqPanel = Color(0xFF151D29)
private val FreqMuted = Color(0xFF91A0B5)
private val FreqPositive = Color(0xFF20C997)
private val FreqNegative = Color(0xFFFF647C)

object FreqtradeReportImporter {
    fun import(context: Context, uri: Uri): FreqtradeReport {
        val filename = context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val index = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            if (index >= 0 && cursor.moveToFirst()) cursor.getString(index) else null
        } ?: ""
        val stream = context.contentResolver.openInputStream(uri)
            ?: error("Không thể đọc tệp đã chọn")
        return stream.use { input ->
            if (filename.endsWith(".zip", ignoreCase = true)) {
                ZipInputStream(input).use { archive ->
                    var selected: String? = null
                    while (true) {
                        val entry = archive.nextEntry ?: break
                        if (entry.isDirectory) continue
                        val base = entry.name.substringAfterLast("/")
                        if (base.endsWith(".json", ignoreCase = true) &&
                            !base.endsWith("_config.json", ignoreCase = true) &&
                            !base.endsWith(".meta.json", ignoreCase = true) &&
                            base.startsWith("backtest-result-", ignoreCase = true)) {
                            require(selected == null) { "ZIP chứa nhiều báo cáo backtest, hãy chọn một ZIP kết quả" }
                            selected = readBounded(archive)
                        }
                        archive.closeEntry()
                    }
                    FreqtradeReportParser.parse(selected
                        ?: error("Không tìm thấy backtest-result-*.json trong ZIP"))
                }
            } else {
                require(filename.endsWith(".json", ignoreCase = true)) { "Chỉ hỗ trợ ZIP hoặc JSON Freqtrade" }
                FreqtradeReportParser.parse(readBounded(input))
            }
        }
    }

    private fun readBounded(input: java.io.InputStream): String {
        val output = ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        while (true) {
            val count = input.read(buffer)
            if (count < 0) break
            require(output.size() + count <= MAX_RESULT_JSON_BYTES) {
                "Báo cáo quá lớn (giới hạn 32 MB)"
            }
            output.write(buffer, 0, count)
        }
        return output.toString(Charsets.UTF_8.name())
    }
}

@Composable
fun FreqtradeBacktestPanel(context: Context, market: MarketEngine, engine: StrategyEngine) {
    val scope = rememberCoroutineScope()
    var report by remember { mutableStateOf<FreqtradeReport?>(null) }
    var filename by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showKotlinComparison by remember { mutableStateOf(false) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            scope.launch {
                loading = true
                error = null
                report = null
                try {
                    val imported = withContext(Dispatchers.IO) {
                        FreqtradeReportImporter.import(context, uri)
                    }
                    report = imported
                    filename = uri.lastPathSegment
                } catch (exc: Exception) {
                    error = exc.message ?: exc.javaClass.simpleName
                } finally {
                    loading = false
                }
            }
        }
    }

    Column(
        Modifier.fillMaxWidth().background(FreqPanel, RoundedCornerShape(14.dp)).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text("FREQTRADE · BACKTEST CHÍNH", style = MaterialTheme.typography.titleMedium, color = Color.White)
        Text("Chọn ZIP kết quả backtest Freqtrade từ Codemagic hoặc JSON báo cáo. Ứng dụng không tự chạy Python và không đặt lệnh.",
            color = FreqMuted, style = MaterialTheme.typography.bodySmall)
        Button(
            enabled = !loading,
            onClick = { launcher.launch(arrayOf("application/zip", "application/x-zip-compressed", "application/json", "application/octet-stream", "*/*")) }
        ) {
            Text(if (loading) "ĐANG ĐỌC BÁO CÁO…" else "MỞ BÁO CÁO FREQTRADE ZIP / JSON")
        }
        if (error != null) Text("Không nhập được báo cáo: $error", color = FreqNegative)
        report?.let { r ->
            Text("Nguồn: ${r.source}", color = FreqMuted)
            Text("Strategy: ${r.strategy}", color = Color.White)
            Text("Kỳ: ${r.period} (${r.days} ngày)", color = FreqMuted, style = MaterialTheme.typography.bodySmall)
            Text("PnL ròng: ${"%+.2f".format(r.netProfit)} USDT",
                color = if (r.netProfit >= 0) FreqPositive else FreqNegative,
                style = MaterialTheme.typography.titleLarge)
            Text("Vốn đầu: ${"%.2f".format(r.startBalance)} · Số dư cuối: ${"%.2f".format(r.endBalance)} USDT",
                color = Color.White)
            Text("Giao dịch: ${r.trades.size} · Win Rate: ${"%.2f".format(r.winRate)}% · DCA: ${r.dcaTrades}",
                color = Color.White)
            Text("Profit Factor: ${r.profitFactor?.let { "%.2f".format(it) } ?: "N/A"} · Max DD báo cáo: ${r.maxDrawdownPct?.let { "%.2f%%".format(it) } ?: "N/A"}",
                color = Color.White)
            val longCount = r.trades.count { it.side == "LONG" }
            val shortCount = r.trades.size - longCount
            Text("LONG: $longCount · SHORT: $shortCount · Liquidation: ${r.liquidationTrades}",
                color = if (r.liquidationTrades > 0) FreqNegative else Color.White)
            Text("Funding toàn kỳ: chưa xác minh · Kotlin–Freqtrade parity: chưa xác minh. Max DD phía trên là chỉ số tổng hợp Freqtrade, không phải equity 5m.",
                color = FreqMuted, style = MaterialTheme.typography.bodySmall)
            Text("GIAO DỊCH ĐÃ ĐÓNG", color = Color.White, style = MaterialTheme.typography.titleSmall)
            r.trades.takeLast(30).reversed().forEach { t ->
                Column(Modifier.fillMaxWidth().background(Color(0xFF0B1018), RoundedCornerShape(8.dp)).padding(10.dp)) {
                    Text("${t.side} · ${t.reason} · ${"%+.3f".format(t.profitUsdt)} USDT",
                        color = if (t.profitUsdt >= 0) FreqPositive else FreqNegative)
                    Text("${t.opened} → ${t.closed} · Entries: ${t.entryCount}",
                        color = FreqMuted, style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        HorizontalDivider()
        TextButton(onClick = { showKotlinComparison = !showKotlinComparison }) {
            Text(if (showKotlinComparison) "ẨN BACKTEST KOTLIN ĐỐI CHIẾU" else "BACKTEST KOTLIN · CHỈ ĐỐI CHIẾU")
        }
        if (showKotlinComparison) {
            Text("Bộ mô phỏng Android dùng dữ liệu Binance và quy tắc fill riêng; không đồng nghĩa Freqtrade parity.",
                color = FreqMuted, style = MaterialTheme.typography.bodySmall)
            BacktestPanel(market, engine)
        }
    }
}
