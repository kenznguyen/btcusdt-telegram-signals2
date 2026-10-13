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
                        val closed = m15.filter { it.closed }
                        val prefs = getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE)
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
                            val body = (event.side ?: "FLAT") + " · Giá " + "%,.2f".format(event.price) + " · " + event.note
                            val notification = NotificationCompat.Builder(this@StrategyMonitorService, "strategy_alerts")
                                .setSmallIcon(android.R.drawable.ic_dialog_info)
                                .setContentTitle("BTCUSDT.P · " + event.kind)
                                .setContentText(body)
                                .setStyle(NotificationCompat.BigTextStyle().bigText(body))
                                .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true).build()
                            (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).notify(event.dedupeKey.hashCode(), notification)
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
