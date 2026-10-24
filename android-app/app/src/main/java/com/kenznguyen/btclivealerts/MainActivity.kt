package com.kenznguyen.btclivealerts

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.core.content.ContextCompat
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val Bg = Color(0xFF0B1018)
private val Panel = Color(0xFF151D29)
private val Green = Color(0xFF20C997)
private val Red = Color(0xFFFF647C)
private val Muted = Color(0xFF91A0B5)

class MainActivity : ComponentActivity() {
    private val permissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        createNotificationChannel()
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
        ContextCompat.startForegroundService(this, Intent(this, StrategyMonitorService::class.java))
        setContent { MaterialTheme(colorScheme = darkColorScheme()) { CompleteDashboard(this) } }
    }

    private fun createNotificationChannel() {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(NotificationChannel("strategy_alerts", "Strategy alerts", NotificationManager.IMPORTANCE_HIGH))
    }
}

@Composable
private fun Dashboard(context: Context) {
    val engine = remember { MarketEngine() }
    var timeframe by remember { mutableStateOf("15m") }
    var candles by remember { mutableStateOf<List<Candle>>(emptyList()) }
    var markPrice by remember { mutableStateOf<Double?>(null) }
    var indicators by remember { mutableStateOf(Indicators(null, null, null, null)) }
    var status by remember { mutableStateOf("Đang kết nối Binance Futures…") }
    var alertsEnabled by remember { mutableStateOf(true) }
    var lastSignal by remember { mutableStateOf("") }
    var history by remember { mutableStateOf(listOf("Ứng dụng chỉ tạo cảnh báo; không đặt lệnh.")) }

    LaunchedEffect(timeframe) {
        while (true) {
            try {
                val data = engine.fetchCandles(timeframe, 200)
                val closed = data.filter { it.closed }
                candles = data
                markPrice = engine.fetchMarkPrice()
                indicators = engine.indicators(closed)
                status = "Đang kết nối · cập nhật ${SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())}"
                if (closed.size >= 2 && alertsEnabled) {
                    val prev = engine.indicators(closed.dropLast(1))
                    val current = indicators
                    val trendLong = (current.plusDi ?: 0.0) > (current.minusDi ?: 0.0)
                    val trendShort = (current.minusDi ?: 0.0) > (current.plusDi ?: 0.0)
                    val signal = when {
                        prev.rsi != null && current.rsi != null && prev.rsi <= 30 && current.rsi > 30 && trendLong -> "LONG ENTRY"
                        prev.rsi != null && current.rsi != null && prev.rsi >= 70 && current.rsi < 70 && trendShort -> "SHORT ENTRY"
                        else -> ""
                    }
                    if (signal.isNotBlank() && signal != lastSignal) {
                        lastSignal = signal
                        history = listOf("$signal · ${markPrice?.let { "%.2f".format(it) } ?: "—"}") + history
                        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                        manager.notify(signal.hashCode(), NotificationCompat.Builder(context, "strategy_alerts")
                            .setSmallIcon(android.R.drawable.ic_dialog_info)
                            .setContentTitle("BTCUSDT.P · $signal")
                            .setContentText("Tín hiệu sơ bộ · xác minh điều kiện chiến lược đầy đủ")
                            .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true).build())
                    }
                }
            } catch (e: Exception) {
                status = "Mất kết nối: ${e.message ?: "lỗi mạng"}"
            }
            delay(15_000)
        }
    }

    Surface(Modifier.fillMaxSize(), color = Bg) {
        LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            item {
                Text("BTCUSDT.P", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = Color.White)
                Text("USDⓈ-M Perpetual · Chỉ xem · Không đặt lệnh", color = Muted)
            }
            item {
                Column(Modifier.fillMaxWidth().background(Panel, RoundedCornerShape(16.dp)).padding(16.dp)) {
                    Text("MARK PRICE", color = Muted)
                    Text(markPrice?.let { "$" + "%,.2f".format(it) } ?: "—", style = MaterialTheme.typography.headlineLarge, color = Color.White)
                    Text(status, color = if (status.startsWith("Đang kết nối ·")) Green else Red)
                }
            }
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("15m", "1h").forEach { tf ->
                        FilterChip(selected = timeframe == tf, onClick = { timeframe = tf }, label = { Text(tf.uppercase()) })
                    }
                    Spacer(Modifier.weight(1f))
                    Text("LIVE", color = Green, modifier = Modifier.align(Alignment.CenterVertically))
                }
            }
            item {
                Column(Modifier.fillMaxWidth().background(Panel, RoundedCornerShape(16.dp)).padding(12.dp)) {
                    Text("Candlestick chart", color = Color.White, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.height(8.dp))
                    CandleChart(candles, Modifier.fillMaxWidth().height(230.dp))
                    Text("Giá nến từ Binance Futures · làm mới 15 giây", color = Muted, style = MaterialTheme.typography.bodySmall)
                }
            }
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    IndicatorCard("RSI (14)", indicators.rsi, Modifier.weight(1f))
                    IndicatorCard("ADX (14)", indicators.adx, Modifier.weight(1f))
                }
            }
            item {
                Column(Modifier.fillMaxWidth().background(Panel, RoundedCornerShape(16.dp)).padding(14.dp)) {
                    Text("Cảnh báo chiến lược", color = Color.White, fontWeight = FontWeight.SemiBold)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Cho phép thông báo", color = Muted, modifier = Modifier.weight(1f))
                        Switch(checked = alertsEnabled, onCheckedChange = { alertsEnabled = it })
                    }
                    Text("Entry đang ở chế độ khung thử nghiệm. DCA/TP/SL chưa được bật trước khi đối chiếu bộ máy Python.", color = Color(0xFFFFC857), style = MaterialTheme.typography.bodySmall)
                }
            }
            item { Text("Lịch sử cảnh báo", color = Color.White, fontWeight = FontWeight.SemiBold) }
            items(history.take(20)) { event ->
                Text(event, color = Muted, modifier = Modifier.fillMaxWidth().background(Panel, RoundedCornerShape(10.dp)).padding(12.dp))
            }
        }
    }
}

@Composable
private fun IndicatorCard(label: String, value: Double?, modifier: Modifier = Modifier) {
    Column(modifier.background(Panel, RoundedCornerShape(12.dp)).padding(14.dp)) {
        Text(label, color = Muted)
        Text(value?.let { "%.2f".format(it) } ?: "—", color = Color.White, style = MaterialTheme.typography.titleLarge)
    }
}

@Composable
private fun CandleChart(candles: List<Candle>, modifier: Modifier = Modifier) {
    Canvas(modifier.background(Bg, RoundedCornerShape(8.dp))) {
        val data = candles.takeLast(70)
        if (data.isEmpty()) return@Canvas
        val low = data.minOf { it.low }
        val high = data.maxOf { it.high }
        val range = (high - low).takeIf { it > 0 } ?: 1.0
        val step = size.width / data.size
        data.forEachIndexed { index, candle ->
            val x = step * (index + 0.5f)
            fun y(price: Double) = size.height - (((price - low) / range).toFloat() * size.height)
            val color = if (candle.close >= candle.open) Green else Red
            drawLine(color, Offset(x, y(candle.high)), Offset(x, y(candle.low)), strokeWidth = 2f)
            val top = minOf(y(candle.open), y(candle.close))
            val bottom = maxOf(y(candle.open), y(candle.close))
            drawRect(color, topLeft = Offset(x - maxOf(1.5f, step * 0.28f), top), size = androidx.compose.ui.geometry.Size(maxOf(3f, step * 0.56f), maxOf(2f, bottom - top)))
        }
    }
}
