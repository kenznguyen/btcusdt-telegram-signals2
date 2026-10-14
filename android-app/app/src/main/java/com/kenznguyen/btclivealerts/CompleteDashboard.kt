package com.kenznguyen.btclivealerts

import android.app.NotificationManager
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
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
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import okhttp3.WebSocket
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
    var catchUp by remember { mutableStateOf(prefs.getBoolean("alert_catch_up_after_quiet", true)) }
    var alertSettingsExpanded by remember { mutableStateOf(false) }
    var monitorHeartbeat by remember { mutableStateOf("Đang chờ lần kiểm tra đầu tiên…") }
    var monitorError by remember { mutableStateOf("") }
    var lastProcessedCandle by remember { mutableStateOf("—") }
    var lastEventCount by remember { mutableIntStateOf(0) }
    var state by remember { mutableStateOf(StrategyState.fromJson(prefs.getString("state_json", null))) }
    var m15Ind by remember { mutableStateOf(IndicatorPoint()) }
    var h1Ind by remember { mutableStateOf(IndicatorPoint()) }
    var showRsi by remember { mutableStateOf(prefs.getBoolean("chart_show_rsi", true)) }
    var showAdx by remember { mutableStateOf(prefs.getBoolean("chart_show_adx", true)) }
    var showDi by remember { mutableStateOf(prefs.getBoolean("chart_show_di", true)) }
    var showH1Trend by remember { mutableStateOf(prefs.getBoolean("chart_show_h1", true)) }
    var chartSettingsExpanded by remember { mutableStateOf(false) }
    var socketStatus by remember { mutableStateOf("Đang đồng bộ REST…") }

    LaunchedEffect(timeframe) {
        val mainHandler = Handler(Looper.getMainLooper())
        var socket: WebSocket? = null
        try {
            val initial = market.fetchCandles(timeframe, 500)
            val cache = java.util.TreeMap<Long, Candle>()
            initial.forEach { cache[it.openTime] = it }
            chart = cache.values.toList()
            var m15Data = if (timeframe == "15m") initial else market.fetchCandles("15m", 500)
            var h1Data = if (timeframe == "1h") initial else market.fetchCandles("1h", 500)
            m15Ind = engine.indicatorSeries(m15Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
            h1Ind = engine.indicatorSeries(h1Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
            price = market.fetchMarkPrice()
            socketStatus = "REST đồng bộ xong · WebSocket đang kết nối"
            socket = market.connectLive(
                interval = timeframe,
                onCandle = { candle ->
                    mainHandler.post {
                        status = "Dữ liệu live đang hoạt động"
                        cache[candle.openTime] = candle
                        while (cache.size > 500) cache.pollFirstEntry()
                        chart = cache.values.toList()
                        socketStatus = "WebSocket live · " + SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
                    }
                },
                onMarkPrice = { mark -> mainHandler.post { price = mark; status = "Dữ liệu live đang hoạt động" } },
                onStatus = { message -> mainHandler.post { socketStatus = message; status = message } }
            )
            while (true) {
                delay(60_000)
                val reconciled = market.fetchCandles(timeframe, 500)
                mainHandler.post {
                    reconciled.forEach { cache[it.openTime] = it }
                    while (cache.size > 500) cache.pollFirstEntry()
                    chart = cache.values.toList()
                    if (timeframe == "15m") m15Data = cache.values.toList() else h1Data = cache.values.toList()
                    m15Ind = engine.indicatorSeries(m15Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
                    h1Ind = engine.indicatorSeries(h1Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
                    state = StrategyState.fromJson(prefs.getString("state_json", null))
                    val heartbeat = prefs.getLong("monitor_last_success_ms", 0L)
                    monitorHeartbeat = if (heartbeat > 0L) "Lần quét thành công: " + SimpleDateFormat("HH:mm:ss dd/MM", Locale.getDefault()).format(Date(heartbeat)) else "Chưa có lần quét thành công"
                    val candleTime = prefs.getLong("monitor_last_candle_open", 0L)
                    lastProcessedCandle = if (candleTime > 0L) SimpleDateFormat("HH:mm dd/MM", Locale.getDefault()).format(Date(candleTime)) else "Chưa có nến được xử lý"
                    lastEventCount = prefs.getInt("monitor_last_event_count", 0)
                    monitorError = prefs.getString("monitor_last_error", "").orEmpty()
                    status = socketStatus
                }
            }
        } catch (e: CancellationException) {
            // LaunchedEffect is cancelled normally when timeframe changes or the screen leaves composition.
            // Do not show coroutine cancellation as a sync/network error.
            throw e
        } catch (e: Exception) {
            status = "Lỗi đồng bộ: " + (e.message ?: "lỗi mạng")
            socketStatus = "REST/WebSocket cần đồng bộ lại"
        } finally {
            socket?.close(1000, "timeframe changed")
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
                    Text(status, color = if (status.startsWith("Đang kết nối") || status.startsWith("Đang tải") || status.startsWith("Đang đồng bộ")) NGreen else if (status.startsWith("Lỗi")) NRed else NMuted)
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
                    Text("Binance Futures · REST + WebSocket · 500 nến", color = NMuted)
                    Text(socketStatus, color = if (socketStatus.contains("live") || socketStatus.contains("kết nối")) NGreen else NRed, style = MaterialTheme.typography.bodySmall)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Chỉ báo hiển thị", color = Color.White, modifier = Modifier.weight(1f))
                        TextButton(onClick = { chartSettingsExpanded = !chartSettingsExpanded }) { Text(if (chartSettingsExpanded) "Thu gọn" else "Tùy chỉnh") }
                    }
                    if (chartSettingsExpanded) {
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            PreferenceSwitch("RSI (14)", showRsi, { showRsi = it; prefs.edit().putBoolean("chart_show_rsi", it).apply() })
                            PreferenceSwitch("ADX (14)", showAdx, { showAdx = it; prefs.edit().putBoolean("chart_show_adx", it).apply() })
                            PreferenceSwitch("+DI / −DI", showDi, { showDi = it; prefs.edit().putBoolean("chart_show_di", it).apply() })
                            PreferenceSwitch("Xu hướng H1", showH1Trend, { showH1Trend = it; prefs.edit().putBoolean("chart_show_h1", it).apply() })
                        }
                    }
                }
            }
            if (showRsi || showAdx) item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    if (showRsi) StatCard("RSI (14)", shown.rsi, Modifier.weight(1f))
                    if (showAdx) StatCard("ADX (14)", shown.adx, Modifier.weight(1f))
                }
            }
            item {
                Column(Modifier.fillMaxWidth().background(NPanel, RoundedCornerShape(14.dp)).padding(14.dp)) {
                    Text("CHIẾN LƯỢC M15 / H1", color = Color.White, fontWeight = FontWeight.Bold)
                    if (showH1Trend) {
                        val plusDiValue = h1Ind.plusDi
                        val minusDiValue = h1Ind.minusDi
                        Text("Xu hướng H1: " + when {
                            plusDiValue == null || minusDiValue == null -> "Đang tính"
                            plusDiValue > minusDiValue -> "TĂNG"
                            minusDiValue > plusDiValue -> "GIẢM"
                            else -> "TRUNG TÍNH"
                        }, color = NMuted)
                    }
                    if (showDi) Text("H1 ADX " + fmt(h1Ind.adx) + " · +DI " + fmt(h1Ind.plusDi) + " · -DI " + fmt(h1Ind.minusDi), color = NMuted)
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
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("Cài đặt thông báo", color = Color.White, fontWeight = FontWeight.Bold)
                            Text("Loại tín hiệu, âm thanh, rung và giờ yên lặng", color = NMuted, style = MaterialTheme.typography.bodySmall)
                        }
                        TextButton(onClick = { alertSettingsExpanded = !alertSettingsExpanded }) { Text(if (alertSettingsExpanded) "Thu gọn" else "Tùy chỉnh") }
                    }
                    if (alertSettingsExpanded) {
                        Column(Modifier.fillMaxWidth().background(NBg, RoundedCornerShape(10.dp)).padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
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

                            PreferenceSwitch("Gửi bù sau giờ yên lặng", catchUp, { catchUp = it; prefs.edit().putBoolean("alert_catch_up_after_quiet", it).apply() })
                            if (quietHours && catchUp) Text("Các cảnh báo đủ điều kiện sẽ được gửi sau khi hết giờ yên lặng.", color = NMuted, style = MaterialTheme.typography.bodySmall)
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
    var visibleCount by remember { mutableIntStateOf(70) }
    var panBars by remember { mutableIntStateOf(0) }
    var selectedOpenTime by remember { mutableStateOf<Long?>(null) }
    Canvas(
        modifier
            .background(NBg, RoundedCornerShape(8.dp))
            .pointerInput(candles.size, visibleCount) {
                detectTapGestures { point ->
                    if (candles.isNotEmpty()) {
                        val end = (candles.size - panBars).coerceIn(1, candles.size)
                        val start = (end - visibleCount).coerceAtLeast(0)
                        val shown = candles.subList(start, end)
                        val index = (point.x / size.width * shown.size).toInt().coerceIn(0, shown.lastIndex)
                        selectedOpenTime = shown[index].openTime
                    }
                }
            }
            .pointerInput(candles.size, visibleCount) {
                detectDragGestures { change, drag ->
                    change.consume()
                    val shown = visibleCount.coerceAtLeast(1)
                    val bars = (drag.x / size.width * shown).toInt()
                    panBars = (panBars + bars).coerceIn(0, (candles.size - 1).coerceAtLeast(0))
                }
            }
            .pointerInput(candles.size) {
                detectTransformGestures { _, _, zoom, _ ->
                    visibleCount = (visibleCount / zoom).toInt().coerceIn(20, 150)
                    panBars = panBars.coerceIn(0, (candles.size - 1).coerceAtLeast(0))
                }
            }
    ) {
        if (candles.isEmpty() || size.width <= 0f || size.height <= 0f) return@Canvas
        val end = (candles.size - panBars).coerceIn(1, candles.size)
        val start = (end - visibleCount).coerceAtLeast(0)
        val data = candles.subList(start, end)
        if (data.isEmpty()) return@Canvas

        // Include mark price in the scale so the live-price line remains visible after sharp moves.
        var low = data.minOf { it.low }
        var high = data.maxOf { it.high }
        markPrice?.let { low = minOf(low, it); high = maxOf(high, it) }
        val rawRange = (high - low).takeIf { it > 0.0 } ?: (high * 0.001).coerceAtLeast(1.0)
        val padding = rawRange * 0.04
        low -= padding
        high += padding
        val range = (high - low).takeIf { it > 0 } ?: 1.0
        fun y(price: Double) = size.height - (((price - low) / range).toFloat() * size.height)

        for (line in 1..4) {
            val gy = size.height * line / 5f
            drawLine(Color(0xFF263243), Offset(0f, gy), Offset(size.width, gy), strokeWidth = 1f)
        }

        val step = size.width / data.size
        data.forEachIndexed { i, candle ->
            val x = step * (i + 0.5f)
            val color = if (candle.close >= candle.open) NGreen else NRed
            drawLine(color, Offset(x, y(candle.high)), Offset(x, y(candle.low)), strokeWidth = 1.5f)
            val top = minOf(y(candle.open), y(candle.close))
            val bottom = maxOf(y(candle.open), y(candle.close))
            drawRect(color, Offset(x - maxOf(1.5f, step * 0.30f), top),
                androidx.compose.ui.geometry.Size(maxOf(2f, step * 0.60f), maxOf(1.5f, bottom - top)))
            if (candle.openTime == selectedOpenTime) {
                drawLine(Color(0xFF9B8AFB), Offset(x, 0f), Offset(x, size.height), strokeWidth = 1f)
                drawLine(Color(0xFF9B8AFB), Offset(0f, y(candle.close)), Offset(size.width, y(candle.close)), strokeWidth = 1f)
            }
        }
        markPrice?.let { current ->
            val py = y(current)
            drawLine(Color(0xFFFFC857), Offset(0f, py), Offset(size.width, py), strokeWidth = 1.5f)
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
