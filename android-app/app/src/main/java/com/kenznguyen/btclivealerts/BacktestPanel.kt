package com.kenznguyen.btclivealerts

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun BacktestPanel(market: MarketEngine, engine: StrategyEngine) {
    val scope = rememberCoroutineScope()
    var loading by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Chưa chạy") }
    var report by remember { mutableStateOf<List<String>>(emptyList()) }
    var trades by remember { mutableStateOf<List<StrategyEvent>>(emptyList()) }
    Column(Modifier.fillMaxWidth().background(Color(0xFF151D29), RoundedCornerShape(14.dp)).padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("BACKTEST · BTCUSDT M15 / H1", color = Color.White, style = MaterialTheme.typography.titleMedium)
        Text("Mô phỏng cục bộ · không đặt lệnh thật · phí và trượt giá là ước tính", color = Color(0xFF91A0B5), style = MaterialTheme.typography.bodySmall)
        Button(enabled = !loading, onClick = {
            scope.launch {
                loading = true
                status = "Đang tải dữ liệu…"
                try {
                    val m15 = market.fetchCandles("15m", 1500).filter { it.closed }
                    val h1 = market.fetchCandles("1h", 1500).filter { it.closed }
                    require(m15.size > 60 && h1.size > 30) { "Không đủ dữ liệu nến." }
                    var state = StrategyState(balance = 100.0)
                    val closedTrades = mutableListOf<StrategyEvent>()
                    for (i in 1 until m15.size) {
                        val result = engine.processClosedCandles(m15.take(i + 1), h1, state)
                        state = result.first
                        result.second.filter { it.kind == "TAKE PROFIT" || it.kind == "SOFT SL" || it.kind == "EMERGENCY SL" }.forEach { closedTrades.add(it) }
                    }
                    val pnls = closedTrades.map { e ->
                        val prefix = "PnL ròng ước tính "
                        val start = e.note.indexOf(prefix)
                        if (start < 0) 0.0 else e.note.substring(start + prefix.length).substringBefore(" ").replace(",", ".").toDoubleOrNull() ?: 0.0
                    }
                    val wins = pnls.count { it > 0.0 }
                    val losses = pnls.count { it < 0.0 }
                    val grossWin = pnls.filter { it > 0.0 }.sum()
                    val grossLoss = -pnls.filter { it < 0.0 }.sum()
                    val pf = if (grossLoss == 0.0) null else grossWin / grossLoss
                    var equity = 100.0
                    var peak = equity
                    var maxDd = 0.0
                    pnls.forEach { pnl ->
                        equity += pnl
                        peak = maxOf(peak, equity)
                        if (peak > 0.0) maxDd = maxOf(maxDd, (peak - equity) / peak * 100.0)
                    }
                    report = listOf(
                        "Net PnL: %+.2f USDT".format(state.balance - 100.0),
                        "Balance cuối: %.2f USDT".format(state.balance),
                        "Lệnh đã đóng: " + closedTrades.size,
                        "Win rate: %.1f%%".format(if (closedTrades.isEmpty()) 0.0 else wins * 100.0 / closedTrades.size),
                        "Profit Factor: " + (pf?.let { "%.2f".format(it) } ?: "∞ (chưa có lệnh lỗ)"),
                        "Max Drawdown: %.2f%%".format(maxDd),
                        "Nến M15: " + m15.size,
                        "Dữ liệu: " + SimpleDateFormat("dd/MM HH:mm", Locale.getDefault()).format(Date(m15.first().openTime)) + " – " + SimpleDateFormat("dd/MM HH:mm", Locale.getDefault()).format(Date(m15.last().openTime))
                    )
                    trades = closedTrades.takeLast(15).reversed()
                    status = "Hoàn tất"
                } catch (e: Exception) {
                    status = "Lỗi: " + (e.message ?: "không xác định")
                } finally {
                    loading = false
                }
            }
        }, modifier = Modifier.fillMaxWidth()) { Text(if (loading) "ĐANG CHẠY…" else "CHẠY BACKTEST") }
        Text(status, color = if (status == "Hoàn tất") Color(0xFF20C997) else Color(0xFF91A0B5))
        report.forEach { line -> Text(line, color = Color.White) }
        if (trades.isNotEmpty()) {
            Text("LỊCH SỬ LỆNH ĐÓNG GẦN NHẤT", color = Color.White, style = MaterialTheme.typography.titleSmall)
            trades.forEach { e ->
                Column(Modifier.fillMaxWidth().background(Color(0xFF0B1018), RoundedCornerShape(8.dp)).padding(10.dp)) {
                    Text(e.kind + " · " + (e.side ?: "—") + " · " + "%.2f".format(e.price), color = if (e.kind.contains("SL")) Color(0xFFFF647C) else Color(0xFF20C997))
                    Text(SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date(e.candleTime)), color = Color(0xFF91A0B5), style = MaterialTheme.typography.bodySmall)
                    Text(e.note, color = Color(0xFF91A0B5), style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}
