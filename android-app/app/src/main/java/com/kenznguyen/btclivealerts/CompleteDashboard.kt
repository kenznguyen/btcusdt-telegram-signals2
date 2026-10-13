package com.kenznguyen.btclivealerts

import android.app.NotificationManager
import android.content.Context
import android.os.Build
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
import androidx.core.app.NotificationManagerCompat
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
    var notificationTestStatus by remember { mutableStateOf("Chưa chạy kiểm thử thông báo") }
    var longAlerts by remember { mutableStateOf(prefs.getBoolean("alert_long", true)) }
    var shortAlerts by remember { mutableStateOf(prefs.getBoolean("alert_short", true)) }
    var entryAlerts by remember { mutableStateOf(prefs.getBoolean("alert_entry", true)) }
    var dcaAlerts by remember { mutableStateOf(prefs.getBoolean("alert_dca", true)) }
    var tpAlerts by remember { mutableStateOf(prefs.getBoolean("alert_take_profit", true)) }
    var softSlAlerts by remember { mutableStateOf(prefs.getBoolean("alert_soft_sl", true)) }
    var emergencySlAlerts by remember { mutableStateOf(prefs.getBoolean("alert_emergency_sl", true)) }
    var vibration by remember { mutableStateOf(prefs.getBoolean("alert_vibration", true)) }
    var sound by remember { mutableStateOf(prefs.getBoolean("alert_sound", true)) }
    var quietHours by remember { mutableStateOf(prefs.getBoolean("quiet_hours_enabled", false)) }
    var quietStart by remember { mutableIntStateOf(prefs.getInt("quiet_start_hour", 23)) }
    var quietEnd by remember { mutableIntStateOf(prefs.getInt("quiet_end_hour", 7)) }
    var monitorHeartbeat by remember { mutableStateOf("Đang chờ lần kiểm tra đầu tiên…") }
    var monitorError by remember { mutableStateOf("") }
    var lastProcessedCandle by remember { mutableStateOf("—") }
    var lastEventCount by remember { mutableIntStateOf(0) }
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
                val heartbeat = prefs.getLong("monitor_last_success_ms", 0L)
                monitorHeartbeat = if (heartbeat > 0L) "Lần quét thành công: " + SimpleDateFormat("HH:mm:ss dd/MM", Locale.getDefault()).format(Date(heartbeat)) else "Chưa có lần quét thành công"
                val candleTime = prefs.getLong("monitor_last_candle_open", 0L)
                lastProcessedCandle = if (candleTime > 0L) SimpleDateFormat("HH:mm dd/MM", Locale.getDefault()).format(Date(candleTime)) else "Chưa có nến được xử lý"
                lastEventCount = prefs.getInt("monitor_last_event_count", 0)
                monitorError = prefs.getString("monitor_last_error", "").orEmpty()
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
                    Text(monitorHeartbeat, color = NMuted, style = MaterialTheme.typography.bodySmall)
                    Text("Nến M15 xử lý gần nhất: $lastProcessedCandle · Sự kiện lần quét gần nhất: $lastEventCount", color = NMuted, style = MaterialTheme.typography.bodySmall)
                    if (monitorError.isNotBlank()) Text("Lỗi giám sát gần nhất: $monitorError", color = NRed, style = MaterialTheme.typography.bodySmall)
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
                    LiveCandles(chart, price, Modifier.fillMaxWidth().height(260.dp))
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
                    Text("TÙY CHỈNH THÔNG BÁO", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("Chọn loại tín hiệu và hướng giao dịch muốn nhận.", color = NMuted, style = MaterialTheme.typography.bodySmall)
                    PreferenceSwitch("LONG", longAlerts, { longAlerts = it; prefs.edit().putBoolean("alert_long", it).apply() })
                    PreferenceSwitch("SHORT", shortAlerts, { shortAlerts = it; prefs.edit().putBoolean("alert_short", it).apply() })
                    PreferenceSwitch("Entry", entryAlerts, { entryAlerts = it; prefs.edit().putBoolean("alert_entry", it).apply() })
                    PreferenceSwitch("DCA", dcaAlerts, { dcaAlerts = it; prefs.edit().putBoolean("alert_dca", it).apply() })
                    PreferenceSwitch("Take Profit", tpAlerts, { tpAlerts = it; prefs.edit().putBoolean("alert_take_profit", it).apply() })
                    PreferenceSwitch("Soft Stop Loss", softSlAlerts, { softSlAlerts = it; prefs.edit().putBoolean("alert_soft_sl", it).apply() })
                    PreferenceSwitch("Emergency Stop Loss", emergencySlAlerts, { emergencySlAlerts = it; prefs.edit().putBoolean("alert_emergency_sl", it).apply() })
                    PreferenceSwitch("Rung / rung nhắc", vibration, { vibration = it; prefs.edit().putBoolean("alert_vibration", it).apply() })
                    PreferenceSwitch("Âm thanh", sound, { sound = it; prefs.edit().putBoolean("alert_sound", it).apply() })
                    PreferenceSwitch("Giờ yên lặng", quietHours, { quietHours = it; prefs.edit().putBoolean("quiet_hours_enabled", it).apply() })
                    if (quietHours) {
                        Text("Giờ yên lặng theo giờ địa phương của điện thoại", color = NMuted, style = MaterialTheme.typography.bodySmall)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Column(Modifier.weight(1f)) {
                                Text("Bắt đầu: " + quietStart + ":00", color = Color.White)
                                Slider(value = quietStart.toFloat(), onValueChange = { quietStart = it.toInt() }, valueRange = 0f..23f, steps = 22, onValueChangeFinished = { prefs.edit().putInt("quiet_start_hour", quietStart).apply() })
                            }
                            Column(Modifier.weight(1f)) {
                                Text("Kết thúc: " + quietEnd + ":00", color = Color.White)
                                Slider(value = quietEnd.toFloat(), onValueChange = { quietEnd = it.toInt() }, valueRange = 0f..23f, steps = 22, onValueChangeFinished = { prefs.edit().putInt("quiet_end_hour", quietEnd).apply() })
                            }
                        }
                    }
                    Button(
                        onClick = {
                            val manager = NotificationManagerCompat.from(context)
                            if (!manager.areNotificationsEnabled()) {
                                notificationTestStatus = "THẤT BẠI: quyền thông báo đang bị tắt. Vào Cài đặt Android > Ứng dụng > BTCUSDT Live Alerts > Thông báo để bật."
                            } else {
                                try {
                                    val now = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
                                    manager.notify(987654, NotificationCompat.Builder(context, "strategy_alerts")
                                        .setSmallIcon(android.R.drawable.ic_dialog_info)
                                        .setContentTitle("BTCUSDT · THÔNG BÁO THỬ")
                                        .setContentText("Kiểm thử thành công lúc $now")
                                        .setStyle(NotificationCompat.BigTextStyle().bigText("Đây là thông báo thử từ ứng dụng BTCUSDT Live Alerts. Thời gian: $now"))
                                        .setPriority(NotificationCompat.PRIORITY_HIGH)
                                        .setAutoCancel(true).build())
                                    notificationTestStatus = "ĐÃ GỬI lúc $now — hãy kiểm tra thanh thông báo."
                                } catch (e: SecurityException) {
                                    notificationTestStatus = "THẤT BẠI: Android từ chối quyền thông báo. Kiểm tra quyền trong Cài đặt."
                                } catch (e: Exception) {
                                    notificationTestStatus = "THẤT BẠI: " + (e.message ?: "không rõ lỗi")
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("GỬI THÔNG BÁO THỬ") }
                    Text(notificationTestStatus, color = if (notificationTestStatus.startsWith("ĐÃ GỬI")) NGreen else NMuted, style = MaterialTheme.typography.bodySmall)
                    Text("Cảnh báo chiến lược chỉ phát sinh khi nến M15 đóng và đủ điều kiện. Thông báo thử chỉ kiểm tra quyền và kênh thông báo; không xác nhận chiến lược đã phát tín hiệu. Theo dõi nền có thể bị Android giới hạn.", color = Color(0xFFFFC857), style = MaterialTheme.typography.bodySmall)
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
            item { BacktestPanel(market, engine) }
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
private fun LiveCandles(candles: List<Candle>, markPrice: Double?, modifier: Modifier = Modifier) {
    Canvas(modifier.background(NBg, RoundedCornerShape(8.dp))) {
        val data = candles.takeLast(70)
        if (data.isEmpty()) return@Canvas
        val low = data.minOf { it.low }
        val high = data.maxOf { it.high }
        val range = (high - low).takeIf { it > 0 } ?: 1.0
        // Price grid makes candle ranges easier to read.
        for (line in 1..4) {
            val gy = size.height * line / 5f
            drawLine(Color(0xFF263243), Offset(0f, gy), Offset(size.width, gy), strokeWidth = 1f)
        }
        markPrice?.takeIf { it in low..high }?.let { current ->
            val py = size.height - (((current - low) / range).toFloat() * size.height)
            drawLine(Color(0xFFFFC857), Offset(0f, py), Offset(size.width, py), strokeWidth = 1.5f)
        }
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


@Composable
private fun PreferenceSwitch(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = NMuted, modifier = Modifier.weight(1f))
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}
