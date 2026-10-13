package com.kenznguyen.btclivealerts

import android.app.NotificationManager
import android.content.Context
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val NBg = Color(0xFF0B1018)
private val NPanel = Color(0xFF151D29)
private val NGreen = Color(0xFF20C997)
private val NRed = Color(0xFFFF647C)
private val NMuted = Color(0xFF91A0B5)

@Composable
fun CompleteDashboard(context: Context) {
    val market = remember { MarketEngine() }
    val engine = remember { StrategyEngine() }
    val prefs = remember { context.getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE) }
    var timeframe by remember { mutableStateOf("15m") }
    var chart by remember { mutableStateOf<List<Candle>>(emptyList()) }
    var price by remember { mutableStateOf<Double?>(null) }
    var status by remember { mutableStateOf("Đang kết nối Binance Futures…") }
    var alerts by remember { mutableStateOf(prefs.getBoolean("alerts_enabled", true)) }
    var state by remember { mutableStateOf(StrategyState.fromJson(prefs.getString("state_json", null))) }
    var m15Ind by remember { mutableStateOf(IndicatorPoint()) }
    var h1Ind by remember { mutableStateOf(IndicatorPoint()) }

    LaunchedEffect(timeframe) {
        while (true) {
            try {
                val m15 = market.fetchCandles("15m", 500)
                val h1 = market.fetchCandles("1h", 500)
                val closed15 = m15.filter { it.closed }
                val closed1h = h1.filter { it.closed }
                chart = if (timeframe == "15m") m15 else h1
                price = market.fetchMarkPrice()
                m15Ind = engine.indicatorSeries(closed15).lastOrNull() ?: IndicatorPoint()
                h1Ind = engine.indicatorSeries(closed1h).lastOrNull() ?: IndicatorPoint()

                // The foreground service is the single writer for position state; UI only reads it.
                state = StrategyState.fromJson(prefs.getString("state_json", null))
                status = "Đang kết nối · cập nhật " + SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
            } catch (e: Exception) {
                status = "Mất kết nối: " + (e.message ?: "lỗi mạng")
            }
            delay(15_000)
        }
    }

    val shown = if (timeframe == "15m") m15Ind else h1Ind
    Surface(Modifier.fillMaxSize(), color = NBg) {
        LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item {
                Text("BTCUSDT.P", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = Color.White)
                Text("USDⓈ-M Perpetual · Chỉ xem · Không đặt lệnh", color = NMuted)
            }
            item {
                Column(Modifier.fillMaxWidth().background(NPanel, RoundedCornerShape(16.dp)).padding(16.dp)) {
                    Text("MARK PRICE", color = NMuted)
                    Text(price?.let { "$" + "%,.2f".format(it) } ?: "—", style = MaterialTheme.typography.headlineLarge, color = Color.White)
                    Text(status, color = if (status.startsWith("Đang kết nối")) NGreen else NRed)
                }
            }
            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    listOf("15m", "1h").forEach { tf ->
                        FilterChip(selected = timeframe == tf, onClick = { timeframe = tf }, label = { Text(tf.uppercase()) })
                        Spacer(Modifier.width(8.dp))
                    }
                    Spacer(Modifier.weight(1f))
                    Text("LIVE", color = NGreen)
                }
            }
            item {
                Column(Modifier.fillMaxWidth().background(NPanel, RoundedCornerShape(14.dp)).padding(12.dp)) {
                    Text("Candlestick · " + timeframe.uppercase(), color = Color.White, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.height(8.dp))
                    LiveCandles(chart, Modifier.fillMaxWidth().height(220.dp))
                    Text("Binance Futures · tải lại 15 giây", color = NMuted)
                }
            }
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    StatCard("RSI (14)", shown.rsi, Modifier.weight(1f))
                    StatCard("ADX (14)", shown.adx, Modifier.weight(1f))
                }
            }
            item {
                Column(Modifier.fillMaxWidth().background(NPanel, RoundedCornerShape(14.dp)).padding(14.dp)) {
                    Text("CHIẾN LƯỢC M15 / H1", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("H1 ADX " + fmt(h1Ind.adx) + " · +DI " + fmt(h1Ind.plusDi) + " · -DI " + fmt(h1Ind.minusDi), color = NMuted)
                    Text("Vị thế mô phỏng: " + (state.position?.side ?: "FLAT"), color = Color.White)
                    Text("Số dư mô phỏng: " + "%.2f".format(state.balance) + " USDT", color = Color.White)
                    state.position?.let { p ->
                        Text("Giá vốn " + "%.2f".format(p.avgEntry) + " · Qty " + "%.6f".format(p.qty) + " BTC", color = NMuted)
                        Text("Margin " + "%.2f".format(p.reservedMargin) + " · DCA " + if (p.dcaUsed) "đã dùng" else "chưa dùng", color = NMuted)
                        val roe = engine.roeFor(p.side, p.avgEntry, price ?: p.avgEntry)
                        Text("ROE tham chiếu " + "%.2f".format(roe) + "%", color = if (roe >= 0) NGreen else NRed)
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Thông báo", color = NMuted, modifier = Modifier.weight(1f))
                        Switch(checked = alerts, onCheckedChange = {
                            alerts = it
                            prefs.edit().putBoolean("alerts_enabled", it).apply()
                        })
                    }
                    Text("Cảnh báo chỉ mô phỏng. Theo dõi khi chạy nền chưa được bảo đảm; Android có thể tạm dừng ứng dụng.", color = Color(0xFFFFC857), style = MaterialTheme.typography.bodySmall)
                }
            }
            item { Text("LỊCH SỬ SỰ KIỆN", color = Color.White, fontWeight = FontWeight.Bold) }
            items(state.recentEvents) { event ->
                Column(Modifier.fillMaxWidth().background(NPanel, RoundedCornerShape(10.dp)).padding(12.dp)) {
                    Text(event.kind + " · " + (event.side ?: "FLAT") + " · " + "%,.2f".format(event.price),
                        color = if (event.kind.contains("SL")) NRed else NGreen, fontWeight = FontWeight.SemiBold)
                    Text(SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date(event.candleTime)), color = NMuted)
                    if (event.note.isNotBlank()) Text(event.note, color = NMuted)
                }
            }
        }
    }
}

private fun fmt(value: Double?): String = value?.let { "%.2f".format(it) } ?: "—"

@Composable
private fun StatCard(label: String, value: Double?, modifier: Modifier = Modifier) {
    Column(modifier.background(NPanel, RoundedCornerShape(12.dp)).padding(14.dp)) {
        Text(label, color = NMuted)
        Text(fmt(value), color = Color.White, style = MaterialTheme.typography.titleLarge)
    }
}

@Composable
private fun LiveCandles(candles: List<Candle>, modifier: Modifier = Modifier) {
    Canvas(modifier.background(NBg, RoundedCornerShape(8.dp))) {
        val data = candles.takeLast(70)
        if (data.isEmpty()) return@Canvas
        val low = data.minOf { it.low }
        val high = data.maxOf { it.high }
        val range = (high - low).takeIf { it > 0 } ?: 1.0
        val step = size.width / data.size
        data.forEachIndexed { i, c ->
            val x = step * (i + 0.5f)
            fun y(p: Double) = size.height - (((p - low) / range).toFloat() * size.height)
            val color = if (c.close >= c.open) NGreen else NRed
            drawLine(color, Offset(x, y(c.high)), Offset(x, y(c.low)), strokeWidth = 2f)
            val top = minOf(y(c.open), y(c.close))
            val bottom = maxOf(y(c.open), y(c.close))
            drawRect(color, Offset(x - maxOf(1.5f, step * 0.28f), top),
                androidx.compose.ui.geometry.Size(maxOf(3f, step * 0.56f), maxOf(2f, bottom - top)))
        }
    }
}
