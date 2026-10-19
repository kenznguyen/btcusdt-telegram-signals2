package com.kenznguyen.btclivealerts

import android.app.NotificationManager
import android.graphics.Paint as AndroidPaint
import android.graphics.Typeface
import android.content.Context
import android.content.SharedPreferences
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
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.window.DialogWindowProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import org.json.JSONArray
import org.json.JSONObject
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import okhttp3.WebSocket
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.isActive

private data class H1TrendMark(val openTime: Long, val direction: Int, val strong: Boolean)
private data class SavedAlert(val title: String, val body: String, val timestamp: Long, val source: String)

private fun chartAlertPrefKey(timeframe: String, name: String): String =
    "chart_alert_${timeframe}_${name}"

private fun saveAlertHistory(prefs: SharedPreferences, title: String, body: String, source: String) {
    synchronized(prefs) {
        val history = runCatching { JSONArray(prefs.getString("notification_history_json", "[]")) }.getOrDefault(JSONArray())
        val item = JSONObject().put("title", title).put("body", body)
            .put("timestamp", System.currentTimeMillis()).put("source", source)
        val updated = JSONArray().put(item)
        for (i in 0 until minOf(history.length(), 99)) {
            val oldIndex = history.length() - 1 - i
            updated.put(history.getJSONObject(oldIndex))
        }
        prefs.edit().putString("notification_history_json", updated.toString()).apply()
    }
}

private fun readAlertHistory(prefs: SharedPreferences): List<SavedAlert> {
    val array = runCatching { JSONArray(prefs.getString("notification_history_json", "[]")) }.getOrDefault(JSONArray())
    return (0 until array.length()).mapNotNull { i ->
        runCatching {
            val item = array.getJSONObject(i)
            SavedAlert(item.optString("title"), item.optString("body"), item.optLong("timestamp"), item.optString("source"))
        }.getOrNull()
    }
}

private val NBg = Color(0xFF0B1018)
private val NPanel = Color(0xFF151D29)
private val NGreen = Color(0xFF20C997)
private val NRed = Color(0xFFFF647C)
private val NMuted = Color(0xFF91A0B5)

private fun mergeCandle(cache: java.util.TreeMap<Long, Candle>, candle: Candle) {
    val existing = cache[candle.openTime]
    // A REST snapshot must never downgrade a WebSocket-confirmed closed candle.
    if (existing?.closed == true && !candle.closed) return
    cache[candle.openTime] = candle
}

internal fun maybeNotifyRsiM15(
    context: Context,
    prefs: SharedPreferences,
    engine: StrategyEngine,
    candles: List<Candle>,
    closedCandle: Candle
) {
    if (!closedCandle.closed || !prefs.getBoolean("alerts_enabled", true) ||
        !prefs.getBoolean("alert_rsi_m15_enabled", false)) return
    val closedPoints = engine.indicatorSeries(candles.filter { it.closed }.sortedBy { it.openTime })
    val latestRsi = closedPoints.lastOrNull()?.rsi ?: return
    val previousRsi = closedPoints.getOrNull(closedPoints.lastIndex - 1)?.rsi ?: return
    val high = prefs.getInt("alert_rsi_m15_high", 70).toDouble().coerceIn(1.0, 99.0)
    val low = prefs.getInt("alert_rsi_m15_low", 30).toDouble().coerceIn(1.0, 99.0)
    val condition = if (low < high) when {
        previousRsi < high && latestRsi >= high -> "HIGH"
        previousRsi > low && latestRsi <= low -> "LOW"
        else -> null
    } else null
    if (condition == null) return
    val eventKey = "${closedCandle.openTime}:$condition"
    val now = SimpleDateFormat("HH:mm dd/MM", Locale.getDefault()).format(Date())
    val threshold = if (condition == "HIGH") high.toInt() else low.toInt()
    val title = if (condition == "HIGH") "BTCUSDT · RSI M15 vượt ngưỡng cao" else "BTCUSDT · RSI M15 xuống ngưỡng thấp"
    val body = "Khung M15 · RSI(14): ${"%.1f".format(Locale.US, latestRsi)} · ngưỡng: $threshold · giá đóng: ${"%,.2f".format(Locale.US, closedCandle.close)} USDT · nến đóng: $now"
    // Atomically reserve the event across the UI socket and background monitor.
    val shouldNotify = synchronized(prefs) {
        if (prefs.getString("alert_rsi_m15_last_event", null) == eventKey) false
        else {
            saveAlertHistory(prefs, title, body, "RSI M15")
            prefs.edit().putString("alert_rsi_m15_last_event", eventKey).apply()
            true
        }
    }
    if (!shouldNotify) return
    deliverChartNotification(context, prefs, "RSI_M15:$eventKey", title, body)
}


private fun isChartAlertQuietHours(prefs: SharedPreferences): Boolean {
    if (!prefs.getBoolean("quiet_hours_enabled", false)) return false
    val start = prefs.getInt("quiet_start_hour", 23)
    val end = prefs.getInt("quiet_end_hour", 7)
    val hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY)
    return if (start == end) true else if (start < end) hour >= start && hour < end else hour >= start || hour < end
}

/** Applies quiet-hours, catch-up, sound and vibration preferences to chart alerts. */
private fun deliverChartNotification(
    context: Context,
    prefs: SharedPreferences,
    key: String,
    title: String,
    body: String
) {
    if (isChartAlertQuietHours(prefs)) {
        if (prefs.getBoolean("alert_catch_up_after_quiet", true)) {
            synchronized(prefs) {
                val queue = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
                queue.add("$key|$title|$body")
                prefs.edit().putStringSet("quiet_alert_queue", queue).apply()
            }
        }
        return
    }
    val manager = NotificationManagerCompat.from(context)
    if (!manager.areNotificationsEnabled()) return
    val builder = NotificationCompat.Builder(context, "strategy_alerts")
        .setSmallIcon(android.R.drawable.ic_dialog_info)
        .setContentTitle(title).setContentText(body)
        .setStyle(NotificationCompat.BigTextStyle().bigText(body))
        .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true)
    if (prefs.getBoolean("alert_vibration", true)) builder.setVibrate(longArrayOf(0, 250, 120, 250))
    else builder.setVibrate(longArrayOf(0))
    if (!prefs.getBoolean("alert_sound", true)) builder.setSilent(true)
    try {
        manager.notify(key.hashCode() and 0x7fffffff, builder.build())
    } catch (_: SecurityException) { }
}

private fun notifyChartAlert(
    context: Context,
    prefs: SharedPreferences,
    key: String,
    notificationId: Int,
    title: String,
    body: String
) {
    if (!prefs.getBoolean("alerts_enabled", true)) return
    val manager = NotificationManagerCompat.from(context)
    if (!manager.areNotificationsEnabled()) return
    if (prefs.getString("chart_alert_last_$key", null) == key.substringAfterLast(":")) return
    try {
        manager.notify(notificationId, NotificationCompat.Builder(context, "strategy_alerts")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title).setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true).build())
        prefs.edit().putString("chart_alert_last_$key", key.substringAfterLast(":")).apply()
    } catch (_: SecurityException) { }
}

internal fun maybeNotifyChartAlerts(
    context: Context,
    prefs: SharedPreferences,
    engine: StrategyEngine,
    candles: List<Candle>,
    closedCandle: Candle,
    timeframe: String
) {
    if (!closedCandle.closed || !prefs.getBoolean("alerts_enabled", true)) return
    val closed = candles.filter { it.closed }.sortedBy { it.openTime }
    if (closed.size < 22 || closed.lastOrNull()?.openTime != closedCandle.openTime) return
    val points = engine.indicatorSeries(closed)
    val current = points.lastOrNull() ?: return
    val previous = points.getOrNull(points.lastIndex - 1) ?: return
    val time = SimpleDateFormat("HH:mm dd/MM", Locale.getDefault()).format(Date(closedCandle.openTime))
    fun fire(setting: String, condition: String, id: Int, title: String, value: String) {
        val settingName = setting.removePrefix("chart_alert_")
        val enabled = prefs.getBoolean(chartAlertPrefKey(timeframe, settingName),
            prefs.getBoolean(setting, false))
        if (enabled) {
            val eventKey = "$timeframe:$condition:${closedCandle.openTime}"
            val prefKey = "chart_alert_last_$setting"
            val body = "$value · ${timeframe.uppercase()} · giá đóng ${"%,.2f".format(Locale.US, closedCandle.close)} USDT"
            // Atomically reserve the event across the UI socket and background monitor.
            val shouldNotify = synchronized(prefs) {
                if (prefs.getString(prefKey, null) == eventKey) false
                else {
                    saveAlertHistory(prefs, title, body, "Biểu đồ · ${timeframe.uppercase()}")
                    prefs.edit().putString(prefKey, eventKey).apply()
                    true
                }
            }
            if (shouldNotify) {
                val notificationBody = "BTCUSDT PERPETUAL\n$value\nKhung thời gian: ${timeframe.uppercase()}\nGiá đóng nến: ${"%,.2f".format(Locale.US, closedCandle.close)} USDT\nThời điểm nến đóng: $time"
                // Stable timeframe + condition key avoids cross-chart notification overwrites.
                deliverChartNotification(context, prefs, "chart:$timeframe:$condition:${closedCandle.openTime}", title, notificationBody)
            }
        }
    }

    // MFI & %B: alert when the combined line crosses user-defined upper/lower levels.
    val combined = current.mfiBProduct
    val priorCombined = previous.mfiBProduct
    val upper = prefs.getFloat(chartAlertPrefKey(timeframe, "mfib_upper"), prefs.getFloat("chart_alert_mfib_upper", 0.8f)).toDouble()
    val lower = prefs.getFloat(chartAlertPrefKey(timeframe, "mfib_lower"), prefs.getFloat("chart_alert_mfib_lower", 0.2f)).toDouble()
    if (combined != null && priorCombined != null && lower < upper) {
        if (priorCombined < upper && combined >= upper)
            fire("chart_alert_mfib_enabled", "MFIB_HIGH", 987671, "BTCUSDT · MFI & %B vượt ngưỡng cao", "Combined: ${"%.2f".format(Locale.US, combined)} (đã cắt lên ngưỡng ${"%.2f".format(Locale.US, upper)}) · giá đóng: ${"%,.2f".format(Locale.US, closedCandle.close)} USDT")
        if (priorCombined > lower && combined <= lower)
            fire("chart_alert_mfib_enabled", "MFIB_LOW", 987672, "BTCUSDT · MFI & %B xuống ngưỡng thấp", "Combined: ${"%.2f".format(Locale.US, combined)} (đã cắt xuống ngưỡng ${"%.2f".format(Locale.US, lower)}) · giá đóng: ${"%,.2f".format(Locale.US, closedCandle.close)} USDT")
    }

    // DMI/ADX: alert only on a fresh upward cross of the ADX strength threshold.
    val adx = current.adx
    val priorAdx = previous.adx
    val adxThreshold = prefs.getFloat(chartAlertPrefKey(timeframe, "adx_threshold"), prefs.getFloat("chart_alert_adx_threshold", 20f)).toDouble()
    if (adx != null && priorAdx != null && priorAdx < adxThreshold && adx >= adxThreshold) {
        val plusDi = current.plusDi ?: 0.0
        val minusDi = current.minusDi ?: 0.0
        val direction = if (plusDi > minusDi) "TĂNG (+DI lớn hơn −DI)" else "GIẢM (−DI lớn hơn hoặc bằng +DI)"
        fire("chart_alert_adx_enabled", "ADX_CROSS", 987673, "BTCUSDT · ADX đạt ngưỡng", "ADX: ${"%.1f".format(Locale.US, adx)} / ngưỡng: ${"%.1f".format(Locale.US, adxThreshold)} · +DI: ${"%.1f".format(Locale.US, plusDi)} · −DI: ${"%.1f".format(Locale.US, minusDi)} · hướng: $direction")
    }

    // Bollinger %B: signal on crossing the upper or lower band.
    val bb = current.pricePercentB
    val priorBb = previous.pricePercentB
    if (bb != null && priorBb != null) {
        if (priorBb < 1.0 && bb >= 1.0)
            fire("chart_alert_bollinger_enabled", "BB_UPPER", 987674, "BTCUSDT · Giá vượt Bollinger trên", "Giá đóng: ${"%,.2f".format(Locale.US, closedCandle.close)} USDT · %B: ${"%.2f".format(Locale.US, bb)} (≥ 1.00, vượt dải trên)")
        if (priorBb > 0.0 && bb <= 0.0)
            fire("chart_alert_bollinger_enabled", "BB_LOWER", 987675, "BTCUSDT · Giá xuống dưới Bollinger", "Giá đóng: ${"%,.2f".format(Locale.US, closedCandle.close)} USDT · %B: ${"%.2f".format(Locale.US, bb)} (≤ 0.00, xuống dưới dải dưới)")
    }

    // H1 trend direction change; only evaluate this on a confirmed H1 candle.
    if (timeframe == "1h") {
        val priorDirection = when {
            (previous.plusDi ?: 0.0) > (previous.minusDi ?: 0.0) -> 1
            (previous.minusDi ?: 0.0) > (previous.plusDi ?: 0.0) -> -1
            else -> 0
        }
        val direction = when {
            (current.plusDi ?: 0.0) > (current.minusDi ?: 0.0) -> 1
            (current.minusDi ?: 0.0) > (current.plusDi ?: 0.0) -> -1
            else -> 0
        }
        if (direction != 0 && priorDirection != 0 && direction != priorDirection) {
            val oldLabel = if (priorDirection > 0) "TĂNG" else "GIẢM"
            val label = if (direction > 0) "TĂNG" else "GIẢM"
            fire("chart_alert_h1_enabled", "H1_TREND_$direction", 987676, "BTCUSDT · Xu hướng H1 đổi sang $label", "Xu hướng: $oldLabel → $label · +DI: ${"%.1f".format(Locale.US, current.plusDi ?: 0.0)} · −DI: ${"%.1f".format(Locale.US, current.minusDi ?: 0.0)} · ADX: ${"%.1f".format(Locale.US, current.adx ?: 0.0)}")
        }
    }
}

@Composable
private fun AlertHistoryDialog(entries: List<SavedAlert>, onDismiss: () -> Unit, onClear: () -> Unit) {
    val startOfToday = remember(entries) {
        java.util.Calendar.getInstance().apply {
            set(java.util.Calendar.HOUR_OF_DAY, 0)
            set(java.util.Calendar.MINUTE, 0)
            set(java.util.Calendar.SECOND, 0)
            set(java.util.Calendar.MILLISECOND, 0)
        }.timeInMillis
    }
    val todayCount = entries.count { it.timestamp >= startOfToday }
    val chartCount = entries.count { it.source.contains("Biểu đồ", ignoreCase = true) }
    val rsiCount = entries.count { it.source.contains("RSI", ignoreCase = true) }
    val strategyCount = entries.size - chartCount - rsiCount
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(
            modifier = Modifier.fillMaxWidth(0.94f).fillMaxHeight(0.82f),
            shape = RoundedCornerShape(18.dp),
            color = NPanel
        ) {
            Column(Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("🔔 Lịch sử thông báo", color = Color.White, fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                    TextButton(onClick = onClear) { Text("Xóa") }
                    TextButton(onClick = onDismiss) { Text("Đóng") }
                }
                Text("Lưu trên thiết bị · tối đa 100 thông báo gần nhất", color = NMuted, style = MaterialTheme.typography.bodySmall)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Column(Modifier.weight(1f).background(NBg, RoundedCornerShape(8.dp)).padding(10.dp)) {
                        Text("Hôm nay", color = NMuted, style = MaterialTheme.typography.labelSmall)
                        Text("$todayCount", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                    Column(Modifier.weight(1f).background(NBg, RoundedCornerShape(8.dp)).padding(10.dp)) {
                        Text("Biểu đồ", color = NMuted, style = MaterialTheme.typography.labelSmall)
                        Text("$chartCount", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                    Column(Modifier.weight(1f).background(NBg, RoundedCornerShape(8.dp)).padding(10.dp)) {
                        Text("RSI M15", color = NMuted, style = MaterialTheme.typography.labelSmall)
                        Text("$rsiCount", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                    Column(Modifier.weight(1f).background(NBg, RoundedCornerShape(8.dp)).padding(10.dp)) {
                        Text("Chiến lược", color = NMuted, style = MaterialTheme.typography.labelSmall)
                        Text("$strategyCount", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                }
                Spacer(Modifier.height(10.dp))
                if (entries.isEmpty()) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("Chưa có thông báo được lưu", color = NMuted)
                    }
                } else {
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(entries) { entry ->
                            Column(Modifier.fillMaxWidth().background(NBg, RoundedCornerShape(10.dp)).padding(12.dp)) {
                                Text(entry.title, color = Color.White, fontWeight = FontWeight.SemiBold)
                                Text(entry.body, color = NMuted, style = MaterialTheme.typography.bodyMedium)
                                Text(
                                    SimpleDateFormat("HH:mm:ss · dd/MM/yyyy", Locale.getDefault()).format(Date(entry.timestamp)) +
                                        if (entry.source.isNotBlank()) " · " + entry.source else "",
                                    color = NMuted, style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

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
    var rsiM15Alerts by remember { mutableStateOf(prefs.getBoolean("alert_rsi_m15_enabled", false)) }
    var rsiM15High by remember { mutableFloatStateOf(prefs.getInt("alert_rsi_m15_high", 70).toFloat()) }
    var rsiM15Low by remember { mutableFloatStateOf(prefs.getInt("alert_rsi_m15_low", 30).toFloat()) }
    var mfiBAlerts by remember { mutableStateOf(prefs.getBoolean(chartAlertPrefKey(timeframe, "mfib_enabled"), prefs.getBoolean("chart_alert_mfib_enabled", false))) }
    var mfiBUpper by remember { mutableFloatStateOf(prefs.getFloat(chartAlertPrefKey(timeframe, "mfib_upper"), prefs.getFloat("chart_alert_mfib_upper", 0.8f))) }
    var mfiBLower by remember { mutableFloatStateOf(prefs.getFloat(chartAlertPrefKey(timeframe, "mfib_lower"), prefs.getFloat("chart_alert_mfib_lower", 0.2f))) }
    var adxChartAlerts by remember { mutableStateOf(prefs.getBoolean(chartAlertPrefKey(timeframe, "adx_enabled"), prefs.getBoolean("chart_alert_adx_enabled", false))) }
    var adxChartThreshold by remember { mutableFloatStateOf(prefs.getFloat(chartAlertPrefKey(timeframe, "adx_threshold"), prefs.getFloat("chart_alert_adx_threshold", 20f))) }
    var bollingerChartAlerts by remember { mutableStateOf(prefs.getBoolean(chartAlertPrefKey(timeframe, "bollinger_enabled"), prefs.getBoolean("chart_alert_bollinger_enabled", false))) }
    var h1TrendChartAlerts by remember { mutableStateOf(prefs.getBoolean(chartAlertPrefKey(timeframe, "h1_enabled"), prefs.getBoolean("chart_alert_h1_enabled", false))) }
    var vibration by remember { mutableStateOf(prefs.getBoolean("alert_vibration", true)) }
    var sound by remember { mutableStateOf(prefs.getBoolean("alert_sound", true)) }
    var quietHours by remember { mutableStateOf(prefs.getBoolean("quiet_hours_enabled", false)) }
    var quietStart by remember { mutableIntStateOf(prefs.getInt("quiet_start_hour", 23)) }
    var quietEnd by remember { mutableIntStateOf(prefs.getInt("quiet_end_hour", 7)) }
    var catchUp by remember { mutableStateOf(prefs.getBoolean("alert_catch_up_after_quiet", true)) }
    var alertSettingsExpanded by remember { mutableStateOf(false) }
    var showNotificationHistory by remember { mutableStateOf(false) }
    var notificationHistory by remember { mutableStateOf(readAlertHistory(prefs)) }
    var monitorHeartbeat by remember { mutableStateOf("Đang chờ lần kiểm tra đầu tiên…") }
    var monitorError by remember { mutableStateOf("") }
    var lastProcessedCandle by remember { mutableStateOf("—") }
    var lastEventCount by remember { mutableIntStateOf(0) }
    var state by remember { mutableStateOf(StrategyState.fromJson(prefs.getString("state_json", null))) }
    var m15Ind by remember { mutableStateOf(IndicatorPoint()) }
    var h1Ind by remember { mutableStateOf(IndicatorPoint()) }
    var h1TrendMarks by remember { mutableStateOf<List<H1TrendMark>>(emptyList()) }
    var chartIndicators by remember { mutableStateOf<List<IndicatorPoint>>(emptyList()) }
    var chartVisibleCount by remember { mutableIntStateOf(120) }
    var chartPanBars by remember { mutableIntStateOf(0) }
    var showRsi by remember { mutableStateOf(prefs.getBoolean("chart_show_rsi_percent_b", prefs.getBoolean("chart_show_rsi", true))) }
    var showMfiB by remember { mutableStateOf(prefs.getBoolean("chart_show_mfi_b", prefs.getBoolean("chart_show_rsi", true))) }
    var showAdx by remember { mutableStateOf(prefs.getBoolean("chart_show_adx", true)) }
    var showDi by remember { mutableStateOf(prefs.getBoolean("chart_show_di", true)) }
    var showH1Trend by remember { mutableStateOf(prefs.getBoolean("chart_show_h1", true)) }
    var showBollinger by remember { mutableStateOf(prefs.getBoolean("chart_show_bollinger", true)) }
    var showVolumeProfile by remember { mutableStateOf(prefs.getBoolean("chart_show_volume_profile", true)) }
    var chartSettingsExpanded by remember { mutableStateOf(false) }
    var chartFullscreen by remember { mutableStateOf(false) }
    var socketStatus by remember { mutableStateOf("Đang đồng bộ REST…") }

    LaunchedEffect(timeframe) {
        mfiBAlerts = prefs.getBoolean(chartAlertPrefKey(timeframe, "mfib_enabled"), prefs.getBoolean("chart_alert_mfib_enabled", false))
        mfiBUpper = prefs.getFloat(chartAlertPrefKey(timeframe, "mfib_upper"), prefs.getFloat("chart_alert_mfib_upper", 0.8f))
        mfiBLower = prefs.getFloat(chartAlertPrefKey(timeframe, "mfib_lower"), prefs.getFloat("chart_alert_mfib_lower", 0.2f))
        adxChartAlerts = prefs.getBoolean(chartAlertPrefKey(timeframe, "adx_enabled"), prefs.getBoolean("chart_alert_adx_enabled", false))
        adxChartThreshold = prefs.getFloat(chartAlertPrefKey(timeframe, "adx_threshold"), prefs.getFloat("chart_alert_adx_threshold", 20f))
        bollingerChartAlerts = prefs.getBoolean(chartAlertPrefKey(timeframe, "bollinger_enabled"), prefs.getBoolean("chart_alert_bollinger_enabled", false))
        h1TrendChartAlerts = prefs.getBoolean(chartAlertPrefKey(timeframe, "h1_enabled"), prefs.getBoolean("chart_alert_h1_enabled", false))
    }

    LaunchedEffect(timeframe) {
        chartPanBars = 0
        val mainHandler = Handler(Looper.getMainLooper())
        var socket: WebSocket? = null
        var connected = AtomicBoolean(false)
        var reconnectRequested = AtomicBoolean(false)
        var connectionStartedAt = System.currentTimeMillis()
        try {
            val initial = market.fetchCandles(timeframe, 1500)
            val cache = java.util.TreeMap<Long, Candle>()
            initial.forEach { mergeCandle(cache, it) }
            chart = cache.values.toList()
            var m15Data = if (timeframe == "15m") initial else market.fetchCandles("15m", 1500)
            var h1Data = if (timeframe == "1h") initial else market.fetchCandles("1h", 1500)
            m15Ind = engine.indicatorSeries(m15Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
            val closedH1 = h1Data.filter { it.closed }.sortedBy { it.openTime }
            val h1Series = engine.indicatorSeries(closedH1)
            h1Ind = h1Series.lastOrNull() ?: IndicatorPoint()
            h1TrendMarks = closedH1.mapIndexedNotNull { index, candle ->
                val point = h1Series.getOrNull(index) ?: return@mapIndexedNotNull null
                val plus = point.plusDi ?: return@mapIndexedNotNull null
                val minus = point.minusDi ?: return@mapIndexedNotNull null
                H1TrendMark(candle.openTime, if (plus > minus) 1 else if (minus > plus) -1 else 0, (point.adx ?: 0.0) >= 20.0)
            }
            chartIndicators = engine.indicatorSeries(initial)
            price = market.fetchMarkPrice()
            socketStatus = "REST đồng bộ xong · WebSocket đang kết nối"
            socket = market.connectLive(
                interval = timeframe,
                onCandle = { candle ->
                    mainHandler.post {
                        status = "Dữ liệu live đang hoạt động"
                        cache[candle.openTime] = candle
                        while (cache.size > 1500) cache.pollFirstEntry()
                        val liveCandles = cache.values.toList()
                        chart = liveCandles
                        chartIndicators = engine.indicatorSeries(liveCandles)
                        if (candle.closed) {
                            maybeNotifyChartAlerts(context, prefs, engine, liveCandles, candle, timeframe)
                            if (timeframe == "15m") maybeNotifyRsiM15(context, prefs, engine, liveCandles, candle)
                        }
                        // Keep strategy/status cards based on confirmed candles; the plot may preview the forming candle.
                        val latestClosed = engine.indicatorSeries(liveCandles.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
                        if (timeframe == "15m") m15Ind = latestClosed else h1Ind = latestClosed
                        socketStatus = "WebSocket live · " + SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
                    }
                },
                onMarkPrice = { mark -> mainHandler.post { price = mark; status = "Dữ liệu live đang hoạt động" } },
                onStatus = { message ->
                    if (message.contains("kết nối", true)) connected.set(true)
                    if (message.contains("gián đoạn", true) || message.contains("đã đóng", true)) { connected.set(false); reconnectRequested.set(true) }
                    mainHandler.post { socketStatus = message; status = message }
                }
            )
            var retryDelayMs = 1_000L
            var lastSyncAt = System.currentTimeMillis()
            while (currentCoroutineContext().isActive) {
                delay(1_000)
                val now = System.currentTimeMillis()
                if (!connected.get() && now - connectionStartedAt > 15_000L) reconnectRequested.set(true)
                if (reconnectRequested.get()) {
                    socket?.close(1001, "reconnect")
                    retryDelayMs = (retryDelayMs * 2).coerceAtMost(30_000L)
                    delay(retryDelayMs)
                    try {
                        val reconciled = market.fetchCandles(timeframe, 1500)
                        val otherTimeframe = if (timeframe == "15m") "1h" else "15m"
                        val otherReconciled = market.fetchCandles(otherTimeframe, 500)
                        mainHandler.post {
                            reconciled.forEach { mergeCandle(cache, it) }
                            while (cache.size > 1500) cache.pollFirstEntry()
                            chart = cache.values.toList()
                            chartIndicators = engine.indicatorSeries(cache.values.toList())
                            if (timeframe == "15m") { m15Data = cache.values.toList(); h1Data = otherReconciled }
                            else { h1Data = cache.values.toList(); m15Data = otherReconciled }
                            m15Ind = engine.indicatorSeries(m15Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
                            h1Ind = engine.indicatorSeries(h1Data.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
                        }
                        price = market.fetchMarkPrice()
                        connected = AtomicBoolean(false)
                        reconnectRequested = AtomicBoolean(false)
                        connectionStartedAt = System.currentTimeMillis()
                        socket = market.connectLive(timeframe,
                            onCandle = { c -> mainHandler.post {
                                mergeCandle(cache, c)
                                while (cache.size > 1500) cache.pollFirstEntry()
                                val liveCandles = cache.values.toList()
                                chart = liveCandles
                                chartIndicators = engine.indicatorSeries(liveCandles)
                                if (c.closed) {
                                    maybeNotifyChartAlerts(context, prefs, engine, liveCandles, c, timeframe)
                                    if (timeframe == "15m") maybeNotifyRsiM15(context, prefs, engine, liveCandles, c)
                                }
                                val closed = engine.indicatorSeries(liveCandles.filter { it.closed }).lastOrNull() ?: IndicatorPoint()
                                if (timeframe == "15m") m15Ind = closed else h1Ind = closed
                            } },
                            onMarkPrice = { mark -> mainHandler.post { price = mark } },
                            onStatus = { message ->
                                if (message.contains("kết nối", true)) connected.set(true)
                                if (message.contains("gián đoạn", true) || message.contains("đã đóng", true)) { connected.set(false); reconnectRequested.set(true) }
                                mainHandler.post { socketStatus = message; status = message }
                            })
                        lastSyncAt = System.currentTimeMillis()
                    } catch (e: CancellationException) { throw e }
                    catch (_: Exception) { retryDelayMs = (retryDelayMs * 2).coerceAtMost(30_000L) }
                    continue
                }
                if (connected.get()) retryDelayMs = 1_000L
                if (now - lastSyncAt >= 60_000L) {
                    try {
                        val reconciled = market.fetchCandles(timeframe, 1500)
                        val otherTimeframe = if (timeframe == "15m") "1h" else "15m"
                        val otherReconciled = market.fetchCandles(otherTimeframe, 500)
                        mainHandler.post {
                            reconciled.forEach { mergeCandle(cache, it) }
                            while (cache.size > 1500) cache.pollFirstEntry()
                            chart = cache.values.toList()
                            chartIndicators = engine.indicatorSeries(cache.values.toList())
                            if (timeframe == "15m") { m15Data = cache.values.toList(); h1Data = otherReconciled }
                            else { h1Data = cache.values.toList(); m15Data = otherReconciled }
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
                        lastSyncAt = now
                    } catch (e: CancellationException) { throw e }
                    catch (_: Exception) { socketStatus = "REST đồng bộ lỗi; sẽ thử lại" }
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

    // M15 RSI monitor is independent of chart timeframe. When chart is M15, its single socket is reused;
    // when chart is H1, this effect owns the only M15 socket.
    LaunchedEffect(timeframe) {
        if (timeframe != "1h") return@LaunchedEffect
        val handler = Handler(Looper.getMainLooper())
        val cache = java.util.TreeMap<Long, Candle>()
        var socket: WebSocket? = null
        var connected = AtomicBoolean(false)
        var reconnect = AtomicBoolean(false)
        var startedAt = System.currentTimeMillis()
        var retryMs = 1_000L
        var lastClosedOpen = 0L
        try {
            val initial = market.fetchCandles("15m", 1500)
            initial.forEach { mergeCandle(cache, it) }
            lastClosedOpen = cache.values.filter { it.closed }.maxOfOrNull { it.openTime } ?: 0L
            while (currentCoroutineContext().isActive) {
                if (connected.get()) retryMs = 1_000L
                if (socket == null || reconnect.get() || (!connected.get() && System.currentTimeMillis() - startedAt > 15_000L)) {
                    val hadSocket = socket != null
                    socket?.close(1001, "M15 monitor reconnect")
                    if (hadSocket) {
                        retryMs = (retryMs * 2).coerceAtMost(30_000L)
                        delay(retryMs)
                    }
                    try {
                        val snapshot = market.fetchCandles("15m", 1500)
                        snapshot.forEach { mergeCandle(cache, it) }
                        while (cache.size > 1500) cache.pollFirstEntry()
                        val newest = cache.values.filter { it.closed }.maxByOrNull { it.openTime }
                        if (newest != null && newest.openTime > lastClosedOpen) {
                            maybeNotifyRsiM15(context, prefs, engine, cache.values.toList(), newest)
                            lastClosedOpen = newest.openTime
                        }
                        connected.set(false)
                        reconnect.set(false)
                        startedAt = System.currentTimeMillis()
                        socket = market.connectLive("15m",
                            onCandle = { candle -> handler.post {
                                mergeCandle(cache, candle)
                                while (cache.size > 1500) cache.pollFirstEntry()
                                if (candle.closed && candle.openTime > lastClosedOpen) {
                                    maybeNotifyRsiM15(context, prefs, engine, cache.values.toList(), candle)
                                    lastClosedOpen = candle.openTime
                                }
                            } },
                            onMarkPrice = { },
                            onStatus = { message ->
                                if (message.contains("kết nối", true)) connected.set(true)
                                if (message.contains("gián đoạn", true) || message.contains("đã đóng", true)) {
                                    connected.set(false); reconnect.set(true)
                                }
                                handler.post { if (timeframe == "1h") socketStatus = "RSI M15 · $message" }
                            })
                    } catch (e: CancellationException) { throw e }
                    catch (_: Exception) { retryMs = (retryMs * 2).coerceAtMost(30_000L) }
                }
                delay(1_000)
            }
        } catch (e: CancellationException) { throw e }
        catch (_: Exception) { if (timeframe == "1h") socketStatus = "Giám sát RSI M15 cần đồng bộ lại" }
        finally { socket?.close(1000, "M15 monitor stopped") }
    }

    val shown = if (timeframe == "15m") m15Ind else h1Ind
    if (showNotificationHistory) {
        AlertHistoryDialog(
            entries = notificationHistory,
            onDismiss = { showNotificationHistory = false },
            onClear = {
                prefs.edit().putString("notification_history_json", "[]").apply()
                notificationHistory = emptyList()
            }
        )
    }
    Surface(Modifier.fillMaxSize(), color = NBg) {
        LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("BTCUSDT.P", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = Color.White)
                        Text("USDⓈ-M Perpetual · Chỉ xem · Không đặt lệnh", color = NMuted)
                    }
                    TextButton(onClick = {
                        notificationHistory = readAlertHistory(prefs)
                        showNotificationHistory = true
                    }) {
                        Text("🔔 ${notificationHistory.size}", color = Color.White, style = MaterialTheme.typography.titleMedium)
                    }
                }
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
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("Candlestick · " + timeframe.uppercase(), color = Color.White, fontWeight = FontWeight.SemiBold)
                            Text("Chạm toàn màn hình để mở rộng biểu đồ và chỉ báo", color = NMuted, style = MaterialTheme.typography.labelSmall)
                        }
                        TextButton(onClick = { chartFullscreen = true }) { Text("⛶ Toàn màn hình") }
                    }
                    Spacer(Modifier.height(8.dp))
                    if (timeframe == "15m" && showH1Trend) H1TrendRibbon(h1Ind)
                    LiveCandles(
                        candles = chart, markPrice = price, visibleCount = chartVisibleCount, panBars = chartPanBars, events = state.recentEvents,
                        h1TrendMarks = if (timeframe == "15m" && showH1Trend) h1TrendMarks else emptyList(),
                        showBollinger = showBollinger,
                        showVolumeProfile = showVolumeProfile,
                        onVisibleCountChange = { chartVisibleCount = it },
                        onPanBarsChange = { chartPanBars = it },
                        modifier = Modifier.fillMaxWidth().height(260.dp)
                    )
                    val axisEnd = if (chart.isEmpty()) 0 else (chart.size - chartPanBars).coerceIn(1, chart.size)
                    val axisStart = (axisEnd - chartVisibleCount).coerceAtLeast(0)
                    TimeAxisBar(chart.subList(axisStart, axisEnd))
                    val viewEnd = if (chart.isEmpty()) 0 else (chart.size - chartPanBars).coerceIn(1, chart.size)
                    val viewStart = (viewEnd - chartVisibleCount).coerceAtLeast(0)
                    val visibleCandles = chart.drop(viewStart).take((viewEnd - viewStart).coerceAtLeast(0))
                    val visibleIndicators = chartIndicators.drop(viewStart).take((viewEnd - viewStart).coerceAtLeast(0))
                    if (showMfiB) {
                        Spacer(Modifier.height(10.dp))
                        IndicatorLineChart(
                            title = "MFI & %B [SEIGLERJ]", points = visibleIndicators, valueSelector = { it.mfiScaled },
                            minValue = -0.5, maxValue = 1.5, thresholds = listOf(0.0, 0.5, 1.0),
                            lineColor = Color(0xFFFFD166), modifier = Modifier.fillMaxWidth().height(142.dp),
                            secondarySelectors = listOf({ it.pricePercentB }, { it.mfiBProduct }),
                            thresholdLabels = listOf("0", "0.5", "1"),
                            legend = listOf("MFI scaled", "Price %B", "Combined"),
                            visibleCount = chartVisibleCount,
                            panBars = chartPanBars,
                            onVisibleCountChange = { chartVisibleCount = it },
                            onPanBarsChange = { chartPanBars = it }
                        )
                    }
                    if (showRsi) {
                        Spacer(Modifier.height(10.dp))
                        IndicatorLineChart(
                            title = "RSI %B SIGNAL", points = visibleIndicators, valueSelector = { it.rsiPercentB },
                            minValue = -0.5, maxValue = 1.5, thresholds = listOf(0.0, 0.5, 1.0),
                            lineColor = Color(0xFF9B8AFB), modifier = Modifier.fillMaxWidth().height(120.dp),
                            secondarySelectors = listOf({ it.rsiPercentBSignal }),
                            thresholdLabels = listOf("0", "0.5", "1"), legend = listOf("%B", "Signal"),
                            visibleCount = chartVisibleCount, panBars = chartPanBars,
                            onVisibleCountChange = { chartVisibleCount = it }, onPanBarsChange = { chartPanBars = it }
                        )
                    }
                    if (showAdx) {
                        Spacer(Modifier.height(10.dp))
                        DmiAdxTrendChart(candles = visibleCandles, points = visibleIndicators, showDi = showDi, visibleCount = chartVisibleCount, panBars = chartPanBars, onVisibleCountChange = { chartVisibleCount = it }, onPanBarsChange = { chartPanBars = it }, modifier = Modifier.fillMaxWidth().height(164.dp))
                    }
                    Text("Binance Futures · REST + WebSocket · ${chart.size} nến đã tải (tối đa 1.500)", color = NMuted)
                    Text(socketStatus, color = if (socketStatus.contains("live") || socketStatus.contains("kết nối")) NGreen else NRed, style = MaterialTheme.typography.bodySmall)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Chỉ báo hiển thị", color = Color.White, modifier = Modifier.weight(1f))
                        TextButton(onClick = { chartSettingsExpanded = !chartSettingsExpanded }) { Text(if (chartSettingsExpanded) "Thu gọn" else "Tùy chỉnh") }
                    }
                    if (chartSettingsExpanded) {
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            PreferenceSwitch("MFI & %B [seiglerj]", showMfiB, { showMfiB = it; prefs.edit().putBoolean("chart_show_mfi_b", it).apply() })
                            PreferenceSwitch("RSI %B Signal", showRsi, { showRsi = it; prefs.edit().putBoolean("chart_show_rsi_percent_b", it).apply() })
                            PreferenceSwitch("DMI & ADX Trend", showAdx, { showAdx = it; prefs.edit().putBoolean("chart_show_adx", it).apply() })
                            PreferenceSwitch("+DI / −DI", showDi, { showDi = it; prefs.edit().putBoolean("chart_show_di", it).apply() })
                            PreferenceSwitch("Xu hướng H1", showH1Trend, { showH1Trend = it; prefs.edit().putBoolean("chart_show_h1", it).apply() })
                            PreferenceSwitch("Bollinger Bands (20, 2)", showBollinger, { showBollinger = it; prefs.edit().putBoolean("chart_show_bollinger", it).apply() })
                            PreferenceSwitch("Volume Profile", showVolumeProfile, { showVolumeProfile = it; prefs.edit().putBoolean("chart_show_volume_profile", it).apply() })
                        }
                    }
                }
            }
            if (showMfiB || showAdx) item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    if (showMfiB) StatCard("MFI & %B Combined", shown.mfiBProduct, Modifier.weight(1f))
                    if (showAdx) StatCard("ADX Trend", shown.adx, Modifier.weight(1f))
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
                    Divider(color = Color(0xFF263243))
                    PreferenceSwitch("Cảnh báo RSI M15", rsiM15Alerts, { rsiM15Alerts = it; prefs.edit().putBoolean("alert_rsi_m15_enabled", it).apply() })
                    Divider(color = Color(0xFF263243))
                    Text("CẢNH BÁO RIÊNG THEO BIỂU ĐỒ · ${timeframe.uppercase()}", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("Mỗi mục có công tắc độc lập; chỉ phát cảnh báo sau khi nến của khung đang theo dõi đóng và có chống lặp.", color = NMuted, style = MaterialTheme.typography.bodySmall)
                    PreferenceSwitch("MFI & %B · Combined chạm ngưỡng", mfiBAlerts, { mfiBAlerts = it; prefs.edit().putBoolean(chartAlertPrefKey(timeframe, "mfib_enabled"), it).apply() })
                    Text("Ngưỡng cao: ${"%.2f".format(Locale.US, mfiBUpper)}", color = Color.White)
                    Slider(value = mfiBUpper, onValueChange = { mfiBUpper = it }, valueRange = 0.5f..1.5f, steps = 19, onValueChangeFinished = { prefs.edit().putFloat(chartAlertPrefKey(timeframe, "mfib_upper"), mfiBUpper).apply() })
                    Text("Ngưỡng thấp: ${"%.2f".format(Locale.US, mfiBLower)}", color = Color.White)
                    Slider(value = mfiBLower, onValueChange = { mfiBLower = it }, valueRange = -0.5f..0.5f, steps = 19, onValueChangeFinished = { prefs.edit().putFloat(chartAlertPrefKey(timeframe, "mfib_lower"), mfiBLower).apply() })
                    if (mfiBLower >= mfiBUpper) Text("Ngưỡng thấp phải nhỏ hơn ngưỡng cao.", color = NRed, style = MaterialTheme.typography.bodySmall)
                    PreferenceSwitch("DMI & ADX · ADX vượt ngưỡng", adxChartAlerts, { adxChartAlerts = it; prefs.edit().putBoolean(chartAlertPrefKey(timeframe, "adx_enabled"), it).apply() })
                    Text("Ngưỡng ADX: ${adxChartThreshold.toInt()}", color = Color.White)
                    Slider(value = adxChartThreshold, onValueChange = { adxChartThreshold = it }, valueRange = 10f..50f, steps = 39, onValueChangeFinished = { prefs.edit().putFloat(chartAlertPrefKey(timeframe, "adx_threshold"), adxChartThreshold).apply() })
                    PreferenceSwitch("Bollinger Bands · Giá vượt dải", bollingerChartAlerts, { bollingerChartAlerts = it; prefs.edit().putBoolean(chartAlertPrefKey(timeframe, "bollinger_enabled"), it).apply() })
                    Text("Báo khi %B cắt lên 1 (dải trên) hoặc cắt xuống 0 (dải dưới).", color = NMuted, style = MaterialTheme.typography.bodySmall)
                    PreferenceSwitch("Xu hướng H1 · Đổi TĂNG/GIẢM", h1TrendChartAlerts, { h1TrendChartAlerts = it; prefs.edit().putBoolean(chartAlertPrefKey(timeframe, "h1_enabled"), it).apply() })
                    Text("Chỉ kiểm tra khi nến H1 đóng; dùng +DI/−DI để xác định hướng.", color = NMuted, style = MaterialTheme.typography.bodySmall)
                    Text("Chỉ thông báo khi RSI(14) cắt qua ngưỡng trên/dưới ở nến M15 đã đóng. Không thay đổi tín hiệu chiến lược.", color = NMuted, style = MaterialTheme.typography.bodySmall)
                    Text("Ngưỡng cao: ${rsiM15High.toInt()}", color = Color.White)
                    Slider(value = rsiM15High, onValueChange = { rsiM15High = it }, valueRange = 50f..95f, steps = 44, onValueChangeFinished = { prefs.edit().putInt("alert_rsi_m15_high", rsiM15High.toInt()).apply() })
                    Text("Ngưỡng thấp: ${rsiM15Low.toInt()}", color = Color.White)
                    Slider(value = rsiM15Low, onValueChange = { rsiM15Low = it }, valueRange = 5f..50f, steps = 44, onValueChangeFinished = { prefs.edit().putInt("alert_rsi_m15_low", rsiM15Low.toInt()).apply() })
                    if (rsiM15Low >= rsiM15High) Text("Lưu ý: ngưỡng thấp nên nhỏ hơn ngưỡng cao.", color = NRed, style = MaterialTheme.typography.bodySmall)
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

    if (chartFullscreen) {
        val viewEnd = if (chart.isEmpty()) 0 else (chart.size - chartPanBars).coerceIn(1, chart.size)
        val viewStart = (viewEnd - chartVisibleCount).coerceAtLeast(0)
        val visibleCandles = chart.drop(viewStart).take((viewEnd - viewStart).coerceAtLeast(0))
        val visibleIndicators = chartIndicators.drop(viewStart).take((viewEnd - viewStart).coerceAtLeast(0))
        Dialog(
            onDismissRequest = { chartFullscreen = false },
            properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)
        ) {
            val dialogView = LocalView.current
            val dialogWindow = (dialogView.parent as? DialogWindowProvider)?.window
            DisposableEffect(dialogWindow) {
                if (dialogWindow != null) {
                    WindowCompat.setDecorFitsSystemWindows(dialogWindow, false)
                    val controller = WindowInsetsControllerCompat(dialogWindow, dialogWindow.decorView)
                    controller.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                    controller.hide(WindowInsetsCompat.Type.systemBars())
                }
                onDispose {
                    if (dialogWindow != null) {
                        WindowInsetsControllerCompat(dialogWindow, dialogWindow.decorView).show(WindowInsetsCompat.Type.systemBars())
                    }
                }
            }
            Surface(Modifier.fillMaxSize(), color = NBg) {
                Column(
                    Modifier.fillMaxSize().padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("BTCUSDT.P · LIVE CHART", color = Color.White, fontWeight = FontWeight.Bold)
                            Text(
                                (price?.let { "$" + "%,.2f".format(it) } ?: "—") + " · " + socketStatus,
                                color = if (socketStatus.contains("live", true) || socketStatus.contains("kết nối", true)) NGreen else NMuted,
                                style = MaterialTheme.typography.labelSmall,
                                maxLines = 1
                            )
                        }
                        listOf("15m", "1h").forEach { tf ->
                            FilterChip(
                                selected = timeframe == tf,
                                onClick = { if (timeframe != tf) timeframe = tf },
                                label = { Text(tf.uppercase()) }
                            )
                            Spacer(Modifier.width(4.dp))
                        }
                        TextButton(onClick = { chartFullscreen = false }) { Text("Đóng ✕") }
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Nến hiển thị: $chartVisibleCount", color = NMuted, style = MaterialTheme.typography.labelSmall)
                        Slider(
                            value = chartVisibleCount.toFloat(),
                            onValueChange = { chartVisibleCount = it.toInt().coerceIn(20, 600) },
                            valueRange = 20f..600f,
                            modifier = Modifier.weight(1f)
                        )
                        TextButton(onClick = { chartPanBars = 0; chartVisibleCount = 120 }) { Text("Đặt lại") }
                    }
                    if (timeframe == "15m" && showH1Trend) H1TrendRibbon(h1Ind)
                    LiveCandles(
                        candles = chart, markPrice = price, visibleCount = chartVisibleCount, panBars = chartPanBars, events = state.recentEvents,
                        h1TrendMarks = if (timeframe == "15m" && showH1Trend) h1TrendMarks else emptyList(),
                        showBollinger = showBollinger,
                        showVolumeProfile = showVolumeProfile,
                        onVisibleCountChange = { chartVisibleCount = it },
                        onPanBarsChange = { chartPanBars = it },
                        modifier = Modifier.fillMaxWidth().weight(if ((showRsi || showMfiB) && showAdx) 0.48f else if (showRsi || showMfiB || showAdx) 0.62f else 0.76f)
                    )
                    TimeAxisBar(visibleCandles)
                    if (showMfiB) {
                        IndicatorLineChart(
                            title = "MFI & %B [SEIGLERJ]", points = visibleIndicators, valueSelector = { it.mfiScaled },
                            minValue = -0.5, maxValue = 1.5, thresholds = listOf(0.0, 0.5, 1.0),
                            lineColor = Color(0xFFFFD166), modifier = Modifier.fillMaxWidth().weight(0.18f),
                            secondarySelectors = listOf({ it.pricePercentB }, { it.mfiBProduct }),
                            thresholdLabels = listOf("0", "0.5", "1"), legend = listOf("MFI scaled", "Price %B", "Combined"),
                            visibleCount = chartVisibleCount, panBars = chartPanBars,
                            onVisibleCountChange = { chartVisibleCount = it }, onPanBarsChange = { chartPanBars = it }
                        )
                    }
                    if (showRsi) {
                        IndicatorLineChart(
                            title = "RSI %B SIGNAL", points = visibleIndicators, valueSelector = { it.rsiPercentB },
                            minValue = -0.5, maxValue = 1.5, thresholds = listOf(0.0, 0.5, 1.0),
                            lineColor = Color(0xFF9B8AFB),
                            modifier = Modifier.fillMaxWidth().weight(0.20f),
                            secondarySelectors = listOf({ it.rsiPercentBSignal }),
                            thresholdLabels = listOf("0", "0.5", "1"),
                            legend = listOf("%B", "Signal"),
                            visibleCount = chartVisibleCount,
                            panBars = chartPanBars,
                            onVisibleCountChange = { chartVisibleCount = it },
                            onPanBarsChange = { chartPanBars = it }
                        )
                    }
                    if (showAdx) {
                        DmiAdxTrendChart(candles = visibleCandles, points = visibleIndicators, showDi = showDi, visibleCount = chartVisibleCount, panBars = chartPanBars, onVisibleCountChange = { chartVisibleCount = it }, onPanBarsChange = { chartPanBars = it }, modifier = Modifier.fillMaxWidth().weight(0.24f))
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("REST + WebSocket · ${chart.size}/1.500 nến", color = NMuted, style = MaterialTheme.typography.labelSmall, modifier = Modifier.weight(1f))
                        TextButton(onClick = { showRsi = !showRsi; prefs.edit().putBoolean("chart_show_rsi_percent_b", showRsi).apply() }) { Text(if (showRsi) "Ẩn RSI %B" else "Hiện RSI %B") }
                        TextButton(onClick = { showMfiB = !showMfiB; prefs.edit().putBoolean("chart_show_mfi_b", showMfiB).apply() }) { Text(if (showMfiB) "Ẩn MFI & %B" else "Hiện MFI & %B") }
                        TextButton(onClick = { showAdx = !showAdx; prefs.edit().putBoolean("chart_show_adx", showAdx).apply() }) { Text(if (showAdx) "Ẩn DMI/ADX" else "Hiện DMI/ADX") }
                    }
                }
            }
        }
    }
}

private fun fmt(value: Double?): String = value?.let { "%.2f".format(it) } ?: "—"

@Composable
private fun H1TrendRibbon(indicator: IndicatorPoint) {
    val plus = indicator.plusDi
    val minus = indicator.minusDi
    val adx = indicator.adx
    val direction = when {
        plus == null || minus == null -> "ĐANG TÍNH"
        plus > minus -> "H1 TĂNG"
        minus > plus -> "H1 GIẢM"
        else -> "H1 TRUNG TÍNH"
    }
    val color = when {
        plus == null || minus == null -> NMuted
        adx != null && adx >= 20.0 && plus > minus -> NGreen
        adx != null && adx >= 20.0 && minus > plus -> NRed
        else -> Color(0xFFFFC857)
    }
    Row(
        Modifier.fillMaxWidth().background(NBg, RoundedCornerShape(8.dp)).padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Box(Modifier.width(4.dp).height(22.dp).background(color, RoundedCornerShape(2.dp)))
        Column(Modifier.weight(1f)) {
            Text(direction, color = color, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.labelLarge)
            Text("Xu hướng khung H1 · +DI ${fmt(plus)} / −DI ${fmt(minus)}", color = NMuted, style = MaterialTheme.typography.labelSmall)
        }
        Text("ADX ${fmt(adx)}", color = color, style = MaterialTheme.typography.labelMedium)
    }
}

@Composable
private fun TimeAxisBar(candles: List<Candle>) {
    val format = remember { SimpleDateFormat("MM-dd HH:mm", Locale.getDefault()) }
    val first = candles.firstOrNull()?.openTime
    val middle = candles.getOrNull(candles.size / 2)?.openTime
    val last = candles.lastOrNull()?.openTime
    Row(
        Modifier.fillMaxWidth().background(NBg, RoundedCornerShape(bottomStart = 6.dp, bottomEnd = 6.dp)).padding(horizontal = 4.dp, vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(first?.let { format.format(Date(it)) } ?: "—", color = NMuted, style = MaterialTheme.typography.labelSmall)
        Text(middle?.let { format.format(Date(it)) } ?: "—", color = NMuted, style = MaterialTheme.typography.labelSmall)
        Text(last?.let { format.format(Date(it)) } ?: "—", color = NGreen, style = MaterialTheme.typography.labelSmall)
    }
}

@Composable
private fun IndicatorLineChart(
    title: String,
    points: List<IndicatorPoint>,
    valueSelector: (IndicatorPoint) -> Double?,
    minValue: Double,
    maxValue: Double,
    thresholds: List<Double>,
    lineColor: Color,
    modifier: Modifier = Modifier,
    secondarySelectors: List<(IndicatorPoint) -> Double?> = emptyList(),
    thresholdLabels: List<String> = emptyList(),
    legend: List<String> = emptyList(),
    visibleCount: Int,
    panBars: Int,
    onVisibleCountChange: (Int) -> Unit,
    onPanBarsChange: (Int) -> Unit
) {
    val currentVisibleCount by rememberUpdatedState(visibleCount)
    val currentPanBars by rememberUpdatedState(panBars)
    val latestOnVisibleCountChange by rememberUpdatedState(onVisibleCountChange)
    val latestOnPanBarsChange by rememberUpdatedState(onPanBarsChange)
    val latest = points.lastOrNull()?.let(valueSelector)?.takeIf { it.isFinite() }
    Column(
        modifier.background(NBg, RoundedCornerShape(8.dp)).padding(horizontal = 10.dp, vertical = 8.dp)
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Text(title, color = Color.White, style = MaterialTheme.typography.labelLarge)
            Text(latest?.let { "%.1f".format(Locale.US, it) } ?: "—", color = lineColor, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
        }
        Canvas(
            Modifier.fillMaxWidth().height(82.dp)
                .pointerInput(points.size, visibleCount) {
                    detectTransformGestures { _, _, zoom, _ ->
                        latestOnVisibleCountChange((currentVisibleCount / zoom).toInt().coerceIn(20, 600))
                    }
                }
                .pointerInput(points.size, visibleCount) {
                    detectDragGestures { change, drag ->
                        change.consume()
                        val bars = (drag.x / size.width.coerceAtLeast(1).toFloat() * currentVisibleCount.toFloat()).toInt()
                        latestOnPanBarsChange((currentPanBars + bars).coerceIn(0, 1499))
                    }
                }
        ) {
            if (points.size < 2 || size.width <= 0f || size.height <= 0f) return@Canvas
            val range = (maxValue - minValue).takeIf { it > 0.0 } ?: 1.0
            fun y(value: Double): Float =
                size.height - (((value.coerceIn(minValue, maxValue) - minValue) / range).toFloat() * size.height)
            for (fraction in listOf(0.25f, 0.5f, 0.75f)) {
                val gy = size.height * fraction
                drawLine(Color(0xFF263243), Offset(0f, gy), Offset(size.width, gy), strokeWidth = 1f)
            }
            thresholds.forEach { level ->
                val yy = y(level)
                drawLine(Color(0xFF566579), Offset(0f, yy), Offset(size.width, yy), strokeWidth = 1f)
            }
            val series = listOf(valueSelector) + secondarySelectors
            val colors = listOf(lineColor, NGreen, NRed)
            series.forEachIndexed { seriesIndex, selector ->
                var previous: Offset? = null
                points.forEachIndexed { index, point ->
                    val value = selector(point)
                    val current = if (value == null || value.isNaN() || value.isInfinite()) null else
                        Offset(size.width * index / (points.size - 1).toFloat(), y(value))
                    if (previous != null && current != null) {
                        drawLine(colors[seriesIndex.coerceAtMost(colors.lastIndex)], previous!!, current!!, strokeWidth = 1.8f)
                    }
                    previous = current
                }
            }
        }
        if (legend.isNotEmpty()) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                legend.forEachIndexed { index, item ->
                    val color = listOf(lineColor, NGreen, NRed)[index.coerceAtMost(2)]
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        Box(Modifier.size(width = 10.dp, height = 3.dp).background(color, RoundedCornerShape(2.dp)))
                        Text(item, color = color, style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("%.0f".format(Locale.US, minValue), color = NMuted, style = MaterialTheme.typography.labelSmall)
            if (thresholdLabels.isNotEmpty()) {
                Text("Ngưỡng " + thresholdLabels.joinToString("/"), color = NMuted, style = MaterialTheme.typography.labelSmall)
            } else {
                Text("Nến " + points.size, color = NMuted, style = MaterialTheme.typography.labelSmall)
            }
            Text("%.0f".format(Locale.US, maxValue), color = NMuted, style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
private fun StatCard(label: String, value: Double?, modifier: Modifier = Modifier) {
    Column(modifier.background(NPanel, RoundedCornerShape(12.dp)).padding(14.dp)) {
        Text(label, color = NMuted)
        Text(fmt(value), color = Color.White, style = MaterialTheme.typography.titleLarge)
    }
}

@Composable
private fun LiveCandles(
    candles: List<Candle>, markPrice: Double?, visibleCount: Int, panBars: Int,
    events: List<StrategyEvent>,
    h1TrendMarks: List<H1TrendMark> = emptyList(),
    showBollinger: Boolean = true,
    showVolumeProfile: Boolean = true,
    onVisibleCountChange: (Int) -> Unit, onPanBarsChange: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedOpenTime by remember { mutableStateOf<Long?>(null) }
    val currentVisibleCount by rememberUpdatedState(visibleCount)
    val currentPanBars by rememberUpdatedState(panBars)
    val latestOnVisibleCountChange by rememberUpdatedState(onVisibleCountChange)
    val latestOnPanBarsChange by rememberUpdatedState(onPanBarsChange)
    val allBands = remember(candles) { ChartAnalytics.bollinger(candles) }
    Canvas(
        modifier
            .background(NBg, RoundedCornerShape(8.dp))
            .pointerInput(candles.size, visibleCount) {
                detectTapGestures { point ->
                    if (candles.isNotEmpty()) {
                        val end = (candles.size - currentPanBars).coerceIn(1, candles.size)
                        val start = (end - currentVisibleCount).coerceAtLeast(0)
                        val shown = candles.subList(start, end)
                        val plotWidth = (size.width - 70.dp.toPx()).coerceAtLeast(1f)
                        val index = (point.x / plotWidth * shown.size).toInt().coerceIn(0, shown.lastIndex)
                        selectedOpenTime = shown[index].openTime
                    }
                }
            }
            .pointerInput(candles.size, visibleCount) {
                detectDragGestures { change, drag ->
                    change.consume()
                    val shown = currentVisibleCount.coerceAtLeast(1)
                    val plotWidth = (size.width - 70.dp.toPx()).coerceAtLeast(1f)
                    val bars = (drag.x / plotWidth * shown).toInt()
                    latestOnPanBarsChange((currentPanBars + bars).coerceIn(0, (candles.size - 1).coerceAtLeast(0)))
                }
            }
            .pointerInput(candles.size) {
                detectTransformGestures { _, _, zoom, _ ->
                    latestOnVisibleCountChange((currentVisibleCount / zoom).toInt().coerceIn(20, 600))
                    latestOnPanBarsChange(currentPanBars.coerceIn(0, (candles.size - 1).coerceAtLeast(0)))
                }
            }
    ) {
        if (candles.isEmpty() || size.width <= 0f || size.height <= 0f) return@Canvas
        val end = (candles.size - currentPanBars).coerceIn(1, candles.size)
        val start = (end - currentVisibleCount).coerceAtLeast(0)
        val data = candles.subList(start, end)
        if (data.isEmpty()) return@Canvas

        val density = this.density
        val axisWidth = 70.dp.toPx()
        val plotWidth = (size.width - axisWidth).coerceAtLeast(1f)
        var low = data.minOf { it.low }
        var high = data.maxOf { it.high }
        markPrice?.let { low = minOf(low, it); high = maxOf(high, it) }
        val rawRange = (high - low).takeIf { it > 0.0 } ?: (high * 0.001).coerceAtLeast(1.0)
        val padding = rawRange * 0.04
        low -= padding
        high += padding
        val range = (high - low).takeIf { it > 0 } ?: 1.0
        fun y(price: Double) = size.height - (((price - low) / range).toFloat() * size.height)
        val axisPaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply {
            color = 0xFF91A0B5.toInt(); textSize = 10f * density
            textAlign = AndroidPaint.Align.LEFT
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.NORMAL)
        }
        for (line in 0..4) {
            val gy = size.height * line / 4f
            val gridPrice = high - range * line / 4.0
            drawLine(Color(0xFF263243), Offset(0f, gy), Offset(plotWidth, gy), strokeWidth = 1f)
            drawContext.canvas.nativeCanvas.drawText("%,.1f".format(Locale.US, gridPrice), plotWidth + 5f * density,
                (gy + 3.5f * density).coerceIn(10f * density, size.height - 2f * density), axisPaint)
        }
        val step = plotWidth / data.size
        if (showVolumeProfile) {
            // Estimated OHLCV profile: volume is allocated by price-range overlap, not trade-level prints.
            val profile = ChartAnalytics.volumeProfile(data, low, high, binCount = 24)
            val maxVolume = profile?.bins?.maxOfOrNull { it.volume }?.takeIf { it > 0.0 } ?: 1.0
            val profileMaxWidth = minOf(plotWidth * 0.22f, 72.dp.toPx())
            val profilePaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply { color = 0x553FA9F5 }
            profile?.bins?.forEach { bin ->
                val barWidth = (bin.volume / maxVolume).toFloat() * profileMaxWidth
                val top = y(bin.upperPrice)
                val bottom = y(bin.lowerPrice)
                drawContext.canvas.nativeCanvas.drawRect(plotWidth - barWidth, top, plotWidth, bottom, profilePaint)
            }
            profile?.let {
                drawLine(Color(0xFF4FC3F7), Offset(plotWidth * 0.72f, y(it.pointOfControl)), Offset(plotWidth, y(it.pointOfControl)), strokeWidth = 1.5f)
            }
        }
        // H1 direction ribbon mapped onto M15 candle timestamps; marks use closed H1 candles only.
        if (h1TrendMarks.isNotEmpty()) {
            val trendPaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply {
                textSize = 9f * density
                typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
                textAlign = AndroidPaint.Align.CENTER
            }
            data.forEachIndexed { i, candle ->
                val hour = candle.openTime - candle.openTime % 3_600_000L
                val mark = h1TrendMarks.lastOrNull { it.openTime <= hour }
                if (mark != null) {
                    val x = step * (i + 0.5f)
                    val color = when {
                        mark.direction > 0 && mark.strong -> 0xFF20C997.toInt()
                        mark.direction < 0 && mark.strong -> 0xFFFF5C70.toInt()
                        mark.direction > 0 -> 0xFF8ACFB7.toInt()
                        mark.direction < 0 -> 0xFFFFA3AD.toInt()
                        else -> 0xFFFFC857.toInt()
                    }
                    drawLine(Color(color), Offset(x, 3f * density), Offset(x, 15f * density), strokeWidth = maxOf(2f, step * 0.65f))
                    val prevHour = if (i == 0) Long.MIN_VALUE else data[i - 1].openTime - data[i - 1].openTime % 3_600_000L
                    val prevMark = if (prevHour == Long.MIN_VALUE) null else h1TrendMarks.lastOrNull { it.openTime <= prevHour }
                    if (i == 0 || prevMark?.direction != mark.direction || prevMark?.strong != mark.strong) {
                        val label = when {
                            mark.direction > 0 && mark.strong -> "H1 TĂNG"
                            mark.direction < 0 && mark.strong -> "H1 GIẢM"
                            mark.direction > 0 -> "TĂNG"
                            mark.direction < 0 -> "GIẢM"
                            else -> "SIDE"
                        }
                        trendPaint.color = color
                        drawContext.canvas.nativeCanvas.drawText(label, x, 28f * density, trendPaint)
                    }
                }
            }
        }
        if (showBollinger && data.size >= 2) {
            // Calculate on the full candle cache, then map visible bars by their original index.
            val bbUpper = mutableListOf<Offset>()
            val bbMiddle = mutableListOf<Offset>()
            val bbLower = mutableListOf<Offset>()
            data.indices.forEach { i ->
                val band = allBands.getOrNull(start + i)
                if (band != null) {
                    val x = step * (i + 0.5f)
                    bbUpper += Offset(x, y(band.upper))
                    bbMiddle += Offset(x, y(band.middle))
                    bbLower += Offset(x, y(band.lower))
                }
            }
            for (i in 1 until bbUpper.size) {
                drawLine(Color(0xFF4FC3F7), bbUpper[i - 1], bbUpper[i], strokeWidth = 1.5f)
                drawLine(Color(0xFF9B8AFB), bbMiddle[i - 1], bbMiddle[i], strokeWidth = 1.1f)
                drawLine(Color(0xFF4FC3F7), bbLower[i - 1], bbLower[i], strokeWidth = 1.5f)
            }
        }
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

        // Overlay strategy event labels at their candle/price without changing strategy logic.
        val visibleStartTime = data.first().openTime
        val visibleEndTime = data.last().openTime
        val eventPaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply {
            textSize = 10f * density
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            textAlign = AndroidPaint.Align.CENTER
        }
        events.asSequence()
            .filter { it.candleTime in visibleStartTime..visibleEndTime }
            .sortedBy { it.candleTime }
            .forEach { event ->
                val idx = data.indexOfLast { it.openTime <= event.candleTime }
                if (idx >= 0) {
                    val candle = data[idx]
                    val x = step * (idx + 0.5f)
                    val isLong = event.side == "LONG" || event.kind.contains("LONG", true)
                    val isShort = event.side == "SHORT" || event.kind.contains("SHORT", true)
                    val color = when {
                        isLong -> 0xFF20C997.toInt()
                        isShort -> 0xFFFF647C.toInt()
                        event.kind.contains("TAKE", true) || event.kind.contains("TP", true) -> 0xFFFFC857.toInt()
                        else -> 0xFF9B8AFB.toInt()
                    }
                    val label = when {
                        event.kind.contains("EMERGENCY", true) -> "E-SL"
                        event.kind.contains("SOFT SL", true) -> "S-SL"
                        event.kind.contains("TAKE", true) -> "TP"
                        event.kind.contains("DCA", true) -> "DCA"
                        isLong -> "LONG"
                        isShort -> "SHORT"
                        else -> event.kind.take(8)
                    }
                    val anchorPrice = if (isLong) candle.low else if (isShort) candle.high else event.price
                    val labelY = (y(anchorPrice) + if (isLong) 14f * density else -6f * density)
                        .coerceIn(12f * density, size.height - 4f * density)
                    val labelX = x.coerceIn(4f * density, plotWidth - 4f * density)
                    eventPaint.color = color
                    val bgPaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply { this.color = 0xDD0B1018.toInt() }
                    val width = eventPaint.measureText(label) + 8f * density
                    drawContext.canvas.nativeCanvas.drawRoundRect(
                        labelX - width / 2f, labelY - 11f * density, labelX + width / 2f, labelY + 3f * density,
                        4f * density, 4f * density, bgPaint
                    )
                    drawContext.canvas.nativeCanvas.drawText(label, labelX, labelY, eventPaint)
                }
            }

        markPrice?.let { current ->
            val py = y(current)
            drawLine(Color(0xFFFFC857), Offset(0f, py), Offset(plotWidth, py), strokeWidth = 1.5f)
            val badgePaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFC857.toInt() }
            val priceTextPaint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply {
                color = 0xFF0B1018.toInt(); textSize = 10f * density
                textAlign = AndroidPaint.Align.CENTER; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            }
            val label = "%,.1f".format(Locale.US, current)
            val badgeWidth = axisWidth - 4f * density
            val badgeHeight = 18f * density
            val badgeY = (py - badgeHeight / 2f).coerceIn(0f, size.height - badgeHeight)
            drawContext.canvas.nativeCanvas.drawRoundRect(plotWidth + 2f * density, badgeY, plotWidth + badgeWidth, badgeY + badgeHeight, 3f * density, 3f * density, badgePaint)
            drawContext.canvas.nativeCanvas.drawText(label, plotWidth + badgeWidth / 2f + density, badgeY + 12f * density, priceTextPaint)
        }
    }
}

@Composable
private fun DmiAdxTrendChart(
    candles: List<Candle>, points: List<IndicatorPoint>, showDi: Boolean,
    visibleCount: Int, panBars: Int,
    onVisibleCountChange: (Int) -> Unit, onPanBarsChange: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    val currentVisibleCount by rememberUpdatedState(visibleCount)
    val currentPanBars by rememberUpdatedState(panBars)
    val latestOnVisibleCountChange by rememberUpdatedState(onVisibleCountChange)
    val latestOnPanBarsChange by rememberUpdatedState(onPanBarsChange)
    val latest = points.lastOrNull()
    val priorAdx = points.getOrNull(points.lastIndex - 1)?.adx
    val rising = latest?.adx != null && priorAdx != null && latest.adx!! >= priorAdx
    val trendColor = when {
        latest?.adx != null && latest.adx >= 20.0 && rising && (latest.plusDi ?: 0.0) > (latest.minusDi ?: 0.0) -> NGreen
        latest?.adx != null && latest.adx >= 20.0 && rising && (latest.minusDi ?: 0.0) > (latest.plusDi ?: 0.0) -> NRed
        else -> Color(0xFFFFC857)
    }
    Column(modifier.background(NBg, RoundedCornerShape(8.dp)).padding(horizontal = 10.dp, vertical = 8.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Text("DMI & ADX TREND", color = Color.White, style = MaterialTheme.typography.labelLarge)
            Text("ADX " + fmt(latest?.adx) + " · +DI " + fmt(latest?.plusDi) + " · −DI " + fmt(latest?.minusDi), color = trendColor, style = MaterialTheme.typography.labelSmall, maxLines = 1)
        }
        Canvas(
            Modifier.fillMaxWidth().weight(1f)
                .pointerInput(points.size, visibleCount) {
                    detectTransformGestures { _, _, zoom, _ ->
                        latestOnVisibleCountChange((currentVisibleCount / zoom).toInt().coerceIn(20, 600))
                    }
                }
                .pointerInput(points.size, visibleCount) {
                    detectDragGestures { change, drag ->
                        change.consume()
                        val bars = (drag.x / size.width.coerceAtLeast(1).toFloat() * currentVisibleCount.toFloat()).toInt()
                        latestOnPanBarsChange((currentPanBars + bars).coerceIn(0, 1499))
                    }
                }
        ) {
            if (points.isEmpty() || size.width <= 0f || size.height <= 0f) return@Canvas
            val n = minOf(points.size, candles.size)
            if (n == 0) return@Canvas
            val ps = points.takeLast(n); val cs = candles.takeLast(n)
            val left = 2f * density; val right = size.width - 2f * density
            val top = 5f * density; val bottom = size.height - 4f * density
            val h = (bottom - top).coerceAtLeast(1f)
            fun y(v: Double) = bottom - (v.coerceIn(0.0, 100.0) / 100.0).toFloat() * h
            for (level in listOf(20.0, 40.0, 60.0, 80.0)) drawLine(Color(0xFF263243), Offset(left, y(level)), Offset(right, y(level)), strokeWidth = 1f)
            drawLine(Color(0xFFFFC857), Offset(left, y(20.0)), Offset(right, y(20.0)), strokeWidth = 1.3f)
            val step = (right - left) / n; val barWidth = (step * 0.62f).coerceAtLeast(1f)
            val paint = AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG)
            ps.forEachIndexed { i, point ->
                val adx = point.adx
                if (adx != null && adx.isFinite()) {
                    val prev = ps.getOrNull(i - 1)?.adx; val risingNow = prev != null && adx >= prev
                    val plus = point.plusDi ?: 0.0; val minus = point.minusDi ?: 0.0; val candle = cs[i]
                    val up = plus > minus && adx >= 20.0 && risingNow && candle.close > candle.open
                    val down = minus > plus && adx >= 20.0 && risingNow && candle.close < candle.open
                    val color = when { risingNow && plus > minus && adx >= 20.0 -> NGreen; risingNow && minus > plus && adx >= 20.0 -> NRed; else -> Color(0xFFFFC857) }
                    if (up || down) drawRect(color.copy(alpha = 0.08f), Offset(left + step * i, top), androidx.compose.ui.geometry.Size(step + 1f, h))
                    paint.color = color.toArgb(); val x = left + step * (i + 0.5f)
                    drawContext.canvas.nativeCanvas.drawRect(x - barWidth / 2f, y(adx), x + barWidth / 2f, bottom, paint)
                }
            }
            if (showDi) {
                fun diLine(selector: (IndicatorPoint) -> Double?, color: Color) {
                    var previous: Offset? = null
                    ps.forEachIndexed { i, point -> val v = selector(point); if (v != null && v.isFinite()) {
                        val current = Offset(left + step * (i + 0.5f), y(v)); previous?.let { drawLine(color, it, current, strokeWidth = 1.8f * density) }; previous = current
                    } else previous = null }
                }
                diLine({ it.plusDi }, Color(0xFF4DA3FF)); diLine({ it.minusDi }, Color(0xFFE879F9))
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("ADX histogram", color = Color(0xFFFFC857), style = MaterialTheme.typography.labelSmall)
            if (showDi) { Text("+DI", color = Color(0xFF4DA3FF), style = MaterialTheme.typography.labelSmall); Text("−DI", color = Color(0xFFE879F9), style = MaterialTheme.typography.labelSmall) }
            Text("Tăng / Giảm / Trung tính", color = NMuted, style = MaterialTheme.typography.labelSmall)
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
