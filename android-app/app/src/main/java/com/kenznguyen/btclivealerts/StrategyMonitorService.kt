package com.kenznguyen.btclivealerts

import android.app.Notification
import android.app.NotificationChannel
import android.app.PendingIntent
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import org.json.JSONArray
import org.json.JSONObject

class StrategyMonitorService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var monitorJob: Job? = null
    private val market by lazy { MarketEngine() }
    private val engine by lazy { StrategyEngine() }

    override fun onCreate() {
        super.onCreate()
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(NotificationChannel("monitor_status", "Market monitoring", NotificationManager.IMPORTANCE_LOW))
        manager.createNotificationChannel(NotificationChannel("strategy_alerts", "Strategy alerts", NotificationManager.IMPORTANCE_HIGH))
        startForeground(1001, ongoing("Đang khởi động theo dõi BTCUSDT…"))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (monitorJob?.isActive != true) {
            monitorJob = scope.launch {
                while (isActive) {
                    try {
                        val m15 = market.fetchCandles("15m", 500)
                        val h1 = market.fetchCandles("1h", 500)
                        val closed = m15.filter { it.closed }.sortedBy { it.openTime }
                        val prefs = getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE)
                        // Retry chart alerts queued while Android notification permission was disabled.
                        drainPendingChartNotifications(this@StrategyMonitorService, prefs)

                        // Evaluate every newly closed candle in the background, not only the
                        // latest one, so reconnect/network gaps do not silently skip chart signals.
                        processChartAlerts("15m", m15, prefs)
                        processChartAlerts("1h", h1, prefs)

                        var state = StrategyState.fromJson(prefs.getString("state_json", null))
                        if (state.lastProcessedOpenTime == 0L && closed.size >= 2) {
                            state = state.copy(lastProcessedOpenTime = closed[closed.size - 2].openTime)
                        }
                        val result = engine.processClosedCandles(m15, h1, state)
                        state = result.first
                        val lastClosedOpen = closed.lastOrNull()?.openTime ?: 0L
                        val pendingKey = "pending_strategy_events_json"
                        val pending = runCatching {
                            JSONArray(prefs.getString(pendingKey, "[]"))
                        }.getOrElse {
                            throw IllegalStateException("Hàng đợi cảnh báo bị lỗi; giữ nguyên trạng thái để tránh mất sự kiện.", it)
                        }
                        val queuedKeys = (0 until pending.length()).mapNotNull { pending.optJSONObject(it)?.optString("key") }.toMutableSet()
                        result.second.forEach { event ->
                            val key = event.dedupeKey + ":" + (event.side ?: "FLAT")
                            if (queuedKeys.add(key)) {
                                pending.put(JSONObject()
                                    .put("key", key)
                                    .put("kind", event.kind)
                                    .put("side", event.side ?: JSONObject.NULL)
                                    .put("price", event.price)
                                    .put("candleTime", event.candleTime)
                                    .put("note", event.note))
                            }
                        }
                        // Persist state and pending notifications together before advancing the
                        // durable cursor. After a process restart, unsent events are drained below.
                        check(prefs.edit()
                            .putString("state_json", state.toJson())
                            .putString(pendingKey, pending.toString())
                            .putLong("monitor_last_candle_open", lastClosedOpen)
                            .putInt("monitor_last_event_count", result.second.size)
                            .putString("monitor_last_error", "")
                            .commit()) { "Không lưu được trạng thái chiến lược/hàng đợi cảnh báo." }

                        val enabled = prefs.getBoolean("alerts_enabled", true)
                        val sent = prefs.getStringSet("notified_event_keys", emptySet())?.toMutableSet() ?: mutableSetOf()
                        val remaining = JSONArray()
                        for (i in 0 until pending.length()) {
                            val item = pending.optJSONObject(i) ?: continue
                            val key = item.optString("key")
                            val kind = item.optString("kind")
                            val side = item.optString("side").takeUnless { it == "null" || it.isBlank() }
                            if (key.isBlank() || key in sent) continue
                            if (!enabled ||
                                !prefs.getBoolean("alert_" + alertPreferenceKey(kind), true) ||
                                (side == "LONG" && !prefs.getBoolean("alert_long", true)) ||
                                (side == "SHORT" && !prefs.getBoolean("alert_short", true))
                            ) continue
                            val title = "BTCUSDT.P · " + kind
                            val body = (side ?: "FLAT") + " · Giá " + "%,.2f".format(item.optDouble("price")) + " · " + item.optString("note")
                            if (isQuietHours(prefs)) {
                                if (prefs.getBoolean("alert_catch_up_after_quiet", true)) {
                                    val quiet = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
                                    quiet.add(key + "|" + title + "|" + body)
                                    prefs.edit().putStringSet("quiet_alert_queue", quiet).commit()
                                }
                                continue
                            }
                            postAlert(key, title, body, prefs)
                            sent.add(key)
                        }
                        prefs.edit()
                            .putString(pendingKey, remaining.toString())
                            .putStringSet("notified_event_keys", sent.toList().takeLast(500).toSet())
                            .putLong("monitor_last_success_ms", System.currentTimeMillis())
                            .commit()

                        if (enabled && !isQuietHours(prefs) && prefs.getBoolean("alert_catch_up_after_quiet", true)) {
                            val quiet = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
                            if (quiet.isNotEmpty()) {
                                quiet.toList().forEach { item ->
                                    val parts = item.split("|", limit = 3)
                                    if (parts.size == 3 && parts[0] !in sent) {
                                        postAlert(parts[0], "Cảnh báo gửi bù · " + parts[1], parts[2], prefs)
                                        sent.add(parts[0])
                                    }
                                }
                                prefs.edit().putStringSet("quiet_alert_queue", emptySet())
                                    .putStringSet("notified_event_keys", sent.toList().takeLast(500).toSet()).commit()
                            }
                        }

                        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                            .notify(1001, ongoing("Đang theo dõi · " + SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())))
                    } catch (e: Exception) {
                        getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE).edit()
                            .putLong("monitor_last_attempt_ms", System.currentTimeMillis())
                            .putString("monitor_last_error", e.message ?: e.javaClass.simpleName)
                            .apply()
                        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                            .notify(1001, ongoing("Lỗi mạng; sẽ thử lại: " + (e.message ?: "không rõ")))
                    }
                    delay(15_000)
                }
            }
        }
        return START_STICKY
    }

    private fun processChartAlerts(
        timeframe: String,
        candles: List<Candle>,
        prefs: android.content.SharedPreferences
    ) {
        val closed = candles.filter { it.closed }.sortedBy { it.openTime }
        if (closed.isEmpty()) return
        val cursorKey = "chart_alert_monitor_last_$timeframe"
        var cursor = prefs.getLong(cursorKey, Long.MIN_VALUE)
        if (cursor == Long.MIN_VALUE) {
            // Start from the prior candle so the most recent close is checked once,
            // without replaying hundreds of historical alerts on first launch.
            cursor = closed.getOrNull(closed.lastIndex - 1)?.openTime ?: closed.last().openTime
            prefs.edit().putLong(cursorKey, cursor).apply()
        }
        for (candle in closed) {
            if (candle.openTime <= cursor) continue
            val prefix = closed.takeWhile { it.openTime <= candle.openTime }
            maybeNotifyChartAlerts(this, prefs, engine, prefix, candle, timeframe)
            prefs.edit().putLong(cursorKey, candle.openTime).apply()
            cursor = candle.openTime
        }
    }

    private fun postAlert(key: String, title: String, body: String, prefs: android.content.SharedPreferences) {
        // Persist the event independently from Android notification permission.
        synchronized(prefs) {
            val history = runCatching { JSONArray(prefs.getString("notification_history_json", "[]")) }.getOrDefault(JSONArray())
            val alreadyRecorded = (0 until history.length()).any { index ->
                history.optJSONObject(index)?.optString("key") == key
            }
            if (!alreadyRecorded) {
                val updated = JSONArray().put(JSONObject().put("key", key).put("title", title).put("body", body)
                    .put("timestamp", System.currentTimeMillis()).put("source", "Chiến lược"))
                for (i in (history.length() - 1) downTo 0) {
                    if (updated.length() >= 100) break
                    updated.put(history.getJSONObject(i))
                }
                prefs.edit().putString("notification_history_json", updated.toString()).commit()
            }
        }

        val builder = NotificationCompat.Builder(this, "strategy_alerts").setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title).setContentText(body).setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true)
        if (prefs.getBoolean("alert_vibration", true)) builder.setVibrate(longArrayOf(0, 250, 120, 250)) else builder.setVibrate(longArrayOf(0))
        if (!prefs.getBoolean("alert_sound", true)) builder.setSilent(true)
        try {
            (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                .notify(key.hashCode() and 0x7fffffff, builder.build())
        } catch (_: SecurityException) {
            // Keep the event in history; the monitor loop still records its dedupe key.
        }
    }
    private fun alertPreferenceKey(kind: String): String = when {
        kind.contains("ENTRY") -> "entry"
        kind == "DCA" -> "dca"
        kind.contains("TAKE PROFIT") -> "take_profit"
        kind.contains("SOFT SL") -> "soft_sl"
        kind.contains("EMERGENCY SL") -> "emergency_sl"
        else -> "other"
    }

    private fun isQuietHours(prefs: android.content.SharedPreferences): Boolean {
        if (!prefs.getBoolean("quiet_hours_enabled", false)) return false
        val start = prefs.getInt("quiet_start_hour", 23)
        val end = prefs.getInt("quiet_end_hour", 7)
        val hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY)
        return if (start == end) true else if (start < end) hour >= start && hour < end else hour >= start || hour < end
    }
    private fun ongoing(text: String): Notification =
        NotificationCompat.Builder(this, "monitor_status")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setContentTitle("BTCUSDT Strategy Monitor")
            .setContentText(text)
            .setOngoing(true).setPriority(NotificationCompat.PRIORITY_LOW).build()

    override fun onBind(intent: Intent?): IBinder? = null

    /**
     * Android 15 limits dataSync foreground services to six hours per 24-hour period.
     * Stop cleanly when the OS calls this callback; otherwise Android can crash the process.
     * The UI can restart monitoring when the user returns to the app.
     */
    override fun onTimeout(startId: Int, fgsType: Int) {
        val prefs = getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE)
        prefs.edit()
            .putLong("monitor_timeout_ms", System.currentTimeMillis())
            .putString("monitor_last_error", "Android đã dừng dịch vụ dataSync do giới hạn thời gian; mở lại ứng dụng để tiếp tục theo dõi.")
            .apply()
        monitorJob?.cancel()

        // Keep the timeout visible after the foreground service stops. Tapping this
        // notification opens the app, whose Activity starts the monitor again.
        val restartIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 1002, restartIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val warning = NotificationCompat.Builder(this, "monitor_status")
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("Theo dõi BTCUSDT đã tạm dừng")
            .setContentText("Android giới hạn thời gian chạy nền. Mở ứng dụng để khởi động lại.")
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "Android đã dừng dịch vụ theo dõi do giới hạn thời gian chạy nền. Chạm để mở ứng dụng và khởi động lại theo dõi."
            ))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setOngoing(false)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()
        try { manager.notify(1002, warning) } catch (_: SecurityException) { }
        stopSelf(startId)
    }

    override fun onDestroy() {
        monitorJob?.cancel()
        scope.cancel()
        super.onDestroy()
    }
}
