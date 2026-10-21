package com.kenznguyen.btclivealerts

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.max

private data class SideStats(val trades: Int, val wins: Int, val pnl: Double, val fees: Double) {
    val winRate: Double get() = if (trades == 0) 0.0 else wins * 100.0 / trades
}
private data class EquityPoint(val time: Long, val equity: Double, val drawdownPct: Double)
private data class BacktestReport(
    val startBalance: Double, val endBalance: Double, val netPnl: Double,
    val fees: Double, val closed: List<StrategyEvent>, val events: List<StrategyEvent>,
    val long: SideStats, val short: SideStats, val equity: List<EquityPoint>,
    val maxDdPct: Double, val maxDdAbs: Double, val openSide: String?,
    val openQty: Double, val openEntry: Double, val openUnrealized: Double,
    val candles: Int, val from: Long, val to: Long
)

@Composable
fun BacktestPanel(market: MarketEngine, engine: StrategyEngine) {
    val scope = rememberCoroutineScope()
    var days by remember { mutableIntStateOf(30) }
    var loading by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Chưa chạy backtest") }
    var report by remember { mutableStateOf<BacktestReport?>(null) }

    Column(Modifier.fillMaxWidth().background(Color(0xFF151D29), RoundedCornerShape(14.dp)).padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("BACKTEST · BTCUSDT M15 / H1", color = Color.White, style = MaterialTheme.typography.titleMedium)
        Text("Dữ liệu Binance Futures · mô phỏng cục bộ · không đặt lệnh thật", color = Muted, style = MaterialTheme.typography.bodySmall)
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            listOf(7, 30, 90, 180, 360).forEach { d ->
                FilterChip(selected = days == d, onClick = { days = d }, enabled = !loading, label = { Text("${d}D") })
            }
        }
        Button(enabled = !loading, onClick = {
            scope.launch {
                loading = true
                status = "Đang tải nến phân trang và tính chỉ báo một lần…"
                try {
                    val r = withContext(Dispatchers.Default) {
                        val m15 = market.fetchHistory("15m", days)
                        val h1 = market.fetchHistory("1h", days)
                        require(m15.size > 60 && h1.size > 30) { "Không đủ dữ liệu lịch sử." }
                        // Critical optimization: calculate indicator series once and process the entire candle set once.
                        // Never replay each growing candle prefix (that made the old implementation O(n²)).
                        val initial = StrategyState(balance = 200.0)
                        var peak = initial.balance
                        var maxDd = 0.0
                        var maxAbs = 0.0
                        val curve = mutableListOf(EquityPoint(m15.first().openTime, initial.balance, 0.0))
                        // Mark equity on every closed M15 candle, including unrealized PnL and
                        // estimated entry + exit fees while a position remains open.
                        val (trackedState, trackedEvents) = engine.processClosedCandles(m15, h1, initial) { candle, state ->
                            val mark = engine.markToMarketEquity(state, candle.close)
                            peak = max(peak, mark)
                            val position = state.position
                            // Estimate adverse mark-to-market at the candle's low (LONG) or high (SHORT)
                            // so intrabar losses are not hidden by a recovery before candle close.
                            val adversePrice = when (position?.side) {
                                "LONG" -> candle.low
                                "SHORT" -> candle.high
                                else -> candle.close
                            }
                            val worstMark = if (position == null) state.balance
                                else engine.markToMarketEquity(state, adversePrice)
                            val ddAbs = max(0.0, peak - minOf(mark, worstMark))
                            val ddPct = if (peak > 0.0) ddAbs / peak * 100.0 else 0.0
                            maxDd = max(maxDd, ddPct)
                            maxAbs = max(maxAbs, ddAbs)
                            curve += EquityPoint(candle.openTime, mark, ddPct)
                        }
                        // Keep report state/events from the same engine pass used for the equity curve.
                        val finalState = trackedState
                        val emitted = trackedEvents
                        val closed = emitted.filter { it.kind == "TAKE PROFIT" || it.kind == "SOFT SL" || it.kind == "EMERGENCY SL" }
                        fun pnl(e: StrategyEvent): Double = noteNumber(e.note, "PnL ròng ước tính ")
                        fun fee(e: StrategyEvent): Double = noteNumber(e.note, "phí ")
                        fun stats(side: String): SideStats {
                            val items = closed.filter { it.side == side }
                            return SideStats(items.size, items.count { pnl(it) > 0 }, items.sumOf { pnl(it) }, items.sumOf { fee(it) })
                        }
                        val p = finalState.position
                        val last = m15.filter { it.closed }.maxByOrNull { it.openTime }?.close
                            ?: error("Không có nến M15 đã đóng để định giá vị thế cuối kỳ.")
                        val unrealized = if (p == null) 0.0 else engine.markToMarketEquity(finalState, last) - finalState.balance
                        BacktestReport(
                            initial.balance, finalState.balance, finalState.balance - initial.balance,
                            emitted.filter { it.kind == "TAKE PROFIT" || it.kind == "SOFT SL" || it.kind == "EMERGENCY SL" }
                                .sumOf { fee(it) },
                            closed, emitted, stats("LONG"), stats("SHORT"), curve, maxDd, maxAbs,
                            p?.side, p?.qty ?: 0.0, p?.avgEntry ?: 0.0, unrealized,
                            m15.size, m15.first().openTime, m15.last().openTime
                        )
                    }
                    report = r
                    status = "Hoàn tất · ${r.candles} nến M15"
                } catch (e: Exception) {
                    status = "Backtest lỗi: " + (e.message ?: e.javaClass.simpleName)
                } finally {
                    loading = false
                }
            }
        }, modifier = Modifier.fillMaxWidth()) { Text(if (loading) "ĐANG CHẠY…" else "CHẠY BACKTEST ${days} NGÀY") }
        Text(status, color = if (status.startsWith("Hoàn tất")) Green else Muted, style = MaterialTheme.typography.bodySmall)
        report?.let { r ->
            Metric("Net PnL đã đóng", "%+.2f USDT".format(r.netPnl), r.netPnl >= 0)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Metric("Số dư sau lệnh đóng", "%.2f".format(r.endBalance), r.endBalance >= r.startBalance, Modifier.weight(1f))
                Metric("Phí lệnh đã đóng", "%.4f USDT".format(r.fees), false, Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Metric("Max DD", "%.2f%%".format(r.maxDdPct), r.maxDdPct < 20, Modifier.weight(1f))
                Metric("Max DD tuyệt đối", "%.2f USDT".format(r.maxDdAbs), r.maxDdAbs < 20, Modifier.weight(1f))
            }
            Text("EQUITY CURVE", color = Color.White, style = MaterialTheme.typography.titleSmall)
            EquityChart(r.equity.map { it.equity }, Color(0xFF20C997), Modifier.fillMaxWidth().height(110.dp))
            Text("DRAWDOWN (%)", color = Color.White, style = MaterialTheme.typography.titleSmall)
            EquityChart(r.equity.map { -it.drawdownPct }, Color(0xFFFF647C), Modifier.fillMaxWidth().height(90.dp))
            Text("LONG · ${r.long.trades} lệnh · Win ${"%.1f".format(r.long.winRate)}% · PnL ${"%+.2f".format(r.long.pnl)} · phí ${"%.4f".format(r.long.fees)}", color = Color.White)
            Text("SHORT · ${r.short.trades} lệnh · Win ${"%.1f".format(r.short.winRate)}% · PnL ${"%+.2f".format(r.short.pnl)} · phí ${"%.4f".format(r.short.fees)}", color = Color.White)
            val p = r.openSide
            Text("VỊ THẾ CÒN MỞ", color = Color.White, style = MaterialTheme.typography.titleSmall)
            if (p == null) Text("Không có vị thế mở tại cuối kỳ.", color = Muted)
            else {
                Text("$p · Qty ${"%.6f".format(r.openQty)} BTC · Giá vốn ${"%.2f".format(r.openEntry)}", color = Color.White)
                Text("PnL chưa thực hiện ước tính sau phí thoát: ${"%+.2f".format(r.openUnrealized)} USDT", color = if (r.openUnrealized >= 0) Green else Red)
            }
            Text("Số lệnh đóng: ${r.closed.size} · Số sự kiện: ${r.events.size}", color = Muted)
            Text("Dữ liệu: ${date(r.from)} – ${date(r.to)}", color = Muted, style = MaterialTheme.typography.bodySmall)
            Text("LỊCH SỬ LỆNH ĐÓNG GẦN NHẤT", color = Color.White, style = MaterialTheme.typography.titleSmall)
            r.closed.takeLast(15).reversed().forEach { e ->
                Column(Modifier.fillMaxWidth().background(Color(0xFF0B1018), RoundedCornerShape(8.dp)).padding(10.dp)) {
                    Text("${e.kind} · ${e.side ?: "—"} · ${"%.2f".format(e.price)}", color = if (e.kind.contains("SL")) Red else Green)
                    Text(date(e.candleTime), color = Muted, style = MaterialTheme.typography.bodySmall)
                    Text(e.note, color = Muted, style = MaterialTheme.typography.bodySmall)
                }
            }
            Text("Equity/Max DD tính theo từng nến M15, gồm PnL thả nổi và phí vào/thoát ước tính cho vị thế mở. Net PnL đã đóng chỉ gồm lệnh đã tất toán; phí và trượt giá là mô phỏng.", color = Color(0xFFFFC857), style = MaterialTheme.typography.bodySmall)
        }
    }
}

private val Muted = Color(0xFF91A0B5)
private val Green = Color(0xFF20C997)
private val Red = Color(0xFFFF647C)

private fun noteNumber(note: String, marker: String): Double {
    val start = note.indexOf(marker)
    if (start < 0) return 0.0
    val raw = note.substring(start + marker.length).substringBefore(" ").replace(",", ".")
    return raw.toDoubleOrNull() ?: 0.0
}
private fun date(ms: Long) = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date(ms))

@Composable
private fun Metric(label: String, value: String, positive: Boolean, modifier: Modifier = Modifier) {
    Column(modifier.background(Color(0xFF0B1018), RoundedCornerShape(10.dp)).padding(10.dp)) {
        Text(label, color = Muted, style = MaterialTheme.typography.bodySmall)
        Text(value, color = if (positive) Green else Red, style = MaterialTheme.typography.titleMedium)
    }
}

@Composable
private fun EquityChart(values: List<Double>, lineColor: Color, modifier: Modifier = Modifier) {
    Canvas(modifier.background(Color(0xFF0B1018), RoundedCornerShape(8.dp))) {
        if (values.size < 2) return@Canvas
        val low = values.minOrNull() ?: return@Canvas
        val high = values.maxOrNull() ?: return@Canvas
        val range = (high - low).takeIf { it > 0.0 } ?: 1.0
        for (i in 1..3) {
            val y = size.height * i / 4f
            drawLine(Color(0xFF263243), Offset(0f, y), Offset(size.width, y), 1f)
        }
        val points = values.mapIndexed { i, value ->
            Offset(size.width * i / (values.size - 1).toFloat(),
                size.height - ((value - low) / range).toFloat() * size.height)
        }
        points.zipWithNext().forEach { (a, b) -> drawLine(lineColor, a, b, 2f) }
    }
}
