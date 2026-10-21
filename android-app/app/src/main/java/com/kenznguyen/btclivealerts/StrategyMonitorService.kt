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
    @Volatile private var orderBookEngine: OrderBookEngine? = null

    override fun onCreate() {
        super.onCreate()
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(NotificationChannel("monitor_status", "Market monitoring", NotificationManager.IMPORTANCE_LOW))
        manager.createNotificationChannel(NotificationChannel("strategy_alerts", "Strategy alerts", NotificationManager.IMPORTANCE_HIGH))
        startForeground(1001, ongoing("Đang khởi động theo dõi BTCUSDT…"))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (orderBookEngine == null) {
            synchronized(this) {
                if (orderBookEngine == null) {
                    orderBookEngine = OrderBookEngine(
                        onMetrics = { metrics ->
                            val json = JSONObject()
                                .put("bestBid", metrics.bestBid)
                                .put("bestAsk", metrics.bestAsk)
                                .put("spreadBps", metrics.spreadBps)
                                .put("bidDepth", metrics.bidDepth)
                                .put("askDepth", metrics.askDepth)
                                .put("imbalance", metrics.imbalance)
                                .put("weightedImbalance", metrics.weightedImbalance)
                                .put("updateId", metrics.updateId)
                                .put("updatedAtMs", metrics.updatedAtMs)
                                .put("synchronized", metrics.synchronized)
                            getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE).edit()
                                .putString("orderbook_metrics_json", json.toString())
                                .putLong("orderbook_last_update_ms", metrics.updatedAtMs)
                                .putString("orderbook_status", "Đã đồng bộ")
                                .apply()
                        },
                        onStatus = { status ->
                            getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE).edit()
                                .putString("orderbook_status", status)
                                .apply()
                        }
                    ).also { it.start() }
                }
            }
        }
        if (monitorJob?.isActive != true) {
            monitorJob = scope.launch {
                while (isActive) {
                    try {
                        val m15 = market.fetchCandles("15m", 500)
                        val h1 = market.fetchCandles("1h", 500)
                        val closed = m15.filter { it.closed }.sortedBy { it.openTime }
                        val prefs = getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE)
                        updateMultiStreamSignal(m15, h1, prefs)

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
                        // Do not advance the durable strategy cursor until its emitted events
                        // have been persisted/queued. This avoids losing signals on process death.
                        prefs.edit()
                            .putLong("monitor_last_candle_open", lastClosedOpen)
                            .putLong("monitor_last_candle_close_ms", if (lastClosedOpen > 0L) lastClosedOpen + 15L * 60_000L else 0L)
                            .putLong("monitor_last_candle_processed_at_ms", System.currentTimeMillis())
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
                            val candleLabel = SimpleDateFormat("HH:mm dd/MM", Locale.getDefault()).format(Date(event.candleTime))
                            val body = (event.side ?: "FLAT") + " · Nến M15 mở " + candleLabel + " · Giá " + "%,.2f".format(event.price) + " · " + event.note
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

                        prefs.edit()
                            .putString("state_json", state.toJson())
                            .putLong("monitor_last_success_ms", System.currentTimeMillis())
                            .apply()

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
    private fun updateMultiStreamSignal(
        m15: List<Candle>,
        h1: List<Candle>,
        prefs: android.content.SharedPreferences
    ) {
        val closedM15 = m15.filter { it.closed }.sortedBy { it.openTime }
        val closedH1 = h1.filter { it.closed }.sortedBy { it.openTime }
        if (closedM15.size < 32 || closedH1.size < 32) return

        // BUY/SELL starts only from the exact closed-candle entry rules in StrategyEngine.
        // The order book is a mandatory directional confirmation filter, not an independent entry trigger.
        val strategyCandidate = engine.latestClosedEntryCandidate(closedM15, closedH1)
        val technicalScore = when (strategyCandidate) { "BUY" -> 1.0; "SELL" -> -1.0; else -> 0.0 }
        val technicalConfidence = if (strategyCandidate != null) 1.0 else 0.0

        val book = try {
            val json = JSONObject(prefs.getString("orderbook_metrics_json", null) ?: "")
            OrderBookMetrics(
                bestBid = json.getDouble("bestBid"),
                bestAsk = json.getDouble("bestAsk"),
                spreadBps = json.getDouble("spreadBps"),
                bidDepth = json.getDouble("bidDepth"),
                askDepth = json.getDouble("askDepth"),
                imbalance = json.getDouble("imbalance"),
                weightedImbalance = json.getDouble("weightedImbalance"),
                updateId = json.getLong("updateId"),
                updatedAtMs = json.getLong("updatedAtMs"),
                synchronized = json.optBoolean("synchronized", false)
            )
        } catch (_: Exception) { null }

        val evaluatedAt = System.currentTimeMillis()
        val result = MultiStreamSignalEngine().evaluate(
            TechnicalSignalInput(technicalScore, technicalConfidence, closedM15.last().openTime + 15L * 60_000L - 1L, "M15+H1"),
            book,
            evaluatedAt
        )
        val bookAgrees = when (strategyCandidate) {
            "BUY" -> result.orderBookScore != null && result.orderBookScore > 0.0
            "SELL" -> result.orderBookScore != null && result.orderBookScore < 0.0
            else -> false
        }
        val finalSignal = if (strategyCandidate != null && result.dataComplete && bookAgrees && result.signal == strategyCandidate) {
            strategyCandidate
        } else {
            "WAIT"
        }
        val finalReason = when {
            strategyCandidate == null -> "Chưa có điều kiện vào lệnh M15/H1 theo StrategyEngine"
            !result.dataComplete -> "WAIT: Order Book chưa đồng bộ hoặc dữ liệu đã cũ"
            !bookAgrees -> "WAIT: Order Book không xác nhận cùng hướng với tín hiệu chiến lược"
            result.signal != strategyCandidate -> "WAIT: điểm hợp nhất chưa đạt ngưỡng xác nhận"
            else -> "Đã xác nhận: điều kiện StrategyEngine + Order Book cùng hướng"
        }
        // Separate provisional alert: never changes the confirmed BUY/SELL card or strategy state.
        val earlyCandidate = engine.earlyEntryCandidate(m15, h1)
        val earlyAgrees = when (earlyCandidate) {
            "EARLY BUY" -> result.orderBookScore != null && result.orderBookScore > 0.0
            "EARLY SELL" -> result.orderBookScore != null && result.orderBookScore < 0.0
            else -> false
        }
        if (earlyCandidate != null && result.dataComplete && earlyAgrees) {
            val candleOpen = m15.filterNot { it.closed }.maxByOrNull { it.openTime }?.openTime ?: 0L
            val alertKey = "early_warning:$earlyCandidate:$candleOpen"
            val sent = prefs.getString("early_warning_last_key", "")
            if (candleOpen > 0L && sent != alertKey && prefs.getBoolean("early_warning_enabled", true)) {
                val time = SimpleDateFormat("HH:mm:ss dd/MM", Locale.getDefault()).format(Date(evaluatedAt))
                postAlert(alertKey, "BTCUSDT · $earlyCandidate (sơ bộ)",
                    "Cảnh báo sớm, chưa phải tín hiệu xác nhận · M15 đang hình thành · RSI gần ngưỡng vào · H1 đã lọc xu hướng · Order Book cùng hướng · ghi nhận $time", prefs)
                prefs.edit().putString("early_warning_last_key", alertKey).apply()
            }
        }

        val output = JSONObject()
            .put("signal", finalSignal)
            .put("strategyCandidate", strategyCandidate ?: JSONObject.NULL)
            .put("score", result.score)
            .put("technicalScore", technicalScore)
            .put("orderBookScore", result.orderBookScore ?: JSONObject.NULL)
            .put("confidence", result.confidence)
            .put("dataComplete", result.dataComplete)
            .put("orderBookAgrees", bookAgrees)
            .put("reason", finalReason)
            .put("evaluatedAtMs", evaluatedAt)
            .put("m15CandleOpenTimeMs", closedM15.last().openTime)
            .put("m15CandleCloseTimeMs", closedM15.last().openTime + 15L * 60_000L)
            .put("h1CandleOpenTimeMs", closedH1.lastOrNull()?.openTime ?: 0L)
            .put("h1CandleCloseTimeMs", closedH1.lastOrNull()?.let { it.openTime + 60L * 60_000L } ?: 0L)
            .put("timeframe", "M15+H1")
            .put("entryFrequencyAudit", engine.entryFrequencyAudit(m15, h1))
            .put("confirmationGate", JSONObject()
                .put("technicalCandidateExists", strategyCandidate != null)
                .put("orderBookPresent", book != null)
                .put("orderBookSynchronized", book?.synchronized ?: false)
                .put("orderBookAgeMs", book?.let { evaluatedAt - it.updatedAtMs } ?: JSONObject.NULL)
                .put("orderBookAgrees", bookAgrees)
                .put("dataComplete", result.dataComplete)
                .put("blockReason", when {
                    strategyCandidate == null -> "NO_TECHNICAL_CANDIDATE"
                    book == null -> "ORDERBOOK_MISSING"
                    !book.synchronized -> "ORDERBOOK_UNSYNCED"
                    book.updatedAtMs > evaluatedAt -> "ORDERBOOK_FUTURE_TIMESTAMP"
                    evaluatedAt - book.updatedAtMs > 2000L -> "ORDERBOOK_STALE"
                    !bookAgrees -> "ORDERBOOK_DIRECTION_MISMATCH"
                    result.signal != strategyCandidate -> "COMBINED_SCORE_REJECTED"
                    else -> "CONFIRMED"
                }))
        prefs.edit().putString("multi_stream_signal_json", output.toString()).apply()
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
        orderBookEngine?.close()
        orderBookEngine = null
        scope.cancel()
        super.onDestroy()
    }
}
