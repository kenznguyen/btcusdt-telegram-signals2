package com.kenznguyen.btclivealerts

import android.app.Notification
import android.app.NotificationChannel
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

                        // Evaluate chart alerts in the foreground service too, so they do not
                        // depend on which timeframe the user currently has open on screen.
                        closed.lastOrNull()?.let { latest ->
                            maybeNotifyChartAlerts(this@StrategyMonitorService, prefs, engine, m15, latest, "15m")
                            maybeNotifyRsiM15(this@StrategyMonitorService, prefs, engine, m15, latest)
                        }
                        h1.filter { it.closed }.maxByOrNull { it.openTime }?.let { latest ->
                            maybeNotifyChartAlerts(this@StrategyMonitorService, prefs, engine, h1, latest, "1h")
                        }

                        var state = StrategyState.fromJson(prefs.getString("state_json", null))
                        if (state.lastProcessedOpenTime == 0L && closed.size >= 2) {
                            state = state.copy(lastProcessedOpenTime = closed[closed.size - 2].openTime)
                        }
                        val result = engine.processClosedCandles(m15, h1, state)
                        state = result.first
                        val lastClosedOpen = closed.lastOrNull()?.openTime ?: 0L
                        prefs.edit()
                            .putString("state_json", state.toJson())
                            .putLong("monitor_last_success_ms", System.currentTimeMillis())
                            .putLong("monitor_last_candle_open", lastClosedOpen)
                            .putInt("monitor_last_event_count", result.second.size)
                            .putString("monitor_last_error", "")
                            .apply()
                        val enabled = prefs.getBoolean("alerts_enabled", true)
                        if (enabled) result.second.forEach { event ->
                            val key = event.dedupeKey + ":" + (event.side ?: "FLAT")
                            if (!prefs.getBoolean("alert_" + alertPreferenceKey(event.kind), true)) return@forEach
                            if (event.side == "LONG" && !prefs.getBoolean("alert_long", true)) return@forEach
                            if (event.side == "SHORT" && !prefs.getBoolean("alert_short", true)) return@forEach
                            val sent = prefs.getStringSet("notified_event_keys", emptySet())?.toMutableSet() ?: mutableSetOf()
                            if (key in sent) return@forEach
                            val title = "BTCUSDT.P · " + event.kind
                            val body = (event.side ?: "FLAT") + " · Giá " + "%,.2f".format(event.price) + " · " + event.note
                            if (isQuietHours(prefs)) {
                                if (prefs.getBoolean("alert_catch_up_after_quiet", true)) {
                                    val queue = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
                                    queue.add(key + "|" + title + "|" + body)
                                    prefs.edit().putStringSet("quiet_alert_queue", queue).apply()
                                }
                                return@forEach
                            }
                            postAlert(key, title, body, prefs)
                            sent.add(key)
                            prefs.edit().putStringSet("notified_event_keys", sent.toList().takeLast(100).toSet()).apply()
                        }
                        if (enabled && !isQuietHours(prefs) && prefs.getBoolean("alert_catch_up_after_quiet", true)) {
                            val queue = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
                            if (queue.isNotEmpty()) {
                                val sent = prefs.getStringSet("notified_event_keys", emptySet())?.toMutableSet() ?: mutableSetOf()
                                queue.toList().forEach { item ->
                                    val parts = item.split("|", limit = 3)
                                    if (parts.size == 3 && parts[0] !in sent) {
                                        postAlert(parts[0], "Cảnh báo gửi bù · " + parts[1], parts[2], prefs)
                                        sent.add(parts[0])
                                    }
                                }
                                prefs.edit().putStringSet("quiet_alert_queue", emptySet()).putStringSet("notified_event_keys", sent.toList().takeLast(100).toSet()).apply()
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

    private fun postAlert(key: String, title: String, body: String, prefs: android.content.SharedPreferences) {
        // Persist the event independently from Android notification permission.
        synchronized(prefs) {
            val history = runCatching { JSONArray(prefs.getString("notification_history_json", "[]")) }.getOrDefault(JSONArray())
            val updated = JSONArray().put(JSONObject().put("title", title).put("body", body)
                .put("timestamp", System.currentTimeMillis()).put("source", "Chiến lược"))
            for (i in 0 until minOf(history.length(), 99)) {
                updated.put(history.getJSONObject(history.length() - 1 - i))
            }
            prefs.edit().putString("notification_history_json", updated.toString()).apply()
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

    override fun onDestroy() {
        monitorJob?.cancel()
        scope.cancel()
        super.onDestroy()
    }
}
